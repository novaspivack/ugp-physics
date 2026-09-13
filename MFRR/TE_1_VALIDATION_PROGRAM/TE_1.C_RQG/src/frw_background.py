"""
FRW + Psi background integration for TE_1.C.

Implements the Phase 1 T2 task in TE_1.C.1_PLAN.md: integrate the
reflexive FRW background, compute CPL (w0, wa), and log diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple, Optional

import numpy as np
from numpy.linalg import lstsq
from scipy.integrate import solve_ivp

try:
    from .constants import CONSTS
except ImportError:  # pragma: no cover
    import sys

    PACKAGE_ROOT = Path(__file__).resolve().parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.append(str(PACKAGE_ROOT))
    from constants import CONSTS


@dataclass
class FRWModelConfig:
    m: float
    beta: float
    omega_bar: float
    rf_bar: float
    hubble_constant: float = CONSTS.hubble_constant
    omega_m0: float = 0.3
    zmax: float = 2.0
    nsteps: int = 1800
    mass_scale: float = 1.0e-5
    linear_scale: float = 1.0e-6
    flat_amplitude: float = 0.0
    flat_width: float = 0.3
    flat_center: float = 0.0
    quartic_coeff: float = 0.0
    use_analytic_potential: bool = False
    analytic_v0: float = 0.0
    analytic_eps0: float = 0.01
    analytic_beta: float = 0.5
    analytic_psiref: float = 0.0
    analytic_transition_amp: float = 0.0
    analytic_transition_width: float = 1.0
    analytic_transition_center: float = 0.0
    analytic_ramp_amp: float = 0.0
    analytic_ramp_slope: float = 0.0
    analytic_ramp_center: float = 0.0
    analytic_plateau_amp: float = 0.0
    analytic_plateau_width: float = 1.0
    analytic_plateau_center: float = 0.0
    analytic_curvature_amp: float = 0.0
    analytic_curvature_width: float = 1.0
    analytic_curvature_center: float = 0.0


@dataclass
class FRWInitialConditions:
    psi0: float = 1.0e-3
    ppsi0: float = 0.0


@dataclass
class FRWDiagnostics:
    w0_psi: float
    wa_psi: float
    w0_eff: float
    wa_eff: float
    w_min: float
    w_max: float


@dataclass
class FRWRunResult:
    config: FRWModelConfig
    diagnostics: FRWDiagnostics
    z: np.ndarray
    scale_factor: np.ndarray
    ln_a: np.ndarray
    w_eff: np.ndarray
    w_psi: np.ndarray
    hubble: np.ndarray
    psi: np.ndarray
    ppsi: np.ndarray
    epsilon: np.ndarray
    eta_sr: np.ndarray
    d_epsilon_dN: np.ndarray
    epsilon_potential: np.ndarray
    eta_potential: np.ndarray

    def to_row(self) -> Dict[str, float]:
        row = asdict(self.config)
        row.update(
            {
                "w0_psi": self.diagnostics.w0_psi,
                "wa_psi": self.diagnostics.wa_psi,
                "w0_eff": self.diagnostics.w0_eff,
                "wa_eff": self.diagnostics.wa_eff,
                "w_min": self.diagnostics.w_min,
                "w_max": self.diagnostics.w_max,
            }
        )
        return row


def _analytic_potential(psi: float, cfg: FRWModelConfig) -> Tuple[float, float, float]:
    """Slow-roll potential with optional plateau, ramp, and transition modulation."""
    rho_crit0 = CONSTS.rho_crit0
    eps0 = max(cfg.analytic_eps0, 1.0e-8)
    beta = max(cfg.analytic_beta, 1.0e-6)
    psi_ref = cfg.analytic_psiref
    shift = psi - psi_ref
    max_clip = 50.0
    exp_arg = np.clip(-0.5 * beta * shift, -max_clip, max_clip)
    exp_term = np.exp(exp_arg)
    A = 2.0 * np.sqrt(2.0 * eps0) / beta
    exponent = np.clip(A * exp_term, -max_clip, max_clip)
    V = cfg.analytic_v0 * rho_crit0 * np.exp(exponent)
    B = np.clip(-0.5 * A * beta * exp_term, -np.exp(max_clip), np.exp(max_clip))
    dV_dpsi = V * B
    dB_dpsi = np.clip(0.25 * A * beta * beta * exp_term, -np.exp(max_clip), np.exp(max_clip))

    transition_amp = cfg.analytic_transition_amp
    F = 1.0
    dF_dpsi = 0.0
    d2F_dpsi2 = 0.0
    if transition_amp != 0.0:
        width = max(cfg.analytic_transition_width, 1.0e-3)
        center = cfg.analytic_transition_center
        x = (psi - center) / width
        cosh_x = np.cosh(np.clip(x, -max_clip, max_clip))
        sech2_x = 1.0 / (cosh_x * cosh_x)
        tanh_x = np.tanh(np.clip(x, -max_clip, max_clip))
        F += transition_amp * tanh_x
        dF_dpsi += transition_amp * sech2_x / width
        d2F_dpsi2 += transition_amp * (-2.0 * tanh_x * sech2_x) / (width * width)

    plateau_amp = cfg.analytic_plateau_amp
    if plateau_amp != 0.0:
        width = max(cfg.analytic_plateau_width, 1.0e-3)
        center = cfg.analytic_plateau_center
        x = (psi - center) / width
        exp_term = np.exp(-np.clip(x * x, -max_clip, max_clip))
        F += plateau_amp * exp_term
        dF_dpsi += plateau_amp * exp_term * (-2.0 * x / width)
        d2F_dpsi2 += plateau_amp * exp_term * ((4.0 * x * x / (width * width)) - 2.0 / width)

    ramp_amp = cfg.analytic_ramp_amp
    if ramp_amp != 0.0:
        slope = cfg.analytic_ramp_slope
        center = cfg.analytic_ramp_center
        ramp = ramp_amp * (psi - center)
        F += ramp
        dF_dpsi += ramp_amp
        d2F_dpsi2 += 0.0

    curvature_amp = cfg.analytic_curvature_amp
    if curvature_amp != 0.0:
        width = max(cfg.analytic_curvature_width, 1.0e-3)
        center = cfg.analytic_curvature_center
        x = (psi - center) / width
        exp_term = np.exp(-np.clip(x * x, -max_clip, max_clip))
        core = (x * x - 0.5) * exp_term
        core_dpsi = (2.0 / width) * x * (1.5 - x * x) * exp_term
        core_d2psi2 = (1.0 / (width * width)) * (3.0 - 12.0 * x * x + 4.0 * x * x * x * x) * exp_term
        F += curvature_amp * core
        dF_dpsi += curvature_amp * core_dpsi
        d2F_dpsi2 += curvature_amp * core_d2psi2

    V_base = V
    dV_base = dV_dpsi
    d2V_base = V * (B * B + dB_dpsi)

    V = V_base * F
    dV_dpsi = dV_base * F + V_base * dF_dpsi
    d2V_dpsi2 = d2V_base * F + 2.0 * dV_base * dF_dpsi + V_base * d2F_dpsi2
    return V, dV_dpsi, d2V_dpsi2


def _rho_components(
    a: float, psi: float, ppsi: float, cfg: FRWModelConfig
) -> Tuple[float, float, float]:
    rho_crit0 = CONSTS.rho_crit0
    rho_m = rho_crit0 * cfg.omega_m0 * a**-3
    lambda_eff = cfg.rf_bar * rho_crit0
    rho_scale = cfg.mass_scale * rho_crit0

    if cfg.use_analytic_potential:
        v_eff, _, _ = _analytic_potential(psi, cfg)
    else:
        u0 = 0.5 * (cfg.m**2) * psi * psi * rho_scale
        u1 = cfg.beta * cfg.omega_bar * psi * (cfg.linear_scale * rho_crit0)
        v_quartic = cfg.quartic_coeff * psi**4 * rho_scale
        if cfg.flat_amplitude != 0.0:
            width = max(cfg.flat_width, 1.0e-3)
            delta = np.clip((psi - cfg.flat_center) / width, -20.0, 20.0)
            v_flat = cfg.flat_amplitude * rho_crit0 * np.exp(-delta**4)
        else:
            v_flat = 0.0
        v_eff = u0 + u1 + v_quartic + v_flat
    v_eff += lambda_eff

    rho_psi = 0.5 * ppsi * ppsi + v_eff
    p_psi = 0.5 * ppsi * ppsi - v_eff
    return rho_m, rho_psi, p_psi


def _hubble(a: float, psi: float, ppsi: float, cfg: FRWModelConfig) -> float:
    rho_m, rho_psi, _ = _rho_components(a, psi, ppsi, cfg)
    rho_total = rho_m + rho_psi
    if rho_total <= 0:
        return 1.0e-32
    prefactor = (8.0 * np.pi * CONSTS.gravitational_constant) / 3.0
    return float(np.sqrt(prefactor * rho_total))


def _rhs(
    x: float, state: np.ndarray, cfg: FRWModelConfig
) -> np.ndarray:
    a = np.exp(np.clip(x, -700.0, 700.0))
    psi, ppsi = state
    H = _hubble(a, psi, ppsi, cfg)
    dpsi_dx = ppsi / H
    dppsi_dx = (-3.0 * H * ppsi - _dV_dpsi(psi, cfg)) / H
    return np.array([dpsi_dx, dppsi_dx])


def _dV_dpsi(psi: float, cfg: FRWModelConfig) -> float:
    if cfg.use_analytic_potential:
        _, grad, _ = _analytic_potential(psi, cfg)
        return grad

    rho_crit0 = CONSTS.rho_crit0
    rho_scale = cfg.mass_scale * rho_crit0

    grad = (cfg.m**2) * psi * rho_scale + cfg.beta * cfg.omega_bar * (
        cfg.linear_scale * rho_crit0
    )

    if cfg.quartic_coeff != 0.0:
        grad += 4.0 * cfg.quartic_coeff * psi**3 * rho_scale

    if cfg.flat_amplitude != 0.0:
        width = max(cfg.flat_width, 1.0e-3)
        delta = np.clip((psi - cfg.flat_center) / width, -20.0, 20.0)
        exp_term = np.exp(-delta**4)
        grad += (
            cfg.flat_amplitude
            * rho_crit0
            * exp_term
            * (-4.0 * delta**3)
            / width
        )

    return grad


def integrate_background(
    cfg: FRWModelConfig,
    ic: FRWInitialConditions,
    rtol: float = 1.0e-7,
    atol: float = 1.0e-9,
    min_ln_a: Optional[float] = None,
) -> FRWRunResult:
    x0 = 0.0
    if min_ln_a is not None:
        xmin = float(min_ln_a)
    else:
        xmin = -np.log(max(1.0e-6, 1.0 + cfg.zmax))
    xs = np.linspace(x0, xmin, cfg.nsteps)

    sol = solve_ivp(
        lambda x, y: _rhs(x, y, cfg),
        (x0, xmin),
        np.array([ic.psi0, ic.ppsi0]),
        t_eval=xs,
        method="RK45",
        rtol=rtol,
        atol=atol,
    )
    if not sol.success:
        raise RuntimeError(f"FRW integration failed: {sol.message}")

    x = sol.t
    a = np.exp(np.clip(x, -700.0, 700.0))
    z = 1.0 / a - 1.0
    psi = sol.y[0]
    ppsi = sol.y[1]

    H = np.array([_hubble(ai, ps, pp, cfg) for ai, ps, pp in zip(a, psi, ppsi)])
    rho_m, rho_psi, p_psi = zip(
        *[_rho_components(ai, ps, pp, cfg) for ai, ps, pp in zip(a, psi, ppsi)]
    )
    rho_m = np.array(rho_m)
    rho_psi = np.array(rho_psi)
    p_psi = np.array(p_psi)
    w_psi = p_psi / rho_psi
    rho_tot = rho_m + rho_psi
    w_eff = p_psi / rho_tot

    # slow-roll parameter epsilon = - d ln H / d ln a
    with np.errstate(divide="ignore", invalid="ignore"):
        lnH = np.log(H)
    dlogH_dx = np.gradient(lnH, x, edge_order=2)
    epsilon = -dlogH_dx
    epsilon = np.where(epsilon < 0, 0.0, epsilon)
    epsilon_floor = np.clip(epsilon, 1.0e-18, None)
    eta_sr = np.gradient(np.log(epsilon_floor), x, edge_order=2)
    d_epsilon_dN = np.gradient(epsilon, x, edge_order=2)

    if cfg.use_analytic_potential:
        eps_potential = []
        eta_potential = []
        for ps in psi:
            V, dV_dpsi, d2V_dpsi2 = _analytic_potential(ps, cfg)
            if V <= 0:
                eps_potential.append(np.nan)
                eta_potential.append(np.nan)
                continue
            B = dV_dpsi / V
            eps_potential.append(0.5 * B * B)
            eta_potential.append(d2V_dpsi2 / V)
        eps_potential_arr = np.array(eps_potential)
        eta_potential_arr = np.array(eta_potential)
    else:
        eps_potential_arr = np.full_like(x, np.nan)
        eta_potential_arr = np.full_like(x, np.nan)

    diagnostics = _compute_diagnostics(z, w_psi, w_eff)
    return FRWRunResult(
        config=cfg,
        diagnostics=diagnostics,
        z=z,
        scale_factor=a,
        ln_a=x,
        w_eff=w_eff,
        w_psi=w_psi,
        hubble=H,
        psi=psi,
        ppsi=ppsi,
        epsilon=epsilon,
        eta_sr=eta_sr,
        d_epsilon_dN=d_epsilon_dN,
        epsilon_potential=eps_potential_arr,
        eta_potential=eta_potential_arr,
    )


def _compute_diagnostics(
    z: np.ndarray, w_psi: np.ndarray, w_eff: np.ndarray, zmax_fit: float = 1.5
) -> FRWDiagnostics:
    w0_psi, wa_psi = _fit_cpl(z, w_psi, zmax_fit=zmax_fit)
    w0_eff, wa_eff = _fit_cpl(z, w_eff, zmax_fit=zmax_fit)
    finite_mask = np.isfinite(w_eff)
    w_min = float(np.min(w_eff[finite_mask])) if finite_mask.any() else np.nan
    w_max = float(np.max(w_eff[finite_mask])) if finite_mask.any() else np.nan
    return FRWDiagnostics(
        w0_psi=w0_psi,
        wa_psi=wa_psi,
        w0_eff=w0_eff,
        wa_eff=wa_eff,
        w_min=w_min,
        w_max=w_max,
    )


def _fit_cpl(
    z: np.ndarray, w: np.ndarray, zmax_fit: float
) -> Tuple[float, float]:
    mask = (z >= 0.0) & (z <= zmax_fit) & np.isfinite(w)
    if mask.sum() < 6:
        return float("nan"), float("nan")
    Z = z[mask]
    X = np.column_stack([np.ones_like(Z), Z / (1.0 + Z)])
    coeffs, *_ = lstsq(X, w[mask], rcond=None)
    w0, wa = coeffs.tolist()
    return float(w0), float(wa)


def run_frw_grid(
    configs: Iterable[FRWModelConfig],
    ic: FRWInitialConditions,
    progress_callback: Callable[[int, int, FRWModelConfig], None] | None = None,
) -> List[FRWRunResult]:
    configs_list = list(configs)
    total = len(configs_list)
    results: List[FRWRunResult] = []
    for idx, cfg in enumerate(configs_list, start=1):
        if progress_callback is not None:
            progress_callback(idx, total, cfg)
        result = integrate_background(cfg, ic)
        if not isfinite(result.diagnostics.w0_psi):
            raise ValueError(f"CPL fit failed for config={cfg}")
        results.append(result)
    return results


def save_frw_results(
    results: List[FRWRunResult],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [res.to_row() for res in results]
    import pandas as pd  # local import to avoid hard dependency elsewhere

    df = pd.DataFrame(rows)
    df.sort_values(
        ["m", "beta", "omega_bar", "rf_bar"],
        inplace=True,
        ignore_index=True,
    )
    df.to_csv(output_dir / "frw_eos.csv", index=False)

    # compute aggregate statistics
    summary = {
        "w0_psi_mean": float(df["w0_psi"].mean()),
        "w0_psi_std": float(df["w0_psi"].std()),
        "wa_psi_max_abs": float(df["wa_psi"].abs().max()),
        "w0_eff_mean": float(df["w0_eff"].mean()),
        "wa_eff_max_abs": float(df["wa_eff"].abs().max()),
        "cases": int(len(df)),
    }
    (output_dir / "frw_eos_summary.json").write_text(
        json_dumps(summary), encoding="utf-8"
    )


def generate_frw_figures(
    results: List[FRWRunResult],
    figs_dir: Path,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    figs_dir.mkdir(parents=True, exist_ok=True)
    case_dir = figs_dir / "frw"
    case_dir.mkdir(exist_ok=True)

    w0_samples: List[float] = []
    wa_samples: List[float] = []

    for res in results:
        tag = (
            f"m{res.config.m:.2e}_b{res.config.beta:.2f}"
            f"_ob{res.config.omega_bar:.2f}_rf{res.config.rf_bar:.2f}"
        )
        z = res.z

        plt.figure(figsize=(6, 4))
        plt.plot(z, res.w_eff, label="w_eff")
        plt.plot(z, res.w_psi, label="w_psi", linestyle="--")
        plt.gca().invert_xaxis()
        plt.xlabel("z")
        plt.ylabel("w(z)")
        plt.title(f"Equation of state — {tag}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(case_dir / f"w_{tag}.png", dpi=160)
        plt.close()

        plt.figure(figsize=(6, 4))
        plt.plot(z, res.hubble / CONSTS.hubble_constant)
        plt.gca().invert_xaxis()
        plt.xlabel("z")
        plt.ylabel("H(z)/H0")
        plt.title(f"Hubble ratio — {tag}")
        plt.tight_layout()
        plt.savefig(case_dir / f"H_{tag}.png", dpi=160)
        plt.close()

        plt.figure(figsize=(6, 4))
        plt.plot(z, res.psi)
        plt.gca().invert_xaxis()
        plt.xlabel("z")
        plt.ylabel("Psi(z)")
        plt.title(f"Psi profile — {tag}")
        plt.tight_layout()
        plt.savefig(case_dir / f"psi_{tag}.png", dpi=160)
        plt.close()

        w0_samples.append(res.diagnostics.w0_psi)
        wa_samples.append(res.diagnostics.wa_psi)

    if w0_samples:
        w0_arr = np.array(w0_samples)
        wa_arr = np.array(wa_samples)
        plt.figure(figsize=(6, 4))
        plt.scatter(wa_arr, w0_arr, color="steelblue", edgecolor="black", alpha=0.8)
        plt.axvline(0.0, color="gray", linestyle="--", linewidth=1.0)
        plt.axhline(-1.0, color="gray", linestyle="--", linewidth=1.0)
        plt.xlabel("w_a")
        plt.ylabel("w_0")
        plt.title("CPL parameters across FRW grid")
        plt.tight_layout()
        plt.savefig(figs_dir / "w0_vs_wa.png", dpi=160)
        plt.close()


def json_dumps(obj: Dict[str, float]) -> str:
    import json

    return json.dumps(obj, indent=2, sort_keys=True)

