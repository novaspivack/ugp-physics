#!/usr/bin/env python3
"""
ngen_bracket_orientation_family.py — Ansatz-robustness scan for the
N_gen bracket-orientation exclusion.

The CC One-Jump Residual Theorem orders the two GTE Omega_Lambda routes:
census (PSC epoch capacity) is the upper bracket, floor (holographic mode
count) is the lower bracket, and the realized ledger value lies between
them. A generation count N is therefore *admissible* (measurement-free)
only if census(N) >= floor(N). This script tests whether the exclusion of
N >= 4 by orientation flip is robust across every defensible
N-generalization of the two route formulas.

Slot structure (the N=3 anchor formulas contain five "3"-slots):
  Always varied (CatAL-anchored, DPP `dimensional_protocol_principle_master`):
    - Friedmann denominator 3 -> N (census prefactor ln2/(N*pi))
    - floor numerator 3 -> N (proper-time rate tau = N_spatial/|Z7|)
  Toggled (interpretive; 2^4 = 16 variants):
    - S2: orbit-count denominator 2000/3 -> 2000/N
          (factorization D^2 N_fam^3 / N_gen)
    - S3: D = 4 -> N+1 in the orbit count
    - S4: N_fam exponent 5^3 -> 5^N
    - S5: floor alphabet 7 -> 2N+1
  Variant {S2} is the canonical orbit-count-anchored scan;
  variant {S2,S3,S4,S5} is the fully generalized scan;
  variant {} is the maximally conservative pure-DPP scaling form, whose
  admissibility boundary has the closed form N <= 3*sqrt(census3/floor3).

PRE-REGISTERED PREDICTIONS (recorded before execution):
  (P1) admissible set = {1, 2, 3} in all 16 variants (flip at N = 4);
  (P2) N = 3 is the unique spread-minimizing integer in all 16 variants;
  (P3) the continuous crossing N* lies in (3, 4) in all 16 variants.
Failure of any prediction in any variant = the exclusion is
ansatz-fragile and the candidate closes NEGATIVE.

Also computes:
  - the closed-form conservative boundary 3*sqrt(ratio) and its match to
    the variant-{} numerical crossing;
  - the adversarial-alphabet threshold q_crit(4) = 4*(pi/2)/census(4)
    per census variant: the alphabet size the floor would need at N = 4
    to avoid the flip, compared with all structural alphabet candidates
    (7 fixed; 2N+1 = 9; minimal prime = 1 mod N = 5; minimal prime with
    embeddable Z3 color = 7).

Expected: P1/P2/P3 all PASS; q_crit ~ 10-13, above every structural
candidate (max 9).
"""
import itertools
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 120


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s — exiting")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

N_FAM = 5
PLANCK = 0.6889


def census(n: float, s2: bool, s3: bool, s4: bool) -> float:
    d = (n + 1) if s3 else 4
    exponent = n if s4 else 3
    orbit = d**2 * N_FAM**exponent
    if s2:
        orbit = orbit / n
    else:
        orbit = orbit / 3
    return math.log(2) / (n * math.pi) * math.log2(orbit)


def floor(n: float, s5: bool) -> float:
    q = (2 * n + 1) if s5 else 7
    return (n / q) * (math.pi / 2)


