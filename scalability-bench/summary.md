| Config | N | Delivery | Wire B / payload B | CPU µs / delivery | p50 / p99 ms | Conns / node |
|---|---|---|---|---|---|---|
| nnet tree K=1 | 16 | 99.39% | 1.30 | 128 | 0.28 / 1.8 | 15.0 |
| nnet tree K=1 | 32 | 98.36% | 1.37 | 149 | 0.62 / 3.2 | 24.8 |
| nnet tree K=1 | 64 | 98.40% | 1.33 | 180 | 0.91 / 2.7 | 31.2 |
| nnet tree K=1 | 128 | 99.63% | 1.43 | 135 | 0.80 / 2.2 | 37.6 |
| nnet tree K=1 | 256 | 99.95% | 1.40 | 184 | 1.47 / 5.0 | 41.9 |
| nnet tree K=3 | 16 | 99.97% | 3.49 | 413 | 0.28 / 2.6 | 15.0 |
| nnet tree K=3 | 32 | 99.97% | 4.16 | 509 | 0.49 / 3.2 | 28.9 |
| nnet tree K=3 | 64 | 99.97% | 4.70 | 422 | 0.77 / 2.2 | 39.2 |
| nnet tree K=3 | 128 | 99.99% | 5.37 | 494 | 1.77 / 13.6 | 47.1 |
| nnet tree K=3 | 256 | 99.95% | 5.55 | 546 | 4.06 / 41.3 | 56.9 |
| nnet push (flood) | 16 | 100.00% | 15.46 | 1237 | 0.55 / 7.8 | 15.0 |
| nnet push (flood) | 32 | 100.00% | 22.84 | 1592 | 521.10 / 2870.1 | 24.4 |
| nnet push (flood) | 64 | 97.26% | 22.16 | 1418 | 476.15 / 1469.1 | 24.9 |
| nnet push (flood) | 128 | 63.86% | 21.13 | 1682 | 129.51 / 1805.3 | 23.5 |
| nnet push (flood) | 256 | 80.02% | 16.81 | 1677 | 772.11 / 3314.6 | 23.6 |
| GossipSub | 16 | 100.00% | 7.37 | 531 | 0.23 / 1.4 | 12.2 |
| GossipSub | 32 | 100.00% | 8.30 | 639 | 0.39 / 1.5 | 15.4 |
| GossipSub | 64 | 100.00% | 7.31 | 584 | 0.68 / 2.2 | 16.4 |
| GossipSub | 128 | 100.00% | 7.48 | 599 | 1.15 / 4.6 | 17.4 |
| GossipSub | 256 | 100.00% | 6.93 | 568 | 1.94 / 9.3 | 17.7 |
| GossipSub + Noise + signing | 16 | 100.00% | 8.50 | 661 | 0.32 / 1.8 | 12.5 |
| GossipSub + Noise + signing | 32 | 100.00% | 7.42 | 545 | 0.51 / 2.5 | 14.9 |
| GossipSub + Noise + signing | 64 | 100.00% | 7.59 | 525 | 0.82 / 4.5 | 16.2 |
| GossipSub + Noise + signing | 128 | 100.00% | 7.65 | 523 | 1.35 / 9.0 | 17.3 |
| GossipSub + Noise + signing | 256 | 100.00% | 7.34 | 489 | 2.27 / 18.8 | 17.6 |
| nnet relay (multi-hop) | 16 | 100.00% | 1.88 | 110 | 0.05 / 0.1 | 15.0 |
| nnet relay (multi-hop) | 32 | 99.99% | 2.32 | 146 | 0.06 / 0.2 | 28.6 |
| nnet relay (multi-hop) | 64 | 100.00% | 2.74 | 191 | 0.07 / 0.3 | 38.8 |
| nnet relay (multi-hop) | 128 | 100.00% | 3.28 | 264 | 0.10 / 0.8 | 47.4 |
| nnet relay (multi-hop) | 256 | 100.00% | 3.84 | 431 | 0.15 / 2.2 | 56.3 |
| libp2p direct, unlimited conns | 16 | 100.00% | 1.00 | 56 | 0.02 / 0.1 | 15.0 |
| libp2p direct, unlimited conns | 32 | 100.00% | 1.00 | 63 | 0.05 / 0.1 | 31.0 |
| libp2p direct, unlimited conns | 64 | 100.00% | 1.01 | 74 | 0.05 / 0.2 | 63.0 |
| libp2p direct, unlimited conns | 128 | 100.00% | 1.09 | 128 | 0.05 / 1.9 | 127.0 |
| libp2p direct, unlimited conns | 256 | 28.45% | 5.51 | 2585 | 154.33 / 5496.6 | 249.9 |
| libp2p direct, conns capped = nnet’s | 16 | 100.00% | 1.00 | 57 | 0.02 / 0.1 | 15.0 |
| libp2p direct, conns capped = nnet’s | 32 | 100.00% | 1.00 | 63 | 0.05 / 0.1 | 31.0 |
| libp2p direct, conns capped = nnet’s | 64 | 100.00% | 1.10 | 122 | 0.05 / 0.7 | 54.1 |
| libp2p direct, conns capped = nnet’s | 128 | 99.99% | 1.70 | 432 | 0.05 / 3.1 | 53.7 |
| libp2p direct, conns capped = nnet’s | 256 | 89.67% | 2.77 | 1477 | 139.80 / 493.7 | 59.0 |
| libp2p direct + Noise | 16 | 100.00% | 1.00 | 58 | 0.02 / 0.1 | 15.0 |
| libp2p direct + Noise | 32 | 100.00% | 1.00 | 67 | 0.05 / 0.1 | 31.0 |
| libp2p direct + Noise | 64 | 100.00% | 1.01 | 73 | 0.05 / 0.2 | 63.0 |
| libp2p direct + Noise | 128 | 100.00% | 1.09 | 141 | 0.05 / 1.8 | 127.0 |
| libp2p direct + Noise | 256 | 28.82% | 5.32 | 3296 | 173.18 / 7518.1 | 242.9 |
| libp2p direct, steady state (after 90 s warm-up) | 128 | 100.00% | 1.00 | 73 | 0.05 / 1.7 | 127.0 |
| libp2p direct, steady state (after 90 s warm-up) | 256 | 99.87% | 1.02 | 334 | 0.09 / 1278.9 | 235.2 |

