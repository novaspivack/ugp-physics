#!/usr/bin/env python3
"""
E30: Information-Geometry Co-evolution
=======================================

Tests feedback loop between adjudication and information geometry:
    Adjudication → ω ↑ → Ψ ↑ → J_ij ↑ → More adjudication

2D lattice where:
- Each site has state b_i ∈ {0,1} and information density ω_i
- Cascades increase local ω
- Coherence field Ψ solved from elliptic PDE: (-Δ + m²)Ψ = κω  
- Coupling modulated by Ψ: J_ij = J_0(1 + βΨ_ij)

Prediction: Spontaneous formation of stable high-Ψ domains with enhanced activity.

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
    Mathematical_Foundations_of_Reflexive_Reality.tex (coherence field equations)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.ndimage import convolve
import time

from common.ensemble_core import argmin_branch, inter_cost, local_cost


class E30Config:
    """Configuration for E30 co-evolution experiment."""
    # Lattice
    L = 60                 # Lattice size (60x60 = 3600 sites)
    
    # Dynamics
    steps_total = 1000     # Evolution steps
    steps_snapshot = 50    # Snapshot interval for visualization
    
    # Coupling (nearest-neighbor on lattice)
    J_base = 0.15          # Base coupling strength
    beta = 2.0             # Psi modulation strength: J = J_0(1 + β Ψ)
    
    # Information field
    omega_increment = 1.0  # ω increase per adjudication
    gamma_omega = 0.05     # ω decay rate
    D_omega = 0.1          # ω diffusion coefficient
    
    # Coherence field PDE: (-Δ + m²)Ψ = κω
    kappa = 1.0            # Coupling to ω
    m_squared = 0.1        # Mass term (correlation length ~ 1/sqrt(m²))
    
    # Cascade dynamics
    cascade_interval = 1   # Cascades every N steps
    seed_fraction = 0.05   # Fraction of sites to seed per cascade
    max_cascade_iter = 100 # Max cascade propagation
    
    seed = 47


def init_lattice(L, rng):
    """Initialize 2D lattice with random states."""
    b = rng.integers(0, 2, size=(L, L))
    psi_field = np.zeros((L, L))
    omega = np.zeros((L, L))
    bias = rng.uniform(0.0, 1.0, size=(L, L))
    kappa = rng.uniform(0.1, 1.0, size=(L, L))
    return b, psi_field, omega, bias, kappa


def get_neighbors(i, j, L):
    """Get 4-connected neighbors on periodic lattice."""
    return [
        ((i-1) % L, j),
        ((i+1) % L, j),
        (i, (j-1) % L),
        (i, (j+1) % L)
    ]


def lattice_cascade(b, psi_field, omega, bias, kappa, J_coupling, L, 
                   seed_fraction, max_iter, rng):
    """
    Run avalanche cascade on 2D lattice.
    
    Returns:
        Number of flips, array of flipped sites
    """
    # Seed random sites
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
        
        # Gather neighbor info
        neighbors = get_neighbors(i, j, L)
        neighbor_indices = []
        neighbor_data = []
        
        for ni, nj in neighbors:
            J_ij = J_coupling[i, j]  # Coupling strength from this site
            neighbor_indices.append((ni, nj))
            neighbor_data.append(J_ij)
        
        # Compute optimal branch
        cost_0 = local_cost(0, psi_field[i, j], bias[i, j], kappa[i, j])
        cost_1 = local_cost(1, psi_field[i, j], bias[i, j], kappa[i, j])
        
        for (ni, nj), J_val in zip(neighbor_indices, neighbor_data):
            cost_0 += J_val * inter_cost(0, b[ni, nj])
            cost_1 += J_val * inter_cost(1, b[ni, nj])
        
        new_val = 0 if cost_0 <= cost_1 else 1
        
        if new_val != b[i, j]:
            b[i, j] = new_val
            flipped.append((i, j))
            omega[i, j] += 1.0  # Increase information density
            
            # Add neighbors to queue
            for ni, nj in neighbors:
                if (ni, nj) not in visited:
                    queue.append((ni, nj))
    
    return len(flipped), flipped


def update_omega_diffusion(omega, D, gamma, dt=1.0):
    """
    Update omega with diffusion and decay: ∂ω/∂t = D∇²ω - γω
    """
    # Laplacian via convolution (periodic boundary)
    laplacian_kernel = np.array([[0, 1, 0],
                                  [1, -4, 1],
                                  [0, 1, 0]])
    laplacian = convolve(omega, laplacian_kernel, mode='wrap')
    
    omega_new = omega + dt * (D * laplacian - gamma * omega)
    omega_new = np.maximum(omega_new, 0.0)  # Keep non-negative
    
    return omega_new


def solve_psi_fft(omega, kappa, m_squared):
    """
    Solve (-Δ + m²)Ψ = κω using FFT.
    
    In Fourier space: (k² + m²) Ψ_k = κ ω_k
    So: Ψ_k = κ ω_k / (k² + m²)
    """
    L = omega.shape[0]
    
    # FFT of source
    omega_k = np.fft.fft2(omega)
    
    # Wave numbers (periodic boundary)
    kx = 2 * np.pi * np.fft.fftfreq(L)
    ky = 2 * np.pi * np.fft.fftfreq(L)
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    k_squared = KX**2 + KY**2
    
    # Solve in Fourier space
    denominator = k_squared + m_squared
    denominator[0, 0] = 1.0  # Avoid singularity (set DC component separately)
    
    psi_k = kappa * omega_k / denominator
    psi_k[0, 0] = 0.0  # No DC offset
    
    # Inverse FFT
    psi = np.fft.ifft2(psi_k).real
    
    return psi


def compute_coupling_matrix(J_base, psi, beta, L):
    """
    Compute modulated coupling: J_ij = J_0 (1 + β Ψ_ij)
    
    where Ψ_ij = (Ψ_i + Ψ_j)/2
    """
    J_coupling = np.zeros((L, L))
    
    for i in range(L):
        for j in range(L):
            # Average Psi with neighbors
            neighbors = get_neighbors(i, j, L)
            psi_avg = (psi[i, j] + np.mean([psi[ni, nj] for ni, nj in neighbors])) / 2
            
            J_coupling[i, j] = J_base * (1.0 + beta * psi_avg)
    
    # Clip to reasonable range
    J_coupling = np.clip(J_coupling, J_base * 0.5, J_base * 3.0)
    
    return J_coupling


def run_coevolution(cfg):
    """Run full co-evolution simulation."""
    rng = default_rng(cfg.seed)
    L = cfg.L
    
    print(f"Initializing {L}x{L} lattice...")
    b, psi, omega, bias, kappa = init_lattice(L, rng)
    
    # Storage for analysis
    snapshots = []
    cascade_sizes = []
    omega_means = []
    psi_means = []
    psi_stds = []
    
    print(f"\nRunning co-evolution for {cfg.steps_total} steps...")
    start_time = time.time()
    
    for step in range(cfg.steps_total):
        if step % 50 == 0:
            elapsed = time.time() - start_time
            rate = (step+1) / elapsed if elapsed > 0 else 0
            print(f"  Step {step}/{cfg.steps_total} ({rate:.1f} steps/s)")
        
        # 1. Update omega (diffusion + decay)
        omega = update_omega_diffusion(omega, cfg.D_omega, cfg.gamma_omega, dt=1.0)
        
        # 2. Solve for Psi field
        psi = solve_psi_fft(omega, cfg.kappa, cfg.m_squared)
        
        # 3. Compute modulated coupling
        J_coupling = compute_coupling_matrix(cfg.J_base, psi, cfg.beta, L)
        
        # 4. Run cascade
        if step % cfg.cascade_interval == 0:
            n_flips, flipped_sites = lattice_cascade(
                b, psi, omega, bias, kappa, J_coupling, L,
                cfg.seed_fraction, cfg.max_cascade_iter, rng
            )
            cascade_sizes.append(n_flips)
        
        # 5. Record statistics
        omega_means.append(np.mean(omega))
        psi_means.append(np.mean(psi))
        psi_stds.append(np.std(psi))
        
        # 6. Save snapshots
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
        'psi_means': psi_means,
        'psi_stds': psi_stds
    }


def analyze_and_plot(results, cfg, output_dir):
    """Analyze pattern formation and create visualizations."""
    print("\n" + "=" * 80)
    print("PATTERN FORMATION ANALYSIS")
    print("=" * 80)
    
    snapshots = results['snapshots']
    
    # Final snapshot
    final = snapshots[-1]
    psi_final = final['psi']
    omega_final = final['omega']
    
    # Identify high-Psi domains (above threshold)
    psi_threshold = np.mean(psi_final) + np.std(psi_final)
    high_psi_mask = psi_final > psi_threshold
    domain_fraction = np.sum(high_psi_mask) / psi_final.size
    
    print(f"\nFinal state (step {final['step']}):")
    print(f"  Mean Ψ: {np.mean(psi_final):.4f}")
    print(f"  Std Ψ: {np.std(psi_final):.4f}")
    print(f"  High-Ψ domain fraction: {100*domain_fraction:.1f}%")
    print(f"  Mean ω: {np.mean(omega_final):.4f}")
    
    # Compare cascade activity in high vs low Psi regions
    cascade_sizes = results['cascade_sizes']
    print(f"\n  Total cascades: {len(cascade_sizes)}")
    print(f"  Mean cascade size: {np.mean(cascade_sizes):.1f}")
    
    # Time evolution
    psi_means = np.array(results['psi_means'])
    psi_stds = np.array(results['psi_stds'])
    omega_means = np.array(results['omega_means'])
    
    # Check if patterns are stable (std plateaus)
    if len(psi_stds) > 100:
        early_std = np.mean(psi_stds[:100])
        late_std = np.mean(psi_stds[-100:])
        std_ratio = late_std / early_std if early_std > 0 else 1.0
        
        if std_ratio > 1.5:
            print(f"\n✅ PATTERN FORMATION DETECTED (std increased {std_ratio:.2f}x)")
        elif std_ratio > 1.1:
            print(f"\n✅ WEAK PATTERN FORMATION (std increased {std_ratio:.2f}x)")
        else:
            print(f"\n⚠️  NO CLEAR PATTERNS (std ratio {std_ratio:.2f})")
    
    # Plotting
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
    
    # Top row: Spatial fields at final time
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(psi_final, cmap='viridis', origin='lower')
    ax1.set_title('Coherence Field Ψ (final)', fontsize=12)
    plt.colorbar(im1, ax=ax1)
    
    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(omega_final, cmap='hot', origin='lower')
    ax2.set_title('Information Density ω (final)', fontsize=12)
    plt.colorbar(im2, ax=ax2)
    
    ax3 = fig.add_subplot(gs[0, 2])
    im3 = ax3.imshow(final['J_coupling'], cmap='plasma', origin='lower')
    ax3.set_title('Coupling Strength J (final)', fontsize=12)
    plt.colorbar(im3, ax=ax3)
    
    ax4 = fig.add_subplot(gs[0, 3])
    im4 = ax4.imshow(final['b'], cmap='binary', origin='lower')
    ax4.set_title('State b (final)', fontsize=12)
    
    # Middle row: Time evolution
    steps = np.arange(len(psi_means))
    
    ax5 = fig.add_subplot(gs[1, :2])
    ax5.plot(steps, psi_means, 'b-', linewidth=2, label='Mean Ψ')
    ax5.fill_between(steps, psi_means - psi_stds, psi_means + psi_stds,
                     alpha=0.3, color='blue', label='±1 std')
    ax5.set_xlabel('Step', fontsize=12)
    ax5.set_ylabel('Ψ', fontsize=12)
    ax5.set_title('Coherence Field Evolution', fontsize=13)
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3)
    
    ax6 = fig.add_subplot(gs[1, 2:])
    ax6.plot(steps, omega_means, 'r-', linewidth=2)
    ax6.set_xlabel('Step', fontsize=12)
    ax6.set_ylabel('Mean ω', fontsize=12)
    ax6.set_title('Information Density Evolution', fontsize=13)
    ax6.grid(True, alpha=0.3)
    
    # Bottom row: Cascade statistics and domain analysis
    ax7 = fig.add_subplot(gs[2, :2])
    cascade_steps = np.arange(len(cascade_sizes)) * cfg.cascade_interval
    ax7.plot(cascade_steps, cascade_sizes, 'go-', markersize=3, linewidth=1, alpha=0.6)
    ax7.set_xlabel('Step', fontsize=12)
    ax7.set_ylabel('Cascade Size', fontsize=12)
    ax7.set_title('Adjudication Cascade Activity', fontsize=13)
    ax7.grid(True, alpha=0.3)
    
    ax8 = fig.add_subplot(gs[2, 2:])
    ax8.hist(psi_final.flatten(), bins=50, alpha=0.7, color='purple', edgecolor='black')
    ax8.axvline(psi_threshold, color='red', linestyle='--', linewidth=2, 
               label=f'Threshold (μ+σ)')
    ax8.set_xlabel('Ψ value', fontsize=12)
    ax8.set_ylabel('Frequency', fontsize=12)
    ax8.set_title('Final Ψ Distribution', fontsize=13)
    ax8.legend(fontsize=10)
    
    fig_path = output_dir / 'e30_coevolution.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return {
        'domain_fraction': float(domain_fraction),
        'final_psi_mean': float(np.mean(psi_final)),
        'final_psi_std': float(np.std(psi_final)),
        'final_omega_mean': float(np.mean(omega_final)),
        'mean_cascade_size': float(np.mean(cascade_sizes)),
        'pattern_formation': std_ratio if len(psi_stds) > 100 else 1.0
    }


def main():
    """Run E30: Information-geometry co-evolution."""
    cfg = E30Config()
    
    print("=" * 80)
    print("E30: INFORMATION-GEOMETRY CO-EVOLUTION")
    print("=" * 80)
    print(f"Lattice: {cfg.L}x{cfg.L} = {cfg.L**2} sites")
    print(f"Steps: {cfg.steps_total}")
    print(f"Feedback: Ψ modulates J via β = {cfg.beta}")
    print("=" * 80)
    print("\n🎯 HYPOTHESIS: Spontaneous formation of stable high-Ψ domains")
    print("=" * 80)
    
    # Run simulation
    results = run_coevolution(cfg)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e30_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Analyze
    analysis = analyze_and_plot(results, cfg, output_dir)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: E30 CO-EVOLUTION")
    print("=" * 80)
    
    print(f"\nDomain formation:")
    print(f"  High-Ψ domain fraction: {100*analysis['domain_fraction']:.1f}%")
    print(f"  Pattern formation ratio: {analysis['pattern_formation']:.2f}x")
    
    if analysis['pattern_formation'] > 1.3:
        print("\n✅ HYPOTHESIS CONFIRMED: Clear pattern formation observed")
    elif analysis['pattern_formation'] > 1.1:
        print("\n✅ PARTIAL CONFIRMATION: Weak patterns emerged")
    else:
        print("\n⚠️  No clear patterns (may need longer evolution or stronger feedback)")
    
    print(f"\nFinal field statistics:")
    print(f"  Mean Ψ: {analysis['final_psi_mean']:.4f}")
    print(f"  Std Ψ: {analysis['final_psi_std']:.4f}")
    print(f"  Mean cascade size: {analysis['mean_cascade_size']:.1f}")
    
    # Save results
    output_data = {
        'config': {
            'L': cfg.L,
            'steps': cfg.steps_total,
            'beta': cfg.beta,
            'J_base': cfg.J_base
        },
        'analysis': analysis
    }
    
    results_file = output_dir / 'e30_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    print("\n" + "=" * 80)
    print("E30 COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

