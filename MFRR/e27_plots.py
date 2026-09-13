#!/usr/bin/env python3
"""
E27 Publication-Quality Plots: Decoherence Rates vs Ensemble Spectrum
======================================================================

Generates figures for MFRR manuscript §15.X (E9b validation).

Cross-reference: MFRR manuscript §7.Y (Thm. EAME-Lindblad)
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.stats import linregress

# Publication settings
rcParams['font.size'] = 11
rcParams['font.family'] = 'serif'
rcParams['axes.linewidth'] = 1.0

def load_data():
    """Load E27 results."""
    with open('e27_decoherence_outputs/e27_results.json', 'r') as f:
        return json.load(f)

def plot_Gamma_vs_W_norm(data):
    """Plot decoherence rate Γ vs spectral norm ||W||₂."""
    summary = data['summary']
    W_norm = np.array(summary['W_norm'])
    Gamma = np.array(summary['Gamma'])
    J = np.array(summary['J'])
    
    # Remove NaNs
    valid = ~np.isnan(Gamma)
    W_norm_valid = W_norm[valid]
    Gamma_valid = Gamma[valid]
    J_valid = J[valid]
    
    if len(Gamma_valid) == 0:
        print("⚠️  No valid Γ fits")
        return
    
    # Linear fit
    slope, intercept, r_value, p_value, std_err = linregress(W_norm_valid, Gamma_valid)
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # Data points
    scatter = ax.scatter(W_norm_valid, Gamma_valid, c=J_valid, cmap='viridis',
                        s=100, edgecolors='black', linewidths=0.5, zorder=3)
    
    # Fit line
    W_fit = np.linspace(W_norm_valid.min(), W_norm_valid.max(), 100)
    Gamma_fit = slope * W_fit + intercept
    ax.plot(W_fit, Gamma_fit, 'r--', lw=2, alpha=0.7, 
           label=f'Linear fit: Γ = {slope:.4f}||W||₂ + {intercept:.4f}\n$R^2$ = {r_value**2:.4f}')
    
    ax.set_xlabel(r'Spectral norm $\|W\|_2$', fontsize=13)
    ax.set_ylabel(r'Decoherence rate $\Gamma$', fontsize=13)
    ax.set_title('E9b: Decoherence Rate vs Ensemble Spectrum', fontsize=14, fontweight='bold')
    ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, ls='--')
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='Coupling $J$')
    
    plt.tight_layout()
    plt.savefig('e27_decoherence_outputs/e27_Gamma_vs_W_norm.png', dpi=300, bbox_inches='tight')
    print("✓ Saved e27_decoherence_outputs/e27_Gamma_vs_W_norm.png")
    plt.close()

def plot_Gamma_vs_Psi(data):
    """Plot decoherence rate Γ vs coherence penalty Γ(Ψ)."""
    summary = data['summary']
    Gamma_Psi = np.array(summary['Gamma_Psi'])
    Gamma = np.array(summary['Gamma'])
    J = np.array(summary['J'])
    
    # Remove NaNs
    valid = ~np.isnan(Gamma)
    Gamma_Psi_valid = Gamma_Psi[valid]
    Gamma_valid = Gamma[valid]
    J_valid = J[valid]
    
    if len(Gamma_valid) == 0:
        print("⚠️  No valid Γ fits")
        return
    
    # Linear fit
    slope, intercept, r_value, p_value, std_err = linregress(Gamma_Psi_valid, Gamma_valid)
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # Data points
    scatter = ax.scatter(Gamma_Psi_valid, Gamma_valid, c=J_valid, cmap='plasma',
                        s=100, edgecolors='black', linewidths=0.5, zorder=3)
    
    # Fit line
    Psi_fit = np.linspace(Gamma_Psi_valid.min(), Gamma_Psi_valid.max(), 100)
    Gamma_fit = slope * Psi_fit + intercept
    ax.plot(Psi_fit, Gamma_fit, 'b--', lw=2, alpha=0.7,
           label=f'Linear fit: Γ = {slope:.4f}Γ(Ψ) + {intercept:.4f}\n$R^2$ = {r_value**2:.4f}')
    
    ax.set_xlabel(r'Coherence penalty $\Gamma(\Psi)$', fontsize=13)
    ax.set_ylabel(r'Decoherence rate $\Gamma$', fontsize=13)
    ax.set_title('E9b: Decoherence Rate vs Coherence Penalty', fontsize=14, fontweight='bold')
    ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, ls='--')
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='Coupling $J$')
    
    plt.tight_layout()
    plt.savefig('e27_decoherence_outputs/e27_Gamma_vs_Psi.png', dpi=300, bbox_inches='tight')
    print("✓ Saved e27_decoherence_outputs/e27_Gamma_vs_Psi.png")
    plt.close()

def plot_autocorrelation_curves(data):
    """Plot example autocorrelation curves C(Δt) with fits."""
    results = data['results']
    
    # Select 4 representative J values
    n_show = min(4, len(results))
    indices = np.linspace(0, len(results)-1, n_show, dtype=int)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    
    for i, idx in enumerate(indices):
        r = results[idx]
        C = np.array(r['C_curve'])
        times = np.arange(len(C)) * data['params']['dt']
        
        ax = axes[i]
        
        # Data
        ax.plot(times, C, 'o-', color='steelblue', markersize=4, lw=1.5, alpha=0.8, label='Data')
        
        # Fit
        if r['fit_success']:
            Gamma, A, C_inf = r['Gamma'], r['A'], r['C_inf']
            C_fit = A * np.exp(-Gamma * times) + C_inf
            ax.plot(times, C_fit, 'r--', lw=2, alpha=0.7,
                   label=f'Fit: $\Gamma$ = {Gamma:.4f}')
        
        ax.set_xlabel(r'Time lag $\Delta t$', fontsize=11)
        ax.set_ylabel(r'Autocorrelation $C(\Delta t)$', fontsize=11)
        ax.set_title(f'$J$ = {r["J"]:.3f}, $\|W\|_2$ = {r["W_norm"]:.3f}', fontsize=11)
        ax.legend(loc='best', frameon=True)
        ax.grid(True, alpha=0.3, ls='--')
    
    plt.suptitle('E9b: Time-Autocorrelation Decay', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig('e27_decoherence_outputs/e27_autocorr_curves.png', dpi=300, bbox_inches='tight')
    print("✓ Saved e27_decoherence_outputs/e27_autocorr_curves.png")
    plt.close()

def main():
    """Generate all E27 plots."""
    print("=" * 80)
    print("E27 Publication-Quality Plots")
    print("=" * 80)
    
    data = load_data()
    
    plot_Gamma_vs_W_norm(data)
    plot_Gamma_vs_Psi(data)
    plot_autocorrelation_curves(data)
    
    print("")
    print("=" * 80)
    print("✓ All E27 figures generated")
    print("=" * 80)

if __name__ == '__main__':
    main()

