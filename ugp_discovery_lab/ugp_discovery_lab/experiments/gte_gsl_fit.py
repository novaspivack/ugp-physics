"""
GSL Parameter Fit from Real GTE Trajectories (Gap 6).

Derives the Generalized Second Law parameters C and p from scratch using
long real GTE trajectories — replacing the unsubstantiated holographic_thermodynamics_extended
result.

Method:
1. Generate boundary states (ridge/mirror events) and bulk states from each trajectory
2. Compute local entropy S(t) via coarse-grained histogram
3. Compute holographic information I_holo(t) = mutual information between
   boundary triple and bulk triple at each step
4. Fit: I_total = S × (1 + C × I_holo^p) to maximize conservation
5. Report best (C, p) and the improvement over entropy-only conservation

If C=0.4, p=1.0 comes back, the result is reproduced. If different values emerge,
those are the correct values to report.
"""

from __future__ import annotations
import json
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import Counter
import itertools

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

N_BINS = 16


def _coarse_grain_single(e: dict) -> Tuple[int, int]:
    try:
        b = abs(int(e["b"]))
        c = abs(int(e["c"]))
        lb = math.log(b + 1)
        lc = math.log(c + 1)
        return (int(lb * N_BINS / 10) % N_BINS, int(lc * N_BINS / 10) % N_BINS)
    except Exception:
        return (0, 0)


def _is_ridge_event(e: dict) -> bool:
    """Simple ridge detection: step_type contains 'ridge' or even step."""
    st = e.get("step_type", "")
    if "ridge" in st.lower():
        return True
    return e.get("step", 0) % 2 == 0


def _local_entropy(states: list, t: int, window: int = 20) -> float:
    """Sliding-window entropy at step t."""
    lo = max(0, t - window)
    window_states = states[lo:t+1]
    if not window_states:
        return 0.0
    counts = Counter(window_states)
    total = len(window_states)
    return -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)


def _mutual_information(boundary_states: list, bulk_states: list, t: int, window: int = 20) -> float:
    """MI between boundary and bulk macro-states in recent window."""
    lo = max(0, t - window)
    bs = boundary_states[lo:t+1]
    bl = bulk_states[lo:t+1]
    if len(bs) != len(bl) or len(bs) < 4:
        return 0.0
    pairs = list(zip(bs, bl))
    n = len(pairs)
    c_b = Counter(bs)
    c_l = Counter(bl)
    c_pair = Counter(pairs)
    mi = 0.0
    for (bi, li), c in c_pair.items():
        pxy = c / n
        px = c_b[bi] / n
        py = c_l[li] / n
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * math.log2(pxy / (px * py))
    return max(0.0, mi)


def _conservation_quality(I_total: np.ndarray) -> Dict[str, float]:
    """How well is I_total conserved? Lower CV = better conservation."""
    if len(I_total) < 3 or I_total.mean() == 0:
        return {"cv": float("inf"), "cv_improvement": 0.0}
    cv = float(I_total.std() / I_total.mean())
    return {"cv": cv}


