#!/usr/bin/env python3
"""
Create unified picture diagram for TE_2.3
Shows: UGP → GTE → SRRG → SM + Nuclear Physics
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib
matplotlib.use('Agg')

# Set publication-quality parameters
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11

# Create figure
fig, ax = plt.subplots(figsize=(12, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Define boxes
boxes = {
    'ugp': FancyBboxPatch((3.5, 8.5), 3, 0.8, boxstyle="round,pad=0.1", 
                          edgecolor='black', facecolor='lightblue', linewidth=2.5),
    'gte': FancyBboxPatch((3.5, 7), 3, 0.8, boxstyle="round,pad=0.1", 
                          edgecolor='black', facecolor='lightgreen', linewidth=2.5),
    'srrg': FancyBboxPatch((3.5, 5.5), 3, 0.8, boxstyle="round,pad=0.1", 
                           edgecolor='black', facecolor='lightyellow', linewidth=2.5),
    'sm': FancyBboxPatch((0.5, 3.5), 3.5, 1, boxstyle="round,pad=0.1", 
                         edgecolor='darkred', facecolor='lightcoral', linewidth=2.5),
    'nuclear': FancyBboxPatch((6, 3.5), 3.5, 1, boxstyle="round,pad=0.1", 
                              edgecolor='darkred', facecolor='lightcoral', linewidth=2.5)
}

# Add boxes to plot
for box in boxes.values():
    ax.add_patch(box)

# Add text labels
ax.text(5, 8.9, 'Universal Generative Principle (UGP)', ha='center', va='center', 
        fontsize=13, weight='bold')
ax.text(5, 7.4, 'Generative Theory of Everything (GTE)', ha='center', va='center', 
        fontsize=12, weight='bold')
ax.text(5, 7.15, '(Discrete triple structure)', ha='center', va='center', fontsize=10, style='italic')
ax.text(5, 5.9, 'Self-Referential RG (SRRG) Flow', ha='center', va='center', 
        fontsize=12, weight='bold')
ax.text(5, 5.65, '(Viability functional $F[S]$)', ha='center', va='center', fontsize=10, style='italic')
ax.text(2.25, 4, 'Standard Model', ha='center', va='center', fontsize=13, weight='bold')
ax.text(7.75, 4, 'Nuclear Physics', ha='center', va='center', fontsize=13, weight='bold')

# Add arrows
arrow_props = dict(arrowstyle='->', mutation_scale=25, linewidth=3, color='black')
arrows = [
    FancyArrowPatch((5, 8.5), (5, 7.8), **arrow_props),
    FancyArrowPatch((5, 7), (5, 6.3), **arrow_props),
    FancyArrowPatch((4.5, 5.5), (3, 4.5), **arrow_props),
    FancyArrowPatch((5.5, 5.5), (7, 4.5), **arrow_props)
]

for arrow in arrows:
    ax.add_patch(arrow)

# Add validation boxes (SM)
sm_validation = [
    '• TS1: 97% attraction',
    '• TS3: Gauge running',
    '• TS9: c-function',
    '• UGP_lab: $\\theta_W \\approx \\pi/12$'
]
ax.text(2.25, 2.8, '\n'.join(sm_validation), 
        ha='center', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, edgecolor='black', linewidth=1.5))

# Add validation boxes (Nuclear)
nuclear_validation = [
    '• TS5: 0.48 MeV MAE',
    '• PERIODIC_TABLE_APP',
    '• AME-2020: 0.489 MeV',
    '• 2,457 nuclei, $R^2 = 0.9996$'
]
ax.text(7.75, 2.8, '\n'.join(nuclear_validation), 
        ha='center', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, edgecolor='black', linewidth=1.5))

# Add SM details
sm_details = [
    'Gauge group:',
    'SU(3)×SU(2)×U(1)',
    '3 generations',
    'Quarter-Lock'
]
ax.text(2.25, 4.7, '\n'.join(sm_details), 
        ha='center', va='bottom', fontsize=8, style='italic')

# Add nuclear details
nuclear_details = [
    'Binding energies',
    'Magic numbers',
    'Shell structure',
    'Island of stability'
]
ax.text(7.75, 4.7, '\n'.join(nuclear_details), 
        ha='center', va='bottom', fontsize=8, style='italic')

# Add title
ax.text(5, 9.7, 'TE_2.3: Unified Picture', ha='center', va='center', 
        fontsize=16, weight='bold',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=2))

# Add caption
caption = 'Same UGP/GTE/SRRG structure uniquely determines both SM gauge couplings and nuclear binding energies'
ax.text(5, 0.3, caption, ha='center', va='center', fontsize=10, style='italic', wrap=True)

plt.tight_layout()
plt.savefig('unified_picture.pdf', dpi=300, bbox_inches='tight')
plt.savefig('unified_picture.png', dpi=300, bbox_inches='tight')
print("Created unified_picture.pdf and .png")
plt.close()

