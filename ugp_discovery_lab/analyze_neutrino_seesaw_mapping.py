#!/usr/bin/env python3
"""
Analyze how LOCKED canonical neutrino triples map to M_D and M_R

This diagnostic script calculates what the current mapping produces
and helps identify where the 10⁸-10²⁶× error comes from.

NO IMPORTS from ugp_discovery_lab - standalone analysis
"""

import numpy as np

print("=" * 80)
print("NEUTRINO SEESAW MAPPING ANALYSIS")
print("=" * 80)
print()

# UGP Kernel Constants (from code)
phi = (1 + np.sqrt(5)) / 2  # 1.618033988749895
k_L2 = 7 / 512  # 0.013671875
k_gen2 = -phi / 2  # -0.8090169943749475
k_gen = np.pi / 2  # 1.5707963267948966
k_M = k_gen2 + 0.25 * k_L2  # -0.8056640625

print("UGP Kernel Constants:")
print(f"  φ = {phi}")
print(f"  k_L2 = {k_L2}")
print(f"  k_gen = {k_gen}")
print()

# LOCKED Canonical Triples (from code lines 66-110)
nu_L_triples = [
    (1, 1, 823),     # ν_e
    (9, 1, 1023),    # ν_μ  
    (5, 1, 65535),   # ν_τ
]

nu_R_triples = [
    (2, 5, 5),       # ν_e_R
    (7, 11, 13),     # ν_μ_R
    (17, 19, 23),    # ν_τ_R
]

gens = [1, 2, 3]

print("LOCKED Canonical Neutrino Triples (N=10):")
print("νL triples:")
for i, triple in enumerate(nu_L_triples, 1):
    print(f"  ν_{i}: {triple}")
print()
print("νR triples:")
for i, triple in enumerate(nu_R_triples, 1):
    print(f"  ν_{i}_R: {triple}")
print()

# Seesaw Scales (from code lines 120-124)
M_R_scale = 1e14  # GeV
M_D_scale = 100   # GeV
hierarchy_factor = 1e-3

print("Seesaw Scale Parameters:")
print(f"  M_R_scale = {M_R_scale:.2e} GeV")
print(f"  M_D_scale = {M_D_scale:.2e} GeV")
print(f"  hierarchy_factor = {hierarchy_factor:.2e}")
print()

# Expected neutrino mass scale from seesaw
m_nu_expected = M_D_scale**2 / M_R_scale
print(f"Expected neutrino mass scale: m_ν ~ M_D²/M_R = {m_nu_expected:.2e} GeV = {m_nu_expected*1e9:.2e} eV")
print()

# Function from code (lines 574-597)
def extract_enhanced_irrep_features(a, b, c, g, sector):
    """Extract enhanced S3 irrep features from GTE triple."""
    
    # A1 (Symmetric)
    s_gen = (a + b + c) / 3
    
    # E (2D Irrep) with enhanced phase structure
    e1 = (2*a - b - c) / np.sqrt(6)
    e2 = (b - c) / np.sqrt(2)
    
    # Apply enhanced generational phase
    if sector == "nu_R":
        # Right-handed neutrinos have different phase structure
        phase_E = np.exp(1j * g * k_gen * 0.5)
    else:
        phase_E = np.exp(1j * g * k_gen)
        
    e1_rotated = e1 * phase_E
    e2_rotated = e2 * phase_E
    
    # A2 (Antisymmetric) with enhanced structure
    delta = (a - b) * (b - c) * (c - a)
    
    return s_gen, (e1_rotated, e2_rotated), delta

print("=" * 80)
print("νL FEATURES (Left-Handed Neutrinos)")
print("=" * 80)
print()

nu_L_features = []
for i, (triple, g) in enumerate(zip(nu_L_triples, gens)):
    a, b, c = triple
    s, (e1, e2), delta = extract_enhanced_irrep_features(a, b, c, g, "nu")
    nu_L_features.append((s, (e1, e2), delta))
    
    print(f"ν_{i+1}: (a,b,c) = {triple}")
    print(f"  s_gen = {s:.4f}")
    print(f"  e1 = {e1:.4f}")
    print(f"  e2 = {e2:.4f}")
    print(f"  delta = {delta:.2e}")
    print()

print("=" * 80)
print("νR FEATURES (Right-Handed Neutrinos)")
print("=" * 80)
print()

nu_R_features = []
for i, (triple, g) in enumerate(zip(nu_R_triples, gens)):
    a, b, c = triple
    s, (e1, e2), delta = extract_enhanced_irrep_features(a, b, c, g, "nu_R")
    nu_R_features.append((s, (e1, e2), delta))
    
    print(f"ν_{i+1}_R: (a,b,c) = {triple}")
    print(f"  s_gen = {s:.4f}")
    print(f"  e1 = {e1:.4f}")
    print(f"  e2 = {e2:.4f}")
    print(f"  delta = {delta:.2e}")
    print()

# Construct M_D (from code lines 344-360)
print("=" * 80)
print("M_D CONSTRUCTION (Dirac Mass Matrix)")
print("=" * 80)
print()

