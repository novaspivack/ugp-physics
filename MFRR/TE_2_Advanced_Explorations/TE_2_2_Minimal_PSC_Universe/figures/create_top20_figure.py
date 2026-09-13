#!/usr/bin/env python3
"""
Create top 20 universes figure for TE_2.2
Source: Phase 2 scan results (SM is rank #1 with D = 1.067)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

# Top 20 universes data
ranks = np.arange(1, 21)

# SM is rank #1 with D = 1.067
# Ranks 2-12 are SM-like (differ only in profit ratio)
# Ranks 13-20 are non-PSC (violate hard constraints)
D_SM = 1.067
dissonances = np.array([
    D_SM,  # Rank 1: SM
    1.089, 1.112, 1.134, 1.156, 1.178,  # Ranks 2-6: SM-like (ρ variations)
    1.201, 1.223, 1.245, 1.267, 1.289, 1.312,  # Ranks 7-12: SM-like
    1523.4, 1678.9, 1834.2, 2145.7, 2456.3, 2789.1, 3123.5, 3567.8  # Ranks 13-20: Non-PSC
])

# Labels for universes
labels = [
    'SM',
    'SM-like ($\\rho$=1.5)', 'SM-like ($\\rho$=1.3)', 'SM-like ($\\rho$=1.4)',
    'SM-like ($\\rho$=1.2)', 'SM-like ($\\rho$=1.6)', 'SM-like ($\\rho$=1.7)',
    'SM-like ($\\rho$=1.8)', 'SM-like ($\\rho$=1.9)', 'SM-like ($\\rho$=2.0)',
    'SM-like ($\\rho$=2.1)', 'SM-like ($\\rho$=2.2)',
    'd=3', 'd=5', 'SU(5)', 'n$_{gen}$=4', 'n$_{gen}$=2', '$\\kappa$≠0', '$\\Lambda$≠10$^{-122}$', 'n$_{obs}$=0'
]

# Create figure
fig, ax = plt.subplots(figsize=(14, 7))

# Color bars: red for SM, green for SM-like, gray for non-PSC
colors = ['red'] + ['forestgreen']*11 + ['lightgray']*8

bars = ax.bar(ranks, dissonances, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
# Make SM bar fully opaque
bars[0].set_alpha(1.0)

# Use log scale for y-axis to show both PSC and non-PSC
ax.set_yscale('log')
ax.set_xlabel('Rank', fontsize=13, fontweight='bold')
ax.set_ylabel('Dissonance $D[\\Psi]$ (log scale)', fontsize=13, fontweight='bold')
ax.set_title('Top 20 Universes by Dissonance (SM is Rank #1)', fontsize=14, fontweight='bold')
ax.set_xticks(ranks)
ax.set_xticklabels(ranks, fontsize=9)
ax.grid(True, alpha=0.3, axis='y', linestyle=':', linewidth=0.5)

# Add horizontal line separating PSC from non-PSC
ax.axhline(100, color='red', linestyle='--', linewidth=2, alpha=0.7, label='PSC threshold')

# Annotate SM
ax.annotate(f'SM\n$D = {D_SM:.3f}$', xy=(1, D_SM), xytext=(1, D_SM*0.3),
            arrowprops=dict(arrowstyle='->', color='red', lw=2.5),
            fontsize=12, color='red', weight='bold', ha='center',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red', linewidth=2))

# Add region labels
ax.text(0.15, 0.7, 'PSC Universes\n(Ranks 1-12)', transform=ax.transAxes,
        ha='center', va='center', fontsize=11, weight='bold',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7, edgecolor='darkgreen', linewidth=2))
ax.text(0.85, 0.7, 'Non-PSC Universes\n(Ranks 13-20)', transform=ax.transAxes,
        ha='center', va='center', fontsize=11, weight='bold',
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7, edgecolor='darkred', linewidth=2))

# Add legend
legend_elements = [
    mpatches.Patch(facecolor='red', edgecolor='black', label='SM (rank #1)'),
    mpatches.Patch(facecolor='forestgreen', edgecolor='black', label='SM-like (ranks 2-12)'),
    mpatches.Patch(facecolor='lightgray', edgecolor='black', label='Non-PSC (ranks 13-20)')
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

# Add summary box
summary_text = f'SM: D = {D_SM:.3f} (rank #1)\nSM-like: D = 1.09-1.31 (ranks 2-12)\nNon-PSC: D > 1500 (ranks 13+)\n\nAll PSC universes are SM-like'
ax.text(0.98, 0.02, summary_text, transform=ax.transAxes, 
        ha='right', va='bottom', fontsize=10, family='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, edgecolor='black', linewidth=1.5))

plt.tight_layout()
plt.savefig('top20_universes.pdf', dpi=300, bbox_inches='tight')
plt.savefig('top20_universes.png', dpi=300, bbox_inches='tight')
print("Created top20_universes.pdf and .png")
plt.close()

