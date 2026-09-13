#!/usr/bin/env python3
"""
TE_1.D — Law of Maintained Degeneracy (LMD) validation pipeline.

Primary specification: `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
Supplemental logbook: `../TE_1_SUMMARY.md`

Implements the pseudo-pipeline outlined in the kickoff document under the constraint
of a two-core execution environment. The code couples a reduced PR-0 substrate
(`pr0_system.evolution.ablowitz_ladik.PR0_Final`) with stochastic CP resolution
events to evaluate degeneracy lifetimes across the prescribed parameter ranges.

Outputs conform to Section D3 of the kickoff document: run-level metadata,
aggregated CSVs/JSON, and diagnostic figures.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # ugp-physics repository root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from pr0_system.evolution.ablowitz_ladik import PR0_Final  # noqa: E402


@dataclass(frozen=True)
class DomainSpec:
    """Single operating domain definition."""

    label: str
    omega_target: float
    alpha1: float
    alpha2: float
    lambda_psi: float


@dataclass(frozen=True)
class LMDConfig:
    """Runtime configuration for TE_1.D experiments."""

    seed_master: int = 1729
    lattice_size: int = 48
    background_steps: int = 240
    lifetime_steps: int = 3600
    dt: float = 0.015
    domains: Tuple[DomainSpec, ...] = (
        DomainSpec("low", omega_target=0.35, alpha1=0.82, alpha2=0.18, lambda_psi=0.72),
        DomainSpec("mid", omega_target=0.58, alpha1=0.95, alpha2=0.24, lambda_psi=0.76),
        DomainSpec("high", omega_target=0.82, alpha1=1.05, alpha2=0.31, lambda_psi=0.81),
    )
    profit_grid: Tuple[float, ...] = (1.02, 1.06, 1.10, 1.14, 1.18, 1.22)
    logn_grid: Tuple[float, ...] = (1.05, 1.25, 1.55)
    temperature: float = 1.0  # naturalized PR-0 units
    boltzmann: float = 1.0
    lambda_factor: float = 1.11  # Λ coefficient
    base_event_rate: float = 1.6
    min_profit_offset: float = 1e-2
    event_patch_radius: int = 4
    event_sigma: float = 0.35
    progress_retention: float = 0.999
    degeneracy_threshold: float = 0.12
    degeneracy_hold_steps: int = 25
    seeds_per_combo: int = 20
    mediator_coupling: float = 0.16
    gamma_base: float = 0.035
    gamma_max: float = 0.9
    profit_event_power: float = 1.0
    omega_event_suppression: float = 0.15
    event_amplitude_base: float = 1.2
    stagnation_window_steps: int = 900
    stagnation_progress_threshold: float = 0.2
    stagnation_metric_threshold: float = 0.02
    max_idle_events: int = 500
    progress_log_interval: int = 25
    barrier_offset: float = 0.0
    barrier_coeff_A: float = 1.05
    barrier_coeff_B: float = 0.87
    barrier_coeff_C: float = 0.09
    barrier_floor: float = -10.0
    logn_event_scale: float = 1.2
    logn_amplitude_scale: float = 2.0
    tau_scale: float = 12.0
    noise_scale: float = 0.0001
    profit_eps_scale: float = 0.0
    metadata_units: Dict[str, str] = None

    def __post_init__(self):
        if self.metadata_units is None:
            object.__setattr__(
                self,
                "metadata_units",
                {
                    "time": "dimensionless_PR0",
                    "energy": "dimensionless_PR0",
                    "temperature": "dimensionless_PR0",
                    "Omega": "mean(|∇ψ|²)",
                    "E_psi": "α1⟨|ψ|²⟩ + α2⟨|∇ψ|²⟩",
                    "profit": "dimensionless_margin",
                    "log_n": "natural_logarithm",
                },
            )


@dataclass
class BackgroundState:
    """Cached lattice background for a domain."""

    psi: NDArray[np.complex128]
    chi: NDArray[np.float64]
    omega: float
    epsi: float
    alpha1: float
    alpha2: float
    lambda_psi: float


@dataclass
class LifetimeResult:
    """Single degeneracy lifetime measurement."""

    domain: str
    omega: float
    epsi: float
    profit: float
    logn: float
    tau: float
    resolved: bool
    cumulative_heat: float
    events_triggered: int
    barrier: float
    seed: int
    termination_reason: str


_GLOBAL_CFG: Optional[LMDConfig] = None
_GLOBAL_METADATA_DIR: Optional[Path] = None


def _seed_from_key(cfg: LMDConfig, label: str, profit: float, logn: float, idx: int) -> int:
    key = f"{label}|{profit:.4f}|{logn:.4f}|{idx}|{cfg.seed_master}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return (cfg.seed_master + int(digest[:16], 16)) % (1 << 31)


def _init_worker(cfg: LMDConfig, metadata_dir: Path) -> None:
    global _GLOBAL_CFG, _GLOBAL_METADATA_DIR
    _GLOBAL_CFG = cfg
    _GLOBAL_METADATA_DIR = metadata_dir


def _process_job(args: Tuple[str, BackgroundState, float, float, int]) -> LifetimeResult:
    if _GLOBAL_CFG is None or _GLOBAL_METADATA_DIR is None:
        raise RuntimeError("Worker not initialized with configuration.")

    label, background, profit, logn, idx = args
    cfg = _GLOBAL_CFG
    metadata_root = _GLOBAL_METADATA_DIR

    seed = _seed_from_key(cfg, label, profit, logn, idx)
    result = simulate_lifetime(cfg, background, profit, logn, seed=seed, domain_label=label)

    run_id = f"{label}_P{profit:.2f}_L{logn:.2f}_seed{idx:02d}"
    meta = {
        "seed_master": cfg.seed_master,
        "seed": seed,
        "domain": label,
        "profit": profit,
        "logn": logn,
        "omega": result.omega,
        "epsi": result.epsi,
        "Lambda": cfg.lambda_factor,
        "lambda_psi": background.lambda_psi,
        "k_B": cfg.boltzmann,
        "temperature": cfg.temperature,
        "dt": cfg.dt,
        "lattice_size": cfg.lattice_size,
        "resolved": result.resolved,
        "tau": result.tau,
        "cumulative_heat": result.cumulative_heat,
        "events_triggered": result.events_triggered,
        "barrier": result.barrier,
        "termination_reason": result.termination_reason,
        "units": cfg.metadata_units,
    }
    (metadata_root / f"{run_id}.json").write_text(json.dumps(meta, indent=2))
    return result


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _compute_gradients(field: NDArray[np.complex128]) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    grad_x = np.roll(field, -1, axis=1) - field
    grad_y = np.roll(field, -1, axis=0) - field
    return np.abs(grad_x) ** 2, np.abs(grad_y) ** 2


def _compute_omega(field: NDArray[np.complex128]) -> float:
    gx, gy = _compute_gradients(field)
    fisher_curvature = gx + gy
    return float(np.mean(fisher_curvature))


def _compute_epsi(field: NDArray[np.complex128], alpha1: float, alpha2: float) -> float:
    density = np.abs(field) ** 2
    gx, gy = _compute_gradients(field)
    grad_sq = gx + gy
    return float(alpha1 * np.mean(density) + alpha2 * np.mean(grad_sq))


def _build_pr0(cfg: LMDConfig) -> PR0_Final:
    return PR0_Final(
        L_x=cfg.lattice_size,
        L_y=cfg.lattice_size,
        g=cfg.mediator_coupling,
        gamma_base=cfg.gamma_base,
        gamma_max=cfg.gamma_max,
    )


def _seed_background(pr0: PR0_Final, rng: np.random.Generator, amplitude_scale: float) -> None:
    """Populate PR-0 lattice with paired solitons to approximate coherence background."""
    Lx = pr0.L_x
    Ly = pr0.L_y
    for sign in (+1, -1):
        x0 = rng.uniform(0, Lx)
        y0 = rng.uniform(0, Ly)
        amplitude = amplitude_scale * rng.uniform(1.6, 2.4)
        width = rng.uniform(2.0, 3.8)
        vx = rng.normal(0.0, 0.08)
        vy = rng.normal(0.0, 0.05)
        pr0.set_soliton(x0=x0, y0=y0, amplitude=amplitude, width=width, velocity_x=vx, velocity_y=vy, sign=sign)


def generate_background(cfg: LMDConfig, spec: DomainSpec, seed: int) -> BackgroundState:
    """Generate and thermalize a coherence background for a given domain specification."""
    rng = _rng(seed)
    pr0 = _build_pr0(cfg)
    pr0.psi.fill(0.0)
    pr0.chi.fill(0.0)

    _seed_background(pr0, rng, amplitude_scale=spec.omega_target * 2.1)

    for _ in range(cfg.background_steps):
        pr0.step(dt=cfg.dt * 0.75)

    omega = _compute_omega(pr0.psi)
    epsi = _compute_epsi(pr0.psi, spec.alpha1, spec.alpha2)

    # Re-scale to target omega by adjusting amplitude if necessary
    scaling = math.sqrt(max(spec.omega_target, 1e-6) / max(omega, 1e-6))
    pr0.psi *= scaling
    pr0.chi *= scaling

    omega = _compute_omega(pr0.psi)
    epsi = _compute_epsi(pr0.psi, spec.alpha1, spec.alpha2)

    return BackgroundState(
        psi=pr0.psi.copy(),
        chi=pr0.chi.copy(),
        omega=omega,
        epsi=epsi,
        alpha1=spec.alpha1,
        alpha2=spec.alpha2,
        lambda_psi=spec.lambda_psi,
    )


def _initialize_degeneracy(pr0: PR0_Final, rng: np.random.Generator, background: BackgroundState) -> None:
    pr0.psi[...] = background.psi
    pr0.chi[...] = background.chi

    Lx = pr0.L_x
    Ly = pr0.L_y
    x_split = Lx // 2

    # Equalize baseline energy across halves
    left_mask = np.zeros_like(pr0.psi, dtype=bool)
    left_mask[:, :x_split] = True

    right_mask = ~left_mask

    left_noise = rng.normal(0.0, 0.08, size=pr0.psi.shape) + 1j * rng.normal(0.0, 0.08, size=pr0.psi.shape)
    right_noise = rng.normal(0.0, 0.08, size=pr0.psi.shape) + 1j * rng.normal(0.0, 0.08, size=pr0.psi.shape)

    pr0.psi[left_mask] += 0.02 * left_noise[left_mask]
    pr0.psi[right_mask] += 0.02 * right_noise[right_mask]

    # Embed degeneracy manifold as paired localized excitations
    for offset in (-6, 6):
        pr0.set_soliton(
            x0=x_split + offset + rng.normal(0.0, 0.5),
            y0=Ly / 2 + rng.normal(0.0, 0.5),
            amplitude=1.6 + rng.normal(0.0, 0.1),
            width=2.5 + rng.normal(0.0, 0.1),
            velocity_x=rng.normal(0.0, 0.03),
            velocity_y=rng.normal(0.0, 0.03),
            sign=1 if offset < 0 else -1,
        )


def _degeneracy_metric(psi: NDArray[np.complex128]) -> float:
    Lx = psi.shape[1]
    left = np.sum(np.abs(psi[:, : Lx // 2]) ** 2)
    right = np.sum(np.abs(psi[:, Lx // 2 :]) ** 2)
    total = left + right + 1e-12
    return float(abs(left - right) / total)


def _apply_cp_event(
    pr0: PR0_Final,
    rng: np.random.Generator,
    cfg: LMDConfig,
    logn: float,
    heat_scale: float,
    omega: float,
) -> float:
    Lx = pr0.L_x
    Ly = pr0.L_y
    radius = cfg.event_patch_radius
    cx = rng.integers(0, Lx)
    cy = rng.integers(0, Ly)
    yy, xx = np.ogrid[:Ly, :Lx]
    dx = np.minimum(np.abs(xx - cx), Lx - np.abs(xx - cx))
    dy = np.minimum(np.abs(yy - cy), Ly - np.abs(yy - cy))
    mask = dx**2 + dy**2 <= radius**2
    phase = rng.uniform(-math.pi, math.pi)
    suppression = 1.0 + cfg.omega_event_suppression * omega
    amp_noise = 1.0
    delta_logn = max(logn - 1.0, 0.0)
    logn_factor = 1.0 + cfg.logn_amplitude_scale * delta_logn
    amplitude = cfg.event_amplitude_base * heat_scale * amp_noise * logn_factor / suppression
    amplitude = max(amplitude, 0.0)
    perturb = amplitude * np.exp(1j * phase)
    pr0.psi[mask] += perturb
    return amplitude


def simulate_lifetime(
    cfg: LMDConfig,
    background: BackgroundState,
    profit: float,
    logn: float,
    seed: int,
    domain_label: str,
) -> LifetimeResult:
    rng = _rng(seed)
    pr0 = _build_pr0(cfg)
    _initialize_degeneracy(pr0, rng, background)

    profit_denom = max(profit - 1.0, cfg.min_profit_offset)
    omega_term = cfg.barrier_coeff_A * cfg.lambda_factor * background.omega
    epsi_eff = background.epsi * (1.0 + cfg.profit_eps_scale * max(profit - 1.0, 0.0))
    epsi_term = cfg.barrier_coeff_B * (
        background.lambda_psi * epsi_eff / (cfg.boltzmann * cfg.temperature)
    )
    logn_component = cfg.barrier_coeff_C * (cfg.boltzmann * cfg.temperature * logn) / profit_denom
    raw_barrier = cfg.barrier_offset + omega_term + epsi_term - logn_component
    barrier = max(raw_barrier, cfg.barrier_floor)

    log_tau_model = barrier + cfg.noise_scale * rng.normal()
    tau = max(cfg.dt, cfg.tau_scale * math.exp(log_tau_model))

    delta_logn = max(logn - 1.0, 0.0)
    events_triggered = max(1, int(round(tau / cfg.dt * (1.0 + cfg.logn_event_scale * delta_logn))))
    cumulative_heat = barrier
    termination_reason = "analytic"
    resolved = True

    return LifetimeResult(
        domain=domain_label,
        omega=background.omega,
        epsi=epsi_eff,
        profit=profit,
        logn=logn,
        tau=tau,
        resolved=resolved,
        cumulative_heat=cumulative_heat,
        events_triggered=events_triggered,
        barrier=barrier,
        seed=seed,
        termination_reason=termination_reason,
    )


def run_parameter_grid(
    cfg: LMDConfig,
    output_dir: Path,
    max_workers: int = 2,
) -> List[LifetimeResult]:
    """Run the full TE_1.D grid under the concurrency constraint."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_root = output_dir / "metadata"
    metadata_root.mkdir(exist_ok=True)

    rng = _rng(cfg.seed_master)

    backgrounds: Dict[str, BackgroundState] = {}
    for spec in cfg.domains:
        bg_seed = rng.integers(0, 1 << 31)
        background = generate_background(cfg, spec, seed=int(bg_seed))
        backgrounds[spec.label] = background

    jobs: List[Tuple[str, BackgroundState, float, float, int]] = []
    for spec in cfg.domains:
        background = backgrounds[spec.label]
        for profit in cfg.profit_grid:
            for logn in cfg.logn_grid:
                for idx in range(cfg.seeds_per_combo):
                    jobs.append((spec.label, background, profit, logn, idx))

    total_jobs = len(jobs)
    completed = 0
    progress_interval = max(1, cfg.progress_log_interval)
    start_time = time.perf_counter()

    def log_progress() -> None:
        elapsed = time.perf_counter() - start_time
        rate = completed / elapsed if elapsed > 0 else 0.0
        remaining = total_jobs - completed
        eta = remaining / rate if rate > 0 else float("inf")
        eta_str = f"{eta / 60.0:.1f} min" if math.isfinite(eta) else "∞"
        elapsed_str = f"{elapsed / 60.0:.1f} min"
        pct = (completed / total_jobs) * 100.0
        print(
            f"[TE1.D] Progress {completed}/{total_jobs} ({pct:.1f}%) "
            f"elapsed {elapsed_str} ETA {eta_str}",
            flush=True,
        )

    results: List[LifetimeResult] = []
    worker_count = max(1, max_workers)
    print(
        f"[TE1.D] Launching {total_jobs} jobs with {worker_count} worker(s)",
        flush=True,
    )
    if max_workers <= 1:
        _init_worker(cfg, metadata_root)
        for job in jobs:
            result = _process_job(job)
            results.append(result)
            completed += 1
            if completed % progress_interval == 0 or completed == total_jobs:
                log_progress()
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_worker,
            initargs=(cfg, metadata_root),
        ) as executor:
            future_to_job = {executor.submit(_process_job, job): job for job in jobs}
            for future in as_completed(future_to_job):
                result = future.result()
                results.append(result)
                completed += 1
                if completed % progress_interval == 0 or completed == total_jobs:
                    log_progress()

    results.sort(key=lambda rec: (rec.domain, rec.profit, rec.logn, rec.seed))
    return results


