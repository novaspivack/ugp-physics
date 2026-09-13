#!/usr/bin/env python3
"""
Execution harness for TE_1.G — Self-Evolving Law validation.

References:
- `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `TE_1_VALIDATION_PROGRAM/TE_1.G_SelfEvolvingLaw/README.md`
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace, asdict
from datetime import datetime
from pathlib import Path

from te1g_pipeline import SRRGConfig, run_pipeline


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TE_1.G SRRG validation.")
    parser.add_argument("--max-workers", type=int, default=2, help="Maximum workers (capped at 2).")
    parser.add_argument("--population", type=int, default=None, help="Population size override.")
    parser.add_argument("--max-steps", type=int, default=None, help="Maximum SRRG steps per law.")
    parser.add_argument("--seed", type=int, default=None, help="Seed override for reproducibility.")
    parser.add_argument("--output-root", type=str, default=str(RESULTS_DIR), help="Output directory for artefacts.")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> SRRGConfig:
    cfg = SRRGConfig()
    if args.population is not None:
        cfg = replace(cfg, population=args.population)
    if args.max_steps is not None:
        cfg = replace(cfg, max_steps=args.max_steps)
    if args.seed is not None:
        cfg = replace(cfg, seed_master=args.seed)
    cfg = replace(cfg, max_workers=max(1, min(args.max_workers, 2)))
    return cfg


def main() -> None:
    args = parse_args()
    cfg = build_config(args)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[TE1.G] Starting SRRG validation (output: {run_dir})", flush=True)
    summary = run_pipeline(cfg, run_dir)

    verdict_path = run_dir / ("PASS.json" if summary.overall_pass else "FAIL.json")
    verdict_path.write_text(json.dumps(asdict(summary), indent=2))

    print(json.dumps(asdict(summary), indent=2))
    print(f"[TE1.G] Artifacts available at {run_dir}")


if __name__ == "__main__":
    main()


