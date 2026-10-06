# nnet vs. libp2p: a technical deep dive

A comparison of [nnet](https://github.com/nknorg/nnet) (NKN's Chord-based overlay) and [libp2p](https://libp2p.io) covering architecture, core algorithms, performance and scalability, with a reproducible side-by-side benchmark.

| Path | Contents |
|---|---|
| [nnet-vs-libp2p-deep-dive.md](nnet-vs-libp2p-deep-dive.md) | The article |
| [images/](images/) | All figures and charts (PNG) |
| [figure-src/](figure-src/) | Figure generator and Chord broadcast/routing simulator |
| [scalability-bench/](scalability-bench/) | Benchmark harness (Go), sweep driver, raw results and analysis |

Regenerate the figures:

```bash
cd figure-src && python3 sim.py && python3 figs.py ../images
```

Rerun the benchmark (about 90 minutes on a 14-core machine):

```bash
cd scalability-bench && go build -tags nnet -o bench-nnet . && go build -tags libp2p -o bench-libp2p . && python3 run.py && ./warm.sh && python3 analyze.py
```
