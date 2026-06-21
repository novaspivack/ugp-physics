"""
EPIC_076 Session 1 — M2/M3 computations
Graviton Fock space from Phi_MDL kinks + Black hole entropy from GTE.
"""

import math
import json

# ────────────────────────────────────────────────────────────────────────────
# Physical constants (natural units: hbar = c = 1)
# ────────────────────────────────────────────────────────────────────────────
hbar_c_MeV_fm = 197.3269804  # MeV·fm  (NIST 2024)
# 1 fm = 1/(197.3269804 MeV)   in natural units
# 1 m  = 1e15 fm → 1 m = 5.06773e12 MeV^{-1}
m_per_MeV_inv = 1e15 / hbar_c_MeV_fm          # MeV^{-1} per metre
kg_per_MeV    = 1.0 / (hbar_c_MeV_fm * 1e15 * 1.602176634e-19 / (2.99792458e8)**2)
# simpler: 1 kg = c^2 / e * 10^{-3} / (MeV/J) ...
# Use: 1 GeV = 1.602176634e-10 J; 1 J = 1 kg m^2/s^2; 1 kg = c^2 J^{-1}
# 1 kg = (2.99792458e8)^2 J / (1.602176634e-10 J/GeV) GeV = 5.60959e26 GeV
kg_per_GeV    = (2.99792458e8)**2 / 1.602176634e-10   # GeV per kg (= 5.6096e26)
kg_per_MeV    = kg_per_GeV * 1e3                       # MeV per kg (= 5.6096e29)

# ────────────────────────────────────────────────────────────────────────────
# GTE parameters (CatAD)
# ────────────────────────────────────────────────────────────────────────────
M_kink_MeV   = 290.10          # MeV  (CatA, P42)
m_tau_MeV    = 1776.86         # MeV  (tau lepton = gen3 GTE kink)
F21          = 21              # |F₂₁|  (Frobenius group order)
Z7           = 7               # |Z₇|
n_orb        = 10              # PSC orbit count (F₂₁ exponent)
b0           = 7               # QCD β₀ coefficient = |Z₇| (CatAL)

# GTE hierarchy formula: M_Pl / m_tau = F21^10 * Z7^7 / 2
ratio_GTE    = (F21**n_orb) * (Z7**b0) / 2
M_Pl_MeV     = m_tau_MeV * ratio_GTE         # MeV
M_Pl_GeV     = M_Pl_MeV * 1e-3               # GeV
ratio_PDG    = 1.2209e19 / 1776.86e-3        # PDG: M_Pl = 1.2209e19 GeV, m_tau = 1776.86 MeV
error_pct    = abs(ratio_GTE - ratio_PDG) / ratio_PDG * 100

# G_N in natural units: G_N = 1/M_Pl^2 [MeV^{-2}]
G_N_natural  = 1.0 / M_Pl_MeV**2

print("=" * 65)
print("GTE PARAMETERS")
print("=" * 65)
print(f"  m_tau          = {m_tau_MeV:.4f} MeV")
print(f"  M_Pl/m_tau GTE = {ratio_GTE:.6e}")
print(f"  M_Pl/m_tau PDG = {ratio_PDG:.6e}")
print(f"  Error          = {error_pct:.4f}%")
print(f"  M_Pl (GTE)     = {M_Pl_GeV:.4e} GeV")
print(f"  G_N (nat.)     = {G_N_natural:.4e} MeV^-2")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK A1: h_μν(r) for static kink (point-mass approx)
# h_00(r) = -4 G_N M_kink / r  (Newtonian × 2 in harmonic gauge)
# In natural units: M_kink [MeV], r [MeV^{-1}], h_00 dimensionless
# ────────────────────────────────────────────────────────────────────────────

distances_fm  = [1.0, 1e-3, 1e-5]  # fm: 1 fm, 1 pm, 0.01 pm (~Å)
distances_label = ["1 fm", "1 pm (10^-3 fm)", "1 Å (10^-5 fm, ~Bohr)"]

print("=" * 65)
print("TASK A1: Linearized metric h_00(r) from single static kink")
print("  (harmonic gauge; h_00 = -4 G_N M_kink / r)")
print("=" * 65)

