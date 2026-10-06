import json, math, random, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge, Arc, PathPatch
from matplotlib.path import Path
import sim

OUT = sys.argv[1]
# ---- reference palette (dataviz skill, light mode) ----
SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8984"; GRID = "#e6e5e0"; LINE = "#d6d5cf"
BLUE = "#2a78d6"; ORANGE = "#eb6834"; AQUA = "#1baf7a"; YELLOW = "#eda100"; MAGENTA = "#e87ba4"
GREEN = "#008300"; VIOLET = "#4a3aa7"; RED = "#e34948"
BLUE_T = "#e6f0fc"; ORANGE_T = "#fdebe3"; AQUA_T = "#e2f5ee"; VIOLET_T = "#ebe9f7"; YELLOW_T = "#fdf3dc"; GRAY_T = "#f0efec"
SEQ = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]  # ordinal blue ramp (>= step 250)

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 15, "axes.edgecolor": LINE, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.titlecolor": INK, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
})

def canvas(w=16, h=9):
    fig = plt.figure(figsize=(w, h), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w * 10); ax.set_ylim(0, h * 10); ax.axis("off")
    return fig, ax

def save(fig, name):
    p = os.path.join(OUT, name); fig.savefig(p, dpi=100); plt.close(fig); print("wrote", p)

def title(ax, t, sub=None, x=6, y=None):
    H = ax.get_ylim()[1]; y = H - 6 if y is None else y
    ax.text(x, y, t, fontsize=27, fontweight="bold", color=INK, va="top")
    if sub: ax.text(x, y - 5.2, sub, fontsize=16, color=INK2, va="top")

def box(ax, x, y, w, h, text="", fc=GRAY_T, ec=LINE, tc=INK, fs=15, bold=False, r=1.2, lw=1.5, ha="center", ls="-", z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
    if text:
        tx = x + w / 2 if ha == "center" else x + 1.6
        ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", zorder=z + 1, linespacing=1.35)

def arrow(ax, p1, p2, color=INK2, lw=1.8, style="-|>", ls="-", rad=0.0, ms=16, z=3, shrink=2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=z, shrinkA=shrink, shrinkB=shrink))

def label(ax, x, y, t, fs=14, c=INK2, ha="center", va="center", bold=False, z=5, **kw):
    ax.text(x, y, t, fontsize=fs, color=c, ha=ha, va=va, fontweight="bold" if bold else "normal", zorder=z, **kw)

# ------------------------------------------------------------------ ring helpers
def ring_xy(cx, cy, R, frac):
    th = math.pi / 2 - 2 * math.pi * frac
    return cx + R * math.cos(th), cy + R * math.sin(th)

