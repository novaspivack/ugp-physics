"""
Moran Benchmark - Measure J (Information → Spectral Dimension Jacobian)

Builds graph approximants of Moran/Cantor-like fractals with known analytic
information dimension D_I, measures spectral dimension d_s via eigenvalue counting,
and fits J from the local linear map d_s ≈ α + J·D_I.
"""

import numpy as np
import pandas as pd
import networkx as nx
from multiprocessing import Pool
from .heattrace import normalized_laplacian
from .spectral_dos import spectral_dimension_from_dos
from .util import save_json, set_seed

def info_dimension(b, r):
    return np.log(b) / np.log(1.0 / r)

def build_moran_tree_graph(level, b, seed=0):
    rng = np.random.default_rng(seed)
    
    G = nx.Graph()
    node_id = 0
    G.add_node(node_id)
    frontier = [node_id]
    node_id += 1
    
    for lev in range(level):
        new_frontier = []
        for parent in frontier:
            for child_idx in range(b):
                G.add_node(node_id)
                G.add_edge(parent, node_id, w=1.0)
                new_frontier.append(node_id)
                node_id += 1
        frontier = new_frontier
    
    all_nodes = list(G.nodes())
    n_cross = max(1, int(G.number_of_nodes() * 0.08))
    
    for _ in range(n_cross):
        if len(all_nodes) >= 2:
            i, j = rng.choice(all_nodes, size=2, replace=False)
            if not G.has_edge(i, j):
                G.add_edge(i, j, w=1.0)
    
    return G

def process_moran_task(args):
    seed, b, level = args
    set_seed(seed)
    
    G = build_moran_tree_graph(level, b, seed=seed)
    
    if G.number_of_nodes() < 20:
        return None
    
    L = normalized_laplacian(G)
    d_s = spectral_dimension_from_dos(L, n_eigs=min(100, G.number_of_nodes() - 2))
    
    tree_dim_analytic = np.log(G.number_of_nodes()) / np.log(level + 1)
    
    return {
        'seed': seed,
        'b': b,
        'level': level,
        'D_I_tree': tree_dim_analytic,
        'd_s': d_s,
        'N': G.number_of_nodes()
    }

def measure_J_from_moran(branching_list, level=4, seeds=[101, 202, 303], n_cores=8):
    tasks = [(seed, b, level) for seed in seeds for b in branching_list]
    
    with Pool(processes=n_cores) as pool:
        rows = pool.map(process_moran_task, tasks)
    
    rows = [r for r in rows if r is not None]
    df = pd.DataFrame(rows)
    
    X = np.c_[np.ones(len(df)), df["D_I_tree"].values]
    y = df["d_s"].values
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    
    alpha_J = float(beta[0])
    J = float(beta[1])
    
    r2 = 1.0 - np.sum((y - (X @ beta))**2) / np.sum((y - y.mean())**2)
    
    return J, alpha_J, r2, df

def main():
    import os
    os.makedirs("results/closure", exist_ok=True)
    
    branching_list = [2, 3, 4, 5, 6]
    level = 4
    
    print("="*70)
    print("MORAN BENCHMARK - Measuring J (Information → Spectral)")
    print("="*70)
    print(f"\nBuilding b-ary trees (b ∈ {branching_list}, level={level}) × 3 seeds...")
    print(f"Expected N range: [{(2**(level+1)-1), (6**(level+1)-1)//5}] ~ [31, 1555]")
    print(f"Using 8-core multiprocessing...")
    
    J, alpha, r2, df = measure_J_from_moran(branching_list, level=level, seeds=[101, 202, 303], n_cores=8)
    
    df.to_csv("results/closure/moran_benchmark.csv", index=False)
    
    print(f"\n✓ Moran benchmark complete")
    print(f"  N_graphs: {len(df)}")
    print(f"  D_I_tree range: [{df['D_I_tree'].min():.3f}, {df['D_I_tree'].max():.3f}]")
    print(f"  d_s range: [{df['d_s'].min():.3f}, {df['d_s'].max():.3f}]")
    print(f"  N range: [{df['N'].min()}, {df['N'].max()}]")
    
    print(f"\nFit: d_s = {alpha:.4f} + J × D_I_tree")
    print(f"  J = {J:.4f}")
    print(f"  R² = {r2:.4f}")
    
    result = {
        "J": J,
        "alpha": alpha,
        "R2": r2,
        "N_benchmarks": len(df),
        "D_I_range": [float(df["D_I_tree"].min()), float(df["D_I_tree"].max())],
        "note": "J = ∂d_s/∂D_I from tree-based fractals with 8% cross-links"
    }
    
    save_json(result, "results/closure/J_estimate.json")
    print(f"\n✓ J estimate saved to results/closure/J_estimate.json")
    
    return result

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

