#!/usr/bin/env python3
"""Turn results.jsonl into charts (../images) and a markdown summary (summary.md)."""
import json, os, math
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "..", "images")
SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e6e5e0"; LINE = "#d6d5cf"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "font.size": 13, "axes.edgecolor": LINE,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})
# fixed categorical order (dataviz reference palette); nnet solid, libp2p dashed
STYLE = {
    "nnet-tree-k1": ("#2a78d6", "-", "nnet tree K=1"),
    "nnet-tree-k3": ("#4a3aa7", "-", "nnet tree K=3"),
    "nnet-push": ("#1baf7a", "-", "nnet push (flood)"),
    "gossipsub": ("#eb6834", (0, (5, 2.5)), "GossipSub"),
    "gossipsub-secure": ("#e34948", (0, (5, 2.5)), "GossipSub + Noise + signing"),
    "nnet-relay": ("#2a78d6", "-", "nnet relay (multi-hop)"),
    "libp2p-direct": ("#eb6834", (0, (5, 2.5)), "libp2p direct, unlimited conns"),
    "libp2p-direct-capped": ("#eda100", (0, (5, 2.5)), "libp2p direct, conns capped = nnet’s"),
    "libp2p-direct-secure": ("#e34948", (0, (5, 2.5)), "libp2p direct + Noise"),
    "libp2p-direct-warm": ("#4a3aa7", (0, (5, 2.5)), "libp2p direct, steady state (after 90 s warm-up)"),
    "nnet-relay-warm": ("#1baf7a", "-", "nnet relay, steady state (90 s warm-up)"),
    "nnet-idle": ("#2a78d6", "-", "nnet (Chord stabilization + RTT pings)"),
    "libp2p-idle": ("#eb6834", (0, (5, 2.5)), "libp2p (GossipSub + Kademlia)"),
}

def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    by = defaultdict(dict)
    for r in rows:
        by[r["label"]][r["n"]] = r  # last run wins
    return by

def slope(ns, ys):
    ns, ys = np.array(ns, float), np.array(ys, float)
    ok = (ys > 0)
    if ok.sum() < 2:
        return float("nan")
    return float(np.polyfit(np.log(ns[ok]), np.log(ys[ok]), 1)[0])

def panel(ax, by, labels, key, title, logy=False, ylim=None, yticks=None):
    for lab in labels:
        if lab not in by:
            continue
        ns = sorted(by[lab]); ys = [by[lab][n][key] for n in ns]
        c, ls, name = STYLE[lab]
        ax.plot(ns, ys, color=c, ls=ls, lw=2.3, marker="o", ms=6.5, mec=SURF, mew=1.6, label=name, zorder=3)
    ax.set_xscale("log", base=2)
    if logy:
        ax.set_yscale("log")
    ax.set_xticks([16, 32, 64, 128, 256], ["16", "32", "64", "128", "256"])
    ax.minorticks_off() if not logy else None
    ax.set_title(title, loc="left", fontsize=14.5, color=INK, fontweight="bold", pad=10)
    ax.yaxis.grid(True, color=GRID, lw=1); ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    if ylim:
        ax.set_ylim(*ylim)
    if yticks:
        ax.set_yticks(yticks, [f"{t:,g}" for t in yticks]); ax.minorticks_off()

def figure(by, labels, panels, fname, title, subtitle, ncols=2):
    rows = math.ceil(len(panels) / ncols)
    fig, axes = plt.subplots(rows, ncols, figsize=(16, 4.3 * rows + 2.0), dpi=100)
    axes = np.array(axes).reshape(-1)
    fig.subplots_adjust(left=0.06, right=0.98, top=1 - 1.75 / (4.3 * rows + 2.0), bottom=0.16 if rows == 1 else (0.13 if len(labels) > 4 else 0.1), hspace=0.42, wspace=0.16)
    fig.text(0.04, 1 - 0.35 / (4.3 * rows + 2.0), title, fontsize=24, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 1 - 0.95 / (4.3 * rows + 2.0), subtitle, fontsize=14, color=INK2, va="top")
    for ax, p in zip(axes, panels):
        panel(ax, by, labels, **p)
    for ax in axes[len(panels):]:
        ax.axis("off")
    for ax in axes[len(panels) - ncols:len(panels)]:
        ax.set_xlabel("Network size N (nodes, log scale)", fontsize=12.5)
    h, l = axes[0].get_legend_handles_labels()
    nc = len(l) if len(l) <= 4 else 3
    fig.legend(h, l, loc="lower center", ncol=nc, frameon=False, fontsize=13, bbox_to_anchor=(0.5, 0.0), handlelength=3.2)
    fig.savefig(os.path.join(IMG, fname), dpi=100); plt.close(fig); print("wrote", fname)

