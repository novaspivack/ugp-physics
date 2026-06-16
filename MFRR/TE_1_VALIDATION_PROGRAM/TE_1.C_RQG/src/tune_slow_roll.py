"""
Slow-roll tuning utility for TE_1.C spectra generation.

Scans background parameters (m, beta, omega_bar, psi0) to locate configurations
that yield an extended slow-roll plateau (epsilon << 1).  The best candidate is
written to configs/spectra_slow_roll.yaml and the full scan report is saved
under results/spectra_slow_roll_tuning.json.
"""

from __future__ import annotations

import json
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import yaml

try:
    from .constants import CONSTS
    from .frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        FRWRunResult,
        integrate_background,
        _dV_dpsi,
        _hubble,
        _analytic_potential,
    )
except ImportError:  # pragma: no cover
    import sys

    PACKAGE_ROOT = Path(__file__).resolve().parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.append(str(PACKAGE_ROOT))
    from constants import CONSTS
    from frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        FRWRunResult,
        integrate_background,
        _dV_dpsi,
        _hubble,
        _analytic_potential,
    )

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
CONFIGS_DIR = ROOT / "configs"

# Coarse scan grid (focused on primary slow-roll knobs)
COARSE_GRID = {
    "m": [0.0],
    "beta": [0.0],
    "omega_bar": [0.0],
    "rf_bar": [0.94, 0.96, 0.98],
    "omega_m0": [0.0, 0.015],
    "mass_scale": [5.0e-9],
    "linear_scale": [1.0e-9],
    "psi0": [2.0, 3.5, 5.5],
    "flat_amplitude": [0.0],
    "flat_width": [0.3],
    "flat_center": [0.0],
    "quartic_coeff": [0.0],
    "use_analytic_potential": [True],
    "analytic_v0": [1.3e-3, 1.7e-3, 2.1e-3],
    "analytic_eps0": [2.0e-4, 5.0e-4, 1.0e-3, 2.5e-3, 5.0e-3, 8.0e-3],
    "analytic_beta": [0.25, 0.4, 0.55, 0.7],
    "analytic_psiref": [2.5, 4.0, 5.2],
    "analytic_transition_amp": [0.0],
    "analytic_transition_width": [1.0],
    "analytic_transition_center": [5.0],
    "analytic_ramp_amp": [0.0],
    "analytic_ramp_slope": [0.0],
    "analytic_ramp_center": [5.0],
    "analytic_plateau_amp": [0.0],
    "analytic_plateau_width": [1.0],
    "analytic_plateau_center": [5.0],
}

# Refinement parameters
REFINE_SCALE_FACTORS = [0.7, 1.0, 1.35]
REFINE_PSI_OFFSETS = [-1.0, -0.5, -0.2, 0.0, 0.2, 0.5, 1.0]
REFINE_RF_OFFSETS = [-0.01, 0.0, 0.01]
REFINE_OMEGA_M0_FACTORS = [1.0]
REFINE_FLAT_AMPL_FACTORS = [0.5, 1.0, 1.8]
REFINE_FLAT_WIDTH_FACTORS = [0.7, 1.0, 1.4]
REFINE_FLAT_CENTER_OFFSETS = [-0.05, 0.0, 0.05]
REFINE_QUARTIC_FACTORS = [0.5, 1.0, 1.8]
REFINE_ANALYTIC_V0_FACTORS = [0.5, 0.7, 1.0, 1.4, 1.8]
REFINE_ANALYTIC_EPS_FACTORS = [0.5, 0.75, 1.0, 1.5, 2.0]
REFINE_ANALYTIC_BETA_FACTORS = [0.6, 0.8, 1.0, 1.3, 1.6]
REFINE_ANALYTIC_SHIFT_OFFSETS = [-0.5, -0.2, 0.0, 0.2, 0.5]
REFINE_TRANSITION_AMP_FACTORS = [0.5, 1.0, 1.5]
REFINE_TRANSITION_WIDTH_FACTORS = [0.7, 1.0, 1.4]
REFINE_TRANSITION_CENTER_OFFSETS = [-0.5, -0.2, 0.0, 0.2, 0.5]
REFINE_RAMP_FACTORS = [0.5, 1.0, 1.5]
REFINE_RAMP_CENTER_OFFSETS = [-0.5, 0.0, 0.5]
REFINE_PLATEAU_FACTORS = [0.5, 1.0, 1.5]
REFINE_PLATEAU_CENTER_OFFSETS = [-0.5, 0.0, 0.5]
REFINE_TOP_K = 10
MAX_VARIANTS_PER_CANDIDATE = 160

