#!/usr/bin/env python3
"""Compute kappa_{mu nu} constants for TE1.T lattice quantization.

The script reads lattice and PT source settings from a YAML config and
calculates the regulated Green-function gradient norms required for the
variance prediction. Heavy FFT computations are chunked and can be controlled
via the `--max-workers` flag. No runs are triggered automatically.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
from functools import partial
from pathlib import Path
from typing import Dict, Tuple

try:
    import yaml  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required for TE1.T analysis. Install with `pip install PyYAML`."
    ) from exc

import numpy as np

TWOPI = 2.0 * math.pi


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute kappa tensor for TE1.T lattice")
    parser.add_argument("--config", required=True, type=Path, help="YAML configuration file")
    parser.add_argument("--max-workers", type=int, default=1, help="Process pool size (default 1)")
    parser.add_argument("--chunk-size", type=int, default=None, help="Override chunk size from config")
    parser.add_argument("--dry-run", action="store_true", help="Print planned workload without executing")
    return parser.parse_args()


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def gaussian_regulated_green(k_squared: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-sigma * sigma * k_squared) / (-k_squared + 1e-15)


def gradient_squared_sum(
    dimensions: Tuple[int, int, int],
    spacing: float,
    sigma: float,
    chunk_index: int,
    chunk_size: int,
) -> Tuple[float, float]:
    nx, ny, nz = dimensions
    kx = np.fft.fftfreq(nx, d=spacing) * TWOPI
    ky = np.fft.fftfreq(ny, d=spacing) * TWOPI
    kz = np.fft.fftfreq(nz, d=spacing) * TWOPI

    start = chunk_index * chunk_size
    end = min(nx, start + chunk_size)
    kx_chunk = kx[start:end]

    kx_grid, ky_grid, kz_grid = np.meshgrid(kx_chunk, ky, kz, indexing="ij")
    k_sq = kx_grid ** 2 + ky_grid ** 2 + kz_grid ** 2

    green = gaussian_regulated_green(k_sq, sigma)
    grad_0_sq = (kx_grid ** 2) * (green ** 2)
    grad_spatial_sq = (ky_grid ** 2 + kz_grid ** 2) * (green ** 2)

    volume_element = spacing ** 3
    kappa_00 = float(np.sum(grad_0_sq) * volume_element)
    kappa_spatial = float(np.sum(grad_spatial_sq) * volume_element)
    return kappa_00, kappa_spatial


def worker_task(
    chunk_index: int,
    dims: Tuple[int, int, int],
    spacing: float,
    sigma: float,
    chunk_size: int,
) -> Dict[str, float]:
    kappa_00, kappa_spatial = gradient_squared_sum(dims, spacing, sigma, chunk_index, chunk_size)
    return {"chunk": chunk_index, "kappa_00": kappa_00, "kappa_spatial": kappa_spatial}


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    dims = tuple(int(x) for x in config["lattice"]["dimensions"])
    spacing = float(config["lattice"]["spacing"])
    sigma_cfg = config["lattice"].get("regulator_sigma", "auto")
    sigma = spacing / math.sqrt(8.0 * math.log(2.0)) if sigma_cfg == "auto" else float(sigma_cfg)

    chunk_size = args.chunk_size or int(config.get("execution", {}).get("chunk_size", 8))
    max_workers = args.max_workers or int(config.get("execution", {}).get("max_workers", 1))
    output_path = Path(config.get("execution", {}).get("output", "kappa_output.json")).resolve()

    total_chunks = max(1, math.ceil(dims[0] / chunk_size))

    if args.dry_run:
        print("Dry run: would compute kappa with", total_chunks, "chunk(s)")
        print("Dimensions:", dims, "spacing:", spacing, "sigma:", sigma)
        print("Output ->", output_path)
        return

    task = partial(worker_task, dims=dims, spacing=spacing, sigma=sigma, chunk_size=chunk_size)
    results = []
    if max_workers > 1:
        with mp.Pool(processes=max_workers) as pool:
            for res in pool.imap(task, range(total_chunks)):
                results.append(res)
    else:
        for idx in range(total_chunks):
            results.append(task(idx))

    kappa_00 = float(np.sum([res["kappa_00"] for res in results]))
    kappa_spatial = float(np.sum([res["kappa_spatial"] for res in results]))

    output = {
        "config": str(args.config.resolve()),
        "dimensions": dims,
        "spacing": spacing,
        "sigma": sigma,
        "chunks": total_chunks,
        "max_workers": max_workers,
        "kappa_00": kappa_00,
        "kappa_spatial": kappa_spatial,
        "notes": "Verify against lattice simulation before final use."
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)

    print(f"Saved kappa summary to {output_path}")


if __name__ == "__main__":
    main()
