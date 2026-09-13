#!/usr/bin/env python3
"""
comp_p01_EBF_21_neutrino_29_9_structural_decomp.py

Structural decomposition audit for the 29/9 neutrino-sector exponent ranked against
QCDF strand bookkeeping at N_c = 3:
  strand_count = (N_c²−1)/4, mirror-offset δ = N_c + (N_c²−1)/2,
  lepton ladder b₁, Koide-phase θ_Koide = (N_c²−1)/(4 N_c²), and selected GUT auxiliary
  integers.

Enumerates decomposition candidates onto a reproducible algebraic landscape prior to any
single closed-form mechanism claim.

Additionally scores candidate absolute-scale formulas that yield sum_mν in [55, 120] meV.
"""

from __future__ import annotations
from fractions import Fraction
import math, itertools

# Core constants derived from rank-3 strand / mirror bookkeeping
N_c = 3
strand_count = (N_c**2 - 1) // 4  # = 2
step = (N_c**2 - 1) // 2          # = 4
delta = N_c + step                 # = 7 (mirror offset)
b1 = N_c**4 - 5 - N_c              # = 73 (lepton ladder; a_τ=5)
a_tau = (N_c**2 + 1) // 2          # = 5
a_mu = N_c**2                      # = 9
a_e = 1                            # = 1
a_top = N_c**4 - a_tau             # = 76
theta_Koide = Fraction(N_c**2 - 1, 4 * N_c**2)  # = 2/9
exponent = Fraction(29, 9)

print("=" * 72)
print("COMP-P01-EBF-21: structural decomposition landscape of 29/9")
print("=" * 72)

print(f"""
Core constants (all from N_c = {N_c}):
  N_c          = {N_c}
  strand_count = (N_c²-1)/4 = {strand_count}
  step         = (N_c²-1)/2 = {step}
  delta        = N_c + step = {delta}
  b_1 (lepton) = N_c⁴ - a_τ - N_c = {b1}
  a_e, a_τ, a_μ = {a_e}, {a_tau}, {a_mu}
  a_top        = N_c⁴ - a_τ = {a_top}
  θ_Koide      = {theta_Koide} = {float(theta_Koide):.6f}

TARGET: exponent = 29/9 = {float(exponent):.6f}
""")

# ─────────────────────────────────────────────────────────────────────────────
# PART A: Algebraic Decompositions of 29/9 in N_c and GTE constants
# ─────────────────────────────────────────────────────────────────────────────

print("─" * 72)
print("PART A — Algebraic decompositions of 29/9")
print("─" * 72)

decompositions = []

# D1: N_c + θ_Koide
f = Fraction(N_c, 1) + theta_Koide
decompositions.append(("D1: N_c + θ_Koide", f, "sum of 'large' integer + 'small' correction"))

# D2: (N_c³ + strand_count) / N_c²  
f = Fraction(N_c**3 + strand_count, N_c**2)
decompositions.append(("D2: (N_c³ + strand_count)/N_c²", f, "color volume + lepton strands / color area"))

# D3: 4 - δ/N_c²  (since 29 = 36 - 7 = 4N_c² - δ)
f = Fraction(4, 1) - Fraction(delta, N_c**2)
decompositions.append(("D3: 4 - δ/N_c²", f, "rank(SU5) minus mirror offset / color area"))

# D4: (4N_c² - δ)/N_c²
f = Fraction(4 * N_c**2 - delta, N_c**2)
decompositions.append(("D4: (4N_c² - δ)/N_c²", f, "equivalent to D3"))

# D5: (N_c+1) - δ/N_c²  = rank(SU5) - correction
f = Fraction(N_c + 1, 1) - Fraction(delta, N_c**2)
decompositions.append(("D5: rank(SU5) - δ/N_c²", f, "GUT rank minus δ/N_c² ratio"))

# D6: dim(SU(N_c))/N_c² + N_c (where dim(SU(N_c)) = N_c²-1 = 8)
f = Fraction(N_c**2 - 1, N_c**2) + Fraction(N_c, 1)
decompositions.append(("D6: dim(SU(N_c))/N_c² + N_c", f, "hmm: gives N_c + 8/9 = 35/9 NOT 29/9"))
# Note: dim(SU(N_c))/N_c² = 8/9 is 4·θ_Koide

# D7: (4N_c³-4+N_c²+3)/(4N_c²)  — expanded numerator test
# 4·27 - 4 + 9 + 3 = 108-4+12 = 116; 116/36 = 29/9 ✓
f = Fraction(4*N_c**3 + N_c**2 - 1, 4 * N_c**2)
decompositions.append(("D7: (4N_c³+N_c²-1)/(4N_c²)", f, "closed numerator form"))

