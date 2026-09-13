"""
Stability diagnostics for the coupled (g_{μν}, Psi) system.

Implements TE_1.C Phase 1 Task T6 (TE_1.C.1_PLAN.md): random perturbations, DEC/SEC checks.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

import numpy as np

try:
    from .frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        integrate_background,
    )
    from .constants import CONSTS
except ImportError:  # pragma: no cover
    import sys

    PACKAGE_ROOT = Path(__file__).resolve().parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.append(str(PACKAGE_ROOT))
    from frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        integrate_background,
    )
    from constants import CONSTS


@dataclass
class StabilityConfig:
    model: FRWModelConfig
    perturbation_scale: float
    realizations: int
    seed: int = 1729


@dataclass
class StabilityRealization:
    delta_psi0: float
    delta_ppsi0: float
    dec_min: float
    sec_min: float
    rho_min: float
    rho_max: float


@dataclass
class StabilitySummary:
    config: StabilityConfig
    realizations: List[StabilityRealization]

    def to_summary(self) -> Dict[str, float]:
        dec_values = np.array([r.dec_min for r in self.realizations])
        sec_values = np.array([r.sec_min for r in self.realizations])
        rho_min = float(min(r.rho_min for r in self.realizations))
        rho_max = float(max(r.rho_max for r in self.realizations))
        return {
            **asdict(self.config),
            "dec_min": float(dec_values.min()),
            "dec_failure_rate": float((dec_values < 0).mean()),
            "sec_min": float(sec_values.min()),
            "sec_failure_rate": float((sec_values < 0).mean()),
            "rho_min": rho_min,
            "rho_max": rho_max,
        }


def run_stability(cfg: StabilityConfig) -> StabilitySummary:
    rng = np.random.default_rng(cfg.seed)
    realizations: List[StabilityRealization] = []
    for _ in range(cfg.realizations):
        delta_psi0 = rng.normal(scale=cfg.perturbation_scale)
        delta_ppsi0 = rng.normal(scale=cfg.perturbation_scale)
        ic = FRWInitialConditions(
            psi0=1.0e-3 + delta_psi0,
            ppsi0=delta_ppsi0,
        )
        result = integrate_background(cfg.model, ic, rtol=1.0e-7, atol=1.0e-9)

        rho_m, rho_psi, p_psi = _energy_components(result, cfg.model)
        rho_tot = rho_m + rho_psi
        pressure_tot = p_psi

        dec = rho_tot - np.abs(pressure_tot)
        sec = rho_tot + 3.0 * pressure_tot

        realization = StabilityRealization(
            delta_psi0=float(delta_psi0),
            delta_ppsi0=float(delta_ppsi0),
            dec_min=float(dec.min()),
            sec_min=float(sec.min()),
            rho_min=float(rho_tot.min()),
            rho_max=float(rho_tot.max()),
        )
        realizations.append(realization)

    return StabilitySummary(config=cfg, realizations=realizations)


def _energy_components(result, model: FRWModelConfig):
    rho_m = CONSTS.rho_crit0 * model.omega_m0 * result.scale_factor**-3
    potential = _potential(result.psi, model)
    rho_psi = 0.5 * result.ppsi**2 + potential
    p_psi = 0.5 * result.ppsi**2 - potential
    return rho_m, rho_psi, p_psi


def _potential(psi: np.ndarray, model: FRWModelConfig) -> np.ndarray:
    rho_crit0 = CONSTS.rho_crit0
    lambda_eff = model.rf_bar * rho_crit0
    u0 = 0.5 * (model.m**2) * psi**2 * (1.0e-5 * rho_crit0)
    u1 = model.beta * model.omega_bar * psi * (1.0e-6 * rho_crit0)
    return lambda_eff + u0 + u1


def save_stability(summary: StabilitySummary, logs_dir: Path) -> None:
    import json

    logs_dir.mkdir(parents=True, exist_ok=True)
    realizations = [r.__dict__ for r in summary.realizations]
    (logs_dir / "stability_realizations.json").write_text(
        json.dumps(realizations, indent=2), encoding="utf-8"
    )
    (logs_dir / "stability_summary.json").write_text(
        json.dumps(summary.to_summary(), indent=2),
        encoding="utf-8",
    )

