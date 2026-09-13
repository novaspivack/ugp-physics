#!/usr/bin/env python3
"""Linearization no-go for the 19-factor of the period-475 attractor.

Every cycle point s is a fixed point of the global map F = sigma^2 T^95
(= R^19, R = sigma^3 T^5 the drift-cancelled return map). This script:

 1. Computes the exact 475-step monodromy charpoly (cross-check vs the R01
    exact result x^3 (x-4)^2).
 2. Computes DF(s) = P^2 . J(s_94)...J(s_0) at every cycle point s, verifies
    the chain-rule identity [DF(s)]^5 = D(T^475)(s), and the charpoly of DF.
 3. Factors charpoly(DF) over GF(7) and computes the multiplicative order of
    every nonzero root in its splitting field (order of x mod the irreducible
    factor). Verdict: all orders divide 15 (=> lie in mu_15 in GF(7^4)*);
    NO root of order 19 exists.
 4. Verifies charpoly constancy along R-orbits (conjugacy invariance).

Expected: orders subset of divisors of 15; no order-19 eigenvalue; the
no-go verdict for the tangent-level GF(7^3) mechanism.
"""
import os
import json
import signal
import sys
from math import gcd

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


def jac(s):
    """Jacobian of T at s: row i = grad of s'_i wrt (s_0..s_4).
    s'_i = p(L,C,R) with L = s_{i-1}, C = s_i, R = s_{i+1};
    dp/dL = -CR, dp/dC = 1 - R - LR, dp/dR = 1 - C - LC."""
    M = [[0] * n for _ in range(n)]
    for i in range(n):
        L, C, R = s[(i - 1) % n], s[i], s[(i + 1) % n]
        M[i][(i - 1) % n] = (-C * R) % Q
        M[i][i] = (1 - R - L * R) % Q
        M[i][(i + 1) % n] = (1 - C - L * C) % Q
    return M


def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(n)) % Q for j in range(n)]
            for i in range(n)]


def matpow(A, e):
    Rm = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    while e:
        if e & 1:
            Rm = matmul(Rm, A)
        A = matmul(A, A)
        e >>= 1
    return Rm


# sigma shift convention: shift(s,1)[i] = s[i+1]; D(sigma^c) = permutation P^c
# with (P x)_i = x_{i+1}  =>  P[i][j] = 1 iff j = i+1 mod n.
def perm(c):
    return [[1 if j == (i + c) % n else 0 for j in range(n)] for i in range(n)]


# --- locate cycle ---
import random
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
        wst = step(s)
        while wst != s:
            c.append(wst)
            wst = step(wst)
        cycle = c
L = len(cycle)
assert L == 475
results = {}

x = sp.symbols('x')


def charpoly_mod7(M):
    Ms = sp.Matrix(M)
    cp = Ms.charpoly(x).as_expr()
    return sp.Poly(cp, x, modulus=Q)


def root_orders(poly):
    """Orders of nonzero roots of each irreducible factor f: order of x in
    GF(7)[x]/(f). Returns list of (degree, order) per nonzero-root factor."""
    out = []
    for fac, mult in sp.factor_list(poly, modulus=Q)[1]:
        fp = sp.Poly(fac, x, modulus=Q)
        k = fp.degree()
        if fp.eval(0) % Q == 0 and k == 1:
            out.append((1, 0, mult))  # root 0 (nilpotent direction)
            continue
        field_order = Q ** k - 1
        # order of x modulo fp
        o = field_order
        for pr in set(sp.factorint(field_order)):
            while o % pr == 0:
                cand = o // pr
                xc = sp.Poly(x, x, modulus=Q)
                if sp.rem(xc ** cand, fp, modulus=Q) == sp.Poly(1, x, modulus=Q):
                    o = cand
                else:
                    break
        out.append((k, int(o), mult))
    return out


# --- 1. full 475 monodromy ---
M475 = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
st = cycle[0]
for t in range(L):
    M475 = matmul(jac(st), M475)
    st = step(st)
cp475 = charpoly_mod7(M475)
print(f"475-monodromy charpoly mod 7: {sp.factor(cp475.as_expr(), modulus=Q)}")
results["monodromy_475_charpoly"] = str(sp.factor(cp475.as_expr(), modulus=Q))

# --- 2./3. DF at every cycle point ---
P2 = perm(2)
charpolys = {}
orders_seen = set()
fifth_power_ok = True
idx = {stt: i for i, stt in enumerate(cycle)}
DFs = {}
for i0 in range(L):
    Macc = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    st = cycle[i0]
    for t in range(95):
        Macc = matmul(jac(st), Macc)
        st = step(st)
    DF = matmul(P2, Macc)
    DFs[i0] = DF
    # fifth-power identity at this point: [DF]^5 = D(T^475)(s)
    M475_i = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    st = cycle[i0]
    if i0 % 25 == 0:  # exact heavy check on 19 sample points
        for t in range(L):
            M475_i = matmul(jac(st), M475_i)
            st = step(st)
        if matpow(DF, 5) != M475_i:
            fifth_power_ok = False
    cp = charpoly_mod7(DF)
    key = str(sp.factor(cp.as_expr(), modulus=Q))
    charpolys[key] = charpolys.get(key, 0) + 1
    if i0 < L:  # orders for all distinct charpolys (cache by key)
        pass
print(f"[DF]^5 = D(T^475) verified at 19 sample points: {fifth_power_ok}")
print(f"distinct charpolys of DF along the cycle ({len(charpolys)}):")
order_table = {}
any19 = False
max_ord = 0
for key in charpolys:
    poly = sp.Poly(sp.sympify(key.replace('^', '**')), x, modulus=Q)
    ro = root_orders(poly)
    order_table[key] = ro
    for (k, o, mult) in ro:
        orders_seen.add(o)
        if o == 19:
            any19 = True
        max_ord = max(max_ord, o)
    print(f"  {key}  (x{charpolys[key]})  root (deg, order, mult): {ro}")
all_div_15 = all(o == 0 or 15 % o == 0 for o in orders_seen)
print(f"eigenvalue orders seen: {sorted(orders_seen)}; all divide 15: "
      f"{all_div_15}; any order-19 eigenvalue: {any19}")

# --- 4. conjugacy invariance along R-orbits ---
def cp_key(i0):
    cp = charpoly_mod7(DFs[i0])
    return str(sp.factor(cp.as_expr(), modulus=Q))


r_invariant = all(cp_key(i0) == cp_key((i0 + 100) % L) for i0 in range(0, L, 19))
print(f"charpoly constant along R-orbits (sampled): {r_invariant}")

results["DF_charpolys"] = {k: {"count": v, "root_orders": order_table[k]}
                           for k, v in charpolys.items()}
results["fifth_power_identity"] = fifth_power_ok
results["eigenvalue_orders"] = sorted(orders_seen)
results["all_orders_divide_15"] = all_div_15
results["any_order_19"] = any19
results["R_orbit_charpoly_invariant"] = r_invariant
results["verdict"] = ("NO-GO: no order-19 eigenvalue at any return-map "
                      "linearization; tangent torsion divides 15 (mu_15 in "
                      "GF(7^4)*)") if (not any19 and all_div_15) else "CHECK"
print(f"VERDICT: {results['verdict']}")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "nineteen_factor_linearization_no_go_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved nineteen_factor_linearization_no_go_results.json")
signal.alarm(0)