h00_results = {}
for r_fm, label in zip(distances_fm, distances_label):
    r_nat = r_fm / hbar_c_MeV_fm          # MeV^{-1}
    h00   = -4.0 * G_N_natural * M_kink_MeV / r_nat
    hij   = -4.0 * G_N_natural * M_kink_MeV / r_nat   # isotropic; each h_ii
    print(f"  r = {label:35s}: h_00 = {h00:.4e},  h_ij = {hij:.4e}  (<<1 ✓)")
    h00_results[label] = {"r_fm": r_fm, "h00": h00, "hij": hij}

print()
print("  Conclusion: h_μν << 1 at all kink scales → linearised approx valid ✓")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK A2: Graviton-kink coupling constant
# gravitational fine-structure constant α_g = G_N M_kink^2 = (M_kink/M_Pl)^2
# Single-graviton vertex factor in harmonic gauge: κ = sqrt(16π G_N)
#   coupling amplitude for kink→kink+graviton ∝ κ M_kink
# ────────────────────────────────────────────────────────────────────────────
alpha_g      = G_N_natural * M_kink_MeV**2
kappa        = math.sqrt(16 * math.pi * G_N_natural)   # [MeV^{-1}]
# g_kink-grav = kappa * M_kink / (2 M_kink) = kappa/2 for static kink
g_kink_grav  = kappa * M_kink_MeV          # coupling in amplitude

print("=" * 65)
print("TASK A2: Graviton-kink coupling")
print("=" * 65)
print(f"  α_g = G_N M_kink^2 = {alpha_g:.4e}  (dimensionless, Planck-suppressed)")
print(f"  κ   = √(16πG_N)    = {kappa:.4e}  MeV^-1")
print(f"  g_{'{kink-grav}'} = κ M_kink    = {g_kink_grav:.4e}  (dimensionless vertex)")
print(f"  (PDG value from 80-QGR: α_g ≈ 5.65×10^-40)")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK A2b: Graviton-kink coupling from Ninja's formula in prompt
# g_kink-graviton = sqrt(4 G_N M_kink) / l_Pl
# l_Pl = 1/M_Pl
# ────────────────────────────────────────────────────────────────────────────
l_Pl         = 1.0 / M_Pl_MeV             # MeV^{-1}
g_kink_grav2 = math.sqrt(4 * G_N_natural * M_kink_MeV) / l_Pl  # = sqrt(4 M_kink M_Pl^2) / M_Pl = 2 sqrt(M_kink M_Pl)
print(f"  g_{'{kink-grav}'} (prompt formula) = {g_kink_grav2:.4e}")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK A3: Graviton Fock space — mode structure
# Mode expansion in a box L: ω_k = |k|, k = 2π n / L
# Zero-point energy density: ρ_vac = ∫_0^{M_Pl} d³k/(2π)³ ω_k/2 (UV cutoff M_Pl)
# In 3D: ρ_vac = (1/4π²) ∫_0^{M_Pl} k³/2 dk = M_Pl^4 / 16π²
# (2 helicity states × 1/2 per mode = 1 per mode, then ×2 for both polarizations)
# ────────────────────────────────────────────────────────────────────────────
rho_vac_grav = M_Pl_MeV**4 / (16 * math.pi**2)   # MeV^4, graviton ZPE density (1 polarization)
rho_vac_grav_both = 2 * rho_vac_grav               # both helicities (+2, -2)

