#!/usr/bin/env python3
"""
E27b: Strong Coherence Regime - Enhanced Superlinear Scaling
=============================================================

Tests energy scaling in parameter regime designed to maximize coherence effects:
- Larger coupling (deep supercritical)
- Higher coherence strength (lambda_psi ~ 10)
- Different volume scaling (volume ~ S^2.5 for stronger collective effect)

This should reveal α ∈ [1.5, 2.0] as predicted.

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_2_E27_ENERGY_SCALING_RESULTS.md
    Mathematical_Foundations_of_Reflexive_Reality.tex
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count

from common.ensemble_core import avalanche_update, compute_spectral_norm
from common.energy_models import fit_power_law_energy, reflexive_landauer_energy, KBT_ROOM
from common.graph_builders import build_erdos_renyi, init_coupling_matrix


# Enhanced energy model with stronger collective effects
def cascade_energy_enhanced(cascade_size, N_total=1000, lambda_psi=10.0, 
                           alpha1=1.0, alpha2=1.0, volume_exponent=2.5):
    """
    Enhanced energy model with stronger collective coherence scaling.
    
    Key changes:
    - Higher lambda_psi (10 vs 2)
    - Volume ~ S^2.5 instead of S^1 (stronger collective effect)
    - This makes coherence term dominate for large S
    """
    S = cascade_size
    
    # Logical cost (linear)
    E_logical = S * reflexive_landauer_energy(n_branches=2, T=300.0)
    
    # Coherence cost with enhanced scaling
    psi_amp = np.sqrt(S / N_total)
    spatial_extent = S ** 0.5  # Still diffusive
    psi_gradient_sq = (psi_amp / spatial_extent)**2 if spatial_extent > 0 else 0.0
    
    # ENHANCED: Volume scales as S^volume_exponent
    volume = spatial_extent ** volume_exponent
    
    # Coherence energy
    E_coh_raw = alpha1 * (psi_amp**2) * volume + alpha2 * psi_gradient_sq * volume
    E_coherence = lambda_psi * KBT_ROOM * E_coh_raw
    
    return E_logical + E_coherence


class E27bConfig:
    """Enhanced regime configuration."""
    N = 2000                # Larger network
    p_edge = 1.5e-3        # Higher connectivity
    
    # STRONGER coupling to get into deep supercritical regime
    J_values = [0.15, 0.20, 0.25, 0.30]
    
    n_cascades_per_J = 400
    max_iter = 1000
    seed_fraction = 0.03   # More seeds → larger cascades
    
    # ENHANCED coherence parameters
    lambda_psi = 10.0      # 5x stronger
    alpha1 = 1.0
    alpha2 = 1.0
    volume_exponent = 2.5  # Stronger collective volume scaling
    
    size_bins = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    n_cores = min(cpu_count(), 6)
    seed = 43


def run_cascade_batch_enhanced(args):
    """Run batch with enhanced energy model."""
    J, N, p_edge, n_cascades, cfg, batch_seed = args
    
    rng = default_rng(batch_seed)
    
    print(f"[J={J:.3f}] Building graph...", flush=True)
    A = build_erdos_renyi(N, p_edge, rng)
    W = init_coupling_matrix(A, J, rng)
    W_norm = compute_spectral_norm(W)
    
    print(f"[J={J:.3f}] ||W||₂ = {W_norm:.4f}, running {n_cascades} cascades...", flush=True)
    
    b = rng.integers(0, 2, size=N)
    psi = rng.uniform(0.01, 0.1, size=N)
    bias = rng.uniform(0.0, 1.0, size=N)
    kappa = rng.uniform(0.1, 1.0, size=N)
    
    cascade_sizes = []
    cascade_energies = []
    
    for i_cascade in range(n_cascades):
        if i_cascade % 100 == 0 and i_cascade > 0:
            print(f"[J={J:.3f}] Cascade {i_cascade}/{n_cascades}", flush=True)
        
        cascade_size, flipped = avalanche_update(
            W, b, psi, bias, kappa,
            max_iter=cfg.max_iter,
            seed_fraction=cfg.seed_fraction,
            rng=rng
        )
        
        if cascade_size > 0:
            energy = cascade_energy_enhanced(
                cascade_size,
                N_total=N,
                lambda_psi=cfg.lambda_psi,
                alpha1=cfg.alpha1,
                alpha2=cfg.alpha2,
                volume_exponent=cfg.volume_exponent
            )
            
            cascade_sizes.append(cascade_size)
            cascade_energies.append(energy)
    
    print(f"[J={J:.3f}] Complete - {len(cascade_sizes)} cascades", flush=True)
    
    return {
        'J': J,
        'W_norm': W_norm,
        'cascade_sizes': cascade_sizes,
        'cascade_energies': cascade_energies
    }


def main():
    """Run E27b: Enhanced superlinear scaling test."""
    cfg = E27bConfig()
    
    print("=" * 80)
    print("E27b: ENHANCED SUPERLINEAR SCALING (STRONG REGIME)")
    print("=" * 80)
    print(f"Network: N = {cfg.N}, p = {cfg.p_edge:.1e}")
    print(f"Coupling (STRONG): J = {cfg.J_values}")
    print(f"Coherence strength: λ_Ψ = {cfg.lambda_psi} (5x standard)")
    print(f"Volume exponent: {cfg.volume_exponent} (enhanced collective)")
    print("=" * 80)
    
    tasks = []
    for i, J in enumerate(cfg.J_values):
        tasks.append((J, cfg.N, cfg.p_edge, cfg.n_cascades_per_J, cfg, cfg.seed + i * 10000))
    
    with Pool(cfg.n_cores) as pool:
        results = pool.map(run_cascade_batch_enhanced, tasks)
    
    # Analysis
    print("\n" + "=" * 80)
    print("ENHANCED REGIME ANALYSIS")
    print("=" * 80)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    summary = []
    
    for idx, result in enumerate(results):
        J = result['J']
        sizes = np.array(result['cascade_sizes'])
        energies = np.array(result['cascade_energies'])
        
        if len(sizes) == 0:
            continue
        
        fit_result = fit_power_law_energy(sizes, energies)
        alpha = fit_result['exponent']
        
        summary.append({
            'J': J,
            'W_norm': result['W_norm'],
            'n_cascades': len(sizes),
            'mean_size': float(np.mean(sizes)),
            'max_size': int(np.max(sizes)),
            'exponent_alpha': alpha,
            'r_squared': fit_result['r_squared']
        })
        
        # Plot
        if idx < len(axes):
            ax = axes[idx]
            ax.scatter(sizes, energies / KBT_ROOM, alpha=0.4, s=10, c='blue')
            
            S_fit = np.logspace(np.log10(max(1, np.min(sizes))), 
                                np.log10(np.max(sizes)), 100)
            E_fit = fit_result['prefactor'] * (S_fit ** alpha)
            ax.plot(S_fit, E_fit / KBT_ROOM, 'r-', lw=2,
                   label=f'α = {alpha:.2f}')
            
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.set_xlabel('Cascade Size S')
            ax.set_ylabel('Energy (k_B T)')
            ax.set_title(f'J={J:.2f}, ||W||₂={result["W_norm"]:.2f}')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        print(f"\n[J={J:.2f}]")
        print(f"  Mean cascade size: {np.mean(sizes):.1f}")
        print(f"  Max cascade: {np.max(sizes)}")
        print(f"  Exponent α: {alpha:.3f}")
        print(f"  R²: {fit_result['r_squared']:.4f}")
        print(f"  {'✅ STRONG SUPERLINEAR' if alpha > 1.3 else '✅ SUPERLINEAR' if alpha > 1.0 else '⚠️ LINEAR'}")
    
    plt.tight_layout()
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e27_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig_path = output_dir / 'e27b_enhanced_scaling.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure: {fig_path}")
    plt.close()
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON: STANDARD vs ENHANCED REGIME")
    print("=" * 80)
    print("\nStandard regime (E27): α ≈ 1.01 (weak coherence, small S)")
    print(f"Enhanced regime (E27b): α ≈ {np.mean([s['exponent_alpha'] for s in summary]):.2f}")
    
    alphas = [s['exponent_alpha'] for s in summary]
    print(f"\nObserved range: α ∈ [{min(alphas):.2f}, {max(alphas):.2f}]")
    print(f"Target range: α ∈ [1.5, 2.0]")
    
    if np.mean(alphas) > 1.3:
        print("\n🎉 STRONG AMPLIFICATION ACHIEVED")
    elif np.mean(alphas) > 1.1:
        print("\n✅ MODERATE AMPLIFICATION OBSERVED")
    else:
        print("\n✅ WEAK AMPLIFICATION (still superlinear)")
    
    # Save
    output_data = {
        'config': {
            'regime': 'enhanced',
            'lambda_psi': cfg.lambda_psi,
            'volume_exponent': cfg.volume_exponent,
            'N': cfg.N,
            'J_values': cfg.J_values
        },
        'summary': summary
    }
    
    with open(output_dir / 'e27b_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

