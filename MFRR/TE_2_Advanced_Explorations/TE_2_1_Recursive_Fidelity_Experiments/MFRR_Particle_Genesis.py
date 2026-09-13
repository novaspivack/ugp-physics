"""
MFRR_Particle_Genesis.py (v2: Orthogonality Upgrade)

Deriving Quantization via Orthogonality Pressure.

This experiment is part of TE_2.1 (Recursive Fidelity Experiments), specified in:
  TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/TE_2_1.1_Recursive Fidelity_Kickoff.md

Hypothesis:
Information states minimize "cross-talk" (ambiguity). Stable states are either
identical (dot product = 1) or orthogonal (dot product = 0). Intermediate
states are unstable high-energy configurations.
"""

import json
import os
import time
from typing import Dict, Any, List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_NODES = 60
S_DIM = 3  # we want to see if they snap to x, y, z axes
FRAMES = 400
DT = 0.05

# Dynamics
KAPPA_GRAVITY = 1.0       # physical attraction
LAMBDA_DARK = 0.005       # physical repulsion

# Quantization forces
# 1. Alignment: if we are close in space, try to be the same species.
GAMMA_ALIGNMENT = 0.5

# 2. Orthogonality: if we are not the same, be perpendicular.
#    This penalizes non-zero dot products.
ZETA_ORTHOGONALITY = 2.0


class MFRR_Discrete_Universe:
    def __init__(self, n_nodes: int, s_dim: int) -> None:
        self.n_nodes = n_nodes
        self.s_dim = s_dim

        # S[i]: information state on the unit sphere
        self.S = np.random.randn(n_nodes, s_dim)
        self.S /= np.linalg.norm(self.S, axis=1, keepdims=True)

        # X[i]: physical position
        self.X = np.random.randn(n_nodes, 3) * 5.0

        self.V_x = np.zeros_like(self.X)
        self.V_s = np.zeros_like(self.S)

    def step(self, dt: float = DT) -> float:
        # ---------------------------
        # 1. PHYSICAL DYNAMICS (standard gravity-like)
        # ---------------------------
        dist_sq = squareform(pdist(self.X, "sqeuclidean"))
        epsilon = 1e-5
        dist_sq = np.maximum(dist_sq, epsilon)
        dist = np.sqrt(dist_sq)

        affinity = np.dot(self.S, self.S.T)
        np.fill_diagonal(affinity, 0.0)

        forces_x = np.zeros_like(self.X)
        for i in range(self.n_nodes):
            diff = self.X[i] - self.X
            d3 = dist[i, :] ** 3
            # Gravity depends on affinity (like attracts like).
            coeff = (affinity[i, :] - LAMBDA_DARK) / d3
            coeff[i] = 0.0
            forces_x[i] = -np.sum(diff * coeff[:, np.newaxis], axis=0)

        # ---------------------------
        # 2. QUANTUM DYNAMICS (Double-Well Quantization)
        # ---------------------------
        # Potential V(x) = x^2 (1 - x^2) with x = S_i · S_j.
        # Minima at x=0 (orthogonal) and x=1 (parallel), maximum at x≈0.707.
        # Force is minus the gradient: dV/dx = 2x - 4x^3.
        dots = np.dot(self.S, self.S.T)  # (N, N)
        # Derivative of potential
        grad_coeff = 2.0 * dots - 4.0 * dots**3

        # Strong quantization pressure
        ZETA = 3.0
        # Global quantization forces: F_i = -Σ_j (dV/dx_ij) S_j
        quantization_forces = -np.dot(grad_coeff, self.S) * ZETA

        # 3. Alignment (local consensus): neighbors choose the same basis vector.
        spatial_weight = 1.0 / (dist + 0.1)
        np.fill_diagonal(spatial_weight, 0.0)
        weighted_sum_s = np.dot(spatial_weight, self.S)
        sum_weights = np.sum(spatial_weight, axis=1, keepdims=True)
        alignment_forces = (weighted_sum_s - sum_weights * self.S) * GAMMA_ALIGNMENT

        forces_s = quantization_forces + alignment_forces

        # ---------------------------
        # Integration
        # ---------------------------
        self.V_x += forces_x * dt
        self.V_x *= 0.95
        self.X += self.V_x * dt

        self.V_s += forces_s * dt
        self.V_s *= 0.90
        self.S += self.V_s * dt
        self.S /= np.linalg.norm(self.S, axis=1, keepdims=True)

        return float(np.linalg.norm(forces_s))


# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------


def analyze_quantization(universe: MFRR_Discrete_Universe) -> Tuple[float, np.ndarray]:
    """
    Analyze the distribution of absolute dot products |S_i · S_j|.

    Quantization score:
      - for each pair, take min distance to {0, 1} in |dot|.
      - ideal quantized: all pairs at 0 or 1 -> min_dist = 0 -> score = 1.
      - maximally ambiguous: all pairs at 0.5 -> min_dist = 0.5 -> score = 0.
    """
    dots = np.dot(universe.S, universe.S.T)
    tri_indices = np.triu_indices(universe.n_nodes, k=1)
    flat_dots = np.abs(dots[tri_indices])

    dist_to_0 = np.abs(flat_dots - 0.0)
    dist_to_1 = np.abs(flat_dots - 1.0)
    min_dist = np.minimum(dist_to_0, dist_to_1)

    score = 1.0 - (np.mean(min_dist) * 2.0)
    return score, flat_dots


def run_particle_ensemble(num_seeds: int = 32) -> Dict[str, Any]:
    print(f"Running MFRR Orthogonal Genesis ({num_seeds} seeds)...")
    print("Hypothesis: orthogonality pressure forces discrete particle species.")

    results: List[Dict[str, Any]] = []

    for seed in range(num_seeds):
        np.random.seed(seed)
        universe = MFRR_Discrete_Universe(N_NODES, S_DIM)

        for _ in range(FRAMES):
            universe.step(DT)

        score, flat_dots = analyze_quantization(universe)
        hist, _ = np.histogram(flat_dots, bins=5, range=(0, 1))

        results.append(
            {
                "seed": seed,
                "quantization_score": score,
                "hist": hist.tolist(),
            }
        )

        print(f"Seed {seed:3d}: Quantization Score = {score:.4f} | Hist: {hist}")

    scores = np.array([r["quantization_score"] for r in results])
    mean_score = float(np.mean(scores))

    print("\nOrthogonal Ensemble Summary:")
    print(f"Mean Quantization Score: {mean_score:.4f} (max 1.0)")

    if mean_score > 0.8:
        print("CONCLUSION: SUCCESS. High quantization.")
        print("States have collapsed into discrete orthogonal species.")
    elif mean_score > 0.5:
        print("CONCLUSION: PARTIAL SUCCESS. Emergent structure detected.")
    else:
        print("CONCLUSION: FAILED. States remain largely continuous.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(
        results_dir,
        f"MFRR_Particle_Orthogonal_{timestamp}.json",
    )

    artifact = {
        "description": "MFRR Orthogonal Genesis ensemble (state-space quantization).",
        "module_path": os.path.abspath(__file__),
        "summary": {"mean_score": mean_score},
        "runs": results,
    }

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"\nOrthogonal ensemble artifact written to: {artifact_path}")

    return {"summary": artifact["summary"], "runs": results, "artifact_path": artifact_path}


if __name__ == "__main__":
    run_particle_ensemble()


