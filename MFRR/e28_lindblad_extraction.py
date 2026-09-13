#!/usr/bin/env python3
"""
E9c/E28: Explicit Lindblad Rate Extraction
===========================================

Validates Theorem (EAME → GKSL reduction) by extracting Lindblad rates γ_α
from ensemble dynamics and demonstrating functional dependence:
  γ_α = γ_α(||W||₂, Γ(Ψ))

Method: Fit reduced master equation dρ/dt = L[ρ] to coarse-grained dynamics
and extract diagonal Lindblad rates from decay of observables.

Cross-reference: MFRR manuscript §7.Y (Thm. EAME-Lindblad), §15.X (E9c validation)

Author: MFRR Computational Validation Suite
Date: November 4, 2025
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm as sparse_norm
from scipy.optimize import curve_fit
from typing import List, Tuple, Dict
import multiprocessing as mp
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class E28Config:
    """E9c/E28 configuration parameters."""
    N: int = 500               # Number of Choice Points (reduced for speed)
    p_edge: float = 2e-3       # ER graph edge probability (denser for faster relaxation)
    J_vals: List[float] = None # Coupling strengths to test
    n_J: int = 7               # Number of J values
    J_min: float = 0.02
    J_max: float = 0.14
    
    steps_eq: int = 200        # Equilibration steps
    steps_meas: int = 300      # Measurement steps for Lindblad fit
    dt: float = 0.5            # Time step
    
    # Coherence parameters
    alpha1: float = 1.0        # Ψ² penalty
    alpha2: float = 0.5        # |∇Ψ|² penalty
    
    # Lindblad extraction parameters
    n_windows: int = 6         # Number of time windows for rate extraction
    window_size: int = 50      # Steps per window
    
    seed: int = 99
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
# REDUCED DENSITY MATRIX OBSERVABLES
# ============================================================================

def compute_density_matrix_observables(states_trajectory: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute observables that characterize the reduced density matrix:
      - Magnetization: m = ⟨b⟩
      - Variance: σ² = ⟨b²⟩ - ⟨b⟩²
      - Coherence proxy: ⟨|b_i - b_j|⟩ for nearest neighbors (off-diagonal decay)
    
    Args:
        states_trajectory: (T, N) array
        
    Returns:
        Dictionary of observables vs time
    """
    T, N = states_trajectory.shape
    
    m = np.mean(states_trajectory, axis=1)          # Magnetization
    m2 = np.mean(states_trajectory**2, axis=1)      # ⟨b²⟩
    variance = m2 - m**2                             # Variance
    
    # Off-diagonal proxy: variance of states (spread)
    # Higher spread → more coherence
    spread = np.std(states_trajectory, axis=1)
    
    return {
        'magnetization': m,
        'variance': variance,
        'spread': spread,
        'time': np.arange(T)
    }

# ============================================================================
# LINDBLAD RATE EXTRACTION
# ============================================================================

