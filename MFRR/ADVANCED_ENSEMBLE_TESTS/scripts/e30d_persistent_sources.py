#!/usr/bin/env python3
"""
E30d: Persistent Information Sources
====================================

Alternative approach: Instead of relying on small transient cascades,
use persistent "information sources" that continuously inject ω at fixed locations.

This tests whether the Ψ-ω-J feedback loop can create patterns when given
sustained information input, analogous to:
- Stars/galaxies as persistent gravitational sources
- Neurons firing persistently
- Active biological processes

If patterns form here but not with transient cascades, it tells us that
self-organization requires SUSTAINED information generation, not just bursts.

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/scripts/e30c_phase_diagram.py
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


class E30dConfig:
    """Persistent sources configuration."""
    L = 60                 # Lattice size
    steps_total = 1500     # Evolution time
    
    # Use BEST parameters from E30c sweep
    J_base = 0.15
    beta = 7.0             # Strong feedback
    omega_increment = 3.0  # High rate (per source per step)
    gamma_omega = 0.05     # Moderate decay
    
    D_omega = 0.15         # Enhanced diffusion
    kappa = 1.0
    m_squared = 0.03       # Longer range
    
    # PERSISTENT SOURCES
    n_sources = 12         # Number of persistent sources
    source_strength = 0.5  # ω injected per source per step
    
    seed = 51


def init_lattice_with_sources(L, n_sources, rng):
    """Initialize with persistent information sources."""
    b = rng.integers(0, 2, size=(L, L))
    psi = np.zeros((L, L))
    omega = np.zeros((L, L))
    
    # Place sources randomly (but fixed for duration)
    source_positions = []
    for _ in range(n_sources):
        i = rng.integers(0, L)
        j = rng.integers(0, L)
        source_positions.append((i, j))
    
    return b, psi, omega, source_positions


def inject_omega_from_sources(omega, sources, strength):
    """Continuously inject omega at source locations."""
    for i, j in sources:
        omega[i, j] += strength
    return omega


def update_omega_diffusion(omega, D, gamma, dt=1.0):
    """Diffusion-decay."""
    laplacian_kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    laplacian = convolve(omega, laplacian_kernel, mode='wrap')
    omega_new = omega + dt * (D * laplacian - gamma * omega)
    return np.maximum(omega_new, 0.0)


def solve_psi_fft(omega, kappa, m_squared):
    """Solve for Psi."""
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
    psi_avg = (psi + np.roll(psi, 1, axis=0) + np.roll(psi, -1, axis=0) +
               np.roll(psi, 1, axis=1) + np.roll(psi, -1, axis=1)) / 5
    
    J_coupling = J_base * (1.0 + beta * psi_avg)
    J_coupling = np.clip(J_coupling, J_base*0.1, J_base*10.0)
    return J_coupling


def run_persistent_sources(cfg):
    """Run co-evolution with persistent sources."""
    rng = default_rng(cfg.seed)
    L = cfg.L
    
    print(f"Initializing {L}×{L} lattice with {cfg.n_sources} persistent sources...")
    b, psi, omega, sources = init_lattice_with_sources(L, cfg.n_sources, rng)
    
    print(f"Source positions: {sources[:5]}... (showing first 5)")
    
    # Storage
    omega_means = []
    omega_stds = []
    omega_maxs = []
    psi_means = []
    psi_stds = []
    psi_maxs = []
    J_means = []
    J_stds = []
    
    snapshots = []
    
    print(f"\nRunning evolution with PERSISTENT sources...")
    print(f"Parameters: J={cfg.J_base}, β={cfg.beta}, γ={cfg.gamma_omega}")
    
    start_time = time.time()
    
    for step in range(cfg.steps_total):
        if step % 100 == 0:
            elapsed = time.time() - start_time
            rate = (step+1) / elapsed if elapsed > 0 else 0
            print(f"  Step {step}/{cfg.steps_total} ({rate:.1f} steps/s) "
                  f"| ⟨ω⟩={np.mean(omega):.3f}, σ(Ψ)={np.std(psi):.3f}, "
                  f"⟨J⟩={np.mean(np.maximum(0, psi)):.3f}", flush=True)
        
        # 1. Inject omega at sources
        omega = inject_omega_from_sources(omega, sources, cfg.source_strength)
        
        # 2. Diffuse and decay
        omega = update_omega_diffusion(omega, cfg.D_omega, cfg.gamma_omega, dt=1.0)
        
        # 3. Solve for Psi
        psi = solve_psi_fft(omega, cfg.kappa, cfg.m_squared)
        
        # 4. Compute modulated coupling
        J_coupling = compute_coupling_matrix(cfg.J_base, psi, cfg.beta, L)
        
        # 5. Statistics
        omega_means.append(np.mean(omega))
        omega_stds.append(np.std(omega))
        omega_maxs.append(np.max(omega))
        psi_means.append(np.mean(psi))
        psi_stds.append(np.std(psi))
        psi_maxs.append(np.max(np.abs(psi)))
        J_means.append(np.mean(J_coupling))
        J_stds.append(np.std(J_coupling))
        
        # 6. Snapshots
        if step % 150 == 0 or step == cfg.steps_total - 1:
            snapshots.append({
                'step': step,
                'psi': psi.copy(),
                'omega': omega.copy(),
                'J_coupling': J_coupling.copy()
            })
    
    total_time = time.time() - start_time
    print(f"\nSimulation complete in {total_time:.1f}s")
    
    return {
        'snapshots': snapshots,
        'sources': sources,
        'omega_means': omega_means,
        'omega_stds': omega_stds,
        'omega_maxs': omega_maxs,
        'psi_means': psi_means,
        'psi_stds': psi_stds,
        'psi_maxs': psi_maxs,
        'J_means': J_means,
        'J_stds': J_stds
    }


def analyze_persistent_patterns(results, cfg, output_dir):
    """Analyze pattern formation with persistent sources."""
    print("\n" + "=" * 80)
    print("PERSISTENT SOURCE PATTERN ANALYSIS")
    print("=" * 80)
    
    snapshots = results['snapshots']
    final = snapshots[-1]
    
    psi_final = final['psi']
    omega_final = final['omega']
    J_final = final['J_coupling']
    
    sources = results['sources']
    
    # Pattern metrics
    psi_stds = np.array(results['psi_stds'])
    omega_stds = np.array(results['omega_stds'])
    
    early_psi = np.mean(psi_stds[:200])
    late_psi = np.mean(psi_stds[-200:])
    pattern_ratio = late_psi / early_psi if early_psi > 1e-10 else 0.0
    
    print(f"\nPattern formation:")
    print(f"  Early std(Ψ): {early_psi:.4f}")
    print(f"  Late std(Ψ): {late_psi:.4f}")
    print(f"  Ratio: {pattern_ratio:.3f}×")
    
    print(f"\nFinal state:")
    print(f"  Mean Ψ: {np.mean(psi_final):.4f}")
    print(f"  Std Ψ: {np.std(psi_final):.4f}")
    print(f"  Max |Ψ|: {np.max(np.abs(psi_final)):.4f}")
    print(f"  Mean ω: {np.mean(omega_final):.4f}")
    print(f"  Max ω: {np.max(omega_final):.4f}")
    print(f"  Mean J: {np.mean(J_final):.4f}")
    print(f"  J range: [{np.min(J_final):.3f}, {np.max(J_final):.3f}]")
    
    # Check if patterns stabilized
    late_window = psi_stds[-300:]
    stability = np.std(late_window) / np.mean(late_window) if np.mean(late_window) > 0 else 999
    
    print(f"\nStability (CV of late std): {stability:.3f}")
    
    if pattern_ratio > 1.5:
        print(f"\n🎉 STRONG PATTERN FORMATION ({pattern_ratio:.1f}× growth)")
    elif pattern_ratio > 1.2:
        print(f"\n✅ CLEAR PATTERNS ({pattern_ratio:.1f}× growth)")
    elif pattern_ratio > 1.0:
        print(f"\n✅ PATTERN EMERGENCE ({pattern_ratio:.1f}× growth)")
    else:
        print(f"\n⚠️  Patterns decay ({pattern_ratio:.1f}×)")
    
    # Visualization
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.3)
    
    # Row 1: Spatial fields
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(psi_final, cmap='RdBu_r', origin='lower')
    # Mark sources
    for i, j in sources:
        ax1.plot(j, i, 'y*', markersize=10, markeredgecolor='black', markeredgewidth=0.5)
    ax1.set_title(f'Coherence Field Ψ\n(yellow stars = sources)', fontsize=11)
    plt.colorbar(im1, ax=ax1, fraction=0.046)
    
    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(omega_final, cmap='hot', origin='lower')
    for i, j in sources:
        ax2.plot(j, i, 'c*', markersize=10, markeredgecolor='black', markeredgewidth=0.5)
    ax2.set_title('Information Density ω', fontsize=11)
    plt.colorbar(im2, ax=ax2, fraction=0.046)
    
    ax3 = fig.add_subplot(gs[0, 2])
    im3 = ax3.imshow(J_final, cmap='plasma', origin='lower')
    ax3.set_title('Coupling J(Ψ)', fontsize=11)
    plt.colorbar(im3, ax=ax3, fraction=0.046)
    
    ax4 = fig.add_subplot(gs[0, 3])
    # Psi gradient magnitude
    psi_grad = np.sqrt(np.gradient(psi_final, axis=0)**2 + 
                       np.gradient(psi_final, axis=1)**2)
    im4 = ax4.imshow(psi_grad, cmap='viridis', origin='lower')
    ax4.set_title('|∇Ψ| (field gradients)', fontsize=11)
    plt.colorbar(im4, ax=ax4, fraction=0.046)
    
    # Row 2: Time evolution
    steps = np.arange(len(psi_stds))
    
    ax5 = fig.add_subplot(gs[1, :2])
    ax5.plot(steps, psi_stds, 'b-', linewidth=2, label='std(Ψ)')
    ax5.plot(steps, results['psi_maxs'], 'r-', linewidth=1.5, alpha=0.7, label='max|Ψ|')
    ax5.set_xlabel('Step', fontsize=11)
    ax5.set_ylabel('Ψ statistics', fontsize=11)
    ax5.set_title(f'Coherence Growth (ratio={pattern_ratio:.2f}×)', fontsize=12)
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
    
    # Row 3: Coupling and distributions
    ax7 = fig.add_subplot(gs[2, :2])
    ax7.plot(steps, results['J_means'], 'purple', linewidth=2, label='mean J')
    ax7.fill_between(steps, 
                     np.array(results['J_means']) - np.array(results['J_stds']),
                     np.array(results['J_means']) + np.array(results['J_stds']),
                     alpha=0.3, color='purple')
    ax7.axhline(cfg.J_base, color='black', linestyle='--', linewidth=1.5, 
               alpha=0.5, label=f'J_base={cfg.J_base}')
    ax7.set_xlabel('Step', fontsize=11)
    ax7.set_ylabel('J', fontsize=11)
    ax7.set_title('Coupling Modulation', fontsize=12)
    ax7.legend(fontsize=10)
    ax7.grid(True, alpha=0.3)
    
    ax8 = fig.add_subplot(gs[2, 2])
    ax8.hist(psi_final.flatten(), bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax8.set_xlabel('Ψ', fontsize=11)
    ax8.set_ylabel('Frequency', fontsize=11)
    ax8.set_title('Ψ Distribution', fontsize=12)
    
    ax9 = fig.add_subplot(gs[2, 3])
    ax9.scatter(omega_final.flatten(), psi_final.flatten(), alpha=0.3, s=2, c='green')
    ax9.set_xlabel('ω', fontsize=11)
    ax9.set_ylabel('Ψ', fontsize=11)
    ax9.set_title('ω-Ψ Correlation', fontsize=12)
    ax9.grid(True, alpha=0.3)
    
    fig_path = output_dir / 'e30d_persistent_sources.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return {
        'pattern_ratio': pattern_ratio,
        'stability': stability,
        'final_psi_std': float(np.std(psi_final)),
        'final_omega_mean': float(np.mean(omega_final)),
        'J_amplification': float(np.mean(J_final) / cfg.J_base)
    }


def main():
    """Run E30d: Persistent sources test."""
    cfg = E30dConfig()
    
    print("=" * 80)
    print("E30d: PERSISTENT INFORMATION SOURCES")
    print("=" * 80)
    print(f"Lattice: {cfg.L}×{cfg.L}")
    print(f"Evolution: {cfg.steps_total} steps")
    print(f"Persistent sources: {cfg.n_sources}")
    print(f"Source strength: {cfg.source_strength} ω/step")
    print(f"\nParameters (from E30c best):")
    print(f"  J_base = {cfg.J_base}")
    print(f"  β = {cfg.beta}")
    print(f"  γ = {cfg.gamma_omega}")
    print("=" * 80)
    print("\n🎯 HYPOTHESIS: Sustained input creates stable patterns")
    print("=" * 80)
    
    results = run_persistent_sources(cfg)
    
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e30_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analysis = analyze_persistent_patterns(results, cfg, output_dir)
    
    print("\n" + "=" * 80)
    print("KEY FINDING")
    print("=" * 80)
    
    if analysis['pattern_ratio'] > 1.2:
        print("\n✅ PERSISTENT SOURCES ENABLE PATTERN FORMATION!")
        print("   This confirms: self-organization requires SUSTAINED information generation")
        print("   Transient cascades alone are insufficient")
    else:
        print("\n📊 Persistent sources show similar behavior to transient cascades")
        print("   Pattern formation may require different physical mechanism")
    
    output_data = {
        'config': {
            'L': cfg.L,
            'n_sources': cfg.n_sources,
            'source_strength': cfg.source_strength,
            'J_base': cfg.J_base,
            'beta': cfg.beta,
            'gamma_omega': cfg.gamma_omega
        },
        'analysis': analysis
    }
    
    results_file = output_dir / 'e30d_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    print("\n" + "=" * 80)
    print("E30d COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

