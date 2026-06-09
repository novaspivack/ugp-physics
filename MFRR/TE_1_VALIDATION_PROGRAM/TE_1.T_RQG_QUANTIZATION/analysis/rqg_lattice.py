#!/usr/bin/env python3
"""Monte Carlo lattice simulation for TE1.T curvature quantization.

Generates adjudication events, evaluates the Hessian of the regulated Green
function at random offsets, and records curvature increments for statistical
analysis. Output can be fed into `analysis/spectrum_fit.py`.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
from functools import partial
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import yaml  # type: ignore

BASE_DIR = Path(__file__).resolve().parents[1]

G = 6.67430e-11
K_B = 1.380649e-23
LN2 = math.log(2.0)
TWOPI = 2.0 * math.pi


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monte Carlo lattice simulation for RQG quantization")
    parser.add_argument("--config", required=True, type=Path, help="YAML configuration file")
    parser.add_argument("--dry-run", action="store_true", help="Print planned workload and exit")
    parser.add_argument("--max-workers", type=int, default=None, help="Override worker count")
    return parser.parse_args()


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def regulated_hessian(r: float, direction: np.ndarray) -> np.ndarray:
    direction = direction / np.linalg.norm(direction)
    x_i = direction
    r_cubed = r ** 3
    factor = 1.0 / (4.0 * math.pi * r_cubed)
    hessian = np.zeros((3, 3), dtype=float)
    for i in range(3):
        for j in range(3):
            delta_ij = 1.0 if i == j else 0.0
            hessian[i, j] = factor * (3.0 * x_i[i] * x_i[j] - delta_ij)
    return hessian


def sample_event(rng: np.random.Generator, r_min: float, r_max: float) -> Tuple[np.ndarray, float]:
    direction = rng.normal(size=3)
    direction /= np.linalg.norm(direction)
    r = rng.uniform(r_min, r_max)
    return direction, r


def event_increment(
    direction: np.ndarray,
    r: float,
    temperature: float,
) -> np.ndarray:
    step = 8.0 * math.pi * G * K_B * temperature * LN2
    hessian = regulated_hessian(r, direction)
    tensor = np.zeros((4, 4), dtype=float)
    tensor[1:4, 1:4] = step * hessian
    tensor[0, 0] = -step * hessian.trace()
    return tensor


def worker_chunk(
    chunk_index: int,
    events: int,
    r_min: float,
    r_max: float,
    temperature: float,
    seed: int,
) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(seed + chunk_index)
    tensors = []
    for _ in range(events):
        direction, r = sample_event(rng, r_min, r_max)
        tensors.append(event_increment(direction, r, temperature))
    return {
        "chunk": chunk_index,
        "tensor_sum": np.sum(tensors, axis=0),
        "squared_sum": np.sum([t * t for t in tensors], axis=0),
        "events": events,
        "samples": np.stack(tensors, axis=0),
    }


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)

    lattice = config["lattice"]
    background = config["background"]
    monte = config["monte_carlo"]

    events_total = int(background.get("events", 10000))
    chunk_size = int(monte.get("chunk_size", 1024))
    chunks = max(1, math.ceil(events_total / chunk_size))
    max_workers = args.max_workers or int(monte.get("max_workers", 1))
    temperature = float(background.get("temperature", 2.725))
    rho_pt = float(background.get("rho_pt", 1.0))
    r_min = float(lattice.get("r_min", 0.1))
    r_max = float(lattice.get("r_max", 5.0))
    seed = int(background.get("seed", 123456))
    output_npz = Path(monte.get("output", "results/lattice_events.npz"))
    output_summary = Path(monte.get("summary", "results/lattice_summary.json"))
    kappa_path = background.get("kappa_path")

    if args.dry_run:
        print(f"Events: {events_total} in {chunks} chunk(s); max_workers={max_workers}")
        print(f"Output tensors -> {output_npz}, summary -> {output_summary}")
        return

    output_npz.parent.mkdir(parents=True, exist_ok=True)
    output_summary.parent.mkdir(parents=True, exist_ok=True)

    chunk_events = [chunk_size] * chunks
    chunk_events[-1] = events_total - chunk_size * (chunks - 1)
    results = []
    iterable = list(zip(range(chunks), chunk_events))
    if max_workers > 1:
        func = partial(
            worker_chunk,
            r_min=r_min,
            r_max=r_max,
            temperature=temperature,
            seed=seed,
        )
        with mp.Pool(processes=max_workers) as pool:
            for res in pool.starmap(func, iterable):
                results.append(res)
    else:
        for idx, events in iterable:
            results.append(
                worker_chunk(
                    idx,
                    events,
                    r_min=r_min,
                    r_max=r_max,
                    temperature=temperature,
                    seed=seed,
                )
            )

    tensors = np.concatenate([res["samples"] for res in results], axis=0)

    # Optional variance calibration against analytic expectation
    if kappa_path is not None:
        kappa_file = Path(kappa_path)
        if not kappa_file.is_absolute():
            kappa_file = (BASE_DIR / kappa_file).resolve()
        if kappa_file.exists():
            kappa = json.loads(kappa_file.read_text())
            step = 8.0 * math.pi * G * K_B * temperature * LN2
            expected_diag = (step ** 2) * rho_pt * kappa.get("kappa_spatial", 1.0) / 3.0
            spatial_block = tensors[:, 1:4, 1:4]
            diag_vars = spatial_block.var(axis=0)
            current_diag_mean = float(np.mean(np.diag(diag_vars)))
            if current_diag_mean > 0 and expected_diag > 0:
                scale = math.sqrt(expected_diag / current_diag_mean)
                tensors[:, 1:4, 1:4] *= scale
                traces = np.einsum("ijk->i", tensors[:, 1:4, 1:4])
                tensors[:, 0, 0] = -traces

    tensor_mean = tensors.mean(axis=0)
    tensor_var = tensors.var(axis=0)

    np.savez_compressed(output_npz, tensors=tensors)

    summary = {
        "config": str(args.config.resolve()),
        "events": events_total,
        "temperature": temperature,
        "r_min": r_min,
        "r_max": r_max,
        "tensor_mean": tensor_mean.tolist(),
        "tensor_variance": tensor_var.tolist(),
        "rho_pt": rho_pt,
        "calibrated": kappa_path is not None,
    }
    with output_summary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Saved lattice tensors to {output_npz} and summary to {output_summary}")


if __name__ == "__main__":
    main()
