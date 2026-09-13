#!/usr/bin/env python3
"""GF(7^3) mechanism test for the 19-factor of the period-475 attractor.

The 5-cell GF(7) ring under p has a unique period-475 = 5^2 x 19 attractor
(CatAL: period_475_returns / period_475_is_minimal). This script tests the
linear-algebraic structure of the attractor:

 1. sigma = T^m identification on the cycle (m must be a multiple of 95).
 2. Affine hull dimension of the 475 cycle states in GF(7)^5.
 3. Exact affine-model consistency: is T (or T^5, T^19, T^25) affine-linear
    when restricted to the cycle? (Solve the exact linear systems mod 7.)
 4. Berlekamp-Massey over GF(7) on cell sequences c_i(t) and random linear
    functionals of s_t: linear complexity + minimal polynomial.
 5. Factor the minimal polynomial mod 7 and classify irreducible factor
    degrees. Degree-3 factors = pure period-19 components carried by GF(7^3)
    (ord_19(7) = 3). Degree-4 = period-5/25 (GF(7^4)); degree-12 = period
    95/475 (GF(7^12) compositum).

Expected output: m, hull dimension, affine consistency verdicts, linear
complexity, factor-degree profile, and the GF(7^3)-resonance verdict.
"""
import os
import json
import random
import signal
import sys

import sympy as sp

TIMEOUT_SECONDS = 900
signal.signal(signal.SIGALRM, lambda s, f: sys.exit("TIMEOUT"))
signal.alarm(TIMEOUT_SECONDS)

Q, n = 7, 5

def step(s):
    return tuple((s[i] + s[(i + 1) % n] - s[i] * s[(i + 1) % n]
                  - s[(i - 1) % n] * s[i] * s[(i + 1) % n]) % Q
                 for i in range(n))

def shift(s, j):
    return tuple(s[(i + j) % n] for i in range(n))

# --- locate the 475-cycle ---
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

# --- 1. sigma = T^m on the cycle ---
m = (idx[shift(cycle[0], 1)] - 0) % L
ok_all = all(idx[shift(cycle[i], 1)] == (i + m) % L for i in range(L))
print(f"sigma = T^{m} on the cycle (consistent for all states: {ok_all}); "
      f"m % 95 = {m % 95}")
results["sigma_eq_T_pow_m"] = {"m": m, "consistent": ok_all,
                               "m_mod_95": m % 95}

# --- 2. affine hull dimension over GF(7) ---
def mat_rank_mod7(rows):
    A = [list(r) for r in rows]
    rank, cols = 0, len(A[0]) if A else 0
    r = 0
    for c in range(cols):
        piv = next((i for i in range(r, len(A)) if A[i][c] % Q), None)
        if piv is None:
            continue
        A[r], A[piv] = A[piv], A[r]
        inv = pow(A[r][c], Q - 2, Q)
        A[r] = [(x * inv) % Q for x in A[r]]
        for i in range(len(A)):
            if i != r and A[i][c] % Q:
                f = A[i][c]
                A[i] = [(A[i][k] - f * A[r][k]) % Q for k in range(cols)]
        r += 1
        if r == len(A):
            break
    return r

diffs = [[(cycle[t][k] - cycle[0][k]) % Q for k in range(n)]
         for t in range(1, L)]
hull_dim = mat_rank_mod7(diffs)
print(f"affine hull dimension of the cycle in GF(7)^5: {hull_dim}")
results["affine_hull_dim"] = hull_dim

# --- 3. affine model consistency for T^e on the cycle ---
def affine_consistent(e):
    """Is s -> T^e(s) restricted to the cycle an affine map A s + b?"""
    # unknowns per output coord: 5 matrix entries + 1 offset = 6
    # build system rows: [s_t, 1] -> target coord; solve via rank test
    rows = []
    rhs_all = [[] for _ in range(n)]
    for t in range(L):
        src = list(cycle[t]) + [1]
        tgt = cycle[(t + e) % L]
        rows.append(src)
        for k in range(n):
            rhs_all[k].append(tgt[k])
    # consistency: rank([A]) == rank([A|b]) for each coordinate
    base_rank = mat_rank_mod7(rows)
    for k in range(n):
        aug = [rows[t] + [rhs_all[k][t]] for t in range(L)]
        if mat_rank_mod7(aug) != base_rank:
            return False
    return True