| Config | N | Bytes / node / s | CPU ms / node / s | Conns / node | Heap MB / node |
|---|---|---|---|---|---|
| nnet (Chord stabilization + RTT pings) | 16 | 718 | 5.3 | 15.0 | 6.0 |
| nnet (Chord stabilization + RTT pings) | 32 | 939 | 8.6 | 28.9 | 9.7 |
| nnet (Chord stabilization + RTT pings) | 64 | 1,133 | 7.7 | 39.2 | 12.3 |
| nnet (Chord stabilization + RTT pings) | 128 | 1,321 | 3.8 | 48.0 | 14.8 |
| nnet (Chord stabilization + RTT pings) | 256 | 1,507 | 3.3 | 56.6 | 17.0 |
| libp2p (GossipSub + Kademlia) | 16 | 0 | 0.2 | 15.0 | 1.6 |
| libp2p (GossipSub + Kademlia) | 32 | 0 | 0.4 | 31.0 | 2.4 |
| libp2p (GossipSub + Kademlia) | 64 | 0 | 0.5 | 60.9 | 3.8 |
| libp2p (GossipSub + Kademlia) | 128 | 0 | 0.8 | 101.5 | 5.4 |
| libp2p (GossipSub + Kademlia) | 256 | 0 | 2.8 | 147.1 | 7.4 |

Scaling elasticity = slope of log(cost) vs log(N); 0 = cost per delivery independent of network size.

| Config | wire-bytes elasticity | CPU elasticity | conns elasticity |
|---|---|---|---|
| nnet tree K=1 | +0.03 | +0.09 | +0.36 |
| nnet tree K=3 | +0.17 | +0.08 | +0.45 |
| nnet push (flood) | +0.01 | +0.10 | +0.13 |
| GossipSub | -0.03 | +0.01 | +0.12 |
| GossipSub + Noise + signing | -0.04 | -0.09 | +0.12 |
| nnet relay (multi-hop) | +0.26 | +0.48 | +0.45 |
| libp2p direct, unlimited conns | +0.50 | +1.21 | +1.02 |
| libp2p direct, conns capped = nnet’s | +0.37 | +1.22 | +0.47 |
| libp2p direct + Noise | +0.49 | +1.27 | +1.01 |
| libp2p direct, steady state (after 90 s warm-up) | +0.03 | +2.19 | +0.89 |
| nnet (Chord stabilization + RTT pings) | +0.26 | -0.25 | +0.46 |
| libp2p (GossipSub + Kademlia) | +nan | +0.82 | +0.83 |
