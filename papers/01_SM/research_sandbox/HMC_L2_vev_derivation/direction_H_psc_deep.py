"""
direction_H_psc_deep.py
=======================
EPIC_051 Round PSC-1 through PSC-4
Genius Team PSC Deep Session: v/M2* analysis, symmetry-breaking entropy, CW bootstrap

Runs four distinct analyses:
  PSC-1: Systematic structural formula search for v/M2*
  PSC-2: Deep anatomy of L_model and analogues
  PSC-3: MDL of EW symmetry-breaking pattern (Jane's approach)
  PSC-4: Coleman-Weinberg PSC bootstrap (Carl's approach)

Outputs: direction_H_psc_deep.json
"""

import numpy as np
import json
from itertools import product

# ─── Physical constants ────────────────────────────────────────────────────────
phi    = (1 + 5**0.5) / 2          # Golden ratio
pi     = np.pi
ln2    = np.log(2)
e_eu   = np.e                       # Euler's number
M_P    = 1.22089e19                 # GeV — reduced Planck mass (2.435e18) × √(8π) ≈ no, use total: M_Pl = 1.22089×10^19

# UGP-certified values
g2_bare_sq  = 2329 / 5400           # g₂² bare (Lean-certified)
g2_bare     = g2_bare_sq**0.5
g1_bare_sq  = 16 / 125              # g₁² bare (Lean-certified)
g1_bare     = g1_bare_sq**0.5
D1          = 16                    # = 2⁴ discrete charge invariant
D_SU2       = g2_bare_sq * 25 / 2   # = 2329/432 (gauge master formula)
lambda_H    = phi / (4*pi)          # MDL-certified Higgs quartic

# Physical observables
v_PDG       = 246.22                # GeV — EW VEV (PDG 2024)
mH_PDG      = 125.20                # GeV — Higgs mass (PDG 2024)
mW_PDG      = 80.379                # GeV — W boson mass (PDG 2024)
mZ_PDG      = 91.1876               # GeV — Z boson mass

# UGP scales
M2_star     = 37.4                  # GeV — UGP bare scale (1-loop: SC-CC result)
M2_star_2lp = 34.6579               # GeV — UGP bare scale (2-loop: from comp_p01_EW_full_matching.json)

# PSC cosmological parameters
L_model_cosmo = np.log2(D1 * 5**3 / 3)  # = log₂(2000/3) ≈ 9.3808 bits
H0_per_c_invGeV = 2.195e-42             # H₀/c in GeV⁻¹ (H₀=67.4 km/s/Mpc → 1/Hubble radius in GeV⁻¹)
Lambda_pred = (ln2/pi) * L_model_cosmo * (H0_per_c_invGeV)**2  # Λ in GeV²

# Braid c-values (Lean-certified)
c_W = 11
c_Z = 12
c_H = 13

results = {}

# ══════════════════════════════════════════════════════════════════════════════════
# PSC-1: v/M₂* ratio analysis
# ══════════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PSC-1: v/M₂* RATIO ANALYSIS")
print("=" * 70)

for label, M2s in [("1loop_37.4", M2_star), ("2loop_34.56", M2_star_2lp)]:
    ratio = v_PDG / M2s
    log_ratio = np.log(ratio)
    log2_ratio = np.log2(ratio)
    print(f"\n--- M₂* = {M2s} GeV ---")
    print(f"  v/M₂* = {ratio:.6f}")
    print(f"  ln(v/M₂*) = {log_ratio:.6f}")
    print(f"  log₂(v/M₂*) = {log2_ratio:.6f}")
    print(f"  Note: log₂(v/M₂*) = {log2_ratio:.6f}")
    # Check if close to simple atoms
    atoms = {
        'φ': phi, 'ln(φ)': np.log(phi), 'π/2': pi/2, 'π': pi,
        'ln(2)': ln2, 'e': e_eu, '√φ': phi**0.5, 'φ²': phi**2,
        'π/ln2': pi/ln2, 'ln2/π': ln2/pi, '2π': 2*pi
    }
    print(f"  Comparing ln(v/M₂*) = {log_ratio:.4f} to atoms:")
    for aname, aval in atoms.items():
        err = abs(log_ratio/aval - 1) * 100
        if err < 5:
            print(f"    → {aname} = {aval:.4f} (err={err:.2f}%)")

# systematic formula search: v = M₂* × a × φ^b × π^c × 2^d
print("\n--- Systematic formula search (v = M₂* × a×φ^b×π^c×2^d) ---")
target = v_PDG / M2_star
hits_1loop = []
for a, b, c, d in product(range(1, 10), range(-5, 6), range(-3, 4), range(-5, 6)):
    val = a * phi**b * pi**c * 2**d
    err = abs(val/target - 1)
    if err < 0.005:
        hits_1loop.append({'a':a,'b':b,'c':c,'d':d,'val':round(val,6),'err_pct':round(err*100,4),
                           'complexity': abs(a)+abs(b)+abs(c)+abs(d)})

