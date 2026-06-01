#!/usr/bin/env python3
"""
Figure templates for E9: Ensemble Adjudication Cascades

Templates:
1. CCDF plot (log-log): P(S >= s) vs s with fitted power-law slope
2. Synchronization order parameter vs ||W||_2 showing threshold transition

Usage:
    python e25_plot_templates.py --data e25_ensemble_outputs/e25_ensemble_results.json
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
from pathlib import Path
from scipy import stats

def plot_ccdf(bursts, output_file="e25_ccdf.png", title_suffix=""):
    """
    Plot complementary cumulative distribution function (CCDF) of burst sizes.
    
    Parameters:
        bursts: array of burst sizes
        output_file: output filename
        title_suffix: optional suffix for title
    """
    if len(bursts) == 0:
        print("No bursts to plot")
        return
    
    unique_sizes, counts = np.unique(bursts, return_counts=True)
    ccdf = 1.0 - np.cumsum(counts) / len(bursts)
    
    # Fit power-law in tail region
    tail_mask = (unique_sizes >= 10) & (unique_sizes <= np.percentile(unique_sizes, 90))
    if np.sum(tail_mask) > 3:
        log_s = np.log(unique_sizes[tail_mask])
        log_ccdf = np.log(ccdf[tail_mask] + 1e-10)
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_s, log_ccdf)
        kappa_est = -slope
    else:
        kappa_est = None
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.loglog(unique_sizes, ccdf, 'o', markersize=4, alpha=0.6, label='Data')
    
    if kappa_est is not None:
        # Plot fitted line
        s_fit = unique_sizes[tail_mask]
        ccdf_fit = np.exp(intercept) * s_fit ** (-kappa_est)
        ax.loglog(s_fit, ccdf_fit, 'r--', linewidth=2, 
                  label=f'Power-law fit: $\\kappa = {kappa_est:.2f}$')
    
    ax.set_xlabel('Cascade size $s$', fontsize=11)
    ax.set_ylabel('$P(S \\geq s)$ (CCDF)', fontsize=11)
    ax.set_title(f'Cascade Size Distribution{title_suffix}', fontsize=12)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, which='both')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved {output_file}")
    plt.close()

def plot_synchronization_order(results, output_file="e25_sync_order.png"):
    """
    Plot synchronization order parameter vs spectral norm ||W||_2.
    
    Parameters:
        results: list of dicts with 'J', 'normW', 'burst_stats'
        output_file: output filename
    """
    J_vals = [r['J'] for r in results]
    normW_vals = [r['normW'] for r in results]
    
    # Order parameter: mean burst size (normalized) or burst rate
    # Alternative: fraction of time in synchronized state
    order_params = []
    for r in results:
        stats = r['burst_stats']
        # Use mean burst size as proxy for synchronization
        # Normalize by system size
        order_param = stats['mean'] / 1000.0  # normalize by typical scale
        order_params.append(order_param)
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(normW_vals, order_params, 'o-', linewidth=2, markersize=8)
    
    # Identify threshold (where order parameter jumps)
    # Simple heuristic: find largest jump
    if len(normW_vals) > 1:
        jumps = np.diff(order_params)
        if len(jumps) > 0:
            max_jump_idx = np.argmax(jumps)
            J_c_est = (normW_vals[max_jump_idx] + normW_vals[max_jump_idx + 1]) / 2
            ax.axvline(J_c_est, color='r', linestyle='--', linewidth=1.5,
                      label=f'Estimated $J_c \\approx {J_c_est:.3f}$')
    
    ax.set_xlabel('Spectral norm $\\|W\\|_2$', fontsize=11)
    ax.set_ylabel('Synchronization order parameter', fontsize=11)
    ax.set_title('Synchronization Transition vs Coupling Strength', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved {output_file}")
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Generate E9 figure templates')
    parser.add_argument('--data', type=str, 
                       default='e25_ensemble_outputs/e25_ensemble_results.json',
                       help='Path to JSON results file')
    parser.add_argument('--output-dir', type=str, default='e25_ensemble_outputs',
                       help='Output directory for figures')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Load results
    try:
        with open(args.data, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Error: Results file not found: {args.data}")
        print("Please run e25_ensemble_cascade.py first to generate data.")
        return
    
    # Plot 1: CCDF for each J value (or combined)
    # For now, combine all bursts
    all_bursts = []
    for r in results:
        # Reconstruct bursts from stats (simplified - in practice, save raw bursts)
        # For template, we'll use a synthetic example
        pass
    
    # Generate synthetic example if no data
    if len(results) == 0:
        print("No results found. Generating example plots...")
        # Example: power-law distributed bursts
        kappa_true = 2.0
        s_min, s_max = 10, 1000
        n_samples = 1000
        # Generate from power-law
        u = np.random.random(n_samples)
        s_example = s_min * (1 - u) ** (-1 / (kappa_true - 1))
        s_example = s_example[s_example <= s_max]
        
        plot_ccdf(s_example, output_dir / "e25_ccdf_example.png", 
                 " (Example)")
        
        # Example synchronization transition
        J_example = np.linspace(0.01, 0.15, 10)
        normW_example = J_example * 2.0  # rough scaling
        order_example = 0.01 + 0.5 * (normW_example > 0.08)
        results_example = [
            {'J': float(J), 'normW': float(nW), 
             'burst_stats': {'mean': float(order * 1000)}}
            for J, nW, order in zip(J_example, normW_example, order_example)
        ]
        plot_synchronization_order(results_example, 
                                   output_dir / "e25_sync_order_example.png")
    else:
        # Plot with real data
        # Extract all bursts (would need to save raw bursts in JSON)
        print("Plotting with results data...")
        # For now, generate example plots
        plot_ccdf(np.array([10, 20, 50, 100, 200, 500]), 
                 output_dir / "e25_ccdf_template.png", " (Template)")
        plot_synchronization_order(results, 
                                  output_dir / "e25_sync_order.png")
    
    print("\n✓ Figure templates generated")
    print("  Note: Replace with actual data arrays from e25_ensemble_cascade.py")

if __name__ == "__main__":
    main()

