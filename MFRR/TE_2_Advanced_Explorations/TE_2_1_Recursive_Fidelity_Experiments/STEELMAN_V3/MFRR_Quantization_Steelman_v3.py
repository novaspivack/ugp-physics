"""
MFRR_Quantization_Steelman_v3.py

Deriving Quantization from Topological Constraints.

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Hypothesis:
1. Local neighbors must agree (alignment) to communicate efficiently.
2. The global system must disagree (orthogonality) to maximize capacity.
3. The result is domain formation (spontaneous symmetry breaking) and
   an effectively bimodal distribution of pairwise overlaps.

Mechanism:
- Nodes have positions X and states S.
- Neighbors (k-nearest in physical space): force S to align (|dot| -> 1).
- Non-neighbors: force S to orthogonalize (|dot| -> 0).
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
N_NODES = 60
VECTOR_DIM = 2
STEPS = 1000
LEARNING_RATE = 0.05
K_NEIGHBORS = 4

# Weights
W_ALIGN = 1.0   # Neighbors want to be parallel (|dot| -> 1)
W_ORTHO = 0.5   # Non-neighbors want to be orthogonal (|dot| -> 0)


class Node:
    def __init__(self, id_: int):
        self.id = id_
        self.pos = np.random.rand(3) * 10.0  # Physical space
        v = np.random.randn(VECTOR_DIM)
        self.state = v / np.linalg.norm(v)   # State space

    def normalize(self) -> None:
        n = np.linalg.norm(self.state)
        if n > 0:
            self.state /= n


def run_quantization_steelman_v3() -> None:
    print("Running MFRR Quantization Steel-Man v3 (Topological)...")

    nodes: List[Node] = [Node(i) for i in range(N_NODES)]

    # Precompute neighbors (static topology)
    positions = np.array([n.pos for n in nodes])
    dist_matrix = squareform(pdist(positions))

    neighbors: List[np.ndarray] = []
    for i in range(N_NODES):
        dists = dist_matrix[i].copy()
        dists[i] = np.inf  # exclude self
        nn = np.argsort(dists)[:K_NEIGHBORS]
        neighbors.append(nn)

    history = {
        "histogram": [],
    }

    for t in range(STEPS):
        gradients = np.zeros((N_NODES, VECTOR_DIM), dtype=float)

        # 1. Local alignment (ferromagnetic within neighborhoods)
        # Energy: E_align ~ - (S_i . S_j)^2 for neighbors
        # Gradient: dE/dS_i = -2 (S_i . S_j) S_j
        for i in range(N_NODES):
            s1 = nodes[i].state
            for j in neighbors[i]:
                s2 = nodes[j].state
                dot = float(np.dot(s1, s2))
                gradients[i] += W_ALIGN * 2.0 * dot * s2

        # 2. Global orthogonality (capacity across non-neighbors)
        # Energy: E_ortho ~ sum_{non-neighbors} (S_i . S_j)^2
        # Gradient: dE/dS_i = 2 (S_i . S_j) S_j
        for i in range(N_NODES):
            s1 = nodes[i].state
            for j in range(N_NODES):
                if i == j:
                    continue
                if j in neighbors[i]:
                    continue
                s2 = nodes[j].state
                dot = float(np.dot(s1, s2))
                gradients[i] -= W_ORTHO * 2.0 * dot * s2

        # Update states
        for i in range(N_NODES):
            nodes[i].state += LEARNING_RATE * gradients[i]
            nodes[i].normalize()

        # Diagnostics
        if t % 100 == 0:
            all_dots: List[float] = []
            for i in range(N_NODES):
                for j in range(i + 1, N_NODES):
                    all_dots.append(abs(float(np.dot(nodes[i].state, nodes[j].state))))
            hist, _ = np.histogram(all_dots, bins=10, range=(0.0, 1.0))
            history["histogram"].append(hist.tolist())
            print(f"Step {t:4d}: Hist={hist}")

    # Final stats
    final_dots: List[float] = []
    for i in range(N_NODES):
        for j in range(i + 1, N_NODES):
            final_dots.append(abs(float(np.dot(nodes[i].state, nodes[j].state))))

    hist, bins = np.histogram(final_dots, bins=20, range=(0.0, 1.0))

    low_bin = int(np.sum(hist[:5]))      # 0.0 - 0.25
    mid_bin = int(np.sum(hist[5:15]))    # 0.25 - 0.75
    high_bin = int(np.sum(hist[15:]))    # 0.75 - 1.0

    print("\n--- RESULTS ---")
    print(f"Low Range (Orthogonal): {low_bin}")
    print(f"Mid Range (Ambiguous):  {mid_bin}")
    print(f"High Range (Parallel):  {high_bin}")

    if mid_bin < low_bin and mid_bin < high_bin and low_bin > 0 and high_bin > 0:
        print("CONCLUSION: Quantization Emerged. Bimodal distribution achieved.")
    else:
        print("CONCLUSION: FAILED. Continuum or Monopole persists.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Quantization_Steelman_v3_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "params": {
                    "N_NODES": N_NODES,
                    "VECTOR_DIM": VECTOR_DIM,
                    "STEPS": STEPS,
                    "LEARNING_RATE": LEARNING_RATE,
                    "K_NEIGHBORS": K_NEIGHBORS,
                    "W_ALIGN": W_ALIGN,
                    "W_ORTHO": W_ORTHO,
                },
                "histograms": {
                    "bins": 10,
                    "range": [0.0, 1.0],
                    "time_slices": history["histogram"],
                },
                "final_histogram": {
                    "bins": bins.tolist(),
                    "counts": hist.tolist(),
                    "low_bin": low_bin,
                    "mid_bin": mid_bin,
                    "high_bin": high_bin,
                },
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    run_quantization_steelman_v3()