M_D = np.zeros((3, 3), dtype=complex)
for i, feat_L in enumerate(nu_L_features):
    for j, feat_R in enumerate(nu_R_features):
        s_L, (e1_L, e2_L), delta_L = feat_L
        s_R, (e1_R, e2_R), delta_R = feat_R
        
        # Enhanced geometric overlap
        overlap = (s_L * s_R + 
                  e1_L * np.conj(e1_R) + e2_L * np.conj(e2_R) + 
                  delta_L * delta_R * k_L2)
        
        # Apply Dirac mass scale
        M_D[i, j] = overlap * M_D_scale

print("M_D (before scaling):")
print("Overlap matrix elements:")
for i in range(3):
    for j in range(3):
        s_L, (e1_L, e2_L), delta_L = nu_L_features[i]
        s_R, (e1_R, e2_R), delta_R = nu_R_features[j]
        overlap = (s_L * s_R + e1_L * np.conj(e1_R) + e2_L * np.conj(e2_R) + delta_L * delta_R * k_L2)
        print(f"  overlap[{i},{j}] = {overlap:.6f}")
print()

print(f"M_D (with M_D_scale = {M_D_scale} GeV):")
print(M_D)
print()
print(f"M_D magnitude range: {np.min(np.abs(M_D)):.2e} to {np.max(np.abs(M_D)):.2e} GeV")
print()

# Construct M_R (from code lines 362-382)
print("=" * 80)
print("M_R CONSTRUCTION (Right-Handed Majorana Mass Matrix)")
print("=" * 80)
print()

M_R = np.zeros((3, 3), dtype=complex)
for i, feat_i in enumerate(nu_R_features):
    for j, feat_j in enumerate(nu_R_features):
        s_i, (e1_i, e2_i), delta_i = feat_i
        s_j, (e1_j, e2_j), delta_j = feat_j
        
        # Enhanced symmetric Gram matrix
        gram = (s_i * s_j + 
               e1_i * np.conj(e1_j) + e2_i * np.conj(e2_j) + 
               delta_i * delta_j * k_L2)
        
        # Apply Majorana mass scale with hierarchy
        hierarchy_factor_ij = (1.0 if i == j else hierarchy_factor)
        M_R[i, j] = gram * M_R_scale * hierarchy_factor_ij

# Ensure M_R is symmetric
M_R = 0.5 * (M_R + M_R.T)
M_R += np.eye(3) * np.trace(M_R) * 0.1

print(f"M_R (with M_R_scale = {M_R_scale:.2e} GeV):")
print(M_R)
print()
print(f"M_R magnitude range: {np.min(np.abs(M_R)):.2e} to {np.max(np.abs(M_R)):.2e} GeV")
print()

# Calculate M_eff (from code lines 396-431)
print("=" * 80)
print("M_eff CALCULATION (Effective Light Neutrino Mass Matrix)")
print("=" * 80)
print()

# Invert M_R
try:
    cond_num = np.linalg.cond(M_R)
    print(f"M_R condition number: {cond_num:.2e}")
    
    if cond_num > 1e12:
        reg_factor = np.trace(M_R) * 1e-6 * np.sqrt(cond_num / 1e12)
        M_R_reg = M_R + np.eye(3) * reg_factor
        print(f"  (Applied regularization: {reg_factor:.2e})")
    else:
        M_R_reg = M_R
    
    M_R_inv = np.linalg.inv(M_R_reg)
    print(f"M_R_inv magnitude range: {np.min(np.abs(M_R_inv)):.2e} to {np.max(np.abs(M_R_inv)):.2e} GeV⁻¹")
    print()
    
except np.linalg.LinAlgError:
    print("❌ M_R is singular!")
    reg_factor = np.trace(M_R) * 1e-4
    M_R_reg = M_R + np.eye(3) * reg_factor
    M_R_inv = np.linalg.inv(M_R_reg)

# Type-I Seesaw formula
M_eff = -M_D @ M_R_inv @ M_D.T

# Ensure symmetric
M_eff = 0.5 * (M_eff + M_eff.T)

print("M_eff:")
print(M_eff)
print()
print(f"M_eff magnitude range: {np.min(np.abs(M_eff)):.2e} to {np.max(np.abs(M_eff)):.2e} GeV²")
print()

# Extract eigenvalues (neutrino masses²)
eigenvals = np.linalg.eigvals(M_eff)
masses_sq_GeV = np.abs(eigenvals)
masses_GeV = np.sqrt(masses_sq_GeV)

# Sort
sorted_indices = np.argsort(masses_GeV)
masses_GeV_sorted = masses_GeV[sorted_indices]

print("=" * 80)
print("NEUTRINO MASSES FROM EIGENVALUES")
print("=" * 80)
print()

print("Eigenvalues (GeV²):")
for i, ev in enumerate(eigenvals):
    print(f"  λ_{i+1} = {ev:.6e}")
print()

print("Masses² (GeV²):")
for i, m_sq in enumerate(masses_sq_GeV):
    print(f"  m_{i+1}² = {m_sq:.6e}")
print()

print("Masses (GeV):")
for i, m in enumerate(masses_GeV):
    print(f"  m_{i+1} = {m:.6e}")
