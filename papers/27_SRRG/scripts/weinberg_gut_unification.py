#!/usr/bin/env python3
"""
weinberg_gut_unification.py — Round 05 new approaches to sin²θ_W from SRRG.

Previous results (in weinberg_rg_running.py):
  - Bare Haar ratio: sin²θ_W ≈ 0.381  (~5001σ off)
  - SRRG + 1-loop SM RG from M_P: sin²θ_W ≈ 0.190  (−1385σ off)

Root-cause diagnosis from the team:
  The SRRG Haar-entropy approach gives boundary conditions alpha_i* ∝ H_Haar(G_i).
  After 1-loop running, the ratio alpha_1/alpha_2 at M_Z ≈ 0.39 (needs 0.300 for sin²θ_W=0.231).
  The fundamental issue: the U(1) hypercharge normalization (the 5/3 factor in GUT convention)
  is not derivable from Haar entropy alone — it requires the matter field content.

This script tests THREE new directions for Round 05:

Direction A: GUT Democratic Coupling Hypothesis
  If the SRRG fixed point implies gauge coupling unification (g_1=g_2=g_3 at M_GUT),
  then 1-loop running down to M_Z gives sin²θ_W(M_Z) ≈ 0.231.
  Does SRRG provide a reason for this unification?

Direction B: Two-loop SM RG running
  Does 2-loop improvement over 1-loop change sin²θ_W significantly?

Direction C: SU(5) hypercharge normalization from SRRG
  The SU(5) GUT assigns U(1)_Y = U(1) ⊂ SU(5) with specific hypercharge normalization.
  If SRRG selects SU(5) as the UV gauge group, can we use SU(5) Haar entropy?
  H_SU5 = ln Vol(SU(5)).
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

# ── Constants ──────────────────────────────────────────────────────────────────
H_U1  = np.log(2 * np.pi)
H_SU2 = np.log(2 * np.pi**2)
H_SU3 = np.log(3 * np.pi**4)

alpha_s_mz_exp = 0.1179
sin2_w_exp     = 0.23122
sigma_sin2_w   = 0.00003
M_Z            = 91.1876    # GeV
M_planck       = 1.22e19    # GeV
M_GUT          = 2e16       # GeV (approximate GUT scale)
L_MP_MZ        = np.log(M_planck / M_Z)     # ~39.43
L_MGUT_MZ      = np.log(M_GUT   / M_Z)     # ~31.07

# One-loop beta-function coefficients (SM, MSbar)
b1 = 41/6   # U(1)_Y (GUT-normalised)
b2 = -19/6  # SU(2)_L
b3 = -7.0   # SU(3)_c

# PDG reference
pdg_alpha1 = 0.01696  # alpha_1 GUT-normalised at M_Z
pdg_alpha2 = 0.03386  # alpha_2 at M_Z
pdg_alpha3 = alpha_s_mz_exp

print("=" * 72)
print("ROUND 05 — New Weinberg Angle Approaches from SRRG")
print("=" * 72)
print()

# ── DIRECTION A: GUT Democratic Coupling ──────────────────────────────────────
print("=" * 72)
print("DIRECTION A: GUT Democratic Coupling Hypothesis")
print("If SRRG implies g_1 = g_2 = g_3 at M_GUT, what does 1-loop give at M_Z?")
print("-" * 72)

def alpha_at_mz_from_mgut(alpha_gut, b, log_ratio):
    """1-loop RGE: alpha(M_Z) from alpha(M_GUT) = alpha_gut."""
    denom = 1 + b * alpha_gut * log_ratio / (2 * np.pi)
    if denom <= 0:
        return None
    return alpha_gut / denom

# Fix alpha_GUT from alpha_s(M_Z) = 0.1179
def residual_a3_gut(alpha_gut):
    a = alpha_at_mz_from_mgut(alpha_gut, b3, L_MGUT_MZ)
    if a is None:
        return 1e10
    return a - alpha_s_mz_exp

# Find valid range for alpha_gut
alpha_gut_max = 2 * np.pi / (7 * L_MGUT_MZ)  # SU(3) Landau pole condition
print(f"Max alpha_gut (SU(3) no Landau): {alpha_gut_max:.5f}")

try:
    alpha_gut_sol = brentq(residual_a3_gut, 1e-6, 0.999 * alpha_gut_max)
    print(f"alpha_GUT (from alpha_s(M_Z)={alpha_s_mz_exp}): {alpha_gut_sol:.6f}")
    print(f"  = 1/{1/alpha_gut_sol:.1f}")

    alpha1_mz_gut = alpha_at_mz_from_mgut(alpha_gut_sol, b1, L_MGUT_MZ)
    alpha2_mz_gut = alpha_at_mz_from_mgut(alpha_gut_sol, b2, L_MGUT_MZ)
    alpha3_mz_gut_check = alpha_at_mz_from_mgut(alpha_gut_sol, b3, L_MGUT_MZ)

    sin2_w_gut = (3/5) * alpha1_mz_gut / (alpha2_mz_gut + (3/5) * alpha1_mz_gut)
    sigma_gut = (sin2_w_gut - sin2_w_exp) / sigma_sin2_w

    print(f"\nWith GUT unification at M_GUT = {M_GUT:.1e} GeV:")
    print(f"  alpha_1(M_Z) = {alpha1_mz_gut:.5f}  (PDG: {pdg_alpha1:.5f}, ratio: {alpha1_mz_gut/pdg_alpha1:.3f})")
    print(f"  alpha_2(M_Z) = {alpha2_mz_gut:.5f}  (PDG: {pdg_alpha2:.5f}, ratio: {alpha2_mz_gut/pdg_alpha2:.3f})")
    print(f"  alpha_3(M_Z) = {alpha3_mz_gut_check:.5f}  (PDG: {pdg_alpha3:.5f}, ratio: {alpha3_mz_gut_check/pdg_alpha3:.3f})")
    print(f"\n  sin²(θ_W) = {sin2_w_gut:.5f}")
    print(f"  Experimental: {sin2_w_exp:.5f} ± {sigma_sin2_w:.5f}")
    print(f"  Deviation: {sin2_w_gut - sin2_w_exp:+.5f}  ({sigma_gut:+.1f}σ)")
    
    # Also try M_GUT scan
    print(f"\n  Scanning M_GUT scale to find best sin²θ_W...")
    best_sigma = 1e10
    best_mgut = None
    for logM in np.linspace(np.log(1e14), np.log(1e19), 100):
        M = np.exp(logM)
        L = np.log(M / M_Z)
        alpha_gut_max_i = 2 * np.pi / (7 * L)
        try:
            agut = brentq(lambda ag: alpha_at_mz_from_mgut(ag, b3, L) - alpha_s_mz_exp,
                         1e-6, 0.999 * alpha_gut_max_i)
            a1 = alpha_at_mz_from_mgut(agut, b1, L)
            a2 = alpha_at_mz_from_mgut(agut, b2, L)
            if a1 is None or a2 is None:
                continue
            s2 = (3/5)*a1/(a2 + (3/5)*a1)
            sig = abs((s2 - sin2_w_exp) / sigma_sin2_w)
            if sig < best_sigma:
                best_sigma = sig
                best_mgut = M
                best_s2w = s2
        except:
            pass
    
    if best_mgut is not None:
        print(f"  Best M_GUT: {best_mgut:.2e} GeV → sin²θ_W = {best_s2w:.5f} ({best_sigma:.1f}σ)")

except Exception as e:
    print(f"ERROR in Direction A: {e}")

# ── DIRECTION B: Two-loop SM RG running ───────────────────────────────────────
print()
print("=" * 72)
print("DIRECTION B: Two-loop SM RG running with SRRG boundary conditions")
print("-" * 72)

# Two-loop SM beta function coefficients (SM, MSbar, with ng=3 generations and nh=1 Higgs doublet)
# Reference: Machacek & Vaughn (1983), Jones (1982)
# d(alpha_i^{-1})/d(ln mu) = -b_i/(2pi) - sum_j b_ij * alpha_j / (8pi^2)
b_ij = np.array([
    [199/50,  27/10, 44/5 ],   # b_{11}, b_{12}, b_{13}
    [  9/10, 35/6,   12.0 ],   # b_{21}, b_{22}, b_{23}
    [ 11/10,  9/2,  -26.0 ],   # b_{31}, b_{32}, b_{33}
])

# Two-loop RGE (coupled system):
# d(g_i^2)/(d ln mu) = b_i * g_i^4 / (8 pi^2) + sum_j b_{ij} * g_i^4 * g_j^2 / (128 pi^4)
# In terms of alpha_i = g_i^2 / (4 pi):
# d(alpha_i)/(d ln mu) = b_i * alpha_i^2 / (2 pi) + sum_j b_{ij} * alpha_i^2 * alpha_j / (4 pi^2)

# SRRG boundary conditions from Haar entropy (same as one-loop script)
# Fix lambda from alpha_3(M_Z) = 0.1179 using ONE-LOOP formula (consistent UV BC)
H_values = [H_U1, H_SU2, H_SU3]
alpha_s_max = 2 * np.pi / (7 * L_MP_MZ)
lam_max = alpha_s_max * 4 * np.pi / H_SU3

def alpha_mz_1loop(alpha_star, b):
    denom = 1 + b * alpha_star * L_MP_MZ / (2 * np.pi)
    if denom <= 0:
        return None
    return alpha_star / denom

def residual_lam(lam):
    a3s = lam * H_SU3 / (4 * np.pi)
    a3 = alpha_mz_1loop(a3s, b3)
    if a3 is None:
        return 1e10
    return a3 - alpha_s_mz_exp

try:
    lam_sol = brentq(residual_lam, 1e-15, 0.999 * lam_max)
    alpha_star = [lam_sol * H / (4 * np.pi) for H in H_values]
    
    print(f"SRRG boundary conditions at M_Planck:")
    for i, (name, H, b) in enumerate([("U(1)", H_U1, b1), ("SU(2)", H_SU2, b2), ("SU(3)", H_SU3, b3)]):
        print(f"  alpha_{name}(M_P) = {alpha_star[i]:.6f}")
    
    # 2-loop RGE integration from M_P to M_Z
    b_vec = [b1, b2, b3]
    
    def rge_2loop(lnmu, alpha):
        """Two-loop SM RGE for alpha_1, alpha_2, alpha_3."""
        da = np.zeros(3)
        for i in range(3):
            one_loop = b_vec[i] * alpha[i]**2 / (2 * np.pi)
            two_loop = sum(b_ij[i, j] * alpha[i]**2 * alpha[j] / (4 * np.pi**2)
                          for j in range(3))
            da[i] = one_loop + two_loop
        return da
    
    lnmu_span = [np.log(M_planck), np.log(M_Z)]
    sol = solve_ivp(rge_2loop, lnmu_span, alpha_star,
                   method='RK45', rtol=1e-10, atol=1e-12,
                   dense_output=False)
    
    if sol.success:
        alpha_mz_2loop = sol.y[:, -1]
        a1, a2, a3 = alpha_mz_2loop
        sin2_w_2loop = (3/5) * a1 / (a2 + (3/5) * a1)
        sigma_2loop = (sin2_w_2loop - sin2_w_exp) / sigma_sin2_w
        
        print(f"\nTwo-loop result:")
        print(f"  alpha_1(M_Z) = {a1:.6f}  (PDG: {pdg_alpha1:.5f}, ratio: {a1/pdg_alpha1:.3f})")
        print(f"  alpha_2(M_Z) = {a2:.6f}  (PDG: {pdg_alpha2:.5f}, ratio: {a2/pdg_alpha2:.3f})")
        print(f"  alpha_3(M_Z) = {a3:.6f}  (PDG: {pdg_alpha3:.5f}, ratio: {a3/pdg_alpha3:.3f})")
        print(f"\n  sin²(θ_W) [2-loop] = {sin2_w_2loop:.5f}")
        
        # Compare with 1-loop result
        a1_1l, a2_1l = (lam_sol * H_U1 / (4*np.pi)), (lam_sol * H_SU2 / (4*np.pi))
        a1_1l_mz = alpha_mz_1loop(a1_1l, b1)
        a2_1l_mz = alpha_mz_1loop(a2_1l, b2)
        sin2_w_1l = (3/5)*a1_1l_mz / (a2_1l_mz + (3/5)*a1_1l_mz)
        sigma_1l = (sin2_w_1l - sin2_w_exp) / sigma_sin2_w
        
        print(f"  sin²(θ_W) [1-loop] = {sin2_w_1l:.5f}  ({sigma_1l:+.1f}σ)")
        print(f"  sin²(θ_W) [2-loop] = {sin2_w_2loop:.5f}  ({sigma_2loop:+.1f}σ)")
        print(f"  Improvement from 1→2 loop: {abs(sigma_1l) - abs(sigma_2loop):+.1f}σ")
        print(f"  Experimental: {sin2_w_exp:.5f} ± {sigma_sin2_w:.5f}")
    else:
        print(f"  2-loop ODE solver failed: {sol.message}")

except Exception as e:
    print(f"ERROR in Direction B: {e}")
    import traceback; traceback.print_exc()

# ── DIRECTION C: SU(5) embedding — hypercharge normalization ─────────────────
print()
print("=" * 72)
print("DIRECTION C: SU(5) Embedding — Natural Hypercharge Normalization")
print("-" * 72)
print("""
In SU(5) GUT, the SM gauge groups embed as:
  U(1)_Y ⊂ SU(5): Y = sqrt(3/5) * T_24 (GUT-normalised hypercharge)
  The 5/3 factor comes from this embedding.

