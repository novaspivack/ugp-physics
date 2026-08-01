"""
Wrapper utilities for modular-flow simulations (Moonshot 1).

This module delegates to `pr0_system.cli.energy_law.run_experiment`, storing the
result payloads in the Moonshot directory when requested.  It is intentionally
lightweight so that tests can execute fast with small problem sizes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pr0_system.cli.energy_law import run_experiment


def run_modular_flow(
    steps: int,
    grid_size: int,
    bootstrap_samples: int = 128,
    seed: int = 20251110,
    output_path: str | Path | None = None,
) -> Dict[str, Any]:
    """
    Execute the log-depth reversible energy experiment and optionally persist results.

    Parameters
    ----------
    steps:
        Number of integration steps (higher gives better statistics at greater cost).
    grid_size:
        Lattice size passed to the underlying PR-0 integrator.
    bootstrap_samples:
        Number of bootstrap draws for confidence intervals.
    seed:
        Random seed for bootstrap reproducibility.
    output_path:
        Optional JSON path for storing the result payload.
    """
    result = run_experiment(
        steps=steps,
        grid_size=grid_size,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )

    if output_path:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run modular-flow (log-depth energy) experiment for Moonshot 1.")
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument("--bootstrap-samples", type=int, default=256)
    parser.add_argument("--seed", type=int, default=20251110)
    parser.add_argument("--output", type=str, help="Optional path to store JSON results.")
    args = parser.parse_args()

    result = run_modular_flow(
        steps=args.steps,
        grid_size=args.grid,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