def elasticity_chart(by, B, U):
    rows = [l for l in B + U if l in by and len(by[l]) >= 4]
    fig = plt.figure(figsize=(16, 8.6), dpi=100)
    fig.text(0.04, 0.955, "Scaling elasticity: how cost per delivery grows with network size", fontsize=24, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.9, "Slope of log(cost) vs log(N) over N = 16…256 · 0 = flat (perfect scaling) · 1 = cost grows in proportion to N",
             fontsize=14, color=INK2, va="top")
    metrics_ = [("wire_bytes_per_delivered_payload_byte", "Wire bytes per delivery"), ("cpu_us_per_delivery", "CPU per delivery"),
                ("conns_per_node", "Connections per node")]
    for j, (k, t) in enumerate(metrics_):
        ax = fig.add_axes([0.25 + j * 0.25, 0.1, 0.21, 0.7])
        ys = np.arange(len(rows))[::-1]
        for y, lab in zip(ys, rows):
            ns = sorted(by[lab]); v = slope(ns, [by[lab][n][k] for n in ns])
            c = STYLE[lab][0]
            ax.plot([0, v], [y, y], color=c, lw=2.2, solid_capstyle="round", zorder=2)
            ax.plot([v], [y], "o", color=c, ms=10, mec=SURF, mew=2, zorder=3)
            ax.text(v + (0.06 if v >= 0 else -0.06), y, f"{v:+.2f}", va="center", ha="left" if v >= 0 else "right", fontsize=12.5, color=INK)
        ax.axvline(0, color=INK2, lw=1.2); ax.axvline(1, color=LINE, lw=1.2, ls=(0, (3, 3)))
        ax.set_xlim(-0.4, 1.75); ax.set_ylim(-0.7, len(rows) - 0.3)
        ax.set_yticks(ys, [STYLE[l][2] + ("*" if l == "nnet-push" else "") for l in rows] if j == 0 else [""] * len(rows), fontsize=12.5)
        ax.tick_params(length=0); ax.spines["left"].set_visible(False)
        ax.set_title(t, fontsize=14.5, fontweight="bold", color=INK, loc="left", pad=8)
        ax.xaxis.grid(True, color=GRID)
        ax.axhline(len([r for r in rows if r in B]) and (len(rows) - len([r for r in rows if r in B]) - 0.5), color=LINE, lw=1)
    fig.text(0.04, 0.025, "* flooding saturated the 14-core machine from N = 32 (delivery fell to 64–80%), so its measured cost is a floor, not a trend. "
             "Unicast elasticities include cold-start connection setup; see the steady-state runs.", fontsize=12, color=INK2)
    fig.text(0.015, 0.62, "Broadcast", rotation=90, fontsize=13, color=INK2, va="center")
    fig.text(0.015, 0.25, "Unicast", rotation=90, fontsize=13, color=INK2, va="center")
    fig.savefig(os.path.join(IMG, "19-bench-scaling-elasticity.png"), dpi=100); plt.close(fig); print("wrote 19")