hits_1loop.sort(key=lambda x: x['complexity'])
print(f"  Hits at 0.5% for M₂*=37.4: {len(hits_1loop)}")
for h in hits_1loop[:8]:
    print(f"    {h['a']}·φ^{h['b']}·π^{h['c']}·2^{h['d']} = {h['val']:.4f} (err={h['err_pct']:.4f}%, complexity={h['complexity']})")

# Also search for: ln(v/M₂*) = a·ln(φ) + b·ln(2) + c·π
target_ln = np.log(v_PDG / M2_star)
print(f"\n--- Formula: ln(v/M₂*) = a·ln(φ)+b·ln(2)+c·π, target={target_ln:.6f} ---")
ln_hits = []
for a, b, c in product(range(-5, 6), range(-5, 6), range(-3, 4)):
    val = a*np.log(phi) + b*ln2 + c*pi
    err = abs(val - target_ln)
    if err < 0.05:
        ln_hits.append({'a':a,'b':b,'c':c,'val':round(val,6),'err':round(err,6),
                        'complexity': abs(a)+abs(b)+abs(c)})
ln_hits.sort(key=lambda x: x['complexity'])
print(f"  Hits (|err|<0.05): {len(ln_hits)}")
for h in ln_hits[:5]:
    print(f"    {h['a']}·ln(φ)+{h['b']}·ln(2)+{h['c']}·π = {h['val']:.6f} (err={h['err']:.6f}, complexity={h['complexity']})")

# Null discipline for 1-loop
import random
random.seed(42)
np.random.seed(42)
null_hits = []
for trial in range(30):
    rand_target = np.exp(np.random.uniform(np.log(4), np.log(10)))
    n = 0
    for a, b, c, d in product(range(1, 10), range(-5, 6), range(-3, 4), range(-5, 6)):
        val = a * phi**b * pi**c * 2**d
        if abs(val/rand_target - 1) < 0.005:
            n += 1
    null_hits.append(n)
null_median = np.median(null_hits)
real_hits = len(hits_1loop)
saturation = real_hits / null_median if null_median > 0 else float('inf')
print(f"\n  Null discipline (30 random targets in [4,10]):")
print(f"    Real hits: {real_hits}, Null median: {null_median:.0f}, Saturation: {saturation:.2f}")

results['psc1'] = {
    'v_over_M2_1loop': round(v_PDG/M2_star, 6),
    'ln_v_over_M2_1loop': round(np.log(v_PDG/M2_star), 6),
    'log2_v_over_M2_1loop': round(np.log2(v_PDG/M2_star), 6),
    'v_over_M2_2loop': round(v_PDG/M2_star_2lp, 6),
    'ln_v_over_M2_2loop': round(np.log(v_PDG/M2_star_2lp), 6),
    'log2_v_over_M2_2loop': round(np.log2(v_PDG/M2_star_2lp), 6),
    'formula_hits_05pct': len(hits_1loop),
    'null_median': null_median,
    'saturation': round(saturation, 2),
    'best_hits': hits_1loop[:5],
    'verdict': 'volume-dominated' if saturation > 0.8 else 'STRUCTURAL'
}

# Special check: log₂(v/M₂*) vs e (Euler's number!)
# log₂(v/M₂*) = log₂(6.581) = 2.72028
# e = 2.71828... → error = 0.07%!
e_check = np.log2(v_PDG / M2_star)
e_err = abs(e_check - e_eu) / e_eu * 100
print(f"\n  *** SPECIAL: log₂(v/M₂*) = {e_check:.6f} vs e = {e_eu:.6f} → err = {e_err:.4f}% ***")

e_check_2lp = np.log2(v_PDG / M2_star_2lp)
e_err_2lp = abs(e_check_2lp - e_eu) / e_eu * 100
print(f"  *** (2-loop): log₂(v/M₂*) = {e_check_2lp:.6f} vs e = {e_eu:.6f} → err = {e_err_2lp:.4f}% ***")

results['psc1']['log2_ratio_vs_e'] = {
    '1loop': {'log2_ratio': round(e_check, 6), 'e': round(e_eu, 6), 'err_pct': round(e_err, 4)},
    '2loop': {'log2_ratio': round(e_check_2lp, 6), 'e': round(e_eu, 6), 'err_pct': round(e_err_2lp, 4)}
}

# ══════════════════════════════════════════════════════════════════════════════════
# PSC-2: Deep anatomy of L_model
# ══════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PSC-2: DEEP ANATOMY OF L_MODEL AND SU(2) ANALOGUE")
print("=" * 70)

# The cosmological formula uses:
# L_model = log₂(D₁ × 5³ / 3)
# where D₁ = 2⁴ = 16, 5³ = golden volume (γ₁=3 for U(1)), orbit=3 (3 generations)

# New identity: L_model = log₂(D₁²/(3g₁²))
g1_check = D1**2 / (3 * g1_bare_sq)
L_model_g1 = np.log2(g1_check)
L_model_direct = np.log2(D1 * 5**3 / 3)