# Slow-roll targets
EPSILON_TARGET = 0.05   # epsilon must stay below this threshold
ETA_TARGET = 0.1        # |eta| should be modest as well
MIN_EFOLDS = 3.0        # plateau must cover at least this many e-folds
MAX_EFOLDS = 8.0        # plateau should not extend beyond this many e-folds in search
HUBBLE_MIN = 1.0e-22
HUBBLE_MAX = 5.0e-4
ETA_H_MAX = 0.15
MIN_LN_A_STOP = -6.0

# Background integration settings for tuning
ZMAX_TUNING = 1.0e8
NSTEPS_TUNING = 8000


def _log_failure_summary(results: List[Dict], stage: str, top_reasons: int = 6) -> None:
    if not results:
        return
    status_counter = Counter(r.get("status", "unknown") for r in results)
    summary = ", ".join(f"{status}={count}" for status, count in status_counter.most_common())
    print(f"[tune] {stage} status counts: {summary}", flush=True)
    reason_counter = Counter(
        (r.get("reason") or "(no reason)")
        for r in results
        if r.get("status") not in {"ok"}
    )
    if reason_counter:
        print(f"[tune] {stage} top failure reasons:", flush=True)
        for reason, count in reason_counter.most_common(top_reasons):
            print(f"    {reason}: {count}", flush=True)


def clamp(value: float, min_value: float, max_value: float) -> float:
    return float(max(min_value, min(max_value, value)))


def _contiguous_segments(mask: np.ndarray) -> List[Tuple[int, int]]:
    """Return list of (start, end) indices (inclusive) for True segments."""
    segments: List[Tuple[int, int]] = []
    start = None
    for idx, value in enumerate(mask):
        if value and start is None:
            start = idx
        elif not value and start is not None:
            segments.append((start, idx - 1))
            start = None
    if start is not None:
        segments.append((start, len(mask) - 1))
    return segments


def _select_epsilon_eta(run: FRWRunResult) -> Tuple[np.ndarray, np.ndarray]:
    eps = np.asarray(run.epsilon_potential)
    eta = np.asarray(run.eta_potential)
    if np.isfinite(eps).any() and np.isfinite(eta).any():
        return eps, eta
    return np.asarray(run.epsilon), np.asarray(run.eta_sr)


def evaluate_slow_roll(run: FRWRunResult) -> Optional[Dict]:
    """Evaluate slow-roll plateau metrics; return None if criteria not met."""
    epsilon, eta = _select_epsilon_eta(run)
    ln_a = run.ln_a
    hubble = run.hubble

    mask = (epsilon >= 0.0) & (epsilon < EPSILON_TARGET) & (np.abs(eta) < ETA_TARGET)
    segments = _contiguous_segments(mask)
    if not segments:
        return None

    best_segment = max(
        segments,
        key=lambda seg: abs(ln_a[seg[0]] - ln_a[seg[1]]),
    )
    start, end = best_segment
    efolds = abs(ln_a[start] - ln_a[end])
    if efolds < MIN_EFOLDS:
        return None

    eps_slice = epsilon[start : end + 1]
    eta_slice = eta[start : end + 1]
    hubble_slice = hubble[start : end + 1]

    return {
        "ln_a_start": float(ln_a[start]),
        "ln_a_end": float(ln_a[end]),
        "efolds": float(efolds),
        "epsilon_mean": float(np.mean(eps_slice)),
        "epsilon_min": float(np.min(eps_slice)),
        "epsilon_max": float(np.max(eps_slice)),
        "eta_mean": float(np.mean(eta_slice)),
        "hubble_mean": float(np.mean(hubble_slice)),
    }


