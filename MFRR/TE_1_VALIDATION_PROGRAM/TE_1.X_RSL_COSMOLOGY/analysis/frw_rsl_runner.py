#!/usr/bin/env python3
"""Run FRW+Psi sweeps for TE1.X Reflexive Second Law analysis.

Example:
    python frw_rsl_runner.py --config configs/frw_rsl_baseline.yaml \
        --entropy ../../TE_1.R_CONTINOUS_MODEL/results/fluctuation/summary.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Tuple
import multiprocessing as mp

try:
    import yaml  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required for TE1.X runner. Install with `pip install PyYAML`."
    ) from exc

import numpy as np

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
FRW_ROOT = PROJECT_ROOT / "MFRR"
if str(FRW_ROOT) not in sys.path:
    sys.path.append(str(FRW_ROOT))

from frw_psi_scan import Params, integrate_background, fit_w0_wa, G, c as C_LIGHT  # type: ignore

TE1E_ROOT = PROJECT_ROOT / "MFRR" / "TE_1_VALIDATION_PROGRAM" / "TE_1.E_Lambda"
if str(TE1E_ROOT) not in sys.path:
    sys.path.append(str(TE1E_ROOT))

import te1e_pipeline  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TE1.X FRW runner")
    parser.add_argument("--config", required=True, type=Path, help="YAML config path")
    parser.add_argument(
        "--entropy",
        required=True,
        type=Path,
        help="TE1.R entropy summary JSON (absolute path preferred)",
    )
    parser.add_argument("--max-workers", type=int, default=1, help="Execution parallelism (default sequential)")
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_entropy(entropy_path: Path) -> Dict[str, float]:
    with entropy_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        "mean_delta_S": float(data.get("mean_delta_S", 0.0)),
        "variance_delta_S": float(data.get("variance_delta_S", 0.0)),
        "samples": int(data.get("samples", 0)),
    }


def parameter_grid(config: Dict[str, any]) -> Iterable[Tuple[float, float, float]]:
    sweeps = config.get("sweeps", [])
    if not sweeps:
        params = config["parameters"]
        yield (
            float(params["lambda_psi"][0]),
            float(params["alpha_1"][0]),
            float(params["alpha_2"][0]),
        )
        return
    for sweep in sweeps:
        for lpsi in sweep["lambda_psi"]:
            for a1 in sweep["alpha_1"]:
                for a2 in sweep["alpha_2"]:
                    yield (float(lpsi), float(a1), float(a2))


def map_to_params(config: Dict[str, any], combo: Tuple[float, float, float]) -> Params:
    lpsi, a1, a2 = combo
    lambda_cfg = te1e_pipeline.LambdaConfig(
        lambda_psi_values=(lpsi,),
        alpha1_values=(a1,),
        alpha2_values=(a2,),
        zmax=float(config["solver"]["zmax"]),
        nsteps=int(config["solver"]["nsteps"]),
        psi0=float(config["solver"]["psi0"]),
        psi_dot0=float(config["solver"]["psi_dot0"]),
        cpl_zmax_fit=1.5,
        target_lambda=1.1056e-52,
    )
    return te1e_pipeline._map_to_frw_params(lambda_cfg, lpsi, a1, a2)


def run_case(config: Dict[str, any], combo: Tuple[float, float, float]) -> Dict[str, any]:
    params = map_to_params(config, combo)
    sol = integrate_background(
        params,
        psi0=float(config["solver"]["psi0"]),
        ppsi0=float(config["solver"].get("psi_dot0", 0.0)),
    )

    psi = sol["psi"]
    ppsi = sol["ppsi"]
    rho_lambda_raw = float(combo[0] * combo[1] * np.mean(psi**2) + combo[2] * np.mean(ppsi**2))
    lambda_raw = float(8.0 * np.pi * G * rho_lambda_raw)
    rho_mass_phys = float(sol["rho_psi"][0])
    lambda_phys = float(8.0 * np.pi * G * rho_mass_phys / (C_LIGHT ** 2))

    w0, wa = fit_w0_wa(sol["z"], sol["w_psi"], zmax_fit=1.5)

    return {
        "lambda_psi": combo[0],
        "alpha_1": combo[1],
        "alpha_2": combo[2],
        "rho_lambda_raw": rho_lambda_raw,
        "lambda_raw": lambda_raw,
        "rho_mass_phys": rho_mass_phys,
        "lambda_phys": lambda_phys,
        "w0": float(w0),
        "wa": float(wa),
        "params": {
            "m": params.m,
            "beta": params.beta,
            "omega_bar": params.omega_bar,
            "Rf_bar": params.Rf_bar,
        },
    }


def process_combo(args_tuple):
    config, combo = args_tuple
    record = run_case(config, combo)
    record["combo"] = combo
    return record


def main() -> None:
    args = parse_args()
    config = load_yaml(args.config)
    entropy_stats = load_entropy(args.entropy)

    output_dir = ensure_dir(Path(config["outputs"]["directory"]).resolve())
    summary: Dict[str, any] = {
        "config": str(args.config.resolve()),
        "entropy_source": str(args.entropy.resolve()),
        "runs": [],
        "entropy": entropy_stats,
    }

    combos = list(parameter_grid(config))
    worker_count = max(1, args.max_workers)

    records = []
    if worker_count > 1 and len(combos) > 1:
        with mp.Pool(processes=worker_count) as pool:
            for record in pool.imap_unordered(process_combo, [(config, combo) for combo in combos]):
                records.append(record)
    else:
        for combo in combos:
            records.append(process_combo((config, combo)))

    for record in records:
        combo = record.pop("combo")
        summary["runs"].append(record)
        run_dir = ensure_dir(output_dir / f"lambda_{combo[0]:.3f}_a1_{combo[1]:.3f}_a2_{combo[2]:.3f}")
        with (run_dir / "summary.json").open("w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2)

    # Aggregate statistics
    summary["max_abs_wa"] = max(abs(run["wa"]) for run in summary["runs"])
    summary["mean_w0"] = float(np.mean([run["w0"] for run in summary["runs"]]))
    summary_path = output_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Saved sweep summary to {summary_path}")


if __name__ == "__main__":
    main()
