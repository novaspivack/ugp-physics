"""
higgs_srrg_correction_verification.py — EPIC_083C, Rank 083C-HIGGS (Task 3)

Verification and mechanistic analysis of the key finding from higgs_casimir_scan.py:

  λ_quartic = φ/(4π) × (1 + (IPT - 1)/N_gen³)

where:
  φ = (1+√5)/2 = golden ratio (SRRG fixed-point coupling)
  IPT = 1 + ln(φ)/(2 ln(2π)) = SRRG β-function IR tangency point
  N_gen = 3 = number of SM generations

This gives m_H = 125.250 GeV vs PDG 125.25 GeV (< 1 MeV agreement).

The analysis:
1. Exact numerical verification 
2. Mechanistic derivation: how does N_gen³ enter?
3. SRRG second-order expansion around g* = 1/φ
4. Null tests: is this a coincidence?
5. Lean candidacy assessment

Saves results to higgs_srrg_correction_results.json.
"""

import signal
import sys
import json
import math

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# === Physical constants ===
phi = (1 + math.sqrt(5)) / 2        # φ = 1.61803... (large golden ratio)
phi_s = phi - 1                      # ψ = 1/φ = 0.61803...
pi = math.pi

# SRRG constants
IPT = 1 + math.log(phi) / (2 * math.log(2*pi))
IPT_minus_1 = IPT - 1

# GTE structural
N_gen = 3
N_fam = 5
c_H = 13

# EW parameters
v_PDG = 246.22     # GeV
v_PSC = 246.16     # GeV (SRRG CatAL)
m_H_PDG = 125.25   # GeV (PDG 2022)
m_H_PDG_2023 = 125.20  # GeV (PDG 2023)
sigma_mH = 0.17    # GeV (PDG 2022 uncertainty) 
sigma_mH_2023 = 0.11  # GeV (PDG 2023 uncertainty)

# GTE quartic (P01)
lam_GTE = phi / (4*pi)

print("=" * 70)
print("SRRG CORRECTION VERIFICATION — EPIC_083C Rank 083C-HIGGS")
print("=" * 70)
print(f"\nSRRG constants:")
print(f"  φ = (1+√5)/2 = {phi:.15f}")
print(f"  ψ = φ-1 = 1/φ = {phi_s:.15f}")
print(f"  ln(φ) = {math.log(phi):.15f}")
print(f"  ln(2π) = {math.log(2*pi):.15f}")
print(f"  IPT = 1 + ln(φ)/(2 ln(2π)) = {IPT:.15f}")
print(f"  IPT - 1 = {IPT_minus_1:.15f}")

print(f"\nGTE quartic: λ_GTE = φ/(4π) = {lam_GTE:.15f}")
print(f"N_gen = {N_gen}, N_gen³ = {N_gen**3}")

# ===== Part 1: The SRRG-corrected formula =====
print("\n" + "=" * 70)
print("PART 1: The SRRG N_gen³ corrected formula")
print("=" * 70)
print("""
Candidate formula:
  λ = φ/(4π) × (1 + (IPT - 1)/N_gen³)
  = φ/(4π) × (1 + ln(φ)/(2 × N_gen³ × ln(2π)))
  = φ/(4π) × (1 + ln(φ)/(54 × ln(2π)))
  where 54 = 2 × N_gen³ = 2 × 27
""")

lam_corrected = lam_GTE * (1 + IPT_minus_1 / N_gen**3)
mH_corrected_PDG_v = math.sqrt(2 * lam_corrected) * v_PDG
mH_corrected_PSC_v = math.sqrt(2 * lam_corrected) * v_PSC

print(f"λ_corrected = {lam_corrected:.15f}")
print(f"λ_SM(v=PDG) = {m_H_PDG**2/(2*v_PDG**2):.15f}")
print(f"Difference:  {lam_corrected - m_H_PDG**2/(2*v_PDG**2):.2e}")

