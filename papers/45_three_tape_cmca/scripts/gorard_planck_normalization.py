"""
Gorard / Planck normalization: C_Gorard from Rule 110 and 8.5% residual analysis.

This script computes C_Gorard — the Ollivier-Ricci coarse-graining coefficient
for the three-tape CMCA — and derives the Planck-scale normalization hierarchy:

    gravity-EM gap = (M_Pl / m_kink)⁴ × C_Gorard  ≈  10^77.5

Physical inputs (GTE-certified):
  m_kink = (8/49) × m_τ  (kink mass from GTE orbit, CatAD, P38)
  m_τ = 1776.86 MeV      (tau lepton mass, PDG)
  M_Pl = 1.22 × 10^19 GeV  (Planck mass)
  κ_3D = 2.32            (three-tape Ollivier-Ricci curvature, CatA, EPIC_078)
  κ_GR_Planck = 8π × (m_kink/M_Pl)⁴  (GR normalization, derived)

Key algebraic identity:
  C_Gorard ≡ κ_3D / (8π)   [exact from the gap definition + GR normalization formula]

This shows C_Gorard is entirely determined by κ_3D (the measured Ricci curvature
of the CMCA graph). The 8.5% residual from 10^77.5 is equivalent to the gap between
κ_3D/(8π) and the target (10^77.5 / (M_Pl/m_kink)^4).

Mixed-dimension formula (best non-tautological form):
  C_mixed = (C_{d=2} + 3×C_{d=4}) / 4 = (1/8 + 3/12) / 4 = 3/32 = 0.09375
  (1.4% error from measured C_Gorard = 0.0925)
  Physical content: one temporal (1+1D, d_eff=2) + three spatial (3+1D, d_eff=4) tapes.

kappa_SD analytic bound from Rule 110:
  For a kink cell with causal-future concentration parameter c (fraction of mass
  propagating to same cell):  κ = 4/3 - c  (simple nearest-neighbor model)
  Measured κ_SD = 0.773 → c_kink = 4/3 - 0.773 = 0.560
  Attempting to derive c_kink = 0.56 from Rule 110 Z₇ transition table.

Expected outputs:
  C_Gorard = κ_3D/(8π) = 0.0923  (exact identity, CatA for κ_3D input)
  log10(gap) = 77.46  (vs target 77.5, 8.5% residual)
  Best analytic form: 3/32 = 0.09375 (1.4% error)
  κ_SD from Rule 110 kink: attempt derivation from transition table

References:
  LAB_NOTE_079_GORARD_COEFFICIENT.md (C_Gorard calculation and Convention 2 correction)
  research-sandbox/epic_079/gorard_coefficient_rule110.py (prior graduated version)
  research-sandbox/epic_078/three_tape_gorard_chain.py (κ_3D computation)
"""

import signal
import json
import sys
import time
import math
import numpy as np
from collections import defaultdict

TIMEOUT_SECONDS = 300


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s limit reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t_start = time.time()

print("=== GORARD / PLANCK NORMALIZATION ===\n")

# ─── 1. Physical parameters (GTE-certified) ─────────────────────────────────

M_TAU_MEV = 1776.86          # tau lepton mass [MeV], PDG 2022
M_KINK_MEV = (8.0 / 49.0) * M_TAU_MEV   # kink mass = (8/49)m_τ (CatAD, P38)
M_KINK_GEV = M_KINK_MEV / 1000.0        # convert to GeV
M_PL_GEV = 1.22e19           # Planck mass [GeV]

KAPPA_3D = 2.32              # three-tape Ollivier-Ricci curvature κ_3D (CatA, EPIC_078)
KAPPA_SD = KAPPA_3D / 3.0   # per-tape SD curvature κ_SD ≈ 0.773

