#!/usr/bin/env python3
"""
E29: Spectral Analysis of Ensemble Fluctuations
================================================

Tests that fluctuations near criticality reveal network eigenvalue structure.

Prediction: Power spectral density (PSD) of global observable should exhibit
peaks corresponding to eigenvalues of coupling matrix W.

This validates that "random" noise in physical systems contains information
about the underlying adjudication network structure.

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
    Mathematical_Foundations_of_Reflexive_Reality.tex (EAME-Lindblad theorem)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import pearsonr
import time

from common.ensemble_core import glauber_step, compute_eigenspectrum
from common.graph_builders import build_erdos_renyi, init_coupling_matrix


class E29Config:
    """Configuration for E29 spectral noise analysis."""
    N = 3000               # Large enough for good spectral resolution
    p_edge = 5e-4          # Sparse connectivity
    J = 0.12               # Near-critical coupling
    
    # Long time series for good PSD resolution
    steps_equilibrate = 500
    steps_measure = 10000  # Long trajectory
    
    # Glauber dynamics parameters
    dt = 0.5
    temperature = 1.0
    
    # Spectral analysis
    n_eigenvalues = 50     # Top eigenvalues to compute
    psd_method = 'welch'   # Welch's method for PSD
    nperseg = 512          # Segment length for Welch
    
    seed = 46


def run_long_trajectory(cfg):
    """Run long Glauber dynamics trajectory and record magnetization."""
    rng = default_rng(cfg.seed)
    
    print("Building network...")
    A = build_erdos_renyi(cfg.N, cfg.p_edge, rng)
    W = init_coupling_matrix(A, cfg.J, rng)
    
    print("Computing eigenspectrum...")
    start_eigen = time.time()
    eigenvalues = compute_eigenspectrum(W, k=cfg.n_eigenvalues)
    eigen_time = time.time() - start_eigen
    print(f"  Computed {len(eigenvalues)} eigenvalues in {eigen_time:.1f}s")
    print(f"  Spectral range: [{np.min(eigenvalues):.4f}, {np.max(eigenvalues):.4f}]")
    
    # Initialize states (spin representation: ±1)
    states = 2 * rng.integers(0, 2, size=cfg.N) - 1
    h_ext = 0.01 * rng.standard_normal(cfg.N)  # Small external field
    
    print(f"\nEquilibrating for {cfg.steps_equilibrate} steps...")
    for _ in range(cfg.steps_equilibrate):
        states = glauber_step(states, W, h_ext, rng, cfg.dt, cfg.temperature)
    
    print(f"Recording trajectory for {cfg.steps_measure} steps...")
    magnetization = np.zeros(cfg.steps_measure)
    
    start_sim = time.time()
    for t in range(cfg.steps_measure):
        if t % 1000 == 0 and t > 0:
            elapsed = time.time() - start_sim
            rate = t / elapsed
            print(f"  Step {t}/{cfg.steps_measure} ({rate:.1f} steps/s)")
        
        states = glauber_step(states, W, h_ext, rng, cfg.dt, cfg.temperature)
        magnetization[t] = np.mean(states)  # Global observable
    
    sim_time = time.time() - start_sim
    print(f"Trajectory complete in {sim_time:.1f}s")
    
    return magnetization, eigenvalues, W


def analyze_spectral_signatures(magnetization, eigenvalues, cfg, output_dir):
    """Compute PSD and correlate with eigenvalues."""
    print("\n" + "=" * 80)
    print("SPECTRAL ANALYSIS")
    print("=" * 80)
    
    # Compute power spectral density
    print("\nComputing power spectral density...")
    if cfg.psd_method == 'welch':
        freqs, psd = signal.welch(
            magnetization,
            fs=1.0/cfg.dt,
            nperseg=cfg.nperseg,
            scaling='density'
        )
    else:
        # Periodogram (simpler but noisier)
        freqs, psd = signal.periodogram(
            magnetization,
            fs=1.0/cfg.dt,
            scaling='density'
        )
    
    print(f"  Frequency range: [0, {np.max(freqs):.4f}]")
    print(f"  PSD points: {len(freqs)}")
    
    # Find peaks in PSD
    peak_indices, peak_properties = signal.find_peaks(
        psd,
        prominence=np.max(psd) * 0.05,  # 5% of max
        distance=5
    )
    peak_freqs = freqs[peak_indices]
    peak_heights = psd[peak_indices]
    
    print(f"\n  Found {len(peak_freqs)} significant peaks")
    if len(peak_freqs) > 0:
        print(f"  Peak frequencies: {peak_freqs[:10]}")  # First 10
    
    # Eigenvalues (absolute values, sorted)
    eigen_abs = np.abs(eigenvalues)
    eigen_abs_sorted = np.sort(eigen_abs)[::-1]  # Descending
    
    print(f"\n  Top 10 eigenvalues: {eigen_abs_sorted[:10]}")
    
    # Correlation analysis
    # Match peak frequencies to eigenvalues (within tolerance)
    matches = []
    tolerance = 0.05  # Frequency matching tolerance
    
    for peak_freq in peak_freqs:
        for eigen_val in eigen_abs_sorted[:cfg.n_eigenvalues]:
            if np.abs(peak_freq - eigen_val) < tolerance:
                matches.append((peak_freq, eigen_val))
                break
    
    match_rate = len(matches) / max(len(peak_freqs), 1)
    print(f"\n  Peak-eigenvalue matches: {len(matches)}/{len(peak_freqs)} ({100*match_rate:.1f}%)")
    
    # Statistical correlation
    # Create histograms in same bins
    freq_max = min(np.max(freqs), np.max(eigen_abs_sorted) * 1.5)
    bins = np.linspace(0, freq_max, 50)
    
    psd_hist, _ = np.histogram(freqs, bins=bins, weights=psd, density=True)
    eigen_hist, _ = np.histogram(eigen_abs_sorted, bins=bins, density=True)
    
    if np.sum(psd_hist) > 0 and np.sum(eigen_hist) > 0:
        psd_hist = psd_hist / np.sum(psd_hist)
        eigen_hist = eigen_hist / np.sum(eigen_hist)
        
        correlation, p_value = pearsonr(psd_hist, eigen_hist)
        print(f"\n  Distribution correlation: ρ = {correlation:.4f} (p = {p_value:.4f})")
    else:
        correlation = np.nan
        p_value = np.nan
    
    # Plotting
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Time series
    ax1 = axes[0, 0]
    t_plot = np.arange(min(1000, len(magnetization))) * cfg.dt
    ax1.plot(t_plot, magnetization[:len(t_plot)], 'b-', linewidth=0.5, alpha=0.7)
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Magnetization $M(t)$', fontsize=12)
    ax1.set_title('Ensemble Fluctuations (First 1000 steps)', fontsize=13)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Power spectral density with peaks
    ax2 = axes[0, 1]
    ax2.semilogy(freqs, psd, 'b-', linewidth=1, alpha=0.6, label='PSD')
    if len(peak_freqs) > 0:
        ax2.semilogy(peak_freqs, peak_heights, 'ro', markersize=8, 
                    label=f'{len(peak_freqs)} peaks')
    ax2.set_xlabel('Frequency', fontsize=12)
    ax2.set_ylabel('Power Spectral Density', fontsize=12)
    ax2.set_title('Fluctuation Spectrum', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Eigenvalue spectrum (histogram)
    ax3 = axes[1, 0]
    ax3.hist(eigen_abs_sorted, bins=30, alpha=0.7, color='green', 
            edgecolor='black', density=True)
    ax3.set_xlabel('|λ| (Eigenvalue magnitude)', fontsize=12)
    ax3.set_ylabel('Density', fontsize=12)
    ax3.set_title(f'Eigenvalue Distribution (top {cfg.n_eigenvalues})', fontsize=13)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Overlay comparison
    ax4 = axes[1, 1]
    # Normalized PSD
    psd_norm = psd / np.max(psd)
    ax4.plot(freqs, psd_norm, 'b-', linewidth=2, alpha=0.7, label='PSD (normalized)')
    
    # Eigenvalue markers
    for i, eigen_val in enumerate(eigen_abs_sorted[:20]):  # Top 20
        height = 0.8 - (i / 20) * 0.6  # Decreasing height
        ax4.axvline(eigen_val, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
        if i < 5:  # Label first 5
            ax4.text(eigen_val, height, f'λ{i+1}', fontsize=8, 
                    ha='center', color='red')
    
    ax4.axvline(np.nan, color='red', linestyle='--', alpha=0.5, 
               linewidth=1.5, label='Eigenvalues')
    
    ax4.set_xlabel('Frequency / Eigenvalue', fontsize=12)
    ax4.set_ylabel('Normalized Power', fontsize=12)
    ax4.set_title(f'PSD vs Eigenspectrum Overlay\nCorrelation: ρ = {correlation:.3f}', 
                 fontsize=13)
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim([0, freq_max])
    
    plt.tight_layout()
    fig_path = output_dir / 'e29_spectral_noise.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return {
        'n_peaks': len(peak_freqs),
        'peak_freqs': peak_freqs.tolist() if len(peak_freqs) > 0 else [],
        'n_eigenvalues': len(eigenvalues),
        'top_eigenvalues': eigen_abs_sorted[:20].tolist(),
        'matches': len(matches),
        'match_rate': match_rate,
        'correlation': float(correlation) if not np.isnan(correlation) else None,
        'p_value': float(p_value) if not np.isnan(p_value) else None
    }


def main():
    """Run E29: Spectral analysis of fluctuations."""
    cfg = E29Config()
    
    print("=" * 80)
    print("E29: SPECTRAL ANALYSIS OF ENSEMBLE FLUCTUATIONS")
    print("=" * 80)
    print(f"Network: N = {cfg.N}, p = {cfg.p_edge:.1e}, J = {cfg.J}")
    print(f"Trajectory length: {cfg.steps_measure} steps")
    print(f"Eigenvalues to compute: {cfg.n_eigenvalues}")
    print("=" * 80)
    print("\n🎯 HYPOTHESIS: PSD peaks should correlate with eigenvalue spectrum")
    print("=" * 80)
    
    # Run simulation
    magnetization, eigenvalues, W = run_long_trajectory(cfg)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e29_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Analyze
    results = analyze_spectral_signatures(magnetization, eigenvalues, cfg, output_dir)
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: E29 SPECTRAL SIGNATURES")
    print("=" * 80)
    
    print(f"\nPSD peaks found: {results['n_peaks']}")
    print(f"Eigenvalues computed: {results['n_eigenvalues']}")
    print(f"Peak-eigenvalue matches: {results['matches']}/{results['n_peaks']} ({100*results['match_rate']:.1f}%)")
    
    if results['correlation'] is not None:
        print(f"\nDistribution correlation: ρ = {results['correlation']:.4f}")
        print(f"Statistical significance: p = {results['p_value']:.4f}")
        
        if results['correlation'] > 0.5:
            print("\n✅ STRONG CORRELATION: Spectral signatures clearly visible")
        elif results['correlation'] > 0.3:
            print("\n✅ MODERATE CORRELATION: Eigenvalue structure evident")
        else:
            print("\n⚠️  WEAK CORRELATION: Signal may be dominated by noise")
    
    if results['match_rate'] > 0.5:
        print("\n✅ HYPOTHESIS SUPPORTED: Network structure visible in fluctuations")
    elif results['match_rate'] > 0.3:
        print("\n✅ PARTIAL SUPPORT: Some eigenvalue signatures detected")
    else:
        print("\n⚠️  Limited matches (may need longer trajectory or finer resolution)")
    
    # Save results
    output_data = {
        'config': {
            'N': cfg.N,
            'J': cfg.J,
            'steps_measure': cfg.steps_measure,
            'n_eigenvalues': cfg.n_eigenvalues
        },
        'results': results
    }
    
    results_file = output_dir / 'e29_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    print("\n" + "=" * 80)
    print("E29 COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

