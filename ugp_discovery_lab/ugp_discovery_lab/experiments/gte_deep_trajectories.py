"""
GTE Deep Trajectory Generator.

Generates long GTE (a,b,c) time series using the lawful_evolution engine,
across the four canonical seeds and multiple law variants. Results are stored
with full evolution_history and used by downstream experiments:
  - gte_rg_attractor_real  (Gap 1 / Gap 3)
  - gte_q4_basin_analysis  (Gap 2)
  - gte_entropy_attractor  (Gap 4)
  - gte_holographic_deep   (Gap 5)
  - gte_gsl_fit            (Gap 6)
"""

from __future__ import annotations
import json
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from .base import Experiment
from .lawful_evolution import LawfulEvolution
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report


CANONICAL_SEEDS = [
    [1, 73, 823],
    [1, 73, 2137],
    [2, 89, 1597],
    [3, 97, 2203],
]

# Surrogate basin labels (from rg_sweep deterministic routing)
SEED_BASIN = {
    (1, 73, 823): "A",
    (1, 73, 2137): "A",
    (2, 89, 1597): "C",
    (3, 97, 2203): "B",
}

LAW_VARIANTS = [
    {"c_policy": "mersenne", "b_policy": "fib",   "a_policy": "gte", "mirror": "d2"},
    {"c_policy": "mersenne", "b_policy": "lucas",  "a_policy": "gte", "mirror": "d2"},
    {"c_policy": "repunit",  "b_policy": "fib",   "a_policy": "gte", "mirror": "d2", "repunit_base": 3},
]


@register_experiment("gte_deep_trajectories")
class GTEDeepTrajectories(Experiment):
    """
    Generate long canonical GTE trajectories for all downstream strengthening experiments.
    Each task produces one (seed, law, window) combination.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        cfg = self.cfg
        steps = cfg.get("steps", 50000)
        windows = cfg.get("windows", [10])
        seeds = cfg.get("seeds", CANONICAL_SEEDS)
        laws = cfg.get("laws", LAW_VARIANTS)
        tasks = []
        for seed in seeds:
            for law in laws:
                for window in windows:
                    c = law["c_policy"]
                    b = law["b_policy"]
                    key = "_".join(map(str, seed))
                    tid = f"deep_{key}_{c}_{b}_w{window}"
                    tasks.append({
                        "task_id": tid,
                        "seed": seed,
                        "law": law,
                        "window": window,
                        "steps": steps,
                    })
        return tasks

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger(f"gte_deep:{task['task_id']}")
        seed = task["seed"]
        law = task["law"]
        window = task["window"]
        steps = task["steps"]

        # Build a minimal LawfulEvolution config and run it
        sub_cfg = {
            "name": "lawful_evolution",
            "le_config": {**law, "triggers": {"ridge": True, "mirror": True}},
            "run": {"windows": [window], "steps": steps, "seed": seed},
        }
        le = LawfulEvolution({"experiment": sub_cfg}, self.root)
        le_tasks = le.tasks()
        if not le_tasks:
            return {"task_id": task["task_id"], "success": False, "error": "no tasks"}
        result = le.run_task(le_tasks[0])
        evo = result.get("evolution_history", [])

        basin = SEED_BASIN.get(tuple(seed), "?")

        return {
            "task_id": task["task_id"],
            "success": bool(evo),
            "seed": seed,
            "law": law,
            "window": window,
            "steps_generated": len(evo),
            "basin": basin,
            "evolution_history": evo,
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        ok = [r for r in results if r.get("success")]
        total_steps = sum(r["steps_generated"] for r in ok)
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(ok),
            "total_gte_steps": total_steps,
            "task_ids": [r["task_id"] for r in ok],
        }
        write_json_report(self.root, "gte_deep_trajectories_summary", summary)
        lines = [
            "# GTE Deep Trajectories — Summary",
            f"- Tasks: {len(ok)}/{len(results)}",
            f"- Total GTE steps: {total_steps:,}",
        ]
        for r in ok:
            lines.append(f"  - {r['task_id']}: {r['steps_generated']:,} steps, basin={r['basin']}")
        write_md_report(self.root, "gte_deep_trajectories_summary", "\n".join(lines))
        return summary