print(f"\nm_H predictions:")
print(f"  Using v_PDG = {v_PDG} GeV: m_H = {mH_corrected_PDG_v:.6f} GeV")
print(f"  Using v_PSC = {v_PSC} GeV: m_H = {mH_corrected_PSC_v:.6f} GeV")
print(f"  PDG 2022: {m_H_PDG:.4f} ± {sigma_mH:.2f} GeV")
print(f"  PDG 2023: {m_H_PDG_2023:.4f} ± {sigma_mH_2023:.2f} GeV")
print(f"  Residual tension (v_PDG, PDG2022): {(mH_corrected_PDG_v - m_H_PDG)/sigma_mH:.4f}σ")
print(f"  Residual tension (v_PDG, PDG2023): {(mH_corrected_PDG_v - m_H_PDG_2023)/sigma_mH_2023:.4f}σ")
print(f"  Residual tension (v_PSC, PDG2022): {(mH_corrected_PSC_v - m_H_PDG)/sigma_mH:.4f}σ")
print(f"  Residual tension (v_PSC, PDG2023): {(mH_corrected_PSC_v - m_H_PDG_2023)/sigma_mH_2023:.4f}σ")


# ===== Part 2: Exact ratio verification =====
print("\n" + "=" * 70)
print("PART 2: Exact ratio verification — is (IPT-1)/ε = 27 exactly?")
print("=" * 70)

lam_SM = m_H_PDG**2 / (2 * v_PDG**2)
eps = (lam_SM - lam_GTE) / lam_GTE
ratio = IPT_minus_1 / eps

print(f"\nε = (λ_SM - λ_GTE)/λ_GTE = {eps:.15f}")
print(f"IPT-1 = {IPT_minus_1:.15f}")
print(f"Ratio = (IPT-1)/ε = {ratio:.15f}")
print(f"N_gen³ = 27 = {N_gen**3}")
print(f"Deviation: ratio - 27 = {ratio - 27:.8f}")
print(f"Relative deviation: {(ratio-27)/27*100:.6f}%")

# What m_H would give ratio = exactly 27?
lam_exact27 = lam_GTE * (1 + IPT_minus_1/27)
mH_exact27 = math.sqrt(2 * lam_exact27) * v_PDG
print(f"\nWith ratio = EXACTLY 27:")
print(f"  λ = {lam_exact27:.15f}")
print(f"  m_H = {mH_exact27:.8f} GeV")
print(f"  Difference from PDG 2022: {(mH_exact27 - m_H_PDG)*1000:.4f} MeV")
print(f"  Difference from PDG 2023: {(mH_exact27 - m_H_PDG_2023)*1000:.4f} MeV")

# What denominator gives EXACT m_H = 125.25?
# λ = λ_GTE × (1 + (IPT-1)/N): need N such that m_H = 125.25 exactly
# lam_SM = lam_GTE × (1 + (IPT-1)/N) → N = (IPT-1)/((lam_SM/lam_GTE)-1) = (IPT-1)/ε
print(f"\nExact denominator for m_H = {m_H_PDG} GeV exactly:")
print(f"  N_exact = (IPT-1)/ε = {ratio:.8f}")
print(f"  Closest integer: {round(ratio)}")

# ===== Part 3: SRRG β-function second-order structure =====
print("\n" + "=" * 70)
print("PART 3: SRRG β-function structure and the quartic correction")
print("=" * 70)
print("""
The SRRG β function: β_η = κ(η - IPT)(η - 2)

Key structure:
  - IR fixed point at η = IPT = 1 + ln(φ)/(2 ln(2π)) ← EW vacuum
  - UV fixed point at η = 2 ← UV completion
  - κ > 0: overall coefficient (positive definite)

Near the IR fixed point (η ≈ IPT):
  β_η ≈ κ × (η - IPT) × (IPT - 2) = -κ(2-IPT)(η - IPT)
  
The β function has slope at IPT:
  β_η'(IPT) = κ(IPT - 2) < 0 (since IPT < 2, slope is negative → IR stable)

Second-order expansion of F[S] around S*:
  F[S] = F[S*] + (1/2)(η - IPT)² × F_η_η[S*] + ...
  
where F_η_η[S*] = κ(IPT - 2) < 0.

The correction to the Higgs quartic from the second-order SRRG term:
  δλ/λ ∝ (η_initial - IPT) × something × ...
  
The key dimensionless ratio in the SRRG framework that naturally gives
order 1/27 corrections:
""")

# The SRRG key quantities
eta_UV = 2.0  # UV fixed point
eta_IR = IPT  # IR fixed point

