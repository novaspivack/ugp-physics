"""
F3: Weight ladder 1 ⊕ 3 ⊕ 3̄ ⊕ 1 for the color rung.
Produces: figures/weight_ladder.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(5.5, 4.2))
ax.set_xlim(-0.3, 4.8)
ax.set_ylim(-0.6, 4.2)
ax.axis('off')

# Charge levels: Q = 0, 1/3, 2/3, 1
charges = [0, 1/3, 2/3, 1]
multiplicities = [1, 3, 3, 1]
labels_phys = [r'$\nu_R$  $(Q=0)$', r'$\bar{d}$  $(Q=1/3)$',
               r'$u$  $(Q=2/3)$', r'$e^+$  $(Q=1)$']
colors = ['#9C27B0', '#2196F3', '#F44336', '#4CAF50']
sector_labels = ['$\mathbf{1}$', '$\mathbf{3}$', '$\mathbf{\overline{3}}$', '$\mathbf{1}$']

y_positions = [0.3, 1.3, 2.3, 3.3]
dot_x_base = 1.0
dot_spacing = 0.38

for i, (Q, mult, label, color, sec, yw) in enumerate(
        zip(charges, multiplicities, labels_phys, colors, sector_labels, y_positions)):

    # Draw horizontal level line
    ax.axhline(y=yw + 0.25, xmin=0.05, xmax=0.95,
               color=color, lw=2.0, alpha=0.25, zorder=1)

    # Draw dots for multiplicity
    for k in range(mult):
        x = dot_x_base + k * dot_spacing
        ax.plot(x, yw + 0.25, 'o', color=color, markersize=14, zorder=3,
                alpha=0.9)

    # Multiplicity label (sector)
    ax.text(0.0, yw + 0.25, sec, fontsize=14, ha='right', va='center',
            color=color, fontweight='bold')

    # Physical label
    ax.text(dot_x_base + mult * dot_spacing + 0.1, yw + 0.25,
            label, fontsize=10, ha='left', va='center')

    # Charge label on right
    ax.text(4.7, yw + 0.25, f'$Q={Q:.0f}$' if Q in (0, 1)
            else (f'$Q=1/3$' if Q < 0.4 else f'$Q=2/3$'),
            fontsize=9, ha='right', va='center', color='#555')

# Title and labels
ax.set_title(r'Weight decomposition: $\mathbf{1}\oplus\mathbf{3}\oplus\overline{\mathbf{3}}\oplus\mathbf{1}$'
             '\n' + r'from the octonionic pencil ($N_c = 3$ lines, $Q = N/3$)',
             fontsize=10.5, pad=8)

ax.text(-0.25, 2.0, r'$Q$', fontsize=12, ha='center', va='center', rotation=90,
        style='italic')

# Arrow for CAR ladder
ax.annotate('', xy=(dot_x_base + 0.19, 3.35), xytext=(dot_x_base + 0.19, 0.55),
            arrowprops=dict(arrowstyle='<->', color='#795548', lw=1.5))
ax.text(dot_x_base + 0.19 - 0.15, 2.0, r'$\alpha_k$', fontsize=9,
        ha='right', va='center', color='#795548')

plt.tight_layout()
plt.savefig('weight_ladder.pdf', bbox_inches='tight', dpi=150)
plt.savefig('weight_ladder.png', bbox_inches='tight', dpi=150)
print("F3: weight_ladder.pdf written")
