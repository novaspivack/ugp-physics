#!/usr/bin/env python3
"""Vacuum-uniqueness theorem for the GTE polynomial via the golden Moebius map.

Verifies, over GF(q) for many primes q, the chain:
  temporal fixed points of T_n (rule p = C+R-CR-LCR on the n-ring)
    <-> closed, infinity-avoiding orbits of the Moebius map mu(x) = (1+x)^{-1}
        on P^1(GF(q)), whose fixed-point equation is the golden quadratic
        x^2 + x - 1 = 0 (disc 5) and whose matrix is Fibonacci [[0,1],[1,1]].

Method notes:
 - The all-n uniqueness property is exactly: the de Bruijn fixed-point digraph
   (nodes (a,b), edge (a,b)->(b,c) iff f(a,b,c) = b) has no directed cycle
   other than the vacuum self-loop at (0,0). Fixed ring configurations of any
   size n = closed walks of length n. Checked by cycle detection (DFS) after
   removing (0,0). Exact for ALL n simultaneously.
 - mu-orbit prediction Fix(T_n) = 1 + sum_{INF-free mu-orbits of length d | n} d
   is cross-checked against brute-force enumeration on small rings.

Checks:
 1. q=7: mu is a single 8-cycle on P^1; digraph acyclic off vacuum =>
    Fix(T_n) = 1 for ALL n; brute force n=3..6 cross-check.
 2. General q in {3,5,11,13,17,19,23,29,31,37,41,43}: mu orbit structure,
    Legendre (5|q), Pisano pi(q), digraph verdict, brute force n=3 (and n=4
    for q<=23) vs prediction.
 3. Null: for the 30 random GF(7) rules of cycle_spectrum_null_battery.py
    (same seed), the all-n unique-fixed-point rate via the digraph test.

Expected output: q=7 single 8-cycle + acyclic verdict; per-q table; null count.
"""
import os
import json
import signal
import sys
from itertools import product

TIMEOUT_SECONDS = 600

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)