print("Physical parameters:")
print(f"  m_τ            = {M_TAU_MEV:.2f} MeV  (PDG)")
print(f"  m_kink = (8/49)m_τ = {M_KINK_MEV:.2f} MeV = {M_KINK_GEV:.4f} GeV  (CatAD)")
print(f"  M_Pl           = {M_PL_GEV:.2e} GeV")
print(f"  κ_3D           = {KAPPA_3D}  (CatA, EPIC_078)")
print(f"  κ_SD = κ_3D/3  = {KAPPA_SD:.4f}  (per-tape)")

# ─── 2. GR normalization formula (derived) ──────────────────────────────────

ratio = M_PL_GEV / M_KINK_GEV
ratio4 = ratio ** 4

# Analytic derivation: κ_GR_Planck = 8π × (m_kink/M_Pl)⁴
# This comes from the Gorard formula: κ(x,y) ≈ (ε²/2(d+2)) × Ric(v,v) in d dimensions
# At the Planck scale for a single kink (source of curvature):
#   Ric_kink [Planck units] = 8π × (m_kink/M_Pl)²
#   cell size a_Pl = m_kink/M_Pl  [Planck units]
#   κ_GR_Planck = Ric_kink × a_Pl² = 8π × (m_kink/M_Pl)⁴
KAPPA_GR_PLANCK_DERIVED = 8.0 * math.pi * (M_KINK_GEV / M_PL_GEV) ** 4
KAPPA_GR_PLANCK_CATА = 8.01e-78   # CatA numerical value from EPIC_078

print(f"\nGR normalization:")
print(f"  κ_GR_Planck (derived) = 8π×(m_kink/M_Pl)⁴ = {KAPPA_GR_PLANCK_DERIVED:.4e}")
print(f"  κ_GR_Planck (CatA)    = {KAPPA_GR_PLANCK_CATА:.4e}  (EPIC_078)")
print(f"  Relative difference   = {abs(KAPPA_GR_PLANCK_DERIVED/KAPPA_GR_PLANCK_CATА - 1)*100:.2f}%")

# ─── 3. Algebraic identity: C_Gorard = κ_3D / (8π) ─────────────────────────

print(f"\n=== ALGEBRAIC IDENTITY ===")
print(f"""
Definition: gap ≡ κ_3D / κ_GR_Planck = (M_Pl/m_kink)⁴ × C_Gorard
→  C_Gorard = κ_3D / (κ_GR_Planck × (M_Pl/m_kink)⁴)

Substituting κ_GR_Planck = 8π × (m_kink/M_Pl)⁴:
→  C_Gorard = κ_3D / (8π × (m_kink/M_Pl)⁴ × (M_Pl/m_kink)⁴)
            = κ_3D / (8π × 1)
            = κ_3D / (8π)   ← algebraic identity, exact by definition
""")

C_GORARD_ALGEBRAIC = KAPPA_3D / (8.0 * math.pi)
print(f"  C_Gorard = κ_3D / (8π) = {KAPPA_3D} / {8*math.pi:.4f} = {C_GORARD_ALGEBRAIC:.6f}")

# ─── 4. Gap computation and 8.5% residual ───────────────────────────────────

gap_measured = KAPPA_3D / KAPPA_GR_PLANCK_CATА
gap_derived = KAPPA_3D / KAPPA_GR_PLANCK_DERIVED
log10_gap = math.log10(gap_measured)

C_GORARD_NUMERICAL = gap_measured / ratio4   # using CatA κ_GR_Planck
C_GORARD_FROM_FORMULA = KAPPA_3D / (8.0 * math.pi)  # algebraic identity

# Target: gap should equal 10^77.5 for exact normalization
TARGET_LOG10_GAP = 77.5
TARGET_GAP = 10.0 ** TARGET_LOG10_GAP
C_GORARD_TARGET = TARGET_GAP / ratio4   # what C_Gorard would need to be for exact match

residual_ratio = C_GORARD_NUMERICAL / C_GORARD_TARGET
residual_pct = (1.0 - residual_ratio) * 100.0

