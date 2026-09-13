#!/usr/bin/env python3
"""
E9d/E29: Topology Universality Test
====================================

Tests ensemble adjudication across different network topologies to validate
that spectral norm ||W||₂ is the universal control parameter, independent
of topology details.

Topologies tested:
  - Erdős–Rényi (random)
  - Watts–Strogatz (small-world)
  - Barabási–Albert (scale-free)

Cross-reference: MFRR manuscript §15 (E9d validation)

Author: MFRR Computational Validation Suite
Date: November 4, 2025
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm as sparse_norm
from typing import List, Tuple
import multiprocessing as mp
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class E29Config:
    """E9d/E29 configuration parameters."""
    N: int = 500               # Number of Choice Points
    J_base: float = 0.08       # Base coupling strength
    n_topologies: int = 3      # ER, WS, BA
    n_realizations: int = 5    # Multiple graph realizations per topology
    
    # ER parameters
    p_er: float = 4e-3         # Edge probability
    
    # Watts-Strogatz parameters
    k_ws: int = 4              # Mean degree
    p_ws: float = 0.3          # Rewiring probability
    
    # Barabási-Albert parameters
    m_ba: int = 2              # Edges to attach per new node
    
    steps_eq: int = 150        # Equilibration steps
    steps_meas: int = 200      # Measurement steps
    dt: float = 0.5            # Time step
    
    seed: int = 777
    n_cores: int = 6
    
# ============================================================================
# GRAPH GENERATORS
# ============================================================================

def build_erdos_renyi(N: int, p: float, rng: np.random.Generator) -> csr_matrix:
    """Erdős–Rényi random graph."""
    edges = rng.random((N, N)) < p
    edges = np.triu(edges, k=1)
    A = edges + edges.T
    return csr_matrix(A, dtype=float)

def build_watts_strogatz(N: int, k: int, p: float, rng: np.random.Generator) -> csr_matrix:
    """Watts–Strogatz small-world graph."""
    # Start with ring lattice
    A = np.zeros((N, N))
    for i in range(N):
        for j in range(1, k // 2 + 1):
            A[i, (i + j) % N] = 1
            A[i, (i - j) % N] = 1
    
    # Rewire with probability p
    for i in range(N):
        neighbors = [j for j in range(N) if A[i, j] > 0 and j > i]
        for j in neighbors:
            if rng.random() < p:
                # Remove edge (i,j)
                A[i, j] = 0
                A[j, i] = 0
                
                # Add edge to random node (avoid self-loops and duplicates)
                candidates = [k for k in range(N) if k != i and A[i, k] == 0]
                if len(candidates) > 0:
                    new_target = rng.choice(candidates)
                    A[i, new_target] = 1
                    A[new_target, i] = 1
    
    return csr_matrix(A, dtype=float)

def build_barabasi_albert(N: int, m: int, rng: np.random.Generator) -> csr_matrix:
    """Barabási–Albert scale-free graph."""
    A = np.zeros((N, N))
    
    # Start with small complete graph
    m0 = max(m, 2)
    for i in range(m0):
        for j in range(i + 1, m0):
            A[i, j] = 1
            A[j, i] = 1
    
    # Add remaining nodes with preferential attachment
    for new_node in range(m0, N):
        # Compute degrees
        degrees = A.sum(axis=1)
        total_degree = degrees.sum()
        
        if total_degree == 0:
            # Fallback: connect to random existing nodes
            targets = rng.choice(new_node, size=min(m, new_node), replace=False)
        else:
            # Preferential attachment probabilities
            probs = degrees[:new_node] / total_degree
            targets = rng.choice(new_node, size=min(m, new_node), replace=False, p=probs)
        
        for target in targets:
            A[new_node, target] = 1
            A[target, new_node] = 1
    
    return csr_matrix(A, dtype=float)

# ============================================================================
# ENSEMBLE DYNAMICS
# ============================================================================

def step_ensemble(states: np.ndarray, W: csr_matrix, h_ext: np.ndarray,
                 rng: np.random.Generator, dt: float) -> np.ndarray:
    """Single Glauber dynamics step."""
    N = len(states)
    h_eff = h_ext + W.dot(states)
    flip_probs = 1.0 / (1.0 + np.exp(2 * states * h_eff))
    flips = rng.random(N) < flip_probs * dt
    new_states = states.copy()
    new_states[flips] *= -1
    return new_states

def measure_synchronization(trajectory: np.ndarray) -> float:
    """Measure synchronization order parameter."""
    return np.mean(np.abs(np.mean(trajectory, axis=1)))

# ============================================================================
# SINGLE TOPOLOGY SIMULATION
# ============================================================================

def run_single_topology(args: Tuple) -> dict:
    """Run simulation for a single topology and realization."""
    topology_type, realization_idx, cfg = args
    rng = np.random.default_rng(cfg.seed + realization_idx * 1000 + 
                                hash(topology_type) % 1000)
    
    # Build graph based on topology type
    if topology_type == 'ER':
        A = build_erdos_renyi(cfg.N, cfg.p_er, rng)
        params = {'type': 'Erdős-Rényi', 'p': cfg.p_er}
    elif topology_type == 'WS':
        A = build_watts_strogatz(cfg.N, cfg.k_ws, cfg.p_ws, rng)
        params = {'type': 'Watts-Strogatz', 'k': cfg.k_ws, 'p': cfg.p_ws}
    elif topology_type == 'BA':
        A = build_barabasi_albert(cfg.N, cfg.m_ba, rng)
        params = {'type': 'Barabási-Albert', 'm': cfg.m_ba}
    else:
        raise ValueError(f"Unknown topology: {topology_type}")
    
    W = cfg.J_base * A
    W_norm = sparse_norm(W, ord=2)
    
    # Compute graph properties
    degrees = np.array(A.sum(axis=1)).flatten()
    avg_degree = np.mean(degrees)
    clustering = compute_clustering_coefficient(A)
    
    # External field
    h_ext = 0.01 * rng.standard_normal(cfg.N)
    
    # Initialize states
    states = 2 * rng.integers(0, 2, size=cfg.N) - 1
    
    # Equilibrate
    for _ in range(cfg.steps_eq):
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Measure trajectory
    trajectory = np.zeros((cfg.steps_meas, cfg.N))
    for t in range(cfg.steps_meas):
        trajectory[t] = states
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Compute synchronization
    sync_order = measure_synchronization(trajectory)
    
    return {
        'topology': topology_type,
        'realization': realization_idx,
        'params': params,
        'W_norm': W_norm,
        'avg_degree': avg_degree,
        'clustering': clustering,
        'sync_order': sync_order,
        'N': cfg.N,
        'J': cfg.J_base
    }

def compute_clustering_coefficient(A: csr_matrix) -> float:
    """Compute global clustering coefficient."""
    A_dense = A.toarray()
    N = A_dense.shape[0]
    
    total_triplets = 0
    closed_triplets = 0
    
    for i in range(N):
        neighbors = np.where(A_dense[i] > 0)[0]
        k = len(neighbors)
        if k < 2:
            continue
        
        total_triplets += k * (k - 1) // 2
        
        for idx1 in range(len(neighbors)):
            for idx2 in range(idx1 + 1, len(neighbors)):
                if A_dense[neighbors[idx1], neighbors[idx2]] > 0:
                    closed_triplets += 1
    
    return closed_triplets / total_triplets if total_triplets > 0 else 0.0

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run E29 topology universality test."""
    cfg = E29Config()
    
    logger.info("=" * 80)
    logger.info("E9d/E29: Topology Universality Test")
    logger.info("=" * 80)
    logger.info(f"N = {cfg.N} CPs, J = {cfg.J_base}")
    logger.info(f"Topologies: ER, WS (small-world), BA (scale-free)")
    logger.info(f"Realizations per topology: {cfg.n_realizations}")
    logger.info(f"Parallelization: {cfg.n_cores} cores")
    logger.info("")
    
    # Prepare arguments
    args_list = []
    for topology in ['ER', 'WS', 'BA']:
        for real_idx in range(cfg.n_realizations):
            args_list.append((topology, real_idx, cfg))
    
    # Run in parallel
    with mp.Pool(cfg.n_cores) as pool:
        results = list(tqdm(
            pool.imap(run_single_topology, args_list),
            total=len(args_list),
            desc="Running topologies"
        ))
    
    # Group results by topology
    by_topology = {'ER': [], 'WS': [], 'BA': []}
    for r in results:
        by_topology[r['topology']].append(r)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS: Topology Universality")
    logger.info("=" * 80)
    logger.info(f"{'Topology':>15s} {'<||W||₂>':>12s} {'σ(||W||₂)':>12s} {'<sync>':>10s} "
                f"{'<k>':>8s} {'<C>':>8s}")
    logger.info("-" * 80)
    
    for topo in ['ER', 'WS', 'BA']:
        data = by_topology[topo]
        W_norms = [d['W_norm'] for d in data]
        syncs = [d['sync_order'] for d in data]
        degrees = [d['avg_degree'] for d in data]
        clusterings = [d['clustering'] for d in data]
        
        logger.info(
            f"{topo:>15s} {np.mean(W_norms):12.4f} {np.std(W_norms):12.4f} "
            f"{np.mean(syncs):10.4f} {np.mean(degrees):8.2f} {np.mean(clusterings):8.4f}"
        )
    
    # Check if sync order correlates with ||W||₂ across topologies
    all_W_norms = [r['W_norm'] for r in results]
    all_syncs = [r['sync_order'] for r in results]
    corr = np.corrcoef(all_W_norms, all_syncs)[0, 1]
    
    logger.info("")
    logger.info(f"Correlation sync vs ||W||₂ (all topologies): ρ = {corr:.4f}")
    
    if corr > 0.3:
        logger.info("✅ SPECTRAL CONTROL CONFIRMED ACROSS TOPOLOGIES")
    else:
        logger.info("⚠️  Weak correlation (may need larger N or more realizations)")
    
    # Save results
    import os
    os.makedirs('e29_topology_outputs', exist_ok=True)
    
    output_data = {
        'params': asdict(cfg),
        'results': results,
        'summary_by_topology': {
            topo: {
                'W_norm_mean': float(np.mean([d['W_norm'] for d in by_topology[topo]])),
                'W_norm_std': float(np.std([d['W_norm'] for d in by_topology[topo]])),
                'sync_mean': float(np.mean([d['sync_order'] for d in by_topology[topo]])),
                'sync_std': float(np.std([d['sync_order'] for d in by_topology[topo]])),
                'degree_mean': float(np.mean([d['avg_degree'] for d in by_topology[topo]])),
                'clustering_mean': float(np.mean([d['clustering'] for d in by_topology[topo]]))
            }
            for topo in ['ER', 'WS', 'BA']
        },
        'correlation': float(corr)
    }
    
    with open('e29_topology_outputs/e29_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Results saved to e29_topology_outputs/e29_results.json")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()

