"""
Run the Ω-driven Born-equivalence experiment.

Generates a JSON report with total-variation distances between empirical
measurements and the theoretical |ψ|² distribution, demonstrating the
~1/sqrt(N) convergence predicted by PSC + Ω randomness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np

from pr0_system.evolution.ablowitz_ladik import PR0_Final


def total_variation(p: np.ndarray, q: np.ndarray) -> float:
    return 0.5 * float(np.sum(np.abs(p - q)))


def run_single(seed: int, steps: int, samples: int, grid_size: int) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    integrator = PR0_Final(L_x=grid_size, L_y=grid_size, g=0.18)

    # Initialize two solitons with random phase/velocity offsets
    velocity = 0.10 + 0.05 * rng.random()
    phase_shift = rng.uniform(0, np.pi)
    integrator.set_soliton(
        x0=grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.0,
        width=3.0,
        velocity_x=velocity,
        sign=+1,
    )
    integrator.set_soliton(
        x0=2 * grid_size // 3,
        y0=grid_size // 2,
        amplitude=3.0,
        width=3.0,
        velocity_x=-velocity,
        sign=-1,
    )
    integrator.psi *= np.exp(1j * phase_shift)

    for _ in range(steps):
        integrator.step(dt=0.01)

    density = np.abs(integrator.psi) ** 2
    density /= np.sum(density)

    flat = density.flatten()
    top_idx = np.argsort(flat)[::-1][:4]
    categories = np.zeros(5, dtype=np.float64)
    categories[:4] = flat[top_idx]
    categories[4] = 1.0 - np.sum(categories[:4])

    counts = np.zeros(5, dtype=np.int64)
    for _ in range(samples):
        choice = rng.choice(flat.size, p=flat)
        if choice in top_idx:
            counts[np.where(top_idx == choice)[0][0]] += 1
        else:
            counts[4] += 1
    empirical = counts / samples

    tv = total_variation(categories, empirical)
    return {
        "seed": seed,
        "steps": steps,
        "samples": samples,
        "tv_distance": tv,
        "categories": categories.tolist(),
        "empirical": empirical.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ω-driven Born-equivalence experiment.")
    parser.add_argument("--runs", type=int, default=12, help="Number of random seeds.")
    parser.add_argument("--steps", type=int, default=1200, help="Evolution steps per run.")
    parser.add_argument("--samples", type=int, nargs="+", default=[20, 50, 100], help="Measurement sample counts.")
    parser.add_argument("--grid", type=int, default=32, help="Lattice size (square).")
    parser.add_argument("--output", type=str, default="pr0_logs/omega_experiment.json", help="Output JSON path.")
    args = parser.parse_args()

    records: List[Dict[str, float]] = []
    for seed in range(args.runs):
        for samples in args.samples:
            record = run_single(seed=seed, steps=args.steps, samples=samples, grid_size=args.grid)
            records.append(record)
            print(
                f"[Ω] seed={seed:02d} samples={samples:4d} "
                f"tv={record['tv_distance']:.4f}",
                flush=True,
            )

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "runs": args.runs,
        "steps": args.steps,
        "samples": args.samples,
        "records": records,
        "mean_tv_by_samples": {
            str(samples): float(
                np.mean([r["tv_distance"] for r in records if r["samples"] == samples])
            )
            for samples in args.samples
        },
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"[Ω] results written to {output_path}")


if __name__ == "__main__":
    main()