# D8: N_c + strand_count/N_c² (identical to D1)
f = Fraction(N_c, 1) + Fraction(strand_count, N_c**2)
decompositions.append(("D8: N_c + strand_count/N_c²", f, "identical to D1 (since strand_count/N_c² = θ)"))

# D9: (N_c + 2)(N_c² - 1)/(4·(N_c²-2)) + const? Test γ_d connection (VV bookkeeping)
# γ_d = -5/14 = -(N_c+2)/(2(N_c²-2))
# |γ_d| × N_c² = 45/14 — no
# Test: 29/9 vs γ_d?
# γ_d for n_c=3 = -5/14. 29/9 / (-5/14) = -29·14/(9·5) = -406/45 = non-integer
decompositions.append(("D9: NO clean γ_d relation", Fraction(0,1), "29/9 and 5/14 are coprime: gcd(29·14, 9·5)=1"))

# D10: 29/9 as sum/diff of SU(5)-aligned VV coefficients α_d=13/9, β_d=-7/6, γ_d=-5/14
alpha_d, beta_d, gamma_d = Fraction(13,9), Fraction(-7,6), Fraction(-5,14)
f = alpha_d + Fraction(16, 9)  # = 13/9 + 16/9 = 29/9
decompositions.append(("D10: α_d + 16/9", f, "α_d=13/9 plus 16/9 (not obviously structural)"))

# D11: α_d × 29/13 — no
# D12: Check if 29/9 = (something with dim(16_SO(10)))
dim_16_SO10 = 16
dim_10_SO10 = 10
dim_45_SO10 = 45
dim_126_SO10 = 126
f = Fraction(dim_16_SO10, 9) + Fraction(N_c+1, N_c**2)   # 16/9 + 4/9 — wait that's 20/9
# Let me try: 29 vs SO(10) reps
# 29 isn't dim of any common rep. 2·10 + 9 = 29. 16 + 13 = 29. 45 - 16 = 29 — interesting! 
# But dim(45) - dim(16) = 29 — is this just coincidence?
dim_45_SU5 = 45
f_diff = Fraction(dim_45_SU5 - dim_16_SO10, N_c**2)
decompositions.append(("D11: (dim(45_SU5) - dim(16_SO10))/N_c²", f_diff, 
                       "dim difference of GJ Higgs minus SO(10) fermion rep, over color area"))

# Verify
print(f"  {'Name':<38} {'Value':<12} {'Match?':<10} {'Note'}")
print(f"  {'-'*100}")
for name, val, note in decompositions:
    is_match = "✓ 29/9" if val == Fraction(29,9) else f"✗ ({val})"
    print(f"  {name:<38} {str(val):<12} {is_match:<10} {note}")

# ─────────────────────────────────────────────────────────────────────────────
# PART B: Self-conjugate braid interpretation
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("PART B — Self-conjugate braid / Majorana state interpretation")
print("─" * 72)

print("""
A Majorana particle is self-conjugate: ψ = ψ^c. In the Braid Atlas:
- A Dirac state has OPPOSITE chirality twin (antiparticle ≠ particle)
- A Majorana state has SAME chirality as its antiparticle (particle = antiparticle)
- A self-conjugate braid has REDUCED degrees of freedom

For counting purposes:
  Dirac orbit volume:     V_Dirac(a,b,c) = orbital states ∝ b^k
  Majorana orbit volume:  V_Maj(a,b,c) = V_Dirac / 2 (self-conjugacy)
  but counts ~ (V_Dirac)² due to MAJORANA squared mass term

For the Majorana mass matrix (16 × 16 × 126̄ in SO(10)):
  m_Majorana ∝ (Yukawa)² × <126> = <126> × f(b)²

If for Dirac f(b) ∝ b^{p_Dirac}, then for Majorana seesaw output:
  m_ν = (m_Dirac)² / M_R ∝ (b^{p_Dirac})² / M_R(b) 
  
For p_Dirac = 29/18 (i.e. ½ × 29/9), the seesaw gives exactly b^{29/9}.

Key algebraic fact:
  29/18 = (N_c + θ_Koide)/2 = (3 + 2/9)/2 = 29/18
  
Can we derive p_Dirac = (N_c + θ)/2 for Majorana?
""")

p_dirac_majorana = exponent / 2
print(f"  Required p_Dirac for Majorana: 29/18 = {float(p_dirac_majorana):.5f}")
print(f"  That's N_c/2 + θ/2 = {N_c/2:.3f} + {float(theta_Koide)/2:.3f}")
print(f"  = {N_c/2 + float(theta_Koide)/2:.5f}")

# Also note: 29/18 is near φ = 1.618
phi = (1 + math.sqrt(5))/2
print(f"\n  Interesting: 29/18 = {float(p_dirac_majorana):.5f}")
print(f"  φ (golden ratio)      = {phi:.5f}")
print(f"  Difference: {phi - float(p_dirac_majorana):.5f} — close but NOT equal")
print(f"  29/18 / φ = {float(p_dirac_majorana)/phi:.5f} — not a simple ratio")

