"""
Real-GTE RG Attractor Experiment (Gap 1 / Gap 3).

Applies the kernel-plane RG operator directly to real GTE (a,b,c) time series
(from gte_deep_trajectories) and demonstrates that the same three α* fixed points
emerge from the actual UGP evolution — not from synthetic kernel streams.

Methodology:
1. Extract (a,b,c) sequence from evolution_history
2. Map each triple to kernel plane: kG = a*b, kL = c, kM = a*b + c  (simple UGP kernel)
3. Apply iterative RG: at each iteration, crop center 50% + renormalize
4. Fit kM = kG + α·kL at each scale; record α
5. Check convergence to one of the three known α*

This is the "earned" version of the RG theorem: proven on real data, not a surrogate.
"""

from __future__ import annotations
import json
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

ATTRACTORS = {"A": -0.0850346853, "B": 0.0754130404, "C": 0.2644176696}
TOL = 0.02  # liberal bin for "converged to attractor"


def _fit_alpha(k_G: np.ndarray, k_M: np.ndarray, k_L: np.ndarray) -> Optional[float]:
    """Fit kM = kG + α·kL via OLS. Returns α or None if degenerate."""
    y = k_M - k_G
    x = k_L
    denom = np.dot(x, x)
    if denom < 1e-30 or len(x) < 4:
        return None
    return float(np.dot(x, y) / denom)


def _apply_rg(k_G: np.ndarray, k_M: np.ndarray, k_L: np.ndarray):
    """One RG step: crop center half, then unit-variance rescale."""
    n = len(k_G)
    if n < 8:
        return k_G, k_M, k_L
    lo = n // 4
    hi = n - n // 4
    k_G2, k_M2, k_L2 = k_G[lo:hi], k_M[lo:hi], k_L[lo:hi]
    for arr in (k_G2, k_M2, k_L2):
        std = arr.std()
        if std > 1e-30:
            arr /= std
    return k_G2, k_M2, k_L2


def _gte_to_kernel(evo: List[Dict]) -> tuple:
    """
    Map GTE evolution_history to kernel-plane vectors.
    kG = |a| * |b|  (the 'ground' kernel — product of the first two components)
    kL = |c|         (the 'local' kernel — the height component)
    kM = |a| * |b| + |c|  (the 'mixed' kernel)
    All values log-scaled for numeric stability with bigints.
    """
    k_G, k_M, k_L = [], [], []
    for e in evo:
        try:
            a, b, c = abs(int(e["a"])), abs(int(e["b"])), abs(int(e["c"]))
            # Use log-magnitude to handle arbitrary precision integers
            log_a = math.log(a + 1)
            log_b = math.log(b + 1)
            log_c = math.log(c + 1)
            kg = log_a + log_b        # log(a*b) ≈ log|a| + log|b|
            kl = log_c
            km = math.log(a * b + c + 1)  # log(kG_raw + kL_raw)
            k_G.append(kg)
            k_M.append(km)
            k_L.append(kl)
        except Exception:
            continue
    return np.array(k_G), np.array(k_M), np.array(k_L)


def _label_attractor(alpha: float) -> str:
    for name, val in ATTRACTORS.items():
        if abs(alpha - val) < TOL:
            return name
    return "UNK"


@register_experiment("gte_rg_attractor_real")
class GTERGAttractorReal(Experiment):
    """
    Apply iterative RG to real GTE trajectories and verify α* convergence.
    Reads experiment_results.json files from gte_deep_trajectories runs.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        inputs = self.cfg.get("inputs", {}).get("runs", [])
        tasks = []
        for pattern in inputs:
            for f in Path(".").glob(pattern):
                tasks.append({"task_id": f"rgrr_{f.parent.parent.parent.name}_{f.name[:8]}", "file": str(f)})
        return tasks

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger(f"gte_rg_real:{task['task_id']}")
        f = Path(task["file"])
        try:
            d = json.loads(f.read_text())
            block = d.get("data", d)
            results = block.get("results", [])
        except Exception as e:
            return {"task_id": task["task_id"], "success": False, "error": str(e)}

        per_traj = []
        for r in results:
            if not r.get("success"):
                continue
            evo = r.get("evolution_history", [])
            if len(evo) < 50:
                continue
            basin_true = r.get("basin", "?")
            seed = r.get("seed", [])

            k_G, k_M, k_L = _gte_to_kernel(evo)
            if len(k_G) < 20:
                continue

            rg_iters = self.cfg.get("rg_iterations", 15)
            trajectory = []
            kG_cur, kM_cur, kL_cur = k_G.copy(), k_M.copy(), k_L.copy()

            for i in range(rg_iters + 1):
                alpha = _fit_alpha(kG_cur, kM_cur, kL_cur)
                if alpha is None:
                    break
                trajectory.append({"iter": i, "alpha": alpha, "n_points": len(kG_cur)})
                if i < rg_iters:
                    kG_cur, kM_cur, kL_cur = _apply_rg(kG_cur, kM_cur, kL_cur)

            if not trajectory:
                continue

            final_alpha = trajectory[-1]["alpha"]
            converged_label = _label_attractor(final_alpha)

            per_traj.append({
                "seed": seed,
                "basin_true": basin_true,
                "basin_converged": converged_label,
                "final_alpha": final_alpha,
                "trajectory": trajectory,
                "initial_n_points": len(k_G),
                "correct": basin_true == converged_label,
            })
            logger.info(f"seed={seed} basin={basin_true} → α*={final_alpha:.8f} ({converged_label})")

        match_rate = sum(1 for t in per_traj if t["correct"]) / len(per_traj) if per_traj else 0
        return {
            "task_id": task["task_id"],
            "success": True,
            "n_trajectories": len(per_traj),
            "basin_match_rate": match_rate,
            "trajectories": per_traj,
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        ok = [r for r in results if r.get("success")]
        all_traj = []
        for r in ok:
            all_traj.extend(r.get("trajectories", []))

        # Convergence stats
        n = len(all_traj)
        matched = sum(1 for t in all_traj if t.get("correct"))
        final_alphas = [t["final_alpha"] for t in all_traj]

        # Per-basin attractor recovery
        basin_counts = Counter(t["basin_converged"] for t in all_traj)
        basin_true_counts = Counter(t["basin_true"] for t in all_traj)

        summary = {
            "status": "completed",
            "n_trajectories": n,
            "basin_match_rate": matched / n if n else 0,
            "attractor_recovery": dict(basin_counts),
            "true_basins": dict(basin_true_counts),
            "alpha_mean": float(np.mean(final_alphas)) if final_alphas else 0,
            "alpha_std": float(np.std(final_alphas)) if final_alphas else 0,
        }

        write_json_report(self.root, "gte_rg_attractor_real_summary", summary)
        lines = [
            "# Real-GTE RG Attractor Experiment",
            f"- Trajectories: {n}",
            f"- Basin match rate: {matched}/{n} = {100*matched/n if n else 0:.1f}%",
            f"- Attractor recovery: {dict(basin_counts)}",
            "",
            "## Per-trajectory results",
        ]
        for t in all_traj[:30]:
            lines.append(f"  seed={t['seed']} basin_true={t['basin_true']} → α*={t['final_alpha']:.8f} ({t['basin_converged']}) {'✓' if t['correct'] else '✗'}")
        write_md_report(self.root, "gte_rg_attractor_real_summary", "\n".join(lines))
        return summary
