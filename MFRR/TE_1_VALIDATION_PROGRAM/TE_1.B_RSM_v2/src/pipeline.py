"""Experiment pipeline for TE₁.B_v2 minimal reflexive statistical mechanics.

Specification: docs/TE1B_Minimal_RSM_Spec.md
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np

from .analysis import (
    bootstrap_ci,
    estimate_crooks_slope,
    finite_difference_response,
    green_kubo_integral,
    jarzynski_statistic,
)
from .controller import ControllerConfig, ReflexiveController
from .minimal_rsm import ReflexiveChain, build_default_chain
from .simulator import ChainFactory, EnsembleConfig, run_ensembles


@dataclass
class GreenKuboConfig:
    mu0: float
    delta_mu: float
    steps: int
    burn_in: int
    observable_state: str = "S1"
    start_state: str = "S0"


@dataclass
class ExperimentConfig:
    controller: ControllerConfig
    calibration: EnsembleConfig
    production: EnsembleConfig
    green_kubo: GreenKuboConfig
    chain_factory: ChainFactory = build_default_chain
    max_calibration_steps: int = 64
    results_root: Path = Path("results")


@dataclass
class ExperimentResult:
    results_dir: Path
    jarzynski: Dict[str, float]
    crooks: Dict[str, float]
    green_kubo: Dict[str, float]
    controller_history: List[Dict[str, float]]
    parameters: Dict[str, float]


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    results_dir = _create_results_dir(config.results_root)
    chain = config.chain_factory(
        config.calibration.forward_mu,
        config.calibration.intensity_alpha,
        config.calibration.reverse_bias_beta,
        seed=None,
    )
    controller = ReflexiveController(config.controller, chain)
    history = _calibrate_controller(controller, config)
    alpha_final, beta_final = controller.parameters

    production_cfg = replace(
        config.production,
        intensity_alpha=alpha_final,
        reverse_bias_beta=beta_final,
    )
    forward_samples, reverse_samples = run_ensembles(production_cfg, config.chain_factory)

    jarz_value = jarzynski_statistic(forward_samples)
    jarz_ci_low, jarz_ci_high = bootstrap_ci(forward_samples, jarzynski_statistic)
    jarz_residual = float(np.log(jarz_value)) if jarz_value > 0 else float("nan")

    crooks_fit = estimate_crooks_slope(forward_samples, reverse_samples)

    gk_metrics = _compute_green_kubo(config.green_kubo, config.chain_factory, alpha_final, beta_final)

    summary = {
        "parameters": {
            "alpha_final": alpha_final,
            "beta_final": beta_final,
        },
        "jarzynski": {
            "value": jarz_value,
            "residual": jarz_residual,
            "ci_low": jarz_ci_low,
            "ci_high": jarz_ci_high,
        },
        "crooks": {
            "slope": crooks_fit.slope,
            "intercept": crooks_fit.intercept,
            "status": crooks_fit.status,
        },
        "green_kubo": gk_metrics,
        "controller_history": history,
    }
    _write_results(results_dir, summary, forward_samples, reverse_samples)
    return ExperimentResult(
        results_dir=results_dir,
        jarzynski=summary["jarzynski"],
        crooks=summary["crooks"],
        green_kubo=summary["green_kubo"],
        controller_history=history,
        parameters=summary["parameters"],
    )


def _calibrate_controller(controller: ReflexiveController, config: ExperimentConfig) -> List[Dict[str, float]]:
    history: List[Dict[str, float]] = []
    for step in range(config.max_calibration_steps):
        alpha, beta = controller.parameters
        cal_cfg = replace(
            config.calibration,
            intensity_alpha=alpha,
            reverse_bias_beta=beta,
        )
        forward_samples, reverse_samples = run_ensembles(cal_cfg, config.chain_factory)
        jarz = jarzynski_statistic(forward_samples)
        residual = float(np.log(jarz)) if jarz > 0 else float("nan")
        crooks_fit = estimate_crooks_slope(forward_samples, reverse_samples)
        controller.update(residual, crooks_fit.slope)
        alpha_new, beta_new = controller.parameters
        history.append(
            {
                "step": float(step),
                "jarzynski": jarz,
                "residual": residual,
                "crooks_slope": crooks_fit.slope,
                "alpha": alpha_new,
                "beta": beta_new,
            }
        )
        if controller.frozen():
            break
    else:
        print("[warning] controller did not reach steady tolerances within max steps")
    return history


def _compute_green_kubo(cfg: GreenKuboConfig, factory: ChainFactory, alpha: float, beta: float) -> Dict[str, float]:
    base_series = _simulate_observable(factory, cfg.mu0, alpha, beta, cfg.start_state, cfg.observable_state, cfg.steps, cfg.burn_in)
    chi_gk = green_kubo_integral(base_series)
    mean_plus = float(np.mean(_simulate_observable(factory, cfg.mu0 + cfg.delta_mu, alpha, beta, cfg.start_state, cfg.observable_state, cfg.steps, cfg.burn_in)))
    mean_minus = float(np.mean(_simulate_observable(factory, cfg.mu0 - cfg.delta_mu, alpha, beta, cfg.start_state, cfg.observable_state, cfg.steps, cfg.burn_in)))
    chi_fd = finite_difference_response(mean_plus, mean_minus, cfg.delta_mu)
    return {
        "chi_gk": chi_gk,
        "chi_fd": chi_fd,
        "mean_plus": mean_plus,
        "mean_minus": mean_minus,
    }


def _simulate_observable(
    factory: ChainFactory,
    mu: float,
    alpha: float,
    beta: float,
    start_state: str,
    observable_state: str,
    steps: int,
    burn_in: int,
    seed: int | None = None,
) -> np.ndarray:
    chain = factory(mu, alpha, beta, seed)
    state = start_state
    values: List[float] = []
    for _ in range(burn_in):
        state, _ = chain.step(state)
    for _ in range(steps):
        state, _ = chain.step(state)
        values.append(1.0 if state == observable_state else 0.0)
    return np.asarray(values, dtype=np.float64)


def _create_results_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = root / f"te1b_v2_{timestamp}"
    path.mkdir(parents=True, exist_ok=True)
    (path / "data").mkdir(exist_ok=True)
    return path


def _write_results(results_dir: Path, summary: Dict, forward: np.ndarray, reverse: np.ndarray) -> None:
    summary_path = results_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    np.savez(results_dir / "data" / "samples.npz", forward=forward, reverse=reverse)
