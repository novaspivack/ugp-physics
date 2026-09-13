#!/usr/bin/env python3
"""
weinberg_rg_running.py — SRRG multi-scale Weinberg angle derivation attempt.

The SRRG fixed-point sets Planck-scale boundary conditions:
    alpha_i* = lambda * H_Haar(G_i) / (4 pi)
where H_Haar(G_i) = ln Vol_Haar(G_i) is the Haar entropy of the SM gauge group G_i.

One-loop SM RGE running from M_Planck to M_Z (exact one-loop solution):
    1/alpha_i(M_Z) = 1/alpha_i* + b_i * ln(M_P/M_Z) / (2 pi)
or equivalently:
    alpha_i(M_Z) = alpha_i* / (1 + b_i * alpha_i* * ln(M_P/M_Z) / (2 pi))

NOTE ON SIGN CONVENTION:  d(1/alpha)/d(ln mu) = -b/(2pi), so
    1/alpha(mu_low) = 1/alpha(mu_high) + b * ln(mu_high/mu_low) / (2pi)
This is the standard MSbar one-loop running.  For asymptotically free groups (b<0),
1/alpha decreases going to the IR, i.e. alpha grows.

We fix the single free parameter lambda from alpha_s(M_Z) = 0.1179 (PDG 2022),
then predict alpha_1(M_Z) and alpha_2(M_Z), and compute sin^2(theta_W).

Hypercharge normalization: in SM GUT-normalised convention,
    g_1 = sqrt(5/3) * g'_Y  =>  sin^2(theta_W) = (3/5)*alpha_1 / (alpha_2 + (3/5)*alpha_1)

PDG reference values at M_Z:
    alpha_s = 0.1179
    alpha_2 ~ 0.0338  (from g_2 ~ 0.653)
    alpha_1 ~ 0.0170  (GUT-normalised, from alpha_EM and sin^2 theta_W)
    sin^2(theta_W) = 0.23122 +/- 0.00003
"""

import numpy as np
from scipy.optimize import brentq

# ── Haar entropies (ln of Haar measure volume) ──────────────────────────────
H_U1  = np.log(2 * np.pi)          # U(1): Vol = 2pi     => ln(2pi)   ≈ 1.8379
H_SU2 = np.log(2 * np.pi**2)       # SU(2) ≅ S³: Vol = 2pi²  => ln(2pi²) ≈ 2.9841
H_SU3 = np.log(3 * np.pi**4)       # SU(3): ln(3pi⁴)          ≈ 5.6781

GROUPS = [
    ("U(1)_Y",  H_U1,  41/6,   "U(1)"),   # (name, H, b, short)
    ("SU(2)_L", H_SU2, -19/6,  "SU(2)"),
    ("SU(3)_c", H_SU3, -7.0,   "SU(3)"),
]

# ── Physical inputs ──────────────────────────────────────────────────────────
alpha_s_mz_exp = 0.1179       # PDG 2022 alpha_s(M_Z)
sin2_w_exp     = 0.23122      # PDG 2022 sin²(theta_W) on-shell
sigma_sin2_w   = 0.00003
M_Z            = 91.1876      # GeV
M_planck       = 1.22e19      # GeV
log_ratio      = np.log(M_planck / M_Z)   # ln(M_P/M_Z) ≈ 39.43

print(f"ln(M_P / M_Z) = {log_ratio:.4f}")
print()

# ── Correct one-loop running formula ─────────────────────────────────────────
# 1/alpha(M_Z) = 1/alpha* + b * ln(M_P/M_Z) / (2*pi)
# => alpha(M_Z) = alpha* / (1 + b * alpha* * L / (2*pi))
#
# For b_3 = -7 (SU(3), asymptotically free):
#   denominator = 1 - 7 * alpha_3* * L / (2*pi), which is < 1, so alpha_3(M_Z) > alpha_3*
#   This denominator can reach zero (Landau pole for SU(3) in the IR direction); we need
#   alpha_3* small enough that denom > 0.

def alpha_mz(alpha_star, b):
    """One-loop RGE: alpha(M_Z) from alpha(M_P) = alpha_star."""
    denom = 1 + b * alpha_star * log_ratio / (2 * np.pi)
    if denom <= 0:
        raise ValueError(f"Denominator non-positive: {denom:.4f} (Landau pole hit)")
    return alpha_star / denom

_, H_SU3_val, b3, _ = GROUPS[2]

def residual_alpha3(lam):
    alpha3_star = lam * H_SU3_val / (4 * np.pi)
    return alpha_mz(alpha3_star, b3) - alpha_s_mz_exp

# Determine valid lambda range (denominator > 0 for SU(3)):
# 1 + b3 * alpha_3* * L/(2pi) > 0
# 1 - 7 * alpha_3* * L/(2pi) > 0
# alpha_3* < 2*pi/(7*L)
alpha3_star_max = 2 * np.pi / (7 * log_ratio)
lam_max_valid   = alpha3_star_max * 4 * np.pi / H_SU3_val
print(f"Max alpha_3*(no Landau pole) = {alpha3_star_max:.6f}")
print(f"Corresponding lambda_max     = {lam_max_valid:.6f}")