# ─────────────────────────────────────────────────────────────────────────────
# PART C: Absolute scale candidates
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("PART C — Absolute scale candidates (sum_mν calculation)")
print("─" * 72)

# Physical constants
v_H = 246.22e9     # eV
M_GUT_ref = 2e25   # eV (2×10^16 GeV)
M_GUT_best = 2.17e25  # prior absolute-scale calibration point

# Braid Atlas b-values
b_vals = [5, 11, 19]

# Compute sum b^{29/9}
sum_b_exp = sum(b**float(exponent) for b in b_vals)
print(f"  Σ b_g^(29/9) = {sum_b_exp:.4f}  (for b = {b_vals})")

# Given sum_mν target = 60 meV with M_R = M_GUT:
# sum_mν = E_D² × sum_b_exp / M_GUT
# → E_D² = 60e-3 × M_GUT / sum_b_exp
# → E_D = sqrt(...)

target_sum = 60e-3  # eV
E_D_required_refGUT = math.sqrt(target_sum * M_GUT_ref / sum_b_exp)
E_D_required_bestGUT = math.sqrt(target_sum * M_GUT_best / sum_b_exp)

print(f"  Required E_D for sum=60meV at M_GUT=2.0×10^16 GeV: {E_D_required_refGUT/1e9:.4f} GeV")
print(f"  Required E_D for sum=60meV at M_GUT=2.17×10^16 GeV: {E_D_required_bestGUT/1e9:.4f} GeV")

# Now enumerate candidate structural scales
print(f"\n  Candidate structural scales for E_D:")
candidates = [
    # (name, value in eV, structural reason)
    ("v_H / N_c³",                v_H / N_c**3,                  "N_c cubed; natural color suppression"),
    ("v_H / N_c^{N_c}",           v_H / N_c**N_c,                "same as above: N_c^N_c = N_c³"),
    ("v_H / 29",                  v_H / 29,                       "denominator of seesaw exponent numerator"),
    ("v_H / (4N_c² - δ)",         v_H / (4*N_c**2 - delta),      "= v_H/29 (explicit)"),
    ("v_H / (N_c³ + strand)",     v_H / (N_c**3 + strand_count), "= v_H/29 (alternative)"),
    ("v_H × θ_Koide / N_c",       v_H * float(theta_Koide) / N_c, "Koide phase scaling"),
    ("v_H / (N_c·δ)",             v_H / (N_c * delta),           "N_c times mirror offset"),
    ("v_H / (N_c² + δ + N_c)",    v_H / (N_c**2 + delta + N_c),  "= v_H/(9+7+3) = v_H/19"),
    ("v_H / b_1 · N_c²",          v_H / b1 * N_c**2,             "b1=73 (lepton ladder)"),
    ("v_H × 2 / (N_c²·4N_c)",     v_H * 2 / (N_c**2 * 4*N_c),    "= v_H·strand/(2·color cube)"),
    ("v_H / (dim(45_SU5)/5)",     v_H / (45/5),                  "v_H/9 — just v_H/N_c²"),
    ("v_H × rank(SU5) / N_c⁴",    v_H * (N_c+1) / N_c**4,        "4·v_H/81 — GUT rank over color fourth"),
]

print(f"  {'Scale':<40} {'E_D (GeV)':>12} {'sum_mν (meV)':>14} {'In [55,120]?'}")
print(f"  {'-'*80}")

best_in_range = None
for name, E_D, reason in candidates:
    sum_meV = E_D**2 * sum_b_exp / M_GUT_ref * 1000  # meV
    in_range = 55 <= sum_meV <= 120
    flag = "✓" if in_range else ""
    print(f"  {name:<40} {E_D/1e9:>10.4f}   {sum_meV:>12.2f}   {flag}")
    if in_range and (best_in_range is None or abs(sum_meV-60) < abs(best_in_range[2]-60)):
        best_in_range = (name, E_D, sum_meV, reason)

if best_in_range:
    print(f"\n  CLOSEST TO 60 meV: {best_in_range[0]}")
    print(f"    E_D = {best_in_range[1]/1e9:.4f} GeV")
    print(f"    sum_mν = {best_in_range[2]:.2f} meV")
    print(f"    Rationale: {best_in_range[3]}")

# ─────────────────────────────────────────────────────────────────────────────
# PART D: M_R structural candidates (the OTHER side of seesaw)
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("PART D — M_R structural candidates")
print("─" * 72)

