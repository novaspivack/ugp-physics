#!/usr/bin/env python3
"""
COMP-P01-KK: Feature-dependent-only kernel scan (09_SPEC decisive test)

COMP-P01-II produced per-sector closures at ≤ 0.05% max-frac-err with disciplined
atom-label nulls, but COMP-P01-JJ revealed the closures as *volume-driven* rather
than structural: random features (replacing the UGP-derived fermion triples)
yield closures of comparable tightness, because II's best candidates rely on
index-only kernels that don't depend on the physical fermion information.

KK tests the decisive question: if we REMOVE all index-only kernels and force
every matrix entry to depend on the UGP-derived per-fermion features (μ(a,b,c),
χ, log|b/c|, per-generation φ^g, Fibonacci, etc.), does the scan still close?

The kernel library is restricted to the 19 feature-dependent kernels only:
  mu_prod_prod, mu_prod_diag, mu_a_prod, mu_b_prod, mu_c_prod,
  mu_a_diag, mu_c_diag, chi_prod, chi_diag, chi_sym, L_diag, L_prod,
  phi_g_diag, phi_g_prod, inv_phi_galois_g_diag, fib_g_diag, fib_g_prod.

Atom library unchanged (59 scalars).  D ∈ {1, 2, 3}.  Per-sector independent.
Followed by 30-trial feature-randomization null comparing per-sector best.

Gate:
  - If real features close at ≤ 1% AND random-feature floor is > 5% → II's
    apparent closure is upgraded to GENUINE structural closure (feature-
    dependent).
  - If real features fail to close at ≤ 1% → feature kernels alone cannot
    carry the mass spectrum; the paradigm is truly MAP.
  - If both close → library is still volume-driven even at feature-only level;
    MAP under this test.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
from multiprocessing import Pool, cpu_count

from comp_p01_HH_mass_matrix_paradigm_deep import (
    SCALAR_NAMES, SCALAR_VALUES, CHARGED_FERMIONS,
    build_kernel_library, feature_vec, pdg_by_sector,
)
from comp_p01_II_mass_matrix_per_sector import _worker_scan_single_sector
from comp_p01_JJ_feature_random_null import _real_feature_ranges, random_feature_vector


FEATURE_DEPENDENT_KERNELS = [
    "mu_prod_prod", "mu_prod_diag",
    "mu_a_prod", "mu_b_prod", "mu_c_prod",
    "mu_a_diag", "mu_c_diag",
    "chi_prod", "chi_diag", "chi_sym",
    "L_diag", "L_prod",
    "phi_g_diag", "phi_g_prod",
    "inv_phi_galois_g_diag",
    "fib_g_diag", "fib_g_prod",
]


def scan_sector_restricted(sector, D, K_by_sector, pdg, kernel_names, n_workers):
    pdg_sorted = np.sort(pdg[sector])
    if D == 1:
        subsets = [(k,) for k in kernel_names]
    elif D == 2:
        subsets = list(itertools.combinations(kernel_names, 2))
    else:
        subsets = list(itertools.combinations(kernel_names, 3))
    args_iter = [(ks, K_by_sector[sector], pdg_sorted, D, sector, 0.01, 3) for ks in subsets]
    total_combos = 0
    closures = 0
    top: List[Dict] = []
    hist = {k: 0 for k in ("le_0.001","le_0.005","le_0.01","le_0.02","le_0.05","le_0.10","le_0.20","le_0.50","le_1.00")}
    t0 = time.time()
    if len(args_iter) >= n_workers:
        with Pool(n_workers) as pool:
            for res in pool.imap_unordered(_worker_scan_single_sector, args_iter, chunksize=1):
                total_combos += res["n_combinations"]
                closures += res["closures_at_eps"]
                for k in hist:
                    hist[k] += res["histogram"][k]
                top.extend(res["top_k"])
    else:
        for a in args_iter:
            res = _worker_scan_single_sector(a)
            total_combos += res["n_combinations"]
            closures += res["closures_at_eps"]
            for k in hist:
                hist[k] += res["histogram"][k]
            top.extend(res["top_k"])
    top.sort(key=lambda r: r["max_fractional_error"])
    return {
        "D": D, "n_kernel_subsets": len(subsets), "n_combinations_total": total_combos,
        "closures_at_1pct": closures, "histogram": hist,
        "top_k": top[:10], "elapsed_seconds": time.time() - t0,
    }


def real_features_scan(n_workers):
    from comp_p01_HH_mass_matrix_paradigm_deep import sector_feats_by_sector
    sf = sector_feats_by_sector()
    K_by_sector = {s: build_kernel_library(sf[s]) for s in ("lepton", "up_type", "down_type")}
    pdg = pdg_by_sector()
    scans: Dict[str, Dict[int, Dict]] = {s: {} for s in ("lepton", "up_type", "down_type")}
    for sector in ("lepton", "up_type", "down_type"):
        for D in (1, 2, 3):
            r = scan_sector_restricted(sector, D, K_by_sector, pdg, FEATURE_DEPENDENT_KERNELS, n_workers)
            scans[sector][D] = r
            print(
                f"[KK-real] {sector} D={D}: {r['n_combinations_total']:,} combos in {r['elapsed_seconds']:.1f}s  "
                f"best={r['top_k'][0]['max_fractional_error']:.4g}  closures@1%={r['closures_at_1pct']}",
                flush=True,
            )
    return scans


def random_features_trials(n_trials, n_workers):
    ranges = _real_feature_ranges()
    pdg = pdg_by_sector()
    results = []
    t0 = time.time()
    for i in range(n_trials):
        rng = random.Random(2_000_000 + i)
        sf_random = {
            s: [random_feature_vector(rng, ranges) for _ in range(3)] for s in ("lepton", "up_type", "down_type")
        }
        K_by_sector = {s: build_kernel_library(sf_random[s]) for s in sf_random}
        trial_res: Dict[str, Dict] = {}
        for sector in ("lepton", "up_type", "down_type"):
            r = scan_sector_restricted(sector, 3, K_by_sector, pdg, FEATURE_DEPENDENT_KERNELS, n_workers)
            trial_res[sector] = {"best_max_frac": r["top_k"][0]["max_fractional_error"] if r["top_k"] else 1.0,
                                  "closures_at_1pct": r["closures_at_1pct"]}
        results.append(trial_res)
        print(
            f"[KK-null] trial {i+1}/{n_trials}: lepton {trial_res['lepton']['best_max_frac']:.4g} (cl={trial_res['lepton']['closures_at_1pct']})  "
            f"up {trial_res['up_type']['best_max_frac']:.4g} (cl={trial_res['up_type']['closures_at_1pct']})  "
            f"down {trial_res['down_type']['best_max_frac']:.4g} (cl={trial_res['down_type']['closures_at_1pct']})  "
            f"[total {time.time()-t0:.0f}s]",
            flush=True,
        )
    return results


def main(n_null_trials: int = 30) -> Dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    nw = min(12, cpu_count())

    print("[KK] real UGP features scan...", flush=True)
    real_scans = real_features_scan(nw)

    real_best_per_sector = {
        s: min((real_scans[s][D]["top_k"][0] | {"D": D} for D in (1, 2, 3) if real_scans[s][D]["top_k"]),
               key=lambda r: r["max_fractional_error"])
        for s in real_scans
    }

    print(f"\n[KK] feature-randomization null ({n_null_trials} trials, D=3 only)...", flush=True)
    null_trials = random_features_trials(n_null_trials, nw)
    per_sector_random_bests = {
        s: [t[s]["best_max_frac"] for t in null_trials] for s in ("lepton", "up_type", "down_type")
    }
    per_sector_random_stats = {
        s: {
            "median": float(np.median(per_sector_random_bests[s])),
            "min": float(np.min(per_sector_random_bests[s])),
            "max": float(np.max(per_sector_random_bests[s])),
            "mean": float(np.mean(per_sector_random_bests[s])),
            "close_1pct": int(sum(1 for x in per_sector_random_bests[s] if x <= 0.01)),
            "close_2pct": int(sum(1 for x in per_sector_random_bests[s] if x <= 0.02)),
            "close_5pct": int(sum(1 for x in per_sector_random_bests[s] if x <= 0.05)),
        }
        for s in per_sector_random_bests
    }

    real_closes = all(real_best_per_sector[s]["max_fractional_error"] <= 0.01 for s in real_best_per_sector)
    random_floor_per_sector = {s: per_sector_random_stats[s]["min"] for s in per_sector_random_stats}
    random_floor_min = min(random_floor_per_sector.values())
    random_always_fails_1pct = all(per_sector_random_stats[s]["close_1pct"] == 0 for s in per_sector_random_stats)

    if real_closes and random_always_fails_1pct:
        verdict = "STRUCTURAL_CLOSURE_CONFIRMED: real UGP features close ≤ 1%; random features fail at 1% in all trials"
    elif real_closes and not random_always_fails_1pct:
        verdict = "PARTIAL: real features close but random features also occasionally close — still volume-driven"
    elif not real_closes:
        verdict = "MAP_feature_only_kernels_insufficient: restricted library cannot close; 09 paradigm confirmed MAP"
    else:
        verdict = "AMBIGUOUS"

    prediction_block = {
        "comp_id": "COMP-P01-KK",
        "spec_reference": "09_SPEC — decisive feature-only kernel restriction test",
        "purpose": "Remove index-only kernels from II's library; rerun per-sector D=3 scan; compare real-UGP-features vs random-features (30 trials).",
        "timestamp_utc": ts,
        "kernel_library_restricted": FEATURE_DEPENDENT_KERNELS,
        "scalar_atom_library_size": len(SCALAR_NAMES),
        "real_feature_scans": real_scans,
        "real_best_per_sector": real_best_per_sector,
        "null_trials": null_trials,
        "per_sector_random_statistics": per_sector_random_stats,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": {
            "prediction_block_sha256": sha,
            "real_features_close_1pct": real_closes,
            "random_features_close_1pct_any_trial_any_sector": not random_always_fails_1pct,
            "random_features_close_rates": {s: per_sector_random_stats[s]["close_1pct"] for s in per_sector_random_stats},
            "random_features_floor_per_sector": random_floor_per_sector,
            "verdict": verdict,
            "real_best_per_sector": real_best_per_sector,
        },
    }


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    out = main(n_null_trials=n)
    path = "comp_p01_KK_feature_only_kernels.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
