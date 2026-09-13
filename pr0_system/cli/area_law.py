"""
Estimate β_log for the PR-0 reflexive area law.

Uses observer metrics (support_area, internal_entropy) to fit
S ≈ α·A + β·log(A) + γ and reports the coefficients.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from pr0_system.evolution.ablowitz_ladik import PR0_Final


def _fit_area_entropy(
    area: np.ndarray,
    entropy: np.ndarray,
    weight_mode: Optional[str] = None,
) -> Tuple[Dict[str, float], np.ndarray]:
    log_area = np.log(area + 1e-12)
    X = np.column_stack([area, log_area, np.ones_like(area)])
    y = entropy

    if weight_mode == "area":
        weights = area
    elif weight_mode == "entropy":
        weights = entropy
    else:
        weights = None

    if weights is not None:
        w = np.sqrt(np.clip(weights, 1e-12, None))
        Xw = X * w[:, None]
        yw = y * w
        coeff, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    else:
        coeff, *_ = np.linalg.lstsq(X, y, rcond=None)

    residuals = y - X @ coeff
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    summary = {
        "alpha": float(coeff[0]),
        "beta_log": float(coeff[1]),
        "gamma": float(coeff[2]),
        "r2": r2,
        "area_mean": float(np.mean(area)),
        "entropy_mean": float(np.mean(entropy)),
        "samples": int(len(area)),
    }
    if weight_mode:
        summary["weight_mode"] = weight_mode
    return summary, residuals


def run_experiment(
    steps: int,
    grid_size: int,
    thresholds: List[float],
    quantile: float | None,
    mass_fraction: float | None,
    weight_mode: Optional[str],
    g: float,
) -> Dict[str, object]:
    integrator = PR0_Final(L_x=grid_size, L_y=grid_size, g=g)
    integrator.set_soliton(
        x0=grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.4,
        width=3.2,
        velocity_x=0.10,
        sign=+1,
    )
    integrator.set_soliton(
        x0=2 * grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.4,
        width=3.2,
        velocity_x=-0.10,
        sign=-1,
    )

    histories: Dict[float, Dict[str, List[float]]] = {
        threshold: {"area": [], "entropy": []} for threshold in thresholds
    }
    mass_history_area: List[float] = []
    mass_history_entropy: List[float] = []

    for _ in range(steps):
        integrator.step(dt=0.01)
        density = np.abs(integrator.psi) ** 2
        prob = density / np.sum(density)
        entropy = float(-np.sum(prob * np.log(prob + 1e-12)))

        for threshold in thresholds:
            area = float(np.sum(density > threshold))
            if area <= 0:
                continue
            histories[threshold]["area"].append(area)
            histories[threshold]["entropy"].append(entropy)

        if mass_fraction is not None and 0.0 < mass_fraction < 1.0:
            flat = np.sort(prob.flatten())[::-1]
            if flat.size == 0:
                continue
            cumsum = np.cumsum(flat)
            idx = int(np.searchsorted(cumsum, mass_fraction))
            area_count = float(min(idx + 1, flat.size))
            if area_count > 0:
                mass_history_area.append(area_count)
                mass_history_entropy.append(entropy)

    fits: Dict[str, Dict[str, float]] = {}
    series: Dict[str, Dict[str, List[float]]] = {}
    for threshold, data in histories.items():
        if len(data["area"]) < 10:
            raise RuntimeError(f"insufficient samples for area-law fit at threshold {threshold}")
        area = np.array(data["area"], dtype=np.float64)
        entropy = np.array(data["entropy"], dtype=np.float64)
        summary, _ = _fit_area_entropy(area, entropy, weight_mode=weight_mode)
        fits[str(threshold)] = summary
        series[str(threshold)] = {
            "area": data["area"],
            "entropy": data["entropy"],
        }

    quantile_fit: Dict[str, float] | None = None
    quantile_threshold: float | None = None
    if quantile is not None:
        # pick threshold with largest median area for tail analysis
        selected_threshold = max(
            histories.keys(),
            key=lambda t: np.median(histories[t]["area"]) if histories[t]["area"] else 0.0,
        )
        area = np.array(histories[selected_threshold]["area"], dtype=np.float64)
        entropy = np.array(histories[selected_threshold]["entropy"], dtype=np.float64)
        cutoff = np.quantile(area, quantile)
        mask = area >= cutoff
        if np.count_nonzero(mask) >= 10:
            tail_summary, _ = _fit_area_entropy(area[mask], entropy[mask], weight_mode=weight_mode)
            tail_summary["cutoff"] = float(cutoff)
            tail_summary["threshold"] = selected_threshold
            quantile_fit = tail_summary
            quantile_threshold = selected_threshold

    mass_fraction_fit: Dict[str, float] | None = None
    if mass_fraction is not None and mass_history_area:
        area = np.array(mass_history_area, dtype=np.float64)
        entropy = np.array(mass_history_entropy, dtype=np.float64)
        if len(area) < 10:
            raise RuntimeError("insufficient samples for mass-fraction area-law fit")
        mass_fraction_fit, _ = _fit_area_entropy(area, entropy, weight_mode=weight_mode)
        mass_fraction_fit["weight_mode"] = weight_mode or "none"
        mass_fraction_fit["mass_fraction"] = mass_fraction

    result: Dict[str, object] = {
        "steps": steps,
        "grid_size": grid_size,
        "thresholds": thresholds,
        "fits": fits,
        "series": series,
    }
    if quantile_fit is not None:
        result["quantile_fit"] = quantile_fit
        result["quantile_threshold"] = quantile_threshold
        result["quantile"] = quantile
    if mass_fraction_fit is not None:
        result["mass_fraction_fit"] = mass_fraction_fit
        result["mass_fraction_series"] = {
            "area": mass_history_area,
            "entropy": mass_history_entropy,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Reflexive area-law experiment.")
    parser.add_argument("--steps", type=int, default=3500)
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument("--g", type=float, default=0.19, help="Nonlinearity parameter for PR-0 integrator.")
    parser.add_argument(
        "--threshold",
        type=float,
        action="append",
        dest="thresholds",
        help="Density thresholds (>0) for support area (can be repeated).",
    )
    parser.add_argument(
        "--quantile",
        type=float,
        default=0.9,
        help="Quantile (0-1) for tail fit; set <0 to disable.",
    )
    parser.add_argument(
        "--mass-fraction",
        type=float,
        default=None,
        help="If set (0-1), use minimal support covering this probability mass for an additional fit.",
    )
    parser.add_argument(
        "--weight-mode",
        type=str,
        default="area",
        choices=["none", "area", "entropy"],
        help="Regression weighting scheme (default: area).",
    )
    parser.add_argument("--output", type=str, default="pr0_logs/area_law.json")
    args = parser.parse_args()

    thresholds = args.thresholds or [0.4, 0.6, 0.8]
    thresholds = sorted(set(thresholds))
    quantile = None if args.quantile < 0 else args.quantile

    weight_mode = args.weight_mode if args.weight_mode != "none" else None

    result = run_experiment(
        steps=args.steps,
        grid_size=args.grid,
        thresholds=thresholds,
        quantile=quantile,
        mass_fraction=args.mass_fraction,
        weight_mode=weight_mode,
        g=args.g,
    )
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    for threshold in thresholds:
        fit = result["fits"][str(threshold)]
        print(
            "[Area] threshold={thr:.2f} α={alpha:.4f} β_log={beta_log:.4f} r²={r2:.3f} samples={samples}".format(
                thr=threshold,
                **fit,
            )
        )
    if "quantile_fit" in result:
        qfit = result["quantile_fit"]
        print(
            "[Area] quantile={quant:.2f} threshold={thr:.2f} β_log={beta_log:.4f} r²={r2:.3f} samples={samples}".format(
                quant=result["quantile"],
                thr=qfit["threshold"],
                beta_log=qfit["beta_log"],
                r2=qfit["r2"],
                samples=qfit["samples"],
            )
        )
    if "mass_fraction_fit" in result:
        mfit = result["mass_fraction_fit"]
        print(
            "[Area] mass_fraction={mf:.2f} β_log={beta_log:.4f} r²={r2:.3f} samples={samples}".format(
                mf=mfit["mass_fraction"],
                beta_log=mfit["beta_log"],
                r2=mfit["r2"],
                samples=mfit["samples"],
            )
        )
    print(f"[Area] results written to {output_path}")


if __name__ == "__main__":
    main()