def _fit_gsl(evo: list, C_grid: list, p_grid: list):
    """Grid search over C, p to minimize CV of I_total."""
    states_all = [_coarse_grain_single(e) for e in evo]
    boundary_states = [_coarse_grain_single(e) for e in evo if _is_ridge_event(e)]
    # align boundary and bulk by step index
    b_map = {e["step"]: _coarse_grain_single(e) for e in evo if _is_ridge_event(e)}
    bl_map = {e["step"]: _coarse_grain_single(e) for e in evo if not _is_ridge_event(e)}

    # Only analyze steps with both boundary and bulk data
    common_steps = sorted(set(b_map) & set(bl_map))
    if len(common_steps) < 20:
        return None

    window = min(20, len(common_steps) // 5)
    S_series = []
    I_holo_series = []

    b_states = [b_map[t] for t in common_steps]
    l_states = [bl_map[t] for t in common_steps]

    for i in range(len(common_steps)):
        lo = max(0, i - window)
        bs = b_states[lo:i+1]
        ls = l_states[lo:i+1]
        # S = entropy of all states up to this point
        all_s = states_all[:common_steps[i]+1]
        cnt = Counter(all_s)
        total = len(all_s)
        S = -sum((c/total)*math.log2(c/total) for c in cnt.values() if c > 0)
        # I_holo = MI between boundary and bulk in window
        pairs = list(zip(bs, ls))
        n = len(pairs)
        cb = Counter(bs)
        cl = Counter(ls)
        cp = Counter(pairs)
        mi = 0.0
        for (bi, li), c in cp.items():
            pxy = c/n
            px = cb[bi]/n
            py = cl[li]/n
            if pxy > 0 and px > 0 and py > 0:
                mi += pxy * math.log2(pxy/(px*py))
        mi = max(0.0, mi)
        S_series.append(S)
        I_holo_series.append(mi)

    S_arr = np.array(S_series)
    Ih_arr = np.array(I_holo_series)

    # Baseline: CV of S alone
    cv_s = float(S_arr.std() / S_arr.mean()) if S_arr.mean() > 0 else float("inf")

    best = {"C": 0.0, "p": 1.0, "cv": float("inf"), "improvement": 0.0}
    for C in C_grid:
        for p in p_grid:
            I_total = S_arr * (1 + C * (Ih_arr ** p))
            cv = float(I_total.std() / I_total.mean()) if I_total.mean() > 0 else float("inf")
            if cv < best["cv"]:
                best = {"C": C, "p": p, "cv": cv,
                        "improvement": (cv_s - cv) / cv_s if cv_s > 0 else 0}

    # Correlation between ΔS and ΔI_holo
    delta_S = np.diff(S_arr)
    delta_Ih = np.diff(Ih_arr)
    if len(delta_S) > 3:
        try:
            from scipy.stats import pearsonr
            r, p_val = pearsonr(delta_S, delta_Ih)
            best["delta_correlation_r"] = float(r)
            best["delta_correlation_p"] = float(p_val)
        except Exception:
            pass

    best["cv_entropy_only"] = cv_s
    best["n_steps"] = len(common_steps)
    return best


@register_experiment("gte_gsl_fit")
class GTEGSLFit(Experiment):

    def tasks(self) -> List[Dict[str, Any]]:
        inputs = self.cfg.get("inputs", {}).get("runs", [])
        tasks = []
        for pattern in inputs:
            for f in Path(".").glob(pattern):
                tasks.append({"task_id": f"gsl_{f.parent.parent.parent.name}", "file": str(f)})
        return tasks

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger(f"gsl:{task['task_id']}")
        cfg = self.cfg
        C_grid = cfg.get("C_grid", [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0])
        p_grid = cfg.get("p_grid", [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0])

        try:
            d = json.loads(Path(task["file"]).read_text())
            block = d.get("data", d)
            results = block.get("results", [])
        except Exception as e:
            return {"task_id": task["task_id"], "success": False, "error": str(e)}

        traj_results = []
        for r in results:
            if not r.get("success"):
                continue
            evo = r.get("evolution_history", [])
            if len(evo) < 200:
                continue
            basin = r.get("basin", "?")
            best = _fit_gsl(evo, C_grid, p_grid)
            if best is None:
                continue
            best["basin"] = basin
            best["seed"] = r.get("seed")
            traj_results.append(best)
            logger.info(f"basin={basin} best C={best['C']}, p={best['p']}, cv={best['cv']:.4f}, improvement={best['improvement']:.2%}")

        return {"task_id": task["task_id"], "success": True, "traj_results": traj_results}

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_traj = []
        for r in results:
            if r.get("success"):
                all_traj.extend(r.get("traj_results", []))

        if not all_traj:
            return {"status": "no_data"}

        # Most common best (C, p) pair
        best_pairs = Counter((t["C"], t["p"]) for t in all_traj)
        modal_C, modal_p = best_pairs.most_common(1)[0][0]

        improvements = [t["improvement"] for t in all_traj if "improvement" in t]
        corrs = [t["delta_correlation_r"] for t in all_traj if "delta_correlation_r" in t]

        summary = {
            "status": "completed",
            "n_trajectories": len(all_traj),
            "modal_C": modal_C,
            "modal_p": modal_p,
            "best_pair_distribution": {f"C={k[0]}_p={k[1]}": v for k, v in best_pairs.most_common(10)},
            "mean_cv_improvement": float(np.mean(improvements)) if improvements else 0,
            "mean_delta_S_I_holo_correlation": float(np.mean(corrs)) if corrs else None,
            "trajectories": all_traj,
        }

        write_json_report(self.root, "gte_gsl_fit_summary", summary)
        lines = [
            "# GSL Parameter Fit (Real GTE Trajectories)",
            "",
            f"- Trajectories: {len(all_traj)}",
            f"- Modal best C={modal_C}, p={modal_p}",
            f"- Mean CV improvement: {float(np.mean(improvements)) if improvements else 0:.2%}",
        ]
        if corrs:
            lines.append(f"- Mean ΔS vs ΔI_holo correlation: r={float(np.mean(corrs)):.4f}")
        lines += ["", "## Best (C,p) distribution (top 5)"]
        for (c, p), cnt in best_pairs.most_common(5):
            lines.append(f"  C={c}, p={p}: {cnt} trajectories")
        write_md_report(self.root, "gte_gsl_fit_summary", "\n".join(lines))
        return summary