# Convert to SI energy density: 1 MeV^4 = ? J/m^3
# 1 MeV = 1.602e-13 J; 1 MeV^{-1} = 197.3e-15 m → 1 MeV^4 = (1.602e-13)^4 J^4 / (197.3e-15 m)^3 ...
# Better: rho_vac in GeV^4, then convert
# 1 GeV^4 = 1.602e-10 J / (197.3e-15 m)^3... use known conversion:
# 1 GeV^4 in natural units = 1 GeV^4 / (hbar c)^3 in J/m^3
# hbar c = 197.3 MeV fm = 197.3e-15 m * 1e6 * 1.6e-19 J/eV = ...
# Use: 1 GeV^4 = 2.320e47 J/m^3 (standard QFT result)
# So 1 MeV^4 = 1e-24 GeV^4 = 2.320e47 * 1e-24 J/m^3 = 2.320e23 J/m^3
MeV4_to_Jm3  = (1.602176634e-13)**4 / (hbar_c_MeV_fm * 1e-15)**3
print("=" * 65)
print("TASK A3: Graviton Fock vacuum energy density")
print("  (UV cutoff = M_Pl, 2 helicity states)")
print("=" * 65)
print(f"  ρ_grav = 2 × M_Pl^4/(16π²) = {rho_vac_grav_both:.4e}  MeV^4")
print(f"         = {rho_vac_grav_both * MeV4_to_Jm3:.4e}  J/m^3")
print(f"  Compare: observed Λ energy density ≈ 6.9×10^-10 J/m^3")
print(f"  Hierarchy (ZPE/Λ_obs) ≈ {rho_vac_grav_both * MeV4_to_Jm3 / 6.9e-10:.4e}  [CC problem]")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK A3b: Single-graviton emission rate (dimensional estimate)
# Kink at rest → emits a graviton of energy ω ~ M_kink (mass-equivalent)
# Rate Γ ~ G_N M_kink^2 × ω ~ α_g × M_kink ~ (M_kink/M_Pl)^2 × M_kink
# (analogous to Larmor formula for gravity: P = G_N a^2 m^2 / (...)
# For kink at rest: P ≈ G_N M_kink^2 × M_kink^2 [NR limit, dimensional est]
# ────────────────────────────────────────────────────────────────────────────
Gamma_kink_grav = alpha_g * M_kink_MeV    # MeV (natural units → Γ in MeV)
# In SI: Γ [s^-1] = Γ [MeV] × 1.519×10^21 s^-1/MeV (since 1 MeV = 1.519e21 ħ s^-1)
MeV_to_inv_s = 1.0 / (6.582119569e-22)    # 1/s per MeV (from hbar = 6.582e-22 MeV·s)
Gamma_SI     = Gamma_kink_grav * MeV_to_inv_s
lifetime_s   = 1.0 / Gamma_SI
print("=" * 65)
print("TASK A3b: Single-graviton emission rate from kink (dim. estimate)")
print("=" * 65)
print(f"  Γ_kink→kink+graviton ~ α_g × M_kink = {Gamma_kink_grav:.4e}  MeV")
print(f"                                       = {Gamma_SI:.4e}  s^-1")
print(f"  Gravitational lifetime τ_grav ~ {lifetime_s:.4e}  s")
print(f"  (Age of universe ~ 4.35×10^17 s → kinks are gravitationally stable ✓)")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK B1: Black hole entropy from GTE-derived M_Pl
# S_BH = A M_Pl^2 / 4  (Bekenstein-Hawking in natural units)
# ────────────────────────────────────────────────────────────────────────────
M_sun_kg   = 1.989e30  # kg
# Convert to MeV
M_sun_MeV  = M_sun_kg * kg_per_MeV

r_S_sun_nat = 2 * G_N_natural * M_sun_MeV    # MeV^{-1}
r_S_sun_m   = r_S_sun_nat / m_per_MeV_inv     # metres
A_sun_nat   = 4 * math.pi * r_S_sun_nat**2    # MeV^{-2}
S_BH_sun    = A_sun_nat * M_Pl_MeV**2 / 4     # dimensionless

# Planck-mass BH
M_Pl_kg     = M_Pl_MeV / kg_per_MeV
r_S_Pl_nat  = 2 * G_N_natural * M_Pl_MeV      # = 2 l_Pl = 2/M_Pl
A_Pl_nat    = 4 * math.pi * r_S_Pl_nat**2
S_BH_Pl     = A_Pl_nat * M_Pl_MeV**2 / 4

print("=" * 65)
print("TASK B1: BH entropy from GTE-derived M_Pl")
print("  S_BH = A × M_Pl^2 / 4  (natural units, dimensionless)")
print("=" * 65)
print(f"  Solar-mass BH:")
print(f"    M_sun          = {M_sun_MeV:.4e}  MeV")
print(f"    r_S(sun)       = {r_S_sun_m:.4f}  m  (PDG: 2953 m)")
print(f"    A(sun)         = {A_sun_nat:.4e}  MeV^-2")
print(f"    S_BH(sun)      = {S_BH_sun:.4e}  (dimensionless)")
print(f"  Planck-mass BH:")
print(f"    M_Pl           = {M_Pl_MeV:.4e}  MeV")
print(f"    r_S(Pl)        = 2/M_Pl = {r_S_Pl_nat:.4e}  MeV^-1")
print(f"    A(Pl)          = {A_Pl_nat:.4e}  MeV^-2")
print(f"    S_BH(Pl)       = {S_BH_Pl:.4f}  (≈ 4π ≈ 12.57 by construction)")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK B2: Z₇ domain wall counting vs Bekenstein-Hawking
# s_wall = log(7) × M_kink^2 per unit area (entropy from Z₇ states at kink sites)
# Compare to S_BH/A = M_Pl^2/4
# ────────────────────────────────────────────────────────────────────────────
s_wall_kink = math.log(7) * M_kink_MeV**2     # entropy per MeV^{-2} (kink-scale counting)
s_BH_per_A  = M_Pl_MeV**2 / 4                 # entropy per MeV^{-2}

