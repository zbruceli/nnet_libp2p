// scalability-bench: apples-to-apples scalability comparison of nnet and libp2p.
//
// One process hosts N nodes of ONE stack on 127.0.0.1/TCP. Each node runs the
// stack's own overlay; the harness only injects load and observes:
//
//	bcast   : every message must reach all N-1 other nodes
//	          nnet-tree (Chord spanning tree, K=1, rx dedup on), nnet-push (flooding),
//	          gossipsub (libp2p GossipSub, one topic)
//	unicast : every message must reach one uniformly random node
//	          nnet-relay (multi-hop Chord routing to the node's ID),
//	          libp2p-direct (Kademlia FindPeer if unknown, then a direct stream, cached)
//	idle    : no application traffic, measures maintenance overhead
//
// Normalised outputs (JSON, one line per run): delivery ratio, latency,
// application-layer wire bytes per delivered payload byte, CPU microseconds per
// delivery, connections / goroutines / heap per node.
package main

import (
	"crypto/rand"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	mrand "math/rand"
	"os"
	"runtime"
	"sort"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

// ---------------------------------------------------------------- options
var (
	impl     = flag.String("impl", "nnet-tree", "nnet-tree | nnet-push | nnet-relay | gossipsub | libp2p-direct | nnet-idle | libp2p-idle")
	numNodes = flag.Int("n", 32, "number of nodes")
	msgSize  = flag.Int("size", 1024, "payload size in bytes")
	load     = flag.Float64("load", 10000, "target deliveries/s for the whole network (bcast: msgs/s = load/(n-1); unicast: msgs/s = load)")
	measure  = flag.Duration("dur", 20*time.Second, "measurement window")
	settle   = flag.Duration("settle", 15*time.Second, "extra settle time after topology is built")
	secure   = flag.Bool("secure", false, "libp2p: Noise encryption + message signing (libp2p defaults); nnet: ignored")
	degree   = flag.Int("degree", 8, "libp2p: number of random peers each node dials at bootstrap")
	basePort = flag.Int("port", 30000, "nnet: first TCP port")
	label    = flag.String("label", "", "free-form label copied to the output")
	fingerK  = flag.Int("k", 1, "nnet: NumFingerSuccessors for broadcast runs (tree redundancy K)")
	connHigh = flag.Int("connhigh", 0, "libp2p: connection manager high-water mark (0 = unlimited); low = 2/3 of it")
	warm     = flag.Duration("warm", 0, "send the same traffic for this long before measuring (not counted), e.g. to reach steady-state connections")
	inflight = flag.Int("inflight", 512, "libp2p-direct: max concurrent sends being set up")
)

// ---------------------------------------------------------------- observation
type stats struct {
	mu        sync.Mutex
	latencies []time.Duration
	delivered atomic.Int64
	wireBytes atomic.Int64 // nnet only; libp2p uses its bandwidth counter
	seen      []sync.Map   // per-node dedup of message ids (counts unique deliveries)
	perNode   []atomic.Int64
	winStart  int64 // unix nanos: only messages sent inside the window count
	winEnd    int64
}

func newStats(n int) *stats {
	return &stats{seen: make([]sync.Map, n), perNode: make([]atomic.Int64, n)}
}

// payload: [0:8] msg seq | [8:16] sender index | [16:24] send time | rest padding
func makePayload(seq uint64, sender int) []byte {
	b := make([]byte, *msgSize)
	binary.BigEndian.PutUint64(b[0:], seq)
	binary.BigEndian.PutUint64(b[8:], uint64(sender))
	binary.BigEndian.PutUint64(b[16:], uint64(time.Now().UnixNano()))
	return b
}

func (s *stats) onDeliver(nodeIdx int, data []byte) {
	if len(data) < 24 {
		return
	}
	sent := int64(binary.BigEndian.Uint64(data[16:]))
	if sent < s.winStart || sent >= s.winEnd {
		return
	}
	if int(binary.BigEndian.Uint64(data[8:])) == nodeIdx {
		return // never count a node receiving its own message
	}
	if _, dup := s.seen[nodeIdx].LoadOrStore(string(data[:16]), struct{}{}); dup {
		return
	}
	s.delivered.Add(1)
	s.perNode[nodeIdx].Add(1)
	lat := time.Duration(time.Now().UnixNano() - sent)
	s.mu.Lock()
	s.latencies = append(s.latencies, lat)
	s.mu.Unlock()
}

// ---------------------------------------------------------------- stack abstraction
type cluster interface {
	send(sender int, payload []byte, dest int) // dest < 0 => broadcast
	conns() float64                            // mean connections per node
	wire() int64                               // application-layer bytes written, whole network
}

// ================================================================ main
func cpuSeconds() float64 {
	var ru syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ru)
	return float64(ru.Utime.Sec+ru.Stime.Sec) + float64(ru.Utime.Usec+ru.Stime.Usec)/1e6
}

func pct(d []time.Duration, p float64) float64 {
	if len(d) == 0 {
		return 0
	}
	return float64(d[min(len(d)-1, int(p*float64(len(d))))].Microseconds()) / 1000
}

