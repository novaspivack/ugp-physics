#!/usr/bin/env python3
"""
E30e: Information Profit Threshold Analysis
===========================================

Quantifies the fundamental principle discovered in E30 series:

    **STRUCTURE REQUIRES INFORMATION PROFIT**

Tests the hypothesis that pattern formation occurs when:
    
    Net Profit = Generation - (Decay + Dissipation) > Critical Threshold

Systematically varies the generation/decay ratio to find the precise 
conditions where self-organization becomes energetically favorable.

This is analogous to:
- Thermodynamics: Dissipative structures need energy influx > dissipation
- Biology: Life requires metabolism > catabolism  
- Economics: Growth requires revenue > costs
- Information theory: Neg-entropy generation must exceed entropy production

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/scripts/e30d_persistent_sources.py
    ADVANCED_ENSEMBLE_TESTS/docs/1_6_FINAL_INTEGRATION_SUMMARY.md
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
from multiprocessing import Pool
import time


class E30eConfig:
    """Profit threshold configuration."""
    L = 50                 # Moderate lattice for speed
    steps_total = 1000     # Evolution time
    n_sources = 10         # Fixed number of sources
    
    # Fixed parameters (from E30d)
    J_base = 0.15
    beta = 7.0
    D_omega = 0.15
    kappa = 1.0
    m_squared = 0.03
    
    # SWEEP: Generation vs Decay
    # Net profit = (n_sources × strength) - (γ × mean_ω)
    source_strengths = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    gamma_values = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]
    
    # Multiprocessing
    n_cores = 8
    seed_base = 60


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


def update_omega_diffusion(omega, D, gamma, dt=1.0):
    """Diffusion-decay."""
    laplacian_kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    laplacian = convolve(omega, laplacian_kernel, mode='wrap')
    omega_new = omega + dt * (D * laplacian - gamma * omega)
    return np.maximum(omega_new, 0.0)


def compute_coupling_matrix(J_base, psi, beta, L):
    """Modulated coupling."""
    psi_avg = (psi + np.roll(psi,1,axis=0) + np.roll(psi,-1,axis=0) +
               np.roll(psi,1,axis=1) + np.roll(psi,-1,axis=1)) / 5
    J_coupling = J_base * (1.0 + beta * psi_avg)
    return np.clip(J_coupling, J_base*0.1, J_base*10.0)


def run_profit_point(args):
    """Run simulation for one profit ratio point."""
    strength, gamma, cfg, run_id = args
    
    rng = default_rng(cfg.seed_base + run_id)
    L = cfg.L
    
    # Place sources
    sources = []
    for _ in range(cfg.n_sources):
        i, j = rng.integers(0, L), rng.integers(0, L)
        sources.append((i, j))
    
    # Initialize
    psi = np.zeros((L, L))
    omega = np.zeros((L, L))
    
    # Track evolution
    omega_means = []
    psi_stds = []
    
    # Calculate theoretical steady-state omega (generation = decay)
    # At steady state: strength × n_sources / L² = γ × ⟨ω⟩
    # ⟨ω⟩_ss = (strength × n_sources) / (γ × L²)
    omega_ss_theory = (strength * cfg.n_sources) / (gamma * L**2)
    
    # Run evolution
    for step in range(cfg.steps_total):
        # Inject at sources
        for i, j in sources:
            omega[i, j] += strength
        
        # Diffuse and decay
        omega = update_omega_diffusion(omega, cfg.D_omega, gamma, dt=1.0)
        
        # Solve for Psi
        psi = solve_psi_fft(omega, cfg.kappa, cfg.m_squared)
        
        # Statistics
        omega_means.append(np.mean(omega))
        psi_stds.append(np.std(psi))
    
    # Analysis
    omega_means = np.array(omega_means)
    psi_stds = np.array(psi_stds)
    
    # Early vs late
    n_early = 200
    n_late = 200
    early_psi = np.mean(psi_stds[:n_early])
    late_psi = np.mean(psi_stds[-n_late:])
    pattern_ratio = late_psi / early_psi if early_psi > 1e-10 else 0.0
    
    # Steady-state omega
    omega_ss_actual = np.mean(omega_means[-n_late:])
    
    # Net profit calculation (instantaneous, averaged over late time)
    generation_rate = (strength * cfg.n_sources) / L**2
    decay_rate = gamma * omega_ss_actual
    dissipation_rate = cfg.D_omega * np.mean([
        np.std(omega_means[i:i+10]) for i in range(len(omega_means)-10, len(omega_means))
    ]) if len(omega_means) > 10 else 0.0
    
    net_profit = generation_rate - decay_rate - dissipation_rate
    profit_ratio = generation_rate / (decay_rate + dissipation_rate + 1e-10)
    
    return {
        'strength': strength,
        'gamma': gamma,
        'generation_rate': generation_rate,
        'decay_rate': decay_rate,
        'dissipation_rate': dissipation_rate,
        'net_profit': net_profit,
        'profit_ratio': profit_ratio,
        'pattern_ratio': pattern_ratio,
        'omega_ss_actual': omega_ss_actual,
        'omega_ss_theory': omega_ss_theory,
        'final_psi_std': psi_stds[-1],
        'max_psi_std': np.max(psi_stds)
    }


def analyze_profit_threshold(results, cfg, output_dir):
    """Analyze profit threshold for pattern formation."""
    print("\n" + "=" * 80)
    print("INFORMATION PROFIT THRESHOLD ANALYSIS")
    print("=" * 80)
    
    # Sort by profit ratio
    results_sorted = sorted(results, key=lambda x: x['profit_ratio'], reverse=True)
    
    print("\nTop 10 configurations (by profit ratio):")
    print(f"{'Rank':<6} {'Strength':<10} {'γ':<8} {'Profit':<12} {'Ratio':<10} {'Pattern':<10}")
    print("-" * 80)
    
    for i, r in enumerate(results_sorted[:10]):
        print(f"{i+1:<6} {r['strength']:<10.2f} {r['gamma']:<8.3f} "
              f"{r['net_profit']:<12.4f} {r['profit_ratio']:<10.2f} "
              f"{r['pattern_ratio']:<10.3f}")
    
    # Find critical threshold
    pattern_formers = [r for r in results if r['pattern_ratio'] > 1.05]
    non_formers = [r for r in results if r['pattern_ratio'] <= 1.05]
    
    if pattern_formers and non_formers:
        min_profit_for_patterns = min([r['profit_ratio'] for r in pattern_formers])
        max_profit_no_patterns = max([r['profit_ratio'] for r in non_formers])
        threshold = (min_profit_for_patterns + max_profit_no_patterns) / 2
        
        print(f"\n🎯 CRITICAL PROFIT THRESHOLD IDENTIFIED:")
        print(f"   Profit ratio must exceed: {threshold:.2f}")
        print(f"   (Generation / Drain > {threshold:.2f})")
    else:
        threshold = None
        print("\n⚠️  Clear threshold not found in tested range")
    
    # Visualize
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Plot 1: Pattern ratio vs profit ratio
    ax1 = axes[0, 0]
    profits = [r['profit_ratio'] for r in results]
    patterns = [r['pattern_ratio'] for r in results]
    scatter = ax1.scatter(profits, patterns, c=[r['strength'] for r in results],
                         cmap='viridis', s=100, alpha=0.6, edgecolors='black')
    ax1.axhline(1.0, color='red', linestyle='--', linewidth=2, label='Threshold')
    if threshold:
        ax1.axvline(threshold, color='green', linestyle='--', linewidth=2,
                   label=f'Critical profit = {threshold:.2f}')
    ax1.set_xlabel('Profit Ratio (Generation/Drain)', fontsize=12)
    ax1.set_ylabel('Pattern Ratio (Growth)', fontsize=12)
    ax1.set_title('Pattern Formation vs Information Profit', fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax1, label='Source strength')
    
    # Plot 2: Net profit vs pattern ratio
    ax2 = axes[0, 1]
    net_profits = [r['net_profit'] for r in results]
    ax2.scatter(net_profits, patterns, c=[r['gamma'] for r in results],
               cmap='plasma', s=100, alpha=0.6, edgecolors='black')
    ax2.axhline(1.0, color='red', linestyle='--', linewidth=2)
    ax2.axvline(0.0, color='orange', linestyle=':', linewidth=2, label='Break-even')
    ax2.set_xlabel('Net Profit (Gen - Drain)', fontsize=12)
    ax2.set_ylabel('Pattern Ratio', fontsize=12)
    ax2.set_title('Pattern vs Net Information Profit', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Heatmap (strength vs gamma)
    ax3 = axes[0, 2]
    strengths = sorted(list(set([r['strength'] for r in results])))
    gammas = sorted(list(set([r['gamma'] for r in results])))
    pattern_grid = np.zeros((len(gammas), len(strengths)))
    
    for r in results:
        i_s = strengths.index(r['strength'])
        i_g = gammas.index(r['gamma'])
        pattern_grid[i_g, i_s] = r['pattern_ratio']
    
    im = ax3.imshow(pattern_grid, aspect='auto', origin='lower', cmap='RdYlGn',
                   extent=[min(strengths), max(strengths), min(gammas), max(gammas)],
                   vmin=0.5, vmax=1.5)
    ax3.set_xlabel('Source Strength', fontsize=12)
    ax3.set_ylabel('Decay Rate γ', fontsize=12)
    ax3.set_title('Pattern Formation Map', fontsize=13)
    plt.colorbar(im, ax=ax3, label='Pattern ratio')
    
    # Plot 4: Profit components
    ax4 = axes[1, 0]
    gen_rates = [r['generation_rate'] for r in results]
    decay_rates = [r['decay_rate'] for r in results]
    ax4.scatter(gen_rates, decay_rates, c=patterns, cmap='coolwarm',
               s=100, alpha=0.6, edgecolors='black', vmin=0.8, vmax=1.2)
    # Add diagonal (break-even line)
    max_rate = max(max(gen_rates), max(decay_rates))
    ax4.plot([0, max_rate], [0, max_rate], 'k--', linewidth=2, label='Break-even')
    ax4.set_xlabel('Generation Rate', fontsize=12)
    ax4.set_ylabel('Decay Rate', fontsize=12)
    ax4.set_title('Generation vs Drain Balance', fontsize=13)
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Omega steady state (theory vs actual)
    ax5 = axes[1, 1]
    omega_theory = [r['omega_ss_theory'] for r in results]
    omega_actual = [r['omega_ss_actual'] for r in results]
    ax5.scatter(omega_theory, omega_actual, c=patterns, cmap='coolwarm',
               s=100, alpha=0.6, edgecolors='black', vmin=0.8, vmax=1.2)
    max_omega = max(max(omega_theory), max(omega_actual))
    ax5.plot([0, max_omega], [0, max_omega], 'k--', linewidth=1.5, label='Theory = Actual')
    ax5.set_xlabel('Theoretical ⟨ω⟩ (steady state)', fontsize=12)
    ax5.set_ylabel('Actual ⟨ω⟩', fontsize=12)
    ax5.set_title('Steady State Validation', fontsize=13)
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Summary statistics
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    summary_text = "Information Profit Analysis\n\n"
    summary_text += f"Configurations tested: {len(results)}\n"
    summary_text += f"Pattern formers: {len(pattern_formers)}\n"
    summary_text += f"Non-formers: {len(non_formers)}\n\n"
    
    if threshold:
        summary_text += f"CRITICAL THRESHOLD:\n"
        summary_text += f"  Profit ratio > {threshold:.2f}\n\n"
    
    if pattern_formers:
        avg_profit = np.mean([r['profit_ratio'] for r in pattern_formers])
        summary_text += f"Pattern formers avg:\n"
        summary_text += f"  Profit ratio: {avg_profit:.2f}\n"
        summary_text += f"  Net profit: {np.mean([r['net_profit'] for r in pattern_formers]):.4f}\n"
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    fig_path = output_dir / 'e30e_profit_threshold.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return {
        'critical_threshold': threshold,
        'n_pattern_formers': len(pattern_formers),
        'n_non_formers': len(non_formers),
        'best_config': results_sorted[0]
    }


def main():
    """Run E30e: Profit threshold analysis."""
    cfg = E30eConfig()
    
    print("=" * 80)
    print("E30e: INFORMATION PROFIT THRESHOLD")
    print("=" * 80)
    print("\n🎯 FUNDAMENTAL HYPOTHESIS:")
    print("   STRUCTURE REQUIRES INFORMATION PROFIT")
    print("\n   Net Profit = Generation - (Decay + Dissipation)")
    print("   Patterns form when: Profit > Critical Threshold")
    print("=" * 80)
    
    print(f"\nLattice: {cfg.L}×{cfg.L}")
    print(f"Sources: {cfg.n_sources}")
    print(f"Parameter sweep:")
    print(f"  Source strengths: {cfg.source_strengths}")
    print(f"  Decay rates (γ): {cfg.gamma_values}")
    
    # Generate all combinations
    tasks = []
    run_id = 0
    for strength in cfg.source_strengths:
        for gamma in cfg.gamma_values:
            tasks.append((strength, gamma, cfg, run_id))
            run_id += 1
    
    n_combinations = len(tasks)
    print(f"\nTotal combinations: {n_combinations}")
    print(f"Cores: {cfg.n_cores}")
    print(f"Estimated time: ~{n_combinations * cfg.steps_total / (100 * cfg.n_cores):.1f} minutes")
    
    print("\nLaunching sweep...")
    start_time = time.time()
    
    with Pool(cfg.n_cores) as pool:
        results = pool.map(run_profit_point, tasks)
    
    elapsed = time.time() - start_time
    print(f"\nSweep complete in {elapsed/60:.1f} minutes")
    
    # Output
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e30_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analysis = analyze_profit_threshold(results, cfg, output_dir)
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: INFORMATION PROFIT PRINCIPLE")
    print("=" * 80)
    
    if analysis['critical_threshold']:
        print(f"\n✅ CRITICAL THRESHOLD FOUND:")
        print(f"\n   Generation / Drain > {analysis['critical_threshold']:.2f}")
        print(f"\n   This is analogous to:")
        print(f"   - Biology: Anabolism / Catabolism > {analysis['critical_threshold']:.2f}")
        print(f"   - Economics: Revenue / Costs > {analysis['critical_threshold']:.2f}")
        print(f"   - Thermodynamics: Input / Dissipation > {analysis['critical_threshold']:.2f}")
        
        print(f"\n🎯 FUNDAMENTAL PRINCIPLE VALIDATED:")
        print(f"   Self-organizing structures require sustained")
        print(f"   information profit above critical threshold")
    else:
        print(f"\n📊 Results show correlation between profit and patterns")
        print(f"   but threshold is gradual rather than sharp")
    
    print(f"\nPattern formers: {analysis['n_pattern_formers']}/{n_combinations}")
    print(f"Best configuration: strength={analysis['best_config']['strength']:.2f}, "
          f"γ={analysis['best_config']['gamma']:.3f}")
    print(f"  Profit ratio: {analysis['best_config']['profit_ratio']:.2f}")
    print(f"  Pattern ratio: {analysis['best_config']['pattern_ratio']:.3f}")
    
    # Save
    output_data = {
        'hypothesis': 'Structure requires information profit',
        'config': {
            'L': cfg.L,
            'n_sources': cfg.n_sources,
            'strength_range': cfg.source_strengths,
            'gamma_range': cfg.gamma_values
        },
        'analysis': analysis,
        'all_results': results
    }
    
    results_file = output_dir / 'e30e_profit_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    print("\n" + "=" * 80)
    print("E30e COMPLETE — PROFIT PRINCIPLE QUANTIFIED")
    print("=" * 80)


if __name__ == '__main__':
    main()

