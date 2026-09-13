"""
L2 Robustness Testing - Extended Validation

Tests the Reflexive Landauer Hierarchy under:
1. Higher depths (n ∈ {10, 12})
2. Variable branching models (constant, linear, exponential)
3. Temperature variations (k_B T ∈ {0.5, 1.0, 2.0})
"""

import numpy as np
import pandas as pd
import yaml
from multiprocessing import Pool
from .util import ensure_dirs, save_json, set_seed

def load_cfg():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, "cfg", "config.yaml")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

def init_state():
    return np.array([0.0])

def pt_update(state, psi_params, rng):
    a, b = psi_params
    x = state[0]
    dx = a * np.tanh(b * x)
    new_x = x + dx + 0.01 * rng.standard_normal()
    return np.array([new_x])

def coherence_norm2(psi_params):
    a, b = psi_params
    return float(a*a + b*b)

def get_n_branches(i, model):
    if model == "constant":
        return 4
    elif model == "linear":
        return max(2, int(2 + i * 0.5))
    elif model == "exponential":
        return max(2, int(2 * (1.2 ** i)))
    else:
        return 4

def process_robust_task(args):
    s, n, steps_per_layer, kbT, branch_model = args
    set_seed(s)
    rng = np.random.default_rng(s+7)
    state = init_state()
    E_landauer = 0.0
    E_coherence = 0.0
    coh = 0.0
    
    for i in range(n):
        n_branches = get_n_branches(i, branch_model)
        E_landauer += kbT * np.log(n_branches)
        
        a = 0.05 + 0.02 * i
        b = 0.8 + 0.1 * i
        psi = (a, b)
        
        psi_norm2 = coherence_norm2(psi)
        E_coherence += 0.5 * psi_norm2
        
        for _ in range(steps_per_layer):
            state = pt_update(state, psi, rng)
        
        coh += psi_norm2
    
    E_total = E_landauer + E_coherence
    return (s, n, kbT, branch_model, E_total, coh, E_landauer, E_coherence)

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    cfg = load_cfg()
    n_cores = cfg.get("n_cores", 8)
    
    # Extended test matrix
    depths_extended = [2, 3, 4, 6, 8, 10, 12]
    kbT_values = [0.5, 1.0, 2.0]
    branch_models = ["constant", "linear", "exponential"]
    seeds = cfg["seeds"]
    steps_per_layer = cfg["lemma2"]["steps_per_layer"]
    
    # Build task list
    tasks = []
    for s in seeds:
        for kbT in kbT_values:
            for branch_model in branch_models:
                for n in depths_extended:
                    tasks.append((s, n, steps_per_layer, kbT, branch_model))
    
    print(f"Running L2 robustness sweep...")
    print(f"  Depths: {depths_extended}")
    print(f"  k_B T: {kbT_values}")
    print(f"  Branch models: {branch_models}")
    print(f"  Total configurations: {len(tasks)}")
    print(f"  Using {n_cores} cores...")
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_robust_task, tasks)
    
    df = pd.DataFrame(rec, columns=["seed", "depth", "kbT", "branch_model", 
                                     "E_total", "coh_sum", "E_landauer", "E_coherence"])
    df.to_csv("results/l2_robust_records.csv", index=False)
    
    print(f"\n✓ Robustness data collected ({len(df)} configurations)")
    
    # Analyze each condition separately
    results = {}
    
    for kbT in kbT_values:
        for branch_model in branch_models:
            subset = df[(df["kbT"] == kbT) & (df["branch_model"] == branch_model)]
            
            if len(subset) < 5:
                continue
            
            # Estimate alpha
            y = subset["E_total"].values
            x_coh = subset["coh_sum"].values
            x_log_n = np.log(subset["depth"].values)
            X_alpha = np.c_[np.ones(len(subset)), x_coh, x_log_n]
            w_alpha = np.linalg.lstsq(X_alpha, y, rcond=None)[0]
            alpha = float(w_alpha[1])
            
            # Regress out coherence
            X = np.c_[np.ones(len(subset)), x_log_n]
            y_resid = y - alpha * x_coh
            w = np.linalg.lstsq(X, y_resid, rcond=None)[0]
            
            intercept = float(w[0])
            slope = float(w[1])
            
            # R² calculation
            yhat = X @ w
            ss_tot = np.sum((y_resid - y_resid.mean())**2)
            ss_res = np.sum((y_resid - yhat)**2)
            r2 = 1.0 - ss_res / (ss_tot + 1e-12)
            
            rel_err = abs(slope - kbT) / kbT
            passed = rel_err <= 0.15  # 15% tolerance for robustness
            
            key = f"kbT_{kbT}_branch_{branch_model}"
            results[key] = {
                "kbT": kbT,
                "branch_model": branch_model,
                "n_configs": len(subset),
                "alpha": alpha,
                "intercept": intercept,
                "slope": slope,
                "R2": float(r2),
                "relative_error": float(rel_err),
                "pass": passed
            }
            
            print(f"\n{key}:")
            print(f"  Slope: {slope:.4f} (expected: {kbT:.4f})")
            print(f"  Error: {rel_err*100:.2f}%")
            print(f"  R²: {r2:.4f}")
            print(f"  Status: {'PASS' if passed else 'FAIL'}")
    
    # Overall statistics
    all_passed = all(r["pass"] for r in results.values())
    mean_error = np.mean([r["relative_error"] for r in results.values()])
    mean_r2 = np.mean([r["R2"] for r in results.values()])
    
    summary = {
        "configurations": results,
        "overall_pass": all_passed,
        "mean_relative_error": float(mean_error),
        "mean_R2": float(mean_r2),
        "n_conditions": len(results),
        "n_pass": sum(1 for r in results.values() if r["pass"]),
        "status": "PASS" if all_passed else "PARTIAL"
    }
    
    save_json(summary, "results/l2_robust_summary.json")
    
    print(f"\n{'='*70}")
    print(f"L2 ROBUSTNESS SUMMARY")
    print(f"{'='*70}")
    print(f"  Conditions tested: {len(results)}")
    print(f"  Passed: {summary['n_pass']}/{len(results)}")
    print(f"  Mean relative error: {mean_error*100:.2f}%")
    print(f"  Mean R²: {mean_r2:.4f}")
    print(f"  Status: {summary['status']}")
    print(f"{'='*70}")
    
    return summary

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

