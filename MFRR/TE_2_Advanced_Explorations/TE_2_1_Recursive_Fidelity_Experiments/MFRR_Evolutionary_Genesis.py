"""
MFRR_Evolutionary_Genesis_v2.py

Deriving the Information Profit Principle via Neuro-Evolution (Curriculum Phase).

Changes from v1:
1. Inputs: Added Target Velocity (allows analytical interception).
2. Fitness: Based on Total Gathered Energy (rewards activity).
3. Physics: Smoother resource trajectories, lower metabolic cost.
4. Goal: Demonstrate convergence to Profit Ratio > 1.13.
"""

import json
import os
import time
import numpy as np


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
FIELD_SIZE = 40.0
FRAMES = 900
DT = 0.1
GENERATIONS = 80

# EVOLUTION PARAMETERS
POPULATION_SIZE = 60
MUTATION_RATE = 0.1
MUTATION_SCALE = 0.08  # Further reduced volatility
ELITISM = 0.2         # Protect top 20%

# PHYSICS & METABOLISM
AGENT_SPEED = 1.0
RESOURCE_SPEED = 0.9  # Slightly slower to allow catching, but still fast
SENSOR_RANGE = 15.0   # Increased range
FOV_ANGLE = np.pi / 1.5

# MFRR-SPECIFIC DYNAMICS (Softened)
METABOLIC_COST = 0.0015      # Softer baseline cost
RESOURCE_DECAY_RATE = 0.0015 # Softer decay; resources persist longer
RESOURCE_MAX_COHERENCE = 1.0
INITIAL_RESOURCES = 60       # Was 30


class Brain:
    """
    Feed-Forward Neural Network.

    Input: 6
      [Dist, Angle, My_Vx, My_Vy, Target_Vx, Target_Vy]
    Hidden: 8 neurons
    Output: 2
      [Thrust_X, Thrust_Y]
    """

    def __init__(self, weights=None):
        self.input_size = 6
        self.hidden_size = 8
        self.output_size = 2

        if weights is None:
            self.w1 = np.random.randn(self.input_size, self.hidden_size)
            self.b1 = np.random.randn(self.hidden_size)
            self.w2 = np.random.randn(self.hidden_size, self.output_size)
            self.b2 = np.random.randn(self.output_size)
        else:
            self.w1, self.b1, self.w2, self.b2 = weights

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        z1 = np.dot(inputs, self.w1) + self.b1
        a1 = np.maximum(0, z1)
        z2 = np.dot(a1, self.w2) + self.b2
        output = np.tanh(z2)
        return output

    def mutate(self) -> "Brain":
        nw1 = self.w1 + np.random.randn(*self.w1.shape) * MUTATION_SCALE * (
            np.random.rand(*self.w1.shape) < MUTATION_RATE
        )
        nb1 = self.b1 + np.random.randn(*self.b1.shape) * MUTATION_SCALE * (
            np.random.rand(*self.b1.shape) < MUTATION_RATE
        )
        nw2 = self.w2 + np.random.randn(*self.w2.shape) * MUTATION_SCALE * (
            np.random.rand(*self.w2.shape) < MUTATION_RATE
        )
        nb2 = self.b2 + np.random.randn(*self.b2.shape) * MUTATION_SCALE * (
            np.random.rand(*self.b2.shape) < MUTATION_RATE
        )
        return Brain((nw1, nb1, nw2, nb2))


class Resource:
    def __init__(self):
        self.pos = np.random.rand(2) * FIELD_SIZE
        self.vel = np.random.randn(2)
        self.vel /= np.linalg.norm(self.vel)
        self.vel *= RESOURCE_SPEED
        self.coherence = 1.0
        self.active = True

    def update(self, dt: float, is_observed: bool) -> None:
        # Physics: momentum walk (smoother)
        perturbation = np.random.randn(2) * 0.05  # reduced noise
        self.vel += perturbation
        speed = np.linalg.norm(self.vel)
        if speed > 0:
            self.vel = (self.vel / speed) * RESOURCE_SPEED

        self.pos += self.vel * dt

        # Bounce
        if self.pos[0] < 0 or self.pos[0] > FIELD_SIZE:
            self.vel[0] *= -1
        if self.pos[1] < 0 or self.pos[1] > FIELD_SIZE:
            self.vel[1] *= -1

        # MFRR dynamics
        if is_observed:
            self.coherence = min(self.coherence + 0.05, RESOURCE_MAX_COHERENCE)
        else:
            self.coherence -= RESOURCE_DECAY_RATE

        if self.coherence <= 0:
            self.active = False


