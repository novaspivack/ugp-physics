#!/usr/bin/env python3
"""
COMP-P01-RC1: Higgs lambda bounded-uniqueness enumeration.

SP-E1 of EPIC 13. Mirrors SP-D but targets the Higgs quartic coupling
  lambda_SM(M_Z pole) ~ 0.1294   (empirical target)
  lambda_UGP = phi / (4 pi)      ~ 0.12876  (UGP claim, P01 Eq 5.7 / eq:lambda_higgs)

Question: is phi/(4 pi) the unique depth-<=3 minimum-residual expression
over UGP-structural atoms for the observed Higgs lambda, or is the match
density-dominated?

Reuses the enumerate_up_to / rank_exprs_for_target machinery from SP-D.
"""

from __future__ import annotations
import hashlib
import json
import math
import os
import random
import sys
import time

# Import the enumerator from the URC SP-D script so we only maintain it once
sys.path.insert(0, os.path.dirname(__file__))
from comp_p01_RC1_urc_bounded_enumeration import (  # type: ignore
    UGP_ATOMS,
    enumerate_up_to,
    rank_exprs_for_target,
    relative_residual,
    find_rank_of,
    randomized_atoms,
    PHI,
)

FOUR_PI = 4.0 * math.pi

# Higgs target: PDG-consistent SM Higgs quartic at the Z pole
# (cf.\ P01 Eq 5.7 and eq:lambda_higgs -- lambda_SM^{Z-pole} ~ 0.1294)
HIGGS_LAMBDA_EMPIRICAL = 0.1294
HIGGS_LAMBDA_UGP_CLAIM = PHI / FOUR_PI  # ~0.12876

TARGET = {
    "name": "higgs_lambda",
    "empirical": HIGGS_LAMBDA_EMPIRICAL,
    "ugp_claim_str": "phi / (4 * pi)  [NOT enumerable -- 4 pi is analytic, not in atom set]",
    "ugp_claim_val": HIGGS_LAMBDA_UGP_CLAIM,
}


def _atom_set_with_pi() -> dict[str, float]:
    """Higgs lambda involves 4 pi from gauge-coupling normalisation.
    Extend the UGP atom set with pi and 4 pi as depth-0 atoms so phi/(4 pi)
    is reachable at depth 1.
    """
    atoms = dict(UGP_ATOMS)
    atoms["pi"] = math.pi
    atoms["four_pi"] = FOUR_PI
    atoms["two_pi"] = 2.0 * math.pi
    return atoms


def _randomized_with_pi(rng: random.Random) -> dict[str, float]:
    out = randomized_atoms(rng)
    # pi is a mathematical constant, not UGP-specific.  For null purposes,
    # we keep pi and its multiples intact (they are "operator-supplied").
    out["pi"] = math.pi
    out["four_pi"] = FOUR_PI
    out["two_pi"] = 2.0 * math.pi
    return out


def source_sha256() -> str:
    with open(__file__, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    max_depth = 3
    n_null_trials = 30
    top_n = 50

    t0 = time.time()
    precommit_sha = source_sha256()

    results = {
        "experiment_id": "COMP-P01-RC1-HL",
        "title": "Higgs lambda bounded-uniqueness enumeration over UGP+pi atoms",
        "epic": "EPIC_CLUSTER13_REFEREE_CLOSURE / SP-E1",
        "pre_commit_sha256": precommit_sha,
        "config": {
            "max_depth": max_depth,
            "n_null_trials": n_null_trials,
            "atoms": _atom_set_with_pi(),
            "target": TARGET,
        },
    }

    atoms = _atom_set_with_pi()
    print(f"[{time.time()-t0:.1f}s] Enumerating up to depth {max_depth} over {len(atoms)} atoms...", file=sys.stderr)
    ugp_exprs = enumerate_up_to(max_depth, atoms)
    print(f"[{time.time()-t0:.1f}s]   Got {len(ugp_exprs)} distinct expressions.", file=sys.stderr)
    results["n_expressions_ugp"] = len(ugp_exprs)

    ranked = rank_exprs_for_target(ugp_exprs, TARGET["empirical"], top_n=top_n)
    ugp_rank = find_rank_of(TARGET["ugp_claim_val"], ranked)
    ugp_residual_pct = 100.0 * relative_residual(TARGET["ugp_claim_val"], TARGET["empirical"])
    best = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None
    gap = (second["residual_pct"] / best["residual_pct"]) if (best and second and best["residual_pct"] > 0) else None

    results["ugp_ranking"] = {
        "target_empirical": TARGET["empirical"],
        "ugp_claim_val": TARGET["ugp_claim_val"],
        "ugp_claim_residual_pct": ugp_residual_pct,
        "ugp_claim_rank_in_top_n": ugp_rank,
        "top_n_considered": top_n,
        "best_expr": best,
        "second_best_expr": second,
        "second_over_best_residual_ratio": gap,
        "top_10": ranked[:10],
    }

    # Null
    print(f"[{time.time()-t0:.1f}s] Running {n_null_trials} null trials...", file=sys.stderr)
    rng = random.Random(20260423)
    null_residuals: list[float] = []
    for trial in range(n_null_trials):
        null_atoms = _randomized_with_pi(rng)
        null_exprs = enumerate_up_to(max_depth, null_atoms)
        null_ranked = rank_exprs_for_target(null_exprs, TARGET["empirical"], top_n=1)
        if null_ranked:
            null_residuals.append(null_ranked[0]["residual_pct"])
        if (trial + 1) % 5 == 0:
            print(f"[{time.time()-t0:.1f}s]   null trial {trial+1}/{n_null_trials}", file=sys.stderr)
    null_residuals.sort()
    better = sum(1 for r in null_residuals if r <= ugp_residual_pct)
    results["null_statistics"] = {
        "ugp_residual_pct": ugp_residual_pct,
        "n_null_trials": len(null_residuals),
        "null_median_residual_pct": null_residuals[len(null_residuals)//2] if null_residuals else None,
        "null_min_residual_pct": null_residuals[0] if null_residuals else None,
        "null_trials_at_or_below_ugp_residual": better,
        "null_better_than_ugp_pct": 100.0 * better / max(len(null_residuals), 1),
    }

    # Gate
    null_better_pct = results["null_statistics"]["null_better_than_ugp_pct"]
    if ugp_rank == 0 and gap is not None and gap >= 2.0 and null_better_pct <= 10.0:
        gate = "A"
    elif ugp_rank is not None and ugp_rank < 10:
        gate = "B"
    else:
        gate = "C"
    results["gate"] = gate
    results["runtime_seconds"] = time.time() - t0

    tmp = json.dumps(results, sort_keys=True, default=str).encode("utf-8")
    results["post_commit_sha256"] = hashlib.sha256(tmp).hexdigest()

    out_path = os.path.join(os.path.dirname(__file__), "comp_p01_RC1_higgs_lambda_uniqueness.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{time.time()-t0:.1f}s] Wrote {out_path}", file=sys.stderr)

    print(json.dumps({
        "pre_commit_sha256": precommit_sha,
        "post_commit_sha256": results["post_commit_sha256"],
        "n_expressions": results["n_expressions_ugp"],
        "gate": gate,
        "ugp_rank_in_top_50": ugp_rank,
        "ugp_residual_pct": ugp_residual_pct,
        "best_expr": best["expr"] if best else None,
        "best_residual_pct": best["residual_pct"] if best else None,
        "second_over_best_ratio": gap,
        "null_better_than_ugp_pct": null_better_pct,
        "null_median_residual_pct": results["null_statistics"]["null_median_residual_pct"],
        "top_10": ranked[:10],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
