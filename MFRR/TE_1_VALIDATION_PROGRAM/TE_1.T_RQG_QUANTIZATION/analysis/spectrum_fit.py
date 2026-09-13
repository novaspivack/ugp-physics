#!/usr/bin/env python3
"""Spectrum fitting for TE1.T curvature increments.

Loads tensors produced by `analysis/rqg_lattice.py`, computes eigenvalue
statistics, and estimates the curvature quantum step size by rounding to the
nearest integer multiple.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fit curvature spectrum from lattice tensors")
    parser.add_argument("--tensors", required=True, type=Path, help="NPZ file with lattice tensors")
    parser.add_argument("--output", type=Path, default=Path("results/spectrum_summary.json"), help="Output JSON path")
    parser.add_argument("--step-init", type=float, default=None, help="Initial guess for quantum step size")
    return parser.parse_args()


def load_tensors(path: Path) -> np.ndarray:
    data = np.load(path)
    return data["tensors"]


def estimate_step(eigenvalues: np.ndarray, step_init: float | None) -> float:
    if step_init is None:
        return float(np.median(np.abs(eigenvalues)))
    return float(step_init)


def fit_quantum_levels(eigenvalues: np.ndarray, step: float) -> Dict[str, float]:
    quanta = np.round(eigenvalues / step)
    residuals = eigenvalues - quanta * step
    return {
        "step": step,
        "mean_residual": float(np.mean(residuals)),
        "std_residual": float(np.std(residuals)),
        "max_residual": float(np.max(np.abs(residuals))),
    }


def main() -> None:
    args = parse_args()
    tensors = load_tensors(args.tensors)
    eigenvalues = []
    for tensor in tensors:
        spatial = tensor[1:4, 1:4]
        evals = np.linalg.eigvalsh(spatial)
        eigenvalues.extend(evals.tolist())
    eigenvalues = np.asarray(eigenvalues)

    step = estimate_step(eigenvalues, args.step_init)
    fit_stats = fit_quantum_levels(eigenvalues, step)
    histogram, edges = np.histogram(eigenvalues / step, bins=range(-5, 6))

    summary = {
        "tensors": str(args.tensors.resolve()),
        "step": fit_stats["step"],
        "mean_residual": fit_stats["mean_residual"],
        "std_residual": fit_stats["std_residual"],
        "max_residual": fit_stats["max_residual"],
        "histogram_bins": edges[:-1].tolist(),
        "histogram_counts": histogram.tolist(),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Saved spectrum summary to {args.output}")


if __name__ == "__main__":
    main()