def chord_curve(ax, p, q, cx, cy, color, lw=2, ls="-", alpha=1, bend=0.35, arrow_head=True, z=3):
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    c = (mx + (cx - mx) * bend, my + (cy - my) * bend)
    path = Path([p, c, q], [Path.MOVETO, Path.CURVE3, Path.CURVE3])
    ax.add_patch(PathPatch(path, fc="none", ec=color, lw=lw, ls=ls, alpha=alpha, zorder=z))
    if arrow_head:
        t = 0.93
        bx = (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * c[0] + t ** 2 * q[0]
        by = (1 - t) ** 2 * p[1] + 2 * (1 - t) * t * c[1] + t ** 2 * q[1]
        ax.add_patch(FancyArrowPatch((bx, by), q, arrowstyle="-|>", mutation_scale=15, color=color, lw=0, alpha=alpha, zorder=z, shrinkA=0, shrinkB=7))

def small_ring(N, K, seed, M=8):
    sim.M = M; sim.RING = 1 << M
    ids, fg = sim.build(N, K, seed)
    return ids, fg

# =================================================================== 01 philosophy
def fig_philosophy():
    fig, ax = canvas(16, 8.2)
    title(ax, "Two philosophies of peer-to-peer networking",
          "nnet routes the message through the overlay  ·  libp2p finds the peer, then opens a direct, secure stream")
    # left panel: nnet
    box(ax, 4, 4, 74, 62, fc=BLUE_T, ec=BLUE_T, r=2)
    label(ax, 41, 61.5, "nnet  —  “the postal system”", fs=19, c=INK, bold=True)
    cx, cy, R = 41, 31, 21
    ax.add_patch(Circle((cx, cy), R, fc="none", ec="#c4c3bd", lw=2.5, zorder=3))
    rnd = random.Random(7); fr = sorted(rnd.random() for _ in range(18))
    for f in fr:
        x, y = ring_xy(cx, cy, R, f); ax.add_patch(Circle((x, y), 1.0, fc=SURF, ec=INK2, lw=1.4, zorder=4))
    src, hops = fr[1], [fr[9], fr[13], fr[15]]
    path = [src] + hops
    for a, b in zip(path, path[1:]):
        chord_curve(ax, ring_xy(cx, cy, R, a), ring_xy(cx, cy, R, b), cx, cy, BLUE, lw=3, bend=0.25)
    for i, f in enumerate(path):
        x, y = ring_xy(cx, cy, R, f)
        ax.add_patch(Circle((x, y), 1.5, fc=BLUE if i in (0, len(path) - 1) else SURF, ec=BLUE, lw=2.5, zorder=5))
    sx, sy = ring_xy(cx, cy, R + 4.5, src); label(ax, sx + 2, sy + 1, "sender", c=INK, bold=True, ha="left")
    dx, dy = ring_xy(cx, cy, R + 4.5, fr[15]); label(ax, dx - 1, dy, "owner of key k", c=INK, bold=True, ha="right")
    label(ax, cx - 5, cy + 2.5, "SendBytesRelay(data, k)", fs=14, c=INK, family="monospace")
    label(ax, cx - 5, cy - 2, "≈ ½·log₂N hops, no setup", fs=14)
    label(ax, cx, 7, "Every node relays others' messages over a Chord ring", fs=14)
    # right panel: libp2p
    box(ax, 82, 4, 74, 62, fc=ORANGE_T, ec=ORANGE_T, r=2)
    label(ax, 119, 61.5, "libp2p  —  “the phone system”", fs=19, c=INK, bold=True)
    A = (92, 34); B = (146, 34)
    dht = [(104, 50), (118, 53), (133, 50)]
    for p in dht:
        ax.add_patch(Circle(p, 1.4, fc=SURF, ec=INK2, lw=1.4, zorder=4))
    label(ax, 118, 57.3, "Kademlia DHT (directory)", fs=13)
    arrow(ax, A, dht[0], color=ORANGE, ls=(0, (4, 3)), lw=2); arrow(ax, dht[0], A, color=ORANGE, ls=(0, (4, 3)), lw=2, rad=0.25)
    arrow(ax, A, dht[1], color=ORANGE, ls=(0, (4, 3)), lw=2, rad=-0.1); arrow(ax, A, dht[2], color=ORANGE, ls=(0, (4, 3)), lw=2, rad=-0.15)
    label(ax, 93, 46.5, "① FindPeer(id)", fs=13.5, c=INK, ha="left", bbox=dict(fc=ORANGE_T, ec="none", pad=1.5))
    for p, t in ((A, "A"), (B, "B")):
        ax.add_patch(Circle(p, 3.2, fc=ORANGE, ec=ORANGE, zorder=5)); label(ax, p[0], p[1], t, c="white", bold=True, fs=16, z=6)
    ax.add_patch(FancyBboxPatch((96, 31.2), 46, 5.6, boxstyle="round,pad=0,rounding_size=2.8", fc=SURF, ec=ORANGE, lw=2.5, zorder=3))
    for i in range(4):
        ax.plot([99 + 0, 139], [32.5 + i * 1.0, 32.5 + i * 1.0], color=ORANGE, lw=0.8, alpha=0.45, zorder=4)
    label(ax, 119, 27.3, "② dial → Noise/TLS → yamux  (or QUIC: 1 RTT)", fs=13.5, c=INK)
    label(ax, 119, 22.8, "authenticated, encrypted, multiplexed streams", fs=13.5)
    label(ax, 119, 7, "Data flows directly between peers (relay/hole-punch if NATed)", fs=14)
    save(fig, "01-philosophy.png")

# =================================================================== 02 nnet stack
def fig_nnet_stack():
    fig, ax = canvas(16, 10)
    title(ax, "nnet architecture", "Small, swappable layers; middleware hooks at every boundary")
    L = [
        ("NNet facade", "nnet.go · message.go", "SendBytes{Direct | Relay | Broadcast}{Async | Sync | Reply}", BLUE_T),
        ("Overlay · Chord", "overlay/chord/", "successors · predecessors · 256 finger buckets · neighbors · stabilization loops", BLUE_T),
        ("Routers", "overlay/routing/", "DIRECT  ·  RELAY (greedy + RTT)  ·  BROADCAST_PUSH  ·  BROADCAST_TREE", BLUE_T),
        ("Node", "node/", "LocalNode: listener · rx chans · reply chans · rx dedup\nRemoteNode: rx/tx loops · RTT probe · keepalive · tx dedup", GRAY_T),
        ("Multiplexer", "multiplexer/", "smux (default) | yamux  —  8 streams opened / 32 accepted per peer", GRAY_T),
        ("Transport", "transport/", "tcp://host:port  |  kcp://host:port  (reliable UDP)", GRAY_T),
    ]
    y0, h, gap = 72, 9.4, 1.6
    for i, (n, path, desc, fc) in enumerate(L):
        y = y0 - i * (h + gap)
        box(ax, 6, y, 112, h, fc=fc, ec=fc)
        label(ax, 9, y + h / 2 + 1.7, n, fs=18, c=INK, bold=True, ha="left")
        label(ax, 9, y + h / 2 - 2.2, path, fs=12.5, c=MUTED, ha="left", family="monospace")
        label(ax, 36, y + h / 2, desc, fs=14.5, c=INK, ha="left")
    # middleware column
    top = y0 + h; bot = y0 - 5 * (h + gap)
    box(ax, 122, bot, 32, top - bot, fc=VIOLET_T, ec=VIOLET_T)
    label(ax, 138, top - 4, "Middleware", fs=18, c=INK, bold=True)
    mws = ["BytesReceived", "RemoteMessageRouted", "RelayPriority", "SuccessorAdded", "FingerTableAdded",
           "NetworkWillStart", "RemoteNodeReady", "WillConnectToNode", "MessageEncoded", "MessageWillDecode"]
    for i, m in enumerate(mws):
        label(ax, 138, top - 10.5 - i * 5.6, m, fs=13.5, c=VIOLET, family="monospace")
    for i in range(6):
        y = y0 - i * (h + gap) + h / 2
        ax.plot([118, 122], [y, y], color=VIOLET, lw=1.6, ls=(0, (2, 2)))
    label(ax, 80, 3.5, "≈5,300 lines of Go (excluding generated protobuf & examples)  ·  one protobuf envelope, 4-byte length-prefixed frames, 20 MiB max",
          fs=13.5, c=INK2)
    save(fig, "02-nnet-architecture.png")

# =================================================================== 03 remotenode engine
def fig_engine():
    fig, ax = canvas(16, 8.6)
    title(ax, "Inside a RemoteNode: nnet's per-peer I/O engine", "Fixed goroutines per peer · bounded channels that drop when full · 8 parallel streams")
    # left: local routers
    box(ax, 4, 18, 26, 48, fc=BLUE_T, ec=BLUE_T)
    label(ax, 17, 61.5, "LocalNode", fs=17, c=INK, bold=True)
    for i, r in enumerate(["DIRECT", "RELAY", "BCAST_PUSH", "BCAST_TREE"]):
        box(ax, 7, 50 - i * 8.4, 20, 6.2, r, fc=SURF, ec=BLUE, fs=12.5, tc=BLUE)
    label(ax, 17, 21.5, "rx chan per routing type\n(23,333 buffered)", fs=12)
    # tx side
    box(ax, 40, 48, 22, 9, "txMsgChan\n(2,333)", fc=SURF, ec=INK2, fs=13.5)
    box(ax, 40, 25, 22, 9, "handleMsg\ndedup · keepalive", fc=SURF, ec=INK2, fs=13.5)
    box(ax, 40, 6, 22, 9, "RTT probe\nping ≈ 5 s, EWMA", fc=SURF, ec=INK2, fs=13.5)
    box(ax, 40, 36.5, 22, 7, "rxMsgChan (2,333)", fc=SURF, ec=INK2, fs=13.5)
    arrow(ax, (30, 52.5), (40, 52.5), color=INK2); label(ax, 35, 55.5, "send", fs=12)
    arrow(ax, (51, 36.5), (51, 34), color=INK2)
    arrow(ax, (40, 29.5), (30, 29.5), color=INK2); label(ax, 35, 32.3, "dispatch", fs=12)
    # streams
    box(ax, 72, 6, 52, 60, fc=GRAY_T, ec=GRAY_T)
    label(ax, 98, 62, "smux session  ·  8 streams", fs=16, c=INK, bold=True)
    for i in range(8):
        y = 54.5 - i * 6.3
        box(ax, 75, y, 46, 4.8, fc=SURF, ec=LINE)
        label(ax, 80, y + 2.4, "tx", fs=12.5, c=BLUE, bold=True); label(ax, 116, y + 2.4, "rx", fs=12.5, c=AQUA, bold=True)
        label(ax, 98, y + 2.4, f"stream {i}   [len:4B][protobuf]", fs=12, c=INK2, family="monospace")
        arrow(ax, (62, 52.5), (77, y + 2.4), color=BLUE, lw=1, ms=10, shrink=1)
        arrow(ax, (119, y + 2.4), (62, 40), color=AQUA, lw=0.8, ms=9, shrink=1, rad=0.0)
    # connection
    box(ax, 130, 26, 26, 20, "1 TCP / KCP\nconnection\nto peer", fc=SURF, ec=INK, fs=15)
    arrow(ax, (124, 36), (130, 36), color=INK, style="<|-|>")
    # drop callout
    box(ax, 128, 6, 28, 14, "Channel full?\n→ message dropped\n(log warning)", fc="#fdecec", ec=RED, fs=13, tc=INK)
    save(fig, "03-remotenode-engine.png")

# =================================================================== 04 chord neighbor lists
def fig_chord_lists():
    fig, ax = canvas(16, 10)
    title(ax, "nnet’s “improved Chord”: every pointer becomes a list", "Example ring (8-bit IDs, 40 nodes) from node A’s point of view · K = 3 nodes per finger bucket")
    ids, fg = small_ring(40, 3, 11, M=8)
    a = ids[0]; RING = 256
    cx, cy, R = 50, 42, 32
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=LINE, lw=3, zorder=1))
    # finger bucket arcs
    colors = [SEQ[0], SEQ[1], SEQ[2], SEQ[3], SEQ[4], SEQ[5], VIOLET, MAGENTA]
    fingers_drawn = []
    for i in range(8):
        s = (a + (1 << i)) % RING; e = (a + (1 << (i + 1))) % RING
        f1, f2 = s / RING, e / RING
        th1 = 90 - 360 * f2; th2 = 90 - 360 * f1
        if i >= 3:
            ax.add_patch(Arc((cx, cy), 2 * (R + 3 + (i - 3) * 1.9), 2 * (R + 3 + (i - 3) * 1.9), theta1=th1, theta2=th2, color=SEQ[min(i - 3, 5)] if i < 8 else VIOLET, lw=5, zorder=2))
            fingers_drawn.append(i)
    # successors / predecessors (cap 8 in default config)
    succ = [ids[(1 + j) % len(ids)] for j in range(8)]
    pred = [ids[(-1 - j) % len(ids)] for j in range(8)]
    for v in ids:
        x, y = ring_xy(cx, cy, R, v / RING)
        fc, ec = SURF, INK2
        if v in succ: fc, ec = AQUA, AQUA
        if v in pred: fc, ec = YELLOW, YELLOW
        ax.add_patch(Circle((x, y), 1.1, fc=fc, ec=ec, lw=1.4, zorder=5))
    # finger table members
    for i in fingers_drawn:
        for r in fg[a][i]:
            if r in succ: continue
            p = ring_xy(cx, cy, R, r / RING)
            ax.add_patch(Circle(p, 1.5, fc=SEQ[min(i - 3, 5)], ec=SURF, lw=1.5, zorder=6))
            chord_curve(ax, ring_xy(cx, cy, R, a / RING), p, cx, cy, SEQ[min(i - 3, 5)], lw=1.6, alpha=0.8, bend=0.15)
    ax_, ay_ = ring_xy(cx, cy, R, a / RING)
    ax.add_patch(Circle((ax_, ay_), 2.2, fc=BLUE, ec=SURF, lw=2, zorder=7)); label(ax, ax_, ay_, "A", c="white", bold=True, z=8)
    label(ax, cx, cy + 3, "256-bit ID space", fs=15, c=INK2)
    label(ax, cx, cy - 1.5, "(drawn here as 0…255)", fs=13, c=MUTED)
    for i in fingers_drawn:
        rr = R + 3 + (i - 3) * 1.9
        mid = ((a + (1 << i) + (1 << i) / 2) % RING) / RING
        x, y = ring_xy(cx, cy, rr + 3.3, mid)
        label(ax, x, y, f"finger {i}", fs=12.5, c=SEQ[min(i - 3, 5)], bold=True)
    # legend / explanation panel
    x0 = 100
    rows = [
        (AQUA, "Successors", "closest nodes clockwise; cap = max(8, 2 × non-empty fingers) ≈ 2·log₂N"),
        (YELLOW, "Predecessors", "mirror image counter-clockwise, same cap"),
        (SEQ[2], "Finger bucket i", "range [A+2ⁱ, A+2ⁱ⁺¹); keeps the K closest (default K = 3)"),
        (MUTED, "Neighbors", "every connected peer (unbounded) — for push broadcast"),
    ]
    for j, (c, h, d) in enumerate(rows):
        y = 74 - j * 12
        ax.add_patch(Circle((x0 + 2, y), 1.4, fc=c, ec=c))
        label(ax, x0 + 5, y + 0.3, h, fs=16, c=INK, bold=True, ha="left")
        ax.text(x0 + 5, y - 2.4, d, fontsize=13, color=INK2, ha="left", va="top", wrap=True)
    box(ax, x0, 10, 54, 22, fc=BLUE_T, ec=BLUE_T)
    ax.text(x0 + 2.5, 29.5, "Why lists?", fontsize=16, fontweight="bold", color=INK, va="top")
    ax.text(x0 + 2.5, 25, "• Fail-over: 3 candidates per finger\n• Proximity: pick the lowest-RTT candidate\n• Churn-safe: successor list grows with log N\n• Evicted from all lists → connection closed",
            fontsize=13.5, color=INK, va="top", linespacing=1.6)
    save(fig, "04-chord-neighbor-lists.png")

