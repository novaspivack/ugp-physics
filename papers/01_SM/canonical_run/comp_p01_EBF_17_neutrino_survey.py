#!/usr/bin/env python3
"""
comp_p01_EBF_17_neutrino_survey.py
EPIC 11 — Round 1: Neutrino Mass Survey

GOAL: Systematic first-principles survey to identify which approach(es)
can predict the neutrino mass RATIOS without an external sum_mnu anchor.

The decisive test: can we predict Δm²₂₁ / Δm²₃₁ ≈ 0.0295 (NuFIT) structurally?

APPROACHES TESTED:
  A. Triple comparison: Braid Atlas vs. prime triples
     - UCL-based M_R estimation for each triple set
     - Which set is more structurally motivated?

  B. S3 overlap with Braid Atlas triples
     - cosine, dot-product, and S3-symmetrized variants
     - Does the Braid Atlas triple set do better than prime triples?

  C. N_c-based Koide analog for neutrinos
     - After EPIC 9: θ_lepton = 2/9 from N_c
     - Is there a neutrino Koide angle derivable from the seesaw?
     - If m_ν_g ~ m_D_g² / M_R_g, and M_R ~ E_GUT/N_c^k, what ratios arise?

  D. MFRR Landauer bound for M_R (seesaw scale)
     - EPIC 8 showed MFRR fails for charged masses (anti-correlation theorem)
     - But M_R is a MAJORANA scale — different physics
     - Test: if M_R_g = k_B T_Planck × log(N_GTE_g), does seesaw give right ratios?

  E. UCL m_ν direct (no seesaw)
     - Does the UCL predict neutrino masses directly from the triples?
     - (Expected MAP based on EPIC 8, but must verify)

  F. Ratio target analysis
     - Given the oscillation data, what M_R RATIOS are needed?
     - Work backwards: what GTE triple structure produces those M_R ratios?
"""

from __future__ import annotations
import math, json, hashlib
import numpy as np
from datetime import datetime, timezone
from fractions import Fraction

PI = math.pi
N_c = 3

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENTAL TARGETS
# ─────────────────────────────────────────────────────────────────────────────

# NuFIT-5.2 central values (normal ordering)
DM21_SQ = 7.42e-5   # eV² (solar)
DM31_SQ = 2.517e-3  # eV² (atmospheric, NH)
RATIO_TARGET = DM21_SQ / DM31_SQ   # ≈ 0.0295

# Current bounds
SUM_MNU_PLANCK = 0.12e3  # meV (upper bound)
SUM_MNU_ANCHOR = 60.0    # meV (used in P01)

print("=" * 72)
print("COMP-P01-EBF-17 — EPIC 11 Round 1: Neutrino Mass Survey")
print("=" * 72)
print(f"  Target: Δm²₂₁/Δm²₃₁ = {RATIO_TARGET:.5f}  (NuFIT-5.2 NH central)")
print(f"  Planck upper: Σmν < {SUM_MNU_PLANCK:.0f} meV")
print()

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH A: TRIPLE COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

print("─" * 72)
print("APPROACH A — Triple Comparison: Braid Atlas vs. Prime Triples")
print("─" * 72)

# Braid Atlas triples (from EPIC 11 overview)
braid_triples = [
    (1, 5, 823),      # ν_{e,R}
    (9, 11, 1023),    # ν_{μ,R}
    (5, 19, 65535),   # ν_{τ,R}
]

# Prime triples (used in P01 paper)
prime_triples = [
    (2, 5, 5),        # ν_{R,1}
    (7, 11, 13),      # ν_{R,2}
    (17, 19, 23),     # ν_{R,3}
]

# Left-handed triples (from P01)
nu_L_triples = [
    (1, 1, 823),
    (9, 1, 1023),
    (5, 1, 65535),
]

print(f"""
  Braid Atlas ν_R:   {braid_triples}
  Prime ν_R:         {prime_triples}
  ν_L (P01):         {nu_L_triples}
  
  Note: b-values match (5,11,19 for both sets).
  Braid Atlas has large c-values: 823, 1023=2^10-1, 65535=2^16-1
  The c=65535 in ν_{{τ,R}} is the SAME c as the tau lepton!
  
  Structural observations:
""")

