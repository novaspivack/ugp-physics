#!/usr/bin/env python3
"""
Execution harness for TE_1.F — Reflexive Information–Consciousness Metric.

References:
  - Kickoff: `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
  - README: `TE_1_VALIDATION_PROGRAM/TE_1.F_RIC/README.md`
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path

from te1f_pipeline import RICConfig, build_dataset, write_outputs, _train_and_evaluate


BASE_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = BASE_DIR / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE_1.F RIC validation.")
    parser.add_argument("--max-workers", type=int, default=2, help="Maximum workers (unused but accepted for symmetry).")
    parser.add_argument("--n-train", type=int, default=None, help="Training episodes (default 800).")
    parser.add_argument("--n-val", type=int, default=None, help="Validation episodes (default 200).")
    parser.add_argument("--n-test", type=int, default=None, help="Test episodes (default 200).")
    parser.add_argument("--output-root", type=str, default=str(RESULTS_ROOT), help="Directory for run artifacts.")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> RICConfig:
    cfg = RICConfig()
    if args.n_train is not None:
        cfg = replace(cfg, n_train=args.n_train)
    if args.n_val is not None:
        cfg = replace(cfg, n_val=args.n_val)
    if args.n_test is not None:
        cfg = replace(cfg, n_test=args.n_test)
    return cfg


def main() -> None:
    args = parse_args()
    cfg = build_config(args)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("[TE1.F] Building dataset...", flush=True)
    dataset = build_dataset(cfg)

    print("[TE1.F] Calibrating models...", flush=True)
    model_base, metrics_base, model_pi, metrics_pi, summary = _train_and_evaluate(cfg, dataset)

    print("[TE1.F] Writing artifacts...", flush=True)
    write_outputs(cfg, dataset, model_base, metrics_base, model_pi, metrics_pi, summary, run_dir)

    verdict_path = run_dir / ("PASS.json" if summary.overall_pass else "FAIL.json")
    verdict_path.write_text(json.dumps(asdict(summary), indent=2))

    print(json.dumps(asdict(summary), indent=2))
    print(f"[TE1.F] Artifacts available at {run_dir}")


if __name__ == "__main__":
    main()


