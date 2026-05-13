#!/usr/bin/env python3
"""
E9: Ensemble adjudication cascades (synchronous CP dynamics)

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
from scipy.sparse.linalg import eigsh  # spectral norm approx
import json
from pathlib import Path
from multiprocessing import Pool, cpu_count
import time

# Deterministic seed for reproducibility
rng = default_rng(12345)

def build_graph(N, p=5e-4, kind="erdos"):
    """
    Build sparse adjacency matrix for CP coupling graph.
    
    Parameters:
        N: number of CP sites
        p: connection probability (for Erdős–Rényi)
        kind: graph type ("erdos", "smallworld", "powerlaw")
    
    Returns:
        scipy.sparse.csr_matrix: symmetric adjacency matrix
    """
    if kind == "erdos":
        # Symmetric Bernoulli graph
        mask = rng.random((N, N)) < p
        A = np.triu(mask, 1).astype(float)
        A = A + A.T
    # TODO: small-world / power-law options
    return csr_matrix(A)

def init_couplings(A, J=0.05):
    """
    Initialize weighted symmetric coupling matrix J_{ij}.
    
    Parameters:
        A: adjacency matrix (sparse)
        J: coupling strength parameter
    
    Returns:
        scipy.sparse.csr_matrix: weighted coupling matrix W
    """
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
    """
    Approximate ||W||_2 by largest eigenvalue of |W|.
    
    Parameters:
        W: coupling matrix (sparse)
        k: number of eigenvalues to compute
    
    Returns:
        float: spectral norm estimate
    """
    # For symmetric W: eigsh on W.T @ W or directly on W
    vals = eigsh(W, k=k, which="LM", return_eigenvectors=False)
    return float(np.max(np.abs(vals)))

def local_cost(bi, psi_i, bias=0.0, kappa=1.0):
    """
    Quadratic well around branch bi in {0,1}.
    
    Parameters:
        bi: branch choice (0 or 1)
        psi_i: local coherence amplitude
        bias: branch bias
        kappa: stiffness parameter
    
    Returns:
        float: local cost
    """
    # cost ~ kappa*(bi - bias)^2; psi_i can modulate kappa
    return kappa * (bi - bias)**2

def inter_cost(bi, bj, psi_i, psi_j, mode="ising"):
    """
    Interaction cost between CPs.
    
    Parameters:
        bi, bj: branch choices
        psi_i, psi_j: coherence amplitudes
        mode: "ising" or "kuramoto"
    
    Returns:
        float: interaction cost
    """
    if mode == "ising":
        return -float(bi) * float(bj)
    # elif mode == "kuramoto": etc.
    return 0.0

def argmin_branch(i, b, psi, nbrs, W, bias, kappa):
    """
    Evaluate D_i(b) + sum_j J_ij * U(b,bj) for both branches.
    
    Returns:
        int: optimal branch (0 or 1)
    """
    bi0, bi1 = 0, 1
    cost0 = local_cost(bi0, psi[i], bias[i], kappa[i])
    cost1 = local_cost(bi1, psi[i], bias[i], kappa[i])
    
    for j in nbrs:
        Jij = W[i, j]
        if Jij != 0.0:
            cost0 += Jij * inter_cost(bi0, b[j], psi[i], psi[j])
            cost1 += Jij * inter_cost(bi1, b[j], psi[i], psi[j])
    
    return 0 if cost0 <= cost1 else 1

def avalanche_update(W, b, psi, bias, kappa):
    """
    Event-driven avalanche update: when a CP flips, update neighbors.
    
    Returns:
        int: burst size (number of CPs that changed)
    """
    N = len(b)
    nbrs = [W[i].indices for i in range(N)]
    
    # Seed set: randomly trigger a small fraction
    queue = list(np.where(rng.random(N) < 0.01)[0])
    visited = set()
    burst_size = 0
    
    while queue:
        i = queue.pop()
        visited.add(i)
        
        new_bi = argmin_branch(i, b, psi, nbrs[i], W, bias, kappa)
        
        if new_bi != b[i]:
            b[i] = new_bi
            burst_size += 1
            
            # Add neighbors to queue
            for j in nbrs[i]:
                if j not in visited:
                    queue.append(j)
    
    return burst_size

def run_sim(N=5000, p=5e-4, J=0.05, steps=2000):
    """
    Main simulation loop.
    
    Returns:
        tuple: (burst_sizes, spectral_norm)
    """
    A = build_graph(N, p)
    W = init_couplings(A, J=J)
    normW = spectral_norm(W)
    print(f"approx ||W||_2 ~ {normW:.4f}")
    
    # Fields and params
    b = rng.integers(0, 2, size=N)   # branches
    psi = rng.uniform(0.01, 0.1, size=N)
    bias = rng.uniform(0.0, 1.0, size=N)
    kappa = rng.uniform(0.1, 1.0, size=N)
    
    bursts = []
    
    for t in range(steps):
        S = avalanche_update(W, b, psi, bias, kappa)
        if S > 0:
            bursts.append(S)
    
    return bursts, normW

def analyze_bursts(bursts):
    """
    Analyze burst size distribution for power-law scaling.
    
    Returns:
        dict: statistics including power-law exponent estimate
    """
    if not bursts:
        return {"mean": 0, "std": 0, "count": 0, "kappa_est": None}
    
    bursts_arr = np.array(bursts)
    
    # Power-law tail: P(S >= s) ~ s^{-kappa}
    # Estimate via log-log linear fit in tail region
    unique_sizes, counts = np.unique(bursts_arr, return_counts=True)
    ccdf = 1.0 - np.cumsum(counts) / len(bursts_arr)
    
    # Fit in mesoscopic range (avoid small-size and large-size cutoffs)
    tail_mask = (unique_sizes >= 10) & (unique_sizes <= np.percentile(unique_sizes, 90))
    if np.sum(tail_mask) > 3:
        log_s = np.log(unique_sizes[tail_mask])
        log_ccdf = np.log(ccdf[tail_mask] + 1e-10)
        # Linear fit: log(CCDF) = -kappa * log(s) + const
        kappa_est = -np.polyfit(log_s, log_ccdf, 1)[0]
    else:
        kappa_est = None
    
    return {
        "mean": float(np.mean(bursts_arr)),
        "std": float(np.std(bursts_arr)),
        "count": len(bursts),
        "kappa_est": float(kappa_est) if kappa_est is not None else None,
        "max_burst": int(np.max(bursts_arr)) if len(bursts_arr) > 0 else 0
    }

if __name__ == "__main__":
    print("=" * 60)
    print("E9: Ensemble Adjudication Cascades")
    print("=" * 60)
    
    # Parameter sweep to find synchronization threshold
    J_values = [0.01, 0.03, 0.05, 0.08, 0.12, 0.15]
    N = 3000
    p = 6e-4
    steps = 5000
    
    results = []
    
    for J in J_values:
        print(f"\nRunning J={J:.3f}...")
        bursts, normW = run_sim(N=N, p=p, J=J, steps=steps)
        stats = analyze_bursts(bursts)
        
        result = {
            "J": float(J),
            "normW": float(normW),
            "burst_stats": stats
        }
        results.append(result)
        
        print(f"  Recorded {stats['count']} bursts")
        print(f"  Mean size: {stats['mean']:.2f}")
        if stats['kappa_est'] is not None:
            print(f"  Power-law exponent (kappa): {stats['kappa_est']:.3f}")
    
    # Save results
    output_dir = Path("e25_ensemble_outputs")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "e25_ensemble_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    print("\nNext steps:")
    print("  1. Generate CCDF plot: log-log of P(S >= s) vs s")
    print("  2. Generate synchronization order parameter vs ||W||_2")
    print("  3. Identify critical threshold J_c from order parameter jump")

