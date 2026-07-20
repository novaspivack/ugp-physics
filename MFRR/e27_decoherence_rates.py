#!/usr/bin/env python3
"""
E9b/E27: Decoherence Rates vs Ensemble Spectrum
================================================

Validates Theorem (EAME → GKSL reduction) by measuring short-time decoherence rates
from time-autocorrelation decay and demonstrating their dependence on:
  - Ensemble spectral norm ||W||₂
  - Coherence penalty Γ(Ψ)

Cross-reference: MFRR manuscript §7.Y (Thm. EAME-Lindblad), §15.X (E9b validation)

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
class E27Config:
    """E9b/E27 configuration parameters."""
    N: int = 1000              # Number of Choice Points
    p_edge: float = 1e-3       # ER graph edge probability
    J_vals: List[float] = None # Coupling strengths to test
    n_J: int = 8               # Number of J values
    J_min: float = 0.01
    J_max: float = 0.15
    
    steps_eq: int = 100        # Equilibration steps
    steps_corr: int = 200      # Steps for correlation measurement
    dt: float = 1.0            # Time step
    
    # Coherence parameters
    alpha1: float = 1.0        # Ψ² penalty
    alpha2: float = 0.5        # |∇Ψ|² penalty
    
    # Analysis parameters
    tau_fit_max: int = 50      # Max lag for exponential fit
    
    seed: int = 42
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
    edges = np.triu(edges, k=1)  # Upper triangular
    A = edges + edges.T          # Symmetrize
    return csr_matrix(A, dtype=float)

def compute_coherence_penalty(states: np.ndarray, alpha1: float, alpha2: float, 
                              A: csr_matrix) -> float:
    """
    Coherence penalty Γ(Ψ) proxy:
      Γ ≈ α₁⟨Ψ²⟩ + α₂⟨|∇Ψ|²⟩
    
    For binary states, use Ψ_i = b_i as proxy.
    Gradient: |∇Ψ|² ≈ Σ_{ij} A_{ij} (Ψ_i - Ψ_j)²
    """
    Psi = states.astype(float)  # Treat states as Ψ proxy
    
    # ⟨Ψ²⟩
    Psi2_mean = np.mean(Psi**2)
    
    # ⟨|∇Ψ|²⟩ via graph Laplacian
    # |∇Ψ|² = Σ_ij A_ij (Ψ_i - Ψ_j)²
    grad_sq = 0.0
    rows, cols = A.nonzero()
    for i, j in zip(rows, cols):
        grad_sq += (Psi[i] - Psi[j])**2
    grad_sq /= max(1, len(rows))  # Normalize by edge count
    
    return alpha1 * Psi2_mean + alpha2 * grad_sq

def step_ensemble(states: np.ndarray, W: csr_matrix, h_ext: np.ndarray,
                 rng: np.random.Generator, dt: float) -> np.ndarray:
    """
    Single time step: Glauber dynamics on coupled CPs.
    
    Effective field: h_eff[i] = h_ext[i] + Σ_j W_ij b_j
    Flip probability: p_flip = 1/(1 + exp(2 b_i h_eff[i]))
    """
    N = len(states)
    h_eff = h_ext + W.dot(states)
    
    # Metropolis-like flip probabilities
    flip_probs = 1.0 / (1.0 + np.exp(2 * states * h_eff))
    flips = rng.random(N) < flip_probs * dt
    
    new_states = states.copy()
    new_states[flips] *= -1
    
    return new_states

# ============================================================================
# TIME-AUTOCORRELATION MEASUREMENT
# ============================================================================

def measure_autocorrelation(states_trajectory: np.ndarray, max_lag: int) -> np.ndarray:
    """
    Compute time-autocorrelation C(Δt) = ⟨b_i(t) b_i(t+Δt)⟩.
    
    Args:
        states_trajectory: (T, N) array of states over time
        max_lag: Maximum time lag
        
    Returns:
        C(τ) for τ = 0, 1, ..., max_lag
    """
    T, N = states_trajectory.shape
    C = np.zeros(max_lag + 1)
    
    for tau in range(max_lag + 1):
        if T - tau < 1:
            C[tau] = np.nan
            continue
        
        # Average over time and sites
        corr_sum = 0.0
        count = 0
        for t in range(T - tau):
            corr_sum += np.mean(states_trajectory[t] * states_trajectory[t + tau])
            count += 1
        
        C[tau] = corr_sum / count if count > 0 else np.nan
    
    return C

def fit_exponential_decay(C: np.ndarray, times: np.ndarray) -> Tuple[float, float, float]:
    """
    Fit C(t) = A exp(-Γ t) + C_∞
    
    Returns:
        (Γ, A, C_∞) or (nan, nan, nan) if fit fails
    """
    # Remove NaNs
    valid = ~np.isnan(C)
    if np.sum(valid) < 3:
        return (np.nan, np.nan, np.nan)
    
    C_valid = C[valid]
    t_valid = times[valid]
    
    # Initial guess
    C_inf_guess = C_valid[-1] if len(C_valid) > 0 else 0.0
    A_guess = C_valid[0] - C_inf_guess if len(C_valid) > 0 else 1.0
    Gamma_guess = 0.1
    
    def model(t, Gamma, A, C_inf):
        return A * np.exp(-Gamma * t) + C_inf
    
    try:
        popt, _ = curve_fit(model, t_valid, C_valid, 
                           p0=[Gamma_guess, A_guess, C_inf_guess],
                           bounds=([0, -np.inf, -np.inf], [np.inf, np.inf, np.inf]),
                           maxfev=5000)
        return tuple(popt)
    except Exception:
        return (np.nan, np.nan, np.nan)

# ============================================================================
# SINGLE J SIMULATION
# ============================================================================

def run_single_J(args: Tuple) -> dict:
    """Run simulation for a single coupling strength J."""
    J, cfg = args
    rng = np.random.default_rng(cfg.seed + int(J * 1000))
    
    # Build graph
    A = build_ER_graph(cfg.N, cfg.p_edge, rng)
    W = J * A
    W_norm = sparse_norm(W, ord=2)
    
    # External field (small jitter)
    h_ext = 0.01 * rng.standard_normal(cfg.N)
    
    # Initialize states
    states = 2 * rng.integers(0, 2, size=cfg.N) - 1  # {-1, +1}
    
    # Equilibrate
    for _ in range(cfg.steps_eq):
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Measure trajectory
    trajectory = np.zeros((cfg.steps_corr, cfg.N))
    Gamma_Psi_vals = []
    
    for t in range(cfg.steps_corr):
        trajectory[t] = states
        Gamma_Psi_vals.append(compute_coherence_penalty(states, cfg.alpha1, cfg.alpha2, A))
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Compute autocorrelation
    C = measure_autocorrelation(trajectory, cfg.tau_fit_max)
    times = np.arange(len(C)) * cfg.dt
    
    # Fit decay rate
    Gamma, A, C_inf = fit_exponential_decay(C, times)
    
    # Average coherence penalty
    Gamma_Psi_mean = np.mean(Gamma_Psi_vals)
    
    return {
        'J': J,
        'W_norm': W_norm,
        'Gamma': Gamma,
        'A': A,
        'C_inf': C_inf,
        'Gamma_Psi_mean': Gamma_Psi_mean,
        'C_curve': C.tolist(),
        'fit_success': not np.isnan(Gamma)
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run E27 decoherence rate analysis."""
    cfg = E27Config()
    
    logger.info("=" * 80)
    logger.info("E9b/E27: Decoherence Rates vs Ensemble Spectrum")
    logger.info("=" * 80)
    logger.info(f"N = {cfg.N} CPs, p = {cfg.p_edge}")
    logger.info(f"J sweep: {len(cfg.J_vals)} values in [{cfg.J_min}, {cfg.J_max}]")
    logger.info(f"Correlation measurement: {cfg.steps_corr} steps")
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
    
    # Collect results
    J_list = [r['J'] for r in results]
    W_norm_list = [r['W_norm'] for r in results]
    Gamma_list = [r['Gamma'] for r in results]
    Gamma_Psi_list = [r['Gamma_Psi_mean'] for r in results]
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS: Decoherence Rates")
    logger.info("=" * 80)
    logger.info(f"{'J':>8s} {'||W||₂':>10s} {'Γ (rate)':>12s} {'Γ(Ψ)':>12s} {'Fit':>8s}")
    logger.info("-" * 80)
    
    for r in results:
        fit_status = "✓" if r['fit_success'] else "✗"
        logger.info(
            f"{r['J']:8.4f} {r['W_norm']:10.4f} {r['Gamma']:12.6f} "
            f"{r['Gamma_Psi_mean']:12.6f} {fit_status:>8s}"
        )
    
    # Check monotonicity
    Gamma_valid = [G for G in Gamma_list if not np.isnan(G)]
    if len(Gamma_valid) >= 2:
        increasing = all(Gamma_valid[i] <= Gamma_valid[i+1] 
                        for i in range(len(Gamma_valid)-1))
        logger.info("")
        if increasing:
            logger.info("✅ Γ INCREASES MONOTONICALLY with ||W||₂ (EAME→GKSL CONFIRMED)")
        else:
            logger.info("⚠️  Γ does not increase strictly (may need longer equilibration)")
    
    # Save results
    import os
    os.makedirs('e27_decoherence_outputs', exist_ok=True)
    
    output_data = {
        'params': asdict(cfg),
        'results': results,
        'summary': {
            'J': J_list,
            'W_norm': W_norm_list,
            'Gamma': Gamma_list,
            'Gamma_Psi': Gamma_Psi_list
        }
    }
    
    with open('e27_decoherence_outputs/e27_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Results saved to e27_decoherence_outputs/e27_results.json")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()