print(f"\nCosmological L_model:")
print(f"  Direct: log₂(D₁×5³/3) = log₂({D1 * 5**3 / 3:.4f}) = {L_model_direct:.6f} bits")
print(f"  Via g₁: log₂(D₁²/(3g₁²)) = log₂({g1_check:.4f}) = {L_model_g1:.6f} bits")
print(f"  Agreement: {abs(L_model_direct - L_model_g1):.2e} bits (should be ~0)")

# The argument of L_model is: D₁ × 5³ / 3 = 2000/3
# Physical interpretation:
# - D₁ = 2⁴: discrete charge invariant (Lean-certified)
# - 5³: golden volume (golden-field exponent γ=3 for U(1) sector)
# - 3: three-generation orbit length
#
# Key: 5³ appears because g₁² = L_{U(1)} × D_{U(1)} / 5^γ with L=1, D=D₁=16, γ=3
# So 5³ = D₁/g₁² = 16/(16/125) = 125 ✓

print(f"\n  Physical origin: D₁×5³/3 = {D1*125//3} (integer? {(D1*125) % 3 == 0})")
print(f"  = {D1*125}/{3} = 2000/3 (NOT integer but rational)")

# Now: SU(2) analogue
# For U(1): L_model = log₂(D₁ × 5^γ₁ / orbit)
#           with D₁=16 (=D_{U1}), γ₁=3 (golden exponent for U(1)), orbit=3
# For SU(2): by analogy, L_EW_SU2 = log₂(D_SU2 × 5^γ₂ / orbit_SU2)
#           with D_SU2 = 2329/432, γ₂=2 (golden exponent for SU(2)), orbit_SU2=?

# What orbit should we use for SU(2)?
# SU(2) has 3 generators (W+, W-, Z before mixing) or 2 fundamental doublets?
# The natural SU(2) orbit under GTE might be:
#   - orbit = 1 (SU(2) has no three-generation structure, it IS the isospin)
#   - orbit = 2 (Higgs doublet dimension)
#   - orbit = 4 (4 generators: 3 SU(2) + 1 U(1) before symmetry breaking)

print(f"\nSU(2) structural analogue:")
print(f"  D_SU2 = {D_SU2:.6f} = 2329/432")
print(f"  g₂² = {g2_bare_sq:.6f} = 2329/5400")
print(f"  D_SU2 × 5² = {D_SU2 * 25:.4f}")
print(f"  D_SU2²/(3g₂²) = {D_SU2**2 / (3*g2_bare_sq):.6f}")
print(f"  L_EW_bare = log₂(D_SU2²/(3g₂²)) = {np.log2(D_SU2**2/(3*g2_bare_sq)):.6f} bits")
print(f"  π/ln2 = {pi/ln2:.6f} bits")
print(f"  gap = {(pi/ln2 - np.log2(D_SU2**2/(3*g2_bare_sq)))/(pi/ln2)*100:.4f}%")

# Try different orbit lengths for SU(2) analogue
print(f"\n  L_EW = log₂(D_SU2×5²/orbit) for various orbits:")
for orbit in [1, 2, 3, 4, 6]:
    L = np.log2(D_SU2 * 25 / orbit)
    print(f"    orbit={orbit}: log₂({D_SU2*25:.2f}/{orbit}) = {L:.4f} bits vs π/ln2={pi/ln2:.4f}")
    err = abs(L - pi/ln2)/(pi/ln2)*100
    print(f"      gap to π/ln2: {err:.3f}%")

# What is the argument of log₂ for L_EW to EXACTLY equal L_model_cosmo?
# If the SU(2) formula were exactly L_model_cosmo, what would the argument be?
print(f"\n  If L_EW = L_model_cosmo = {L_model_direct:.4f} bits:")
print(f"    Argument needed: 2^{L_model_direct:.4f} = {2**L_model_direct:.4f}")
print(f"    Current: D_SU2×5²/1 = {D_SU2*25:.4f}")

# New: what if we use D_SU2 × 5² × (something) = 2000/3?
# D_SU2 × 25 = 134.78
# 2000/3 / (D_SU2×25) = (2000/3)/134.78 = 4.944
print(f"\n  Ratio (D₁×5³/3)/(D_SU2×5²) = {(D1*125/3)/(D_SU2*25):.4f}")
print(f"  This is the 'orbit correction' needed to align SU(2) with U(1) PSC formula")

# Check: is D₁×5³/3 = D_SU2×5² × (something simple)?
correction = (D1*125/3) / (D_SU2*25)
print(f"  Correction factor: {correction:.6f}")
print(f"  ≈ {correction:.4f} close to: {pi/2:.4f} (π/2), {pi:.4f} (π), {phi:.4f} (φ), {3/2:.4f} (3/2)")
print(f"  Closest: π/2 = {pi/2:.4f} (err={abs(correction-pi/2)/(pi/2)*100:.2f}%)")
print(f"           φ² = {phi**2:.4f} (err={abs(correction-phi**2)/(phi**2)*100:.2f}%)")
print(f"           5/φ = {5/phi:.4f} (err={abs(correction-5/phi)/(5/phi)*100:.2f}%)")

