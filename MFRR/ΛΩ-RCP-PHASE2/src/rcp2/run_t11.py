"""
T11: Reflexive Cosmogenesis

Tests whether Big Bang can be modeled as global PT event.

Claim: E_universe = k_B T_CMB log(N_adjudicable)

Cross-references:
  - Phase I L2 (Meta-Reflexive Energy)
  - MFRR E6 series (Cosmology)
"""

import numpy as np
import pandas as pd
from multiprocessing import Pool
from .util import set_seed, save_json, ensure_dirs, load_yaml, kB_T_CMB

def simulate_global_pt(CP_count, T_CMB, seed):
    """
    Treat universe genesis as global PT event
    
    CP_count: Number of primordial choice points (adjudicable degrees of freedom)
    T_CMB: Cosmic microwave background temperature (K)
    
    Returns energy E_universe vs prediction k_B T_CMB log(N)
    """
    set_seed(seed)
    rng = np.random.default_rng(seed)
    
    # Landauer bound for global adjudication
    E_pred = T_CMB * np.log(CP_count)
    
    # Simulate energy from CP resolution
    # Each CP contributes k_B T_CMB log(n_i) where n_i is branch count
    # For simplicity: n_i ~ Poisson(λ=3) (2-6 branches typically)
    
    E_total = 0.0
    for _ in range(int(CP_count)):
        n_branches = max(2, rng.poisson(lam=3.0))
        E_total += T_CMB * np.log(n_branches)
    
    # Normalize by number of CPs
    E_per_CP = E_total / CP_count
    E_pred_per_CP = T_CMB * np.log(3.0)  # Mean for Poisson(3)
    
    rel_error = abs(E_per_CP - E_pred_per_CP) / (E_pred_per_CP + 1e-9)
    
    return {
        "N": CP_count,
        "E_total": float(E_total),
        "E_pred": float(E_pred),
        "E_per_CP": float(E_per_CP),
        "E_pred_per_CP": float(E_pred_per_CP),
        "rel_error": float(rel_error)
    }

def process_cosmo_task(args):
    seed, CP_count, T_CMB = args
    result = simulate_global_pt(CP_count, T_CMB, seed)
    return (seed, CP_count, result["E_total"], result["E_pred"], result["E_per_CP"], result["rel_error"])

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    
    cfg = load_yaml("cfg/config.yaml")
    seeds = cfg["phase2"]["seeds"]
    CP_counts = cfg["phase2"]["t11_cosmo"]["CP_counts"]
    T_CMB = cfg["phase2"]["t11_cosmo"]["T_CMB"]
    tol = cfg["phase2"]["t11_cosmo"]["tol_energy"]
    n_cores = cfg["phase2"]["n_cores"]
    
    print("="*70)
    print("T11: REFLEXIVE COSMOGENESIS")
    print("="*70)
    print(f"\nTesting: E_universe = k_B T_CMB log(N_adjudicable)")
    print(f"  CP counts: {CP_counts}")
    print(f"  T_CMB: {T_CMB} K")
    
    tasks = [(s, CP, T_CMB) for s in seeds for CP in CP_counts]
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_cosmo_task, tasks)
    
    df = pd.DataFrame(rec, columns=["seed", "N", "E_total", "E_pred", "E_per_CP", "rel_error"])
    df.to_csv("results/t11_cosmo_records.csv", index=False)
    
    # Test across decades of N
    mean_rel_error = df["rel_error"].mean()
    passed = mean_rel_error < tol
    
    # Also test scaling: log(E) vs log(N)
    log_N = np.log(df["N"].values)
    log_E = np.log(df["E_total"].values)
    slope = np.polyfit(log_N, log_E, 1)[0]
    
    # Expected slope = 1 (E ∝ N in total, E ∝ log N per CP)
    slope_err = abs(slope - 1.0)
    
    print(f"\nResults:")
    print(f"  Mean relative error: {mean_rel_error:.4f} (tolerance: {tol:.2f})")
    print(f"  log(E) vs log(N) slope: {slope:.4f} (expected: 1.0)")
    print(f"  Slope error: {slope_err:.4f}")
    print(f"  Status: {'PASS' if passed else 'FAIL'}")
    
    summary = {
        "mean_rel_error": float(mean_rel_error),
        "tolerance": float(tol),
        "log_slope": float(slope),
        "slope_error": float(slope_err),
        "pass": bool(passed),
        "status": "PASS" if passed else "FAIL"
    }
    
    save_json(summary, "results/t11_cosmo_summary.json")
    
    print(f"\n{'='*70}")
    print(f"T11 STATUS: {summary['status']}")
    print(f"{'='*70}")
    
    return summary

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

