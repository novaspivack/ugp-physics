#!/usr/bin/env python3
"""Parallel slow-roll search utility for TE_1.C (ref. TE_1.C_RQG docs)."""
from __future__ import annotations

import argparse
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

# Local imports (reachable when executed from project root)
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from config_loader import load_config  # type: ignore  # noqa: E402
from spectra_analytic import compute_slow_roll_spectra  # type: ignore  # noqa: E402
from tune_slow_roll import (  # type: ignore  # noqa: E402
    FRWInitialConditions,
    FRWModelConfig,
    evaluate_slow_roll,
    _estimate_ppsi0,
    integrate_background,
)

K_TARGETS = [2e-5, 8e-5, 3e-4, 1e-3, 5e-3, 2e-2, 8e-2, 2e-1, 5e-1]


def _parse_param(arg: str) -> Tuple[str, float, float]:
    """Parse "name=min:max" spec."""
    if "=" not in arg or ":" not in arg:
        raise ValueError(f"Invalid param specification '{arg}'. Expected name=min:max")
    name, span = arg.split("=", 1)
    lo, hi = span.split(":", 1)
    return name.strip(), float(lo), float(hi)


def _sample_parameters(
    base_cfg: Dict[str, float],
    sample_count: int,
    specs: List[Tuple[str, float, float]],
    seed: int,
) -> List[Dict[str, float]]:
    rng = np.random.default_rng(seed)
    dim = len(specs)
    samples = rng.random((sample_count, dim))
    points: List[Dict[str, float]] = []
    for row in samples:
        cfg = dict(base_cfg)
        for value, (name, lo, hi) in zip(row, specs):
            cfg[name] = lo + (hi - lo) * value
        points.append(cfg)
    return points


def _evaluate_point(args: Tuple[Dict[str, float], float, Dict[str, float]]) -> Dict[str, float]:
    cfg_kwargs, psi0, base_cfg = args
    cfg_dict = dict(base_cfg)
    cfg_dict.update(cfg_kwargs)
    cfg = FRWModelConfig(**cfg_dict)
    ppsi0 = _estimate_ppsi0(cfg, psi0)
    ic = FRWInitialConditions(psi0=psi0, ppsi0=ppsi0)
    run = integrate_background(cfg, ic, rtol=1e-7, atol=1e-9, min_ln_a=-6.0)
    metrics = evaluate_slow_roll(run)
    if not metrics:
        raise RuntimeError("No slow-roll plateau identified")
    points = compute_slow_roll_spectra(run, K_TARGETS)
    ns = np.array([p.n_s for p in points])
    rvals = np.array([p.r for p in points])
    eps_exit = np.array([p.epsilon_exit for p in points])
    eta_exit = np.array([p.eta_exit for p in points])
    summary = {
        "ns_mean": float(np.mean(ns)),
        "ns_min": float(np.min(ns)),
        "ns_max": float(np.max(ns)),
        "r_mean": float(np.mean(rvals)),
        "r_min": float(np.min(rvals)),
        "r_max": float(np.max(rvals)),
        "epsilon_exit_mean": float(np.mean(eps_exit)),
        "epsilon_exit_max": float(np.max(eps_exit)),
        "eta_exit_mean": float(np.mean(eta_exit)),
        "epsilon_mean": float(metrics.get("epsilon_mean", math.nan)),
        "epsilon_max": float(metrics.get("epsilon_max", math.nan)),
        "efolds": float(metrics.get("efolds", math.nan)),
        "psi0": psi0,
    }
    summary.update(cfg_kwargs)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Parallel slow-roll parameter search")
    parser.add_argument(
        "--base-config",
        default="configs/spectra_slow_roll.yaml",
        help="YAML config providing baseline parameters",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=256,
        help="Number of random samples to evaluate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20251113,
        help="Random seed for sampling",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=9,
        help="Maximum parallel worker processes (respect core limits)",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Parameter range specification name=min:max (can repeat)",
    )
    parser.add_argument(
        "--psi0-range",
        default="4.0:4.0",
        help="Range for psi0 initial value (min:max)",
    )
    parser.add_argument(
        "--output",
        default="results/slow_roll_search_results.json",
        help="Output JSON path for aggregated results",
    )
    args = parser.parse_args()

    base_cfg = load_config(Path(args.base_config))["background"]
    psi0_lo, psi0_hi = (float(x) for x in args.psi0_range.split(":"))

    if not args.param:
        parser.error("Provide at least one --param specification")

    specs = [_parse_param(p) for p in args.param]
    samples = _sample_parameters(base_cfg, args.samples, specs, args.seed)

    rng = np.random.default_rng(args.seed + 101)
    psi0_samples = psi0_lo + (psi0_hi - psi0_lo) * rng.random(len(samples))

    payloads = []
    for cfg_kwargs, psi0 in zip(samples, psi0_samples):
        payloads.append((cfg_kwargs, psi0, base_cfg))

    results: List[Dict[str, float]] = []
    failures = 0
    max_workers = max(1, min(args.workers, len(payloads)))
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        future_map = {pool.submit(_evaluate_point, payload): payload for payload in payloads}
        total = len(future_map)
        completed = 0
        for future in as_completed(future_map):
            completed += 1
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"[error] {exc}", flush=True)
            else:
                results.append(result)
            if completed % max(1, total // 20) == 0 or completed == total:
                print(f"[progress] {completed}/{total} evaluations", flush=True)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({
        "meta": {
            "samples": args.samples,
            "seed": args.seed,
            "workers": max_workers,
            "failures": failures,
        },
        "specs": [{"name": name, "min": lo, "max": hi} for name, lo, hi in specs],
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"[done] stored {len(results)} results (failures={failures}) in {output_path}")

    if results:
        results.sort(key=lambda r: (abs(r["ns_mean"] - 0.965), r["r_mean"]))
        best = results[0]
        print("[best] ns_mean={:.4f} r_mean={:.4f} eps_mean={:.5f}".format(
            best["ns_mean"], best["r_mean"], best["epsilon_mean"]
        ))
        print("        psi0={:.4f}".format(best["psi0"]))
        for name, _, _ in specs:
            print(f"        {name}={best[name]:.6f}")


if __name__ == "__main__":
    main()