def main():
    by = load(os.path.join(HERE, "results.jsonl"))
    B = ["nnet-tree-k1", "nnet-tree-k3", "nnet-push", "gossipsub", "gossipsub-secure"]
    U = ["nnet-relay", "libp2p-direct", "libp2p-direct-capped", "libp2p-direct-secure", "libp2p-direct-warm"]
    I = ["nnet-idle", "libp2p-idle"]
    figure(by, B, [
        dict(key="wire_bytes_per_delivered_payload_byte", title="Wire bytes per delivered payload byte", logy=True, yticks=[1, 2, 5, 10, 20]),
        dict(key="cpu_us_per_delivery", title="CPU µs per delivery (whole network)", logy=True, yticks=[100, 200, 500, 1000, 2000]),
        dict(key="delivery_ratio", title="Delivery ratio (push saturates the machine from N = 32)"),
        dict(key="lat_p99_ms", title="p99 delivery latency (ms)", logy=True, yticks=[1, 10, 100, 1000]),
    ], "16-bench-broadcast-scaling.png", "Measured: broadcast cost as the network grows",
        "Same harness · 1 KB messages · constant 10,000 deliveries/s network-wide · TCP on one Apple M4 Pro · lower is better except delivery ratio")
    figure(by, U, [
        dict(key="wire_bytes_per_delivered_payload_byte", title="Wire bytes per delivered payload byte"),
        dict(key="cpu_us_per_delivery", title="CPU µs per delivery (whole network)", logy=True, yticks=[50, 100, 200, 500, 1000, 2000]),
        dict(key="conns_per_node", title="Open connections per node"),
        dict(key="lat_p99_ms", title="p99 delivery latency (ms)", logy=True, yticks=[0.1, 1, 10, 100, 1000]),
    ], "17-bench-unicast-scaling.png", "Measured: point-to-point messaging cost as the network grows",
        "Random source → random destination · 1 KB · constant 5,000 msgs/s · nnet routes over Chord; libp2p finds the peer (Kademlia) and uses a direct stream")
    figure(by, I, [
        dict(key="wire_bytes_per_node_s", title="Maintenance bytes per node per second"),
        dict(key="cpu_ms_per_node_s", title="Maintenance CPU ms per node per second"),
        dict(key="conns_per_node", title="Open connections per node"),
        dict(key="heap_mb_per_node", title="Heap MB per node"),
    ], "18-bench-idle-overhead.png", "Measured: the cost of just staying in the network",
        "No application traffic · nnet pings every neighbor and runs Chord stabilization; libp2p wrote no stream bytes when idle (only uncounted yamux keep-alives)")

    elasticity_chart(by, B, U)

    # ---- summary table
    out = ["| Config | N | Delivery | Wire B / payload B | CPU µs / delivery | p50 / p99 ms | Conns / node |",
           "|---|---|---|---|---|---|---|"]
    for lab in B + U:
        for n in sorted(by.get(lab, {})):
            r = by[lab][n]
            out.append(f"| {STYLE[lab][2]} | {n} | {r['delivery_ratio']*100:.2f}% | {r['wire_bytes_per_delivered_payload_byte']:.2f} | "
                       f"{r['cpu_us_per_delivery']:.0f} | {r['lat_p50_ms']:.2f} / {r['lat_p99_ms']:.1f} | {r['conns_per_node']:.1f} |")
    out += ["", "| Config | N | Bytes / node / s | CPU ms / node / s | Conns / node | Heap MB / node |", "|---|---|---|---|---|---|"]
    for lab in I:
        for n in sorted(by.get(lab, {})):
            r = by[lab][n]
            out.append(f"| {STYLE[lab][2]} | {n} | {r['wire_bytes_per_node_s']:,.0f} | {r['cpu_ms_per_node_s']:.1f} | {r['conns_per_node']:.1f} | {r['heap_mb_per_node']:.1f} |")
    out += ["", "Scaling elasticity = slope of log(cost) vs log(N); 0 = cost per delivery independent of network size.", "",
            "| Config | wire-bytes elasticity | CPU elasticity | conns elasticity |", "|---|---|---|---|"]
    for lab in B + U + I:
        if lab not in by:
            continue
        ns = sorted(by[lab])
        k1 = "wire_bytes_per_node_s" if lab in I else "wire_bytes_per_delivered_payload_byte"
        k2 = "cpu_ms_per_node_s" if lab in I else "cpu_us_per_delivery"
        out.append(f"| {STYLE[lab][2]} | {slope(ns, [by[lab][n][k1] for n in ns]):+.2f} | {slope(ns, [by[lab][n][k2] for n in ns]):+.2f} | "
                   f"{slope(ns, [by[lab][n]['conns_per_node'] for n in ns]):+.2f} |")
    open(os.path.join(HERE, "summary.md"), "w").write("\n".join(out) + "\n")
    print("\n".join(out))

if __name__ == "__main__":
    main()
