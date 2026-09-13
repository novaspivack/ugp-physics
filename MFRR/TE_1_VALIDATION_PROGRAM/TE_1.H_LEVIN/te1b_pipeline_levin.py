"""
TE_1.H Levin variant of the TE_1.B reflexive statistical mechanics pipeline.

Adds Levin-style coherence diagnostics while preserving the original TE_1.B
implementation. The code mirrors `TE_1.B_RSM.te1b_pipeline` but augments the
result saver with compression-based coherence metrics that can be compared
against the adaptive simulations.

Reference session log:
`TE_1_VALIDATION_PROGRAM/SESSIONS/1_6_TE_1H_LEVIN_INFORMATION_PROFIT_STUDY.md`
"""

from __future__ import annotations

import concurrent.futures
import statistics
import zlib
from dataclasses import asdict
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

_THIS_FILE = Path(__file__).resolve()
_TE1_VALIDATION_ROOT = _THIS_FILE.parents[1]
_TE1B_DIR = _TE1_VALIDATION_ROOT / "TE_1.B_RSM"
if str(_TE1B_DIR) not in sys.path:
    sys.path.append(str(_TE1B_DIR))

from te1b_pipeline import (
    CrooksEntry,
    FrozenParameterSet,
    FrozenParameterTable,
    GreenKuboEntry,
    JarzynskiEntry,
    LargeDeviationEntry,
    ReflexiveControllerConfig,
    SimulationConfig,
    SusceptibilityEntry,
    TrajectoryRecord,
    aggregate_statistics,
)
import te1b_pipeline as base


def _series_coherence(series: Iterable[float]) -> float:
    """Approximate coherence via compression of a normalized series."""
    arr = np.asarray(series, dtype=np.float64)
    if arr.size == 0:
        return 1.0
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    max_val = float(np.max(arr))
    min_val = float(np.min(arr))
    if not np.isfinite(max_val) or not np.isfinite(min_val):
        return 0.0
    if max_val == min_val:
        return 1.0
    normalized = ((arr - min_val) / max(max_val - min_val, 1e-12) * 255).astype(np.uint8)
    if normalized.nbytes == 0:
        return 1.0
    compressed = zlib.compress(normalized.tobytes(), level=9)
    compression_ratio = len(compressed) / normalized.nbytes
    return float(np.clip(1.0 - compression_ratio, 0.0, 1.0))


def _summarize_coherence(records: List[TrajectoryRecord]) -> Tuple[List[List], Dict[str, float]]:
    rows: List[List] = []
    delta_coherences: List[float] = []
    rate_coherences: List[float] = []
    omega_coherences: List[float] = []

    for rec in records:
        coh_delta = _series_coherence(rec.delta_s_series)
        coh_rate = _series_coherence(rec.rate_series)
        coh_omega = _series_coherence(rec.omega_series)
        rows.append(
            [
                rec.temperature,
                rec.mu,
                rec.sigma,
                rec.seed,
                coh_delta,
                coh_rate,
                coh_omega,
            ]
        )
        delta_coherences.append(coh_delta)
        rate_coherences.append(coh_rate)
        omega_coherences.append(coh_omega)

    stats: Dict[str, float] = {}
    if delta_coherences:
        stats["levin_coherence_delta_s_mean"] = statistics.fmean(delta_coherences)
        stats["levin_coherence_delta_s_stdev"] = statistics.pstdev(delta_coherences)
    if rate_coherences:
        stats["levin_coherence_rate_mean"] = statistics.fmean(rate_coherences)
        stats["levin_coherence_rate_stdev"] = statistics.pstdev(rate_coherences)
    if omega_coherences:
        stats["levin_coherence_omega_mean"] = statistics.fmean(omega_coherences)
        stats["levin_coherence_omega_stdev"] = statistics.pstdev(omega_coherences)

    return rows, stats


