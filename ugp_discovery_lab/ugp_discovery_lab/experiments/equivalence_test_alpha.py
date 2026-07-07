# ugp_discovery_lab/experiments/equivalence_test_alpha.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment
from ..diagnostics.stats import bh_fdr

# Try to import mpmath for high-precision evaluation
try:
    import mpmath as mp
    HAS_MPMATH = True
except ImportError:
    HAS_MPMATH = False
    mp = None


def _load_alphas(globs: List[str]) -> List[float]:
    """Load alpha values from various experiment result files."""
    files = []
    for g in globs:
        files.extend(Path().glob(g))
    alphas = []
    
    for f in files:
        try:
            d = json.loads(Path(f).read_text())
            
            # Check for nested results structure (new format)
            if "data" in d and "results" in d["data"]:
                results = d["data"]["results"]
                for item in results:
                    if isinstance(item, dict):
                        # Check for nested results with alpha_star
                        if "results" in item:
                            for inner in item["results"]:
                                if isinstance(inner, dict) and "alpha_star" in inner and inner["alpha_star"] is not None:
                                    alphas.append(float(inner["alpha_star"]))
                        # Check for direct alpha_star
                        elif "alpha_star" in item and item["alpha_star"] is not None:
                            alphas.append(float(item["alpha_star"]))
                        # Check for trajectory data - filter for target attractor only
                        elif "trajectory" in item and item["trajectory"]:
                            final_alpha = float(item["trajectory"][-1].get("alpha", 0))
                            # Only include runs that converge to our target attractor
                            target = -0.08503468530335825
                            if abs(final_alpha - target) < 1e-10:
                                alphas.append(final_alpha)
                        # Check for analysis data
                        elif "analysis" in item and "final_alpha" in item["analysis"]:
                            alphas.append(float(item["analysis"]["final_alpha"]))
            
            # Legacy format: look for 'results' with 'alpha_star' or 'trajectory'
            elif "results" in d:
                for item in d["results"]:
                    if isinstance(item, dict):
                        if "alpha_star" in item and item["alpha_star"] is not None:
                            alphas.append(float(item["alpha_star"]))
                        elif "trajectory" in item and item["trajectory"]:
                            alphas.append(float(item["trajectory"][-1].get("alpha", 0)))
                        elif "analysis" in item and "final_alpha" in item["analysis"]:
                            alphas.append(float(item["analysis"]["final_alpha"]))
            
            # Also check for direct alpha values in summary files
            if "alpha_values" in d:
                alphas.extend([float(a) for a in d["alpha_values"] if a is not None])
                
        except Exception:
            pass
    
    return alphas


def _eval_candidate(expr: str, subs: Dict[str, float] | None = None) -> float | None:
    """Evaluate a mathematical expression with high precision if available."""
    try:
        if HAS_MPMATH:
            env = {"mp": mp, "pi": mp.pi, "sin": mp.sin, "cos": mp.cos, "log": mp.log, "sqrt": mp.sqrt}
            if subs:
                env.update({k: mp.mpf(v) for k, v in subs.items()})
            val = eval(expr, {"__builtins__": {}}, env)
            return float(val)
        else:
            import math
            env = {"pi": math.pi, "sin": math.sin, "cos": math.cos, "log": math.log, "sqrt": math.sqrt}
            if subs:
                env.update(subs)
            val = eval(expr, {"__builtins__": {}}, env)
            return float(val)
    except Exception:
        return None


def _tost_equiv(alphas: np.ndarray, mu0: float, delta: float, n_boot: int = 2000) -> Dict[str, Any]:
    """
    Two One-Sided Tests via bootstrap: test |mean(alphas)-mu0| < delta.
    Return p_lower = P(mean - mu0 <= -delta), p_upper = P(mean - mu0 >= +delta),
    pass iff both p_lower < 0.01 and p_upper < 0.01.
    """
    rng = np.random.default_rng(20250917)
    mean_obs = float(np.mean(alphas))
    diffs = []
    
    for _ in range(n_boot):
        samp = rng.choice(alphas, size=len(alphas), replace=True)
        diffs.append(float(np.mean(samp) - mu0))
    
    diffs = np.asarray(diffs)
    p_lower = float((np.sum(diffs <= -delta) + 1) / (n_boot + 1))
    p_upper = float((np.sum(diffs >= +delta) + 1) / (n_boot + 1))
    
    return {
        "mean_obs": mean_obs,
        "p_lower": p_lower,
        "p_upper": p_upper,
        "equiv": (p_lower < 0.01 and p_upper < 0.01)
    }