ratio_kink_vs_BH = s_BH_per_A / s_wall_kink

print("=" * 65)
print("TASK B2: Domain wall Z₇ counting vs. Bekenstein-Hawking")
print("=" * 65)
print(f"  s_wall (Z₇ kink-site)  = log(7) × M_kink^2 = {s_wall_kink:.4e}  MeV^2")
print(f"  S_BH/A                 = M_Pl^2/4           = {s_BH_per_A:.4e}  MeV^2")
print(f"  Ratio (S_BH/A) / s_wall = {ratio_kink_vs_BH:.4e}")
print(f"  (M_Pl/M_kink)^2        = {(M_Pl_MeV/M_kink_MeV)**2:.4e}")
print(f"  Interpretation: BH horizon must be counted at Planck scale, not kink scale")
print()

# Planck-scale site counting: N_sites = A × M_Pl^2
# For S_BH = A × M_Pl^2/4: need entropy per Planck site = 1/4 nat
# or equivalently log(N_states) = 1/4 per Planck site
# 1/4 = log(e^{1/4}) → effective number of states per Planck area = e^{1/4} ≈ 1.284
N_states_per_Pl_area = math.exp(0.25)
print(f"  Planck-site counting: log(N_states)/Planck area = 1/4")
print(f"  → N_states per Planck area = e^{{1/4}} = {N_states_per_Pl_area:.4f}  (non-integer)")
print(f"  → log(4)/4 per Planck area: 4 states → S = A × M_Pl^2 × log(4)/4 = {math.log(4)/4:.4f} per Planck site")
print(f"  → log(3)/4 per Planck area: 3 states → S = A × M_Pl^2 × log(3)/4 = {math.log(3)/4:.4f} per Planck site")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK B3: GTE-specific entropy formula
# The GTE MDL entropy for the gravitational hierarchy:
# S_GTE = n log|F₂₁| + b₀ log|Z₇| - log 2
#       = log(F₂₁^10 × Z₇^7 / 2)
#       = log(M_Pl/m_tau)
# This is the description length of the hierarchy, NOT an entropy per unit area.
# ────────────────────────────────────────────────────────────────────────────
S_GTE_hierarchy = n_orb * math.log(F21) + b0 * math.log(Z7) - math.log(2)
print("=" * 65)
print("TASK B3: GTE MDL entropy and its relation to S_BH")
print("=" * 65)
print(f"  S_GTE = n·log(F₂₁) + b₀·log(Z₇) - log(2)")
print(f"        = 10·log(21) + 7·log(7) - log(2)")
print(f"        = {S_GTE_hierarchy:.4f}  nats")
print(f"        = log({ratio_GTE:.4e}) = log(M_Pl/m_tau) ✓")
print(f"  (This is the description length of the hierarchy — not entropy/area)")
print()
print(f"  The THREE distinct notions of entropy in GTE:")
print(f"    1. S_GTE = log(M_Pl/m_tau) = {S_GTE_hierarchy:.2f}  [MDL description length]")
print(f"    2. s_BH/A = M_Pl^2/4       [geometric entropy density in Planck units]")
print(f"    3. s_wall = log(7)×M_kink^2 [kink-site Z₇ counting]")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK B4: H3 holographic interpretation
# If horizon is a domain wall at r_S with sites at Planck spacing (1/M_Pl):
# N_sites = A × M_Pl^2
# Each site: how many GTE states?
# For S = A × M_Pl^2/4: need N_states_per_site = e^{1/4}
# BUT: in GTE, a Planck-scale site is a junction of MDL kinks.
# The REFLEXIVE UNITARITY (P16) already establishes BH information is preserved.
# The entropic formula S_BH = A/(4G) emerges from the GTE Lorentz geometry
# once G = m_tau^2/(M_Pl/m_tau)^2 is inserted.
# ────────────────────────────────────────────────────────────────────────────