# Check c-values
tau_c = 65535  # from tau lepton GTE triple
tau_nu_c = braid_triples[2][2]
print(f"  c(ν_{{τ,R}}) = {tau_nu_c} = c(τ lepton)? {'YES ← structural link!' if tau_nu_c == tau_c else 'NO'}")
print(f"  c(ν_{{μ,R}}) = {braid_triples[1][2]} = 2^10 - 1 = {2**10 - 1}  {'← ridge-1 !' if braid_triples[1][2] == 2**10-1 else ''}")
print(f"  c(ν_{{e,R}}) = {braid_triples[0][2]} = prime? {all(braid_triples[0][2] % i != 0 for i in range(2, int(braid_triples[0][2]**0.5)+1))}")

print(f"""
  The Braid Atlas triples share b-values with prime triples.
  The c-values in Braid Atlas encode the GTE structure:
    - 65535 = 2^16 - 1: the maximum c-value (full 16-bit), same as τ lepton
    - 1023  = 2^10 - 1: one less than 2^10 (ridge level n=10 gives 2^10=1024)
    - 823:  prime, appears as c in ν_{{e,L}} triple too
  
  The b-values {5,11,19} are all prime.
  
  STRUCTURAL QUESTION: Are the Braid Atlas triples "more correct" for seesaw?
  The c-values encode the cascade depth; larger c → deeper cascade → higher M_R.
""")

