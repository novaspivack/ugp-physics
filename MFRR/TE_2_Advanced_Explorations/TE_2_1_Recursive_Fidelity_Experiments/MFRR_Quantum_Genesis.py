"""
MFRR_Quantum_Genesis.py

Emergent Quantum Mechanics via Maximal Fidelity Representation Recursion (MFRR).

This experiment is part of TE_2.1 (Recursive Fidelity Experiments), specified in:
  TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/TE_2_1.1_Recursive Fidelity_Kickoff.md

Hypothesis:
1. Superposition is the state of high entropy (low constraint) where the MFRR solution is non-unique.
2. Collapse is the rapid reduction of solution space when information density (constraints) increases.
"""

import json
import os
import time
from typing import Dict, Any, List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
import matplotlib.animation as animation  # reserved for future visualizers


# ---------------------------------------------------------
# MFRR CONSTANTS
# ---------------------------------------------------------
KAPPA = 1.0
LAMBDA_COMPLEXITY = 0.005
S_DIM = 10
N_NODES = 50


# ---------------------------------------------------------
# QUANTUM CONSTANTS
# ---------------------------------------------------------
PLANCK_H = 0.1          # Minimum uncertainty scale
DISPERSION_RATE = 0.02  # How fast waves spread in vacuum
COLLAPSE_STRENGTH = 3.0  # How hard observation forces localization (stronger collapse)