def compute_fallback_metrics(run: FRWRunResult) -> Dict[str, float]:
    epsilon, eta = _select_epsilon_eta(run)
    ln_a = np.asarray(run.ln_a)

    with np.errstate(invalid="ignore"):
        min_epsilon = float(
            np.nan_to_num(np.nanmin(epsilon), nan=1.0e9, posinf=1.0e9, neginf=1.0e9)
        )
        min_abs_eta = float(
            np.nan_to_num(np.nanmin(np.abs(eta)), nan=1.0e9, posinf=1.0e9, neginf=1.0e9)
        )

    relaxed_mask = (epsilon > 0) & (epsilon < EPSILON_TARGET * 5.0) & (
        np.abs(eta) < max(ETA_TARGET * 5.0, 1.0)
    )
    segments = _contiguous_segments(relaxed_mask)
    candidate_efolds = 0.0
    if segments:
        candidate_efolds = max(abs(ln_a[start] - ln_a[end]) for start, end in segments)

    return {
        "min_epsilon": min_epsilon,
        "min_abs_eta": min_abs_eta,
        "candidate_efolds": float(candidate_efolds),
    }


def _estimate_ppsi0(cfg: FRWModelConfig, psi0: float) -> float:
    H0 = _hubble(1.0, psi0, 0.0, cfg)
    if H0 <= 0.0:
        return 0.0
    grad = _dV_dpsi(psi0, cfg)
    return -grad / (3.0 * H0)


def _estimate_ns_from_potential(cfg: FRWModelConfig, psi0: float) -> Optional[float]:
    if not cfg.use_analytic_potential:
        return None
    V, dV, d2V = _analytic_potential(psi0, cfg)
    if V <= 0:
        return None
    eps = 0.5 * (dV / V) ** 2
    eta = d2V / V
    return 1.0 - 6.0 * eps + 2.0 * eta


def _evaluate_params(params: Dict[str, float]) -> Dict:
    local_params = dict(params)
    cfg = FRWModelConfig(
        m=local_params["m"],
        beta=local_params["beta"],
        omega_bar=local_params["omega_bar"],
        rf_bar=local_params["rf_bar"],
        omega_m0=local_params["omega_m0"],
        mass_scale=local_params["mass_scale"],
        linear_scale=local_params["linear_scale"],
        flat_amplitude=local_params["flat_amplitude"],
        flat_width=local_params["flat_width"],
        flat_center=local_params["flat_center"],
        quartic_coeff=local_params["quartic_coeff"],
        use_analytic_potential=local_params["use_analytic_potential"],
        analytic_v0=local_params["analytic_v0"],
        analytic_eps0=local_params["analytic_eps0"],
        analytic_beta=local_params["analytic_beta"],
        analytic_psiref=local_params["analytic_psiref"],
        analytic_transition_amp=local_params["analytic_transition_amp"],
        analytic_transition_width=local_params["analytic_transition_width"],
        analytic_transition_center=local_params["analytic_transition_center"],
        analytic_ramp_amp=local_params["analytic_ramp_amp"],
        analytic_ramp_slope=local_params["analytic_ramp_slope"],
        analytic_ramp_center=local_params["analytic_ramp_center"],
        analytic_plateau_amp=local_params["analytic_plateau_amp"],
        analytic_plateau_width=local_params["analytic_plateau_width"],
        analytic_plateau_center=local_params["analytic_plateau_center"],
        zmax=ZMAX_TUNING,
        nsteps=NSTEPS_TUNING,
    )
    psi0 = local_params["psi0"]
    ppsi0 = local_params.get("ppsi0")
    if ppsi0 is None:
        ppsi0 = _estimate_ppsi0(cfg, psi0)
        local_params["ppsi0"] = float(ppsi0)
    ns_pred = _estimate_ns_from_potential(cfg, psi0)
    if ns_pred is not None:
        local_params["ns_pred"] = float(ns_pred)
    if ns_pred is not None and (ns_pred < 0.85 or ns_pred > 1.08):
        return {
            "config": local_params,
            "status": "fail_prefilter",
            "reason": f"n_s_pred={ns_pred:.3f}",
            "metrics": None,
            "fallback": None,
        }
    ic = FRWInitialConditions(psi0=psi0, ppsi0=ppsi0)
    try:
        run = integrate_background(cfg, ic, rtol=1.0e-7, atol=1.0e-9, min_ln_a=MIN_LN_A_STOP)
    except RuntimeError as exc:
        return {
            "config": local_params,
            "status": "fail",
            "reason": str(exc),
            "metrics": None,
            "fallback": None,
        }

    metrics = evaluate_slow_roll(run)
    fallback = compute_fallback_metrics(run)

    epsilon_h = np.asarray(run.epsilon)
    eta_h = np.asarray(run.eta_sr)
    hubble = np.asarray(run.hubble)

    if not np.all(np.isfinite(epsilon_h)) or not np.all(np.isfinite(hubble)):
        return {
            "config": local_params,
            "status": "fail_dynamic",
            "reason": "non-finite values in dynamics",
            "metrics": metrics,
            "fallback": fallback,
        }

    epsilon_h_max = float(np.nanmax(epsilon_h))
    eta_h_max = float(np.nanmax(np.abs(eta_h))) if eta_h.size else float("nan")
    hubble_min = float(np.nanmin(hubble))
    hubble_max = float(np.nanmax(hubble))

    if metrics is None:
        if epsilon_h_max >= EPSILON_TARGET:
            return {
                "config": local_params,
                "status": "fail_dynamic",
                "reason": f"epsilon_H_max={epsilon_h_max:.3e}",
                "metrics": metrics,
                "fallback": fallback,
            }

        if np.isfinite(eta_h_max) and eta_h_max >= ETA_H_MAX:
            return {
                "config": local_params,
                "status": "fail_dynamic",
                "reason": f"eta_H_max={eta_h_max:.3e}",
                "metrics": metrics,
                "fallback": fallback,
            }

    if hubble_max > HUBBLE_MAX or hubble_min < HUBBLE_MIN:
        return {
            "config": local_params,
            "status": "fail_dynamic",
            "reason": f"hubble_range=({hubble_min:.3e},{hubble_max:.3e})",
            "metrics": metrics,
            "fallback": fallback,
        }

    status = "ok" if metrics is not None else "no_plateau"
    return {
        "config": local_params,
        "status": status,
        "metrics": metrics,
        "fallback": fallback,
    }