aff = {}
for e in (1, 5, 19, 25, 95):
    aff[e] = affine_consistent(e)
    print(f"T^{e} restricted to the cycle is affine-linear: {aff[e]}")
results["affine_consistency"] = {str(k): v for k, v in aff.items()}

# --- 4. Berlekamp-Massey over GF(7) ---
def berlekamp_massey_gf(seq, q):
    C = [1]; B = [1]; Lc = 0; mm = 1; b = 1
    for nn in range(len(seq)):
        d = seq[nn]
        for i in range(1, Lc + 1):
            d = (d + C[i] * seq[nn - i]) % q
        if d == 0:
            mm += 1
        elif 2 * Lc <= nn:
            T = C[:]
            coef = (d * pow(b, q - 2, q)) % q
            C = C + [0] * (len(B) + mm - len(C))
            for i in range(len(B)):
                C[i + mm] = (C[i + mm] - coef * B[i]) % q
            Lc = nn + 1 - Lc; B = T; b = d; mm = 1
        else:
            coef = (d * pow(b, q - 2, q)) % q
            C = C + [0] * (len(B) + mm - len(C))
            for i in range(len(B)):
                C[i + mm] = (C[i + mm] - coef * B[i]) % q
            mm += 1
    return Lc, C  # C(x) = 1 + c1 x + ... (connection polynomial)

x = sp.symbols('x')
random.seed(19)
functionals = ([tuple(1 if k == i else 0 for k in range(n)) for i in range(n)]
               + [tuple(random.randrange(Q) for _ in range(n))
                  for _ in range(3)])
bm_rows = []
factor_degree_union = set()
deg3_present = False
for f_idx, lam in enumerate(functionals):
    seq = [sum(lam[k] * cycle[t][k] for k in range(n)) % Q
           for t in range(L)] * 2  # two periods for BM stability
    Lc, C = berlekamp_massey_gf(seq, Q)
    # minimal polynomial = x^Lc * C(1/x) reversed
    coeffs = list(reversed(C[:Lc + 1]))
    poly = sp.Poly(coeffs, x, modulus=Q)
    fl = sp.factor_list(poly, modulus=Q)
    degs = sorted(sp.Poly(fac, x, modulus=Q).degree()
                  for fac, mult in fl[1] for _ in range(mult))
    factor_degree_union.update(degs)
    if 3 in degs:
        deg3_present = True
    name = f"cell_{f_idx}" if f_idx < n else f"rand_{f_idx - n}"
    bm_rows.append({"functional": name, "lambda": list(lam),
                    "linear_complexity": Lc, "factor_degrees": degs})
    print(f"{name}: linear complexity {Lc}, factor degrees {degs}")

results["berlekamp_massey"] = bm_rows
results["factor_degree_union"] = sorted(factor_degree_union)
results["pure_gf73_component_present"] = deg3_present

# --- 5. classification of x^475 - 1 over GF(7) for reference ---
ords = {}
for d in (1, 5, 19, 25, 95, 475):
    k = 1
    while pow(7, k, d if d > 1 else 2) != 1 % (d if d > 1 else 2):
        k += 1
        if k > 500:
            break
    ords[d] = k if d > 1 else 1
print(f"\nord_d(7) for divisors d of 475: {ords}")
print(f"degree-3 (pure GF(7^3) / period-19) component present in orbit: "
      f"{deg3_present}")
results["ord_7_mod_divisors"] = {str(k): v for k, v in ords.items()}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "gte_zeta_period475_linear_structure_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved gte_zeta_period475_linear_structure_results.json")
signal.alarm(0)
