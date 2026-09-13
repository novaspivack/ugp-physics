#!/usr/bin/env python3
"""
cc_two_route_ngen_scan_canonical.py — Canonical N-scan of the two GTE
Omega_Lambda routes under the orbit-count-anchored ansatz.

This is the canonical-formula N-scan first computed inline for the
083-NGEN-CC-UNIQUENESS result (epic_083; previously not saved as a script).
It scans the generation count N through the two structural routes:

  Route 1 (PSC epoch census, upper bracket):
      Omega_census(N) = (ln 2 / (N*pi)) * log2(D^2 * N_fam^3 / N)
      with D = 4 and N_fam = 5 held at their corpus values
      (orbit count 2000/N; at N = 3 this is the published 2000/3),
  Route 2 (holographic floor, lower bracket):
      Omega_floor(N) = (N / |Z7|) * (pi/2)  with |Z7| = 7 fixed.

The N-dependence enters only through the DPP identification
N_spatial = N_gen (the Friedmann 3 in Route 1's denominator and the
proper-time numerator in Route 2; `dimensional_protocol_principle_master`,
CatAL) and through the orbit-count denominator factorization
2000/3 = D^2 * N_fam^3 / N_gen.

Computes and verifies:
  (R1) The published N = 3 anchor values to full precision:
       census = 0.689914414741625, floor = 3*pi/14 = 0.673198425769241,
       ratio = 1.024830701220495, spread = 0.01671599,
       Planck 2018 deviations +0.18 sigma (census) / -2.80 sigma (floor).
  (R2) The N = 1..11 table with per-route sigma vs Planck 2018
       (0.6889 +/- 0.0056) and the published criterion "both routes
       within 5 sigma" -> expected unique N = 3; published spreads
       0.650 (N=2), 0.403 (N=4), >= 0.40 for all N != 3.
  (R3) The continuous spread minimum: expected N* = 3.034 with common
       value 0.6809 (-1.43 sigma).
  (R4) Diagnostics per N (recorded for the bracket-orientation
       adjudication): naive unordered containment of the Planck value,
       and oriented-interval non-emptiness census(N) >= floor(N).

Expected: R1/R2/R3 reproduce the published values exactly; R4 shows
naive containment is non-discriminating under this ansatz while the
oriented interval is non-empty exactly for N in {1, 2, 3}.
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 60


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s — exiting")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

D = 4
N_FAM = 5
Z7 = 7
PLANCK = 0.6889
PLANCK_SIGMA = 0.0056


def census(n: float) -> float:
    return math.log(2) / (n * math.pi) * math.log2(D**2 * N_FAM**3 / n)


def floor(n: float) -> float:
    return (n / Z7) * (math.pi / 2)


# ---- R1: N = 3 anchor values --------------------------------------------------
c3, f3 = census(3), floor(3)
r1 = {
    "census_N3": c3,
    "floor_N3": f3,
    "ratio": c3 / f3,
    "spread": c3 - f3,
    "sigma_census": (c3 - PLANCK) / PLANCK_SIGMA,
    "sigma_floor": (f3 - PLANCK) / PLANCK_SIGMA,
    "matches_published_census": abs(c3 - 0.689914414741625) < 1e-15,
    "matches_published_floor": abs(f3 - 0.673198425769241) < 1e-15,
    "matches_published_ratio": abs(c3 / f3 - 1.024830701220495) < 1e-14,
}

# ---- R2: N = 1..11 table ------------------------------------------------------
rows = []
within_5sigma = []
for N in range(1, 12):
    c, f = census(N), floor(N)
    sc, sf = (c - PLANCK) / PLANCK_SIGMA, (f - PLANCK) / PLANCK_SIGMA
    both5 = abs(sc) <= 5 and abs(sf) <= 5
    if both5:
        within_5sigma.append(N)
    rows.append({
        "N": N,
        "census": round(c, 4),
        "floor": round(f, 4),
        "sigma_census": round(sc, 1),
        "sigma_floor": round(sf, 1),
        "both_within_5sigma": both5,
        "spread_abs": round(abs(c - f), 4),
        "naive_containment": min(c, f) < PLANCK < max(c, f),
        "oriented_interval_nonempty": c >= f,
    })

# ---- R3: continuous spread minimum -------------------------------------------
# golden-section minimization of |census - floor| on [2.5, 3.5]
lo, hi = 2.5, 3.5
g = (math.sqrt(5) - 1) / 2
a, b = hi - g * (hi - lo), lo + g * (hi - lo)
spread_fn = lambda n: abs(census(n) - floor(n))
for _ in range(200):
    if spread_fn(a) < spread_fn(b):
        hi = b
    else:
        lo = a
    a, b = hi - g * (hi - lo), lo + g * (hi - lo)
n_star = (lo + hi) / 2
common_value = census(n_star)
r3 = {
    "n_star": round(n_star, 4),
    "common_value": round(common_value, 4),
    "sigma_common": round((common_value - PLANCK) / PLANCK_SIGMA, 2),
}

# ---- R4 summary ---------------------------------------------------------------
naive_passers = [r["N"] for r in rows if r["naive_containment"]]
oriented_admissible = [r["N"] for r in rows if r["oriented_interval_nonempty"]]

results = {
    "ansatz": "orbit-count-anchored: census=(ln2/Npi)log2(2000/N), floor=(N/7)(pi/2)",
    "R1_anchor_N3": {k: (v if isinstance(v, bool) else round(v, 15))
                     for k, v in r1.items()},
    "R2_table": rows,
    "R2_unique_within_5sigma": within_5sigma,
    "R3_continuous_spread_minimum": r3,
    "R4_naive_containment_passers": naive_passers,
    "R4_oriented_admissible_set": oriented_admissible,
}

signal.alarm(0)
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "cc_two_route_ngen_scan_canonical_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