class MFRR_Quantum_Universe:
    """
    Universe where each node carries both a classical position (mu)
    and a quantum uncertainty (sigma).
    """

    def __init__(self, n_nodes: int, s_dim: int) -> None:
        self.n_nodes = n_nodes
        self.s_dim = s_dim

        # S[i]: intrinsic information content of each node.
        self.S = np.random.randn(n_nodes, s_dim)
        self.S /= np.linalg.norm(self.S, axis=1, keepdims=True)

        # Mu[i]: mean position (classical coordinate) in 3D.
        self.Mu = np.random.randn(n_nodes, 3) * 5.0

        # Sigma[i]: uncertainty radius (quantum wavefunction width).
        # Initially moderately fuzzy.
        self.Sigma = np.ones(n_nodes) * 0.5

        # Velocity for Mu.
        self.V = np.zeros_like(self.Mu)

    def compute_dynamics(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute evolution for both position (Mu) and uncertainty (Sigma).

        Returns
        -------
        forces : np.ndarray
            Forces on mean positions.
        d_sigma : np.ndarray
            Time derivative of uncertainty for each node.
        """
        # Classical gravity/fidelity forces acting on Mu
        dist_sq = squareform(pdist(self.Mu, "sqeuclidean"))
        epsilon = 1e-5
        dist_sq = np.maximum(dist_sq, epsilon)
        dist = np.sqrt(dist_sq)

        affinity = np.dot(self.S, self.S.T)
        np.fill_diagonal(affinity, 0)

        forces = np.zeros_like(self.Mu)
        local_potential = np.zeros(self.n_nodes)

        for i in range(self.n_nodes):
            diff = self.Mu[i] - self.Mu
            d3 = dist[i, :] ** 3
            d1 = dist[i, :]

            # Standard MFRR-style force
            coeff = (affinity[i, :] - LAMBDA_COMPLEXITY) / d3
            coeff[i] = 0.0
            forces[i] = -np.sum(diff * coeff[:, np.newaxis], axis=0)

            # Local information density / observation strength.
            # Interacting with a sharper neighbor provides more information.
            obs_terms = affinity[i, :] / (d1 * self.Sigma)
            obs_terms[i] = 0.0
            local_potential[i] = np.sum(obs_terms)

        # Quantum dynamics acting on Sigma:
        # Rule A: Dispersion – uncertainty grows naturally (entropy).
        # Rule B: Collapse – uncertainty shrinks with local information density.
        #
        # dSigma = DISPERSION_RATE - (COLLAPSE_STRENGTH * local_potential * Sigma)
        d_sigma = DISPERSION_RATE - (COLLAPSE_STRENGTH * local_potential * self.Sigma)

        return forces, d_sigma

    def step(self, dt: float = 0.05, friction: float = 0.98) -> float:
        """
        Evolve the universe one time step.

        Updates both position (Mu) and uncertainty (Sigma).
        Returns the mean uncertainty as a simple diagnostic.
        """
        forces, d_sigma = self.compute_dynamics()

        # Update position (Mu)
        self.V += forces * dt
        self.V *= friction
        self.Mu += self.V * dt

        # Update uncertainty (Sigma)
        self.Sigma += d_sigma * dt

        # Clamp Sigma: cannot be smaller than PLANCK_H, cannot be arbitrarily large.
        self.Sigma = np.clip(self.Sigma, PLANCK_H, 10.0)

        return float(np.mean(self.Sigma))


# ---------------------------------------------------------
# ANALYSIS & EXECUTION
# ---------------------------------------------------------


def run_quantum_ensemble(
    num_seeds: int = 32,
    frames: int = 200,
    dt: float = 0.05,
) -> Dict[str, Any]:
    """
    Run a quantum ensemble and measure uncertainty in clusters vs void.

    We classify nodes as "cluster" or "void" based on spatial proximity
    and affinity, then compare their final uncertainty radii.
    """
    print(f"Running MFRR Quantum Ensemble (num_seeds={num_seeds})...")

    results: List[Dict[str, Any]] = []

    for seed in range(num_seeds):
        np.random.seed(seed)
        universe = MFRR_Quantum_Universe(N_NODES, S_DIM)

        sigma_history: List[float] = []

        for _ in range(frames):
            avg_sigma = universe.step(dt=dt)
            sigma_history.append(avg_sigma)

        # Final analysis: classify nodes into clusters vs void by local information density.
        affinity = np.dot(universe.S, universe.S.T)
        np.fill_diagonal(affinity, 0.0)

        dist_matrix = squareform(pdist(universe.Mu))
        epsilon = 1e-5
        dist_matrix = np.maximum(dist_matrix, epsilon)

        # Local information density proxy: sum_j affinity_ij / distance_ij
        local_info = np.sum(affinity / dist_matrix, axis=1)

        # Define clusters as the top quartile in local information density,
        # and void as the bottom quartile.
        sorted_idx = np.argsort(local_info)
        n_q = max(1, universe.n_nodes // 4)
        void_indices = sorted_idx[:n_q]
        cluster_indices = sorted_idx[-n_q:]

        cluster_mask = np.zeros(universe.n_nodes, dtype=bool)
        void_mask = np.zeros(universe.n_nodes, dtype=bool)
        cluster_mask[cluster_indices] = True
        void_mask[void_indices] = True

        avg_sigma_cluster = (
            float(np.mean(universe.Sigma[cluster_mask])) if np.any(cluster_mask) else float("nan")
        )
        avg_sigma_void = (
            float(np.mean(universe.Sigma[void_mask])) if np.any(void_mask) else float("nan")
        )

        ratio = (
            avg_sigma_cluster / avg_sigma_void
            if (np.isfinite(avg_sigma_cluster) and avg_sigma_void > 0)
            else float("nan")
        )

        results.append(
            {
                "seed": seed,
                "sigma_cluster": avg_sigma_cluster,
                "sigma_void": avg_sigma_void,
                "ratio": ratio,
            }
        )

        print(
            f"Seed {seed:3d}: Sigma(Cluster)={avg_sigma_cluster:.4f} | "
            f"Sigma(Void)={avg_sigma_void:.4f}"
        )

    # Summary statistics
    ratios = np.array([r["ratio"] for r in results if np.isfinite(r["ratio"])])
    mean_ratio = float(np.mean(ratios)) if ratios.size > 0 else float("nan")
    std_ratio = float(np.std(ratios, ddof=1)) if ratios.size > 1 else float("nan")

    print("\nQuantum Ensemble Summary:")
    print(f"Mean Uncertainty Ratio (Cluster / Void): {mean_ratio:.4f}")
    if np.isfinite(std_ratio):
        print(f"Std(Cluster / Void) = {std_ratio:.4f}")

    if np.isfinite(mean_ratio) and mean_ratio < 0.5:
        print("CONCLUSION: SUCCESS. High information density causes wavefunction collapse.")
        print("We have simulated a quantum–classical transition from MFRR.")
    else:
        print("CONCLUSION: INCONCLUSIVE. No strong separation of quantum states.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(
        results_dir,
        f"MFRR_Quantum_ensemble_{timestamp}.json",
    )

    artifact = {
        "description": "Ensemble of MFRR Quantum Genesis runs (uncertainty vs information density).",
        "module_path": os.path.abspath(__file__),
        "summary": {"mean_ratio": mean_ratio, "std_ratio": std_ratio},
        "runs": results,
    }

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"\nQuantum ensemble artifact written to: {artifact_path}")

    return {"summary": artifact["summary"], "runs": results, "artifact_path": artifact_path}


if __name__ == "__main__":
    run_quantum_ensemble()


