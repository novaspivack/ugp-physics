"""
Fisher-Ω Computation from Graph Models

Fits parametric models (degree-corrected or simple) to graphs,
computes Fisher information metric, and estimates intensive Fisher Ω.
Then regresses against graph Ω to measure ν (normalization factor).
"""

import numpy as np
import pandas as pd
from multiprocessing import Pool
from .fisher_graphs import build_lattice4d, build_lattice4d_smallworld, build_mutual_knn4d, omega_intensive_ricci
from .util import save_json, set_seed, phi

def estimate_fisher_omega_simple(G, sample_size=500):
    degrees = np.array([G.degree(n) for n in G.nodes()])
    
    mean_deg = np.mean(degrees)
    var_deg = np.var(degrees) + 1e-9
    
    p_est = mean_deg / (G.number_of_nodes() - 1.0 + 1e-9)
    p_est = np.clip(p_est, 1e-6, 1.0 - 1e-6)
    
    fisher_p = 1.0 / (p_est * (1.0 - p_est) + 1e-9)
    
    fisher_mean_k = 1.0 / (var_deg + 1e-9)
    
    Omega_F = np.sqrt(fisher_p * fisher_mean_k)
    
    return float(Omega_F)

def process_omega_task(args):
    gname, gparams, seed = args
    set_seed(seed)
    rng = np.random.default_rng(seed)
    
    if gname == "lattice4d":
        n = gparams
        G = build_lattice4d(n)
        label = f"lattice4d_n{n}"
    elif gname == "lattice4d_sw":
        n, p = gparams
        G = build_lattice4d_smallworld(n, p, rng)
        label = f"lattice4d_sw_n{n}"
    elif gname == "mutual_knn4d":
        N, k = gparams
        G = build_mutual_knn4d(seed, N, k)
        label = f"knn4d_N{N}_k{k}"
    else:
        return None
    
    Omega_F = estimate_fisher_omega_simple(G, sample_size=500)
    Omega_graph = omega_intensive_ricci(G, sample_edges=500, signed=False)
    
    return {
        'graph': label,
        'N': G.number_of_nodes(),
        'Omega_F': Omega_F,
        'Omega_graph': Omega_graph
    }

def measure_nu(n_cores=8):
    tasks = []
    
    for seed in [101, 202, 303]:
        for n in [7, 8, 9]:
            tasks.append(("lattice4d", n, seed))
            tasks.append(("lattice4d_sw", (n, 0.05), seed))
        
        for N in [4000, 8000]:
            for k in [10, 16, 24]:
                tasks.append(("mutual_knn4d", (N, k), seed))
    
    with Pool(processes=n_cores) as pool:
        rows = pool.map(process_omega_task, tasks)
    
    rows = [r for r in rows if r is not None]
    df = pd.DataFrame(rows)
    
    log_phi_omega_F = np.log(df["Omega_F"].values) / np.log(phi())
    log_phi_omega_graph = np.log(df["Omega_graph"].values) / np.log(phi())
    
    X = np.c_[np.ones(len(df)), log_phi_omega_graph]
    y = log_phi_omega_F
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    
    a0 = float(beta[0])
    nu = float(beta[1])
    
    yhat = X @ beta
    r2 = 1.0 - np.sum((y - yhat)**2) / np.sum((y - y.mean())**2)
    
    return nu, a0, r2, df

def main():
    import os
    os.makedirs("results/closure", exist_ok=True)
    
    print("="*70)
    print("FISHER-Ω MEASUREMENT - Measuring ν (Fisher → Graph)")
    print("="*70)
    print(f"\nComputing Fisher-Ω and graph-Ω on shared graph set...")
    print(f"Using 8-core multiprocessing...")
    
    nu, a0, r2, df = measure_nu(n_cores=8)
    
    df.to_csv("results/closure/omega_mapping.csv", index=False)
    
    print(f"\n✓ Ω mapping complete")
    print(f"  N_graphs: {len(df)}")
    print(f"  Omega_F range: [{df['Omega_F'].min():.3f}, {df['Omega_F'].max():.3f}]")
    print(f"  Omega_graph range: [{df['Omega_graph'].min():.3f}, {df['Omega_graph'].max():.3f}]")
    
    print(f"\nFit: log_φ(Ω_F) = {a0:.4f} + ν × log_φ(Ω_graph)")
    print(f"  ν = {nu:.4f}")
    print(f"  R² = {r2:.4f}")
    
    result = {
        "nu": nu,
        "a0": a0,
        "R2": r2,
        "N_graphs": len(df),
        "note": "ν maps graph-curvature Ω to Fisher-Ω"
    }
    
    save_json(result, "results/closure/nu_estimate.json")
    print(f"\n✓ ν estimate saved to results/closure/nu_estimate.json")
    
    return result

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