print(f"""
Given: m_ν_g = M_D_g² / M_R_g
Target: m_ν_g ∝ b_g^{{29/9}} to match absolute-ratio bridge
Sub-target: sum_mν ≈ 60 meV

Two independent requirements on (M_D_g, M_R_g):
  (a) M_D_g² / M_R_g ∝ b_g^{{29/9}} (ratio match)
  (b) sum over g equals ~60 meV (scale match)

If M_D = y_ν × v_H (the natural Dirac coupling is O(1) × v_H),
then M_R_g = y_ν² v_H² / (k × b_g^{{-29/9}} × m_ν,scale)

For y_ν = 1 (natural value): M_R_g = v_H² / m_ν_g ~ (246 GeV)²/meV ~ 10^{14} GeV
For generation-dependent y_ν: the required M_R sits at 10^14-10^17 GeV.

The BRAID ATLAS c-values encode the cascade depth:
  c(ν_e,R)  = 823
  c(ν_μ,R)  = 1023 = 2^10 - 1
  c(ν_τ,R)  = 65535 = 2^16 - 1 = c(τ) [SHARED with tau lepton!]

If M_R_g ∝ c_g, then M_R ratios are tied to c-hierarchy.
If M_R_g ∝ c_g^{{-1}}, M_R_τ would be smallest (makes sense: heaviest Majorana partner gives lightest neutrino).

Actually: MFRR Reflexive Landauer says E ∝ k_B T × log(N_states).
  If N_states(g) = c_g (distinct cascade configurations), then
  M_R_g ∝ log(c_g) × M_Pl × (some factor)
""")

# Compute log(c) values
import math as m
c_vals = [823, 1023, 65535]
print(f"  log(c_g) for g=e,μ,τ: {[f'{m.log(c):.3f}' for c in c_vals]}")
print(f"  log(c_τ/c_μ) = log(65535/1023) = log(64.06) = {m.log(65535/1023):.4f}")
print(f"  6·log(2) = {6*m.log(2):.4f}  — cascade jump is exactly 2^6 between gen 2 and 3")

# ─────────────────────────────────────────────────────────────────────────────
# PART E: The N_c³ + strand_count decomposition deeper
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("PART E — Structural interpretation of N_c³ + strand_count")
print("─" * 72)

print(f"""
The exponent 29/9 has a clean decomposition:

  29/9 = (N_c³ + strand_count) / N_c²
       = (27 + 2) / 9
       = N_c + strand_count/N_c²
       = N_c + θ_Koide

Proposal: This counts "effective modes" per "color area":
  - N_c³ = {N_c**3}: color cube — the number of (color, color, color) contractions in
    a 3-fermion interaction (left, right, conjugate)
  - strand_count = {strand_count}: the number of SU(2) lepton doublet strands in the 
    braid atlas representation (directly topological)
  - N_c² = {N_c**2}: color area — the number of (color, anti-color) pairs = 
    dim(adjoint of U(N_c)) = dim(SU(N_c)) + 1

So 29/9 = [color-cube contractions + lepton strand count] / [color-antipair pairs]

If each Dirac coupling contributes 1/N_c² (normalization of SU(N_c) traces),
then the self-conjugate MAJORANA coupling effectively contributes 
N_c × N_c² = N_c³ color-cube contractions plus the lepton-strand couplings.

This gives the exponent N_c + strand_count/N_c² = 29/9.
""")

# Alternative decomposition as difference
print(f"Alternative: 29/9 = 4 - δ/N_c² = (N_c+1) - δ/N_c²")
print(f"  where N_c+1 = rank(SU(5))")
print(f"  and δ = 7 is the mirror offset from strand bookkeeping at N_c = 3")
print(f"  So: exponent = rank(GUT) - (mirror_offset/color_area)")
print(f"  Physical: full GUT rank minus correction for mirror degrees of freedom in color space")

# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────

import json
results = {
    "experiment_id": "COMP-P01-EBF-21",
    "epic": "EPIC_12_ROUND_1_STRUCTURAL_DECOMP",
    "target_exponent": str(exponent),
    "decompositions": [
        {"name": name, "value": str(val), "note": note}
        for name, val, note in decompositions
    ],
    "best_absolute_scale": {
        "name": best_in_range[0] if best_in_range else None,
        "E_D_GeV": float(best_in_range[1]/1e9) if best_in_range else None,
        "sum_mnu_meV": float(best_in_range[2]) if best_in_range else None,
    },
    "key_identities": {
        "29_eq_4Nc2_minus_delta": 4*N_c**2 - delta == 29,
        "29_eq_Nc3_plus_strand": N_c**3 + strand_count == 29,
        "exp_eq_Nc_plus_theta": str(Fraction(N_c, 1) + theta_Koide) == "29/9",
    }
}
with open("comp_p01_EBF_21_neutrino_29_9_structural_decomp.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults → comp_p01_EBF_21_neutrino_29_9_structural_decomp.json")
