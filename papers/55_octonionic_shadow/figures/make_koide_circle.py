"""
F6: Koide phase torsor with δ = 2/9 marked.

Representation: the UNIT PHASE CIRCLE (the Z₃-torsor {1, ω, ω²} rotated by δ).
Each generation k occupies the phase φ_k = δ − 2πk/3 on the unit circle; the
Koide parametrization √m_k = A(1 + √2|z|cos φ_k) assigns the mass to that
phase. The radii in this figure are all equal (unit circle) — the figure shows
the PHASES, not the magnitudes √m_k (which differ by a factor ~59 between the
electron and the tau and cannot be drawn to scale on one circle).

Numerical anchors (from electroweak_housing_closure.py on PDG masses):
  Koide Q = (Σm)/(Σ√m)² = 0.6666605  (2/3 − 6×10⁻⁶)
  |z| = 1 − 9×10⁻⁶
  torsor-invariant angle |δ mod 2π/3| = 0.222229631 = 2/9 + 7.41×10⁻⁶

Produces: figures/koide_circle.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# PDG masses in MeV
m_e = 0.51099895
m_mu = 105.6583755
m_tau = 1776.86

# Sanity checks against the graduated-script values
sqrts = np.array([np.sqrt(m_e), np.sqrt(m_mu), np.sqrt(m_tau)])
A = np.mean(sqrts)
Q = (m_e + m_mu + m_tau) / (sqrts.sum() ** 2)
print(f"A = {A:.6f} sqrtMeV")
print(f"Koide Q = (sum m)/(sum sqrt m)^2 = {Q:.7f}  (expect 2/3 = {2/3:.7f})")

# Torsor-invariant angle (from electroweak_housing_closure.py): 2/9 + 7.41e-6
delta = 0.222229631
print(f"delta = {delta:.9f} rad  (2/9 = {2/9:.9f}; offset {delta - 2/9:.2e})")

# sqrt-mass values at each phase for the point annotations
sqrt_m_labels = [np.sqrt(m_e), np.sqrt(m_mu), np.sqrt(m_tau)]

fig, ax = plt.subplots(figsize=(5.6, 5.6))
ax.set_aspect('equal')

# Unit torsor circle
theta_circ = np.linspace(0, 2 * np.pi, 500)
ax.plot(np.cos(theta_circ), np.sin(theta_circ), '-', color='#9E9E9E',
        lw=1.4, alpha=0.8, zorder=1)

# The three generation phases: φ_k = δ − 2πk/3
colors = ['#B71C1C', '#1565C0', '#2E7D32']
gen_names = [r'gen$_1$ = $e$ ($V$)',
             r'gen$_2$ = $\mu$ ($S^+$)',
             r'gen$_3$ = $\tau$ ($S^-$)']

phases = [delta - 2 * np.pi * k / 3 for k in range(3)]

scales = [1.45, 1.30, 1.30]   # gen1 label pushed further out, clear of the circle
for k in range(3):
    ph = phases[k]
    xp, yp = np.cos(ph), np.sin(ph)
    ax.plot(xp, yp, 'o', color=colors[k], markersize=11, zorder=4)
    # Radial spoke from origin (all unit length: phases only, not magnitudes)
    ax.plot([0, xp], [0, yp], '-', color=colors[k], lw=1.1, alpha=0.5, zorder=2)
    # Label with generation and its sqrt-m value at this phase
    scale = scales[k]
    label = gen_names[k] + '\n' + rf'$\sqrt{{m}} = {sqrt_m_labels[k]:.2f}$'
    ax.annotate(label, (xp, yp),
                xytext=(scale * xp, scale * yp),
                ha='center', va='center', fontsize=8.5, color=colors[k],
                bbox=dict(facecolor='white', edgecolor='none', pad=1.2,
                          alpha=0.85))

# δ angle: thin arc spanning φ=0 → φ=δ (12.7°), drawn at a large radius.
# A thin line (lw 1.6) keeps the short arc reading as an arc, not a blob.
r_arc = 0.72
theta_arc = np.linspace(0, delta, 60)
ax.plot(r_arc * np.cos(theta_arc), r_arc * np.sin(theta_arc),
        '-', color='#FF6F00', lw=1.6, zorder=3, solid_capstyle='butt')
# Light reference radius along φ=0 so the angle is visually spanned
ax.plot([0, 1.0], [0, 0], '-', color='#FF6F00', lw=0.8, alpha=0.45, zorder=2)
# δ label away from all lines, thin leader line down to the arc midpoint
arc_mid = (r_arc * np.cos(delta / 2), r_arc * np.sin(delta / 2))
ax.annotate(r'$\delta = 2/9$', xy=arc_mid, xytext=(0.42, 0.55),
            fontsize=11, color='#FF6F00', fontweight='bold',
            ha='center', va='center',
            bbox=dict(facecolor='white', edgecolor='none', pad=1.5),
            arrowprops=dict(arrowstyle='-', color='#FF6F00',
                            lw=0.9, shrinkA=6, shrinkB=2))

# σ-symmetric reference direction (δ=0) on the circle
ax.plot(1.0, 0.0, 's', color='#546E7A', markersize=8, zorder=3)
ax.text(1.0, -0.17, r'$\delta=0$ ($\sigma$-symmetric)', fontsize=8,
        color='#546E7A', ha='center', va='top')

# Reference axis
ax.axhline(y=0, color='#BDBDBD', lw=0.6, alpha=0.4)
ax.plot(0, 0, '+', color='#444', markersize=8, markeredgewidth=1.5, zorder=5)

# ρ cyclic-shift arcs (dashed, outside the circle)
rho_color = '#7B1FA2'
for k in range(3):
    ph1 = phases[k]
    ph2 = phases[(k + 1) % 3]
    dph = ph2 - ph1
    while dph > np.pi:
        dph -= 2 * np.pi
    while dph < -np.pi:
        dph += 2 * np.pi
    arc_thetas = np.linspace(ph1 + 0.25 * dph, ph1 + 0.75 * dph, 30)
    r_rho = 1.10
    ax.plot(r_rho * np.cos(arc_thetas), r_rho * np.sin(arc_thetas),
            '--', color=rho_color, lw=1.1, alpha=0.5)
ax.text(-1.28, -0.62, r'$\rho: -2\pi/3$', fontsize=8.5, color=rho_color,
        ha='center', alpha=0.85)

ax.set_xlim(-1.75, 1.85)
ax.set_ylim(-1.7, 1.75)
ax.set_xlabel(r'$\cos\phi$', fontsize=10)
ax.set_ylabel(r'$\sin\phi$', fontsize=10)
ax.set_title('Koide phase torsor (unit circle): generation $k$ at phase '
             r'$\phi_k = \delta - 2\pi k/3$'
             '\n' + r'$\sqrt{m_k} = A(1+\sqrt{2}|z|\cos\phi_k)$;'
             r'  $|\delta\ \mathrm{mod}\ 2\pi/3| = 2/9 + 7.4\times10^{-6}$',
             fontsize=9)
ax.grid(True, alpha=0.1)

plt.tight_layout()
plt.savefig('koide_circle.pdf', bbox_inches='tight', dpi=150)
plt.savefig('koide_circle.png', bbox_inches='tight', dpi=150)
print("F6: koide_circle.pdf written")
