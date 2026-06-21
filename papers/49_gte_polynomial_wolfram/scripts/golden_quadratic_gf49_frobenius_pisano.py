#!/usr/bin/env python3
"""GF(49) golden roots, Frobenius action, and the Pisano period mechanism.

Computes, in GF(49) = GF(7)[t]/(t^2-3):
 1. The roots of the master quadratic m(x)=x^2+x-1 (expected 3+-t) and of the
    Fibonacci characteristic polynomial f(x)=x^2-x-1 = m(-x) (expected 4+-t),
    verifying the exact reflection correspondence root(f) = -root(m).
 2. Frobenius x -> x^7: confirms it swaps each conjugate root pair and fixes
    GF(7) pointwise (so it cannot implement the dark-mirror w -> -w).
 3. Multiplicative orders of all four roots in GF(49)* (order 48).
 4. Diagonal fixed points of p over GF(49) (singleton invariant ethers).
 5. Pisano period pi(7) and the mechanism chain:
       pi(q) = ord of the Fibonacci matrix Q = [[1,1],[1,0]] in GL2(GF(q));
       for inert q, Q is conjugate over GF(q^2) to diag(phi, psi) with
       phi,psi the roots of f in GF(q^2), so pi(q) = lcm(ord(phi), ord(psi)).
    Verifies pi(7) = 16 = lcm of the orders computed in step 3.
 6. Null battery for the pi(7) = 16 = D^2 contact: computes pi(q) vs the
    classical bound 2(q+1) for all inert primes q < 200 (does pi attain the
    bound generically? counterexamples?), and tests the arithmetic reduction
    2(q+1) = (N_gen+1)^2 <=> N_gen = 3 at q = 2*N_gen+1.

Expected: roots 3+-t and 4+-t; Frobenius swaps; pi(7)=16=lcm(ord(4+t),ord(4-t));
pi(q)=2(q+1) for many but not all inert primes (q=47 expected counterexample).
"""
import os
import json
import signal
import sys

TIMEOUT_SECONDS = 300

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
# GF(49) elements as (a, b) = a + b*t with t^2 = 3 (3 is a non-square mod 7)

def gmul(x, y):
    a, b = x
    c, d = y
    return ((a * c + 3 * b * d) % Q, (a * d + b * c) % Q)

def gadd(x, y):
    return ((x[0] + y[0]) % Q, (x[1] + y[1]) % Q)

def gpow(x, n):
    r = (1, 0)
    while n:
        if n & 1:
            r = gmul(r, x)
        x = gmul(x, x)
        n >>= 1
    return r

def order(x):
    for n in range(1, 49):
        if gpow(x, n) == (1, 0):
            return n
    return None

ALL = [(a, b) for a in range(Q) for b in range(Q)]
results = {}

# 1. Roots of m and f in GF(49)
def m_eval(x):
    return gadd(gadd(gmul(x, x), x), (Q - 1, 0))

def f_eval(x):
    return gadd(gadd(gmul(x, x), (Q - x[0], (Q - x[1]) % Q)), (Q - 1, 0))

roots_m = [x for x in ALL if m_eval(x) == (0, 0)]
roots_f = [x for x in ALL if f_eval(x) == (0, 0)]
neg = lambda x: ((Q - x[0]) % Q, (Q - x[1]) % Q)
reflection_ok = sorted(roots_f) == sorted(neg(x) for x in roots_m)
print(f"1. roots of m=x^2+x-1 in GF(49): {roots_m}; roots of f=x^2-x-1: {roots_f}")
print(f"   reflection roots(f) = -roots(m): {reflection_ok}")
results["roots_m"] = roots_m
results["roots_f"] = roots_f
results["reflection_f_eq_m_neg"] = reflection_ok

# 2. Frobenius
frob = lambda x: gpow(x, Q)
frob_swaps_m = sorted(frob(x) for x in roots_m) == sorted(roots_m) and all(frob(x) != x for x in roots_m)
frob_fixes_base = all(frob((a, 0)) == (a, 0) for a in range(Q))
print(f"2. Frobenius swaps the two roots of m: {frob_swaps_m}; fixes GF(7) pointwise: {frob_fixes_base}")
results["frobenius"] = {"swaps_golden_roots": frob_swaps_m, "fixes_gf7_pointwise": frob_fixes_base}

