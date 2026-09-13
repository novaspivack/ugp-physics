"""Command-line entry point for TE₁.B_v2 minimal experiment.

Specification: docs/TE1B_Minimal_RSM_Spec.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .controller import ControllerConfig
from .pipeline import ExperimentConfig, GreenKuboConfig, run_experiment
from .simulator import EnsembleConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE₁.B_v2 minimal reflexive experiment")
    parser.add_argument("--results-root", type=Path, default=Path("results"), help="Root directory for experiment outputs")
    parser.add_argument("--forward-count", type=int, default=32, help="Calibration trajectories per ensemble (forward)")
    parser.add_argument("--reverse-count", type=int, default=32, help="Calibration trajectories per ensemble (reverse)")
    parser.add_argument("--production-count", type=int, default=256, help="Production trajectories per ensemble")
    parser.add_argument("--trajectory-length", type=int, default=64, help="Length of each trajectory (events)")
    parser.add_argument("--processes", type=int, default=None, help="Number of processes for ensemble runs")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ExperimentConfig:
    controller_cfg = ControllerConfig(
        window_size=6,
        jarzynski_band=0.05,
        crooks_band=0.05,
        learning_rate_alpha=0.12,
        learning_rate_beta=0.08,
        steady_windows=5,
        alpha_min=0.5,
        alpha_max=2.5,
        beta_min=-1.0,
        beta_max=1.0,
    )
    calibration_cfg = EnsembleConfig(
        forward_mu=0.25,
        reverse_mu=-0.25,
        trajectory_length=args.trajectory_length,
        forward_count=args.forward_count,
        reverse_count=args.reverse_count,
        intensity_alpha=1.0,
        reverse_bias_beta=0.0,
        processes=args.processes,
    )
    production_cfg = EnsembleConfig(
        forward_mu=0.25,
        reverse_mu=-0.25,
        trajectory_length=args.trajectory_length,
        forward_count=args.production_count,
        reverse_count=args.production_count,
        intensity_alpha=1.0,
        reverse_bias_beta=0.0,
        processes=args.processes,
    )
    gk_cfg = GreenKuboConfig(
        mu0=0.0,
        delta_mu=0.02,
        steps=8192,
        burn_in=1024,
        observable_state="S1",
        start_state="S0",
    )
    return ExperimentConfig(
        controller=controller_cfg,
        calibration=calibration_cfg,
        production=production_cfg,
        green_kubo=gk_cfg,
        max_calibration_steps=64,
        results_root=args.results_root,
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)
    result = run_experiment(config)
    print(f"Results saved to: {result.results_dir}")
    print("Jarzynski:", result.jarzynski)
    print("Crooks:", result.crooks)
    print("Green–Kubo:", result.green_kubo)


if __name__ == "__main__":
    main()
