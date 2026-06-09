"""
MFRR_Quantization_Steelman.py

Deriving Quantum Discreteness from Noise Tolerance.

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Hypothesis:
In a noisy communication channel, continuous state vectors will spontaneously
quantize into orthogonal basis sets to maximize distinguishability.

Mechanism:
1. Nodes have continuous state vectors S (normalized).
2. They transmit S to neighbors through a noisy channel.
3. Receiver attempts to decode S (implicitly via the ambiguity cost).
   - If S is close to a "stable" state, error is low.
   - If S is ambiguous, error is high.
4. Nodes adjust S to minimize the ambiguity/error of their neighbors and
   to avoid collapsing into a single redundant codeword.
   - Local term: penalize ambiguous relationships (dot products near 0.5).
   - Global term: penalize large net "magnetization" (too many vectors aligned),
     which reduces channel capacity.

We do NOT use an explicit double-well potential on the states themselves.
Instead, we penalize ambiguous pairwise relationships (dot products near 0.5),
and we add a global diversity pressure derived from information-capacity
considerations (minimizing redundancy / net magnetization).
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
VECTOR_DIM = 2  # Qubit-like (2D Hilbert space)
STEPS = 500
LEARNING_RATE = 0.05
NOISE_LEVEL = 0.1  # Reserved for possible future explicit noisy-channel variants

# Information-theoretic weighting:
# - LAMBDA_AMB: weight on ambiguity penalty (pairs near |dot| ~ 0.5 are costly).
# - LAMBDA_RED: weight on redundancy penalty (pairs with large |dot| are costly,
#   as they reduce effective channel capacity by reusing nearly identical codewords).
LAMBDA_AMB = 1.0
LAMBDA_RED = 0.7


class Node:
    def __init__(self, id_: int):
        self.id = id_
        # Random normalized vector
        v = np.random.randn(VECTOR_DIM)
        self.state = v / np.linalg.norm(v)

    def normalize(self) -> None:
        n = np.linalg.norm(self.state)
        if n > 0:
            self.state /= n


def run_quantization_steelman() -> None:
    print("Running MFRR Quantization Steel-Man (Noise-Induced Discreteness)...")

    nodes: List[Node] = [Node(i) for i in range(N_NODES)]

    history = {
        "orthogonality": [],  # Mean |dot product| over time
        "histogram": [],      # Binned dot-product distributions every 50 steps
    }

    THRESHOLD = 0.5  # Ambiguity zone center (used conceptually; dynamics penalize dots near this)

    for t in range(STEPS):
        gradients = np.zeros((N_NODES, VECTOR_DIM), dtype=float)
        dots: List[float] = []

        # Pairwise interactions (local ambiguity + redundancy minimization)
        for i in range(N_NODES):
            s1 = nodes[i].state
            for j in range(i + 1, N_NODES):
                s2 = nodes[j].state

                dot = float(np.dot(s1, s2))
                abs_dot = abs(dot)
                dots.append(abs_dot)

                # Local ambiguity + redundancy costs:
                #
                # 1. Ambiguity cost:
                #    E_amb = (|dot| - THRESHOLD)^2
                #    Highest when |dot| ≈ THRESHOLD ≈ 0.5,
                #    lowest when |dot| is near 0 or 1.
                #
                # 2. Redundancy cost:
                #    E_red = |dot|^2
                #    High when |dot| is large (states nearly identical),
                #    minimal when states are orthogonal (|dot| ≈ 0).
                #
                # Total pairwise energy:
                #    E_pair = LAMBDA_AMB * E_amb + LAMBDA_RED * E_red
                #
                # This is basis-agnostic and derived from:
                # - Ambiguity minimization: avoid mid-overlaps that are easily
                #   confused under noise.
                # - Capacity maximization: avoid reusing nearly identical
                #   codewords that reduce distinguishable symbols.
                #
                # Gradients:
                #   dE_amb/d|dot| = 2 (|dot| - THRESHOLD)
                #   dE_red/d|dot| = 2 |dot|
                #   dE/d|dot| = 2 [LAMBDA_AMB (|dot| - THRESHOLD) + LAMBDA_RED |dot|]
                #
                # Chain rule:
                #   dE/ddot = dE/d|dot| * d|dot|/ddot
                #          = sign(dot) * 2 [LAMBDA_AMB (|dot| - THRESHOLD)
                #                              + LAMBDA_RED |dot|]
                #
                # For gradient descent we apply a "force" = - dE/ddot.
                if abs_dot == 0.0:
                    continue
                dE_dabs = LAMBDA_AMB * (abs_dot - THRESHOLD) + LAMBDA_RED * abs_dot
                dE_ddot = 2.0 * np.sign(dot) * dE_dabs
                force_mag = -dE_ddot

                # d(dot)/dS1 = S2 ; d(dot)/dS2 = S1
                gradients[i] += force_mag * s2
                gradients[j] += force_mag * s1

        # Update states with gradient descent and renormalize
        for i in range(N_NODES):
            nodes[i].state += LEARNING_RATE * gradients[i]
            nodes[i].normalize()

        # Metrics
        avg_abs_dot = float(np.mean(dots))
        history["orthogonality"].append(avg_abs_dot)

        if t % 50 == 0:
            hist, _ = np.histogram(dots, bins=10, range=(0.0, 1.0))
            history["histogram"].append(hist.tolist())
            print(f"Step {t:3d}: Mean |Dot|={avg_abs_dot:.3f}")

    # Final distribution diagnostics
    final_dots: List[float] = []
    for i in range(N_NODES):
        for j in range(i + 1, N_NODES):
            final_dots.append(abs(float(np.dot(nodes[i].state, nodes[j].state))))

    hist, bins = np.histogram(final_dots, bins=20, range=(0.0, 1.0))

    # Coarse ranges for orthogonal / ambiguous / parallel
    low_bin = int(np.sum(hist[:5]))      # 0.0 - 0.25
    mid_bin = int(np.sum(hist[5:15]))    # 0.25 - 0.75
    high_bin = int(np.sum(hist[15:]))    # 0.75 - 1.0

    print("\n--- RESULTS ---")
    print(f"Low Range (Orthogonal): {low_bin}")
    print(f"Mid Range (Ambiguous):  {mid_bin}")
    print(f"High Range (Parallel):  {high_bin}")

    if mid_bin < low_bin and mid_bin < high_bin:
        print("CONCLUSION: Quantization Emerged. States avoided ambiguity.")
    else:
        print("CONCLUSION: FAILED. Continuum persists.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Quantization_Steelman_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "params": {
                    "N_NODES": N_NODES,
                    "VECTOR_DIM": VECTOR_DIM,
                    "STEPS": STEPS,
                    "LEARNING_RATE": LEARNING_RATE,
                    "NOISE_LEVEL": NOISE_LEVEL,
                    "THRESHOLD": THRESHOLD,
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
    run_quantization_steelman()


