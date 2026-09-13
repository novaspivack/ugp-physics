"""
EPIC_076 M5 — Planck-Scale Effective Field Theory
GTE-derived Planck mass: M_Pl = m_τ × 21^10 × 7^7 / 2 (CatAD)
G_N = m_τ²/M_Pl² (CatAD)

Computes:
  1. GTE Planck scale summary table
  2. EFT breakdown (α_grav at multiple scales)
  3. Graviton exchange vs QCD at kink scale
  4. GTE prediction for Planck-scale physics (lattice interpretation)
  5. Minimum black hole mass
  6. Hawking temperature for 10 M_Pl black hole

Run: python3 epic076_planck_eft.py
Output: epic076_planck_eft_results.json
"""

import math
import json

# ─────────────────────────────────────────────────────────
# 1. GTE Planck scale summary table
# ─────────────────────────────────────────────────────────

# Physical constants (natural units where ℏ=c=1, energies in MeV)
hbar_c_MeV_fm = 197.3269804  # MeV·fm   (NIST 2018 CODATA)
c_m_per_s     = 2.99792458e8 # m/s
hbar_J_s      = 1.054571817e-34  # J·s
k_B_MeV_per_K = 8.617333262e-11  # MeV/K
fm_per_m      = 1e15         # 1 m = 10^15 fm

# GTE-derived values
m_tau_MeV = 1776.86          # PDG tau mass, MeV
M_Pl_ratio = 21**10 * 7**7 / 2   # dimensionless ratio M_Pl/m_τ (CatAD)
M_Pl_GTE_MeV = m_tau_MeV * M_Pl_ratio
M_Pl_GTE_GeV = M_Pl_GTE_MeV / 1e3
M_Pl_GTE_kg  = M_Pl_GTE_MeV * 1.602176634e-13 / c_m_per_s**2  # J/c² → kg

# PDG Planck mass (ℏ=c=1 convention: M_Pl = sqrt(ℏc/G) ≈ 1.2209×10^19 GeV)
# = 1.2209×10^22 MeV
M_Pl_PDG_GeV = 1.22089e19   # GeV  (PDG 2022)
M_Pl_PDG_MeV = M_Pl_PDG_GeV * 1e3

# Discrepancy
discrepancy_frac = (M_Pl_GTE_MeV - M_Pl_PDG_MeV) / M_Pl_PDG_MeV
discrepancy_pct  = abs(discrepancy_frac) * 100

# GTE Planck length  ℓ_Pl = ℏc / M_Pl  (in fm)
l_Pl_GTE_fm = hbar_c_MeV_fm / M_Pl_GTE_MeV
l_Pl_GTE_m  = l_Pl_GTE_fm / fm_per_m

# GTE Planck time  t_Pl = ℓ_Pl / c
t_Pl_GTE_s = l_Pl_GTE_m / c_m_per_s

# Newton G from GTE (SI)
# G = (ℏc) / M_Pl²  in units of MeV·fm · fm² / MeV²  → fm³/MeV
# Convert to SI: 1 fm = 1e-15 m; 1 MeV = 1.602176634e-13 J
G_GTE_natural = hbar_c_MeV_fm / M_Pl_GTE_MeV**2   # fm/MeV
G_GTE_SI = (hbar_c_MeV_fm * 1e-15 *         # ℏc in J·m
             (1.602176634e-13)               # MeV→J numerator factor?
            ) / (M_Pl_GTE_MeV * 1.602176634e-13)**2 * c_m_per_s
# Careful SI calculation: G = ℏ c / M_Pl²
# ℏ = 1.054571817e-34 J·s, c = 2.998e8 m/s, M_Pl in kg
G_GTE_SI_v2 = hbar_J_s * c_m_per_s / M_Pl_GTE_kg**2    # m³/(kg·s²)
G_PDG_SI    = 6.67430e-11  # m³/(kg·s²)

G_discrepancy_pct = abs(G_GTE_SI_v2 - G_PDG_SI) / G_PDG_SI * 100

# Gravitational fine-structure constant α_G = (m_τ/M_Pl)² = 1/M_Pl_ratio²
alpha_G = (m_tau_MeV / M_Pl_GTE_MeV)**2

