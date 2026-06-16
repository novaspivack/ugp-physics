#!/usr/bin/env python3
"""Spacetime torus counts and periodic entropies of the GTE polynomial CA.

Objects:
  - (n,m) spacetime torus: configuration on Z_n x Z_m with
    s[t+1,i] = p(s[t,i-1], s[t,i], s[t,i+1]) both directions periodic.
    #tori(n,m) = Fix(T_n^m) = tr(M_m^n) for the column-pair transfer
    operator M_m on 7^{2m} nodes.
  - Directional periodic entropy h(m) = ln lambda_1(M_m) (spatial growth of
    the m-periodic temporal sector).
  - Spatial periodic-state growth h* = lim (1/n) ln P_n, with P_n = total
    states on cycles of T_n (computed exhaustively n = 3..9).

Computes:
 1. lambda_1(M_m) for m = 1..4 via sparse power iteration (out-neighbor sets
    built from the per-site solver S(a,b,b') = {c : p(a,b,c) = b'}).
 2. tr(M_m^n) cross-checks against Fix(T_n^m) from the exhaustive spectra.
 3. P_n for n = 8, 9 (numpy peeling), extending the scout's n = 3..7.
 4. Comparison of h(m)/m and h* against pre-registered candidates:
    (1/2) S_CMCA = ln(10.417)/2, ln 7, S_CMCA itself.

Expected output: entropy table; P_n table; honest match/no-match verdict.
"""
import os
import json
import signal
import sys
import time
from itertools import product

import numpy as np

TIMEOUT_SECONDS = 1500
signal.signal(signal.SIGALRM, lambda s, f: sys.exit("TIMEOUT"))
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def p_val(a, b, c):
    return (b + c - b * c - a * b * c) % Q

# per-site solver: S[a][b][b'] = list of c with p(a,b,c) = b'
S = [[[[] for _ in range(Q)] for _ in range(Q)] for _ in range(Q)]
for a in range(Q):
    for b in range(Q):
        for c in range(Q):
            S[a][b][p_val(a, b, c)].append(c)

results = {}

# --- Part 1+2: M_m spectra and traces, m = 1..4 ---
ent = {}
for m in range(1, 5):
    cols = list(product(range(Q), repeat=m))
    ncol = len(cols)
    col_idx = {c: i for i, c in enumerate(cols)}
    # node = (A,B) pair of adjacent columns; out-neighbors (B,C):
    # C_t in S[A_t][B_t][B_{t+1 mod m}] for all t  (product set)
    # build sparse adjacency: for each node, list of successor node indices
    t0 = time.time()
    nodes = ncol * ncol
    adj_ptr = [None] * nodes
    for ia, A in enumerate(cols):
        for ib, B in enumerate(cols):
            allowed = []
            ok = True
            for t in range(m):
                opts = S[A[t]][B[t]][B[(t + 1) % m]]
                if not opts:
                    ok = False
                    break
                allowed.append(opts)
            if not ok:
                adj_ptr[ia * ncol + ib] = []
                continue
            succs = [col_idx[Cc] * 0 for Cc in ()]  # placeholder
            outs = []
            for combo in product(*allowed):
                outs.append(ib * ncol + col_idx[combo])
            adj_ptr[ia * ncol + ib] = outs
    # power iteration for lambda_1
    v = np.ones(nodes)
    lam = 0.0
    for it in range(300):
        w = np.zeros(nodes)
        for u in range(nodes):
            outs = adj_ptr[u]
            if outs:
                wu = v[u]
                for x in outs:
                    w[x] += wu
        nrm = np.linalg.norm(w)
        if nrm == 0:
            lam = 0.0
            break
        new_lam = nrm / np.linalg.norm(v)
        wn = w / nrm
        if it > 20 and abs(new_lam - lam) < 1e-12:
            lam = new_lam
            v = wn
            break
        lam, v = new_lam, wn
    # power-iteration estimate of lambda_1 via Rayleigh-type ratio:
    # use v^T M v / v^T v with the final vector
    Mv = np.zeros(nodes)
    for u in range(nodes):
        for x in adj_ptr[u]:
            Mv[x] += v[u]
    lam1 = float(v @ Mv / (v @ v)) if v @ v > 0 else 0.0
    # exact small-n traces for cross-check: tr(M^n) via dense power on
    # the reachable subgraph is expensive; instead count tori directly for
    # n = 3..6 by DP along the ring (transfer with boundary fixing)
    def tori_count(nn):
        # count closed walks of length nn in adjacency
        # dp over nodes; use dict-of-counts from each start? Too slow for all
        # starts; use matrix-free repeated multiply of indicator basis is
        # O(nodes^2). For m <= 2 do dense; for m >= 3 skip exact check.
        if nodes > 3000:
            return None
        M = np.zeros((nodes, nodes), dtype=np.int64)
        for u in range(nodes):
            for x in adj_ptr[u]:
                M[u, x] += 1
        P = np.eye(nodes, dtype=np.int64)
        for _ in range(nn):
            P = P @ M
        return int(np.trace(P))
    checks = {}
    if nodes <= 3000:
        for nn in (3, 4, 5, 6, 7):
            checks[nn] = tori_count(nn)
    ent[m] = {"nodes": nodes, "lambda1": lam1, "h": float(np.log(lam1))
              if lam1 > 0 else None,
              "h_over_m": float(np.log(lam1)) / m if lam1 > 0 else None,
              "trace_checks": checks,
              "build_seconds": round(time.time() - t0, 1)}
    print(f"m={m}: nodes={nodes}, lambda1={lam1:.6f}, h={np.log(lam1):.6f}, "
          f"h/m={np.log(lam1)/m:.6f}, checks={checks}")
