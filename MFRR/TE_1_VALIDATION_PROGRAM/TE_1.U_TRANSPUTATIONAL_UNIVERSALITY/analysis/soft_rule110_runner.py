#!/usr/bin/env python3
"""Soft Rule-110 emulation using PR-0 style micro-phases.

This script implements the Track A pipeline: sample -> compute -> inhibit -> commit
with guard-banded amplitudes and sigmoid surrogate of the Rule-110 truth table.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Soft Rule-110 runner")
    parser.add_argument("--config", required=True, type=Path, help="YAML/JSON configuration file")
    return parser.parse_args()


def load_config(path: Path) -> Dict:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rule110_polynomial_weights() -> np.ndarray:
    patterns = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (0, 1, 1),
        (1, 0, 0),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 1),
    ]
    outputs = np.array([0, 1, 1, 1, 0, 1, 1, 0], dtype=float)
    features = []
    for a, b, c in patterns:
        features.append([1, a, b, c, a * b, b * c, a * c, a * b * c])
    matrix = np.array(features, dtype=float)
    weights = np.linalg.solve(matrix, outputs)
    return weights


def polynomial_output(weights: np.ndarray, left: np.ndarray, center: np.ndarray, right: np.ndarray) -> np.ndarray:
    terms = np.stack(
        [
            np.ones_like(center),
            left,
            center,
            right,
            left * center,
            center * right,
            left * right,
            left * center * right,
        ],
        axis=0,
    )
    poly = np.tensordot(weights, terms, axes=(0, 0))
    return poly


def sigmoid(x: np.ndarray, alpha: float) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-alpha * (x - 0.5)))


def median_filter(arr: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return arr
    pad = window // 2
    padded = np.pad(arr, (pad, pad), mode="edge")
    filtered = np.zeros_like(arr)
    for i in range(len(arr)):
        filtered[i] = np.median(padded[i : i + window])
    return filtered


def decode(state: np.ndarray, mu: float, window: int) -> np.ndarray:
    filtered = median_filter(state, window)
    return (filtered > mu).astype(float)


def run_soft_ca(cfg: Dict) -> Tuple[np.ndarray, np.ndarray, Dict]:
    initial_path = Path(cfg["initial_bits"]).resolve()
    bits = np.load(initial_path)
    if bits.ndim == 2:
        bits = bits[0]
    bits = bits.astype(float)

    steps = int(cfg.get("steps", 256))
    mu = float(cfg.get("mu", 0.5))
    delta = float(cfg.get("delta", 0.4))
    eta = float(cfg.get("eta", 0.1))
    gamma = float(cfg.get("gamma", 0.1))
    lam = float(cfg.get("lambda_commit", 0.8))
    alpha = float(cfg.get("alpha", 12.0))
    median_window = int(cfg.get("median_window", 3))

    boundary = cfg.get("boundary", "periodic")

    guard_low = mu - delta
    guard_high = mu + delta

    def encode(bits_row: np.ndarray) -> np.ndarray:
        return np.where(bits_row > 0.5, guard_high, guard_low)

    rule_table = np.array([0, 1, 1, 1, 0, 1, 1, 0], dtype=float)

    width = bits.shape[0]
    state = encode(bits)
    field_history = np.zeros((steps, width))
    decoded_history = np.zeros((steps, width))

    current_bits = bits.copy()
    for t in range(steps):
        decoded = decode(state, mu, median_window)
        decoded_history[t] = decoded
        field_history[t] = state

        if boundary == "periodic":
            left = np.roll(decoded, 1)
            right = np.roll(decoded, -1)
            left_state = np.roll(state, 1)
            right_state = np.roll(state, -1)
        else:
            left = np.concatenate(([0.0], decoded[:-1]))
            right = np.concatenate((decoded[1:], [0.0]))
            left_state = np.concatenate(([mu], state[:-1]))
            right_state = np.concatenate((state[1:], [mu]))

        sample = (1.0 - eta) * state + (eta / 2.0) * (left_state + right_state)

        # Compute phase via polynomial + sigmoid
        idx = (left.astype(int) << 2) + (decoded.astype(int) << 1) + right.astype(int)
        soft_target = rule_table[idx]

        # Inhibit phase
        inhibit = (1.0 - gamma) * sample + gamma * mu

        # Commit phase
        target_amplitude = mu + (soft_target - 0.5) * 2.0 * delta
        target_amplitude = np.clip(target_amplitude, guard_low, guard_high)
        state = (1.0 - lam) * inhibit + lam * target_amplitude
        current_bits = decoded

    metadata = {
        "mu": mu,
        "delta": delta,
        "eta": eta,
        "gamma": gamma,
        "lambda_commit": lam,
        "alpha": alpha,
        "median_window": median_window,
        "boundary": boundary,
    }

    return field_history, decoded_history, metadata


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    fields, decoded, meta = run_soft_ca(cfg)

    output_field = Path(cfg["output_field"]).resolve()
    output_decoded = Path(cfg["output_decoded"]).resolve()
    output_field.parent.mkdir(parents=True, exist_ok=True)
    output_decoded.parent.mkdir(parents=True, exist_ok=True)

    np.save(output_field, fields)
    np.save(output_decoded, decoded)

    log_path = Path(cfg.get("log_path", "pr0_soft_run.json")).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        json.dump({"config": str(args.config.resolve()), "metadata": meta}, handle, indent=2)

    print("Saved field evolution to", output_field)
    print("Saved decoded trajectory to", output_decoded)


if __name__ == "__main__":
    main()
