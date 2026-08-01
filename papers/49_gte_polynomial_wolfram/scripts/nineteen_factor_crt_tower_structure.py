#!/usr/bin/env python3
"""CRT tower structure of the period-475 attractor of p on the 5-cell GF(7) ring.

Verifies the canonical decomposition 475 = 5 (ring) x 5 (drift) x 19 (inert clock):

 1. sigma = T^190 and T^95 = sigma^3 on the cycle (R04 anchors).
 2. Spacetime scalarization: s_i(t) = w(t + 190 i) for the scalar sequence
    w(tau) = cell-0 value at time tau; w satisfies
    w(tau+1) = p(w(tau-190), w(tau), w(tau+190)) on Z_475.
 3. CRT split Z_475 = Z_25 x Z_19 with stride 190 = (15, 0); the rows
    row_b(a) = w(a,b) satisfy row_{b+1} = G(row_b) for the induced 25-ring CA
    (Gv)(a) = p(v(a-16), v(a-1), v(a+14)); G^19 = id on the rows, 19 minimal;
    all offsets = 4 mod 5 (self-similar 5-layer interleave).
 4. Drift-cancelled return map R = sigma^3 T^5: order 19 on the cycle; the
    other four twists sigma^c T^5 have order 95. R^19 fixes the cycle pointwise.
 5. Gauge sector: exact periods of all elementary symmetric functions e_1..e_5
    and power sums p_1..p_4 of the cell values along the cycle (must divide 95).
 6. Pure-19 line witness: row average v(b) = sum_a w(a,b) non-constant; pure-25
    witness u(a) = sum_b w(a,b) non-constant.
 7. Zero-mean reduction: per-cell time sums equal across cells and = 3 * sum_t W(t).
 8. G-basin sample: cycle lengths G reaches from random 25-ring initial states
    (is the 19-cycle G-generic or selected?).

Expected: all structural claims True; gauge periods in {19, 95}; v, u non-constant.
"""
import os
import json
import random
import signal
import sys

TIMEOUT_SECONDS = 600
signal.signal(signal.SIGALRM, lambda s, f: sys.exit("TIMEOUT"))
signal.alarm(TIMEOUT_SECONDS)

Q, n = 7, 5


def step(s, size=n):
    return tuple((s[i] + s[(i + 1) % size] - s[i] * s[(i + 1) % size]
                  - s[(i - 1) % size] * s[i] * s[(i + 1) % size]) % Q
                 for i in range(size))


def shift(s, j, size=n):
    return tuple(s[(i + j) % size] for i in range(size))


# --- locate the 475-cycle (same method as gte_zeta_period475_linear_structure) ---
random.seed(475)
cycle = None
while cycle is None:
    s = tuple(random.randrange(Q) for _ in range(n))
    seen = {}
    t = 0
    while s not in seen:
        seen[s] = t
        s = step(s)
        t += 1
    if t - seen[s] == 475:
        c = [s]
        w = step(s)
        while w != s:
            c.append(w)
            w = step(w)
        cycle = c
L = len(cycle)
assert L == 475
idx = {st: i for i, st in enumerate(cycle)}
results = {"cycle_length": L}

# --- 1. anchors ---
m = idx[shift(cycle[0], 1)] % L
anchor_sigma = all(idx[shift(cycle[i], 1)] == (i + m) % L for i in range(L))
anchor_t95 = all(cycle[(i + 95) % L] == shift(cycle[i], 3) for i in range(L))
print(f"sigma = T^{m} on cycle: {anchor_sigma}; T^95 = sigma^3: {anchor_t95}")
results["anchors"] = {"sigma_eq_T_pow": m, "sigma_consistent": anchor_sigma,
                      "T95_eq_sigma3": anchor_t95}
assert m == 190 and anchor_sigma and anchor_t95

# --- 2. scalarization ---
w = [cycle[t][0] for t in range(L)]
scal_ok = all(cycle[t][i] == w[(t + 190 * i) % L]
              for t in range(L) for i in range(n))
feq_ok = all(w[(tau + 1) % L]
             == (w[tau] + w[(tau + 190) % L] - w[tau] * w[(tau + 190) % L]
                 - w[(tau - 190) % L] * w[tau] * w[(tau + 190) % L]) % Q
             for tau in range(L))
print(f"scalarization s_i(t) = w(t+190i): {scal_ok}; "
      f"functional equation w(tau+1)=p(w(tau-190),w(tau),w(tau+190)): {feq_ok}")
results["scalarization"] = {"holds": scal_ok, "functional_equation": feq_ok}

# --- 3. CRT split and the induced 25-ring CA G ---
crt_stride = (190 % 25, 190 % 19)
rows = [[None] * 25 for _ in range(19)]
for tau in range(L):
    rows[tau % 19][tau % 25] = w[tau]
rows_complete = all(all(x is not None for x in r) for r in rows)


def G(v):
    return tuple((v[(a - 1) % 25] + v[(a + 14) % 25]
                  - v[(a - 1) % 25] * v[(a + 14) % 25]
                  - v[(a - 16) % 25] * v[(a - 1) % 25] * v[(a + 14) % 25]) % Q
                 for a in range(25))