def _evaluate_grid(param_list: Iterable[Dict[str, float]], num_workers: int) -> List[Dict]:
    params = list(param_list)
    if not params:
        return []
    results: List[Dict] = []
    if num_workers <= 1:
        for p in params:
            results.append(_evaluate_params(p))
    else:
        with ProcessPoolExecutor(max_workers=num_workers) as pool:
            futures = {pool.submit(_evaluate_params, p): p for p in params}
            for fut in as_completed(futures):
                results.append(fut.result())
    return results


def _generate_coarse_grid() -> List[Dict[str, float]]:
    keys = list(COARSE_GRID.keys())
    value_lists = [COARSE_GRID[k] for k in keys]
    grid: List[Dict[str, float]] = []
    seen = set()
    for values in product(*value_lists):
        params = {}
        for key, value in zip(keys, values):
            if isinstance(value, bool):
                params[key] = value
            elif isinstance(value, (int, float)):
                params[key] = float(value)
            else:
                params[key] = value
        key = tuple(sorted(params.items()))
        if key in seen:
            continue
        seen.add(key)
        grid.append(params)
    return grid


def _expand_positive(base_value: float, fallback: float, min_val: float, max_val: float) -> List[float]:
    base = base_value if base_value > 0 else fallback
    values = set()
    for factor in REFINE_SCALE_FACTORS:
        candidate = clamp(base * factor, min_val, max_val)
        values.add(candidate)
    if base_value > 0:
        values.add(clamp(base_value, min_val, max_val))
    return sorted(values)


