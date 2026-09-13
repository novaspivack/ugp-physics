#!/usr/bin/env python3
"""
Create Hessian eigenvalue spectrum figure for TE_2.3
Source: TE_2_3_SM_Nuclear_Rigidity Phase 1 results
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Set publication-quality parameters
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

# Eigenvalues from Phase 1 results
# Full 8D space (includes 3 near-zero gauge directions)
eigenvalues_full = np.array([
    -0.001,  # Near-zero (Quarter-Lock)
    0.000,   # Near-zero (Higgs correlation)
    0.001,   # Near-zero (Higgs rescaling)
    2.005,   # Physical mode 1
    2.891,   # Physical mode 2
    3.456,   # Physical mode 3
    5.123,   # Physical mode 4
    8.202    # Physical mode 5
])

# Physical 5D space (after gauge projection)
eigenvalues_phys = np.array([2.005, 2.891, 3.456, 5.123, 8.202])

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Panel (a): Full 8D spectrum
colors_full = ['red' if abs(ev) < 0.01 else 'steelblue' for ev in eigenvalues_full]
bars1 = ax1.bar(range(1, 9), eigenvalues_full, color=colors_full, alpha=0.7, edgecolor='black', linewidth=1.5)
ax1.axhline(0, color='black', linestyle='-', linewidth=1)
ax1.axhline(0.01, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Gauge threshold')
ax1.axhline(-0.01, color='red', linestyle='--', linewidth=1, alpha=0.5)
ax1.set_xlabel('Eigenvalue Index', fontweight='bold')
ax1.set_ylabel(r'Eigenvalue $\lambda_i$', fontweight='bold')
ax1.set_title('(a) Full 8D Hessian Spectrum', fontweight='bold')
ax1.set_xticks(range(1, 9))
ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
ax1.legend(loc='upper left')
ax1.text(0.5, 0.05, '3 gauge redundancies\n(near-zero eigenvalues)', 
         transform=ax1.transAxes, ha='center', va='bottom', fontsize=9,
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

# Panel (b): Physical 5D spectrum
bars2 = ax2.bar(range(1, 6), eigenvalues_phys, color='forestgreen', alpha=0.7, edgecolor='black', linewidth=1.5)
ax2.axhline(0, color='red', linestyle='--', linewidth=2, label=r'$\lambda = 0$')
ax2.set_xlabel('Eigenvalue Index', fontweight='bold')
ax2.set_ylabel(r'Eigenvalue $\lambda_i$', fontweight='bold')
ax2.set_title('(b) Physical 5D Hessian Spectrum\n(Gauge-Projected)', fontweight='bold')
ax2.set_xticks(range(1, 6))
ax2.set_ylim([0, 9])
ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
ax2.legend(loc='upper left')
ax2.text(0.5, 0.95, r'$\lambda_{\min} = 2.005 > 0$ ✓' + '\nLocal rigidity confirmed', 
         transform=ax2.transAxes, ha='center', va='top', fontsize=11, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8, edgecolor='darkgreen', linewidth=2))

plt.tight_layout()
plt.savefig('hessian_spectrum.pdf', dpi=300, bbox_inches='tight')
plt.savefig('hessian_spectrum.png', dpi=300, bbox_inches='tight')
print("✓ Created hessian_spectrum.pdf and .png")
plt.close()

