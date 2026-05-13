#!/usr/bin/env python3
"""
Execution harness for TE_1.L — Reflexive Adjudication Cosmology.

References:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.L_REFLEXIVE_ADJUDICATION_COSMOLOGY/TE_1.L_KICKOFF.md`
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace, asdict
from datetime import datetime
from pathlib import Path

from te1l_pipeline import ReflexiveConfig, run_pipeline


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE_1.L reflexive transducer validation.")
    parser.add_argument("--max-workers", type=int, default=2, help="Maximum workers (capped at 2).")
    parser.add_argument("--simulations-per-profit", type=int, default=None, help="Override runs per profit value.")
    parser.add_argument("--time-steps", type=int, default=None, help="Override simulation length.")
    parser.add_argument("--seed", type=int, default=None, help="Seed override.")
    parser.add_argument("--output-root", type=str, default=str(RESULTS_DIR), help="Output directory.")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ReflexiveConfig:
    cfg = ReflexiveConfig()
    if args.simulations_per_profit is not None:
        cfg = replace(cfg, simulations_per_profit=args.simulations_per_profit)
    if args.time_steps is not None:
        cfg = replace(cfg, time_steps=args.time_steps)
    if args.seed is not None:
        cfg = replace(cfg, seed_master=args.seed)
    cfg = replace(cfg, progress_interval=max(1, cfg.progress_interval))
    return cfg


def main() -> None:
    args = parse_args()
    cfg = build_config(args)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[TE1.L] Starting reflexive transducer validation (output: {run_dir})", flush=True)
    summary = run_pipeline(cfg, run_dir)

    verdict_path = run_dir / ("PASS.json" if summary.overall_pass else "FAIL.json")
    verdict_path.write_text(json.dumps(asdict(summary), indent=2))

    print(json.dumps(asdict(summary), indent=2))
    print(f"[TE1.L] Artifacts available at {run_dir}")


if __name__ == "__main__":
    main()


