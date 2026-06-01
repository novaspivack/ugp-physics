#!/usr/bin/env python3
"""
Rank 074-VORTEX-3D: Phi_MDL domain wall junction (vortex line) tension in 3+1D.

OQ-3DALG-3: Do 3D Phi_MDL vortex lines exist (intersections of two domain walls),
and what is their tension lambda relative to domain wall tension sigma = 7450.31 MeV/fm^2?

Physics setup:
  Two perpendicular domain walls in 3+1D intersect along the z-axis, forming a
  domain wall junction line. In the Z7-symmetric real scalar field Phi_MDL, the
  vacuum manifold is {0, 2pi/7, 4pi/7, ..., 12pi/7} (7 discrete points). Because
  pi_1(Z7) = 0 (discrete set has no non-contractible loops), there are NO vortex
  lines in the topological U(1) sense. What exists are domain wall junctions:
  lines where multiple domain walls meet.

  Product ansatz:
    phi(x,y,z) = kink(x - L/2) + kink(y - L/2)
  This creates:
    Quadrant (x<0, y<0): phi ~ 0          (Z7 vacuum k=0)
    Quadrant (x>0, y<0): phi ~ 2pi/7      (Z7 vacuum k=1)
    Quadrant (x<0, y>0): phi ~ 2pi/7      (Z7 vacuum k=1)
    Quadrant (x>0, y>0): phi ~ 4pi/7      (Z7 vacuum k=2)
  Two domain walls meet along the z-axis: a legitimate Z7 junction line.

  Junction (vortex line) tension lambda:
    The excess energy per unit z-length relative to two isolated domain walls.
    lambda = E_junction/L_z - 2*sigma*L

  If lambda < 0: junction is energetically favorable (binding); walls attract.
  If lambda > 0: junction costs extra energy (topological barrier).

Physical parameters (from prior work, Rank 074-3D):
  m_phi = M_tau = 1776.86 MeV
  M_kink = (8/49) * m_phi = 290.10 MeV  (BPS kink mass, confirmed CatA)
  sigma  = 7450.31 MeV/fm^2             (domain wall tension, confirmed CatA)
  Wall thickness ~ 1/m_phi = 0.111 fm

Wall-clock cap: 600s.
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time

TIMEOUT_SECONDS = 600


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

# --- Physical constants and parameters (from prior Rank 074-3D) ---
N7 = 7
M_TAU_MEV = 1776.86                          # m_phi = M_tau (MeV)
M_KINK_BPS_MEV = (8.0 / 49.0) * M_TAU_MEV  # = 290.10 MeV, 1D BPS kink mass
M_KINK_BPS_GEV = M_KINK_BPS_MEV / 1000.0   # = 0.29010 GeV
HBAR_C_GEV_FM = 0.1973269804                # hbar*c in GeV*fm
HBAR_C_MEV_FM = 197.3269804                 # hbar*c in MeV*fm
SIGMA_PRIOR_MEV_PER_FM2 = 7450.31           # sigma from Rank 074-3D [MeV/fm^2]
SIGMA_SCRIPT_GEV = M_KINK_BPS_GEV          # sigma in script units [GeV]
WALL_THICKNESS_FM = HBAR_C_MEV_FM / M_TAU_MEV  # ~ 1/m_phi in fm = 0.111 fm


# ---------------------------------------------------------------------------
# Field functions (dimensionless coordinates X = m_phi * x, phi dimensionless)
# ---------------------------------------------------------------------------

def kink_profile(X: float) -> float:
    """Z7 kink phi(X) = (4/7) arctan(exp(X)), X = m_phi * x dimensionless."""
    arg = max(-500.0, min(500.0, X))
    return (4.0 / N7) * math.atan(math.exp(arg))


def kink_deriv(X: float) -> float:
    """d(phi)/d(X) = (2/7) sech(X)."""
    arg = max(-500.0, min(500.0, X))
    em = math.exp(arg)
    return (4.0 / N7) / (em + 1.0 / em)   # = (4/7) * 1/(exp(X)+exp(-X)) = (2/7)/cosh(X)


def V_red(phi: float) -> float:
    """Reduced potential (dimensionless): V_red = (1/49)(1 - cos(7*phi))."""
    return (1.0 / 49.0) * (1.0 - math.cos(7.0 * phi))


def T00_red_1d(X: float) -> float:
    """1D reduced energy density (dimensionless): T00 = (1/2)(dphi/dX)^2 + V_red."""
    d = kink_deriv(X)
    phi = kink_profile(X)
    return 0.5 * d * d + V_red(phi)


# ---------------------------------------------------------------------------
# Unit conversion (consistent with Rank 074-3D script)
#
# In dimensionless coordinates (X = m_phi*x):
#   sigma_script [GeV] = m_phi [GeV] * sigma_dim  (sigma_dim = 8/49 dimensionless)
#   sigma_3D [MeV/fm^2] = sigma_script [GeV] * 1000 / (hbar_c_GEV_FM)^2
#
# For the junction tension:
#   lambda_dim [dimensionless] = integral_2D excess V_red dX dY
#   lambda_script [dimensionless] = lambda_dim (same -- 2D integral of dim'less quantity)
#
# Unit conversion (derived from sigma relationship):
#   lambda_ratio = lambda_script / sigma_script  [1/GeV]
#   lambda_over_sigma [fm] = lambda_ratio * hbar_c_GEV_FM [GeV*fm]
#   lambda_3D [MeV/fm] = sigma_3D [MeV/fm^2] * lambda_over_sigma [fm]
#
# Equivalently (verified below):
#   lambda_3D [MeV/fm] = lambda_dim * sigma_3D * hbar_c_GEV_FM / sigma_script
#                      = lambda_dim * 7450.31 * 0.1973 / 0.29010
#                      = lambda_dim * 5067.5  MeV/fm
# ---------------------------------------------------------------------------

CONVERSION_LAMBDA = SIGMA_PRIOR_MEV_PER_FM2 * HBAR_C_GEV_FM / SIGMA_SCRIPT_GEV
# = 7450.31 * 0.1973 / 0.29010 ≈ 5067 MeV/fm per unit of lambda_dim


# =========================================================================
# STEP 1: Sanity check — domain wall tension from 1D BPS integral
# =========================================================================
print("=" * 72)
print("RANK 074-VORTEX-3D: Phi_MDL domain wall junction tension")
print("=" * 72)
print("\nStep 1: Domain wall tension sanity check")

X_MAX_1D = 15.0
N_PTS_1D = 4000
dx_1d = 2.0 * X_MAX_1D / N_PTS_1D
sigma_dim = sum(T00_red_1d(-X_MAX_1D + (i + 0.5) * dx_1d) * dx_1d
               for i in range(N_PTS_1D))

sigma_script_numeric_GeV = M_KINK_BPS_GEV / 49.0 * 49.0 * (sigma_dim / (8.0 / 49.0))
# simpler: sigma_script = m_phi * sigma_dim
sigma_script_numeric_GeV = (M_TAU_MEV / 1000.0) * sigma_dim

sigma_3D_numeric = sigma_script_numeric_GeV * 1000.0 / HBAR_C_GEV_FM**2
sigma_rel_err = abs(sigma_3D_numeric - SIGMA_PRIOR_MEV_PER_FM2) / SIGMA_PRIOR_MEV_PER_FM2
sigma_pass = sigma_rel_err < 1e-4

print(f"  sigma_dim (dimensionless BPS integral) = {sigma_dim:.6f}  [expect 8/49 = {8/49:.6f}]")
print(f"  sigma_script_numeric [GeV] = {sigma_script_numeric_GeV:.6f}  [expect {M_KINK_BPS_GEV:.6f}]")
print(f"  sigma_3D_numeric [MeV/fm^2] = {sigma_3D_numeric:.2f}  [expect {SIGMA_PRIOR_MEV_PER_FM2:.2f}]")
print(f"  relative error vs prior: {100*sigma_rel_err:.6f}%  {'PASS' if sigma_pass else 'FAIL'}")


# =========================================================================
# STEP 2: Junction (vortex line) tension from 2D integral
#
# Product ansatz: phi(X,Y) = kink(X) + kink(Y)  (both walls centered at origin)
#
# Excess potential energy per unit z-length (in dimensionless units):
#   lambda_dim = int int dX dY [V_red(kink(X)+kink(Y)) - V_red(kink(X)) - V_red(kink(Y))]
#
# The kinetic terms cancel exactly (each contributes only to its own wall's energy).
# Derivation:
#   E_combined/L_z = int int dX dY [1/2(d kink_x/dX)^2 + 1/2(d kink_y/dY)^2
#                                   + V(kink_x+kink_y)]
#   E_walls/L_z    = int int dX dY [1/2(d kink_x/dX)^2 + V(kink_x)]
#                  + int int dX dY [1/2(d kink_y/dY)^2 + V(kink_y)]
#                  = L_X*sigma_dim + L_Y*sigma_dim   (two isolated walls)
#   lambda_dim = int int dX dY [V(kink_x+kink_y) - V(kink_x) - V(kink_y)]
#               (kinetic terms cancel since they factor into 1D integrals)
#
# Note: V(0) = 0, so no vacuum subtraction needed.
# =========================================================================
print("\nStep 2: Junction tension lambda (2D grid integral)")

X_MAX_2D = 12.0   # dimensionless — captures well beyond wall thickness
Y_MAX_2D = 12.0
N_GRID = 256       # 256x256 grid — fine enough for ~ 0.1% accuracy

dx2 = 2.0 * X_MAX_2D / N_GRID
dy2 = 2.0 * Y_MAX_2D / N_GRID
dA = dx2 * dy2

# Build kink profile lookup on x-grid (same profile reused for y by symmetry)
kink_vals = [kink_profile(-X_MAX_2D + (i + 0.5) * dx2) for i in range(N_GRID)]
V_kink_vals = [V_red(k) for k in kink_vals]

# Compute 2D integral: sum over all (X, Y) grid cells
lambda_dim = 0.0
total_V_combined = 0.0
total_V_sum = 0.0

for ix in range(N_GRID):
    kx = kink_vals[ix]
    Vkx = V_kink_vals[ix]
    for iy in range(N_GRID):
        ky = kink_vals[iy]   # kink_y(Y) = kink_x(Y) by symmetry
        Vky = V_kink_vals[iy]
        phi_combined = kx + ky
        V_combined = V_red(phi_combined)
        excess = V_combined - Vkx - Vky
        lambda_dim += excess * dA

elapsed = time.time() - t0
print(f"  Grid {N_GRID}x{N_GRID} integration done in {elapsed:.1f}s")
print(f"  lambda_dim (dimensionless excess energy) = {lambda_dim:.6f}")

# Convert to physical units
lambda_MeV_per_fm = lambda_dim * CONVERSION_LAMBDA
lambda_over_sigma_fm = lambda_dim * HBAR_C_GEV_FM / (SIGMA_SCRIPT_GEV * (M_TAU_MEV / 1000.0) / M_KINK_BPS_GEV)
# Simpler form: lambda/sigma [fm] = lambda_dim/sigma_dim * hbar_c/m_phi
lambda_over_sigma_fm_v2 = (lambda_dim / sigma_dim) * WALL_THICKNESS_FM
lambda_MeV_per_fm_v2 = lambda_over_sigma_fm_v2 * SIGMA_PRIOR_MEV_PER_FM2

print(f"  Conversion factor: {CONVERSION_LAMBDA:.2f} MeV/fm per unit lambda_dim")
print(f"  lambda_3D = lambda_dim * {CONVERSION_LAMBDA:.2f} = {lambda_MeV_per_fm:.2f} MeV/fm")
print(f"  [Cross-check v2] lambda_3D = {lambda_MeV_per_fm_v2:.2f} MeV/fm")
print(f"  lambda/sigma = lambda_dim/sigma_dim = {lambda_dim/sigma_dim:.4f}")
print(f"  lambda/sigma [fm] = {lambda_over_sigma_fm_v2:.4f} fm")
print(f"  Wall thickness 1/m_phi = {WALL_THICKNESS_FM:.4f} fm")
print(f"  |lambda/sigma| / wall_thickness = {abs(lambda_dim/sigma_dim):.4f}")


# =========================================================================
# STEP 3: Sign interpretation and stability analysis
# =========================================================================
print("\nStep 3: Sign and stability analysis")
is_negative = lambda_dim < 0
print(f"  lambda_dim = {lambda_dim:.6f}  ({'NEGATIVE: junction releases energy' if is_negative else 'POSITIVE: junction costs energy'})")

if is_negative:
    print("  Physical interpretation:")
    print("   -> lambda < 0: the domain wall junction is ENERGETICALLY FAVORABLE")
    print("   -> Two domain walls of opposite orientations attract and bind")
    print("   -> Junction (z-axis) lowers total energy by |lambda| per unit length")
    print("   -> This is the 'binding energy' of the domain wall junction")
    print("   -> For Z7: three or more walls can meet at a junction (Y-junction)")
    print("   -> pi_1(Z7) = 0: no winding/vortex in topological U(1) sense")
    print("   -> Junction is a codimension-2 wall-junction, not a topological vortex")
else:
    print("  Physical interpretation: lambda > 0 — junction costs energy")
    print("  This would indicate topological barrier to wall intersection.")


# =========================================================================
# STEP 4: Convergence test — compare 128x128 vs 256x256
# =========================================================================
print("\nStep 4: Convergence test (128x128 vs 256x256)")

N_COARSE = 128
dx_c = 2.0 * X_MAX_2D / N_COARSE
dy_c = 2.0 * Y_MAX_2D / N_COARSE
dA_c = dx_c * dy_c

kink_coarse = [kink_profile(-X_MAX_2D + (i + 0.5) * dx_c) for i in range(N_COARSE)]
V_kink_coarse = [V_red(k) for k in kink_coarse]

lambda_dim_coarse = 0.0
for ix in range(N_COARSE):
    kx = kink_coarse[ix]
    Vkx = V_kink_coarse[ix]
    for iy in range(N_COARSE):
        ky = kink_coarse[iy]
        Vky = V_kink_coarse[iy]
        phi_combined = kx + ky
        lambda_dim_coarse += (V_red(phi_combined) - Vkx - Vky) * dA_c

conv_err = abs(lambda_dim - lambda_dim_coarse) / abs(lambda_dim)
print(f"  lambda_dim (128x128) = {lambda_dim_coarse:.6f}")
print(f"  lambda_dim (256x256) = {lambda_dim:.6f}")
print(f"  Convergence error = {100*conv_err:.4f}%")
conv_pass = conv_err < 0.01  # better than 1%
print(f"  Convergence: {'PASS (<1%)' if conv_pass else 'FAIL'}")

lambda_MeV_per_fm_final = lambda_MeV_per_fm
lambda_over_sigma_fm_final = lambda_over_sigma_fm_v2


# =========================================================================
# STEP 5: Physical interpretation — what does lambda measure?
# =========================================================================
print("\nStep 5: Physical summary")
print(f"  Domain wall tension:   sigma  = {SIGMA_PRIOR_MEV_PER_FM2:.2f} MeV/fm^2  (from Rank 074-3D)")
print(f"  Junction line tension: lambda = {lambda_MeV_per_fm_final:.2f} MeV/fm")
print(f"  Ratio lambda/sigma     = {lambda_MeV_per_fm_final/SIGMA_PRIOR_MEV_PER_FM2:.4f} fm")
print(f"  |lambda/sigma|         = {abs(lambda_over_sigma_fm_final):.4f} fm")
print(f"  Wall thickness 1/m_phi = {WALL_THICKNESS_FM:.4f} fm")
print(f"  |lambda/sigma|         = {abs(lambda_over_sigma_fm_final)/WALL_THICKNESS_FM:.3f} x wall_thickness")

# Note on topology:
# Z7 has pi_1 = 0, so the "vortex line" is actually a domain wall junction.
# A proper topological vortex requires pi_1(M) != 0. For Z_N discrete
# symmetries, the defect hierarchy is:
#   Codimension-1: domain walls (Z7 → allowed, sigma = 7450 MeV/fm^2)
#   Codimension-2: vortex strings (requires pi_1 != 0 → NOT topological in Z7)
#   Codimension-3: monopoles (requires pi_2 != 0 → NOT in Z7)
# The "vortex" in this context is a WALL JUNCTION (where two wall-types meet),
# which exists but is NOT topologically protected.

print(f"\n  Topology note:")
print(f"  Z7 vacuum manifold = 7 discrete points, pi_1(Z7) = 0")
print(f"  -> No topological vortex strings in Z7 model")
print(f"  -> lambda is the WALL JUNCTION line tension (codimension-2 junction)")
print(f"  -> Junction occurs where domain walls (winding +1) and (winding +1) meet")
print(f"  -> In the (x>0,y>0) quadrant: phi ~ 4pi/7 (vacuum k=2)")
print(f"  -> This is a VALID Z7 configuration with two walls meeting at z-axis")


# =========================================================================
# Save results
# =========================================================================

elapsed_total = time.time() - t0
all_pass = sigma_pass and conv_pass

results = {
    "rank_id": "074-VORTEX-3D",
    "title": "Phi_MDL domain wall junction (vortex line) tension in 3+1D",
    "oq_closed": "OQ-3DALG-3",
    "field": "Z7-symmetric Klein-Gordon Phi_MDL",
    "ansatz": "phi(x,y) = kink_x(x) + kink_y(y) — two perpendicular domain walls",
    "physical_parameters": {
        "m_phi_MeV": M_TAU_MEV,
        "M_kink_MeV": M_KINK_BPS_MEV,
        "sigma_prior_MeV_per_fm2": SIGMA_PRIOR_MEV_PER_FM2,
        "wall_thickness_fm": WALL_THICKNESS_FM,
        "hbar_c_MeV_fm": HBAR_C_MEV_FM,
    },
    "step1_domain_wall_sanity": {
        "sigma_dim": sigma_dim,
        "sigma_dim_expected": 8.0 / 49.0,
        "sigma_3D_numeric_MeV_per_fm2": sigma_3D_numeric,
        "sigma_rel_err": sigma_rel_err,
        "pass": sigma_pass,
    },
    "step2_junction_tension": {
        "grid_size": f"{N_GRID}x{N_GRID}",
        "X_max_dimensionless": X_MAX_2D,
        "lambda_dim": lambda_dim,
        "sigma_dim": sigma_dim,
        "lambda_over_sigma_dimensionless": lambda_dim / sigma_dim,
        "lambda_over_sigma_fm": lambda_over_sigma_fm_final,
        "lambda_MeV_per_fm": lambda_MeV_per_fm_final,
        "conversion_factor_MeV_per_fm_per_unit": CONVERSION_LAMBDA,
    },
    "step4_convergence": {
        "lambda_dim_128": lambda_dim_coarse,
        "lambda_dim_256": lambda_dim,
        "convergence_error_pct": 100.0 * conv_err,
        "pass": conv_pass,
    },
    "step5_summary": {
        "sigma_MeV_per_fm2": SIGMA_PRIOR_MEV_PER_FM2,
        "lambda_MeV_per_fm": lambda_MeV_per_fm_final,
        "lambda_over_sigma_fm": lambda_over_sigma_fm_final,
        "lambda_over_wall_thickness": lambda_over_sigma_fm_final / WALL_THICKNESS_FM,
        "sign_negative": bool(is_negative),
        "physical_interpretation": (
            "lambda < 0: junction RELEASES energy — domain wall junction is energetically "
            "favorable; walls attract each other at the junction line"
            if is_negative else
            "lambda > 0: junction costs extra energy"
        ),
    },
    "topology_note": {
        "pi_1_Z7": 0,
        "topological_vortex_exists": False,
        "defect_type": "domain_wall_junction (codimension-2)",
        "codimension_1_defect": "domain walls (sigma = 7450.31 MeV/fm^2)",
        "codimension_2_defect": "wall junction line (lambda computed above)",
        "stability": "energetically favorable junction (lambda < 0)" if is_negative else "metastable",
    },
    "wall_clock_seconds": elapsed_total,
    "status": "PASS" if all_pass else "FAIL",
}

out_path = "phimdl_vortex_3d_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)

print("\n" + "=" * 72)
print("FINAL RESULTS")
print("=" * 72)
print(f"  sigma  = {SIGMA_PRIOR_MEV_PER_FM2:.2f} MeV/fm^2  (domain wall tension, Rank 074-3D)")
print(f"  lambda = {lambda_MeV_per_fm_final:.2f} MeV/fm   (wall junction line tension)")
print(f"  lambda/sigma = {lambda_MeV_per_fm_final/SIGMA_PRIOR_MEV_PER_FM2:.5f} fm")
print(f"  |lambda/sigma| = {abs(lambda_over_sigma_fm_final):.5f} fm")
print(f"  |lambda/sigma| / (1/m_phi) = {abs(lambda_over_sigma_fm_final)/WALL_THICKNESS_FM:.3f}")
print(f"  Sign: {'NEGATIVE (junction binding)' if is_negative else 'POSITIVE (junction barrier)'}")
print(f"  Convergence: {100*conv_err:.4f}%  {'PASS' if conv_pass else 'FAIL'}")
print(f"  Status: {results['status']}")
print(f"  Results: {out_path}")
