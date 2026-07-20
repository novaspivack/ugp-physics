"""Exact domain-wall and bulk-defect energies of the spin-7 chain.

The 1D spin-7 chain has energy E[s] = sum_i p(s_{i-1}, s_i, s_{i+1}) with
p(L,C,R) = (C+R-CR-LCR) mod 7, and exactly three uniform ground sectors
{0^n, 1^n, 5^n} (CatAL gte_ring_ground_states_uniform_general).

This script computes EXACTLY (integer arithmetic, no fits):
  1. The minimal interface (domain-wall) energy E_w(g,g') between every ordered
     pair of ground sectors g != g' in {0,1,5}: the minimal total weight of a
     path in the 49-node pair digraph from (g,g) to (g',g'), edge
     (a,b)->(b,c) weighted p(a,b,c).  Also the minimal path length and the
     number of minimal-weight paths of each length (prefactor input).
  2. The minimal bulk-defect energy above each uniform sector: minimal energy
     of any single-site and two-site replacement in a long g...g background
     (window enumeration), i.e. the minimal cost of a closed excursion
     (g,g) -> ... -> (g,g) of positive weight.
  3. The predicted asymptotic exponential slope of the transfer-matrix gap:
     slope = min( E_w over sector pairs, E_loop over sectors ) discriminated
     by which mechanism splits the 3-fold degenerate Perron multiplet.

Expected output range: small integers (1..6) for E_w and E_loop.
"""

import heapq
import json
import os
import signal
import sys
from itertools import product

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

# ---------------------------------------------------------------- digraph
# nodes: (a,b); edge (a,b)->(b,c) with weight p(a,b,c)
nodes = [(a, b) for a in range(Q) for b in range(Q)]

def edges_from(node):
    a, b = node
    for c in range(Q):
        yield (b, c), p_gf7(a, b, c)

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

# 1. minimal interface energies between ground sectors
print("=== Minimal interface (domain-wall) energies E_w(g -> g') ===")
wall = {}
for g in GS:
    dist = dijkstra((g, g))
    for gp in GS:
        if gp == g:
            continue
        wall[(g, gp)] = dist[(gp, gp)]
        print(f"  E_w({g} -> {gp}) = {dist[(gp, gp)]}")
E_w_min = min(wall.values())
print(f"  => minimal wall energy E_w = {E_w_min}")

# minimal path lengths and path counts at minimal weight (for the prefactor):
# count paths from (g,g) to (g',g') with total weight == E_w(g,g') as a
# function of length n (number of edges), for n up to N_MAX.  Uses DP over
# (node, accumulated weight <= E_w).
N_MAX = 30

def minimal_path_counts(g, gp, E_target):
    counts = []
    # state: dict[(node, w)] = number of paths
    state = {((g, g), 0): 1}
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

print("\n=== Minimal-weight path counts vs length (prefactor input) ===")
path_counts = {}
for (g, gp), Ew in sorted(wall.items()):
    if Ew == E_w_min:
        counts = minimal_path_counts(g, gp, Ew)
        first = next((i + 1 for i, c in enumerate(counts) if c > 0), None)
        path_counts[f"{g}->{gp}"] = {"E_w": Ew, "first_length": first,
                                     "counts_by_length": counts[:20]}
        print(f"  {g}->{gp} (E_w={Ew}): first length {first}, "
              f"counts n=1..12: {counts[:12]}")

# 2. minimal bulk-defect (closed-excursion) energies per sector:
# minimal weight of a closed walk (g,g) -> ... -> (g,g) with positive weight.
# Equivalently minimal positive energy of a local perturbation of the uniform
# background.  Dijkstra from (g,g) over states with weight>0 forced:
print("\n=== Minimal bulk-defect energies E_loop(g) (closed positive excursions) ===")

def min_positive_loop(g):
    # shortest positive-weight closed walk at (g,g): for each first step
    # (g,g)->(g,c) with weight w0, then shortest path back to (g,g).
    best = None
    for c in range(Q):
        w0 = p_gf7(g, g, c)
        dist = dijkstra((g, c))
        back = dist[(g, g)]
        total = w0 + back
        if total > 0 and (best is None or total < best):
            best = total
    return best

E_loop = {}
for g in GS:
    E_loop[g] = min_positive_loop(g)
    print(f"  E_loop({g}) = {E_loop[g]}")

# also: single-site and two-site replacement energies by direct enumeration
print("\n=== Direct enumeration: single/two-site defect energies in g^inf ===")
defect = {}
for g in GS:
    best1 = None
    for x in range(Q):
        if x == g:
            continue
        # windows affected: (g,g,x), (g,x,g), (x,g,g)
        E = p_gf7(g, g, x) + p_gf7(g, x, g) + p_gf7(x, g, g)
        if best1 is None or E < best1:
            best1 = E
    best2 = None
    for x in range(Q):
        for y in range(Q):
            if x == g and y == g:
                continue
            E = (p_gf7(g, g, x) + p_gf7(g, x, y) + p_gf7(x, y, g)
                 + p_gf7(y, g, g))
            if E > 0 and (best2 is None or E < best2):
                best2 = E
    defect[g] = {"single_site_min": best1, "two_site_min_positive": best2}
    print(f"  sector {g}: min single-site defect E = {best1}, "
          f"min positive two-site defect E = {best2}")

# 3. predicted slope
E_loop_min = min(E_loop.values())
print("\n=== Predicted asymptotic gap slope ===")
print(f"  min wall energy   E_w    = {E_w_min}")
print(f"  min loop energy   E_loop = {E_loop_min}")
# The Perron multiplet splitting at large beta:
#  - wall fugacities connect sectors: contribute e^{-beta E_w} OFF-diagonal
#  - loop fugacities shift sectors:   contribute e^{-beta E_loop} ON-diagonal
# If E_loop < E_w and the loop corrections are sector-ASYMMETRIC, the gap
# slope is E_loop; if loops are symmetric (or E_w <= E_loop), slope is E_w.
loop_sym = len(set(E_loop.values())) == 1
print(f"  loop energies sector-symmetric at minimal order: {loop_sym}")
if E_w_min <= E_loop_min:
    predicted = E_w_min
    mech = "wall-dominated"
else:
    predicted = E_loop_min if not loop_sym else E_w_min
    mech = ("loop-asymmetry-dominated" if not loop_sym
            else "wall-dominated (symmetric loops cancel in ratio)")
print(f"  PREDICTED slope of Delta(beta) ~ e^(-beta*slope): {predicted}  ({mech})")
print("  NOTE: symmetric loop corrections shift lambda_1 and lambda_2 equally")
print("  at leading order only if the corrections are equal across sectors;")
print("  the numerical scaling study adjudicates.")

signal.alarm(0)

out = {
    "wall_energies": {f"{g}->{gp}": v for (g, gp), v in wall.items()},
    "E_w_min": E_w_min,
    "minimal_path_counts": path_counts,
    "loop_energies": {str(g): E_loop[g] for g in GS},
    "E_loop_min": E_loop_min,
    "loop_sector_symmetric": loop_sym,
    "direct_defects": {str(g): defect[g] for g in GS},
    "predicted_slope": predicted,
    "mechanism": mech,
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_domain_wall_energy_exact.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
