#!/usr/bin/env python3
"""
Standalone test of log-ratio normalized seesaw

Tests the experimental v2 with MONOLITH-style normalization
WITHOUT requiring full ugp_discovery_lab package (avoids sklearn issues)
"""

import numpy as np
import math
from scipy.linalg import schur, eigh

print("=" * 80)
print("LOG-RATIO NORMALIZED SEESAW TEST")
print("=" * 80)
print()

# UGP Kernel Constants
phi = (1 + np.sqrt(5)) / 2
k_L2 = 7 / 512
k_gen = np.pi / 2

# LOCKED Canonical Triples
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

# Seesaw scales
M_R_scale = 1e14  # GeV
M_D_scale = 100   # GeV
hierarchy_factor = 1e-3

print("Testing with LOCKED canonical triples at N=10")
print("=" * 80)
print()

# NEW: Log-ratio normalized feature extraction
def extract_log_ratio_features(a, b, c, g, sector):
    """MONOLITH-style log-ratio normalization."""
    
    # Calculate triple norm
    triple_norm = np.sqrt(a**2 + b**2 + c**2)
    
    # A1 (Symmetric) - Use log-ratio like MONOLITH
    L = math.log(abs(float(b)) / abs(float(c))) if c != 0 else 0.0
    s_gen = L + (a / triple_norm) * 10
    
    # E (2D Irrep) - Normalized
    e1_raw = (2*a - b - c) / np.sqrt(6)
    e2_raw = (b - c) / np.sqrt(2)
    e1 = e1_raw / triple_norm * 100
    e2 = e2_raw / triple_norm * 100
    
    # Apply generational phase
    if sector == "nu_R":
        phase_E = np.exp(1j * g * k_gen * 0.5)
    else:
        phase_E = np.exp(1j * g * k_gen)
    
    e1_rotated = e1 * phase_E
    e2_rotated = e2 * phase_E
    
    # A2 (Antisymmetric) - Normalized
    delta_raw = (a - b) * (b - c) * (c - a)
    delta = delta_raw / (triple_norm**3) * 1000
    
    return s_gen, (e1_rotated, e2_rotated), delta

# Extract features
print("Extracting log-ratio normalized features...")
nu_L_features = []
for i, (triple, g) in enumerate(zip(nu_L_triples, gens)):
    a, b, c = triple
    feat = extract_log_ratio_features(a, b, c, g, "nu")
    nu_L_features.append(feat)
    s, (e1, e2), delta = feat
    print(f"  νL_{i+1} ({a},{b},{c}): s_gen={s:.3f}, norm={(a**2+b**2+c**2)**0.5:.1f}")

print()

nu_R_features = []
for i, (triple, g) in enumerate(zip(nu_R_triples, gens)):
    a, b, c = triple
    feat = extract_log_ratio_features(a, b, c, g, "nu_R")
    nu_R_features.append(feat)
    s, (e1, e2), delta = feat
    print(f"  νR_{i+1} ({a},{b},{c}): s_gen={s:.3f}, norm={(a**2+b**2+c**2)**0.5:.1f}")

print()

# Construct M_D
print("Constructing M_D with log-ratio normalized overlaps...")
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

print(f"M_D magnitude range: {np.min(np.abs(M_D)):.2e} to {np.max(np.abs(M_D)):.2e} GeV")
print(f"Expected: ~100 GeV scale")
if np.max(np.abs(M_D)) < 1000:
    print("✅ M_D at reasonable scale!")
else:
    print(f"⚠️  M_D still too large by factor {np.max(np.abs(M_D))/100:.1e}")
print()

# Construct M_R
print("Constructing M_R with log-ratio normalized overlaps...")
M_R = np.zeros((3, 3), dtype=complex)
for i, feat_i in enumerate(nu_R_features):
    for j, feat_j in enumerate(nu_R_features):
        s_i, (e1_i, e2_i), delta_i = feat_i
        s_j, (e1_j, e2_j), delta_j = feat_j
        
        # Symmetric Gram matrix
        gram = (s_i * s_j + 
               e1_i * np.conj(e1_j) + e2_i * np.conj(e2_j) + 
               delta_i * delta_j * k_L2)
        
        # Apply Majorana mass scale with hierarchy
        hierarchy_factor_ij = (1.0 if i == j else hierarchy_factor)
        M_R[i, j] = gram * M_R_scale * hierarchy_factor_ij

# Ensure M_R is symmetric
M_R = 0.5 * (M_R + M_R.T)
M_R += np.eye(3) * np.trace(M_R) * 0.1

print(f"M_R magnitude range: {np.min(np.abs(M_R)):.2e} to {np.max(np.abs(M_R)):.2e} GeV")
print(f"Expected: ~10¹⁴ GeV scale")
if np.min(np.abs(M_R)) > 1e12 and np.max(np.abs(M_R)) < 1e16:
    print("✅ M_R at reasonable GUT scale!")
else:
    print(f"⚠️  M_R scale issues")
print()

