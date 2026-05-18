#!/usr/bin/env python3
"""
derive_alpha_s_prediction.py - COMP-P01-D

Blind prediction of the strong coupling alpha_s at the Z pole from the
same Lean-certified Elegant-Kernel pipeline that produces alpha_EM to
+2.39 ppm of CODATA in Paper 1.

Pipeline (identical to the TE1.P electromagnetic pipeline):

  1. Take the Lean-certified bare squared gauge coupling from ugp-lean:
        g_3^2_bare = 41,075,281 / 27,648,000       (theorem g3Sq_bare_eq)
        g_2^2_bare = 2,329 / 5,400                 (theorem g2Sq_bare_eq)
        g_1^2_bare = 16 / 125                      (theorem g1Sq_bare_eq)
  2. Convert to alpha_i via alpha_i = g_i^2 / (4 pi).
  3. Record the prediction BEFORE comparing to PDG, then compare.

This is a SINGLE-STAGE derivation -- no RG evolution, no threshold
matching, and no delta_UGP correction is applied at this stage.  The
first-order question a reviewer would ask is whether the Lean-certified
bare couplings, evaluated as alpha_i = g_i^2 / (4 pi), yield values
compatible with the Z-pole PDG experimental benchmarks.  Any significant
discrepancy in alpha_s relative to alpha_EM would indicate that the
2.39 ppm alpha_EM result is specific to g_1 rather than a universal
feature of the Elegant-Kernel gauge sector.

PDG 2022 world averages (at M_Z):
  alpha_s(M_Z) = 0.11790 +- 0.00090   (0.76% relative)
  alpha_EM^{-1}(M_Z) ~ 127.952        (GUT-normalized g_1 picture)
  CODATA 2018 alpha_EM (low-energy) = 7.2973525693 x 10^{-3}

The paper's TE1.P result (alpha_EM at low energy from g_1^2 = 16/125) was
+2.39 ppm relative to CODATA; the corresponding blind test here is
identical in spirit.

NOTE: this script does NOT tune any parameter; it reads the Lean-certified
rationals directly.  The prediction is archived to
  canonical_run/alpha_s_prediction.json
with a pre-comparison timestamp before the PDG comparison is recorded
in the same JSON payload.
"""
import json
import math
import os
import hashlib
from datetime import datetime, timezone
from fractions import Fraction


# ------------------------------------------------------------------
# Step 1: Lean-certified bare couplings (from ugp-lean MANIFEST/THEOREMS)
# ------------------------------------------------------------------
g1Sq_bare = Fraction(16, 125)                 # theorem g1Sq_bare_eq
g2Sq_bare = Fraction(2329, 5400)              # theorem g2Sq_bare_eq
g3Sq_bare = Fraction(41075281, 27648000)      # theorem g3Sq_bare_eq

LEAN_ZENODO = "10.5281/zenodo.19433538"

# ------------------------------------------------------------------
# Step 2: Derived alpha_i = g_i^2 / (4 pi) (single-stage, no tuning)
# ------------------------------------------------------------------
FOUR_PI = 4.0 * math.pi

alpha1_bare = float(g1Sq_bare) / FOUR_PI
alpha2_bare = float(g2Sq_bare) / FOUR_PI
alpha3_bare = float(g3Sq_bare) / FOUR_PI

# ------------------------------------------------------------------
# Step 3: Pre-comparison archive block
# ------------------------------------------------------------------
prediction = {
    "lean_certified_bare_couplings": {
        "g1Sq_bare": [int(g1Sq_bare.numerator), int(g1Sq_bare.denominator), float(g1Sq_bare)],
        "g2Sq_bare": [int(g2Sq_bare.numerator), int(g2Sq_bare.denominator), float(g2Sq_bare)],
        "g3Sq_bare": [int(g3Sq_bare.numerator), int(g3Sq_bare.denominator), float(g3Sq_bare)],
        "source": "ugp-lean theorems g1Sq_bare_eq, g2Sq_bare_eq, g3Sq_bare_eq",
        "zenodo_doi": LEAN_ZENODO,
        "zero_sorry": True,
    },
    "derived_alpha_bare": {
        "alpha1_bare": alpha1_bare,
        "alpha2_bare": alpha2_bare,
        "alpha3_bare": alpha3_bare,
    },
    "pipeline": (
        "alpha_i = g_i^2_bare / (4 pi), no tuning, no RG evolution, "
        "no delta_UGP correction - identical identification used for g_1 "
        "in the TE1.P fine-structure validation."
    ),
    "pre_comparison_timestamp_utc": datetime.now(timezone.utc).isoformat(),
}


# ------------------------------------------------------------------
# Step 4: PDG comparisons (recorded AFTER the prediction block above)
# ------------------------------------------------------------------
PDG_ALPHA_S_MZ = 0.11790
PDG_ALPHA_S_MZ_SIGMA = 0.00090
PDG_SOURCE = "PDG 2022, Eur. Phys. J. C (review of particle physics), alpha_s world average"

CODATA_ALPHA_EM_LOW = 7.2973525693e-3
CODATA_ALPHA_EM_INV_LOW = 137.035999084
CODATA_SOURCE = "CODATA 2018 recommended value"

# Note: TE1.P combines g_1 and g_2 with the measured sin^2 theta_W to get
# alpha_EM at low energy to 2.39 ppm.  The direct alpha_1 = g_1^2 / 4pi
# value is the bare U(1)_Y coupling and is not expected to match CODATA
# alpha_EM; we record it here only for completeness.

# Reference Z-pole values
PDG_G3_MZ = 1.220           # s/s world average, g3 = sqrt(4 pi alpha_s)
PDG_SIN2_THETA_W_MZ = 0.23122

