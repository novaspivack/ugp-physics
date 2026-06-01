#!/usr/bin/env python3
"""
COMP-P01-S2  —  Best-expression Pareto hunt for SM dimensionless observables

User critique (round 7b): "Why are we stuck on phi/(4 pi) is unique if there
are more unique ones?  What is the purpose here?  Why don't we find the truly
unique best ones?"

New experimental design:
  1.  Enumerate a richer basis: {phi, pi, e, 1/e, zeta(3), gamma (Euler-
      Mascheroni), log p for small primes p, sqrt(n) for small n, small
      coprime rationals}.
  2.  For each of 12 dimensionless SM observables, compute the Pareto
      frontier (description length, ppm deviation).
  3.  Find the truly best expression for each observable at each complexity
      level.
  4.  Flag expressions whose coefficients are UGP-native structural integers
      (7, 11, 13, 15, 16, 17, 43, 73, 209, 823, 1008, Fermat products, ...).
  5.  Report: for each observable, the best UGP-native expression and the
      best generic expression.  A UGP-native expression that is competitive
      with the best generic expression is a potential new structural anchor.

This is NOT a null test.  It is a SEARCH for better algebraic identifications
than those currently in the paper, with UGP-structural interpretability as
a bonus criterion.

Outputs:
  comp_p01_S2_best_expression_hunt.json
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
# Extended transcendental basis
# -----------------------------------------------------------------
PHI  = (1.0 + math.sqrt(5.0)) / 2.0
PI   = math.pi
E    = math.e
ZETA3 = 1.2020569031595942854      # Apery's constant
EULER_MASCHERONI = 0.5772156649015329

# sqrt(n) atoms for small non-perfect-square n
SQRT_ATOMS = {
    "sqrt2": math.sqrt(2),
    "sqrt3": math.sqrt(3),
    "sqrt5": math.sqrt(5),
    "sqrt6": math.sqrt(6),
    "sqrt7": math.sqrt(7),
    "sqrt10": math.sqrt(10),
    "sqrt15": math.sqrt(15),
}

# log p for small primes
LOG_ATOMS = {
    "log2":  math.log(2),
    "log3":  math.log(3),
    "log5":  math.log(5),
    "log7":  math.log(7),
    "log11": math.log(11),
    "log13": math.log(13),
}

# Transcendentals
TRANS_ATOMS = {
    "phi":     PHI,
    "pi":      PI,
    "e":       E,
    "zeta3":   ZETA3,
    "euler_g": EULER_MASCHERONI,
}

ALL_TRANS = {**TRANS_ATOMS, **SQRT_ATOMS, **LOG_ATOMS}


# -----------------------------------------------------------------
# UGP structural integers (from ugp-lean and paper 1 canonical)
# -----------------------------------------------------------------
UGP_INTEGERS = {
    7, 11, 13, 16, 17, 20, 23, 43, 73, 209, 255, 257, 823, 1008, 1023,
    2137, 3, 5, 9,  # Fermat primes and 9 (from a2)
    15,   # F0 * F1 = 3 * 5
    85,   # F0 * F1 * F1.5? 5*17; actually F1*F2 = 5*17 = 85
    51,   # 3 * 17 = F0 * F2
    65535,   # 2^16 - 1 = F0*F1*F2*F3
    65537,   # F4
    512,  # 2^9
    2048, # 2^11
    1024, # 2^10
}

# -----------------------------------------------------------------
# SM observables (PDG 2024 central values)
# -----------------------------------------------------------------
SM_OBSERVABLES = {
    "lambda_H":        0.1294,
    "sin2_theta_W":    0.23122,
    "alpha_s_MZ":      0.1179,
    "m_h_over_m_t":    125.25 / 172.69,
    "m_W_over_m_Z":    80.369 / 91.1876,
    "m_b_over_m_t":    4.183  / 172.69,
    "m_tau_over_m_b":  1.77686 / 4.183,
    "Koide_Q":         2.0/3.0,
    "V_cb":            0.0408,
    "V_us":            0.2243,
    "sin_theta_13":    0.1461,
    "cos_theta_W":     80.369 / 91.1876,  # same as m_W/m_Z approx
}


# -----------------------------------------------------------------
# Expression enumeration over a budgeted description language
# -----------------------------------------------------------------
# Description-length definition (integer units):
#   constant atom cost: 1 (pi, phi, e, sqrt(n), log(p))
#   integer atom cost: 1 (integer in {1..24})
#   exponent cost: |exp| (so phi^2 is cost 2 + 1 = 3 if written as phi*phi)
#   rational p/q cost: digits(p) + digits(q)
#
# For simplicity: enumerate expressions of form
#   (a/b) * X^p * Y^q
# with X, Y in ALL_TRANS U {1}, and p, q in [-3, 3], a, b in small coprimes.
# Cost = digits(a) + digits(b) + |p| + |q|.

def digits(n):
    return len(str(abs(n))) if n != 0 else 1


SMALL_RATIONAL_NUMS = list(range(1, 25))
SMALL_RATIONAL_DENS = list(range(1, 25))


def enumerate_expressions_budget(max_cost=8):
    """Yield (rep, value, cost, atoms_used) for expressions a/b * X^p * Y^q
    within cost budget.  Atoms are drawn from ALL_TRANS plus the identity."""
    trans_keys = list(ALL_TRANS.keys()) + ["1"]
    seen_values = set()
    for a in SMALL_RATIONAL_NUMS:
        for b in SMALL_RATIONAL_DENS:
            if gcd(a, b) != 1:
                continue
            rat_cost = digits(a) + digits(b)
            if rat_cost > max_cost:
                continue
            for X in trans_keys:
                x_val = 1.0 if X == "1" else ALL_TRANS[X]
                for p in range(-3, 4):
                    exp_cost_1 = abs(p)
                    if rat_cost + exp_cost_1 > max_cost:
                        continue
                    for Y in trans_keys:
                        if Y <= X:   # canonical ordering
                            continue
                        y_val = 1.0 if Y == "1" else ALL_TRANS[Y]
                        for q in range(-3, 4):
                            cost = rat_cost + abs(p) + abs(q)
                            if cost > max_cost:
                                continue
                            try:
                                val = (a / b) * (x_val ** p) * (y_val ** q)
                            except OverflowError:
                                continue
                            if not math.isfinite(val) or val <= 0:
                                continue
                            if val < 1e-6 or val > 1e3:
                                continue
                            # dedupe
                            key = round(math.log(val), 10)
                            if key in seen_values:
                                continue
                            seen_values.add(key)
                            atoms = {X: p} if X != "1" else {}
                            if Y != "1":
                                atoms[Y] = q
                            integers_used = {a, b}
                            rep_parts = []
                            if b == 1:
                                rep_parts.append(f"{a}")
                            else:
                                rep_parts.append(f"({a}/{b})")
                            if X != "1" and p != 0:
                                rep_parts.append(f"{X}^{p}")
                            if Y != "1" and q != 0:
                                rep_parts.append(f"{Y}^{q}")
                            rep = " * ".join(rep_parts)
                            yield {
                                "rep":            rep,
                                "value":          val,
                                "cost":           cost,
                                "atoms":          atoms,
                                "integers":       sorted(integers_used),
                                "rational_num":   a,
                                "rational_den":   b,
                            }


def is_ugp_native(expr):
    """Check if all integers in the expression are UGP-native structural
    integers."""
    ints_present = set(expr["integers"])
    # 1 is always allowed (trivially UGP)
    ints_to_check = ints_present - {1}
    if not ints_to_check:
        return True
    return ints_to_check.issubset(UGP_INTEGERS)


def find_pareto_frontier(hits):
    """Given a list of {cost, ppm}, return the Pareto frontier (lower cost
    AND lower ppm dominate)."""
    hits_sorted = sorted(hits, key=lambda h: (h["cost"], h["ppm"]))
    frontier = []
    best_ppm = float("inf")
    for h in hits_sorted:
        if h["ppm"] < best_ppm:
            frontier.append(h)
            best_ppm = h["ppm"]
    return frontier


def analyze_observable(obs_name, obs_val, expressions):
    hits = []
    for e in expressions:
        rel = abs(e["value"] - obs_val) / obs_val
        hits.append({
            "rep":          e["rep"],
            "value":        e["value"],
            "cost":         e["cost"],
            "ppm":          1e6 * rel,
            "integers":     e["integers"],
            "atoms":        e["atoms"],
            "is_ugp_native": is_ugp_native(e),
        })
    hits_sorted = sorted(hits, key=lambda h: h["ppm"])
    best_generic = hits_sorted[0] if hits_sorted else None
    ugp_hits = [h for h in hits_sorted if h["is_ugp_native"]]
    best_ugp = ugp_hits[0] if ugp_hits else None
    pareto_generic = find_pareto_frontier(hits_sorted[:500])
    pareto_ugp = find_pareto_frontier(ugp_hits[:500]) if ugp_hits else []
    return {
        "observable":        obs_name,
        "target_value":      obs_val,
        "best_generic":      best_generic,
        "best_ugp_native":   best_ugp,
        "pareto_frontier_generic": pareto_generic[:10],
        "pareto_frontier_ugp":     pareto_ugp[:10],
        "count_total":       len(hits),
        "count_under_0p5pct": sum(1 for h in hits if h["ppm"] < 5000),
        "count_under_0p1pct": sum(1 for h in hits if h["ppm"] < 1000),
        "count_ugp_native":  len(ugp_hits),
    }


def main() -> int:
    print("Enumerating expressions over extended basis...")
    exprs = list(enumerate_expressions_budget(max_cost=8))
    print(f"  {len(exprs)} distinct expressions enumerated (cost <= 8)")
    print(f"  Basis: transcendentals = {list(ALL_TRANS.keys())}")
    print(f"  Rationals: a in [1,24], b in [1,24], gcd(a,b)=1")
    print(f"  UGP-native integer flags: {sorted(UGP_INTEGERS)}")
    print()

    per_observable = {}
    for obs_name, obs_val in SM_OBSERVABLES.items():
        per_observable[obs_name] = analyze_observable(obs_name, obs_val, exprs)

    # Highlight findings
    print("==== BEST EXPRESSION PER OBSERVABLE ====\n")
    ugp_native_strong_hits = []
    for obs_name, analysis in per_observable.items():
        bg = analysis["best_generic"]
        bu = analysis["best_ugp_native"]
        print(f"  {obs_name:18s}  target = {analysis['target_value']:12.6g}")
        if bg:
            print(f"    BEST generic (cost={bg['cost']}):       {bg['rep']:40s}  "
                  f"value = {bg['value']:.6g}   ppm = {bg['ppm']:12.2f}")
        if bu:
            print(f"    BEST UGP-native (cost={bu['cost']}):    {bu['rep']:40s}  "
                  f"value = {bu['value']:.6g}   ppm = {bu['ppm']:12.2f}   "
                  f"integers = {bu['integers']}")
            if bu["ppm"] < 1000.0:  # <0.1% UGP-native hit
                ugp_native_strong_hits.append((obs_name, bu))
        print()

    # Compare to current paper identifications
    print("==== COMPARISON TO PAPER IDENTIFICATIONS ====\n")
    paper_ids = {
        "lambda_H":        ("phi/(4*pi)", PHI / (4 * PI)),
        "sin2_theta_W":    ("empirical 0.23122",  0.23122),
        "m_h_over_m_t":    ("theoretical 0.725",   125.25/172.69),
    }
    for obs_name, (formula, value) in paper_ids.items():
        if obs_name not in per_observable:
            continue
        target = SM_OBSERVABLES[obs_name]
        ppm_paper = 1e6 * abs(value - target) / target
        best_any = per_observable[obs_name]["best_generic"]
        best_ugp = per_observable[obs_name]["best_ugp_native"]
        print(f"  {obs_name}: paper uses {formula} -> ppm = {ppm_paper:.1f}")
        if best_any and best_any["ppm"] < ppm_paper:
            ratio = ppm_paper / max(best_any["ppm"], 1e-6)
            print(f"    BEATEN by {best_any['rep']} at ppm = {best_any['ppm']:.1f}  "
                  f"({ratio:.1f}x improvement)")
        if best_ugp and best_ugp["ppm"] < ppm_paper:
            ratio = ppm_paper / max(best_ugp["ppm"], 1e-6)
            print(f"    UGP-native BEATER: {best_ugp['rep']} at ppm = {best_ugp['ppm']:.1f}  "
                  f"({ratio:.1f}x improvement; integers {best_ugp['integers']})")

    # Summary verdict
    print("\n==== STRONG UGP-NATIVE HITS (sub-0.1% ppm in UGP-integer basis) ====\n")
    if ugp_native_strong_hits:
        for obs_name, hit in ugp_native_strong_hits:
            print(f"  {obs_name}: {hit['rep']} -> {hit['ppm']:.2f} ppm   "
                  f"(integers {hit['integers']})")
    else:
        print("  None found at sub-0.1% over the extended basis with UGP-native integers only.")

    report = {
        "experiment_id": "COMP-P01-S2",
        "question": (
            "Find the truly best algebraic expression for each SM observable "
            "on an extended basis, with UGP-structural-integer flag.  "
            "Report the Pareto frontier (cost, ppm) and flag UGP-native "
            "hits at sub-0.1% as candidate new structural anchors."
        ),
        "basis_transcendentals":      list(ALL_TRANS.keys()),
        "basis_rational_num_range":   [min(SMALL_RATIONAL_NUMS), max(SMALL_RATIONAL_NUMS)],
        "basis_rational_den_range":   [min(SMALL_RATIONAL_DENS), max(SMALL_RATIONAL_DENS)],
        "cost_budget":                8,
        "ugp_native_integers":        sorted(UGP_INTEGERS),
        "distinct_expressions_count": len(exprs),
        "observables":                SM_OBSERVABLES,
        "per_observable":             per_observable,
        "ugp_native_strong_hits":     [(n, h) for (n, h) in ugp_native_strong_hits],
        "timestamp_utc":              _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }
    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False, default=list)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"\n[write] {out_path.name}")
    print(f"[sha]   {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
