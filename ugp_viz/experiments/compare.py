"""
Cross-run comparison.

Compares one or more saved ExperimentResult JSON files on a chosen metric
and emits a comparison figure / summary table.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def compare_runs(
    run_paths: Iterable[str | Path],
    metric: str = "energy",
    output: str | Path | None = None,
) -> dict:
    """
    Compare runs on a given history metric (or scalar measurement).

    `metric` may be either a key in `history` (time series) or in
    `measurements` (scalar). Returns the summary dict and, if `output`
    is set, writes a PNG comparison figure.
    """
    paths = [Path(p) for p in run_paths]
    runs = [_load(p) for p in paths]
    summary: dict = {"metric": metric, "runs": []}

    is_history = all(metric in r.get("history", {}) for r in runs)
    is_scalar = all(metric in r.get("measurements", {}) for r in runs)

    if is_history:
        if output:
            fig, ax = plt.subplots(figsize=(12, 6))
            for path, run in zip(paths, runs):
                ts = run["history"].get("time", [])
                ys = run["history"].get(metric, [])
                ax.plot(ts, ys, label=Path(path).stem, linewidth=1.5)
            ax.set_xlabel("Time")
            ax.set_ylabel(metric)
            ax.set_title(f"Comparison: {metric}")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9)
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output, dpi=150, bbox_inches="tight")
            plt.close(fig)
            summary["figure"] = str(output)
        for path, run in zip(paths, runs):
            ys = np.array(run["history"].get(metric, []))
            summary["runs"].append({
                "name": Path(path).stem,
                "min": float(ys.min()) if ys.size else None,
                "max": float(ys.max()) if ys.size else None,
                "mean": float(ys.mean()) if ys.size else None,
                "final": float(ys[-1]) if ys.size else None,
            })
    elif is_scalar:
        if output:
            fig, ax = plt.subplots(figsize=(10, 5))
            names = [Path(p).stem for p in paths]
            vals = [r["measurements"][metric] for r in runs]
            ax.bar(names, vals, color="C0")
            ax.set_ylabel(metric)
            ax.set_title(f"Comparison: {metric}")
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output, dpi=150, bbox_inches="tight")
            plt.close(fig)
            summary["figure"] = str(output)
        for path, run in zip(paths, runs):
            summary["runs"].append({
                "name": Path(path).stem,
                "value": run["measurements"][metric],
            })
    else:
        raise KeyError(
            f"metric '{metric}' is not present as history or "
            f"measurement in all runs"
        )
    return summary
