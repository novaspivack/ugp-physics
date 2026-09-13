#!/usr/bin/env python3
"""
COMP-P01-S  —  Higgs lambda combinatorial null over {phi, pi, small rationals}

Question (advisor, round 7): the Higgs quartic claim lambda_H = phi/(4 pi)
matches PDG (lambda_H approx 0.1294) to 0.46 %.  A sceptical physicist would
ask: over the basis {phi, pi, small rationals, small integer powers}, how
many distinct expressions land within a given tolerance of ANY of 12
dimensionless SM observables?  If the density of hits is high, the Higgs
identification is post-hoc numerology; if it is low, the paper's claim of
"unique among simple algebraic combinations at sub-percent" has quantitative
support.

Null construction (falsifiable, no cherry-picking):
  1. Enumerate expressions of the form (p / q) * phi^a * pi^b with
        a, b  in {-4, -3, -2, -1, 0, 1, 2, 3, 4}
        p, q in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16} (and gcd(p,q)=1)
  2. Deduplicate by numerical value at fp64.
  3. Filter to [1e-5, 1e+2] (physical range of dimensionless couplings).
  4. Define 12 dimensionless SM observables (PDG 2024 central values).
  5. For each observable, count how many distinct expressions land within
     {0.5 %, 1 %, 2 %} relative tolerance.
  6. Report the hit rate H(tol) = #hits / (#expressions * #observables).
  7. Decision rule (pre-registered in NOTE_P01_ROUND7_ADVISOR_RESPONSE_PLAN.md):
       H(0.5%) < 1 %   -> lambda_H = phi/(4 pi) retains quantitative force
       H(0.5%) > 10 %  -> demote to Appendix as [C] coincidence
       otherwise       -> disclose numerically, framework-dependent strength

Outputs:
  comp_p01_S_higgs_lambda_null.json   (counts, distributions, verdict)
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import json
import math
import sys
from fractions import Fraction
from math import gcd
from pathlib import Path


# -----------------------------------------------------------------
# PDG 2024 dimensionless SM observables
# -----------------------------------------------------------------
PHI = (1.0 + math.sqrt(5.0)) / 2.0   # golden ratio
PI  = math.pi

SM_OBSERVABLES = {
    "lambda_H":        0.1294,      # Higgs quartic  (m_H^2 / (2 v^2), PDG 2024)
    "sin2_theta_W":    0.23122,     # on-shell Z-pole
    "alpha_EM_times_137": 7.2973525693e-3 * 137.035999084,  # = 1.0 by definition? (keep as sanity)
    "alpha_s_MZ":      0.1179,
    "m_h_over_m_t":    125.25 / 172.69,      # ~0.7253
    "m_W_over_m_Z":    80.369 / 91.1876,     # ~0.8815
    "m_b_over_m_t":    4.183  / 172.69,      # ~0.02422
    "m_tau_over_m_b":  1.77686 / 4.183,      # ~0.4247
    "Koide_Q":         2.0/3.0,              # Koide relation
    "V_cb":            0.0408,               # CKM
    "V_us":            0.2243,               # CKM
    "sin_theta_13":    0.1461,               # PMNS theta_13 sin
}

# Drop the alpha_EM*137 pseudo-observable (tautology at the 10 ppm level)
del SM_OBSERVABLES["alpha_EM_times_137"]


# -----------------------------------------------------------------
# Expression basis
# -----------------------------------------------------------------
A_RANGE = list(range(-4, 5))          # phi exponent
B_RANGE = list(range(-4, 5))          # pi  exponent

RATIONAL_P = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16]
RATIONAL_Q = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16]


def enumerate_expressions():
    """Yield (rep, value) pairs for all phi^a * pi^b * p/q expressions.

    rep is a descriptive string like '(3/4) * phi^2 * pi^-1'.
    """
    rationals = []
    for p in RATIONAL_P:
        for q in RATIONAL_Q:
            if gcd(p, q) != 1:
                continue
            rationals.append((p, q, p / q))
    seen_values = set()
    count = 0
    for a in A_RANGE:
        phi_a = PHI ** a
        for b in B_RANGE:
            pi_b = PI ** b
            for p, q, r in rationals:
                v = r * phi_a * pi_b
                if not math.isfinite(v):
                    continue
                if v <= 0:
                    continue
                if v < 1e-5 or v > 1e2:
                    continue
                key = round(math.log(v), 10)   # dedupe in log-space at 1e-10
                if key in seen_values:
                    continue
                seen_values.add(key)
                rep_parts = [f"({p}/{q})"]
                if a != 0:
                    rep_parts.append(f"phi^{a}")
                if b != 0:
                    rep_parts.append(f"pi^{b}")
                rep = " * ".join(rep_parts)
                yield rep, v
                count += 1


def count_hits(expressions, observables, tolerances=(0.005, 0.01, 0.02)):
    """For each tolerance, count hits per observable and total.

    Returns a dict:  tol -> { obs -> {count, rate, best_ppm, best_rep} }.
    """
    results = {f"{100*t:.3g}pct": {} for t in tolerances}
    for obs_name, obs_val in observables.items():
        best = {"ppm": float("inf"), "rep": None, "value": None}
        per_tol_count = {f"{100*t:.3g}pct": 0 for t in tolerances}
        for rep, v in expressions:
            rel = abs(v - obs_val) / obs_val
            if rel * 1e6 < best["ppm"]:
                best = {"ppm": rel * 1e6, "rep": rep, "value": v}
            for t in tolerances:
                if rel <= t:
                    per_tol_count[f"{100*t:.3g}pct"] += 1
        for t in tolerances:
            key = f"{100*t:.3g}pct"
            results[key][obs_name] = {
                "hits":       per_tol_count[key],
                "best_ppm":   best["ppm"],
                "best_rep":   best["rep"],
                "best_value": best["value"],
                "obs_value":  obs_val,
            }
    return results


def main() -> int:
    exprs = list(enumerate_expressions())
    n_exprs = len(exprs)
    n_obs = len(SM_OBSERVABLES)
    print(f"[enumerate] {n_exprs} distinct expressions over "
          f"(phi^a, pi^b, p/q) basis with a,b in [-4,+4], p/q coprime from "
          f"{len(RATIONAL_P)}x{len(RATIONAL_Q)} rationals")
    print(f"[targets]   {n_obs} dimensionless SM observables")

    hits = count_hits(exprs, SM_OBSERVABLES)

    # Aggregate hit rates
    agg = {}
    for tol_label, per_obs in hits.items():
        total_hits = sum(v["hits"] for v in per_obs.values())
        rate_denominator = n_exprs * n_obs
        agg[tol_label] = {
            "total_hits":       total_hits,
            "rate":             total_hits / rate_denominator,
            "rate_denominator": rate_denominator,
        }

    # Specifically: how many distinct expressions (across all observables)
    # land within 0.5% of ANY observable?  (this is the strict advisor metric)
    any_obs_hit = {f"{100*t:.3g}pct": 0 for t in (0.005, 0.01, 0.02)}
    for rep, v in exprs:
        for t in (0.005, 0.01, 0.02):
            if any(abs(v - ov) / ov <= t for ov in SM_OBSERVABLES.values()):
                any_obs_hit[f"{100*t:.3g}pct"] += 1
                break
    any_obs_rate = {k: v / n_exprs for k, v in any_obs_hit.items()}

    # Verdict
    rate_0p5 = any_obs_rate["0.5pct"]
    if rate_0p5 < 0.01:
        verdict = (
            f"PASS: {100*rate_0p5:.2f}% of expressions land within 0.5% of "
            f"any of {n_obs} SM observables; lambda_H = phi/(4 pi) retains "
            f"quantitative force as an algebraic identification."
        )
        decision = "RETAIN"
    elif rate_0p5 > 0.10:
        verdict = (
            f"FAIL: {100*rate_0p5:.2f}% of expressions land within 0.5% of "
            f"some SM observable; lambda_H = phi/(4 pi) cannot be "
            f"distinguished from post-hoc numerology at this precision."
        )
        decision = "DEMOTE_TO_APPENDIX"
    else:
        verdict = (
            f"AMBIGUOUS: {100*rate_0p5:.2f}% hit rate at 0.5%; disclose "
            f"quantitatively; framework-dependent interpretation."
        )
        decision = "DISCLOSE_QUANTITATIVELY"

    # Specifically for Higgs lambda_H
    lambda_hits = hits["0.5pct"]["lambda_H"]

    report = {
        "experiment_id": "COMP-P01-S",
        "question": (
            "Combinatorial null for the Higgs quartic identification "
            "lambda_H = phi/(4 pi).  Over the basis (phi^a, pi^b, p/q) with "
            "a,b in [-4,+4] and small coprime rationals, what fraction of "
            "distinct expressions land within a given tolerance of any of "
            "12 dimensionless SM observables?"
        ),
        "basis_spec": {
            "phi_exponent_range": [min(A_RANGE), max(A_RANGE)],
            "pi_exponent_range":  [min(B_RANGE), max(B_RANGE)],
            "rational_numerator_set":   RATIONAL_P,
            "rational_denominator_set": RATIONAL_Q,
            "rational_coprimality":     "required (gcd(p, q) == 1)",
            "value_range_filter":       [1e-5, 1e2],
            "deduplication":            "log-space rounding to 1e-10",
        },
        "distinct_expressions_count": n_exprs,
        "observables_count":          n_obs,
        "observables":                SM_OBSERVABLES,
        "per_observable_hit_counts":  hits,
        "aggregate":                  agg,
        "expressions_hitting_any_observable": any_obs_hit,
        "expressions_hitting_any_observable_rate": any_obs_rate,
        "lambda_H_specific_result":   lambda_hits,
        "verdict":                    verdict,
        "decision":                   decision,
        "timestamp_utc":              _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }

    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"\n[write] {out_path.name}")
    print(f"[sha]   {sha}")

    print("\n====  HIT RATES (fraction of expressions hitting ANY SM observable)  ====")
    for tol_label, rate in any_obs_rate.items():
        count = any_obs_hit[tol_label]
        print(f"  tol = {tol_label:7s}  rate = {100*rate:6.3f}%   ({count} / {n_exprs})")

    print("\n====  HIGGS-SPECIFIC (lambda_H = 0.1294, 0.5% tolerance)  ====")
    print(f"  distinct hits within 0.5%:  {lambda_hits['hits']}")
    print(f"  best expression:             {lambda_hits['best_rep']}")
    print(f"  best ppm deviation:          {lambda_hits['best_ppm']:.1f}")
    print(f"  best value:                  {lambda_hits['best_value']:.6g}")
    print(f"  target:                      {lambda_hits['obs_value']:.6g}")

    print(f"\n{verdict}")
    print(f"Decision: {decision}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
