#!/usr/bin/env python3
"""
Test PURE log-ratio normalization (no additional scale factors)

Try using log-ratio features directly without arbitrary scale factors
"""

import numpy as np
import math
from scipy.linalg import schur, eigh

print("=" * 80)
print("PURE LOG-RATIO SEESAW TEST (No arbitrary scale factors)")
print("=" * 80)
print()

# Constants
phi = (1 + np.sqrt(5)) / 2
k_L2 = 7 / 512
k_gen = np.pi / 2

# LOCKED triples
nu_L_triples = [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)]
nu_R_triples = [(2, 5, 5), (7, 11, 13), (17, 19, 23)]
gens = [1, 2, 3]

# Seesaw scales - TRY DIFFERENT VALUES
M_R_scale = 1e14  # GeV
M_D_scale = 1.0   # GeV ← Try much smaller!
hierarchy_factor = 1e-3

print(f"Testing with M_D_scale = {M_D_scale} GeV (much smaller than 100 GeV)")
print()

def extract_pure_log_ratio_features(a, b, c, g, sector):
    """Pure log-ratio - minimal arbitrary factors."""
    
    # Log-ratio (MONOLITH style)
    L = math.log(abs(float(b)) / abs(float(c))) if c != 0 else 0.0
    
    # Use L directly for s_gen (no additional factors)
    s_gen = L
    
    # For e1, e2: normalize to O(1)
    triple_norm = np.sqrt(a**2 + b**2 + c**2)
    e1_raw = (2*a - b - c) / np.sqrt(6)
    e2_raw = (b - c) / np.sqrt(2)
    
    # Normalize WITHOUT arbitrary scale factors
    e1 = e1_raw / triple_norm
    e2 = e2_raw / triple_norm
    
    # Apply generational phase
    if sector == "nu_R":
        phase_E = np.exp(1j * g * k_gen * 0.5)
    else:
        phase_E = np.exp(1j * g * k_gen)
    
    e1_rotated = e1 * phase_E
    e2_rotated = e2 * phase_E
    
    # Delta: normalize aggressively
    delta_raw = (a - b) * (b - c) * (c - a)
    delta = delta_raw / (triple_norm**3)  # No additional scale factor
    
    return s_gen, (e1_rotated, e2_rotated), delta

# Extract features
nu_L_features = [extract_pure_log_ratio_features(*triple, g, "nu") 
                 for triple, g in zip(nu_L_triples, gens)]
nu_R_features = [extract_pure_log_ratio_features(*triple, g, "nu_R") 
                 for triple, g in zip(nu_R_triples, gens)]

# Construct M_D
M_D = np.zeros((3, 3), dtype=complex)
for i, feat_L in enumerate(nu_L_features):
    for j, feat_R in enumerate(nu_R_features):
        s_L, (e1_L, e2_L), delta_L = feat_L
        s_R, (e1_R, e2_R), delta_R = feat_R
        
        overlap = (s_L * s_R + 
                  e1_L * np.conj(e1_R) + e2_L * np.conj(e2_R) + 
                  delta_L * delta_R * k_L2)
        
        M_D[i, j] = overlap * M_D_scale

print(f"M_D magnitude range: {np.min(np.abs(M_D)):.2e} to {np.max(np.abs(M_D)):.2e} GeV")
print()

# Construct M_R
M_R = np.zeros((3, 3), dtype=complex)
for i, feat_i in enumerate(nu_R_features):
    for j, feat_j in enumerate(nu_R_features):
        s_i, (e1_i, e2_i), delta_i = feat_i
        s_j, (e1_j, e2_j), delta_j = feat_j
        
        gram = (s_i * s_j + 
               e1_i * np.conj(e1_j) + e2_i * np.conj(e2_j) + 
               delta_i * delta_j * k_L2)
        
        hierarchy_factor_ij = (1.0 if i == j else hierarchy_factor)
        M_R[i, j] = gram * M_R_scale * hierarchy_factor_ij

M_R = 0.5 * (M_R + M_R.T)
M_R += np.eye(3) * np.trace(M_R) * 0.1

print(f"M_R magnitude range: {np.min(np.abs(M_R)):.2e} to {np.max(np.abs(M_R)):.2e} GeV")
print()

# Calculate M_eff
M_R_inv = np.linalg.inv(M_R)
M_eff = -M_D @ M_R_inv @ M_D.T
M_eff = 0.5 * (M_eff + M_eff.T)

# Extract masses
eigenvals = np.linalg.eigvals(M_eff)
masses_sq_GeV = np.abs(eigenvals)
masses_GeV = np.sqrt(masses_sq_GeV)
masses_eV = masses_GeV * 1e9
masses_sq_eV = masses_sq_GeV * (1e9)**2

print("NEUTRINO MASSES:")
for i, m in enumerate(masses_eV, 1):
    print(f"  m_{i} = {m:.6e} eV")
print()

# Mass differences
masses_sq_sorted = np.sort(masses_sq_eV)
delta_m21_sq = masses_sq_sorted[1] - masses_sq_sorted[0]
delta_m31_sq = masses_sq_sorted[2] - masses_sq_sorted[0]

print("MASS DIFFERENCES:")
print(f"  Δm²₂₁ = {delta_m21_sq:.6e} eV²")
print(f"  Δm²₃₁ = {delta_m31_sq:.6e} eV²")
print()

# Errors
exp_delta_m21_sq = 7.5e-5
exp_delta_m31_sq = 2.5e-3
error_21 = abs(delta_m21_sq - exp_delta_m21_sq) / exp_delta_m21_sq
error_31 = abs(abs(delta_m31_sq) - exp_delta_m31_sq) / exp_delta_m31_sq

print(f"ERRORS:")
print(f"  Δm²₂₁ error = {error_21*100:.2f}%")
print(f"  |Δm²₃₁| error = {error_31*100:.2f}%")
print()

if error_21 < 0.10 and error_31 < 0.10:
    print("✅ ✅ ✅ SUCCESS: Both within 10% PDG!")
elif error_21 < 0.30 and error_31 < 0.30:
    print("✅ GOOD: Within 30%, needs tuning")
else:
    print(f"⚠️  Still too large")

# Cosmology
sum_m = np.sum(masses_eV)
print(f"\nΣm_i = {sum_m:.2e} eV (limit: < 0.12 eV)")

