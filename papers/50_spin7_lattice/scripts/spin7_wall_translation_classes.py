"""Translation-class counts of minimal directed domain walls of the spin-7 chain.

For each ordered ground-sector pair (g, g') in {0,1,5}^2, g != g', count paths
in the pair digraph from (g,g) to (g',g') of total weight exactly E_w(g,g')
as a function of path length n.  For a finite set of wall SHAPES, the count
grows exactly linearly at large n (pure translation freedom); the increment
equals the number of translation classes w_{gg'} (the per-site wall insertion
rate entering the dilute directed wall gas).

Outputs the directed wall table (E_w, w) and the predicted asymptotic gap law
  Delta(beta) ~ 2*sqrt(w_01*w_10) * exp(-beta*(E_w(0->1)+E_w(1->0))/2),
i.e. slope E_+ = 3/2 and prefactor from the translation-class counts,
PLUS the subleading sector-5 channel exponents for the cross-check.

Expected output: small integer translation-class counts (1..10 range).
"""

import json
import os
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
GS = [0, 1, 5]

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q

nodes = [(a, b) for a in range(Q) for b in range(Q)]

def edges_from(node):
    a, b = node
    for c in range(Q):
        yield (b, c), p_gf7(a, b, c)

# wall energies (recompute for self-containment)
import heapq

def dijkstra(src):
    dist = {n: None for n in nodes}
    dist[src] = 0
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if dist[u] is not None and d > dist[u]:
            continue
        for v, w in edges_from(u):
            nd = d + w
            if dist[v] is None or nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist

wall = {}
for g in GS:
    dist = dijkstra((g, g))
    for gp in GS:
        if gp != g:
            wall[(g, gp)] = dist[(gp, gp)]

N_MAX = 60

def path_counts(g, gp, E_target):
    state = {((g, g), 0): 1}
    counts = []
    for n in range(1, N_MAX + 1):
        new = {}
        for (node, w), cnt in state.items():
            for v, dw in edges_from(node):
                nw = w + dw
                if nw <= E_target:
                    key = (v, nw)
                    new[key] = new.get(key, 0) + cnt
        state = new
        counts.append(state.get(((gp, gp), E_target), 0))
    return counts

print("=== Directed wall table: E_w and translation classes w ===")
table = {}
for (g, gp), Ew in sorted(wall.items()):
    counts = path_counts(g, gp, Ew)
    # increments at large n; verify exact linearity over the last 20 lengths
    incs = [counts[i] - counts[i - 1] for i in range(1, len(counts))]
    tail = incs[-20:]
    linear = len(set(tail)) == 1
    w_classes = tail[-1] if linear else None
    table[f"{g}->{gp}"] = {"E_w": Ew, "translation_classes": w_classes,
                           "tail_linear": linear,
                           "counts_n_1_12": counts[:12]}
    print(f"  {g}->{gp}: E_w={Ew}  w={w_classes}  (tail linear: {linear}; "
          f"counts n=1..10: {counts[:10]})")

w01 = table["0->1"]["translation_classes"]
w10 = table["1->0"]["translation_classes"]
w05 = table["0->5"]["translation_classes"]
w50 = table["5->0"]["translation_classes"]
w15 = table["1->5"]["translation_classes"]
w51 = table["5->1"]["translation_classes"]

E01, E10 = wall[(0, 1)], wall[(1, 0)]
E05, E50 = wall[(0, 5)], wall[(5, 0)]
E15, E51 = wall[(1, 5)], wall[(5, 1)]

import math
slope_01 = (E01 + E10) / 2
slope_05 = (E05 + E50) / 2
slope_15 = (E15 + E51) / 2
pref_01 = 2 * math.sqrt(w01 * w10)

print("\n=== Channel exponents (geometric-mean law for directed walls) ===")
print(f"  0<->1: slope (E01+E10)/2 = {slope_01}   prefactor 2*sqrt(w01*w10) = {pref_01:.6f}")
print(f"  0<->5: slope (E05+E50)/2 = {slope_05}")
print(f"  1<->5: slope (E15+E51)/2 = {slope_15}")
print(f"\nPREDICTION: Delta(beta) ~ {pref_01:.6f} * exp(-{slope_01}*beta)")
print("(0<->1 channel dominates; 0<->5 and 1<->5 subleading)")

signal.alarm(0)

out = {
    "wall_table": table,
    "channel_slopes": {"01": slope_01, "05": slope_05, "15": slope_15},
    "predicted_slope": slope_01,
    "predicted_prefactor": pref_01,
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_wall_translation_classes.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
