import os
import math
import numpy as np
import pandas as pd
import yaml
from multiprocessing import Pool
from functools import partial
from .util import set_seed, ensure_dirs, save_json, Lambda, phi
from .fisher_graphs import build_srrg_graph, fisher_metric_proxy, scalar_curvature_proxy, omega_complexity
from .spectral_dim import spectral_dimension

def load_cfg():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, "cfg", "config.yaml")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

def process_graph_task(args):
    s, N, t_grid, synthetic_mode, synthetic_noise = args
    set_seed(s)
    
    if synthetic_mode:
        rng = np.random.default_rng(s)
        Omega_base = 240.0 + (N / 2000.0) * 790.0
        Omega = Omega_base * (1.0 + synthetic_noise * rng.standard_normal())
        Omega = max(200.0, Omega)
        
        log_phi_Omega = np.log(Omega) / np.log(phi())
        ds_true = 4.0 + Lambda() * log_phi_Omega
        ds = ds_true + synthetic_noise * Lambda() * rng.standard_normal()
        ds = max(1.0, min(10.0, ds))
    else:
        G = build_srrg_graph(s, N, None)
        I = fisher_metric_proxy(G)
        R = scalar_curvature_proxy(I)
        Omega = omega_complexity(R, I)
        ds = spectral_dimension(G, t_grid, s+13)
    
    return (s, N, Omega, ds)

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    cfg = load_cfg()
    seeds = cfg["seeds"]
    Ns = cfg["lemma1"]["N_list"]
    lg_min = cfg["lemma1"]["t_grid_log10_min"]
    lg_max = cfg["lemma1"]["t_grid_log10_max"]
    pts = cfg["lemma1"]["t_grid_points"]
    t_grid = np.logspace(lg_min, lg_max, pts)
    n_cores = cfg.get("n_cores", 8)
    synthetic_mode = cfg["lemma1"].get("synthetic_test", False)
    synthetic_noise = cfg["lemma1"].get("synthetic_noise", 0.02)
    
    tasks = [(s, N, t_grid, synthetic_mode, synthetic_noise) for s in seeds for N in Ns]
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_graph_task, tasks)
    
    df = pd.DataFrame(rec, columns=["seed", "N", "Omega", "ds"])
    X = np.c_[np.ones(len(df)), np.log(df["Omega"].values) / np.log(phi())]
    y = df["ds"].values
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    
    intercept = float(beta[0])
    slope = float(beta[1])
    
    target_d = cfg["lemma1"]["target_dim"]
    lambda_expected = cfg["lemma1"]["lambda_expected"]
    tol_d = cfg["lemma1"]["tol_intercept"]
    tol_l = cfg["lemma1"]["tol_lambda_rel"]
    
    pass_d = abs(intercept - target_d) <= tol_d
    pass_l = abs(slope - lambda_expected) / lambda_expected <= tol_l
    status = "PASS" if (pass_d and pass_l) else "FAIL"
    
    df.to_csv("results/l1_records.csv", index=False)
    save_json({
        "intercept": intercept,
        "slope": slope,
        "target_dim": target_d,
        "lambda_expected": lambda_expected,
        "pass_intercept": pass_d,
        "pass_lambda": pass_l,
        "status": status,
        "synthetic_mode": synthetic_mode,
        "synthetic_noise": synthetic_noise
    }, "results/l1_summary.json")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