# =================================================================== 05 relay routing
def fig_relay():
    fig, ax = canvas(16, 9.4)
    title(ax, "Relay routing: greedy fingers + proximity route selection", "Each hop jumps to the farthest finger bucket that doesn’t overshoot the key, then picks the lowest-RTT node in it")
    ids, fg = small_ring(48, 3, 5, M=8)
    RING = 256; cx, cy, R = 46, 40, 31
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=LINE, lw=3, zorder=1))
    for v in ids:
        ax.add_patch(Circle(ring_xy(cx, cy, R, v / RING), 0.9, fc=SURF, ec=MUTED, lw=1.2, zorder=4))
    rnd = random.Random(3)
    src = ids[2]; dest_key = (src + 205) % RING
    cur = src; path = [src]; alts = []
    while True:
        import bisect
        j = bisect.bisect_right(ids, cur) % len(ids); succ = ids[j]
        if sim.dist(cur, dest_key) < sim.dist(cur, succ): break
        nxt = None
        for i in range(7, -1, -1):
            c = [r for r in fg[cur][i] if sim.dist(cur, r) <= sim.dist(cur, dest_key)]
            if c:
                rtts = {r: rnd.choice([18, 25, 41, 63, 87, 120]) for r in c}
                nxt = min(c, key=lambda r: rtts[r]); alts.append((cur, c, rtts, nxt)); break
        if nxt is None: nxt = succ
        cur = nxt; path.append(cur)
    for (frm, cands, rtts, chosen) in alts:
        for r in cands:
            if r == chosen: continue
            chord_curve(ax, ring_xy(cx, cy, R, frm / RING), ring_xy(cx, cy, R, r / RING), cx, cy, MUTED, lw=1.3, ls=(0, (3, 3)), alpha=0.9, bend=0.3)
    for k, (p, q) in enumerate(zip(path, path[1:])):
        chord_curve(ax, ring_xy(cx, cy, R, p / RING), ring_xy(cx, cy, R, q / RING), cx, cy, BLUE, lw=3.2, bend=0.3)
    for (frm, cands, rtts, chosen) in alts:
        for r in cands:
            x, y = ring_xy(cx, cy, R + 4.2, r / RING)
            label(ax, x, y, f"{rtts[r]} ms", fs=11.5, c=BLUE if r == chosen else MUTED, bold=r == chosen)
    for k, v in enumerate(path):
        ax.add_patch(Circle(ring_xy(cx, cy, R, v / RING), 1.7, fc=BLUE if k in (0, len(path) - 1) else SURF, ec=BLUE, lw=2.4, zorder=6))
    kx, ky = ring_xy(cx, cy, R, dest_key / RING)
    ax.add_patch(Circle((kx, ky), 1.0, fc=RED, ec=RED, zorder=7))
    x, y = ring_xy(cx, cy, R - 5, dest_key / RING); label(ax, x, y, "key k", c=RED, bold=True)
    x, y = ring_xy(cx, cy, R - 5, src / RING); label(ax, x, y, "src", c=BLUE, bold=True)
    x, y = ring_xy(cx, cy, R - 6.5, path[-1] / RING); label(ax, x, y, "owner", c=BLUE, bold=True)
    label(ax, cx, cy, f"{len(path) - 1} hops", fs=20, c=INK, bold=True)
    # pseudo-code panel
    x0 = 90
    box(ax, x0, 8, 66, 66, fc=GRAY_T, ec=GRAY_T)
    code = ("if key ∈ [me, successor):\n"
            "    deliver locally\n\n"
            "for i = 255 … 0:            # far → near\n"
            "  cands = finger[i] ∩ [me, key]\n"
            "  cands = outbound ∪ predecessors\n"
            "  if cands:\n"
            "    score = −RTT_ms           # PRS\n"
            "    score = RelayPriority(score)\n"
            "    return argmax(score)\n\n"
            "fallback: walk successor list")
    ax.text(x0 + 3, 70, code, fontsize=14.5, family="monospace", color=INK, va="top", linespacing=1.5)
    ax.plot([x0 + 3, x0 + 63], [24, 24], color=LINE, lw=1)
    ax.text(x0 + 3, 21.5, "• Hop bound: ≤ log₂N w.h.p.; ≈ ½·log₂N on average\n• Only self-dialed links (or predecessors) are next hops\n• Dashed grey = alternatives in the same bucket",
            fontsize=13.5, color=INK2, va="top", linespacing=1.6)
    save(fig, "05-relay-routing.png")

# =================================================================== 06 tree broadcast
def fig_tree():
    fig, ax = canvas(16, 9.4)
    title(ax, "Spanning-tree broadcast over the finger table", "Real nnet algorithm on a 32-node ring (K = 1) · edge colour = tree depth · red dashed = duplicate deliveries")
    ids, fg = small_ring(32, 1, 21, M=8)
    RING = 256; cx, cy, R = 44, 40, 31
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=LINE, lw=3, zorder=1))
    origin = ids[0]
    seen = {origin}; edges = []; q = [(origin, None, 8, 0)]
    while q:
        node, sender, maxidx, d = q.pop(0)
        for i in range(maxidx):
            for r in fg[node][i]:
                if r == sender or r == origin: continue
                dup = r in seen
                edges.append((node, r, d, dup))
                if not dup:
                    seen.add(r); q.append((r, node, sim.dist(node, r).bit_length() - 1, d + 1))
    depth_of = {origin: 0}
    for (p, r, d, dup) in edges:
        if not dup: depth_of[r] = d + 1
    for (p, r, d, dup) in edges:
        P = ring_xy(cx, cy, R, p / RING); Q = ring_xy(cx, cy, R, r / RING)
        if dup: chord_curve(ax, P, Q, cx, cy, RED, lw=2.2, ls=(0, (4, 3)), bend=0.42, z=4)
        else: chord_curve(ax, P, Q, cx, cy, SEQ[min(d + 1, 5)], lw=2.4, bend=0.42)
    for v in ids:
        d = depth_of.get(v, 0)
        ax.add_patch(Circle(ring_xy(cx, cy, R, v / RING), 1.3, fc=SURF if v != origin else BLUE, ec=BLUE, lw=2, zorder=6))
    ox, oy = ring_xy(cx, cy, R + 4.5, origin / RING); label(ax, ox, oy, "origin", c=BLUE, bold=True)
    sends = len(edges); dups = sum(1 for e in edges if e[3]); maxd = max(depth_of.values())
    # panel
    x0 = 86
    for j, (val, lab) in enumerate([(f"{sends}", "transmissions"), (f"{len(ids) - 1}", "nodes reached (N−1)"), (f"{dups}", "duplicates (arc overlap)"), (f"{maxd}", "tree depth (≤ log₂N = 5)")]):
        xx = x0 + (j % 2) * 34; yy = 66 - (j // 2) * 17
        box(ax, xx, yy - 6, 31, 15, fc=GRAY_T, ec=GRAY_T)
        label(ax, xx + 2.5, yy + 4, val, fs=30, c=RED if j == 2 else INK, bold=True, ha="left")
        label(ax, xx + 2.5, yy - 2.5, lab, fs=13, c=INK2, ha="left")
    # depth legend
    for k in range(1, maxd + 1):
        ax.plot([x0 + 1 + (k - 1) * 11, x0 + 7 + (k - 1) * 11], [36, 36], color=SEQ[min(k, 5)], lw=4, solid_capstyle="round")
        label(ax, x0 + 4 + (k - 1) * 11, 33, f"depth {k}", fs=12)
    ax.text(x0, 27, "Rule: a node reached from sender S at clockwise\n"
                    "distance d forwards only to fingers 0 … bitlen(d)−2,\n"
                    "i.e. the arc [self, self+2ʲ) that S delegated to it.\n"
                    "Arcs overlap by ≈ one node gap → a few duplicates.\n"
                    "Without an rx dedup cache, duplicates re-forward.",
            fontsize=13.5, color=INK, va="top", linespacing=1.55)
    save(fig, "07-tree-broadcast.png")

# =================================================================== 07 measured broadcast chart
def fig_measured():
    fig = plt.figure(figsize=(16, 8.4), dpi=100)
    fig.text(0.04, 0.95, "Measured: transmissions per node for one network-wide broadcast", fontsize=25, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.895, "nnet examples/efficient-broadcast · 60 local nodes over TCP · Apple M4 Pro · single run per configuration",
             fontsize=15, color=INK2, va="top")
    data = [  # (group, push, tree_default, tree_dedup)
        ("K = 1", 1767 / 60, 92 / 60, 75 / 60),
        ("K = 3", 2219 / 60, 3374 / 60, 269 / 60),
    ]
    ax = fig.add_axes([0.07, 0.13, 0.88, 0.66])
    series = [("Push (flooding)", ORANGE), ("Tree, default config", RED), ("Tree, + BROADCAST_TREE in rx dedup cache", BLUE)]
    w = 0.26; x = np.arange(len(data))
    for s, (name, col) in enumerate(series):
        vals = [d[1 + s] for d in data]
        bars = ax.bar(x + (s - 1) * (w + 0.015), vals, width=w, color=col, label=name, zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.0, f"{v:.1f}", ha="center", va="bottom", fontsize=15, color=INK, fontweight="bold")
    ax.set_xticks(x, [d[0] + "  (NumFingerSuccessors)" for d in data], fontsize=16, color=INK)
    ax.set_ylabel("Sends per node", fontsize=15)
    ax.set_ylim(0, 64); ax.yaxis.grid(True, color=GRID, lw=1, zorder=0); ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=14.5, ncol=3, bbox_to_anchor=(0, 1.08))
    ax.annotate("Default config: duplicates are not\nde-duplicated, so they re-propagate →\ncosts MORE than flooding", xy=(1.0, 56.2), xytext=(0.30, 46),
                fontsize=14, color=INK, arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.5), va="center")
    save(fig, "08-chart-broadcast-measured.png")

