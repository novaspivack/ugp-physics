#!/usr/bin/env python3
"""
Test MFRR Information Profit Principle against Symmetry Breaking Data
"""
import numpy as np

# Norfleet's constant
Lambda = np.log(1.618033988749895) / np.log(2*np.pi)  # φ = golden ratio
profit_critical = 1 + Lambda/2

print("="*70)
print("TESTING INFORMATION PROFIT PRINCIPLE IN SYMMETRY BREAKING")
print("="*70)
print(f"\nTheoretical Predictions:")
print(f"Profit_critical = 1 + Λ/2 = {profit_critical:.6f}")
print(f"Λ = {Lambda:.6f}")
print(f"Λ/2 = {Lambda/2:.6f}")
print()

# ============================================================================
# TEST 1: QCD Chiral Symmetry Breaking (Pions as pseudo-Goldstone bosons)
# ============================================================================
print("="*70)
print("TEST 1: QCD Chiral Symmetry Breaking (Pions)")
print("="*70)

m_pi = 139.57  # MeV (charged pion)
f_pi = 92.2    # MeV (pion decay constant)
Lambda_QCD = 400  # MeV (rough QCD scale)

print(f"\nKnown values:")
print(f"  m_π = {m_pi:.2f} MeV")
print(f"  f_π = {f_pi:.2f} MeV") 
print(f"  Λ_QCD ≈ {Lambda_QCD} MeV")

print(f"\nTest A: (m_π/Λ_QCD)² vs Λ/2")
ratio_A = (m_pi / Lambda_QCD)**2
print(f"  (m_π/Λ_QCD)² = ({m_pi}/{Lambda_QCD})² = {ratio_A:.6f}")
print(f"  Λ/2 = {Lambda/2:.6f}")
print(f"  Error: {abs(ratio_A - Lambda/2)/( Lambda/2)*100:.2f}%")

print(f"\nTest B: (m_π/f_π)² vs Λ/2")
ratio_B = (m_pi / f_pi)**2
print(f"  (m_π/f_π)² = ({m_pi:.2f}/{f_pi:.2f})² = {ratio_B:.6f}")
print(f"  Λ/2 = {Lambda/2:.6f}")
print(f"  Error: {abs(ratio_B - Lambda/2)/(Lambda/2)*100:.2f}%")

print(f"\nTest C: f_π²/v² where v is some breaking scale")
# In QCD, the constituent quark mass is ~300 MeV
v_QCD_constituent = 300  # MeV
ratio_C1 = f_pi**2 / v_QCD_constituent**2
expected_C = 1/(1 + Lambda/2)
print(f"  v_QCD = {v_QCD_constituent} MeV (constituent quark)")
print(f"  f_π²/v² = {ratio_C1:.6f}")
print(f"  Expected (1/(1+Λ/2)) = {expected_C:.6f}")
print(f"  Error: {abs(ratio_C1 - expected_C)/expected_C*100:.2f}%")

# Alternative: use Lambda_QCD as v
ratio_C2 = f_pi**2 / Lambda_QCD**2
print(f"\n  v_QCD = {Lambda_QCD} MeV (Λ_QCD)")
print(f"  f_π²/v² = {ratio_C2:.6f}")
print(f"  Expected (1/(1+Λ/2)) = {expected_C:.6f}")
print(f"  Error: {abs(ratio_C2 - expected_C)/expected_C*100:.2f}%")

# ============================================================================
# TEST 2: Electroweak Symmetry Breaking
# ============================================================================
print("\n" + "="*70)
print("TEST 2: Electroweak Symmetry Breaking")
print("="*70)

m_W = 80379  # MeV (W boson mass)
m_Z = 91188  # MeV (Z boson mass) 
m_H = 125090  # MeV (Higgs mass)
v_EW = 246000  # MeV (electroweak VEV)
g_weak = 0.653  # weak coupling at M_Z

print(f"\nKnown values:")
print(f"  m_W = {m_W} MeV")
print(f"  m_Z = {m_Z} MeV")
print(f"  m_H = {m_H} MeV")
print(f"  v_EW = {v_EW} MeV")

# W and Z are "eaten" Goldstone bosons that became massive via Higgs mechanism
# This is different - they SHOULD be massless but aren't due to gauge coupling

