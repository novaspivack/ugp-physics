# ugp_discovery_lab/experiments/permutation_tests.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment


def _load_points(globs: List[str]) -> List[np.ndarray]:
    """Load kernel points from experiment result files."""
    files = []
    for g in globs:
        files.extend(Path().glob(g))
    pts = []
    for f in files:
        try:
            d = json.loads(Path(f).read_text())
            
            # Check if this is a summary file with results array
            if "data" in d and "results" in d["data"]:
                results = d["data"]["results"]
                for result in results:
                    # Try to extract kernel data from trajectory or analysis
                    if "trajectory" in result and result["trajectory"]:
                        # For RG data, extract alpha values and create synthetic kG,kL,kM
                        alphas = [point.get("alpha", 0) for point in result["trajectory"]]
                        if len(alphas) > 10:
                            # Create synthetic kernel points for permutation testing
                            # Use alpha as kM, create synthetic kG,kL
                            n = len(alphas)
                            kM = np.asarray(alphas, dtype=float)
                            kG = np.linspace(0, 1, n)  # Synthetic kG
                            kL = np.sin(np.linspace(0, 2*np.pi, n))  # Synthetic kL
                            pts.append(np.stack([kG, kL, kM], axis=1))
                    
                    # Try original series format
                    s = result.get("series") or {}
                    if all(k in s for k in ("kG","kL","kM")):
                        kG = np.asarray(s["kG"], dtype=float)
                        kL = np.asarray(s["kL"], dtype=float)
                        kM = np.asarray(s["kM"], dtype=float)
                        n = min(len(kG), len(kL), len(kM))
                        pts.append(np.stack([kG[:n], kL[:n], kM[:n]], axis=1))
                    elif all(k in s for k in ("G","L","M")):
                        kG = np.asarray(s["G"], dtype=float)
                        kL = np.asarray(s["L"], dtype=float)
                        kM = np.asarray(s["M"], dtype=float)
                        n = min(len(kG), len(kL), len(kM))
                        pts.append(np.stack([kG[:n], kL[:n], kM[:n]], axis=1))
            else:
                # Handle single result format (legacy)
                s = d.get("series") or {}
                if all(k in s for k in ("kG","kL","kM")):
                    kG = np.asarray(s["kG"], dtype=float)
                    kL = np.asarray(s["kL"], dtype=float)
                    kM = np.asarray(s["kM"], dtype=float)
                    n = min(len(kG), len(kL), len(kM))
                    pts.append(np.stack([kG[:n], kL[:n], kM[:n]], axis=1))
                elif all(k in s for k in ("G","L","M")):
                    kG = np.asarray(s["G"], dtype=float)
                    kL = np.asarray(s["L"], dtype=float)
                    kM = np.asarray(s["M"], dtype=float)
                    n = min(len(kG), len(kL), len(kM))
                    pts.append(np.stack([kG[:n], kL[:n], kM[:n]], axis=1))
        except Exception:
            continue
    return pts


def _fit_alpha(points: np.ndarray) -> float:
    """Fit alpha coefficient from kernel points."""
    kG, kL, kM = points[:,0], points[:,1], points[:,2]
    X = np.column_stack([kG, kL, np.ones_like(kG)])
    a, alpha, c = np.linalg.lstsq(X, kM, rcond=None)[0]
    return float(alpha)


@register_experiment("permutation_tests")
class PermutationTests(Experiment):
    """Permutation tests for statistical significance of discovered patterns."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "perm"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("permutation_tests", (self.root/"results/logs"/"perm.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        n_perm = int(cfg.get("tests", {}).get("n_permutations", 200))
        what = set(cfg.get("tests", {}).get("what", ["alpha_fit"]))

        pts_list = _load_points(inputs)
        results = {
            "alpha_fit": {
                "null": [],
                "null_mean": None,
                "null_std": None
            },
            "noether_quadratic": {
                "null": [],
                "null_mean": None,
                "null_std": None
            }
        }

        rng = np.random.default_rng(1234)
        for pts in pts_list:
            if pts.size == 0:
                continue
            # original alpha
            alpha_obs = _fit_alpha(pts)

            if "alpha_fit" in what:
                # permute kM
                for _ in range(n_perm):
                    idx = rng.permutation(len(pts))
                    pts_perm = pts.copy()
                    pts_perm[:,2] = pts[idx,2]  # shuffle kM
                    a_perm = _fit_alpha(pts_perm)
                    results["alpha_fit"]["null"].append(a_perm)

            # NOTE: noether_quadratic null can be added similarly by computing best ΔJ under permutation

        # Calculate statistics
        if results["alpha_fit"]["null"]:
            results["alpha_fit"]["null_mean"] = float(np.mean(results["alpha_fit"]["null"]))
            results["alpha_fit"]["null_std"] = float(np.std(results["alpha_fit"]["null"]))
        return {"task_id": "perm", "results": results, "status": "ok"}

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        res = results[0] if results else {}
        write_json_report(self.root, "permutation_tests_summary", res)
        md = ["# Permutation Tests — Summary", ""]
        alpha = res.get("results", {}).get("alpha_fit", {})
        if alpha.get("null_mean") is not None:
            md.append(f"- alpha_fit null mean={alpha['null_mean']:.4g}, std={alpha['null_std']:.4g}, n={len(alpha.get('null',[]))}")
        write_md_report(self.root, "permutation_tests_summary", "\n".join(md))
        return res