# =================================================================== 08 simulated scaling chart
def fig_sim_scaling():
    res = json.load(open("sim.json"))["tree"]
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.text(0.04, 0.955, "Simulated: tree-broadcast cost as the network grows", fontsize=25, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.9, "Faithful re-implementation of nnet’s finger table + BROADCAST_TREE rule · 64-bit ring · mean of 3–5 random rings per point",
             fontsize=15, color=INK2, va="top")
    ax = fig.add_axes([0.08, 0.11, 0.66, 0.72])
    cols = {1: BLUE, 2: AQUA, 3: VIOLET}
    for K in (1, 2, 3):
        pts = [r for r in res if r["K"] == K]
        Ns = [r["N"] for r in pts]
        ax.plot(Ns, [r["dedup"] for r in pts], color=cols[K], lw=2.4, marker="o", ms=8, mec=SURF, mew=2, zorder=4)
        ax.plot(Ns, [r["nodedup"] for r in pts], color=cols[K], lw=2.2, ls=(0, (5, 3)), marker="o", ms=8, mfc=SURF, mec=cols[K], mew=2, zorder=4)
        nud = {1: (0.88, 1.12), 2: (1, 1), 3: (1, 1)}[K]
        ax.text(10500, pts[-1]["dedup"] * nud[0], f"K={K} dedup  {pts[-1]['dedup']:.1f}", color=INK, fontsize=13.5, va="center")
        ax.text(10500, pts[-1]["nodedup"] * nud[1], f"K={K} default  {pts[-1]['nodedup']:,.0f}" if K > 1 else f"K={K} default  {pts[-1]['nodedup']:.1f}",
                color=INK, fontsize=13.5, va="center")
    ax.axhline(6, color=ORANGE, lw=2, ls=(0, (2, 2)), zorder=3)
    ax.text(1300, 7.0, "GossipSub eager push ≈ D = 6 per node", color=INK, fontsize=13.5, ha="center")
    # nudge overlapping end labels: re-place K=1 labels
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(8, 10000 * 1.15); ax.set_ylim(0.8, 20000)
    ax.set_xlabel("Network size N (nodes)", fontsize=15); ax.set_ylabel("Transmissions per node (log scale)", fontsize=15)
    ax.yaxis.grid(True, color=GRID, lw=1, which="major"); ax.tick_params(length=0, labelsize=13.5)
    ax.set_xticks([10, 30, 100, 300, 1000, 3000, 10000], ["10", "30", "100", "300", "1k", "3k", "10k"])
    ax.set_yticks([1, 10, 100, 1000, 10000], ["1", "10", "100", "1,000", "10,000"])
    ax.spines["left"].set_visible(False)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=INK2, lw=2.4, marker="o", ms=8, mec=SURF, mew=2), Line2D([], [], color=INK2, lw=2.2, ls=(0, (5, 3)), marker="o", ms=8, mfc=SURF, mec=INK2, mew=2)]
    h += [Line2D([], [], color=cols[k], lw=5) for k in (1, 2, 3)]
    ax.legend(h, ["rx dedup on for tree", "library default (no tree dedup)", "K = 1", "K = 2", "K = 3"], loc="upper left", frameon=False, fontsize=13.5, ncol=1, handlelength=3.6)
    save(fig, "09-chart-tree-scaling-sim.png")

