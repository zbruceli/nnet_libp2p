# nnet vs. libp2p: apples-to-apples scalability benchmark

This harness answers one question: **as the network grows, how much does each stack pay to deliver one useful message?**
Absolute throughput on one laptop says little about a real deployment. *Cost per delivery as N grows* does carry over, because it measures the work the protocol itself creates.

## What is held equal

| Dimension | nnet | libp2p |
|---|---|---|
| Language / runtime | Go 1.26, same process model | same |
| Transport | TCP on 127.0.0.1 | TCP on 127.0.0.1 (QUIC, WebRTC, etc. disabled) |
| Stream multiplexer | smux (nnet default) | yamux (libp2p default) |
| Serialization | protobuf | protobuf |
| Encryption | none (nnet has none built in) | **none** (`libp2p.NoSecurity`) in the main series; Noise in the `-secure` series |
| Message authentication | none | **none** (`StrictNoSign`) in the main series; signing in `gossipsub-secure` |
| Resource limits | nnet's bounded channels (2,333 per peer) | `NullResourceManager`; GossipSub outbound and validation queues raised to 1,024 so they are comparable to nnet's buffers |
| Payload | 1 KB, same generator, same random seed | same |
| Offered load | constant total **deliveries/s** at every N | same |
| Process isolation | one process per (stack, N) run, and each binary links only one stack (build tags) | same |

Only the stack and its own routing algorithm differ.

## Workloads

- **bcast**: every message must reach all N−1 other nodes. Senders are chosen at random, at `load/(N−1)` messages/s, so the network always performs `load` = 10,000 deliveries/s.
  - `nnet-tree-k1`: Chord spanning tree with one node per finger and rx dedup on (the most efficient setting).
  - `nnet-tree-k3`: the same with K = 3 redundancy (nnet's default finger size), with dedup on.
  - `nnet-push`: flooding to all neighbors.
  - `gossipsub`: one topic, every node subscribed, default GossipSub parameters (D = 6, flood-publish on).
  - `gossipsub-secure`: the same plus Noise encryption and message signing, i.e. libp2p's defaults.
- **unicast**: a random source sends to a uniformly random destination at 5,000 msgs/s.
  - `nnet-relay`: `SendBytesRelayAsync` to the destination's ID, routed hop by hop over Chord.
  - `libp2p-direct`: if the sender doesn't know the peer's address it calls Kademlia `FindPeer`, then opens a direct stream that is cached per (src, dst) pair. Connections are unlimited, which is the default with `NullResourceManager`.
  - `libp2p-direct-capped`: the same, but a connection manager caps each node at **the number of connections nnet used at that N**, so both stacks get the same connection budget.
  - `libp2p-direct-secure`: unlimited, with Noise.
- **idle**: no application traffic. Measures the cost of staying in the network (Chord stabilization and RTT pings, versus GossipSub heartbeats, Kademlia refresh and identify).

## Metrics (per run, written as one JSON line)

| Metric | Meaning |
|---|---|
| `delivery_ratio` | unique deliveries / expected deliveries, for messages sent inside the measurement window |
| `min_node_coverage`, `nodes_below_99pct` | broadcast only: is any node systematically missed? |
| `wire_bytes_per_delivered_payload_byte` | all application-layer bytes written by all nodes (data + control + maintenance) ÷ useful payload bytes delivered. **Amplification factor; 1.0 is ideal.** |
| `cpu_us_per_delivery` | process CPU time (user + sys) over the window ÷ deliveries |
| `lat_p50_ms`, `lat_p99_ms` | send → first receipt |
| `conns_per_node`, `heap_mb_per_node`, `goroutines_per_node` | state each node carries |
| `wire_bytes_per_node_s`, `cpu_ms_per_node_s` | for idle runs, the maintenance overhead |

**Scaling elasticity** (computed in `summary.md`) is the slope of log(cost) against log(N). An elasticity of 0 means per-delivery cost doesn't depend on network size (perfect scaling), 1 means cost grows linearly with N, and log-N growth shows up as a small positive slope.

Wire bytes are counted at the application layer in both stacks. For nnet that is the `MessageEncoded` middleware: protobuf frame plus the 4-byte length prefix. For libp2p it is the `BandwidthReporter` on streams. Muxer frame headers and TCP/IP headers are excluded on both sides.

## Known limitations

- **One machine.** All N nodes share 14 cores and loopback, so CPU per delivery includes scheduler and GC contention. Compare stacks with each other, not with production numbers.
- **N ≤ 256.** Larger networks need multiple machines. Use the trend (elasticity), not the endpoints. The Chord simulation in `../figure-src/sim.py` extends the nnet broadcast-cost curve to 10,000 nodes.
- **No real latency or bandwidth limits.** Loopback RTT is microseconds, so latency results show protocol hops and queuing, not WAN behavior.
- **Static membership.** No churn during measurement. With churn, nnet's K = 1 tree would lose more messages, and GossipSub's mesh repair would matter more.
- **Different multiplexers** (smux vs. yamux), because each stack uses its own default. nnet can also run yamux (`Multiplexer: "yamux"`).

## Run it

```bash
go build -tags nnet -o bench-nnet . && go build -tags libp2p -o bench-libp2p .
```

```bash
python3 run.py
```

```bash
python3 analyze.py
```

A single configuration can be run with, for example, `./bench-libp2p -impl gossipsub -n 64 -secure`.
