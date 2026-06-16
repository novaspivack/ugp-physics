#!/usr/bin/env python3
"""
E9 Publication-Quality Plots with MLE/KS Statistical Analysis

Generates:
1. CCDF plots with MLE power-law fits and KS goodness-of-fit
2. Synchronization order parameter vs ||W||_2
3. Statistical summary table for SI

Usage:
    python3 e25_publication_plots.py

Outputs saved to e25_ensemble_outputs/
"""

import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from scipy import stats
from scipy.optimize import minimize_scalar

# Publication-quality matplotlib settings
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'font.family': 'serif',
    'text.usetex': False  # Set to True if LaTeX available
})

def power_law_mle(data, s_min):
    """
    Maximum likelihood estimator for power-law exponent κ.
    
    κ̂ = 1 + n / Σ ln(S_i/s_min)
    
    Parameters:
        data: array of burst sizes
        s_min: lower cutoff for tail
    
    Returns:
        float: MLE estimate of κ
    """
    tail = data[data >= s_min]
    if len(tail) < 2:
        return np.nan
    
    kappa_mle = 1.0 + len(tail) / np.sum(np.log(tail / s_min))
    return kappa_mle

def power_law_ccdf(s, kappa, s_min):
    """Theoretical CCDF for power-law: P(S >= s) = (s/s_min)^{-(κ-1)}"""
    return (s / s_min) ** (-(kappa - 1))

def ks_statistic(data, kappa, s_min):
    """
    Kolmogorov-Smirnov statistic between empirical and fitted CCDF.
    
    Returns:
        float: KS distance
    """
    tail = data[data >= s_min]
    if len(tail) < 2:
        return np.nan
    
    # Empirical CCDF
    sorted_tail = np.sort(tail)
    n = len(tail)
    empirical_ccdf = 1.0 - np.arange(1, n + 1) / n
    
    # Theoretical CCDF
    theoretical_ccdf = power_law_ccdf(sorted_tail, kappa, s_min)
    
    # KS distance
    ks = np.max(np.abs(empirical_ccdf - theoretical_ccdf))
    return ks

def find_optimal_s_min(data, s_candidates=None):
    """
    Find optimal s_min by minimizing KS distance.
    
    Returns:
        tuple: (optimal_s_min, kappa_at_optimal, ks_at_optimal)
    """
    if s_candidates is None:
        # Use quantiles
        s_candidates = np.percentile(data, [10, 20, 30, 40, 50])
    
    best_s_min = None
    best_kappa = None
    best_ks = np.inf
    
    for s_min in s_candidates:
        if s_min < np.min(data):
            continue
        
        kappa = power_law_mle(data, s_min)
        if np.isnan(kappa):
            continue
        
        ks = ks_statistic(data, kappa, s_min)
        if ks < best_ks:
            best_ks = ks
            best_kappa = kappa
            best_s_min = s_min
    
    return best_s_min, best_kappa, best_ks