print(f"\nTest: (m_H/v_EW)² vs Λ/2")
ratio_EW = (m_H / v_EW)**2
print(f"  (m_H/v_EW)² = ({m_H}/{v_EW})² = {ratio_EW:.6f}")
print(f"  Λ/2 = {Lambda/2:.6f}")
print(f"  Error: {abs(ratio_EW - Lambda/2)/(Lambda/2)*100:.2f}%")

# ============================================================================
# TEST 3: Different mass ratios within QCD
# ============================================================================
print("\n" + "="*70)
print("TEST 3: Alternative QCD Ratios")
print("="*70)

m_rho = 775.3  # MeV (rho meson - massive mode)
m_K = 493.7    # MeV (kaon - heavier pseudo-Goldstone)

print(f"\nTest A: (m_π/m_ρ)² vs Λ/2")
ratio_rho = (m_pi / m_rho)**2  
print(f"  (m_π/m_ρ)² = ({m_pi:.2f}/{m_rho:.1f})² = {ratio_rho:.6f}")
print(f"  Λ/2 = {Lambda/2:.6f}")
print(f"  Error: {abs(ratio_rho - Lambda/2)/(Lambda/2)*100:.2f}%")

print(f"\nTest B: m_π / (f_π·√(1+Λ/2))")
expected_ratio = np.sqrt(Lambda/2) 
actual_ratio = m_pi / (f_pi * np.sqrt(1 + Lambda/2))
print(f"  m_π / (f_π·√(1+Λ/2)) = {actual_ratio:.6f}")
print(f"  Expected √(Λ/2) = {expected_ratio:.6f}")
print(f"  Error: {abs(actual_ratio - expected_ratio)/expected_ratio*100:.2f}%")

# ============================================================================
# TEST 4: Degrees of Freedom Interpretation
# ============================================================================
print("\n" + "="*70)
print("TEST 4: Degrees of Freedom / Phase Space Interpretation")
print("="*70)

# QCD: SU(3)_L × SU(3)_R → SU(3)_V
# Broken generators: 3² - 1 = 8 (one is neutral under everything)
# Goldstone bosons: 8 (pions, kaons, eta)
# But flavor SU(3) is explicitly broken by quark masses

print(f"\nQCD Chiral Breaking: SU(3)_L × SU(3)_R → SU(3)_V")
print(f"  Generators in G/H: 9 + 9 - 9 = 9 (really 8 physical)")
print(f"  Goldstone bosons: π⁺, π⁻, π⁰, K⁺, K⁻, K⁰, K̄⁰, η")
print(f"  All acquire small masses due to explicit quark mass breaking")

print(f"\nInterpretation as profit margin:")
print(f"  If 'profit' = (free DOF) / (constrained DOF)")
print(f"  And we need profit > 1.13 for stability...")
print(f"  Then: N_Goldstone / N_effective_massive ≈ Λ/2?")

N_goldstone = 8
N_massive_approx = N_goldstone / (Lambda/2)  # predicted
print(f"  Predicted N_massive ≈ {N_massive_approx:.1f}")
print(f"  (This would be the effective number of 'expensive' modes)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("SUMMARY OF RESULTS")
print("="*70)

results = [
    ("QCD: (m_π/Λ_QCD)²", ratio_A, Lambda/2, abs(ratio_A - Lambda/2)/(Lambda/2)*100),
    ("QCD: (m_π/f_π)²", ratio_B, Lambda/2, abs(ratio_B - Lambda/2)/(Lambda/2)*100),
    ("QCD: (m_π/m_ρ)²", ratio_rho, Lambda/2, abs(ratio_rho - Lambda/2)/(Lambda/2)*100),
    ("EW: (m_H/v)²", ratio_EW, Lambda/2, abs(ratio_EW - Lambda/2)/(Lambda/2)*100),
]

print(f"\n{'Test':<25} {'Observed':<12} {'Expected':<12} {'Error':<10}")
print("-"*70)
for test_name, obs, exp, err in results:
    print(f"{test_name:<25} {obs:<12.6f} {exp:<12.6f} {err:<10.2f}%")

print("\n" + "="*70)
best_match = min(results, key=lambda x: x[3])
print(f"BEST MATCH: {best_match[0]}")
print(f"  Error: {best_match[3]:.2f}%")
print("="*70)
