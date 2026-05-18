#!/usr/bin/env python3
"""
TE_1.A execution harness

Runs the Quantized Transputation Dynamics validation suite as specified in
`1_1_TE_1_KICKOFF.md`, coordinating background generation, transputon
simulation, analysis, and PASS/FAIL assessment.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple, List

import numpy as np
from scipy import stats

from te1a_pipeline import (
    SimulationConfig,
    SimulationResult,
    run_te1a_case,
    save_metadata,
)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = BASE_DIR / "results"


def _run_case(args: Tuple[SimulationConfig, float, Path]) -> Tuple[float, SimulationResult]:
    cfg, omega_target, output_dir = args
    result, background, cp_divergence, cp_masks, d_density, lambda_grid = run_te1a_case(cfg, omega_target, output_dir)
    save_metadata(
        cfg,
        background,
        output_dir,
        extra={
            "omega_target": float(omega_target),
            "lambda_grid": [float(lam) for lam in lambda_grid],
        },
    )
    np.savez(output_dir / "sources.npz", cp_divergence=cp_divergence, cp_masks=cp_masks, d_density=d_density)
    return omega_target, result


def _relative_rmse(result: SimulationResult) -> float:
    omega_values = np.array([row["omega"] for row in result.dispersion_table], dtype=float)
    if omega_values.size == 0:
        return float("inf")
    omega_sq = omega_values ** 2
    return result.rmse / max(np.mean(omega_sq), 1e-9)


def _evaluate(results: Iterable[Tuple[float, SimulationResult]]) -> dict:
    sorted_results = sorted(results, key=lambda item: item[0])
    omegas = np.array([omega for omega, _ in sorted_results], dtype=float)
    masses = np.array([res.m_pt_squared for _, res in sorted_results], dtype=float)

    slope, _, _, p_value, _ = stats.linregress(omegas, masses)

    dispersion_pass = bool(all(_relative_rmse(res) <= 0.03 for _, res in sorted_results))
    monotonic_pass = bool(slope > 0 and p_value < 0.01)

    landauer_pass = bool(all(res.lv_stats["median"] >= 1.0 and res.lv_stats["p5"] >= 0.9 for _, res in sorted_results))

    gksl_pass = True
    for _, res in sorted_results:
        lam = np.array([row["lambda"] for row in res.gksl_table], dtype=float)
        delta = np.array([row["delta_gamma"] for row in res.gksl_table], dtype=float)
        if lam.size < 2:
            gksl_pass = False
            break
        fit = np.polyfit(lam, delta, 1)
        pred = np.polyval(fit, lam)
        err = np.abs(delta - pred)
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(np.abs(pred) > 1e-9, err / np.abs(pred), 0.0)
        mask = np.isclose(delta, 0.0, atol=1e-9)
        if np.nanmax(rel[~mask] if np.any(~mask) else rel) > 0.10:
            gksl_pass = False
            break
    gksl_pass = bool(gksl_pass)

    srrg_pass = True
    for _, res in sorted_results:
        if len(res.srrg_table) < 2:
            srrg_pass = False
            break
        last = res.srrg_table[-1]
        prev = res.srrg_table[-2]

        def rel_delta(key: str) -> float:
            denom = max(abs(prev[key]), 1e-9)
            return abs(last[key] - prev[key]) / denom

        if rel_delta("c_sq") >= 0.05 or rel_delta("m_sq") >= 0.05:
            srrg_pass = False
            break
    srrg_pass = bool(srrg_pass)

    summary = {
        "dispersion_pass": dispersion_pass,
        "monotonic_pass": monotonic_pass,
        "monotonic_slope": float(slope),
        "monotonic_p_value": float(p_value),
        "gksl_pass": gksl_pass,
        "landauer_pass": landauer_pass,
        "srrg_pass": srrg_pass,
        "overall_pass": bool(all([dispersion_pass, monotonic_pass, gksl_pass, landauer_pass, srrg_pass])),
        "omegas": omegas.tolist(),
        "masses": masses.tolist(),
    }
    return summary


def main() -> None:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS_ROOT / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    cfg = SimulationConfig()
    omega_targets = [1400.0, 2000.0, 2600.0, 3200.0, 3800.0, 4400.0, 5000.0]

    args: List[Tuple[SimulationConfig, float, Path]] = []
    for idx, omega in enumerate(omega_targets):
        out_dir = run_dir / f"omega_{int(round(omega))}"
        cfg_dict = dict(cfg.__dict__)
        cfg_dict["seed"] = cfg.seed + idx
        case_cfg = SimulationConfig(**cfg_dict)
        args.append((case_cfg, omega, out_dir))

    max_workers = min(len(args), min(9, max(1, (os.cpu_count() or 10) - 1)))
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_case, arg): arg[1] for arg in args}
        for future in as_completed(futures):
            omega, result = future.result()
            results.append((omega, result))

    summary = _evaluate(results)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    verdict_path = run_dir / ("PASS.txt" if summary["overall_pass"] else "FAIL.txt")
    verdict_path.write_text("PASS" if summary["overall_pass"] else "FAIL")

    print(json.dumps(summary, indent=2))
    print(f"Summary saved to {run_dir}")


if __name__ == "__main__":
    main()
