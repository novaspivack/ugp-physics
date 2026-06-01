#!/usr/bin/env python3
"""
TE_1.L — Reflexive Adjudication Cosmology validation pipeline.

Specification references:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.L_REFLEXIVE_ADJUDICATION_COSMOLOGY/TE_1.L_KICKOFF.md`

This module simulates reduced reflexive-transducer dynamics to illustrate the
three adjudicative regimes (absorptive/black-hole-like, reflexive transducer,
emissive/white-hole-like). It verifies flux balance, entropy balance, and
profit-driven sensitivity, and writes artefacts for TE₁ documentation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402


@dataclass(frozen=True)
class ReflexiveConfig:
    seed_master: int = 1729
    profit_grid: Tuple[float, ...] = (0.95, 1.00, 1.08, 1.13, 1.20)
    simulations_per_profit: int = 24
    time_steps: int = 240
    convergence_window: int = 6
    dt: float = 0.12
    coherence_gain: float = 1.25
    coherence_decay: float = 0.45
    entropy_coupling: float = 0.06
    base_flux_in: float = 0.38
    base_flux_out: float = 0.33
    flux_gain: float = 0.42
    flux_out_gain: float = 0.20
    flux_profit_coupling: float = 0.12
    noise_scale: float = 0.01
    convergence_fraction_threshold: float = 0.8
    flux_balance_tolerance: float = 0.035
    progress_interval: int = 5


@dataclass
class TransducerState:
    coherence: float
    internal_entropy: float
    external_entropy: float
    flux_in: float
    flux_out: float


@dataclass
class SimulationResult:
    profit: float
    flux_balance: float
    entropy_balance: float
    regime: str
    mean_coherence: float
    steps_to_equilibrium: int


@dataclass
class SummaryMetrics:
    overall_pass: bool
    flux_balance_pass: bool
    entropy_balance_pass: bool
    profit_sensitivity_pass: bool
    reflexive_fraction_1p13: float
    reflexive_fraction_1p20: float
    balance_statistics: Dict[str, float]


def _rng(cfg: ReflexiveConfig) -> np.random.Generator:
    return np.random.default_rng(cfg.seed_master)


def _initial_state(rng: np.random.Generator) -> TransducerState:
    coherence = rng.uniform(0.05, 0.35)
    internal_entropy = rng.uniform(0.25, 0.45)
    external_entropy = 1.0 - internal_entropy
    return TransducerState(
        coherence=coherence,
        internal_entropy=internal_entropy,
        external_entropy=external_entropy,
        flux_in=0.0,
        flux_out=0.0,
    )


def _update_state(
    cfg: ReflexiveConfig,
    state: TransducerState,
    profit: float,
    rng: np.random.Generator,
) -> TransducerState:
    # Flux calculations: absorbing regime emphasises inflow, emitting emphasises outflow.
    flux_in = (
        cfg.base_flux_in
        + cfg.flux_gain * (1.0 - state.coherence)
        + 0.18 * (1.0 - profit)
        + 0.12 * (0.3 - state.internal_entropy)
        + cfg.noise_scale * rng.normal()
    )
    flux_out = (
        cfg.base_flux_out
        + cfg.flux_out_gain * state.coherence
        + cfg.flux_profit_coupling * (profit - 1.0)
        + cfg.noise_scale * rng.normal()
    )

    # Coherence dynamics: gain drives coherence toward unity near reflexive balance.
    delta_coherence = (
        cfg.dt
        * (
            cfg.coherence_gain * profit * (1.0 - state.coherence)
            - cfg.coherence_decay * state.coherence
            - 0.35 * max(flux_out - flux_in, 0.0)
        )
    )
    coherence = float(np.clip(state.coherence + delta_coherence, 0.0, 1.0))

    # Entropy balance: internal decreases when coherence rises, increases when absorbing heat.
    delta_entropy = cfg.dt * (
        -cfg.entropy_coupling * coherence
        + 0.15 * (flux_in - flux_out)
    )
    internal_entropy = float(np.clip(state.internal_entropy + delta_entropy, 0.05, 0.95))
    external_entropy = float(np.clip(state.external_entropy - delta_entropy, 0.05, 0.95))

    return TransducerState(
        coherence=coherence,
        internal_entropy=internal_entropy,
        external_entropy=external_entropy,
        flux_in=flux_in,
        flux_out=flux_out,
    )


def _classify_regime(cfg: ReflexiveConfig, balances: NDArray[np.float64]) -> str:
    mean_balance = float(np.mean(balances))
    if abs(mean_balance) <= cfg.flux_balance_tolerance:
        return "reflexive_transducer"
    if mean_balance > 0:
        return "absorptive"
    return "emissive"


def _simulate_single(
    cfg: ReflexiveConfig,
    profit: float,
    rng: np.random.Generator,
) -> SimulationResult:
    state = _initial_state(rng)
    flux_balances: List[float] = []
    entropy_balances: List[float] = []
    coherence_history: List[float] = []
    equilibrium_step = cfg.time_steps

    for step in range(cfg.time_steps):
        state = _update_state(cfg, state, profit, rng)
        flux_balances.append(state.flux_in - state.flux_out)
        entropy_balances.append(state.internal_entropy + state.external_entropy)
        coherence_history.append(state.coherence)

        if step >= cfg.convergence_window:
            window_balances = flux_balances[-cfg.convergence_window :]
            if (
                max(abs(b) for b in window_balances) <= cfg.flux_balance_tolerance
                and equilibrium_step == cfg.time_steps
            ):
                equilibrium_step = step

    final_window = slice(int(cfg.time_steps * 0.6), cfg.time_steps)
    mean_flux_balance = float(np.mean(np.array(flux_balances)[final_window]))
    final_entropy_balance = float(np.mean(np.array(entropy_balances)[final_window]))
    regime = _classify_regime(cfg, np.array(flux_balances)[final_window])
    mean_coherence = float(np.mean(np.array(coherence_history)[final_window]))

    return SimulationResult(
        profit=profit,
        flux_balance=mean_flux_balance,
        entropy_balance=final_entropy_balance,
        regime=regime,
        mean_coherence=mean_coherence,
        steps_to_equilibrium=equilibrium_step,
    )


def run_simulations(cfg: ReflexiveConfig) -> List[SimulationResult]:
    rng = _rng(cfg)
    results: List[SimulationResult] = []
    total_jobs = cfg.simulations_per_profit * len(cfg.profit_grid)
    completed = 0
    for profit in cfg.profit_grid:
        for _ in range(cfg.simulations_per_profit):
            res = _simulate_single(cfg, profit, rng)
            results.append(res)
            completed += 1
            if completed % cfg.progress_interval == 0 or completed == total_jobs:
                pct = 100.0 * completed / total_jobs
                print(f"[TE1.L] progress {completed}/{total_jobs} ({pct:.1f}%)", flush=True)
    return results


def compute_summary(cfg: ReflexiveConfig, results: Sequence[SimulationResult]) -> SummaryMetrics:
    flux_balances = np.array([r.flux_balance for r in results])
    entropy_balances = np.array([r.entropy_balance for r in results])

    flux_balance_pass = float(np.max(np.abs(flux_balances))) <= 0.12
    entropy_balance_pass = float(np.max(np.abs(entropy_balances - 1.0))) <= 0.05

    convergence_by_profit: Dict[str, float] = {}
    for profit in cfg.profit_grid:
        mask = [r for r in results if abs(r.profit - profit) < 1e-9]
        if not mask:
            convergence_by_profit[f"{profit:.2f}"] = 0.0
            continue
        reflexive_count = sum(1 for r in mask if r.regime == "reflexive_transducer")
        convergence_by_profit[f"{profit:.2f}"] = reflexive_count / len(mask)

    reflexive_fraction_113 = convergence_by_profit.get("1.13", 0.0)
    reflexive_fraction_120 = convergence_by_profit.get("1.20", 0.0)
    profit_sensitivity_pass = (
        reflexive_fraction_113 >= cfg.convergence_fraction_threshold
        and reflexive_fraction_120 >= cfg.convergence_fraction_threshold
        and convergence_by_profit.get("1.00", 0.0) < 0.2
    )

    overall_pass = flux_balance_pass and entropy_balance_pass and profit_sensitivity_pass

    balance_statistics = {
        "mean_flux_balance": float(np.mean(flux_balances)),
        "std_flux_balance": float(np.std(flux_balances)),
        "max_abs_flux_balance": float(np.max(np.abs(flux_balances))),
        "entropy_mean": float(np.mean(entropy_balances)),
        "entropy_std": float(np.std(entropy_balances)),
    }

    return SummaryMetrics(
        overall_pass=overall_pass,
        flux_balance_pass=flux_balance_pass,
        entropy_balance_pass=entropy_balance_pass,
        profit_sensitivity_pass=profit_sensitivity_pass,
        reflexive_fraction_1p13=reflexive_fraction_113,
        reflexive_fraction_1p20=reflexive_fraction_120,
        balance_statistics=balance_statistics,
    )


def _plot_flux_balance(
    cfg: ReflexiveConfig,
    results: Sequence[SimulationResult],
    output_path: Path,
) -> None:
    profits = [float(f"{p:.2f}") for p in cfg.profit_grid]
    balances = []
    regimes = []
    for profit in cfg.profit_grid:
        subset = [r for r in results if abs(r.profit - profit) < 1e-9]
        balances.append(np.mean([r.flux_balance for r in subset]))
        regimes.append(subset)

    plt.figure(figsize=(6.4, 4.2))
    plt.axhline(0.0, color="gray", linestyle="--", linewidth=1.0)
    plt.plot(profits, balances, marker="o")
    plt.xlabel("Profit Π")
    plt.ylabel("Mean flux balance (in - out)")
    plt.title("Flux balance across profit regimes")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def _plot_coherence(
    cfg: ReflexiveConfig,
    results: Sequence[SimulationResult],
    output_path: Path,
) -> None:
    profits = [float(f"{p:.2f}") for p in cfg.profit_grid]
    coherence_means = []
    for profit in cfg.profit_grid:
        subset = [r for r in results if abs(r.profit - profit) < 1e-9]
        coherence_means.append(np.mean([r.mean_coherence for r in subset]))

    plt.figure(figsize=(6.4, 4.2))
    plt.plot(profits, coherence_means, marker="s", color="tab:purple")
    plt.xlabel("Profit Π")
    plt.ylabel("Mean coherence")
    plt.title("Coherence vs profit")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def write_outputs(
    cfg: ReflexiveConfig,
    results: Sequence[SimulationResult],
    summary: SummaryMetrics,
    output_dir: Path,
) -> None:
    results_dir = output_dir / "results"
    figs_dir = output_dir / "figs"
    logs_dir = output_dir / "logs"
    data_dir = output_dir / "data"

    results_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    with (results_dir / "flux_balance.csv").open("w") as fh:
        fh.write("profit,flux_balance,entropy_balance,regime,mean_coherence,steps_to_equilibrium\n")
        for res in results:
            fh.write(
                f"{res.profit:.2f},{res.flux_balance:.6f},{res.entropy_balance:.6f},"
                f"{res.regime},{res.mean_coherence:.6f},{res.steps_to_equilibrium}\n"
            )

    summary_path = results_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "config": asdict(cfg),
                "summary": asdict(summary),
            },
            indent=2,
        )
    )

    _plot_flux_balance(cfg, results, figs_dir / "flux_balance_vs_profit.png")
    _plot_coherence(cfg, results, figs_dir / "coherence_vs_profit.png")

    with (logs_dir / "summary.txt").open("w") as fh:
        fh.write("TE_1.L Reflexive Transducer Validation\n")
        fh.write("=====================================\n")
        fh.write(f"Overall PASS: {summary.overall_pass}\n")
        fh.write(f"Flux balance PASS: {summary.flux_balance_pass}\n")
        fh.write(f"Entropy balance PASS: {summary.entropy_balance_pass}\n")
        fh.write(f"Profit sensitivity PASS: {summary.profit_sensitivity_pass}\n")
        fh.write(f"Reflexive fraction Π=1.13: {summary.reflexive_fraction_1p13:.3f}\n")
        fh.write(f"Reflexive fraction Π=1.20: {summary.reflexive_fraction_1p20:.3f}\n")
        fh.write(f"Balance statistics: {summary.balance_statistics}\n")


def run_pipeline(cfg: ReflexiveConfig, output_dir: Path) -> SummaryMetrics:
    results = run_simulations(cfg)
    summary = compute_summary(cfg, results)
    write_outputs(cfg, results, summary, output_dir)
    return summary


__all__ = [
    "ReflexiveConfig",
    "SimulationResult",
    "SummaryMetrics",
    "run_pipeline",
]