print(f"\nNormalization gap analysis:")
print(f"  M_Pl/m_kink = {ratio:.6e}")
print(f"  (M_Pl/m_kink)⁴ = {ratio4:.6e}")
print(f"  gap (measured) = κ_3D/κ_GR_Planck = {gap_measured:.4e}")
print(f"  log₁₀(gap) = {log10_gap:.4f}  (target: {TARGET_LOG10_GAP})")
print(f"  C_Gorard (numerical) = {C_GORARD_NUMERICAL:.6f}")
print(f"  C_Gorard (algebraic) = {C_GORARD_ALGEBRAIC:.6f}")
print(f"  C_Gorard (target for 10^77.5) = {C_GORARD_TARGET:.6f}")
print(f"  Residual = C_Gorard / C_target = {residual_ratio:.4f} → {residual_pct:.1f}% below target")

# ─── 5. Candidate analytic forms ────────────────────────────────────────────

C_measured = C_GORARD_NUMERICAL

# Mixed-dimension formula: 1 temporal tape (d=2) + 3 spatial tapes (d=4)
C_d2 = 1.0 / (2 * (2 + 2))   # = 1/8  (Gorard d=2 coefficient)
C_d4 = 1.0 / (2 * (4 + 2))   # = 1/12 (Gorard d=4 coefficient)
C_mixed = (1.0 * C_d2 + 3.0 * C_d4) / 4.0   # = 3/32

candidates = {
    "κ_3D/(8π) [algebraic identity]": KAPPA_3D / (8.0 * math.pi),
    "3/32 [mixed-dim formula]":       3.0 / 32.0,
    "(C_d2+3C_d4)/4":                 C_mixed,
    "1/11":                           1.0 / 11.0,
    "1/(2(d+2))_d=3":                 1.0 / 10.0,
    "1/(2(d+2))_d=4":                 1.0 / 12.0,
    "κ_SD/8":                         KAPPA_SD / 8.0,
    "3κ_SD/(8π) [kappa factored]":    3.0 * KAPPA_SD / (8.0 * math.pi),
}

print(f"\nCandidate analytic forms for C_Gorard = {C_measured:.4f}:")
print(f"{'Form':>38} {'Value':>10} {'Error%':>10}")
print("-" * 62)
for name, val in sorted(candidates.items(), key=lambda x: abs(x[1] - C_measured)):
    err = abs(val - C_measured) / C_measured * 100
    print(f"  {name:>38} {val:>10.5f} {err:>9.1f}%")

# ─── 6. Mixed-dimension formula derivation ──────────────────────────────────

print(f"""
Mixed-dimension formula derivation:
  Standard Gorard: κ(x,y) ≈ (ε²/2(d+2)) × Ric(v,v) → C_std(d) = 1/(2(d+2))
  Per-tape (1+1D, d_eff=2):     C_d2 = 1/(2×4) = 1/8  = {C_d2:.5f}
  Effective 3+1D (d_eff=4):     C_d4 = 1/(2×6) = 1/12 = {C_d4:.5f}
  Weighted average (1 time + 3 space tapes):
    C_mixed = (1×C_d2 + 3×C_d4) / 4 = ({C_d2:.4f} + 3×{C_d4:.4f}) / 4
            = {C_mixed:.5f} = 3/32
  Error vs measured: {abs(C_mixed-C_measured)/C_measured*100:.1f}%
  
  Note: 3/32 = (C_d2+3C_d4)/4 — these are equal:
    (1/8 + 3/12)/4 = (3/24 + 6/24)/4 = (9/24)/4 = 9/96 = 3/32 ✓
""")

# ─── 7. κ_SD analytic derivation from Rule 110 ──────────────────────────────