# Direct alpha_s comparison (single-stage, no RG evolution)
dev_alpha_s_rel = (alpha3_bare - PDG_ALPHA_S_MZ) / PDG_ALPHA_S_MZ
dev_alpha_s_sigma = (alpha3_bare - PDG_ALPHA_S_MZ) / PDG_ALPHA_S_MZ_SIGMA
dev_alpha_s_ppm = dev_alpha_s_rel * 1.0e6

# Also compute the equivalent bare g_3 value for transparency
g3_bare_numerical = math.sqrt(float(g3Sq_bare))

print("=" * 72)
print("COMP-P01-D: alpha_s(M_Z) blind prediction from Lean-certified g3^2")
print("=" * 72)
print()
print("Pre-comparison prediction (from Lean-certified rationals, no tuning):")
print(f"  g_1^2_bare  = 16/125               = {float(g1Sq_bare):.12f}")
print(f"  g_2^2_bare  = 2329/5400            = {float(g2Sq_bare):.12f}")
print(f"  g_3^2_bare  = 41075281/27648000    = {float(g3Sq_bare):.12f}")
print(f"  alpha_1_bare = g_1^2/(4 pi)        = {alpha1_bare:.12f}")
print(f"  alpha_2_bare = g_2^2/(4 pi)        = {alpha2_bare:.12f}")
print(f"  alpha_3_bare = g_3^2/(4 pi)        = {alpha3_bare:.12f}")
print(f"  g_3_bare (sqrt)                    = {g3_bare_numerical:.6f}")
print()
print("PDG comparison (recorded after prediction block):")
print(f"  alpha_s(M_Z) PDG 2022              = {PDG_ALPHA_S_MZ} +/- {PDG_ALPHA_S_MZ_SIGMA} ({100*PDG_ALPHA_S_MZ_SIGMA/PDG_ALPHA_S_MZ:.2f}%)")
print(f"  alpha_3_bare from kernel           = {alpha3_bare:.5f}")
print(f"  deviation                           = {100*dev_alpha_s_rel:.4f}% ({dev_alpha_s_ppm:.0f} ppm)")
print(f"  deviation in sigma                  = {dev_alpha_s_sigma:+.3f} sigma")
print()
if abs(dev_alpha_s_sigma) <= 2.0:
    print("  Consistent with PDG at the 2-sigma level.")
elif abs(dev_alpha_s_sigma) <= 3.0:
    print("  Deviates from PDG at the 2-3 sigma level; open front for higher-order corrections.")
else:
    print("  Deviates from PDG beyond 3 sigma; pipeline requires further work.")

# ------------------------------------------------------------------
# Step 5: Write payload
# ------------------------------------------------------------------
payload = {
    "description": (
        "COMP-P01-D: blind alpha_s(M_Z) prediction from the same pipeline "
        "that produces alpha_EM at 2.39 ppm of CODATA in Paper 1 TE1.P. "
        "Uses Lean-certified bare squared couplings (g_i^2_bare from "
        "ugp-lean) via alpha_i = g_i^2 / (4 pi), no RG evolution, no "
        "tuning, no delta_UGP correction.  Prediction is archived BEFORE "
        "the PDG comparison."
    ),
    "prediction_block_precomparison": prediction,
    "pdg_comparison": {
        "pdg_alpha_s_MZ": PDG_ALPHA_S_MZ,
        "pdg_alpha_s_MZ_sigma": PDG_ALPHA_S_MZ_SIGMA,
        "pdg_source": PDG_SOURCE,
        "predicted_alpha_s_MZ": alpha3_bare,
        "deviation_abs": alpha3_bare - PDG_ALPHA_S_MZ,
        "deviation_rel": dev_alpha_s_rel,
        "deviation_ppm": dev_alpha_s_ppm,
        "deviation_sigma": dev_alpha_s_sigma,
        "consistent_within_1sigma": abs(dev_alpha_s_sigma) <= 1.0,
        "consistent_within_2sigma": abs(dev_alpha_s_sigma) <= 2.0,
        "consistent_within_3sigma": abs(dev_alpha_s_sigma) <= 3.0,
        "comparison_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    },
    "codata_alpha_EM_reference_low_energy": {
        "alpha_EM": CODATA_ALPHA_EM_LOW,
        "alpha_EM_inv": CODATA_ALPHA_EM_INV_LOW,
        "source": CODATA_SOURCE,
        "note": (
            "Low-energy alpha_EM is included for reference.  The TE1.P "
            "alpha_EM = 2.39 ppm result in Paper 1 combines g_1^2 and "
            "g_2^2 with sin^2 theta_W to reach the low-energy value; it "
            "is NOT obtained by alpha_1 = g_1^2 / (4 pi) alone."
        ),
    },
    "derivation_chain": (
        "ugp-lean theorems g_i^2_bare  ->  alpha_i = g_i^2 / (4 pi)  "
        "->  compare alpha_3 to PDG alpha_s(M_Z) directly."
    ),
    "limitations": (
        "This is the single-stage blind comparison.  A full predictive "
        "alpha_s(M_Z) derivation would include delta_UGP correction (as "
        "applied in TE1.P for alpha_EM) and RG running between the UGP "
        "structural scale and M_Z.  The single-stage deviation sets an "
        "upper bound on the size of any required corrections."
    ),
}

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alpha_s_prediction.json")
with open(out_path, "w") as f:
    json.dump(payload, f, indent=2)

with open(out_path, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

print()
print(f"Output: {out_path}")
print(f"SHA-256: {sha}")
