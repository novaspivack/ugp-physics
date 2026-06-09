#!/usr/bin/env python3
"""
E28 Publication-Quality Plots: Lindblad Rate Extraction
=========================================================

Generates figures for MFRR manuscript §15.X (E9c validation).
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.stats import linregress

rcParams['font.size'] = 11
rcParams['font.family'] = 'serif'
rcParams['axes.linewidth'] = 1.0

def load_data():
    """Load E28 results."""
    with open('e28_lindblad_outputs/e28_results.json', 'r') as f:
        return json.load(f)

def plot_gamma_vs_W_norm(data):
    """Plot Lindblad rates vs spectral norm ||W||₂."""
    summary = data['summary']
    W_norm = np.array(summary['W_norm'])
    gamma_m = np.array(summary['gamma_m'])
    gamma_spread = np.array(summary['gamma_spread'])
    J = np.array(summary['J'])
    
    # Remove NaNs
    valid_m = ~np.isnan(gamma_m)
    valid_s = ~np.isnan(gamma_spread)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # γ_m vs ||W||₂
    if np.sum(valid_m) >= 2:
        W_m = W_norm[valid_m]
        g_m = gamma_m[valid_m]
        J_m = J[valid_m]
        
        slope, intercept, r_value, _, _ = linregress(W_m, g_m)
        
        scatter1 = ax1.scatter(W_m, g_m, c=J_m, cmap='viridis', s=100,
                               edgecolors='black', linewidths=0.5, zorder=3)
        
        W_fit = np.linspace(W_m.min(), W_m.max(), 100)
        g_fit = slope * W_fit + intercept
        ax1.plot(W_fit, g_fit, 'r--', lw=2, alpha=0.7,
                label=f'$\\gamma_m$ = {slope:.3f}||W||₂ + {intercept:.3f}\n$R^2$ = {r_value**2:.4f}')
        
        ax1.set_xlabel(r'Spectral norm $\|W\|_2$', fontsize=13)
        ax1.set_ylabel(r'Lindblad rate $\gamma_m$ (magnetization)', fontsize=13)
        ax1.set_title('Magnetization Damping Rate', fontsize=12, fontweight='bold')
        ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.3, ls='--')
        plt.colorbar(scatter1, ax=ax1, label='Coupling $J$')
    
    # γ_spread vs ||W||₂
    if np.sum(valid_s) >= 2:
        W_s = W_norm[valid_s]
        g_s = gamma_spread[valid_s]
        J_s = J[valid_s]
        
        slope, intercept, r_value, _, _ = linregress(W_s, g_s)
        
        scatter2 = ax2.scatter(W_s, g_s, c=J_s, cmap='plasma', s=100,
                               edgecolors='black', linewidths=0.5, zorder=3)
        
        W_fit = np.linspace(W_s.min(), W_s.max(), 100)
        g_fit = slope * W_fit + intercept
        ax2.plot(W_fit, g_fit, 'b--', lw=2, alpha=0.7,
                label=f'$\\gamma_{{spread}}$ = {slope:.3f}||W||₂ + {intercept:.3f}\n$R^2$ = {r_value**2:.4f}')
        
        ax2.set_xlabel(r'Spectral norm $\|W\|_2$', fontsize=13)
        ax2.set_ylabel(r'Lindblad rate $\gamma_{spread}$ (coherence)', fontsize=13)
        ax2.set_title('Coherence Damping Rate', fontsize=12, fontweight='bold')
        ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax2.grid(True, alpha=0.3, ls='--')
        plt.colorbar(scatter2, ax=ax2, label='Coupling $J$')
    
    plt.suptitle('E9c: Lindblad Rates vs Ensemble Spectrum', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('e28_lindblad_outputs/e28_gamma_vs_W_norm.png', dpi=300, bbox_inches='tight')
    print("✓ Saved e28_lindblad_outputs/e28_gamma_vs_W_norm.png")
    plt.close()

def plot_gamma_vs_Psi(data):
    """Plot Lindblad rates vs coherence penalty Γ(Ψ)."""
    summary = data['summary']
    Gamma_Psi = np.array(summary['Gamma_Psi'])
    gamma_m = np.array(summary['gamma_m'])
    J = np.array(summary['J'])
    
    valid = ~np.isnan(gamma_m)
    if np.sum(valid) < 2:
        print("⚠️  Insufficient valid data for γ vs Γ(Ψ)")
        return
    
    Psi_valid = Gamma_Psi[valid]
    g_valid = gamma_m[valid]
    J_valid = J[valid]
    
    slope, intercept, r_value, _, _ = linregress(Psi_valid, g_valid)
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    scatter = ax.scatter(Psi_valid, g_valid, c=J_valid, cmap='coolwarm', s=100,
                        edgecolors='black', linewidths=0.5, zorder=3)
    
    Psi_fit = np.linspace(Psi_valid.min(), Psi_valid.max(), 100)
    g_fit = slope * Psi_fit + intercept
    ax.plot(Psi_fit, g_fit, 'k--', lw=2, alpha=0.7,
           label=f'$\\gamma_m$ = {slope:.3f}Γ(Ψ) + {intercept:.3f}\n$R^2$ = {r_value**2:.4f}')
    
    ax.set_xlabel(r'Coherence penalty $\Gamma(\Psi)$', fontsize=13)
    ax.set_ylabel(r'Lindblad rate $\gamma_m$', fontsize=13)
    ax.set_title('E9c: Lindblad Rate vs Coherence Penalty', fontsize=14, fontweight='bold')
    ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, ls='--')
    plt.colorbar(scatter, ax=ax, label='Coupling $J$')
    
    plt.tight_layout()
    plt.savefig('e28_lindblad_outputs/e28_gamma_vs_Psi.png', dpi=300, bbox_inches='tight')
    print("✓ Saved e28_lindblad_outputs/e28_gamma_vs_Psi.png")
    plt.close()

def main():
    """Generate all E28 plots."""
    print("=" * 80)
    print("E28 Publication-Quality Plots")
    print("=" * 80)
    
    data = load_data()
    
    plot_gamma_vs_W_norm(data)
    plot_gamma_vs_Psi(data)
    
    print("")
    print("=" * 80)
    print("✓ All E28 figures generated")
    print("=" * 80)

if __name__ == '__main__':
    main()

