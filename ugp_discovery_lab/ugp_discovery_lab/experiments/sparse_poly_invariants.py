# ugp_discovery_lab/experiments/sparse_poly_invariants.py
"""
Sparse random polynomial invariant scan up to degree 3.
Samples tiny random subsets of monomials and tests for near-conservation.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import numpy as np
import random

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment


def _load_runs(run_globs: List[str]) -> List[Dict[str, Any]]:
    """Load experiment result files from glob patterns."""
    files = []
    for g in run_globs:
        files.extend(Path().glob(g))
    
    out = []
    for f in files:
        try:
            out.append(json.loads(Path(f).read_text()))
        except Exception:
            pass
    return out


def _extract_series(data: List[Dict[str, Any]]) -> List[np.ndarray]:
    """Extract M, G, L series from datasets."""
    series_list = []
    
    for d in data:
        for item in d.get("results", []):
            s = item.get("series") or {}
            if all(k in s for k in ("M", "G", "L")):
                M = np.asarray(s["M"], dtype=float)
                G = np.asarray(s["G"], dtype=float)
                L = np.asarray(s["L"], dtype=float)
                n = min(len(M), len(G), len(L))
                if n > 10:
                    series_list.append(np.stack([M[:n], G[:n], L[:n]], axis=1))
    
    return series_list


def _build_monomial_library(degree_max: int = 3) -> List[Tuple[str, callable]]:
    """Build library of monomial functions up to degree_max."""
    monomials = []
    
    # Linear terms
    monomials.append(("M", lambda x: x[:, 0]))
    monomials.append(("G", lambda x: x[:, 1]))
    monomials.append(("L", lambda x: x[:, 2]))
    
    if degree_max >= 2:
        # Quadratic terms
        monomials.append(("M^2", lambda x: x[:, 0] ** 2))
        monomials.append(("G^2", lambda x: x[:, 1] ** 2))
        monomials.append(("L^2", lambda x: x[:, 2] ** 2))
        monomials.append(("MG", lambda x: x[:, 0] * x[:, 1]))
        monomials.append(("ML", lambda x: x[:, 0] * x[:, 2]))
        monomials.append(("GL", lambda x: x[:, 1] * x[:, 2]))
    
    if degree_max >= 3:
        # Cubic terms
        monomials.append(("M^3", lambda x: x[:, 0] ** 3))
        monomials.append(("G^3", lambda x: x[:, 1] ** 3))
        monomials.append(("L^3", lambda x: x[:, 2] ** 3))
        monomials.append(("M^2G", lambda x: x[:, 0] ** 2 * x[:, 1]))
        monomials.append(("M^2L", lambda x: x[:, 0] ** 2 * x[:, 2]))
        monomials.append(("G^2M", lambda x: x[:, 1] ** 2 * x[:, 0]))
        monomials.append(("G^2L", lambda x: x[:, 1] ** 2 * x[:, 2]))
        monomials.append(("L^2M", lambda x: x[:, 2] ** 2 * x[:, 0]))
        monomials.append(("L^2G", lambda x: x[:, 2] ** 2 * x[:, 1]))
        monomials.append(("MGL", lambda x: x[:, 0] * x[:, 1] * x[:, 2]))
    
    return monomials


def _l1_coordinate_descent(X: np.ndarray, y: np.ndarray, lambda_l1: float, max_iter: int = 100) -> np.ndarray:
    """Simple coordinate descent for L1-regularized least squares."""
    n_features = X.shape[1]
    w = np.zeros(n_features)
    
    for _ in range(max_iter):
        w_old = w.copy()
        for j in range(n_features):
            # Compute residual without feature j
            r = y - X @ w + X[:, j] * w[j]
            # Soft thresholding
            xj_norm = np.sum(X[:, j] ** 2)
            if xj_norm > 0:
                soft_thresh = np.sum(r * X[:, j]) / xj_norm
                w[j] = np.sign(soft_thresh) * max(0, abs(soft_thresh) - lambda_l1 / xj_norm)
        
        # Check convergence
        if np.max(np.abs(w - w_old)) < 1e-6:
            break
    
    return w


def _test_invariant(series: np.ndarray, monomial_indices: List[int], monomials: List[Tuple[str, callable]], 
                   lambda_l1: float) -> Dict[str, Any]:
    """Test a specific invariant combination."""
    try:
        # Build design matrix
        X = np.column_stack([monomials[i][1](series) for i in monomial_indices])
        
        # Compute J = sum of monomials
        J = np.sum(X, axis=1)
        
        # Compute ΔJ = J[t+1] - J[t]
        dJ = np.diff(J)
        
        # Check if this looks like a conserved quantity
        max_abs_dJ = np.max(np.abs(dJ))
        mean_abs_dJ = np.mean(np.abs(dJ))
        
        # Build feature matrix for L1 regression
        X_lagged = X[:-1]  # Remove last point
        y = X[1:]  # Predict next values
        
        # Fit with L1 regularization
        w = _l1_coordinate_descent(X_lagged, y, lambda_l1)
        
        # Check sparsity (how many coefficients are non-zero)
        n_nonzero = np.sum(np.abs(w) > 1e-6)
        sparsity = n_nonzero / len(w)
        
        return {
            "monomial_names": [monomials[i][0] for i in monomial_indices],
            "max_abs_dJ": float(max_abs_dJ),
            "mean_abs_dJ": float(mean_abs_dJ),
            "coefficients": w.tolist(),
            "sparsity": float(sparsity),
            "n_points": len(dJ)
        }
    
    except Exception as e:
        return {"error": str(e)}


def _permutation_test(series: np.ndarray, monomial_indices: List[int], monomials: List[Tuple[str, callable]], 
                     n_perm: int = 200) -> float:
    """Permutation test for significance."""
    # Get observed statistic
    result = _test_invariant(series, monomial_indices, monomials, 0.0)  # No regularization for null test
    if "error" in result:
        return 1.0
    
    observed_max_dJ = result["max_abs_dJ"]
    
    # Generate null distribution
    null_stats = []
    for _ in range(n_perm):
        # Shuffle the series
        perm_series = series.copy()
        np.random.shuffle(perm_series)
        
        perm_result = _test_invariant(perm_series, monomial_indices, monomials, 0.0)
        if "error" not in perm_result:
            null_stats.append(perm_result["max_abs_dJ"])
    
    if not null_stats:
        return 1.0
    
    # Compute p-value
    p_value = np.mean(np.array(null_stats) <= observed_max_dJ)
    return float(p_value)


@register_experiment("sparse_poly_invariants")
class SparsePolyInvariants(Experiment):
    """Sparse random polynomial invariant scan up to degree 3."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        cfg = self.cfg
        trials = int(cfg.get("search", {}).get("trials", 200))
        
        return [{"task_id": "sparse_poly_scan", "trials": trials}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("sparse_poly_invariants", (self.root / "results/logs" / "sparse_poly.log"))
        cfg = self.cfg
        
        # Configuration
        degree_max = int(cfg.get("search", {}).get("degree_max", 3))
        trials = int(cfg.get("search", {}).get("trials", 200))
        subset_size = int(cfg.get("search", {}).get("subset_size", 5))
        lambda_l1 = float(cfg.get("search", {}).get("lambda_l1", 1e-4))
        tol_max_abs_dJ = float(cfg.get("search", {}).get("tol_max_abs_dJ", 1e-8))
        tol_mean_abs_dJ = float(cfg.get("search", {}).get("tol_mean_abs_dJ", 1e-9))
        n_perm = int(cfg.get("nulls", {}).get("n_perm", 200))
        
        # Load data
        inputs = cfg.get("inputs", {}).get("runs", [])
        datasets = _load_runs(inputs)
        series_list = _extract_series(datasets)
        
        if not series_list:
            logger.warning("No valid series found")
            return {"task_id": "sparse_poly_scan", "status": "no_data", "candidates": []}
        
        # Build monomial library
        monomials = _build_monomial_library(degree_max)
        logger.info(f"Built monomial library with {len(monomials)} terms up to degree {degree_max}")
        
        # Test random subsets
        candidates = []
        rng = random.Random(12345)
        
        for trial in range(trials):
            # Random subset of monomials
            monomial_indices = rng.sample(range(len(monomials)), min(subset_size, len(monomials)))
            
            # Test on all series
            for series in series_list:
                result = _test_invariant(series, monomial_indices, monomials, lambda_l1)
                
                if "error" not in result:
                    max_dJ = result["max_abs_dJ"]
                    mean_dJ = result["mean_abs_dJ"]
                    
                    # Check tolerance
                    if max_dJ <= tol_max_abs_dJ and mean_dJ <= tol_mean_abs_dJ:
                        # Run permutation test
                        p_value = _permutation_test(series, monomial_indices, monomials, n_perm)
                        
                        candidate = {
                            "trial": trial,
                            "monomial_names": result["monomial_names"],
                            "max_abs_dJ": max_dJ,
                            "mean_abs_dJ": mean_dJ,
                            "sparsity": result["sparsity"],
                            "p_value": p_value,
                            "significant": p_value <= 0.01
                        }
                        candidates.append(candidate)
        
        # Sort by significance and conservation quality
        candidates.sort(key=lambda c: (c["significant"], -c["max_abs_dJ"]))
        
        # Count significant candidates
        n_significant = sum(1 for c in candidates if c["significant"])
        
        verdict = n_significant > 0
        
        return {
            "task_id": "sparse_poly_scan",
            "trials": trials,
            "n_series_tested": len(series_list),
            "n_candidates": len(candidates),
            "n_significant": n_significant,
            "verdict": verdict,
            "top_candidates": candidates[:10],  # Top 10 candidates
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        r = results[0] if results else {}
        write_json_report(self.root, "sparse_poly_invariants_summary", r)
        
        md = [
            "# Sparse Polynomial Invariants — Summary",
            f"- Trials: {r.get('trials', 0)}",
            f"- Series tested: {r.get('n_series_tested', 0)}",
            f"- Total candidates: {r.get('n_candidates', 0)}",
            f"- Significant candidates: {r.get('n_significant', 0)}",
            f"- Verdict: {'PASS' if r.get('verdict') else 'FAIL'}"
        ]
        
        if r.get("top_candidates"):
            md.append("\n## Top Candidates")
            for i, candidate in enumerate(r["top_candidates"][:5]):
                md.append(f"### Candidate {i+1}")
                md.append(f"- Monomials: {', '.join(candidate['monomial_names'])}")
                md.append(f"- max|ΔJ|: {candidate['max_abs_dJ']:.2e}")
                md.append(f"- mean|ΔJ|: {candidate['mean_abs_dJ']:.2e}")
                md.append(f"- p-value: {candidate['p_value']:.3f}")
                md.append(f"- Significant: {'Yes' if candidate['significant'] else 'No'}")
        
        write_md_report(self.root, "sparse_poly_invariants_summary", "\n".join(md))
        return r
