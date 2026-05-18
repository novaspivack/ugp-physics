"""
Q4 Logarithmic Complexity Charge — Basin Analysis (Gap 2).

For each GTE trajectory, compute Q4 = log|a| + log|b| + log|c| at every step.
Then:
  1. Report mean ± std per basin
  2. One-way ANOVA to test statistical separability
  3. Mann-Whitney pairwise tests (A vs B, A vs C, B vs C)
  4. Verify that Q4 is "statistically conserved" within trajectories

Replaces the unsubstantiated Table 2 in the paper with real data.
"""

from __future__ import annotations
import json
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

try:
    from scipy import stats as _scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def _q4(a, b, c) -> float:
    try:
        return float(math.log(abs(int(a)) + 1) + math.log(abs(int(b)) + 1) + math.log(abs(int(c)) + 1))
    except Exception:
        return float("nan")


@register_experiment("gte_q4_basin_analysis")
class GTEQ4BasinAnalysis(Experiment):
    """
    Compute Q4 per basin from deep GTE trajectories and test statistical separability.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        inputs = self.cfg.get("inputs", {}).get("runs", [])
        tasks = []
        for pattern in inputs:
            for f in Path(".").glob(pattern):
                tasks.append({"task_id": f"q4_{f.parent.parent.parent.name}", "file": str(f)})
        return tasks

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger(f"q4:{task['task_id']}")
        try:
            d = json.loads(Path(task["file"]).read_text())
            block = d.get("data", d)
            results = block.get("results", [])
        except Exception as e:
            return {"task_id": task["task_id"], "success": False, "error": str(e)}

        basin_q4: Dict[str, List[float]] = defaultdict(list)
        per_traj_stats = []

        for r in results:
            if not r.get("success"):
                continue
            evo = r.get("evolution_history", [])
            basin = r.get("basin", "?")
            if not evo:
                continue

            q4s = [_q4(e["a"], e["b"], e["c"]) for e in evo]
            q4s = [v for v in q4s if not math.isnan(v)]
            if not q4s:
                continue

            basin_q4[basin].extend(q4s)
            mean_q4 = float(np.mean(q4s))
            std_q4 = float(np.std(q4s))
            cv = std_q4 / mean_q4 if mean_q4 > 0 else float("inf")
            per_traj_stats.append({
                "task_id": r["task_id"],
                "basin": basin,
                "n_steps": len(q4s),
                "mean_q4": mean_q4,
                "std_q4": std_q4,
                "cv": cv,
                "seed": r.get("seed"),
            })
            logger.info(f"basin={basin} seed={r.get('seed')} Q4={mean_q4:.3f}±{std_q4:.3f} CV={cv:.4f}")

        return {
            "task_id": task["task_id"],
            "success": True,
            "basin_q4": {k: v for k, v in basin_q4.items()},
            "per_traj_stats": per_traj_stats,
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Aggregate across all tasks
        basin_q4: Dict[str, List[float]] = defaultdict(list)
        all_per_traj = []
        for r in results:
            if not r.get("success"):
                continue
            for basin, vals in r.get("basin_q4", {}).items():
                basin_q4[basin].extend(vals)
            all_per_traj.extend(r.get("per_traj_stats", []))

        # Per-basin summary stats
        basin_summary = {}
        for basin, vals in sorted(basin_q4.items()):
            arr = np.array(vals)
            basin_summary[basin] = {
                "n": len(arr),
                "mean": float(arr.mean()),
                "std": float(arr.std()),
                "min": float(arr.min()),
                "max": float(arr.max()),
                "cv": float(arr.std() / arr.mean()) if arr.mean() > 0 else 0,
            }

        # Statistical tests
        stat_tests = {}
        basins_sorted = sorted(basin_q4.keys())
        if HAS_SCIPY and len(basins_sorted) >= 2:
            groups = [np.array(basin_q4[b]) for b in basins_sorted]
            # One-way ANOVA
            if len(groups) >= 2 and all(len(g) > 1 for g in groups):
                try:
                    F, p_anova = _scipy_stats.f_oneway(*groups)
                    stat_tests["anova"] = {"F": float(F), "p": float(p_anova), "basins": basins_sorted}
                except Exception as e:
                    stat_tests["anova"] = {"error": str(e)}

            # Pairwise Mann-Whitney
            from itertools import combinations
            for b1, b2 in combinations(basins_sorted, 2):
                g1, g2 = np.array(basin_q4[b1]), np.array(basin_q4[b2])
                try:
                    u, p_mw = _scipy_stats.mannwhitneyu(g1, g2, alternative="two-sided")
                    # Effect size: rank-biserial correlation
                    n1, n2 = len(g1), len(g2)
                    r_rb = 1 - 2 * u / (n1 * n2)
                    stat_tests[f"mannwhitney_{b1}_{b2}"] = {
                        "U": float(u), "p": float(p_mw), "r_rb": float(r_rb),
                        "n1": n1, "n2": n2,
                    }
                except Exception as e:
                    stat_tests[f"mannwhitney_{b1}_{b2}"] = {"error": str(e)}

        summary = {
            "status": "completed",
            "basin_summary": basin_summary,
            "statistical_tests": stat_tests,
            "per_trajectory_stats": all_per_traj,
            "scipy_available": HAS_SCIPY,
        }

        write_json_report(self.root, "gte_q4_basin_analysis_summary", summary)

        lines = [
            "# Q4 Logarithmic Complexity Charge — Basin Analysis",
            "",
            "## Per-Basin Summary",
            "| Basin | N steps | Mean Q4 | Std Q4 | CV |",
            "|-------|---------|---------|--------|-----|",
        ]
        for basin, s in sorted(basin_summary.items()):
            lines.append(f"| {basin} | {s['n']:,} | {s['mean']:.4f} | {s['std']:.4f} | {s['cv']:.4f} |")

        lines += ["", "## Statistical Tests"]
        for name, t in stat_tests.items():
            if "error" in t:
                lines.append(f"- {name}: ERROR {t['error']}")
            elif "F" in t:
                lines.append(f"- ANOVA: F={t['F']:.2f}, p={t['p']:.2e} (basins: {t['basins']})")
            elif "U" in t:
                lines.append(f"- Mann-Whitney {name}: p={t['p']:.2e}, r_rb={t['r_rb']:.4f} (N={t['n1']},{t['n2']})")

        write_md_report(self.root, "gte_q4_basin_analysis_summary", "\n".join(lines))
        return summary
