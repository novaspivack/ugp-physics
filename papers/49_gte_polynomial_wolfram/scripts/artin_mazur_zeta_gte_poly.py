#!/usr/bin/env python3
"""Artin-Mazur dynamical zeta function of the GTE polynomial CA.

For the global CA map T_n : GF(7)^n -> GF(7)^n (cyclic ring, rule
p(L,C,R) = C+R-CR-LCR mod 7), compute the periodic-point counts
Fix(T_n^m) for n = 3..7, m = 1..12, the cycle spectrum (number of cycles of
each length), and the Artin-Mazur zeta function

    zeta_n(t) = exp( sum_m Fix(T_n^m) t^m / m ) = prod_L (1 - t^L)^{-c_L}

where c_L is the number of cycles of length L. Looks for closed-form
structure in n (dynamical analogue of |V(p)(GF(q))| = Phi_6(q)).

Expected output: cycle spectra per n; Fix counts; zeta in product form.
"""
import os
import json
import signal
import sys

TIMEOUT_SECONDS = 600

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def step(s, n):
    return tuple((s[i] + s[(i + 1) % n] - s[i] * s[(i + 1) % n]
                  - s[(i - 1) % n] * s[i] * s[(i + 1) % n]) % Q
                 for i in range(n))

results = {}
for n in range(3, 8):
    N = Q ** n
    # enumerate states as tuples via mixed-radix decoding
    # find all states on cycles: iterate to attractor per state with memo
    succ = {}
    def enc(s):
        v = 0
        for x in s:
            v = v * Q + x
        return v
    def dec(v):
        s = []
        for _ in range(n):
            s.append(v % Q)
            v //= Q
        return tuple(reversed(s))

    succ_arr = [0] * N
    for v in range(N):
        succ_arr[v] = enc(step(dec(v), n))

    # find cyclic states: a state is periodic iff it recurs under iteration
    # standard technique: compute in-degree, peel leaves (states with no
    # preimage chain), remaining states are on cycles
    indeg = [0] * N
    for v in range(N):
        indeg[succ_arr[v]] += 1
    queue = [v for v in range(N) if indeg[v] == 0]
    removed = [False] * N
    while queue:
        v = queue.pop()
        removed[v] = True
        w = succ_arr[v]
        indeg[w] -= 1
        if indeg[w] == 0:
            queue.append(w)
    cyclic = [v for v in range(N) if not removed[v]]

    # extract cycle lengths
    seen = set()
    cycle_spectrum = {}
    for v in cyclic:
        if v in seen:
            continue
        # walk the cycle
        cyc = [v]
        w = succ_arr[v]
        while w != v:
            cyc.append(w)
            w = succ_arr[w]
        for x in cyc:
            seen.add(x)
        L = len(cyc)
        cycle_spectrum[L] = cycle_spectrum.get(L, 0) + 1

    # Fix(T^m) = sum over cycle lengths L dividing m of L * c_L
    fix = {}
    for m in range(1, 13):
        fix[m] = sum(L * c for L, c in cycle_spectrum.items() if m % L == 0)

    total_cyclic = sum(L * c for L, c in cycle_spectrum.items())
    print(f"n={n}: |S|={N}, periodic states={total_cyclic}, "
          f"cycle spectrum {{L: count}} = {dict(sorted(cycle_spectrum.items()))}")
    print(f"      Fix(T^m), m=1..12: {[fix[m] for m in range(1, 13)]}")
    results[n] = {"states": N, "periodic_states": total_cyclic,
                  "cycle_spectrum": {str(k): v for k, v in
                                      sorted(cycle_spectrum.items())},
                  "fix_counts_m1_12": [fix[m] for m in range(1, 13)]}

# Structure probes: Fix(T^1) per n; periodic-state totals per n
fixed_per_n = {n: results[n]["fix_counts_m1_12"][0] for n in results}
per_n = {n: results[n]["periodic_states"] for n in results}
print("\nFixed configurations Fix(T) per n:", fixed_per_n)
print("Total periodic states per n:", per_n)
results["summary"] = {"fixed_per_n": fixed_per_n, "periodic_per_n": per_n}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "artin_mazur_zeta_gte_poly_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved artin_mazur_zeta_gte_poly_results.json")
signal.alarm(0)
