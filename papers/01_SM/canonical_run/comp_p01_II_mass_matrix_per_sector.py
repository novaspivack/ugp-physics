#!/usr/bin/env python3
"""
COMP-P01-II: Per-sector independent mass-matrix scan (09_SPEC Phase 2, relaxed)

HH scanned the JOINT-constraint version (same atom/kernel triple across all 3
charged-fermion sectors) and produced a clean MAP at ~38% max-frac-err floor.
II relaxes that constraint to the spec's weakest form (§1.3: "sector
differences only in which atoms are used"): each of the 3 sectors is scanned
independently with the same 59-atom scalar × 32-kernel binary library at
D ∈ {1, 2, 3}.  A PARTIAL CLOSE in any sector is itself a major result.

Re-uses infrastructure from HH.  Runtime budget: comparable to HH (< 5 min on
12 cores) since joint scan was only 3× the work of one sector.

SHA-256 protocol preserved.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import numpy as np
from multiprocessing import Pool, cpu_count

from comp_p01_HH_mass_matrix_paradigm_deep import (
    SCALAR_NAMES, SCALAR_VALUES,
    build_kernel_library, sector_feats_by_sector, pdg_by_sector,
    koide_residual,
)


def _worker_scan_single_sector(args):
    kernel_subset, K_stack, pdg_sector_sorted, D, sector_name, closure_eps, top_k = args
    Ks = np.stack([K_stack[k] for k in kernel_subset])   # (D, 3, 3)
    idx = np.array(list(itertools.permutations(range(len(SCALAR_VALUES)), D)), dtype=np.int64)
    alphas = SCALAR_VALUES[idx]                          # (N, D)
    M = np.einsum("nk,kij->nij", alphas, Ks)             # (N, 3, 3)
    evals = np.linalg.eigvalsh(M)
    sv = np.sort(np.abs(evals), axis=1)
    scale = pdg_sector_sorted[0] / np.maximum(sv[:, 0], 1e-30)
    pred = sv * scale[:, None]
    frac = np.max(np.abs(pred - pdg_sector_sorted[None, :]) / np.maximum(pdg_sector_sorted[None, :], 1e-30), axis=1)
    order = np.argsort(frac)[:top_k]
    top = [
        {
            "atoms": [SCALAR_NAMES[idx[i, k]] for k in range(D)],
            "kernels": list(kernel_subset),
            "max_fractional_error": float(frac[i]),
            "predicted_masses_MeV": pred[i].tolist(),
        }
        for i in order
    ]
    hist = {
        k: int(np.sum(frac <= v))
        for k, v in (
            ("le_0.001", 0.001), ("le_0.005", 0.005), ("le_0.01", 0.01),
            ("le_0.02", 0.02), ("le_0.05", 0.05), ("le_0.10", 0.10),
            ("le_0.20", 0.20), ("le_0.50", 0.50), ("le_1.00", 1.0),
        )
    }
    return {
        "n_combinations": int(alphas.shape[0]),
        "closures_at_eps": int(np.sum(frac <= closure_eps)),
        "best_max_frac": float(np.min(frac)),
        "top_k": top,
        "histogram": hist,
    }


def scan_sector(sector: str, D: int, K_by_sector, pdg, kernel_names, n_workers):
    pdg_sorted = np.sort(pdg[sector])
    if D == 1:
        subsets = [(k,) for k in kernel_names]
    elif D == 2:
        subsets = list(itertools.combinations(kernel_names, 2))
    else:
        subsets = list(itertools.combinations(kernel_names, 3))
    args_iter = [(ks, K_by_sector[sector], pdg_sorted, D, sector, 0.01, 5) for ks in subsets]
    total_combos = 0
    closures = 0
    top: List[Dict] = []
    total_hist = {k: 0 for k in ("le_0.001", "le_0.005", "le_0.01", "le_0.02", "le_0.05", "le_0.10", "le_0.20", "le_0.50", "le_1.00")}
    t0 = time.time()
    with Pool(n_workers) as pool:
        for res in pool.imap_unordered(_worker_scan_single_sector, args_iter, chunksize=1):
            total_combos += res["n_combinations"]
            closures += res["closures_at_eps"]
            for k in total_hist:
                total_hist[k] += res["histogram"][k]
            top.extend(res["top_k"])
    top.sort(key=lambda r: r["max_fractional_error"])
    return {
        "sector": sector,
        "D": D,
        "n_kernel_subsets": len(subsets),
        "n_combinations_total": total_combos,
        "closures_at_1pct": closures,
        "histogram": total_hist,
        "top_k": top[:20],
        "elapsed_seconds": time.time() - t0,
    }


def null_sector(sector, D, trials, K_by_sector, pdg, kernel_names, seed=20260419):
    pdg_sorted = np.sort(pdg[sector])
    rng = random.Random(seed + {"lepton": 1, "up_type": 2, "down_type": 3}[sector])
    hits = 0
    best = math.inf
    for _ in range(trials):
        perm = list(range(len(SCALAR_VALUES)))
        rng.shuffle(perm)
        vals_scrambled = SCALAR_VALUES[perm]
        ks = rng.sample(kernel_names, D)
        atom_idx = rng.sample(range(len(SCALAR_VALUES)), D)
        alpha = vals_scrambled[atom_idx][None, :]
        K_stack = np.stack([K_by_sector[sector][k] for k in ks])
        M = np.einsum("nk,kij->nij", alpha, K_stack)
        evals = np.linalg.eigvalsh(M)
        sv = np.sort(np.abs(evals), axis=1)
        scale = pdg_sorted[0] / max(sv[0, 0], 1e-30)
        pred = sv * scale
        frac = float(np.max(np.abs(pred - pdg_sorted) / np.maximum(pdg_sorted, 1e-30)))
        best = min(best, frac)
        if frac <= 0.01:
            hits += 1
    return {"trials": trials, "hits_at_1pct": hits, "hit_rate": hits / trials, "best_random_max_frac": best}


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sf = sector_feats_by_sector()
    K_by_sector = {s: build_kernel_library(sf[s]) for s in ("lepton", "up_type", "down_type")}
    kernel_names = list(K_by_sector["lepton"].keys())
    pdg = pdg_by_sector()
    nw = min(12, cpu_count())
    scans: Dict[str, Dict[int, Dict]] = {s: {} for s in ("lepton", "up_type", "down_type")}
    nulls: Dict[str, Dict[int, Dict]] = {s: {} for s in ("lepton", "up_type", "down_type")}
    for sector in ("lepton", "up_type", "down_type"):
        for D in (1, 2, 3):
            print(f"[II] {sector}  D={D} ...", flush=True)
            scans[sector][D] = scan_sector(sector, D, K_by_sector, pdg, kernel_names, nw)
            s = scans[sector][D]
            print(
                f"[II]   {sector} D={D}: {s['n_combinations_total']:,} combos in {s['elapsed_seconds']:.1f}s  "
                f"best={s['top_k'][0]['max_fractional_error']:.4g}  closures@1%={s['closures_at_1pct']}"
            )
        for D in (1, 2, 3):
            nulls[sector][D] = null_sector(sector, D, 1000, K_by_sector, pdg, kernel_names)
            n = nulls[sector][D]
            print(
                f"[II]   null {sector} D={D}: {n['hits_at_1pct']}/{n['trials']}  rate={n['hit_rate']:.4f}  best_rand={n['best_random_max_frac']:.4g}"
            )

    best_per_sector = {
        s: min(
            (scans[s][D]["top_k"][0] | {"D": D} for D in (1, 2, 3) if scans[s][D]["top_k"]),
            key=lambda r: r["max_fractional_error"],
        )
        for s in scans
    }

    any_sector_closes = any(best_per_sector[s]["max_fractional_error"] <= 0.01 for s in best_per_sector)
    any_sector_near_close = any(best_per_sector[s]["max_fractional_error"] <= 0.02 for s in best_per_sector)
    max_null = max(
        nulls[s][D]["hit_rate"] for s in nulls for D in (1, 2, 3)
    )
    null_disciplined = max_null < 0.01

    if any_sector_closes and null_disciplined:
        verdict = "PARTIAL_CLOSES_structural_beats_null_per_sector"
    elif any_sector_near_close and null_disciplined:
        verdict = "NEAR_PARTIAL_CLOSES_at_2pct_null_disciplined"
    else:
        verdict = "MAP_per_sector_also_insufficient"

    prediction_block = {
        "comp_id": "COMP-P01-II",
        "spec_reference": "09_SPEC Phase 2 (per-sector independent — spec §1.3 relaxed constraint)",
        "relationship_to_HH": "HH ran joint-constraint (same atoms across sectors) MAP @ ~38% floor; II tests the strictly weaker per-sector-independent constraint with the same 59×32 library.",
        "timestamp_utc": timestamp,
        "closure_eps": 0.01,
        "near_closure_eps": 0.02,
        "scalar_atom_library_size": len(SCALAR_NAMES),
        "binary_kernel_library_size": len(kernel_names),
        "scans": scans,
        "nulls": nulls,
        "best_per_sector": best_per_sector,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "any_sector_closes_at_1pct": any_sector_closes,
        "any_sector_at_2pct": any_sector_near_close,
        "max_null_hit_rate": max_null,
        "null_disciplined": null_disciplined,
        "verdict": verdict,
        "best_per_sector": best_per_sector,
    }
    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_II_mass_matrix_per_sector.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
