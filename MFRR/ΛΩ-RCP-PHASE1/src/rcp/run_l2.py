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
    dE = abs(dx) + 0.5 * a * a
    return np.array([new_x]), float(dE)

def coherence_norm2(psi_params):
    a, b = psi_params
    return float(a*a + b*b)

def estimate_alpha_coh(df):
    y = df["E_total"].values
    x = df["coh_sum"].values
    z = np.log(df["depth"].values)
    X = np.c_[np.ones(len(df)), x, z]
    w = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(w[1])

def process_depth_task(args):
    s, n, steps_per_layer, kbT = args
    set_seed(s)
    rng = np.random.default_rng(s+7)
    state = init_state()
    E_landauer = 0.0
    E_coherence = 0.0
    coh = 0.0
    
    # Model: each layer i has depth-dependent number of admissible branches
    # n_branches grows with layer index to model meta-reflexive complexity
    for i in range(n):
        # Number of admissible branches at this layer (grows with depth)
        n_branches = max(2, int(2 + i * 0.5))
        
        # Landauer term: k_B T log(n_branches) per layer
        E_landauer += kbT * np.log(n_branches)
        
        # Coherence field parameters
        a = 0.05 + 0.02 * i
        b = 0.8 + 0.1 * i
        psi = (a, b)
        
        # Coherence term: λ_Ψ ∫ Ψ² (simplified as norm²)
        psi_norm2 = coherence_norm2(psi)
        E_coherence += 0.5 * psi_norm2  # λ_Ψ = 0.5
        
        # State update (simulates PT operation)
        for _ in range(steps_per_layer):
            state, _ = pt_update(state, psi, rng)
        
        coh += psi_norm2
    
    E_total = E_landauer + E_coherence
    return (s, n, E_total, coh, E_landauer, E_coherence)

def run_meta_energy(depths, steps_per_layer, kbT, seeds, n_cores=8):
    tasks = [(s, n, steps_per_layer, kbT) for s in seeds for n in depths]
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_depth_task, tasks)
    
    return pd.DataFrame(rec, columns=["seed", "depth", "E_total", "coh_sum", "E_landauer", "E_coherence"])

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    cfg = load_cfg()
    n_cores = cfg.get("n_cores", 8)
    df = run_meta_energy(cfg["lemma2"]["depths"], cfg["lemma2"]["steps_per_layer"], cfg["lemma2"]["kbT"], cfg["seeds"], n_cores)
    df.to_csv("results/l2_records.csv", index=False)
    
    # Regress out coherence term
    alpha = estimate_alpha_coh(df)
    X = np.c_[np.ones(len(df)), np.log(df["depth"].values)]
    y = df["E_total"].values - alpha * df["coh_sum"].values
    w = np.linalg.lstsq(X, y, rcond=None)[0]
    
    intercept = float(w[0])
    slope = float(w[1])
    
    # Also check Landauer term directly
    X_land = np.c_[np.ones(len(df)), np.log(df["depth"].values)]
    y_land = df["E_landauer"].values
    w_land = np.linalg.lstsq(X_land, y_land, rcond=None)[0]
    slope_landauer = float(w_land[1])
    
    kbT = cfg["lemma2"]["kbT"]
    tol = cfg["lemma2"]["tol_kbT_rel"]
    pass_slope = abs(slope - kbT) / kbT <= tol
    
    # Diagnostic output
    print(f"\nL2 Results:")
    print(f"  Total energy after regressing coherence:")
    print(f"    Slope vs log(depth): {slope:.4f} (expected: {kbT:.4f})")
    print(f"    Intercept: {intercept:.4f}")
    print(f"  Landauer term directly:")
    print(f"    Slope vs log(depth): {slope_landauer:.4f}")
    print(f"    Mean E_landauer: {df['E_landauer'].mean():.4f}")
    print(f"  Coherence coefficient α: {alpha:.4f}")
    print(f"  Status: {'PASS' if pass_slope else 'FAIL'}")
    
    save_json({
        "alpha_coh": alpha,
        "slope_vs_log_depth": slope,
        "slope_landauer_direct": slope_landauer,
        "intercept": intercept,
        "mean_E_landauer": float(df["E_landauer"].mean()),
        "kbT_expected": kbT,
        "pass": pass_slope,
        "status": "PASS" if pass_slope else "FAIL"
    }, "results/l2_summary.json")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