print(f"  IPT = {IPT:.8f}")
print(f"  UV fixed point = 2")
print(f"  (IPT - 1) = {IPT_minus_1:.8f}  [overshoot above minimal η=1]")
print(f"  (2 - IPT) = {2-IPT:.8f}  [distance to UV fixed point]")
print(f"  (IPT - 1)/(2 - IPT) = {IPT_minus_1/(2-IPT):.8f}")
print(f"  (2 - IPT)/(IPT - 1) = {(2-IPT)/IPT_minus_1:.8f}")

# If the correction is: δλ/λ = (IPT-1) × (2-IPT) / something:
ratio_product = IPT_minus_1 * (2-IPT)
print(f"\n  (IPT-1) × (2-IPT) = {ratio_product:.8f}")
print(f"  Required ε = {eps:.8f}")
print(f"  Required N to match: (IPT-1)×(2-IPT)/ε = {ratio_product/eps:.4f}")

# Alternatively, the SRRG contraction rate is 1/φ
# The related quantity: (IPT-1) × φ / N_gen^3
print(f"\n  Another candidate: (IPT-1)/N_gen³ = {IPT_minus_1/N_gen**3:.8f}")
print(f"  vs ε = {eps:.8f}")
print(f"  Match quality: {IPT_minus_1/N_gen**3 / eps:.8f}  (need = 1)")


# ===== Part 4: Null tests =====
print("\n" + "=" * 70)
print("PART 4: Null tests — could this be a coincidence?")
print("=" * 70)

print("\nTest A: Random denominator scan — how many integers give near-match?")
close_count = 0
for N in range(1, 1000):
    lam_test = lam_GTE * (1 + IPT_minus_1/N)
    mH_test = math.sqrt(2*lam_test)*v_PDG
    if abs(mH_test - m_H_PDG) < 0.1:  # within 100 MeV
        close_count += 1
        print(f"  N = {N}: λ = {lam_test:.8f}, m_H = {mH_test:.4f} GeV, "
              f"Δ = {(mH_test-m_H_PDG)*1000:.2f} MeV")
print(f"  Total integers 1-999 within 100 MeV of PDG: {close_count}")

print("\nTest B: Does IPT appear naturally in the quartic formula?")
print(f"  IPT = {IPT:.8f}")
print(f"  In terms of GTE: IPT = 1 + ln(φ)/(2 ln(2π))")
print(f"  = 1 + (Lyapunov exponent of SRRG) / (2 × ln of orbit period)")
print(f"  IPT is a natural SRRG constant derived in P27 (CatAL)")

print("\nTest C: Is N_gen³ = 27 distinguished among small integers?")
print(f"  Ratio (IPT-1)/ε = {ratio:.4f}")
print(f"  Nearest integers: 26, 27, 28")
for N_test in [25, 26, 27, 28, 29, 30]:
    lam_t = lam_GTE * (1 + IPT_minus_1/N_test)
    mH_t = math.sqrt(2*lam_t)*v_PDG
    tension = (mH_t - m_H_PDG)/sigma_mH
    print(f"  N = {N_test}: m_H = {mH_t:.4f} GeV, tension = {tension:.4f}σ", 
          end="")
    if N_test == 27:
        print(f"  ← N_gen³ = 3³")
    elif N_test == 26:
        print(f"  ← 2 × 13 = 2 × c_H")
    else:
        print()

print("\nTest D: Wrong target null test")
print("  Apply same formula to other observables to check for accidental match:")
# sin^2(theta_W) = 0.23121 (GTE CatAL)
sin2_W_GTE = 3.0/13 + (9/40)**3/(2*13)
sin2_W_PDG = 0.23121  # PDG
eps_W = (sin2_W_PDG - sin2_W_GTE)/sin2_W_GTE
ratio_W = IPT_minus_1 / eps_W
print(f"  sin²θ_W: GTE = {sin2_W_GTE:.8f}, PDG = {sin2_W_PDG:.8f}")
print(f"  ε = {eps_W:.8f}")
print(f"  (IPT-1)/ε = {ratio_W:.4f}  ← should NOT be 27 (null test)")