def _expand_rf(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_RF_OFFSETS:
        values.add(clamp(base_value + offset, 0.90, 0.999))
    values.add(clamp(base_value, 0.90, 0.999))
    return sorted(values)


def _expand_omega_m0(base_value: float) -> List[float]:
    values = set()
    base = base_value if base_value > 0 else 1.0e-10
    for factor in REFINE_OMEGA_M0_FACTORS:
        values.add(clamp(base * factor, 0.0, 1.0e-7))
        values.add(clamp(base / factor, 0.0, 1.0e-7))
    values.add(clamp(base_value, 0.0, 1.0e-7))
    values.add(0.0)
    return sorted(values)


def _expand_psi(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_PSI_OFFSETS:
        values.add(clamp(base_value + offset, -2.0, 2.0))
    values.add(clamp(base_value, -2.0, 2.0))
    return sorted(values)


def _expand_quartic_coeff(base_value: float) -> List[float]:
    values = set()
    base = base_value if base_value > 0 else 1.0e-10
    for factor in REFINE_QUARTIC_FACTORS:
        values.add(clamp(base * factor, 0.0, 10.0))
        values.add(clamp(base / factor, 0.0, 10.0))
    values.add(clamp(base_value, 0.0, 10.0))
    values.add(0.0)
    return sorted(values)


def _expand_flat_amplitude(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 1.0e-3
    values = set()
    for factor in REFINE_FLAT_AMPL_FACTORS:
        values.add(clamp(base * factor, 0.0, 5.0e-3))
    values.add(clamp(base_value, 0.0, 5.0e-3))
    return sorted(values)


def _expand_flat_width(base_value: float) -> List[float]:
    width = base_value if base_value > 0 else 0.3
    values = set()
    for factor in REFINE_FLAT_WIDTH_FACTORS:
        values.add(clamp(width * factor, 0.1, 0.7))
    values.add(clamp(width, 0.1, 0.7))
    return sorted(values)


def _expand_flat_center(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_FLAT_CENTER_OFFSETS:
        values.add(clamp(base_value + offset, -0.15, 0.15))
    values.add(clamp(base_value, -0.15, 0.15))
    return sorted(values)


def _expand_quartic(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 1.0
    values = set()
    for factor in REFINE_QUARTIC_FACTORS:
        values.add(clamp(base * factor, 0.0, 6.0))
    values.add(clamp(base_value, 0.0, 6.0))
    return sorted(values)


def _expand_analytic_v0(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 1.0e-3
    values = set()
    for factor in REFINE_ANALYTIC_V0_FACTORS:
        values.add(clamp(base * factor, 5.0e-4, 5.0e-3))
    values.add(clamp(base_value, 5.0e-4, 5.0e-3))
    return sorted(values)


def _expand_analytic_eps0(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 5.0e-3
    values = set()
    for factor in REFINE_ANALYTIC_EPS_FACTORS:
        values.add(clamp(base * factor, 1.0e-3, 5.0e-2))
    values.add(clamp(base_value, 1.0e-3, 5.0e-2))
    return sorted(values)


def _expand_analytic_beta(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 0.5
    values = set()
    for factor in REFINE_ANALYTIC_BETA_FACTORS:
        values.add(clamp(base * factor, 0.2, 1.5))
    values.add(clamp(base_value, 0.2, 1.5))
    return sorted(values)


def _expand_analytic_shift(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_ANALYTIC_SHIFT_OFFSETS:
        values.add(clamp(base_value + offset, -0.5, 0.5))
    values.add(clamp(base_value, -0.5, 0.5))
    return sorted(values)


def _expand_transition_amp(base_value: float) -> List[float]:
    base = base_value if base_value != 0.0 else 0.05
    values = set()
    for factor in REFINE_TRANSITION_AMP_FACTORS:
        values.add(clamp(base * factor, -0.2, 0.2))
        values.add(clamp(-base * factor, -0.2, 0.2))
    values.add(clamp(base_value, -0.2, 0.2))
    values.add(0.0)
    return sorted(values)


def _expand_transition_width(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 1.0
    values = set()
    for factor in REFINE_TRANSITION_WIDTH_FACTORS:
        values.add(clamp(base * factor, 0.3, 2.5))
    values.add(clamp(base_value, 0.3, 2.5))
    return sorted(values)


def _expand_transition_center(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_TRANSITION_CENTER_OFFSETS:
        values.add(clamp(base_value + offset, 3.0, 6.5))
    values.add(clamp(base_value, 3.0, 6.5))
    return sorted(values)


def _expand_ramp_amp(base_value: float) -> List[float]:
    values = set()
    for factor in REFINE_RAMP_FACTORS:
        values.add(clamp(base_value * factor, -0.05, 0.05))
        values.add(clamp(-base_value * factor, -0.05, 0.05))
    values.add(clamp(base_value, -0.05, 0.05))
    values.add(0.0)
    return sorted(values)


def _expand_ramp_center(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_RAMP_CENTER_OFFSETS:
        values.add(clamp(base_value + offset, 3.0, 6.5))
    values.add(clamp(base_value, 3.0, 6.5))
    return sorted(values)


def _expand_plateau_amp(base_value: float) -> List[float]:
    base = base_value if base_value != 0.0 else 0.02
    values = set()
    for factor in REFINE_PLATEAU_FACTORS:
        values.add(clamp(base * factor, 0.0, 0.1))
    values.add(clamp(base_value, 0.0, 0.1))
    values.add(0.0)
    return sorted(values)


def _expand_plateau_width(base_value: float) -> List[float]:
    base = base_value if base_value > 0 else 1.0
    values = set()
    for factor in REFINE_PLATEAU_FACTORS:
        values.add(clamp(base * factor, 0.3, 2.0))
    values.add(clamp(base_value, 0.3, 2.0))
    return sorted(values)


def _expand_plateau_center(base_value: float) -> List[float]:
    values = set()
    for offset in REFINE_PLATEAU_CENTER_OFFSETS:
        values.add(clamp(base_value + offset, 3.0, 6.5))
    values.add(clamp(base_value, 3.0, 6.5))
    return sorted(values)


def _generate_refined_grid(candidates: List[Dict], max_variants: int) -> List[Dict[str, float]]:
    grid: List[Dict[str, float]] = []
    seen = set()
    for cand in candidates:
        cfg = cand["config"]
        analytic_flag = bool(cfg.get("use_analytic_potential", False))

        value_grid = product(
            _expand_positive(cfg["m"], 5.0e-9, 0.0, 5.0e-7),
            _expand_positive(cfg["beta"], 4.0e-5, 0.0, 5.0e-4),
            _expand_positive(cfg["omega_bar"], 4.0e-5, 0.0, 5.0e-4),
            _expand_positive(cfg["mass_scale"], 1.0e-8, 5.0e-10, 5.0e-7),
            _expand_positive(cfg["linear_scale"], 8.0e-10, 5.0e-11, 5.0e-7),
            _expand_psi(cfg["psi0"]),
            _expand_rf(cfg["rf_bar"]),
            _expand_omega_m0(cfg["omega_m0"]),
            _expand_flat_amplitude(cfg.get("flat_amplitude", 0.0)),
            _expand_flat_width(cfg.get("flat_width", 0.3)),
            _expand_flat_center(cfg.get("flat_center", 0.0)),
            _expand_quartic(cfg.get("quartic_coeff", 0.0)),
            _expand_analytic_v0(cfg.get("analytic_v0", 1.5e-3)),
            _expand_analytic_eps0(cfg.get("analytic_eps0", 5.0e-3)),
            _expand_analytic_beta(cfg.get("analytic_beta", 0.5)),
            _expand_analytic_shift(cfg.get("analytic_psiref", 0.0)),
            _expand_transition_amp(cfg.get("analytic_transition_amp", 0.0)),
            _expand_transition_width(cfg.get("analytic_transition_width", 1.0)),
            _expand_transition_center(cfg.get("analytic_transition_center", 0.0)),
            _expand_ramp_amp(cfg.get("analytic_ramp_amp", 0.0)),
            _expand_ramp_center(cfg.get("analytic_ramp_center", 0.0)),
            _expand_plateau_amp(cfg.get("analytic_plateau_amp", 0.0)),
            _expand_plateau_width(cfg.get("analytic_plateau_width", 1.0)),
            _expand_plateau_center(cfg.get("analytic_plateau_center", 0.0)),
        )

    for (
        m,
        beta,
        omega_bar,
        mass_scale,
        linear_scale,
        psi0,
            rf_bar,
            omega_m0,
            flat_amp,
            flat_width,
            flat_center,
            quartic,
            analytic_v0,
            analytic_eps,
            analytic_beta,
            analytic_shift,
            trans_amp,
            trans_width,
            trans_center,
            ramp_amp,
            ramp_center,
            plateau_amp,
            plateau_width,
            plateau_center,
        ) in value_grid:
            params = {
                "m": float(m),
                "beta": float(beta),
                "omega_bar": float(omega_bar),
                "rf_bar": float(rf_bar),
                "omega_m0": float(omega_m0),
                "mass_scale": float(mass_scale),
                "linear_scale": float(linear_scale),
                "psi0": float(psi0),
                "flat_amplitude": float(flat_amp),
                "flat_width": float(flat_width),
                "flat_center": float(flat_center),
                "quartic_coeff": float(quartic),
                "use_analytic_potential": analytic_flag,
                "analytic_v0": float(analytic_v0),
                "analytic_eps0": float(analytic_eps),
                "analytic_beta": float(analytic_beta),
                "analytic_psiref": float(analytic_shift),
                "analytic_transition_amp": float(trans_amp),
                "analytic_transition_width": float(trans_width),
                "analytic_transition_center": float(trans_center),
                "analytic_ramp_amp": float(ramp_amp),
                "analytic_ramp_slope": 0.0,
                "analytic_ramp_center": float(ramp_center),
                "analytic_plateau_amp": float(plateau_amp),
                "analytic_plateau_width": float(plateau_width),
                "analytic_plateau_center": float(plateau_center),
            }
            key = tuple(sorted(params.items()))
            if key in seen:
                continue
            seen.add(key)
            grid.append(params)
            if len(grid) >= max_variants:
                return grid
    return grid


def _select_refinement_candidates(results: List[Dict], top_k: int) -> List[Dict]:
    scored = []
    for idx, entry in enumerate(results):
        fallback = entry.get("fallback") or {}
        try:
            efolds = float(fallback.get("candidate_efolds", 0.0) or 0.0)
        except (TypeError, ValueError):
            efolds = 0.0
        try:
            min_eps = float(fallback.get("min_epsilon", np.inf))
        except (TypeError, ValueError):
            min_eps = float(np.inf)
        try:
            min_abs_eta = float(fallback.get("min_abs_eta", np.inf))
        except (TypeError, ValueError):
            min_abs_eta = float(np.inf)
        scored.append((-efolds, min_eps, min_abs_eta, idx, entry))
    scored.sort()
    selected = []
    seen_configs = set()
    for _, __, ___, __idx, entry in scored:
        key = tuple(sorted(entry["config"].items()))
        if key in seen_configs:
            continue
        seen_configs.add(key)
        selected.append(entry)
        if len(selected) >= top_k:
            break
    return selected


def scan_parameter_space(num_workers: int, refine_top_k: int, max_refine: int) -> List[Dict]:
    results: List[Dict] = []

    coarse_grid = _generate_coarse_grid()
    coarse_results = _evaluate_grid(coarse_grid, num_workers)
    for r in coarse_results:
        r["stage"] = "coarse"
    results.extend(coarse_results)
    _log_failure_summary(coarse_results, "coarse")

    if any(r.get("status") == "ok" for r in coarse_results):
        return results

    candidates = _select_refinement_candidates(coarse_results, refine_top_k)
    if not candidates:
        return results

    refined_grid = _generate_refined_grid(candidates, max_refine)
    refined_results = _evaluate_grid(refined_grid, num_workers)
    for r in refined_results:
        r["stage"] = "refine"
    results.extend(refined_results)
    _log_failure_summary(refined_results, "refine")

    return results


def pick_best_candidate(results: List[Dict]) -> Optional[Dict]:
    """Select best slow-roll candidate according to mean epsilon and e-folds."""
    candidates = [
        r for r in results if r.get("status") == "ok" and r.get("metrics")
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda r: (r["metrics"]["epsilon_mean"], -r["metrics"]["efolds"]),
    )


def write_outputs(scan_results: List[Dict], best: Dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

    # full scan report
    scan_path = RESULTS_DIR / "spectra_slow_roll_tuning.json"
    with scan_path.open("w", encoding="utf-8") as f:
        json.dump(scan_results, f, indent=2)

    if best:
        cfg = best["config"]
        metrics = best["metrics"]
        yaml_payload = {
            "background": {
                "m": cfg["m"],
                "beta": cfg["beta"],
                "omega_bar": cfg["omega_bar"],
                "rf_bar": cfg["rf_bar"],
                "hubble_constant": float(CONSTS.hubble_constant),
                "omega_m0": cfg["omega_m0"],
                "mass_scale": cfg["mass_scale"],
                "linear_scale": cfg["linear_scale"],
                "flat_amplitude": cfg["flat_amplitude"],
                "flat_width": cfg["flat_width"],
                "flat_center": cfg["flat_center"],
                "quartic_coeff": cfg["quartic_coeff"],
                "use_analytic_potential": cfg["use_analytic_potential"],
                "analytic_v0": cfg["analytic_v0"],
                "analytic_eps0": cfg["analytic_eps0"],
                "analytic_beta": cfg["analytic_beta"],
                "analytic_psiref": cfg["analytic_psiref"],
                "analytic_transition_amp": cfg["analytic_transition_amp"],
                "analytic_transition_width": cfg["analytic_transition_width"],
                "analytic_transition_center": cfg["analytic_transition_center"],
                "analytic_ramp_amp": cfg.get("analytic_ramp_amp", 0.0),
                "analytic_ramp_slope": cfg.get("analytic_ramp_slope", 0.0),
                "analytic_ramp_center": cfg.get("analytic_ramp_center", 0.0),
                "analytic_plateau_amp": cfg.get("analytic_plateau_amp", 0.0),
                "analytic_plateau_width": cfg.get("analytic_plateau_width", 1.0),
                "analytic_plateau_center": cfg.get("analytic_plateau_center", 0.0),
                "zmax": ZMAX_TUNING,
                "nsteps": NSTEPS_TUNING,
            },
            "initial_conditions": {
                "psi0": cfg["psi0"],
                "ppsi0": cfg.get("ppsi0", 0.0),
            },
            "k_targets_m_inv": [1e-17, 1e-16, 5e-15, 1e-13, 1e-11, 1e-9],
            "slow_roll_metrics": metrics,
        }
        cfg_path = CONFIGS_DIR / "spectra_slow_roll.yaml"
        with cfg_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_payload, f, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Adaptive slow-roll tuner for TE_1.C spectra.")
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Number of worker processes for background integrations (default: 1).",
    )
    parser.add_argument(
        "--refine-top-k",
        type=int,
        default=REFINE_TOP_K,
        help="How many coarse candidates to refine (default: %(default)s).",
    )
    parser.add_argument(
        "--max-refine",
        type=int,
        default=MAX_VARIANTS_PER_CANDIDATE,
        help="Maximum refinement variants per candidate (default: %(default)s).",
    )
    args = parser.parse_args()

    num_workers = max(args.num_workers, 1)
    refine_top_k = max(args.refine_top_k, 1)
    max_refine = max(args.max_refine, 0)

    print("== TE_1.C Slow-Roll Tuner ==")
    print(
        f"Workers={num_workers}, refine_top_k={refine_top_k}, "
        f"max_refine={max_refine}, coarse_grid={len(_generate_coarse_grid())}"
    )

    scan_results = scan_parameter_space(
        num_workers=num_workers,
        refine_top_k=refine_top_k,
        max_refine=max_refine,
    )
    best = pick_best_candidate(scan_results)
    write_outputs(scan_results, best)

    total = len(scan_results)
    ok_count = sum(1 for r in scan_results if r.get("status") == "ok")
    coarse_count = sum(1 for r in scan_results if r.get("stage") == "coarse")
    refine_count = sum(1 for r in scan_results if r.get("stage") == "refine")
    print(
        f"Scanned {total} configurations "
        f"(coarse={coarse_count}, refine={refine_count}); slow-roll candidates: {ok_count}"
    )
    if best:
        cfg = best["config"]
        metrics = best["metrics"]
        print("Best candidate:")
        print(
            f"  m={cfg['m']:.3e}, beta={cfg['beta']:.3e}, omega_bar={cfg['omega_bar']:.3e}, "
            f"rf_bar={cfg['rf_bar']:.3f}, mass_scale={cfg['mass_scale']:.1e}, "
            f"linear_scale={cfg['linear_scale']:.1e}, omega_m0={cfg['omega_m0']:.1e}, psi0={cfg['psi0']:.2f}"
        )
        print(
            f"  epsilon_mean={metrics['epsilon_mean']:.3e}, "
            f"efolds={metrics['efolds']:.2f}, "
            f"hubble_mean={metrics['hubble_mean']:.3e}"
        )
        print("Wrote configs/spectra_slow_roll.yaml")
    else:
        print("No viable slow-roll candidate found; see scan report for details.")


if __name__ == "__main__":
    main()