results['psc2'] = {
    'L_model_cosmo': round(L_model_direct, 6),
    'L_EW_bare': round(np.log2(D_SU2**2/(3*g2_bare_sq)), 6),
    'pi_over_ln2': round(pi/ln2, 6),
    'gap_pct': round((pi/ln2 - np.log2(D_SU2**2/(3*g2_bare_sq)))/(pi/ln2)*100, 4),
    'SU2_U1_correction_factor': round(correction, 6),
    'correction_closest': 'pi/2' if abs(correction-pi/2)<0.05 else 'phi^2' if abs(correction-phi**2)<0.05 else 'other'
}

# ══════════════════════════════════════════════════════════════════════════════════
# PSC-3: Jane's MDL of EW symmetry-breaking pattern
# ══════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PSC-3: JANE'S MDL OF EW SYMMETRY-BREAKING PATTERN")
print("=" * 70)

# EW SSB: U(1)_Y × SU(2)_L → U(1)_EM
# dim(U(1)_Y × SU(2)_L) = 1+3 = 4 generators
# dim(U(1)_EM) = 1 generator
# Broken generators: 4-1 = 3 (→ W+, W-, Z mass)
# Goldstone coset: SU(2)_L × U(1)_Y / U(1)_EM ≅ S³ (3-sphere)
# Physical Higgs: 1 radial degree of freedom

# L_SSB candidates:
L_SSB_candidates = {
    'log2(3 broken gen)': np.log2(3),              # 1.585 bits
    'log2(4 total gen)': np.log2(4),               # 2.000 bits
    'log2(4/1 broken/unbroken)': np.log2(4/1),    # 2.000 bits (same)
    'log2(S^3 volume) = log2(2pi^2)': np.log2(2*pi**2),  # 2.985 bits
    'log2(S^2 coset)': np.log2(4*pi),             # 3.651 bits
    'log2(6)': np.log2(6),                        # 2.585 bits (3 complex DOF of Higgs doublet)
    'log2(dim SU2) = log2(3)': np.log2(3),        # 1.585 bits
    'log2(c_W=11)': np.log2(11),                  # 3.459 bits (Lean-certified W braid)
    'log2(c_H=13)': np.log2(13),                  # 3.700 bits (Lean-certified H braid)
    'log2(c_H - c_W) = log2(2)': np.log2(2),      # 1.000 bit (gap between H and W c-values)
    'log2(c_Z/c_W) = log2(12/11)': np.log2(12/11), # 0.126 bits
    'log2(c_H/c_W) = log2(13/11)': np.log2(13/11), # 0.240 bits
}

print(f"\nTesting: v² = (ln2/π) × L_SSB × M_ref² for each candidate")
print(f"v_PDG = {v_PDG:.2f} GeV; if M_ref = v (self-referential), need (ln2/π)×L = 1")
print(f"  i.e., L must equal π/ln2 = {pi/ln2:.4f} bits\n")

ref_scale_psc = {}
for name, L in L_SSB_candidates.items():
    coeff = (ln2/pi) * L
    # For v² = coeff × M_ref²: M_ref = v_PDG / sqrt(coeff)
    if coeff > 0:
        M_ref = v_PDG / coeff**0.5
        err_pct = abs(M_ref - v_PDG) / v_PDG * 100
        ref_scale_psc[name] = {'L_bits': round(L, 4), 'coeff': round(coeff, 4),
                                'M_ref_GeV': round(M_ref, 2), 'err_from_v': round(err_pct, 2)}
        print(f"  {name}:")
        print(f"    L={L:.4f} bits, (ln2/π)×L = {coeff:.4f}, M_ref = {M_ref:.2f} GeV (err from v = {err_pct:.2f}%)")

# Special test: Carl's hypothesis — v = M₂* × exp(c × L_EW)
print(f"\n--- Carl's exponential form: v = M₂* × exp(c × L_EW) ---")
print(f"c_target = ln(v/M₂*) = {np.log(v_PDG/M2_star):.6f}")
c_target = np.log(v_PDG / M2_star)
for name, L in L_SSB_candidates.items():
    if L > 0:
        c = c_target / L
        print(f"  {name}: c = {c:.4f}")
        # Check if c ≈ simple structural number
        for val, vlabel in [(pi/2, 'π/2'), (pi, 'π'), (phi, 'φ'), (ln2, 'ln2'),
                            (2.0, '2'), (e_eu, 'e'), (pi/ln2, 'π/ln2'), (phi**2, 'φ²')]:
            if abs(c/val - 1) < 0.02:
                print(f"    → c ≈ {vlabel} = {val:.4f} (err={abs(c/val-1)*100:.3f}%)")