# The Z₃-invariant entropy approach for B-H:
# The GTE Ansatz: each Planck-scale cell on the horizon has Z₃ × Z₃ states
# |Z₃ × Z₃| = 9 states → S = A × M_Pl^2 × log(9)/1 = A × M_Pl^2 × 2log(3)
# That's too large by factor 8 log(3).
# 
# Alternative: the entropy is NOT from counting micro-states at each site
# but from the TOTAL MDL description length of the horizon geometry.
# S_BH = A/A_Pl × log(|F₂₁| × |Z₇| / |F₂₁|×...) 
# This needs a different derivation.

# Numerics for specific BH masses:
print("=" * 65)
print("TASK B4: S_BH for specific GTE-predicted masses")
print("=" * 65)

# Tau lepton mass BH (hypothetical)
M_tau_BH_MeV = m_tau_MeV
r_S_tau      = 2 * G_N_natural * M_tau_BH_MeV
A_tau        = 4 * math.pi * r_S_tau**2
S_tau_BH     = A_tau * M_Pl_MeV**2 / 4
print(f"  Tau-mass BH (M = m_tau = {m_tau_MeV:.2f} MeV):")
print(f"    r_S = {r_S_tau:.4e} MeV^-1  = {r_S_tau / m_per_MeV_inv:.4e} m")
print(f"    S_BH = {S_tau_BH:.4f}  (sub-quantum; smaller than 1 nat → not a classical BH)")
print()

# Earth-mass BH
M_earth_kg  = 5.972e24
M_earth_MeV = M_earth_kg * kg_per_MeV
r_S_earth   = 2 * G_N_natural * M_earth_MeV
A_earth     = 4 * math.pi * r_S_earth**2
S_earth_BH  = A_earth * M_Pl_MeV**2 / 4
print(f"  Earth-mass BH (M = M_earth = {M_earth_MeV:.4e} MeV):")
print(f"    r_S = {r_S_earth/m_per_MeV_inv*1e3:.4f} mm  (PDG: 8.87 mm)")
print(f"    S_BH = {S_earth_BH:.4e}")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK B5: Summary of routes to S_BH from GTE
# ────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("TASK B5: Interpretation scorecard for S_BH from GTE")
print("=" * 65)
print()
print("  Route (a): Plug GTE-derived G_N into Bekenstein-Hawking formula")
print(f"    S_BH(sun) = {S_BH_sun:.4e}  [GTE prediction, CatA once G CatA]")
print()
print("  Route (b): Z₇ domain wall counting at KINK scale")
print(f"    s_wall(kink) = log(7) × M_kink^2 = {s_wall_kink:.4e} MeV^2")
print(f"    Disagreement with S_BH/A by factor = {ratio_kink_vs_BH:.4e}")
print(f"    → FAILS: kink sites are NOT Planck-scale sites. Different physics.")
print()
print("  Route (c): Z₇ counting at PLANCK scale (holographic H3)")
print(f"    Each Planck site has k states; for S = A M_Pl^2/4:")
print(f"      need k = e^(1/4) = {N_states_per_Pl_area:.4f}  (non-integer → no exact GTE formula yet)")
print()
print("  Route (d): MDL description length approach")
print(f"    S_GTE = log(M_Pl/m_tau) = {S_GTE_hierarchy:.4f} nats")
print(f"    This is the horizon self-encoding entropy IF the horizon area = 1 Planck area.")
print(f"    For macroscopic BH: multiply by A/A_Pl:")
print(f"      S_MDL = (A/A_Pl) × log(M_Pl/m_tau)")
print()
A_Pl_nat_exact = (4 * math.pi * (2.0/M_Pl_MeV)**2)   # = 16π/M_Pl^2
S_sun_MDL_route = (A_sun_nat / A_Pl_nat_exact) * S_GTE_hierarchy
print(f"    S_MDL(sun) = (A_sun / A_Pl) × log(M_Pl/m_tau)")
print(f"               = {A_sun_nat / A_Pl_nat_exact:.4e} × {S_GTE_hierarchy:.4f}")
print(f"               = {S_sun_MDL_route:.4e}")
print(f"    S_BH(sun)  = {S_BH_sun:.4e}")
ratio_mdl = S_sun_MDL_route / S_BH_sun
print(f"    Ratio MDL/BH = {ratio_mdl:.4f}")
print(f"    log(M_Pl/m_tau) / (1/4) = {S_GTE_hierarchy / 0.25:.4f}")
print(f"    → MDL route gives S ~ 4 log(M_Pl/m_tau) × S_BH  (off by factor {ratio_mdl:.2f})")
print()

