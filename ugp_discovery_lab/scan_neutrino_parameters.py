#!/usr/bin/env python3
"""
Systematic parameter scan for neutrino mass seesaw

Scans M_R_scale, M_D_scale, hierarchy_factor to find combination
that achieves Δm²₂₁ and Δm²₃₁ within 10% of PDG values

Uses log-ratio normalized features with LOCKED canonical triples
"""

import numpy as np
import math
import json
from pathlib import Path

print("=" * 80)
print("NEUTRINO SEESAW PARAMETER SCAN")
print("=" * 80)
print()

# Constants
phi = (1 + np.sqrt(5)) / 2
k_L2 = 7 / 512
k_gen = np.pi / 2

# LOCKED canonical triples  
nu_L_triples = [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)]
nu_R_triples = [(2, 5, 5), (7, 11, 13), (17, 19, 23)]
gens = [1, 2, 3]

# PDG targets
PDG_delta_m21_sq = 7.5e-5  # eV²
PDG_delta_m31_sq = 2.5e-3  # eV²

def extract_pure_log_ratio_features(a, b, c, g, sector):
    """Pure log-ratio normalization."""
    L = math.log(abs(float(b)) / abs(float(c))) if c != 0 else 0.0
    triple_norm = np.sqrt(a**2 + b**2 + c**2)
    
    s_gen = L
    e1 = ((2*a - b - c) / np.sqrt(6)) / triple_norm
    e2 = ((b - c) / np.sqrt(2)) / triple_norm
    
    phase_E = np.exp(1j * g * k_gen * (0.5 if sector == "nu_R" else 1.0))
    e1_rotated = e1 * phase_E
    e2_rotated = e2 * phase_E
    
    delta = ((a - b) * (b - c) * (c - a)) / (triple_norm**3)
    
    return s_gen, (e1_rotated, e2_rotated), delta

def calculate_masses(M_R_scale, M_D_scale, hierarchy_factor):
    """Calculate neutrino masses for given parameters."""
    
    # Extract features
    nu_L_features = [extract_pure_log_ratio_features(*t, g, "nu") 
                     for t, g in zip(nu_L_triples, gens)]
    nu_R_features = [extract_pure_log_ratio_features(*t, g, "nu_R") 
                     for t, g in zip(nu_R_triples, gens)]
    
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
    
    # Construct M_R
    M_R = np.zeros((3, 3), dtype=complex)
    for i, feat_i in enumerate(nu_R_features):
        for j, feat_j in enumerate(nu_R_features):
            s_i, (e1_i, e2_i), delta_i = feat_i
            s_j, (e1_j, e2_j), delta_j = feat_j
            
            gram = (s_i * s_j + 
                   e1_i * np.conj(e1_j) + e2_i * np.conj(e2_j) + 
                   delta_i * delta_j * k_L2)
            
            h_factor = (1.0 if i == j else hierarchy_factor)
            M_R[i, j] = gram * M_R_scale * h_factor
    
    M_R = 0.5 * (M_R + M_R.T)
    M_R += np.eye(3) * np.trace(M_R) * 0.1
    
    # Check if M_R is singular
    try:
        M_R_inv = np.linalg.inv(M_R)
    except:
        return None  # Singular matrix
    
    # Calculate M_eff
    M_eff = -M_D @ M_R_inv @ M_D.T
    M_eff = 0.5 * (M_eff + M_eff.T)
    
    # Extract masses
    eigenvals = np.linalg.eigvals(M_eff)
    masses_sq_GeV = np.abs(eigenvals)
    masses_sq_eV = masses_sq_GeV * (1e9)**2
    
    # Mass differences
    masses_sq_sorted = np.sort(masses_sq_eV)
    delta_m21_sq = masses_sq_sorted[1] - masses_sq_sorted[0]
    delta_m31_sq = masses_sq_sorted[2] - masses_sq_sorted[0]
    
    # Errors
    error_21 = abs(delta_m21_sq - PDG_delta_m21_sq) / PDG_delta_m21_sq
    error_31 = abs(abs(delta_m31_sq) - PDG_delta_m31_sq) / PDG_delta_m31_sq
    
    masses_eV = np.sqrt(masses_sq_GeV) * 1e9
    sum_masses = np.sum(masses_eV)
    
    return {
        'M_R_scale': M_R_scale,
        'M_D_scale': M_D_scale,
        'hierarchy_factor': hierarchy_factor,
        'delta_m21_sq': delta_m21_sq,
        'delta_m31_sq': delta_m31_sq,
        'error_21_pct': error_21 * 100,
        'error_31_pct': error_31 * 100,
        'max_error_pct': max(error_21, error_31) * 100,
        'sum_masses_eV': sum_masses,
        'masses_eV': masses_eV.tolist(),
        'success_10pct': (error_21 < 0.10 and error_31 < 0.10),
        'success_30pct': (error_21 < 0.30 and error_31 < 0.30),
        'cosmology_ok': (sum_masses < 0.12)
    }

