#!/usr/bin/env python3
"""
Runner for TE_1.H Levin Information Profit diagnostics leveraging TE_1.B reflexive analytics.

Cross-reference: `1_6_TE_1H_LEVIN_INFORMATION_PROFIT_STUDY.md`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import csv

from te1b_pipeline_levin import FrozenParameterSet, SimulationConfig, run_validation


def _load_frozen_parameters(path: Path):
    table = {}
    with path.open("r", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            key = (
                float(row["temperature"]),
                float(row["mu"]),
                float(row["sigma"]),
            )
            table[key] = FrozenParameterSet(
                cp_scale=float(row["cp_scale"]),
                delta_gain=float(row["delta_gain"]),
                reverse_fraction=float(row["reverse_fraction"]),
            )
    return table


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run TE_1.H Levin-augmented reflexive validation.")
    parser.add_argument("--calibration", action="store_true", help="Run short calibration sweep for tuning (legacy flag).")
    parser.add_argument(
        "--phase",
        choices=["standard", "calibration", "adapt", "frozen"],
        default="standard",
        help="Select execution phase. Use 'adapt' for reflexive tuning and 'frozen' to validate learned parameters.",
    )
    parser.add_argument(
        "--frozen-params",
        type=Path,
        help="Path to reflexive_parameters.csv produced during the adapt phase (required for --phase frozen).",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum worker processes for trajectory execution.",
    )
    args = parser.parse_args()

    phase = args.phase
    if args.calibration or phase == "calibration":
        phase = "calibration"

    base_dir = Path(__file__).resolve().parent
    results_root = base_dir / "results"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = results_root / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    config = SimulationConfig(calibration=(phase == "calibration"), phase=phase)
    if phase == "adapt":
        config.reflexive.enabled = True
    if phase == "frozen":
        param_path = args.frozen_params
        if param_path is None:
            raise SystemExit("Frozen phase requires --frozen-params pointing to reflexive_parameters.csv.")
        if not param_path.exists():
            raise SystemExit(f"Frozen parameter file not found: {param_path}")
        config.frozen_parameter_table = _load_frozen_parameters(param_path)

    summary = run_validation(config, run_dir, max_workers=args.max_workers)

    print(json.dumps(summary, indent=2))
    print(f"Summary saved to {run_dir}")


if __name__ == "__main__":
    main()

