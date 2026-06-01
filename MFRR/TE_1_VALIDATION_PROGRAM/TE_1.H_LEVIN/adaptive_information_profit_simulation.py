"""
Adaptive Information Profit simulation with homeostatic feedback.

Reference session log:
`TE_1_VALIDATION_PROGRAM/SESSIONS/1_6_TE_1H_LEVIN_INFORMATION_PROFIT_STUDY.md`
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import zlib

style.use("seaborn-v0_8-darkgrid")


@dataclass
class AdaptiveSystemConfig:
    """Configuration parameters for adaptive experiment."""

    size: Tuple[int, int] = (128, 128)
    seed: int = 101
    drain_rate: float = 0.08
    low_noise: float = 0.02
    high_noise: float = 0.15
    initial_generation_amp: float = 0.1
    target_coherence: float = 0.8
    adaptation_rate: float = 0.05
    max_generation_amp: float = 0.5
    control_generation_amp: float = 0.12
    steps: int = 600
    shock_step: int = 300


class InformationProfitSystem:
    """
    Simulates Information Profit dynamics with optional adaptive feedback.
    """

    def __init__(
        self,
        size: Tuple[int, int] = (128, 128),
        seed: int = 42,
        initial_generation_amp: float = 0.1,
        target_coherence: float = 0.8,
        adaptation_rate: float = 0.05,
        max_generation_amp: float = 0.5,
    ) -> None:
        self.size = size
        self.rng = np.random.default_rng(seed)
        self.grid = self.rng.random(self.size, dtype=np.float32) * 0.1

        x = np.linspace(0, 2 * np.pi, self.size[1], dtype=np.float32)
        y = np.linspace(0, 2 * np.pi, self.size[0], dtype=np.float32)
        self.xx, self.yy = np.meshgrid(x, y)

        self.generation_amp = initial_generation_amp
        self.target_coherence = target_coherence
        self.adaptation_rate = adaptation_rate
        self.max_generation_amp = max_generation_amp
        self.time_step = 0

    def measure_coherence(self) -> float:
        """Proxy for inverse Kolmogorov complexity via compression ratio."""
        grid_max = float(self.grid.max())
        grid_min = float(self.grid.min())
        if grid_max == grid_min:
            return 1.0

        normalized = (255 * (self.grid - grid_min) / (grid_max - grid_min)).astype(np.uint8)
        original_size = normalized.nbytes
        compressed = zlib.compress(normalized.tobytes(), level=9)
        compression_ratio = len(compressed) / original_size
        coherence = 1.0 - compression_ratio
        return float(np.clip(coherence, 0.0, 1.0))

    def step(self, drain_rate: float, noise_amp: float, is_adaptive: bool) -> Tuple[float, float]:
        """Advance one timestep with optional adaptation."""
        self.time_step += 1

        freq_x = 2.0 + np.sin(self.time_step / 50.0)
        freq_y = 2.0 + np.cos(self.time_step / 50.0)
        pattern = np.sin(self.xx * freq_x) * np.cos(self.yy * freq_y)
        self.grid += self.generation_amp * pattern

        self.grid *= 1.0 - drain_rate

        noise = self.rng.random(self.size, dtype=np.float32) - 0.5
        self.grid += noise_amp * noise

        coherence = self.measure_coherence()
        if is_adaptive:
            error = self.target_coherence - coherence
            self.generation_amp += self.adaptation_rate * error
            self.generation_amp = float(np.clip(self.generation_amp, 0.0, self.max_generation_amp))

        return coherence, self.generation_amp


def run_adaptive_experiment(config: AdaptiveSystemConfig) -> Tuple[List[float], List[float], List[float]]:
    """Run adaptive vs control comparison with noise shock."""
    control_system = InformationProfitSystem(
        size=config.size,
        seed=config.seed,
        initial_generation_amp=config.control_generation_amp,
        target_coherence=config.target_coherence,
        adaptation_rate=0.0,
        max_generation_amp=config.max_generation_amp,
    )
    adaptive_system = InformationProfitSystem(
        size=config.size,
        seed=config.seed,
        initial_generation_amp=config.initial_generation_amp,
        target_coherence=config.target_coherence,
        adaptation_rate=config.adaptation_rate,
        max_generation_amp=config.max_generation_amp,
    )

    control_coherence: List[float] = []
    adaptive_coherence: List[float] = []
    adaptive_generation: List[float] = []

    for step in range(config.steps):
        current_noise = config.low_noise if step < config.shock_step else config.high_noise

        control_system.generation_amp = config.control_generation_amp
        coherence_control, _ = control_system.step(
            drain_rate=config.drain_rate, noise_amp=current_noise, is_adaptive=False
        )
        coherence_adaptive, gen_amp = adaptive_system.step(
            drain_rate=config.drain_rate, noise_amp=current_noise, is_adaptive=True
        )

        control_coherence.append(coherence_control)
        adaptive_coherence.append(coherence_adaptive)
        adaptive_generation.append(gen_amp)

    return control_coherence, adaptive_coherence, adaptive_generation


def save_histories(
    control_coh: List[float],
    adaptive_coh: List[float],
    adaptive_generation: List[float],
    output_dir: Path,
) -> None:
    """Persist time-series data to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    steps = range(len(control_coh))

    with (output_dir / "control_coherence.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "coherence"])
        writer.writerows(zip(steps, (f"{c:.12f}" for c in control_coh)))

    with (output_dir / "adaptive_coherence.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "coherence"])
        writer.writerows(zip(steps, (f"{c:.12f}" for c in adaptive_coh)))

    with (output_dir / "adaptive_generation.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "generation_amp"])
        writer.writerows(zip(steps, (f"{g:.12f}" for g in adaptive_generation)))


def plot_results(
    control_coh: List[float],
    adaptive_coh: List[float],
    adaptive_generation: List[float],
    config: AdaptiveSystemConfig,
    figure_path: Path,
) -> None:
    """Generate comparison figure with coherence and generative effort."""
    figure_path.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)

    ax1.plot(control_coh, label="Control System (Fixed Generation)", lw=2, color="crimson")
    ax1.plot(adaptive_coh, label="Adaptive System (Homeostatic)", lw=3, color="royalblue")
    ax1.axvline(x=config.shock_step, color="black", linestyle="--", lw=2, label="Noise Shock")
    ax1.axhline(y=config.target_coherence, color="royalblue", linestyle=":", alpha=0.7, label="Target Coherence")
    ax1.set_title("System Coherence: Adaptive vs. Control", fontsize=16)
    ax1.set_ylabel("Coherence (1 - Compression Ratio)", fontsize=12)
    ax1.set_ylim(0.0, 1.0)
    ax1.legend(fontsize=11)
    ax1.grid(True, which="both", linestyle="--", linewidth=0.5)

    ax1.text(config.shock_step - 10, 0.5, "Low Noise", ha="right", fontsize=12, color="gray")
    ax1.text(config.shock_step + 10, 0.5, "High Noise", ha="left", fontsize=12, color="gray")

    ax1.text(
        config.shock_step + 150,
        max(control_coh[-50:], default=0.0) - 0.1,
        "Coherence Collapse",
        ha="center",
        fontsize=12,
        color="crimson",
    )
    ax1.text(
        config.shock_step + 150,
        min(max(adaptive_coh[-50:], default=0.0) + 0.05, 0.95),
        "Adaptation & Recovery",
        ha="center",
        fontsize=12,
        color="royalblue",
    )

    ax2.plot(adaptive_generation, label="Adaptive Generation Amplitude", lw=2, color="green")
    ax2.axvline(x=config.shock_step, color="black", linestyle="--", lw=2)
    ax2.set_title("Adaptive System Generative Effort", fontsize=16)
    ax2.set_xlabel("Time Steps", fontsize=12)
    ax2.set_ylabel("Generation Amplitude", fontsize=12)
    ax2.set_ylim(bottom=0.0)
    ax2.legend(fontsize=11)
    ax2.grid(True, which="both", linestyle="--", linewidth=0.5)

    ax2.text(
        config.shock_step + 150,
        max(adaptive_generation[-50:], default=0.0) + 0.02,
        "Increased effort to combat noise",
        ha="center",
        fontsize=12,
        color="green",
    )

    plt.suptitle("Adaptive Homeostasis vs. Environmental Shock", fontsize=20, y=0.95)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(figure_path, dpi=300)
    plt.close(fig)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    figs_dir = base_dir / "figs"
    results_dir = base_dir / "results" / "adaptive"

    config = AdaptiveSystemConfig()
    control_coh, adaptive_coh, adaptive_generation = run_adaptive_experiment(config)

    save_histories(
        control_coh=control_coh,
        adaptive_coh=adaptive_coh,
        adaptive_generation=adaptive_generation,
        output_dir=results_dir,
    )
    plot_results(
        control_coh=control_coh,
        adaptive_coh=adaptive_coh,
        adaptive_generation=adaptive_generation,
        config=config,
        figure_path=figs_dir / "adaptive_homeostasis_vs_shock.png",
    )


if __name__ == "__main__":
    main()

