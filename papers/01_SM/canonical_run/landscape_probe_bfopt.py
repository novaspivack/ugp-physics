#!/usr/bin/env python3
"""
landscape_probe_bfopt.py — extends landscape_probe.py with the
two studies the user's memory most likely refers to:

  AXIS 4 — N-value coordinate profiles (per particle), as the
           UGP_GTE_SM_Verifier's run_coordinate_profiles_on_N does.  Tests
           whether the GTE N-value optimum is broad-flat per particle.

  AXIS 5 — (phase_k, renorm_k) 2D grid in phase_mode=dimless,
           UGP_GTE_SM_Verifier's BFOpt suite (run_param_grid_phasek_renormk).
           This is where (phase_k, renorm_k) actually act on primary
           sigma and where the historical BFOpt result is documented.

Both axes use the canonical primary-sigma metric.  Each is classified
as broad-flat or narrow at ±1% jitter.
"""
import copy
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VERIFIER_DIR = os.path.join(REPO, "UGP_GTE_SM_Verifier")
sys.path.insert(0, VERIFIER_DIR)

_SCRATCH = tempfile.mkdtemp(prefix="p01_landscape_bfopt_")
os.chdir(_SCRATCH)

import numpy as np  # noqa: E402
import UGP_GTE_SM_Verifier as M  # noqa: E402


def gmean(xs):
    return math.exp(sum(math.log(max(x, 1e-30)) for x in xs) / len(xs))


def classify(geomean):
    if geomean < 10: return "broad-flat"
    if geomean < 1000: return "intermediate"
    return "narrow"


def main():
    print("=" * 78)
    print("Landscape probe extension — N-value profiles + (phase_k,renorm_k) BFOpt")
    print("=" * 78)

    out = {
        "description": (
            "Extension of landscape_probe.py to cover the two studies "
            "in the canonical SD5 BFOpt suite: per-particle N coordinate "
            "profiles, and (phase_k, renorm_k) 2D grid in phase_mode=dimless."
        ),
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    # ----------------------------------------------------------------
    # AXIS 4 — N coordinate profiles (per particle, ±5% over 9 steps)
    # ----------------------------------------------------------------
    print("\nAXIS 4 — N coordinate profiles (per particle, ±5% over 9 steps)")
    print("  (uses UGP_GTE_SM_Verifier's run_coordinate_profiles_on_N)")
    bf = M.run_coordinate_profiles_on_N(percent_span=5.0, steps=9, write_artifacts=False)
    profiles = bf["profiles"]

    axis4 = {"per_particle": {}, "summary": {}}
    all_min_max_ratios = []
    for name, points in profiles.items():
        baseline_idx = len(points) // 2  # m=1.0 is the middle
        # Find the canonical (m=1.0) sigma — closest to multiplier=1
        canon = min(points, key=lambda p: abs(p["multiplier"] - 1.0))
        canon_sigma = canon["sigma_primary"]
        if canon_sigma <= 0:
            continue
        ratios = [p["sigma_primary"] / canon_sigma for p in points if p["sigma_primary"] > 0]
        axis4["per_particle"][name] = {
            "canon_sigma": canon_sigma,
            "min_ratio": min(ratios),
            "max_ratio": max(ratios),
            "geom_mean_ratio": gmean(ratios),
            "n_points": len(points),
        }
        all_min_max_ratios.append((min(ratios), max(ratios), gmean(ratios)))
        print(f"  {name:18s}: ratios over ±5% N grid = [{min(ratios):.2e}, {max(ratios):.2e}], geomean={gmean(ratios):.2e}")

    if all_min_max_ratios:
        # overall summary at the ±5% boundary
        max_ratio_overall = max(r[1] for r in all_min_max_ratios)
        gm_overall = gmean([r[2] for r in all_min_max_ratios])
        axis4["summary"] = {
            "max_ratio_overall": max_ratio_overall,
            "geom_mean_ratio_overall": gm_overall,
            "classification_at_5pct": classify(gm_overall),
        }
        print(f"  --> AXIS 4 classification at ±5% N-jitter: {classify(gm_overall).upper()}")
    out["axes_extension"] = {"N_coordinate_profiles_5pct": axis4}

    # ----------------------------------------------------------------
    # AXIS 5 — (phase_k, renorm_k) 2D grid in phase_mode=dimless
    # ----------------------------------------------------------------
    print("\nAXIS 5 — (phase_k, renorm_k) 2D grid, phase_mode=dimless")
    print("  Sweeping phase_k ∈ [1.6, 2.4], renorm_k ∈ [1200, 1700], 9×9 grid")
    grid = M.run_param_grid_phasek_renormk(
        k_range=(1.6, 2.4), k_steps=9,
        K_range=(1200.0, 1700.0), K_steps=9,
        write_artifacts=False
    )
    sigma_grid = np.array(grid["sigma_grid"], dtype=float)
    finite_mask = np.isfinite(sigma_grid) & (sigma_grid > 0)
    if finite_mask.sum() == 0:
        print("  ERROR: no finite sigma values in BFOpt grid")
        return 1

    sigmas = sigma_grid[finite_mask]
    sigma_min = float(sigmas.min())
    sigma_max = float(sigmas.max())
    sigma_med = float(np.median(sigmas))
    sigma_p25, sigma_p75 = float(np.percentile(sigmas, 25)), float(np.percentile(sigmas, 75))
    best = grid["best"]

    # broad-flat metric: ratio max/min across grid
    spread = sigma_max / sigma_min
    iqr_ratio = sigma_p75 / sigma_p25

    axis5 = {
        "k_range": [1.6, 2.4],
        "K_range": [1200.0, 1700.0],
        "n_grid_points": int(finite_mask.sum()),
        "sigma_min": sigma_min,
        "sigma_max": sigma_max,
        "sigma_median": sigma_med,
        "sigma_p25": sigma_p25,
        "sigma_p75": sigma_p75,
        "max_min_spread": spread,
        "iqr_ratio_p75_p25": iqr_ratio,
        "best_in_grid": best,
    }
    print(f"  Grid sigma min/median/max:       {sigma_min:.3e} / {sigma_med:.3e} / {sigma_max:.3e}")
    print(f"  Max/min spread across grid:      {spread:.3f}x")
    print(f"  IQR ratio (p75/p25):             {iqr_ratio:.3f}x")
    print(f"  Best-in-grid (sigma, phase_k, renorm_k): "
          f"sigma={best['sigma_primary']:.3e}, phase_k={best['phase_k']:.3f}, renorm_k={best['renorm_K']:.1f}")

    # Broad-flat verdict: if spread < 2x, the basin is genuinely broad-flat
    if spread < 2.0:
        cls5 = "broad-flat (spread < 2x)"
    elif spread < 10.0:
        cls5 = "intermediate"
    else:
        cls5 = "narrow"
    axis5["classification"] = cls5
    print(f"  --> AXIS 5 classification:       {cls5.upper()}")

    out["axes_extension"]["phasek_renormk_BFOpt_dimless"] = axis5

    out_path = os.path.join(HERE, "landscape_probe_bfopt.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"\nOutput: {out_path}")
    print(f"SHA-256: {sha}")

    import shutil
    try: shutil.rmtree(_SCRATCH)
    except Exception: pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