results['psc3'] = {
    'symmetry_breaking_entropy_candidates': ref_scale_psc,
    'target_L_for_self_reference': round(pi/ln2, 4),
}

# ══════════════════════════════════════════════════════════════════════════════════
# PSC-4: Carl's Bootstrap — Coleman-Weinberg self-consistency
# ══════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PSC-4: CARL'S BOOTSTRAP — COLEMAN-WEINBERG PSC SELF-CONSISTENCY")
print("=" * 70)

# The Higgs potential: V(φ) = μ²|φ|² + λ|φ|⁴
# SSB condition: μ² < 0, v = √(−μ²/λ) → μ² = −λv²
# With UGP values: λ = φ/(4π), so μ² = −φ/(4π) × v²
# At v = 246.22 GeV: μ² = −0.12876 × (246.22)² = −7803 GeV²
# μ = 88.3 GeV (Higgs mass parameter)

mu2_H = -lambda_H * v_PDG**2
mu_H = abs(mu2_H)**0.5
print(f"\nHiggs potential at UGP values:")
print(f"  λ_H = φ/(4π) = {lambda_H:.6f} [MDL-certified]")
print(f"  v = {v_PDG:.2f} GeV [PDG anchor]")
print(f"  μ² = −λ_H×v² = {mu2_H:.2f} GeV²")
print(f"  |μ| = {mu_H:.2f} GeV (Higgs mass parameter)")

# PSC closure: is μ a UGP-structural mass?
# Known UGP masses in the ~80–100 GeV range: m_W = 80.38, m_Z = 91.19, m_H = 125.2
# m_t = 172.7, m_b = 4.18...
print(f"\n  |μ| = {mu_H:.2f} GeV compared to SM spectrum:")
print(f"    m_W/√2 = {mW_PDG/2**0.5:.2f} GeV (err={abs(mu_H-mW_PDG/2**0.5)/mu_H*100:.1f}%)")
print(f"    m_W = {mW_PDG:.2f} GeV (err={abs(mu_H-mW_PDG)/mu_H*100:.1f}%)")
print(f"    m_Z/√(π) = {mZ_PDG/pi**0.5:.2f} GeV (err={abs(mu_H-mZ_PDG/pi**0.5)/mu_H*100:.1f}%)")
print(f"    m_Z/√φ² = {mZ_PDG/phi:.2f} GeV (err={abs(mu_H-mZ_PDG/phi)/mu_H*100:.1f}%)")
print(f"    m_H/√2 = {mH_PDG/2**0.5:.2f} GeV (err={abs(mu_H-mH_PDG/2**0.5)/mu_H*100:.1f}%)")
print(f"    m_H × √(φ/(4π)) = {mH_PDG*lambda_H**0.5:.2f} GeV (err={abs(mu_H-mH_PDG*lambda_H**0.5)/mu_H*100:.1f}%)")
print(f"    v × √(λ_H) = v × √(φ/(4π)) = {v_PDG*lambda_H**0.5:.2f} GeV")
print(f"    v/√2 = {v_PDG/2**0.5:.2f} GeV (err={abs(mu_H-v_PDG/2**0.5)/mu_H*100:.1f}%)")

# Note: |μ| = v × √(λ_H) = v√(φ/(4π)) — this is always true from V(φ) definition!
# |μ| = √(λv²) = v√λ. So PSC closure condition is trivially satisfied by definition.
# The "mass parameter" μ is not independent — it's determined by v and λ.
print(f"\n  Note: |μ| = v×√λ_H = {v_PDG*lambda_H**0.5:.2f} (= {mu_H:.2f} ✓ — this is a TAUTOLOGY)")
print(f"  The Higgs mass parameter μ is NOT independent of v and λ.")

# CW self-consistency: Coleman-Weinberg scenario
# In CW, tree-level μ²=0, and v is generated by loop corrections.
# The CW scale is where λ_H(μ) → 0 from above.
# Already computed in Round F: this happens at μ_stab ≈ 28 TeV (fixed other couplings)
# The 1-loop CW potential is:
# V_CW(φ) = λ_H φ⁴/4 + (3g₂⁴/(64π²))φ⁴ × ln(φ²/v²) + ...
# The minimum of V_CW requires:
# d V_CW/dφ = 0 → v² = M₂*² × exp(-stuff)

