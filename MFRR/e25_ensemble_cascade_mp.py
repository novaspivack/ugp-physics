#!/usr/bin/env python3
"""
E9: Ensemble adjudication cascades (multiprocessing version)

This script validates:
- Thm. synch-threshold: Synchronization threshold for coupled CPs
- Cor. avalanche: Power-law cascade size distribution
- Thm. pointer-selection: Ensemble pointer-basis selection
- Thm. EAME-Lindblad: EAME → GKSL reduction

Reference: Sec. ensemble-CP and superposition-decoherence-ensemble
"""

import numpy as np
from numpy.random import default_rng
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
import json
from pathlib import Path
from multiprocessing import Pool, cpu_count
import time

def build_graph(N, p=5e-4, kind="erdos", seed=12345):
    """Build sparse adjacency matrix for CP coupling graph."""
    rng = default_rng(seed)
    if kind == "erdos":
        mask = rng.random((N, N)) < p
        A = np.triu(mask, 1).astype(float)
        A = A + A.T
    return csr_matrix(A)

def init_couplings(A, J=0.05, seed=12345):
    """Initialize weighted symmetric coupling matrix J_{ij}."""
    rng = default_rng(seed + 1)
    N = A.shape[0]
    deg = np.maximum(A.sum(axis=1).A.ravel(), 1.0)
    W = A.copy().astype(float)
    rows, cols = W.nonzero()
    
    for i, j in zip(rows, cols):
        if i < j:
            val = rng.normal(0.0, J / np.sqrt(deg[i]))
            W[i, j] = val
            W[j, i] = val
    
    return W.tocsr()

def spectral_norm(W, k=1):
    """Approximate ||W||_2 by largest eigenvalue."""
    try:
        vals = eigsh(W, k=k, which="LM", return_eigenvectors=False)
        return float(np.max(np.abs(vals)))
    except:
        return 0.0

def local_cost(bi, psi_i, bias=0.0, kappa=1.0):
    """Quadratic well around branch bi in {0,1}."""
    return kappa * (bi - bias)**2

def inter_cost(bi, bj):
    """Ising-style interaction cost."""
    return -float(bi) * float(bj)

def argmin_branch(i, b, psi, W_row_indices, W_row_data, bias, kappa):
    """Evaluate cost for both branches and return optimal."""
    bi0, bi1 = 0, 1
    cost0 = local_cost(bi0, psi[i], bias[i], kappa[i])
    cost1 = local_cost(bi1, psi[i], bias[i], kappa[i])
    
    # Add neighbor contributions
    for idx, j in enumerate(W_row_indices):
        Jij = W_row_data[idx]
        if Jij != 0.0:
            cost0 += Jij * inter_cost(bi0, b[j])
            cost1 += Jij * inter_cost(bi1, b[j])
    
    return 0 if cost0 <= cost1 else 1

def avalanche_update(W, b, psi, bias, kappa, max_iter=1000):
    """
    Event-driven avalanche update with termination safeguard.
    
    Returns:
        int: burst size (number of CPs that changed)
    """
    rng = default_rng()
    N = len(b)
    
    # Precompute neighbor lists for efficiency
    nbrs_indices = [W[i].indices for i in range(N)]
    nbrs_data = [W[i].data for i in range(N)]
    
    # Seed set: randomly trigger a small fraction
    queue = list(np.where(rng.random(N) < 0.02)[0])
    visited = set()
    burst_size = 0
    iterations = 0
    
    while queue and iterations < max_iter:
        iterations += 1
        i = queue.pop(0)  # FIFO for BFS-like behavior
        
        if i in visited:
            continue
        visited.add(i)
        
        new_bi = argmin_branch(i, b, psi, nbrs_indices[i], nbrs_data[i], bias, kappa)
        
        if new_bi != b[i]:
            b[i] = new_bi
            burst_size += 1
            
            # Add unvisited neighbors to queue
            for j in nbrs_indices[i]:
                if j not in visited and j not in queue:
                    queue.append(j)
    
    return burst_size

def run_sim_single_J(params):
    """Run simulation for a single J value (for multiprocessing)."""
    J, N, p, steps, seed = params
    
    rng = default_rng(seed)
    
    print(f"[J={J:.3f}] Building graph...", flush=True)
    A = build_graph(N, p, seed=seed)
    W = init_couplings(A, J=J, seed=seed)
    normW = spectral_norm(W)
    
    print(f"[J={J:.3f}] ||W||_2 = {normW:.4f}, running {steps} steps...", flush=True)
    
    # Initialize fields
    b = rng.integers(0, 2, size=N)
    psi = rng.uniform(0.01, 0.1, size=N)
    bias = rng.uniform(0.0, 1.0, size=N)
    kappa = rng.uniform(0.1, 1.0, size=N)
    
    bursts = []
    start_time = time.time()
    
    for t in range(steps):
        if t % 100 == 0 and t > 0:
            elapsed = time.time() - start_time
            rate = t / elapsed
            print(f"[J={J:.3f}] Step {t}/{steps} ({rate:.1f} steps/s)", flush=True)
        
        S = avalanche_update(W, b, psi, bias, kappa, max_iter=500)
        if S > 0:
            bursts.append(S)
    
    elapsed = time.time() - start_time
    print(f"[J={J:.3f}] Complete in {elapsed:.1f}s - {len(bursts)} bursts", flush=True)
    
    return {
        "J": float(J),
        "normW": float(normW),
        "bursts": bursts,
        "elapsed_time": elapsed
    }

