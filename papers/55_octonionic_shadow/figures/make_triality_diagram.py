"""
F5: Triality diagram — slots (V, S+, S-) ↔ (gen1, gen2, gen3) with ρ, σ arrows.

Geometry:
- The three ρ arrows (cyclic V → S+ → S- → V) bulge OUTWARD from the triangle.
- Each ρ label is placed at the arc midpoint pushed a further 0.45 units along
  the outward normal, with a white bounding box, so no glyph touches a line.
- The σ double-headed arrow between S+ and S- bulges INWARD (above the bottom
  edge); its label sits in the clear gap between the σ arc and the bottom ρ arc,
  also with a white bounding box.

Produces: figures/triality_diagram.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

fig, ax = plt.subplots(figsize=(6.0, 5.6))
ax.set_xlim(-3.0, 3.0)
ax.set_ylim(-3.0, 3.0)
ax.set_aspect('equal')
ax.axis('off')

# Three node positions (equilateral triangle): V top, S+ lower-left, S- lower-right
r = 1.75
positions = {
    'V':  np.array([r * np.cos(np.radians(90)),  r * np.sin(np.radians(90))]),
    'Sp': np.array([r * np.cos(np.radians(210)), r * np.sin(np.radians(210))]),
    'Sm': np.array([r * np.cos(np.radians(330)), r * np.sin(np.radians(330))]),
}

labels = {
    'V':  ('$V$', r'$\mathrm{gen}_1$', r'electron', '#B71C1C'),
    'Sp': ('$S^+$', r'$\mathrm{gen}_2$', r'muon', '#1565C0'),
    'Sm': ('$S^-$', r'$\mathrm{gen}_3$', r'tau', '#2E7D32'),
}

node_radius = 0.42

# Draw nodes
for key, pos in positions.items():
    x, y = pos
    slot_lbl, gen_lbl, phys_lbl, color = labels[key]
    ax.add_patch(mpatches.Circle((x, y), node_radius, color=color,
                                 alpha=0.15, zorder=2))
    ax.add_patch(mpatches.Circle((x, y), node_radius, fill=False,
                                 edgecolor=color, lw=2.0, zorder=3))
    ax.text(x, y + 0.10, slot_lbl, ha='center', va='center',
            fontsize=13, fontweight='bold', color=color, zorder=4)
    ax.text(x, y - 0.12, gen_lbl, ha='center', va='center',
            fontsize=9, color=color, zorder=4)
    outward = pos / np.linalg.norm(pos)
    ax.text(x + outward[0] * 0.80, y + outward[1] * 0.80,
            phys_lbl, ha='center', va='center',
            fontsize=9, color=color, style='italic')

# --- ρ arrows (cyclic: V → S+ → S- → V), bulging OUTWARD -------------------
# rad = +0.22 renders as an outward bulge for this traversal (verified).
rho_color = '#1565C0'
rho_rad = 0.22
shrink_pts = node_radius * 69

keys_cycle = ['V', 'Sp', 'Sm', 'V']
for i in range(3):
    src = positions[keys_cycle[i]]
    dst = positions[keys_cycle[i + 1]]
    ax.add_patch(FancyArrowPatch(src, dst,
                                 arrowstyle='->', color=rho_color, lw=2.0,
                                 mutation_scale=14,
                                 connectionstyle=f'arc3,rad={rho_rad}',
                                 shrinkA=shrink_pts, shrinkB=shrink_pts,
                                 zorder=5))

    # ρ label: arc apex = midpoint + outward-normal * sag; label a further
    # 0.45 units outward, with a white bbox so it can never merge with a line.
    mid = (src + dst) / 2.0
    u_out = mid / np.linalg.norm(mid)      # outward normal (from centroid)
    chord = np.linalg.norm(dst - src)
    sag = rho_rad * chord / 2.0            # approximate arc bulge
    label_pos = mid + u_out * (sag + 0.45)
    ax.text(label_pos[0], label_pos[1], r'$\rho$', fontsize=15,
            color=rho_color, fontweight='bold', ha='center', va='center',
            zorder=6,
            bbox=dict(facecolor='white', edgecolor='none', pad=1.5))

# --- σ arrow (transposition S+ ↔ S-), bulging INWARD (above bottom edge) ---
sigma_color = '#B71C1C'
sigma_rad = -0.28
src = positions['Sp']
dst = positions['Sm']
ax.add_patch(FancyArrowPatch(src, dst,
                             arrowstyle='<->', color=sigma_color, lw=2.2,
                             mutation_scale=14,
                             connectionstyle=f'arc3,rad={sigma_rad}',
                             shrinkA=shrink_pts, shrinkB=shrink_pts,
                             zorder=5))

# σ label: midway between the σ arc apex (inside, y ≈ -0.46) and the bottom
# ρ arc apex (outside, y ≈ -1.21) — clear space between the two arcs.
mid_bottom = (src + dst) / 2.0
chord = np.linalg.norm(dst - src)
sigma_apex_y = mid_bottom[1] + abs(sigma_rad) * chord / 2.0
rho_apex_y = mid_bottom[1] - rho_rad * chord / 2.0
sigma_label_y = 0.5 * (sigma_apex_y + rho_apex_y)
ax.text(0.0, sigma_label_y, r'$\sigma$', fontsize=15,
        color=sigma_color, ha='center', va='center', fontweight='bold',
        zorder=6,
        bbox=dict(facecolor='white', edgecolor='none', pad=1.5))

# Indicate V is fixed by σ
vx, vy = positions['V']
ax.text(vx, vy - node_radius - 0.22, r'fixed by $\sigma$',
        ha='center', va='top', fontsize=8, color=sigma_color,
        style='italic')

# Klein center V₄ (centroid)
ax.text(0, 0.28, r'$V_4 = Z(\mathrm{Spin}(8))$', ha='center', va='center',
        fontsize=8.5, color='#546E7A',
        bbox=dict(boxstyle='round,pad=0.3', fc='#ECEFF1', ec='#546E7A', lw=1.0),
        zorder=3)

# Title
ax.set_title(r'Triality $S_3 = \langle\rho,\sigma\rangle$ on Spin(8) representation slots'
             '\n' + r'$\mathrm{gen}_1 \leftrightarrow V$: Eisenstein norm selection (Theorem G6)',
             fontsize=10, pad=6)

# Legend
legend_patches = [
    mpatches.Patch(color=rho_color, alpha=0.7, label=r'$\rho$: cyclic (order 3)'),
    mpatches.Patch(color=sigma_color, alpha=0.7, label=r'$\sigma$: spinor swap (order 2)'),
]
ax.legend(handles=legend_patches, loc='lower right', fontsize=8.5,
          bbox_to_anchor=(1.0, -0.02), framealpha=0.9)

plt.tight_layout()
plt.savefig('triality_diagram.pdf', bbox_inches='tight', dpi=150)
plt.savefig('triality_diagram.png', bbox_inches='tight', dpi=200)
print("F5: triality_diagram.pdf written")