print("=== κ_SD ANALYTIC DERIVATION FROM GTE POLYNOMIAL ===")
print("""
Approach: Compute Ollivier-Ricci curvature for kink-ether edges in the CMCA graph.
  κ(x,y) = 1 - W₁(μ_x, μ_y) / d(x,y)
where μ_x is the distribution of causal future of cell x at the next step.

Simple nearest-neighbor model (cells at positions 0,1,2):
  Kink distribution:  [f, c, f] where c = kink concentration, f = (1-c)/2
  Ether distribution: [1/3, 1/3, 1/3]
  W₁ = 2|f - 1/3| = 2|(1-c)/2 - 1/3| = |1 - 3c/3 - 2/3| = |(1-3c+2)/3|...

Derivation: for c > 1/3 (kink more concentrated than ether):
  f = (1-c)/2 < 1/3
  W₁ = CDF_kink at 0: f = (1-c)/2
       CDF_ether at 0: 1/3
  |Δ at x=0| = 1/3 - (1-c)/2 = (2-3(1-c)) / 6 = (3c-1)/6  [for c>1/3]
  |Δ at x=1| = |2f+c - 2/3| = |(1-c)+c - 2/3| = |1 - 2/3| = ... 
  Actually W₁ = ∫|CDF_kink - CDF_ether|dx between consecutive atoms.
  
  CDF_kink(x=0⁺) = f = (1-c)/2
  CDF_ether(x=0⁺) = 1/3
  Contribution to W₁ from interval [0,1]: |(1-c)/2 - 1/3| × 1 = (3c-1)/6
  
  CDF_kink(x=1⁺) = f+c = 1-f = (1+c)/2
  CDF_ether(x=1⁺) = 2/3
  Contribution from interval [1,2]: |(1+c)/2 - 2/3| × 1 = |(3+3c-4)/6| = (3c-1)/6
  
  W₁ = 2 × (3c-1)/6 = (3c-1)/3

  κ_simple = 1 - W₁ = 1 - (3c-1)/3 = (3 - 3c + 1)/3 = (4-3c)/3

  Equivalently: κ = 4/3 - c

Measured κ_SD = 0.773 → c_kink = 4/3 - 0.773 = 0.560
""")

# Compute from the formula
c_kink_from_kappa = 4.0/3.0 - KAPPA_SD
kappa_from_formula = 4.0/3.0 - c_kink_from_kappa
print(f"  κ_SD measured = {KAPPA_SD:.4f}")
print(f"  c_kink = 4/3 - κ_SD = {c_kink_from_kappa:.4f}")
print(f"  Verification: κ = 4/3 - c = {kappa_from_formula:.4f} ✓")

# Attempt analytic c_kink from GTE polynomial transition table
print(f"\nAttempting to derive c_kink from GTE Z₇ polynomial transition structure...")

# For the CMCA: a kink at position x in state w=1 (w≠0)
# The next state at each position depends on (L, C, R) via p(L,C,R) mod 7
# For the simple kink configuration ...0,0,1,0,0... on ether background w=0:
# Positions:   x-2, x-1, x, x+1, x+2
# States:      0,   0,   1, 0,   0

kink_config_ether = {
    -2: 0, -1: 0, 0: 1, 1: 0, 2: 0
}

def gte_poly_z7(L: int, C: int, R: int) -> int:
    return (C + R - C * R - L * C * R) % 7

# Compute next-step values for the simple kink configuration
print(f"\n  Single-kink Rule on ether background (GTE Z₇ polynomial):")
print(f"  Config: ...0, 0, 1, 0, 0, ... (kink at position 0)")
print(f"  {'Pos':>5} {'L':>3} {'C':>3} {'R':>3} {'p(L,C,R)':>10} {'Status':>10}")
for pos in range(-2, 4):
    L = kink_config_ether.get(pos - 1, 0)
    C = kink_config_ether.get(pos, 0)
    R = kink_config_ether.get(pos + 1, 0)
    p_val = gte_poly_z7(L, C, R)
    status = "← kink" if p_val != 0 else "ether"
    print(f"  {pos:>5} {L:>3} {C:>3} {R:>3} {p_val:>10} {status:>10}")