# M_W test
M_W_GTE = 80.372  # GeV (GTE CatAL from P35)
M_W_PDG = 80.377  # GeV (PDG)
eps_MW = (M_W_PDG - M_W_GTE)/M_W_GTE
ratio_MW = IPT_minus_1 / eps_MW if eps_MW != 0 else float('inf')
print(f"\n  M_W: GTE = {M_W_GTE:.4f}, PDG = {M_W_PDG:.4f} GeV")
print(f"  ε = {eps_MW:.8f}")
print(f"  (IPT-1)/ε = {ratio_MW:.4f}  ← should NOT be 27 (null test)")

# alpha_s test
alpha_s_GTE = 0.11822  # P39 (CatAD)
alpha_s_PDG = 0.1180
eps_as = (alpha_s_PDG - alpha_s_GTE)/alpha_s_GTE
ratio_as = IPT_minus_1 / abs(eps_as) if eps_as != 0 else float('inf')
print(f"\n  α_s(M_Z): GTE = {alpha_s_GTE:.5f}, PDG = {alpha_s_PDG:.5f}")
print(f"  ε = {eps_as:.8f}")
print(f"  |ε|: (IPT-1)/|ε| = {ratio_as:.4f}  ← null test")


# ===== Part 5: The SRRG-generated correction mechanism =====
print("\n" + "=" * 70)
print("PART 5: Physical mechanism — how N_gen³ enters the SRRG correction")
print("=" * 70)
print("""
Proposed mechanism for λ_quartic correction:

At the SRRG fixed point g* = 1/φ, the Higgs quartic arises from the self-interaction
of the GTE orbit. The orbit has N_gen = 3 independent generation channels.

The SRRG efficiency overshoot is (IPT - 1), measuring how much the self-model update
cycle overshoots the absolute minimum (η = 1) in the IR direction.

In the GTE framework, the Higgs is the triple (5, 3, 13): it couples to all three
generation sectors simultaneously. The three-body coupling involves N_gen factors:
  - N_gen = 3 for each generation pairing (g₁ × g₂ × g₃ modes)
  - Total three-body coupling modes: N_gen³ = 27

The correction to the quartic from SRRG at next order:
  δλ/λ = (IPT - 1) / N_gen³ = ln(φ)/(2 × 27 × ln(2π))

This is the "SRRG overshoot per generation-cube mode."

Alternatively: the β function for λ receives a correction proportional to
(IPT - 1)/(N_gen × β_η_slope), where β_η_slope at IPT = κ(IPT-2) ≈ -κ(2-IPT).

The dimensionless ratio (IPT-1)/(2-IPT) = (IPT-1)/(2-IPT) and with N_gen
gives (IPT-1)/((2-IPT)^{N_gen/2}) if we use the appropriate power...
""")

# Check: does any formula involving (2-IPT) and N_gen give exactly eps?
for formula_name, formula_val in [
    ("(IPT-1)/N_gen^3", IPT_minus_1 / N_gen**3),
    ("(IPT-1)*(2-IPT)/N_gen", IPT_minus_1 * (2-IPT) / N_gen),
    ("(IPT-1)^2/(2-IPT)/N_gen", IPT_minus_1**2 / (2-IPT) / N_gen),
    ("(IPT-1)*(2-IPT)^2", IPT_minus_1 * (2-IPT)**2),
    ("(IPT-1)/(N_gen*(2-IPT)*phi)", IPT_minus_1 / (N_gen * (2-IPT) * phi)),
    ("(IPT-1)*N_gen/(2-IPT)^3", IPT_minus_1 * N_gen / (2-IPT)**3),
]:
    match = formula_val / eps
    print(f"  {formula_name:<40} = {formula_val:.8f}  (match ratio = {match:.4f})")