print("=" * 60)
print("SECTION 1: GTE Planck Scale Summary")
print("=" * 60)
print(f"M_Pl ratio (21^10 × 7^7 / 2):  {M_Pl_ratio:.6e}")
print(f"GTE Planck mass:                {M_Pl_GTE_MeV:.6e} MeV")
print(f"                                {M_Pl_GTE_GeV:.6e} GeV")
print(f"PDG Planck mass:                {M_Pl_PDG_MeV:.6e} MeV")
print(f"Discrepancy (GTE vs PDG):       {discrepancy_pct:.4f}%")
print(f"  (signed: GTE {'above' if discrepancy_frac > 0 else 'below'} PDG)")
print(f"GTE Planck length:              {l_Pl_GTE_fm:.4e} fm  =  {l_Pl_GTE_m:.4e} m")
print(f"GTE Planck time:                {t_Pl_GTE_s:.4e} s")
print(f"G_N (GTE, SI):                  {G_GTE_SI_v2:.4e} m³/(kg·s²)")
print(f"G_N (PDG):                      {G_PDG_SI:.4e} m³/(kg·s²)")
print(f"G discrepancy:                  {G_discrepancy_pct:.4f}%")
print(f"α_G = (m_τ/M_Pl)²:             {alpha_G:.4e}")

# ─────────────────────────────────────────────────────────
# 2. EFT breakdown: α_grav(E) = (E/M_Pl)²
# ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 2: EFT Breakdown — α_grav(E) = (E/M_Pl_GTE)²")
print("=" * 60)

M_kink_MeV  = 290.10    # MeV (CatA from P42)
Lambda_QCD   = 200.0     # MeV (rough)
M_Z_MeV      = 91187.6   # MeV
LHC_10TeV    = 10e6      # MeV (10 TeV)
LHC_14TeV    = 14e6      # MeV (14 TeV)
Higgs_MeV    = 125090.0  # MeV

energy_scales = [
    ("M_kink = 290.10 MeV  (GTE kink)",   M_kink_MeV),
    ("Λ_QCD  ≈ 200 MeV",                  Lambda_QCD),
    ("M_Z    = 91.2 GeV",                  M_Z_MeV),
    ("M_H    = 125.1 GeV  (Higgs)",        Higgs_MeV),
    ("LHC    = 10 TeV",                    LHC_10TeV),
    ("LHC    = 14 TeV",                    LHC_14TeV),
    ("M_Pl (GTE) — EFT breakdown",         M_Pl_GTE_MeV),
]

alpha_grav_table = {}
print(f"{'Scale':<42}  {'E (MeV)':>14}  {'α_grav':>14}  {'EFT valid?'}")
print("-" * 90)
for label, E in energy_scales:
    ag = (E / M_Pl_GTE_MeV)**2
    valid = "YES" if ag < 1e-10 else ("MARGINAL" if ag < 0.1 else "BREAKDOWN")
    print(f"  {label:<40}  {E:>14.4e}  {ag:>14.4e}  {valid}")
    alpha_grav_table[label.strip()] = {"E_MeV": E, "alpha_grav": ag, "EFT_valid": valid}

print(f"\n  EFT breakdown (α_grav = 1) at E = M_Pl_GTE = {M_Pl_GTE_MeV:.4e} MeV")
print(f"  i.e. continuum GR + QFT description fails above {M_Pl_GTE_GeV:.4e} GeV")

# ─────────────────────────────────────────────────────────
# 3. Graviton exchange vs QCD — crossover scale
# ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 3: Graviton Exchange vs QCD — Crossover Scale")
print("=" * 60)

alpha_s = 0.118   # strong coupling at M_Z (PDG)

# Born amplitude ratio: A_grav/A_QCD = (G_N M_kink²) / (α_s)
# At q = M_kink:
A_grav_M_kink = (M_kink_MeV / M_Pl_GTE_MeV)**2   # = α_G at kink
A_QCD_M_kink  = alpha_s
ratio_at_kink = A_grav_M_kink / A_QCD_M_kink

# Crossover: G_N E² = α_s  → E = M_Pl_GTE × sqrt(α_s)
q_crossover_MeV = M_Pl_GTE_MeV * math.sqrt(alpha_s)
q_crossover_GeV = q_crossover_MeV / 1e3

print(f"α_s (at M_Z):                   {alpha_s}")
print(f"α_grav at M_kink:               {A_grav_M_kink:.4e}")
print(f"A_grav/A_QCD at M_kink:         {ratio_at_kink:.4e}")
print(f"  → gravity suppressed by       {1/ratio_at_kink:.2e} relative to QCD at kink")
print(f"Crossover q (grav ≈ QCD):       {q_crossover_MeV:.4e} MeV  =  {q_crossover_GeV:.4e} GeV")
print(f"  (= {q_crossover_GeV/1e9:.2e} × 10^9 GeV = {q_crossover_GeV/M_Pl_PDG_GeV:.4f} M_Pl_PDG)")
print(f"  → graviton ≈ QCD only at Planck scale (α_s^(1/2) × M_Pl ≈ 0.34 × M_Pl)")