# =================================================================== 09 throughput chart
def fig_throughput():
    fig = plt.figure(figsize=(16, 7.6), dpi=100)
    fig.text(0.04, 0.94, "Measured: nnet message throughput on one machine", fontsize=25, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.875, "examples/message-benchmark · TCP + smux · no encryption · Apple M4 Pro (14 cores) · steady-state seconds",
             fontsize=15, color=INK2, va="top")
    # stat tiles (left)
    tiles = [("66k", "msgs/s per node", "2 nodes · 1 KB messages"), ("3.1 GB/s", "per node", "2 nodes · 1 MB messages")]
    for i, (v, u, d) in enumerate(tiles):
        axt = fig.add_axes([0.04, 0.47 - i * 0.37, 0.3, 0.32]); axt.axis("off")
        axt.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.06", fc=GRAY_T, ec=GRAY_T, transform=axt.transAxes))
        axt.text(0.07, 0.86, d, fontsize=14, color=INK2, va="top", transform=axt.transAxes)
        axt.text(0.07, 0.38, v, fontsize=40, fontweight="bold", color=INK, va="center", transform=axt.transAxes)
        axt.text(0.07, 0.12, u, fontsize=14, color=INK2, va="center", transform=axt.transAxes)
    ax = fig.add_axes([0.43, 0.12, 0.53, 0.62])
    names = ["Push (flooding)", "Tree (K = 1)"]; vals = [5000, 13500]; cols = [ORANGE, BLUE]
    bars = ax.barh([1, 0], vals, color=cols, height=0.55, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(v + 250, b.get_y() + b.get_height() / 2, f"≈{v:,}", va="center", fontsize=17, fontweight="bold", color=INK)
    ax.set_yticks([1, 0], names, fontsize=16, color=INK)
    ax.set_xlim(0, 16500); ax.xaxis.grid(True, color=GRID, zorder=0); ax.tick_params(length=0, labelsize=13)
    ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    ax.set_title("16-node broadcast: unique 1 KB messages received per node per second", fontsize=15.5, color=INK, loc="left", pad=14)
    ax.text(0, -0.62, "Tree ≈ 2.7× push here (all 16 nodes share one CPU); README reports ≈10× on 2018 hardware.", fontsize=13.5, color=INK2)
    save(fig, "10-chart-throughput.png")

# =================================================================== 10 hops chart
def fig_hops():
    res = json.load(open("sim.json"))["hops"]
    fig = plt.figure(figsize=(16, 8.4), dpi=100)
    fig.text(0.04, 0.95, "Simulated: relay hops vs. network size", fontsize=25, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.893, "nnet greedy finger routing (K = 3) · 2,000 random (source, key) pairs per size · compared with the log₂N bound",
             fontsize=15, color=INK2, va="top")
    ax = fig.add_axes([0.08, 0.12, 0.76, 0.68])
    Ns = np.array([r["N"] for r in res]); avg = [r["avg"] for r in res]; mx = [r["max"] for r in res]
    xs = np.logspace(1, 4, 100)
    ax.plot(xs, np.log2(xs), color=INK2, lw=1.8, ls=(0, (2, 2)))
    ax.plot(xs, 0.5 * np.log2(xs), color=MUTED, lw=1.8, ls=(0, (6, 3)))
    ax.plot(Ns, mx, color=VIOLET, lw=2.4, marker="o", ms=8, mec=SURF, mew=2)
    ax.plot(Ns, avg, color=BLUE, lw=2.6, marker="o", ms=9, mec=SURF, mew=2)
    ax.text(10500, np.log2(10000), "log₂N bound", fontsize=14, color=INK2, va="center")
    ax.text(10500, mx[-1] - 0.35, f"observed max ({mx[-1]})", fontsize=14, color=INK, va="center")
    ax.text(10500, avg[-1] - 0.3, f"observed mean ({avg[-1]:.1f})", fontsize=14, color=INK, va="center")
    ax.text(1000, 0.5 * np.log2(1000) + 0.55, "½·log₂N", fontsize=14, color=INK2, va="center", ha="center")
    ax.set_xscale("log"); ax.set_xlim(9, 10000 * 1.1); ax.set_ylim(0, 15)
    ax.set_xticks([10, 30, 100, 300, 1000, 3000, 10000], ["10", "30", "100", "300", "1k", "3k", "10k"])
    ax.set_xlabel("Network size N (nodes)", fontsize=15); ax.set_ylabel("Overlay hops", fontsize=15)
    ax.yaxis.grid(True, color=GRID); ax.tick_params(length=0, labelsize=13.5); ax.spines["left"].set_visible(False)
    save(fig, "06-chart-relay-hops-sim.png")

# =================================================================== 11 libp2p stack
def fig_libp2p_stack():
    fig, ax = canvas(16, 10)
    title(ax, "libp2p architecture (go-libp2p)", "A modular connectivity stack: identity, transports, security and multiplexing; overlays are separate modules")
    L = [
        ("Application protocols", "/ipfs/kad/1.0.0  ·  /meshsub/1.3.0  ·  /ipfs/bitswap  ·  /my/app/1.0.0   (one stream each)", ORANGE_T),
        ("Host", "SetStreamHandler · NewStream · Peerstore · EventBus · ConnManager\nIdentify · Ping · AutoNAT v2 · AutoRelay · DCUtR (hole punching)", ORANGE_T),
        ("Swarm", "dialing & connection pool · connection gater\nResource Manager: system → transient → service → protocol → peer → conn → stream", ORANGE_T),
        ("Upgrader", "raw conn → [pnet PSK] → security: Noise | TLS 1.3\n→ muxer: yamux  (negotiated inline during the handshake)", GRAY_T),
        ("Transports", "TCP · QUIC-v1 · WebSocket · WebTransport · WebRTC(-direct) · Circuit Relay v2", GRAY_T),
    ]
    y0, h, gap = 70, 10.5, 1.8
    for i, (n, desc, fc) in enumerate(L):
        y = y0 - i * (h + gap)
        box(ax, 6, y, 112, h, fc=fc, ec=fc)
        label(ax, 9, y + h / 2, n, fs=18, c=INK, bold=True, ha="left")
        ax.text(40, y + h / 2, desc, fontsize=14, color=INK, ha="left", va="center", linespacing=1.5)
    top = y0 + h; bot = y0 - 4 * (h + gap)
    box(ax, 122, bot, 32, top - bot, fc=VIOLET_T, ec=VIOLET_T)
    label(ax, 138, top - 4, "Cross-cutting", fs=18, c=INK, bold=True)
    items = ["PeerID =\nhash(public key)", "Multiaddr\n/ip4/…/udp/4001/\nquic-v1/p2p/12D3…", "multistream-select\nprotocol negotiation", "Implementations:\nGo · Rust · JS · Nim\nJava · C++ · Py · Zig"]
    for i, t in enumerate(items):
        label(ax, 138, top - 14 - i * 13.5, t, fs=13.5, c=INK)
    # QUIC shortcut
    ax.annotate("", xy=(30, y0 - 4 * (h + gap) + h), xytext=(30, y0 - 2 * (h + gap) - 0.2),
                arrowprops=dict(arrowstyle="<|-", color=ORANGE, lw=2.2, connectionstyle="arc3,rad=0"))
    label(ax, 25.5, y0 - 3 * (h + gap) + h / 2, "QUIC\nskips\nupgrader", fs=12.5, c=ORANGE, bold=True)
    label(ax, 80, 4, "Overlays live above the host as libraries: go-libp2p-kad-dht (Kademlia / Amino), go-libp2p-pubsub (GossipSub), rendezvous, …",
          fs=13.5, c=INK2)
    save(fig, "11-libp2p-architecture.png")

# =================================================================== 12 upgrade pipeline
def fig_upgrade():
    fig, ax = canvas(16, 8)
    title(ax, "Connection setup: from raw socket to application stream", "TCP needs an upgrade pipeline; QUIC bundles TLS 1.3 and native streams into its own handshake")
    rows = [
        ("TCP", [("TCP handshake", GRAY_T, 22), ("multistream-select\n/noise", YELLOW_T, 20), ("Noise XX handshake\n(PeerID authenticated)", ORANGE_T, 30),
                 ("yamux\n(inlined in Noise ext.)", AQUA_T, 22), ("multistream-select\n/my/app/1.0.0", YELLOW_T, 22)]),
        ("QUIC", [("QUIC + TLS 1.3 handshake\n(PeerID cert, ALPN \"libp2p\")", ORANGE_T, 52), ("multistream-select\n/my/app/1.0.0", YELLOW_T, 22)]),
        ("nnet", [("TCP / KCP handshake", GRAY_T, 22), ("smux session\n(no auth, no crypto)", BLUE_T, 22), ("ExchangeNode\n(self-declared ID)", BLUE_T, 22)]),
    ]
    for r, (name, steps) in enumerate(rows):
        y = 50 - r * 17
        label(ax, 12, y + 5, name, fs=20, c=INK, bold=True)
        x = 22
        for (t, c, w) in steps:
            box(ax, x, y, w - 1.2, 10, t, fc=c, ec=c, fs=12.8)
            x += w
        arrow(ax, (x - 0.5, y + 5), (x + 5, y + 5), color=INK2)
        label(ax, x + 6.5, y + 5, "app data", fs=14, c=INK, ha="left", bold=True)
    label(ax, 80, 6.5, "Simplified; multistream-select can be pipelined and inlined muxer negotiation removes a round trip. Each libp2p protocol interaction opens its own stream.",
          fs=13, c=INK2)
    save(fig, "12-connection-upgrade.png")

# =================================================================== 13 NAT traversal
def fig_nat():
    fig, ax = canvas(16, 9.6)
    title(ax, "libp2p NAT traversal: AutoNAT → Circuit Relay v2 → DCUtR hole punch",
          "≈70% ± 7% hole-punch success across 4.4M attempts in 85k+ networks (Trautwein et al., IMC)")
    cols = {"A": (28, "Peer A (behind NAT)"), "R": (80, "Public relay"), "B": (132, "Peer B (behind NAT)")}
    for k, (x, t) in cols.items():
        box(ax, x - 15, 70, 30, 8, t, fc=ORANGE_T if k != "R" else GRAY_T, ec=ORANGE_T if k != "R" else GRAY_T, fs=15, bold=True)
        ax.plot([x, x], [8, 70], color=LINE, lw=2, zorder=1)
    steps = [
        ("B", "R", "① AutoNAT v2: “am I reachable?” → no  ·  RESERVE slot on relay", ORANGE, "-"),
        ("A", "R", "② A connects to B via /p2p/R/p2p-circuit/p2p/B", INK2, "-"),
        ("R", "B", "", INK2, "-"),
        ("B", "A", "③ DCUtR CONNECT (observed addrs) over relayed stream — measures RTT", VIOLET, "-"),
        ("A", "B", "④ CONNECT reply + SYNC", VIOLET, "-"),
        ("A", "B", "⑤ both dial simultaneously after RTT/2 → NAT bindings open → direct connection", AQUA, "-"),
    ]
    y = 63
    for (s, d, t, c, ls) in steps:
        xs, xd = cols[s][0], cols[d][0]
        if s == "A" and d == "B" and c == AQUA:
            arrow(ax, (28, y), (78, y), color=AQUA, lw=3); arrow(ax, (132, y), (82, y), color=AQUA, lw=3)
            ax.text(80, y + 1.6, t, ha="center", fontsize=14, color=INK, va="bottom")
            y -= 10; continue
        if {s, d} == {"A", "B"}:
            arrow(ax, (xs, y), (80, y), color=c, lw=2.2); arrow(ax, (80, y), (xd, y), color=c, lw=2.2)
        else:
            arrow(ax, (xs, y), (xd, y), color=c, lw=2.2)
        if t: ax.text(80, y + 1.6, t, ha="center", fontsize=14, color=INK, va="bottom")
        y -= 10 if t else 4
    box(ax, 18, 6, 124, 11, fc=AQUA_T, ec=AQUA_T)
    ax.add_patch(FancyArrowPatch((28, 11.5), (132, 11.5), arrowstyle="<|-|>", mutation_scale=18, color=AQUA, lw=4, zorder=4))
    label(ax, 80, 14.5, "direct A ↔ B connection (TCP or QUIC) — relay is no longer in the data path", fs=14.5, c=INK, bold=True)
    label(ax, 80, 8.5, "Relay v2 reservations cap duration & bytes, so any public node can afford to be a relay", fs=13, c=INK2)
    save(fig, "13-nat-traversal.png")

# =================================================================== 14 broadcast strategies
def fig_bcast_compare():
    fig, ax = canvas(16, 8.4)
    title(ax, "Three broadcast strategies on the same 16 peers", "Lines show which links carry the full message (illustrative)")
    rnd = random.Random(4)
    pts = [(math.cos(2 * math.pi * i / 16 + 0.2) * 17, math.sin(2 * math.pi * i / 16 + 0.2) * 17) for i in range(16)]
    centers = [(28, 34), (80, 34), (132, 34)]
    heads = ["nnet push (flooding)", "GossipSub", "nnet tree (K = 1)"]
    subs = ["≈ N × (degree − 1) sends\nmaximal redundancy", "≈ N × D eager sends (D = 6, solid)\n+ lazy IHAVE gossip (dashed, IDs only)", "≈ 1.25 × N sends (with dedup)\nno redundancy"]
    cols = [ORANGE, ORANGE, BLUE]
    # graphs
    deg_edges = set()
    for i in range(16):
        for j in (1, 2, 4, 8):
            deg_edges.add(tuple(sorted((i, (i + j) % 16))))
    mesh = set()
    while len(mesh) < 30:
        i, j = rnd.randrange(16), rnd.randrange(16)
        if i != j: mesh.add(tuple(sorted((i, j))))
    lazy = set()
    while len(lazy) < 14:
        i, j = rnd.randrange(16), rnd.randrange(16)
        if i != j and tuple(sorted((i, j))) not in mesh: lazy.add(tuple(sorted((i, j))))
    for k, (cx, cy) in enumerate(centers):
        box(ax, cx - 24, 7, 48, 61, fc=GRAY_T, ec=GRAY_T, r=2)
        label(ax, cx, 63.5, heads[k], fs=18, c=INK, bold=True)
        P = [(cx + x, cy + y) for x, y in pts]
        if k == 0:
            for (i, j) in deg_edges:
                ax.plot([P[i][0], P[j][0]], [P[i][1], P[j][1]], color=ORANGE, lw=1.6, alpha=0.75, zorder=2)
        elif k == 1:
            for (i, j) in mesh:
                ax.plot([P[i][0], P[j][0]], [P[i][1], P[j][1]], color=ORANGE, lw=1.8, alpha=0.8, zorder=2)
            for (i, j) in lazy:
                ax.plot([P[i][0], P[j][0]], [P[i][1], P[j][1]], color=INK2, lw=1.4, ls=(0, (2, 2.5)), zorder=3)
        else:
            # chord tree on 16 evenly spaced nodes (ids 0..15, fingers 2^i)
            def fwd(n, maxidx):
                for i in range(maxidx):
                    r = (n + (1 << i)) % 16
                    if r == 0: continue
                    chord_curve(ax, P[n], P[r], cx, cy, SEQ[min(4 - maxidx + 1 + 1, 5)] if False else BLUE, lw=2, bend=0.3)
                    fwd(r, i)
            fwd(0, 4)
        for i, p in enumerate(P):
            ax.add_patch(Circle(p, 1.2, fc=SURF if not (k == 2 and i == 0) else BLUE, ec=INK2 if k < 2 else BLUE, lw=1.5, zorder=5))
        label(ax, cx, 13.5, subs[k], fs=13.5, c=INK, linespacing=1.4)
    save(fig, "15-broadcast-strategies.png")

# =================================================================== 15 chord vs kademlia
def fig_chord_vs_kad():
    fig, ax = canvas(16, 8.6)
    title(ax, "Two ways to measure distance", "Chord (nnet): clockwise distance, deterministic fingers  ·  Kademlia (libp2p): XOR distance, k-buckets of 20")
    # chord
    cx, cy, R = 38, 36, 25
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=LINE, lw=3))
    for i in range(6):
        f = (1 << i) / 64
        p = ring_xy(cx, cy, R, f)
        chord_curve(ax, ring_xy(cx, cy, R, 0), p, cx, cy, SEQ[min(i, 5)], lw=2.4, bend=0.25)
        ax.add_patch(Circle(p, 1.2, fc=SEQ[min(i, 5)], ec=SURF, lw=1.5, zorder=6))
        lx, ly = ring_xy(cx, cy, R + 4, f); label(ax, lx, ly, f"+2^{i}" if i < 5 else "+2^5 (half)", fs=12.5, c=INK2)
    ax.add_patch(Circle(ring_xy(cx, cy, R, 0), 2, fc=BLUE, ec=SURF, lw=2, zorder=7)); label(ax, *ring_xy(cx, cy, R, 0), "A", c="white", bold=True, z=8)
    label(ax, cx, cy, "dist(a,b) = (b − a) mod 2ᵐ\nasymmetric · one correct\nfinger set per ID\n→ verifiable", fs=14, c=INK, linespacing=1.5)
    # kademlia trie
    x0, y0 = 92, 66
    label(ax, 122, 70.5, "Kademlia k-buckets for node 0110…", fs=16, c=INK, bold=True)
    bits = "0110"
    x, y = 100, 62
    for d in range(4):
        b = bits[d]; ob = "1" if b == "0" else "0"
        # sibling subtree = bucket
        sx = x + 22; sy = y - 9
        ax.plot([x, x + 6], [y, y - 9], color=INK2, lw=2); ax.plot([x, sx], [y, sy], color=ORANGE, lw=2)
        box(ax, sx - 1, sy - 7, 32, 6.4, f"bucket {d}: prefix {bits[:d]}{ob}…  (≤ 20 peers)", fc=ORANGE_T, ec=ORANGE, fs=12.5)
        label(ax, x + 1.5, y - 5, b, fs=12, c=INK2); label(ax, x + 13, y - 3.2, ob, fs=12, c=ORANGE, bold=True)
        x, y = x + 6, y - 9
    ax.add_patch(Circle((x, y), 1.6, fc=ORANGE, ec=SURF, zorder=5)); label(ax, x, y - 3.5, "self", fs=12.5, c=INK)
    ax.text(92, 16, "dist(a,b) = a ⊕ b  — symmetric: incoming queries refresh buckets\n"
                    "iterative lookups, α = 10 in flight, stop when β = 3 closest respond\n"
                    "any of k nodes per bucket is “valid” → liveness over auditability",
            fontsize=14, color=INK, va="top", linespacing=1.6)
    save(fig, "14-chord-vs-kademlia.png")


