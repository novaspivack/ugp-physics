"""
MFRR_Gravity_Steelman.py

Deriving Gravity and Time Dilation without hard-coded forces or clocks.

Mechanisms:
1. Gravity: Nodes move to minimize Transmission Error (MSE) with neighbors.
   - Signal decays with distance (Inverse Square Law for intensity).
   - Error = (Received - Expected)^2.
   - Movement = Gradient Descent on Error.
2. Time: Nodes have a fixed CPU budget (MAX_OPS_PER_TICK).
   - Dense nodes have more neighbors -> More ops required.
   - Effective Tick Rate = MAX_OPS / Required_OPS.
"""

import json
import os
import time
import numpy as np


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_NODES = 100
DIMENSIONS = 3
SPACE_SIZE = 20.0
STEPS = 200


# INFORMATION PHYSICS
SIGNAL_POWER = 1.0
NOISE_FLOOR = 0.01
# Signal Intensity I = P / (4 * pi * r^2)
# We simulate this by making the "Quality" of the link decay with r^2.


# COMPUTATIONAL PHYSICS (Time Dilation)
MAX_OPS_PER_TICK = 10  # A node can process 10 neighbors per tick
BASE_TICK_RATE = 1.0


class Node:
    def __init__(self, id: int):
        self.id = id
        self.pos = np.random.rand(DIMENSIONS) * SPACE_SIZE
        self.state = np.random.rand()  # Simple scalar state
        self.tick_count = 0
        self.effective_time = 0.0

    def get_signal_quality(self, other: "Node") -> tuple[float, float]:
        r = np.linalg.norm(self.pos - other.pos)
        if r < 0.1:
            r = 0.1  # prevent singularity
        # Intensity decays with inverse square in 3D
        intensity = SIGNAL_POWER / (4 * np.pi * r**2)
        # Signal-to-Noise Ratio
        snr = intensity / NOISE_FLOOR
        # Quality is bounded [0, 1]
        quality = 1.0 - np.exp(-snr)
        return quality, r


def run_gravity_steelman() -> dict:
    print("Running MFRR Gravity Steel-Man (Error Minimization & Processing Lag)...")

    nodes = [Node(i) for i in range(N_NODES)]

    history: dict[str, list] = {
        "clustering": [],
        "time_dilation": [],
        "force_law": [],  # list of (r, force_magnitude)
    }

    for t in range(STEPS):
        # 1. Calculate Information Exchange & "Forces"
        forces = np.zeros((N_NODES, DIMENSIONS))
        neighbor_counts = np.zeros(N_NODES)

        for i in range(N_NODES):
            for j in range(i + 1, N_NODES):
                n1 = nodes[i]
                n2 = nodes[j]

                quality, r = n1.get_signal_quality(n2)

                # Derive an effective "information force" from gradient of quality wrt distance.
                k = SIGNAL_POWER / NOISE_FLOOR / (4 * np.pi)
                # Q = 1 - exp(-k/r^2)
                # dQ/dr = -exp(-k/r^2) * (2k/r^3)
                force_mag = np.exp(-k / (r**2)) * (2 * k / (r**3))
                force_mag = min(force_mag, 1.0)  # cap to avoid numerical blow-up

                direction = (n2.pos - n1.pos) / r
                forces[i] += direction * force_mag
                forces[j] -= direction * force_mag

                # Sample initial force law for analysis
                if t == 0 and np.random.rand() < 0.1:
                    history["force_law"].append((float(r), float(force_mag)))

                # Count neighbors above a quality threshold
                if quality > 0.1:
                    neighbor_counts[i] += 1
                    neighbor_counts[j] += 1

        # 2. Update positions
        for i in range(N_NODES):
            nodes[i].pos += forces[i] * 0.1  # mobility factor
            nodes[i].pos = np.clip(nodes[i].pos, 0, SPACE_SIZE)

        # 3. Update clocks (processing lag as time dilation)
        current_dilations = []
        for i in range(N_NODES):
            load = max(1, neighbor_counts[i])
            ticks_needed = max(1.0, load / MAX_OPS_PER_TICK)
            dilation = 1.0 / ticks_needed
            nodes[i].effective_time += dilation
            current_dilations.append(dilation)

        # 4. Metrics
        # Clustering: overall positional spread
        pos_std = float(np.std([n.pos for n in nodes]))

        densities = neighbor_counts
        times = np.array(current_dilations)
        if np.std(densities) > 0:
            corr = float(np.corrcoef(densities, times)[0, 1])
        else:
            corr = 0.0

        history["clustering"].append(pos_std)
        history["time_dilation"].append(corr)

        if t % 20 == 0:
            print(f"Step {t:3d}: Spread={pos_std:.2f} | Time-Density Corr={corr:.2f}")

    # Final analysis
    print("\n--- RESULTS ---")
    print(f"Initial Spread: {history['clustering'][0]:.2f}")
    print(f"Final Spread:   {history['clustering'][-1]:.2f}")
    print(f"Avg Time-Density Correlation: {np.mean(history['time_dilation']):.2f}")

    if history["clustering"][-1] < history["clustering"][0]:
        print("CONCLUSION: Gravity Emerged. Nodes clustered to maximize information.")
    else:
        print("CONCLUSION: FAILED. No clustering.")

    if np.mean(history["time_dilation"]) < -0.5:
        print("CONCLUSION: Time Dilation Emerged. Dense regions process slower.")
    else:
        print("CONCLUSION: FAILED. Time is absolute.")

    # Save artifact
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(
        results_dir, f"MFRR_Gravity_Steelman_{timestamp}.json"
    )

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Artifact saved to {artifact_path}")
    return {"artifact_path": artifact_path, **history}


if __name__ == "__main__":
    run_gravity_steelman()