print("Starting systematic parameter scan...")
print()

# Parameter ranges to scan
M_R_scales = [1e10, 1e12, 1e14, 1e16, 1e18, 1e20]
M_D_scales = [1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]
hierarchy_factors = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]

best_results = []
total_tests = len(M_R_scales) * len(M_D_scales) * len(hierarchy_factors)
test_count = 0

print(f"Scanning {total_tests} parameter combinations...")
print(f"Target: Δm²₂₁ and Δm²₃₁ errors < 10%")
print()

for M_R in M_R_scales:
    for M_D in M_D_scales:
        for h_f in hierarchy_factors:
            test_count += 1
            
            result = calculate_masses(M_R, M_D, h_f)
            
            if result is None:
                continue  # Skip singular matrices
            
            # Progress indicator
            if test_count % 50 == 0:
                print(f"  Tested {test_count}/{total_tests} combinations...")
            
            # Save if reasonably good
            if result['max_error_pct'] < 100:  # Within factor 2
                best_results.append(result)
            
            # Report if very good
            if result['success_10pct']:
                print(f"\n✅ ✅ FOUND 10% PDG SOLUTION:")
                print(f"   M_R_scale = {M_R:.2e} GeV")
                print(f"   M_D_scale = {M_D:.2e} GeV")
                print(f"   hierarchy_factor = {h_f:.2e}")
                print(f"   Δm²₂₁ error = {result['error_21_pct']:.2f}%")
                print(f"   Δm²₃₁ error = {result['error_31_pct']:.2f}%")
                print()
            elif result['success_30pct'] and test_count % 50 == 0:
                print(f"  → Found 30% solution: M_R={M_R:.1e}, M_D={M_D:.1e}, h={h_f:.1e}")

print()
print("=" * 80)
print("SCAN COMPLETE")
print("=" * 80)
print()

# Sort by max error
best_results.sort(key=lambda x: x['max_error_pct'])

print(f"Found {len(best_results)} reasonable solutions (< factor 2)")
print()

if best_results:
    print("TOP 10 SOLUTIONS:")
    print()
    for i, res in enumerate(best_results[:10], 1):
        status = "✅ 10% PDG" if res['success_10pct'] else "✓ 30%" if res['success_30pct'] else "○"
        print(f"{i}. {status} M_R={res['M_R_scale']:.1e}, M_D={res['M_D_scale']:.1e}, h={res['hierarchy_factor']:.1e}")
        print(f"   Errors: Δm²₂₁={res['error_21_pct']:.1f}%, Δm²₃₁={res['error_31_pct']:.1f}%")
        print(f"   Δm²₂₁={res['delta_m21_sq']:.2e} eV², Δm²₃₁={res['delta_m31_sq']:.2e} eV²")
        if i <= 3:
            print(f"   Masses: [{res['masses_eV'][0]:.2e}, {res['masses_eV'][1]:.2e}, {res['masses_eV'][2]:.2e}] eV")
            print(f"   Σm={res['sum_masses_eV']:.2e} eV, Cosmo OK: {res['cosmology_ok']}")
        print()
    
    # Save best results
    output_file = Path("neutrino_parameter_scan_results.json")
    with open(output_file, 'w') as f:
        json.dump(best_results[:20], f, indent=2)
    
    print(f"✅ Top 20 solutions saved to: {output_file}")
    print()
    
    # Check if we found a 10% solution
    solutions_10pct = [r for r in best_results if r['success_10pct']]
    if solutions_10pct:
        print(f"🎉 🎉 🎉 SUCCESS: Found {len(solutions_10pct)} solutions within 10% PDG!")
        print()
        print("BEST SOLUTION:")
        best = solutions_10pct[0]
        print(f"  M_R_scale = {best['M_R_scale']:.2e} GeV")
        print(f"  M_D_scale = {best['M_D_scale']:.2e} GeV")
        print(f"  hierarchy_factor = {best['hierarchy_factor']:.2e}")
        print(f"  Δm²₂₁ error = {best['error_21_pct']:.2f}% ✅")
        print(f"  Δm²₃₁ error = {best['error_31_pct']:.2f}% ✅")
    else:
        print("⚠️  No 10% PDG solutions found in this scan")
        print("   Try expanding parameter ranges or different formula")

else:
    print("❌ No reasonable solutions found")
    print("   The overlap formula may need fundamental revision")

