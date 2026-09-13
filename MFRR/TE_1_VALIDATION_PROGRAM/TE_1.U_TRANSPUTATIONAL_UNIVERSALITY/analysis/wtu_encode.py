#!/usr/bin/env python3
"""Compute epsilon metrics for TE1.U weak universality benchmarks.

Usage:
    python wtu_encode.py --config configs/wtu_rule110.yaml \
                         --reference data/rule110_reference.npy \
                         --simulation results/wtu/rule110/pr0_output.npy

The script reads benchmark metadata from the YAML config, loads reference and
PR-0 simulated trajectories, computes error metrics, and writes a JSON summary
into the configured output directory.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from typing import Any, Dict, Tuple

try:
    import yaml  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
    raise SystemExit(
        "PyYAML is required for TE1.U analysis. Install with `pip install PyYAML`."
    ) from exc

import numpy as np


def load_array(path: pathlib.Path) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return np.asarray(data, dtype=float)


def l2_error(reference: np.ndarray, simulation: np.ndarray) -> float:
    diff = simulation - reference
    return float(np.sqrt(np.mean(diff * diff)))


def total_variation(reference: np.ndarray, simulation: np.ndarray) -> float:
    diff = np.abs(simulation - reference)
    return float(np.sum(diff) / diff.size)


def spectral_coherence(reference: np.ndarray, simulation: np.ndarray) -> float:
    ref_fft = np.fft.rfft(reference, axis=-1)
    sim_fft = np.fft.rfft(simulation, axis=-1)
    numerator = np.abs(np.sum(ref_fft * np.conjugate(sim_fft)))
    denominator = math.sqrt(np.sum(np.abs(ref_fft) ** 2) * np.sum(np.abs(sim_fft) ** 2))
    if denominator == 0.0:
        return 0.0
    return float(numerator / denominator)


def auc_delta(reference: np.ndarray, simulation: np.ndarray) -> float:
    if reference.ndim != 2:
        raise ValueError("AUC delta expects 2D arrays (samples x timesteps)")
    # Treat final column as score and approximate AUC via trapezoidal rule
    ref_auc = np.trapz(reference, axis=1).mean()
    sim_auc = np.trapz(simulation, axis=1).mean()
    return float(sim_auc - ref_auc)


def calibration_error(reference: np.ndarray, simulation: np.ndarray) -> float:
    # Expected to be in [0,1]; compute mean absolute error
    return float(np.mean(np.abs(simulation - reference)))


def ensure_output_dir(config: Dict[str, Any]) -> pathlib.Path:
    output_dir = pathlib.Path(config["metrics"]["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TE1.U epsilon metric evaluator")
    parser.add_argument("--config", required=True, type=pathlib.Path, help="YAML config path")
    parser.add_argument("--reference", required=True, type=pathlib.Path, help="Reference trajectory file (npy/json)")
    parser.add_argument("--simulation", required=True, type=pathlib.Path, help="PR-0 simulation output file (npy/json)")
    parser.add_argument("--label", required=False, default="baseline", help="Run label for summary JSON")
    return parser.parse_args()


def validate_shapes(reference: np.ndarray, simulation: np.ndarray, benchmark: Dict[str, Any]) -> None:
    if reference.shape != simulation.shape:
        raise ValueError(f"Shape mismatch: reference {reference.shape} vs simulation {simulation.shape}")
    timesteps = benchmark.get("timesteps")
    if timesteps and reference.shape[0] != timesteps:
        raise ValueError("Trajectory length does not match benchmark specification")
    feature_dim = benchmark.get("feature_dim")
    if feature_dim and reference.shape[1] != feature_dim:
        raise ValueError("Feature dimension does not match benchmark specification")


def main() -> None:
    args = parse_args()
    with args.config.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    benchmark_cfg: Dict[str, Any] = config.get("benchmark", {})
    benchmark_type = benchmark_cfg.get("type", "metrics")

    reference = load_array(args.reference)
    simulation = load_array(args.simulation)
    validate_shapes(reference, simulation, benchmark_cfg)

    if benchmark_type == "binary":
        reference = reference.astype(int)
        simulation = simulation.astype(int)

    metrics_cfg: Dict[str, Any] = config.get("metrics", {})

    normalization = metrics_cfg.get("normalization")
    if normalization == "column_std" and benchmark_type != "binary":
        ref_mean = reference.mean(axis=0, keepdims=True)
        ref_std = reference.std(axis=0, keepdims=True)
        ref_std = np.where(ref_std == 0, 1.0, ref_std)
        reference = (reference - ref_mean) / ref_std
        simulation = (simulation - ref_mean) / ref_std
    elif normalization:
        raise ValueError(f"Unsupported normalization mode: {normalization}")

    results: Dict[str, Any] = {
        "label": args.label,
        "config": str(args.config.resolve()),
        "reference": str(args.reference.resolve()),
        "simulation": str(args.simulation.resolve()),
    }

    if metrics_cfg.get("epsilon_norm") == "L2":
        results["epsilon_L2"] = l2_error(reference, simulation)
    if metrics_cfg.get("epsilon_tv"):
        results["epsilon_TV"] = total_variation(reference, simulation)
    if metrics_cfg.get("spectral_coherence"):
        results["spectral_coherence"] = spectral_coherence(reference, simulation)
    if metrics_cfg.get("auc_delta"):
        results["auc_delta"] = auc_delta(reference, simulation)
    if metrics_cfg.get("calibration"):
        results["calibration_error"] = calibration_error(reference, simulation)
    if benchmark_type == "binary":
        mismatches = int(np.not_equal(reference, simulation).sum())
        total = int(reference.size)
        results["hamming_fraction"] = mismatches / total if total else 0.0

    output_dir = ensure_output_dir(config)
    summary_path = output_dir / f"epsilon_summary_{args.label}.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print(f"Saved metrics to {summary_path}")


if __name__ == "__main__":
    main()