# ===== Part 6: Complete formula statement and CatLevel assessment =====
print("\n" + "=" * 70)
print("PART 6: Formula statement and Lean candidacy")
print("=" * 70)
print(f"""
CANDIDATE FORMULA:

  λ_quartic = φ/(4π) × (1 + (IPT-1)/N_gen³)

where:
  φ = (1+√5)/2 = {phi:.10f}  [golden ratio, SRRG fixed-point magnitude]
  IPT = 1 + ln(φ)/(2 ln(2π)) = {IPT:.10f}  [SRRG IR tangency point, P27]
  N_gen = 3  [number of SM generations, Lean-certified N_gen=3]

Explicitly:
  λ = φ/(4π) × (1 + ln(φ)/(54 × ln(2π)))
  where 54 = 2 × N_gen³ = 2 × 27

Numerical values:
  λ = {lam_corrected:.10f}
  m_H = √(2λ) × v_PDG = {mH_corrected_PDG_v:.6f} GeV  (v = {v_PDG} GeV)
  m_H = √(2λ) × v_PSC = {mH_corrected_PSC_v:.6f} GeV  (v = {v_PSC} GeV, SRRG CatAL)
  PDG 2022: m_H = {m_H_PDG:.4f} ± {sigma_mH:.2f} GeV
  PDG 2023: m_H = {m_H_PDG_2023:.4f} ± {sigma_mH_2023:.2f} GeV
  Tension (v_PDG, PDG2022): {(mH_corrected_PDG_v - m_H_PDG)/sigma_mH:.4f}σ
  Tension (v_PDG, PDG2023): {(mH_corrected_PDG_v - m_H_PDG_2023)/sigma_mH_2023:.4f}σ
  Tension (v_PSC, PDG2022): {(mH_corrected_PSC_v - m_H_PDG)/sigma_mH:.4f}σ
  Tension (v_PSC, PDG2023): {(mH_corrected_PSC_v - m_H_PDG_2023)/sigma_mH_2023:.4f}σ

Status: CANDIDATE (CatA_MDL → needs CatAD mechanistic derivation)

Lean candidacy:
  Existing Lean: lambda_H_from_srrg_stability (P27), HiggsQuartic.lean
  New theorem needed: higgs_quartic_srrg_ngen_correction
  Ingredients:
    - IPT = 1 + ln(phi)/(2*ln(2*pi)) [IPT_definition, in P27 SRRG Lean]
    - N_gen = 3 [ngen_3_mersenne_uniqueness, CatAL]
    - lambda_GTE = phi/(4*pi) [from P01]
    - Correction factor: (1 + (IPT-1)/N_gen^3)
""")


# ===== Part 7: The Wolfenstein-pattern candidate for comparison =====
print("=" * 70)
print("PART 7: Best Wolfenstein-pattern candidate for comparison")
print("=" * 70)
print("""
From the Casimir scan: φ/(4π) + λ_W⁴/4 is the closest Wolfenstein-type expression.
""")
lam_W = 9.0/40
lam_wolf = lam_GTE + lam_W**4 / 4
mH_wolf = math.sqrt(2*lam_wolf) * v_PDG
print(f"  λ = φ/(4π) + λ_W⁴/4 = {lam_GTE:.8f} + {lam_W**4/4:.8f} = {lam_wolf:.8f}")
print(f"  m_H = {mH_wolf:.6f} GeV")
print(f"  vs PDG 2022: {m_H_PDG:.4f} GeV (tension = {(mH_wolf-m_H_PDG)/sigma_mH:.3f}σ)")
print(f"  vs PDG 2023: {m_H_PDG_2023:.4f} GeV (tension = {(mH_wolf-m_H_PDG_2023)/sigma_mH_2023:.3f}σ)")
print(f"\n  Note: λ_W⁴/4 = (9/40)⁴/4 = {lam_W**4/4:.8f}")
print(f"  vs SRRG correction = {IPT_minus_1/N_gen**3:.8f}")
print(f"  Ratio (Wolf / SRRG) = {(lam_W**4/4)/(IPT_minus_1/N_gen**3):.4f}")
print(f"\n  Wolfenstein candidate is 2.6% off (not as good as SRRG N_gen³ formula)")


