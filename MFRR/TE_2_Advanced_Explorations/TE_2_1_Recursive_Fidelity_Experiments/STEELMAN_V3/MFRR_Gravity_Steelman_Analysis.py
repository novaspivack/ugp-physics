"""
MFRR_Gravity_Steelman_Analysis.py

Analyze the force-law exponent and time-dilation statistics from
MFRR_Gravity_Steelman runs in STEELMAN_V3/results.
"""

import glob
import json
import os
from typing import List, Tuple

import numpy as np


def fit_power_law(force_samples: List[Tuple[float, float]]) -> float:
    """
    Given a list of (r, f) pairs, fit f ~ c * r^{-p} via linear regression
    on log-log data, and return the exponent p.
    """
    rs = np.array([r for r, _ in force_samples], dtype=float)
    fs = np.array([f for _, f in force_samples], dtype=float)

    # Filter out tiny or saturated values
    mask = (rs > 0.2) & (fs > 1e-6) & (fs < 0.9)
    rs = rs[mask]
    fs = fs[mask]
    if rs.size < 10:
        return np.nan

    log_r = np.log(rs)
    log_f = np.log(fs)
    A = np.vstack([np.ones_like(log_r), -log_r]).T  # log f = a - p log r
    sol, _, _, _ = np.linalg.lstsq(A, log_f, rcond=None)
    a_hat, p_hat = sol
    return float(p_hat)


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    pattern = os.path.join(results_dir, "MFRR_Gravity_Steelman_*.json")
    files = sorted(glob.glob(pattern))

    exponents: List[float] = []
    spreads_initial: List[float] = []
    spreads_final: List[float] = []
    time_corr_means: List[float] = []

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        force_samples = data.get("force_law", [])
        p_hat = fit_power_law(force_samples)
        exponents.append(p_hat)

        clustering = data.get("clustering", [])
        if clustering:
            spreads_initial.append(clustering[0])
            spreads_final.append(clustering[-1])

        time_dilation = data.get("time_dilation", [])
        if time_dilation:
            time_corr_means.append(float(np.mean(time_dilation)))

    print("Analyzed files:", len(files))
    exponents_arr = np.array(exponents, dtype=float)
    print("Force-law exponent p (f ~ 1/r^p):")
    print("  mean p:", np.nanmean(exponents_arr))
    print("  std p: ", np.nanstd(exponents_arr))

    print("\nClustering (spread):")
    print("  mean initial:", np.mean(spreads_initial))
    print("  mean final:  ", np.mean(spreads_final))

    print("\nTime-density correlation (per run mean):")
    print("  mean corr:", np.mean(time_corr_means))
    print("  std corr: ", np.std(time_corr_means))


if __name__ == "__main__":
    main()