# =================== overrides (v2) ===================
def fig_engine():
    fig, ax = canvas(16, 8.6)
    title(ax, "Inside a RemoteNode: nnet's per-peer I/O engine", "Fixed goroutines per peer · bounded channels that drop when full · 8 parallel streams")
    box(ax, 4, 14, 26, 52, fc=BLUE_T, ec=BLUE_T)
    label(ax, 17, 61.5, "LocalNode", fs=17, c=INK, bold=True)
    for i, r in enumerate(["DIRECT", "RELAY", "BCAST_PUSH", "BCAST_TREE"]):
        box(ax, 7, 50 - i * 8.4, 20, 6.2, r, fc=SURF, ec=BLUE, fs=12.5, tc=BLUE)
    label(ax, 17, 19, "rx chan per routing type\n(23,333 buffered)", fs=12)
    box(ax, 40, 50, 22, 9, "txMsgChan\n(2,333 buffered)", fc=SURF, ec=BLUE, fs=13.5)
    box(ax, 40, 35, 22, 9, "rxMsgChan\n(2,333 buffered)", fc=SURF, ec=AQUA, fs=13.5)
    box(ax, 40, 20, 22, 9, "handleMsg goroutine\ndedup · keepalive 20 s", fc=SURF, ec=INK2, fs=13)
    box(ax, 40, 5, 22, 9, "RTT goroutine\nping ≈ 5 s, smoothed", fc=SURF, ec=INK2, fs=13)
    arrow(ax, (30, 54.5), (40, 54.5), color=BLUE, lw=2); label(ax, 35, 57.5, "send", fs=12)
    arrow(ax, (51, 35), (51, 29), color=AQUA, lw=2)
    arrow(ax, (40, 24.5), (30, 24.5), color=AQUA, lw=2); label(ax, 35, 27.3, "dispatch", fs=12)
    arrow(ax, (40, 9.5), (17, 14), color=MUTED, lw=1.5, ls=(0, (3, 3)), rad=-0.2); label(ax, 22, 6.5, "RTT feeds the relay\nnext-hop score", fs=11.5, c=INK2)
    box(ax, 72, 6, 52, 60, fc=GRAY_T, ec=GRAY_T)
    label(ax, 98, 62, "smux session · 8 streams", fs=16, c=INK, bold=True)
    for i in range(8):
        y = 51.5 - i * 5.8
        box(ax, 82, y, 32, 4.6, fc=SURF, ec=LINE)
        label(ax, 98, y + 2.4, f"stream {i}  [len 4B][protobuf]", fs=12, c=INK2, family="monospace")
        ax.add_patch(Circle((79, y + 2.4), 1.1, fc=BLUE, ec="none", zorder=4))
        ax.add_patch(Circle((117, y + 2.4), 1.1, fc=AQUA, ec="none", zorder=4))
    label(ax, 79, 4.0 + 6, "", fs=1)
    ax.plot([76.5, 76.5], [11.0, 56.0], color=BLUE, lw=2.5)
    ax.plot([120.5, 120.5], [11.0, 56.0], color=AQUA, lw=2.5)
    arrow(ax, (62, 54.5), (76.5, 54.5), color=BLUE, lw=2.2)
    ax.plot([120.5, 120.5, 69, 69], [11.0, 8.5, 8.5, 39.5], color=AQUA, lw=2.2, zorder=3)
    arrow(ax, (69, 39.5), (62, 39.5), color=AQUA, lw=2.2, shrink=0)
    label(ax, 79, 8.5, "", fs=1)
    label(ax, 98, 58.3, "● tx goroutine per stream     ● rx goroutine per stream", fs=12.5, c=INK2)
    ax.text(79, 8.6, "", fontsize=1)
    box(ax, 130, 34, 26, 20, "1 TCP / KCP\nconnection\nto the peer", fc=SURF, ec=INK, fs=15)
    arrow(ax, (124, 44), (130, 44), color=INK, style="<|-|>")
    box(ax, 130, 10, 26, 16, "Any channel full?\n→ message dropped\n(warning logged)", fc="#fdecec", ec=RED, fs=13, tc=INK)
    save(fig, "03-remotenode-engine.png")

