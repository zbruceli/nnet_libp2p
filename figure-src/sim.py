# Faithful re-implementation of nnet's Chord fingers, BROADCAST_TREE and RELAY routing
import random, bisect, sys, json
from functools import lru_cache
sys.setrecursionlimit(100000)
M = 64
RING = 1 << M
def build(N, K, seed):
    rnd = random.Random(seed)
    s = set()
    while len(s) < N: s.add(rnd.getrandbits(M))
    ids = sorted(s)
    def first_k(start, end_excl):  # first K nodes clockwise in [start, end)
        out = []
        j = bisect.bisect_left(ids, start % RING)
        for t in range(N):
            v = ids[(j + t) % N]
            if (v - start) % RING < (end_excl - start) % RING or (end_excl - start) % RING == 0:
                out.append(v)
                if len(out) == K: break
            else: break
        return out
    fingers = {}
    for a in ids:
        fl = []
        for i in range(M):
            s = (a + (1 << i)) % RING; e = (a + (1 << (i + 1))) % RING
            fl.append([x for x in first_k(s, e) if x != a])
        fingers[a] = fl
    return ids, fingers
def dist(a, b): return (b - a) % RING
def tree_sends(ids, fingers, dedup, origin):
    if dedup:
        seen = {origin}; sends = 0; q = [(origin, None, M)]
        while q:
            node, sender, maxidx = q.pop()
            for i in range(maxidx):
                for r in fingers[node][i]:
                    if r == sender or r == origin: continue
                    sends += 1
                    if r not in seen:
                        seen.add(r); q.append((r, node, dist(node, r).bit_length() - 1))
        return sends, len(seen)
    @lru_cache(None)
    def f(node, sender, maxidx):
        tot = 0
        for i in range(maxidx):
            for r in fingers[node][i]:
                if r == sender or r == origin: continue
                tot += 1 + f(r, node, dist(node, r).bit_length() - 1)
        return tot
    return f(origin, None, M), None
def relay_hops(ids, fingers, src, dest, rnd):
    hops = 0; cur = src
    while True:
        j = bisect.bisect_right(ids, cur) % len(ids); succ = ids[j]
        if dist(cur, dest) < dist(cur, succ): return hops
        nxt = None
        for i in range(M - 1, -1, -1):
            c = [r for r in fingers[cur][i] if dist(cur, r) <= dist(cur, dest)]
            if c: nxt = rnd.choice(c); break
        if nxt is None: nxt = succ
        cur = nxt; hops += 1
if __name__ == "__main__":
    res = {"tree": [], "hops": []}
    for N in [10, 30, 60, 100, 300, 1000, 3000, 10000]:
        for K in [1, 2, 3]:
            vals = {"nodedup": [], "dedup": [], "cov": []}
            for seed in range(3 if N >= 3000 else 5):
                ids, fg = build(N, K, seed)
                o = ids[0]
                nd, _ = tree_sends(ids, fg, False, o)
                dd, cov = tree_sends(ids, fg, True, o)
                vals["nodedup"].append(nd / N); vals["dedup"].append(dd / N); vals["cov"].append(cov / N)
            r = {k: sum(v) / len(v) for k, v in vals.items()}; r.update(N=N, K=K)
            res["tree"].append(r); print(r, flush=True)
        ids, fg = build(N, 3, 42); rnd = random.Random(1)
        hs = [relay_hops(ids, fg, rnd.choice(ids), rnd.randrange(RING), rnd) for _ in range(2000)]
        res["hops"].append({"N": N, "avg": sum(hs) / len(hs), "max": max(hs)}); print(res["hops"][-1], flush=True)
    json.dump(res, open("sim.json", "w"), indent=1)
