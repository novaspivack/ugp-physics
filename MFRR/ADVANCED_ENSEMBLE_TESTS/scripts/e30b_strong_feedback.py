#!/usr/bin/env python3
"""
E30b: Strong Feedback Regime - Enhanced Pattern Formation
==========================================================

Enhanced version of E30 with stronger parameters to clearly demonstrate
spontaneous pattern formation through information-geometry co-evolution.

Changes from E30:
- Stronger coupling: J_base = 0.25 (vs 0.15)
- Stronger feedback: β = 5.0 (vs 2.0)
- Larger omega increment: 2.0 (vs 1.0)
- Slower decay: γ = 0.02 (vs 0.05)
- Longer evolution: 2000 steps (vs 1000)
- Larger lattice: 80x80 (vs 60x60)

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

from common.ensemble_core import argmin_branch, inter_cost, local_cost


class E30bConfig:
    """Enhanced configuration for strong feedback regime."""
    # LARGER LATTICE
    L = 80                 # 80x80 = 6400 sites
    
    # LONGER EVOLUTION
    steps_total = 2000     # Double the time
    steps_snapshot = 100   # Snapshot interval
    
    # STRONGER COUPLING
    J_base = 0.25          # Higher base coupling
    beta = 5.0             # STRONG Psi modulation (2.5x stronger)
    
    # ENHANCED INFORMATION ACCUMULATION
    omega_increment = 2.0  # Double the increment per flip
    gamma_omega = 0.02     # Slower decay (keep info longer)
    D_omega = 0.15         # Slightly more diffusion
    
    # Coherence field (same as E30)
    kappa = 1.0
    m_squared = 0.05       # Longer correlation length
    
    # ENHANCED CASCADE DYNAMICS
    cascade_interval = 1
    seed_fraction = 0.08   # More seeds
    max_cascade_iter = 150  # Longer propagation
    
    seed = 48


def init_lattice(L, rng):
    """Initialize 2D lattice."""
    b = rng.integers(0, 2, size=(L, L))
    psi_field = np.zeros((L, L))
    omega = np.zeros((L, L))
    bias = rng.uniform(0.0, 1.0, size=(L, L))
    kappa = rng.uniform(0.1, 1.0, size=(L, L))
    return b, psi_field, omega, bias, kappa


def get_neighbors(i, j, L):
    """4-connected neighbors with periodic boundaries."""
    return [
        ((i-1) % L, j),
        ((i+1) % L, j),
        (i, (j-1) % L),
        (i, (j+1) % L)
    ]


def lattice_cascade(b, psi_field, omega, bias, kappa, J_coupling, L, 
                   seed_fraction, max_iter, rng, omega_increment):
    """Cascade on 2D lattice with omega accumulation."""
    seed_mask = rng.random((L, L)) < seed_fraction
    queue = list(zip(*np.where(seed_mask)))
    visited = set()
    flipped = []
    
    iterations = 0
    while queue and iterations < max_iter:
        iterations += 1
        if len(queue) == 0:
            break
        
        i, j = queue.pop(0)
        
        if (i, j) in visited:
            continue
        visited.add((i, j))
        
        neighbors = get_neighbors(i, j, L)
        
        cost_0 = local_cost(0, psi_field[i, j], bias[i, j], kappa[i, j])
        cost_1 = local_cost(1, psi_field[i, j], bias[i, j], kappa[i, j])
        
        for ni, nj in neighbors:
            J_val = J_coupling[i, j]
            cost_0 += J_val * inter_cost(0, b[ni, nj])
            cost_1 += J_val * inter_cost(1, b[ni, nj])
        
        new_val = 0 if cost_0 <= cost_1 else 1
        
        if new_val != b[i, j]:
            b[i, j] = new_val
            flipped.append((i, j))
            omega[i, j] += omega_increment  # Enhanced accumulation
            
            for ni, nj in neighbors:
                if (ni, nj) not in visited:
                    queue.append((ni, nj))
    
    return len(flipped), flipped


def update_omega_diffusion(omega, D, gamma, dt=1.0):
    """Diffusion-decay: ∂ω/∂t = D∇²ω - γω"""
    laplacian_kernel = np.array([[0, 1, 0],
                                  [1, -4, 1],
                                  [0, 1, 0]])
    laplacian = convolve(omega, laplacian_kernel, mode='wrap')
    omega_new = omega + dt * (D * laplacian - gamma * omega)
    omega_new = np.maximum(omega_new, 0.0)
    return omega_new


def solve_psi_fft(omega, kappa, m_squared):
    """Solve (-Δ + m²)Ψ = κω via FFT."""
    L = omega.shape[0]
    omega_k = np.fft.fft2(omega)
    
    kx = 2 * np.pi * np.fft.fftfreq(L)
    ky = 2 * np.pi * np.fft.fftfreq(L)
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    k_squared = KX**2 + KY**2
    
    denominator = k_squared + m_squared
    denominator[0, 0] = 1.0
    
    psi_k = kappa * omega_k / denominator
    psi_k[0, 0] = 0.0
    
    psi = np.fft.ifft2(psi_k).real
    return psi


def compute_coupling_matrix(J_base, psi, beta, L):
    """J_ij = J_0(1 + β Ψ_ij) with stronger modulation."""
    J_coupling = np.zeros((L, L))
    
    for i in range(L):
        for j in range(L):
            neighbors = get_neighbors(i, j, L)
            psi_avg = (psi[i, j] + np.mean([psi[ni, nj] for ni, nj in neighbors])) / 2
            J_coupling[i, j] = J_base * (1.0 + beta * psi_avg)
    
    # Allow wider range with strong feedback
    J_coupling = np.clip(J_coupling, J_base * 0.2, J_base * 5.0)
    return J_coupling


def run_coevolution_strong(cfg):
    """Run co-evolution with strong feedback."""
    rng = default_rng(cfg.seed)
    L = cfg.L
    
    print(f"Initializing {L}x{L} lattice ({L**2} sites)...")
    b, psi, omega, bias, kappa = init_lattice(L, rng)
    
    snapshots = []
    cascade_sizes = []
    omega_means = []
    omega_maxs = []
    psi_means = []
    psi_stds = []
    psi_maxs = []
    J_means = []
    
    print(f"\nRunning STRONG feedback co-evolution for {cfg.steps_total} steps...")
    print(f"Parameters: J_base={cfg.J_base}, β={cfg.beta}, ω_inc={cfg.omega_increment}")
    
    start_time = time.time()
    
    for step in range(cfg.steps_total):
        if step % 100 == 0:
            elapsed = time.time() - start_time
            rate = (step+1) / elapsed if elapsed > 0 else 0
            print(f"  Step {step}/{cfg.steps_total} ({rate:.1f} steps/s) "
                  f"| ⟨Ψ⟩={np.mean(psi):.3f}, σ(Ψ)={np.std(psi):.3f}, "
                  f"⟨ω⟩={np.mean(omega):.3f}", flush=True)
        
        # 1. Update omega
        omega = update_omega_diffusion(omega, cfg.D_omega, cfg.gamma_omega, dt=1.0)
        
        # 2. Solve for Psi
        psi = solve_psi_fft(omega, cfg.kappa, cfg.m_squared)
        
        # 3. Modulated coupling
        J_coupling = compute_coupling_matrix(cfg.J_base, psi, cfg.beta, L)
        
        # 4. Cascade
        if step % cfg.cascade_interval == 0:
            n_flips, flipped = lattice_cascade(
                b, psi, omega, bias, kappa, J_coupling, L,
                cfg.seed_fraction, cfg.max_cascade_iter, rng,
                cfg.omega_increment
            )
            cascade_sizes.append(n_flips)
        
        # 5. Statistics
        omega_means.append(np.mean(omega))
        omega_maxs.append(np.max(omega))
        psi_means.append(np.mean(psi))
        psi_stds.append(np.std(psi))
        psi_maxs.append(np.max(np.abs(psi)))
        J_means.append(np.mean(J_coupling))
        
        # 6. Snapshots
        if step % cfg.steps_snapshot == 0 or step == cfg.steps_total - 1:
            snapshots.append({
                'step': step,
                'b': b.copy(),
                'psi': psi.copy(),
                'omega': omega.copy(),
                'J_coupling': J_coupling.copy()
            })
    
    total_time = time.time() - start_time
    print(f"\nSimulation complete in {total_time:.1f}s")
    
    return {
        'snapshots': snapshots,
        'cascade_sizes': cascade_sizes,
        'omega_means': omega_means,
        'omega_maxs': omega_maxs,
        'psi_means': psi_means,
        'psi_stds': psi_stds,
        'psi_maxs': psi_maxs,
        'J_means': J_means
    }


def analyze_strong_feedback(results, cfg, output_dir):
    """Analyze pattern formation with strong feedback."""
    print("\n" + "=" * 80)
    print("STRONG FEEDBACK PATTERN ANALYSIS")
    print("=" * 80)
    
    snapshots = results['snapshots']
    final = snapshots[-1]
    
    psi_final = final['psi']
    omega_final = final['omega']
    J_final = final['J_coupling']
    
    # Domain identification
    psi_threshold = np.mean(psi_final) + 0.5 * np.std(psi_final)
    high_psi_mask = psi_final > psi_threshold
    domain_fraction = np.sum(high_psi_mask) / psi_final.size
    
    # Cascade activity in high vs low Psi regions
    cascade_sizes = results['cascade_sizes']
    
    print(f"\nFinal state (step {final['step']}):")
    print(f"  Mean Ψ: {np.mean(psi_final):.4f}")
    print(f"  Std Ψ: {np.std(psi_final):.4f}")
    print(f"  Max |Ψ|: {np.max(np.abs(psi_final)):.4f}")
    print(f"  High-Ψ domain fraction: {100*domain_fraction:.1f}%")
    print(f"\n  Mean ω: {np.mean(omega_final):.4f}")
    print(f"  Max ω: {np.max(omega_final):.4f}")
    print(f"\n  Mean J: {np.mean(J_final):.4f}")
    print(f"  J range: [{np.min(J_final):.4f}, {np.max(J_final):.4f}]")
    print(f"\n  Total cascades: {len(cascade_sizes)}")
    print(f"  Mean cascade size: {np.mean(cascade_sizes):.1f}")
    print(f"  Max cascade: {np.max(cascade_sizes)}")
    
    # Pattern formation metric
    psi_stds = np.array(results['psi_stds'])
    if len(psi_stds) > 200:
        early_std = np.mean(psi_stds[:200])
        late_std = np.mean(psi_stds[-200:])
        std_ratio = late_std / early_std if early_std > 0 else 1.0
        
        print(f"\nPattern formation:")
        print(f"  Early std(Ψ): {early_std:.4f}")
        print(f"  Late std(Ψ): {late_std:.4f}")
        print(f"  Ratio: {std_ratio:.2f}x")
        
        if std_ratio > 2.0:
            print(f"\n🎉 STRONG PATTERN FORMATION (>{std_ratio:.1f}x growth)")
        elif std_ratio > 1.5:
            print(f"\n✅ CLEAR PATTERN FORMATION ({std_ratio:.1f}x growth)")
        elif std_ratio > 1.2:
            print(f"\n✅ MODERATE PATTERNS ({std_ratio:.1f}x growth)")
        else:
            print(f"\n⚠️  Weak patterns ({std_ratio:.1f}x)")
    else:
        std_ratio = 1.0
    
    # Visualization
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(4, 4, hspace=0.35, wspace=0.3)
    
    # Row 1: Final spatial fields
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(psi_final, cmap='RdBu_r', origin='lower', 
                     vmin=-np.max(np.abs(psi_final)), vmax=np.max(np.abs(psi_final)))
    ax1.set_title(f'Coherence Field Ψ\nMax |Ψ|={np.max(np.abs(psi_final)):.3f}', fontsize=11)
    plt.colorbar(im1, ax=ax1, fraction=0.046)
    
    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(omega_final, cmap='hot', origin='lower')
    ax2.set_title(f'Information Density ω\nMax ω={np.max(omega_final):.3f}', fontsize=11)
    plt.colorbar(im2, ax=ax2, fraction=0.046)
    
    ax3 = fig.add_subplot(gs[0, 2])
    im3 = ax3.imshow(J_final, cmap='plasma', origin='lower')
    ax3.set_title(f'Coupling J(Ψ)\nRange [{np.min(J_final):.2f}, {np.max(J_final):.2f}]', fontsize=11)
    plt.colorbar(im3, ax=ax3, fraction=0.046)
    
    ax4 = fig.add_subplot(gs[0, 3])
    im4 = ax4.imshow(high_psi_mask.astype(float), cmap='binary', origin='lower')
    ax4.set_title(f'High-Ψ Domains\n{100*domain_fraction:.1f}% coverage', fontsize=11)
    
    # Row 2: Evolution of field statistics
    steps = np.arange(len(results['psi_stds']))
    
    ax5 = fig.add_subplot(gs[1, :2])
    ax5.plot(steps, results['psi_stds'], 'b-', linewidth=2, label='std(Ψ)')
    ax5.plot(steps, results['psi_maxs'], 'r-', linewidth=1.5, alpha=0.7, label='max|Ψ|')
    ax5.set_xlabel('Step', fontsize=11)
    ax5.set_ylabel('Ψ statistics', fontsize=11)
    ax5.set_title('Coherence Field Growth', fontsize=12)
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3)
    
    ax6 = fig.add_subplot(gs[1, 2:])
    ax6.plot(steps, results['omega_means'], 'g-', linewidth=2, label='mean ω')
    ax6.plot(steps, results['omega_maxs'], 'm-', linewidth=1.5, alpha=0.7, label='max ω')
    ax6.set_xlabel('Step', fontsize=11)
    ax6.set_ylabel('ω', fontsize=11)
    ax6.set_title('Information Accumulation', fontsize=12)
    ax6.legend(fontsize=10)
    ax6.grid(True, alpha=0.3)
    
    # Row 3: Cascade activity and coupling evolution
    ax7 = fig.add_subplot(gs[2, :2])
    cascade_steps = np.arange(len(cascade_sizes)) * cfg.cascade_interval
    ax7.plot(cascade_steps, cascade_sizes, 'o-', markersize=2, linewidth=0.8, 
            color='darkgreen', alpha=0.6)
    ax7.set_xlabel('Step', fontsize=11)
    ax7.set_ylabel('Cascade Size', fontsize=11)
    ax7.set_title(f'Adjudication Activity (mean={np.mean(cascade_sizes):.1f})', fontsize=12)
    ax7.grid(True, alpha=0.3)
    
    ax8 = fig.add_subplot(gs[2, 2:])
    ax8.plot(steps, results['J_means'], 'purple', linewidth=2)
    ax8.axhline(cfg.J_base, color='black', linestyle='--', linewidth=1.5, 
               alpha=0.5, label=f'J_base={cfg.J_base}')
    ax8.set_xlabel('Step', fontsize=11)
    ax8.set_ylabel('Mean J', fontsize=11)
    ax8.set_title('Coupling Amplification', fontsize=12)
    ax8.legend(fontsize=10)
    ax8.grid(True, alpha=0.3)
    
    # Row 4: Distributions and correlations
    ax9 = fig.add_subplot(gs[3, 0])
    ax9.hist(psi_final.flatten(), bins=60, alpha=0.7, color='blue', edgecolor='black')
    ax9.axvline(psi_threshold, color='red', linestyle='--', linewidth=2, label='Threshold')
    ax9.set_xlabel('Ψ', fontsize=11)
    ax9.set_ylabel('Frequency', fontsize=11)
    ax9.set_title('Ψ Distribution', fontsize=12)
    ax9.legend(fontsize=9)
    
    ax10 = fig.add_subplot(gs[3, 1])
    ax10.hist(omega_final.flatten(), bins=60, alpha=0.7, color='orange', edgecolor='black')
    ax10.set_xlabel('ω', fontsize=11)
    ax10.set_ylabel('Frequency', fontsize=11)
    ax10.set_title('ω Distribution', fontsize=12)
    
    ax11 = fig.add_subplot(gs[3, 2])
    scatter = ax11.scatter(omega_final.flatten(), psi_final.flatten(), 
                          alpha=0.3, s=1, c='green')
    ax11.set_xlabel('ω', fontsize=11)
    ax11.set_ylabel('Ψ', fontsize=11)
    ax11.set_title('ω-Ψ Correlation', fontsize=12)
    ax11.grid(True, alpha=0.3)
    
    ax12 = fig.add_subplot(gs[3, 3])
    ax12.text(0.1, 0.9, f"Strong Feedback Results", fontsize=14, weight='bold',
             transform=ax12.transAxes, va='top')
    ax12.text(0.1, 0.75, f"Lattice: {cfg.L}×{cfg.L}", fontsize=10,
             transform=ax12.transAxes)
    ax12.text(0.1, 0.68, f"β = {cfg.beta}", fontsize=10,
             transform=ax12.transAxes)
    ax12.text(0.1, 0.61, f"Pattern ratio: {std_ratio:.2f}×", fontsize=10,
             transform=ax12.transAxes, weight='bold',
             color='green' if std_ratio > 1.5 else 'orange')
    ax12.text(0.1, 0.54, f"Domain coverage: {100*domain_fraction:.1f}%", fontsize=10,
             transform=ax12.transAxes)
    ax12.text(0.1, 0.47, f"Mean cascade: {np.mean(cascade_sizes):.1f}", fontsize=10,
             transform=ax12.transAxes)
    ax12.text(0.1, 0.40, f"J amplification: {np.mean(results['J_means'])/cfg.J_base:.2f}×", 
             fontsize=10, transform=ax12.transAxes)
    ax12.axis('off')
    
    fig_path = output_dir / 'e30b_strong_feedback.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return {
        'domain_fraction': float(domain_fraction),
        'final_psi_std': float(np.std(psi_final)),
        'final_psi_max': float(np.max(np.abs(psi_final))),
        'final_omega_mean': float(np.mean(omega_final)),
        'final_omega_max': float(np.max(omega_final)),
        'mean_cascade_size': float(np.mean(cascade_sizes)),
        'max_cascade_size': int(np.max(cascade_sizes)),
        'pattern_ratio': float(std_ratio),
        'J_amplification': float(np.mean(results['J_means']) / cfg.J_base)
    }


def main():
    """Run E30b: Strong feedback regime."""
    cfg = E30bConfig()
    
    print("=" * 80)
    print("E30b: STRONG FEEDBACK REGIME — ENHANCED PATTERN FORMATION")
    print("=" * 80)
    print(f"Lattice: {cfg.L}×{cfg.L} = {cfg.L**2} sites")
    print(f"Evolution: {cfg.steps_total} steps")
    print(f"STRONG parameters:")
    print(f"  J_base = {cfg.J_base} (vs 0.15)")
    print(f"  β = {cfg.beta} (vs 2.0)")
    print(f"  ω_increment = {cfg.omega_increment} (vs 1.0)")
    print(f"  γ = {cfg.gamma_omega} (vs 0.05)")
    print("=" * 80)
    print("\n🎯 TARGET: Clear spontaneous pattern formation")
    print("=" * 80)
    
    results = run_coevolution_strong(cfg)
    
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e30_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analysis = analyze_strong_feedback(results, cfg, output_dir)
    
    print("\n" + "=" * 80)
    print("COMPARISON: E30 (weak) vs E30b (strong)")
    print("=" * 80)
    
    print("\nE30 (weak feedback):")
    print("  Pattern ratio: 0.12× (decay)")
    print("  Mean cascade: 2.3")
    print("  Domain coverage: 13.2%")
    
    print(f"\nE30b (STRONG feedback):")
    print(f"  Pattern ratio: {analysis['pattern_ratio']:.2f}× ({'GROWTH' if analysis['pattern_ratio'] > 1 else 'decay'})")
    print(f"  Mean cascade: {analysis['mean_cascade_size']:.1f}")
    print(f"  Domain coverage: {100*analysis['domain_fraction']:.1f}%")
    print(f"  Max |Ψ|: {analysis['final_psi_max']:.3f}")
    print(f"  J amplification: {analysis['J_amplification']:.2f}×")
    
    if analysis['pattern_ratio'] > 1.5:
        print("\n🎉 SUCCESS: Strong patterns emerged through positive feedback!")
    elif analysis['pattern_ratio'] > 1.1:
        print("\n✅ CONFIRMED: Pattern formation observed")
    else:
        print("\n⚠️  Weak patterns (may need even stronger parameters)")
    
    output_data = {
        'config': {
            'L': cfg.L,
            'steps': cfg.steps_total,
            'J_base': cfg.J_base,
            'beta': cfg.beta,
            'omega_increment': cfg.omega_increment,
            'gamma_omega': cfg.gamma_omega
        },
        'analysis': analysis
    }
    
    results_file = output_dir / 'e30b_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    print("\n" + "=" * 80)
    print("E30b COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