class Agent:
    def __init__(self, brain: Brain | None = None):
        self.pos = np.random.rand(2) * FIELD_SIZE
        self.vel = np.zeros(2)
        self.brain = brain if brain is not None else Brain()
        self.energy = 1.0
        self.generation_energy = 0.0  # fitness metric
        self.drain_energy = 0.0

    def update(self, resources: list[Resource], dt: float) -> Resource | None:
        # 1. sense
        nearest = None
        min_dist = SENSOR_RANGE
        for r in resources:
            if not r.active:
                continue
            d = np.linalg.norm(r.pos - self.pos)
            if d < min_dist:
                min_dist = d
                nearest = r

        inputs = np.zeros(6, dtype=float)
        if nearest:
            rel = nearest.pos - self.pos
            dist = np.linalg.norm(rel)
            angle = np.arctan2(rel[1], rel[0])
            inputs[0] = dist / SENSOR_RANGE
            inputs[1] = angle / np.pi
            inputs[2] = self.vel[0] / AGENT_SPEED
            inputs[3] = self.vel[1] / AGENT_SPEED
            # target velocity
            inputs[4] = nearest.vel[0] / RESOURCE_SPEED
            inputs[5] = nearest.vel[1] / RESOURCE_SPEED

        # 2. think
        thrust = self.brain.forward(inputs)

        # 3. act
        target_vel = thrust * AGENT_SPEED
        self.vel = self.vel * 0.8 + target_vel * 0.2
        self.pos += self.vel * dt
        self.pos = np.clip(self.pos, 0, FIELD_SIZE)

        # 4. metabolism
        move_cost = np.linalg.norm(thrust) * 0.002
        cost = METABOLIC_COST + move_cost
        self.energy -= cost
        self.drain_energy += cost

        return nearest


def run_evolutionary_genesis_v2() -> dict:
    print(f"Running MFRR Evolutionary Genesis v2 ({GENERATIONS} generations)...")
    print("Hypothesis: With velocity inputs and survivable physics, Profit Ratio > 1.13 will emerge.")

    agents = [Agent() for _ in range(POPULATION_SIZE)]
    history: list[dict] = []

    best_profit_overall = 0.0
    best_gen_idx = -1

    for gen in range(GENERATIONS):
        resources = [Resource() for _ in range(INITIAL_RESOURCES)]

        for frame in range(FRAMES):
            observed_resources: set[Resource] = set()

            for a in agents:
                if a.energy <= 0:
                    continue

                target = a.update(resources, DT)
                if target:
                    observed_resources.add(target)
                    d = np.linalg.norm(a.pos - target.pos)
                    if d < 1.0 and target.active:
                        gain = 1.0 * target.coherence
                        a.energy += gain
                        a.generation_energy += gain
                        target.active = False

            # Resource updates
            active_res_count = 0
            for r in resources:
                if not r.active:
                    continue
                is_seen = r in observed_resources
                r.update(DT, is_seen)
                if r.active:
                    active_res_count += 1

            if active_res_count < 15:
                resources.append(Resource())

        # Generation stats
        alive_agents = [a for a in agents if a.energy > 0]
        total_gen = sum(a.generation_energy for a in agents)
        total_drain = sum(a.drain_energy for a in agents)
        profit_ratio = total_gen / (total_drain + 1e-6)

        print(f"Gen {gen:3d}: Survivors={len(alive_agents)}/{POPULATION_SIZE} | Profit Ratio={profit_ratio:.3f}")

        if profit_ratio > best_profit_overall:
            best_profit_overall = profit_ratio
            best_gen_idx = gen

        history.append(
            {"gen": gen, "survivors": len(alive_agents), "profit_ratio": profit_ratio}
        )

        # Selection
        if len(alive_agents) == 0:
            # Soft restart: reseed from best fossils
            agents.sort(key=lambda x: x.generation_energy, reverse=True)
            print("  Extinction. Reseeding from best fossils.")
            alive_agents = agents[:5]

        all_agents_sorted = sorted(agents, key=lambda x: x.generation_energy, reverse=True)
        new_agents: list[Agent] = []

        # Elitism
        elite_count = int(POPULATION_SIZE * ELITISM)
        for i in range(elite_count):
            parent = all_agents_sorted[i]
            new_agents.append(Agent(parent.brain))

        # Mutation
        parents = all_agents_sorted[: int(POPULATION_SIZE / 2)]
        while len(new_agents) < POPULATION_SIZE:
            parent = np.random.choice(parents)
            child_brain = parent.brain.mutate()
            new_agents.append(Agent(child_brain))

        agents = new_agents

    final_ratio = history[-1]["profit_ratio"]
    print("\nEvolutionary Genesis v2 Summary:")
    print(f"Final Profit Ratio: {final_ratio:.3f}")
    if final_ratio > 1.13:
        print("CONCLUSION: SUCCESS. Information Profit Principle satisfied.")
    else:
        print("CONCLUSION: FAILED. Profit Ratio insufficient.")
    print(f"Best observed Profit Ratio over run: {best_profit_overall:.3f} at generation {best_gen_idx}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    artifact_path = os.path.join(
        results_dir, f"MFRR_Evolutionary_Genesis_v2_{timestamp}.json"
    )

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, indent=2)

    return {"artifact_path": artifact_path, "history": history}


if __name__ == "__main__":
    run_evolutionary_genesis_v2()