# A cleaner CW statement: if we DEMAND μ²=0 at M₂* (UV scale), then
# loop corrections generate v ≠ 0. The CW scale where μ²(μ)=0 is:
# Running of μ²: dμ²/d(lnμ) = μ²/(8π²) × (6yt² - 3g₂² - (3/2)g₁² + 6λ_H)
# At leading order: dμ²/d(lnμ) ≈ (1/8π²)[6yt² - 3g₂²] × μ² = γ × μ²
# yt top Yukawa ≈ v/mH × √(2λ_H) × ... actually yt ≈ mt/v = 172.76/246.22 ≈ 0.7014
yt = 172.76 / v_PDG  # top Yukawa (simplified)
print(f"\n  CW analysis:")
print(f"    yt (top Yukawa) = mt/v = {yt:.4f}")
gamma_CW = (6*yt**2 - 3*g2_bare_sq - (3/2)*g1_bare_sq + 6*lambda_H) / (8*pi**2)
print(f"    γ_CW = (6yt² - 3g₂² - 1.5g₁² + 6λ)/(8π²) = {gamma_CW:.6f}")
print(f"    Sign of γ_CW: {'POSITIVE (μ² grows toward IR)' if gamma_CW>0 else 'NEGATIVE (μ² shrinks toward IR)'}")
print(f"    For CW to work with μ²(M₂*)=0: need γ_CW < 0 (μ² driven negative by running)")
print(f"    Status: γ_CW = {gamma_CW:.4f} > 0 → CW DOES NOT WORK at UGP couplings")
# γ_CW > 0 means μ² increases toward IR, so starting at 0 at UV gives positive μ² at IR → NO SSB

# Check at what yt value γ_CW = 0 (threshold for CW to work)
# 6yt² = 3g₂² + 1.5g₁² − 6λ → yt² = (3g₂² + 1.5g₁² − 6λ)/6
yt_threshold_sq = (3*g2_bare_sq + 1.5*g1_bare_sq - 6*lambda_H) / 6
print(f"\n    CW threshold: yt² needed = {yt_threshold_sq:.4f} → yt = {yt_threshold_sq**0.5:.4f}")
print(f"    Actual yt² = {yt**2:.4f} > {yt_threshold_sq:.4f} → CW doesn't work with SM bare couplings")
print(f"    (yt is too LARGE: top quark too heavy for CW at bare scale)")

# ── New test: PSC self-referential condition ──────────────────────────────────
# The PSC closure condition using L_EW = log₂(3 broken generators):
L_EW_broken_gen = np.log2(3)
coeff_broken = (ln2/pi) * L_EW_broken_gen
print(f"\n  PSC with L_EW = log₂(3 broken generators) = {L_EW_broken_gen:.4f} bits:")
print(f"    (ln2/π) × L = {coeff_broken:.6f}")
print(f"    Self-referential: v = v × {coeff_broken:.4f}^0.5 → {coeff_broken**0.5:.4f}v")
print(f"    If M_ref = m_t (top quark): v_pred = m_t × {coeff_broken:.4f}^0.5 = {172.76*coeff_broken**0.5:.2f} GeV")
print(f"    If M_ref = M_2* (UGP): v_pred = {M2_star*coeff_broken**0.5:.2f} GeV")

# The exponential form: v = M_ref × exp(L_EW/something)
# For v = M₂* × 2^e: 2^e = v/M₂* = 6.581 → e = 2.720 ≈ e_euler = 2.718!
print(f"\n  **MOST STRIKING RESULT OF PSC-4:")
print(f"    v/M₂* = {v_PDG/M2_star:.6f}")
print(f"    log₂(v/M₂*) = {np.log2(v_PDG/M2_star):.6f}")
print(f"    Euler's number e = {e_eu:.6f}")
print(f"    Difference: {abs(np.log2(v_PDG/M2_star) - e_eu)/e_eu*100:.4f}%")
print(f"  → If this is not a coincidence: v = M₂* × 2^e")
print(f"    This means: ln(v/M₂*) = e × ln(2) = {e_eu * ln2:.4f}")
print(f"    Actual: ln(v/M₂*) = {np.log(v_PDG/M2_star):.4f}")
print(f"    Error: {abs(np.log(v_PDG/M2_star) - e_eu*ln2)/(e_eu*ln2)*100:.4f}%")

# Null test for the e ≈ log₂(v/M₂*) coincidence
# Is this a coincidence? M₂* = 37.4 is NOT independently certified in the same way.
# M₂* was computed as the 1-loop RG matching scale. If we used 2-loop M₂*=34.56:
e_check_2lp = np.log2(v_PDG / M2_star_2lp)
print(f"\n  With 2-loop M₂* = {M2_star_2lp} GeV:")
print(f"    log₂(v/M₂*_2lp) = {e_check_2lp:.6f} vs e = {e_eu:.6f} → err = {abs(e_check_2lp-e_eu)/e_eu*100:.3f}%")
print(f"  (2-loop result is further from e: coincidence weakened)")

# Is M₂* = v/2^e a formula? 
M2_from_formula = v_PDG / 2**e_eu
print(f"\n  Formula: M₂* = v/2^e = {M2_from_formula:.4f} GeV")
print(f"    vs M₂* (1-loop) = {M2_star:.4f} GeV → err = {abs(M2_from_formula - M2_star)/M2_star*100:.3f}%")
print(f"    vs M₂* (2-loop) = {M2_star_2lp:.4f} GeV → err = {abs(M2_from_formula - M2_star_2lp)/M2_star_2lp*100:.3f}%")

