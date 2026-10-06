"""Hero image: nnet's Chord ring (real spanning-tree broadcast) meeting a libp2p-style mesh.

usage: python3 hero.py ../images
"""
import math, random, sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path
import sim

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
BG = "#0b1220"; BLUE = "#3987e5"; BLUE_L = "#86b6ef"; ORANGE = "#eb6834"; ORANGE_L = "#f4a07c"; INK = "#f5f4f0"; INK2 = "#a9b3c4"
plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
W, H = 16, 8.4  # 1600 x 840


def ring_xy(cx, cy, R, frac):
    th = math.pi / 2 - 2 * math.pi * frac
    return cx + R * math.cos(th), cy + R * math.sin(th)


def curve(ax, p, q, c, color, lw, alpha, bend, z=2):
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    ctrl = (mx + (c[0] - mx) * bend, my + (c[1] - my) * bend)
    ax.add_patch(PathPatch(Path([p, ctrl, q], [Path.MOVETO, Path.CURVE3, Path.CURVE3]), fc="none", ec=color, lw=lw, alpha=alpha, zorder=z,
                           capstyle="round"))


def glow_dot(ax, xy, r, color, z=5):
    for k, a in ((3.2, 0.06), (2.2, 0.12), (1.5, 0.22)):
        ax.add_patch(Circle(xy, r * k, fc=color, ec="none", alpha=a, zorder=z))
    ax.add_patch(Circle(xy, r, fc=color, ec="none", zorder=z + 1))


def render(with_text, fname):
    fig = plt.figure(figsize=(W, H), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 84); ax.axis("off")
    fig.patch.set_facecolor(BG)
    # faint background grid of "address space" dots
    rng = np.random.default_rng(3)
    xs, ys = rng.uniform(0, 160, 900), rng.uniform(0, 84, 900)
    ax.scatter(xs, ys, s=rng.uniform(0.5, 3, 900), c=INK2, alpha=0.12, lw=0, zorder=0)

    # ---------------- left: Chord ring with real tree broadcast (nnet algorithm, K=1)
    sim.M = 10; sim.RING = 1 << 10
    ids, fg = sim.build(72, 1, 9)
    cx, cy, R = 42, 51, 25.5
    ax.add_patch(Circle((cx, cy), R, fc="none", ec=BLUE, lw=1.2, alpha=0.35, zorder=1))
    origin = ids[0]
    seen = {origin}; q = [(origin, None, sim.M, 0)]; edges = []
    while q:
        node, sender, maxidx, d = q.pop(0)
        for i in range(maxidx):
            for r in fg[node][i]:
                if r == sender or r == origin or r in seen:
                    continue
                seen.add(r); edges.append((node, r, d)); q.append((r, node, sim.dist(node, r).bit_length() - 1, d + 1))
    pos = {v: ring_xy(cx, cy, R, v / sim.RING) for v in ids}
    for (p, r, d) in edges:
        curve(ax, pos[p], pos[r], (cx, cy), BLUE_L if d == 0 else BLUE, lw=2.4 - 0.35 * d, alpha=0.95 - 0.13 * d, bend=0.45)
    for v in ids:
        glow_dot(ax, pos[v], 0.42, BLUE_L)
    glow_dot(ax, pos[origin], 0.9, INK, z=7)

    # ---------------- right: libp2p-style mesh (random D-regular-ish graph, a few bold direct streams)
    rnd = random.Random(11)
    pts = []
    while len(pts) < 46:
        x, y = rnd.uniform(90, 155), rnd.uniform(28, 77)
        if all((x - a) ** 2 + (y - b) ** 2 > 30 for a, b in pts):
            pts.append((x, y))
    # nearest-neighbour style mesh, degree ~ 4-6
    E = set()
    for i, (x, y) in enumerate(pts):
        near = sorted(range(len(pts)), key=lambda j: (pts[j][0] - x) ** 2 + (pts[j][1] - y) ** 2)[1:6]
        for j in near[: rnd.choice([3, 4, 5])]:
            E.add(tuple(sorted((i, j))))
    for (i, j) in E:
        ax.plot([pts[i][0], pts[j][0]], [pts[i][1], pts[j][1]], color=ORANGE, lw=1.1, alpha=0.38, zorder=2)
    # long-range direct streams (dial anyone, anywhere)
    for (i, j) in [(2, 30), (7, 41), (15, 25), (33, 11)]:
        a, b = pts[i % len(pts)], pts[j % len(pts)]
        ax.plot([a[0], b[0]], [a[1], b[1]], color=ORANGE_L, lw=2.6, alpha=0.9, zorder=3, solid_capstyle="round")
        for k in range(4):  # multiplexed-stream feel: thin parallel strands
            off = (k - 1.5) * 0.35
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nx, ny = -dy / L * off, dx / L * off
            ax.plot([a[0] + nx, b[0] + nx], [a[1] + ny, b[1] + ny], color=ORANGE, lw=0.6, alpha=0.5, zorder=3)
    for p in pts:
        glow_dot(ax, p, 0.5, ORANGE_L)

    # ---------------- bridge: a few links from the ring to the mesh
    ring_right = sorted(ids, key=lambda v: -pos[v][0])[:5]
    targets = sorted(range(len(pts)), key=lambda j: pts[j][0])[:5]
    for v, j in zip(ring_right, targets):
        p, qq = pos[v], pts[j]
        ctrl = ((p[0] + qq[0]) / 2, (p[1] + qq[1]) / 2 + rnd.uniform(-8, 8))
        ax.add_patch(PathPatch(Path([p, ctrl, qq], [Path.MOVETO, Path.CURVE3, Path.CURVE3]), fc="none", ec=INK2, lw=1.0, alpha=0.35,
                               ls=(0, (2, 3)), zorder=1, ) if False else PathPatch(Path([p, ctrl, qq], [Path.MOVETO, Path.CURVE3, Path.CURVE3]), fc="none", ec=INK2, lw=1.2, alpha=0.55, ls=(0, (2, 3)), zorder=1))

    if with_text:
        # darken a band behind the title for legibility
        ax.text(6, 13.5, "Rings and Toolkits", fontsize=46, fontweight="bold", color=INK, zorder=10, va="center")
        ax.text(6.3, 6.2, "nnet vs. libp2p: architecture, algorithms, performance and scalability", fontsize=19, color=INK2, zorder=10, va="center")
        ax.text(42, 80.5, "nnet · Chord ring + spanning-tree broadcast", fontsize=13, color=BLUE_L, ha="center", zorder=10, alpha=0.9)
        ax.text(122.5, 80.5, "libp2p · direct, multiplexed streams over a mesh", fontsize=13, color=ORANGE_L, ha="center", zorder=10, alpha=0.9)
    if not with_text:
        ax.set_ylim(11, 95)  # same 84-unit span: re-centre the artwork when there is no title strip
    fig.savefig(os.path.join(OUT, fname), dpi=100, facecolor=BG)
    plt.close(fig)
    print("wrote", fname)


render(True, "00-hero.png")
render(False, "00-hero-notext.png")