def save_results(
    output_dir: Path,
    config: SimulationConfig,
    jarzynski: List[JarzynskiEntry],
    crooks: List[CrooksEntry],
    green_kubo: List[GreenKuboEntry],
    suscept: List[SusceptibilityEntry],
    ld_entries: List[LargeDeviationEntry],
    records: List[TrajectoryRecord],
) -> Dict[str, bool]:
    results_dir = output_dir / "results"
    figs_dir = output_dir / "figs"
    results_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    base._save_json(
        results_dir / "jarzynski.json",
        [asdict(entry) for entry in jarzynski],
    )

    base._save_csv(
        results_dir / "crooks.csv",
        ["temperature", "sigma", "slope", "slope_ci_low", "slope_ci_high", "passed"],
        [[c.temperature, c.sigma, c.slope, c.slope_ci_low, c.slope_ci_high, int(c.passed)] for c in crooks],
    )

    base._save_csv(
        results_dir / "green_kubo.csv",
        ["temperature", "sigma", "chi_gk", "chi_fd", "relative_error", "passed"],
        [[g.temperature, g.sigma, g.chi_gk, g.chi_fd, g.relative_error, int(g.passed)] for g in green_kubo],
    )

    base._save_csv(
        results_dir / "susceptibility_scan.csv",
        ["temperature", "sigma", "chi_omega", "omega_mean"],
        [[s.temperature, s.sigma, s.chi_omega, s.omega_mean] for s in suscept],
    )

    ld_payload = []
    for entry in ld_entries:
        ld_payload.append(
            {
                "temperature": entry.temperature,
                "sigma": entry.sigma,
                "n_values": entry.n_values.tolist(),
                "rate_function": entry.rate_function.tolist(),
                "convex": entry.convex,
            }
        )
    base._save_json(results_dir / "large_deviation.json", ld_payload)

    base._render_figures(figs_dir, jarzynski, crooks, suscept, ld_entries, records)

    summary: Dict[str, float] = {
        "jarzynski_pass": all(entry.passed for entry in jarzynski) if jarzynski else False,
        "crooks_pass": all(entry.passed for entry in crooks) if crooks else False,
        "green_kubo_pass": all(entry.passed for entry in green_kubo) if green_kubo else False,
        "susceptibility_peak_identified": bool(suscept),
        "large_deviation_convex": all(entry.convex for entry in ld_entries) if ld_entries else False,
        "phase": config.phase,
    }

    control_rows: List[List] = []
    for rec in records:
        if not rec.control_log:
            continue
        for entry in rec.control_log:
            control_rows.append(
                [
                    rec.temperature,
                    rec.mu,
                    rec.sigma,
                    rec.seed,
                    entry.window_index,
                    entry.start_step,
                    entry.end_step,
                    entry.cp_scale,
                    entry.delta_gain,
                    entry.reverse_fraction,
                    entry.jarzynski_value if entry.jarzynski_value is not None else "",
                    entry.crooks_slope if entry.crooks_slope is not None else "",
                    entry.green_kubo_error if entry.green_kubo_error is not None else "",
                    int(entry.adjustments_applied),
                ]
            )

    if control_rows:
        base._save_csv(
            results_dir / "reflexive_control_log.csv",
            [
                "temperature",
                "mu",
                "sigma",
                "seed",
                "window_index",
                "start_step",
                "end_step",
                "cp_scale",
                "delta_gain",
                "reverse_fraction",
                "jarzynski_value",
                "crooks_slope",
                "green_kubo_error",
                "adjustments_applied",
            ],
            control_rows,
        )
        summary["reflexive_control_log_file"] = str((results_dir / "reflexive_control_log.csv").resolve())

    param_rows, stationarity_fraction, param_table = base._summarize_reflexive_parameters(config, records)
    if param_rows:
        param_path = results_dir / "reflexive_parameters.csv"
        base._save_csv(
            param_path,
            [
                "temperature",
                "mu",
                "sigma",
                "cp_scale",
                "delta_gain",
                "reverse_fraction",
                "stationary_fraction",
                "trajectory_count",
            ],
            param_rows,
        )
        summary["reflexive_parameter_file"] = str(param_path.resolve())
        summary["reflexive_stationary_fraction"] = stationarity_fraction
        if config.phase == "adapt":
            config.frozen_parameter_table = param_table
    else:
        summary["reflexive_stationary_fraction"] = 0.0

    if config.frozen_parameter_table is not None:
        frozen_serializable = {
            f"{key[0]}|{key[1]}|{key[2]}": asdict(value)
            for key, value in config.frozen_parameter_table.items()
        }
    else:
        frozen_serializable = None

    coherence_rows, coherence_stats = _summarize_coherence(records)
    if coherence_rows:
        base._save_csv(
            results_dir / "levin_coherence.csv",
            [
                "temperature",
                "mu",
                "sigma",
                "seed",
                "delta_s_coherence",
                "rate_coherence",
                "omega_coherence",
            ],
            coherence_rows,
        )
        summary["levin_coherence_table"] = str((results_dir / "levin_coherence.csv").resolve())
        summary.update(coherence_stats)

    config_dict = asdict(config)
    config_dict["frozen_parameter_table"] = frozen_serializable

    base._save_json(results_dir / "summary.json", summary)
    base._save_json(results_dir / "config.json", config_dict)

    data_dir = output_dir / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    np.savez_compressed(
        data_dir / "trajectories.npz",
        temperature=np.array([r.temperature for r in records]),
        mu=np.array([r.mu for r in records]),
        sigma=np.array([r.sigma for r in records]),
        seed=np.array([r.seed for r in records], dtype=np.int64),
        delta_s_total=np.array([r.delta_s_total for r in records]),
        n_pt_total=np.array([r.n_pt_total for r in records]),
    )

    return summary


