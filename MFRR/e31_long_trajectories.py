#!/usr/bin/env python3
"""
E9f/E31: Extended Long-Trajectory Test
=======================================

Extends E9b/E9c to 1000+ step trajectories for refined Lindblad rate extraction.
Longer timescales allow cleaner separation of short-time thermalization from
long-time master-equation relaxation.

Cross-reference: MFRR manuscript §15 (E9f validation)

Author: MFRR Computational Validation Suite
Date: November 4, 2025
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm as sparse_norm
from scipy.optimize import curve_fit
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
class E31Config:
    """E9f/E31 configuration parameters."""
    N: int = 400               # Number of Choice Points
    p_edge: float = 3e-3       # ER graph edge probability
    J_vals: List[float] = None # Coupling strengths to test
    n_J: int = 6               # Number of J values
    J_min: float = 0.03
    J_max: float = 0.13
    
    steps_eq: int = 300        # Longer equilibration
    steps_meas: int = 1000     # LONG measurement (key improvement)
    dt: float = 0.5            # Time step
    
    # Coherence parameters
    alpha1: float = 1.0        # Ψ² penalty
    alpha2: float = 0.5        # |∇Ψ|² penalty
    
    # Analysis parameters
    n_windows: int = 10        # More windows for better statistics
    
    seed: int = 999
    n_cores: int = 6
    
    def __post_init__(self):
        if self.J_vals is None:
            self.J_vals = np.linspace(self.J_min, self.J_max, self.n_J).tolist()

# ============================================================================
# ENSEMBLE DYNAMICS
# ============================================================================

def build_ER_graph(N: int, p: float, rng: np.random.Generator) -> csr_matrix:
    """Build Erdős–Rényi adjacency matrix."""
    edges = rng.random((N, N)) < p
    edges = np.triu(edges, k=1)
    A = edges + edges.T
    return csr_matrix(A, dtype=float)

def compute_coherence_penalty(states: np.ndarray, alpha1: float, alpha2: float, 
                              A: csr_matrix) -> float:
    """Coherence penalty Γ(Ψ) proxy."""
    Psi = states.astype(float)
    Psi2_mean = np.mean(Psi**2)
    
    grad_sq = 0.0
    rows, cols = A.nonzero()
    for i, j in zip(rows, cols):
        grad_sq += (Psi[i] - Psi[j])**2
    grad_sq /= max(1, len(rows))
    
    return alpha1 * Psi2_mean + alpha2 * grad_sq

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

# ============================================================================
# REFINED LINDBLAD RATE EXTRACTION
# ============================================================================

def extract_refined_rates(trajectory: np.ndarray, dt: float, 
                         n_windows: int) -> dict:
    """
    Extract Lindblad rates with improved multi-window analysis.
    
    Returns:
        Dictionary with gamma_early, gamma_late, gamma_avg, gamma_std
    """
    T, N = trajectory.shape
    window_size = T // n_windows
    
    # Compute magnetization time series
    m_series = np.mean(trajectory, axis=1)
    
    rates = []
    for w in range(n_windows):
        t_start = w * window_size
        t_end = min((w + 1) * window_size, T)
        
        if t_end - t_start < 20:
            continue
        
        t_win = np.arange(t_end - t_start) * dt
        m_win = m_series[t_start:t_end]
        
        # Fit exponential
        def model(t, gamma, m_0, m_inf):
            return m_inf + (m_0 - m_inf) * np.exp(-gamma * t)
        
        try:
            popt, _ = curve_fit(model, t_win, m_win,
                               p0=[0.01, m_win[0], m_win[-1]],
                               bounds=([0, -1, -1], [1, 1, 1]),
                               maxfev=5000)
            rates.append(popt[0])
        except Exception:
            pass
    
    if len(rates) < 3:
        return {
            'gamma_early': np.nan,
            'gamma_late': np.nan,
            'gamma_avg': np.nan,
            'gamma_std': np.nan,
            'n_windows_valid': 0
        }
    
    # Early vs late dynamics
    n_early = max(1, len(rates) // 3)
    gamma_early = np.mean(rates[:n_early])
    gamma_late = np.mean(rates[-n_early:])
    
    return {
        'gamma_early': gamma_early,
        'gamma_late': gamma_late,
        'gamma_avg': np.mean(rates),
        'gamma_std': np.std(rates),
        'n_windows_valid': len(rates)
    }

# ============================================================================
# SINGLE J SIMULATION
# ============================================================================

def run_single_J(args: Tuple) -> dict:
    """Run long-trajectory simulation for a single coupling strength J."""
    J, cfg = args
    rng = np.random.default_rng(cfg.seed + int(J * 100000))
    
    # Build graph
    A = build_ER_graph(cfg.N, cfg.p_edge, rng)
    W = J * A
    W_norm = sparse_norm(W, ord=2)
    
    # External field
    h_ext = 0.01 * rng.standard_normal(cfg.N)
    
    # Initialize states
    states = 2 * rng.integers(0, 2, size=cfg.N) - 1
    
    # Long equilibration
    for _ in range(cfg.steps_eq):
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # LONG measurement trajectory
    trajectory = np.zeros((cfg.steps_meas, cfg.N))
    Gamma_Psi_vals = []
    
    for t in range(cfg.steps_meas):
        trajectory[t] = states
        Gamma_Psi_vals.append(compute_coherence_penalty(states, cfg.alpha1, cfg.alpha2, A))
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Extract refined rates
    rate_data = extract_refined_rates(trajectory, cfg.dt, cfg.n_windows)
    
    # Average coherence penalty
    Gamma_Psi_mean = np.mean(Gamma_Psi_vals)
    
    return {
        'J': J,
        'W_norm': W_norm,
        'Gamma_Psi_mean': Gamma_Psi_mean,
        **rate_data
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run E31 long-trajectory Lindblad rate extraction."""
    cfg = E31Config()
    
    logger.info("=" * 80)
    logger.info("E9f/E31: Extended Long-Trajectory Test")
    logger.info("=" * 80)
    logger.info(f"N = {cfg.N} CPs, p = {cfg.p_edge}")
    logger.info(f"J sweep: {len(cfg.J_vals)} values in [{cfg.J_min}, {cfg.J_max}]")
    logger.info(f"Measurement: {cfg.steps_meas} steps (LONG), {cfg.n_windows} windows")
    logger.info(f"Parallelization: {cfg.n_cores} cores")
    logger.info("")
    
    # Prepare arguments
    args_list = [(J, cfg) for J in cfg.J_vals]
    
    # Run in parallel
    with mp.Pool(cfg.n_cores) as pool:
        results = list(tqdm(
            pool.imap(run_single_J, args_list),
            total=len(args_list),
            desc="Running J sweep"
        ))
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS: Refined Lindblad Rates (Long Trajectories)")
    logger.info("=" * 80)
    logger.info(f"{'J':>8s} {'||W||₂':>10s} {'γ_avg':>12s} {'γ_std':>12s} "
                f"{'γ_early/late':>15s} {'Windows':>8s}")
    logger.info("-" * 80)
    
    for r in results:
        ratio_str = f"{r['gamma_early']/r['gamma_late']:.2f}" if not np.isnan(r['gamma_late']) and r['gamma_late'] > 0 else "N/A"
        logger.info(
            f"{r['J']:8.4f} {r['W_norm']:10.4f} "
            f"{r['gamma_avg']:12.6f} {r['gamma_std']:12.6f} "
            f"{ratio_str:>15s} {r['n_windows_valid']:8d}"
        )
    
    # Check correlation
    gamma_vals = [r['gamma_avg'] for r in results if not np.isnan(r['gamma_avg'])]
    W_norm_vals = [r['W_norm'] for r in results if not np.isnan(r['gamma_avg'])]
    
    if len(gamma_vals) >= 3:
        corr = np.corrcoef(W_norm_vals, gamma_vals)[0, 1]
        logger.info("")
        logger.info(f"Correlation γ_avg vs ||W||₂: ρ = {corr:.4f}")
        
        # Check if std is lower than in E9c (refinement)
        avg_std = np.mean([r['gamma_std'] for r in results if not np.isnan(r['gamma_std'])])
        logger.info(f"Average γ_std (window-to-window): {avg_std:.4f}")
        logger.info("✅ REFINED RATE EXTRACTION COMPLETE (1000-step trajectories)")
    
    # Save results
    import os
    os.makedirs('e31_long_outputs', exist_ok=True)
    
    output_data = {
        'params': asdict(cfg),
        'results': results,
        'summary': {
            'J': [r['J'] for r in results],
            'W_norm': [r['W_norm'] for r in results],
            'gamma_avg': [r['gamma_avg'] for r in results],
            'gamma_std': [r['gamma_std'] for r in results],
            'correlation': float(corr) if len(gamma_vals) >= 3 else np.nan
        }
    }
    
    with open('e31_long_outputs/e31_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Results saved to e31_long_outputs/e31_results.json")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()

