#!/usr/bin/env python3
"""Exact monodromy charpolys of GTE polynomial CA cycles vs the master quadratic.

Supersedes the charpoly computation in golden_quadratic_monodromy_spectrum.py,
whose Lagrange interpolation aliased degree-7 characteristic polynomials mod
(x^7 - x) on the n=7 ring (only 7 evaluation points exist in GF(7)). Here the
characteristic polynomial det(xI - M) is computed exactly over the integers
(sympy Berkowitz) and then reduced mod 7 -- valid for any matrix size.

Tests (as before):
 1. n=5 period-475 attractor monodromy: does m(x) = x^2+x-1 divide cp mod 7?
 2. n=7 glider/chaotic cycles (L = 14, 21, 49, 189, 602): same test.
 3. Null battery: 20 random multilinear rules aC+bR+cCR+dLCR on the n=5 ring.

Expected output: exact factorized charpolys and divisibility verdicts; the
n=5 result must reproduce spectrum {0,0,0,4,4} = x^3 (x-4)^2 as cross-check.
"""
import os
import json
import random
import signal
import sys

import sympy as sp

TIMEOUT_SECONDS = 900

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
x = sp.symbols('x')

def step(state, coeffs=(1, 1, -1, -1)):
    a, b, c, d = coeffs
    n = len(state)
    return tuple((a * state[i] + b * state[(i + 1) % n]
                  + c * state[i] * state[(i + 1) % n]
                  + d * state[(i - 1) % n] * state[i] * state[(i + 1) % n]) % Q
                 for i in range(n))

def jacobian(state, coeffs=(1, 1, -1, -1)):
    a, b, c, d = coeffs
    n = len(state)
    J = [[0] * n for _ in range(n)]
    for i in range(n):
        L, C, R = state[(i - 1) % n], state[i], state[(i + 1) % n]
        J[i][(i - 1) % n] = (d * C * R) % Q
        J[i][i] = (a + c * R + d * L * R) % Q
        J[i][(i + 1) % n] = (b + c * C + d * L * C) % Q
    return J

def matmul(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) % Q for j in range(n)]
            for i in range(n)]

def find_cycle(start, coeffs=(1, 1, -1, -1), max_steps=20000):
    seen = {}
    s = start
    for t in range(max_steps):
        if s in seen:
            mu = seen[s]
            return list(seen.keys())[mu:], mu
        seen[s] = t
        s = step(s, coeffs)
    return None, None

def monodromy(cycle, coeffs=(1, 1, -1, -1)):
    n = len(cycle[0])
    M = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for s in cycle:
        M = matmul(jacobian(s, coeffs), M)
    return M

def charpoly_mod7(M):
    cp = sp.Matrix(M).charpoly(x).as_expr()
    poly = sp.Poly(cp, x, modulus=Q)
    return poly

M_POLY = sp.Poly(x**2 + x - 1, x, modulus=Q)
F_POLY = sp.Poly(x**2 - x - 1, x, modulus=Q)

def analyze(M):
    cp = charpoly_mod7(M)
    fac = sp.factor_list(cp.as_expr(), x, modulus=Q)
    fac_str = " * ".join(f"({sp.sstr(f)})^{m}" for f, m in fac[1])
    div_m = sp.rem(cp.as_expr(), M_POLY.as_expr(), x, modulus=Q) == 0
    div_f = sp.rem(cp.as_expr(), F_POLY.as_expr(), x, modulus=Q) == 0
    return {"charpoly_mod7": sp.sstr(cp.as_expr()), "factorization": fac_str,
            "master_quadratic_divides": bool(div_m),
            "fibonacci_quadratic_divides": bool(div_f)}

results = {"supersedes": "golden_quadratic_monodromy_spectrum.py (n=7 charpolys aliased)"}
GTE = (1, 1, -1, -1)

# --- 1. n=5 period-475 ---
random.seed(11)
cyc475 = None
for _ in range(50):
    s0 = tuple(random.randrange(Q) for _ in range(5))
    cyc, mu = find_cycle(s0, GTE)
    if cyc and len(cyc) == 475:
        cyc475 = cyc
        break
assert cyc475 is not None
res = analyze(monodromy(cyc475, GTE))
res["cycle_length"] = 475
results["n5_period475"] = res
print(f"1. n=5 L=475: {res['factorization']}  m|cp: {res['master_quadratic_divides']}  f|cp: {res['fibonacci_quadratic_divides']}")

# --- 2. n=7 cycles ---
results["n7_cycles"] = {}
random.seed(7)
found = {}
attempts = 0
while len(found) < 5 and attempts < 300000:
    attempts += 1
    s0 = tuple(random.randrange(Q) for _ in range(7))
    cyc, mu = find_cycle(s0, GTE)
    if cyc:
        L = len(cyc)
        if L in (14, 21, 49, 189, 602) and L not in found:
            found[L] = cyc
for L in sorted(found):
    res = analyze(monodromy(found[L], GTE))
    results["n7_cycles"][L] = res
    print(f"2. n=7 L={L}: {res['factorization']}  m|cp: {res['master_quadratic_divides']}  f|cp: {res['fibonacci_quadratic_divides']}")

# --- 3. Null battery (n=5, exact method) ---
random.seed(42)
hits_m = hits_f = total = 0
rows = []
while total < 20:
    coeffs = tuple(random.randrange(Q) for _ in range(4))
    if coeffs == (1, 1, 6, 6) or all(c == 0 for c in coeffs):
        continue
    s0 = tuple(random.randrange(Q) for _ in range(5))
    cyc, mu = find_cycle(s0, coeffs)
    if not cyc or len(cyc) < 2:
        continue
    res = analyze(monodromy(cyc, coeffs))
    hits_m += res["master_quadratic_divides"]
    hits_f += res["fibonacci_quadratic_divides"]
    total += 1
    rows.append({"coeffs": coeffs, "cycle_len": len(cyc),
                 "m_divides": res["master_quadratic_divides"],
                 "f_divides": res["fibonacci_quadratic_divides"],
                 "factorization": res["factorization"]})
results["null_battery"] = {"n_rules": total, "m_hits": hits_m, "f_hits": hits_f, "rows": rows}
print(f"3. null battery: m divides {hits_m}/20, f divides {hits_f}/20")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "golden_quadratic_monodromy_charpoly_exact_results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
print("Saved golden_quadratic_monodromy_charpoly_exact_results.json")
signal.alarm(0)