# 3. Multiplicative orders
orders = {str(x): order(x) for x in roots_m + roots_f}
print(f"3. multiplicative orders in GF(49)*: {orders}")
results["orders"] = orders

# 4. Diagonal fixed points of p over GF(49): p(x,x,x)=x <=> x*(x^2+x-1)=0
diag_fps = [x for x in ALL if x == (0, 0) or m_eval(x) == (0, 0)]
# direct check via p
def p_diag(x):
    x2 = gmul(x, x)
    x3 = gmul(x2, x)
    v = gadd(gadd(gmul((2, 0), x), neg(x2)), neg(x3))
    return v

diag_direct = [x for x in ALL if p_diag(x) == x]
print(f"4. diagonal fixed points of p over GF(49): {sorted(diag_direct)} (matches 0 + roots(m): {sorted(diag_direct)==sorted(diag_fps)})")
results["gf49_diagonal_fixed_points"] = sorted(diag_direct)

# binary floor still invariant: p on {0,1}^3 stays in {0,1} (multilinear ext of R110)
def p_full(L, C, R):
    t1 = gadd(C, R)
    t2 = neg(gmul(C, R))
    t3 = neg(gmul(L, gmul(C, R)))
    return gadd(gadd(t1, t2), t3)

bin_ok = all(p_full(a, b, c) in [(0, 0), (1, 0)]
             for a in [(0, 0), (1, 0)] for b in [(0, 0), (1, 0)] for c in [(0, 0), (1, 0)])
print(f"   binary floor {{0,1}} invariant over GF(49): {bin_ok}")
results["gf49_binary_floor_invariant"] = bin_ok

# 5. Pisano period mechanism
def pisano(mod):
    a, b = 0, 1
    for i in range(1, 6 * mod * mod + 1):
        a, b = b, (a + b) % mod
        if a == 0 and b == 1:
            return i
    return None

pi7 = pisano(7)
phi_psi_orders = [order(x) for x in roots_f]
from math import lcm
lcm_orders = lcm(*phi_psi_orders)
print(f"5. pi(7) = {pi7}; ord(phi), ord(psi) in GF(49)* = {phi_psi_orders}; lcm = {lcm_orders}")
print(f"   mechanism pi(7) = lcm(ord(phi), ord(psi)): {pi7 == lcm_orders}")
results["pisano_mechanism"] = {"pi_7": pi7, "fib_root_orders": phi_psi_orders,
                               "lcm": lcm_orders, "match": pi7 == lcm_orders}

# 6. Null battery: pi(q) vs 2(q+1) for inert primes q < 200
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True

inert_scan = {}
attain, fail = [], []
for q in range(3, 200):
    if is_prime(q) and q % 5 in (2, 3):
        piq = pisano(q)
        bound = 2 * (q + 1)
        inert_scan[q] = {"pi": piq, "bound_2(q+1)": bound, "attains": piq == bound}
        (attain if piq == bound else fail).append(q)
print(f"6. inert primes q<200 attaining pi(q)=2(q+1): {attain}")
print(f"   NOT attaining (counterexamples to maximality): {fail}")
for q in fail:
    print(f"     q={q}: pi={inert_scan[q]['pi']} vs bound {inert_scan[q]['bound_2(q+1)']}")
results["pisano_inert_scan"] = inert_scan
results["pisano_maximality"] = {"attain": attain, "fail": fail}

# arithmetic reduction: 2(q+1) = (N+1)^2 has integer solution exactly N=3,q=7 among GTE-relevant
red = [(N, (N * N + 2 * N - 1) % 2 == 0 and (N * N + 2 * N - 1) // 2) for N in range(1, 10)]
# 2(q+1) = (N+1)^2  =>  q = ((N+1)^2 - 2)/2
qs = {N: ((N + 1) ** 2 - 2) / 2 for N in range(1, 10)}
print(f"   q solving 2(q+1)=(N+1)^2 for N=1..9: {qs}  (integer & prime only at N=3 -> q=7? check)")
results["d_squared_reduction"] = {str(N): qs[N] for N in qs}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "golden_quadratic_gf49_frobenius_pisano_results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
print("Saved golden_quadratic_gf49_frobenius_pisano_results.json")
signal.alarm(0)