# Causal future of the kink cell (position 0 at t=0):
# Cells that are non-zero at t=1 form the causal future
next_config = {}
for pos in range(-3, 5):
    L = kink_config_ether.get(pos - 1, 0)
    C = kink_config_ether.get(pos, 0)
    R = kink_config_ether.get(pos + 1, 0)
    next_config[pos] = gte_poly_z7(L, C, R)

kink_positions_t1 = {pos: val for pos, val in next_config.items() if val != 0}
print(f"\n  Non-zero cells at t=1: {kink_positions_t1}")

total_kink_weight = sum(kink_positions_t1.values())
if total_kink_weight > 0:
    kink_dist = {pos: val/total_kink_weight for pos, val in kink_positions_t1.items()}
else:
    kink_dist = {}

print(f"  Kink weight distribution (normalized): {kink_dist}")

# Check if the kink spreads and compute concentration
if 0 in kink_dist:
    c_kink_z7 = kink_dist[0]  # fraction at original position
    kappa_from_z7 = 4.0/3.0 - c_kink_z7 if c_kink_z7 > 1.0/3.0 else None
    print(f"  c_kink (Z₇ transition) = {c_kink_z7:.4f}")
    if kappa_from_z7:
        print(f"  κ from simple model = 4/3 - {c_kink_z7:.4f} = {kappa_from_z7:.4f}")
        print(f"  Measured κ_SD = {KAPPA_SD:.4f}  (diff: {abs(kappa_from_z7-KAPPA_SD):.4f})")

# Run 10 steps of Rule 110 (binary, for visualization of kink propagation)
print(f"\n  Rule 110 (binary) kink propagation for 5 steps:")
rule110 = {(L, C, R): ((110 >> (4*L + 2*C + R)) & 1)
           for L in range(2) for C in range(2) for R in range(2)}

state = [0] * 20
state[10] = 1  # kink at center
print(f"  t=0: {''.join('█' if x else '.' for x in state)}")
for t in range(1, 6):
    new_state = [0] * 20
    for i in range(1, 19):
        new_state[i] = rule110[(state[i-1], state[i], state[i+1])]
    state = new_state
    print(f"  t={t}: {''.join('█' if x else '.' for x in state)}")

# Analyze kink spread at t=5
total = sum(state)
if total > 0:
    center = sum(i * v for i, v in enumerate(state)) / total
    c_kink_binary = max(state) / total if total > 0 else 0
    print(f"  Binary Rule 110: {total} active cells at t=5, center-of-mass={center:.1f}")

# ─── 8. Path to CatAD ───────────────────────────────────────────────────────

print(f"""
=== PATH TO CatAD ===

Current status: C_Gorard = κ_3D/(8π) = {C_GORARD_ALGEBRAIC:.4f} [CatA, since κ_3D is CatA]

For C_Gorard to become CatAD, need either:
(a) Analytic derivation of κ_3D = κ_SD × 3 from first principles
    → requires kink concentration c_kink from Rule 110 Z₇ transition table
    → κ_SD = 4/3 - c_kink [simple model] or exact Ollivier-Ricci computation

(b) Show the 8.5% residual vanishes in the continuum limit:
    → C_Gorard(N_cells→∞) → C_Gorard_target = {C_GORARD_TARGET:.4f}
    → requires finite-size analysis of κ_3D(N_cells)

(c) Identify c_kink from the Z₇ GTE polynomial transition table:
    Simple kink: p(0,0,1) = 1, p(0,1,0) = 1, p(1,0,0) = 0
    → kink spreads to positions {{-1, 0}} at t+1
    → c_kink = 0.5 (equal weight) → κ = 4/3 - 0.5 = 0.833 ≠ 0.773

    Discrepancy (0.833 vs 0.773) means the actual kink is not a single Z₇ cell
    but a multi-cell cluster in the full CMCA simulation. The κ_SD = 0.773 is
    from the cluster dynamics (three_tape_gorard_chain.py, EPIC_078).
""")

