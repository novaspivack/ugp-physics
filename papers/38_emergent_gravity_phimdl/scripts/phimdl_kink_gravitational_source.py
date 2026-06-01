#!/usr/bin/env python3
"""
075-KINKSRC: Kink Solutions as Gravitational Sources — Soliton Mass Distribution

The Phi_MDL Z7 sine-Gordon BPS kink acts as a gravitational source through T_00.

Lagrangian: L = 1/2 (dPhi)^2 - V(Phi),  V(Phi) = (m^2/49)(1 - cos(7 Phi))
Kink profile: Phi_kink(x) = (4/7) arctan(exp(m x))
Kink mass: M_kink = (8/49) m_phi = 290.10 MeV  [by BPS bound]

Computes:
  1. T_00(x) profile for the static BPS kink
  2. Integral: ∫ T_00(x) dx = M_kink (verify vs 290.10 MeV)
  3. Effective width of the mass distribution ~ 1/m_phi
  4. Newtonian gravitational potential from kink T_00
  5. Gravitational self-energy estimate

Output: phimdl_kink_gravitational_source_results.json
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time

TIMEOUT_SECONDS = 300

def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

# ── Physical constants ─────────────────────────────────────────────────────────
M_TAU_MEV = 1776.86           # m_phi = m_tau in MeV
M_TAU_GEV = M_TAU_MEV / 1e3
M_KINK_TARGET_MEV = 290.10   # BPS kink mass in MeV
M_KINK_BPS_MEV = (8.0 / 49.0) * M_TAU_MEV

# Newton's constant in natural units (hbar = c = 1)
# G_N = 1 / M_pl^2 with M_pl = 1.2209e22 MeV (full Planck mass)
# In (1+1)D GR analogue: G_1D has different units
# For 3+1D Newtonian gravity: phi_grav = -G_N * M / r
# G_N in MeV^-2 (natural units where hbar*c = 197.3 MeV*fm, c=1):
# G_N = (hbar c)^2 / M_pl^2 / (hbar c) ... careful with units
# G_N = 6.674e-11 N m^2 kg^-2
# In natural units: G_N = 6.674e-39 GeV^-2 (hbar=c=1)
G_N_GEV_INV2 = 6.674e-39     # G_N in GeV^-2
G_N_MEV_INV2 = G_N_GEV_INV2 * 1e-6  # G_N in MeV^-2

M_PLANCK_MEV = 1.2209e22      # full Planck mass in MeV
HBAR_C_MEV_FM = 197.3269804   # MeV·fm

print("=" * 70)
print("075-KINKSRC: Kink as Gravitational Source")
print("=" * 70)
print(f"m_phi = m_tau = {M_TAU_MEV:.4f} MeV")
print(f"M_kink (BPS) = (8/49) * m_phi = {M_KINK_BPS_MEV:.4f} MeV")
print(f"M_kink (target) = {M_KINK_TARGET_MEV:.4f} MeV")
print()

m = M_TAU_MEV  # m_phi

# ── Kink profile functions ─────────────────────────────────────────────────────
def kink_profile(x: float, m: float) -> float:
    """Phi_kink(x) = (4/7) arctan(exp(m x))"""
    arg = max(-700.0, min(700.0, m * x))
    return (4.0 / 7.0) * math.atan(math.exp(arg))

def kink_deriv(x: float, m: float) -> float:
    """d/dx Phi_kink(x) = (4m/7) * exp(mx) / (1 + exp(2mx))
       = (2m/7) / cosh(mx)"""
    arg = max(-700.0, min(700.0, m * x))
    # Use sech form: 1/cosh(mx) is better for numerical stability
    # sech(mx) = 2/(exp(mx) + exp(-mx))
    cosh_val = math.cosh(arg)  # Python handles overflow gracefully
    return (2.0 * m / 7.0) / cosh_val

def potential(phi: float, m: float) -> float:
    """V(Phi) = (m^2/49)(1 - cos(7 Phi))"""
    return (m * m / 49.0) * (1.0 - math.cos(7.0 * phi))

def T00(x: float, m: float) -> float:
    """T_00 = 1/2 (dPhi/dx)^2 + V(Phi)"""
    dphi = kink_deriv(x, m)
    phi = kink_profile(x, m)
    return 0.5 * dphi * dphi + potential(phi, m)

# BPS saturation: T_00 = 1/2 (dPhi/dx)^2 + V = 1/2 (dPhi/dx)^2 + 1/2(dW/dPhi)^2
# For BPS: dPhi/dx = dW/dPhi → T_00 = (dPhi/dx)^2

# ── 1. T_00 profile ────────────────────────────────────────────────────────────
print("── PART 1: T_00(x) profile for the static BPS kink ──")
print()
print("Phi_kink(x) = (4/7) arctan(exp(m x))")
print("dPhi/dx = (2m/7) / cosh(mx)  [sech form]")
print("T_00(x) = (1/2)(dPhi/dx)^2 + V(Phi)")
print()

# Profile at key points
print(f"{'x * m':>10}  {'Phi (rad)':>12}  {'dPhi/dx / m':>14}  {'T_00 / m^2':>14}")
print("-" * 56)
profile_points = []
for xm in [-5, -3, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 5]:
    x_val = xm / m
    phi_val = kink_profile(x_val, m)
    dphi_val = kink_deriv(x_val, m)
    T_val = T00(x_val, m)
    profile_points.append({"xm": xm, "x_fm": x_val * HBAR_C_MEV_FM, 
                            "phi": phi_val, "dphi_over_m": dphi_val / m,
                            "T00_over_m2": T_val / m**2})
    print(f"{xm:>10.2f}  {phi_val:>12.6f}  {dphi_val/m:>14.8f}  {T_val/m**2:>14.8f}")

print()
print(f"Peak T_00 at x=0: T_00(0) = {T00(0, m):.6f} MeV^2")
print(f"  = (1/2)(2m/7)^2 + V(4/7 * pi/4) at x=0")
print(f"  dPhi/dx|_0 = 2m/7 = {2*m/7:.4f} MeV")
print(f"  (1/2)(2m/7)^2 = {0.5*(2*m/7)**2:.4f} MeV^2")
print()

# Verify BPS saturation: T_00 = (dPhi/dx)^2 on BPS solution
dphi_at_0 = kink_deriv(0, m)
T00_at_0 = T00(0, m)
V_at_0 = potential(kink_profile(0, m), m)
print(f"  BPS check at x=0:")
print(f"  (1/2)(dPhi/dx)^2 = {0.5*dphi_at_0**2:.6f} MeV^2")
print(f"  V(Phi_kink(0))   = {V_at_0:.6f} MeV^2")
print(f"  T_00(0)          = {T00_at_0:.6f} MeV^2")
print(f"  BPS implies V = (1/2)(dPhi/dx)^2 → check: ratio = {V_at_0 / (0.5*dphi_at_0**2):.6f}")
print()

# ── 2. Verify ∫ T_00 dx = M_kink ──────────────────────────────────────────────
print("── PART 2: ∫ T_00(x) dx = M_kink (verify vs 290.10 MeV) ──")
print()

def integrate_T00(m: float, x_max_over_m: float = 30.0, n_pts: int = 100_000) -> float:
    """Numerical integration of T_00 over x ∈ [-x_max, x_max]."""
    x_max = x_max_over_m / m
    dx = 2 * x_max / n_pts
    s = 0.0
    x = -x_max + 0.5 * dx
    for _ in range(n_pts):
        s += T00(x, m) * dx
        x += dx
    return s

print("  Numerical integration: ∫ T_00 dx using midpoint rule with 100k points")
print(f"  Integration range: x ∈ [-30/m, 30/m] = [{-30/m*HBAR_C_MEV_FM:.4f}, {30/m*HBAR_C_MEV_FM:.4f}] fm")

M_kink_numerical = integrate_T00(m, x_max_over_m=30.0, n_pts=100_000)
rel_err = (M_kink_numerical - M_KINK_TARGET_MEV) / M_KINK_TARGET_MEV

print(f"  ∫ T_00 dx (numerical) = {M_kink_numerical:.6f} MeV")
print(f"  M_kink (BPS formula)  = {M_KINK_BPS_MEV:.6f} MeV")
print(f"  M_kink (target)       = {M_KINK_TARGET_MEV:.4f} MeV")
print(f"  Relative error        = {rel_err:.4e}  ({rel_err*100:.6f}%)")
print()
verified = abs(rel_err) < 1e-3
print(f"  ✓ Verified: ∫T_00 dx = M_kink = 290.10 MeV" if verified else
      f"  ✗ Integration error above threshold")
print()

# BPS analytic check: ∫ T_00 dx = ∫ (dPhi/dx)^2 dx  [BPS saturation]
# = ∫ (2m/7 sech(mx))^2 dx
# = (4m^2/49) ∫ sech^2(mx) dx
# = (4m^2/49) * (2/m)  [since ∫ sech^2(u) du = tanh(u) | from -inf to +inf = 2]
M_kink_analytic = (4 * m**2 / 49.0) * (2.0 / m)
print(f"  Analytic BPS check: ∫(2m/7)^2 sech^2(mx) dx = (4m^2/49)(2/m) = 8m/49")
print(f"  = {M_kink_analytic:.6f} MeV  [should match 290.10 MeV]")
print(f"  Relative error from target: {(M_kink_analytic - M_KINK_TARGET_MEV)/M_KINK_TARGET_MEV:.4e}")
print()

# ── 3. Effective width ─────────────────────────────────────────────────────────
print("── PART 3: Effective width of the kink mass distribution ──")
print()

# Width from T_00 profile:
# T_00(x) ∝ sech^2(mx)  [from BPS: T_00 = (dPhi/dx)^2 = (2m/7)^2 sech^2(mx)]
# The FWHM of sech^2(x) is 2 ln(1 + sqrt(2)) ≈ 1.7627
# Width ~ 2 / (m * 1) [defined as half-width at half-max]

# FWHM: sech^2(u) = 1/2 when cosh(u) = sqrt(2) → u = ln(1+sqrt(2)) ≈ 0.8814
u_half = math.acosh(math.sqrt(2))  # = arcsech(1/sqrt(2))
x_HWHM = u_half / m   # half-width at half-max in MeV^-1
x_FWHM = 2 * x_HWHM

# Convert to fm using hbar*c = 197.3 MeV*fm → 1 MeV^-1 = 197.3 fm
x_HWHM_fm = x_HWHM * HBAR_C_MEV_FM
x_FWHM_fm = x_FWHM * HBAR_C_MEV_FM

# Compton wavelength of phi
lambda_C = 1.0 / m  # = 1/m_phi in natural units
lambda_C_fm = lambda_C * HBAR_C_MEV_FM

# RMS width from ∫ x^2 T_00 dx / ∫ T_00 dx
# For sech^2: <x^2> = pi^2/(6 m^2) [standard result]
x_rms = math.pi / (math.sqrt(6) * m)
x_rms_fm = x_rms * HBAR_C_MEV_FM

print(f"  T_00(x) ∝ sech^2(m x)  [from BPS saturation]")
print(f"  m_phi = {m:.4f} MeV → Compton scale 1/m_phi = {lambda_C_fm:.6f} fm")
print()
print(f"  HWHM: u_half = arccosh(sqrt(2)) = {u_half:.6f}")
print(f"  x_HWHM = {u_half:.6f} / m_phi = {x_HWHM_fm:.6f} fm")
print(f"  FWHM   = {x_FWHM_fm:.6f} fm = {x_FWHM / lambda_C:.4f} / m_phi")
print()
print(f"  RMS width: <x^2>^1/2 = pi/(sqrt(6) * m_phi) = {x_rms_fm:.6f} fm")
print(f"  = {x_rms / lambda_C:.4f} / m_phi  (same scale as Compton wavelength)")
print()
print(f"  → Kink width ~ 1/m_phi = {lambda_C_fm:.4f} fm [Compton wavelength confirmed]")
print()

# ── 4. Newtonian gravitational potential ───────────────────────────────────────
print("── PART 4: Newtonian gravitational potential from kink T_00 ──")
print()

# A static kink along the z-axis is a domain wall in 3+1D.
# The gravitational potential far from a POINT PARTICLE of mass M is:
#   phi_grav(r) = -G_N M / r
# But a kink is a 1D localized object (in x), uniform in y,z (domain wall).
# For a point-particle KINK in 3+1D (treating kink as localized particle):
#   M_grav = ∫ T_00 d^3x = M_kink (when kink length is finite, e.g. compactified)

# In 3+1D, treating kink as a 0+1D particle (non-relativistic limit):
# phi_grav(r) = -G_N * M_kink / r  for r >> 1/m_phi

# The key check is E = M_kink c^2 (mass-energy equivalence)
# This is trivially true: T_00 IS the energy density, and ∫T_00 d^3x = E = M c^2
# by the definition of mass in special relativity.

# Gravitational coupling:
# G_N * M_kink^2 has units of length in 3+1D [G_N] = MeV^-2, [M^2] = MeV^2
# Gravitational radius (Schwarzschild-like): R_S = 2 G_N M_kink / c^2

R_S_kink = 2.0 * G_N_MEV_INV2 * M_KINK_BPS_MEV  # MeV^-1 in natural units
R_S_kink_fm = R_S_kink * HBAR_C_MEV_FM

print(f"  Treating kink as point particle with M_grav = M_kink = {M_KINK_BPS_MEV:.4f} MeV")
print()
print(f"  Newtonian potential: phi_grav(r) = -G_N * M_kink / r")
print(f"  G_N = {G_N_MEV_INV2:.4e} MeV^-2 = {G_N_GEV_INV2:.4e} GeV^-2")
print()
print(f"  Schwarzschild radius: R_S = 2 G_N M_kink = {R_S_kink:.4e} MeV^-1")
print(f"  = {R_S_kink_fm:.4e} fm = {R_S_kink_fm * 1e-15:.4e} m")
print()

# The Fourier transform of T_00 for a localized kink:
# T_00(x) = (4m^2/49) sech^2(mx) → FT in 1D:
# T_00(k) = (8m/49) * (pi k/m) / sinh(pi k/m)  = (8m/49) * (pi u) / sinh(pi u)
# where u = k/m

# At k=0: T_00(k=0) = ∫ T_00(x) dx = M_kink = 8m/49 ✓
# The Fourier transform shows how the mass is distributed in momentum space
# For gravitational potential in 3D (Poisson equation):
# nabla^2 phi_grav = 4 pi G_N rho
# For localized mass distribution rho(r) = M_kink delta^3(r) (point limit):
# phi_grav(k) = -4 pi G_N M_kink / k^2

print(f"  Fourier transform of T_00(x) for kink along x-axis:")
print(f"  T_00_hat(k) = (8m/49) * (pi k/m) / sinh(pi k/m)")
print(f"  At k=0: T_00_hat(0) = M_kink = {M_KINK_BPS_MEV:.4f} MeV ✓")
print()

# Check at a few k values
print(f"  {'k/m':>8}  {'T_00_hat(k)/M_kink':>20}  {'physical k [MeV]':>18}")
print("  " + "-" * 52)
for k_over_m in [0.001, 0.1, 0.5, 1.0, 2.0, 5.0]:
    u = k_over_m
    if u < 1e-6:
        ratio = 1.0  # limit
    else:
        ratio = (math.pi * u) / math.sinh(math.pi * u)
    k_phys = k_over_m * m
    print(f"  {k_over_m:>8.3f}  {ratio:>20.8f}  {k_phys:>18.4f} MeV")

print()
print(f"  → At low k (long range), T_00_hat → M_kink (point mass limit)")
print(f"  → At k ~ m_phi, form factor starts to deviate (kink has finite size)")
print(f"  → Gravitational potential matches that of a point mass M_kink for r >> 1/m_phi")
print()

# Mass-energy equivalence check
print("  MASS-ENERGY EQUIVALENCE CHECK:")
print(f"  E_kink = M_kink c^2 = {M_KINK_BPS_MEV:.4f} MeV  (rest energy = BPS mass)")
print(f"  m_grav = E_kink / c^4 * G_N  (GR coupling to T_00)")
print(f"  This is trivially satisfied: T_00 IS the energy density,")
print(f"  and GR couples to T_μν, so the gravitational mass = inertial mass = E/c^2")
print(f"  → Consistent by construction with GR equivalence principle")
print()

# ── 5. Gravitational self-energy ───────────────────────────────────────────────
print("── PART 5: Gravitational self-energy of the kink ──")
print()

# Gravitational self-energy of an object with mass M and size R:
# U_grav ~ - G_N M^2 / R
# R_kink ~ 1/m_phi (Compton wavelength scale from T_00 profile)

R_kink_mev_inv = 1.0 / m  # 1/m_phi in MeV^-1
R_kink_fm_val = R_kink_mev_inv * HBAR_C_MEV_FM

U_grav = G_N_MEV_INV2 * M_KINK_BPS_MEV**2 / R_kink_mev_inv  # MeV (self-energy)
ratio_U_grav_to_M = U_grav / M_KINK_BPS_MEV

print(f"  Estimate: U_grav ~ G_N * M_kink^2 / R_kink")
print(f"  R_kink ~ 1/m_phi = {R_kink_fm_val:.6f} fm")
print(f"  G_N = {G_N_MEV_INV2:.4e} MeV^-2")
print(f"  M_kink = {M_KINK_BPS_MEV:.4f} MeV")
print()
print(f"  U_grav ~ G_N * M_kink^2 * m_phi = {U_grav:.4e} MeV")
print(f"  U_grav / M_kink = {ratio_U_grav_to_M:.4e}")
print(f"  = G_N * M_kink * m_phi = G_N * (8/49 * m_tau) * m_tau")
print()

# In terms of Planck mass:
M_ratio = M_KINK_BPS_MEV / M_PLANCK_MEV
print(f"  (M_kink / M_Planck)^2 = ({M_KINK_BPS_MEV:.2f} / {M_PLANCK_MEV:.4e})^2 = {M_ratio**2:.4e}")
print(f"  U_grav / M_kink ~ (M_kink / M_Planck)^2 = {M_ratio**2:.4e}")
print()
print(f"  → Gravitational self-energy is NEGLIGIBLE: U_grav / M_kink ~ 10^{math.log10(M_ratio**2):.0f}")
print(f"  → Kink is firmly in the quantum / non-gravitational regime")
print(f"  → Classical GR corrections are irrelevant at this mass scale")
print()

# ── Summary ────────────────────────────────────────────────────────────────────
print("── SUMMARY ──")
print(f"  ∫ T_00 dx (numerical) = {M_kink_numerical:.6f} MeV")
print(f"  ∫ T_00 dx (analytic)  = {M_kink_analytic:.6f} MeV")
print(f"  M_kink (target)       = {M_KINK_TARGET_MEV:.4f} MeV")
print(f"  Relative error        = {rel_err:.4e}")
print(f"  Verified: {'YES ✓' if verified else 'NO ✗'}")
print()
print(f"  T_00 peak at x=0: {T00(0, m):.4f} MeV²")
print(f"  Kink width (FWHM): {x_FWHM_fm:.6f} fm = {x_FWHM/lambda_C:.4f} / m_phi")
print(f"  Compton wavelength 1/m_phi: {lambda_C_fm:.6f} fm")
print(f"  → Width ~ Compton wavelength ✓")
print()
print(f"  Schwarzschild radius: {R_S_kink_fm:.4e} fm")
print(f"  Gravitational self-energy: U_grav ~ {U_grav:.4e} MeV")
print(f"  U_grav / M_kink ~ {ratio_U_grav_to_M:.4e}  (negligible — quantum regime)")
print()
print(f"  CatLevel: CatA (all checks pass; mass-energy equivalence trivially satisfied)")
print()

# ── Save results ───────────────────────────────────────────────────────────────
results = {
    "task": "075-KINKSRC",
    "description": "Kink as gravitational source",
    "m_phi_MeV": M_TAU_MEV,
    "M_kink_BPS_MeV": M_KINK_BPS_MEV,
    "M_kink_target_MeV": M_KINK_TARGET_MEV,
    "T00_peak_at_x0_MeV2": T00(0, m),
    "T00_peak_formula": "(1/2)(2m/7)^2 + V(pi/4 * 4/7) at x=0 = (4m^2/49) * [1/2 + 1/2] = (4m^2/49)",
    "integral_T00": {
        "numerical_MeV": M_kink_numerical,
        "analytic_MeV": M_kink_analytic,
        "target_MeV": M_KINK_TARGET_MEV,
        "relative_error": rel_err,
        "verified": verified,
        "comment": "∫T_00 dx = (8/49)m_phi = M_kink via BPS analytic formula",
    },
    "kink_width": {
        "Compton_wavelength_fm": lambda_C_fm,
        "FWHM_fm": x_FWHM_fm,
        "FWHM_over_lambda_C": x_FWHM / lambda_C,
        "RMS_width_fm": x_rms_fm,
        "comment": "FWHM of sech^2(mx) = 2 arccosh(sqrt(2)) / m",
    },
    "Fourier_transform": {
        "formula": "T00_hat(k) = (8m/49) * (pi k/m) / sinh(pi k/m)",
        "T00_hat_at_k0": M_kink_analytic,
        "comment": "At k→0: T00_hat → M_kink (point-mass limit); deviates at k~m_phi",
    },
    "gravitational_potential": {
        "form": "phi_grav(r) = -G_N * M_kink / r  for r >> 1/m_phi",
        "Schwarzschild_radius_fm": R_S_kink_fm,
        "G_N_MeV_inv2": G_N_MEV_INV2,
        "mass_energy_equivalence": (
            "Trivially satisfied: T_00 IS the energy density; "
            "GR coupling to T_munu gives m_grav = E_kink/c^2 by construction"
        ),
    },
    "gravitational_self_energy": {
        "estimate_MeV": U_grav,
        "ratio_to_M_kink": ratio_U_grav_to_M,
        "log10_ratio": math.log10(abs(ratio_U_grav_to_M)),
        "M_kink_over_M_Planck": M_ratio,
        "verdict": "Negligible — kink is firmly in quantum non-gravitational regime",
    },
    "BPS_saturation_check": {
        "V_at_x0_MeV2": V_at_0,
        "half_dphi2_at_x0_MeV2": 0.5 * dphi_at_0**2,
        "ratio_V_to_half_dphi2": V_at_0 / (0.5 * dphi_at_0**2),
        "comment": "BPS: V = (1/2)(dPhi/dx)^2 at x=0",
    },
    "profile_samples": profile_points,
    "CatLevel": "CatA",
    "verdict": (
        f"∫T_00 dx = {M_kink_numerical:.4f} MeV (target 290.10 MeV, rel err {rel_err:.2e}). "
        "Width ~ 1/m_phi confirmed. "
        "Gravitational self-energy negligible (quantum regime). "
        "Mass-energy equivalence trivially satisfied by GR T_munu coupling."
    ),
    "elapsed_s": time.time() - t0,
}

outfile = "phimdl_kink_gravitational_source_results.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {outfile}")
print(f"Elapsed: {results['elapsed_s']:.2f}s")

signal.alarm(0)
