//go:build libp2p

package main

import (
	"bufio"
	"context"
	"encoding/binary"
	"fmt"
	"io"
	mrand "math/rand"
	"sync"
	"time"

	"github.com/libp2p/go-libp2p"
	dht "github.com/libp2p/go-libp2p-kad-dht"
	pubsub "github.com/libp2p/go-libp2p-pubsub"
	pubsubpb "github.com/libp2p/go-libp2p-pubsub/pb"
	"github.com/libp2p/go-libp2p/core/host"
	"github.com/libp2p/go-libp2p/core/metrics"
	"github.com/libp2p/go-libp2p/core/network"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/core/protocol"
	"github.com/libp2p/go-libp2p/p2p/muxer/yamux"
	"github.com/libp2p/go-libp2p/p2p/net/connmgr"
	"github.com/libp2p/go-libp2p/p2p/security/noise"
	"github.com/libp2p/go-libp2p/p2p/transport/tcp"
)

const benchProto = protocol.ID("/bench/unicast/1.0.0")
const topicName = "bench"

func build(impl string, n int, st *stats) (cluster, error) {
	ctx := context.Background()
	switch impl {
	case "gossipsub":
		return buildLibp2p(ctx, n, st, "bcast")
	case "libp2p-direct":
		return buildLibp2p(ctx, n, st, "unicast")
	case "libp2p-idle":
		return buildLibp2p(ctx, n, st, "idle")
	}
	return nil, fmt.Errorf("impl %s not in this binary (built with -tags libp2p)", impl)
}

// ================================================================ libp2p
type p2pCluster struct {
	hosts  []host.Host
	topics []*pubsub.Topic
	dhts   []*dht.IpfsDHT
	bwc    []*metrics.BandwidthCounter
	index  map[peer.ID]int
	st     *stats
	mode   string
	// unicast: one cached outbound stream per (src,dst)
	streams []map[int]*lockedStream
	smu     []sync.Mutex
	sem     chan struct{}
}

type lockedStream struct {
	mu sync.Mutex
	s  network.Stream
	w  *bufio.Writer
}

func buildLibp2p(ctx context.Context, n int, st *stats, mode string) (*p2pCluster, error) {
	c := &p2pCluster{index: map[peer.ID]int{}, st: st, mode: mode, sem: make(chan struct{}, *inflight)}
	for i := 0; i < n; i++ {
		bwc := metrics.NewBandwidthCounter()
		opts := []libp2p.Option{
			libp2p.ListenAddrStrings("/ip4/127.0.0.1/tcp/0"),
			libp2p.Transport(tcp.NewTCPTransport),
			libp2p.Muxer(yamux.ID, yamux.DefaultTransport),
			libp2p.ResourceManager(&network.NullResourceManager{}),
			libp2p.BandwidthReporter(bwc),
			libp2p.DisableRelay(),
		}
		if *connHigh > 0 {
			cm, err := connmgr.NewConnManager(*connHigh*2/3, *connHigh, connmgr.WithGracePeriod(2*time.Second), connmgr.WithSilencePeriod(time.Second))
			if err != nil {
				return nil, err
			}
			opts = append(opts, libp2p.ConnectionManager(cm))
		}
		if *secure {
			opts = append(opts, libp2p.Security(noise.ID, noise.New))
		} else {
			opts = append(opts, libp2p.NoSecurity)
		}
		h, err := libp2p.New(opts...)
		if err != nil {
			return nil, err
		}
		c.hosts = append(c.hosts, h)
		c.bwc = append(c.bwc, bwc)
		c.index[h.ID()] = i
	}
	// bootstrap: each node dials `degree` random earlier-or-later peers
	for i, h := range c.hosts {
		for _, j := range mrand.Perm(n)[:min(*degree+1, n)] {
			if j == i {
				continue
			}
			o := c.hosts[j]
			h.Peerstore().AddAddrs(o.ID(), o.Addrs(), time.Hour)
			if err := h.Connect(ctx, peer.AddrInfo{ID: o.ID(), Addrs: o.Addrs()}); err != nil {
				return nil, err
			}
		}
	}
	switch mode {
	case "bcast", "idle":
		for i, h := range c.hosts {
			popts := []pubsub.Option{pubsub.WithPeerOutboundQueueSize(1024), pubsub.WithValidateQueueSize(1024)}
			if !*secure {
				popts = append(popts,
					pubsub.WithMessageSignaturePolicy(pubsub.StrictNoSign),
					pubsub.WithMessageIdFn(func(m *pubsubpb.Message) string { return string(m.Data[:16]) }))
			} else {
				popts = append(popts, pubsub.WithMessageIdFn(func(m *pubsubpb.Message) string { return string(m.Data[:16]) }))
			}
			ps, err := pubsub.NewGossipSub(ctx, h, popts...)
			if err != nil {
				return nil, err
			}
			t, err := ps.Join(topicName)
			if err != nil {
				return nil, err
			}
			sub, err := t.Subscribe()
			if err != nil {
				return nil, err
			}
			c.topics = append(c.topics, t)
			idx := i
			go func() {
				for {
					m, err := sub.Next(ctx)
					if err != nil {
						return
					}
					st.onDeliver(idx, m.Data)
				}
			}()
		}
	}
	if mode == "unicast" || mode == "idle" {
		c.streams = make([]map[int]*lockedStream, n)
		c.smu = make([]sync.Mutex, n)
		for i, h := range c.hosts {
			c.streams[i] = map[int]*lockedStream{}
			d, err := dht.New(h, dht.Mode(dht.ModeServer), dht.ProtocolPrefix("/bench"))
			if err != nil {
				return nil, err
			}
			c.dhts = append(c.dhts, d)
			idx := i
			h.SetStreamHandler(benchProto, func(s network.Stream) {
				r := bufio.NewReaderSize(s, 64<<10)
				lb := make([]byte, 4)
				for {
					if _, err := io.ReadFull(r, lb); err != nil {
						s.Reset()
						return
					}
					buf := make([]byte, binary.BigEndian.Uint32(lb))
					if _, err := io.ReadFull(r, buf); err != nil {
						s.Reset()
						return
					}
					st.onDeliver(idx, buf)
				}
			})
		}
		for _, d := range c.dhts {
			d.Bootstrap(ctx)
		}
		// let routing tables fill (peers learn each other via DHT queries)
		time.Sleep(5 * time.Second)
		for _, d := range c.dhts {
			d.RefreshRoutingTable()
		}
	}
	return c, nil
}