# ─── 9. Summary table ────────────────────────────────────────────────────────

print(f"=== SUMMARY ===")
print(f"  m_kink = (8/49)m_τ = {M_KINK_MEV:.2f} MeV  [CatAD]")
print(f"  M_Pl/m_kink = {ratio:.4e}")
print(f"  κ_3D = {KAPPA_3D}  [CatA]")
print(f"  κ_GR_Planck = 8π(m_kink/M_Pl)⁴ = {KAPPA_GR_PLANCK_DERIVED:.4e}  [derived]")
print(f"  Gap = κ_3D/κ_GR_Planck = {gap_measured:.4e},  log₁₀(gap) = {log10_gap:.4f}")
print(f"  C_Gorard = κ_3D/(8π) = {C_GORARD_ALGEBRAIC:.5f}  [algebraic identity]")
print(f"  Target C_Gorard for 10^77.5 = {C_GORARD_TARGET:.5f}")
print(f"  Residual = {residual_ratio:.4f}  ({residual_pct:.1f}% below 10^77.5)")
print(f"  Best non-tautological form: 3/32 = {3/32:.5f}  (1.4% from measured)")
print(f"  κ_SD simple model → c_kink=0.5 → κ=0.833 ≠ 0.773  [cluster dynamics needed]")

# ─── 10. Save results ────────────────────────────────────────────────────────

elapsed = round(time.time() - t_start, 2)
out_path = "papers/45_three_tape_cmca/scripts/gorard_planck_normalization_results.json"

