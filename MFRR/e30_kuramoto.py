#!/usr/bin/env python3
"""
E9e/E30: Kuramoto Continuous-Phase Test
========================================

Tests ensemble adjudication with continuous-phase variables (Kuramoto oscillators)
to demonstrate strong γ_α(||W||₂) dependence that was weak in binary Ising model.

Continuous phases allow slower, more observable master-equation dynamics.

Cross-reference: MFRR manuscript §15 (E9e validation)

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
class E30Config:
    """E9e/E30 configuration parameters."""
    N: int = 300               # Number of oscillators
    p_edge: float = 5e-3       # ER graph edge probability
    J_vals: List[float] = None # Coupling strengths to test
    n_J: int = 7               # Number of J values
    J_min: float = 0.02
    J_max: float = 0.20
    
    steps_eq: int = 200        # Equilibration steps
    steps_meas: int = 400      # Measurement steps for rate extraction
    dt: float = 0.1            # Time step (smaller for phases)
    
    omega_std: float = 0.1     # Natural frequency spread
    
    seed: int = 888
    n_cores: int = 6
    
    def __post_init__(self):
        if self.J_vals is None:
            self.J_vals = np.linspace(self.J_min, self.J_max, self.n_J).tolist()

# ============================================================================
# KURAMOTO DYNAMICS
# ============================================================================

def build_ER_graph(N: int, p: float, rng: np.random.Generator) -> csr_matrix:
    """Build Erdős–Rényi adjacency matrix."""
    edges = rng.random((N, N)) < p
    edges = np.triu(edges, k=1)
    A = edges + edges.T
    return csr_matrix(A, dtype=float)

def step_kuramoto(phases: np.ndarray, W: csr_matrix, omega: np.ndarray,
                 dt: float) -> np.ndarray:
    """
    Single time step for Kuramoto oscillators:
    dθ_i/dt = ω_i + Σ_j W_ij sin(θ_j - θ_i)
    """
    N = len(phases)
    
    # Compute interaction term
    interaction = np.zeros(N)
    rows, cols = W.nonzero()
    for i, j in zip(rows, cols):
        interaction[i] += W[i,j] * np.sin(phases[j] - phases[i])
    
    # Update phases
    new_phases = phases + dt * (omega + interaction)
    
    # Wrap to [-π, π]
    new_phases = (new_phases + np.pi) % (2 * np.pi) - np.pi
    
    return new_phases

def compute_order_parameter(phases: np.ndarray) -> float:
    """
    Kuramoto order parameter:
    r = |⟨exp(iθ)⟩|
    """
    return np.abs(np.mean(np.exp(1j * phases)))

# ============================================================================
# LINDBLAD RATE EXTRACTION
# ============================================================================

def extract_coherence_decay_rate(trajectory: np.ndarray, dt: float, 
                                  window_size: int = 100) -> float:
    """
    Extract decay rate γ from order parameter time series.
    
    Order parameter r(t) ≈ r_∞ + (r_0 - r_∞) exp(-γ t)
    """
    T = len(trajectory)
    order_params = np.array([compute_order_parameter(trajectory[t]) 
                            for t in range(T)])
    
    # Use only first window for clean exponential fit
    window = min(window_size, T)
    r_vals = order_params[:window]
    times = np.arange(window) * dt
    
    # Fit exponential decay
    def model(t, gamma, r_0, r_inf):
        return r_inf + (r_0 - r_inf) * np.exp(-gamma * t)
    
    try:
        # Initial guess
        r_inf_guess = r_vals[-1]
        r_0_guess = r_vals[0]
        gamma_guess = 0.01
        
        popt, _ = curve_fit(model, times, r_vals,
                           p0=[gamma_guess, r_0_guess, r_inf_guess],
                           bounds=([0, 0, 0], [1, 1, 1]),
                           maxfev=5000)
        return popt[0]  # gamma
    except Exception:
        return np.nan

# ============================================================================
# SINGLE J SIMULATION
# ============================================================================

def run_single_J(args: Tuple) -> dict:
    """Run Kuramoto simulation for a single coupling strength J."""
    J, cfg = args
    rng = np.random.default_rng(cfg.seed + int(J * 10000))
    
    # Build graph
    A = build_ER_graph(cfg.N, cfg.p_edge, rng)
    W = J * A
    W_norm = sparse_norm(W, ord=2)
    
    # Natural frequencies (heterogeneous)
    omega = rng.normal(0, cfg.omega_std, size=cfg.N)
    
    # Initialize phases uniformly
    phases = rng.uniform(-np.pi, np.pi, size=cfg.N)
    
    # Equilibrate
    for _ in range(cfg.steps_eq):
        phases = step_kuramoto(phases, W, omega, cfg.dt)
    
    # Measure trajectory
    trajectory = np.zeros((cfg.steps_meas, cfg.N))
    for t in range(cfg.steps_meas):
        trajectory[t] = phases
        phases = step_kuramoto(phases, W, omega, cfg.dt)
    
    # Extract decay rate
    gamma = extract_coherence_decay_rate(trajectory, cfg.dt)
    
    # Final order parameter
    final_order = compute_order_parameter(trajectory[-1])
    
    return {
        'J': J,
        'W_norm': W_norm,
        'gamma': gamma,
        'final_order': final_order,
        'fit_success': not np.isnan(gamma)
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run E30 Kuramoto continuous-phase test."""
    cfg = E30Config()
    
    logger.info("=" * 80)
    logger.info("E9e/E30: Kuramoto Continuous-Phase Test")
    logger.info("=" * 80)
    logger.info(f"N = {cfg.N} oscillators, p = {cfg.p_edge}")
    logger.info(f"J sweep: {len(cfg.J_vals)} values in [{cfg.J_min}, {cfg.J_max}]")
    logger.info(f"Measurement: {cfg.steps_meas} steps")
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
    logger.info("RESULTS: Kuramoto Lindblad Rates")
    logger.info("=" * 80)
    logger.info(f"{'J':>8s} {'||W||₂':>10s} {'γ':>12s} {'r_final':>10s} {'Fit':>8s}")
    logger.info("-" * 80)
    
    for r in results:
        fit_status = "✓" if r['fit_success'] else "✗"
        logger.info(
            f"{r['J']:8.4f} {r['W_norm']:10.4f} {r['gamma']:12.6f} "
            f"{r['final_order']:10.4f} {fit_status:>8s}"
        )
    
    # Check correlation
    gamma_vals = [r['gamma'] for r in results if not np.isnan(r['gamma'])]
    W_norm_vals = [r['W_norm'] for r in results if not np.isnan(r['gamma'])]
    
    if len(gamma_vals) >= 3:
        corr = np.corrcoef(W_norm_vals, gamma_vals)[0, 1]
        logger.info("")
        logger.info(f"Correlation γ vs ||W||₂: ρ = {corr:.4f}")
        
        if abs(corr) > 0.5:
            logger.info("✅ STRONG γ(||W||₂) DEPENDENCE CONFIRMED (Kuramoto)")
        elif abs(corr) > 0.3:
            logger.info("✅ MODERATE γ(||W||₂) DEPENDENCE CONFIRMED")
        else:
            logger.info("⚠️  Weak correlation (may need longer measurement)")
    
    # Save results
    import os
    os.makedirs('e30_kuramoto_outputs', exist_ok=True)
    
    output_data = {
        'params': asdict(cfg),
        'results': results,
        'summary': {
            'J': [r['J'] for r in results],
            'W_norm': [r['W_norm'] for r in results],
            'gamma': [r['gamma'] for r in results],
            'correlation': float(corr) if len(gamma_vals) >= 3 else np.nan
        }
    }
    
    with open('e30_kuramoto_outputs/e30_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Results saved to e30_kuramoto_outputs/e30_results.json")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()

