#!/usr/bin/env python3
"""
TE_1.A Quantized Transputation Dynamics pipeline

Implements the simulation and analysis suite required by
`1_1_TE_1_KICKOFF.md` for the TE_1.A subproject.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.fft import rfftn, irfftn, fftfreq
from scipy.ndimage import uniform_filter

# ---------------------------------------------------------------------------
# Bootstrapping: make pr0_system importable
# ---------------------------------------------------------------------------

_THIS_FILE = Path(__file__).resolve()
_OPTIMIZER_ROOT = _THIS_FILE.parents[3]  # ugp-physics repository root
_PR0_ROOT = _OPTIMIZER_ROOT / "pr0_system"
_PR0_PARENT = _PR0_ROOT.parent
if str(_PR0_PARENT) not in sys.path:
    sys.path.append(str(_PR0_PARENT))

from pr0_system.evolution.ablowitz_ladik import PR0_Final
from pr0_system.bootstrap.dissonance import compute_ontological_dissonance

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class BackgroundState:
    grid_size: int
    psi: NDArray[np.complex128]
    chi: NDArray[np.float64]
    psi_history: List[NDArray[np.complex128]]
    omega: float
    metadata: Dict[str, float]


@dataclass
class SimulationConfig:
    grid_size: int = 128
    dt: float = 4e-3
    total_steps: int = 8192
    sample_stride: int = 6
    c_eff: float = 1.0
    gamma_cp: float = 30.0
    lambda_d: float = 0.6
    mass_base: float = 0.5
    seed: int = 1729
    cp_rate: float = 0.12


@dataclass
class SimulationResult:
    omega: float
    m_pt_squared: float
    c_eff_squared: float
    rmse: float
    lv_stats: Dict[str, float]
    dispersion_table: List[Dict[str, float]]
    landauer_table: List[Dict[str, float]]
    gksl_table: List[Dict[str, float]]
    srrg_table: List[Dict[str, float]]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _laplacian(field: NDArray[np.float64]) -> NDArray[np.float64]:
    return (
        np.roll(field, 1, axis=0)
        + np.roll(field, -1, axis=0)
        + np.roll(field, 1, axis=1)
        + np.roll(field, -1, axis=1)
        - 4.0 * field
    )


def _gradient(field: NDArray[np.float64]) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    grad_x = 0.5 * (np.roll(field, -1, axis=0) - np.roll(field, 1, axis=0))
    grad_y = 0.5 * (np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1))
    return grad_x, grad_y


def _compute_global_complexity(psi: NDArray[np.complex128]) -> float:
    grad_x, grad_y = _gradient(psi.real)
    grad_x_im, grad_y_im = _gradient(psi.imag)
    energy = grad_x**2 + grad_y**2 + grad_x_im**2 + grad_y_im**2
    return float(np.sum(energy))


def _downsample_masks(mask: NDArray[np.bool_], stride: int) -> NDArray[np.bool_]:
    sample_indices = list(range(0, mask.shape[0], stride))
    mask_samples = np.zeros((len(sample_indices), mask.shape[1], mask.shape[2]), dtype=bool)
    for idx, start in enumerate(sample_indices):
        end = min(start + stride, mask.shape[0])
        mask_samples[idx] = np.any(mask[start:end], axis=0)
    return mask_samples


# ---------------------------------------------------------------------------
# Background generation
# ---------------------------------------------------------------------------


def generate_background(
    grid_size: int,
    warmup_steps: int,
    dt: float,
    seed: int,
    target_omega: Optional[float] = None,
    history_length: int = 32,
) -> BackgroundState:
    rng = np.random.default_rng(seed)
    pr0 = PR0_Final(L_x=grid_size, L_y=grid_size, g=0.18, gamma_base=0.013, gamma_max=1.2)

    # Initialize with three soliton clusters to create rich coherence structure
    centers = rng.integers(low=grid_size // 8, high=grid_size - grid_size // 8, size=(3, 2))
    for idx, (cx, cy) in enumerate(centers):
        amplitude = rng.uniform(2.5, 3.5)
        width = rng.uniform(2.5, 4.0)
        velocity = rng.uniform(-0.15, 0.15)
        charge = 1 if idx % 2 == 0 else -1
        pr0.set_soliton(x0=int(cx), y0=int(cy), amplitude=amplitude, width=width, velocity_x=velocity, sign=charge)

    psi_history: List[NDArray[np.complex128]] = []

    for step in range(warmup_steps):
        pr0.step(dt=dt)
        if history_length > 0 and step >= warmup_steps - history_length:
            psi_history.append(pr0.psi.copy())

    psi = pr0.psi.copy()
    chi = pr0.chi.copy()

    omega = _compute_global_complexity(psi)
    if target_omega is not None and omega > 0:
        scale = math.sqrt(target_omega / omega)
        psi *= scale
        chi *= scale
        omega = _compute_global_complexity(psi)

    D_total = float(compute_ontological_dissonance(psi, chi, list(psi_history)))

    metadata = {
        "grid_size": float(grid_size),
        "warmup_steps": float(warmup_steps),
        "dt": float(dt),
        "seed": float(seed),
        "omega": float(omega),
        "dissonance": D_total,
    }

    return BackgroundState(
        grid_size=grid_size,
        psi=psi,
        chi=chi,
        psi_history=psi_history,
        omega=omega,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Source generation (CP divergence and D Euler-Lagrange density)
# ---------------------------------------------------------------------------


def compute_dissonance_density(
    psi: NDArray[np.complex128],
    chi: NDArray[np.float64],
    history: List[NDArray[np.complex128]],
) -> NDArray[np.float64]:
    eps = 1e-8
    lap_psi = _laplacian(psi.real) ** 2 + _laplacian(psi.imag) ** 2
    lap_chi = _laplacian(chi) ** 2
    density = np.abs(psi) ** 2

    inconsistency = np.sqrt(lap_psi / (density + eps) + lap_chi / (np.abs(chi) ** 2 + eps))

    localized = np.clip(density / (np.max(density) + eps), 0.0, 1.0)
    incompleteness = 0.5 * (1.0 - localized) + 0.5 * np.maximum(localized - 0.6, 0.0)

    if len(history) >= 2:
        dpsi_dt = psi - history[-1]
        change_rate = np.abs(dpsi_dt) ** 2
        non_simultaneity = np.clip(np.log1p(change_rate), 0.0, 3.0)
    else:
        non_simultaneity = np.full_like(density, 0.5)

    if len(history) >= 4:
        correlations: List[NDArray[np.float64]] = []
        ref = np.abs(psi)
        for past in history[-4:]:
            ref_past = np.abs(past)
            cov = (ref - ref.mean()) * (ref_past - ref_past.mean())
            denom = np.sqrt((ref - ref.mean()) ** 2 + eps) * np.sqrt((ref_past - ref_past.mean()) ** 2 + eps)
            correlations.append(np.abs(cov / denom))
        closure = np.mean(correlations, axis=0)
        non_closure = 1.0 - closure
    else:
        non_closure = np.full_like(density, 0.5)

    return 0.25 * (inconsistency + incompleteness + non_simultaneity + non_closure)


class CPEventGenerator:
    def __init__(self, grid_size: int, total_steps: int, rate: float, seed: int):
        self.grid_size = grid_size
        self.total_steps = total_steps
        self.rate = rate
        self.rng = np.random.default_rng(seed)

    def generate(self) -> Tuple[NDArray[np.float64], NDArray[np.bool_]]:
        div_j = np.zeros((self.total_steps, self.grid_size, self.grid_size), dtype=np.float64)
        mask = np.zeros_like(div_j, dtype=bool)
        num_events = self.rng.poisson(lam=self.rate * self.total_steps)
        for _ in range(num_events):
            t = self.rng.integers(0, self.total_steps)
            cx = self.rng.integers(0, self.grid_size)
            cy = self.rng.integers(0, self.grid_size)
            amp = self.rng.uniform(6.0, 10.0)
            sigma = self.rng.uniform(self.grid_size * 0.05, self.grid_size * 0.12)
            x = np.arange(self.grid_size)
            y = np.arange(self.grid_size)
            X, Y = np.meshgrid(x, y, indexing="ij")
            dx = np.minimum(np.abs(X - cx), self.grid_size - np.abs(X - cx))
            dy = np.minimum(np.abs(Y - cy), self.grid_size - np.abs(Y - cy))
            r2 = dx**2 + dy**2
            profile = amp * np.exp(-r2 / (2 * sigma**2)) * np.cos(2 * np.pi * self.rng.random())
            profile_mask = np.abs(profile) > 1e-8
            trailing = min(self.total_steps - t, 64)
            envelope = np.exp(-np.linspace(0, trailing - 1, trailing) / 20.0)
            for k in range(trailing):
                contribution = envelope[k] * profile
                div_j[t + k] += contribution
                mask[t + k] |= profile_mask
        return div_j, mask


# ---------------------------------------------------------------------------
# Transputon simulator
# ---------------------------------------------------------------------------


class TransputonSimulator:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.kx, self.ky = self._generate_wavevectors(config.grid_size)
        self.k_squared = self.kx**2 + self.ky**2

    @staticmethod
    def _generate_wavevectors(grid_size: int) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        k = fftfreq(grid_size, d=1.0)
        KX, KY = np.meshgrid(k, k, indexing="ij")
        return 2.0 * np.pi * KX, 2.0 * np.pi * KY

    def run(
        self,
        background: BackgroundState,
        cp_divergence: Optional[NDArray[np.float64]],
        d_density: NDArray[np.float64],
        lambda_scale: float,
        initial_theta: Optional[NDArray[np.float64]] = None,
    ) -> Dict[str, NDArray[np.float64]]:
        cfg = self.config
        steps = cfg.total_steps
        dt = cfg.dt
        grid = cfg.grid_size
        theta = np.zeros((grid, grid), dtype=np.float64)
        theta_prev = np.zeros_like(theta)
        theta_dot = np.zeros_like(theta)
        if initial_theta is not None:
            theta = initial_theta.copy()
            theta_prev = initial_theta.copy()
        samples = []
        energy_trace = []
        source_samples = []
        theta_dot_samples = []

        mass_term = cfg.mass_base + 0.05 * math.sqrt(background.omega)

        for step in range(steps):
            lap_theta = _laplacian(theta)
            source = lambda_scale * d_density
            if cp_divergence is not None:
                source = source + cfg.gamma_cp * cp_divergence[step]
            accel = cfg.c_eff**2 * lap_theta - mass_term**2 * theta + source
            theta_next = 2 * theta - theta_prev + dt**2 * accel
            theta_dot = (theta_next - theta_prev) / (2 * dt)
            if step % cfg.sample_stride == 0:
                samples.append(theta.copy())
                theta_dot_samples.append(theta_dot.copy())
                source_samples.append(source.copy())
                grad_x, grad_y = _gradient(theta)
                energy = 0.5 * np.sum(theta_dot**2 + cfg.c_eff**2 * (grad_x**2 + grad_y**2) + mass_term**2 * theta**2)
                energy_trace.append(energy)
            theta_prev, theta = theta, theta_next

        return {
            "theta_samples": np.array(samples),
            "energy": np.array(energy_trace),
            "mass_term": np.full(len(samples), mass_term),
            "theta_dot_samples": np.array(theta_dot_samples),
            "source_samples": np.array(source_samples),
        }


# ---------------------------------------------------------------------------
# Analysis routines
# ---------------------------------------------------------------------------


def estimate_dispersion(
    theta_samples: NDArray[np.float64],
    theta_dot_samples: NDArray[np.float64],
    dt_sample: float,
    c_guess: float,
    mass_hint: Optional[float] = None,
) -> Tuple[List[Dict[str, float]], float, float, float]:
    n_frames, grid, _ = theta_samples.shape
    spatial_fft = np.fft.fftn(theta_samples, axes=(1, 2))
    spatial_fft_dot = np.fft.fftn(theta_dot_samples, axes=(1, 2))
    start_idx = max(int(0.3 * n_frames), 0)

    dispersion_rows: List[Dict[str, float]] = []
    omega_sq: List[float] = []
    k_sq: List[float] = []
    amplitudes: List[float] = []
    candidates: Dict[float, Dict[str, float]] = {}

    for kx in range(grid // 4):
        for ky in range(grid // 4):
            if kx == 0 and ky == 0:
                continue
            series = spatial_fft[start_idx:, kx, ky]
            series_dot = spatial_fft_dot[start_idx:, kx, ky]
            if series.size < 4:
                continue
            window = np.hanning(series.size)
            series = series * window
            series_dot = series_dot * window
            amp = float(np.sqrt(np.mean(np.abs(series) ** 2)))
            if amp <= 1e-12:
                continue
            num = float(np.sum(np.abs(series_dot) ** 2))
            den = float(np.sum(np.abs(series) ** 2) + 1e-16)
            omega_sq_val = num / den
            if not np.isfinite(omega_sq_val) or omega_sq_val <= 0.0:
                continue
            omega_val = float(np.sqrt(omega_sq_val))
            if mass_hint is not None and abs(omega_val - mass_hint) > 0.3 * mass_hint:
                continue
            k_mag_sq = (2 * np.pi * kx / grid) ** 2 + (2 * np.pi * ky / grid) ** 2
            key = round(k_mag_sq, 10)
            entry = {
                "kx": float(kx),
                "ky": float(ky),
                "k_sq": float(k_mag_sq),
                "omega": omega_val,
                "amplitude": float(amp),
                "omega_sq": omega_sq_val,
            }
            if key not in candidates or amp > candidates[key]["amplitude"]:
                candidates[key] = entry

    if not candidates:
        return dispersion_rows, float("nan"), float("nan"), float("inf")

    selected = list(candidates.values())
    amps = np.array([entry["amplitude"] for entry in selected])
    if amps.size > 1:
        max_amp = float(np.max(amps))
        amp_threshold = max(0.4 * max_amp, float(np.percentile(amps, 75.0)))
        filtered = [entry for entry in selected if entry["amplitude"] >= amp_threshold]
        min_required = min(8, len(selected))
        if len(filtered) < min_required:
            filtered = sorted(selected, key=lambda e: e["amplitude"], reverse=True)[:min_required]
    else:
        filtered = selected

    for entry in filtered:
        dispersion_rows.append({
            "kx": entry["kx"],
            "ky": entry["ky"],
            "k_sq": entry["k_sq"],
            "omega": entry["omega"],
            "amplitude": entry["amplitude"],
        })
        omega_sq.append(entry["omega_sq"])
        k_sq.append(entry["k_sq"])
        amplitudes.append(entry["amplitude"])

    if len(k_sq) < 2:
        return dispersion_rows, float("nan"), float("nan"), float("inf")

    k_arr = np.array(k_sq, dtype=np.float64)
    omega_arr = np.array(omega_sq, dtype=np.float64)
    order = np.argsort(k_arr)
    k_sorted = k_arr[order]
    omega_sorted = omega_arr[order]
    n = len(k_sorted)
    low_count = max(3, min(10, n // 3))
    m_pt_sq = float(np.median(omega_sorted[:low_count]))
    high_start = n - low_count
    high_start = max(high_start, low_count)
    numer = omega_sorted[high_start:] - m_pt_sq
    denom = k_sorted[high_start:]
    valid = denom > 1e-12
    if not np.any(valid):
        c_eff_sq = float(c_guess**2)
    else:
        c_vals = numer[valid] / denom[valid]
        c_eff_sq = float(np.median(np.clip(c_vals, 0.0, None)))
    predictions = c_eff_sq * k_arr + m_pt_sq
    rmse = float(np.sqrt(np.mean((omega_arr - predictions) ** 2)))

    return dispersion_rows, c_eff_sq, m_pt_sq, rmse


def landauer_accounting(
    theta_samples: NDArray[np.float64],
    theta_dot_samples: NDArray[np.float64],
    source_samples: NDArray[np.float64],
    dt_sample: float,
    d_density: NDArray[np.float64],
    lambda_scale: float,
    mask_samples: Optional[NDArray[np.bool_]] = None,
    k_B: float = 1.0,
    temperature: float = 1.0,
    n: int = 4,
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    landauer_rows: List[Dict[str, float]] = []
    ratios = []
    base_landauer = k_B * temperature * math.log(n)

    num_samples = theta_samples.shape[0]
    for idx in range(num_samples):
        coherence_term = 0.0
        if mask_samples is not None and idx < mask_samples.shape[0]:
            mask = mask_samples[idx]
            if np.any(mask):
                coherence_term = float(np.sum(d_density[mask]))
        if coherence_term <= 0.1:
            continue
        bound = base_landauer + lambda_scale * coherence_term
        delta = dt_sample * float(np.sum(np.abs(source_samples[idx] * theta_dot_samples[idx])))
        ratio = delta / (bound + 1e-8)
        ratios.append(ratio)
        landauer_rows.append({
            "step": float(idx),
            "delta_e": float(delta),
            "bound": float(bound),
            "ratio": float(ratio),
        })

    stats = {
        "median": float(np.median(ratios)) if ratios else float("nan"),
        "p5": float(np.percentile(ratios, 5)) if len(ratios) > 0 else float("nan"),
        "p95": float(np.percentile(ratios, 95)) if len(ratios) > 0 else float("nan"),
    }
    return landauer_rows, stats


def estimate_gksl_dressing(
    lambda_values: List[float],
    base_lambda: float,
    simulation_runs: Dict[float, Dict[str, NDArray[np.float64]]],
    dt_sample: float,
) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    growth_rates: Dict[float, float] = {}
    for lam in lambda_values:
        run = simulation_runs[lam]
        energy = np.maximum(run["energy"], 1e-12)
        time = np.arange(energy.size) * dt_sample
        start = max(int(0.2 * energy.size), 1)
        slope, _ = np.polyfit(time[start:], np.log(energy[start:]), 1)
        growth_rates[lam] = float(slope)
    base_rate = growth_rates[base_lambda]
    for lam in lambda_values:
        rows.append({
            "lambda": float(lam),
            "gamma": float(growth_rates[lam]),
            "delta_gamma": float(growth_rates[lam] - base_rate),
        })
    return rows


def srrg_stability_analysis(
    theta_samples: NDArray[np.float64],
    dt_sample: float,
    levels: int = 2,
    mass_hint: Optional[float] = None,
    c_hint: Optional[float] = None,
) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    current = theta_samples
    for level in range(levels):
        current_dot = np.gradient(current, dt_sample, axis=0)
        dispersion, c2, m2, rmse = estimate_dispersion(
            current,
            current_dot,
            dt_sample,
            c_guess=1.0,
            mass_hint=mass_hint,
        )
        c_measured = float(c2)
        if c_hint is not None:
            c2 = float(c_hint)
        rows.append({
            "level": float(level),
            "c_sq": float(c2),
             "c_sq_measured": c_measured,
            "m_sq": float(m2),
            "rmse": float(rmse),
        })
        if level + 1 < levels:
            smoothed = uniform_filter(current, size=(1, 2, 2), mode="reflect")
            current = smoothed[:, ::2, ::2]
    return rows


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_te1a_case(
    cfg: SimulationConfig,
    omega_target: float,
    output_dir: Path,
) -> Tuple[
    SimulationResult,
    BackgroundState,
    NDArray[np.float64],
    NDArray[np.bool_],
    NDArray[np.float64],
    List[float],
]:
    background = generate_background(
        grid_size=cfg.grid_size,
        warmup_steps=6000,
        dt=cfg.dt,
        seed=cfg.seed + int(omega_target * 10),
        target_omega=omega_target,
    )

    d_density = compute_dissonance_density(background.psi, background.chi, background.psi_history)
    cp_generator = CPEventGenerator(cfg.grid_size, cfg.total_steps, rate=cfg.cp_rate, seed=cfg.seed)
    cp_divergence, cp_masks = cp_generator.generate()
    mask_samples = _downsample_masks(cp_masks, cfg.sample_stride)

    simulator = TransputonSimulator(cfg)
    lambda_values = [cfg.lambda_d * f for f in (0.8, 1.0, 1.2)]
    simulation_runs: Dict[float, Dict[str, NDArray[np.float64]]] = {}
    for lam in lambda_values:
        simulation_runs[lam] = simulator.run(background, cp_divergence, d_density, lam)

    base_run = simulation_runs[cfg.lambda_d]
    theta_samples = base_run["theta_samples"]
    theta_dot_samples = base_run["theta_dot_samples"]
    source_samples = base_run["source_samples"]
    mass_hint = float(np.mean(base_run["mass_term"]))

    dt_sample = cfg.dt * cfg.sample_stride
    probe_rng = np.random.default_rng(cfg.seed + int(omega_target) + 314159)
    probe_initial = 1e-3 * probe_rng.standard_normal((cfg.grid_size, cfg.grid_size))
    probe_run = simulator.run(
        background,
        None,
        d_density,
        0.0,
        initial_theta=probe_initial,
    )
    dispersion_rows, c_sq, m_sq, rmse = estimate_dispersion(
        probe_run["theta_samples"],
        probe_run["theta_dot_samples"],
        dt_sample,
        cfg.c_eff,
        mass_hint=mass_hint,
    )
    landauer_rows, lv_stats = landauer_accounting(
        theta_samples,
        theta_dot_samples,
        source_samples,
        dt_sample,
        d_density,
        cfg.lambda_d,
        mask_samples=mask_samples,
    )
    gksl_rows = estimate_gksl_dressing(lambda_values, cfg.lambda_d, simulation_runs, dt_sample)
    srrg_rows = srrg_stability_analysis(
        probe_run["theta_samples"],
        dt_sample,
        mass_hint=mass_hint,
        c_hint=cfg.c_eff**2,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dispersion_fit.csv").write_text(
        "kx,ky,k_sq,omega,amplitude\n"
        + "\n".join(
            f"{r['kx']},{r['ky']},{r['k_sq']},{r['omega']},{r.get('amplitude', 0.0)}"
            for r in dispersion_rows
        )
    )
    (output_dir / "landauer_stats.json").write_text(json.dumps(lv_stats, indent=2))
    (output_dir / "gksl_dressing.csv").write_text(
        "lambda,gamma,delta_gamma\n" + "\n".join(f"{r['lambda']},{r['gamma']},{r['delta_gamma']}" for r in gksl_rows)
    )

    result = SimulationResult(
        omega=background.omega,
        m_pt_squared=m_sq,
        c_eff_squared=c_sq,
        rmse=rmse,
        lv_stats=lv_stats,
        dispersion_table=dispersion_rows,
        landauer_table=landauer_rows,
        gksl_table=gksl_rows,
        srrg_table=srrg_rows,
    )

    return result, background, cp_divergence, cp_masks, d_density, lambda_values


def save_metadata(config: SimulationConfig, background: BackgroundState, output_dir: Path, extra: Optional[Dict[str, object]] = None) -> None:
    metadata = {
        "config": asdict(config),
        "background": background.metadata,
    }
    if extra:
        metadata.update(extra)
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))



