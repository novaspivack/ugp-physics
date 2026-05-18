"""
MFRR_Gravity_Genesis.py

Emergent spacetime curvature via Maximal Fidelity Representation Recursion (MFRR).

This module implements the "MFRR Gravity Genesis" simulation described in:
  TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/TE_2_1.1_Recursive Fidelity_Kickoff.md

The goal is to test the hypothesis that gravity and dark-energy-like behavior
can emerge from a purely informational fidelity optimization process.
"""

import json
import os
import time
from typing import Dict, Any, List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
import matplotlib.animation as animation


# ---------------------------------------------------------
# MFRR THEORETICAL CONSTANTS
# ---------------------------------------------------------
# Adam's Constant: Coupling of Information to Geometry
KAPPA = 1.0
# Carl's Constant: The Complexity Penalty (Cosmological Constant)
LAMBDA_COMPLEXITY = 0.005
# The Dimension of the Abstract Information Space
S_DIM = 10
# Number of Particles (Information Nodes)
N_NODES = 50


class MFRR_Universe:
    def __init__(self, n_nodes: int, s_dim: int) -> None:
        """
        Initialize the Universe with random Information States S[i].
        We treat 'positions' in the emergent manifold as variables to be optimized.
        """
        self.n_nodes = n_nodes
        self.s_dim = s_dim

        # S[i]: The intrinsic information content of each node.
        self.S = np.random.randn(n_nodes, s_dim)
        self.S /= np.linalg.norm(self.S, axis=1, keepdims=True)  # Normalize

        # X[i]: The coordinates in the emergent manifold (3D).
        self.X = np.random.randn(n_nodes, 3) * 5.0

        # Velocity for momentum-based optimization.
        self.V = np.zeros_like(self.X)

        # Proper Time (tau) for each node: experienced duration of the node.
        self.proper_time = np.zeros(n_nodes)

    def compute_fidelity_potential(self) -> float:
        """
        Calculate the potential energy (for monitoring).
        """
        dist_matrix = squareform(pdist(self.X))
        epsilon = 1e-5
        dist_matrix = np.maximum(dist_matrix, epsilon)

        affinity = np.dot(self.S, self.S.T)
        np.fill_diagonal(affinity, 0)

        fidelity_potential = -np.sum(affinity / dist_matrix)
        entropy_potential = LAMBDA_COMPLEXITY * np.sum(1.0 / dist_matrix)

        return fidelity_potential + entropy_potential

    def compute_gradients_and_dilation(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Derive forces (gradients) and time-dilation factors.

        Returns
        -------
        forces : np.ndarray
            Vector forces on X.
        dilation_factors : np.ndarray
            Rate of proper time flow d_tau/dt.
            Values < 1.0 mean time is moving slower (deeper in an information well).
        """
        # Squared distances
        dist_sq = squareform(pdist(self.X, "sqeuclidean"))
        epsilon = 1e-5
        dist_sq = np.maximum(dist_sq, epsilon)
        dist = np.sqrt(dist_sq)

        # Affinity (information correlation)
        affinity = np.dot(self.S, self.S.T)
        np.fill_diagonal(affinity, 0)

        forces = np.zeros_like(self.X)

        # Local information potential for time dilation:
        # Phi_i ~ sum_j Affinity_ij / Distance_ij
        local_potential = np.zeros(self.n_nodes)

        for i in range(self.n_nodes):
            diff = self.X[i] - self.X
            d3 = dist[i, :] ** 3
            d1 = dist[i, :]

            # Force coefficient
            coeff = (affinity[i, :] - LAMBDA_COMPLEXITY) / d3
            coeff[i] = 0.0
            forces[i] = -np.sum(diff * coeff[:, np.newaxis], axis=0)

            # Potential terms for time dilation (computational load)
            pot_terms = affinity[i, :] / d1
            pot_terms[i] = 0.0
            local_potential[i] = np.sum(pot_terms)

        # Time dilation factor:
        # d_tau = dt * (1 / (1 + alpha * InformationDensity))
        alpha = 0.5  # coupling constant for time dilation
        dilation_factors = 1.0 / (1.0 + alpha * local_potential)

        return forces, dilation_factors

    def step(self, dt: float = 0.01, friction: float = 0.98) -> float:
        """
        Evolve the universe one time step.

        Updates positions (space) and proper time (time).
        Returns the norm of the total force field as a simple convergence metric.
        """
        forces, dilation_factors = self.compute_gradients_and_dilation()

        # Symplectic Euler integration for space
        self.V += forces * dt
        self.V *= friction
        self.X += self.V * dt

        # Euler integration for time
        self.proper_time += dt * dilation_factors

        return float(np.linalg.norm(forces))


# ---------------------------------------------------------
# ANALYSIS HELPERS
# ---------------------------------------------------------


def compute_distance_stats(
    universe: MFRR_Universe,
    high_threshold: float = 0.5,
    low_threshold: float = 0.0,
) -> Tuple[float, float]:
    """
    Compute average distances for high-fidelity and low-fidelity pairs.

    This is the core diagnostic: in a gravity-like phase we expect
    avg_dist_high < avg_dist_low.
    """
    dist_matrix = squareform(pdist(universe.X))
    affinity = np.dot(universe.S, universe.S.T)

    high_aff_mask = affinity > high_threshold
    low_aff_mask = affinity < low_threshold

    if np.any(high_aff_mask):
        avg_dist_high = float(np.mean(dist_matrix[high_aff_mask]))
    else:
        avg_dist_high = float("nan")

    if np.any(low_aff_mask):
        avg_dist_low = float(np.mean(dist_matrix[low_aff_mask]))
    else:
        avg_dist_low = float("nan")

    return avg_dist_high, avg_dist_low


def run_single_experiment(
    seed: int,
    n_nodes: int = N_NODES,
    s_dim: int = S_DIM,
    frames: int = 200,
    dt: float = 0.05,
    sample_stride: int = 10,
) -> Dict[str, Any]:
    """
    Run a single numeric experiment tracking space AND time.

    Returns a dictionary with:
    - final spatial clustering statistics
    - coarse time series of high- vs low-fidelity pair distances
    - average proper time for cluster vs void nodes and their ratio
    """
    np.random.seed(seed)
    universe = MFRR_Universe(n_nodes, s_dim)

    steps: List[int] = []
    d_high_series: List[float] = []
    d_low_series: List[float] = []

    for step_idx in range(frames):
        _ = universe.step(dt=dt)
        if (step_idx % sample_stride == 0) or (step_idx == frames - 1):
            avg_high, avg_low = compute_distance_stats(universe)
            steps.append(step_idx)
            d_high_series.append(avg_high)
            d_low_series.append(avg_low)

    final_high, final_low = compute_distance_stats(universe)
    # Time dilation analysis: compare proper time in clusters vs void.
    # We classify nodes by their current dilation factors (lower = deeper well).
    _, dilation_factors = universe.compute_gradients_and_dilation()

    sorted_indices = np.argsort(dilation_factors)
    # Deepest quarter = cluster core; shallowest quarter = void
    cluster_indices = sorted_indices[: n_nodes // 4]
    void_indices = sorted_indices[-(n_nodes // 4) :]

    avg_time_cluster = float(np.mean(universe.proper_time[cluster_indices]))
    avg_time_void = float(np.mean(universe.proper_time[void_indices]))
    time_dilation_ratio = avg_time_cluster / avg_time_void if avg_time_void != 0 else float("nan")

    return {
        "seed": seed,
        "n_nodes": n_nodes,
        "s_dim": s_dim,
        "frames": frames,
        "dt": dt,
        "final_avg_dist_high": final_high,
        "final_avg_dist_low": final_low,
        "avg_proper_time_cluster": avg_time_cluster,
        "avg_proper_time_void": avg_time_void,
        "time_dilation_ratio": time_dilation_ratio,
        "steps": steps,
        "series_avg_dist_high": d_high_series,
        "series_avg_dist_low": d_low_series,
    }


def run_ensemble(
    num_seeds: int = 32,
    n_nodes: int = N_NODES,
    s_dim: int = S_DIM,
    frames: int = 200,
    dt: float = 0.05,
    sample_stride: int = 10,
) -> Dict[str, Any]:
    """
    Run an ensemble of seeded experiments and compute space and time statistics.
    """
    print(
        f"Running ensemble: num_seeds={num_seeds}, "
        f"n_nodes={n_nodes}, s_dim={s_dim}, frames={frames}, dt={dt}"
    )

    all_results: List[Dict[str, Any]] = []
    final_high_vals: List[float] = []
    final_low_vals: List[float] = []
    dilation_ratios: List[float] = []

    for seed in range(num_seeds):
        res = run_single_experiment(
            seed=seed,
            n_nodes=n_nodes,
            s_dim=s_dim,
            frames=frames,
            dt=dt,
            sample_stride=sample_stride,
        )
        all_results.append(res)
        final_high_vals.append(res["final_avg_dist_high"])
        final_low_vals.append(res["final_avg_dist_low"])
        dilation_ratios.append(res["time_dilation_ratio"])

        print(
            f"Seed {seed:3d}: Space(H/L)={res['final_avg_dist_high']:.1f}/"
            f"{res['final_avg_dist_low']:.1f} | "
            f"Time Ratio={res['time_dilation_ratio']:.4f}"
        )

    high_arr = np.array(final_high_vals)
    low_arr = np.array(final_low_vals)
    ratio_arr = np.array(dilation_ratios)

    high_mean = float(np.nanmean(high_arr))
    low_mean = float(np.nanmean(low_arr))
    ratio_mean = float(np.nanmean(ratio_arr))
    ratio_std = float(np.nanstd(ratio_arr, ddof=1))

    summary: Dict[str, Any] = {
        "num_seeds": num_seeds,
        "n_nodes": n_nodes,
        "s_dim": s_dim,
        "frames": frames,
        "dt": dt,
        "sample_stride": sample_stride,
        "final_avg_dist_high_mean": high_mean,
        "final_avg_dist_low_mean": low_mean,
        "time_dilation_ratio_mean": ratio_mean,
        "time_dilation_ratio_std": ratio_std,
    }

    print("\nEnsemble summary:")
    print(f"  mean d_high = {high_mean:.4f}")
    print(f"  mean d_low  = {low_mean:.4f}")
    print(f"  Mean Time Dilation Ratio (Cluster/Void) = {ratio_mean:.4f} ± {ratio_std:.4f}")
    if ratio_mean < 1.0:
        print("  CONCLUSION: Time moves SLOWER in high-fidelity clusters.")
    else:
        print("  CONCLUSION: No time dilation detected.")

    # Persist results as a TE_2 artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(
        results_dir,
        f"MFRR_Gravity_Time_ensemble_{timestamp}.json",
    )

    artifact = {
        "description": "Ensemble MFRR space-time genesis (gravity + time dilation).",
        "module_path": os.path.abspath(__file__),
        "summary": summary,
        "runs": all_results,
    }

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"\nEnsemble artifact written to: {artifact_path}")

    return {"summary": summary, "runs": all_results, "artifact_path": artifact_path}


# ---------------------------------------------------------
# VISUALIZATION AND SINGLE-RUN EXECUTION
# ---------------------------------------------------------

def run_simulation(n_nodes: int = N_NODES, s_dim: int = S_DIM, frames: int = 200, dt: float = 0.05,
                   with_animation: bool = True) -> None:
    """
    Run the MFRR Gravity Genesis simulation.

    Parameters
    ----------
    n_nodes : int
        Number of information nodes.
    s_dim : int
        Dimension of the intrinsic information state vectors.
    frames : int
        Number of animation / evolution steps.
    dt : float
        Time-step for the symplectic Euler integrator.
    with_animation : bool
        If True, display an interactive matplotlib animation. In headless or
        batch environments, set to False to skip the GUI while still performing
        the evolution and final analysis.
    """
    print("Initializing MFRR Gravity Genesis...")
    print("Hypothesis: Gravity emerges from Information Fidelity Optimization.")

    universe = MFRR_Universe(n_nodes, s_dim)

    if with_animation:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        # Color nodes by their primary information component for visual tracking
        colors = universe.S[:, 0]

        scat = ax.scatter(universe.X[:, 0], universe.X[:, 1], universe.X[:, 2],
                          c=colors, cmap="viridis", s=50)

        # Lines connecting high-affinity nodes (the "metric" connections)
        lines = []

        def init():
            ax.set_xlim(-10, 10)
            ax.set_ylim(-10, 10)
            ax.set_zlim(-10, 10)
            ax.set_title("MFRR Genesis: Emergent Geometry from Fidelity")
            return scat,

        def update(frame_idx):
            force_mag = universe.step(dt=dt)

            # Update positions
            scat._offsets3d = (universe.X[:, 0], universe.X[:, 1], universe.X[:, 2])

            # Visualize the "metric tensor" (connections)
            # Only draw lines between nodes with high mutual information (affinity)
            # This represents the "fabric of spacetime" knitting together.
            for ln in lines:
                ln.remove()
            lines.clear()

            affinity = np.dot(universe.S, universe.S.T)
            threshold = 0.5  # only strong information links create geometry

            count = 0
            for i in range(universe.n_nodes):
                for j in range(i + 1, universe.n_nodes):
                    if affinity[i, j] > threshold:
                        # Check distance to see if they successfully clustered
                        dist_ij = np.linalg.norm(universe.X[i] - universe.X[j])
                        alpha = max(0.0, 1.0 - dist_ij / 5.0)  # fade out if too far
                        if alpha > 0.1:
                            line, = ax.plot(
                                [universe.X[i, 0], universe.X[j, 0]],
                                [universe.X[i, 1], universe.X[j, 1]],
                                [universe.X[i, 2], universe.X[j, 2]],
                                color="black", alpha=alpha * 0.3, lw=0.5,
                            )
                            lines.append(line)
                            count += 1
                            if count > 100:
                                break
                if count > 100:
                    break

            ax.set_title(f"Epoch {frame_idx}: Force Magnitude {force_mag:.4f}")
            return scat, lines

        print("Starting animation... Close window to stop.")
        animation.FuncAnimation(fig, update, frames=frames,
                                init_func=init, blit=False, interval=50)
        plt.show()
    else:
        # Purely numeric evolution without GUI, suitable for headless runs.
        print(f"Running {frames} numeric evolution steps (no animation)...")
        for step_idx in range(frames):
            force_mag = universe.step(dt=dt)
            if step_idx % 20 == 0:
                print(f"Step {step_idx:4d}: |F| = {force_mag:.4f}")

    # Final analysis
    print("Simulation complete.")
    print("Analyzing resulting manifold distances for fidelity-induced clustering...")

    avg_dist_high, avg_dist_low = compute_distance_stats(universe)

    print(f"Average Distance (High Fidelity Pairs): {avg_dist_high:.4f}")
    print(f"Average Distance (Low Fidelity Pairs):  {avg_dist_low:.4f}")

    if np.isfinite(avg_dist_high) and np.isfinite(avg_dist_low) and avg_dist_high < avg_dist_low:
        print("CONCLUSION: SUCCESS. Geometry has warped to accommodate information fidelity.")
        print("Gravity-like clustering has emerged from the MFRR protocol.")
    else:
        print("CONCLUSION: INCONCLUSIVE/FAILED. No clear geometric convergence in this run.")


if __name__ == "__main__":
    # Default behavior: single interactive or numeric run.
    # For TE_2 ensemble experiments, import this module and call `run_ensemble`.
    run_simulation()


