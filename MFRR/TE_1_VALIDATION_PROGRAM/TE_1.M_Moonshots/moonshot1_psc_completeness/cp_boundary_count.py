"""
Entropy-area regression utilities for Moonshot 1.

This module loads area-law datasets (e.g. those generated in TE₁.O) and fits
the linear model

    S = α A + β_log log A + γ

It provides CLI access for quick sanity checks of the 1/4 area coefficient
and the adjudicator-driven logarithmic term.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np


@dataclass
class RegressionResult:
    alpha: float
    beta_log: float
    gamma: float
    r2: float
    samples: int


def load_area_entropy_series(path: str | Path, threshold: str | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load area/entropy arrays from an area-law JSON payload.

    Parameters
    ----------
    path:
        JSON file produced by `pr0_system.cli.area_law`.
    threshold:
        Optional key (string) selecting a specific density threshold. If None,
        the function attempts to read the top-level "area_series" keys.
    """
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))

    if threshold is None:
        # Backwards compatibility with earlier format
        area_series = payload["area_series"]
        entropy_series = payload["entropy_series"]
        return np.array(area_series, dtype=float), np.array(entropy_series, dtype=float)

    series_dict = payload["series"][threshold]
    return np.array(series_dict["area"], dtype=float), np.array(series_dict["entropy"], dtype=float)


def estimate_coefficients(area: np.ndarray, entropy: np.ndarray) -> RegressionResult:
    """
    Fit S = α A + β_log log A + γ via least squares.
    """
    if area.shape != entropy.shape:
        raise ValueError("Area and entropy arrays must have the same length.")

    mask = area > 0
    filtered_area = area[mask]
    filtered_entropy = entropy[mask]
    if filtered_area.size < 3:
        raise ValueError("Need at least three samples with positive area for regression.")

    log_area = np.log(filtered_area)
    X = np.column_stack([filtered_area, log_area, np.ones_like(filtered_area)])
    coeffs, *_ = np.linalg.lstsq(X, filtered_entropy, rcond=None)

    predictions = X @ coeffs
    ss_res = float(np.sum((filtered_entropy - predictions) ** 2))
    ss_tot = float(np.sum((filtered_entropy - np.mean(filtered_entropy)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    return RegressionResult(
        alpha=float(coeffs[0]),
        beta_log=float(coeffs[1]),
        gamma=float(coeffs[2]),
        r2=r2,
        samples=int(filtered_area.size),
    )


def summarize(result: RegressionResult) -> str:
    return (
        "Regression summary:\n"
        f"  α        = {result.alpha:.6f}\n"
        f"  β_log    = {result.beta_log:.6f}\n"
        f"  γ        = {result.gamma:.6f}\n"
        f"  R²       = {result.r2:.6f}\n"
        f"  samples  = {result.samples}"
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fit entropy/area relation for PSC boundary counts.")
    parser.add_argument("input", help="Path to area_law.json payload.")
    parser.add_argument("--threshold", help="Density threshold key (e.g. '0.6').", default=None)
    args = parser.parse_args()

    area, entropy = load_area_entropy_series(args.input, threshold=args.threshold)
    result = estimate_coefficients(area, entropy)
    print(summarize(result))


if __name__ == "__main__":
    main()