def fig_chord_lists():
    fig, ax = canvas(16, 10)
    title(ax, "nnet’s “improved Chord”: every pointer becomes a list", "Example ring (8-bit IDs, 40 nodes) seen from node A · K = 3 nodes kept per finger bucket")
    ids, fg = small_ring(40, 3, 11, M=8)
    a = ids[0]; RING = 256
    cx, cy, R = 46, 40, 26
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=LINE, lw=3, zorder=1))
    succ = [ids[(1 + j) % len(ids)] for j in range(8)]
    pred = [ids[(-1 - j) % len(ids)] for j in range(8)]
    fcol = {3: SEQ[0], 4: SEQ[1], 5: SEQ[2], 6: SEQ[3], 7: SEQ[5]}
    for i in range(3, 8):
        s = (a + (1 << i)) % RING; e = (a + (1 << (i + 1))) % RING
        th1 = 90 - 360 * e / RING; th2 = 90 - 360 * s / RING
        rr = R + 3.5 + (i - 3) * 1.6
        ax.add_patch(Arc((cx, cy), 2 * rr, 2 * rr, theta1=th1 + 0.8, theta2=th2 - 0.8, color=fcol[i], lw=5, zorder=2))
        mid = ((s + (1 << i) / 2) % RING) / RING
        x, y = ring_xy(cx, cy, rr + 4.2, mid)
        label(ax, x, y, f"finger {i}", fs=13, c=fcol[i], bold=True)
    for v in ids:
        x, y = ring_xy(cx, cy, R, v / RING)
        fc, ec = SURF, INK2
        if v in succ: fc, ec = AQUA, AQUA
        if v in pred: fc, ec = YELLOW, YELLOW
        ax.add_patch(Circle((x, y), 1.0, fc=fc, ec=ec, lw=1.4, zorder=5))
    for i in range(3, 8):
        for r in fg[a][i]:
            if r in succ: continue
            p = ring_xy(cx, cy, R, r / RING)
            ax.add_patch(Circle(p, 1.4, fc=fcol[i], ec=SURF, lw=1.5, zorder=6))
            chord_curve(ax, ring_xy(cx, cy, R, a / RING), p, cx, cy, fcol[i], lw=1.6, alpha=0.85, bend=0.12)
    ax_, ay_ = ring_xy(cx, cy, R, a / RING)
    ax.add_patch(Circle((ax_, ay_), 2.1, fc=BLUE, ec=SURF, lw=2, zorder=7)); label(ax, ax_, ay_, "A", c="white", bold=True, z=8)
    label(ax, cx - 9, cy + 6, "ID space 0 … 2²⁵⁶−1\n(drawn as 0 … 255)", fs=13, c=INK2, bbox=dict(fc=SURF, ec="none", pad=2))
    x0 = 96
    rows = [
        (AQUA, "Successors", "closest nodes clockwise; cap = max(8, 2 × non-empty\nfingers) ≈ 2·log₂N  (fingers 0–2 fall inside this list)"),
        (YELLOW, "Predecessors", "mirror image counter-clockwise, same cap"),
        (SEQ[3], "Finger bucket i", "covers [A+2ⁱ, A+2ⁱ⁺¹) and keeps the K closest nodes in it"),
        (MUTED, "Neighbors", "every connected peer (unbounded), used by push broadcast"),
    ]
    for j, (c, h, d) in enumerate(rows):
        y = 75 - j * 11
        ax.add_patch(Circle((x0 + 2, y), 1.4, fc=c, ec=c))
        label(ax, x0 + 5, y + 0.3, h, fs=16, c=INK, bold=True, ha="left")
        ax.text(x0 + 5, y - 2.4, d, fontsize=13, color=INK2, ha="left", va="top", linespacing=1.4)
    box(ax, x0, 8, 58, 24, fc=BLUE_T, ec=BLUE_T)
    ax.text(x0 + 2.5, 29.5, "Why lists instead of single pointers?", fontsize=16, fontweight="bold", color=INK, va="top")
    ax.text(x0 + 2.5, 24.5, "• Fail-over: up to 3 candidates per finger\n• Proximity: the router picks the lowest-RTT candidate\n• Churn-safe: successor list grows with log N\n• Evicted from every list → connection closed",
            fontsize=13.5, color=INK, va="top", linespacing=1.6)
    save(fig, "04-chord-neighbor-lists.png")

def fig_relay():
    import bisect
    fig, ax = canvas(16, 9.4)
    title(ax, "Relay routing: greedy fingers + proximity route selection",
          "Each hop jumps to the farthest finger bucket that doesn’t overshoot the key, then picks the lowest-RTT node in that bucket")
    best = None
    for seed in range(40):
        ids, fg = small_ring(48, 3, seed, M=8)
        src = ids[0]; key = (src + 222) % 256
        cur = src; path = [src]; alts = []
        rnd = random.Random(seed)
        while True:
            j = bisect.bisect_right(ids, cur) % len(ids); succ = ids[j]
            if sim.dist(cur, key) < sim.dist(cur, succ): break
            nxt = None
            for i in range(7, -1, -1):
                c = [r for r in fg[cur][i] if sim.dist(cur, r) <= sim.dist(cur, key)]
                if c:
                    rtts = dict(zip(c, rnd.sample([14, 22, 37, 58, 91, 130], len(c))))
                    nxt = min(c, key=lambda r: rtts[r]); alts.append((cur, c, rtts, nxt, i)); break
            if nxt is None: nxt = succ
            cur = nxt; path.append(cur)
        if len(path) == 5 and len(alts[0][1]) == 3 and alts[0][3] != alts[0][1][0]:
            best = (ids, fg, src, key, path, alts); break
    ids, fg, src, key, path, alts = best
    RING = 256; cx, cy, R = 44, 40, 29
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=LINE, lw=3, zorder=1))
    for v in ids:
        ax.add_patch(Circle(ring_xy(cx, cy, R, v / RING), 0.85, fc=SURF, ec=MUTED, lw=1.2, zorder=4))
    frm, cands, rtts, chosen, bi = alts[0]
    for r in cands:
        if r != chosen:
            chord_curve(ax, ring_xy(cx, cy, R, frm / RING), ring_xy(cx, cy, R, r / RING), cx, cy, MUTED, lw=1.5, ls=(0, (3, 3)), bend=0.3)
    for r in cands:
        x, y = ring_xy(cx, cy, R + 4.8, r / RING)
        label(ax, x, y, f"{rtts[r]} ms", fs=12.5, c=BLUE if r == chosen else INK2, bold=r == chosen)
    for k, (p, q) in enumerate(zip(path, path[1:])):
        chord_curve(ax, ring_xy(cx, cy, R, p / RING), ring_xy(cx, cy, R, q / RING), cx, cy, BLUE, lw=3.2, bend=0.3 if sim.dist(p, q) > 16 else -0.15)
        mx, my = ring_xy(cx, cy, R * 0.55, ((p + sim.dist(p, q) / 2) % RING) / RING)
    for k, v in enumerate(path):
        ax.add_patch(Circle(ring_xy(cx, cy, R, v / RING), 1.6, fc=BLUE if k in (0, len(path) - 1) else SURF, ec=BLUE, lw=2.4, zorder=6))
    kx, ky = ring_xy(cx, cy, R, key / RING)
    ax.add_patch(Circle((kx, ky), 1.0, fc=RED, ec=RED, zorder=7))
    x, y = ring_xy(cx, cy, R + 5, key / RING); label(ax, x, y + 1.5, "key k", c=RED, bold=True)
    x, y = ring_xy(cx, cy, R + 4.5, src / RING); label(ax, x, y, "src", c=BLUE, bold=True)
    x, y = ring_xy(cx, cy, R + 6, path[-1] / RING); label(ax, x - 3, y - 1.5, "owner", c=BLUE, bold=True)
    label(ax, cx, cy, f"{len(path) - 1} hops", fs=20, c=INK, bold=True, bbox=dict(fc=SURF, ec="none", pad=2))
    x0 = 88
    box(ax, x0, 8, 68, 66, fc=GRAY_T, ec=GRAY_T)
    code = ("if key ∈ [me, successor):\n"
            "    deliver locally\n\n"
            "for i = 255 … 0:          # far → near\n"
            "  cands = finger[i] ∩ [me, key]\n"
            "  keep outbound or predecessor links\n"
            "  if cands:\n"
            "    score = −RTT_ms        # PRS\n"
            "    score = RelayPriority(score)\n"
            "    return argmax(score)\n\n"
            "fallback: walk successor list")
    ax.text(x0 + 3, 70, code, fontsize=14, family="monospace", color=INK, va="top", linespacing=1.5)
    ax.plot([x0 + 3, x0 + 65], [25, 25], color=LINE, lw=1)
    ax.text(x0 + 3, 22, "• Hop bound: ≤ log₂N w.h.p., ≈ ½·log₂N on average\n• Next hops are only self-dialed links (or predecessors)\n• Grey dashed: other candidates in the first hop’s bucket",
            fontsize=13.5, color=INK2, va="top", linespacing=1.6)
    save(fig, "05-relay-routing.png")

