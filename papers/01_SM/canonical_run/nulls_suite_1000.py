#!/usr/bin/env python3
"""
nulls_suite_1000.py — COMP-P01-A
Extends the canonical permutation-null suite from 256 -> 1000 trials per
stream (N-permutations and b-permutations).

This imports the canonical null-suite runner from UGP_GTE_SM_Verifier, so the
underlying per-trial computation is byte-identical to the 256-trial
canonical_run/nulls_suite.json:

    canonical mass pipeline + same RNG seed (1337) + same _primary_sigma metric

Only the `trials` parameter is increased. All numerical operations in
`run_stronger_nulls_suite` are deterministic at a given RNG seed.

Output: canonical_run/nulls_suite_1000.json (extended fields added).
"""

import json
import math
import os
import sys
import hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VERIFIER_DIR = os.path.join(REPO, "UGP_GTE_SM_Verifier")
sys.path.insert(0, VERIFIER_DIR)

import UGP_GTE_SM_Verifier as M  # noqa: E402


def summarize(xs):
    xs = list(xs)
    xs_sorted = sorted(xs)
    return {
        "n": len(xs),
        "min": float(xs_sorted[0]),
        "max": float(xs_sorted[-1]),
        "mean": float(sum(xs) / len(xs)),
        "median": float(xs_sorted[len(xs) // 2]),
        "p05": float(xs_sorted[int(0.05 * len(xs))]),
        "p95": float(xs_sorted[int(0.95 * len(xs))]),
    }


def main(trials: int = 1000) -> int:
    print("=" * 60)
    print(f"COMP-P01-A: Permutation-null suite @ {trials} trials per stream")
    print("=" * 60)

    result = M.run_stronger_nulls_suite(trials=trials, write_artifacts=False)

    baseline_sigma = float(result["baseline_sigma"])
    wrong_b_sigma = float(result["wrong_b_sigma"])
    perm_N_sigmas = [float(x) for x in result["perm_N_sigmas"]]
    perm_b_sigmas = [float(x) for x in result["perm_b_sigmas"]]

    assert len(perm_N_sigmas) == trials, f"expected {trials} N-perms, got {len(perm_N_sigmas)}"
    assert len(perm_b_sigmas) == trials, f"expected {trials} b-perms, got {len(perm_b_sigmas)}"

    N_summary = summarize(perm_N_sigmas)
    b_summary = summarize(perm_b_sigmas)

    min_N_sigma = N_summary["min"]
    min_b_sigma = b_summary["min"]
    min_N_ratio = min_N_sigma / baseline_sigma
    min_b_ratio = min_b_sigma / baseline_sigma

    payload = {
        "description": (
            "COMP-P01-A: 1000-permutation null suite for Paper 1 Primary-sigma "
            "goodness-of-fit. Two independent null streams: (a) perm_N - shuffle "
            "of optimized V42.1 N-values across particle names; (b) perm_b - "
            "shuffle of canonical b-indices across particle names. "
            "Identical mass pipeline and primary-sigma metric as the canonical run."
        ),
        "trials_per_stream": trials,
        "rng_seed": 1337,
        "baseline_sigma": baseline_sigma,
        "wrong_b_sigma": wrong_b_sigma,
        "perm_N_summary": N_summary,
        "perm_b_summary": b_summary,
        "min_N_sigma": min_N_sigma,
        "min_b_sigma": min_b_sigma,
        "min_N_ratio_to_baseline": min_N_ratio,
        "min_b_ratio_to_baseline": min_b_ratio,
        "mean_N_ratio_to_baseline": N_summary["mean"] / baseline_sigma,
        "mean_b_ratio_to_baseline": b_summary["mean"] / baseline_sigma,
        "perm_N_sigmas": perm_N_sigmas,
        "perm_b_sigmas": perm_b_sigmas,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "verifier_path": os.path.relpath(
            os.path.join(
                VERIFIER_DIR,
                "UGP_GTE_SM_Verifier.py",
            ),
            REPO,
        ),
    }

    out_path = os.path.join(HERE, "nulls_suite_1000.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    print()
    print("Results:")
    print(f"  Baseline sigma (canonical):     {baseline_sigma:.6e}")
    print(f"  perm_N min sigma:               {min_N_sigma:.6e}  (ratio = {min_N_ratio:.1f})")
    print(f"  perm_N mean sigma:              {N_summary['mean']:.6e}")
    print(f"  perm_N max sigma:               {N_summary['max']:.6e}")
    print(f"  perm_b min sigma:               {min_b_sigma:.6e}  (ratio = {min_b_ratio:.1f})")
    print(f"  perm_b mean sigma:              {b_summary['mean']:.6e}")
    print(f"  perm_b max sigma:               {b_summary['max']:.6e}")
    print()
    print(f"  -> 0 of {trials} N-permutations score within a factor of {min_N_ratio:.0f} of the canonical result")
    print(f"  -> 0 of {trials} b-permutations score within a factor of {min_b_ratio:.0f} of the canonical result")
    print()
    print(f"  Output: {out_path}")
    print(f"  SHA-256: {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
