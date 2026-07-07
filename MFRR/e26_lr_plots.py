#!/usr/bin/env python3
"""
E26 Publication-Quality Plots: Correlation Length & Hysteresis

Generates:
1. Correlation length ξ(s) for different memory times
2. Hysteresis loops m(s) for up/down sweeps
3. Hysteresis area vs τ_J

Usage:
    python3 e26_lr_plots.py
"""

import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'figure.dpi': 300
})

def plot_correlation_length(data, output_file="e26_xi_vs_s.png"):
    """Plot correlation length vs scaled coupling for different τ values."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for idx, tau in enumerate(data['tau_list']):
        tau_str = str(float(tau))
        if tau_str not in data['sweeps']:
            continue
        
        sweeps = data['sweeps'][tau_str]
        if 'up' not in sweeps:
            continue
        
        s_vals = np.array(sweeps['up']['s_vals'])
        xi_vals = np.array(sweeps['up']['xi_vals'])
        
        # Filter out nans
        valid = ~np.isnan(xi_vals)
        s_valid = s_vals[valid]
        xi_valid = xi_vals[valid]
        
        ax.plot(s_valid, xi_valid, 'o-', linewidth=2, markersize=6,
               color=colors[idx % len(colors)], label=f'$\\tau_J = {tau:.0f}$')
    
    ax.set_xlabel('Scaled coupling $s$', fontsize=11)
    ax.set_ylabel('Correlation length $\\xi$', fontsize=11)
    ax.set_title('Correlation Length vs Coupling (E26)', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved {output_file}")
    plt.close()

def plot_hysteresis_loops(data, output_file="e26_hysteresis.png"):
    """Plot hysteresis loops for different τ_J."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    
    for idx, tau in enumerate(data['tau_list']):
        tau_str = str(float(tau))
        if tau_str not in data['sweeps']:
            continue
        
        sweeps = data['sweeps'][tau_str]
        if 'up' not in sweeps or 'down' not in sweeps:
            continue
        
        s_up = np.array(sweeps['up']['s_vals'])
        m_up = np.array(sweeps['up']['m_vals'])
        s_dn = np.array(sweeps['down']['s_vals'])
        m_dn = np.array(sweeps['down']['m_vals'])
        
        ax = axes[idx]
        ax.plot(s_up, m_up, 'o-', linewidth=2, markersize=5, label='Up', color='#2E86AB')
        ax.plot(s_dn, m_dn, 's-', linewidth=2, markersize=5, label='Down', color='#A23B72')
        
        # Shade loop
        ax.fill_between(s_up, m_up, np.interp(s_up, s_dn, m_dn), alpha=0.2, color='gray')
        
        area = data['hysteresis_areas'].get(tau_str, 0)
        ax.set_title(f'$\\tau_J = {tau:.0f}$, Area$={area:.4f}$', fontsize=11)
        ax.set_xlabel('$s$', fontsize=10)
        ax.set_ylabel('$m = \\langle b \\rangle$', fontsize=10)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('Hysteresis Loops (E26)', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved {output_file}")
    plt.close()

def plot_area_vs_tau(data, output_file="e26_area_vs_tau.png"):
    """Plot hysteresis area vs memory time constant."""
    tau_vals = []
    areas = []
    
    for tau_str, area in data['hysteresis_areas'].items():
        tau_vals.append(float(tau_str))
        areas.append(area)
    
    # Sort
    sorted_pairs = sorted(zip(tau_vals, areas))
    tau_vals = [p[0] for p in sorted_pairs]
    areas = [p[1] for p in sorted_pairs]
    
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot(tau_vals, areas, 'o-', linewidth=2.5, markersize=9,
           color='#E63946', markerfacecolor='white', markeredgewidth=2)
    
    ax.set_xlabel('Memory time constant $\\tau_J$', fontsize=11)
    ax.set_ylabel('Hysteresis loop area', fontsize=11)
    ax.set_title('Memory-Dependent Hysteresis (E26)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved {output_file}")
    plt.close()

def main():
    """Generate all E26 publication figures."""
    results_file = Path("e26_lr_outputs/e26_lr_results.json")
    
    if not results_file.exists():
        print(f"Error: {results_file} not found!")
        print("Run e26_lr_selforg_mp.py first.")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    output_dir = Path("e26_lr_outputs")
    
    print("=" * 60)
    print("E26 Publication-Quality Plots")
    print("=" * 60)
    
    plot_correlation_length(data, output_dir / "e26_xi_vs_s.png")
    plot_hysteresis_loops(data, output_dir / "e26_hysteresis.png")
    plot_area_vs_tau(data, output_dir / "e26_area_vs_tau.png")
    
    print("\n" + "=" * 60)
    print("✓ All E26 figures generated")
    print("=" * 60)

if __name__ == "__main__":
    main()

