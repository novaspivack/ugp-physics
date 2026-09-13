"""
Demonstrate gauge converter invariants (PR-0 ↔ analytic proxy).

Applies a smooth analytic-like transform to ψ, renormalizes, and compares
invariants (density sum, entropy, support area).  Reports relative errors to
confirm preservation within tolerance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from scipy.ndimage import gaussian_filter

from pr0_system.evolution.ablowitz_ladik import PR0_Final


def invariants(psi: np.ndarray) -> Dict[str, float]:
    density = np.abs(psi) ** 2
    density_sum = float(np.sum(density))
    prob = density / (density_sum + 1e-12)
    entropy = float(-np.sum(prob * np.log(prob + 1e-12)))
    support_area = float(np.sum(density > 0.5))
    return {
        "density_sum": density_sum,
        "entropy": entropy,
        "support_area": support_area,
    }


def _smooth_with_schedule(
    psi: np.ndarray,
    sigmas: List[float],
    weights: Optional[List[float]],
) -> np.ndarray:
    if not sigmas:
        raise ValueError("at least one sigma value is required")
    if weights is None:
        weights = [1.0 for _ in sigmas]
    if len(weights) != len(sigmas):
        raise ValueError("weights must match sigma schedule length")

    total_weight = float(sum(weights))
    if total_weight <= 0:
        raise ValueError("sum of weights must be positive")

    filtered_real = np.zeros_like(psi.real)
    filtered_imag = np.zeros_like(psi.imag)
    for sigma, weight in zip(sigmas, weights):
        filtered_real += weight * gaussian_filter(psi.real, sigma=sigma)
        filtered_imag += weight * gaussian_filter(psi.imag, sigma=sigma)
    filtered_real /= total_weight
    filtered_imag /= total_weight
    analytic = filtered_real + 1j * filtered_imag

    analytic_norm = np.sqrt(np.sum(np.abs(analytic) ** 2))
    if analytic_norm > 0:
        target_norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        analytic *= target_norm / analytic_norm
    return analytic


def run_experiment(
    steps: int,
    grid_size: int,
    sigmas: List[float],
    weights: Optional[List[float]],
) -> Dict[str, float]:
    integrator = PR0_Final(L_x=grid_size, L_y=grid_size, g=0.18)
    integrator.set_soliton(
        x0=grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.0,
        width=3.0,
        velocity_x=0.08,
        sign=+1,
    )
    integrator.set_soliton(
        x0=2 * grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.0,
        width=3.0,
        velocity_x=-0.08,
        sign=-1,
    )

    for _ in range(steps):
        integrator.step(dt=0.01)

    psi = integrator.psi.copy()
    before = invariants(psi)

    analytic = _smooth_with_schedule(psi, sigmas=sigmas, weights=weights)
    after = invariants(analytic)

    errors = {
        key: float(np.abs(after[key] - before[key]) / (before[key] + 1e-12))
        for key in before
    }

    return {
        "steps": steps,
        "grid_size": grid_size,
        "sigma_schedule": sigmas,
        "weights": weights or [1.0 for _ in sigmas],
        "before": before,
        "after": after,
        "relative_errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gauge converter invariant check.")
    parser.add_argument("--steps", type=int, default=1500)
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument(
        "--sigma",
        type=float,
        action="append",
        dest="sigmas",
        help="Gaussian smoothing σ values (can repeat for schedule).",
    )
    parser.add_argument(
        "--weight",
        type=float,
        action="append",
        dest="weights",
        help="Weights for each σ (defaults to uniform if omitted).",
    )
    parser.add_argument("--output", type=str, default="pr0_logs/gauge_converter.json")
    args = parser.parse_args()

    sigmas = args.sigmas or [0.6, 0.3, 0.1]
    weights = args.weights
    result = run_experiment(steps=args.steps, grid_size=args.grid, sigmas=sigmas, weights=weights)
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    err = result["relative_errors"]
    print(
        "[Gauge] rel. errors density={density_sum:.3e}, entropy={entropy:.3e}, area={support_area:.3e}".format(
            **err
        )
    )
    print(
        "[Gauge] schedule σ="
        + ",".join(f"{sigma:.2f}" for sigma in result["sigma_schedule"])
        + " weights="
        + ",".join(f"{w:.2f}" for w in result["weights"])
    )
    print(f"[Gauge] results written to {output_path}")


if __name__ == "__main__":
    main()


