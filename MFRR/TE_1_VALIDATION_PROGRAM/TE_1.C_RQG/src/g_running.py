"""
Renormalization-group running of the reflexive Newton constant.

Implements Phase 1 portions of TE_1.C.1_PLAN.md (Tasks T1/T3).
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
class GRGConfig:
    k_min: float  # minimum renormalization scale (1/m)
    k_max: float  # maximum renormalization scale (1/m)
    num_points: int
    k0: float  # reference scale (1/m)
    alpha_coupling: float  # dimensionless reflexive beta-function prefactor
    omega_sensitivity: float  # coupling to Moonshot Λ slope
    lambda_slope: float  # slope from Moonshot 1 (in m^-2)


@dataclass
class GRGResult:
    config: GRGConfig
    k: np.ndarray
    Gk: np.ndarray
    beta_coeff: float
    slope_loglog: float

    @property
    def delta_rel(self) -> float:
        G0 = CONSTS.gravitational_constant
        return float((self.Gk.max() - self.Gk.min()) / G0)

    def to_summary(self) -> Dict[str, float]:
        base = asdict(self.config)
        base.update(
            {
                "delta_rel": self.delta_rel,
                "G_min": float(self.Gk.min()),
                "G_max": float(self.Gk.max()),
                "beta_coeff": self.beta_coeff,
                "slope_loglog": self.slope_loglog,
            }
        )
        return base


def compute_running(cfg: GRGConfig) -> GRGResult:
    k = np.linspace(cfg.k_min, cfg.k_max, cfg.num_points)
    if np.any(k <= 0.0):
        raise ValueError("Renormalization scale k must be positive.")
    G0 = CONSTS.gravitational_constant

    # Effective beta function combines reflexive coupling and Λ slope insights.
    beta_coeff = cfg.alpha_coupling + cfg.omega_sensitivity * cfg.lambda_slope

    ln_ratio = np.log(k / cfg.k0)
    denominator = 1.0 + beta_coeff * G0 * ln_ratio
    # Guard against Landau poles; clip extremely small denominators.
    denominator = np.where(np.abs(denominator) < 1.0e-8, np.sign(denominator) * 1.0e-8, denominator)
    Gk = G0 / denominator
    slope = float(_fit_log_slope(k, Gk))
    return GRGResult(config=cfg, k=k, Gk=Gk, beta_coeff=beta_coeff, slope_loglog=slope)


def save_running(result: GRGResult, results_dir: Path) -> None:
    import pandas as pd

    results_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"k": result.k, "Gk": result.Gk})
    df.to_csv(results_dir / "g_running.csv", index=False)

    summary = result.to_summary()
    (results_dir / "g_running_summary.json").write_text(json_dumps(summary), encoding="utf-8")


def plot_running(result: GRGResult, figs_dir: Path) -> None:
    import matplotlib.pyplot as plt

    figs_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.plot(result.k, result.Gk / CONSTS.gravitational_constant, color="darkblue")
    plt.xlabel("k [1/m]")
    plt.ylabel("G(k)/G0")
    plt.title("Reflexive running of G(k)")
    plt.annotate(
        f"slope={result.slope_loglog:.2e}",
        xy=(0.05, 0.05),
        xycoords="axes fraction",
        fontsize=9,
    )
    plt.tight_layout()
    plt.savefig(figs_dir / "g_running.png", dpi=160)
    plt.close()


def json_dumps(obj: Dict[str, float]) -> str:
    import json

    return json.dumps(obj, indent=2, sort_keys=True)


def _fit_log_slope(k: np.ndarray, Gk: np.ndarray) -> float:
    log_k = np.log(k)
    log_G = np.log(Gk)
    coeffs = np.polyfit(log_k, log_G, 1)
    slope = coeffs[0]
    return float(slope)