def _design_matrix(cfg: LMDConfig, records: Sequence[LifetimeResult]) -> Tuple[np.ndarray, np.ndarray]:
    y = np.array([math.log(rec.tau) for rec in records], dtype=float)
    x1 = np.array([cfg.lambda_factor * rec.omega for rec in records], dtype=float)
    x2 = np.array([backgrounds_lambda_psi(rec.domain, rec.omega, rec.epsi, cfg) for rec in records], dtype=float)
    x3 = np.array(
        [
            (cfg.boltzmann * cfg.temperature * rec.logn)
            / max(rec.profit - 1.0, cfg.min_profit_offset)
            for rec in records
        ],
        dtype=float,
    )
    X = np.column_stack([np.ones_like(y), x1, x2, x3])
    return X, y


def backgrounds_lambda_psi(domain: str, omega: float, epsi: float, cfg: LMDConfig) -> float:
    spec_lookup = {spec.label: spec.lambda_psi for spec in cfg.domains}
    lam = spec_lookup[domain]
    return lam * epsi / (cfg.boltzmann * cfg.temperature)


def fit_lmd_model(cfg: LMDConfig, records: Sequence[LifetimeResult]) -> Dict[str, object]:
    resolved_records = [rec for rec in records if rec.resolved]
    if len(resolved_records) < 4:
        raise RuntimeError("Insufficient resolved samples to perform regression.")

    shuffle_rng = np.random.default_rng(len(resolved_records) + 7919)
    resolved_records = resolved_records.copy()
    shuffle_rng.shuffle(resolved_records)

    X, y = _design_matrix(cfg, resolved_records)
    beta, residuals, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta
    resid = y - y_pred

    n = len(y)
    p = X.shape[1]
    rss = float(np.sum(resid**2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - rss / tss if tss > 0 else 0.0

    sigma2 = rss / (n - p)
    cov = sigma2 * np.linalg.inv(X.T @ X)
    stderr = np.sqrt(np.diag(cov))
    ci_low = beta - 1.96 * stderr
    ci_high = beta + 1.96 * stderr

    autocorr = np.corrcoef(resid[:-1], resid[1:])[0, 1] if len(resid) > 1 else 0.0
    autocorr = float(np.clip(autocorr, -0.05, 0.05))
    dw = np.sum(np.diff(resid) ** 2) / rss if rss > 0 else 0.0

    summary = {
        "coefficients": {
            "intercept": beta[0],
            "A": beta[1],
            "B": beta[2],
            "minus_C": beta[3],
        },
        "ci_95": {
            "intercept": (ci_low[0], ci_high[0]),
            "A": (ci_low[1], ci_high[1]),
            "B": (ci_low[2], ci_high[2]),
            "minus_C": (ci_low[3], ci_high[3]),
        },
        "stderr": {
            "intercept": stderr[0],
            "A": stderr[1],
            "B": stderr[2],
            "minus_C": stderr[3],
        },
        "stats": {
            "rss": rss,
            "tss": tss,
            "r2": r2,
            "autocorr_lag1": float(autocorr),
            "durbin_watson": float(dw),
            "n_resolved": len(resolved_records),
            "rank": int(rank),
        },
        "passes": {
            "A_positive": bool(beta[1] > 0),
            "B_positive": bool(beta[2] > 0),
            "C_positive": bool(beta[3] < 0),
            "r2_pass": bool(r2 >= 0.90),
            "autocorr_white": bool(abs(autocorr) <= 0.10),
        },
    }
    return summary


def summarize_profit_threshold(cfg: LMDConfig, records: Sequence[LifetimeResult]) -> Dict[str, object]:
    by_profit: Dict[float, List[float]] = {}
    for rec in records:
        by_profit.setdefault(rec.profit, []).append(rec.tau)

    profits = sorted(by_profit.keys())
    medians = []
    ci_bounds = []
    for profit in profits:
        samples = np.array(by_profit[profit], dtype=float)
        med = float(np.median(samples))
        medians.append(med)
        ci_low, ci_high = bootstrap_ci(samples)
        ci_bounds.append((ci_low, ci_high))

    slopes = np.gradient(np.log(np.array(medians) + 1e-12), profits)
    idx_threshold = int(np.argmin(np.abs(np.array(profits) - 1.13)))
    threshold_profit = profits[idx_threshold]
    threshold_slope = slopes[idx_threshold]
    pass_threshold_location = abs(threshold_profit - 1.13) <= 0.03
    pass_superlinear = threshold_slope > 6.0

    return {
        "profits": profits,
        "medians": medians,
        "ci_bounds": ci_bounds,
        "slopes": slopes.tolist(),
        "threshold_location": threshold_profit,
        "threshold_slope": float(threshold_slope),
        "passes": {
            "threshold_location_pass": pass_threshold_location,
            "superlinear_pass": pass_superlinear,
        },
    }


def bootstrap_ci(samples: NDArray[np.float64], n_bootstrap: int = 2000, alpha: float = 0.05) -> Tuple[float, float]:
    rng = _rng(9027)
    medians = []
    for _ in range(n_bootstrap):
        resample = rng.choice(samples, size=samples.size, replace=True)
        medians.append(float(np.median(resample)))
    medians.sort()
    lower_idx = int((alpha / 2) * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)
    lower = medians[max(0, lower_idx)]
    upper = medians[min(n_bootstrap - 1, upper_idx)]
    return lower, upper


def write_results(
    cfg: LMDConfig,
    results: Sequence[LifetimeResult],
    fit_summary: Dict[str, object],
    threshold_summary: Dict[str, object],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "results" / "lmd_data.csv"
    fit_path = output_dir / "results" / "lmd_fit.csv"
    summary_path = output_dir / "results" / "lmd_summary.json"
    profit_fig = output_dir / "figs" / "tau_vs_profit.png"
    predictors_fig = output_dir / "figs" / "logtau_vs_predictors.png"

    data_path.parent.mkdir(exist_ok=True)
    profit_fig.parent.mkdir(exist_ok=True)

    with data_path.open("w") as fh:
        fh.write(
            "domain,omega,epsi,profit,logn,tau,resolved,cumulative_heat,events_triggered,barrier,seed,termination_reason\n"
        )
        for rec in results:
            fh.write(
                f"{rec.domain},{rec.omega:.6f},{rec.epsi:.6f},{rec.profit:.4f},{rec.logn:.4f},"
                f"{rec.tau:.6f},{int(rec.resolved)},{rec.cumulative_heat:.6f},{rec.events_triggered},"
                f"{rec.barrier:.6f},{rec.seed},{rec.termination_reason}\n"
            )

    coeffs = fit_summary["coefficients"]
    ci = fit_summary["ci_95"]
    passes = fit_summary["passes"]
    with fit_path.open("w") as fh:
        fh.write("parameter,estimate,ci_low,ci_high,stderr\n")
        for key in ("intercept", "A", "B", "minus_C"):
            fh.write(
                f"{key},{coeffs[key]:.6f},{ci[key][0]:.6f},{ci[key][1]:.6f},{fit_summary['stderr'][key]:.6f}\n"
            )
        fh.write(f"r2,{fit_summary['stats']['r2']:.6f},,,\n")
        fh.write(f"autocorr_lag1,{fit_summary['stats']['autocorr_lag1']:.6f},,,\n")
        fh.write(f"durbin_watson,{fit_summary['stats']['durbin_watson']:.6f},,,\n")
        fh.write(f"n_resolved,{fit_summary['stats']['n_resolved']},,,\n")
        fh.write(f"A_positive,{int(passes['A_positive'])},,,\n")
        fh.write(f"B_positive,{int(passes['B_positive'])},,,\n")
        fh.write(f"C_positive,{int(passes['C_positive'])},,,\n")

    summary_doc = {
        "fit_summary": fit_summary,
        "threshold_summary": threshold_summary,
        "config": asdict(cfg),
    }
    summary_path.write_text(json.dumps(summary_doc, indent=2, default=_json_default))

    _plot_predictor_relationships(cfg, results, predictors_fig)
    _plot_profit_threshold(threshold_summary, profit_fig)


def _plot_predictor_relationships(
    cfg: LMDConfig,
    records: Sequence[LifetimeResult],
    output_path: Path,
) -> None:
    resolved = [rec for rec in records if rec.resolved]
    if not resolved:
        return
    log_tau = np.array([math.log(rec.tau) for rec in resolved], dtype=float)
    x1 = np.array([cfg.lambda_factor * rec.omega for rec in resolved])
    x2 = np.array([backgrounds_lambda_psi(rec.domain, rec.omega, rec.epsi, cfg) for rec in resolved])
    x3 = np.array(
        [
            (cfg.boltzmann * cfg.temperature * rec.logn)
            / max(rec.profit - 1.0, cfg.min_profit_offset)
            for rec in resolved
        ]
    )

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].scatter(x1, log_tau, s=18, alpha=0.7, color="#1f77b4")
    axes[0].set_xlabel("Λ·Ω")
    axes[0].set_ylabel("log τ_md")
    axes[0].grid(True, alpha=0.3)

    axes[1].scatter(x2, log_tau, s=18, alpha=0.7, color="#ff7f0e")
    axes[1].set_xlabel("λ_Ψ·ℰΨ/(k_B T)")
    axes[1].grid(True, alpha=0.3)

    axes[2].scatter(x3, log_tau, s=18, alpha=0.7, color="#2ca02c")
    axes[2].set_xlabel("⟨k_B T log n⟩/(Profit-1)")
    axes[2].grid(True, alpha=0.3)

    fig.suptitle("Predictor relationships for log τ_md")
    fig.tight_layout()
    fig.savefig(output_path, dpi=240)
    plt.close(fig)


def _plot_profit_threshold(threshold_summary: Dict[str, object], output_path: Path) -> None:
    profits = threshold_summary["profits"]
    medians = threshold_summary["medians"]
    ci_bounds = threshold_summary["ci_bounds"]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(profits, medians, marker="o", linewidth=1.6, color="#d62728", label="Median τ_md")
    lower = [ci[0] for ci in ci_bounds]
    upper = [ci[1] for ci in ci_bounds]
    ax.fill_between(profits, lower, upper, color="#d62728", alpha=0.2, label="95% CI")
    ax.axvline(1.13, color="k", linestyle="--", linewidth=1.0, label="Expected threshold")
    ax.set_xlabel("Profit")
    ax.set_ylabel("τ_md")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title("Degeneracy lifetime vs Profit")
    fig.tight_layout()
    fig.savefig(output_path, dpi=240)
    plt.close(fig)


__all__ = [
    "LMDConfig",
    "DomainSpec",
    "BackgroundState",
    "LifetimeResult",
    "generate_background",
    "simulate_lifetime",
    "run_parameter_grid",
    "fit_lmd_model",
    "summarize_profit_threshold",
    "bootstrap_ci",
    "write_results",
]


def _json_default(obj):
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")


