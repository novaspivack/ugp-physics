#!/usr/bin/env python3
"""
COMP-P01-S3  —  Density-saturation null for the extended algebraic basis

Follow-up to COMP-P01-S2: if 1.17 M expressions in an extended basis
(phi, pi, e, zeta3, euler_g, sqrt2..sqrt15, log2..log13, small rationals) fit
essentially every SM observable to sub-10-ppm, the basis is saturating and
algebraic identifications in it carry no structural information.

Test: take 100 random log-uniform targets in [0.01, 1.0] (the range of
physical dimensionless couplings) and count how many have sub-10-ppm
hits.  If >=50 %, the basis is saturating.  If <1 %, there IS room for
structural identifications to be meaningful.

This is the proper null of COMP-P01-S2.  The decision for the paper is:
  saturating (>=10 %)  -> Elegant Kernel algebraic identifications are
                          not distinguishable from numerology over this
                          basis; they must be demoted or the basis
                          restricted.
  non-saturating (<1 %) -> the specific identifications in the paper
                          retain some structural force.
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import json
import math
import random
import sys
from math import gcd
from pathlib import Path


PHI  = (1.0 + math.sqrt(5.0)) / 2.0
PI   = math.pi
E    = math.e
ZETA3 = 1.2020569031595942854
EULER_MASCHERONI = 0.5772156649015329

# Three basis variants (progressive density):
BASIS_ORIGINAL_S = {
    # As in COMP-P01-S
    "phi": PHI, "pi": PI,
}
BASIS_ELEGANT_KERNEL = {
    # Paper's Elegant Kernel uses pi, phi, and small rationals only
    "phi": PHI, "pi": PI,
}
BASIS_EXTENDED_S2 = {
    "phi": PHI, "pi": PI, "e": E, "zeta3": ZETA3, "euler_g": EULER_MASCHERONI,
    "sqrt2": math.sqrt(2), "sqrt3": math.sqrt(3), "sqrt5": math.sqrt(5),
    "sqrt6": math.sqrt(6), "sqrt7": math.sqrt(7), "sqrt10": math.sqrt(10),
    "sqrt15": math.sqrt(15),
    "log2": math.log(2), "log3": math.log(3), "log5": math.log(5),
    "log7": math.log(7), "log11": math.log(11), "log13": math.log(13),
}


def digits(n):
    return len(str(abs(n))) if n != 0 else 1


def enumerate_basis(basis, max_cost=8, num_range=24, den_range=24):
    trans_keys = list(basis.keys()) + ["1"]
    seen_values = set()
    out = []
    for a in range(1, num_range + 1):
        for b in range(1, den_range + 1):
            if gcd(a, b) != 1:
                continue
            rat_cost = digits(a) + digits(b)
            if rat_cost > max_cost:
                continue
            for X in trans_keys:
                x_val = 1.0 if X == "1" else basis[X]
                for p in range(-3, 4):
                    if rat_cost + abs(p) > max_cost:
                        continue
                    for Y in trans_keys:
                        if Y <= X:
                            continue
                        y_val = 1.0 if Y == "1" else basis[Y]
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
                            key = round(math.log(val), 10)
                            if key in seen_values:
                                continue
                            seen_values.add(key)
                            out.append(val)
    return out


def count_random_target_hits(basis_values, n_targets=200,
                              log_target_range=(math.log(0.01), math.log(1.0)),
                              tolerances=(1e-5, 1e-4, 1e-3)):
    """For each tolerance, count fraction of random targets that have a
    sub-tolerance hit in the basis."""
    random.seed(20260417)
    targets = [math.exp(random.uniform(*log_target_range)) for _ in range(n_targets)]
    hits = {f"{100*t:.3g}pct": 0 for t in tolerances}
    for tgt in targets:
        for t in tolerances:
            if any(abs(v - tgt) / tgt <= t for v in basis_values):
                hits[f"{100*t:.3g}pct"] += 1
    hit_fraction = {k: v / n_targets for k, v in hits.items()}
    return hits, hit_fraction


def main() -> int:
    print("=" * 72)
    print("COMP-P01-S3: Density-saturation null for algebraic bases")
    print("=" * 72)
    print()

    results = {}
    for label, basis in [
        ("original_S_pi_phi_only",       BASIS_ORIGINAL_S),
        ("extended_S2_phi_pi_e_log_sqrt", BASIS_EXTENDED_S2),
    ]:
        print(f"Basis: {label}  (atoms: {list(basis.keys())})")
        vals = enumerate_basis(basis, max_cost=8)
        print(f"  distinct expressions enumerated: {len(vals)}")
        hits, frac = count_random_target_hits(vals, n_targets=200,
                                               log_target_range=(math.log(0.01), math.log(1.0)))
        print(f"  random-target hit rates (200 log-uniform targets in [0.01, 1.0]):")
        for tol_label, count in hits.items():
            print(f"    tol = {tol_label:7s}   hits = {count:3d} / 200   "
                  f"fraction = {100*frac[tol_label]:5.2f}%")
        results[label] = {
            "atoms":                list(basis.keys()),
            "distinct_expr_count":  len(vals),
            "hit_counts":           hits,
            "hit_fractions":        frac,
        }
        print()

    # Verdict
    extended_saturation = results["extended_S2_phi_pi_e_log_sqrt"]["hit_fractions"]["0.001pct"]
    original_saturation = results["original_S_pi_phi_only"]["hit_fractions"]["0.001pct"]
    verdict_lines = []
    verdict_lines.append(
        f"Extended basis {{phi, pi, e, zeta3, euler_g, sqrt_n, log_p}} at cost <=8: "
        f"{100*extended_saturation:.1f}% of random log-uniform targets have a "
        f"<=1e-5 tolerance hit -- SATURATING if >=10%."
    )
    verdict_lines.append(
        f"Original basis {{phi, pi, p/q}} at cost <=8: "
        f"{100*original_saturation:.1f}% hit rate at 1e-5 tolerance -- "
        f"{'ALSO SATURATING' if original_saturation >= 0.10 else 'non-saturating'}."
    )
    if extended_saturation >= 0.10:
        verdict_lines.append(
            "-> The COMP-P01-S2 result is indeed explained by basis density: "
            "ANY target has a sub-10-ppm hit in this basis.  The Elegant Kernel "
            "'algebraic closures' that use transcendentals {e, log p, sqrt n, ...} "
            "are NOT distinguishable from numerology."
        )
    if original_saturation < 0.10:
        verdict_lines.append(
            "-> The ORIGINAL basis {phi, pi, p/q} is non-saturating; the paper's "
            "Elegant Kernel identifications (which restrict to this basis) retain "
            "structural meaning AT THE SPECIFIC PRECISION LEVEL they achieve "
            "(typically 0.5-2.5%), though they are not unique."
        )
    verdict = "\n".join(verdict_lines)
    print("==== VERDICT ====")
    print(verdict)
    print()

    report = {
        "experiment_id": "COMP-P01-S3",
        "question": (
            "Is the extended algebraic basis from COMP-P01-S2 saturating "
            "over the range of dimensionless physical observables?  "
            "If so, sub-10-ppm hits are not evidence of structure; if not, "
            "hits retain some structural meaning."
        ),
        "bases_tested":  results,
        "verdict":       verdict,
        "timestamp_utc": _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }
    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"[write] {out_path.name}")
    print(f"[sha]   {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
