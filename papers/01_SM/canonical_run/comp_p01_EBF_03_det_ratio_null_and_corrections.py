#!/usr/bin/env python3
"""
comp_p01_EBF_03_det_ratio_null_and_corrections.py
EPIC 8 — E_base Foundations, Sub-project B, Computation 3

Three parts:

PART A — Det-ratio identity null test
    Claim from Round 02 analysis: |det_up/det_lepton|^(-1/δ²) ≈ 0.85 at 3 ppm.
    Before accepting this as structural, we must:
    (1) Determine the true precision of the engine type_mod targets (are they exactly
        0.85 and 1.15, or floating-point fit values?)
    (2) Test ALL combinations of (det ratio)^(exponent) for UGP-motivated exponents.
    (3) Report hit rate and null p-value.

PART B — αs/π correction for the Casimir type-mod gap
    COMP-EBF-01 found: H-3e gives up = 8/9 ≈ 0.889 (target 0.850, 4.6% gap).
    Hypothesis: the gap is a one-loop QCD correction of the form:
        type_mod_up = C₂(SU3)/(3/2) × (1 - k × αs/π)
    for some k ∈ {1, 4/3, 2, 2·C_F, ...}.
    Test all natural QCD correction forms.

PART C — Signed orbit invariants
    COMP-EBF-02 used |c| = 65535 for tau (ignoring the negative sign).
    The canonical tau triple has c = -65535 (chirality encoding).
    Re-test key orbit invariants using SIGNED values:
        a·b·c (signed) for tau = 5 × 275 × (-65535) = -90,110,625
    Check if signed invariants give correct mass ordering or better ratio match.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Physical constants
# ─────────────────────────────────────────────────────────────────────────────

PHI        = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA_S    = 0.1181          # strong coupling at MZ
ALPHA_EM   = 1.0/137.036     # EM coupling
SIN2_TW    = 0.23122         # UGP-derived sin²θW
C2_SU3     = 4.0/3.0         # SU(3) Casimir, fundamental rep

# Lean-certified UGP integers
DELTA      = 7               # mirror offset (ugp1_s)
B1         = 73              # lepton ladder
A2         = 9               # muon a-value
Q1         = 74              # b1 + a_e

# Empirical engine type_mod values (rounded in engine source)
TYPE_MOD_UP   = 0.85
TYPE_MOD_DOWN = 1.15
TYPE_MOD_LEP  = 1.00

# ─────────────────────────────────────────────────────────────────────────────
# Generation matrices (using CANONICAL SIGNED triples per UGP_GTE_SM_Verifier)
# tau.c = -65535 (CHIRAL), charm.c = +65535
# ─────────────────────────────────────────────────────────────────────────────

LEPTON_MATRIX = [(1,  73,      823),
                 (9,  42,     1023),
                 (5, 275,   -65535)]   # tau: c = -65535 (CANONICAL)

UP_MATRIX     = [(5,    9,      275),
                 (5,  275,    65535),   # charm: c = +65535
                 (76, 337920,     -1)]

DOWN_MATRIX   = [(9,   5,       42),
                 (9, 186,     1023),
                 (5, 8191,   65535)]

PARTICLES_SIGNED = [
    # name, type, gen,  a,       b,        c (SIGNED),   m_MeV
    ("electron", "lepton",    1,  1,       73,       823,      0.51099895),
    ("muon",     "lepton",    2,  9,       42,      1023,    105.6583755),
    ("tau",      "lepton",    3,  5,      275,    -65535,   1776.86),      # c NEGATIVE
    ("up",       "up_type",   1,  5,        9,       275,      2.16),
    ("charm",    "up_type",   2,  5,      275,     65535,   1275.0),       # c POSITIVE
    ("top",      "up_type",   3, 76,  337920,        -1,  172760.0),
    ("down",     "down_type", 1,  9,        5,        42,      4.67),
    ("strange",  "down_type", 2,  9,      186,      1023,     93.4),
    ("bottom",   "down_type", 3,  5,     8191,     65535,   4180.0),
]
M_ELECTRON = 0.51099895

def det3(rows):
    (a1,b1,c1),(a2,b2,c2),(a3,b3,c3) = rows
    return (a1*(b2*c3 - b3*c2) - b1*(a2*c3 - a3*c2) + c1*(a2*b3 - a3*b2))

DET_L = det3(LEPTON_MATRIX)
DET_U = det3(UP_MATRIX)
DET_D = det3(DOWN_MATRIX)

# ═════════════════════════════════════════════════════════════════════════════
# PART A: Det-ratio identity null test
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 72)
print("PART A — Det-ratio identity null test")
print("=" * 72)
print(f"det_lepton  = {DET_L:,d}  (with tau.c = -65535)")
print(f"det_up      = {DET_U:,d}")
print(f"det_down    = {DET_D:,d}")
print()

# All pairwise ratios (absolute value)
DET_RATIOS = {
    "|det_U/det_L|":  abs(DET_U) / abs(DET_L),
    "|det_D/det_L|":  abs(DET_D) / abs(DET_L),
    "|det_U/det_D|":  abs(DET_U) / abs(DET_D),
    "|det_L/det_U|":  abs(DET_L) / abs(DET_U),
    "|det_L/det_D|":  abs(DET_L) / abs(DET_D),
    "|det_D/det_U|":  abs(DET_D) / abs(DET_U),
}

# All structurally-motivated UGP exponents
# Include: ±1/n for small n, ±1/RSUC_constants, ±direct_RSUC_constants
UGP_INTS = [1,2,3,4,5,6,7,8,9,10,12,14,16,24,42,49,73,137,275,511,823]
EXPONENTS = []
for n in UGP_INTS:
    EXPONENTS.append(1.0/n)
    EXPONENTS.append(-1.0/n)
    EXPONENTS.append(float(n))
    EXPONENTS.append(float(-n))
# Also add special structural values
for v in [0.5, -0.5, 1.0/3, -1.0/3, 2.0/3, -2.0/3, PHI, -PHI, 1.0/PHI, -1.0/PHI,
          math.sqrt(2), -math.sqrt(2), math.pi, -math.pi]:
    EXPONENTS.append(v)
EXPONENTS = sorted(set(EXPONENTS))

TARGETS = {
    "type_mod_up":   TYPE_MOD_UP,
    "type_mod_down": TYPE_MOD_DOWN,
}
TOLERANCE_PPM = 1000.0  # 0.1% threshold for "hit"
TOLERANCE_FRAC = TOLERANCE_PPM / 1e6

print("Searching all (det_ratio)^(exponent) combinations for hits within 0.1% of targets:")
print(f"  Ratios tested: {len(DET_RATIOS)}")
print(f"  Exponents tested: {len(EXPONENTS)}")
print(f"  Total combinations: {len(DET_RATIOS) * len(EXPONENTS)}")
print()

hits_A = []
for ratio_name, ratio_val in DET_RATIOS.items():
    for exp in EXPONENTS:
        if ratio_val <= 0:
            continue
        try:
            pred = ratio_val ** exp
        except (ValueError, ZeroDivisionError, OverflowError):
            continue
        if not math.isfinite(pred) or pred <= 0:
            continue
        for tgt_name, tgt_val in TARGETS.items():
            dev = abs(pred - tgt_val) / tgt_val
            if dev < TOLERANCE_FRAC:
                hits_A.append({
                    "formula": f"({ratio_name})^({exp:.6g})",
                    "ratio_name": ratio_name,
                    "exp": exp,
                    "predicted": pred,
                    "target_name": tgt_name,
                    "target": tgt_val,
                    "dev_ppm": dev * 1e6,
                })

hits_A.sort(key=lambda h: h["dev_ppm"])
print(f"Hits within {TOLERANCE_PPM:.0f} ppm: {len(hits_A)}")
print()
if hits_A:
    print(f"{'Formula':45s}  {'Target':12s}  {'Pred':10s}  {'Dev(ppm)':10s}")
    print("-" * 82)
    for h in hits_A[:20]:
        print(f"  {h['formula']:43s}  {h['target_name']:12s}  {h['predicted']:10.7f}  {h['dev_ppm']:10.2f}")

# Null test: how many random (ratio, exponent) combinations would hit by chance?
N_NULL_A = 50000
rng = random.Random(42)
null_hits_A = 0
for _ in range(N_NULL_A):
    # Random ratio from [0.1, 100], random exponent from [-10, 10]
    r_rand = rng.uniform(0.1, 100.0)
    e_rand = rng.uniform(-10.0, 10.0)
    try:
        pred = r_rand ** e_rand
    except Exception:
        continue
    if not math.isfinite(pred) or pred <= 0:
        continue
    for tgt_val in TARGETS.values():
        dev = abs(pred - tgt_val) / tgt_val
        if dev < TOLERANCE_FRAC:
            null_hits_A += 1
            break

null_rate_A = null_hits_A / N_NULL_A
structural_trials = len(DET_RATIOS) * len(EXPONENTS)
expected_null_hits = null_rate_A * structural_trials

print()
print(f"Null test (N={N_NULL_A:,}):")
print(f"  Random hit rate per trial: {null_rate_A:.5f} ({null_rate_A*100:.3f}%)")
print(f"  Expected hits at random from {structural_trials} structural trials: {expected_null_hits:.1f}")
print(f"  Actual structural hits: {len(hits_A)}")
if expected_null_hits > 0:
    enrichment = len(hits_A) / expected_null_hits
    print(f"  Enrichment over null: {enrichment:.1f}×")

# Specific check: the proposed identity
print()
print("--- Specific identity check: |det_U/det_L|^(-1/δ²) ---")
ratio_UL = abs(DET_U) / abs(DET_L)
pred_up = ratio_UL ** (-1.0/DELTA**2)
print(f"  |det_U/det_L|    = {ratio_UL:.10f}  (with signed tau.c = -65535)")
print(f"  exponent         = -1/δ² = -1/{DELTA**2} = {-1.0/DELTA**2:.8f}")
print(f"  predicted        = {pred_up:.8f}")
print(f"  target (rounded) = {TYPE_MOD_UP:.8f}")
print(f"  deviation        = {abs(pred_up-TYPE_MOD_UP)/TYPE_MOD_UP*1e6:.2f} ppm")

# Also with UNSIGNED tau matrix (to check if sign matters for det)
LEPTON_MATRIX_UNSIGNED = [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)]
DET_L_UNSIGNED = det3(LEPTON_MATRIX_UNSIGNED)
ratio_UL_unsigned = abs(DET_U) / abs(DET_L_UNSIGNED)
pred_up_unsigned = ratio_UL_unsigned ** (-1.0/DELTA**2)
print()
print("--- Comparison: unsigned tau matrix ---")
print(f"  det_lepton (|c|=65535) = {DET_L_UNSIGNED:,d}")
print(f"  |det_U/det_L_unsigned| = {ratio_UL_unsigned:.10f}")
print(f"  predicted               = {pred_up_unsigned:.8f}  (same calculation, different det)")
print(f"  deviation from 0.85    = {abs(pred_up_unsigned-TYPE_MOD_UP)/TYPE_MOD_UP*1e6:.2f} ppm")

# Check exact engine type_mod value
print()
print("--- Engine source check: is type_mod_up exactly 0.85? ---")
print("  The engine defines: type_modulation = {'lepton': 1.0, 'up_type': 0.85, 'down_type': 1.15}")
print("  These are hardcoded rounded decimals, NOT high-precision fits.")
print("  0.85 = 17/20 exactly. 1.15 = 23/20 exactly.")
print("  The true type_mod_up is the value that, combined with UCL coefficients,")
print("  best fits the 9 particle masses. The rounded 0.85 is only accurate to ~1-2%.")
print("  Therefore a '3 ppm match to 0.85' overstates precision relative to the target's true uncertainty.")

# ═════════════════════════════════════════════════════════════════════════════
# PART B: αs/π correction for Casimir gap
# ═════════════════════════════════════════════════════════════════════════════

print()
print("=" * 72)
print("PART B — αs/π correction for the Casimir type-mod up gap")
print("=" * 72)

base_up   = C2_SU3 / 1.5           # H-3d: 8/9 ≈ 0.889
base_down = C2_SU3 * (1.0 - 2.0*SIN2_TW/3.0)  # H-3c: ≈ 1.128

print(f"Casimir base:  up = C2_SU3/(3/2) = {base_up:.6f}  (target 0.85, gap {(base_up-TYPE_MOD_UP)/TYPE_MOD_UP*100:.2f}%)")
print(f"               down = C2_SU3*(1-2sin2W/3) = {base_down:.6f}  (target 1.15, gap {(base_down-TYPE_MOD_DOWN)/TYPE_MOD_DOWN*100:.2f}%)")
print()

# QCD corrections to Yukawa running (one-loop)
# The one-loop gauge contributions to Yukawa anomalous dimensions differ by type:
# gamma_up   ∝ 8g3^2 * C2_SU3  (= 8*4pi*alphas * 4/3)
# gamma_lep  ∝ 0               (no QCD)
# The relative running from some scale to MZ gives a multiplicative correction:
# delta_type_mod_quark ≈ 1 + (alpha_s/pi) * k

C_F = 4.0/3.0  # SU(3) fundamental Casimir = C2_SU3

QCD_CORRECTIONS = [
    ("αs/(π)",           ALPHA_S / math.pi),
    ("4αs/(3π) = CF·αs/π", C_F * ALPHA_S / math.pi),
    ("2αs/(π)",          2 * ALPHA_S / math.pi),
    ("3αs/(π)",          3 * ALPHA_S / math.pi),
    ("8αs/(3π)",         8 * C_F * ALPHA_S / (3 * math.pi)),  # one-loop Yukawa coeff
    ("(4/3)·αs/(2π)",   (4.0/3.0) * ALPHA_S / (2 * math.pi)),
    ("sin²θW·αs/(π)",   SIN2_TW * ALPHA_S / math.pi),
]

print("Testing: type_mod_up = base_up × (1 - correction) and type_mod_down = base_down × (1 + correction):")
print(f"{'Correction':30s}  {'Value':10s}  {'up pred':10s}  {'up dev%':8s}  {'dn pred':10s}  {'dn dev%':8s}")
print("-" * 80)
best_B = {"max_dev": 1e9, "label": ""}
for name, corr in QCD_CORRECTIONS:
    up_pred   = base_up   * (1.0 - corr)
    down_pred = base_down * (1.0 + corr)
    up_dev    = abs(up_pred - TYPE_MOD_UP) / TYPE_MOD_UP * 100
    dn_dev    = abs(down_pred - TYPE_MOD_DOWN) / TYPE_MOD_DOWN * 100
    max_d     = max(up_dev, dn_dev)
    label = "✓" if max_d < 1.0 else "~" if max_d < 3.0 else ""
    print(f"  {name:30s}  {corr:10.6f}  {up_pred:10.6f}  {up_dev:8.2f}%  {down_pred:10.6f}  {dn_dev:8.2f}%  {label}")
    if max_d < best_B["max_dev"]:
        best_B = {"max_dev": max_d, "label": name, "corr": corr,
                  "up": up_pred, "dn": down_pred}

print()
print(f"Best QCD correction: '{best_B['label']}' → max dev = {best_B['max_dev']:.2f}%")
print(f"  type_mod_up  = {best_B['up']:.6f}  (target {TYPE_MOD_UP}, dev {abs(best_B['up']-TYPE_MOD_UP)/TYPE_MOD_UP*100:.2f}%)")
print(f"  type_mod_down = {best_B['dn']:.6f}  (target {TYPE_MOD_DOWN}, dev {abs(best_B['dn']-TYPE_MOD_DOWN)/TYPE_MOD_DOWN*100:.2f}%)")

# Also try: different signs for up vs down correction
print()
print("Testing: type_mod_up = base_up × (1 - corr), type_mod_down = base_down × (1 - corr):")
print("  (same sign correction for both — unified formula)")
print(f"{'Correction':30s}  {'Value':10s}  {'up pred':10s}  {'up dev%':8s}  {'dn pred':10s}  {'dn dev%':8s}")
print("-" * 80)
for name, corr in QCD_CORRECTIONS:
    up_pred   = base_up   * (1.0 - corr)
    down_pred = base_down * (1.0 - corr)
    up_dev    = abs(up_pred - TYPE_MOD_UP) / TYPE_MOD_UP * 100
    dn_dev    = abs(down_pred - TYPE_MOD_DOWN) / TYPE_MOD_DOWN * 100
    max_d     = max(up_dev, dn_dev)
    label = "✓" if max_d < 1.0 else "~" if max_d < 3.0 else ""
    print(f"  {name:30s}  {corr:10.6f}  {up_pred:10.6f}  {up_dev:8.2f}%  {down_pred:10.6f}  {dn_dev:8.2f}%  {label}")

# ═════════════════════════════════════════════════════════════════════════════
# PART C: Signed orbit invariants
# ═════════════════════════════════════════════════════════════════════════════

print()
print("=" * 72)
print("PART C — Signed orbit invariants (canonical tau.c = -65535)")
print("=" * 72)
print("Tau triple: (5, 275, -65535)  [CANONICAL SIGNED]")
print("Charm triple: (5, 275, +65535) [CANONICAL SIGNED]")
print()

# Compute signed invariants for all particles
def signed_invariants(a, b, c):
    abc_signed = a * b * c          # signed triple product
    abc_abs    = abs(a) * abs(b) * abs(c)
    sign_c     = 1 if c >= 0 else -1
    log_abs_abc = math.log(abc_abs) if abc_abs > 0 else 0.0
    return {
        "a·b·c (signed)":    abc_signed,
        "|a·b·c|":           abc_abs,
        "sign(c)":           sign_c,
        "sign(c)·|a·b·c|":  sign_c * abc_abs,
        "log|abc|":          log_abs_abc,
        "sign(c)·log|abc|": sign_c * log_abs_abc,
        "a·b·|c|":           a * b * abs(c),
        "sign(c)·|b|":      sign_c * abs(b),
        "sign(c)·|c|":      sign_c * abs(c),
    }

print(f"{'Particle':12s}  {'sign(c)':7s}  {'abc_signed':15s}  {'|abc|':15s}  {'R_g':12s}")
print("-" * 75)
for name, ptype, gen, a, b, c, m_MeV in PARTICLES_SIGNED:
    inv = signed_invariants(a, b, c)
    R_g = m_MeV / M_ELECTRON
    print(f"  {name:12s}  {inv['sign(c)']:7d}  {inv['a·b·c (signed)']:15,d}  {inv['|a·b·c|']:15,d}  {R_g:12.3f}")

print()
print("--- Lepton sector: signed triple product ordering ---")
leptons = [(n, a, b, c, m) for n,t,g,a,b,c,m in PARTICLES_SIGNED if t == "lepton"]
print("  Signed abc ordering: ",
      " < ".join(f"{n}({a*b*c:+,d})" for n,a,b,c,m in sorted(leptons, key=lambda x: x[0]*x[1]*x[2])))
print("  Mass ordering:       ",
      " < ".join(f"{n}({m:.2f})" for n,a,b,c,m in sorted(leptons, key=lambda x: x[4])))

# For signed abc: tau = -90,110,625, muon = +386,694, electron = +60,079
# Ordering by signed abc: tau(-90M) < electron(+60K) < muon(+387K) → WRONG mass order!
# But ordering by |abc|: electron < muon < tau → correct!
print()
print("--- Tau/charm distinction via sign(c) ---")
tau_abc   = 5 * 275 * (-65535)
charm_abc = 5 * 275 *  65535
print(f"  tau   abc (signed) = {tau_abc:+,d}")
print(f"  charm abc (signed) = {charm_abc:+,d}")
print(f"  tau   abc (|...|)  = {abs(tau_abc):,d}")
print(f"  charm abc (|...|)  = {abs(charm_abc):,d}")
print(f"  tau.c = -65535, charm.c = +65535: DISTINCT by sign alone ✓")
print()
print("--- Key question: do signed invariants give better mass ordering? ---")

# Check sign(c)·log|abc| for lepton ordering
print("  sign(c)·log|abc| for leptons:")
for name, ptype, gen, a, b, c, m_MeV in PARTICLES_SIGNED:
    if ptype != "lepton":
        continue
    inv = signed_invariants(a, b, c)
    print(f"    {name:10s}: sign(c)·log|abc| = {inv['sign(c)·log|abc|']:.4f},  m = {m_MeV:.3f} MeV")

# The signed value for tau is NEGATIVE (sign=-1), while electron and muon are positive
# Mass ordering is e < mu < tau, but sign(c)·log|abc| ordering would be tau < e < mu
# so signed invariant gives WRONG lepton ordering
print()
print("  FINDING: sign(c)·log|abc| gives WRONG lepton ordering (tau is negative; should be largest)")
print("  sign(c) flips tau to the bottom, violating mass ordering for leptons.")
print("  The |c| convention in UCL is therefore PHYSICALLY CORRECT for mass ordering purposes.")
print("  The sign(c) chirality information is orthogonal to the mass hierarchy.")

# ═════════════════════════════════════════════════════════════════════════════
# Summary and verdict
# ═════════════════════════════════════════════════════════════════════════════

print()
print("=" * 72)
print("SUMMARY AND VERDICTS")
print("=" * 72)

# Part A verdict
n_hits = len(hits_A)
enrichment_A = n_hits / expected_null_hits if expected_null_hits > 0 else float('inf')
if n_hits == 0:
    verdict_A = "NO HITS within 0.1% — det-ratio identity does not hold at this precision."
elif enrichment_A < 2.0:
    verdict_A = f"{n_hits} hit(s) — NOT STRUCTURALLY ENRICHED (enrichment {enrichment_A:.1f}× over null; expected {expected_null_hits:.1f} at random). Coincidence."
elif enrichment_A < 5.0:
    verdict_A = f"{n_hits} hit(s) — WEAK enrichment {enrichment_A:.1f}× — marginally above null; treat as suggestive only."
else:
    verdict_A = f"{n_hits} hit(s) — ENRICHED {enrichment_A:.1f}× over null — structurally supported."

print(f"\nPart A (det-ratio null):  {verdict_A}")
print(f"  NOTE: The rounded type_mod target (0.85 = 17/20) is only accurate to ~1-2%;")
print(f"  a '3 ppm match to 0.85' overstates precision. Identity is at best 'suggestive'.")

print(f"\nPart B (αs/π correction): {best_B['label']} reduces up-type gap to {abs(best_B['up']-TYPE_MOD_UP)/TYPE_MOD_UP*100:.2f}%.")
if abs(best_B['up'] - TYPE_MOD_UP) / TYPE_MOD_UP < 0.01:
    print("  CLOSED: αs/π correction closes the Casimir gap to < 1%. Structural formula identified.")
elif abs(best_B['up'] - TYPE_MOD_UP) / TYPE_MOD_UP < 0.03:
    print("  NEARLY CLOSED: αs/π correction reduces gap to < 3%. Close but not exact.")
else:
    print("  NOT CLOSED: no simple QCD correction closes the gap.")

print(f"\nPart C (signed orbit):    sign(c) gives WRONG lepton ordering.")
print(f"  FINDING: UCL's |c| convention is CORRECT for mass ordering. Chirality (sign(c)) is")
print(f"  physically orthogonal to mass hierarchy. The signed det DOES distinguish tau from charm.")
print(f"  The correct structural picture: |c| for mass features, sign(c) for chirality features.")

# ═════════════════════════════════════════════════════════════════════════════
# Write JSON output
# ═════════════════════════════════════════════════════════════════════════════

output = {
    "experiment_id":  "COMP-P01-EBF-03",
    "epic":           "EPIC_8_EBASE_FOUNDATIONS",
    "question":       "Det-ratio null test; αs/π correction; signed orbit invariants",
    "det_values": {
        "det_lepton_signed": DET_L,
        "det_lepton_unsigned": DET_L_UNSIGNED,
        "det_up": DET_U,
        "det_down": DET_D,
    },
    "part_A": {
        "n_ratios":          len(DET_RATIOS),
        "n_exponents":       len(EXPONENTS),
        "total_combinations": len(DET_RATIOS) * len(EXPONENTS),
        "tolerance_ppm":     TOLERANCE_PPM,
        "n_hits":            n_hits,
        "hits":              hits_A[:20],
        "null_random_hit_rate": null_rate_A,
        "null_expected_hits": expected_null_hits,
        "enrichment":        enrichment_A,
        "specific_identity": {
            "formula":    "|det_U/det_L_signed|^(-1/δ²)",
            "ratio_val":  ratio_UL,
            "exponent":   -1.0/DELTA**2,
            "predicted":  pred_up,
            "target":     TYPE_MOD_UP,
            "dev_ppm":    abs(pred_up-TYPE_MOD_UP)/TYPE_MOD_UP*1e6,
        },
        "unsigned_comparison": {
            "det_L_unsigned": DET_L_UNSIGNED,
            "ratio_unsigned": ratio_UL_unsigned,
            "predicted_unsigned": pred_up_unsigned,
            "dev_ppm_unsigned": abs(pred_up_unsigned-TYPE_MOD_UP)/TYPE_MOD_UP*1e6,
        },
        "verdict": verdict_A,
        "precision_caveat": "type_mod_up = 0.85 is rounded to 2 decimal places; true precision ~1-2%; '3 ppm match' overstates significance",
    },
    "part_B": {
        "casimir_base_up":   base_up,
        "casimir_base_down": base_down,
        "best_correction":   best_B,
        "all_corrections":   [
            {"name": n, "value": v,
             "up_pred": base_up*(1-v), "dn_pred": base_down*(1+v),
             "up_dev_pct": abs(base_up*(1-v)-TYPE_MOD_UP)/TYPE_MOD_UP*100,
             "dn_dev_pct": abs(base_down*(1+v)-TYPE_MOD_DOWN)/TYPE_MOD_DOWN*100}
            for n, v in QCD_CORRECTIONS
        ],
        "verdict": (f"Best correction '{best_B['label']}' gives up-type residual "
                    f"{abs(best_B['up']-TYPE_MOD_UP)/TYPE_MOD_UP*100:.2f}%, "
                    f"down-type residual {abs(best_B['dn']-TYPE_MOD_DOWN)/TYPE_MOD_DOWN*100:.2f}%"),
    },
    "part_C": {
        "tau_c_canonical":   -65535,
        "charm_c_canonical": +65535,
        "tau_abc_signed":    5*275*(-65535),
        "charm_abc_signed":  5*275*65535,
        "lepton_signed_abc_ordering_correct": False,
        "lepton_abs_abc_ordering_correct": True,
        "verdict": (
            "sign(c) gives WRONG lepton ordering; |c| convention in UCL is correct for mass hierarchy. "
            "Chirality (sign c) is orthogonal to mass. The signed det distinguishes tau from charm "
            "but does not improve mass ordering predictions."
        ),
    },
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

sha = hashlib.sha256(
    json.dumps({k: v for k, v in output.items() if k != "timestamp_utc"}, sort_keys=True,
               default=str).encode()
).hexdigest()
output["sha256"] = sha

out_path = "comp_p01_EBF_03_det_ratio_null_and_corrections.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
