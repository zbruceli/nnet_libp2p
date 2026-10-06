//go:build nnet

package main

import (
	"fmt"
	mrand "math/rand"
	"sort"
	"time"

	"github.com/nknorg/nnet"
	"github.com/nknorg/nnet/node"
	"github.com/nknorg/nnet/overlay/chord"
	pbmsg "github.com/nknorg/nnet/protobuf/message"
)

func build(impl string, n int, st *stats) (cluster, error) {
	switch impl {
	case "nnet-tree":
		return buildNNet(n, st, pbmsg.RoutingType_BROADCAST_TREE)
	case "nnet-push":
		return buildNNet(n, st, pbmsg.RoutingType_BROADCAST_PUSH)
	case "nnet-relay", "nnet-idle":
		return buildNNet(n, st, pbmsg.RoutingType_RELAY)
	}
	return nil, fmt.Errorf("impl %s not in this binary (built with -tags nnet)", impl)
}

// ================================================================ nnet
type quietLogger struct{}

func (quietLogger) Debug(...interface{})            {}
func (quietLogger) Debugf(string, ...interface{})   {}
func (quietLogger) Info(...interface{})             {}
func (quietLogger) Infof(string, ...interface{})    {}
func (quietLogger) Warning(...interface{})          {}
func (quietLogger) Warningf(string, ...interface{}) {}
func (quietLogger) Error(...interface{})            {}
func (quietLogger) Errorf(string, ...interface{})   {}

type nnetCluster struct {
	nodes []*nnet.NNet
	ids   [][]byte
	rt    pbmsg.RoutingType
	st    *stats
}

func buildNNet(n int, st *stats, rt pbmsg.RoutingType) (*nnetCluster, error) {
	nnet.SetLogger(quietLogger{})
	c := &nnetCluster{rt: rt, st: st}
	for i := 0; i < n; i++ {
		conf := &nnet.Config{
			Port:                uint16(*basePort + i),
			Hostname:            "127.0.0.1",
			NumFingerSuccessors: uint32(*fingerK), // K: tree redundancy (1 = pure spanning tree)
			LocalRxMsgCacheRoutingType: []pbmsg.RoutingType{
				pbmsg.RoutingType_BROADCAST_PUSH, pbmsg.RoutingType_BROADCAST_TREE,
			},
		}
		if rt == pbmsg.RoutingType_RELAY {
			conf.NumFingerSuccessors = 3 // library default; gives RTT-based route choice
		}
		nn, err := nnet.NewNNet(nil, conf)
		if err != nil {
			return nil, err
		}
		idx := i
		nn.MustApplyMiddleware(node.BytesReceived{Func: func(msg, msgID, srcID []byte, rn *node.RemoteNode) ([]byte, bool) {
			st.onDeliver(idx, msg)
			return msg, true
		}, Priority: 0})
		nn.MustApplyMiddleware(node.MessageEncoded{Func: func(rn *node.RemoteNode, buf []byte) ([]byte, bool) {
			st.wireBytes.Add(int64(len(buf) + 4)) // + 4-byte length prefix
			return buf, true
		}, Priority: 0})
		c.nodes = append(c.nodes, nn)
		c.ids = append(c.ids, nn.GetLocalNode().Id)
	}
	for i, nn := range c.nodes {
		if err := nn.Start(i == 0); err != nil {
			return nil, err
		}
		if i > 0 {
			if err := nn.Join(c.nodes[mrand.Intn(i)].GetLocalNode().Addr); err != nil {
				return nil, err
			}
		}
		time.Sleep(40 * time.Millisecond)
	}
	// wait until the ring is correct: every node's first successor is its true successor
	sorted := make([]int, n)
	for i := range sorted {
		sorted[i] = i
	}
	sort.Slice(sorted, func(a, b int) bool { return chord.CompareID(c.ids[sorted[a]], c.ids[sorted[b]]) < 0 })
	trueSucc := make(map[int][]byte, n)
	for k, i := range sorted {
		trueSucc[i] = c.ids[sorted[(k+1)%n]]
	}
	deadline := time.Now().Add(5 * time.Minute)
	for time.Now().Before(deadline) {
		ok := 0
		for i, nn := range c.nodes {
			succ := nn.Network.(*chord.Chord).Successors()
			if len(succ) > 0 && chord.CompareID(succ[0].Id, trueSucc[i]) == 0 {
				ok++
			}
		}
		if ok == n {
			break
		}
		time.Sleep(500 * time.Millisecond)
	}
	return c, nil
}

func (c *nnetCluster) send(sender int, payload []byte, dest int) {
	nn := c.nodes[sender]
	if dest < 0 {
		nn.SendBytesBroadcastAsync(payload, c.rt)
	} else {
		nn.SendBytesRelayAsync(payload, c.ids[dest])
	}
}
func (c *nnetCluster) conns() float64 {
	t := 0
	for _, nn := range c.nodes {
		nb, _ := nn.GetLocalNode().GetNeighbors(nil)
		t += len(nb)
	}
	return float64(t) / float64(len(c.nodes))
}
func (c *nnetCluster) wire() int64 { return c.st.wireBytes.Load() }