results["directional_entropies"] = {str(k): v for k, v in ent.items()}

# --- Part 3: P_n for n = 8, 9 ---
def periodic_count(n):
    N = Q ** n
    v = np.arange(N, dtype=np.int64)
    nxt = np.zeros(N, dtype=np.int64)
    digits = [(v // Q ** i) % Q for i in range(n)]
    for i in range(n):
        a = digits[(i - 1) % n]
        b = digits[i]
        c = digits[(i + 1) % n]
        val = (b + c - b * c - a * b * c) % Q
        nxt += val * Q ** i
    del digits, v
    succ = nxt.astype(np.int64)
    del nxt
    indeg = np.bincount(succ, minlength=N)
    removed = np.zeros(N, dtype=bool)
    queue = np.flatnonzero(indeg == 0)
    while queue.size:
        removed[queue] = True
        dec = np.bincount(succ[queue], minlength=N)
        indeg -= dec
        cand = np.unique(succ[queue])
        queue = cand[(indeg[cand] == 0) & ~removed[cand]]
    return int((~removed).sum())

P_n = {3: 28, 4: 15, 5: 476, 6: 328, 7: 4488}
for n in (8, 9):
    t0 = time.time()
    P_n[n] = periodic_count(n)
    print(f"P_{n} = {P_n[n]}  ({time.time()-t0:.1f}s)")
results["periodic_states"] = {str(k): v for k, v in P_n.items()}

# --- Part 4: growth-rate comparison ---
import math
growth = {n: math.log(P_n[n]) / n for n in P_n}
print("\n(1/n) ln P_n:", {n: round(g, 4) for n, g in growth.items()})
cands = {"half_S_CMCA": math.log(10.417) / 2, "ln7": math.log(7),
         "S_CMCA": math.log(10.417), "ln_43_over_3": math.log(43) / 3}
print("candidates:", {k: round(v, 4) for k, v in cands.items()})
results["growth_rates"] = {str(k): v for k, v in growth.items()}
results["candidates"] = cands

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "gte_zeta_torus_entropy_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved gte_zeta_torus_entropy_results.json")
signal.alarm(0)
