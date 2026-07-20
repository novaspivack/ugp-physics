import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from .util import phi, Lambda

def main():
    df = pd.read_csv("results/l1_lap_records.csv")
    
    with open("results/l1_lap_summary.json", "r") as f:
        summary = json.load(f)
    
    intercept = summary["intercept"]
    slope = summary["slope"]
    R2 = summary["R2"]
    status = summary["status"]
    
    log_phi_Omega = np.log(df["Omega"].values) / np.log(phi())
    d_eff = df["d_eff"].values
    
    Omega_sorted = np.sort(df["Omega"].values)
    log_phi_sorted = np.log(Omega_sorted) / np.log(phi())
    fit_line = intercept + slope * log_phi_sorted
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    colors = {'lattice4d': '#1f77b4', 'rgg4d': '#ff7f0e', 'lattice4d_sw': '#2ca02c'}
    markers = {'lattice4d': 'o', 'rgg4d': 's', 'lattice4d_sw': '^'}
    
    for graph_type in df["graph"].unique():
        prefix = graph_type.rsplit('_', 1)[0] if '_n' in graph_type or '_N' in graph_type else graph_type
        mask = df["graph"].str.startswith(prefix)
        ax.scatter(log_phi_Omega[mask], d_eff[mask], 
                  c=colors.get(prefix, 'gray'), 
                  marker=markers.get(prefix, 'x'),
                  s=100, alpha=0.7, 
                  label=prefix.replace('_', ' ').title(), 
                  edgecolors='black', linewidths=0.5)
    
    ax.plot(log_phi_sorted, fit_line, 'k--', linewidth=2, alpha=0.8, 
            label=f'Fit: $D_{{eff}} = {intercept:.3f} + {slope:.3f} \\log_\\phi(\\Omega)$')
    
    ax.axhline(y=4.0, color='gray', linestyle=':', linewidth=1.5, alpha=0.5, label='Target $d=4$')
    
    ax.set_xlabel('$\\log_\\phi(\\Omega)$ (Geometric Complexity)', fontsize=14, fontweight='bold')
    ax.set_ylabel('$D_{eff}$ (Effective Spectral Dimension)', fontsize=14, fontweight='bold')
    ax.set_title(f'L1: Λ–Φ Duality Validation (Heat-Trace Method)\n'
                f'$\\Lambda = {Lambda():.4f}$ | $R^2 = {R2:.3f}$ | Status: {status}', 
                fontsize=15, fontweight='bold', pad=20)
    
    ax.legend(loc='best', fontsize=11, framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    textstr = f'Measured slope: ${slope:.4f}$\n'
    textstr += f'Expected ($\\Lambda$): ${Lambda():.4f}$\n'
    textstr += f'Deviation: ${abs(slope - Lambda())/Lambda() * 100:.1f}\\%$\n'
    textstr += f'Intercept: ${intercept:.3f}$ (target: $4.0$)'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig("results/fig_l1_lap_fit.png", dpi=300, bbox_inches='tight')
    print("✓ Plot saved to results/fig_l1_lap_fit.png")
    
    plt.close()

if __name__ == "__main__":
    main()