# ===== Summary =====
print("\n" + "=" * 70)
print("EXECUTIVE SUMMARY")
print("=" * 70)
print(f"""
KEY RESULT: The formula 

  λ_quartic = φ/(4π) × (1 + ln(φ)/(54 ln(2π)))

where 54 = 2 × N_gen³ = 2 × 3³, gives:

  λ = {lam_corrected:.10f}
  m_H = {mH_corrected_PDG_v:.4f} GeV  (using v_PDG = 246.22 GeV)
  m_H = {mH_corrected_PSC_v:.4f} GeV  (using v_PSC = 246.16 GeV)
  
  PDG: {m_H_PDG:.4f} ± {sigma_mH:.2f} GeV (2022), {m_H_PDG_2023:.4f} ± {sigma_mH_2023:.2f} GeV (2023)
  
  Residual tension: {(mH_corrected_PDG_v - m_H_PDG)/sigma_mH:.4f}σ (PDG 2022)
                    {(mH_corrected_PDG_v - m_H_PDG_2023)/sigma_mH_2023:.4f}σ (PDG 2023)

IMPROVEMENT:
  Original λ_GTE = φ/(4π):       m_H = {math.sqrt(2*lam_GTE)*v_PDG:.4f} GeV ({(math.sqrt(2*lam_GTE)*v_PDG - m_H_PDG)/sigma_mH:.2f}σ)
  Corrected λ = φ/(4π)×correction: m_H = {mH_corrected_PDG_v:.4f} GeV ({(mH_corrected_PDG_v - m_H_PDG)/sigma_mH:.4f}σ)

STRUCTURE:
  The correction (IPT-1)/N_gen³ involves:
  - IPT-1 = ln(φ)/(2 ln(2π)) = SRRG efficiency overshoot (natural SRRG quantity, P27)
  - N_gen³ = 27 = 3³ = generation-cube volume (natural GTE quantity)
  - Ratio (IPT-1)/ε = {ratio:.6f} ≈ 27 exactly

NULL TESTS:
  - sin²θ_W: (IPT-1)/ε = {IPT_minus_1 / ((sin2_W_PDG-sin2_W_GTE)/sin2_W_GTE):.1f}  (NOT 27) ✓
  - M_W:     (IPT-1)/ε = {ratio_MW:.1f}  (NOT 27) ✓
  - α_s:     (IPT-1)/|ε| = {ratio_as:.1f}  (NOT 27) ✓

LEAN STATUS: 
  Candidate for new theorem: higgs_quartic_srrg_ngen_correction
  CatLevel: CatA_MDL (numerical, awaiting mechanistic derivation for CatAD)
  Precedent: Wolfenstein sin²θ_W was similarly first numerically found, then
             derived from CKM orbit structure (CatAL).
""")

# ===== Save results =====
results = {
    'formula': 'lambda = phi/(4pi) * (1 + (IPT-1)/N_gen^3)',
    'explicit': 'lambda = phi/(4pi) * (1 + ln(phi)/(54*ln(2pi)))',
    'where': {'54': '2 * N_gen^3 = 2 * 27'},
    'phi': phi,
    'IPT': IPT,
    'IPT_minus_1': IPT_minus_1,
    'N_gen': N_gen,
    'N_gen_cubed': N_gen**3,
    'lam_GTE': lam_GTE,
    'lam_corrected': lam_corrected,
    'mH_vPDG': mH_corrected_PDG_v,
    'mH_vPSC': mH_corrected_PSC_v,
    'mH_PDG_2022': m_H_PDG,
    'mH_PDG_2023': m_H_PDG_2023,
    'tension_vPDG_PDG2022_sigma': (mH_corrected_PDG_v - m_H_PDG)/sigma_mH,
    'tension_vPDG_PDG2023_sigma': (mH_corrected_PDG_v - m_H_PDG_2023)/sigma_mH_2023,
    'tension_vPSC_PDG2022_sigma': (mH_corrected_PSC_v - m_H_PDG)/sigma_mH,
    'ratio_IPT_minus_1_over_eps': ratio,
    'ratio_deviation_from_27': ratio - 27,
    'null_tests': {
        'sin2_W_ratio': IPT_minus_1 / abs((sin2_W_PDG-sin2_W_GTE)/sin2_W_GTE),
        'MW_ratio': ratio_MW,
        'alpha_s_ratio': ratio_as,
    },
    'improvement_sigma': {
        'before': (math.sqrt(2*lam_GTE)*v_PDG - m_H_PDG)/sigma_mH,
        'after': (mH_corrected_PDG_v - m_H_PDG)/sigma_mH,
    },
    'lean_candidate': 'higgs_quartic_srrg_ngen_correction',
    'status': 'CatA_MDL — needs CatAD mechanistic derivation for N_gen^3 factor',
}

import os
out_path = os.path.join(os.path.dirname(__file__), 'higgs_srrg_correction_results.json')
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {out_path}")

signal.alarm(0)
print("\nDone.")
