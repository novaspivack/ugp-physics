"""
MFRR_Quantization_Steelman_v5.py

Deriving Quantization from Stochastic Measurement (Quantum Zeno Effect).

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Hypothesis:
1. Interactions are probabilistic (Born Rule: p = |dot|^2).
2. Systems drift away from high-variance states (p=0.5) to low-variance states (p=0 or 1).
3. Quantization is the attractor of stochastic stability.

Mechanism:
- Nodes interact stochastically with neighbors.
- "Measure" neighbor: outcome is Parallel (1) or Orthogonal (0).
- Update state based on outcome (nudge toward the realized result).
"""

import json
import os
import time
from typing import List

import numpy as np
from scipy.spatial.distance import pdist, squareform

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_NODES = 100
VECTOR_DIM = 3
STEPS = 2000  # Stochastic processes need time to settle
LEARNING_RATE = 0.05
K_NEIGHBORS = 8  # Higher connectivity helps global synchronization


class Node:
    def __init__(self, id_: int):
        self.id = id_
        v = np.random.randn(VECTOR_DIM)
        self.state = v / np.linalg.norm(v)

    def normalize(self) -> None:
        n = np.linalg.norm(self.state)
        if n > 0:
            self.state /= n


def run_quantization_steelman_v5() -> None:
    print("Running MFRR Quantization Steel-Man v5 (Stochastic Measurement)...")

    nodes: List[Node] = [Node(i) for i in range(N_NODES)]

    # Topology: k-nearest neighbors in a random geometric graph
    positions = np.random.rand(N_NODES, 3)
    dist_matrix = squareform(pdist(positions))
    neighbors: List[np.ndarray] = []
    for i in range(N_NODES):
        dists = dist_matrix[i].copy()
        dists[i] = np.inf
        nn = np.argsort(dists)[:K_NEIGHBORS]
        neighbors.append(nn)

    history = {
        "histogram": [],
    }

    for t in range(STEPS):
        # Stochastic updates per tick
        updates = np.zeros((N_NODES, VECTOR_DIM), dtype=float)

        for i in range(N_NODES):
            if len(neighbors[i]) == 0:
                continue

            # Pick a random neighbor to interact with
            j = int(np.random.choice(neighbors[i]))

            s1 = nodes[i].state
            s2 = nodes[j].state

            dot = float(np.dot(s1, s2))
            prob = dot * dot  # Born rule: probability of "Yes" outcome

            if np.random.rand() < prob:
                # Outcome: Parallel (measured "Yes")
                # Move S1 toward S2 * sign(dot) (treat anti-parallel as same axis)
                target = s2 * (np.sign(dot) if dot != 0.0 else 1.0)
                updates[i] += (target - s1) * LEARNING_RATE
            else:
                # Outcome: Orthogonal (measured "No")
                # Soft orthogonalization: remove the component of S2 from S1
                # S1_new = S1 - alpha * (S1.S2) * S2
                updates[i] -= s2 * dot * LEARNING_RATE

        # Apply updates
        for i in range(N_NODES):
            nodes[i].state += updates[i]
            nodes[i].normalize()

        # Metrics
        if t % 100 == 0:
            all_dots: List[float] = []
            # Sample pairs
            for _ in range(2000):
                idx = np.random.choice(N_NODES, 2, replace=False)
                d = abs(float(np.dot(nodes[idx[0]].state, nodes[idx[1]].state)))
                all_dots.append(d)

            hist, _ = np.histogram(all_dots, bins=10, range=(0.0, 1.0))
            history["histogram"].append(hist.tolist())
            print(f"Step {t:4d}: Hist={hist}")

    # Final statistics
    final_dots: List[float] = []
    for i in range(N_NODES):
        for j in range(i + 1, N_NODES):
            final_dots.append(abs(float(np.dot(nodes[i].state, nodes[j].state))))

    hist, bins = np.histogram(final_dots, bins=20, range=(0.0, 1.0))

    low_bin = int(np.sum(hist[:5]))
    mid_bin = int(np.sum(hist[5:15]))
    high_bin = int(np.sum(hist[15:]))

    print("\n--- RESULTS ---")
    print(f"Low Range (Orthogonal): {low_bin}")
    print(f"Mid Range (Ambiguous):  {mid_bin}")
    print(f"High Range (Parallel):  {high_bin}")

    if mid_bin < low_bin and mid_bin < high_bin:
        print("CONCLUSION: Quantization Emerged. Stochastic stability favored discrete states.")
    else:
        print("CONCLUSION: FAILED. Continuum persists.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Quantization_Steelman_v5_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    run_quantization_steelman_v5()