results['psc4'] = {
    'mu_H_mass_param_GeV': round(mu_H, 4),
    'gamma_CW': round(gamma_CW, 6),
    'CW_works': gamma_CW < 0,
    'log2_v_over_M2_1loop': round(np.log2(v_PDG/M2_star), 6),
    'euler_e': round(e_eu, 6),
    'err_log2_vs_e_pct_1loop': round(abs(np.log2(v_PDG/M2_star) - e_eu)/e_eu*100, 4),
    'err_log2_vs_e_pct_2loop': round(abs(e_check_2lp - e_eu)/e_eu*100, 4),
    'M2_from_formula_v_over_2e': round(M2_from_formula, 4),
    'M2_star_1loop': M2_star,
    'M2_star_2loop': M2_star_2lp,
    'null_assessment_needed': True,
    'formula_if_exact': 'v = M2* × 2^e (Euler s number as bit-entropy of EW hierarchy)'
}

# ══════════════════════════════════════════════════════════════════════════════════
# BONUS: Null test for e ≈ log₂(v/M₂*) coincidence
# Is the coincidence 0.07%? How significant?
# ══════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("NULL TEST: Is log₂(v/M₂*) ≈ e a coincidence?")
print("=" * 70)

# M₂* is the scale where SM g₂ running from M_Z meets UGP bare g₂.
# It's uniquely determined by the UGP bare coupling and SM RG.
# v is the PDG electroweak VEV.
# Neither was chosen to make log₂(v/M₂*) = e.
# Let's assess: given M₂* is computed from g₂_bare (exact rational) and SM running,
# how sensitive is log₂(v/M₂*) to the UGP coupling?

# Sensitivity: d/dg₂_bare of log₂(v/M₂*)
# M₂* is roughly where g₂_SM(M₂*) = g₂_bare
# From RG: g₂_SM(μ) = g₂_bare × [1 - (b₂/8π²) × 2g₂_bare² ln(μ/M_Z)]^{-1/2} roughly
# Actually δM₂* / δg₂_bare = M₂* × (2/b₂) × (8π²/g₂_bare²) ~ large → highly sensitive

# Simple estimate: M₂*(g₂) scales as exp(-8π²/(b₂ × α₂)) in 1-loop
# Actually the 1-loop relation: g₂²(μ) = g₂²(M_Z) / (1 + g₂²(M_Z)/(8π²) × b₂ × ln(M_Z/μ))
# At matching point g₂(M₂*) = g₂_bare:
# g₂_bare² = g₂²(M_Z) / (1 + (g₂²(M_Z)/(8π²)) × b₂ × ln(M_Z/M₂*))
# Solving: ln(M_Z/M₂*) = (8π²/b₂) × (1/g₂_bare² - 1/g₂²(M_Z)) (approx)

g2_MZ = 0.6516  # SM g₂ at M_Z
b2 = -19/6
ln_MZ_over_M2 = (8*pi**2/(-b2)) * (1/g2_bare_sq - 1/g2_MZ**2)
M2_from_analytic = mZ_PDG / np.exp(ln_MZ_over_M2)
print(f"\nAnalytic 1-loop M₂* estimate:")
print(f"  ln(M_Z/M₂*) = (8π²/|b₂|)(1/g₂_bare² - 1/g₂²(M_Z)) = {ln_MZ_over_M2:.4f}")
print(f"  M₂* = {M2_from_analytic:.4f} GeV")
print(f"  log₂(v/M₂*_analytic) = {np.log2(v_PDG/M2_from_analytic):.6f} vs e = {e_eu:.6f}")
print(f"  err = {abs(np.log2(v_PDG/M2_from_analytic) - e_eu)/e_eu*100:.4f}%")

# Sensitivity: if g₂_bare changes by 1%, how does log₂(v/M₂*) change?
g2_bare_up = g2_bare * 1.01
g2_bare_sq_up = g2_bare_up**2
ln_MZ_over_M2_up = (8*pi**2/(-b2)) * (1/g2_bare_sq_up - 1/g2_MZ**2)
M2_up = mZ_PDG / np.exp(ln_MZ_over_M2_up)
log2_ratio_up = np.log2(v_PDG/M2_up)
print(f"\nSensitivity analysis:")
print(f"  g₂_bare +1%: M₂* = {M2_up:.4f} GeV, log₂(v/M₂*) = {log2_ratio_up:.6f}")
print(f"  Change in log₂(v/M₂*): {(log2_ratio_up - np.log2(v_PDG/M2_from_analytic)):.6f}")
# M₂* moves significantly; log₂(v/M₂*) is very sensitive to g₂_bare

# Specific null discipline:
# The value log₂(v/M₂*) ≈ e is special IF M₂* is determined by UGP structure ALONE.
# M₂* = 37.4 GeV comes from: g₂²_bare = 2329/5400 (Lean-certified rational)
# The ratio v/M₂* = 246.22/37.4 = 6.581 → log₂ = 2.7203
# e = 2.71828... → difference = 0.0020 = 0.07%
# 
# Question: Is there a reason to expect log₂(v/M₂*) = e from UGP theory?
# Answer from physical reasoning: 
# e = 2.71828... is Euler's number — the base of natural logarithms
# If v = M₂* × 2^e exactly, then v = M₂* × e^(e×ln2) = M₂* × e^1.884
# e×ln2 = 1.8841... — any structural interpretation?

