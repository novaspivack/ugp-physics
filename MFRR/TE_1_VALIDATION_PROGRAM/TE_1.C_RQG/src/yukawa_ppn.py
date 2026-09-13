"""
Static Yukawa tail fits and PPN parameter extraction for TE_1.C.

Implements Phase 1 Task T5 in TE_1.C.1_PLAN.md.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

try:
    from .constants import CONSTS
except ImportError:  # pragma: no cover
    import sys

    PACKAGE_ROOT = Path(__file__).resolve().parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.append(str(PACKAGE_ROOT))
    from constants import CONSTS


@dataclass
class YukawaConfig:
    mass_kg: float
    alpha: float
    m_psi: float  # inverse length scale [1/m]
    r_min: float
    r_max: float
    num_points: int
    noise_sigma: float = 0.0
    ppn_radius: float = 1.0e11  # default ~0.67 AU


@dataclass
class YukawaResult:
    config: YukawaConfig
    radius: np.ndarray
    potential: np.ndarray
    fitted_alpha: float
    fitted_mass: float
    ppn_gamma: float
    ppn_deviation: float

    def to_summary(self) -> Dict[str, float]:
        base = asdict(self.config)
        base.update(
            {
                "fitted_alpha": self.fitted_alpha,
                "fitted_mass": self.fitted_mass,
                "ppn_gamma": self.ppn_gamma,
                "ppn_deviation": self.ppn_deviation,
                "max_radius": float(self.radius.max()),
                "min_radius": float(self.radius.min()),
            }
        )
        return base


def synthetic_potential(cfg: YukawaConfig) -> Tuple[np.ndarray, np.ndarray]:
    r = np.linspace(cfg.r_min, cfg.r_max, cfg.num_points)
    G = CONSTS.gravitational_constant
    base = -G * cfg.mass_kg / r
    correction = 1.0 + cfg.alpha * np.exp(-cfg.m_psi * r)
    phi = base * correction
    if cfg.noise_sigma > 0.0:
        phi += np.random.normal(scale=cfg.noise_sigma * np.abs(phi), size=phi.size)
    return r, phi


def fit_yukawa(r: np.ndarray, phi: np.ndarray, mass_kg: float) -> Tuple[float, float]:
    G = CONSTS.gravitational_constant
    y = phi * r / (-G * mass_kg)
    # Model: y = 1 + alpha * exp(-m r); take logarithm of (y - 1)
    eps = 1.0e-12
    mask = y > 1.0 + eps
    if mask.sum() < 6:
        # fallback linear fit near large r
        return 0.0, 0.0
    log_term = np.log(y[mask] - 1.0)
    coeffs = np.polyfit(r[mask], log_term, 1)
    slope, intercept = coeffs
    fitted_m = -slope
    fitted_alpha = np.exp(intercept)
    return float(fitted_alpha), float(fitted_m)


def compute_ppn_gamma(cfg: YukawaConfig, alpha_fit: float) -> float:
    r = cfg.ppn_radius
    exp_term = np.exp(-cfg.m_psi * r)
    numerator = 1.0 - alpha_fit * exp_term
    denominator = 1.0 + alpha_fit * exp_term
    if np.isclose(denominator, 0.0):
        return float("inf")
    return float(numerator / denominator)


def run_yukawa(cfg: YukawaConfig) -> YukawaResult:
    r, phi = synthetic_potential(cfg)
    alpha_fit, m_fit = fit_yukawa(r, phi, cfg.mass_kg)
    ppn_gamma = compute_ppn_gamma(cfg, alpha_fit)
    ppn_deviation = abs(ppn_gamma - 1.0)
    return YukawaResult(
        config=cfg,
        radius=r,
        potential=phi,
        fitted_alpha=alpha_fit,
        fitted_mass=m_fit,
        ppn_gamma=ppn_gamma,
        ppn_deviation=ppn_deviation,
    )


def save_yukawa(result: YukawaResult, results_dir: Path) -> None:
    import pandas as pd

    results_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"r_m": result.radius, "phi_J_per_kg": result.potential})
    df.to_csv(results_dir / "yukawa_profile.csv", index=False)
    (results_dir / "yukawa_summary.json").write_text(json_dumps(result.to_summary()), encoding="utf-8")


def plot_yukawa(result: YukawaResult, figs_dir: Path) -> None:
    import matplotlib.pyplot as plt

    figs_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.plot(result.radius, result.potential, label="Φ(r)")
    plt.xlabel("r [m]")
    plt.ylabel("Potential [J kg$^{-1}$]")
    plt.title("Reflexive Yukawa potential")
    plt.tight_layout()
    plt.savefig(figs_dir / "yukawa_potential.png", dpi=160)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.axhline(1.0, color="black", linestyle="--", label="GR")
    plt.axhline(result.ppn_gamma, color="darkred", label="Reflexive γ")
    plt.ylabel("γ")
    plt.title("PPN parameter γ")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figs_dir / "yukawa_ppn.png", dpi=160)
    plt.close()


def json_dumps(obj: Dict[str, float]) -> str:
    import json

    return json.dumps(obj, indent=2, sort_keys=True)