# ─────────────────────────────────────────────────────────
# 4. GTE prediction for Planck-scale physics
# ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 4: GTE Planck-Scale Physics Predictions")
print("=" * 60)

# CMCA lattice interpretation
# M_Pl^GTE in lattice units = π/√3 (from 28-QGR CatAD result)
M_Pl_lattice = math.pi / math.sqrt(3)
eps0_at_MPl  = math.pi**2 / (3 * (math.pi / math.sqrt(3))**2)   # = 1 by construction

# Physical lattice spacing a = ℏc / M_Pl  (same as Planck length)
a_lattice_fm = hbar_c_MeV_fm / M_Pl_GTE_MeV
a_lattice_m  = a_lattice_fm / fm_per_m

# Graviton wavelength at M_Pl: λ = ℏc/M_Pl = ℓ_Pl
lambda_graviton_fm = hbar_c_MeV_fm / M_Pl_GTE_MeV

print(f"M_Pl in lattice units (π/√3):   {M_Pl_lattice:.6f}")
print(f"ε₀ at M_Pl:                     {eps0_at_MPl:.6f}  (= 1 by construction)")
print(f"CMCA lattice spacing a:         {a_lattice_fm:.4e} fm  =  {a_lattice_m:.4e} m")
print(f"Graviton wavelength at M_Pl:    {lambda_graviton_fm:.4e} fm")
print(f"λ_graviton = a_lattice:         {abs(lambda_graviton_fm - a_lattice_fm) < 1e-30}")
print(f"  → At M_Pl, graviton wavelength = lattice spacing")
print(f"     ∴ Planck-scale gravitons resolve the GTE discrete spacetime structure")
print(f"  → Sub-Planck physics: lattice QGR replaces continuum EFT")
print(f"  → Above M_Pl^GTE the continuum description breaks down completely")

# ─────────────────────────────────────────────────────────
# 5. Minimum black hole mass
# ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 5: Minimum Black Hole Mass (GTE)")
print("=" * 60)

# M_BH_min: Compton wavelength = Schwarzschild radius
# ℏ/(M c) = 2G_N M / c²  →  M² = ℏc / (2G_N) = M_Pl²/2
# M_BH_min = M_Pl / sqrt(2)
M_BH_min_MeV = M_Pl_GTE_MeV / math.sqrt(2)
M_BH_min_GeV = M_BH_min_MeV / 1e3
M_BH_min_kg  = M_BH_min_MeV * 1.602176634e-13 / c_m_per_s**2

# Compton wavelength at M_BH_min
lambda_C_fm  = hbar_c_MeV_fm / M_BH_min_MeV
# Schwarzschild radius r_s = 2G M / c²  (in fm using G = ℏc/M_Pl²)
# r_s = 2 ℏc M_BH / M_Pl²  (in fm)
r_s_fm = 2 * hbar_c_MeV_fm * M_BH_min_MeV / M_Pl_GTE_MeV**2

print(f"M_BH_min = M_Pl/√2:             {M_BH_min_MeV:.6e} MeV")
print(f"                                {M_BH_min_GeV:.6e} GeV")
print(f"                                {M_BH_min_kg:.4e} kg")
print(f"Compton wavelength at M_BH_min: {lambda_C_fm:.4e} fm")
print(f"Schwarzschild radius:           {r_s_fm:.4e} fm")
print(f"λ_C = r_s (self-consistent):   {abs(lambda_C_fm - r_s_fm)/lambda_C_fm:.4f} relative error")
print(f"  → Minimum black hole = Planck-mass black hole (M_BH_min ≈ M_Pl)")

# ─────────────────────────────────────────────────────────
# 6. Hawking temperature for 10 M_Pl black holes
# ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 6: Hawking Temperature for GTE-Scale Black Holes")
print("=" * 60)

# T_H = M_Pl² / (8π M_BH)  in natural units (ℏ=c=k_B=1)
# In MeV units: T_H = M_Pl_GTE² / (8π M_BH)
for n_MPl in [1, 2, 5, 10, 100]:
    M_BH_MeV = n_MPl * M_Pl_GTE_MeV
    T_H_MeV  = M_Pl_GTE_MeV**2 / (8 * math.pi * M_BH_MeV)
    T_H_GeV  = T_H_MeV / 1e3
    T_H_K    = T_H_MeV / k_B_MeV_per_K
    print(f"  M_BH = {n_MPl:3d} M_Pl: T_H = {T_H_MeV:.4e} MeV  = {T_H_GeV:.4e} GeV  = {T_H_K:.4e} K")

