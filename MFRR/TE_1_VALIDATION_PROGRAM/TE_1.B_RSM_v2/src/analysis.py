"""Analysis utilities for TE₁.B_v2 minimal reflexive testbed.

Specification: docs/TE1B_Minimal_RSM_Spec.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Tuple

import math
import numpy as np


@dataclass
class CrooksFitResult:
    slope: float
    intercept: float
    status: str


def estimate_crooks_slope(forward: Iterable[float], reverse: Iterable[float]) -> CrooksFitResult:
    """Estimate Crooks slope using logistic regression.

    Args:
        forward: ΔS_ref samples from forward protocol.
        reverse: ΔS_ref samples from reverse protocol.
    """
    fwd = np.asarray(list(forward), dtype=np.float64)
    rev = np.asarray(list(reverse), dtype=np.float64)
    if fwd.size == 0 or rev.size == 0:
        return CrooksFitResult(slope=float("nan"), intercept=float("nan"), status="insufficient")
    x = np.concatenate([fwd, rev])
    y = np.concatenate([np.zeros(fwd.size, dtype=np.float64), np.ones(rev.size, dtype=np.float64)])
    intercept, slope, status = _logistic_fit(x, y)
    return CrooksFitResult(slope=abs(slope), intercept=intercept, status=status)


def _logistic_fit(x: np.ndarray, y: np.ndarray, max_iter: int = 80, tol: float = 1e-8) -> Tuple[float, float, str]:
    beta = np.zeros(2, dtype=np.float64)
    for _ in range(max_iter):
        z = beta[0] + beta[1] * x
        p = 1.0 / (1.0 + np.exp(-z))
        w = p * (1.0 - p)
        grad0 = np.sum(p - y)
        grad1 = np.sum((p - y) * x)
        grad = np.array([grad0, grad1])
        h00 = np.sum(w)
        h01 = np.sum(w * x)
        h11 = np.sum(w * x * x)
        hessian = np.array([[h00, h01], [h01, h11]])
        try:
            step = np.linalg.solve(hessian, grad)
        except np.linalg.LinAlgError:
            return beta[0], beta[1], "singular"
        beta -= step
        if np.linalg.norm(step) < tol:
            return beta[0], beta[1], "converged"
    return beta[0], beta[1], "max_iter"


def jarzynski_statistic(samples: Iterable[float]) -> float:
    values = np.asarray(list(samples), dtype=np.float64)
    if values.size == 0:
        return float("nan")
    return float(np.mean(np.exp(-values)))


def bootstrap_ci(samples: Iterable[float], estimator: Callable[[Iterable[float]], float], *, n_bootstrap: int = 1000, confidence: float = 0.95, rng: np.random.Generator | None = None) -> Tuple[float, float]:
    """Non-parametric bootstrap confidence interval for an estimator."""
    data = np.asarray(list(samples), dtype=np.float64)
    if data.size == 0:
        return float("nan"), float("nan")
    rng = rng or np.random.default_rng()
    estimates = []
    for _ in range(n_bootstrap):
        resample = rng.choice(data, size=data.size, replace=True)
        estimates.append(estimator(resample))
    estimates = np.array(estimates, dtype=np.float64)
    lower = np.quantile(estimates, (1.0 - confidence) / 2.0)
    upper = np.quantile(estimates, 1.0 - (1.0 - confidence) / 2.0)
    return float(lower), float(upper)


def green_kubo_integral(series: np.ndarray, dt: float = 1.0) -> float:
    """Compute Green–Kubo susceptibility via autocorrelation integral."""
    if series.size == 0:
        return float("nan")
    series = series - np.mean(series)
    autocorr = np.correlate(series, series, mode="full")
    autocorr = autocorr[autocorr.size // 2 :] / np.arange(series.size, 0, -1)
    return float(np.sum(autocorr) * dt)


def finite_difference_response(mean_plus: float, mean_minus: float, delta_mu: float) -> float:
    if delta_mu == 0.0:
        return float("nan")
    return (mean_plus - mean_minus) / (2.0 * delta_mu)
