"""
MFRR_Evolutionary_Sweep.py

Validating the universality of the 1.13 Information Profit Threshold.

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Mechanism:
- Reuse the v2 evolutionary environment from `MFRR_Evolutionary_Genesis.py`.
- Sweep over metabolic cost and resource decay parameters.
- For each grid point, run a shortened evolutionary curriculum and record
  the final profit ratio (generation/drain).
- Examine whether the transition from "struggle" to "thriving" clusters
  near the IPP threshold Gen/Drain ≈ 1.13 across conditions.
"""

import json
import multiprocessing as mp
import os
import time
from typing import List, Tuple

import contextlib
import io

import numpy as np

import MFRR_Evolutionary_Genesis as evo


def run_simulation_instance(args: Tuple[float, float, int]) -> Tuple[float, float, float]:
    """
    One evolutionary run for a given (metabolic_cost, decay_rate, seed).

    We reuse the full v2 curriculum from `MFRR_Evolutionary_Genesis.run_evolutionary_genesis_v2`,
    but shorten the number of generations and frames for tractability, and
    override the key parameters (METABOLIC_COST, RESOURCE_DECAY_RATE).
    """
    metabolic_cost, decay_rate, seed = args
    np.random.seed(seed)

    # Backup original globals
    orig_generations = evo.GENERATIONS
    orig_frames = evo.FRAMES
    orig_metabolic = evo.METABOLIC_COST
    orig_decay = evo.RESOURCE_DECAY_RATE

    # Shortened but still curriculum-like run
    evo.GENERATIONS = 40
    evo.FRAMES = 600
    evo.METABOLIC_COST = metabolic_cost
    evo.RESOURCE_DECAY_RATE = decay_rate

    try:
        # Suppress per-generation printing from the underlying function
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = evo.run_evolutionary_genesis_v2()
        history = result["history"]
        ratio = float(history[-1]["profit_ratio"])
    finally:
        # Restore original globals
        evo.GENERATIONS = orig_generations
        evo.FRAMES = orig_frames
        evo.METABOLIC_COST = orig_metabolic
        evo.RESOURCE_DECAY_RATE = orig_decay

    return metabolic_cost, decay_rate, ratio


def run_sweep() -> None:
    print("Running MFRR Evolutionary Sweep (Parameter Grid)...")

    # Refined grid focused around the empirically supercritical region
    # observed in the coarse sweep (low cost, higher decay).
    costs = [0.0008, 0.0010, 0.0012, 0.0015]
    decays = [0.0040, 0.0043, 0.0046, 0.0049, 0.0052, 0.0055]

    tasks: List[Tuple[float, float, int]] = []
    seed = 0
    for c in costs:
        for d in decays:
            # Run 3 seeds per grid point
            for _ in range(3):
                tasks.append((c, d, seed))
                seed += 1

    total = len(tasks)
    print(f"Total simulations: {total}")

    results: List[Tuple[float, float, float]] = []
    with mp.Pool(processes=9) as pool:
        for idx, res in enumerate(pool.imap_unordered(run_simulation_instance, tasks), start=1):
            results.append(res)
            if idx % 5 == 0 or idx == total:
                print(f"Completed {idx}/{total}")

    # Aggregate results by (cost, decay)
    aggregated: dict[Tuple[float, float], List[float]] = {}
    for c, d, r in results:
        key = (c, d)
        if key not in aggregated:
            aggregated[key] = []
        aggregated[key].append(r)

    print("\n--- SWEEP RESULTS (mean final profit ratio) ---")
    print("Cost | Decay | Mean_Ratio")
    for (c, d), rs in sorted(aggregated.items()):
        avg_ratio = float(np.mean(rs))
        print(f"{c:.3f} | {d:.3f} | {avg_ratio:.3f}")

    # Save raw results
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Evolutionary_Sweep_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "grid": {"costs": costs, "decays": decays},
                "runs": [
                    {"metabolic_cost": c, "decay_rate": d, "profit_ratio": r}
                    for (c, d, r) in results
                ],
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    run_sweep()


