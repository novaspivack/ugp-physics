"""
MFRR_Observer_Genesis_v3.py

Deriving Agency: The Necessity of Inertia.

Hypothesis:
In a universe where objects have momentum (temporal correlation),
predictive strategies (interception) dominate reactive strategies (pursuit).
"""

import json
import os
import time
from typing import Dict, Any, List
import numpy as np


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
N_AGENTS_PER_TYPE = 50
N_RESOURCES = 10
FRAMES = 600
DT = 0.1
FIELD_SIZE = 25.0


# EVOLUTIONARY PRESSURE
AGENT_SPEED = 0.6
RESOURCE_SPEED = 0.75
CAPTURE_RADIUS = 0.8
PREDICTION_WINDOW = 5


class Resource:
    def __init__(self, id: int):
        self.id = id
        self.pos = np.random.randn(2) * 5.0
        # initialize velocity with constant speed
        vel = np.random.randn(2)
        vel /= np.linalg.norm(vel)
        self.vel = vel * RESOURCE_SPEED

    def update_pos(self, t: float) -> np.ndarray:
        # Momentum walk (inertia) with small random perturbations
        perturbation = np.random.randn(2) * 0.1
        self.vel += perturbation

        # normalize to maintain constant speed
        speed = np.linalg.norm(self.vel)
        if speed > 0:
            self.vel = (self.vel / speed) * RESOURCE_SPEED

        # soft boundary: bounce off "walls"
        if abs(self.pos[0]) > FIELD_SIZE:
            self.vel[0] *= -1
        if abs(self.pos[1]) > FIELD_SIZE:
            self.vel[1] *= -1

        self.pos += self.vel * DT
        return self.pos


class Agent:
    def __init__(self, type_name: str):
        self.type = type_name
        self.pos = np.random.randn(2) * 5.0
        self.energy = 0.0

    def move(self, target_pos: np.ndarray, dt: float) -> None:
        direction = target_pos - self.pos
        dist = np.linalg.norm(direction)
        if dist > 0:
            direction /= dist
            step = min(dist, AGENT_SPEED * dt)
            self.pos += direction * step


class ReflexiveAgent(Agent):
    def __init__(self):
        super().__init__("Reflexive")
        self.history: List[np.ndarray] = []

    def decide_target(self, resources: List[Resource], t: float) -> np.ndarray:
        # 1. nearest resource
        dists = [np.linalg.norm(r.pos - self.pos) for r in resources]
        nearest_idx = int(np.argmin(dists))
        nearest_r = resources[nearest_idx]

        # 2. update history
        self.history.append(nearest_r.pos.copy())
        if len(self.history) > PREDICTION_WINDOW:
            self.history.pop(0)

        # 3. predict interception
        if len(self.history) >= 2:
            delta = self.history[-1] - self.history[0]
            avg_vel = delta / (len(self.history) - 1)  # per frame
            dist = dists[nearest_idx]

            steps_to_reach = dist / (AGENT_SPEED * DT)
            lookahead_steps = min(steps_to_reach, 15.0)

            predicted_pos = nearest_r.pos + avg_vel * lookahead_steps
            return predicted_pos
        else:
            return nearest_r.pos


class PassiveAgent(Agent):
    def __init__(self):
        super().__init__("Passive")

    def decide_target(self, resources: List[Resource], t: float) -> np.ndarray:
        dists = [np.linalg.norm(r.pos - self.pos) for r in resources]
        nearest_idx = int(np.argmin(dists))
        return resources[nearest_idx].pos


def run_observer_genesis(num_seeds: int = 32) -> Dict[str, Any]:
    print(f"Running MFRR Observer Genesis v3 ({num_seeds} seeds)...")
    print(f"Condition: Inertial Resources. Speed {RESOURCE_SPEED} > Agent {AGENT_SPEED}")

    results: List[Dict[str, Any]] = []

    for seed in range(num_seeds):
        np.random.seed(seed)

        resources = [Resource(i) for i in range(N_RESOURCES)]
        passive_pop = [PassiveAgent() for _ in range(N_AGENTS_PER_TYPE)]
        reflexive_pop = [ReflexiveAgent() for _ in range(N_AGENTS_PER_TYPE)]

        for frame in range(FRAMES):
            t = frame * DT

            for r in resources:
                r.update_pos(t)

            # passive
            for a in passive_pop:
                target = a.decide_target(resources, t)
                a.move(target, DT)
                if min(np.linalg.norm(a.pos - r.pos) for r in resources) < CAPTURE_RADIUS:
                    a.energy += 1.0

            # reflexive
            for a in reflexive_pop:
                target = a.decide_target(resources, t)
                a.move(target, DT)
                if min(np.linalg.norm(a.pos - r.pos) for r in resources) < CAPTURE_RADIUS:
                    a.energy += 1.0

        avg_passive = float(np.mean([a.energy for a in passive_pop]))
        avg_reflexive = float(np.mean([a.energy for a in reflexive_pop]))

        if avg_passive < 0.1:
            avg_passive = 0.1
        ratio = avg_reflexive / avg_passive

        results.append({"seed": seed, "ratio": ratio, "avg_passive": avg_passive, "avg_reflexive": avg_reflexive})
        print(f"Seed {seed:3d}: Passive={avg_passive:.1f} | Reflexive={avg_reflexive:.1f} | Ratio={ratio:.2f}")

    ratios = [r["ratio"] for r in results]
    mean_ratio = float(np.mean(ratios))
    std_ratio = float(np.std(ratios, ddof=1)) if len(ratios) > 1 else float("nan")

    print("\nObserver Genesis v3 Summary:")
    print(f"Mean Performance Ratio: {mean_ratio:.4f} ± {std_ratio:.4f}")

    if mean_ratio > 1.2:
        print("CONCLUSION: SUCCESS. Agency dominates in an inertial universe.")
    else:
        print("CONCLUSION: FAILED.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(results_dir, f"MFRR_Observer_Genesis_v3_{timestamp}.json")

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump({"summary": {"mean_ratio": mean_ratio, "std_ratio": std_ratio}, "runs": results}, f, indent=2)

    return {"artifact_path": artifact_path, "mean_ratio": mean_ratio, "std_ratio": std_ratio, "runs": results}


if __name__ == "__main__":
    run_observer_genesis()