results = {
    "description": (
        "Gorard/Planck normalization: C_Gorard derivation, gap analysis, "
        "8.5% residual, and analytic formula candidates."
    ),
    "physical_inputs": {
        "m_tau_MeV": M_TAU_MEV,
        "m_kink_formula": "(8/49)*m_tau",
        "m_kink_MeV": round(M_KINK_MEV, 4),
        "m_kink_GeV": round(M_KINK_GEV, 6),
        "M_Pl_GeV": M_PL_GEV,
        "ratio_MPl_mkink": round(ratio, 6),
        "ratio_4th_power": float(f"{ratio4:.6e}"),
        "kappa_3D": KAPPA_3D,
        "kappa_SD": round(KAPPA_SD, 5),
        "kappa_GR_Planck_CatA": KAPPA_GR_PLANCK_CATА,
        "kappa_GR_Planck_derived": round(KAPPA_GR_PLANCK_DERIVED, 6),
        "kappa_GR_formula": "8pi * (m_kink/M_Pl)^4",
    },
    "algebraic_identity": {
        "formula": "C_Gorard = kappa_3D / (8*pi)  [exact algebraic identity from gap definition]",
        "derivation": (
            "gap = kappa_3D/kappa_GR_Planck = (M_Pl/m_kink)^4 * C_Gorard. "
            "Substituting kappa_GR_Planck = 8pi*(m_kink/M_Pl)^4 gives: "
            "C_Gorard = kappa_3D / (8pi). "
            "This is an exact identity — C_Gorard is entirely determined by kappa_3D."
        ),
        "C_Gorard_algebraic": round(C_GORARD_ALGEBRAIC, 6),
        "C_Gorard_numerical": round(C_GORARD_NUMERICAL, 6),
        "agreement_pct": round(abs(C_GORARD_ALGEBRAIC / C_GORARD_NUMERICAL - 1) * 100, 2),
    },
    "gap_analysis": {
        "gap_measured": float(f"{gap_measured:.6e}"),
        "log10_gap": round(log10_gap, 4),
        "target_log10_gap": TARGET_LOG10_GAP,
        "gap_pass": abs(log10_gap - TARGET_LOG10_GAP) < 0.2,
        "C_Gorard_for_exact_match": round(C_GORARD_TARGET, 6),
        "residual_ratio": round(residual_ratio, 4),
        "residual_pct_below_target": round(residual_pct, 2),
    },
    "analytic_forms": {
        "kappa_3D_over_8pi": {
            "value": round(KAPPA_3D / (8 * math.pi), 6),
            "error_pct": round(abs(KAPPA_3D / (8 * math.pi) - C_measured) / C_measured * 100, 2),
            "status": "Algebraic identity (tautological given kappa_GR formula)",
        },
        "3_over_32": {
            "value": 3.0 / 32.0,
            "error_pct": round(abs(3.0/32.0 - C_measured) / C_measured * 100, 2),
            "status": "Best non-tautological form; equals mixed-dim formula",
        },
        "mixed_dim_formula": {
            "value": round(C_mixed, 6),
            "formula": "(C_d2 + 3*C_d4)/4 = (1/8 + 3/12)/4 = 3/32",
            "error_pct": round(abs(C_mixed - C_measured) / C_measured * 100, 2),
            "physical_content": (
                "Gorard coefficient averaged over 1 temporal (d=2) and 3 spatial (d=4) tapes. "
                "Weights: 1 time dimension + 3 spatial dimensions = 4 total."
            ),
        },
        "gorard_d4_standard": {
            "value": round(1.0 / 12.0, 6),
            "error_pct": round(abs(1.0/12.0 - C_measured) / C_measured * 100, 2),
            "status": "Standard Gorard d=4; does not account for temporal dimension",
        },
    },
    "kappa_SD_analysis": {
        "kappa_SD_measured": round(KAPPA_SD, 5),
        "simple_model_formula": "kappa = 4/3 - c_kink (nearest-neighbor transport)",
        "c_kink_from_measurement": round(c_kink_from_kappa, 4),
        "kink_concentration_meaning": (
            "c_kink = 0.560: kink cell directs 56% of causal mass to itself, "
            "22% each to neighbors"
        ),
        "simple_Z7_kink": {
            "config": "...0, 0, 1, 0, 0, ...  (single kink on ether background)",
            "next_step_nonzero": {str(k): int(v) for k, v in kink_positions_t1.items()},
            "c_kink_simple": round(kink_dist.get(0, 0), 4) if kink_dist else None,
            "kappa_simple": round(4.0/3.0 - kink_dist.get(0, 0), 4) if kink_dist and 0 in kink_dist else None,
            "vs_measured": f"simple→{4.0/3.0-kink_dist.get(0,0):.3f} vs measured {KAPPA_SD:.3f}" if kink_dist else "N/A",
            "note": (
                "Simple 1-cell kink model gives κ=0.833 ≠ 0.773. "
                "Measured κ_SD=0.773 comes from multi-cell kink cluster dynamics "
                "in three_tape_gorard_chain.py (EPIC_078). "
                "Full derivation requires the cluster distribution, not single-cell."
            ),
        },
    },
    "confidence": "CatA",
    "cat_level_rationale": (
        "C_Gorard = kappa_3D/(8pi) is algebraically exact (CatAD structure) "
        "but CatA because kappa_3D=2.32 is measured not derived. "
        "Path to CatAD: derive kappa_3D analytically from Rule 110 Z₇ kink cluster dynamics. "
        "The 8.5% residual from 10^77.5 reflects the gap between kappa_3D=2.32 and "
        "the target value kappa_3D_target = 8pi * C_Gorard_target = {:.4f}.".format(
            8 * math.pi * C_GORARD_TARGET
        )
    ),
    "open_question_OQ_079_5_CGord": (
        "Derive kappa_SD analytically from the Rule 110 Z₇ kink cluster structure. "
        "Simple 1-cell model: kappa=0.833. Measured: 0.773. "
        "Gap explained by multi-cell cluster effects, needs three_tape_gorard_chain analysis."
    ),
    "elapsed_s": elapsed,
}

with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved → {out_path}")
print(f"Total elapsed: {elapsed:.1f}s")

signal.alarm(0)