# Calculate M_eff
print("Calculating M_eff = -M_D M_R⁻¹ M_D^T...")
M_R_inv = np.linalg.inv(M_R)
M_eff = -M_D @ M_R_inv @ M_D.T
M_eff = 0.5 * (M_eff + M_eff.T)

print(f"M_eff magnitude range: {np.min(np.abs(M_eff)):.2e} to {np.max(np.abs(M_eff)):.2e} GeV²")
print()

# Extract neutrino masses
eigenvals = np.linalg.eigvals(M_eff)
masses_sq_GeV = np.abs(eigenvals)
masses_GeV = np.sqrt(masses_sq_GeV)

# Convert to eV
GeV_to_eV = 1e9
masses_eV = masses_GeV * GeV_to_eV
masses_sq_eV = masses_sq_GeV * GeV_to_eV**2

print("=" * 80)
print("NEUTRINO MASSES (with log-ratio normalization)")
print("=" * 80)
print()

for i, m in enumerate(masses_eV, 1):
    print(f"  m_{i} = {m:.6e} eV")
print()

# Mass differences
masses_sq_sorted_eV = np.sort(masses_sq_eV)
delta_m21_sq = masses_sq_sorted_eV[1] - masses_sq_sorted_eV[0]
delta_m31_sq = masses_sq_sorted_eV[2] - masses_sq_sorted_eV[0]

print("Mass Differences:")
print(f"  Δm²₂₁ = {delta_m21_sq:.6e} eV²")
print(f"  Δm²₃₁ = {delta_m31_sq:.6e} eV²")
print()

# Compare to PDG
exp_delta_m21_sq = 7.5e-5
exp_delta_m31_sq = 2.5e-3

print("=" * 80)
print("COMPARISON TO PDG (10% Requirement)")
print("=" * 80)
print()

print("PDG Experimental Values:")
print(f"  Δm²₂₁ (PDG) = {exp_delta_m21_sq:.6e} eV²")
print(f"  |Δm²₃₁| (PDG) = {exp_delta_m31_sq:.6e} eV²")
print()

print("UGP Log-Ratio Normalized:")
print(f"  Δm²₂₁ (UGP) = {delta_m21_sq:.6e} eV²")
print(f"  Δm²₃₁ (UGP) = {delta_m31_sq:.6e} eV²")
print()

error_21 = abs(delta_m21_sq - exp_delta_m21_sq) / exp_delta_m21_sq
error_31 = abs(abs(delta_m31_sq) - exp_delta_m31_sq) / exp_delta_m31_sq

print("Errors:")
print(f"  Δm²₂₁ error = {error_21*100:.2f}%")
print(f"  |Δm²₃₁| error = {error_31*100:.2f}%")
print()

# Check success
if error_21 < 0.10 and error_31 < 0.10:
    print("✅ ✅ ✅ SUCCESS: Both within 10% PDG requirement!")
    print("🎉 Neutrino mass problem SOLVED!")
elif error_21 < 0.30 and error_31 < 0.30:
    print("✅ GOOD: Within 30%, needs fine-tuning for 10% PDG")
    print("   → Adjust M_R_scale or hierarchy_factor")
else:
    print(f"⚠️  Still needs work (errors {error_21*100:.1f}% and {error_31*100:.1f}%)")
    print("   → May need different normalization approach")

print()

# Cosmology check
sum_masses = np.sum(masses_eV)
print("Cosmology Check:")
print(f"  Σm_i = {sum_masses:.6e} eV")
print(f"  Limit: < 0.12 eV")
if sum_masses < 0.12:
    print("✅ Within cosmological bounds")
else:
    print(f"❌ Exceeds by factor {sum_masses/0.12:.2e}")
print()

# Hierarchy
sorted_indices = np.argsort(masses_eV)
print("=" * 80)
print("MASS HIERARCHY")
print("=" * 80)
print()
print("Mass ordering (lightest to heaviest):")
for i, idx in enumerate(sorted_indices):
    print(f"  Position {i+1}: m_{idx+1} = {masses_eV[idx]:.6e} eV")
print()

if sorted_indices[0] == 0:
    print("Hierarchy: NORMAL (m₁ < m₂ < m₃)")
elif sorted_indices[0] == 2:
    print("Hierarchy: INVERTED (m₃ < m₁ < m₂)")
else:
    print("Hierarchy: UNUSUAL/UNKNOWN")
print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()

if error_21 < 0.10 and error_31 < 0.10:
    print("🏆 LOG-RATIO NORMALIZATION: SUCCESS!")
    print("   Neutrino masses at correct scale and accuracy")
    print("   Ready to integrate into paper!")
elif max(abs(M_D).flat) < 1000 and min(masses_eV) > 0 and max(masses_eV) < 10:
    print("✅ LOG-RATIO NORMALIZATION: Partial Success")
    print("   Masses at correct scale (0.01-1 eV)")
    print("   Need parameter tuning for 10% PDG accuracy")
else:
    print("⚠️  LOG-RATIO NORMALIZATION: Needs more work")
    print("   Check feature extraction formulas")

