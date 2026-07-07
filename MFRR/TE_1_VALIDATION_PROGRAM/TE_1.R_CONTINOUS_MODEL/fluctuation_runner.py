#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Reference: TE_1.R plan (1_1_TE_1R_PLAN.md)
"""
Reflexive fluctuation theorem analyzer for TE_1.R.

Reads precomputed ensemble outputs from SRRG validation (rft_outputs/summary.csv),
computes aggregate statistics, and writes TE_1.R-specific reports under
results/fluctuation/.

Outputs:
- summary.json: global mean, std, and deviation from unity for <exp(-ΔS_ref)>.
- dataset.csv: copy of underlying rows used for traceability.

Usage:
    python fluctuation_runner.py \
        --input \"../../rft_outputs/summary.csv\" \
        --output results/fluctuation
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd


def analyze_fluctuation(input_path: Path) -> Dict[str, float]:
    df = pd.read_csv(input_path)
    metric = df["E[exp(-dS)]"]
    mean = metric.mean()
    std = metric.std(ddof=0)
    max_dev = (metric - 1.0).abs().max()
    result = {
        "n_rows": int(len(df)),
        "mean_exp_neg_dS": float(mean),
        "std_exp_neg_dS": float(std),
        "max_abs_deviation": float(max_dev),
        "mean_delta_S": float(df["E[dS]"].mean()),
        "std_delta_S": float(df["E[dS]"].std(ddof=0)),
    }
    return result, df


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze reflexive fluctuation theorem data.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to SRRG fluctuation summary CSV (e.g., ../../rft_outputs/summary.csv).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/fluctuation"),
        help="Directory to write TE_1.R reports (default: results/fluctuation).",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file {args.input} not found.")

    summary, df = analyze_fluctuation(args.input)
    args.output.mkdir(parents=True, exist_ok=True)

    (args.output / "summary.json").write_text(json.dumps(summary, indent=2))
    df.to_csv(args.output / "dataset.csv", index=False)

    print(
        "[Fluctuation] <exp(-ΔS)> = "
        f"{summary['mean_exp_neg_dS']:.6f} ± {summary['std_exp_neg_dS']:.6f} "
        f"(max deviation {summary['max_abs_deviation']:.6f})"
    )


if __name__ == "__main__":
    main()