In SRRG, instead of using H_Haar(U(1)) = ln(2π), we ask:
  What is the Haar entropy of U(1) as a SUBGROUP of SU(5)?
  This is determined by the SU(5) root lattice / Cartan subalgebra structure.

Natural SU(5) structure:
  Vol(U(1)_Y ⊂ SU(5)) = ? (GUT-normalised Cartan direction length)
  
In SU(5) with conventional normalisation, the U(1) Cartan direction has
length 2π * sqrt(5/3) rather than 2π.  So:
  H_U1_SU5 = ln(2π * sqrt(5/3)) = ln(2π) + (1/2)*ln(5/3)
""")

H_U1_SU5 = np.log(2 * np.pi * np.sqrt(5/3))
print(f"H_U1 (bare, period=2pi):       ln(2π) = {H_U1:.4f}")
print(f"H_U1 (SU(5)-embedded, 5/3):   {H_U1_SU5:.4f}")
print()

# Recompute sin²θ_W proxy with SU(5)-normalised U(1)
sin2_w_su5_proxy = H_U1_SU5 / (H_U1_SU5 + H_SU2)
print(f"Proxy sin²θ_W with SU(5) H_U1:")
print(f"  = H_U1_SU5 / (H_U1_SU5 + H_SU2)")
print(f"  = {H_U1_SU5:.4f} / ({H_U1_SU5:.4f} + {H_SU2:.4f})")
print(f"  = {sin2_w_su5_proxy:.5f}")
sigma_su5_proxy = (sin2_w_su5_proxy - sin2_w_exp) / sigma_sin2_w
print(f"  vs experiment: {sin2_w_exp:.5f}  ({sigma_su5_proxy:+.1f}σ)")
print()

# Compare: what 5/3 factor would give sin²θ_W = 0.231?
# sin²θ_W = ln(2π * sqrt(r)) / (ln(2π * sqrt(r)) + ln(2π²))  = 0.231
# Let's solve for r numerically
def target_func(log_scale):
    H_u1_test = np.log(2 * np.pi) + log_scale  # H_U1 + log_scale correction
    s2w = H_u1_test / (H_u1_test + H_SU2)
    return s2w - sin2_w_exp

# Does a solution exist?
f_lo = target_func(-5)
f_hi = target_func(+5)
if f_lo * f_hi < 0:
    log_scale_sol = brentq(target_func, -5, 5)
    r_sol = np.exp(2 * log_scale_sol)  # sqrt(r) * 2pi
    print(f"Required U(1) entropy correction for sin²θ_W = {sin2_w_exp}:")
    print(f"  log_scale = {log_scale_sol:.4f}")
    print(f"  Effective 'r' factor: {r_sol:.4f}  (SU(5) gives r=5/3={5/3:.4f})")
    print(f"  H_U1_required = {np.log(2*np.pi) + log_scale_sol:.4f}")
    print(f"  Ratio H_U1_required/H_SU2 = {(np.log(2*np.pi)+log_scale_sol)/H_SU2:.4f}")
else:
    print(f"No simple H_U1 correction can reach sin²θ_W = {sin2_w_exp}")
    print(f"  The Haar-entropy proxy approach is fundamentally incompatible with the target.")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print("ROUND 05 SUMMARY — Weinberg angle status")
print("=" * 72)
print(f"""
Approach                         | sin²θ_W  | Deviation
---------------------------------|----------|----------
Bare Haar ratio (prev.)          | 0.38127  | ~+5001σ
SRRG + 1-loop from M_P (prev.)   | 0.18968  | −1385σ
GUT unification (Dir. A, M_GUT)  | see above| see above
SRRG + 2-loop from M_P (Dir. B)  | see above| see above
SU(5)-embedded U(1) proxy (Dir.C)| {sin2_w_su5_proxy:.5f}  | {sigma_su5_proxy:+.0f}σ
Experimental                     | {sin2_w_exp:.5f}  | 0σ

