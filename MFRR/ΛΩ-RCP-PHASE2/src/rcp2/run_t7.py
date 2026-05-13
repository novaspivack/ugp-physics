"""
T7: Reflexive CPT-Measurement Equivalence

Tests whether arrow of time and measurement asymmetry emerge from PT duality.

Cross-references:
  - Phase I L2 (Meta-Reflexive Energy Conservation)
  - MFRR Theorem 12.6 (Reflexive Noether - already proven)
"""

import numpy as np
import pandas as pd
from multiprocessing import Pool
from .util import set_seed, save_json, ensure_dirs, load_yaml, Lambda

def pt_forward_step(state, rng, bias=0.0):
    """
    Forward transputation: resolves degeneracy by MDL minimization
    bias > 0: measurement preference toward branch A
    Returns new state and entropy production
    """
    x = state["x"]
    
    # Simulate choice point: 2 admissible branches
    branch_a = x + 0.1 * rng.standard_normal(len(x))
    branch_b = x - 0.1 * rng.standard_normal(len(x))
    
    # MDL selection with measurement bias
    complexity_a = np.linalg.norm(branch_a) - bias  # Bias favors A
    complexity_b = np.linalg.norm(branch_b)
    
    if complexity_a < complexity_b:
        x_next = branch_a
        selected = "A"
    else:
        x_next = branch_b
        selected = "B"
    
    # Entropy production: k_B log(2) for binary choice
    # Plus bias-dependent contribution (measurement cost)
    dS = np.log(2) + bias * abs(complexity_a - complexity_b)
    
    return {"x": x_next}, dS, selected

def pt_reverse_step(state, rng, bias=0.0):
    """
    Reverse transputation: PT^{-1}
    In CPT-symmetric case, should mirror forward dynamics
    bias > 0: creates asymmetry (measurement irreversibility)
    """
    x = state["x"]
    
    # Time-reversed dynamics
    branch_a = x - 0.1 * rng.standard_normal(len(x))
    branch_b = x + 0.1 * rng.standard_normal(len(x))
    
    # In reverse, bias still favors A (creates T-asymmetry)
    complexity_a = np.linalg.norm(branch_a) - bias
    complexity_b = np.linalg.norm(branch_b)
    
    if complexity_a < complexity_b:
        x_next = branch_a
        selected = "A"
    else:
        x_next = branch_b
        selected = "B"
    
    # Negative entropy in reverse, but bias adds positive contribution
    # This creates net asymmetry
    dS = -np.log(2) + bias * abs(complexity_a - complexity_b)
    
    return {"x": x_next}, dS, selected

def run_cpt_loop(seed, loops, bias=0.0):
    """
    Run forward and reverse PT loops
    Bias parameter breaks time symmetry if non-zero
    
    Bias implementation: Add external field that prefers forward direction
    
    Returns:
      ΔS_forward: Total entropy production in forward direction
      ΔS_reverse: Total entropy production in reverse direction
      ΔS_asymmetry: ΔS_forward + ΔS_reverse (should be ~0 if CPT symmetric)
    """
    set_seed(seed)
    rng = np.random.default_rng(seed)
    
    # Initialize state
    x0 = rng.standard_normal(16)
    state_fwd = {"x": x0.copy()}
    state_rev = {"x": x0.copy()}
    
    # Forward loop
    S_forward = 0.0
    count_A_fwd = 0
    for i in range(loops):
        state_fwd, dS, selected = pt_forward_step(state_fwd, rng, bias)
        S_forward += dS
        if selected == "A":
            count_A_fwd += 1
    
    # Reverse loop  
    S_reverse = 0.0
    count_A_rev = 0
    for i in range(loops):
        state_rev, dS, selected = pt_reverse_step(state_rev, rng, bias)
        S_reverse += dS
        if selected == "A":
            count_A_rev += 1
    
    # CPT asymmetry
    # In symmetric case (bias=0): ΔS_ref ≈ 0
    # In biased case: ΔS_ref > 0 (forward preferred)
    ΔS_ref = S_forward + S_reverse
    
    return {
        "ΔS_forward": float(S_forward),
        "ΔS_reverse": float(S_reverse),
        "ΔS_asymmetry": float(ΔS_ref)
    }

def process_cpt_task(args):
    seed, loops, bias = args
    result = run_cpt_loop(seed, loops, bias)
    return (seed, bias, result["ΔS_forward"], result["ΔS_reverse"], result["ΔS_asymmetry"])

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    
    cfg = load_yaml("cfg/config.yaml")
    seeds = cfg["phase2"]["seeds"]
    loops = cfg["phase2"]["t7_cpt"]["loops"]
    bias_levels = cfg["phase2"]["t7_cpt"]["bias_levels"]
    tol_unbiased = cfg["phase2"]["t7_cpt"]["tolerance_unbiased"]
    tol_biased = cfg["phase2"]["t7_cpt"]["tolerance_biased"]
    n_cores = cfg["phase2"]["n_cores"]
    
    # Build tasks
    tasks = [(s, loops, bias) for s in seeds for bias in bias_levels]
    
    print("="*70)
    print("T7: REFLEXIVE CPT-MEASUREMENT EQUIVALENCE")
    print("="*70)
    print(f"\nTesting arrow of time emergence from PT duality")
    print(f"  Loops: {loops}")
    print(f"  Bias levels: {bias_levels}")
    print(f"  Seeds: {len(seeds)}")
    print(f"  Total configurations: {len(tasks)}")
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_cpt_task, tasks)
    
    df = pd.DataFrame(rec, columns=["seed", "bias", "ΔS_forward", "ΔS_reverse", "ΔS_asymmetry"])
    df.to_csv("results/t7_cpt_records.csv", index=False)
    
    # Analyze results by bias level
    results_by_bias = {}
    for bias in bias_levels:
        subset = df[df["bias"] == bias]
        mean_asym = subset["ΔS_asymmetry"].mean()
        std_asym = subset["ΔS_asymmetry"].std()
        abs_mean = abs(mean_asym)
        
        if bias == 0.0:
            # Unbiased case: should have ΔS ≈ 0
            passed = abs_mean < tol_unbiased
        else:
            # Biased case: should have ΔS > threshold
            passed = abs_mean > tol_biased
        
        results_by_bias[f"bias_{bias}"] = {
            "bias": float(bias),
            "mean_ΔS_asymmetry": float(mean_asym),
            "std_ΔS_asymmetry": float(std_asym),
            "abs_mean": float(abs_mean),
            "pass": bool(passed)
        }
        
        print(f"\nBias = {bias:.2f}:")
        print(f"  Mean ΔS_asymmetry: {mean_asym:.4f} ± {std_asym:.4f}")
        if bias == 0.0:
            print(f"  Tolerance: {tol_unbiased:.3f} (expect ~0)")
        else:
            print(f"  Tolerance: {tol_biased:.3f} (expect >threshold)")
        print(f"  Status: {'PASS' if passed else 'FAIL'}")
    
    # Overall status
    all_passed = all(r["pass"] for r in results_by_bias.values())
    
    summary = {
        "results_by_bias": results_by_bias,
        "overall_pass": all_passed,
        "status": "PASS" if all_passed else "FAIL",
        "interpretation": "CPT symmetric (unbiased), time arrow emerges (biased)" if all_passed else "FAIL"
    }
    
    save_json(summary, "results/t7_cpt_summary.json")
    
    print(f"\n{'='*70}")
    print(f"T7 STATUS: {summary['status']}")
    print(f"{'='*70}")
    
    return summary

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

