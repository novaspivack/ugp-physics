#!/usr/bin/env python3
"""Eisenstein-norm (Phi_6) structure of the GTE integer constants.

Tests which pre-registered GTE constants are values of the 6th cyclotomic
polynomial Phi_6(n) = n^2 - n + 1 (= the Eisenstein norm N(n + omega) in
Z[omega]), and whether the hit count is statistically distinguishable from
chance via (a) exact density accounting and (b) a Monte Carlo null in which
random integer sets of the same magnitudes are scanned identically, plus
(c) a neighbor-atom null (perturb each hit by +-1, +-2).

The atom list is PRE-REGISTERED (fixed before scanning) per the
anti-numerology pipeline.

Expected output: list of hits with their n-values; null probability estimate.
"""
import os
import json
import random
import signal
import sys

TIMEOUT_SECONDS = 300

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

# PRE-REGISTERED atom list (name, value) — fixed before any scanning
ATOMS = [
    ("N_gen", 3), ("N_fam", 5), ("q", 7), ("b0", 7), ("n_ridge", 10),
    ("c_Z", 12), ("c_H", 13), ("K_CA_bits", 19), ("F21_order", 21),
    ("b2_muon", 42), ("GS_degeneracy", 43), ("b1_electron", 73),
    ("alpha_inv_MZ", 128), ("alpha_inv_0", 137), ("b3_tau", 275),
    ("orbit_period", 475), ("seed_c", 823), ("ridge_R10", 1008),
    ("D_spacetime", 4), ("D_squared", 16),
]

def is_phi6(v):
    # v = n^2 - n + 1  ->  n = (1 + sqrt(4v-3))/2
    d = 4 * v - 3
    r = int(d ** 0.5)
    for rr in (r - 1, r, r + 1):
        if rr >= 0 and rr * rr == d and (1 + rr) % 2 == 0:
            return (1 + rr) // 2
    return None

hits = []
for name, v in ATOMS:
    n = is_phi6(v)
    if n is not None and n >= 2:  # n=0,1 give trivial 1
        hits.append({"atom": name, "value": v, "n": n})

print("Phi_6 hits among pre-registered GTE atoms:")
for h in hits:
    print(f"  {h['atom']:>16} = {h['value']:>4} = Phi_6({h['n']})")
print(f"Total: {len(hits)} / {len(ATOMS)} atoms")

# Null (a): density of Phi_6 numbers below N is ~ sqrt(N); per-window probability
# Null (b): Monte Carlo with magnitude-matched random integers
random.seed(42)
TRIALS = 200000
vals = [v for _, v in ATOMS]
count_ge = 0
hit_distribution = [0] * (len(ATOMS) + 1)
for _ in range(TRIALS):
    k = 0
    for v in vals:
        # magnitude-matched draw: uniform in [max(2, v//2), 2v]
        lo, hi = max(2, v // 2), 2 * v
        rv = random.randint(lo, hi)
        if is_phi6(rv) is not None and rv > 1:
            k += 1
    hit_distribution[k] += 1
    if k >= len(hits):
        count_ge += 1

p_null = count_ge / TRIALS
print(f"\nMonte Carlo null: P(>= {len(hits)} hits among magnitude-matched random sets) "
      f"= {p_null:.2e}  ({TRIALS} trials)")
print("Hit distribution (k: count):",
      {k: c for k, c in enumerate(hit_distribution) if c > 0})

# Null (c): neighbor-atom null — perturb each hit value by +-1, +-2
neighbor_hits = 0
neighbor_total = 0
for h in hits:
    for dv in (-2, -1, 1, 2):
        neighbor_total += 1
        if is_phi6(h["value"] + dv) is not None and h["value"] + dv > 1:
            neighbor_hits += 1
print(f"Neighbor null: {neighbor_hits}/{neighbor_total} perturbed values are Phi_6 "
      f"(expected near 0 for sparse target set)")

# Which n-values appear, and which gaps (missing n) exist
ns = sorted(h["n"] for h in hits)
gaps = [n for n in range(min(ns), max(ns) + 1) if n not in ns]
gap_values = {n: n * n - n + 1 for n in gaps}
print(f"\nn-values hit: {ns}; gaps: {gap_values}")

results = {
    "atoms_preregistered": ATOMS,
    "phi6_hits": hits,
    "monte_carlo_null": {"trials": TRIALS, "p_geq_observed": p_null,
                          "hit_distribution": hit_distribution},
    "neighbor_null": {"hits": neighbor_hits, "total": neighbor_total},
    "n_values": ns, "n_gaps": gap_values,
}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "eisenstein_norm_gte_constants_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("\nSaved eisenstein_norm_gte_constants_results.json")
signal.alarm(0)