def plot_ccdf_all_J(results, output_file="e25_ccdf_combined.png"):
    """
    Plot CCDF for all J values with MLE fits.
    
    Parameters:
        results: list of dicts from e25_ensemble_cascade_mp.py
        output_file: output filename
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(results)))
    
    for idx, r in enumerate(results):
        J = r['J']
        bursts = r.get('bursts', [])
        
        if len(bursts) < 10:
            continue
        
        bursts_arr = np.array(bursts)
        
        # Compute CCDF
        unique_sizes = np.unique(bursts_arr)
        ccdf = np.array([np.mean(bursts_arr >= s) for s in unique_sizes])
        
        # MLE fit with optimal s_min
        s_min_opt, kappa_mle, ks_dist = find_optimal_s_min(bursts_arr)
        
        # Plot data
        ax.loglog(unique_sizes, ccdf, 'o', markersize=4, alpha=0.6, 
                 color=colors[idx], label=f'$J={J:.2f}$')
        
        # Plot MLE fit
        if not np.isnan(kappa_mle):
            s_fit = unique_sizes[unique_sizes >= s_min_opt]
            ccdf_fit = power_law_ccdf(s_fit, kappa_mle, s_min_opt)
            ax.loglog(s_fit, ccdf_fit, '-', linewidth=1.5, color=colors[idx], alpha=0.8)
    
    ax.set_xlabel('Cascade size $S$', fontsize=11)
    ax.set_ylabel('$P(S \\geq s)$ (CCDF)', fontsize=11)
    ax.set_title('Ensemble Adjudication Cascade Distributions (E9)', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved {output_file}")
    plt.close()

def plot_sync_order_parameter(results, output_file="e25_sync_order_param.png"):
    """
    Plot synchronization order parameter vs ||W||_2 with threshold detection.
    """
    normW_vals = [r['normW'] for r in results]
    J_vals = [r['J'] for r in results]
    
    # Order parameter: mean burst size (proxy for synchronization)
    mean_sizes = []
    for r in results:
        stats = r.get('burst_stats', {})
        mean_sizes.append(stats.get('mean', 0))
    
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    
    # Plot
    ax.plot(normW_vals, mean_sizes, 'o-', linewidth=2.5, markersize=9, 
           color='#2E86AB', markerfacecolor='white', markeredgewidth=2)
    
    # Detect threshold
    if len(mean_sizes) > 1:
        jumps = np.diff(mean_sizes)
        if len(jumps) > 0 and np.max(jumps) > np.mean(jumps) * 1.5:
            max_jump_idx = np.argmax(jumps)
            J_c_est = (normW_vals[max_jump_idx] + normW_vals[max_jump_idx + 1]) / 2
            
            ax.axvline(J_c_est, color='#A23B72', linestyle='--', linewidth=2,
                      label=f'$J_c \\approx {J_c_est:.3f}$')
            
            # Shade subcritical/supercritical regions
            ax.axvspan(min(normW_vals), J_c_est, alpha=0.1, color='blue', label='Subcritical')
            ax.axvspan(J_c_est, max(normW_vals), alpha=0.1, color='red', label='Supercritical')
    
    ax.set_xlabel('Spectral norm $\\|W\\|_2$', fontsize=11)
    ax.set_ylabel('Mean cascade size', fontsize=11)
    ax.set_title('Synchronization Threshold (E9)', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved {output_file}")
    plt.close()

def generate_stats_table(results, output_file="e25_stats_table.txt"):
    """
    Generate statistical summary table for SI appendix.
    """
    with open(output_file, 'w') as f:
        f.write("E9 Statistical Summary Table\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'J':>6s}  {'||W||_2':>8s}  {'N_burst':>8s}  {'<S>':>7s}  ")
        f.write(f"{'S_max':>6s}  {'κ_MLE':>7s}  {'s_min':>7s}  {'KS':>7s}\n")
        f.write("-" * 80 + "\n")
        
        for r in results:
            J = r['J']
            normW = r['normW']
            bursts = np.array(r.get('bursts', []))
            
            if len(bursts) < 5:
                f.write(f"{J:6.3f}  {normW:8.4f}  {'N/A':>8s}\n")
                continue
            
            n_bursts = len(bursts)
            mean_s = np.mean(bursts)
            max_s = np.max(bursts)
            
            # MLE with optimal s_min
            s_min_opt, kappa_mle, ks_dist = find_optimal_s_min(bursts)
            
            f.write(f"{J:6.3f}  {normW:8.4f}  {n_bursts:8d}  {mean_s:7.2f}  ")
            f.write(f"{max_s:6d}  {kappa_mle:7.3f}  {s_min_opt:7.1f}  {ks_dist:7.4f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("κ_MLE: Maximum likelihood estimate of power-law exponent\n")
        f.write("s_min: Optimal lower cutoff (minimizes KS distance)\n")
        f.write("KS: Kolmogorov-Smirnov distance (goodness-of-fit)\n")
    
    print(f"✓ Saved {output_file}")

def main():
    """Generate all publication-quality E9 figures and statistics."""
    
    # Load results
    results_file = Path("e25_ensemble_outputs/e25_ensemble_results.json")
    
    if not results_file.exists():
        print(f"Error: {results_file} not found!")
        print("Run e25_ensemble_cascade_mp.py first.")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    output_dir = Path("e25_ensemble_outputs")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("E9 Publication-Quality Plots and Statistics")
    print("=" * 60)
    
    # Generate plots
    print("\nGenerating figures...")
    plot_ccdf_all_J(results, output_dir / "e25_ccdf_combined.png")
    plot_sync_order_parameter(results, output_dir / "e25_sync_order_param.png")
    
    # Generate stats table
    print("\nGenerating statistical summary...")
    generate_stats_table(results, output_dir / "e25_stats_table.txt")
    
    print("\n" + "=" * 60)
    print("✓ All E9 publication materials generated")
    print("=" * 60)
    print("\nFiles created:")
    print("  - e25_ccdf_combined.png (CCDF with MLE fits)")
    print("  - e25_sync_order_param.png (Threshold plot)")
    print("  - e25_stats_table.txt (Statistical summary)")

if __name__ == "__main__":
    main()

