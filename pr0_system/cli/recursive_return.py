"""
Evaluate HALT ⇔ recursive-return correspondence using PR-0 simulations.

Produces a JSON report summarizing agreement between a dissipative "halt"
criterion and a variance-based "recursive return" detector.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np

from pr0_system.evolution.ablowitz_ladik import PR0_Final


def run_single(seed: int, steps: int, grid_size: int, window: int, halt_epsilon: float, return_epsilon: float) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    integrator = PR0_Final(L_x=grid_size, L_y=grid_size, g=0.16)

    velocity = 0.07 + 0.03 * rng.random()
    integrator.set_soliton(
        x0=grid_size // 3,
        y0=grid_size // 2,
        amplitude=2.8,
        width=3.2,
        velocity_x=velocity,
        sign=+1,
    )
    integrator.set_soliton(
        x0=2 * grid_size // 3,
        y0=grid_size // 2,
        amplitude=2.8,
        width=3.2,
        velocity_x=-velocity,
        sign=-1,
    )

    density_history: List[float] = []
    for _ in range(steps):
        integrator.step(dt=0.01)
        density_history.append(float(np.sum(np.abs(integrator.psi) ** 2)))

    recent = density_history[-window:] if len(density_history) >= window else density_history
    diffs = np.abs(np.diff(recent))
    max_delta = float(np.max(diffs)) if diffs.size else 0.0
    variance = float(np.var(recent))

    halt = max_delta < halt_epsilon
    recursive_return = variance < return_epsilon

    return {
        "seed": seed,
        "halt": halt,
        "recursive_return": recursive_return,
        "max_delta": max_delta,
        "variance": variance,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="HALT ⇔ recursive-return experiment.")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--steps", type=int, default=1500)
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument("--window", type=int, default=64)
    parser.add_argument("--halt-eps", type=float, default=5e-4)
    parser.add_argument("--return-eps", type=float, default=1e-4)
    parser.add_argument("--output", type=str, default="pr0_logs/recursive_return.json")
    args = parser.parse_args()

    records = [
        run_single(
            seed=seed,
            steps=args.steps,
            grid_size=args.grid,
            window=args.window,
            halt_epsilon=args.halt_eps,
            return_epsilon=args.return_eps,
        )
        for seed in range(args.runs)
    ]

    matches = sum(1 for r in records if r["halt"] == r["recursive_return"])
    summary = {
        "runs": args.runs,
        "steps": args.steps,
        "window": args.window,
        "halt_epsilon": args.halt_eps,
        "return_epsilon": args.return_eps,
        "records": records,
        "match_fraction": matches / args.runs,
    }

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(
        f"[HALT] agreement {matches}/{args.runs} "
        f"({summary['match_fraction']:.2%}) written to {output_path}"
    )


if __name__ == "__main__":
    main()


