#!/usr/bin/env python3
"""
Generate figure assets for *The Dynamics and Universality of the UGP* (PRE paper).

Reads a completed `rg_sweep` `experiment_results.json` and writes:
  - `rg_convergence_plot.png` — α vs RG iteration for a stratified subset of tasks.

Usage (from the ugp_discovery_lab root inside ugp-physics):
  python scripts/export_pre_dynamics_paper_figures.py \\
    --rg-json UGP_discovery_lab_runs/<run>/results/reports/experiment_results.json \\
    --output-dir ../../papers/04_dynamics/figures

Requires: matplotlib (install with `pip install -e ".[plots]"`).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _iter_alpha_series(result: dict) -> list[float] | None:
    traj = result.get("trajectory") or []
    if not traj:
        return None
    return [float(p["alpha"]) for p in traj if "alpha" in p]


def _label_attractor(alpha: float) -> str:
    if -0.09 <= alpha <= -0.08:
        return "A"
    if 0.07 <= alpha <= 0.08:
        return "B"
    if 0.26 <= alpha <= 0.27:
        return "C"
    return "UNK"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--rg-json",
        type=Path,
        required=True,
        help="Path to rg_sweep experiment_results.json",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for PNG outputs (e.g. paper figures/)",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-curves", type=int, default=24)
    args = ap.parse_args()

    data = json.loads(args.rg_json.read_text(encoding="utf-8"))
    block = data.get("data", data)
    results = block.get("results", [])

    series_list: list[tuple[str, list[float]]] = []
    for r in results:
        if not r.get("success"):
            continue
        tid = r.get("task_id", "?")
        ys = _iter_alpha_series(r)
        if ys and len(ys) > 1:
            series_list.append((tid, ys))

    rng = random.Random(args.seed)
    if len(series_list) > args.max_curves:
        series_list = rng.sample(series_list, args.max_curves)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # --- RG convergence multi-curve ---
    plt.figure(figsize=(8, 5))
    ref_lines = (-0.0850346853, 0.0754130404, 0.2644176696)
    for y in ref_lines:
        plt.axhline(y, color="0.75", linewidth=0.8, linestyle="--", zorder=0)
    for tid, ys in series_list:
        xs = list(range(len(ys)))
        plt.plot(xs, ys, linewidth=1.0, alpha=0.65)
    plt.xlabel("RG iteration")
    plt.ylabel(r"$\alpha$ (kernel-plane fit)")
    plt.title("RG trajectories (subset of rg_sweep tasks)")
    plt.tight_layout()
    out_rg = args.output_dir / "rg_convergence_plot.png"
    plt.savefig(out_rg, dpi=200)
    plt.close()
    print(f"Wrote {out_rg}")

    # --- Modal attractor label heatmap: window × law policy string ---
    grid: dict[tuple[int, str], list[str]] = {}
    for r in results:
        if not r.get("success"):
            continue
        w = int(r.get("window", -1))
        law = r.get("law") or {}
        pol = f"{law.get('c_policy')}_{law.get('b_policy')}"
        fa = r.get("analysis", {}).get("final_alpha")
        if fa is None:
            continue
        lab = _label_attractor(float(fa))
        key = (w, pol)
        grid.setdefault(key, []).append(lab)

    if grid:
        windows = sorted({k[0] for k in grid})
        policies = sorted({k[1] for k in grid})
        mat = np.zeros((len(windows), len(policies)))
        for i, win in enumerate(windows):
            for j, pol in enumerate(policies):
                labs = grid.get((win, pol), [])
                if not labs:
                    mat[i, j] = np.nan
                    continue
                mode = max(set(labs), key=labs.count)
                mat[i, j] = {"A": 0.0, "B": 1.0, "C": 2.0, "UNK": 3.0}.get(mode, 3.0)

        plt.figure(figsize=(10, 6))
        im = plt.imshow(mat, cmap="RdYlBu_r", aspect="auto", vmin=0, vmax=3)
        plt.colorbar(im, label="A=0, B=1, C=2, UNK=3")
        plt.xticks(range(len(policies)), policies, rotation=45, ha="right")
        plt.yticks(range(len(windows)), [str(w) for w in windows])
        plt.xlabel("Law policy (c_b)")
        plt.ylabel("Window")
        plt.title("Modal RG basin label vs window × policy (rg_sweep)")
        plt.tight_layout()
        out_hm = args.output_dir / "seed_partition_heatmap.png"
        plt.savefig(out_hm, dpi=175)
        plt.close()
        print(f"Wrote {out_hm}")


if __name__ == "__main__":
    main()
