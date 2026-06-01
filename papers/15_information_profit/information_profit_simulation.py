"""
Information Profit Principle simulation against Levin-style randomness.

Reference session log:
`TE_1_VALIDATION_PROGRAM/SESSIONS/1_6_TE_1H_LEVIN_INFORMATION_PROFIT_STUDY.md`
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import zlib


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration for a single simulation scenario."""

    label: str
    generation_amplitude: float
    drain_rate: float
    noise_amplitude: float
    steps: int = 300
    seed: int = 42


@dataclass
class ExperimentResult:
    """Container for experiment outputs."""

    config: ExperimentConfig
    coherence_history: List[float]


class InformationProfitSystem:
    """
    Simulates the MFRR Information Profit dynamics on a 2D scalar field.

    The field evolves through:
    - generation: addition of coherent, low-complexity patterns
    - drain: exponential decay of existing structure
    - stochastic noise: injection of high Kolmogorov complexity perturbations
    """

    def __init__(self, size: tuple[int, int] = (128, 128), seed: int = 42) -> None:
        self.size = size
        self.rng = np.random.default_rng(seed)
        self.grid = self.rng.random(self.size, dtype=np.float32) * 0.1
        x = np.linspace(0, 2 * np.pi, self.size[1], dtype=np.float32)
        y = np.linspace(0, 2 * np.pi, self.size[0], dtype=np.float32)
        self.xx, self.yy = np.meshgrid(x, y)
        self.time_step = 0

    def measure_coherence(self) -> float:
        """Approximate coherence as inverse compression ratio (proxy for low Kolmogorov complexity)."""
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

    def step(self, generation_amp: float, drain_rate: float, noise_amp: float) -> None:
        """Advance the simulation by one step."""
        freq_x = 2.0 + np.sin(self.time_step / 50.0)
        freq_y = 2.0 + np.cos(self.time_step / 50.0)
        pattern = np.sin(self.xx * freq_x) * np.cos(self.yy * freq_y)

        self.grid += generation_amp * pattern
        self.grid *= 1.0 - drain_rate

        noise = self.rng.random(self.size, dtype=np.float32) - 0.5
        self.grid += noise_amp * noise
        self.time_step += 1


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    """Execute a simulation for the supplied configuration."""
    system = InformationProfitSystem(seed=config.seed)
    coherence_history: List[float] = []
    for _ in range(config.steps):
        system.step(
            generation_amp=config.generation_amplitude,
            drain_rate=config.drain_rate,
            noise_amp=config.noise_amplitude,
        )
        coherence_history.append(system.measure_coherence())
    return ExperimentResult(config=config, coherence_history=coherence_history)


def plot_results(results: Sequence[ExperimentResult], output_path: Path) -> None:
    """Create a plot showing coherence trajectories for each experiment."""
    plt.figure(figsize=(14, 8))
    for result in results:
        plt.plot(result.coherence_history, label=result.config.label, linewidth=2.4)

    plt.title("Information Profit Principle vs Levin Randomness")
    plt.xlabel("Time Steps")
    plt.ylabel("Coherence (1 - Compression Ratio)")
    plt.ylim(0.0, 1.0)
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.6, alpha=0.7)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def write_csv(result: ExperimentResult, output_dir: Path) -> Path:
    """Persist coherence history to CSV; return file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sanitized_label = result.config.label.lower().replace(" ", "_").replace("/", "_")
    file_path = output_dir / f"{sanitized_label}_coherence_history.csv"
    with file_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "step",
                "coherence",
                "generation_amplitude",
                "drain_rate",
                "noise_amplitude",
                "seed",
            ]
        )
        for idx, coherence in enumerate(result.coherence_history):
            writer.writerow(
                [
                    idx,
                    f"{coherence:.12f}",
                    result.config.generation_amplitude,
                    result.config.drain_rate,
                    result.config.noise_amplitude,
                    result.config.seed,
                ]
            )
    return file_path


def save_results(results: Sequence[ExperimentResult], base_dir: Path) -> list[Path]:
    """Save all CSV outputs and return paths."""
    csv_paths = []
    data_dir = base_dir / "csv"
    for result in results:
        csv_paths.append(write_csv(result, data_dir))
    return csv_paths


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    results_dir = base_dir / "results"

    experiments: Iterable[ExperimentConfig] = [
        ExperimentConfig(
            label="Unprofitable: Gen/Drain ≈ 0.8 (< 1.13)",
            generation_amplitude=0.07,
            drain_rate=0.08,
            noise_amplitude=0.03,
            steps=400,
        ),
        ExperimentConfig(
            label="Profitable: Gen/Drain ≈ 1.4 (> 1.13)",
            generation_amplitude=0.14,
            drain_rate=0.08,
            noise_amplitude=0.02,
            steps=400,
        ),
        ExperimentConfig(
            label="Profitable Gen + High Noise: Gen/Drain < 1.0",
            generation_amplitude=0.14,
            drain_rate=0.08,
            noise_amplitude=0.12,
            steps=400,
        ),
    ]

    results: List[ExperimentResult] = [run_experiment(config) for config in experiments]
    save_results(results, results_dir)
    plot_results(results, results_dir / "mfrr_information_profit_vs_levin_noise.png")


if __name__ == "__main__":
    main()

