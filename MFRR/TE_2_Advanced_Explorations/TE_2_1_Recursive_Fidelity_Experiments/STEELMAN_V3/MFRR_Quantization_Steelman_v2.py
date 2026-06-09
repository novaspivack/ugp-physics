"""
MFRR_Quantization_Steelman_v2.py

Deriving Quantum Discreteness from Noise Tolerance AND Information Capacity.

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Hypothesis:
1. Local Ambiguity Minimization forces states to be parallel or orthogonal.
2. Global Entropy Maximization forces states to be diverse (sum to zero).
3. The result is a discrete basis set (e.g., two opposite poles on the Bloch sphere).

Mechanism:
- Pairwise force: minimize ambiguity (push |dot| away from 0.5).
- Global force: minimize net dipole (push sum(S) to 0).
"""

import json
import os
import time
from typing import List

import numpy as np

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_NODES = 50
VECTOR_DIM = 2
STEPS = 800
LEARNING_RATE = 0.05

# Weights
W_AMBIGUITY = 1.0  # Local: be clear (prefer |dot| near 0 or 1, not 0.5)
W_DIVERSITY = 2.0  # Global: be different (drive sum(S) -> 0)


class Node:
    def __init__(self, id_: int):
        self.id = id_
        v = np.random.randn(VECTOR_DIM)
        self.state = v / np.linalg.norm(v)

    def normalize(self) -> None:
        n = np.linalg.norm(self.state)
        if n > 0:
            self.state /= n


def run_quantization_steelman_v2() -> None:
    print("Running MFRR Quantization Steel-Man v2 (Entropy-Driven)...")

    nodes: List[Node] = [Node(i) for i in range(N_NODES)]

    history = {
        "orthogonality": [],
        "histogram": [],
    }

    for t in range(STEPS):
        gradients = np.zeros((N_NODES, VECTOR_DIM), dtype=float)

        # 1. Global diversity force (entropy / capacity)
        # We want sum(S) ≈ 0 to avoid a ferromagnetic (all-parallel) ground state.
        # E_div = |sum(S)|^2  ⇒  dE/dS_i = 2 * sum(S)
        total_vec = np.sum([n.state for n in nodes], axis=0)
        diversity_grad = 2.0 * total_vec

        # Apply global diversity force (same direction for all nodes)
        for i in range(N_NODES):
            gradients[i] -= (W_DIVERSITY / N_NODES) * diversity_grad

        # 2. Local ambiguity force (noise tolerance)
        dots: List[float] = []
        for i in range(N_NODES):
            s1 = nodes[i].state
            for j in range(i + 1, N_NODES):
                s2 = nodes[j].state

                dot = float(np.dot(s1, s2))
                abs_dot = abs(dot)
                dots.append(abs_dot)

                # Ambiguity potential:
                # Ambiguity is maximal near |dot| = 0.5 and minimal near 0 or 1.
                # Define a cost peaked at 0.5:
                #   Cost(abs_dot) = 1 - (2*abs_dot - 1)^2
                # which is 0 at 0 and 1, and 1 at 0.5.
                #
                # dCost/d|dot| = -4(2|dot| - 1) = 4 - 8|dot|.
                # Chain rule to dot:
                #   dCost/ddot = sign(dot) * (4 - 8|dot|)
                #
                # For gradient descent on Cost, the force is -dCost/ddot.
                force_mag = (4.0 - 8.0 * abs_dot) * np.sign(dot)

                gradients[i] += W_AMBIGUITY * force_mag * s2
                gradients[j] += W_AMBIGUITY * force_mag * s1

        # Update states
        for i in range(N_NODES):
            nodes[i].state += LEARNING_RATE * gradients[i]
            nodes[i].normalize()

        # Metrics
        avg_ortho = float(np.mean(dots))
        history["orthogonality"].append(avg_ortho)

        if t % 50 == 0:
            hist, _ = np.histogram(dots, bins=10, range=(0.0, 1.0))
            history["histogram"].append(hist.tolist())
            print(f"Step {t:3d}: Mean |Dot|={avg_ortho:.3f}")

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
    artifact_path = os.path.join(results_dir, f"MFRR_Quantization_Steelman_v2_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "params": {
                    "N_NODES": N_NODES,
                    "VECTOR_DIM": VECTOR_DIM,
                    "STEPS": STEPS,
                    "LEARNING_RATE": LEARNING_RATE,
                    "W_AMBIGUITY": W_AMBIGUITY,
                    "W_DIVERSITY": W_DIVERSITY,
                },
                "orthogonality": history["orthogonality"],
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
    run_quantization_steelman_v2()