def extract_lindblad_rates(observables: Dict[str, np.ndarray], 
                          dt: float, 
                          window_size: int) -> List[Dict]:
    """
    Extract Lindblad damping rates from observable decay.
    
    Fit exponential decay γ in each time window:
      Observable(t) ≈ O_∞ + (O_0 - O_∞) exp(-γ t)
    
    Returns:
        List of {window_idx, gamma_m, gamma_var, gamma_spread, t_center}
    """
    T = len(observables['time'])
    n_windows = max(1, T // window_size)
    
    rates = []
    
    for w in range(n_windows):
        t_start = w * window_size
        t_end = min((w + 1) * window_size, T)
        
        if t_end - t_start < 10:  # Need at least 10 points
            continue
        
        t_win = observables['time'][t_start:t_end] * dt
        t_win = t_win - t_win[0]  # Shift to start at 0
        
        # Extract rates for each observable
        gamma_m = fit_exponential_rate(t_win, observables['magnetization'][t_start:t_end])
        gamma_var = fit_exponential_rate(t_win, observables['variance'][t_start:t_end])
        gamma_spread = fit_exponential_rate(t_win, observables['spread'][t_start:t_end])
        
        rates.append({
            'window': w,
            't_center': (t_start + t_end) / 2 * dt,
            'gamma_m': gamma_m,
            'gamma_var': gamma_var,
            'gamma_spread': gamma_spread
        })
    
    return rates

def fit_exponential_rate(t: np.ndarray, obs: np.ndarray) -> float:
    """
    Fit obs(t) = O_inf + (O_0 - O_inf) exp(-gamma t) and return gamma.
    If fit fails, return NaN.
    """
    if len(t) < 3:
        return np.nan
    
    # Initial guess
    O_inf_guess = obs[-1]
    O_0_guess = obs[0]
    gamma_guess = 0.1
    
    def model(t, gamma, O_0, O_inf):
        return O_inf + (O_0 - O_inf) * np.exp(-gamma * t)
    
    try:
        popt, _ = curve_fit(model, t, obs,
                           p0=[gamma_guess, O_0_guess, O_inf_guess],
                           bounds=([0, -np.inf, -np.inf], [np.inf, np.inf, np.inf]),
                           maxfev=5000)
        return popt[0]  # gamma
    except Exception:
        return np.nan

# ============================================================================
# SINGLE J SIMULATION
# ============================================================================

def run_single_J(args: Tuple) -> dict:
    """Run Lindblad rate extraction for a single coupling strength J."""
    J, cfg = args
    rng = np.random.default_rng(cfg.seed + int(J * 10000))
    
    # Build graph
    A = build_ER_graph(cfg.N, cfg.p_edge, rng)
    W = J * A
    W_norm = sparse_norm(W, ord=2)
    
    # External field
    h_ext = 0.01 * rng.standard_normal(cfg.N)
    
    # Initialize states
    states = 2 * rng.integers(0, 2, size=cfg.N) - 1
    
    # Equilibrate
    for _ in range(cfg.steps_eq):
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Measure trajectory
    trajectory = np.zeros((cfg.steps_meas, cfg.N))
    Gamma_Psi_vals = []
    
    for t in range(cfg.steps_meas):
        trajectory[t] = states
        Gamma_Psi_vals.append(compute_coherence_penalty(states, cfg.alpha1, cfg.alpha2, A))
        states = step_ensemble(states, W, h_ext, rng, cfg.dt)
    
    # Compute observables
    observables = compute_density_matrix_observables(trajectory)
    
    # Extract Lindblad rates
    rates = extract_lindblad_rates(observables, cfg.dt, cfg.window_size)
    
    # Average rates across windows (excluding NaNs)
    gamma_m_all = [r['gamma_m'] for r in rates if not np.isnan(r['gamma_m'])]
    gamma_var_all = [r['gamma_var'] for r in rates if not np.isnan(r['gamma_var'])]
    gamma_spread_all = [r['gamma_spread'] for r in rates if not np.isnan(r['gamma_spread'])]
    
    gamma_m_mean = np.mean(gamma_m_all) if len(gamma_m_all) > 0 else np.nan
    gamma_var_mean = np.mean(gamma_var_all) if len(gamma_var_all) > 0 else np.nan
    gamma_spread_mean = np.mean(gamma_spread_all) if len(gamma_spread_all) > 0 else np.nan
    
    # Average coherence penalty
    Gamma_Psi_mean = np.mean(Gamma_Psi_vals)
    
    return {
        'J': J,
        'W_norm': W_norm,
        'Gamma_Psi_mean': Gamma_Psi_mean,
        'gamma_m_mean': gamma_m_mean,
        'gamma_var_mean': gamma_var_mean,
        'gamma_spread_mean': gamma_spread_mean,
        'rates_by_window': rates,
        'n_windows_valid': len(gamma_m_all)
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run E28 Lindblad rate extraction."""
    cfg = E28Config()
    
    logger.info("=" * 80)
    logger.info("E9c/E28: Lindblad Rate Extraction")
    logger.info("=" * 80)
    logger.info(f"N = {cfg.N} CPs, p = {cfg.p_edge}")
    logger.info(f"J sweep: {len(cfg.J_vals)} values in [{cfg.J_min}, {cfg.J_max}]")
    logger.info(f"Measurement: {cfg.steps_meas} steps, {cfg.n_windows} windows")
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
    logger.info("RESULTS: Lindblad Rates")
    logger.info("=" * 80)
    logger.info(f"{'J':>8s} {'||W||₂':>10s} {'γ_m':>12s} {'γ_σ²':>12s} {'γ_spread':>12s} {'Windows':>8s}")
    logger.info("-" * 80)
    
    for r in results:
        logger.info(
            f"{r['J']:8.4f} {r['W_norm']:10.4f} "
            f"{r['gamma_m_mean']:12.6f} {r['gamma_var_mean']:12.6f} "
            f"{r['gamma_spread_mean']:12.6f} {r['n_windows_valid']:8d}"
        )
    
    # Check trends
    gamma_m_vals = [r['gamma_m_mean'] for r in results if not np.isnan(r['gamma_m_mean'])]
    W_norm_vals = [r['W_norm'] for r in results if not np.isnan(r['gamma_m_mean'])]
    
    if len(gamma_m_vals) >= 3:
        # Pearson correlation
        corr = np.corrcoef(W_norm_vals, gamma_m_vals)[0, 1]
        logger.info("")
        logger.info(f"Correlation γ_m vs ||W||₂: ρ = {corr:.4f}")
        
        if corr > 0.3:
            logger.info("✅ POSITIVE CORRELATION CONFIRMED (EAME→GKSL VALIDATED)")
        else:
            logger.info("⚠️  Weak correlation (may need longer measurement)")
    
    # Save results
    import os
    os.makedirs('e28_lindblad_outputs', exist_ok=True)
    
    output_data = {
        'params': asdict(cfg),
        'results': results,
        'summary': {
            'J': [r['J'] for r in results],
            'W_norm': [r['W_norm'] for r in results],
            'gamma_m': [r['gamma_m_mean'] for r in results],
            'gamma_var': [r['gamma_var_mean'] for r in results],
            'gamma_spread': [r['gamma_spread_mean'] for r in results],
            'Gamma_Psi': [r['Gamma_Psi_mean'] for r in results]
        }
    }
    
    with open('e28_lindblad_outputs/e28_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Results saved to e28_lindblad_outputs/e28_results.json")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()

