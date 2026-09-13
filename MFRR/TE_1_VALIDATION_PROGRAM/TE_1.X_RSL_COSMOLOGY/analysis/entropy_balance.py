#!/usr/bin/env python3
"""Compute entropy-coupled diagnostics for TE1.X FRW runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entropy balance summary for TE1.X")
    parser.add_argument("--summary", required=True, type=Path, help="FRW sweep summary JSON")
    parser.add_argument("--entropy", required=True, type=Path, help="TE1.R entropy summary JSON")
    parser.add_argument("--output", type=Path, default=Path("results/entropy_balance.json"))
    return parser.parse_args()


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    args = parse_args()
    summary = load_json(args.summary)
    entropy_stats = load_json(args.entropy)

    runs: List[Dict] = summary.get("runs", [])
    lambda_obs = 1.1056e-52
    records = []

    for run in runs:
        lambda_phys = run.get("lambda_phys", lambda_obs)
        lambda_resid = abs(lambda_phys - lambda_obs) / lambda_obs
        w0 = run.get("w0", -1.0)
        wa = run.get("wa", 0.0)
        records.append(
            {
                "lambda_psi": run.get("lambda_psi"),
                "alpha_1": run.get("alpha_1"),
                "alpha_2": run.get("alpha_2"),
                "lambda_residual": lambda_resid,
                "w0": w0,
                "wa": wa,
            }
        )

    wa_values = np.array([r["wa"] for r in records])
    lambda_resids = np.array([r["lambda_residual"] for r in records])

    report = {
        "summary": str(args.summary.resolve()),
        "entropy_source": str(args.entropy.resolve()),
        "mean_delta_S": float(entropy_stats.get("mean_delta_S", 0.0)),
        "lambda_residual_max": float(lambda_resids.max() if lambda_resids.size else 0.0),
        "lambda_residual_mean": float(lambda_resids.mean() if lambda_resids.size else 0.0),
        "wa_max": float(np.max(np.abs(wa_values)) if wa_values.size else 0.0),
        "records": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(f"Saved entropy balance report to {args.output}")


if __name__ == "__main__":
    main()