# Check endpoints
f_lo = residual_alpha3(1e-15)
f_hi = residual_alpha3(0.999 * lam_max_valid)
print(f"f(lam=1e-15) = {f_lo:.6f},  f(lam=0.999*lam_max) = {f_hi:.6f}")
print()

if f_lo * f_hi > 0:
    print("ERROR: no root found in valid range — SRRG RG approach cannot fix lambda.")
    print(f"  Maximum achievable alpha_3(M_Z) = {alpha_mz(0.999*alpha3_star_max, b3):.5f}")
    print(f"  Experimental alpha_s(M_Z)       = {alpha_s_mz_exp:.5f}")
    import sys; sys.exit(0)

lam_sol = brentq(residual_alpha3, 1e-15, 0.999 * lam_max_valid)
print(f"lambda (fixed from alpha_s(M_Z) = {alpha_s_mz_exp}) = {lam_sol:.6e}")
print()

# ── Predict all couplings ─────────────────────────────────────────────────────
# PDG reference values (GUT-normalised)
pdg_ref = {
    "U(1)":  0.01696,   # alpha_1 = (5/3) * alpha_EM / cos²theta_W
    "SU(2)": 0.03386,   # alpha_2 from g_2 ~ 0.653
    "SU(3)": alpha_s_mz_exp,
}

results = {}
print(f"{'Group':<12} {'H_Haar':>8}  {'alpha*':>10}  {'alpha(M_Z)':>12}  {'PDG alpha':>10}  {'ratio':>7}")
print("-" * 72)

for name, H, b, short in GROUPS:
    alpha_star = lam_sol * H / (4 * np.pi)
    a_mz       = alpha_mz(alpha_star, b)
    pdg        = pdg_ref.get(short)
    ratio_str  = f"{a_mz/pdg:.3f}" if pdg else "—"
    pdg_str    = f"{pdg:.5f}" if pdg else "—"
    print(f"{name:<12} {H:>8.4f}  {alpha_star:>10.6f}  {a_mz:>12.6f}  {pdg_str:>10}  {ratio_str:>7}")
    results[short] = {"alpha_star": alpha_star, "alpha_mz": a_mz}

print()

# ── Weinberg angle ────────────────────────────────────────────────────────────
alpha1 = results["U(1)"]["alpha_mz"]
alpha2 = results["SU(2)"]["alpha_mz"]

sin2_w_srrg = (3/5) * alpha1 / (alpha2 + (3/5) * alpha1)
deviation_sigma = (sin2_w_srrg - sin2_w_exp) / sigma_sin2_w

print(f"sin²(θ_W) from SRRG RG running:  {sin2_w_srrg:.5f}")
print(f"Experimental (PDG 2022):          {sin2_w_exp:.5f} ± {sigma_sin2_w:.5f}")
print(f"Deviation:                        {sin2_w_srrg - sin2_w_exp:+.5f}  ({deviation_sigma:+.1f}σ)")
print()

# Also report 1/alpha_EM at M_Z (tree level mixing formula)
alpha_em = alpha1 * alpha2 / (alpha1 * (3/5) + alpha2)  # tree-level mixing
print(f"alpha_EM^{{tree}}(M_Z) from SRRG: 1/{1/alpha_em:.1f}  (PDG: 1/127.9)")
print()

# ── Summary verdict ───────────────────────────────────────────────────────────
print("=" * 72)
if abs(deviation_sigma) < 5:
    print(f"VERDICT [SIGNIFICANT]: sin²θ_W = {sin2_w_srrg:.5f}")
    print(f"  Within 5σ of experiment. This is a significant SRRG derivation.")
elif abs(deviation_sigma) < 50:
    print(f"VERDICT [MARGINAL]: sin²θ_W = {sin2_w_srrg:.5f}")
    print(f"  {deviation_sigma:.0f}σ off. Possible with threshold corrections.")
else:
    print(f"VERDICT [NEGATIVE]: sin²θ_W = {sin2_w_srrg:.5f}")
    print(f"  {deviation_sigma:+.0f}σ off. SRRG Haar-entropy + 1-loop SM running does NOT")
    print(f"  reproduce sin²θ_W. The alpha_i(M_Z) ratios are off from PDG by factors ~{alpha1/pdg_ref['U(1)']:.2f}--{alpha2/pdg_ref['SU(2)']:.2f}.")
    print()
    print("  Root cause: the SRRG Haar-entropy boundary conditions at M_P give")
    print("  coupling RATIOS alpha_1*/alpha_2* = H_U1/H_SU2 ≈ 0.616.")
    print("  After 1-loop running, the ratio shifts but sin²θ_W ≈ 0.19, far from 0.231.")
    print()
    print("  The missing ingredient: the U(1) hypercharge assignment (GUT normalization)")
    print("  is an input, not derived from SRRG. The Weinberg angle depends on the")
    print("  hypercharge convention, which requires a deeper SRRG treatment of the")
    print("  U(1) factor beyond Haar entropy alone.")
print("=" * 72)
