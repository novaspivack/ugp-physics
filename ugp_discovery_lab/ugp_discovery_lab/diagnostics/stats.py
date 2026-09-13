# ugp_discovery_lab/diagnostics/stats.py
"""
Statistical helpers for rigorous hypothesis testing.
Includes bootstrap confidence intervals, empirical p-values, and FDR correction.
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple


def bootstrap_ci(x: np.ndarray, n_boot: int = 1000, agg: str = "mean", alpha: float = 0.05) -> List[float]:
    """
    Bootstrap confidence interval for a statistic.
    
    Args:
        x: Input data array
        n_boot: Number of bootstrap samples
        agg: Aggregation function ("mean", "median")
        alpha: Significance level (default 0.05 for 95% CI)
        
    Returns:
        [lower_bound, upper_bound] or [None, None] if insufficient data
    """
    rng = np.random.default_rng(20250917)
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return [None, None]
    
    stats = []
    for _ in range(n_boot):
        sample = x[rng.integers(0, len(x), size=len(x))]
        if agg == "mean":
            stats.append(sample.mean())
        elif agg == "median":
            stats.append(np.median(sample))
        else:
            stats.append(sample.mean())
    
    stats = np.sort(np.asarray(stats))
    lo = stats[int((alpha/2) * n_boot)]
    hi = stats[int((1-alpha/2) * n_boot) - 1]
    return [float(lo), float(hi)]


def empirical_pvalue(obs: float, nulls: np.ndarray, side: str = "two") -> float:
    """
    Compute empirical p-value from null distribution.
    
    Args:
        obs: Observed statistic value
        nulls: Array of null statistic values
        side: Test direction ("two", "greater", "less")
        
    Returns:
        Empirical p-value
    """
    nulls = np.asarray(nulls, dtype=float)
    if nulls.size == 0:
        return None
    
    if side == "two":
        return float((np.sum(np.abs(nulls) >= abs(obs)) + 1) / (len(nulls) + 1))
    elif side == "greater":
        return float((np.sum(nulls >= obs) + 1) / (len(nulls) + 1))
    else:  # "less"
        return float((np.sum(nulls <= obs) + 1) / (len(nulls) + 1))


def bh_fdr(pvals: np.ndarray, alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Benjamini-Hochberg false discovery rate correction.
    
    Args:
        pvals: Array of p-values
        alpha: FDR threshold
        
    Returns:
        (rejection_decisions, adjusted_p_values)
    """
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranks = np.arange(1, n + 1)
    thresh = alpha * ranks / n
    rej = np.zeros(n, dtype=bool)
    rej[order] = p[order] <= thresh
    
    # Strong control: ensure monotonicity
    if rej.any():
        kmax = np.max(np.where(rej)[0])
        rej[:kmax+1] = True
        rej[kmax+1:] = False
    
    return rej.tolist(), p.tolist()