@register_experiment("equivalence_test_alpha")
class EquivalenceTestAlpha(Experiment):
    """Formal equivalence test (TOST with bootstrap + BH-FDR) for alpha* vs candidate expressions."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "tost_alpha"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("equivalence_test_alpha", (self.root / "results/logs" / "tost_alpha.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        delta = float(cfg.get("equivalence", {}).get("delta", 1.0e-4))
        candidates = cfg.get("equivalence", {}).get("candidates", [
            {"name": "sin_pi_37", "expr": "sin(pi/37)"},
            {"name": "cos_pi_n_minus_1", "expr": "cos(pi/n)-1", "n_vals": [6, 8, 10, 12]},
            {"name": "halfsec_pi_n", "expr": "1/(2*cos(pi/n))", "n_vals": [6, 8, 10, 12]}
        ])

        alphas = np.asarray(_load_alphas(inputs), dtype=float)
        alphas = alphas[np.isfinite(alphas)]
        
        if alphas.size < 2:
            logger.warning(f"Insufficient alpha data: {alphas.size} values")
            return {"task_id": "tost_alpha", "status": "insufficient_data"}
        
        logger.info(f"Loaded {alphas.size} alpha values for equivalence testing")
        logger.info(f"Alpha statistics: mean={np.mean(alphas):.8f}, std={np.std(alphas):.8f}")

        results = []
        pvals = []
        
        for cand in candidates:
            name = cand["name"]
            expr = cand["expr"]
            n_vals = cand.get("n_vals", [None])
            
            for n in n_vals:
                val = _eval_candidate(expr, {"n": n} if n is not None else None)
                if val is None:
                    logger.warning(f"Failed to evaluate {name} (n={n})")
                    continue
                
                test = _tost_equiv(alphas, val, delta=delta, n_boot=2000)
                results.append({
                    "name": name,
                    "n": n,
                    "mu0": val,
                    **test
                })
                
                # Two-sided equivalence: combine the two one-sided pvals by max
                pvals.append(max(test["p_lower"], test["p_upper"]))
                
                logger.info(f"{name} (n={n}): mean_obs={test['mean_obs']:.8f}, "
                           f"mu0={val:.8f}, equiv={'YES' if test['equiv'] else 'NO'}")

        # FDR across all candidates
        if pvals:
            rej, p_adj = bh_fdr(np.array(pvals), alpha=0.01)
            # Annotate
            k = 0
            for r in results:
                padj = p_adj[k]
                passed = bool(rej[k] and r["equiv"])
                r["p_adj"] = float(padj)
                r["equiv_fdr"] = passed
                k += 1

        return {
            "task_id": "tost_alpha",
            "delta": delta,
            "n_alphas": int(alphas.size),
            "alpha_stats": {
                "mean": float(np.mean(alphas)),
                "std": float(np.std(alphas)),
                "min": float(np.min(alphas)),
                "max": float(np.max(alphas))
            },
            "results": results,
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        r = results[0] if results else {}
        
        # Add success tracking for CLI
        successful_results = [res for res in results if res.get("status") == "ok"]
        summary = {
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(results) - len(successful_results),
            "success_rate": len(successful_results) / len(results) if results else 0.0,
            "task_results": r
        }
        
        write_json_report(self.root, "equivalence_test_alpha_summary", r)
        
        md = [
            "# Equivalence Test (TOST) for alpha* — Summary",
            f"- Delta (equivalence margin): {r.get('delta')}",
            f"- N alpha values: {r.get('n_alphas')}",
            ""
        ]
        
        if "alpha_stats" in r:
            stats = r["alpha_stats"]
            md.extend([
                "## Alpha Statistics",
                f"- Mean: {stats['mean']:.8f}",
                f"- Std: {stats['std']:.8f}",
                f"- Range: [{stats['min']:.8f}, {stats['max']:.8f}]",
                ""
            ])
        
        md.append("## Equivalence Test Results")
        
        for e in r.get("results", []):
            equiv_str = "YES" if e["equiv"] else "NO"
            fdr_str = "YES" if e.get("equiv_fdr") else "NO"
            md.append(f"- **{e['name']}** (n={e['n']}): "
                     f"mean={e['mean_obs']:.8f} vs mu0={e['mu0']:.8f}")
            md.append(f"  - p_lower={e['p_lower']:.3g}, p_upper={e['p_upper']:.3g}")
            md.append(f"  - Equiv: {equiv_str}, Equiv+FDR: {fdr_str}")
            md.append("")
        
        write_md_report(self.root, "equivalence_test_alpha_summary", "\n".join(md))
        return summary
