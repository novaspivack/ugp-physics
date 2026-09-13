#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Reference: TE_1.R plan (1_1_TE_1R_PLAN.md)
"""
Spectral convergence validator for TE_1.R.

Consumes SRRG spectral results (ts9_spectral_convergence_results.json) and
computes diagnostic ratios required for Step C and the geometric closure task.
Outputs go to results/spectral/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_results(path: Path) -> Dict:
    return json.loads(path.read_text())


def summarize(entries: List[Dict], lambda1_theory: float) -> Dict[str, float]:
    ratios = [entry["spectral_gap"] / lambda1_theory for entry in entries]
    ricci = [entry["mean_ricci"] for entry in entries]
    return {
        "n_cases": len(entries),
        "mean_eigen_ratio": sum(ratios) / len(ratios),
        "min_eigen_ratio": min(ratios),
        "max_eigen_ratio": max(ratios),
        "mean_ricci": sum(ricci) / len(ricci),
        "min_ricci": min(ricci),
        "max_ricci": max(ricci),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Spectral convergence analyzer.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to ts9_spectral_convergence_results.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/spectral"),
        help="Output directory (default: results/spectral).",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file {args.input} not found.")

    data = load_results(args.input)
    entries = data.get("results", [])
    if not entries:
        raise SystemExit("No spectral cases found in input.")

    theoretical = data.get("theoretical_values", {})
    lambda1 = theoretical.get("lambda_1", 1.0)
    summary = summarize(entries, lambda1)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2))

    print(
        "[Spectral] mean eigen ratio "
        f"{summary['mean_eigen_ratio']:.6f} "
        f"(min {summary['min_eigen_ratio']:.6f}, max {summary['max_eigen_ratio']:.6f})"
    )


if __name__ == "__main__":
    main()

