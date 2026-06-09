"""
Reflexive ringdown and polarization mixing diagnostics.

Implements Tasks T1/T4 in TE_1.C.1_PLAN.md (Phase 1).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict

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
class RingdownConfig:
    mass_solar: float
    spin: float
    psi_gradient: float
    beta_mix: float
    ell: int = 2
    mode_index: int = 0  # fundamental


@dataclass
class RingdownResult:
    config: RingdownConfig
    omega_real: float
    omega_imag: float
    damping_time: float
    quality_factor: float
    polarization_mix: float

    def to_summary(self) -> Dict[str, float]:
        base = asdict(self.config)
        base.update(
            {
                "omega_real": self.omega_real,
                "omega_imag": self.omega_imag,
                "damping_time": self.damping_time,
                "quality_factor": self.quality_factor,
                "polarization_mix": self.polarization_mix,
            }
        )
        return base


def _mass_in_seconds(mass_solar: float) -> float:
    M_sun = 1.98847e30  # kg
    G = CONSTS.gravitational_constant
    c = CONSTS.speed_of_light
    return G * M_sun * mass_solar / c**3


def _baseline_qnm(config: RingdownConfig) -> Dict[str, float]:
    """
    Empirical fit for Kerr QNM frequencies (Berti+ 2006).
    """
    M = _mass_in_seconds(config.mass_solar)
    a = np.clip(config.spin, 0.0, 0.99)
    # Fit coefficients for l=2, n=0
    f1, f2, f3 = 1.5251, -1.1568, 0.1292
    q1, q2, q3 = 0.7000, 1.4187, -0.4990

    omega_R = (f1 + f2 * (1.0 - a) ** f3) / (2.0 * np.pi * M)
    omega_I = (q1 + q2 * (1.0 - a) ** q3) / (2.0 * M)
    return {"omega_R": omega_R, "omega_I": omega_I}


def compute_ringdown(config: RingdownConfig) -> RingdownResult:
    base = _baseline_qnm(config)
    omega_R = base["omega_R"]
    omega_I = base["omega_I"]

    # Reflexive correction: adjudicative Psi gradient induces effective shear.
    delta = config.beta_mix * config.psi_gradient
    omega_R_corr = omega_R * (1.0 + delta)
    omega_I_corr = omega_I * (1.0 + 0.5 * delta)

    damping_time = 1.0 / np.abs(omega_I_corr)
    quality = omega_R_corr / (2.0 * np.abs(omega_I_corr))

    # Polarization mixing: proportional to gradient and spin coupling.
    polarization_mix = float(np.tanh(np.abs(config.psi_gradient) * (1.0 + config.spin)))

    return RingdownResult(
        config=config,
        omega_real=float(omega_R_corr),
        omega_imag=float(-np.abs(omega_I_corr)),
        damping_time=float(damping_time),
        quality_factor=float(quality),
        polarization_mix=polarization_mix,
    )


def save_ringdown(result: RingdownResult, results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "ringdown_summary.json").write_text(json_dumps(result.to_summary()), encoding="utf-8")


def plot_ringdown(result: RingdownResult, figs_dir: Path) -> None:
    import matplotlib.pyplot as plt

    figs_dir.mkdir(parents=True, exist_ok=True)
    freqs = np.array([result.omega_real, -result.omega_imag])
    labels = ["Re(ω)", "Im(ω)"]
    plt.figure(figsize=(5, 4))
    plt.bar(labels, freqs, color=["steelblue", "indianred"])
    plt.ylabel("Angular frequency [rad s$^{-1}$]")
    plt.title("Reflexive QNM frequencies")
    plt.tight_layout()
    plt.savefig(figs_dir / "ringdown_frequencies.png", dpi=160)
    plt.close()

    plt.figure(figsize=(5, 4))
    metrics = [result.damping_time, result.quality_factor, result.polarization_mix]
    labels = ["τ", "Q", "Mix"]
    plt.bar(labels, metrics, color=["darkgreen", "slategray", "purple"])
    plt.ylabel("Value")
    plt.title("Ringdown diagnostics")
    plt.tight_layout()
    plt.savefig(figs_dir / "ringdown_diagnostics.png", dpi=160)
    plt.close()


def json_dumps(obj: Dict[str, float]) -> str:
    import json

    return json.dumps(obj, indent=2, sort_keys=True)

