"""
F1: Fano plane with QR(7) pencil highlighted.
Produces: figures/fano_plane_qr7.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# Points of the Fano plane on Z/7, arranged in a circle plus center
# Standard Fano labeling: points 0..6, center at 0
# Place 0 at bottom, 1..6 around the heptagon
N = 7
theta = np.linspace(0, 2*np.pi, N, endpoint=False) + np.pi/2  # start at top
# Point layout: 0 = center, 1-6 on the circle
# Actually use a layout where point 0 (apex) is at bottom-center
# and 1..6 arranged on circle for visual clarity

# Better: arrange all 7 points on a circle for symmetry
# Then draw the 7 lines of the Fano plane
theta_pts = np.linspace(0, 2*np.pi, 7, endpoint=False) + np.pi/2

coords = {i: (np.cos(theta_pts[i]), np.sin(theta_pts[i])) for i in range(7)}

# The 7 lines of the Fano plane: translates of D = {1,2,4} mod 7
D = {1, 2, 4}
lines = []
for t in range(7):
    line = tuple(sorted((t + d) % 7 for d in D))
    if line not in lines:
        lines.append(line)
lines = list(set(lines))
lines.sort()

# The three pencil lines through point 0 (apex)
apex = 0
pencil_lines = [l for l in lines if apex in l]

# Color scheme for pencil
pencil_colors = ['#2196F3', '#FF9800', '#4CAF50']  # blue, orange, green
other_color = '#BDBDBD'

fig, ax = plt.subplots(1, 1, figsize=(5.5, 5.5))
ax.set_aspect('equal')
ax.axis('off')

# Draw all 7 lines, pencil lines highlighted
for l in lines:
    p1, p2, p3 = l
    xs = [coords[p1][0], coords[p2][0], coords[p3][0]]
    ys = [coords[p1][1], coords[p2][1], coords[p3][1]]

    if l in pencil_lines:
        idx = pencil_lines.index(l)
        color = pencil_colors[idx]
        lw = 2.4
        alpha = 0.85
    else:
        color = other_color
        lw = 1.4
        alpha = 0.65

    # For a Fano line, draw the chord between all three pairs
    for i in range(3):
        for j in range(i+1, 3):
            xi = [xs[i], xs[j]]
            yi = [ys[i], ys[j]]
            ax.plot(xi, yi, '-', color=color, lw=lw, alpha=alpha, zorder=1)

# Draw points
for i, (x, y) in coords.items():
    if i == apex:
        ax.plot(x, y, 'o', color='#B71C1C', markersize=12, zorder=4)
        ax.annotate(f'$0$\n(apex)', (x, y), fontsize=9,
                    ha='center', va='top', xytext=(0, -14), textcoords='offset points',
                    fontweight='bold', color='#B71C1C')
    else:
        ax.plot(x, y, 'o', color='#37474F', markersize=10, zorder=4)
        # label offset radially outward
        r = 1.18
        ax.annotate(f'${i}$', (x, y), fontsize=10,
                    ha='center', va='center',
                    xytext=(r * np.cos(theta_pts[i]) * 70,
                            r * np.sin(theta_pts[i]) * 70),
                    textcoords='offset points')

# Legend
legend_patches = [
    mpatches.Patch(color=pencil_colors[0], label=f'Pencil line $\\{{{0,1,3}\\}}$'),
    mpatches.Patch(color=pencil_colors[1], label=f'Pencil line $\\{{{0,2,6}\\}}$'),
    mpatches.Patch(color=pencil_colors[2], label=f'Pencil line $\\{{{0,4,5}\\}}$'),
    mpatches.Patch(color=other_color, label='Other Fano lines'),
]
ax.legend(handles=legend_patches, loc='lower center', bbox_to_anchor=(0.5, -0.04),
          fontsize=8, ncol=2, framealpha=0.9)

ax.set_title('Fano plane on $\\mathbb{Z}/7$: pencil through apex $0$',
             fontsize=11, pad=10)
ax.set_xlim(-1.4, 1.4)
ax.set_ylim(-1.5, 1.4)

plt.tight_layout()
plt.savefig('fano_plane_qr7.pdf', bbox_inches='tight', dpi=150)
plt.savefig('fano_plane_qr7.png', bbox_inches='tight', dpi=150)
print("F1: fano_plane_qr7.pdf written")