# ────────────────────────────────────────────────────────────────────────────
# TASK B6: The exact GTE formula for S_BH
# ────────────────────────────────────────────────────────────────────────────
# Route (a) is the correct one numerically.
# The GTE contribution is: M_Pl IS derived from GTE (CatAD), so:
# S_BH = A × m_tau^2 × (F₂₁^10 × Z₇^7/2)^2 / 4
# This is a PURE GTE PREDICTION for S_BH once M_Pl is CatA.
print("=" * 65)
print("TASK B6: Pure GTE formula for S_BH (Route a)")
print("=" * 65)
print(f"  S_BH = A × m_tau^2 × (|F₂₁|^10 × |Z₇|^7 / 2)^2 / 4")
print(f"       = A × m_tau^2 × (21^10 × 7^7 / 2)^2 / 4")
print(f"       = A × ({m_tau_MeV:.2f} MeV)^2 × ({ratio_GTE:.4e})^2 / 4")
print(f"       = A × M_Pl^2 / 4")
print(f"  [Dimensionless; A in MeV^-2]")
print()
print(f"  This is ROUTE (a): it IS correct physics once G is CatA.")
print(f"  The GTE formula provides G_N = m_tau^2/(F₂₁^10×Z₇^7/2)^2,")
print(f"  and the Bekenstein-Hawking formula then gives S_BH in terms of")
print(f"  GTE-derived fundamental constants.")
print()
print(f"  CatLevel for S_BH via route (a): CatAD")
print(f"  (Inherits from M_Pl/m_tau formula CatAD; no independent state-counting derivation)")
print()

# ────────────────────────────────────────────────────────────────────────────
# Compile summary
# ────────────────────────────────────────────────────────────────────────────
results = {
    "GTE_parameters": {
        "m_tau_MeV": m_tau_MeV,
        "M_Pl_GeV": M_Pl_GeV,
        "ratio_GTE": ratio_GTE,
        "ratio_PDG": ratio_PDG,
        "error_pct": error_pct,
        "G_N_natural_MeV_minus2": G_N_natural,
        "alpha_g": alpha_g,
    },
    "task_A1_h_munu": {
        r: {"h00": v["h00"], "hij": v["hij"]}
        for r, v in h00_results.items()
    },
    "task_A2_coupling": {
        "alpha_g": alpha_g,
        "kappa_MeV_inv": kappa,
        "g_kink_grav": g_kink_grav,
        "g_kink_grav_prompt_formula": g_kink_grav2,
    },
    "task_A3_fock_vacuum": {
        "rho_vac_grav_MeV4": rho_vac_grav_both,
        "rho_vac_grav_Jm3": rho_vac_grav_both * MeV4_to_Jm3,
        "graviton_lifetime_tau_s": lifetime_s,
        "Gamma_kink_to_kink_graviton_MeV": Gamma_kink_grav,
    },
    "task_B1_S_BH": {
        "S_BH_solar": S_BH_sun,
        "S_BH_Planck": S_BH_Pl,
        "r_S_solar_m": r_S_sun_m,
    },
    "task_B2_counting": {
        "s_wall_kink_MeV2": s_wall_kink,
        "s_BH_per_A_MeV2": s_BH_per_A,
        "ratio_BH_over_kink": ratio_kink_vs_BH,
    },
    "task_B5_routes": {
        "route_a_CatLevel": "CatAD",
        "route_b_fails": True,
        "route_c_CatLevel": "open (non-integer N_states)",
        "route_d_off_factor": ratio_mdl,
    }
}

with open("phimdl_graviton_fock_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("=" * 65)
print("Results saved to: phimdl_graviton_fock_results.json")
print("=" * 65)