print()

# Convert to eV
GeV_to_eV = 1e9
masses_eV = masses_GeV * GeV_to_eV
masses_sq_eV = masses_sq_GeV * GeV_to_eV**2

print("Masses (eV):")
for i, m in enumerate(masses_eV):
    print(f"  m_{i+1} = {m:.6e} eV")
print()

# Mass differences
masses_sq_sorted_eV = np.sort(masses_sq_eV)
delta_m21_sq = masses_sq_sorted_eV[1] - masses_sq_sorted_eV[0]
delta_m31_sq = masses_sq_sorted_eV[2] - masses_sq_sorted_eV[0]

print("=" * 80)
print("MASS DIFFERENCES")
print("=" * 80)
print()

print(f"Δm²₂₁ = {delta_m21_sq:.6e} eV²")
print(f"Δm²₃₁ = {delta_m31_sq:.6e} eV²")
print()

# Compare to PDG
exp_delta_m21_sq = 7.5e-5  # eV²
exp_delta_m31_sq = 2.5e-3  # eV²

print("PDG Experimental Values:")
print(f"  Δm²₂₁ (PDG) = {exp_delta_m21_sq:.6e} eV²")
print(f"  |Δm²₃₁| (PDG) = {exp_delta_m31_sq:.6e} eV²")
print()

error_21 = abs(delta_m21_sq - exp_delta_m21_sq) / exp_delta_m21_sq
error_31 = abs(abs(delta_m31_sq) - exp_delta_m31_sq) / exp_delta_m31_sq

print(f"Errors:")
print(f"  Δm²₂₁ error = {error_21*100:.2f}%")
print(f"  |Δm²₃₁| error = {error_31*100:.2f}%")
print()

if error_21 < 0.10 and error_31 < 0.10:
    print("✅ SUCCESS: Both within 10% PDG requirement!")
elif error_21 < 0.30 and error_31 < 0.30:
    print("⚠️  GOOD: Within 30%, but need < 10% for PDG standard")
else:
    print(f"❌ FAIL: Errors too large (need < 10%, have {max(error_21, error_31)*100:.1f}%)")

# Identify scale factors needed
print()
print("=" * 80)
print("SCALE FACTOR DIAGNOSIS")
print("=" * 80)
print()

print("To match PDG Δm²₂₁:")
scale_factor_21 = exp_delta_m21_sq / delta_m21_sq
print(f"  Need to scale by factor: {scale_factor_21:.2e}")
print()

print("To match PDG |Δm²₃₁|:")
scale_factor_31 = exp_delta_m31_sq / abs(delta_m31_sq)
print(f"  Need to scale by factor: {scale_factor_31:.2e}")
print()

# If both scale factors are similar, we can adjust seesaw parameters
if abs(np.log10(scale_factor_21) - np.log10(scale_factor_31)) < 1:
    avg_scale_factor = np.sqrt(scale_factor_21 * scale_factor_31)
    print(f"Scale factors are similar (within factor 10)")
    print(f"Average scale factor needed: {avg_scale_factor:.2e}")
    print()
    
    # Calculate new M_R_scale
    # Since m_ν ~ M_D²/M_R, and m² ~ (M_D²/M_R)²
    # To scale m² by factor f, we need M_R → M_R/f
    new_M_R_scale = M_R_scale / avg_scale_factor
    
    print(f"PROPOSED FIX:")
    print(f"  Change M_R_scale from {M_R_scale:.2e} to {new_M_R_scale:.2e} GeV")
    print(f"  (factor {avg_scale_factor:.2e} decrease)")
    print()
else:
    print(f"❌ Scale factors differ significantly:")
    print(f"   Δm²₂₁ needs factor {scale_factor_21:.2e}")
    print(f"   Δm²₃₁ needs factor {scale_factor_31:.2e}")
    print(f"   Ratio: {scale_factor_21/scale_factor_31:.2e}")
    print()
    print("This suggests:")
    print("- Can't fix both with just M_R_scale adjustment")
    print("- Need to also adjust hierarchy_factor or M_D structure")
    print()

# Sum of masses check
sum_masses_eV = np.sum(masses_eV)
print("=" * 80)
print("COSMOLOGY CHECK")
print("=" * 80)
print()

print(f"Σm_i = {sum_masses_eV:.6e} eV")
print(f"Cosmology limit: < 0.12 eV")
if sum_masses_eV < 0.12:
    print("✅ Within cosmological bounds")
else:
    print(f"❌ Exceeds limit by factor {sum_masses_eV/0.12:.2e}")
print()

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print()

print("KEY FINDINGS:")
print(f"1. Current masses are {error_21:.1e}× to {error_31:.1e}× too large")
print(f"2. Need to reduce mass scale by factor ~{avg_scale_factor:.2e} if factors align")
print("3. Can be done by adjusting M_R_scale (simple) or M_D/hierarchy (complex)")
print()

print("NEXT STEPS:")
print("1. Test adjusted M_R_scale in experimental version")
print("2. Verify PMNS mixing is preserved")
print("3. Fine-tune if needed")
print("4. Validate against 10% PDG requirement")