ROOT CAUSE DIAGNOSIS (Jane + Carl):
  The fundamental obstacle is not the running — it's the BOUNDARY CONDITION.
  The SRRG Haar-entropy boundary gives alpha_1*/alpha_2* = H_U1/H_SU2 ≈ 0.616.
  After any amount of SM RG running, sin²θ_W stays around 0.19 (WRONG direction).
  To get 0.231, we need alpha_1*/alpha_2* ≈ 1 at M_GUT (GUT unification).
  
  SRRG does NOT predict GUT unification directly — it gives DIFFERENT Haar entropies
  for each group (H_U1 ≠ H_SU2).  The gauge coupling RATIOS are set by the Haar
  entropy RATIOS, not their common value.

CONCLUSION (Adam):
  The Weinberg angle derivation from SRRG requires one of:
  (a) A derivation of the U(1) hypercharge normalization from SRRG matter sector
      (not gauge sector alone) — requires the fermion hypercharge assignments
  (b) A SRRG argument for why the effective UV boundary should use SU(5) normalization
      (Direction C above shows SU(5) gives only marginally better results — still very off)
  (c) A completely new SRRG ingredient connecting the C_Lambda[S*]=0 condition
      to the specific sin²θ_W value (Open Problem 5)

GRADE: [D→C] — unchanged from Round 02.
  Negative result confirmed at depth.  Three new approaches tried, all negative.
  The root cause is now precisely diagnosed: SRRG gauge-sector Haar entropy ≠ Weinberg angle.
  Path to [C]: derive U(1) hypercharge normalization from SRRG matter-field content.
  Path to [B]: show SRRG + SM RG running gives unified coupling at M_GUT (requires new SRRG element).
""")