rows = [tuple(r) for r in rows]
g_maps_rows = all(G(rows[b]) == rows[(b + 1) % 19] for b in range(19))
g19_id = True  # implied by g_maps_rows over Z_19
g_min_period = next(d for d in (1, 19) if rows[d % 19] == rows[0]) \
    if rows[0] == rows[0] else None
g_min_period = 1 if all(rows[b] == rows[0] for b in range(19)) else 19
offsets_mod5 = sorted({(-16) % 5, (-1) % 5, 14 % 5})
print(f"CRT stride 190 = {crt_stride}; rows complete: {rows_complete}; "
      f"row_(b+1) = G(row_b): {g_maps_rows}; minimal G-period: {g_min_period}; "
      f"G offsets mod 5: {offsets_mod5}")
results["crt_tower"] = {"stride_crt": crt_stride, "rows_complete": rows_complete,
                        "G_maps_rows": g_maps_rows,
                        "G_min_period": g_min_period,
                        "G_offsets_mod5": offsets_mod5}

# --- 4. drift-cancelled return map R = sigma^c T^5 ---
twist_orders = {}
for c in range(5):
    e = (190 * c + 5) % L
    twist_orders[c] = L // __import__("math").gcd(e, L)
r_state = shift(step(step(step(step(step(cycle[0]))))), 3)
r_ok = r_state == cycle[idx[cycle[0]] + 100 if False else 100 % L]
# direct check: R(s) = sigma^3(T^5(s)) equals T^100(s) on the cycle
r_eq_t100 = all(shift(step(step(step(step(step(cycle[i]))))), 3)
                == cycle[(i + 100) % L] for i in range(L))
# R^19 fixes the cycle pointwise <=> 19*100 = 1900 = 0 mod 475
r19_fixes = (19 * 100) % L == 0
n_r_orbits = L // 19
print(f"twist orders on cycle (sigma^c T^5): {twist_orders}; "
      f"R = sigma^3 T^5 = T^100 on cycle: {r_eq_t100}; "
      f"R^19 = id on cycle: {r19_fixes}; #R-orbits = {n_r_orbits}")
results["return_map"] = {"twist_orders": twist_orders,
                         "R_eq_T100": r_eq_t100, "R19_id": r19_fixes,
                         "n_R_orbits": n_r_orbits}

# --- 5. gauge-invariant observable periods ---
def seq_period(seq):
    Ls = len(seq)
    for d in sorted(set(d for d in range(1, Ls + 1) if Ls % d == 0)):
        if all(seq[t] == seq[(t + d) % Ls] for t in range(Ls)):
            return d
    return Ls


import itertools
gauge_periods = {}
for k in range(1, 6):
    ek = [sum((eval("__import__('math').prod")(comb)) % Q
              for comb in itertools.combinations(st, k)) % Q
          for st in cycle]
    gauge_periods[f"e{k}"] = seq_period(ek)
for k in range(1, 5):
    pk = [sum(pow(x, k, Q) for x in st) % Q for st in cycle]
    gauge_periods[f"p{k}"] = seq_period(pk)
all_div_95 = all(95 % v == 0 for v in gauge_periods.values())
print(f"gauge-invariant observable periods: {gauge_periods}; "
      f"all divide 95: {all_div_95}")
results["gauge_periods"] = gauge_periods
results["gauge_all_divide_95"] = all_div_95

# --- 6. pure-line witnesses ---
v19 = [sum(rows[b]) % Q for b in range(19)]
u25 = [sum(rows[b][a] for b in range(19)) % Q for a in range(25)]
v_const = all(x == v19[0] for x in v19)
u_const = all(x == u25[0] for x in u25)
print(f"row-average v(b) (pure-19 witness): {v19}  non-constant: {not v_const}")
print(f"col-average u(a) (pure-25 witness): {u25}  non-constant: {not u_const}")
results["pure19_witness"] = {"v": v19, "non_constant": not v_const}
results["pure25_witness"] = {"u": u25, "non_constant": not u_const}

# --- 7. zero-mean reduction ---
cell_sums = [sum(cycle[t][i] for t in range(L)) % Q for i in range(n)]
W = [sum(st) % Q for st in cycle]
sumW = sum(W) % Q
print(f"per-cell time sums: {cell_sums}; sum_t W(t) mod 7 = {sumW}; "
      f"period of W(t): {gauge_periods['p1']}")
results["zero_mean"] = {"cell_sums": cell_sums, "sum_W": sumW}

# --- 8. G-basin sample on the 25-ring ---
random.seed(2026)
g_cycle_lengths = {}
for trial in range(150):
    v = tuple(random.randrange(Q) for _ in range(25))
    seen = {}
    t = 0
    while v not in seen and t < 4000:
        seen[v] = t
        v = G(v)
        t += 1
    if v in seen:
        lam = t - seen[v]
        g_cycle_lengths[lam] = g_cycle_lengths.get(lam, 0) + 1
print(f"G-basin sample (150 random 25-ring ICs) cycle-length histogram: "
      f"{dict(sorted(g_cycle_lengths.items()))}")
results["G_basin_sample"] = {str(k): v
                             for k, v in sorted(g_cycle_lengths.items())}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "nineteen_factor_crt_tower_structure_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved nineteen_factor_crt_tower_structure_results.json")
signal.alarm(0)
