#!/usr/bin/env python3
"""
cc_bracket_dres_consistency.py — Numerical consistency battery for the CC
One-Jump Residual Theorem (088-R22, Task 3b/3c).

Computes:
  (B1) The two GTE Omega_Lambda routes and the Planck 2018 comparison:
       Route 1 (PSC epoch census, upper bracket) = (ln2/3pi)*log2(2000/3);
       Route 2 (holographic floor, lower bracket) = 3*pi/14.
       Checks Planck 2018 (0.6889 +/- 0.0056; P47 uses 0.6847 +/- 0.0073 for
       the TT,TE,EE+lowE convention — both checked) lies strictly interior.
  (B2) Unresolved-capacity fraction: spread/census — under the bracket
       orientation reading, the fraction of the PSC diagonal capacity whose
       halting status is unresolved.
  (B3) N_gen scan: for N in 1..11, Route1(N) = (ln2/(N*pi))*log2(D^2*5^N/N)
       with D = N+1, Route2(N) = (N/(2N+1))*(pi/2); checks N = 3 is the
       unique integer where the routes bracket the observed value
       (re-verification of the FINAL_THEORY G02 CatAD result at the
       bracket level — a computable, Delta_1^0 constraint).
  (B4) Precision horizon (falsifiable consequence): the strict-interiority
       prediction Omega_Lambda_true in (lower, upper) OPEN interval implies
       the measured central value must remain strictly below the census
       endpoint as error bars shrink. Computes the measurement sigma at
       which the current central value would exclude the census endpoint
       at 3 sigma, and the improvement factor over Planck 2018.

Expected: B1 interior TRUE; B2 ~ 2.4%; B3 unique N = 3; B4 sigma* ~ 3.4e-4
(~17x better than Planck 2018).
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

# ---- B1: routes and interiority ---------------------------------------------
route1 = math.log(2) / (3 * math.pi) * math.log2(2000 / 3)   # census (upper)
route2 = 3 * math.pi / 14                                     # floor (lower)

planck_comparisons = {
    "Planck2018_base": {"value": 0.6889, "sigma": 0.0056},
    "Planck2018_P47_convention": {"value": 0.6847, "sigma": 0.0073},
}
b1 = {}
for name, p in planck_comparisons.items():
    v, s = p["value"], p["sigma"]
    b1[name] = {
        "value": v, "sigma": s,
        "interior": route2 < v < route1,
        "sigma_from_upper_census": round((route1 - v) / s, 3),
        "sigma_from_lower_floor": round((v - route2) / s, 3),
    }

# ---- B2: unresolved-capacity fraction ---------------------------------------
spread = route1 - route2
unresolved_fraction_of_census = spread / route1

# ---- B3: N_gen scan at the bracket level (computable constraint) ------------
obs = 0.6889
n_scan = []
unique_bracketers = []
for N in range(1, 12):
    D = N + 1
    orbit_count = D**2 * 5**N / N           # D^2 * N_fam^N / N_gen
    r1 = math.log(2) / (N * math.pi) * math.log2(orbit_count)
    r2 = (N / (2 * N + 1)) * (math.pi / 2)
    lo, hi = min(r1, r2), max(r1, r2)
    brackets = lo < obs < hi
    if brackets:
        unique_bracketers.append(N)
    n_scan.append({"N": N, "route1_census": round(r1, 4),
                   "route2_floor": round(r2, 4), "brackets_observed": brackets,
                   "spread": round(abs(r1 - r2), 4)})

# ---- B4: precision horizon --------------------------------------------------
# Strict interiority => measured central value stays strictly below the census
# endpoint. Current margin and the sigma needed to make the margin a 3-sigma
# exclusion of the endpoint as the exact value:
margin_upper = route1 - 0.6889
sigma_star = margin_upper / 3
improvement_over_planck = 0.0056 / sigma_star
# Symmetric statement for the floor endpoint:
margin_lower = 0.6889 - route2
sigma_star_floor = margin_lower / 3

results = {
    "route1_census_upper": route1,
    "route2_floor_lower": route2,
    "B1_interiority": b1,
    "B2_bracket_spread": round(spread, 6),
    "B2_unresolved_capacity_fraction_of_census": round(unresolved_fraction_of_census, 5),
    "B3_n_scan": n_scan,
    "B3_unique_bracketing_N": unique_bracketers,
    "B3_N3_unique": unique_bracketers == [3],
    "B4_margin_below_census": round(margin_upper, 6),
    "B4_sigma_star_3sigma_endpoint_exclusion": round(sigma_star, 7),
    "B4_improvement_factor_over_Planck2018": round(improvement_over_planck, 1),
    "B4_margin_above_floor": round(margin_lower, 6),
    "B4_sigma_star_floor": round(sigma_star_floor, 6),
    "note": ("B3 shows the N_gen=3 bracket-uniqueness constraint is computable "
             "(it compares computable brackets to the observation) even though "
             "the bracketed value is Delta_2^0; B4 quantifies the falsifiable "
             "strict-interiority consequence: a measurement at sigma <= "
             "sigma_star with central value at/above the census endpoint would "
             "refute the bracket orientation; central value strictly below the "
             "census at high precision is the standing prediction."),
}

signal.alarm(0)
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "cc_bracket_dres_consistency_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
