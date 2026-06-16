#!/usr/bin/env python3
"""
Execution harness for TE_1.P — Reflexive Fine-Structure Calibration (FSC).

References:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.P_FSC/README.md`
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace, asdict
from datetime import datetime
from pathlib import Path

from te1p_pipeline import (
    FSCConfig,
    calibrate_energy_scale,
    evaluate_results,
    run_parameter_grid,
    write_results,
)


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE_1.P fine-structure calibration suite.")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="Maximum worker processes (default: 2).",
    )
    parser.add_argument(
        "--lambda-em",
        type=float,
        nargs="*",
        default=None,
        help="Override λ_EM grid.",
    )
    parser.add_argument(
        "--alpha-cp",
        type=float,
        nargs="*",
        default=None,
        help="Override α_CP grid.",
    )
    parser.add_argument(
        "--tau-adj",
        type=float,
        nargs="*",
        default=None,
        help="Override τ_adj grid.",
    )
    parser.add_argument(
        "--skip-calibration",
        action="store_true",
        help="Skip energy-scale calibration (use theoretical scale = 1).",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default=str(RESULTS_DIR),
        help="Directory to store run outputs.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> FSCConfig:
    cfg = FSCConfig()
    if args.lambda_em:
        cfg = replace(cfg, lambda_em_values=tuple(args.lambda_em))
    if args.alpha_cp:
        cfg = replace(cfg, alpha_cp_values=tuple(args.alpha_cp))
    if args.tau_adj:
        cfg = replace(cfg, tau_adj_values=tuple(args.tau_adj))
    return cfg


def main() -> None:
    args = parse_args()
    cfg = build_config(args)

    calibration_payload = None
    if cfg.energy_scale is None and not args.skip_calibration:
        cfg, calibration_payload = calibrate_energy_scale(cfg)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    records = run_parameter_grid(cfg, run_dir, max_workers=max(1, min(args.max_workers, 4)))
    summary = evaluate_results(cfg, records)
    write_results(cfg, records, summary, run_dir)

    verdict_path = run_dir / ("PASS.json" if summary.overall_pass else "FAIL.json")
    verdict_payload = asdict(summary)
    if calibration_payload is not None:
        verdict_payload["calibration"] = calibration_payload
    verdict_path.write_text(json.dumps(verdict_payload, indent=2))

    print(json.dumps(verdict_payload, indent=2))
    print(f"Artifacts written to {run_dir}")


if __name__ == "__main__":
    main()


