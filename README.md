# Rings and Toolkits: nnet vs. libp2p

![nnet's Chord ring with a spanning-tree broadcast beside a libp2p-style mesh of direct streams](images/00-hero.png)

A technical deep dive into [nnet](https://github.com/nknorg/nnet), NKN's Chord-based overlay network, and how it compares to [libp2p](https://libp2p.io). It covers architecture, core algorithms, performance and scalability, and includes a side-by-side benchmark you can rerun.

**📖 Read the full article: [as a web page](https://zbruceli.github.io/nnet_libp2p/) (recommended: contents sidebar, dark mode, works on phones) or [on GitHub](nnet-vs-libp2p-deep-dive.md).**

---

## The gist in one picture

![nnet routes messages over a ring; libp2p looks up a peer and dials it directly](images/01-philosophy.png)

Both get called "p2p network stacks", but they solve different problems:

- **nnet is an overlay network.** Every node joins one structured topology, an enhanced Chord ring. You hand nnet some bytes and a 256-bit key, and **the network carries the message hop by hop** to whichever node owns that key. The core is about 5,300 lines of Go.
- **libp2p is a connectivity toolkit.** Its job is to let any peer open an **authenticated, encrypted, multiplexed stream** to any other peer, over any transport and through NATs. Overlays such as the Kademlia DHT and GossipSub are separate modules. They help you *find* peers or *spread* messages, but data normally travels over a direct connection.

nnet's core operation is *"route this message through the network"*. libp2p's is *"open a secure stream to that peer"*. Almost every other difference follows from that one choice.

## At a glance

| | **nnet** | **libp2p** |
|---|---|---|
| Core abstraction | Message routed over a Chord overlay | Secure, multiplexed stream to a peer |
| Identity | Arbitrary 32-byte ID (application decides) | PeerID = hash of a public key, verified in the handshake |
| Transports | TCP, KCP | TCP, QUIC, WebSocket, WebTransport, WebRTC, … |
| Security | None built in (added through middleware) | Noise or TLS 1.3, mandatory |
| Message to a non-neighbor | Multi-hop relay, ≈ ½·log₂N hops | DHT lookup, then a direct dial (hole punching if needed) |
| Network-wide broadcast | Chord spanning tree (≈ 1 send per node) or flooding | GossipSub mesh (≈ 6 eager sends per node) plus lazy gossip |
| NAT traversal | UPnP / NAT-PMP | AutoNAT v2, Circuit Relay v2, DCUtR (≈ 70% hole-punch success) |
| Overload | Bounded channels that **drop** messages | Flow-controlled streams plus a hierarchical Resource Manager |
| Languages | Go | Go, Rust, JS/TS, Nim, Java, C++, Python, Zig, .NET, … |

## Key findings

**1. nnet's spanning-tree broadcast is its standout idea.** The Chord finger table already defines a spanning tree rooted at any node. Each node forwards only to the fingers below the arc its sender delegated to it, so every node receives the message about once and the tree is at most log₂N hops deep. ([§3.5](nnet-vs-libp2p-deep-dive.md#35-broadcast-ii-the-chord-spanning-tree))

![Spanning-tree broadcast edges on a 32-node ring](images/07-tree-broadcast.png)

**2. Its default configuration has a trap.** Duplicate filtering is enabled only for flooded messages, not tree messages. With one node per finger (K = 1) a few duplicates leak through, which is harmless. With redundancy (K = 3), duplicates re-propagate: in a 60-node local test, the tree cost **more than flooding** (56 vs. 37 sends per node), and simulation puts it at about **7,100 sends per node at 10,000 nodes**. Adding `BROADCAST_TREE` to `LocalRxMsgCacheRoutingType` (one config line) brings it down to 4.5. ([§3.5](nnet-vs-libp2p-deep-dive.md#35-broadcast-ii-the-chord-spanning-tree))

**3. Side by side, both stacks scale flat for broadcast. nnet is leaner but less reliable.** I benchmarked both from 16 to 256 nodes under identical conditions: same harness, same messages, constant total load, and libp2p security off to match nnet. ([§7.4](nnet-vs-libp2p-deep-dive.md#74-measured-an-apples-to-apples-scalability-benchmark))

| Broadcast, 1 KB messages | Wire bytes per delivered byte | CPU per delivery | Delivered |
|---|---|---|---|
| nnet tree, K = 1 | **1.3–1.4** | **130–185 µs** | 98.4–100% |
| nnet tree, K = 3 | 3.5–5.6 | 410–550 µs | 100% |
| GossipSub | 6.9–8.3 | 530–640 µs | 100% |
| nnet flooding | 15–23 | ≈ 1.6 ms | saturated the machine from 32 nodes |

The single-copy tree is about **5× leaner on the wire and 3.5× cheaper in CPU** than GossipSub. It still lost up to 1.6% of deliveries, and some nodes missed up to 11%, even with no nodes joining or leaving. With enough redundancy to deliver everything, it costs about the same as GossipSub.

**4. For point-to-point messages, the winner depends on how many peers each node talks to.** With random destinations, libp2p's direct streams are **2–3× cheaper** while every node can stay connected to every other node. But their connection count grows linearly with N, and per-message CPU rose 4.6× from 128 to 256 nodes. nnet's relay grows only logarithmically. Given the same connection budget, nnet's relay was cheaper from 128 nodes upward.

![Scaling elasticity of cost per delivery for every configuration](images/19-bench-scaling-elasticity.png)

*Scaling elasticity is how cost per delivery grows with network size: 0 means flat, 1 means proportional to N.*

**5. nnet pays to stay connected; libp2p pays on demand.** With no traffic, each nnet node still sends 0.7–1.5 KB/s of pings and Chord stabilization traffic to its O(log N) neighbors. libp2p sent no stream-level traffic while idle.

**6. Security is the biggest practical gap.** nnet doesn't bind node IDs to keys, has no encryption, and has no per-peer resource limits; all of these are left to the application. In libp2p they are mandatory, and in the benchmark Noise encryption plus signing added at most about 15% to GossipSub's wire bytes and no measurable CPU cost. ([§8](nnet-vs-libp2p-deep-dive.md#8-security-posture))

## Which one should you use?

**nnet (or its design)** fits when your application is naturally **key-addressed**, nodes are **publicly reachable servers or incentivized operators**, you need **cheap network-wide broadcast** of high-volume, loss-tolerant data, or you want a **deterministic, verifiable topology** so that relaying can be audited or rewarded.

**libp2p** fits when peers are **heterogeneous** (browsers, phones, NATed home machines, many languages), you need **security by default**, traffic is **session-oriented** between known peers, or you need **topic-based pubsub that holds up under attack**.

**Or combine them.** nnet's two best ideas, key-based relay with latency-aware next hops and finger-table tree broadcast, could run as a libp2p protocol and inherit libp2p's identity, encryption and NAT traversal. ([§10](nnet-vs-libp2p-deep-dive.md#10-which-one-should-you-use))

## What's in the full article

1. [Two philosophies](nnet-vs-libp2p-deep-dive.md#1-two-philosophies)
2. [nnet architecture](nnet-vs-libp2p-deep-dive.md#2-nnet-architecture): layers, wire protocol, the per-peer I/O engine, middleware
3. [nnet's core algorithms](nnet-vs-libp2p-deep-dive.md#3-nnets-core-algorithms): the "improved Chord", stabilization, latency-aware relay routing, flooding and tree broadcast
4. [libp2p architecture](nnet-vs-libp2p-deep-dive.md#4-libp2p-architecture): PeerID, multiaddr, the connection upgrade pipeline, NAT traversal, resource management
5. [libp2p's core algorithms](nnet-vs-libp2p-deep-dive.md#5-libp2ps-core-algorithms): Kademlia, GossipSub v1.0–v1.3, broadcast comparison
6. [Performance](nnet-vs-libp2p-deep-dive.md#6-performance): throughput, latency, who pays the bandwidth
7. [Scalability](nnet-vs-libp2p-deep-dive.md#7-scalability), including the [side-by-side benchmark](nnet-vs-libp2p-deep-dive.md#74-measured-an-apples-to-apples-scalability-benchmark)
8. [Security posture](nnet-vs-libp2p-deep-dive.md#8-security-posture)
9. [Developer experience](nnet-vs-libp2p-deep-dive.md#9-developer-experience)
10. [Which one should you use?](nnet-vs-libp2p-deep-dive.md#10-which-one-should-you-use)

The article includes 19 figures and charts.

## Repository layout

| Path | Contents |
|---|---|
| [nnet-vs-libp2p-deep-dive.md](nnet-vs-libp2p-deep-dive.md) | The article (Markdown) |
| [index.html](index.html) | The same article as a styled web page, published at [zbruceli.github.io/nnet_libp2p](https://zbruceli.github.io/nnet_libp2p/) (rebuild with `python3 build_html.py`) |
| [images/](images/) | All figures and charts (PNG) |
| [figure-src/](figure-src/) | Figure generator, hero image, and a simulator of nnet's broadcast and routing algorithms |
| [scalability-bench/](scalability-bench/) | Benchmark harness (Go), sweep driver, raw results and analysis ([methodology](scalability-bench/README.md)) |

Regenerate the figures:

```bash
cd figure-src && python3 sim.py && python3 figs.py ../images && python3 hero.py ../images
```

Rerun the benchmark (about 90 minutes on a 14-core machine):

```bash
cd scalability-bench && go build -tags nnet -o bench-nnet . && go build -tags libp2p -o bench-libp2p . && python3 run.py && ./warm.sh && python3 analyze.py
```

**Caveats:** the benchmark ran on one 14-core machine over loopback, with up to 256 nodes, no nodes joining or leaving, and a single run per point. Read it as relative comparisons and scaling trends, not production capacity.
