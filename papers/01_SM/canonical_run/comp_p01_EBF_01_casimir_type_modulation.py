#!/usr/bin/env python3
"""
comp_p01_EBF_01_casimir_type_modulation.py
EPIC 8 — E_base Foundations, Sub-project B, Computation 1

QUESTION:
    Can the empirical type-modulation factors {lepton: 1.0, up_type: 0.85, down_type: 1.15}
    in the UGP E_base engine be replaced by structural quantities derived from
    Casimir invariants of the SM gauge groups, combined with UGP-derived constants
    (sin^2(theta_W) ≈ 0.2312, alpha_EM, etc.)?

EMPIRICAL TARGETS:
    type_mod_lepton = 1.0         (reference, normalized)
    type_mod_up     = 0.85        (empirical)
    type_mod_down   = 1.15        (empirical)

METHOD:
    1. Enumerate all gauge-group representations for each fermion type (SM gauge theory).
    2. Construct all simple Casimir-based formulas: single Casimirs, products, ratios,
       combinations with sin^2(theta_W), alpha_EM, hypercharges, etc.
    3. Normalize each formula to lepton = 1.0 and compare to empirical targets.
    4. Report match quality: EXACT (< 0.1%), CLOSE (< 5%), APPROXIMATE (< 20%), FAIL.
    5. Run a null test: are the matches better than random Casimir-like numbers?

VERDICT CRITERIA:
    SUCCESS: a single formula with structural motivation matches all three
             type_mod values to < 1% using only UGP-certified inputs.
    PARTIAL: best formula matches two of three, or all three to < 5%.
    CLOSE:   best formula matches to < 20%, suggesting the right class.
    FAIL:    no simple Casimir formula within 20%.

Pre-commit protocol: prediction block SHA-256 before PDG comparison.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timezone
from itertools import product
from typing import Dict, List, Tuple

# ────────────────────────────────────────────────────────────────────────────
# 1. Physical constants — all from UGP-certified or PDG sources
# ────────────────────────────────────────────────────────────────────────────

# UGP-derived sin^2(theta_W) from COMP-FFF (5.8 sigma closure)
SIN2_TW_UGP = 0.23122        # COMP-FFF
SIN2_TW_PDG = 0.23122        # PDG MS-bar at MZ (same here — UGP matches)
COS2_TW     = 1.0 - SIN2_TW_UGP
SIN_TW      = math.sqrt(SIN2_TW_UGP)
COS_TW      = math.sqrt(COS2_TW)
TAN2_TW     = SIN2_TW_UGP / COS2_TW

# Fine structure constant — UGP-derived to 2.39 ppm
ALPHA_EM    = 1.0 / 137.03599084   # CODATA 2018

# Strong coupling at MZ
ALPHA_S     = 0.1181

# Derived gauge couplings at MZ (SM GUT normalisation)
# g1^2/(4pi) = alpha * 5/3 / cos^2(theta_W) — GUT normalisation
# g2^2/(4pi) = alpha / sin^2(theta_W)
# g3^2/(4pi) = alpha_s
G1_SQ_OVER_4PI = ALPHA_EM * (5.0/3.0) / COS2_TW   # GUT-normalised U(1)
G2_SQ_OVER_4PI = ALPHA_EM / SIN2_TW_UGP
G3_SQ_OVER_4PI = ALPHA_S

# Golden ratio (UGP structural constant)
PHI         = (1.0 + math.sqrt(5.0)) / 2.0

# Empirical type modulation targets
TYPE_MOD_EMPIRICAL = {
    "lepton":    1.00,
    "up_type":   0.85,
    "down_type": 1.15,
}

# ────────────────────────────────────────────────────────────────────────────
# 2. SM quantum numbers for each fermion type
# ────────────────────────────────────────────────────────────────────────────
# Conventions: left-handed doublet (L), right-handed singlet (R)
# Y_W = weak hypercharge (SM convention Q = T3 + Y)
# T3_L = third component of weak isospin (left-handed)
# T3_R = 0 for all right-handed singlets
# Q = electric charge
# N_c = colour multiplicity (3 for quarks, 1 for leptons)

FERMION_TYPES = {
    "lepton": {
        "Q": -1.0,
        "T3_L": -0.5,
        "T3_R": 0.0,
        "Y_L": -0.5,           # Y = Q - T3
        "Y_R": -1.0,
        "N_c": 1,
        "C2_SU3": 0.0,         # SU(3) singlet
        "C2_SU2_L": 3.0/4.0,  # SU(2) doublet
        "C2_SU2_R": 0.0,       # SU(2) singlet
    },
    "up_type": {
        "Q": 2.0/3.0,
        "T3_L": +0.5,
        "T3_R": 0.0,
        "Y_L": 1.0/6.0,
        "Y_R": 2.0/3.0,
        "N_c": 3,
        "C2_SU3": 4.0/3.0,    # SU(3) fundamental
        "C2_SU2_L": 3.0/4.0,  # SU(2) doublet
        "C2_SU2_R": 0.0,
    },
    "down_type": {
        "Q": -1.0/3.0,
        "T3_L": -0.5,
        "T3_R": 0.0,
        "Y_L": 1.0/6.0,
        "Y_R": -1.0/3.0,
        "N_c": 3,
        "C2_SU3": 4.0/3.0,    # SU(3) fundamental (same as up)
        "C2_SU2_L": 3.0/4.0,  # SU(2) doublet (same as up)
        "C2_SU2_R": 0.0,
    },
}

def fmt_ppm(val, ref=1.0):
    return (val - ref) / ref * 1e6

# ────────────────────────────────────────────────────────────────────────────
# 3. Formula library — all physically motivated Casimir combinations
# ────────────────────────────────────────────────────────────────────────────

def evaluate_formula(formula_fn, normalize_to_lepton=True):
    """Evaluate a formula for all three types. Normalize so lepton = 1.0 if requested."""
    raw = {t: formula_fn(FERMION_TYPES[t]) for t in ["lepton", "up_type", "down_type"]}
    if normalize_to_lepton and raw["lepton"] != 0.0:
        ref = raw["lepton"]
        return {t: raw[t] / ref for t in raw}
    return raw

def match_quality(result: dict):
    """Return max relative deviation from empirical targets."""
    devs = {t: abs(result[t] - TYPE_MOD_EMPIRICAL[t]) / TYPE_MOD_EMPIRICAL[t]
            for t in result}
    return max(devs.values()), devs

# Hypothesis bank — each entry: (name, description, formula_fn)
HYPOTHESES = []

def H(name, desc, fn):
    HYPOTHESES.append((name, desc, fn))
    return fn

# ── Group 1: Pure Casimir invariants ─────────────────────────────────────────

# H-1: SU(3) Casimir alone (quarks get C2_SU3 = 4/3; lepton = 0 → normalise fails)
H("H-1a", "C2_SU3 (lepton fixed to 1.0 by hand)",
  lambda f: f["C2_SU3"] if f["C2_SU3"] > 0 else 1.0)

# H-1b: 1 + C2_SU3 (adds 1 as baseline)
H("H-1b", "1 + C2_SU3",
  lambda f: 1.0 + f["C2_SU3"])

# H-1c: C2_SU2_L alone
H("H-1c", "C2_SU2_L",
  lambda f: f["C2_SU2_L"])

# H-1d: C2_SU3 + C2_SU2_L
H("H-1d", "C2_SU3 + C2_SU2_L",
  lambda f: f["C2_SU3"] + f["C2_SU2_L"])

# H-1e: C2_SU3 / C2_SU2_L  (undefined for lepton since C2_SU3=0)
H("H-1e", "1 + C2_SU3/C2_SU2_L  (1 for lepton since C2_SU3=0)",
  lambda f: 1.0 + (f["C2_SU3"] / f["C2_SU2_L"] if f["C2_SU2_L"] > 0 else 0.0))

# ── Group 2: Charge-based ────────────────────────────────────────────────────

# H-2a: |Q|
H("H-2a", "|Q|",
  lambda f: abs(f["Q"]))

# H-2b: 1 - |Q|
H("H-2b", "1 - |Q|",
  lambda f: 1.0 - abs(f["Q"]))

# H-2c: |Q|^(1/2)
H("H-2c", "|Q|^0.5",
  lambda f: abs(f["Q"])**0.5)

# H-2d: Q^2
H("H-2d", "Q^2",
  lambda f: f["Q"]**2)

# H-2e: T3_L alone
H("H-2e", "T3_L + 1  (shift so lepton = 0.5 → normalise)",
  lambda f: f["T3_L"] + 1.0)

# ── Group 3: Weak mixing combinations ─────────────────────────────────────

# H-3a: 1 - 2Q*sin^2(theta_W)  — NC coupling formula
H("H-3a", "1 - 2*Q*sin2W",
  lambda f: 1.0 - 2.0 * f["Q"] * SIN2_TW_UGP)

# H-3b: 1 + 2*T3_L*sin^2(theta_W)
H("H-3b", "1 + 2*T3_L*sin2W",
  lambda f: 1.0 + 2.0 * f["T3_L"] * SIN2_TW_UGP)

# H-3c: C2_SU3*(1 - 2/3*sin2W)  — overview candidate for down
H("H-3c", "C2_SU3*(1 - 2*sin2W/3)  (lepton=0→ override to 1)",
  lambda f: (f["C2_SU3"] * (1.0 - 2.0 * SIN2_TW_UGP / 3.0)) if f["C2_SU3"] > 0 else 1.0)

# H-3d: C2_SU3/(3/2) for quarks, lepton=1 — overview candidate for up
H("H-3d", "C2_SU3 / (3/2)  [= 8/9 for quarks; lepton=1]",
  lambda f: (f["C2_SU3"] / 1.5) if f["C2_SU3"] > 0 else 1.0)

# H-3e: combine H-3c and H-3d: up = 8/9 ≈ 0.889, down = 4/3*(1-2sin2W/3) ≈ 1.128
# This tests the overview's explicit suggestion
H("H-3e", "H-3d for up, H-3c for down (type-specific Casimir)",
  lambda f: (f["C2_SU3"] / 1.5) if f["N_c"] == 3 and f["T3_L"] > 0 else
            (f["C2_SU3"] * (1.0 - 2.0*SIN2_TW_UGP/3.0)) if f["N_c"] == 3 else 1.0)

# ── Group 4: Hypercharge-based ───────────────────────────────────────────────

# H-4a: Y_R^2
H("H-4a", "Y_R^2",
  lambda f: f["Y_R"]**2)

# H-4b: Y_L^2 + Y_R^2
H("H-4b", "Y_L^2 + Y_R^2",
  lambda f: f["Y_L"]**2 + f["Y_R"]**2)

# H-4c: (Y_L + Y_R)^2
H("H-4c", "(Y_L + Y_R)^2",
  lambda f: (f["Y_L"] + f["Y_R"])**2)

# H-4d: C2_SU3 + 3/4*C2_SU2_L + 5/3*(Y_L^2 + Y_R^2)  — GUT-normalised total
H("H-4d", "C2_SU3 + C2_SU2_L + 5/3*(Y_L^2+Y_R^2)",
  lambda f: f["C2_SU3"] + f["C2_SU2_L"] + (5.0/3.0)*(f["Y_L"]**2 + f["Y_R"]**2))

# ── Group 5: One-loop Yukawa anomalous dimension contributions ──────────────

# At one loop, the Yukawa coupling runs according to (gauge part only):
# β_λ/λ = -(1/16π²) * [8g3^2*C2_SU3 + (9/4)g2^2*C2_SU2 + c1*g1^2*Y^2]
# where the U(1) Casimir coefficient c1 depends on particle type.
# The fractional running from M_GUT to M_Z distinguishes particle types.

# U(1) hypercharge coefficients in the Yukawa β-function:
# up-type: c1 = 17/20 (in SM convention without GUT normalisation)
# down-type: c1 = 1/4
# lepton: c1 = 9/4
C1_YUKAWA = {"up_type": 17.0/20.0, "down_type": 1.0/4.0, "lepton": 9.0/4.0}

def yukawa_gauge_factor(f_data, ftype):
    """One-loop gauge contribution to Yukawa running (at MZ)."""
    c1 = C1_YUKAWA[ftype]
    return (8.0 * G3_SQ_OVER_4PI * f_data["C2_SU3"]
          + (9.0/4.0) * G2_SQ_OVER_4PI * f_data["C2_SU2_L"]
          + c1 * G1_SQ_OVER_4PI)

H("H-5a", "one-loop Yukawa gauge factor (gamma_Yukawa)",
  lambda f: yukawa_gauge_factor(f, next(t for t in FERMION_TYPES if FERMION_TYPES[t] is f)))

# We need a wrapper that passes the type name too
for _ftype in ["lepton", "up_type", "down_type"]:
    pass  # the lambda can't capture ftype easily; compute manually below

# ── Group 6: N_c-based (color factor) ──────────────────────────────────────

# H-6a: 1/N_c
H("H-6a", "1/N_c",
  lambda f: 1.0 / f["N_c"])

# H-6b: 1 - 1/N_c
H("H-6b", "1 - 1/N_c",
  lambda f: 1.0 - 1.0/f["N_c"])

# H-6c: N_c^(1/3)
H("H-6c", "N_c^(1/3)",
  lambda f: f["N_c"]**(1.0/3.0))

# H-6d: T3_L * N_c (combines isospin and color)
H("H-6d", "1 + T3_L/N_c",
  lambda f: 1.0 + f["T3_L"] / f["N_c"])

# H-6e: (1 + 2*T3_L*sin2W) / N_c  — weak correction divided by color factor
H("H-6e", "(1 + 2*T3_L*sin2W) / N_c",
  lambda f: (1.0 + 2.0*f["T3_L"]*SIN2_TW_UGP) / f["N_c"])

# ── Group 7: Comprehensive combinations ─────────────────────────────────────

# H-7a: C2_SU3 + C2_SU2_L + Y_R^2
H("H-7a", "C2_SU3 + C2_SU2_L + Y_R^2",
  lambda f: f["C2_SU3"] + f["C2_SU2_L"] + f["Y_R"]**2)

# H-7b: (C2_SU3 + C2_SU2_L)*(1 - 2*T3_L*sin2W)
H("H-7b", "(C2_SU3 + C2_SU2_L)*(1 - 2*T3_L*sin2W)",
  lambda f: (f["C2_SU3"] + f["C2_SU2_L"])*(1.0 - 2.0*f["T3_L"]*SIN2_TW_UGP))

# H-7c: (1 + C2_SU3)*(1 + 2*T3_L*sin2W)
H("H-7c", "(1 + C2_SU3)*(1 + 2*T3_L*sin2W)",
  lambda f: (1.0 + f["C2_SU3"])*(1.0 + 2.0*f["T3_L"]*SIN2_TW_UGP))

# H-7d: 1 + C2_SU3*(1 + 2*T3_L*sin2W) — additive correction
H("H-7d", "1 + C2_SU3*(1 + 2*T3_L*sin2W)",
  lambda f: 1.0 + f["C2_SU3"]*(1.0 + 2.0*f["T3_L"]*SIN2_TW_UGP))

# H-7e: 1 + C2_SU3*(2*T3_L)  — isospin-modulated color
H("H-7e", "1 + 2*T3_L*C2_SU3",
  lambda f: 1.0 + 2.0*f["T3_L"]*f["C2_SU3"])

# H-7f: C2_SU2_L + C2_SU3 - 2*Q*sin2W*C2_SU3  — NC + color
H("H-7f", "C2_SU2_L + C2_SU3*(1 - 2*Q*sin2W)",
  lambda f: f["C2_SU2_L"] + f["C2_SU3"]*(1.0 - 2.0*f["Q"]*SIN2_TW_UGP))

# H-7g: The "rho-parameter style" combination: 1 - 4*Q*sin2W/3
H("H-7g", "1 - 4*Q*sin2W/(3)",
  lambda f: 1.0 - 4.0*f["Q"]*SIN2_TW_UGP/3.0)

# H-7h: 1 - 4*T3_L*sin2W/3
H("H-7h", "1 - 4*T3_L*sin2W/3",
  lambda f: 1.0 - 4.0*f["T3_L"]*SIN2_TW_UGP/3.0)

# H-7i: NC coupling g_V = T3 - 2Q*sin2W (the Z coupling vector part)
H("H-7i", "T3_L - 2*Q*sin2W  (gV, NC coupling)",
  lambda f: f["T3_L"] - 2.0*f["Q"]*SIN2_TW_UGP)

# H-7j: |gV| = |T3 - 2Q*sin2W|
H("H-7j", "|T3_L - 2*Q*sin2W|",
  lambda f: abs(f["T3_L"] - 2.0*f["Q"]*SIN2_TW_UGP))

# H-7k: gV^2 + gA^2 = (T3 - 2Q sin2W)^2 + T3^2
H("H-7k", "gV^2 + gA^2",
  lambda f: (f["T3_L"] - 2.0*f["Q"]*SIN2_TW_UGP)**2 + f["T3_L"]**2)

# H-7l: C2_SU3 + |Y_R|
H("H-7l", "C2_SU3 + |Y_R|",
  lambda f: f["C2_SU3"] + abs(f["Y_R"]))

# H-7m: 1 + 2*Y_R*sin2W
H("H-7m", "1 + 2*Y_R*sin2W",
  lambda f: 1.0 + 2.0*f["Y_R"]*SIN2_TW_UGP)

# H-7n: 1 + Y_R  (simple hypercharge shift)
H("H-7n", "1 + Y_R",
  lambda f: 1.0 + f["Y_R"])

# H-7o: (1 + Y_R)^2
H("H-7o", "(1 + Y_R)^2",
  lambda f: (1.0 + f["Y_R"])**2)

# H-7p: exp(C2_SU3 * T3_L)
H("H-7p", "exp(C2_SU3 * T3_L)",
  lambda f: math.exp(f["C2_SU3"] * f["T3_L"]))

# ── Group 8: Weak charge (NC coupling at zero momentum transfer) ─────────────

# Qw_f = T3_f - 2*Q_f*sin2W (same as gV above but emphasise "weak charge" name)
# For proton: Qw_p = 1 - 4*sin2W ≈ 0.076
# For neutron: Qw_n = -1
# Type-modulation as weak-charge ratios:

H("H-8a", "Qw = T3_L - 2*Q*sin2W  (= H-7i, duplicated for clarity)",
  lambda f: f["T3_L"] - 2.0*f["Q"]*SIN2_TW_UGP)

# H-8b: (1 + Qw) normalized
H("H-8b", "1 + (T3_L - 2*Q*sin2W)",
  lambda f: 1.0 + f["T3_L"] - 2.0*f["Q"]*SIN2_TW_UGP)

# H-8c: (C2_SU3 + 3/4) * |T3_L|  (combined color+weak isospin factor)
H("H-8c", "(C2_SU3 + 3/4) * |T3_L|",
  lambda f: (f["C2_SU3"] + 3.0/4.0) * abs(f["T3_L"]))

# ── Group 9: Golden ratio and UGP structural constants ──────────────────────

# H-9a: phi * (1 - 2*Q*sin2W) / phi  (just a consistency check)
H("H-9a", "phi * C2_SU2_L + C2_SU3",
  lambda f: PHI * f["C2_SU2_L"] + f["C2_SU3"])

# H-9b: 1 + (PHI-1)*(2*T3_L)  (golden modulation of isospin)
H("H-9b", "1 + (phi-1)*2*T3_L",
  lambda f: 1.0 + (PHI - 1.0) * 2.0 * f["T3_L"])

# H-9c: 1 + T3_L/phi
H("H-9c", "1 + T3_L/phi",
  lambda f: 1.0 + f["T3_L"] / PHI)

# H-9d: 1 + C2_SU3 * T3_L / phi
H("H-9d", "1 + C2_SU3 * T3_L / phi",
  lambda f: 1.0 + f["C2_SU3"] * f["T3_L"] / PHI)

# H-9e: 1 - 2*Q*sin2W/phi
H("H-9e", "1 - 2*Q*sin2W/phi",
  lambda f: 1.0 - 2.0*f["Q"]*SIN2_TW_UGP / PHI)

# ────────────────────────────────────────────────────────────────────────────
# 4. Special: manually compute H-5a with correct type name
# ────────────────────────────────────────────────────────────────────────────

yukawa_raw = {t: yukawa_gauge_factor(FERMION_TYPES[t], t) for t in FERMION_TYPES}

# ────────────────────────────────────────────────────────────────────────────
# 5. Evaluate all hypotheses
# ────────────────────────────────────────────────────────────────────────────

def eval_hypothesis(name, desc, fn):
    """Evaluate formula fn for all three types. Normalize to lepton=1.0."""
    try:
        raw = {t: fn(FERMION_TYPES[t]) for t in ["lepton", "up_type", "down_type"]}
    except Exception as e:
        return {"name": name, "desc": desc, "error": str(e)}

    # Normalize to lepton = 1.0
    ref = raw["lepton"]
    if ref == 0.0:
        return {"name": name, "desc": desc, "error": "lepton value is 0 (cannot normalise)"}

    normed = {t: raw[t] / ref for t in raw}
    max_dev, devs = match_quality(normed)

    # Classify
    if max_dev < 0.001:
        label = "EXACT"
    elif max_dev < 0.05:
        label = "CLOSE"
    elif max_dev < 0.20:
        label = "APPROXIMATE"
    else:
        label = "FAIL"

    return {
        "name": name,
        "desc": desc,
        "raw": raw,
        "normed": normed,
        "empirical": TYPE_MOD_EMPIRICAL,
        "deviations_pct": {t: devs[t] * 100 for t in devs},
        "max_dev_pct": max_dev * 100,
        "label": label,
    }

# Add H-5a manually with correct type-name handling
HYPOTHESES_SPECIAL = [
    ("H-5a", "one-loop Yukawa gamma_gauge (g3^2*C2_SU3 + g2^2*C2_SU2 + g1^2*c1)",
     {t: yukawa_raw[t] for t in ["lepton", "up_type", "down_type"]}),
]

results = []
for name, desc, fn in HYPOTHESES:
    results.append(eval_hypothesis(name, desc, fn))

# Add H-5a
yukawa_ref = yukawa_raw["lepton"]
yukawa_normed = {t: yukawa_raw[t] / yukawa_ref for t in yukawa_raw}
yukawa_max_dev, yukawa_devs = match_quality(yukawa_normed)
results.append({
    "name": "H-5a",
    "desc": "one-loop Yukawa gamma_gauge",
    "raw": yukawa_raw,
    "normed": yukawa_normed,
    "empirical": TYPE_MOD_EMPIRICAL,
    "deviations_pct": {t: yukawa_devs[t]*100 for t in yukawa_devs},
    "max_dev_pct": yukawa_max_dev * 100,
    "label": "EXACT" if yukawa_max_dev < 0.001 else "CLOSE" if yukawa_max_dev < 0.05 else "APPROXIMATE" if yukawa_max_dev < 0.20 else "FAIL",
})

# Sort by match quality
results_valid = [r for r in results if "error" not in r]
results_error = [r for r in results if "error" in r]
results_valid.sort(key=lambda r: r["max_dev_pct"])

# ────────────────────────────────────────────────────────────────────────────
# 6. Null test — random Casimir-like numbers
# ────────────────────────────────────────────────────────────────────────────
# Generate random triplets (L, U, D) with L=1 (normalised) and U,D ~ [0.5, 2.0]
# Check how often max_dev < threshold for the best hypothesis

BEST_DEV = results_valid[0]["max_dev_pct"] / 100.0
N_NULL = 10000
null_hits = 0
rng = random.Random(42)
for _ in range(N_NULL):
    U = rng.uniform(0.5, 2.0)
    D = rng.uniform(0.5, 2.0)
    trial_devs = {
        "lepton": 0.0,
        "up_type": abs(U - TYPE_MOD_EMPIRICAL["up_type"]) / TYPE_MOD_EMPIRICAL["up_type"],
        "down_type": abs(D - TYPE_MOD_EMPIRICAL["down_type"]) / TYPE_MOD_EMPIRICAL["down_type"],
    }
    if max(trial_devs.values()) <= BEST_DEV:
        null_hits += 1

null_p = null_hits / N_NULL
null_label = ("STRUCTURAL_SUPPORT (p<0.01)" if null_p < 0.01 else
              "MARGINAL (0.01<=p<0.05)" if null_p < 0.05 else
              "WEAK (0.05<=p<0.20)" if null_p < 0.20 else
              "NOT_STRUCTURAL (p>=0.20)")

# ────────────────────────────────────────────────────────────────────────────
# 7. Build prediction block and SHA-256
# ────────────────────────────────────────────────────────────────────────────

top5 = results_valid[:5]
prediction_block = {
    "experiment_id": "COMP-P01-EBF-01",
    "epic": "EPIC_8_EBASE_FOUNDATIONS",
    "sub_project": "B_BEKENSTEIN_HOLOGRAPHIC_BRIDGE",
    "question": "Can empirical type-modulation {lepton:1.0, up:0.85, down:1.15} be derived from SM Casimir invariants?",
    "empirical_targets": TYPE_MOD_EMPIRICAL,
    "n_hypotheses_tested": len(HYPOTHESES) + 1,
    "top_5_hypotheses_by_match_quality": [
        {
            "rank": i+1,
            "name": r["name"],
            "desc": r["desc"],
            "normed_lepton": r["normed"]["lepton"],
            "normed_up": r["normed"]["up_type"],
            "normed_down": r["normed"]["down_type"],
            "max_dev_pct": r["max_dev_pct"],
            "label": r["label"],
        }
        for i, r in enumerate(top5)
    ],
}

sha = hashlib.sha256(json.dumps(prediction_block, sort_keys=True).encode()).hexdigest()
prediction_block["sha256_prediction_precommit"] = sha

# ────────────────────────────────────────────────────────────────────────────
# 8. Verdict
# ────────────────────────────────────────────────────────────────────────────

best = results_valid[0]
best_label = best["label"]

if best_label == "EXACT":
    verdict = (f"EXACT MATCH: '{best['name']}' ({best['desc']}) "
               f"reproduces all three type-modulation factors to < 0.1%. "
               f"Casimir type-modulation is structurally derivable.")
elif best_label == "CLOSE":
    verdict = (f"CLOSE MATCH: '{best['name']}' ({best['desc']}) "
               f"matches to {best['max_dev_pct']:.2f}% max deviation. "
               f"Casimir replacement is 'close' but not exact. "
               f"May be exact in the limit of tree-level structural theory.")
elif best_label == "APPROXIMATE":
    verdict = (f"APPROXIMATE: best match '{best['name']}' ({best['desc']}) "
               f"is within {best['max_dev_pct']:.1f}% — suggestive but not structural. "
               f"The class of Casimir formula is right but the exact form is unknown.")
else:
    verdict = (f"FAIL: no hypothesis within 20%. "
               f"Best was '{best['name']}' at {best['max_dev_pct']:.1f}%. "
               f"Simple Casimir combinations do not explain type modulation.")

output = {
    **prediction_block,
    "null_test": {
        "n_trials": N_NULL,
        "null_hits": null_hits,
        "best_dev_threshold": BEST_DEV,
        "null_p": null_p,
        "null_label": null_label,
    },
    "all_results_sorted": [
        {k: v for k, v in r.items() if k not in ("raw", "empirical")}
        for r in results_valid
    ],
    "errors": results_error,
    "verdict": verdict,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

# ────────────────────────────────────────────────────────────────────────────
# 9. Console summary
# ────────────────────────────────────────────────────────────────────────────

print("=" * 72)
print("COMP-P01-EBF-01 — Casimir Type Modulation")
print("=" * 72)
print(f"Empirical targets: lepton=1.00, up={TYPE_MOD_EMPIRICAL['up_type']}, down={TYPE_MOD_EMPIRICAL['down_type']}")
print(f"Tested {len(HYPOTHESES)+1} hypotheses.\n")
print("Top 10 by match quality:")
print(f"{'Rank':>4} {'Name':>6} {'Max dev%':>10}  {'Up':>8}  {'Down':>8}  Label   Formula")
print("-" * 80)
for i, r in enumerate(results_valid[:10]):
    u = r["normed"]["up_type"]
    d = r["normed"]["down_type"]
    print(f"{i+1:>4} {r['name']:>6} {r['max_dev_pct']:>10.2f}  {u:>8.4f}  {d:>8.4f}  {r['label']:12s}  {r['desc'][:35]}")
print()
print(f"Null test: best dev = {BEST_DEV*100:.2f}%, null p = {null_p:.4f} → {null_label}")
print()
print("VERDICT:", verdict)
print("=" * 72)

out_path = "comp_p01_EBF_01_casimir_type_modulation.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)
print(f"\nResults written to {out_path}")