func (c *p2pCluster) stream(src, dst int) (*lockedStream, error) {
	c.smu[src].Lock()
	ls, ok := c.streams[src][dst]
	if !ok {
		ls = &lockedStream{}
		c.streams[src][dst] = ls
	}
	c.smu[src].Unlock()
	ls.mu.Lock()
	if ls.s != nil && ls.s.Conn().IsClosed() {
		ls.s = nil
	}
	if ls.s != nil {
		return ls, nil // returned locked
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	h := c.hosts[src]
	target := c.hosts[dst].ID()
	if h.Network().Connectedness(target) != network.Connected && len(h.Peerstore().Addrs(target)) == 0 {
		info, err := c.dhts[src].FindPeer(ctx, target) // the libp2p way to locate an unknown peer
		if err != nil {
			ls.mu.Unlock()
			return nil, err
		}
		h.Peerstore().AddAddrs(info.ID, info.Addrs, time.Hour)
	}
	s, err := h.NewStream(ctx, target, benchProto)
	if err != nil {
		ls.mu.Unlock()
		return nil, err
	}
	ls.s, ls.w = s, bufio.NewWriterSize(s, 64<<10)
	return ls, nil
}

func (c *p2pCluster) send(sender int, payload []byte, dest int) {
	if dest < 0 {
		c.topics[sender].Publish(context.Background(), payload)
		return
	}
	c.sem <- struct{}{}
	go func() {
		defer func() { <-c.sem }()
		lb := make([]byte, 4)
		binary.BigEndian.PutUint32(lb, uint32(len(payload)))
		for attempt := 0; attempt < 2; attempt++ { // retry once if a cached stream died (e.g. connection trimmed)
			ls, err := c.stream(sender, dest)
			if err != nil {
				return
			}
			ls.w.Write(lb)
			ls.w.Write(payload)
			err = ls.w.Flush()
			if err != nil {
				ls.s.Reset()
				ls.s = nil
			}
			ls.mu.Unlock()
			if err == nil {
				return
			}
		}
	}()
}
func (c *p2pCluster) conns() float64 {
	t := 0
	for _, h := range c.hosts {
		t += len(h.Network().Peers())
	}
	return float64(t) / float64(len(c.hosts))
}
func (c *p2pCluster) wire() int64 {
	var t int64
	for _, b := range c.bwc {
		t += b.GetBandwidthTotals().TotalOut
	}
	return t
}