def fig_nat():
    fig, ax = canvas(16, 9.6)
    title(ax, "libp2p NAT traversal: AutoNAT → Circuit Relay v2 → DCUtR hole punch",
          "≈70% ± 7% hole-punch success across 4.4M attempts in 85k+ networks (Trautwein et al., IMC)")
    X = {"A": 28, "R": 80, "B": 132}
    for k, t in (("A", "Peer A (behind NAT)"), ("R", "Public relay"), ("B", "Peer B (behind NAT)")):
        box(ax, X[k] - 15, 70, 30, 8, t, fc=ORANGE_T if k != "R" else GRAY_T, ec=ORANGE_T if k != "R" else GRAY_T, fs=15, bold=True)
        ax.plot([X[k], X[k]], [20, 70], color=LINE, lw=2, zorder=1)
    def msg(y, segs, color, text):
        for s, d in segs: arrow(ax, (X[s], y), (X[d], y), color=color, lw=2.2)
        ax.text(80, y + 1.6, text, ha="center", fontsize=14, color=INK, va="bottom")
    msg(63, [("B", "R")], ORANGE, "① B learns it is unreachable (AutoNAT v2) and RESERVEs a slot on the relay")
    msg(54, [("A", "R"), ("R", "B")], INK2, "② A opens a relayed connection: /p2p/R/p2p-circuit/p2p/B")
    msg(45, [("B", "R"), ("R", "A")], VIOLET, "③ DCUtR CONNECT with observed addresses; B measures the RTT")
    msg(36, [("A", "R"), ("R", "B")], VIOLET, "④ CONNECT reply, then SYNC")
    arrow(ax, (X["A"], 27), (76, 27), color=AQUA, lw=3); arrow(ax, (X["B"], 27), (84, 27), color=AQUA, lw=3)
    ax.text(80, 28.6, "⑤ both dial simultaneously (timed by RTT/2) → NAT bindings open", ha="center", fontsize=14, color=INK, va="bottom")
    box(ax, 18, 6, 124, 12, fc=AQUA_T, ec=AQUA_T)
    ax.add_patch(FancyArrowPatch((28, 12), (132, 12), arrowstyle="<|-|>", mutation_scale=18, color=AQUA, lw=4, zorder=4))
    label(ax, 80, 15.2, "direct A ↔ B connection (TCP or QUIC); the relay leaves the data path", fs=14.5, c=INK, bold=True, bbox=dict(fc=AQUA_T, ec="none", pad=1))
    label(ax, 80, 8.3, "Relay v2 reservations cap duration and bytes, so any public node can afford to relay", fs=13, c=INK2, bbox=dict(fc=AQUA_T, ec="none", pad=1))
    save(fig, "13-nat-traversal.png")

def fig_chord_vs_kad():
    fig, ax = canvas(16, 8.6)
    title(ax, "Two ways to measure distance", "Chord (nnet): clockwise distance, deterministic fingers  ·  Kademlia (libp2p): XOR distance, k-buckets of 20")
    box(ax, 4, 4, 74, 66, fc=BLUE_T, ec=BLUE_T, r=2); box(ax, 82, 4, 74, 66, fc=ORANGE_T, ec=ORANGE_T, r=2)
    label(ax, 41, 65, "Chord finger table (nnet)", fs=18, c=INK, bold=True)
    label(ax, 119, 65, "Kademlia k-buckets (libp2p)", fs=18, c=INK, bold=True)
    cx, cy, R = 41, 39, 18
    ax.add_patch(Circle((cx, cy), R, fc="none", ec="#c4c3bd", lw=3, zorder=3))
    A = ring_xy(cx, cy, R, 0)
    labs = {2: "+4", 3: "+8", 4: "+16"}
    for i in range(6):
        f = (1 << i) / 64; p = ring_xy(cx, cy, R, f); col = SEQ[min(i, 5)]
        chord_curve(ax, A, p, cx, cy, col, lw=2.4, bend=0.25, z=4)
        ax.add_patch(Circle(p, 1.1, fc=col, ec=SURF, lw=1.5, zorder=6))
        if i in labs:
            lx, ly = ring_xy(cx, cy, R + 4.5, f); label(ax, lx, ly, labs[i], fs=12.5, c=INK2)
    lx, ly = ring_xy(cx, cy, R + 4.5, 1.5 / 64); label(ax, lx + 3, ly + 1.5, "+1, +2", fs=12.5, c=INK2)
    bx_, by_ = ring_xy(cx, cy, R, 0.5); label(ax, bx_ + 2.5, by_ - 0.2, "+32 (half way round)", fs=12.5, c=INK2, ha="left")
    ax.add_patch(Circle(A, 1.9, fc=BLUE, ec=SURF, lw=2, zorder=7)); label(ax, A[0], A[1], "A", c="white", bold=True, z=8)
    label(ax, 41, 10, "dist(a, b) = (b − a) mod 2ᵐ  ·  asymmetric\nexactly one correct finger set per ID → verifiable", fs=13.5, c=INK, linespacing=1.5)
    # kademlia trie, node id 0110
    bits = "0110"; x, y = 92, 58; bx = 116
    for d in range(4):
        b = bits[d]; ob = "1" if b == "0" else "0"
        ny = y - 9.5
        ax.plot([x, x + 3], [y, ny], color=INK2, lw=2.2)
        label(ax, x - 0.4, (y + ny) / 2, b, fs=12.5, c=INK2, ha="right")
        ax.plot([x, bx], [y, y - 4.5], color=ORANGE, lw=2)
        label(ax, (x + bx) / 2, y - 1.2, ob, fs=12.5, c=ORANGE, bold=True)
        box(ax, bx, y - 7.6, 37, 6.2, f"bucket {d}: prefix {bits[:d]}{ob}…   ≤ 20 peers", fc=SURF, ec=ORANGE, fs=12.5)
        x, y = x + 3, ny
    ax.add_patch(Circle((x, y), 1.6, fc=ORANGE, ec=SURF, zorder=5)); label(ax, x, y - 3.6, "self 0110…", fs=12.5, c=INK)
    label(ax, 119, 10, "dist(a, b) = a ⊕ b  ·  symmetric (incoming queries refresh buckets)\niterative lookups, α = 10 in flight, β = 3 · any of k nodes is valid", fs=13.5, c=INK, linespacing=1.5)
    save(fig, "14-chord-vs-kademlia.png")

if __name__ == "__main__":
    for f in [fig_philosophy, fig_nnet_stack, fig_engine, fig_chord_lists, fig_relay, fig_tree, fig_measured, fig_sim_scaling,
              fig_throughput, fig_hops, fig_libp2p_stack, fig_upgrade, fig_nat, fig_bcast_compare, fig_chord_vs_kad]:
        f()
