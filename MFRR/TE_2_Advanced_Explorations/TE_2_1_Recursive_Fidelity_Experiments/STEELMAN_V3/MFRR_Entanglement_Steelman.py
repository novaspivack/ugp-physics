"""
MFRR_Entanglement_Steelman.py

Deriving ER = EPR via Topological Thermodynamics.

This module is part of the TE_2_1 Recursive Fidelity experiment suite:
see `TE_2_1.2_Recursive_Fidelity_Results.md` for lab notes and analysis.

Hypothesis:
    A "wormhole" (direct topological link) is the thermodynamic ground state
    of a graph where two distant nodes have high mutual information.
    The topology deforms to minimize an energy functional combining:
    - Wire cost (sparse, short edges preferred),
    - Latency cost (correlated nodes prefer short graph distance).
"""

import json
import os
import time
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_NODES = 40  # reduced for tractable all-pairs distances
STEPS = 300
MC_STEPS_PER_TICK = 10  # topology proposals per physics tick

# PHYSICS
WIRE_COST = 2.0      # cost per edge
LATENCY_COST = 5.0   # cost per unit correlation-distance


class Universe:
    def __init__(self) -> None:
        self.nodes = np.zeros(N_NODES, dtype=float)
        self.graph = nx.path_graph(N_NODES)  # initial 1D chain
        self.history = np.zeros((STEPS, N_NODES), dtype=float)
        self.correlations = np.zeros((N_NODES, N_NODES), dtype=float)

    # ----------------------------- Physics ------------------------------
    def step_physics(self, t: int) -> None:
        """Diffusive dynamics on the current graph plus an entanglement driver."""
        new_nodes = self.nodes.copy()

        # 1. Local diffusion on graph
        for i in range(N_NODES):
            neighbors = list(self.graph.neighbors(i))
            if not neighbors:
                continue
            local_avg = float(np.mean([self.nodes[n] for n in neighbors]))
            new_nodes[i] += 0.5 * (local_avg - self.nodes[i])

        # 2. Entanglement driver: keep nodes 0 and N-1 in sync for most of the run
        if t < 200:
            signal = np.sin(t * 0.5)
            new_nodes[0] = signal
            new_nodes[N_NODES - 1] = signal

        # 3. Perturbation test: send a sharp spike late in the run
        if t == 250:
            new_nodes[0] = 10.0

        self.nodes = new_nodes
        self.history[t] = self.nodes

    def update_correlations(self, t: int, window: int = 50) -> None:
        """Update correlation matrix from recent history window."""
        if t < 20:
            return
        start = max(0, t - window)
        data = self.history[start:t].T  # shape: (N_NODES, window)
        # Add tiny noise to avoid degenerate covariance
        data = data + np.random.normal(0.0, 0.01, size=data.shape)
        self.correlations = np.abs(np.corrcoef(data))
        np.fill_diagonal(self.correlations, 0.0)

    # --------------------------- Energy Model ---------------------------
    def _all_pairs_shortest_paths(self) -> Dict[int, Dict[int, int]]:
        try:
            return dict(nx.all_pairs_shortest_path_length(self.graph))
        except nx.NetworkXError:
            # If graph becomes disconnected, treat energy as infinite
            return {}

    def calculate_energy(self) -> float:
        """
        H = Wire_Cost * Num_Edges
            + Latency_Cost * sum_{i<j} Corr_ij * GraphDist_ij   (for Corr_ij > 0.5)
        """
        # 1. Wire cost
        num_edges = self.graph.number_of_edges()
        e_wire = WIRE_COST * num_edges

        # 2. Latency cost
        path_lengths = self._all_pairs_shortest_paths()
        if not path_lengths:
            # disconnected or error
            return float("inf")

        e_latency = 0.0
        for i in range(N_NODES):
            for j in range(i + 1, N_NODES):
                corr = float(self.correlations[i, j])
                if corr <= 0.5:
                    continue
                try:
                    dist = path_lengths[i][j]
                except KeyError:
                    # unreachable: heavy penalty
                    e_latency += 1000.0
                    continue
                e_latency += LATENCY_COST * corr * dist

        return e_wire + e_latency

    # ------------------------ Topology Dynamics ------------------------
    def step_topology(self) -> None:
        """One Metropolis-Hastings step on the graph topology."""
        current_energy = self.calculate_energy()

        # Randomly propose add/remove edge
        u, v = np.random.choice(N_NODES, 2, replace=False)
        had_edge = self.graph.has_edge(u, v)

        if had_edge:
            self.graph.remove_edge(u, v)
            # avoid disconnecting the graph (simplification)
            if not nx.is_connected(self.graph):
                self.graph.add_edge(u, v)
                return
        else:
            self.graph.add_edge(u, v)

        new_energy = self.calculate_energy()
        delta_E = new_energy - current_energy

        if delta_E <= 0:
            # Accept improvement or neutral move
            return

        # Finite-temperature Metropolis acceptance
        T = 0.1
        accept_prob = np.exp(-delta_E / T)
        if np.random.rand() < accept_prob:
            return

        # Reject: revert the change
        if had_edge:
            self.graph.add_edge(u, v)
        else:
            self.graph.remove_edge(u, v)


def run_entanglement_steelman() -> Tuple[int, bool]:
    print("Running MFRR Entanglement Steel-Man (Thermodynamic Topology)...")

    u = Universe()
    delays: List[int] = []

    for t in range(STEPS):
        u.step_physics(t)

        if t % 5 == 0:
            u.update_correlations(t)

        if 50 < t < 240:
            for _ in range(MC_STEPS_PER_TICK):
                u.step_topology()

        # Logging and wormhole check
        if t % 50 == 0:
            edges = u.graph.number_of_edges()
            print(f"Step {t:3d}: Edges={edges}")
            if u.graph.has_edge(0, N_NODES - 1):
                print("  >>> WORMHOLE DETECTED (0 <-> N-1)")

        # Signal propagation: after spike at t=250
        if t > 250:
            val_end = u.nodes[N_NODES - 1]
            if val_end > 1.0:
                delay = t - 250
                print(f"SIGNAL RECEIVED at Step {t}. Delay: {delay}")
                delays.append(delay)
                break

    # Final graph analysis
    has_wormhole = bool(u.graph.has_edge(0, N_NODES - 1))
    dist = int(nx.shortest_path_length(u.graph, 0, N_NODES - 1))

    print("\n--- RESULTS ---")
    print(f"Final Distance (0 to {N_NODES-1}): {dist}")
    print(f"Direct Wormhole Exists: {has_wormhole}")

    if dist <= 2:
        print("CONCLUSION: SUCCESS. Topology deformed to minimize information tension.")
        print("ER = EPR derived via thermodynamic optimization.")
    else:
        print("CONCLUSION: FAILED. Space remained effectively flat.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Entanglement_Steelman_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "final_edges": [tuple(map(int, e)) for e in u.graph.edges()],
                "final_dist": dist,
                "has_wormhole": has_wormhole,
                "delays": [int(d) for d in delays],
                "params": {
                    "N_NODES": N_NODES,
                    "STEPS": STEPS,
                    "MC_STEPS_PER_TICK": MC_STEPS_PER_TICK,
                    "WIRE_COST": WIRE_COST,
                    "LATENCY_COST": LATENCY_COST,
                },
            },
            f,
            indent=2,
        )

    return dist, has_wormhole


if __name__ == "__main__":
    run_entanglement_steelman()


