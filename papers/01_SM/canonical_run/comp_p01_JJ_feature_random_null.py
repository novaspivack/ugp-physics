#!/usr/bin/env python3
"""
COMP-P01-JJ: Feature-randomization null for the per-sector mass-matrix closure
(09_SPEC, diagnostic for COMP-P01-II).

II closed each charged-fermion sector to ≤ 0.05% max-frac-err at D=3 using the
UGP-derived triples (a, b, c) of the physical fermions.  The naive atom-label
null in II is statistically under-powered: it draws only 1000 samples from a
space where structural hit density is ~10⁻⁶.

JJ runs the *right* null: for N=30 trials, each trial replaces the 3 × 3
per-generation feature vectors (one vector per generation per sector) with
random draws from distributions matching the real features' ranges, rebuilds
the 32-kernel library from those random features, and re-runs the full D=3
per-sector scan (59 scalar atoms, 32 kernels, 967M combos per sector in 3
sectors).  We record: (i) the best per-sector max-frac-err for each trial and
(ii) the number of trials that achieve ≤ 1% closure in any sector.

If random features routinely close at ≤ 1%: II's result is volume-driven, not
structural.  If random features consistently fail (> few % floor): the real
UGP triples encode physically relevant structure and II's closure is real.

Expected wall clock on 12 cores: ~75 min (30 trials × 150 s/trial).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import numpy as np
from multiprocessing import Pool, cpu_count

from comp_p01_HH_mass_matrix_paradigm_deep import (
    SCALAR_NAMES, SCALAR_VALUES, CHARGED_FERMIONS,
    build_kernel_library, feature_vec, pdg_by_sector, PHI,
)
from comp_p01_II_mass_matrix_per_sector import _worker_scan_single_sector


def _real_feature_ranges() -> Dict[str, Tuple[float, float]]:
    """Extract min/max for each feature across all 9 fermions."""
    feats = [feature_vec(f[1], f[3]) for f in CHARGED_FERMIONS]
    keys = feats[0].keys()
    ranges = {}
    for k in keys:
        vals = [f[k] for f in feats]
        ranges[k] = (min(vals), max(vals))
    return ranges


def random_feature_vector(rng: random.Random, ranges: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    f: Dict[str, float] = {}
    for k, (lo, hi) in ranges.items():
        if k in ("mu_a", "mu_b", "mu_c"):
            f[k] = rng.choice([-1.0, 0.0, 1.0])
        elif k == "mu_prod":
            f[k] = rng.choice([-1.0, 0.0, 1.0])
        elif k == "chi":
            f[k] = rng.choice([0.0, 1.0])
        elif k == "sign_c":
            f[k] = rng.choice([-1.0, 1.0])
        elif k == "gen":
            f[k] = float(rng.choice([1, 2, 3]))
        elif k == "gen2":
            f[k] = f.get("gen", 1.0) ** 2 if "gen" in f else float(rng.choice([1, 4, 9]))
        elif k == "fib_g":
            f[k] = float(rng.choice([1, 1, 2, 3, 5]))
        elif k == "lucas_g":
            f[k] = float(rng.choice([2, 1, 3, 4, 7]))
        elif k == "phi_g":
            f[k] = rng.uniform(lo, hi)
        elif k == "inv_phi_g":
            f[k] = rng.uniform(lo, hi)
        elif k == "inv_phi_galois_g":
            f[k] = rng.uniform(lo, hi)
        else:
            f[k] = rng.uniform(lo, hi)
    return f


def run_one_trial(trial_idx: int, ranges, pdg, kernel_names, n_workers, D: int = 3) -> Dict:
    rng = random.Random(10**6 + trial_idx)
    sector_feats = {
        s: [random_feature_vector(rng, ranges) for _ in range(3)] for s in ("lepton", "up_type", "down_type")
    }
    K_by_sector = {s: build_kernel_library(sector_feats[s]) for s in sector_feats}
    results: Dict[str, Dict] = {}
    t0 = time.time()
    subsets = list(itertools.combinations(kernel_names, D))
    for sector in ("lepton", "up_type", "down_type"):
        pdg_sorted = np.sort(pdg[sector])
        args_iter = [(ks, K_by_sector[sector], pdg_sorted, D, sector, 0.01, 1) for ks in subsets]
        best = math.inf
        closures = 0
        best_rec = None
        with Pool(n_workers) as pool:
            for res in pool.imap_unordered(_worker_scan_single_sector, args_iter, chunksize=1):
                closures += res["closures_at_eps"]
                if res["best_max_frac"] < best:
                    best = res["best_max_frac"]
                    best_rec = res["top_k"][0]
        results[sector] = {
            "best_max_frac": best,
            "closures_at_1pct": closures,
            "best_candidate": best_rec,
        }
    results["elapsed_seconds"] = time.time() - t0
    return results


def main(n_trials: int = 30) -> Dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pdg = pdg_by_sector()
    # use an arbitrary sector_feats just to read kernel names
    feats0 = [feature_vec(f[1], f[3]) for f in CHARGED_FERMIONS[:3]]
    kernel_names = list(build_kernel_library(feats0).keys())
    ranges = _real_feature_ranges()
    nw = min(12, cpu_count())

    trials: List[Dict] = []
    t0 = time.time()
    for i in range(n_trials):
        r = run_one_trial(i, ranges, pdg, kernel_names, nw)
        summary = {s: {"best_max_frac": r[s]["best_max_frac"], "closures_at_1pct": r[s]["closures_at_1pct"]} for s in ("lepton", "up_type", "down_type")}
        trials.append({"trial": i, "summary": summary, "best_candidates": {s: r[s]["best_candidate"] for s in ("lepton","up_type","down_type")}})
        print(
            f"[JJ] trial {i+1}/{n_trials}: lepton {r['lepton']['best_max_frac']:.4g} (cl={r['lepton']['closures_at_1pct']})  "
            f"up {r['up_type']['best_max_frac']:.4g} (cl={r['up_type']['closures_at_1pct']})  "
            f"down {r['down_type']['best_max_frac']:.4g} (cl={r['down_type']['closures_at_1pct']})  "
            f"[{r['elapsed_seconds']:.0f}s, total {time.time()-t0:.0f}s]", flush=True
        )

    per_sector_bests = {s: [t["summary"][s]["best_max_frac"] for t in trials] for s in ("lepton", "up_type", "down_type")}
    per_sector_close_1pct = {s: sum(1 for t in trials if t["summary"][s]["best_max_frac"] <= 0.01) for s in per_sector_bests}
    per_sector_close_2pct = {s: sum(1 for t in trials if t["summary"][s]["best_max_frac"] <= 0.02) for s in per_sector_bests}
    per_sector_close_5pct = {s: sum(1 for t in trials if t["summary"][s]["best_max_frac"] <= 0.05) for s in per_sector_bests}
    per_sector_stats = {
        s: {
            "median": float(np.median(per_sector_bests[s])),
            "min": float(np.min(per_sector_bests[s])),
            "max": float(np.max(per_sector_bests[s])),
            "mean": float(np.mean(per_sector_bests[s])),
            "p10": float(np.percentile(per_sector_bests[s], 10)),
        }
        for s in per_sector_bests
    }

    any_close_1pct = any(per_sector_close_1pct[s] > 0 for s in per_sector_close_1pct)
    if any_close_1pct:
        # Count by trial: did ANY sector close in the SAME trial?
        joint_close_trials = sum(
            1 for t in trials if any(t["summary"][s]["best_max_frac"] <= 0.01 for s in ("lepton", "up_type", "down_type"))
        )
    else:
        joint_close_trials = 0

    prediction_block = {
        "comp_id": "COMP-P01-JJ",
        "spec_reference": "09_SPEC — feature-randomization null for COMP-P01-II",
        "purpose": "Test whether per-sector D=3 closures found by II depend on the UGP-derived per-fermion triples, or are a volume effect of the 59×32 library.",
        "timestamp_utc": timestamp,
        "n_trials": n_trials,
        "trials": trials,
        "per_sector_best_max_frac_across_trials": per_sector_bests,
        "per_sector_statistics": per_sector_stats,
        "per_sector_close_rates": {
            "1pct": per_sector_close_1pct,
            "2pct": per_sector_close_2pct,
            "5pct": per_sector_close_5pct,
        },
        "joint_close_trials_at_1pct": joint_close_trials,
    }

    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    if any_close_1pct:
        verdict = f"WEAKENS_II: random features also close in {joint_close_trials}/{n_trials} trials"
    else:
        # Compare random-feature floor to II's ~0.05% floor
        worst_random_median = max(per_sector_stats[s]["median"] for s in per_sector_stats)
        if worst_random_median > 0.05:
            verdict = "CONFIRMS_II: random features fail (median > 5%) while real UGP features close at <0.05%"
        else:
            verdict = "AMBIGUOUS: random features don't close at 1% but get close at few-pct level"

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "any_random_trial_closes_1pct": any_close_1pct,
        "joint_close_trials_at_1pct": joint_close_trials,
        "per_sector_close_rates": prediction_block["per_sector_close_rates"],
        "per_sector_statistics": per_sector_stats,
        "verdict": verdict,
    }
    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    out = main(n_trials=n)
    path = "comp_p01_JJ_feature_random_null.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