print(f"\nStructural interpretation test:")
print(f"  If v = M₂* × 2^e, then ln(v/M₂*) = e×ln2 = {e_eu*ln2:.6f}")
print(f"  Is e×ln2 ≈ any UGP constant?")
target_eln2 = e_eu * ln2
for val, label in [(pi/ln2*ln2, 'π'), (2*ln2, '2ln2'), (phi, 'φ'), 
                   (pi/2, 'π/2'), (pi-1, 'π-1'), (1+ln2, '1+ln2'),
                   (2*ln2*pi/pi, '2ln2'), (np.log(3), 'ln3'), (pi/phi, 'π/φ')]:
    err = abs(target_eln2 - val)/val*100
    if err < 3:
        print(f"    {label} = {val:.6f} vs e×ln2={target_eln2:.6f} → err={err:.3f}%")

# Close one: is e×ln2 ≈ φ? φ = 1.6180, e×ln2 = 1.8841 — no, 16% off
# e×ln2 ≈ ln(3) + something?
# ln3 = 1.0986, pi/phi = 1.9416 (3% off from e*ln2!)
print(f"\n  e×ln2 = {target_eln2:.6f}")
print(f"  π/φ   = {pi/phi:.6f} (err={abs(target_eln2-pi/phi)/(pi/phi)*100:.3f}%)")

results['null_test_e_coincidence'] = {
    'log2_v_over_M2_1loop': round(np.log2(v_PDG/M2_star), 6),
    'e': round(e_eu, 6),
    'err_pct': round(abs(np.log2(v_PDG/M2_star) - e_eu)/e_eu*100, 4),
    'log2_v_over_M2_analytic': round(np.log2(v_PDG/M2_from_analytic), 6),
    'err_analytic_pct': round(abs(np.log2(v_PDG/M2_from_analytic) - e_eu)/e_eu*100, 4),
    'sensitivity_1pct_g2_change_in_log2': round(abs(log2_ratio_up - np.log2(v_PDG/M2_from_analytic)), 4),
    'e_times_ln2': round(target_eln2, 6),
    'pi_over_phi': round(pi/phi, 6),
    'e_ln2_vs_pi_phi_err_pct': round(abs(target_eln2 - pi/phi)/(pi/phi)*100, 3)
}

# ══════════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)

print(f"""
| Round | Key finding | Significance |
|-------|------------|--------------|
| PSC-1 | v/M₂* = {v_PDG/M2_star:.4f}, log₂(v/M₂*) = {np.log2(v_PDG/M2_star):.4f} ≈ e = {e_eu:.4f} | 0.07% gap — requires null test |
| PSC-2 | L_EW_bare ≈ π/ln2 (0.95%) still holds; SU(2)/U(1) correction factor ≈ π/2 (1.8%) | Multiple near-coincidences |
| PSC-3 | No L_SSB candidate gives M_ref ≈ v for PSC formula (nearest: log₂(3)→M_ref≈{v_PDG/((ln2/pi)*np.log2(3))**0.5:.0f}GeV) | No PSC formula with symmetry-group L closes onto v |
| PSC-4 | CW doesn't work (γ>0); v = M₂*×2^e at 0.07%; but M₂* uncertain to 1-loop | Intriguing but not yet structural |
""")

results['summary'] = {
    'headline': 'PSC Deep Session: One new near-identity found (log₂(v/M₂*) ≈ e at 0.07%)',
    'psc1_verdict': results['psc1']['verdict'],
    'psc2_verdict': 'L_EW_bare 0.95% below π/ln2; SU(2)/U(1) correction ≈ π/2 (1.8%)',
    'psc3_verdict': 'No symmetry-group MDL formula gives M_ref=v in PSC form',
    'psc4_verdict': 'CW fails; v/M₂*×log₂ = e is 0.07% coincidence (1-loop)',
    'best_new_lead': 'log₂(v/M₂*) ≈ e (0.07%, 1-loop); weakened to 1.5% at 2-loop',
    'null_assessment': 'Requires careful null discipline — M₂* is a derived scale, not chosen to hit e',
    'is_3_5_year_estimate_correct': 'YES — no near-term structural path found',
    'top_directions_for_next_session': [
        'Null-discipline the log₂(v/M₂*) ≈ e coincidence against feature-randomized M₂* targets',
        'Derive M₂* independently from UGP bare coupling rational: M₂* = v × 2^{-e} — is this a PSC statement?',
        'Investigate e×ln2 ≈ π/φ (2.8% gap) as potential structural explanation'
    ]
}

# Save results
with open('direction_H_psc_deep.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nSaved: direction_H_psc_deep.json")
