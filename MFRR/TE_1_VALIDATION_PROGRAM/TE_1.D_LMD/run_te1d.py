#!/usr/bin/env python3
"""
Execution harness for TE_1.D — Law of Maintained Degeneracy (LMD).

References:
    Kickoff: `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
    Summary: `../TE_1_SUMMARY.md`

The script orchestrates background generation, degeneracy lifetime measurements,
regression analysis, and PASS/FAIL evaluation while respecting the available
two-core execution budget.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from te1d_pipeline import (
    LMDConfig,
    fit_lmd_model,
    run_parameter_grid,
    summarize_profit_threshold,
    write_results,
    _json_default,
)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = BASE_DIR / "results"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE_1.D LMD validation suite.")
    parser.add_argument("--max-workers", type=int, default=2, help="Maximum parallel workers (threads).")
    parser.add_argument(
        "--output-root",
        type=str,
        default=str(RESULTS_ROOT),
        help="Root directory for run outputs.",
    )
    parser.add_argument(
        "--seeds-per-combo",
        type=int,
        default=None,
        help="Override seeds per parameter combination (default 20).",
    )
    parser.add_argument(
        "--tuning",
        action="store_true",
        help="Activate reduced diagnostic mode for rapid parameter tuning.",
    )
    return parser.parse_args()


def _build_config(args: argparse.Namespace) -> LMDConfig:
    cfg = LMDConfig()
    if args.seeds_per_combo is not None:
        cfg = replace(cfg, seeds_per_combo=args.seeds_per_combo)
    if args.tuning:
        tuned_domains = tuple(cfg.domains[:2])
        cfg = replace(
            cfg,
            domains=tuned_domains,
            profit_grid=(1.02, 1.10, 1.18),
            logn_grid=(1.05, 1.55),
            seeds_per_combo=min(cfg.seeds_per_combo, 5),
            lifetime_steps=2400,
        )
    return cfg


def _evaluate_pass_fail(cfg: LMDConfig, fit_summary: Dict[str, Any], threshold_summary: Dict[str, Any]) -> Dict[str, bool]:
    coeffs = fit_summary["coefficients"]
    passes = fit_summary["passes"].copy()
    passes["A_near_Lambda"] = bool(0.7 * cfg.lambda_factor <= coeffs["A"] <= 1.3 * cfg.lambda_factor)
    passes.update(threshold_summary["passes"])
    return passes


def main() -> None:
    args = _parse_args()
    cfg = _build_config(args)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_label = "tuning" if args.tuning else "run"
    run_dir = Path(args.output_root) / f"{run_label}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    results = run_parameter_grid(cfg, run_dir, max_workers=max(1, min(args.max_workers, 2)))
    fit_summary = fit_lmd_model(cfg, results)
    threshold_summary = summarize_profit_threshold(cfg, results)
    passes = _evaluate_pass_fail(cfg, fit_summary, threshold_summary)

    write_results(cfg, results, fit_summary, threshold_summary, run_dir)

    overall_pass = all(
        [
            passes["A_positive"],
            passes["B_positive"],
            passes["C_positive"],
            passes["r2_pass"],
            passes["A_near_Lambda"],
            passes["threshold_location_pass"],
            passes["superlinear_pass"],
        ]
    )

    verdict_path = run_dir / ("PASS.txt" if overall_pass else "FAIL.txt")
    verdict_path.write_text("PASS" if overall_pass else "FAIL")

    console_summary = {
        "overall_pass": overall_pass,
        "r2": fit_summary["stats"]["r2"],
        "A": fit_summary["coefficients"]["A"],
        "B": fit_summary["coefficients"]["B"],
        "C": -fit_summary["coefficients"]["minus_C"],
        "threshold_profit": threshold_summary["threshold_location"],
        "threshold_slope": threshold_summary["threshold_slope"],
        "passes": passes,
    }
    print(json.dumps(console_summary, indent=2, default=_json_default))
    print(f"Run artifacts written to {run_dir}")


if __name__ == "__main__":
    main()


