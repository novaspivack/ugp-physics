#!/usr/bin/env python3
"""
E30c: Pattern Formation Phase Diagram
======================================

Systematic parameter sweep to identify critical conditions for spontaneous
pattern formation through information-geometry co-evolution.

Sweeps over:
- Coupling strength (J_base)
- Feedback strength (beta)
- Information accumulation rate (omega_increment)
- Decay rate (gamma_omega)

Goal: Map out phase space and identify "sweet spot" for pattern formation.

This is a critical investigation to understand the precise conditions where
self-organizing informational structures emerge.

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/scripts/e30_coevolution.py
    Mathematical_Foundations_of_Reflexive_Reality.tex
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import time
from multiprocessing import Pool
from itertools import product

from common.ensemble_core import argmin_branch, inter_cost, local_cost


class E30cConfig:
    """Phase diagram sweep configuration."""
    # Fixed parameters
    L = 50                 # Moderate lattice for speed
    steps_total = 800      # Shorter for sweep efficiency
    
    # Parameter ranges to sweep
    J_base_values = [0.15, 0.20, 0.25, 0.30]
    beta_values = [1.0, 2.0, 3.0, 5.0, 7.0]
    omega_increment_values = [0.5, 1.0, 2.0, 3.0]
    gamma_omega_values = [0.01, 0.02, 0.05, 0.10]
    
    # Fixed (non-swept) parameters
    D_omega = 0.1
    kappa = 1.0
    m_squared = 0.05
    cascade_interval = 1
    seed_fraction = 0.05
    max_cascade_iter = 100
    
    # Multiprocessing
    n_cores = 8
    
    seed_base = 50


def init_lattice(L, rng):
    """Initialize lattice."""
    b = rng.integers(0, 2, size=(L, L))
    psi = np.zeros((L, L))
    omega = np.zeros((L, L))
    bias = rng.uniform(0.0, 1.0, size=(L, L))
    kappa = rng.uniform(0.1, 1.0, size=(L, L))
    return b, psi, omega, bias, kappa


def get_neighbors(i, j, L):
    """4-neighbors periodic."""
    return [((i-1)%L, j), ((i+1)%L, j), (i, (j-1)%L), (i, (j+1)%L)]


def lattice_cascade(b, psi, omega, bias, kappa, J_coupling, L, 
                   seed_frac, max_iter, rng, omega_inc):
    """Cascade with omega accumulation."""
    seed_mask = rng.random((L, L)) < seed_frac
    queue = list(zip(*np.where(seed_mask)))
    visited = set()
    flipped = []
    
    iterations = 0
    while queue and iterations < max_iter:
        iterations += 1
        if not queue:
            break
        
        i, j = queue.pop(0)
        if (i, j) in visited:
            continue
        visited.add((i, j))
        
        neighbors = get_neighbors(i, j, L)
        
        cost_0 = local_cost(0, psi[i,j], bias[i,j], kappa[i,j])
        cost_1 = local_cost(1, psi[i,j], bias[i,j], kappa[i,j])
        
        for ni, nj in neighbors:
            J_val = J_coupling[i,j]
            cost_0 += J_val * inter_cost(0, b[ni,nj])
            cost_1 += J_val * inter_cost(1, b[ni,nj])
        
        new_val = 0 if cost_0 <= cost_1 else 1
        
        if new_val != b[i,j]:
            b[i,j] = new_val
            flipped.append((i,j))
            omega[i,j] += omega_inc
            
            for ni, nj in neighbors:
                if (ni,nj) not in visited:
                    queue.append((ni,nj))
    
    return len(flipped)


def update_omega_diffusion(omega, D, gamma, dt=1.0):
    """Diffusion-decay."""
    laplacian_kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    laplacian = convolve(omega, laplacian_kernel, mode='wrap')
    omega_new = omega + dt * (D * laplacian - gamma * omega)
    return np.maximum(omega_new, 0.0)


def solve_psi_fft(omega, kappa, m_squared):
    """Solve for Psi via FFT."""
    L = omega.shape[0]
    omega_k = np.fft.fft2(omega)
    
    kx = 2*np.pi*np.fft.fftfreq(L)
    ky = 2*np.pi*np.fft.fftfreq(L)
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    k_squared = KX**2 + KY**2
    
    denom = k_squared + m_squared
    denom[0,0] = 1.0
    
    psi_k = kappa * omega_k / denom
    psi_k[0,0] = 0.0
    
    return np.fft.ifft2(psi_k).real


def compute_coupling_matrix(J_base, psi, beta, L):
    """Modulated coupling."""
    J_coupling = np.zeros((L,L))
    
    for i in range(L):
        for j in range(L):
            neighbors = get_neighbors(i, j, L)
            psi_avg = (psi[i,j] + np.mean([psi[ni,nj] for ni,nj in neighbors])) / 2
            J_coupling[i,j] = J_base * (1.0 + beta * psi_avg)
    
    J_coupling = np.clip(J_coupling, J_base*0.1, J_base*10.0)
    return J_coupling


def run_single_parameter_point(args):
    """Run simulation for one parameter combination."""
    J_base, beta, omega_inc, gamma_omega, cfg, run_id = args
    
    rng = default_rng(cfg.seed_base + run_id)
    L = cfg.L
    
    # Initialize
    b, psi, omega, bias, kappa = init_lattice(L, rng)
    
    # Track statistics
    psi_stds = []
    omega_means = []
    cascade_sizes = []
    
    # Run evolution
    for step in range(cfg.steps_total):
        # Update fields
        omega = update_omega_diffusion(omega, cfg.D_omega, gamma_omega, dt=1.0)
        psi = solve_psi_fft(omega, cfg.kappa, cfg.m_squared)
        J_coupling = compute_coupling_matrix(J_base, psi, beta, L)
        
        # Cascade
        if step % cfg.cascade_interval == 0:
            n_flips = lattice_cascade(
                b, psi, omega, bias, kappa, J_coupling, L,
                cfg.seed_fraction, cfg.max_cascade_iter, rng, omega_inc
            )
            cascade_sizes.append(n_flips)
        
        # Statistics
        psi_stds.append(np.std(psi))
        omega_means.append(np.mean(omega))
    
    # Compute pattern formation metrics
    psi_stds = np.array(psi_stds)
    
    # Early vs late comparison
    n_early = min(200, len(psi_stds)//3)
    n_late = min(200, len(psi_stds)//3)
    
    if len(psi_stds) > 2*n_early:
        early_std = np.mean(psi_stds[:n_early])
        late_std = np.mean(psi_stds[-n_late:])
        pattern_ratio = late_std / early_std if early_std > 1e-10 else 0.0
    else:
        pattern_ratio = 0.0
        early_std = 0.0
        late_std = 0.0
    
    # Peak std (maximum pattern strength during evolution)
    peak_std = np.max(psi_stds)
    
    # Final state metrics
    final_psi_std = psi_stds[-1] if len(psi_stds) > 0 else 0.0
    final_omega_mean = omega_means[-1] if len(omega_means) > 0 else 0.0
    mean_cascade = np.mean(cascade_sizes) if len(cascade_sizes) > 0 else 0.0
    
    # Stability: does std stay high?
    if len(psi_stds) > 100:
        stable_std = np.mean(psi_stds[-100:])
        stability = stable_std / (peak_std + 1e-10)
    else:
        stability = 0.0
    
    return {
        'J_base': J_base,
        'beta': beta,
        'omega_increment': omega_inc,
        'gamma_omega': gamma_omega,
        'pattern_ratio': pattern_ratio,
        'peak_std': peak_std,
        'final_psi_std': final_psi_std,
        'final_omega_mean': final_omega_mean,
        'mean_cascade': mean_cascade,
        'stability': stability,
        'early_std': early_std,
        'late_std': late_std
    }


def analyze_phase_diagram(results, cfg, output_dir):
    """Analyze and visualize phase diagram."""
    print("\n" + "=" * 80)
    print("PHASE DIAGRAM ANALYSIS")
    print("=" * 80)
    
    # Find best parameters
    results_sorted = sorted(results, key=lambda x: x['pattern_ratio'], reverse=True)
    
    print("\nTop 10 parameter combinations (by pattern ratio):")
    print(f"{'Rank':<6} {'J_base':<8} {'beta':<8} {'ω_inc':<8} {'γ':<8} {'Ratio':<10} {'Peak σ(Ψ)':<10}")
    print("-" * 80)
    
    for i, r in enumerate(results_sorted[:10]):
        print(f"{i+1:<6} {r['J_base']:<8.2f} {r['beta']:<8.1f} "
              f"{r['omega_increment']:<8.1f} {r['gamma_omega']:<8.3f} "
              f"{r['pattern_ratio']:<10.3f} {r['peak_std']:<10.4f}")
    
    # Identify "sweet spot"
    best = results_sorted[0]
    print(f"\n🎯 OPTIMAL PARAMETERS FOUND:")
    print(f"   J_base = {best['J_base']:.2f}")
    print(f"   β = {best['beta']:.1f}")
    print(f"   ω_increment = {best['omega_increment']:.1f}")
    print(f"   γ = {best['gamma_omega']:.3f}")
    print(f"   Pattern ratio: {best['pattern_ratio']:.3f}×")
    print(f"   Peak std(Ψ): {best['peak_std']:.4f}")
    print(f"   Stability: {best['stability']:.3f}")
    
    # Create phase diagrams (2D slices)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Slice 1: J_base vs beta (fixing omega_inc, gamma at their best values)
    ax1 = axes[0]
    plot_2d_slice(results, 'J_base', 'beta', 'pattern_ratio', ax1, cfg)
    ax1.set_title('Pattern Ratio: J vs β', fontsize=12)
    
    # Slice 2: omega_inc vs gamma
    ax2 = axes[1]
    plot_2d_slice(results, 'omega_increment', 'gamma_omega', 'pattern_ratio', ax2, cfg)
    ax2.set_title('Pattern Ratio: ω_inc vs γ', fontsize=12)
    
    # Slice 3: beta vs omega_inc
    ax3 = axes[2]
    plot_2d_slice(results, 'beta', 'omega_increment', 'pattern_ratio', ax3, cfg)
    ax3.set_title('Pattern Ratio: β vs ω_inc', fontsize=12)
    
    # Slice 4: Peak std heatmap
    ax4 = axes[3]
    plot_2d_slice(results, 'J_base', 'beta', 'peak_std', ax4, cfg)
    ax4.set_title('Peak std(Ψ): J vs β', fontsize=12)
    
    # Slice 5: Mean cascade size
    ax5 = axes[4]
    plot_2d_slice(results, 'omega_increment', 'gamma_omega', 'mean_cascade', ax5, cfg)
    ax5.set_title('Mean Cascade Size: ω_inc vs γ', fontsize=12)
    
    # Slice 6: Stability metric
    ax6 = axes[5]
    plot_2d_slice(results, 'J_base', 'gamma_omega', 'stability', ax6, cfg)
    ax6.set_title('Stability: J vs γ', fontsize=12)
    
    plt.tight_layout()
    fig_path = output_dir / 'e30c_phase_diagram.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Phase diagram saved: {fig_path}")
    plt.close()
    
    return best


def plot_2d_slice(results, param1, param2, metric, ax, cfg):
    """Plot 2D heatmap of metric vs two parameters."""
    # Get unique values
    vals1 = sorted(list(set([r[param1] for r in results])))
    vals2 = sorted(list(set([r[param2] for r in results])))
    
    # Create grid
    grid = np.zeros((len(vals2), len(vals1)))
    counts = np.zeros((len(vals2), len(vals1)))
    
    for r in results:
        try:
            i1 = vals1.index(r[param1])
            i2 = vals2.index(r[param2])
            grid[i2, i1] += r[metric]
            counts[i2, i1] += 1
        except ValueError:
            continue
    
    # Average over other parameters
    with np.errstate(divide='ignore', invalid='ignore'):
        grid = np.where(counts > 0, grid / counts, 0)
    
    # Plot
    im = ax.imshow(grid, aspect='auto', origin='lower', cmap='viridis',
                   extent=[min(vals1), max(vals1), min(vals2), max(vals2)])
    ax.set_xlabel(param1, fontsize=10)
    ax.set_ylabel(param2, fontsize=10)
    plt.colorbar(im, ax=ax, fraction=0.046)
    
    # Mark optimum
    if metric == 'pattern_ratio':
        max_idx = np.unravel_index(np.argmax(grid), grid.shape)
        best_val1 = vals1[max_idx[1]] if max_idx[1] < len(vals1) else vals1[-1]
        best_val2 = vals2[max_idx[0]] if max_idx[0] < len(vals2) else vals2[-1]
        ax.plot(best_val1, best_val2, 'r*', markersize=15, markeredgecolor='white', 
               markeredgewidth=1.5)


def main():
    """Run E30c: Phase diagram sweep."""
    cfg = E30cConfig()
    
    print("=" * 80)
    print("E30c: PATTERN FORMATION PHASE DIAGRAM")
    print("=" * 80)
    print(f"Lattice: {cfg.L}×{cfg.L}")
    print(f"Evolution: {cfg.steps_total} steps per point")
    print(f"\nParameter ranges:")
    print(f"  J_base: {cfg.J_base_values}")
    print(f"  beta: {cfg.beta_values}")
    print(f"  omega_increment: {cfg.omega_increment_values}")
    print(f"  gamma_omega: {cfg.gamma_omega_values}")
    
    # Generate all combinations
    param_combinations = list(product(
        cfg.J_base_values,
        cfg.beta_values,
        cfg.omega_increment_values,
        cfg.gamma_omega_values
    ))
    
    n_combinations = len(param_combinations)
    print(f"\nTotal parameter combinations: {n_combinations}")
    print(f"Parallelization: {cfg.n_cores} cores")
    print(f"Estimated time: ~{n_combinations * cfg.steps_total / (40 * cfg.n_cores):.1f} minutes")
    print("=" * 80)
    
    # Prepare tasks
    tasks = []
    for run_id, (J, beta, omega_inc, gamma) in enumerate(param_combinations):
        tasks.append((J, beta, omega_inc, gamma, cfg, run_id))
    
    print(f"\nLaunching {n_combinations} simulations...")
    start_time = time.time()
    
    # Run in parallel
    with Pool(cfg.n_cores) as pool:
        results = pool.map(run_single_parameter_point, tasks)
    
    elapsed = time.time() - start_time
    print(f"\nAll simulations complete in {elapsed/60:.1f} minutes")
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e30_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Analyze
    best_params = analyze_phase_diagram(results, cfg, output_dir)
    
    # Save full results
    output_data = {
        'config': {
            'L': cfg.L,
            'steps': cfg.steps_total,
            'parameter_ranges': {
                'J_base': cfg.J_base_values,
                'beta': cfg.beta_values,
                'omega_increment': cfg.omega_increment_values,
                'gamma_omega': cfg.gamma_omega_values
            },
            'n_combinations': n_combinations
        },
        'best_parameters': best_params,
        'top_10': sorted(results, key=lambda x: x['pattern_ratio'], reverse=True)[:10],
        'all_results': results  # Full dataset for later analysis
    }
    
    results_file = output_dir / 'e30c_phase_diagram_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Full results saved: {results_file}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    
    if best_params['pattern_ratio'] > 1.5:
        print(f"\n🎉 STRONG PATTERN FORMATION REGIME IDENTIFIED!")
        print(f"   Use these parameters for robust self-organization")
    elif best_params['pattern_ratio'] > 1.1:
        print(f"\n✅ PATTERN FORMATION CONDITIONS FOUND")
        print(f"   Moderate but clear pattern emergence")
    else:
        print(f"\n⚠️  WEAK PATTERNS IN TESTED RANGE")
        print(f"   May need to explore beyond current parameter space")
    
    print(f"\nPattern formation appears to require:")
    
    # Analyze trends
    high_pattern = [r for r in results if r['pattern_ratio'] > 1.2]
    if high_pattern:
        avg_J = np.mean([r['J_base'] for r in high_pattern])
        avg_beta = np.mean([r['beta'] for r in high_pattern])
        avg_omega = np.mean([r['omega_increment'] for r in high_pattern])
        avg_gamma = np.mean([r['gamma_omega'] for r in high_pattern])
        
        print(f"  - Coupling J ≈ {avg_J:.2f}")
        print(f"  - Feedback β ≈ {avg_beta:.1f}")
        print(f"  - Information rate ω_inc ≈ {avg_omega:.1f}")
        print(f"  - Decay rate γ ≈ {avg_gamma:.3f}")
    
    print("\n" + "=" * 80)
    print("E30c COMPLETE — PHASE SPACE MAPPED")
    print("=" * 80)


if __name__ == '__main__':
    main()

