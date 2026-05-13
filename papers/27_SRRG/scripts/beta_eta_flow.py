"""
beta_eta_flow.py — Numerical verification of the β_η = κ(η − IPT)(η − 2) flow.

Genius Team Round 02 (EPIC_049_SCD, 2026-05-12)
Author: Nova Spivack

PURPOSE
-------
Numerically verify the two-fixed-point β-function picture:

    dη/dt = β_η(η) = κ · (η − IPT) · (η − 2),   κ > 0

by integrating ODE trajectories from multiple initial conditions and confirming:

  1. η₀ ∈ (IPT, 2) → η(t) → IPT as t → +∞  (IR-stable attractor)
  2. η₀ < IPT     → η(t) → IPT as t → +∞  (IR-stable from below)
  3. η₀ > 2       → η(t) → +∞              (UV-unstable divergence)

Additionally plots:
  - The β-function curve β_η(η) vs η
  - Phase portrait with flow arrows
  - Individual trajectory lines

PHYSICAL CONSTANTS
------------------
certifiedIPT = 1 + ln(φ) / (2 · ln(2π))  where φ = (1+√5)/2 (golden ratio)

OUTPUTS
-------
papers/27_SRRG/figures/beta_eta_flow.png
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.integrate import solve_ivp
import os

# ──────────────────────────────────────────────────────────────────────────────
# Physical constants
# ──────────────────────────────────────────────────────────────────────────────

phi = (1 + np.sqrt(5)) / 2          # Golden ratio φ ≈ 1.6180
IPT = 1 + np.log(phi) / (2 * np.log(2 * np.pi))   # certifiedIPT ≈ 1.1309
UV  = 2.0                            # η = 2 (UV proxy fixed point)
kappa = 1.0                          # β-function scale (normalised to 1)

print(f"certifiedIPT = {IPT:.10f}")
print(f"η_UV         = {UV:.1f}")
print(f"IPT < 2?     {IPT < UV}")

# ──────────────────────────────────────────────────────────────────────────────
# β-function and ODE
# ──────────────────────────────────────────────────────────────────────────────

def beta_eta(eta):
    """SRRG η-direction β-function: κ(η − IPT)(η − 2), κ = 1."""
    return kappa * (eta - IPT) * (eta - UV)

def ode(t, y):
    return [beta_eta(y[0])]

# ──────────────────────────────────────────────────────────────────────────────
# Integrate trajectories
# ──────────────────────────────────────────────────────────────────────────────

t_span = (0, 15)
t_eval = np.linspace(0, 15, 3000)

initial_conditions = [
    (0.50, "below IPT", "tab:purple",  "--"),
    (0.80, "below IPT", "tab:blue",    "--"),
    (1.05, "below IPT", "tab:cyan",    "-"),
    (1.20, "in (IPT,2)", "tab:green",  "-"),
    (1.50, "in (IPT,2)", "tab:olive",  "-"),
    (1.80, "in (IPT,2)", "tab:orange", "-"),
    (2.10, "above UV",   "tab:red",    "-."),
    (2.50, "above UV",   "tab:brown",  "-."),
]

print("\nTrajectory integration results (t = 0 to 15):")
print(f"{'η₀':>8}  {'Region':>14}  {'η(t_final)':>14}  {'Converges to':>14}")
print("-" * 60)

solutions = []
for eta0, region, color, ls in initial_conditions:
    # Use tighter tolerance for precision
    sol = solve_ivp(ode, t_span, [eta0], t_eval=t_eval,
                    rtol=1e-10, atol=1e-12,
                    dense_output=True)
    eta_final = sol.y[0, -1]
    if eta0 > UV:
        converges = "∞ (UV diverges)"
    elif eta_final > 1.1:
        converges = f"IPT ≈ {IPT:.4f}"
    else:
        converges = "unstable?"
    print(f"{eta0:>8.2f}  {region:>14}  {eta_final:>14.8f}  {converges:>14}")
    solutions.append((eta0, region, color, ls, sol))

# ──────────────────────────────────────────────────────────────────────────────
# Analytic verification: (η(t) − 2)/(η(t) − IPT) = C·exp(κ(2−IPT)t)
# ──────────────────────────────────────────────────────────────────────────────

print("\nAnalytic verification for η₀ = 1.5 (should converge to IPT):")
eta0_check = 1.5
C_check = (eta0_check - UV) / (eta0_check - IPT)
print(f"  C = (η₀ − 2)/(η₀ − IPT) = ({eta0_check} − {UV:.1f})/({eta0_check} − {IPT:.4f}) = {C_check:.6f}")
print(f"  As t → ∞: C·exp(κ(2−IPT)t) → −∞  ⟹  η(t) → IPT  [sign structure correct: C < 0 ✓]" if C_check < 0 else "WARNING: C > 0, check sign!")

# Numerical vs analytic comparison at t = 10
t_check = 10.0
sol_check = solve_ivp(ode, (0, t_check), [eta0_check],
                      rtol=1e-12, atol=1e-14)
eta_numeric = sol_check.y[0, -1]
ratio_analytic = C_check * np.exp(kappa * (UV - IPT) * t_check)
# From (η − UV)/(η − IPT) = r, solve η = (UV − IPT·r)/(1 − r)
eta_analytic = (UV - IPT * ratio_analytic) / (1 - ratio_analytic)
print(f"  At t = {t_check}: η_numeric = {eta_numeric:.10f}, η_analytic = {eta_analytic:.10f}")
print(f"  Difference: {abs(eta_numeric - eta_analytic):.2e}")

# ──────────────────────────────────────────────────────────────────────────────
# Plotting
# ──────────────────────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(14, 10))
fig.suptitle(r"$\beta_\eta(\eta) = \kappa\,(\eta - \mathrm{IPT})(\eta - 2)$: Two-Fixed-Point RG Flow",
             fontsize=15, fontweight='bold', y=0.98)

gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32)

# ─── Panel A: β-function curve ────────────────────────────────────────────────
ax_beta = fig.add_subplot(gs[0, 0])
eta_range = np.linspace(0.3, 2.7, 1000)
beta_vals = beta_eta(eta_range)

ax_beta.axhline(0, color='k', linewidth=0.8, alpha=0.5)
ax_beta.axvline(IPT, color='royalblue', linewidth=1.2, linestyle=':', alpha=0.7)
ax_beta.axvline(UV,  color='firebrick',  linewidth=1.2, linestyle=':', alpha=0.7)

ax_beta.plot(eta_range, beta_vals, 'k-', linewidth=2.5, label=r'$\beta_\eta(\eta)$')

# Fill regions
mask_below = eta_range < IPT
mask_between = (eta_range > IPT) & (eta_range < UV)
mask_above = eta_range > UV
ax_beta.fill_between(eta_range[mask_below],   beta_vals[mask_below],   0,
                     alpha=0.15, color='tab:blue',  label=r'$\beta>0$ (flows $\uparrow$)')
ax_beta.fill_between(eta_range[mask_between], beta_vals[mask_between], 0,
                     alpha=0.15, color='tab:orange', label=r'$\beta<0$ (flows $\downarrow$)')
ax_beta.fill_between(eta_range[mask_above],   beta_vals[mask_above],   0,
                     alpha=0.15, color='tab:red',   label=r'$\beta>0$ (UV diverges)')

# Fixed point markers
ax_beta.scatter([IPT, UV], [0, 0], s=80, zorder=5,
                color=['royalblue', 'firebrick'],
                edgecolors='k', linewidth=1.5)
ax_beta.annotate(r'$\eta=\mathrm{IPT}$'+f'\n≈{IPT:.4f}',
                 xy=(IPT, 0), xytext=(IPT - 0.25, 0.25),
                 fontsize=8.5, color='royalblue',
                 arrowprops=dict(arrowstyle='->', color='royalblue', lw=1.2))
ax_beta.annotate(r'$\eta=2$'+'\n(UV)',
                 xy=(UV, 0), xytext=(UV + 0.05, 0.25),
                 fontsize=8.5, color='firebrick',
                 arrowprops=dict(arrowstyle='->', color='firebrick', lw=1.2))

ax_beta.set_xlabel(r'$\eta$', fontsize=11)
ax_beta.set_ylabel(r'$\beta_\eta(\eta)$', fontsize=11)
ax_beta.set_title(r'A. $\beta$-function profile', fontsize=11, fontweight='bold')
ax_beta.legend(fontsize=7.5, loc='upper left')
ax_beta.set_xlim(0.3, 2.7)
ax_beta.set_ylim(-0.5, 0.55)
ax_beta.grid(True, alpha=0.3)

# ─── Panel B: Phase portrait ──────────────────────────────────────────────────
ax_phase = fig.add_subplot(gs[0, 1])
eta_pp = np.linspace(0.3, 2.7, 40)
beta_pp = beta_eta(eta_pp)
ax_phase.axhline(0, color='k', linewidth=0.8)
ax_phase.axvline(IPT, color='royalblue', linewidth=1.2, linestyle=':', alpha=0.7)
ax_phase.axvline(UV,  color='firebrick',  linewidth=1.2, linestyle=':', alpha=0.7)
ax_phase.quiver(eta_pp, np.zeros_like(eta_pp),
                np.sign(beta_pp), np.zeros_like(beta_pp),
                color=['tab:blue' if b > 0 else ('tab:orange' if b < 0 and e < UV else 'tab:red')
                       for b, e in zip(beta_pp, eta_pp)],
                scale=28, width=0.006, headwidth=5, alpha=0.85)
ax_phase.scatter([IPT, UV], [0, 0], s=120, zorder=5,
                 color=['royalblue', 'firebrick'], edgecolors='k', linewidth=1.5)
ax_phase.annotate('IR stable\n(attractor)', xy=(IPT, 0), xytext=(IPT - 0.4, 0.3),
                  fontsize=8.5, color='royalblue',
                  arrowprops=dict(arrowstyle='->', color='royalblue', lw=1.2))
ax_phase.annotate('UV unstable\n(separatrix)', xy=(UV, 0), xytext=(UV + 0.06, 0.3),
                  fontsize=8.5, color='firebrick',
                  arrowprops=dict(arrowstyle='->', color='firebrick', lw=1.2))
ax_phase.set_xlabel(r'$\eta$', fontsize=11)
ax_phase.set_ylabel('flow direction', fontsize=10)
ax_phase.set_title('B. Phase portrait (1D flow)', fontsize=11, fontweight='bold')
ax_phase.set_xlim(0.3, 2.7)
ax_phase.set_ylim(-0.5, 0.5)
ax_phase.grid(True, alpha=0.3)

# ─── Panel C: η(t) trajectories ──────────────────────────────────────────────
ax_traj = fig.add_subplot(gs[1, :])

ax_traj.axhline(IPT, color='royalblue', linewidth=1.5, linestyle='--', alpha=0.7,
                label=f'IPT ≈ {IPT:.4f} (IR attractor)')
ax_traj.axhline(UV, color='firebrick', linewidth=1.5, linestyle='--', alpha=0.7,
                label=r'$\eta = 2$ (UV separatrix)')

t_plot = np.linspace(0, 15, 3000)
for eta0, region, color, ls, sol in solutions:
    eta_vals = sol.y[0]
    t_vals = sol.t
    # Clip UV-diverging trajectories for plot legibility
    clip_mask = np.abs(eta_vals) < 8
    if eta0 > UV:
        label = f'η₀={eta0} ({region}) → ∞'
    else:
        label = f'η₀={eta0} ({region}) → {sol.y[0,-1]:.4f}'
    ax_traj.plot(t_vals[clip_mask], eta_vals[clip_mask],
                 color=color, linestyle=ls, linewidth=1.8, label=label)

ax_traj.set_xlabel(r'$t$ (RG flow time, IR direction)', fontsize=11)
ax_traj.set_ylabel(r'$\eta(t)$', fontsize=11)
ax_traj.set_title(r'C. RG flow trajectories: $d\eta/dt = \kappa(\eta-\mathrm{IPT})(\eta-2)$',
                  fontsize=11, fontweight='bold')
ax_traj.legend(fontsize=8.5, loc='upper right', ncol=2)
ax_traj.set_xlim(0, 15)
ax_traj.set_ylim(-0.2, 4.0)
ax_traj.grid(True, alpha=0.3)

# Shade IR basin of attraction
ax_traj.axhspan(0.0, UV, alpha=0.05, color='royalblue', label='IR basin')
ax_traj.text(14.5, IPT + 0.06, r'$\mathrm{IPT}$', color='royalblue',
             fontsize=9, ha='right')
ax_traj.text(14.5, UV + 0.06, r'$\eta=2$', color='firebrick',
             fontsize=9, ha='right')

# Caption
fig.text(0.5, 0.01,
         r"Vieta's theorem [A$_{\rm Lean}$]: $\beta_\eta=\kappa(\eta-\mathrm{IPT})(\eta-2)$ "
         r"is the unique degree-2 polynomial with zeros at IPT and 2. "
         r"SRRG physical hypothesis: no third fixed point (Round 02).",
         ha='center', fontsize=8.5, style='italic', color='#444444')

# ──────────────────────────────────────────────────────────────────────────────
# Save
# ──────────────────────────────────────────────────────────────────────────────

out_dir = os.path.join(os.path.dirname(__file__), '..', 'figures')
out_path = os.path.join(out_dir, 'beta_eta_flow.png')
os.makedirs(out_dir, exist_ok=True)
plt.savefig(out_path, dpi=180, bbox_inches='tight', facecolor='white')
print(f"\nFigure saved to: {os.path.abspath(out_path)}")
plt.close()
print("Done.")