func main() {
	flag.Parse()
	n := *numNodes
	st := newStats(n)
	var c cluster
	var err error
	mode := map[string]string{"nnet-tree": "bcast", "nnet-push": "bcast", "gossipsub": "bcast",
		"nnet-relay": "unicast", "libp2p-direct": "unicast", "nnet-idle": "idle", "libp2p-idle": "idle"}[*impl]
	buildStart := time.Now()
	c, err = build(*impl, n, st)
	if err != nil {
		fmt.Fprintln(os.Stderr, "build:", err)
		os.Exit(1)
	}
	buildSecs := time.Since(buildStart).Seconds()
	time.Sleep(*settle)

	msgsPerSec := 0.0
	switch mode {
	case "bcast":
		msgsPerSec = *load / float64(n-1)
	case "unicast":
		msgsPerSec = *load
	}

	// ---- optional warm-up traffic (not counted: winStart/winEnd are still 0)
	if *warm > 0 && msgsPerSec > 0 {
		wrng := mrand.New(mrand.NewSource(2))
		interval := time.Duration(float64(time.Second) / msgsPerSec)
		w0 := time.Now()
		next := w0
		seq := uint64(1) << 40
		for time.Now().Before(w0.Add(*warm)) {
			if d := time.Until(next); d > 0 {
				time.Sleep(d)
			}
			for !next.After(time.Now()) {
				s := wrng.Intn(n)
				dest := -1
				if mode == "unicast" {
					dest = wrng.Intn(n - 1)
					if dest >= s {
						dest++
					}
				}
				c.send(s, makePayload(seq, s), dest)
				seq++
				next = next.Add(interval)
			}
		}
		time.Sleep(5 * time.Second)
	}

	// ---- measurement window
	runtime.GC()
	wire0, cpu0 := c.wire(), cpuSeconds()
	t0 := time.Now()
	st.winStart = t0.UnixNano()
	st.winEnd = t0.Add(*measure).UnixNano()
	var sent int64
	rng := mrand.New(mrand.NewSource(1))
	var buf [16]byte
	rand.Read(buf[:])
	if msgsPerSec > 0 {
		interval := time.Duration(float64(time.Second) / msgsPerSec)
		next := t0
		for time.Now().Before(t0.Add(*measure)) {
			if d := time.Until(next); d > 0 {
				time.Sleep(d)
			}
			// catch up in batches if the sleep overshot
			for !next.After(time.Now()) && next.Before(t0.Add(*measure)) {
				s := rng.Intn(n)
				dest := -1
				if mode == "unicast" {
					dest = rng.Intn(n - 1)
					if dest >= s {
						dest++
					}
				}
				c.send(s, makePayload(uint64(sent), s), dest)
				sent++
				next = next.Add(interval)
			}
		}
	} else {
		time.Sleep(*measure)
	}
	time.Sleep(5 * time.Second) // drain
	elapsed := time.Since(t0).Seconds()
	wire1, cpu1 := c.wire(), cpuSeconds()

	expected := sent
	if mode == "bcast" {
		expected = sent * int64(n-1)
	}
	delivered := st.delivered.Load()
	st.mu.Lock()
	lat := append([]time.Duration(nil), st.latencies...)
	st.mu.Unlock()
	sort.Slice(lat, func(a, b int) bool { return lat[a] < lat[b] })
	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)

	wireBytes := float64(wire1 - wire0)
	minCov, below := 1.0, 0
	if mode == "bcast" && sent > 0 {
		for i := 0; i < n; i++ {
			// node i should receive every message not sent by itself (~ sent*(n-1)/n)
			cov := float64(st.perNode[i].Load()) / (float64(sent) * float64(n-1) / float64(n))
			if cov < minCov {
				minCov = cov
			}
			if cov < 0.99 {
				below++
			}
		}
	}
	cpu := cpu1 - cpu0
	res := map[string]any{
		"impl": *impl, "mode": mode, "n": n, "secure": *secure, "label": *label, "size": *msgSize,
		"offered_deliveries_per_s": *load, "msgs_sent": sent, "expected": expected, "delivered": delivered,
		"delivery_ratio": float64(delivered) / float64(max(expected, 1)),
		"lat_p50_ms":     pct(lat, 0.50), "lat_p99_ms": pct(lat, 0.99),
		"wire_bytes":                            wireBytes,
		"wire_bytes_per_delivered_payload_byte": wireBytes / float64(max(delivered, 1)*int64(*msgSize)),
		"cpu_s":                                 cpu,
		"cpu_us_per_delivery":                   cpu * 1e6 / float64(max(delivered, 1)),
		"wire_bytes_per_node_s":                 wireBytes / elapsed / float64(n),
		"cpu_ms_per_node_s":                     cpu * 1e3 / elapsed / float64(n),
		"conns_per_node":                        c.conns(),
		"goroutines_per_node":                   float64(runtime.NumGoroutine()) / float64(n),
		"heap_mb_per_node":                      float64(ms.HeapInuse) / 1e6 / float64(n),
		"build_s":                               buildSecs, "min_node_coverage": minCov, "nodes_below_99pct": below, "conn_high": *connHigh,
	}
	out, _ := json.Marshal(res)
	fmt.Println(string(out))
	os.Exit(0)
}
