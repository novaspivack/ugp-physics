#!/usr/bin/env python3
"""Category check: spin-7 lattice values are CA winding values, not Phi_MDL vacuum labels.

Tests whether the P50 {0,1,5} ground-state selection can bias the 7 Phi_MDL
vacuum sectors (branch B of the Z7 domain-wall question). Four computations:

  1. Diagonal table p(x,x,x) mod 7 and the CA flow of uniform states: every
     uniform state flows to uniform-0 within <= 3 steps (the alphabet has ONE
     dynamical vacuum, not seven).
  2. Z7-shift equivariance test: p(L+1,C+1,R+1) != p(L,C,R)+1 generically --
     the spin-7 Hamiltonian explicitly breaks the vacuum-label shift symmetry,
     so it CANNOT be a functional of the vacuum label (which has exact shift
     symmetry in the pure Phi_MDL potential, CatAL).
  3. Transfer-matrix cross-check against P50 spectral data at beta = 1
     (lambda_1 = 10.417, lambda_2 = 6.728).
  4. The {0,1,5} ground-state set is a transversal of the F21 Z3-orbits
     {0},{1,2,4},{3,5,6} on Z7 (one representative per multiplication-by-2
     orbit) -- a structural observation recorded for the board.

Expected output: shift-equivariance fails for most inputs; uniform flow ->0;
transversal property True.
"""
import json
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

def p(L, C, R):
    return (C + R - C * R - L * C * R) % 7

results = {}

# 1. diagonal table and uniform-state flow
print("=== 1. Diagonal p(x,x,x) and uniform-state CA flow ===")
diag = {x: p(x, x, x) for x in range(7)}
print(f"  p(x,x,x): {diag}   (roots {{x: p=0}} = {sorted(x for x,v in diag.items() if v==0)})")
flows = {}
for x in range(7):
    orbit = [x]
    cur = x
    for _ in range(10):
        cur = p(cur, cur, cur)
        orbit.append(cur)
        if cur == orbit[-2]:
            break
    flows[x] = orbit
    print(f"  uniform-{x} flow: {' -> '.join(map(str, orbit))}")
all_to_zero = all(fl[-1] == 0 for fl in flows.values())
print(f"  ALL uniform states flow to uniform-0: {all_to_zero}")
results["diagonal"] = diag
results["uniform_flows"] = flows
results["all_flow_to_vacuum0"] = all_to_zero

# 2. shift equivariance
print("\n=== 2. Z7-shift equivariance of p ===")
fail = sum(1 for L in range(7) for C in range(7) for R in range(7)
           if p((L+1) % 7, (C+1) % 7, (R+1) % 7) != (p(L, C, R) + 1) % 7)
print(f"  p(L+1,C+1,R+1) == p(L,C,R)+1 fails on {fail}/343 inputs")
print("  -> the spin-7 energy is NOT a function of a shift-symmetric vacuum label;")
print("     its argument is the winding/alphabet value (Object 0 variable).")
results["shift_equivariance_failures"] = fail

# 3. transfer-matrix cross-check (P50 Table: beta=1 -> 10.417, 6.728)
print("\n=== 3. Transfer matrix cross-check (P50) ===")
import cmath
def tm_eigs(beta):
    import itertools
    T = [[sum(2.718281828459045 ** (-beta * p(a, b, c)) for a in range(7))
          for c in range(7)] for b in range(7)]
    # power iteration + deflation is overkill; use numpy
    import numpy as np
    ev = np.linalg.eigvals(np.array(T))
    ev = sorted(ev, key=lambda z: -abs(z))
    return [complex(z) for z in ev]
ev1 = tm_eigs(1.0)
print(f"  beta=1 eigenvalues |.|-sorted: {[round(abs(z),3) for z in ev1[:3]]} "
      f"(P50: 10.417, 6.728, 0)")
results["tm_beta1_top"] = [abs(ev1[0]), abs(ev1[1])]

# 4. transversal property
print("\n=== 4. {0,1,5} vs F21 Z3-orbits on Z7 ===")
def orbit(x):
    o, cur = set(), x
    while cur not in o:
        o.add(cur)
        cur = (2 * cur) % 7
    return frozenset(o)
orbits = sorted({orbit(x) for x in range(7)}, key=lambda s: min(s))
gs = {0, 1, 5}
transversal = all(len(gs & set(o)) == 1 for o in orbits)
print(f"  <x2> orbits on Z7: {[sorted(o) for o in orbits]}")
print(f"  {{0,1,5}} contains exactly one element of each orbit: {transversal}")
results["z3_orbits"] = [sorted(o) for o in orbits]
results["gs_is_transversal"] = transversal

print("\nVERDICT: the spin-7 {0,1,5} structure lives on the winding alphabet")
print("(CA cell values), not on the Phi_MDL vacuum label; it cannot bias the")
print("7 vacuum sectors without contradicting the CatAL shift-symmetry of the")
print("pure Z7 potential. Branch B via the spin-7 free energy: CATEGORY MISMATCH.")

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "z7_domain_wall_winding_vs_vacuum_category_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved z7_domain_wall_winding_vs_vacuum_category_results.json")
signal.alarm(0)