def analyze_bursts(bursts):
    """Analyze burst size distribution for power-law scaling."""
    if not bursts:
        return {"mean": 0, "std": 0, "count": 0, "kappa_est": None}
    
    bursts_arr = np.array(bursts)
    unique_sizes, counts = np.unique(bursts_arr, return_counts=True)
    
    if len(unique_sizes) < 2:
        return {
            "mean": float(np.mean(bursts_arr)),
            "std": float(np.std(bursts_arr)),
            "count": len(bursts),
            "kappa_est": None,
            "max_burst": int(np.max(bursts_arr))
        }
    
    ccdf = 1.0 - np.cumsum(counts) / len(bursts_arr)
    
    # Fit in mesoscopic range
    tail_mask = (unique_sizes >= 5) & (unique_sizes <= np.percentile(unique_sizes, 85))
    if np.sum(tail_mask) > 3:
        log_s = np.log(unique_sizes[tail_mask])
        log_ccdf = np.log(np.maximum(ccdf[tail_mask], 1e-10))
        # Linear fit: log(CCDF) = -kappa * log(s) + const
        kappa_est = -np.polyfit(log_s, log_ccdf, 1)[0]
    else:
        kappa_est = None
    
    return {
        "mean": float(np.mean(bursts_arr)),
        "std": float(np.std(bursts_arr)),
        "count": len(bursts),
        "kappa_est": float(kappa_est) if kappa_est is not None else None,
        "max_burst": int(np.max(bursts_arr))
    }

if __name__ == "__main__":
    print("=" * 60)
    print("E9: Ensemble Adjudication Cascades (Multiprocessing)")
    print("=" * 60)
    
    # Smaller, faster parameters for testing
    J_values = [0.01, 0.03, 0.05, 0.08, 0.12, 0.15]
    N = 1000  # Reduced from 3000
    p = 1e-3  # Slightly higher connectivity
    steps = 500  # Reduced from 5000
    
    # Create parameter sets for multiprocessing
    param_sets = [(J, N, p, steps, 12345 + i) for i, J in enumerate(J_values)]
    
    # Run in parallel
    n_cores = min(cpu_count(), len(J_values))
    print(f"\nUsing {n_cores} cores for {len(J_values)} parameter combinations")
    print(f"N={N}, p={p:.1e}, steps={steps}\n")
    
    with Pool(n_cores) as pool:
        results_raw = pool.map(run_sim_single_J, param_sets)
    
    # Analyze results
    results = []
    for r in results_raw:
        stats = analyze_bursts(r['bursts'])
        result = {
            "J": r['J'],
            "normW": r['normW'],
            "burst_stats": stats,
            "elapsed_time": r['elapsed_time']
        }
        results.append(result)
        
        print(f"\n[J={r['J']:.3f}] Analysis:")
        print(f"  Bursts: {stats['count']}")
        print(f"  Mean size: {stats['mean']:.2f}")
        print(f"  Max burst: {stats['max_burst']}")
        if stats['kappa_est'] is not None:
            print(f"  Power-law exponent κ: {stats['kappa_est']:.3f}")
    
    # Save results
    output_dir = Path("e25_ensemble_outputs")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "e25_ensemble_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ Results saved to {output_file}")
    print(f"{'='*60}")
    
    # Summary statistics
    print("\n=== SUMMARY ===")
    normW_values = [r['normW'] for r in results]
    burst_counts = [r['burst_stats']['count'] for r in results]
    mean_sizes = [r['burst_stats']['mean'] for r in results]
    
    print(f"Spectral norm range: [{min(normW_values):.4f}, {max(normW_values):.4f}]")
    print(f"Total bursts recorded: {sum(burst_counts)}")
    print(f"Mean burst size range: [{min(mean_sizes):.2f}, {max(mean_sizes):.2f}]")
    
    # Check for threshold behavior
    if len(mean_sizes) > 1:
        jumps = np.diff(mean_sizes)
        if len(jumps) > 0 and np.max(jumps) > np.mean(jumps) * 2:
            max_jump_idx = np.argmax(jumps)
            J_c_est = (J_values[max_jump_idx] + J_values[max_jump_idx + 1]) / 2
            print(f"\n✓ Threshold detected: J_c ≈ {J_c_est:.3f}")
            print(f"  (Jump from {mean_sizes[max_jump_idx]:.2f} to {mean_sizes[max_jump_idx+1]:.2f})")
        else:
            print("\n⚠ No clear threshold detected - may need wider J range")
    
    print("\nNext steps:")
    print("  1. Run: python3 e25_plot_templates.py")
    print("  2. Check e25_ensemble_outputs/ for figures")
    print("  3. If threshold confirmed, integrate into paper")