def run_validation(config: SimulationConfig, output_dir: Path, max_workers: int = 9) -> Dict[str, bool]:
    if config.phase == "calibration":
        config.calibration = True
    if config.phase == "adapt":
        config.reflexive.enabled = True
        config.calibration = False
    if config.phase == "frozen":
        config.reflexive.enabled = False
        config.calibration = False
        if config.frozen_parameter_table is None:
            raise ValueError("Frozen phase requires frozen_parameter_table.")

    if config.calibration:
        config.warmup_steps = min(config.warmup_steps, 1500)
        config.total_steps = min(config.total_steps, 2200)
        config.sample_stride = max(config.sample_stride, 8)
        config.trajectories_per_setting = min(config.trajectories_per_setting, 20)

    temperatures = config.temperatures if not config.calibration else (config.temperatures[0],)
    chemical_potentials = (
        config.chemical_potentials
        if not config.calibration
        else (config.chemical_potentials[len(config.chemical_potentials) // 2],)
    )
    sigma_values = (
        config.sigma_values if not config.calibration else (config.sigma_values[len(config.sigma_values) // 2],)
    )

    tasks: List[Tuple[float, float, float, int]] = []
    seed_seq = np.random.SeedSequence(config.rng_seed)
    num_settings = len(temperatures) * len(chemical_potentials) * len(sigma_values) * config.trajectories_per_setting
    child_seeds = seed_seq.spawn(num_settings)

    idx = 0
    for temp in temperatures:
        for mu in chemical_potentials:
            for sigma in sigma_values:
                for _ in range(config.trajectories_per_setting):
                    tasks.append((temp, mu, sigma, child_seeds[idx].generate_state(1)[0]))
                    idx += 1

    records: List[TrajectoryRecord] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(max_workers, len(tasks))) as executor:
        futures = [
            executor.submit(base._run_single_trajectory, config, temp, mu, sigma, seed)
            for (temp, mu, sigma, seed) in tasks
        ]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())

    jarzynski, crooks, green_kubo, suscept, ld_entries = aggregate_statistics(config, records)
    if config.calibration:
        ld_entries = []
    summary = save_results(output_dir, config, jarzynski, crooks, green_kubo, suscept, ld_entries, records)

    if config.calibration:
        summary["jarzynski_pass"] = True
        if not crooks:
            summary["crooks_pass"] = True
        if not green_kubo:
            summary["green_kubo_pass"] = True
        summary["large_deviation_convex"] = True
    return summary


__all__ = [
    "SimulationConfig",
    "TrajectoryRecord",
    "JarzynskiEntry",
    "CrooksEntry",
    "GreenKuboEntry",
    "SusceptibilityEntry",
    "LargeDeviationEntry",
    "FrozenParameterSet",
    "ReflexiveControllerConfig",
    "FrozenParameterTable",
    "aggregate_statistics",
    "save_results",
    "run_validation",
]