def crossing(cen, flo) -> float:
    """Bisection for census(n) = floor(n) on [1, 10]."""
    g = lambda n: cen(n) - flo(n)
    lo, hi = 1.0, 10.0
    if g(lo) <= 0 or g(hi) >= 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        if g(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


variants = []
for s2, s3, s4, s5 in itertools.product([False, True], repeat=4):
    name = "{" + ",".join(s for s, on in
                          zip(("S2", "S3", "S4", "S5"), (s2, s3, s4, s5))
                          if on) + "}"
    cen = lambda n, s2=s2, s3=s3, s4=s4: census(n, s2, s3, s4)
    flo = lambda n, s5=s5: floor(n, s5)
    table = []
    admissible = []
    spreads = {}
    for N in range(1, 11):
        c, f = cen(N), flo(N)
        ok = c >= f
        if ok:
            admissible.append(N)
        spreads[N] = abs(c - f)
        table.append({"N": N, "census": round(c, 4), "floor": round(f, 4),
                      "admissible": ok})
    flip_n = next((N for N in range(1, 11) if N not in admissible), None)
    spread_min_n = min(spreads, key=spreads.get)
    n_star = crossing(cen, flo)
    c4, f4 = cen(4), flo(4)
    variants.append({
        "variant": name,
        "is_canonical_scan": name == "{S2}",
        "is_full_generalization": name == "{S2,S3,S4,S5}",
        "admissible_set": admissible,
        "first_inadmissible_N": flip_n,
        "continuous_crossing_n_star": round(n_star, 4),
        "spread_min_integer": spread_min_n,
        "spread_at_3": round(spreads[3], 6),
        "spread_at_4": round(spreads[4], 6),
        "inversion_margin_N4": round(f4 - c4, 4),
        "q_crit_N4": round(4 * (math.pi / 2) / c4, 2),
        "table": table,
    })

# Separation certificate for ALL N >= 4 (not just the scanned range).
# Note: census is NOT globally monotone for S4-on/S3-off variants — it dips
# below its asymptote ln5/pi and recovers from below with minimum at
# n = 16e ~ 43.49. The exclusion does not need monotonicity; it needs
#   sup_{n>=4} census(n) < inf_{n>=4} floor(n).
# Floor is strictly increasing in both variants (n/7; n/(2n+1)), so
# inf = floor(4). Census on [4, inf) is bounded by max(census(4), asymptote),
# asymptote = ln5/pi (S4 on) or 0 (S4 off). Certificate per variant:
#   (i) floor strictly increasing on the grid;
#   (ii) census(n) <= census(4) for all grid n in [4, 50];
#   (iii) max(census(4), asymptote) < floor(4).
GRID = [4 + 0.01 * k for k in range(4601)]  # 4.00 .. 50.00
floor_increasing = True
for s5 in (False, True):
    vals = [floor(n, s5) for n in GRID]
    if any(b <= a for a, b in zip(vals, vals[1:])):
        floor_increasing = False
separation_ok = True
for s2, s3, s4 in itertools.product([False, True], repeat=3):
    c4 = census(4, s2, s3, s4)
    tail_max = max(census(n, s2, s3, s4) for n in GRID)
    asym = math.log(5) / math.pi if s4 else 0.0
    sup_census = max(c4, asym)
    if tail_max > c4 + 1e-12:
        separation_ok = False
    for s5 in (False, True):
        if sup_census >= floor(4, s5):
            separation_ok = False
all_n_ge_4_excluded = floor_increasing and separation_ok

# Closed-form conservative boundary (variant {}):
c3 = census(3, False, False, False)
f3 = floor(3, False)
closed_form_boundary = 3 * math.sqrt(c3 / f3)
empty_variant = next(v for v in variants if v["variant"] == "{}")

# Pre-registered prediction checks
p1 = all(v["admissible_set"] == [1, 2, 3] for v in variants)
p2 = all(v["spread_min_integer"] == 3 for v in variants)
p3 = all(3 < v["continuous_crossing_n_star"] < 4 for v in variants)
n_star_range = (min(v["continuous_crossing_n_star"] for v in variants),
                max(v["continuous_crossing_n_star"] for v in variants))
q_candidates = {"Z7_fixed": 7, "2N+1_at_4": 9,
                "min_prime_1_mod_N_at_4": 5, "min_prime_embeddable_Z3": 7}
q_crit_min = min(v["q_crit_N4"] for v in variants)
q_adversarial_pass = q_crit_min > max(q_candidates.values())

results = {
    "preregistered_P1_admissible_123_all_variants": p1,
    "preregistered_P2_spreadmin_3_all_variants": p2,
    "preregistered_P3_crossing_in_3_4_all_variants": p3,
    "n_star_range_across_family": [round(n_star_range[0], 4),
                                   round(n_star_range[1], 4)],
    "closed_form_conservative_boundary_3sqrt_ratio":
        round(closed_form_boundary, 6),
    "closed_form_matches_empty_variant_crossing":
        abs(closed_form_boundary
            - empty_variant["continuous_crossing_n_star"]) < 5e-4,
    "min_inversion_margin_N4": min(v["inversion_margin_N4"]
                                   for v in variants),
    "max_inversion_margin_N4": max(v["inversion_margin_N4"]
                                   for v in variants),
    "separation_certificate_floor_increasing": floor_increasing,
    "separation_certificate_all_N_ge_4_excluded": all_n_ge_4_excluded,
    "census_nonmonotonicity_note": ("S4-on/S3-off census dips below its "
                                    "asymptote ln5/pi with minimum at n=16e"
                                    "~43.49; exclusion uses sup-census < "
                                    "inf-floor, not monotonicity"),
    "adversarial_alphabet": {
        "q_crit_N4_min_across_family": q_crit_min,
        "structural_candidates": q_candidates,
        "no_structural_candidate_reaches_q_crit": q_adversarial_pass,
    },
    "variants": variants,
}

signal.alarm(0)
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "ngen_bracket_orientation_family_results.json"), "w") as f:
    json.dump(results, f, indent=2)
# print summary only (full tables in JSON)
summary = {k: v for k, v in results.items() if k != "variants"}
summary["per_variant"] = [
    {k: v[k] for k in ("variant", "admissible_set", "first_inadmissible_N",
                       "continuous_crossing_n_star", "spread_min_integer",
                       "inversion_margin_N4", "q_crit_N4")}
    for v in variants
]
print(json.dumps(summary, indent=2))
