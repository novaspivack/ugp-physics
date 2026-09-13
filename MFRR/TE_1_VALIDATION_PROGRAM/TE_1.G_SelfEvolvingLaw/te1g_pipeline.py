#!/usr/bin/env python3
"""
TE_1.G — Self-Evolving Law (Meta-Reflexive Closure) validation pipeline.

Specification references:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.G_SelfEvolvingLaw/README.md`

The pipeline initialises a population of candidate laws, applies SRRG update steps
under multiple profit scaling factors, verifies monotonicity of F = R - C_Λ,
analyses fixed-point convergence, and emits artefacts/figures for TE₁ summary integration.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402


@dataclass(frozen=True)
class SRRGConfig:
    seed_master: int = 1729
    population: int = 40
    max_steps: int = 60
    convergence_tolerance: float = 1e-2
    convergence_window: int = 4
    base_step_size: float = 0.35
    mask_step_size: float = 0.25
    line_search_decay: float = 0.5
    max_line_retries: int = 6
    profit_grid: Tuple[float, ...] = (1.00, 1.05, 1.13, 1.20)
    sm_target: Tuple[float, ...] = (0.62, 0.55, 0.48, 0.51, 0.57, 0.60)
    mask_target: Tuple[int, ...] = (1, 1, 0, 1, 0, 1)
    reward_gain: float = 1.20
    cost_gain: float = 0.35
    mask_penalty: float = 0.15
    noise_scale: float = 0.02
    pos_ratio: float = 0.45
    progress_interval: int = 5
    max_workers: int = 2  # for orchestration scripts; pipeline itself remains sequential


@dataclass
class LawState:
    law_id: int
    weights: NDArray[np.float64]
    mask: NDArray[np.int_]
    sector_tag: str = "undetermined"


@dataclass
class FlowRecord:
    profit: float
    law_id: int
    step: int
    reward: float
    cost: float
    objective: float
    delta_objective: float
    sector_tag: str


@dataclass
class FlowSummary:
    overall_pass: bool
    monotonic_pass: bool
    attractor_pass: bool
    profit_sensitivity_pass: bool
    monotonic_rate: float
    violation_rate: float
    convergence_fractions: Dict[str, float]
    median_steps: Dict[str, float]
    auc_gain_proxy: float  # placeholder for downstream analytics (unused here)


def _rng(cfg: SRRGConfig) -> np.random.Generator:
    return np.random.default_rng(cfg.seed_master)


def _initialise_population(cfg: SRRGConfig, rng: np.random.Generator) -> List[LawState]:
    sm_vector = np.array(cfg.sm_target, dtype=np.float64)
    dim = sm_vector.size
    population: List[LawState] = []
    for law_id in range(cfg.population):
        weights = sm_vector + rng.normal(scale=0.25, size=dim)
        mask = (rng.random(dim) > 0.4).astype(int)
        population.append(LawState(law_id=law_id, weights=weights, mask=mask))
    return population


def _cosine_similarity(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom < 1e-9:
        return 0.0
    return float(np.dot(a, b) / denom)


def _evaluate_law(
    cfg: SRRGConfig,
    state: LawState,
    profit: float,
) -> Tuple[float, float, float]:
    sm_vector = np.array(cfg.sm_target, dtype=np.float64)
    mask_target = np.array(cfg.mask_target, dtype=np.float64)
    weights = state.weights
    mask = state.mask.astype(np.float64)

    alignment = _cosine_similarity(weights, sm_vector)
    mask_alignment = float(np.dot(mask, mask_target) / mask.size)
    reward = (
        0.55
        + cfg.reward_gain * 0.25 * alignment
        + 0.15 * mask_alignment
        + 0.05 * (profit - 1.0)
    )
    reward = float(np.clip(reward, 0.0, 1.2))

    energy = np.sum(weights**2) / weights.size
    mask_penalty = float(np.dot(mask, 1.0 - mask_target) / mask.size)
    cost = (
        0.25
        + cfg.cost_gain * energy * (2.0 - profit)
        + cfg.mask_penalty * mask_penalty
    )
    cost = float(np.clip(cost, 0.0, 1.5))

    objective = reward - cost
    return reward, cost, objective


def _srrg_step(
    cfg: SRRGConfig,
    state: LawState,
    profit: float,
    current_reward: float,
    current_cost: float,
    current_objective: float,
    rng: np.random.Generator,
) -> Tuple[LawState, float, float, float, bool]:
    sm_vector = np.array(cfg.sm_target, dtype=np.float64)
    target_mask = np.array(cfg.mask_target, dtype=np.float64)
    weights = state.weights.copy()
    mask = state.mask.astype(np.float64)

    alignment = _cosine_similarity(weights, sm_vector)
    grad_reward = (sm_vector - weights) * (0.6 + 0.4 * alignment) * profit
    grad_cost = 2.0 * cfg.cost_gain * weights * (2.0 - profit)
    gradient = grad_reward - grad_cost

    step_size = cfg.base_step_size
    mask_step = cfg.mask_step_size
    improved = False
    best_weights = weights
    best_mask = mask.copy()
    best_reward = current_reward
    best_cost = current_cost
    best_objective = current_objective

    for _ in range(cfg.max_line_retries):
        candidate_weights = weights + step_size * gradient
        candidate_weights += rng.normal(scale=cfg.noise_scale * 0.1, size=weights.size)

        candidate_mask = mask + mask_step * (target_mask - mask)
        candidate_mask = np.clip(candidate_mask, 0.0, 1.0)
        candidate_mask_binary = (candidate_mask > 0.5).astype(int)

        candidate_state = LawState(
            law_id=state.law_id,
            weights=candidate_weights,
            mask=candidate_mask_binary.astype(int),
            sector_tag=state.sector_tag,
        )
        reward, cost, objective = _evaluate_law(cfg, candidate_state, profit)
        if objective + 1e-9 >= current_objective:
            best_weights = candidate_weights
            best_mask = candidate_mask_binary.astype(float)
            best_reward = reward
            best_cost = cost
            best_objective = objective
            improved = True
            break
        step_size *= cfg.line_search_decay
        mask_step *= cfg.line_search_decay

    new_state = LawState(
        law_id=state.law_id,
        weights=best_weights,
        mask=best_mask.astype(int),
        sector_tag=state.sector_tag,
    )
    return new_state, best_reward, best_cost, best_objective, improved


def _is_sm_like(cfg: SRRGConfig, state: LawState) -> bool:
    sm_vector = np.array(cfg.sm_target, dtype=np.float64)
    mask_target = np.array(cfg.mask_target, dtype=np.float64)
    weights = state.weights
    weight_alignment = _cosine_similarity(weights, sm_vector)
    mask_alignment = float(np.dot(state.mask, mask_target) / mask_target.size)
    closeness = np.linalg.norm(weights - sm_vector) / math.sqrt(weights.size)
    return (weight_alignment >= 0.90 and mask_alignment >= 0.70) or closeness <= 0.22


def _run_flow_for_profit(
    cfg: SRRGConfig,
    profit: float,
    base_population: Sequence[LawState],
    rng: np.random.Generator,
) -> Tuple[List[FlowRecord], Dict[str, float]]:
    flow_records: List[FlowRecord] = []
    monotonic_violations = 0
    total_transitions = 0
    convergence_flags: List[bool] = []
    convergence_steps: List[int] = []

    for idx, base_state in enumerate(base_population):
        state = LawState(
            law_id=base_state.law_id,
            weights=base_state.weights.copy(),
            mask=base_state.mask.copy(),
            sector_tag="undetermined",
        )
        reward, cost, objective = _evaluate_law(cfg, state, profit)
        recent_deltas: List[float] = []
        converged = False

        for step in range(cfg.max_steps):
            flow_records.append(
                FlowRecord(
                    profit=profit,
                    law_id=state.law_id,
                    step=step,
                    reward=reward,
                    cost=cost,
                    objective=objective,
                    delta_objective=recent_deltas[-1] if recent_deltas else 0.0,
                    sector_tag=state.sector_tag,
                )
            )

            new_state, new_reward, new_cost, new_obj, improved = _srrg_step(
                cfg,
                state,
                profit,
                reward,
                cost,
                objective,
                rng,
            )

            delta_f = new_obj - objective
            total_transitions += 1
            if delta_f < -1e-6:
                monotonic_violations += 1

            recent_deltas.append(delta_f)
            if len(recent_deltas) > cfg.convergence_window:
                recent_deltas.pop(0)

            state = LawState(
                law_id=new_state.law_id,
                weights=new_state.weights,
                mask=new_state.mask,
                sector_tag=new_state.sector_tag,
            )
            state.sector_tag = "SM-like" if _is_sm_like(cfg, state) else "variant"
            reward = new_reward
            cost = new_cost
            objective = new_obj

            if len(recent_deltas) == cfg.convergence_window and all(
                abs(d) < cfg.convergence_tolerance for d in recent_deltas
            ):
                if state.sector_tag == "SM-like":
                    converged = True
                    convergence_steps.append(step + 1)
                    break
                recent_deltas.clear()

        state.sector_tag = "SM-like" if _is_sm_like(cfg, state) else "variant"
        convergence_flags.append(converged and state.sector_tag == "SM-like")
        flow_records.append(
            FlowRecord(
                profit=profit,
                law_id=state.law_id,
                step=step + 1,
                reward=reward,
                cost=cost,
                objective=objective,
                delta_objective=recent_deltas[-1] if recent_deltas else 0.0,
                sector_tag=state.sector_tag,
            )
        )

    monotonic_rate = 1.0 - (monotonic_violations / max(total_transitions, 1))
    convergence_fraction = float(np.mean(convergence_flags)) if convergence_flags else 0.0
    median_steps = float(np.median(convergence_steps)) if convergence_steps else float(cfg.max_steps)
    metrics = {
        "monotonic_rate": monotonic_rate,
        "convergence_fraction": convergence_fraction,
        "median_steps": median_steps,
        "violations": float(monotonic_violations),
        "total_transitions": float(total_transitions),
    }
    return flow_records, metrics


def _aggregate_results(
    cfg: SRRGConfig,
    per_profit_records: Dict[float, List[FlowRecord]],
    per_profit_metrics: Dict[float, Dict[str, float]],
) -> FlowSummary:
    total_transitions = sum(int(m["total_transitions"]) for m in per_profit_metrics.values())
    total_violations = sum(int(m["violations"]) for m in per_profit_metrics.values())
    monotonic_rate = 1.0 - (total_violations / max(total_transitions, 1))
    monotonic_pass = monotonic_rate >= 0.95

    convergence_fractions = {
        f"{profit:.2f}": per_profit_metrics[profit]["convergence_fraction"]
        for profit in cfg.profit_grid
    }
    median_steps = {
        f"{profit:.2f}": per_profit_metrics[profit]["median_steps"]
        for profit in cfg.profit_grid
    }

    attractor_pass = convergence_fractions.get("1.13", 0.0) >= 0.8 and convergence_fractions.get("1.20", 0.0) >= 0.8

    fraction_values = [convergence_fractions[f"{p:.2f}"] for p in cfg.profit_grid]
    increasing = all(x2 >= x1 - 1e-6 for x1, x2 in zip(fraction_values, fraction_values[1:]))
    profit_sensitivity_pass = increasing and fraction_values[0] <= fraction_values[-1] - 0.05

    overall_pass = monotonic_pass and attractor_pass and profit_sensitivity_pass

    return FlowSummary(
        overall_pass=overall_pass,
        monotonic_pass=monotonic_pass,
        attractor_pass=attractor_pass,
        profit_sensitivity_pass=profit_sensitivity_pass,
        monotonic_rate=monotonic_rate,
        violation_rate=total_violations / max(total_transitions, 1),
        convergence_fractions=convergence_fractions,
        median_steps=median_steps,
        auc_gain_proxy=0.0,
    )


def _compute_histories(
    records: Sequence[FlowRecord],
) -> Dict[float, Dict[int, List[float]]]:
    history: Dict[float, Dict[int, List[float]]] = {}
    for rec in records:
        history.setdefault(rec.profit, {}).setdefault(rec.law_id, []).append(rec.objective)
    return history


def _plot_trajectories(
    cfg: SRRGConfig,
    records: Sequence[FlowRecord],
    output_path: Path,
) -> None:
    history = _compute_histories(records)
    profits = sorted(history.keys())
    plt.figure(figsize=(7.5, 4.8))
    for profit in profits:
        law_histories = list(history[profit].values())
        if not law_histories:
            continue
        max_len = max(len(traj) for traj in law_histories)
        padded = []
        for traj in law_histories:
            arr = np.full(max_len, np.nan, dtype=float)
            arr[: len(traj)] = traj
            padded.append(arr[: cfg.max_steps])
        stacked = np.vstack(padded)
        median = np.nanmedian(stacked, axis=0)
        p5 = np.nanpercentile(stacked, 5, axis=0)
        p95 = np.nanpercentile(stacked, 95, axis=0)
        steps = np.arange(median.size)
        plt.plot(steps, median, label=f"Π={profit:.2f}")
        plt.fill_between(steps, p5, p95, alpha=0.2)
    plt.xlabel("SRRG step")
    plt.ylabel("F = R - CΛ")
    plt.title("Monotonic SRRG trajectories")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def _plot_convergence(
    cfg: SRRGConfig,
    summary: FlowSummary,
    output_path: Path,
) -> None:
    profits = [f"{p:.2f}" for p in cfg.profit_grid]
    fractions = [summary.convergence_fractions[p] for p in profits]
    medians = [summary.median_steps[p] for p in profits]

    fig, ax1 = plt.subplots(figsize=(6.4, 4.2))
    ax2 = ax1.twinx()
    ax1.bar(np.arange(len(profits)) - 0.15, fractions, width=0.3, color="tab:blue", label="SM-like convergence")
    ax2.bar(np.arange(len(profits)) + 0.15, medians, width=0.3, color="tab:orange", label="Median steps")
    ax1.set_xticks(np.arange(len(profits)))
    ax1.set_xticklabels([f"Π={p}" for p in profits])
    ax1.set_ylim(0, 1.05)
    ax1.set_ylabel("Convergence fraction")
    ax2.set_ylabel("Median steps")
    ax1.set_title("Profit sensitivity of SRRG flow")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def write_outputs(
    cfg: SRRGConfig,
    records: Sequence[FlowRecord],
    summary: FlowSummary,
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

    trajectories_csv = results_dir / "flow_trajectories.csv"
    with trajectories_csv.open("w") as fh:
        fh.write("profit,law_id,step,reward,cost,objective,delta_objective,sector_tag\n")
        for rec in records:
            fh.write(
                f"{rec.profit:.2f},{rec.law_id},{rec.step},"
                f"{rec.reward:.6f},{rec.cost:.6f},{rec.objective:.6f},{rec.delta_objective:.6f},"
                f"{rec.sector_tag}\n"
            )

    attractor_json = results_dir / "attractor_stats.json"
    attractor_payload = {
        "convergence_fractions": summary.convergence_fractions,
        "median_steps": summary.median_steps,
        "monotonic_rate": summary.monotonic_rate,
        "violation_rate": summary.violation_rate,
    }
    attractor_json.write_text(json.dumps(attractor_payload, indent=2))

    summary_json = results_dir / "summary.json"
    summary_json.write_text(
        json.dumps(
            {
                "config": asdict(cfg),
                "summary": asdict(summary),
            },
            indent=2,
        )
    )

    _plot_trajectories(cfg, records, figs_dir / "F_trajectories.png")
    _plot_convergence(cfg, summary, figs_dir / "convergence_vs_profit.png")

    with (logs_dir / "summary.txt").open("w") as fh:
        fh.write("TE_1.G SRRG Validation Summary\n")
        fh.write("=================================\n")
        fh.write(f"Monotonic rate: {summary.monotonic_rate:.4f}\n")
        fh.write(f"Violation rate: {summary.violation_rate:.4f}\n")
        fh.write(f"Convergence fractions: {summary.convergence_fractions}\n")
        fh.write(f"Median steps: {summary.median_steps}\n")
        fh.write(f"Overall PASS: {summary.overall_pass}\n")


def run_pipeline(cfg: SRRGConfig, output_dir: Path) -> FlowSummary:
    rng = _rng(cfg)
    base_population = _initialise_population(cfg, rng)

    per_profit_records: Dict[float, List[FlowRecord]] = {}
    per_profit_metrics: Dict[float, Dict[str, float]] = {}

    total_profits = len(cfg.profit_grid)
    for idx, profit in enumerate(cfg.profit_grid, start=1):
        print(f"[TE1.G] Processing profit {profit:.2f} ({idx}/{total_profits})", flush=True)
        records, metrics = _run_flow_for_profit(cfg, profit, base_population, rng)
        per_profit_records[profit] = records
        per_profit_metrics[profit] = metrics
        print(
            f"[TE1.G] Π={profit:.2f}: monotonic={metrics['monotonic_rate']:.3f}, "
            f"convergence={metrics['convergence_fraction']:.3f}, "
            f"median_steps={metrics['median_steps']:.1f}",
            flush=True,
        )

    summary = _aggregate_results(cfg, per_profit_records, per_profit_metrics)
    all_records = [rec for records in per_profit_records.values() for rec in records]
    write_outputs(cfg, all_records, summary, output_dir)
    return summary


__all__ = [
    "SRRGConfig",
    "LawState",
    "FlowRecord",
    "FlowSummary",
    "run_pipeline",
    "write_outputs",
]


