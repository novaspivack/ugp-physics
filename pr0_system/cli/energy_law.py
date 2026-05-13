"""
Evaluate the log-depth reversible energy law for PR-0.

Collects density and entropy metrics across time, fits a linear model of
energy proxies vs log(step), and reports slope / goodness-of-fit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from pr0_system.evolution.ablowitz_ladik import PR0_Final


def _linear_fit(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(slope), float(intercept), r2


def _bootstrap_ci(
    x: np.ndarray,
    y: np.ndarray,
    samples: int,
    random_seed: int,
) -> Tuple[float, float]:
    rng = np.random.default_rng(random_seed)
    slopes = []
    n = len(x)
    for _ in range(samples):
        idx = rng.integers(0, n, size=n)
        slope, _, _ = _linear_fit(x[idx], y[idx])
        slopes.append(slope)
    lower, upper = np.percentile(slopes, [2.5, 97.5])
    return float(lower), float(upper)


def _piecewise_fit(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    mid = len(x) // 2
    x1, y1 = x[:mid], y[:mid]
    x2, y2 = x[mid:], y[mid:]
    slope1, intercept1, _ = _linear_fit(x1, y1)
    slope2, intercept2, _ = _linear_fit(x2, y2)
    pred = np.concatenate(
        [slope1 * x1 + intercept1, slope2 * x2 + intercept2],
        axis=0,
    )
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {
        "slope_early": float(slope1),
        "intercept_early": float(intercept1),
        "slope_late": float(slope2),
        "intercept_late": float(intercept2),
        "break_log_depth": float(x[mid]),
        "r2": r2,
    }


def run_experiment(steps: int, grid_size: int, bootstrap_samples: int, seed: int) -> Dict[str, object]:
    integrator = PR0_Final(L_x=grid_size, L_y=grid_size, g=0.18)
    integrator.set_soliton(
        x0=grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.2,
        width=3.0,
        velocity_x=0.12,
        sign=+1,
    )
    integrator.set_soliton(
        x0=2 * grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.2,
        width=3.0,
        velocity_x=-0.12,
        sign=-1,
    )

    history: List[Dict[str, float]] = []

    def observer(metrics: Dict[str, float]) -> None:
        history.append(metrics.copy())

    integrator.attach_observer(observer)

    for _ in range(steps):
        integrator.step(dt=0.01)

    filtered = [m for m in history if m["timestep"] > 0]
    timesteps = np.array([m["timestep"] for m in filtered], dtype=np.float64)
    density_sum = np.array([m["density_sum"] for m in filtered], dtype=np.float64)
    internal_entropy = np.array([m["internal_entropy"] for m in filtered], dtype=np.float64)

    log_depth = np.log(timesteps + 1e-12)

    slope_density, intercept_density, r2_density = _linear_fit(log_depth, density_sum)
    slope_entropy, intercept_entropy, r2_entropy = _linear_fit(log_depth, internal_entropy)

    density_ci = _bootstrap_ci(log_depth, density_sum, bootstrap_samples, seed)
    entropy_ci = _bootstrap_ci(log_depth, internal_entropy, bootstrap_samples, seed + 1)

    density_piecewise = _piecewise_fit(log_depth, density_sum)
    entropy_piecewise = _piecewise_fit(log_depth, internal_entropy)

    return {
        "steps": steps,
        "grid_size": grid_size,
        "linear": {
            "density": {
                "slope": slope_density,
                "intercept": intercept_density,
                "r2": r2_density,
                "slope_ci95": density_ci,
            },
            "entropy": {
                "slope": slope_entropy,
                "intercept": intercept_entropy,
                "r2": r2_entropy,
                "slope_ci95": entropy_ci,
            },
        },
        "piecewise": {
            "density": density_piecewise,
            "entropy": entropy_piecewise,
        },
        "series": {
            "log_depth": log_depth.tolist(),
            "density_sum": density_sum.tolist(),
            "internal_entropy": internal_entropy.tolist(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Log-depth reversible energy law experiment.")
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument("--bootstrap-samples", type=int, default=256)
    parser.add_argument("--seed", type=int, default=20251110)
    parser.add_argument("--output", type=str, default="pr0_logs/energy_law.json")
    args = parser.parse_args()

    result = run_experiment(
        steps=args.steps,
        grid_size=args.grid,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    lin_density = result["linear"]["density"]
    lin_entropy = result["linear"]["entropy"]
    print(
        "[Energy] linear slopes: density={sd:.4f} (CI {sd_ci[0]:.4f},{sd_ci[1]:.4f}), "
        "entropy={se:.4f} (CI {se_ci[0]:.4f},{se_ci[1]:.4f})".format(
            sd=lin_density["slope"],
            sd_ci=lin_density["slope_ci95"],
            se=lin_entropy["slope"],
            se_ci=lin_entropy["slope_ci95"],
        )
    )
    print(
        "[Energy] r² linear: density={rd:.3f}, entropy={re:.3f}".format(
            rd=lin_density["r2"],
            re=lin_entropy["r2"],
        )
    )
    print(
        "[Energy] piecewise slopes: density=({sd1:.4f},{sd2:.4f}), entropy=({se1:.4f},{se2:.4f})".format(
            sd1=result["piecewise"]["density"]["slope_early"],
            sd2=result["piecewise"]["density"]["slope_late"],
            se1=result["piecewise"]["entropy"]["slope_early"],
            se2=result["piecewise"]["entropy"]["slope_late"],
        )
    )
    print(f"[Energy] results written to {output_path}")


if __name__ == "__main__":
    main()