T_H_10MPl_MeV = M_Pl_GTE_MeV / (8 * math.pi * 10)
T_H_10MPl_GeV = T_H_10MPl_MeV / 1e3
T_H_10MPl_K   = T_H_10MPl_MeV / k_B_MeV_per_K

print(f"\n  ★ Primary result (M_BH = 10 M_Pl):")
print(f"    T_H = M_Pl/(80π) = {T_H_10MPl_MeV:.6e} MeV = {T_H_10MPl_GeV:.6e} GeV")
print(f"    T_H in Kelvin:    {T_H_10MPl_K:.4e} K")
print(f"\n  Note: T_H decreases as M_BH increases — Planck-scale BHs")
print(f"        are the hottest, evaporating instantaneously.")

# ─────────────────────────────────────────────────────────
# Cat Level Assessment
# ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 7: CatLevel Assessment for 076-PLANCK-EFT")
print("=" * 60)

cat_assessment = """
CatLevel: CatAD

Justification:
  - G_N = m_τ²/M_Pl² is CatAD (EPIC_076 M1, Z₃-invariant entropy theorem, CatAD)
  - M_Pl_GTE = m_τ × 21^10 × 7^7 / 2 is CatAD (all components CatAL/CatA/CatAD)
  - α_grav(E) = (E/M_Pl)² is a standard EFT formula, applied to GTE M_Pl (CatAD input)
  - M_BH_min = M_Pl/√2 follows from equating Compton λ = Schwarzschild r (CatA algebra)
  - T_H = M_Pl²/(8π M_BH) is the standard Hawking formula (Bekenstein-Hawking), applied 
    to GTE M_Pl — accuracy inherits from M_Pl accuracy (CatAD = 0.040%)
  - Graviton-QCD crossover = M_Pl × √α_s (CatAD, modulo α_s uncertainty ~1%)
  - Lattice interpretation (λ_grav = ℓ_Pl = a) is exact by construction (CatAD)

  Formula accuracy: all GTE predictions inherit the 0.040% M_Pl discrepancy.
  EFT breakdown scale: 0.040% error in M_Pl → 0.080% error in M_Pl² (negligible).
  
  Blocker for CatAL: full Lean 4 proof of Z₃-invariant entropy theorem 
  (OQ-G1-LEAN, OQ-G1-LEAN2) — not yet certified.
"""
print(cat_assessment)

# ─────────────────────────────────────────────────────────
# Save JSON results
# ─────────────────────────────────────────────────────────