def legendre(a, p):
    a %= p
    if a == 0:
        return 0
    return 1 if pow(a, (p - 1) // 2, p) == 1 else -1


def pisano(m):
    a, b, k = 0, 1, 0
    while True:
        a, b = b, (a + b) % m
        k += 1
        if (a, b) == (0, 1):
            return k


def mu_orbits(q):
    INF = q
    def mu(x):
        if x == INF:
            return 0
        d = (1 + x) % q
        if d == 0:
            return INF
        return pow(d, q - 2, q)
    seen = set()
    orbits = []
    for x in list(range(q)) + [INF]:
        if x in seen:
            continue
        orb = [x]
        y = mu(x)
        while y != x:
            orb.append(y)
            y = mu(y)
        seen.update(orb)
        orbits.append(orb)
    return orbits, INF


def rule_eval(coeffs, q, a, b, c):
    a1, a2, a3, a4, a5, a6, a7 = coeffs
    return (a1 * a + a2 * b + a3 * c + a4 * a * b + a5 * a * c
            + a6 * b * c + a7 * a * b * c) % q


def digraph_cycles_off_vacuum(coeffs, q):
    """True iff the fixed-point de Bruijn digraph has a cycle besides (0,0) loop."""
    adj = {}
    for a in range(q):
        for b in range(q):
            outs = [c for c in range(q) if rule_eval(coeffs, q, a, b, c) == b]
            adj[(a, b)] = [(b, c) for c in outs]
    # remove vacuum node, detect any directed cycle among the rest
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {v: WHITE for v in adj if v != (0, 0)}
    sys.setrecursionlimit(10000)
    def dfs(v):
        color[v] = GRAY
        for w in adj[v]:
            if w == (0, 0):
                continue
            if color[w] == GRAY:
                return True
            if color[w] == WHITE and dfs(w):
                return True
        color[v] = BLACK
        return False
    return any(color[v] == WHITE and dfs(v) for v in list(color))


def brute_fix(coeffs, q, n):
    """Brute-force count of temporal fixed ring configurations."""
    cnt = 0
    for s in product(range(q), repeat=n):
        ok = all(rule_eval(coeffs, q, s[(i - 1) % n], s[i], s[(i + 1) % n])
                 == s[i] for i in range(n))
        cnt += ok
    return cnt


def p_coeffs(q):
    return (0, 1, 1, 0, 0, (q - 1) % q, (q - 1) % q)


results = {}

# --- Part 1: q = 7 ---
orbits, INF = mu_orbits(7)
single = len(orbits) == 1
has_extra_cycles = digraph_cycles_off_vacuum(p_coeffs(7), 7)
bf = {n: brute_fix(p_coeffs(7), 7, n) for n in range(3, 7)}
print(f"q=7: mu orbit lengths = {[len(o) for o in orbits]} (single cycle: {single})")
print(f"q=7: de Bruijn digraph has non-vacuum cycle: {has_extra_cycles}"
      f" => Fix(T_n)=1 for ALL n: {not has_extra_cycles}")
print(f"q=7: brute-force Fix(T_n) n=3..6: {bf}")
results["q7"] = {"mu_orbit_lengths": [len(o) for o in orbits],
                 "mu_single_cycle": single,
                 "legendre_5_q": legendre(5, 7), "pisano": pisano(7),
                 "pisano_eq_2qplus2": pisano(7) == 16,
                 "unique_fixed_point_all_n": not has_extra_cycles,
                 "brute_force_fix_n3_6": bf}

# --- Part 2: general q ---
table = {}
for q in (3, 5, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43):
    orbits, INF = mu_orbits(q)
    lens = sorted(len(o) for o in orbits)
    inf_free = sorted(len(o) for o in orbits if INF not in o)
    leg, pis = legendre(5, q), pisano(q)
    extra = digraph_cycles_off_vacuum(p_coeffs(q), q)
    pred3 = 1 + sum(d for d in inf_free if 3 % d == 0)
    bf3 = brute_fix(p_coeffs(q), q, 3)
    row = {"legendre_5_q": leg, "pisano": pis,
           "pisano_eq_2qplus2": pis == 2 * (q + 1),
           "mu_orbit_lengths": lens, "inf_free_orbit_lengths": inf_free,
           "unique_fixed_point_all_n": not extra,
           "pred_fix_n3": pred3, "brute_fix_n3": bf3,
           "pred_matches_n3": pred3 == bf3}
    if q <= 23:
        pred4 = 1 + sum(d for d in inf_free if 4 % d == 0)
        bf4 = brute_fix(p_coeffs(q), q, 4)
        row.update({"pred_fix_n4": pred4, "brute_fix_n4": bf4,
                    "pred_matches_n4": pred4 == bf4})
    table[q] = row
    print(f"q={q:2d}: (5|q)={leg:+d} pi(q)={pis:4d} 2(q+1)={2*(q+1):4d} "
          f"orbits={lens} inf-free={inf_free} uniq-all-n={not extra} "
          f"Fix(T_3) pred/bf={pred3}/{bf3}"
          + (f" Fix(T_4) pred/bf={row['pred_fix_n4']}/{row['brute_fix_n4']}"
             if q <= 23 else ""))
results["general_q"] = table

# --- Part 2b: orbit-only classification scan, all odd primes q < 200 ---
# Exact criterion under test: with alpha a root of the Fibonacci polynomial
# x^2 - x - 1 and ord(alpha) = pi(q) (Pisano), the projective order of the
# Moebius map is d0 = pi(q) / gcd(pi(q), q - 1)   [cyclic-subgroup
# intersection |<alpha> cap GF(q)*| = gcd(pi(q), q-1)].
# Unique-fixed-point-for-all-n  <=>  (5|q) = -1  AND  d0 = q + 1
# (single (q+1)-cycle through INF on P^1).
from math import gcd

def is_prime(m):
    if m < 2:
        return False
    return all(m % d for d in range(2, int(m ** 0.5) + 1))

scan = {}
pattern_holds = True
for q in [m for m in range(3, 200) if is_prime(m) and m != 5]:
    orbits, INF = mu_orbits(q)
    lens = sorted(len(o) for o in orbits)
    inf_free = sorted(len(o) for o in orbits if INF not in o)
    leg = legendre(5, q)
    uniq = len(inf_free) == 0
    pis = pisano(q)
    d0 = pis // gcd(pis, q - 1)
    predicted_uniq = (leg == -1) and (d0 == q + 1)
    if predicted_uniq != uniq:
        pattern_holds = False
        print(f"  CRITERION VIOLATION at q={q}: pred={predicted_uniq}, "
              f"actual={uniq}, pi={pis}, d0={d0}")
    scan[q] = {"legendre": leg, "pisano": pis, "d0": d0,
               "orbit_lengths": lens, "inf_free": inf_free,
               "unique_all_n": uniq}
uniq_primes = sorted(q for q, r in scan.items() if r["unique_all_n"])
print(f"\nOrbit scan q<200: exact criterion holds everywhere: {pattern_holds}")
print(f"Primes with vacuum-unique fixed point for ALL n: {uniq_primes}")
results["orbit_scan_q200"] = {"criterion_holds": pattern_holds,
                              "unique_all_n_primes": uniq_primes,
                              "table": scan}

# --- Part 3: null over the same 30 random GF(7) rules ---
import numpy as np
rng = np.random.default_rng(20260609)
P_COEFFS = (0, 1, 1, 0, 0, 6, 6)
def mirror(c):
    a1, a2, a3, a4, a5, a6, a7 = c
    return (a3, a2, a1, a6, a5, a4, a7)
structured_vals = [mirror(P_COEFFS),
                   (0, 2, 1, 0, 0, 6, 6), (0, 1, 2, 0, 0, 6, 6),
                   (0, 1, 1, 0, 0, 5, 6), (0, 1, 1, 0, 0, 6, 5),
                   tuple((3 * c) % 7 for c in P_COEFFS),
                   (0, 1, 1, 0, 0, 6, 0), (1, 1, 1, 0, 0, 0, 0),
                   (0, 1, 1, 0, 0, 1, 1), (0, 1, 1, 0, 0, 3, 3)]
seen = {P_COEFFS} | set(structured_vals)
rand_rules = []
while len(rand_rules) < 30:
    c = tuple(int(x) for x in rng.integers(0, 7, size=7))
    if c in seen:
        continue
    seen.add(c)
    rand_rules.append(c)

count = 0
per_rule = []
for c in rand_rules:
    uniq = not digraph_cycles_off_vacuum(c, 7)
    count += uniq
    per_rule.append({"coeffs": list(c), "unique_fix_all_n": bool(uniq)})
print(f"\nNULL (unique fixed point for ALL n): {count}/30 random rules")
results["null_all_n"] = {"count_unique_all_n": count, "out_of": 30,
                         "per_rule": per_rule}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "gte_zeta_moebius_fixed_point_theorem_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved gte_zeta_moebius_fixed_point_theorem_results.json")
signal.alarm(0)
