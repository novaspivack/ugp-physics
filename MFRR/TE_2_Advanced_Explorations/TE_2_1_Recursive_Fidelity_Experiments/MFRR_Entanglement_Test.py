"""
MFRR_Entanglement_Test.py

Deriving non-locality (entanglement) and the effective speed of light (causality)
in the MFRR framework.

This experiment is part of TE_2.1 (Recursive Fidelity Experiments), specified in:
  TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/TE_2_1.1_Recursive Fidelity_Kickoff.md

Hypothesis:
1. "Light speed" is the propagation delay of information through the spatial
   neighbor graph (local MFRR updates).
2. "Entanglement" is a direct edge in the information graph that bypasses
   spatial distance (topological link in information space).
"""

import json
import os
import time
from typing import Dict, Any, List

import numpy as np


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_NODES = 50
CHAIN_LENGTH = 20.0  # physical length of the 1D universe
C_SPEED = 1.0        # nominal information speed in the mesh (units/step)
ENTANGLEMENT_STRENGTH = 5.0  # strength of the "spooky action" link
DIFFUSION_ALPHA = 0.8        # how aggressively local diffusion updates


class MFRR_Causal_Universe:
    def __init__(self, n_nodes: int) -> None:
        self.n_nodes = n_nodes

        # 1. Set up a 1D line of nodes (the "vacuum")
        self.X = np.linspace(0.0, CHAIN_LENGTH, n_nodes).reshape(-1, 1)

        # 2. Initialize state S (scalar in [-1, 1]) – all neutral vacuum initially
        self.S = np.zeros(n_nodes)

        # 3. Create an entangled pair (indices 0 and N-1) at opposite ends
        self.pair_a = 0
        self.pair_b = n_nodes - 1

        # Entanglement flag (topological link in information space)
        self.is_entangled = True

    def step(self, perturbation_val: float = 0.0) -> List[float]:
        """
        Evolve the system one tick.

        Spatial neighbors exchange information with a finite radius (simulating
        a speed limit), while the entangled pair can synchronize non-locally.
        """
        new_S = np.copy(self.S)

        # 1. Apply perturbation to node A (the "source" / measurement)
        if perturbation_val != 0.0:
            new_S[self.pair_a] = perturbation_val

        # 2. Spatial information propagation (local physics)
        # Each node updates based on its spatial neighbors within a fixed radius.
        radius = C_SPEED * 1.5  # interaction radius per tick (mesh-limited)
        for i in range(self.n_nodes):
            dists = np.abs(self.X - self.X[i]).flatten()
            neighbors = np.where((dists < radius) & (dists > 0.0))[0]
            if neighbors.size > 0:
                local_avg = float(np.mean(self.S[neighbors]))
                # Simple diffusion: S_new = S_old + alpha * (Avg - S_old)
                new_S[i] += DIFFUSION_ALPHA * (local_avg - self.S[i])

        # 3. Entanglement update (topological non-local link)
        if self.is_entangled:
            # Pull B towards A on the updated state in this same tick.
            err = new_S[self.pair_a] - new_S[self.pair_b]
            new_S[self.pair_b] += 0.8 * err  # fast snap towards A

        self.S = new_S
        return self.S.tolist()


def run_entanglement_test() -> Dict[str, Any]:
    print("Running MFRR Entanglement vs Light Speed Test...")

    universe = MFRR_Causal_Universe(N_NODES)

    history_a: List[float] = []
    history_b: List[float] = []
    history_mid: List[float] = []

    mid_node = N_NODES // 2

    print(f"Setup: Node A at X={float(universe.X[0]):.2f}, "
          f"Node B at X={float(universe.X[-1]):.2f}")
    print(f"Middle Node at X={float(universe.X[mid_node]):.2f}")
    print("Perturbing A at step t = 10...\n")

    reaction_time_b = -1
    reaction_time_mid = -1

    n_steps = 100
    for t in range(n_steps):
        perturb = 0.0
        if t == 10:
            perturb = 1.0  # "measurement" at A
        elif t > 10:
            perturb = 1.0  # hold A in the excited state

        states = universe.step(perturb)

        val_a = states[universe.pair_a]
        val_b = states[universe.pair_b]
        val_mid = states[mid_node]

        history_a.append(val_a)
        history_b.append(val_b)
        history_mid.append(val_mid)

        # Detect first significant reaction (thresholds above vacuum)
        if reaction_time_b == -1 and val_b > 0.1:
            reaction_time_b = t
        if reaction_time_mid == -1 and val_mid > 0.02:
            reaction_time_mid = t

        if t % 5 == 0:
            print(f"t={t:2d}: A={val_a:.2f} | Mid={val_mid:.2f} | B={val_b:.2f}")

    print("\n--- RESULTS ---")
    print("Perturbation at t = 10")
    print(f"Node B (distance ~{CHAIN_LENGTH:.1f}) reacted at t = {reaction_time_b}")
    print(f"Mid Node (distance ~{CHAIN_LENGTH/2:.1f}) reacted at t = {reaction_time_mid}")

    delay_b = reaction_time_b - 10 if reaction_time_b != -1 else None
    delay_mid = reaction_time_mid - 10 if reaction_time_mid != -1 else None

    print(f"Delay B (entangled): {delay_b} ticks")
    print(f"Delay Mid (causal):  {delay_mid} ticks\n")

    if delay_b is not None and delay_mid is not None and delay_b < delay_mid:
        print("CONCLUSION: SUCCESS. Entanglement is effectively superluminal.")
        print("Information bypassed the spatial manifold via a topological link.")
        print("ER = EPR behavior observed in this toy MFRR universe.")
    else:
        print("CONCLUSION: FAILED/INCONCLUSIVE. Local causality dominated.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(
        results_dir,
        f"MFRR_Entanglement_Test_{timestamp}.json",
    )

    artifact: Dict[str, Any] = {
        "history_a": history_a,
        "history_b": history_b,
        "history_mid": history_mid,
        "reaction_time_b": reaction_time_b,
        "reaction_time_mid": reaction_time_mid,
        "delay_b": delay_b,
        "delay_mid": delay_mid,
    }

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"Artifact saved to {artifact_path}")

    return {"artifact_path": artifact_path, **artifact}


if __name__ == "__main__":
    run_entanglement_test()


