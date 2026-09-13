#!/usr/bin/env python3
"""Utilities for assembling RIET perturbation datasets.

This module ingests precomputed outputs from TE1.C, TE1.R, TE1.E, and TE1.O
runs and prepares batched perturbation configurations for downstream
variational checks. It does **not** execute simulations; consumers should call
`prepare_batches` and iterate as needed.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
TE1C_RESULTS = BASE_DIR / ".." / "TE_1.C_RQG" / "results"
TE1R_RESULTS = BASE_DIR / ".." / "TE_1.R_CONTINOUS_MODEL" / "results"
TE1E_RESULTS = BASE_DIR / ".." / "TE_1.E_Lambda" / "results"
TE1O_FASTWIN = BASE_DIR / ".." / "TE_1.O_ABSOLUTE_GAUGE" / "results" / "fast_win_summary.json"


@dataclass
class PerturbationConfig:
    """Container for perturbation magnitudes."""

    delta_g: float
    delta_I: float
    delta_psi: float
    label: str


def _load_json(path: pathlib.Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_slow_roll_summary() -> Dict:
    """Load TE1.C slow-roll residuals."""

    summary_path = TE1C_RESULTS / "phase1_summary.json"
    return _load_json(summary_path)


def load_pt_selector_summary() -> Dict:
    """Load TE1.R PT selector and fluctuation statistics."""

    pt_dir = TE1R_RESULTS / "pt_selector"
    summaries = {}
    for path in pt_dir.glob("*_summary.json"):
        summaries[path.stem] = _load_json(path)
    fluct_summary = _load_json(TE1R_RESULTS / "fluctuation" / "summary.json")
    return {"pt": summaries, "fluctuation": fluct_summary}


def load_lambda_summary() -> Dict:
    """Load TE1.E Lambda regression baseline."""

    baseline_dir = TE1E_RESULTS / "run_20251110_230054"
    return _load_json(baseline_dir / "results" / "summary.json")


def load_fast_win_summary() -> Dict:
    """Load TE1.O fast win metrics (Lambda-Omega)."""

    return _load_json(TE1O_FASTWIN)


def prepare_batches(
    configs: Iterable[PerturbationConfig],
    batch_size: int = 8,
    seed: int | None = None,
) -> List[Dict[str, np.ndarray]]:
    """Prepare perturbation batches for downstream variational checks.

    Parameters
    ----------
    configs:
        Iterable of perturbation magnitudes to apply.
    batch_size:
        Number of random samples per batch (default 8).
    seed:
        Optional RNG seed for reproducibility.
    """

    rng = np.random.default_rng(seed)
    batches: List[Dict[str, np.ndarray]] = []
    for cfg in configs:
        perturbations = {
            "delta_g": rng.normal(loc=0.0, scale=cfg.delta_g, size=(batch_size, 4, 4)),
            "delta_I": rng.normal(loc=0.0, scale=cfg.delta_I, size=(batch_size, 3, 3)),
            "delta_psi": rng.normal(loc=0.0, scale=cfg.delta_psi, size=(batch_size,)),
            "label": np.array([cfg.label] * batch_size, dtype=object),
        }
        batches.append(perturbations)
    return batches


def default_configs() -> List[PerturbationConfig]:
    """Return default perturbation scales derived from TE1 datasets."""

    slow_roll = load_slow_roll_summary()
    pt_selector = load_pt_selector_summary()["pt"]
    lambda_summary = load_lambda_summary()
    fast_win = load_fast_win_summary()

    epsilon_scale = float(slow_roll["slow_roll"]["epsilon_mean"]) if "slow_roll" in slow_roll else 1e-5
    if pt_selector:
        first_run = next(iter(pt_selector.values()))
        pt_scale = float(first_run.get("max_normal_step", 1e-3))
    else:
        pt_scale = 1e-3
    lambda_scale = float(lambda_summary.get("lambda_phys_mean", 1e-52))
    fastwin_scale = float(fast_win.get("two_pi_lambda", 1.0))

    return [
        PerturbationConfig(delta_g=epsilon_scale, delta_I=pt_scale, delta_psi=1e-3, label="baseline"),
        PerturbationConfig(delta_g=epsilon_scale * 5, delta_I=pt_scale * 2, delta_psi=5e-3, label="stress"),
        PerturbationConfig(delta_g=lambda_scale, delta_I=fastwin_scale * 1e-2, delta_psi=1e-4, label="lambda-omega"),
    ]


if __name__ == "__main__":  # pragma: no cover - convenience only
    configs = default_configs()
    print("Prepared", len(configs), "perturbation configurations (no runs performed).")
    batches = prepare_batches(configs, batch_size=4, seed=42)
    print("Example batch shapes:", {k: v.shape for k, v in batches[0].items() if k != "label"})
    print("Labels:", batches[0]["label"])
