#!/usr/bin/env python3
"""
COMP-P01-X2 — Phase 1.5 narrow-basis saturation null for THM-UCL-1.

Target: k_gen² = −φ/2 from Fibonacci companion-matrix spectrum on GTE
even step.

Criterion (E) sparsity test:  is the sub-basis {φ, small rationals} sparse
enough at the claimed precision (~0.03%, i.e., the dual-path convergence
deviation for this coefficient) to rule out numerology?

Also runs the rigidity scan (criterion D): enumerate nearby algebraic
expressions in {φ, p/q, φ^k} and identify how many match the empirical
value at the dual-path precision.

The empirical k_gen² is -0.80925 (from the UCL2.3 fit).
The theoretical claim is -φ/2 = -0.80901699...
Deviation: (-0.80902 - -0.80925)/(-0.80925) = 0.000285 = 28.5 ppm
           or 0.0285%.
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import itertools
import json
import math
import random
import sys
from fractions import Fraction
from math import gcd
from pathlib import Path


PHI = (1.0 + math.sqrt(5.0)) / 2.0
K_GEN2_EMPIRICAL = -0.80925      # UCL2.3 calibrated value
K_GEN2_THEORETICAL = -PHI / 2.0  # Elegant Kernel claim

# Tolerance for "match": the dual-path deviation between empirical and
# theoretical is 0.03%, so we use 0.05% as a generous match window.
MATCH_TOL = 5e-4     # 0.05 % = 500 ppm


def enumerate_narrow_basis():
    """Enumerate algebraic expressions of the form (p/q) * φ^k for
    small rationals (p/q) (coprime, with |p|,q <= 16) and k ∈ {-3,…,+3}.

    Returns a list of (rep, value) pairs.
    """
    results = []
    for p in range(-16, 17):
        for q in range(1, 17):
            if p == 0 or gcd(abs(p), q) != 1:
                if p == 0:
                    continue
                if gcd(abs(p), q) != 1:
                    continue
            ratio = p / q
            for k in range(-3, 4):
                v = ratio * (PHI ** k)
                rep = f"({p}/{q})·φ^{k}" if k != 0 else f"({p}/{q})"
                results.append((rep, v))
    return results


def enumerate_random_targets(n: int, low: float = -5.0, high: float = 5.0, seed: int = 20260417):
    random.seed(seed)
    return [random.uniform(low, high) for _ in range(n)]


def count_saturation(basis, targets, tolerances):
    """For each tolerance, count fraction of targets that have a basis
    match at that relative tolerance."""
    results = {}
    for tol_rel in tolerances:
        hits = 0
        for t in targets:
            if t == 0:
                continue
            for rep, v in basis:
                if abs(v - t) / abs(t) <= tol_rel:
                    hits += 1
                    break
        results[tol_rel] = hits / len(targets)
    return results


def closest_basis_matches(basis, target, n: int = 10):
    """Return the top-n basis expressions closest to target."""
    scored = [(rep, v, abs(v - target) / abs(target) if target != 0 else float("inf"))
              for rep, v in basis]
    scored.sort(key=lambda x: x[2])
    return scored[:n]


def main() -> int:
    print("=" * 72)
    print("COMP-P01-X2 — Phase 1.5 narrow-basis saturation null for k_gen²")
    print("=" * 72)
    print()
    print(f"φ = (1+√5)/2 = {PHI:.10f}")
    print(f"Empirical k_gen² (UCL2.3)    = {K_GEN2_EMPIRICAL:+.10f}")
    print(f"Theoretical k_gen² = −φ/2    = {K_GEN2_THEORETICAL:+.10f}")
    dev = abs(K_GEN2_THEORETICAL - K_GEN2_EMPIRICAL) / abs(K_GEN2_EMPIRICAL)
    print(f"Dual-path deviation          = {100*dev:.4f}% = {1e6*dev:.1f} ppm")
    print()

    basis = enumerate_narrow_basis()
    print(f"Narrow basis: {{(p/q)·φ^k : |p|,q ≤ 16, k ∈ [-3,+3]}}")
    print(f"  total expressions: {len(basis)}")
    print()

    # Closest matches to the empirical value
    print("--- Criterion (D): closest basis expressions to EMPIRICAL k_gen² = -0.80925 ---")
    closest_emp = closest_basis_matches(basis, K_GEN2_EMPIRICAL, 15)
    for rep, v, rel in closest_emp:
        print(f"  {rep:20s}  value = {v:+.8f}   rel dev = {rel*1e6:10.1f} ppm ({100*rel:.4f}%)")
    print()

    # Saturation null
    n_targets = 2000
    targets = enumerate_random_targets(n_targets, low=-5.0, high=5.0)
    # Filter zero and very small targets to avoid division artifacts
    targets = [t for t in targets if abs(t) > 0.05]
    print(f"--- Criterion (E): saturation null over {len(targets)} random uniform targets in [-5, 5] ---")
    tolerances = [1e-6, 1e-5, 1e-4, 5e-4, 1e-3, 1e-2, 5e-2]
    sat = count_saturation(basis, targets, tolerances)
    for tol in tolerances:
        print(f"  tol = {tol:8.1e}   saturation = {100*sat[tol]:6.2f}%")
    print()

    # Rigidity: enumerate nearby "obvious" alternatives and compute their deviations
    phi = PHI
    alts = {
        "-φ/2":           -phi/2,
        "-1/(2φ)":        -1/(2*phi),
        "-φ²/4":          -phi*phi/4,
        "-(φ−1)":         -(phi - 1),
        "-(1+φ)/4":       -(1 + phi)/4,
        "-(3+√5)/8":      -(3 + math.sqrt(5))/8,
        "-(φ²+1)/(2φ+2)": -(phi*phi + 1)/(2*phi + 2),
        "-3/(1+2·φ)":     -3/(1 + 2*phi),
        "-sin(π/2)*φ/2":  -math.sin(math.pi/2) * phi / 2,   # simplifies to -φ/2
        "-φ·cos(0)/2":    -phi * math.cos(0) / 2,           # simplifies to -φ/2
    }
    print("--- Criterion (D): rigidity — nearby structural alternatives ---")
    for name, val in alts.items():
        rel = abs(val - K_GEN2_EMPIRICAL) / abs(K_GEN2_EMPIRICAL)
        print(f"  {name:25s}  value = {val:+.8f}   rel dev from empirical = {rel*1e6:10.1f} ppm")
    print()

    # Honest interpretation
    # Count how many basis expressions match at MATCH_TOL=0.05%
    n_matches = sum(1 for rep, v in basis
                    if abs(v - K_GEN2_EMPIRICAL) / abs(K_GEN2_EMPIRICAL) <= MATCH_TOL)
    n_matches_strict = sum(1 for rep, v in basis
                           if abs(v - K_GEN2_EMPIRICAL) / abs(K_GEN2_EMPIRICAL) <= 1e-4)
    print(f"Basis expressions matching empirical k_gen² within {MATCH_TOL*100}%:  {n_matches} / {len(basis)}")
    print(f"Basis expressions matching within 0.01% (100 ppm):                    {n_matches_strict} / {len(basis)}")
    print()

    if n_matches_strict == 1 and sat[1e-4] < 0.05:
        verdict = ("PASS (strong): target matches basis uniquely at 100 ppm precision; "
                   "narrow basis is non-saturating at this level.")
    elif n_matches <= 2 and sat[5e-4] < 0.15:
        verdict = ("PASS (moderate): target matches basis at 0.05% with 1-2 candidates; "
                   "narrow basis is non-saturating but not categorically sparse.")
    else:
        verdict = ("MARGINAL or FAIL: multiple basis expressions match within claimed "
                   "precision; narrow basis may be saturating at target resolution.")

    report = {
        "experiment_id":            "COMP-P01-X2",
        "question":                 "Narrow-basis saturation null for THM-UCL-1 (k_gen² = −φ/2).",
        "basis_spec":               "(p/q) · φ^k for coprime p/q with |p|,q ≤ 16, k ∈ [-3, +3]",
        "basis_cardinality":        len(basis),
        "phi":                      PHI,
        "empirical_k_gen2":         K_GEN2_EMPIRICAL,
        "theoretical_k_gen2":       K_GEN2_THEORETICAL,
        "dual_path_deviation":      dev,
        "closest_basis_matches":    [(r, v, rel) for r, v, rel in closest_emp],
        "saturation_null":          {f"{t:.1e}": sat[t] for t in tolerances},
        "nearby_structural_alternatives": {k: v for k, v in alts.items()},
        "n_matches_within_500_ppm": n_matches,
        "n_matches_within_100_ppm": n_matches_strict,
        "verdict":                  verdict,
        "timestamp_utc":            _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }

    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"[write] {out_path.name}")
    print(f"[sha]   {sha}")
    print()
    print(f"VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
