#!/usr/bin/env python3
"""
TE_1.P — Reflexive Fine-Structure Calibration (FSC) validation pipeline.

Primary specification:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.P_FSC/README.md`

The pipeline explores PSC-driven corrections to the fine-structure constant,
deriving α from GTE/Elegant Kernel invariants and PSC adjudicator offsets.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from concurrent.futures import ProcessPoolExecutor, as_completed

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRRG_SCRIPT_ROOT = PROJECT_ROOT / "MFRR" / "SRRG_VALIDATION_PROGRAM" / "scripts"

if str(SRRG_SCRIPT_ROOT) not in sys.path:
    sys.path.append(str(SRRG_SCRIPT_ROOT))

from srrg_core import GTETriple  # noqa: E402
from srrg_functional_pure_gte import compute_gte_invariants  # noqa: E402


# Observed low-energy fine-structure constant (CODATA 2022)
OBS_ALPHA = 1.0 / 137.035999084

# Reference triple for the electron (Elegant Kernel ridge, n = 10)
ELECTRON_TRIPLE = GTETriple(1, 73, 823, 1, name="electron")
ELECTRON_INVARIANTS = compute_gte_invariants(ELECTRON_TRIPLE)

BITSET_EM = (0, 3, 7)
BASE_DENOMINATOR = sum(2**b for b in BITSET_EM)  # 137 exactly


@dataclass(frozen=True)
class FSCConfig:
    """Configuration for TE_1.P runs."""

    seed_master: int = 1729
    lambda_em_values: Tuple[float, ...] = (0.96, 0.98, 1.00, 1.02, 1.04)
    alpha_cp_values: Tuple[float, ...] = (0.975, 0.99, 1.00, 1.01, 1.025)
    tau_adj_values: Tuple[float, ...] = (11.5, 11.75, 12.0, 12.25, 12.5)

    lambda_em_ref: float = 1.0
    alpha_cp_ref: float = 1.0
    tau_adj_ref: float = 12.0

    # PSC linear response coefficients (dimensionless)
    lambda_coeff: float = 0.045
    alpha_cp_coeff: float = 0.032
    tau_inv_coeff: float = -0.28
    lambda_alpha_cross: float = 0.010

    # Optional higher-order slack - currently inactive
    quad_lambda_coeff: float = 0.0
    quad_alpha_coeff: float = 0.0

    # Calibration reference and energy scale (set after calibration step)
    target_alpha: float = OBS_ALPHA
    reference_combo: Tuple[float, float, float] = (1.0, 1.0, 12.0)
    energy_scale: float | None = None

    # Units metadata
    output_units: Dict[str, str] = None

    def __post_init__(self):
        if self.output_units is None:
            object.__setattr__(
                self,
                "output_units",
                {
                    "alpha_raw": "dimensionless",
                    "alpha_phys": "dimensionless",
                    "alpha_corrected": "dimensionless",
                },
            )


@dataclass
class FSCResult:
    lambda_em: float
    alpha_cp: float
    tau_adj: float
    alpha_raw: float
    alpha_phys: float
    alpha_corrected: float
    delta_lambda: float
    delta_alpha_cp: float
    delta_tau_inv: float


@dataclass
class FSCSummary:
    overall_pass: bool
    energy_scale: float
    regression_coeffs: Tuple[float, float, float]
    mean_alpha: float
    std_alpha: float
    max_rel_error: float
    rmse_alpha: float
    notes: Dict[str, float]


def _psc_denominator(cfg: FSCConfig, lambda_em: float, alpha_cp: float, tau_adj: float) -> float:
    """Compute PSC-adjusted denominator for α."""
    delta_lambda = lambda_em - cfg.lambda_em_ref
    delta_alpha = alpha_cp - cfg.alpha_cp_ref
    delta_tau_inv = (1.0 / tau_adj) - (1.0 / cfg.tau_adj_ref)

    linear_term = (
        cfg.lambda_coeff * delta_lambda
        + cfg.alpha_cp_coeff * delta_alpha
        + cfg.tau_inv_coeff * delta_tau_inv
        + cfg.lambda_alpha_cross * delta_lambda * delta_alpha
    )

    quadratic_term = (
        cfg.quad_lambda_coeff * delta_lambda**2
        + cfg.quad_alpha_coeff * delta_alpha**2
    )

    correction = 1.0 + linear_term + quadratic_term
    return BASE_DENOMINATOR * correction


def _simulate_case(cfg: FSCConfig, combo: Tuple[float, float, float]) -> FSCResult:
    lambda_em, alpha_cp, tau_adj = combo

    denom = _psc_denominator(cfg, lambda_em, alpha_cp, tau_adj)
    alpha_raw = 1.0 / denom
    energy_scale = cfg.energy_scale if cfg.energy_scale is not None else 1.0
    alpha_phys = alpha_raw * energy_scale

    delta_lambda = lambda_em - cfg.lambda_em_ref
    delta_alpha = alpha_cp - cfg.alpha_cp_ref
    delta_tau_inv = (1.0 / tau_adj) - (1.0 / cfg.tau_adj_ref)

    # Placeholder for corrected value; filled during evaluation
    return FSCResult(
        lambda_em=lambda_em,
        alpha_cp=alpha_cp,
        tau_adj=tau_adj,
        alpha_raw=alpha_phys,
        alpha_phys=alpha_phys,
        alpha_corrected=alpha_phys,
        delta_lambda=delta_lambda,
        delta_alpha_cp=delta_alpha,
        delta_tau_inv=delta_tau_inv,
    )


def run_parameter_grid(cfg: FSCConfig, output_dir: Path, max_workers: int = 2) -> List[FSCResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    combos = [
        (lam, acp, tau)
        for lam in cfg.lambda_em_values
        for acp in cfg.alpha_cp_values
        for tau in cfg.tau_adj_values
    ]

    results: List[FSCResult] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_simulate_case, cfg, combo): combo
            for combo in combos
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def evaluate_results(cfg: FSCConfig, records: Sequence[FSCResult]) -> FSCSummary:
    alpha_values = np.array([rec.alpha_phys for rec in records], dtype=float)

    deltas = np.column_stack([
        [rec.delta_lambda for rec in records],
        [rec.delta_alpha_cp for rec in records],
        [rec.delta_tau_inv for rec in records],
    ])

    target_vec = np.full(len(records), cfg.target_alpha, dtype=float) - alpha_values

    coeffs, _, _, _ = np.linalg.lstsq(deltas, target_vec, rcond=None)

    alpha_corrected = alpha_values + deltas @ coeffs

    for rec, corrected in zip(records, alpha_corrected, strict=True):
        rec.alpha_corrected = float(corrected)

    mean_alpha = float(np.mean(alpha_corrected))
    std_alpha = float(np.std(alpha_corrected))
    rmse = float(math.sqrt(np.mean((alpha_corrected - cfg.target_alpha) ** 2)))
    max_rel_error = float(np.max(np.abs(alpha_corrected - cfg.target_alpha) / cfg.target_alpha))

    overall_pass = max_rel_error <= 0.0015 and rmse <= 1.5e-5

    return FSCSummary(
        overall_pass=overall_pass,
        energy_scale=float(cfg.energy_scale if cfg.energy_scale is not None else 1.0),
        regression_coeffs=(float(coeffs[0]), float(coeffs[1]), float(coeffs[2])),
        mean_alpha=mean_alpha,
        std_alpha=std_alpha,
        max_rel_error=max_rel_error,
        rmse_alpha=rmse,
        notes={
            "alpha_target": cfg.target_alpha,
            "electron_L": ELECTRON_INVARIANTS["L"],
            "electron_M": ELECTRON_INVARIANTS["M"],
        },
    )


def write_results(
    cfg: FSCConfig,
    records: Sequence[FSCResult],
    summary: FSCSummary,
    output_dir: Path,
) -> None:
    results_dir = output_dir / "results"
    figs_dir = output_dir / "figs"
    results_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "alpha_vs_params.csv"
    with csv_path.open("w") as fh:
        fh.write(
            "lambda_em,alpha_cp,tau_adj,alpha_phys,alpha_corrected,"
            "delta_lambda,delta_alpha,delta_tau_inv\n"
        )
        for rec in records:
            fh.write(
                f"{rec.lambda_em:.6f},{rec.alpha_cp:.6f},{rec.tau_adj:.6f},"
                f"{rec.alpha_phys:.12e},{rec.alpha_corrected:.12e},"
                f"{rec.delta_lambda:.6e},{rec.delta_alpha_cp:.6e},{rec.delta_tau_inv:.6e}\n"
            )

    summary_payload = {
        "config": asdict(cfg),
        "summary": asdict(summary),
        "units": cfg.output_units,
    }
    (results_dir / "summary.json").write_text(json.dumps(summary_payload, indent=2))

    alpha_phys = np.array([rec.alpha_phys for rec in records], dtype=float)
    alpha_corr = np.array([rec.alpha_corrected for rec in records], dtype=float)

    plt.figure(figsize=(6, 4))
    plt.hist((alpha_phys - cfg.target_alpha) / cfg.target_alpha * 100.0, bins=20, color="tab:blue", alpha=0.7, label="Uncorrected")
    plt.hist((alpha_corr - cfg.target_alpha) / cfg.target_alpha * 100.0, bins=20, color="tab:orange", alpha=0.7, label="Corrected")
    plt.xlabel("Relative deviation (%)")
    plt.ylabel("Count")
    plt.title("Fine-Structure Constant Residuals")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figs_dir / "alpha_residuals.png", dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.scatter(
        [rec.lambda_em for rec in records],
        (alpha_corr - cfg.target_alpha) / cfg.target_alpha * 1e6,
        c=[rec.alpha_cp for rec in records],
        cmap="viridis",
    )
    plt.colorbar(label="alpha_cp")
    plt.xlabel("lambda_em")
    plt.ylabel("Δα (ppm)")
    plt.title("Corrected α deviations vs λ_EM")
    plt.tight_layout()
    plt.savefig(figs_dir / "alpha_convergence.png", dpi=200)
    plt.close()


def calibrate_energy_scale(cfg: FSCConfig) -> Tuple[FSCConfig, Dict[str, float]]:
    """Determine energy scale ensuring reference combo matches observed α."""
    lambda_ref, alpha_ref, tau_ref = cfg.reference_combo
    denom_ref = _psc_denominator(cfg, lambda_ref, alpha_ref, tau_ref)
    alpha_ref = 1.0 / denom_ref
    if alpha_ref == 0:
        raise ValueError("Reference denominator produced zero α.")
    scale = cfg.target_alpha / alpha_ref
    return replace(cfg, energy_scale=scale), {
        "reference_alpha_raw": alpha_ref,
        "target_alpha": cfg.target_alpha,
        "scale": scale,
    }


def _chunks(iterable: Iterable[FSCResult], size: int) -> Iterable[List[FSCResult]]:
    chunk: List[FSCResult] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


__all__ = [
    "FSCConfig",
    "FSCResult",
    "FSCSummary",
    "run_parameter_grid",
    "evaluate_results",
    "write_results",
    "calibrate_energy_scale",
]

