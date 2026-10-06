#!/usr/bin/env python3
"""Sweep driver: runs each (stack, N) configuration in its own process, appends JSON lines.

usage: python3 run.py [--quick] [--only substr] [--out results.jsonl]
"""
import argparse, json, subprocess, sys, time, os

HERE = os.path.dirname(os.path.abspath(__file__))
# (binary, impl, extra flags, label)
BCAST = [("nnet", "nnet-tree", ["-k", "1"], "nnet-tree-k1"), ("nnet", "nnet-tree", ["-k", "3"], "nnet-tree-k3"),
         ("nnet", "nnet-push", [], "nnet-push"), ("libp2p", "gossipsub", [], "gossipsub"),
         ("libp2p", "gossipsub", ["-secure"], "gossipsub-secure")]
UNICAST = [("nnet", "nnet-relay", [], "nnet-relay"), ("libp2p", "libp2p-direct", [], "libp2p-direct"),
           ("libp2p", "libp2p-direct", ["-connhigh", "MATCH"], "libp2p-direct-capped"),
           ("libp2p", "libp2p-direct", ["-secure"], "libp2p-direct-secure")]
IDLE = [("nnet", "nnet-idle", [], "nnet-idle"), ("libp2p", "libp2p-idle", [], "libp2p-idle")]
SIZES = [16, 32, 64, 128, 256]

def run(binary, impl, extra, n, common, out, label):
    cmd = [os.path.join(HERE, f"bench-{binary}"), "-impl", impl, "-n", str(n), "-label", label] + common + extra
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    line = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    try:
        d = json.loads(line)
    except Exception:
        print("FAILED", cmd, p.stderr[-500:], file=sys.stderr, flush=True); return None
    d["wall_s"] = round(time.time() - t, 1)
    with open(out, "a") as f:
        f.write(json.dumps(d) + "\n")
    keys = ["label", "n", "delivery_ratio", "lat_p50_ms", "lat_p99_ms", "wire_bytes_per_delivered_payload_byte",
            "cpu_us_per_delivery", "cpu_ms_per_node_s", "wire_bytes_per_node_s", "conns_per_node", "heap_mb_per_node"]
    keys += ["min_node_coverage", "conn_high"]
    print(" ".join(f"{k}={round(d[k], 3) if isinstance(d[k], float) else d[k]}" for k in keys if k in d), flush=True)
    return d

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--sizes", default=",".join(map(str, SIZES)))
    ap.add_argument("--out", default=os.path.join(HERE, "results.jsonl"))
    ap.add_argument("--dur", default="20s")
    ap.add_argument("--settle", default="45s")
    a = ap.parse_args()
    sizes = [int(x) for x in a.sizes.split(",")]
    plans = [("bcast", BCAST, ["-load", "10000"]), ("unicast", UNICAST, ["-load", "5000"]), ("idle", IDLE, [])]
    for mode, cfgs, common in plans:
        for n in sizes:
            nnet_conns = None
            for binary, impl, extra, label in cfgs:
                if a.only and a.only not in label and a.only != mode:
                    continue
                if "MATCH" in extra:  # give libp2p the same connection budget nnet used at this N
                    if nnet_conns is None:
                        continue
                    extra = [x if x != "MATCH" else str(max(4, round(nnet_conns))) for x in extra]
                d = run(binary, impl, extra, n, common + ["-dur", a.dur, "-settle", a.settle], a.out, label)
                if d and impl == "nnet-relay":
                    nnet_conns = d["conns_per_node"]