results = {
    "rank": "076-PLANCK-EFT",
    "epic": "EPIC_076",
    "cat_level": "CatAD",
    "status": "COMPLETE",
    "date": "2026-05-26",
    "prerequisite": "G_N = m_τ²/M_Pl² CatAD (M1, Z₃-invariant entropy)",

    "section1_planck_scale": {
        "m_tau_MeV": m_tau_MeV,
        "M_Pl_ratio_exact": "21^10 × 7^7 / 2",
        "M_Pl_ratio_value": M_Pl_ratio,
        "M_Pl_GTE_MeV": M_Pl_GTE_MeV,
        "M_Pl_GTE_GeV": M_Pl_GTE_GeV,
        "M_Pl_PDG_MeV": M_Pl_PDG_MeV,
        "M_Pl_PDG_GeV": M_Pl_PDG_GeV,
        "discrepancy_pct": discrepancy_pct,
        "discrepancy_sign": "GTE above PDG" if discrepancy_frac > 0 else "GTE below PDG",
        "l_Pl_GTE_fm": l_Pl_GTE_fm,
        "l_Pl_GTE_m": l_Pl_GTE_m,
        "t_Pl_GTE_s": t_Pl_GTE_s,
        "G_GTE_SI_m3_per_kg_s2": G_GTE_SI_v2,
        "G_PDG_SI_m3_per_kg_s2": G_PDG_SI,
        "G_discrepancy_pct": G_discrepancy_pct,
        "alpha_G_at_kink": alpha_G,
    },

    "section2_eft_breakdown": {
        "alpha_grav_table": alpha_grav_table,
        "EFT_breakdown_E_MeV": M_Pl_GTE_MeV,
        "EFT_breakdown_E_GeV": M_Pl_GTE_GeV,
        "formula": "alpha_grav(E) = (E / M_Pl_GTE)^2",
        "note": "EFT valid for E << M_Pl; breakdown at E ~ M_Pl where alpha_grav ~ 1",
    },

    "section3_graviton_vs_QCD": {
        "alpha_s": alpha_s,
        "alpha_grav_at_M_kink": A_grav_M_kink,
        "A_grav_over_A_QCD_at_kink": ratio_at_kink,
        "suppression_factor": 1.0 / ratio_at_kink,
        "crossover_q_MeV": q_crossover_MeV,
        "crossover_q_GeV": q_crossover_GeV,
        "crossover_formula": "q_cross = M_Pl × sqrt(alpha_s)",
        "note": "Graviton exchange ≈ QCD only at 0.34 × M_Pl — deep Planck regime",
    },

    "section4_planck_physics": {
        "M_Pl_lattice_units": M_Pl_lattice,
        "eps0_at_MPl": eps0_at_MPl,
        "lattice_spacing_a_fm": a_lattice_fm,
        "lattice_spacing_a_m": a_lattice_m,
        "graviton_wavelength_at_MPl_fm": lambda_graviton_fm,
        "lambda_graviton_equals_lattice": True,
        "interpretation": "At M_Pl, graviton wavelength = GTE lattice spacing: gravitons resolve discrete spacetime",
    },

    "section5_min_BH": {
        "formula": "M_BH_min = M_Pl / sqrt(2)  (Compton λ = Schwarzschild r)",
        "M_BH_min_MeV": M_BH_min_MeV,
        "M_BH_min_GeV": M_BH_min_GeV,
        "M_BH_min_kg": M_BH_min_kg,
        "Compton_wavelength_fm": lambda_C_fm,
        "Schwarzschild_radius_fm": r_s_fm,
        "self_consistency_error": abs(lambda_C_fm - r_s_fm) / lambda_C_fm,
    },

    "section6_hawking_temperature": {
        "formula": "T_H = M_Pl^2 / (8 pi M_BH)  (Bekenstein-Hawking)",
        "T_H_for_10MPl_MeV": T_H_10MPl_MeV,
        "T_H_for_10MPl_GeV": T_H_10MPl_GeV,
        "T_H_for_10MPl_K": T_H_10MPl_K,
        "T_H_for_1MPl_MeV": M_Pl_GTE_MeV / (8 * math.pi),
        "T_H_for_2MPl_MeV": M_Pl_GTE_MeV / (8 * math.pi * 2),
        "T_H_for_5MPl_MeV": M_Pl_GTE_MeV / (8 * math.pi * 5),
        "T_H_for_100MPl_MeV": M_Pl_GTE_MeV / (8 * math.pi * 100),
    },

    "cat_level_justification": {
        "level": "CatAD",
        "G_input": "CatAD (M1 — Z₃-invariant entropy theorem)",
        "M_Pl_accuracy": "0.040% vs PDG",
        "EFT_formula": "Standard GR EFT applied to GTE M_Pl (CatAD inheritance)",
        "BH_threshold": "CatA (elementary algebra from M_Pl definition)",
        "Hawking_T": "CatAD (standard Bekenstein-Hawking applied to GTE M_Pl)",
        "blocker_for_CatAL": "Lean proofs OQ-G1-LEAN and OQ-G1-LEAN2 pending",
    },
}

output_path = "epic076_planck_eft_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_path}")
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"GTE Planck mass:         {M_Pl_GTE_MeV:.6e} MeV  ({discrepancy_pct:.4f}% from PDG)")
print(f"G discrepancy:           {G_discrepancy_pct:.4f}% from PDG G_N")
print(f"α_grav at M_kink:        {A_grav_M_kink:.4e}  (gravity ÷ QCD: {ratio_at_kink:.2e})")
print(f"α_grav at LHC 10 TeV:    {(LHC_10TeV/M_Pl_GTE_MeV)**2:.4e}")
print(f"Crossover q (grav=QCD):  {q_crossover_GeV:.4e} GeV  (= {q_crossover_GeV/M_Pl_PDG_GeV:.3f} M_Pl_PDG)")
print(f"M_BH_min:                {M_BH_min_MeV:.6e} MeV")
print(f"T_H (10 M_Pl BH):        {T_H_10MPl_MeV:.6e} MeV")
print(f"CatLevel 076-PLANCK-EFT: CatAD")
