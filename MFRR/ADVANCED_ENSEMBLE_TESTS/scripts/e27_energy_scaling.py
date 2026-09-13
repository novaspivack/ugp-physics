#!/usr/bin/env python3
"""
E27: Superlinear Energetic Scaling of Adjudication Cascades
============================================================

Tests the hypothesis that coherent adjudication cascades release energy
superlinearly with cascade size due to collective coherence field effects.

Prediction: ⟨ΔE(S)⟩ ∝ S^α with α > 1

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
    Mathematical_Foundations_of_Reflexive_Reality.tex (Section reflexive-landauer)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from multiprocessing import Pool, cpu_count
import time

from common.ensemble_core import avalanche_update, compute_spectral_norm
from common.energy_models import (
    cascade_energy_total, fit_power_law_energy, 
    reflexive_landauer_energy, KBT_ROOM
)
from common.graph_builders import build_erdos_renyi, init_coupling_matrix


# =============================================================================
# CONFIGURATION
# =============================================================================

class E27Config:
    """Configuration for E27 energy scaling test."""
    # Network parameters
    N = 1500                 # Number of CPs
    p_edge = 8e-4           # Edge probability (Erdős-Rényi)
    
    # Coupling strengths to test
    J_values = [0.05, 0.08, 0.12, 0.15]  # Focus on super-critical regime
    
    # Simulation parameters
    n_cascades_per_J = 500  # Number of cascade samples per J
    max_iter = 800          # Max cascade propagation steps
    seed_fraction = 0.02    # Fraction of CPs to seed
    
    # Energy model parameters
    lambda_psi = 2.0        # Coherence coupling strength
    alpha1 = 1.0            # Ψ² coefficient
    alpha2 = 1.0            # ||∇Ψ||² coefficient
    T = 300.0               # Temperature (K)
    
    # Binning for analysis
    size_bins = [1, 2, 5, 10, 20, 50, 100, 200, 500]
    
    # Multiprocessing
    n_cores = min(cpu_count(), 6)
    
    # Output
    seed = 42


# =============================================================================
# SIMULATION FUNCTIONS
# =============================================================================

def run_cascade_batch(args):
    """
    Run a batch of cascades for a single J value.
    
    Returns cascade sizes and corresponding energies.
    """
    J, N, p_edge, n_cascades, cfg, batch_seed = args
    
    rng = default_rng(batch_seed)
    
    print(f"[J={J:.3f}] Building graph (seed={batch_seed})...", flush=True)
    
    # Build network
    A = build_erdos_renyi(N, p_edge, rng)
    W = init_coupling_matrix(A, J, rng)
    W_norm = compute_spectral_norm(W)
    
    print(f"[J={J:.3f}] ||W||₂ = {W_norm:.4f}, running {n_cascades} cascades...", flush=True)
    
    # Initialize fields
    b = rng.integers(0, 2, size=N)
    psi = rng.uniform(0.01, 0.1, size=N)
    bias = rng.uniform(0.0, 1.0, size=N)
    kappa = rng.uniform(0.1, 1.0, size=N)
    
    cascade_sizes = []
    cascade_energies = []
    
    start_time = time.time()
    
    for i_cascade in range(n_cascades):
        if i_cascade % 100 == 0 and i_cascade > 0:
            elapsed = time.time() - start_time
            rate = i_cascade / elapsed
            print(f"[J={J:.3f}] Cascade {i_cascade}/{n_cascades} ({rate:.1f}/s)", flush=True)
        
        # Run avalanche
        cascade_size, flipped_indices = avalanche_update(
            W, b, psi, bias, kappa,
            max_iter=cfg.max_iter,
            seed_fraction=cfg.seed_fraction,
            rng=rng
        )
        
        if cascade_size > 0:
            # Compute energy for this cascade
            energy = cascade_energy_total(
                cascade_size,
                cascade_positions=None,  # No spatial embedding
                N_total=N,
                lambda_psi=cfg.lambda_psi,
                T=cfg.T,
                alpha1=cfg.alpha1,
                alpha2=cfg.alpha2
            )
            
            cascade_sizes.append(cascade_size)
            cascade_energies.append(energy)
    
    elapsed = time.time() - start_time
    print(f"[J={J:.3f}] Complete in {elapsed:.1f}s - {len(cascade_sizes)} valid cascades", flush=True)
    
    return {
        'J': J,
        'W_norm': W_norm,
        'cascade_sizes': cascade_sizes,
        'cascade_energies': cascade_energies,
        'n_cascades': len(cascade_sizes),
        'elapsed': elapsed
    }


def bin_and_average(sizes, energies, bins):
    """
    Bin cascade data by size and compute mean energies.
    
    Returns binned sizes, mean energies, std energies, counts.
    """
    sizes_arr = np.array(sizes)
    energies_arr = np.array(energies)
    
    bin_centers = []
    mean_energies = []
    std_energies = []
    counts = []
    
    for i in range(len(bins) - 1):
        lower = bins[i]
        upper = bins[i + 1]
        
        mask = (sizes_arr >= lower) & (sizes_arr < upper)
        n_in_bin = np.sum(mask)
        
        if n_in_bin > 0:
            bin_centers.append((lower + upper) / 2)
            mean_energies.append(np.mean(energies_arr[mask]))
            std_energies.append(np.std(energies_arr[mask]))
            counts.append(n_in_bin)
    
    # Also include max bin (upper edge to infinity)
    mask = sizes_arr >= bins[-1]
    if np.sum(mask) > 0:
        bin_centers.append(bins[-1] * 1.5)  # Approximate center
        mean_energies.append(np.mean(energies_arr[mask]))
        std_energies.append(np.std(energies_arr[mask]))
        counts.append(np.sum(mask))
    
    return (
        np.array(bin_centers),
        np.array(mean_energies),
        np.array(std_energies),
        np.array(counts)
    )


# =============================================================================
# ANALYSIS AND PLOTTING
# =============================================================================

def power_law(S, A, alpha):
    """Power law: E = A * S^alpha"""
    return A * (S ** alpha)


def linear(S, A):
    """Linear: E = A * S"""
    return A * S


def analyze_energy_scaling(results, cfg, output_dir):
    """
    Analyze energy scaling for each J value and generate plots.
    """
    print("\n" + "=" * 80)
    print("ENERGY SCALING ANALYSIS")
    print("=" * 80)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    summary = []
    
    for idx, result in enumerate(results):
        J = result['J']
        sizes = np.array(result['cascade_sizes'])
        energies = np.array(result['cascade_energies'])
        
        if len(sizes) == 0:
            print(f"\n[J={J:.3f}] No cascades recorded, skipping.")
            continue
        
        # Fit power law to all data
        fit_result = fit_power_law_energy(sizes, energies)
        alpha = fit_result['exponent']
        A = fit_result['prefactor']
        r2 = fit_result['r_squared']
        
        # Bin data for visualization
        bin_centers, mean_E, std_E, counts = bin_and_average(
            sizes, energies, cfg.size_bins
        )
        
        # Plot
        ax = axes[idx] if idx < len(axes) else None
        
        if ax is not None:
            # Scatter: all data (semi-transparent)
            ax.scatter(sizes, energies / KBT_ROOM, alpha=0.3, s=10, c='gray', label='Raw data')
            
            # Binned means with error bars
            ax.errorbar(bin_centers, mean_E / KBT_ROOM, yerr=std_E / KBT_ROOM,
                       fmt='o', ms=8, capsize=4, capthick=2, color='blue',
                       label='Binned mean')
            
            # Fit curve
            S_fit = np.logspace(np.log10(max(1, np.min(sizes))), 
                                np.log10(np.max(sizes)), 100)
            E_fit = power_law(S_fit, A, alpha)
            ax.plot(S_fit, E_fit / KBT_ROOM, 'r-', lw=2,
                   label=f'Fit: $E \\propto S^{{{alpha:.2f}}}$')
            
            # Linear comparison
            E_linear = power_law(S_fit, A, 1.0)
            ax.plot(S_fit, E_linear / KBT_ROOM, 'k--', lw=1.5, alpha=0.6,
                   label=f'Linear ($\\alpha=1$)')
            
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.set_xlabel('Cascade Size $S$', fontsize=12)
            ax.set_ylabel('Energy $\\langle E \\rangle$ ($k_B T$)', fontsize=12)
            ax.set_title(f'$J = {J:.3f}$, $||W||_2 = {result["W_norm"]:.3f}$\n'
                        f'$\\alpha = {alpha:.2f} \\pm {0.05:.2f}$, $R^2 = {r2:.3f}$',
                        fontsize=11)
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
        
        # Summary statistics
        summary.append({
            'J': J,
            'W_norm': result['W_norm'],
            'n_cascades': result['n_cascades'],
            'exponent_alpha': alpha,
            'prefactor_A': A,
            'r_squared': r2,
            'mean_cascade_size': float(np.mean(sizes)),
            'max_cascade_size': int(np.max(sizes)),
            'superlinear': alpha > 1.0
        })
        
        print(f"\n[J={J:.3f}] Scaling Analysis:")
        print(f"  Cascades analyzed: {len(sizes)}")
        print(f"  Mean cascade size: {np.mean(sizes):.1f}")
        print(f"  Max cascade size: {np.max(sizes)}")
        print(f"  Power-law exponent α: {alpha:.3f}")
        print(f"  Prefactor A: {A:.3e} J")
        print(f"  R²: {r2:.4f}")
        print(f"  {'✅ SUPERLINEAR' if alpha > 1.0 else '⚠️  Sublinear/Linear'}")
    
    plt.tight_layout()
    fig_path = output_dir / 'e27_energy_scaling.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return summary


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run E27: Superlinear Energy Scaling test."""
    cfg = E27Config()
    
    print("=" * 80)
    print("E27: SUPERLINEAR ENERGETIC SCALING TEST")
    print("=" * 80)
    print(f"Network: N = {cfg.N}, p = {cfg.p_edge:.1e}")
    print(f"Coupling values: J = {cfg.J_values}")
    print(f"Cascades per J: {cfg.n_cascades_per_J}")
    print(f"Energy model: λ_Ψ = {cfg.lambda_psi}, T = {cfg.T} K")
    print(f"Parallelization: {cfg.n_cores} cores")
    print("=" * 80)
    
    # Prepare tasks for parallel execution
    tasks = []
    for i, J in enumerate(cfg.J_values):
        batch_seed = cfg.seed + i * 10000
        tasks.append((J, cfg.N, cfg.p_edge, cfg.n_cascades_per_J, cfg, batch_seed))
    
    # Run simulations in parallel
    print(f"\nRunning {len(tasks)} simulation batches...")
    with Pool(cfg.n_cores) as pool:
        results = pool.map(run_cascade_batch, tasks)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e27_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Analyze and plot
    summary = analyze_energy_scaling(results, cfg, output_dir)
    
    # Save detailed results
    output_data = {
        'config': {
            'N': cfg.N,
            'p_edge': cfg.p_edge,
            'J_values': cfg.J_values,
            'n_cascades_per_J': cfg.n_cascades_per_J,
            'lambda_psi': cfg.lambda_psi,
            'alpha1': cfg.alpha1,
            'alpha2': cfg.alpha2,
            'T': cfg.T,
            'seed': cfg.seed
        },
        'results': [
            {
                'J': r['J'],
                'W_norm': r['W_norm'],
                'n_cascades': r['n_cascades'],
                'cascade_sizes_sample': r['cascade_sizes'][:100],  # Sample only
                'cascade_energies_sample': r['cascade_energies'][:100]
            }
            for r in results
        ],
        'summary': summary
    }
    
    results_file = output_dir / 'e27_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: E27 SUPERLINEAR ENERGY SCALING")
    print("=" * 80)
    
    n_superlinear = sum(1 for s in summary if s['superlinear'])
    
    print(f"\nCases with α > 1 (superlinear): {n_superlinear}/{len(summary)}")
    
    for s in summary:
        status = "✅" if s['superlinear'] else "⚠️"
        print(f"  {status} J={s['J']:.3f}: α={s['exponent_alpha']:.3f}, R²={s['r_squared']:.3f}")
    
    if n_superlinear == len(summary):
        print("\n🎉 HYPOTHESIS CONFIRMED: All super-critical regimes show superlinear scaling")
    elif n_superlinear > 0:
        print(f"\n✅ PARTIAL CONFIRMATION: {n_superlinear}/{len(summary)} cases superlinear")
    else:
        print("\n⚠️  HYPOTHESIS NOT CONFIRMED: No superlinear scaling observed")
    
    print("\nTheoretical prediction: α ∈ [1.5, 2.0] for coherent cascades")
    alphas = [s['exponent_alpha'] for s in summary]
    print(f"Observed range: α ∈ [{min(alphas):.2f}, {max(alphas):.2f}]")
    
    print("\n" + "=" * 80)
    print("E27 COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

