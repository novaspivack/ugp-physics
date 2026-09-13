#!/usr/bin/env python3
"""
L1 Curvature Functional Variants

Tests alternative curvature functionals to see if the slope converges to Λ:
- Ollivier-Ricci signed (no absolute value)
- Forman-Ricci absolute
- Forman-Ricci signed
"""

import os
import numpy as np
import pandas as pd
import yaml
from multiprocessing import Pool
from .util import ensure_dirs, save_json, set_seed, phi, Lambda
from .fisher_graphs import (build_lattice4d, build_lattice4d_smallworld, build_mutual_knn4d,
                             omega_intensive_ricci, omega_intensive_forman, omega_rel)
from .heattrace import normalized_laplacian
from .spectral_dos import spectral_dimension_from_dos

def load_cfg():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, "cfg", "config.yaml")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

def get_mean_degree(G):
    if G.number_of_nodes() == 0:
        return 0.0
    return 2.0 * G.number_of_edges() / G.number_of_nodes()

def process_task(args):
    gname, gparams, seed, cfg, curvature_method = args
    set_seed(seed)
    rng = np.random.default_rng(seed)
    
    if gname == "lattice4d":
        n = gparams
        G = build_lattice4d(n)
        label = f"lattice4d_n{n}"
    elif gname == "lattice4d_sw":
        n = gparams
        G = build_lattice4d_smallworld(n, cfg["lemma1"]["smallworld_p"], rng)
        label = f"lattice4d_sw_n{n}"
    elif gname == "mutual_knn4d":
        N, k = gparams
        G = build_mutual_knn4d(seed, N, k)
        label = f"knn4d_N{N}_k{k}"
    else:
        raise ValueError(f"Unknown graph type: {gname}")
    
    if curvature_method == "orc_signed":
        Omega_int = omega_intensive_ricci(G, sample_edges=500, signed=True)
        ref_omega = 0.0
    elif curvature_method == "forman_abs":
        Omega_int = omega_intensive_forman(G, sample_edges=500, signed=False)
        ref_omega = 4.0
    elif curvature_method == "forman_signed":
        Omega_int = omega_intensive_forman(G, sample_edges=500, signed=True)
        ref_omega = 0.0
    else:
        Omega_int = omega_intensive_ricci(G, sample_edges=500, signed=False)
        ref_omega = 0.875
    
    Omega_rel = omega_rel(Omega_int, ref_omega)
    
    L = normalized_laplacian(G)
    d_eff = spectral_dimension_from_dos(L, n_eigs=min(200, G.number_of_nodes() - 2))
    mean_deg = get_mean_degree(G)
    
    return {
        "seed": seed,
        "graph": label,
        "N": G.number_of_nodes(),
        "mean_degree": float(mean_deg),
        "Omega_int": float(Omega_int),
        "Omega_rel": float(Omega_rel),
        "d_eff": float(d_eff),
        "curvature_method": curvature_method
    }

def test_curvature_method(cfg, curvature_method):
    tasks = []
    
    for s in cfg["seeds"]:
        for gname in ["lattice4d", "lattice4d_sw", "mutual_knn4d"]:
            if gname == "lattice4d":
                for n in cfg["lemma1"]["lattice4d_n_list"]:
                    tasks.append((gname, n, s, cfg, curvature_method))
            elif gname == "lattice4d_sw":
                for n in cfg["lemma1"]["lattice4d_n_list"]:
                    tasks.append((gname, n, s, cfg, curvature_method))
            elif gname == "mutual_knn4d":
                for N in cfg["lemma1"]["knn4d_N_list"]:
                    for k in cfg["lemma1"]["knn4d_k_list"]:
                        tasks.append((gname, (N, k), s, cfg, curvature_method))
    
    with Pool(processes=8) as pool:
        rows = pool.map(process_task, tasks)
    
    df = pd.DataFrame(rows)
    
    log_phi_omega = np.log(df["Omega_rel"].values) / np.log(phi())
    y = df["d_eff"].values
    
    X = np.c_[np.ones(len(df)), log_phi_omega]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    yhat = X @ beta
    r2 = 1.0 - np.sum((y - yhat)**2) / np.sum((y - y.mean())**2)
    
    return {
        'intercept': float(beta[0]),
        'slope': float(beta[1]),
        'R2': float(r2),
        'slope_over_Lambda': float(beta[1] / Lambda()),
        'df': df
    }

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    os.makedirs("results/calibration", exist_ok=True)
    
    cfg = load_cfg()
    
    methods = {
        'orc_abs': 'Ollivier-Ricci |mean|',
        'orc_signed': 'Ollivier-Ricci signed mean',
        'forman_abs': 'Forman-Ricci |mean|',
        'forman_signed': 'Forman-Ricci signed mean'
    }
    
    print("="*70)
    print("L1 CURVATURE FUNCTIONAL VARIANTS")
    print("="*70)
    
    results_all = {}
    
    for method_key, method_name in methods.items():
        print(f"\nTesting {method_name}...")
        result = test_curvature_method(cfg, method_key)
        results_all[method_key] = result
        
        print(f"  Intercept: {result['intercept']:.4f}")
        print(f"  Slope: {result['slope']:.4f} (Λ = {Lambda():.4f})")
        print(f"  Slope/Λ: {result['slope_over_Lambda']:.2f}×")
        print(f"  R²: {result['R2']:.4f}")
        
        if abs(result['slope_over_Lambda'] - 1.0) <= 0.15:
            print(f"  ✅ PASS - Recovered Λ within 15%!")
        else:
            print(f"  ✗ FAIL - Still {abs(result['slope_over_Lambda'] - 1.0)*100:.1f}% off")
    
    save_json({k: {kk: vv for kk, vv in v.items() if kk != 'df'} 
               for k, v in results_all.items()}, 
              "results/calibration/curvature_variants.json")
    
    print(f"\n✓ Results saved to results/calibration/curvature_variants.json")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