# Compare log(c) ratios — key for M_R hierarchy
print("  log(c) ratios (relevant for M_R hierarchy):")
for (label, triples) in [("Braid Atlas", braid_triples), ("Prime", prime_triples)]:
    log_c = [math.log(t[2]) for t in triples]
    ratios = [log_c[i+1] - log_c[i] for i in range(2)]
    print(f"    {label}: log c = {[f'{x:.3f}' for x in log_c]}")
    print(f"          Δlog c = {[f'{x:.3f}' for x in ratios]}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH B: S3 OVERLAP WITH BRAID ATLAS TRIPLES
# ─────────────────────────────────────────────────────────────────────────────

print("─" * 72)
print("APPROACH B — S3 Overlap Seesaw with Braid Atlas Triples")
print("─" * 72)

def overlap_cosine(t1, t2):
    t1, t2 = np.array(t1, float), np.array(t2, float)
    return float(np.dot(t1, t2) / (np.linalg.norm(t1) * np.linalg.norm(t2)))

def overlap_dot(t1, t2):
    t1, t2 = np.array(t1, float), np.array(t2, float)
    return float(np.dot(t1, t2))

def seesaw_from_overlaps(nu_L, nu_R, overlap_fn):
    """Type-I seesaw from GTE triple overlaps."""
    n = len(nu_L)
    # M_D[i,j] = overlap(nu_L[i], nu_R[j])
    M_D = np.array([[overlap_fn(nu_L[i], nu_R[j]) for j in range(n)] for i in range(n)])
    # M_R[i,j] = overlap(nu_R[i], nu_R[j])
    M_R = np.array([[overlap_fn(nu_R[i], nu_R[j]) for j in range(n)] for i in range(n)])
    try:
        M_R_inv = np.linalg.inv(M_R)
    except np.linalg.LinAlgError:
        return None, None, None
    M_eff = -M_D @ M_R_inv @ M_D.T
    eigenvalues = np.linalg.eigvalsh(M_eff)
    masses_sq = np.abs(eigenvalues)
    masses_sq_sorted = np.sort(masses_sq)
    return M_eff, masses_sq_sorted, M_D

# Test with both triple sets
for triple_label, nu_R_set in [("Braid Atlas", braid_triples), ("Prime", prime_triples)]:
    print(f"\n  ν_R = {triple_label} triples:")
    for overlap_label, overlap_fn in [("cosine", overlap_cosine), ("dot-product", overlap_dot)]:
        M_eff, m_sq, M_D = seesaw_from_overlaps(nu_L_triples, nu_R_set, overlap_fn)
        if m_sq is None or np.any(m_sq <= 0):
            print(f"    {overlap_label}: DEGENERATE/FAILED")
            continue
        if len(m_sq) >= 2:
            if m_sq[2] > 0 and m_sq[1] > 0 and m_sq[0] > 0:
                ratio_21 = (m_sq[1] - m_sq[0]) / m_sq[2]  # Δm²₂₁ / m²₃ ≈ Δm²₂₁/Δm²₃₁
                # Better: (m1, m2, m3)
                m = np.sqrt(m_sq)
                dm21_sq = m_sq[1] - m_sq[0]
                dm31_sq = m_sq[2] - m_sq[0]
                ratio = dm21_sq / dm31_sq if dm31_sq > 0 else float('inf')
                print(f"    {overlap_label}: Δm²₂₁/Δm²₃₁ = {ratio:.5f}  (target: {RATIO_TARGET:.5f})  "
                      f"ratio/target = {ratio/RATIO_TARGET:.2f}×")
            else:
                print(f"    {overlap_label}: non-positive eigenvalues")
        else:
            print(f"    {overlap_label}: insufficient eigenvalues")

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH C: N_c-BASED SEESAW ESTIMATE
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("APPROACH C — N_c-Based Seesaw: Structural M_R from N_c chain")
print("─" * 72)

print(f"""
  EPIC 9 result: all charged lepton structural constants from N_c = 3.
  Specifically: δ = 7, b₁ = 73, a_τ = 5, a_μ = 9, a_e = 1.
  
  Seesaw: m_ν_g = m_D_g² / M_R_g
  
  If M_D ~ m_lep (Yukawa coupling unification), then:
    m_ν_g ≈ m_lep_g² / M_R_g
  
  For the N_c formula to give neutrino RATIOS, we need M_R to have 
  specific generational structure.
  
  Approach: Use the c-values of the GTE triples to set M_R_g.
  The c-values encode the cascade depth; the UCL mass scale is:
    m_g ∝ Cf × m_e where Cf depends on the triple.
  
  For right-handed neutrinos with Braid Atlas triples,
  the "cascade depth" is proportional to log(c_g):
    log(c_e) = log(823) ≈ 6.71
    log(c_μ) = log(1023) ≈ 6.93
    log(c_τ) = log(65535) ≈ 11.09
""")

# M_R proportional to c_g (from GTE cascade depth)
c_vals_braid = [t[2] for t in braid_triples]
c_vals_prime = [t[2] for t in prime_triples]

# Charged lepton masses (MeV) for m_D estimate
m_lep = np.array([0.511, 105.66, 1776.86])  # e, μ, τ in MeV

for label, c_vals in [("Braid Atlas", c_vals_braid), ("Prime", c_vals_prime)]:
    # M_R ∝ c_g (or log c_g)
    M_R_prop_c    = np.array(c_vals, float)
    M_R_prop_logc = np.array([math.log(c) for c in c_vals])

    for mr_label, M_R in [("∝ c", M_R_prop_c), ("∝ log(c)", M_R_prop_logc)]:
        m_nu = m_lep**2 / M_R
        m_nu_norm = m_nu / m_nu[0]  # normalize to first generation
        if m_nu[2] > 0:
            dm21 = m_nu[1]**2 - m_nu[0]**2
            dm31 = m_nu[2]**2 - m_nu[0]**2
            ratio = dm21/dm31 if dm31 > 0 else float('inf')
            print(f"  {label}, M_R {mr_label}: Δm²₂₁/Δm²₃₁ = {ratio:.5f}  (target {RATIO_TARGET:.5f})  "
                  f"factor = {ratio/RATIO_TARGET:.2f}×")

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH D: MFRR LANDAUER BOUND FOR M_R
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("APPROACH D — MFRR Landauer Bound for M_R (Majorana Scale)")
print("─" * 72)

print("""
  MFRR Reflexive Landauer: the information content of a GTE state
  sets a minimum energy k_B T × log(N_states).
  
  For right-handed neutrinos, the "N_states" is the number of 
  distinct GTE orbit configurations — related to the triple's b-value 
  (orbit width) or c-value (orbit depth).
  
  The Landauer energy at the Planck temperature T_Planck = M_Pl/k_B
  sets M_R_g = M_Planck × f(triple_g).
  
  Candidate: M_R_g ∝ M_GUT × (b_g / b_max)^k
  where b_max = max(b) = 19 for the neutrino sector.
""")

M_Pl  = 1.22e28  # eV (Planck mass)
M_GUT = 2e25     # eV (GUT scale ~2×10^16 GeV = 2×10^25 eV)

b_vals = [t[1] for t in braid_triples]   # 5, 11, 19

print(f"  b-values: {b_vals}")
for power in [1, 2, 3]:
    b_arr = np.array(b_vals, float)
    M_R = M_GUT * (b_arr / b_arr[-1])**power  # normalize so gen 3 = M_GUT
    m_D = m_lep * 1e6  # convert to eV
    m_nu = m_D**2 / M_R  # eV
    if all(m > 0 for m in m_nu):
        dm21 = m_nu[1]**2 - m_nu[0]**2
        dm31 = m_nu[2]**2 - m_nu[0]**2
        ratio = dm21/dm31 if dm31 > 0 else float('inf')
        print(f"  M_R ∝ (b/b_max)^{power}: Δm²₂₁/Δm²₃₁ = {ratio:.5f}  factor = {ratio/RATIO_TARGET:.2f}×  "
              f"sum_mnu = {sum(m_nu)*1000:.1f} meV")

# Also try M_R proportional to b^2 × c (information content proxy)
print(f"\n  Composite M_R ∝ b² × log(c) (information content proxy):")
for label, triples in [("Braid", braid_triples), ("Prime", prime_triples)]:
    info_content = np.array([t[1]**2 * math.log(t[2]) for t in triples])
    M_R = M_GUT * info_content / info_content[-1]
    m_D = m_lep * 1e6  # eV
    m_nu = m_D**2 / M_R
    if all(m > 0 for m in m_nu):
        dm21 = m_nu[1]**2 - m_nu[0]**2
        dm31 = m_nu[2]**2 - m_nu[0]**2
        ratio = dm21/dm31 if dm31 > 0 else float('inf')
        print(f"  {label}: Δm²₂₁/Δm²₃₁ = {ratio:.5f}  factor = {ratio/RATIO_TARGET:.2f}×  "
              f"sum_mnu = {sum(m_nu)*1000:.1f} meV")

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH E: UCL DIRECT PREDICTION
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("APPROACH E — UCL Direct Prediction (no seesaw)")
print("─" * 72)

print("""
  The UCL maps GTE triples to masses via:
    m = k_gen × E_base × Cf(a,b,c,g)
  
  If we apply UCL directly to the neutrino triples (treating them like
  any other fermion), what masses do we get?
  
  This is expected to fail (neutrinos are fundamentally different from 
  charged fermions — they get mass via seesaw, not Yukawa), but we need
  to check to be thorough.
""")

# UCL parameters from EPIC 8
k_gen   = 1.5388    # φ·cos(π/10)
E_base  = 0.511     # keV (m_e)
delta   = 7         # mirror offset
b1      = 73        # lepton ladder

# Simple UCL approximation: m ~ E_base × Cf where Cf = exp(UCL polynomial in L,gen)
# Using the CR1 coefficients from neutrino_canonical.py
CR1 = {
    "const": 0.46628393930689865,
    "L":    -0.11840028502574501,
    "L2":    0.015298276550094339,
    "gen":  -1.3311566280619973,
    "gen2":  0.20254057938869213,
    "M":    -0.26443985830013417,
    "mu_a": -0.48403462203073427,
    "mu_b": -0.92493933577666199,
    "mu_c": -0.10926515575407812,
}

def ucl_cf(a, b, c, gen, mu_a=1, mu_b=1, mu_c=-1):
    """Evaluate UCL Cf from CR1 coefficients."""
    L = math.log(abs(b) / abs(c)) if abs(c) > 0 else 0
    M = mu_a * mu_b * mu_c
    log_cf = (CR1["const"] + CR1["L"]*L + CR1["L2"]*(L**2)
              + CR1["gen"]*gen + CR1["gen2"]*(gen**2)
              + CR1["M"]*M + CR1["mu_a"]*mu_a
              + CR1["mu_b"]*mu_b + CR1["mu_c"]*mu_c)
    return math.exp(log_cf)

m_e_keV = 0.511  # keV

print("  UCL direct prediction from Braid Atlas ν triples (using gen 1,2,3):")
nu_masses_ucl = []
for i, (a, b, c) in enumerate(braid_triples):
    gen = i + 1
    cf = ucl_cf(a, b, c, gen)
    m_pred = k_gen * m_e_keV * cf  # keV
    nu_masses_ucl.append(m_pred)
    print(f"    ν_{['e','μ','τ'][i]}: (a,b,c)=({a},{b},{c}) → Cf={cf:.4f} → m = {m_pred*1e6:.3f} eV")

if all(m > 0 for m in nu_masses_ucl):
    m_arr = np.array(nu_masses_ucl)
    dm21 = m_arr[1]**2 - m_arr[0]**2
    dm31 = m_arr[2]**2 - m_arr[0]**2
    ratio = dm21/dm31 if dm31 > 0 else float('inf')
    print(f"  Ratio Δm²₂₁/Δm²₃₁ = {ratio:.5f}  (target {RATIO_TARGET:.5f})")
    print(f"  Sum mν = {sum(m_arr)*1e6*1000:.3f} meV")
    print(f"  → UCL direct: {'within factor 3 of target' if 0.003<ratio<0.3 else 'significantly off target'}")

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH F: REVERSE ENGINEERING — WHAT M_R RATIOS ARE NEEDED?
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("APPROACH F — Reverse Engineering: Required M_R Ratios from Oscillation Data")
print("─" * 72)

print(f"""
  Given: Δm²₂₁ = {DM21_SQ:.3e} eV², Δm²₃₁ = {DM31_SQ:.3e} eV²
  
  For Type-I seesaw with m_D_g ~ m_lep_g (Yukawa unification):
    m_ν_g = m_D_g² / M_R_g  ⟹  M_R_g = m_D_g² / m_ν_g
    
  The mass-squared splitting ratios impose:
    Δm²₂₁ / Δm²₃₁ = (m_ν₂² - m_ν₁²) / (m_ν₃² - m_ν₁²) ≈ 0.0295
    
  From the anchored seesaw (sum = 60 meV, NH):
    m_ν₁ ≈ 1.1 meV, m_ν₂ ≈ 8.7 meV, m_ν₃ ≈ 50.2 meV
    
  Required M_R ratios (using m_D ~ m_lep):
""")

m_nu_anchored = np.array([1.1, 8.7, 50.2]) * 1e-3  # eV
m_D = m_lep * 1e6  # eV (m_lep in eV)
M_R_required = m_D**2 / m_nu_anchored  # eV

print(f"  M_R_e = {M_R_required[0]:.3e} eV = {M_R_required[0]*1e-9:.3e} GeV")
print(f"  M_R_μ = {M_R_required[1]:.3e} eV = {M_R_required[1]*1e-9:.3e} GeV")
print(f"  M_R_τ = {M_R_required[2]:.3e} eV = {M_R_required[2]*1e-9:.3e} GeV")
print()
print(f"  M_R ratios:")
print(f"    M_R_τ / M_R_e = {M_R_required[2]/M_R_required[0]:.2e}")
print(f"    M_R_τ / M_R_μ = {M_R_required[2]/M_R_required[1]:.2e}")
print(f"    M_R_μ / M_R_e = {M_R_required[1]/M_R_required[0]:.2e}")

# What GTE c-values would reproduce these M_R ratios?
print()
print("  Reconstructing GTE c-values from required M_R ratios:")
# If M_R ∝ c^k, then log M_R ∝ k × log c
# Solve for k: log(M_R_τ/M_R_e) / log(c_τ/c_e) = k
log_MR_ratio_tau_e = math.log(M_R_required[2]/M_R_required[0])
log_c_ratio_braid  = math.log(braid_triples[2][2]/braid_triples[0][2])
log_c_ratio_prime  = math.log(prime_triples[2][2]/prime_triples[0][2])

k_braid = log_MR_ratio_tau_e / log_c_ratio_braid
k_prime = log_MR_ratio_tau_e / log_c_ratio_prime

print(f"  If M_R ∝ c^k:")
print(f"    Braid Atlas: required k = {k_braid:.3f}")
print(f"    Prime:       required k = {k_prime:.3f}")
print(f"  k=1 would mean M_R linear in c. k=2 would mean M_R ∝ c².")
print()

# Test k=1 and k=2 for Braid Atlas
for k in [0.5, 1.0, 1.5, 2.0, k_braid]:
    c_arr = np.array([t[2] for t in braid_triples], float)
    M_R = M_GUT * (c_arr / c_arr[-1])**k
    m_nu = (m_D**2 / M_R)
    if all(m > 0 for m in m_nu):
        dm21 = m_nu[1]**2 - m_nu[0]**2
        dm31 = m_nu[2]**2 - m_nu[0]**2
        ratio = dm21/dm31 if dm31 > 0 else float('inf')
        sum_mnu = sum(m_nu)*1e3  # meV
        print(f"  Braid, M_R ∝ c^{k:.2f}: ratio = {ratio:.5f}  ({ratio/RATIO_TARGET:.2f}× target)  sum = {sum_mnu:.1f} meV")

# ─────────────────────────────────────────────────────────────────────────────
# SYNTHESIS
# ─────────────────────────────────────────────────────────────────────────────

print()
print("─" * 72)
print("SYNTHESIS — Round 1 Survey Results")
print("─" * 72)

print(f"""
  TARGET: Δm²₂₁/Δm²₃₁ = {RATIO_TARGET:.5f}

  APPROACH RESULTS:
  
  A. Triple comparison:
     - Braid Atlas c-values encode GTE structure (823, 1023=2^10-1, 65535=2^16-1)
     - Same c as ν_L triples; c(ν_{{τ,R}}) = c(τ lepton) = 65535 — structural link
     - Prime triples have much smaller c-values (5,13,23)
     → Braid Atlas is the structurally motivated choice
  
  B. S3 overlap with Braid Atlas:
     - Tests cosine and dot-product variants
     - (Results from computation above)
  
  C. N_c-based M_R ∝ c or log(c):
     - Large spread in Braid c-values makes M_R_τ >> M_R_e
     - Need specific power k to hit the ratio target
  
  D. MFRR / b-value:
     - M_R ∝ b^k gives different ratios depending on k
     - b-values {5,11,19} ~ arithmetic progression
  
  E. UCL direct:
     - Gives masses in some range, probably off
  
  F. Reverse engineering:
     - Required k for M_R ∝ c^k to reproduce oscillation ratios computed above
""")

print()
print(f"  STRUCTURAL KEY FINDING: c(ν_{{τ,R}}) = {braid_triples[2][2]} = c(τ lepton)")
print(f"  This suggests ν_{{τ,R}} and τ share the same cascade endpoint.")
print(f"  Physical meaning: both have the same GTE orbit size → same 'depth' in the GTE tree.")
print(f"  In seesaw: M_R_τ is set by the tau sector's cascade depth.")
print()
print(f"  MFRR RELEVANCE: The information content log(c_g) grows as:")
for i, t in enumerate(braid_triples):
    print(f"    gen {i+1}: log(c) = log({t[2]}) = {math.log(t[2]):.4f}")
print(f"  The jump from log(1023) to log(65535) is {math.log(65535)-math.log(1023):.4f}")
print(f"  = log(65535/1023) = log({65535/1023:.2f}) ≈ log(64) = {math.log(64):.4f}")
print(f"  = 6 × log(2) — a factor of 64 = 2^6 in cascade depth from gen 2 to gen 3")

# Save results
results = {
    "experiment_id": "COMP-P01-EBF-17",
    "epic": "EPIC_11_ROUND_1_SURVEY",
    "target_ratio": RATIO_TARGET,
    "braid_atlas_triples": braid_triples,
    "prime_triples": prime_triples,
    "key_structural_findings": [
        "c(nu_tau_R) = 65535 = c(tau lepton) — shared cascade depth",
        "c(nu_mu_R) = 1023 = 2^10-1 — one less than 2^10 ridge reference",
        "b-values {5,11,19} primes, same for both triple sets",
        "log(c) jump gen2→gen3: factor 64 = 2^6"
    ],
    "approach_summary": "See computation output for detailed results",
    "timestamp_utc": datetime.now(timezone.utc).isoformat()
}

with open("comp_p01_EBF_17_neutrino_survey.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults written to comp_p01_EBF_17_neutrino_survey.json")
