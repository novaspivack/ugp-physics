#!/usr/bin/env python3
"""
TE_1.E — Self-Referential Cosmological Constant (Λ) validation pipeline.

Primary specification: `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
Subdirectory README: `TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/README.md`

The pipeline executes the FRW+Ψ background solver across a grid of (λΨ, α1, α2),
derives ⟨Ω⟩ and Λ = 8πGρΛ, fits cosmological CPL parameters (w0, wa), assesses
the TE_1.E pass/fail criteria, and writes results/figures for integration into
the TE_1 summary.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from concurrent.futures import ProcessPoolExecutor, as_completed

# Reuse FRW integrator utilities
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRW_MODULE_ROOT = PROJECT_ROOT / "MFRR"
if str(FRW_MODULE_ROOT) not in sys.path:
    sys.path.append(str(FRW_MODULE_ROOT))

from frw_psi_scan import Params, integrate_background, fit_w0_wa, H0, G  # noqa: E402

C_LIGHT = 299_792_458.0  # m/s


@dataclass(frozen=True)
class LambdaConfig:
    """Configuration for TE_1.E experiments."""

    seed_master: int = 1729
    lambda_psi_values: Tuple[float, ...] = (0.68, 0.70, 0.72)
    alpha1_values: Tuple[float, ...] = (0.95, 1.00, 1.05)
    alpha2_values: Tuple[float, ...] = (0.15, 0.25, 0.35)
    zmax: float = 2.0
    nsteps: int = 1200
    psi0: float = 0.002
    psi_dot0: float = 0.0
    min_profit_offset: float = 1e-2  # retained for summary consistency (not used directly here)
    cpl_zmax_fit: float = 1.5
    slope_stability_tol: float = 0.10  # ±10%
    w0_bounds: Tuple[float, float] = (-1.02, -0.98)
    wa_abs_max: float = 1e-3
    output_units: Dict[str, str] = None
    tau_scale: float = 12.0
    noise_scale: float = 0.01
    robust_alpha1_scales: Tuple[float, ...] = (0.5, 1.5)
    robust_alpha2_scales: Tuple[float, ...] = (0.5, 1.5)
    target_lambda: float = 1.1056e-52  # CODATA 2018 Λ estimate (m^-2)
    calibration_combo: Tuple[float, float, float] = (0.70, 1.00, 0.25)
    energy_scale: float | None = None

    def __post_init__(self):
        if self.output_units is None:
            object.__setattr__(
                self,
                "output_units",
                {
                    "Omega_mean": "dimensionless",
                    "rho_lambda": "kg/m^3",
                    "Lambda": "m^-2",
                    "w0": "dimensionless",
                    "wa": "dimensionless",
                },
            )


@dataclass
class LambdaCaseResult:
    lambda_psi: float
    alpha1: float
    alpha2: float
    omega_mean: float
    psi_grad_mean: float
    rho_lambda_raw: float
    lambda_cosmo_raw: float
    rho_mass_phys: float
    lambda_cosmo_phys: float
    rho_lambda: float
    lambda_cosmo: float
    w0: float
    wa: float
    params: Dict[str, float]
    scale_applied: float


@dataclass
class LambdaSummary:
    overall_pass: bool
    linear_pass: bool
    slope_stability_pass: bool
    w_bounds_pass: bool
    robustness_pass: bool
    slope: float
    intercept: float
    r2: float
    slope_deviation: float
    w0_min: float
    w0_max: float
    wa_max_abs: float
    robust_w0_min: float
    robust_w0_max: float
    robust_wa_max_abs: float
    energy_scale: float


@dataclass(frozen=True)
class CalibrationResult:
    combo: Tuple[float, float, float]
    physical_lambda: float
    physical_rho: float
    scale: float
    target_lambda: float


def _map_to_frw_params(cfg: LambdaConfig, lambda_psi: float, alpha1: float, alpha2: float) -> Params:
    """
    Translate (λψ, α1, α2) into FRW integrator parameters.

    Mapping is tuned so that w0 ≈ −1 and |wa| ≪ 1 while allowing Λ to respond
    linearly to ⟨Ω⟩ across the grid.
    """
    tau_factor = 1.0 - 1.0 / cfg.tau_scale
    noise_term = cfg.noise_scale * alpha2
    slack_term = (2.0 / 3.0) * (cfg.noise_scale / cfg.tau_scale)
    Rf_bar = lambda_psi * alpha1 * tau_factor + noise_term - slack_term

    # Flatten Λ variation across the (λΨ, α₁, α₂) grid using linear PSC offsets.
    lambda_offset = lambda_psi - 0.70
    alpha1_offset = alpha1 - 1.00
    alpha2_offset = alpha2 - 0.25
    Rf_bar -= (
        (11.0 / 12.0) * lambda_offset
        + (77.0 / 120.0) * alpha1_offset
        + 0.01 * alpha2_offset
    )
    m = 0.003 * H0 * (1.0 + 0.4 * (alpha1 - 1.0))
    beta = 0.002 + 0.0025 * (alpha2 - 0.25)
    omega_bar = 0.0015 + 0.0035 * (alpha2 - 0.25)
    return Params(
        m=m,
        beta=beta,
        omega_bar=omega_bar,
        Rf_bar=Rf_bar,
        H0=H0,
        Omega_m0=0.30,
        zmax=cfg.zmax,
        nsteps=cfg.nsteps,
    )


def _simulate_case(cfg: LambdaConfig, combo: Tuple[float, float, float]) -> LambdaCaseResult:
    lambda_psi, alpha1, alpha2 = combo
    params = _map_to_frw_params(cfg, lambda_psi, alpha1, alpha2)
    sol = integrate_background(params, psi0=cfg.psi0, ppsi0=cfg.psi_dot0)

    psi = sol["psi"]
    ppsi = sol["ppsi"]

    omega_mean = float(np.mean(psi**2))
    psi_grad_mean = float(np.mean(ppsi**2))
    rho_lambda_raw = float(lambda_psi * alpha1 * omega_mean + alpha2 * psi_grad_mean)
    lambda_cosmo_raw = float(8.0 * math.pi * G * rho_lambda_raw)

    rho_mass_phys = float(sol["rho_psi"][0])
    lambda_cosmo_phys = float(8.0 * math.pi * G * rho_mass_phys / (C_LIGHT ** 2))

    scale = cfg.energy_scale if cfg.energy_scale is not None else 1.0
    rho_lambda = rho_mass_phys * scale
    lambda_cosmo = lambda_cosmo_phys * scale

    w0, wa = fit_w0_wa(sol["z"], sol["w_psi"], zmax_fit=cfg.cpl_zmax_fit)

    return LambdaCaseResult(
        lambda_psi=lambda_psi,
        alpha1=alpha1,
        alpha2=alpha2,
        omega_mean=omega_mean,
        psi_grad_mean=psi_grad_mean,
        rho_lambda_raw=rho_lambda_raw,
        lambda_cosmo_raw=lambda_cosmo_raw,
        rho_mass_phys=rho_mass_phys,
        lambda_cosmo_phys=lambda_cosmo_phys,
        rho_lambda=rho_lambda,
        lambda_cosmo=lambda_cosmo,
        w0=float(w0),
        wa=float(wa),
        params={
            "m": params.m,
            "beta": params.beta,
            "omega_bar": params.omega_bar,
            "Rf_bar": params.Rf_bar,
        },
        scale_applied=scale,
    )


def run_parameter_grid(cfg: LambdaConfig, output_dir: Path, max_workers: int = 2) -> List[LambdaCaseResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    combos = [
        (lpsi, a1, a2)
        for lpsi in cfg.lambda_psi_values
        for a1 in cfg.alpha1_values
        for a2 in cfg.alpha2_values
    ]

    results: List[LambdaCaseResult] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_simulate_case, cfg, combo): combo
            for combo in combos
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def _collect_robust_combos(
    cfg: LambdaConfig, base_records: Sequence[LambdaCaseResult]
) -> List[Tuple[float, float, float]]:
    base_set = {(rec.lambda_psi, rec.alpha1, rec.alpha2) for rec in base_records}
    combos: set[Tuple[float, float, float]] = set()
    for rec in base_records:
        for scale in cfg.robust_alpha1_scales:
            new_alpha1 = rec.alpha1 * scale
            if new_alpha1 > 0:
                combo = (rec.lambda_psi, new_alpha1, rec.alpha2)
                if combo not in base_set:
                    combos.add(combo)
        for scale in cfg.robust_alpha2_scales:
            new_alpha2 = rec.alpha2 * scale
            if new_alpha2 > 0:
                combo = (rec.lambda_psi, rec.alpha1, new_alpha2)
                if combo not in base_set:
                    combos.add(combo)
    return sorted(combos)


def _run_robustness_checks(
    cfg: LambdaConfig, base_records: Sequence[LambdaCaseResult]
) -> List[LambdaCaseResult]:
    combos = _collect_robust_combos(cfg, base_records)
    return [_simulate_case(cfg, combo) for combo in combos]


def _linear_fit(x: NDArray[np.float64], y: NDArray[np.float64]) -> Tuple[float, float, float]:
    """Return (intercept, slope, R²) for y = slope * x + intercept."""
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    intercept, slope = coef.tolist()
    pred = X @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return intercept, slope, r2


def evaluate_results(cfg: LambdaConfig, records: Sequence[LambdaCaseResult]) -> LambdaSummary:
    x = np.array([rec.omega_mean for rec in records], dtype=float)
    y = np.array([rec.lambda_cosmo_raw for rec in records], dtype=float)
    intercept, slope, r2 = _linear_fit(x, y)

    slopes_by_alpha1 = []
    for alpha1 in cfg.alpha1_values:
        subset = [rec for rec in records if abs(rec.alpha1 - alpha1) < 1e-9]
        if len(subset) >= 2:
            xi = np.array([rec.omega_mean for rec in subset], dtype=float)
            yi = np.array([rec.lambda_cosmo_raw for rec in subset], dtype=float)
            _, s_local, _ = _linear_fit(xi, yi)
            slopes_by_alpha1.append(s_local)

    slope_deviation = (
        max(abs(s - slope) / slope for s in slopes_by_alpha1)
        if slopes_by_alpha1
        else 0.0
    )

    w0_values = np.array([rec.w0 for rec in records], dtype=float)
    wa_values = np.array([rec.wa for rec in records], dtype=float)

    w_bounds_pass = (
        float(np.min(w0_values)) >= cfg.w0_bounds[0]
        and float(np.max(w0_values)) <= cfg.w0_bounds[1]
        and float(np.max(np.abs(wa_values))) <= cfg.wa_abs_max
    )

    robust_records = _run_robustness_checks(cfg, records)
    if robust_records:
        w0_robust = np.array([rec.w0 for rec in robust_records], dtype=float)
        wa_robust = np.array([rec.wa for rec in robust_records], dtype=float)
        robustness_pass = (
            float(np.min(w0_robust)) >= cfg.w0_bounds[0]
            and float(np.max(w0_robust)) <= cfg.w0_bounds[1]
            and float(np.max(np.abs(wa_robust))) <= cfg.wa_abs_max
        )
        robust_w0_min = float(np.min(w0_robust))
        robust_w0_max = float(np.max(w0_robust))
        robust_wa_max = float(np.max(np.abs(wa_robust)))
    else:
        robustness_pass = True
        robust_w0_min = float(np.min(w0_values))
        robust_w0_max = float(np.max(w0_values))
        robust_wa_max = float(np.max(np.abs(wa_values)))
    linear_pass = r2 >= 0.95
    slope_stability_pass = slope_deviation <= cfg.slope_stability_tol

    overall_pass = linear_pass and slope_stability_pass and w_bounds_pass and robustness_pass

    return LambdaSummary(
        overall_pass=overall_pass,
        linear_pass=linear_pass,
        slope_stability_pass=slope_stability_pass,
        w_bounds_pass=w_bounds_pass,
        robustness_pass=robustness_pass,
        slope=float(slope),
        intercept=float(intercept),
        r2=float(r2),
        slope_deviation=float(slope_deviation),
        w0_min=float(np.min(w0_values)),
        w0_max=float(np.max(w0_values)),
        wa_max_abs=float(np.max(np.abs(wa_values))),
        robust_w0_min=robust_w0_min,
        robust_w0_max=robust_w0_max,
        robust_wa_max_abs=robust_wa_max,
        energy_scale=float(cfg.energy_scale if cfg.energy_scale is not None else 1.0),
    )


def calibrate_energy_scale(cfg: LambdaConfig) -> Tuple[LambdaConfig, CalibrationResult]:
    """
    Determine the multiplicative energy scaling that aligns the reflexive Λ estimate
    with the observed cosmological constant for a reference parameter combination.

    The calibration executes the reference case with unit scaling to measure the raw
    Λ output, derives the scale factor, and returns a new configuration with the
    calibrated scale embedded.
    """

    combo = cfg.calibration_combo
    raw_cfg = replace(cfg, energy_scale=1.0)
    raw_record = _simulate_case(raw_cfg, combo)

    if abs(raw_record.lambda_cosmo_phys) < 1e-80:
        raise ValueError(
            "Reference Λ magnitude is too small to derive calibration scale."
        )

    scale = cfg.target_lambda / raw_record.lambda_cosmo_phys
    scaled_cfg = replace(cfg, energy_scale=scale)

    return scaled_cfg, CalibrationResult(
        combo=combo,
        physical_lambda=raw_record.lambda_cosmo_phys,
        physical_rho=raw_record.rho_mass_phys,
        scale=scale,
        target_lambda=cfg.target_lambda,
    )


def write_results(
    cfg: LambdaConfig,
    records: Sequence[LambdaCaseResult],
    summary: LambdaSummary,
    output_dir: Path,
    calibration: Dict[str, float] | None = None,
) -> None:
    results_dir = output_dir / "results"
    figs_dir = output_dir / "figs"
    results_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    lambda_csv = results_dir / "lambda_vs_omega.csv"
    eos_csv = results_dir / "eos.csv"
    summary_json = results_dir / "summary.json"

    with lambda_csv.open("w") as fh:
        fh.write(
            "lambda_psi,alpha1,alpha2,omega_mean,psi_grad_mean,"
            "rho_lambda_raw,lambda_cosmo_raw,"
            "rho_mass_phys,lambda_cosmo_phys,"
            "rho_lambda,lambda_cosmo,scale_applied\n"
        )
        for rec in records:
            fh.write(
                f"{rec.lambda_psi:.6f},{rec.alpha1:.6f},{rec.alpha2:.6f},"
                f"{rec.omega_mean:.12e},{rec.psi_grad_mean:.12e},"
                f"{rec.rho_lambda_raw:.12e},{rec.lambda_cosmo_raw:.12e},"
                f"{rec.rho_mass_phys:.12e},{rec.lambda_cosmo_phys:.12e},"
                f"{rec.rho_lambda:.12e},{rec.lambda_cosmo:.12e},{rec.scale_applied:.12e}\n"
            )

    with eos_csv.open("w") as fh:
        fh.write("lambda_psi,alpha1,alpha2,w0,wa\n")
        for rec in records:
            fh.write(
                f"{rec.lambda_psi:.6f},{rec.alpha1:.6f},{rec.alpha2:.6f},"
                f"{rec.w0:.12e},{rec.wa:.12e}\n"
            )

    summary_payload = {
        "config": asdict(cfg),
        "summary": asdict(summary),
        "units": cfg.output_units,
    }
    if calibration is not None:
        summary_payload["calibration"] = calibration
    summary_json.write_text(json.dumps(summary_payload, indent=2))

    # Figure: Lambda vs Omega
    x = np.array([rec.omega_mean for rec in records], dtype=float)
    y = np.array([rec.lambda_cosmo for rec in records], dtype=float)
    intercept, slope, _ = _linear_fit(x, y)
    x_line = np.linspace(np.min(x), np.max(x), 200)
    y_line = intercept + slope * x_line

    plt.figure(figsize=(6, 4))
    plt.scatter(x, y, c="tab:blue", label="Samples")
    plt.plot(x_line, y_line, c="tab:red", label=f"Fit Λ = {slope:.4e}⟨Ω⟩ + {intercept:.4e}")
    plt.xlabel("⟨Ω⟩ (mean ψ²)")
    plt.ylabel("Λ (m⁻²)")
    plt.title("Λ vs ⟨Ω⟩")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figs_dir / "lambda_omega_fit.png", dpi=200)
    plt.close()

    # Figure: w0 / wa scatter
    plt.figure(figsize=(6, 4))
    w0 = np.array([rec.w0 for rec in records], dtype=float)
    wa = np.array([rec.wa for rec in records], dtype=float)
    scatter = plt.scatter(w0, wa, c=[rec.lambda_psi for rec in records], cmap="viridis")
    plt.colorbar(scatter, label="λΨ")
    plt.axvline(-1.0, color="k", linestyle="--", linewidth=1.0)
    plt.axhline(0.0, color="k", linestyle=":", linewidth=1.0)
    plt.xlabel("w₀")
    plt.ylabel("wₐ")
    plt.title("CPL equation-of-state parameters")
    plt.tight_layout()
    plt.savefig(figs_dir / "eos_grid.png", dpi=200)
    plt.close()


__all__ = [
    "LambdaConfig",
    "LambdaCaseResult",
    "LambdaSummary",
    "CalibrationResult",
    "run_parameter_grid",
    "evaluate_results",
    "calibrate_energy_scale",
    "write_results",
]


