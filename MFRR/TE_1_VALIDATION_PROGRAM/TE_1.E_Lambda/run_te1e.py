#!/usr/bin/env python3
"""
Execution harness for TE_1.E — Self-Referential Cosmological Constant (Λ).

References:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/README.md`
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace, asdict
from datetime import datetime
from pathlib import Path

from te1e_pipeline import (
    CalibrationResult,
    LambdaConfig,
    calibrate_energy_scale,
    evaluate_results,
    run_parameter_grid,
    write_results,
)


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE_1.E Λ validation suite.")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="Maximum worker processes (default: 2 for current CPU constraints).",
    )
    parser.add_argument(
        "--lambda-psi",
        type=float,
        nargs="*",
        default=None,
        help="Override λΨ grid (space separated list).",
    )
    parser.add_argument(
        "--alpha1",
        type=float,
        nargs="*",
        default=None,
        help="Override α₁ grid.",
    )
    parser.add_argument(
        "--alpha2",
        type=float,
        nargs="*",
        default=None,
        help="Override α₂ grid.",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default=str(RESULTS_DIR),
        help="Directory to store run outputs.",
    )
    parser.add_argument(
        "--skip-calibration",
        action="store_true",
        help="Use theoretical energy scale only (no Λ normalization).",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> LambdaConfig:
    cfg = LambdaConfig()
    if args.lambda_psi:
        cfg = replace(cfg, lambda_psi_values=tuple(args.lambda_psi))
    if args.alpha1:
        cfg = replace(cfg, alpha1_values=tuple(args.alpha1))
    if args.alpha2:
        cfg = replace(cfg, alpha2_values=tuple(args.alpha2))
    return cfg


def main() -> None:
    args = parse_args()
    cfg = build_config(args)

    calibration: CalibrationResult | None = None
    if cfg.energy_scale is None:
        if args.skip_calibration:
            cfg = replace(cfg, energy_scale=1.0)
        else:
            cfg, calibration = calibrate_energy_scale(cfg)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    records = run_parameter_grid(cfg, run_dir, max_workers=max(1, min(args.max_workers, 2)))
    summary = evaluate_results(cfg, records)
    calibration_payload = asdict(calibration) if calibration is not None else None
    write_results(cfg, records, summary, run_dir, calibration=calibration_payload)

    verdict_path = run_dir / ("PASS.json" if summary.overall_pass else "FAIL.json")
    verdict_path.write_text(json.dumps(asdict(summary), indent=2))

    print(json.dumps(asdict(summary), indent=2))
    print(f"Artifacts written to {run_dir}")


if __name__ == "__main__":
    main()


