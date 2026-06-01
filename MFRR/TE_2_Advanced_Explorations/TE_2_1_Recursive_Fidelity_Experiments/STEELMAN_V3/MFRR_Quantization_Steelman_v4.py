"""
MFRR_Quantization_Steelman_v4.py

Deriving Quantization from Contrast Maximization (Pauli Exclusion).

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Hypothesis:
1. Information requires difference (contrast).
2. Neighbors in a network must be orthogonal to distinguish their states.
3. This constraint forces the continuous state space to crystallize into
   a discrete basis.

Mechanism:
- Nodes have 3D state vectors.
- Neighbors (k=6) apply "Contrast Force" (minimize |dot|^2).
- Random pairs apply "Ambiguity Force" (avoid |dot| ~ 0.5).
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
VECTOR_DIM = 3  # 3D state space (allows x, y, z basis)
STEPS = 1000
LEARNING_RATE = 0.05
K_NEIGHBORS = 6

# Weights
W_CONTRAST = 1.0   # Neighbors want to be orthogonal (Pauli-like repulsion)
W_AMBIGUITY = 0.2  # Weak pressure to avoid "muddy" states (|dot| ~ 0.5)


class Node:
    def __init__(self, id_: int):
        self.id = id_
        # Random 3D vector
        v = np.random.randn(VECTOR_DIM)
        self.state = v / np.linalg.norm(v)

    def normalize(self) -> None:
        n = np.linalg.norm(self.state)
        if n > 0:
            self.state /= n


def run_quantization_steelman_v4() -> None:
    print("Running MFRR Quantization Steel-Man v4 (Contrast-Driven)...")

    nodes: List[Node] = [Node(i) for i in range(N_NODES)]

    # 1. Establish topology (distance-based random graph)
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
        gradients = np.zeros((N_NODES, VECTOR_DIM), dtype=float)

        # 1. Contrast force (neighbors): minimize E = sum (S_i . S_j)^2
        #    dE/dS_i = 2 (S_i . S_j) S_j  ⇒ force = -dE/dS_i
        for i in range(N_NODES):
            s1 = nodes[i].state
            for j in neighbors[i]:
                s2 = nodes[j].state
                dot = float(np.dot(s1, s2))
                gradients[i] -= W_CONTRAST * 2.0 * dot * s2

        # 2. Ambiguity force (sampled pairs): avoid |dot| ≈ 0.5
        for i in range(N_NODES):
            others = np.random.choice(N_NODES, size=10, replace=False)
            s1 = nodes[i].state
            for j in others:
                if i == j:
                    continue
                s2 = nodes[j].state
                dot = float(np.dot(s1, s2))
                abs_dot = abs(dot)
                # Ambiguity potential: push away from 0.5
                # Force magnitude: (4 - 8*abs_dot) * sign(dot)
                force_mag = (4.0 - 8.0 * abs_dot) * np.sign(dot)
                gradients[i] += W_AMBIGUITY * force_mag * s2

        # Update states
        for i in range(N_NODES):
            nodes[i].state += LEARNING_RATE * gradients[i]
            nodes[i].normalize()

        # Metrics: histogram of sampled pairwise |dot| values
        if t % 100 == 0:
            all_dots: List[float] = []
            for _ in range(1000):
                idx = np.random.choice(N_NODES, 2, replace=False)
                d = abs(float(np.dot(nodes[idx[0]].state, nodes[idx[1]].state)))
                all_dots.append(d)
            hist, _ = np.histogram(all_dots, bins=10, range=(0.0, 1.0))
            history["histogram"].append(hist.tolist())
            print(f"Step {t:4d}: Hist={hist}")

    # Final stats (full matrix)
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

    # Success if we have peaks at edges and valley in middle
    if mid_bin < low_bin and mid_bin < high_bin:
        print("CONCLUSION: Quantization Emerged. Bimodal distribution achieved.")
    elif low_bin > mid_bin and high_bin == 0:
        print("CONCLUSION: Orthogonalization. System formed a basis (Crystal).")
    else:
        print("CONCLUSION: FAILED. Continuum persists.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Quantization_Steelman_v4_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "params": {
                    "N_NODES": N_NODES,
                    "VECTOR_DIM": VECTOR_DIM,
                    "STEPS": STEPS,
                    "LEARNING_RATE": LEARNING_RATE,
                    "K_NEIGHBORS": K_NEIGHBORS,
                    "W_CONTRAST": W_CONTRAST,
                    "W_AMBIGUITY": W_AMBIGUITY,
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
    run_quantization_steelman_v4()


