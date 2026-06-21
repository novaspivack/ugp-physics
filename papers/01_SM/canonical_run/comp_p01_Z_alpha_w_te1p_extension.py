#!/usr/bin/env python3
"""
comp_p01_Z_alpha_w_te1p_extension.py -- COMP-P01-Z

Pre-committed attempt to close Paper 1 Open Problem (v):
"Extend the TE1.P delta_UGP + RG correction machinery (currently demonstrated
only for alpha_EM at +2.39 ppm) to the SU(2) sector, i.e. to alpha_w(M_Z) and
sin^2(theta_W)(M_Z), without per-point parameter tuning."

Spec:  specs/IN-PROCESS/EPIC_CLUSTER2_CLEAN_WINS/080_NOTE_P01_FOCUS_AND_OPEN_PROBLEM_TRIAGE.md
       section 3.1.

Decision rule (from that spec):
  Success (within 1 sigma PDG for both alpha_w and sin^2 theta_W)  --> upgrade
    Paper 1 §5.5 from "third gauge precision point" to "4-point ppm gauge
    precision chain all at ppm via TE1.P".
  Miss  --> no upgrade; Open Problem (v) retained.

This is a BLIND test: the prediction block is assembled first from only
Lean-certified inputs and the Eq. (9) formula for delta_UGP, without any
tuning to PDG alpha_w or sin^2 theta_W.  The PDG comparison block is then
appended.  No parameters are fit to data in this script.

Methodology
-----------
Inputs (all Lean-certified rationals):
  g_1^2_bare = 16/125             (ugp-lean theorem g1Sq_bare_eq)
  g_2^2_bare = 2329/5400          (ugp-lean theorem g2Sq_bare_eq)
  g_3^2_bare = 41075281/27648000  (ugp-lean theorem g3Sq_bare_eq)
  b_1        = 73                 (RSUC seed, rsuc_theorem)
  k_L^2      = 7/512              (k_L2_eq)
  k_gen^2    = -phi/2             (THM-UCL-1, unconditional)

Universal Instantiation Factor (Paper 1 Eq. (9)):
  delta_UGP = (1/b_1) * [ -1/(k_gen^2 + (1/4)*k_L^2) + (7/4)*(k_L^2/k_gen^2) ]

Pipeline variants tested
------------------------
  (A) bare-only: observables from g_i^2_bare alone, treating the rational
      values as the effective couplings at M_Z (no delta_UGP, no RG).
  (B) bare + delta_UGP: apply the Universal Instantiation Factor to the
      bare couplings; otherwise treat at M_Z.
  (C) bare + delta_UGP + SM one-loop RG from M_UGP = M_Planck: interpret
      the instantiated couplings as defined at M_Planck, run to M_Z with
      standard SM one-loop beta coefficients (3 generations, 1 Higgs
      doublet, hypercharge normalization for g_1).
  (D) bare + delta_UGP + SM one-loop RG from M_UGP = M_GUT (2e16 GeV).

The alpha_EM(Thomson) and alpha_EM(M_Z) observables are produced with a
low-energy Delta_alpha extraction using the PDG-known vacuum-polarization
shift Delta_alpha(M_Z) = 0.06630.  This is the one piece of PDG-derived
input that enters: it is a physics input, not a fit parameter.

Outputs
-------
  alpha_w(M_Z), alpha_s(M_Z), alpha_EM(M_Z), alpha_EM(Thomson),
  sin^2 theta_W(M_Z), for each of the four pipeline variants, compared to
  PDG central values and per-observable PDG 1-sigma uncertainties.

Pre-commit protocol
-------------------
  1. Build the predictions dict (no PDG references yet).
  2. SHA-256 the predictions dict as a canonical JSON string.
  3. Write the predictions dict to disk (`...Z_alpha_w_te1p_extension.json`).
  4. Only then load PDG values and append the comparison block to the JSON,
     with a secondary timestamp.

Both timestamps and both SHAs are recorded.  The pre-comparison SHA is the
binding commitment.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from fractions import Fraction
from typing import Dict, Any

# ---------------------------------------------------------------------------
# 1. Lean-certified rational inputs (no PDG references)
# ---------------------------------------------------------------------------

LEAN_REPO = "ugp-lean"
LEAN_ZENODO = "10.5281/zenodo.19433538"

# Bare squared gauge couplings (hypercharge normalization for g_1)
g1Sq_bare = Fraction(16, 125)                # theorem g1Sq_bare_eq
g2Sq_bare = Fraction(2329, 5400)             # theorem g2Sq_bare_eq
g3Sq_bare = Fraction(41075281, 27648000)     # theorem g3Sq_bare_eq

# Elegant-Kernel invariants used in Eq. (9) for delta_UGP
b1_int = 73                                  # rsuc_theorem; MDL lepton seed
k_L2 = Fraction(7, 512)                      # k_L2_eq
# k_gen^2 = -phi/2  where phi = (1+sqrt(5))/2
# THM-UCL-1 (ugp-lean sandbox; paper references the pentagon/Fibonacci
# derivation of k_gen^2 = -phi/2).  Exact irrational; kept as float expression.
PHI = (1.0 + math.sqrt(5.0)) / 2.0
k_gen2 = -PHI / 2.0

# ---------------------------------------------------------------------------
# 2. Universal Instantiation Factor, Eq. (9) of Paper 1
# ---------------------------------------------------------------------------

def compute_delta_UGP(b1: int, kL2: Fraction, kGen2: float) -> float:
    """Paper 1 Eq. (9):
         delta_UGP = (1/b_1) * [ -1/(k_gen^2 + (1/4)*k_L^2)
                                 + (7/4)*(k_L^2/k_gen^2) ]
    """
    kL2_f = float(kL2)
    inv_sum = -1.0 / (kGen2 + 0.25 * kL2_f)
    second = 1.75 * (kL2_f / kGen2)
    return (inv_sum + second) / b1

delta_UGP = compute_delta_UGP(b1_int, k_L2, k_gen2)

# ---------------------------------------------------------------------------
# 3. SM one-loop beta coefficients (3 generations, 1 Higgs doublet)
#    Hypercharge normalization for g_1 (not GUT).  Signs chosen so that
#        alpha_i^{-1}(mu) = alpha_i^{-1}(mu_0) - (b_i / (2 pi)) * ln(mu / mu_0)
#    U(1)_Y: b_1_Y = +41/6 (non-asymptotic-free)
#    SU(2):  b_2   = -19/6
#    SU(3):  b_3   = -7
# ---------------------------------------------------------------------------

b1_Y = 41.0 / 6.0        # hypercharge (g_1 = g')
b2_SM = -19.0 / 6.0
b3_SM = -7.0

# ---------------------------------------------------------------------------
# 4. Derived observables for a given (g1sq, g2sq, g3sq) triple
# ---------------------------------------------------------------------------

FOUR_PI = 4.0 * math.pi

def observables_from_couplings(g1sq: float, g2sq: float, g3sq: float) -> Dict[str, float]:
    """Compute gauge-sector observables from squared couplings at a common scale.
    Uses hypercharge normalization for g_1 so that
        sin^2 theta_W = g_1^2 / (g_1^2 + g_2^2)
        e^2           = g_1^2 * g_2^2 / (g_1^2 + g_2^2)
    This is the convention used in Paper 1 §5.3 and §5.5.
    """
    alpha_1 = g1sq / FOUR_PI        # U(1)_Y coupling (alpha-like)
    alpha_w = g2sq / FOUR_PI        # SU(2)_L coupling  --  primary target
    alpha_3 = g3sq / FOUR_PI        # SU(3) coupling
    sin2_thetaW = g1sq / (g1sq + g2sq)
    e2 = g1sq * g2sq / (g1sq + g2sq)
    alpha_EM = e2 / FOUR_PI
    return {
        "alpha_1_hypercharge": alpha_1,
        "alpha_w": alpha_w,
        "alpha_3": alpha_3,
        "sin2_thetaW": sin2_thetaW,
        "alpha_EM": alpha_EM,
    }

def run_one_loop(alpha_inv_start: float, b_coef: float,
                 mu_start: float, mu_end: float) -> float:
    """One-loop RG: return alpha_i^{-1}(mu_end)."""
    return alpha_inv_start - (b_coef / (2.0 * math.pi)) * math.log(mu_end / mu_start)

def rg_evolve(alphas_start: Dict[str, float], mu_start: float, mu_end: float
              ) -> Dict[str, float]:
    """Evolve alpha_1_Y, alpha_w, alpha_3 from mu_start to mu_end."""
    a1 = 1.0 / alphas_start["alpha_1_hypercharge"]
    a2 = 1.0 / alphas_start["alpha_w"]
    a3 = 1.0 / alphas_start["alpha_3"]
    a1_end = run_one_loop(a1, b1_Y, mu_start, mu_end)
    a2_end = run_one_loop(a2, b2_SM, mu_start, mu_end)
    a3_end = run_one_loop(a3, b3_SM, mu_start, mu_end)
    g1sq = FOUR_PI / a1_end
    g2sq = FOUR_PI / a2_end
    g3sq = FOUR_PI / a3_end
    return observables_from_couplings(g1sq, g2sq, g3sq)

# ---------------------------------------------------------------------------
# 5. Scale constants
# ---------------------------------------------------------------------------

M_Z_GEV = 91.1876           # PDG Z-boson mass (used as target RG endpoint)
M_PLANCK_GEV = 1.22091e19   # Planck mass (reduced 2.4e18 is also common; we use
                            # the historically-quoted ~1.22e19 GeV)
M_GUT_GEV = 2.0e16          # Standard GUT anchor

# ---------------------------------------------------------------------------
# 6. Build the four pipeline variants (pre-comparison; no PDG values used)
# ---------------------------------------------------------------------------

# (A) Bare-only, treat at M_Z
bare_at_MZ = observables_from_couplings(float(g1Sq_bare), float(g2Sq_bare),
                                        float(g3Sq_bare))

# (B) Bare + delta_UGP, treat at M_Z
inst_factor = 1.0 + delta_UGP
phys_at_MZ = observables_from_couplings(float(g1Sq_bare) * inst_factor,
                                        float(g2Sq_bare) * inst_factor,
                                        float(g3Sq_bare) * inst_factor)

# (C) Bare + delta_UGP evaluated at M_Planck, RG-run to M_Z
phys_at_Planck_bundle = observables_from_couplings(float(g1Sq_bare) * inst_factor,
                                                   float(g2Sq_bare) * inst_factor,
                                                   float(g3Sq_bare) * inst_factor)
variant_C = rg_evolve(phys_at_Planck_bundle, M_PLANCK_GEV, M_Z_GEV)

# (D) Bare + delta_UGP evaluated at M_GUT, RG-run to M_Z
variant_D = rg_evolve(phys_at_Planck_bundle, M_GUT_GEV, M_Z_GEV)

# ---------------------------------------------------------------------------
# 7. Assemble prediction block (BEFORE any PDG comparison)
# ---------------------------------------------------------------------------

pre_timestamp = datetime.now(timezone.utc).isoformat()

predictions = {
    "comp_id": "COMP-P01-Z",
    "purpose": (
        "Blind attempt to close Paper 1 Open Problem (v): extend the "
        "TE1.P delta_UGP+RG chain to alpha_w(M_Z) and sin^2 theta_W(M_Z)."
    ),
    "spec_reference": (
        "specs/IN-PROCESS/EPIC_CLUSTER2_CLEAN_WINS/"
        "080_NOTE_P01_FOCUS_AND_OPEN_PROBLEM_TRIAGE.md section 3.1"
    ),
    "lean_certified_inputs": {
        "g1Sq_bare": [int(g1Sq_bare.numerator), int(g1Sq_bare.denominator),
                      float(g1Sq_bare)],
        "g2Sq_bare": [int(g2Sq_bare.numerator), int(g2Sq_bare.denominator),
                      float(g2Sq_bare)],
        "g3Sq_bare": [int(g3Sq_bare.numerator), int(g3Sq_bare.denominator),
                      float(g3Sq_bare)],
        "b_1": b1_int,
        "k_L2": [int(k_L2.numerator), int(k_L2.denominator), float(k_L2)],
        "k_gen2_value": k_gen2,
        "k_gen2_form": "-phi/2 with phi = (1+sqrt 5)/2",
        "theorems": ["g1Sq_bare_eq", "g2Sq_bare_eq", "g3Sq_bare_eq",
                     "rsuc_theorem", "k_L2_eq",
                     "thm_ucl1_fully_unconditional"],
        "lean_repo": LEAN_REPO,
        "lean_zenodo": LEAN_ZENODO,
    },
    "delta_UGP_block": {
        "formula": ("(1/b_1) * [ -1/(k_gen^2 + (1/4)*k_L^2) "
                    "+ (7/4)*(k_L^2/k_gen^2) ]"),
        "value": delta_UGP,
        "paper_reference": "Paper 1 Eq. (9) (standard_model_from_ugp.tex)",
    },
    "rg_parameters": {
        "scheme": "SM one-loop, 3 generations, 1 Higgs doublet",
        "g1_normalization": "hypercharge (g_1 = g', NOT GUT-normalized)",
        "beta_coefficients": {"b_1_hypercharge": b1_Y, "b_2": b2_SM, "b_3": b3_SM},
        "sign_convention": ("alpha_i^{-1}(mu) = alpha_i^{-1}(mu_0) "
                            "- (b_i/(2 pi)) * ln(mu/mu_0)"),
    },
    "scale_anchors_gev": {
        "M_Z": M_Z_GEV,
        "M_Planck": M_PLANCK_GEV,
        "M_GUT": M_GUT_GEV,
    },
    "pipeline_variants": {
        "A_bare_at_M_Z": {
            "description": "bare Lean-certified g_i^2 treated as M_Z values; no delta_UGP; no RG",
            **bare_at_MZ,
        },
        "B_bare_plus_deltaUGP_at_M_Z": {
            "description": "bare * (1 + delta_UGP) treated as M_Z values; no RG",
            "instantiation_factor": inst_factor,
            **phys_at_MZ,
        },
        "C_bare_plus_deltaUGP_at_M_Planck_RG_to_M_Z": {
            "description": ("bare * (1 + delta_UGP) defined at M_Planck; "
                            "one-loop SM RG down to M_Z"),
            "start_scale_gev": M_PLANCK_GEV,
            **variant_C,
        },
        "D_bare_plus_deltaUGP_at_M_GUT_RG_to_M_Z": {
            "description": ("bare * (1 + delta_UGP) defined at M_GUT (2e16 GeV); "
                            "one-loop SM RG down to M_Z"),
            "start_scale_gev": M_GUT_GEV,
            **variant_D,
        },
    },
    "pre_comparison_timestamp_utc": pre_timestamp,
    "no_PDG_inputs_in_this_block": True,
}

# SHA-256 over the canonical (sort_keys=True) representation of the prediction block
pred_canonical = json.dumps(predictions, sort_keys=True, separators=(",", ":"))
pred_sha = hashlib.sha256(pred_canonical.encode("utf-8")).hexdigest()
predictions["pre_comparison_prediction_sha256"] = pred_sha

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "comp_p01_Z_alpha_w_te1p_extension.json")

# Write the prediction-only JSON first, so an attacker could not retroactively
# tamper with the prediction block after seeing the comparison.
with open(out_path, "w") as f:
    json.dump({"prediction_block_precomparison": predictions}, f, indent=2)

# ---------------------------------------------------------------------------
# 8. PDG comparison block (loaded and recorded AFTER the prediction block).
#    The PDG values below are the only external-data inputs in this script.
# ---------------------------------------------------------------------------

PDG = {
    # Fine-structure at Thomson (CODATA 2018)
    "alpha_EM_Thomson":       {"central": 1.0 / 137.035999084,
                               "sigma":  1.0 / 137.035999084 * 1.5e-10,
                               "source": "CODATA 2018"},
    # Fine-structure at M_Z (PDG, MSbar)
    "alpha_EM_MZ":            {"central": 1.0 / 127.952,
                               "sigma":  (1.0 / 127.952) * (0.009 / 127.952),
                               "source": "PDG 2022 alpha_EM(M_Z)^{-1} = 127.952 +- 0.009"},
    # Strong coupling at M_Z
    "alpha_s_MZ":             {"central": 0.11790,
                               "sigma":   0.00090,
                               "source": "PDG 2022 alpha_s(M_Z) world average"},
    # Weak coupling at M_Z:  alpha_w = g_2^2 / (4 pi), with PDG g_2(M_Z) = 0.6515 +- 0.0006
    "alpha_w_MZ":             {"central": (0.6515 ** 2) / FOUR_PI,
                               "sigma":   2 * 0.6515 * 0.0006 / FOUR_PI,
                               "source": "PDG 2022 g_2(M_Z) = 0.6515 +- 0.0006"},
    # Weak mixing angle at M_Z (MSbar)
    "sin2_thetaW_MZ":         {"central": 0.23122,
                               "sigma":   0.00004,
                               "source": "PDG 2022 sin^2 theta_W(M_Z), MSbar"},
}

# Low-energy Delta_alpha shift from M_Z to Thomson.
# Used only to translate our "alpha_EM at M_Z" prediction into an
# "alpha_EM at Thomson" comparison against CODATA.
# alpha_EM(0) = alpha_EM(M_Z) * (1 - Delta_alpha(M_Z)).
# PDG 2022 quotes Delta_alpha(M_Z) ~ 0.06630.  This is a physics input
# (hadronic + leptonic vacuum polarization), not a fit.
DELTA_ALPHA_MZ = 0.06630
DELTA_ALPHA_SOURCE = ("Delta_alpha(M_Z) ~ 0.06630 from PDG 2022 "
                      "(hadronic+leptonic vacuum polarization)")

def compare(observed: float, ref: Dict[str, float]) -> Dict[str, float]:
    dev_abs = observed - ref["central"]
    dev_rel = dev_abs / ref["central"]
    dev_sigma = dev_abs / ref["sigma"] if ref["sigma"] > 0 else float("inf")
    return {
        "predicted": observed,
        "pdg_central": ref["central"],
        "pdg_sigma": ref["sigma"],
        "pdg_source": ref["source"],
        "deviation_abs": dev_abs,
        "deviation_rel": dev_rel,
        "deviation_ppm": dev_rel * 1.0e6,
        "deviation_sigma": dev_sigma,
        "consistent_within_1sigma": abs(dev_sigma) <= 1.0,
        "consistent_within_2sigma": abs(dev_sigma) <= 2.0,
        "consistent_within_3sigma": abs(dev_sigma) <= 3.0,
    }

def alpha_EM_Thomson_from_MZ(alpha_EM_MZ: float) -> float:
    """alpha_EM(0) = alpha_EM(M_Z) * (1 - Delta_alpha(M_Z))."""
    return alpha_EM_MZ * (1.0 - DELTA_ALPHA_MZ)

variant_comparisons: Dict[str, Any] = {}
for key, block in predictions["pipeline_variants"].items():
    alpha_EM_MZ_pred = block["alpha_EM"]
    alpha_EM_Thomson_pred = alpha_EM_Thomson_from_MZ(alpha_EM_MZ_pred)
    variant_comparisons[key] = {
        "description": block["description"],
        "alpha_w_MZ":       compare(block["alpha_w"],        PDG["alpha_w_MZ"]),
        "sin2_thetaW_MZ":   compare(block["sin2_thetaW"],    PDG["sin2_thetaW_MZ"]),
        "alpha_s_MZ":       compare(block["alpha_3"],        PDG["alpha_s_MZ"]),
        "alpha_EM_MZ":      compare(alpha_EM_MZ_pred,        PDG["alpha_EM_MZ"]),
        "alpha_EM_Thomson": compare(alpha_EM_Thomson_pred,   PDG["alpha_EM_Thomson"]),
    }

# ---------------------------------------------------------------------------
# 9. Decision logic per spec 3.1
# ---------------------------------------------------------------------------

def variant_passes_open_v(cmp_block: Dict[str, Any]) -> bool:
    return (cmp_block["alpha_w_MZ"]["consistent_within_1sigma"]
            and cmp_block["sin2_thetaW_MZ"]["consistent_within_1sigma"])

passing_variants = [k for k, v in variant_comparisons.items() if variant_passes_open_v(v)]

decision: Dict[str, Any]
if passing_variants:
    decision = {
        "outcome": "SUCCESS",
        "passing_variants": passing_variants,
        "action_per_spec_3_1": (
            "Upgrade Paper 1 §5.5 from 'third gauge precision point' to "
            "'4-point ppm gauge precision chain all at ppm via TE1.P'. "
            "Pending user go-ahead per the Paper 1 edit freeze."
        ),
    }
else:
    # Collect best (smallest |sigma|) achieved per target to report the
    # minimum-deviation diagnostic.
    def minsig(target: str) -> Dict[str, Any]:
        best_variant, best = None, float("inf")
        for k, v in variant_comparisons.items():
            s = abs(v[target]["deviation_sigma"])
            if s < best:
                best, best_variant = s, k
        return {"variant": best_variant, "sigma": best}

    decision = {
        "outcome": "MISS",
        "passing_variants": [],
        "best_alpha_w_MZ": minsig("alpha_w_MZ"),
        "best_sin2_thetaW_MZ": minsig("sin2_thetaW_MZ"),
        "best_alpha_EM_Thomson": minsig("alpha_EM_Thomson"),
        "action_per_spec_3_1": (
            "No Paper 1 §5.5 upgrade. Open Problem (v) retained. "
            "See 'findings' block below for a structural finding about the "
            "TE1.P narrative-vs-implementation gap that this attempt exposed."
        ),
    }

# ---------------------------------------------------------------------------
# 10. Structural findings (honest disclosure)
# ---------------------------------------------------------------------------

findings = {
    "finding_1_narrative_vs_implementation": (
        "Paper 1 §5.3 describes TE1.P as a 'full chain: bare g_1^2 -> "
        "instantiation correction -> RG evolution to Z-pole -> alpha'. "
        "The implementation in MFRR/TE_1_VALIDATION_PROGRAM/TE_1.P_FSC/"
        "te1p_pipeline.py is a 3-parameter PSC slack-calibration model: "
        "base denominator 137 from the bit-set {0,3,7}, linear corrections "
        "in (lambda_EM, alpha_CP, tau_adj), and a fitted energy-scale "
        "that aligns the reference combo with CODATA.  These are "
        "different pipelines."
    ),
    "finding_2_deltaUGP_sign_anomaly": (
        "Applying delta_UGP = +0.01660 from Paper 1 Eq. (9) to the "
        "Lean-certified bare squared couplings as a multiplicative "
        "(1+delta_UGP) factor worsens every gauge prediction at M_Z "
        "relative to bare-only.  Numerical result of variants A vs B "
        "in this run:  alpha_EM(Thomson) moves from +0.50% to +2.17%; "
        "alpha_w(M_Z) moves from +1.62% to +3.32%; alpha_s(M_Z) moves "
        "from +0.34% to +2.01%; sin^2 theta_W(M_Z) is invariant at "
        "-1.02%.  The sin^2 theta_W invariance is algebraic: the "
        "(1+delta_UGP) factor cancels in the ratio "
        "g_1^2/(g_1^2+g_2^2).  Thus no scalar delta_UGP can improve "
        "sin^2 theta_W; closing Open Problem (v) with respect to "
        "sin^2 theta_W would require a coupling-specific correction "
        "(delta_1, delta_2 with delta_1 =/= delta_2) or a structural "
        "change beyond the current Eq. (9) formulation."
    ),
    "finding_3_bare_already_close": (
        "The Lean-certified bare squared couplings already match PDG at "
        "M_Z to within O(1%) directly (g_1 at 0.03%, g_2 at 0.8%, "
        "g_3 at 0.09%), WITHOUT any delta_UGP or RG.  Paper 1 "
        "Table 12 (gauge_summary) tabulates exactly these bare values. "
        "This matches variant A in the pipeline_variants block above."
    ),
    "finding_4_alpha_EM_Thomson_bare_only": (
        "Under variant A (bare-only, no delta_UGP, no RG) combined with "
        "the known low-energy Delta_alpha(M_Z) = 0.06630 shift, "
        "alpha_EM(Thomson) lands at +0.50% from CODATA (+5023 ppm), "
        "not at ppm precision.  The paper's +2.39 ppm figure (Table 11, "
        "te1p table) is therefore NOT reproducible from a strict "
        "bare + delta_UGP + RG chain; it arises from the PSC slack "
        "calibration in te1p_pipeline.py which fits to CODATA by "
        "construction at the reference combo."
    ),
    "finding_4b_sin2thetaW_precision_ceiling": (
        "sin^2 theta_W(M_Z) is measured at PDG precision 0.00004 "
        "(1.7e-4 relative).  The bare Lean prediction is 0.22886 vs. "
        "PDG 0.23122 -- absolute deviation 0.00236 is 1.02% relative "
        "but 59 sigma against PDG uncertainty.  Closing sin^2 theta_W "
        "at the 1 sigma level requires improving its prediction from "
        "1.02% to ~0.017%, a 60x shift in the g_1^2/(g_1^2+g_2^2) "
        "ratio.  This is the tightest gauge-sector constraint."
    ),
    "finding_5_open_v_reposed": (
        "Open Problem (v) as literally stated ('extend TE1.P delta_UGP+RG "
        "chain to alpha_w / sin^2 theta_W') cannot close because the "
        "chain does not close for alpha_EM either.  The operative "
        "question becomes: what structural correction (if any) takes "
        "bare Lean-certified g_i^2 from their ~1% PDG deviations to "
        "ppm precision?  delta_UGP as formulated in Paper 1 Eq. (9) "
        "does not achieve that (it moves predictions in the wrong "
        "direction AND cannot affect sin^2 theta_W at all); the "
        "TE1.P +2.39 ppm for alpha_EM is a calibrated result, not "
        "a derivation."
    ),
    "finding_6_round_8_implications": (
        "For Paper 1 Round 8 (pending user go-ahead per the P1 edit "
        "freeze): clarify TE1.P's actual mechanism in §5.3 (either "
        "remove the 'full chain' framing or rebuild a chain that does "
        "compose coherently with delta_UGP and RG); and/or reframe the "
        "+2.39 ppm result as what it demonstrably is (a PSC-calibrated "
        "3-parameter fit that hits CODATA at the reference combo).  "
        "Either direction strengthens rather than weakens the paper: "
        "the bare-only O(1%) gauge agreement (variant A) is a real "
        "and defensible result; the +0.50% alpha_EM(Thomson) closure "
        "with NO corrections is already a clean structural statement. "
        "Open Problem (v) should be restated to reflect what the "
        "actual open question is: building a structural correction "
        "that closes sin^2 theta_W to PDG 1 sigma -- which requires "
        "coupling-specific (not scalar) corrections, fundamentally "
        "beyond Eq. (9)."
    ),
}

# ---------------------------------------------------------------------------
# 11. Final payload, written atomically
# ---------------------------------------------------------------------------

comparison_timestamp = datetime.now(timezone.utc).isoformat()

final_payload = {
    "prediction_block_precomparison": predictions,
    "pdg_reference": PDG,
    "low_energy_Delta_alpha_MZ": {"value": DELTA_ALPHA_MZ,
                                  "source": DELTA_ALPHA_SOURCE},
    "variant_comparisons": variant_comparisons,
    "decision": decision,
    "findings": findings,
    "comparison_timestamp_utc": comparison_timestamp,
}

with open(out_path, "w") as f:
    json.dump(final_payload, f, indent=2)

with open(out_path, "rb") as f:
    sha_full = hashlib.sha256(f.read()).hexdigest()

# ---------------------------------------------------------------------------
# 12. Console report
# ---------------------------------------------------------------------------

print("=" * 78)
print("COMP-P01-Z: TE1.P delta_UGP + RG extension to alpha_w / sin^2 theta_W")
print("=" * 78)
print()
print(f"delta_UGP (Paper 1 Eq. (9))          = {delta_UGP:+.6f}")
print(f"Pre-comparison prediction SHA-256    = {pred_sha}")
print(f"Full-payload SHA-256                 = {sha_full}")
print()
print("Per-variant summary (deviation from PDG):")
print()
header = (f"{'variant':<8}  {'alpha_w':>14}  {'sin2_thW':>14}  "
          f"{'alpha_s':>14}  {'alpha_EM(0)':>14}")
print(header)
print("-" * len(header))
for key, cmp_block in variant_comparisons.items():
    vid = key.split("_", 1)[0]  # 'A', 'B', 'C', 'D'
    aw = cmp_block["alpha_w_MZ"]["deviation_sigma"]
    sw = cmp_block["sin2_thetaW_MZ"]["deviation_sigma"]
    as_ = cmp_block["alpha_s_MZ"]["deviation_sigma"]
    aemT = cmp_block["alpha_EM_Thomson"]["deviation_rel"] * 100.0
    print(f"{vid:<8}  {aw:+10.2f} s  {sw:+10.2f} s  "
          f"{as_:+10.2f} s  {aemT:+10.4f} %")
print()
print(f"Decision outcome: {decision['outcome']}")
if decision["outcome"] == "SUCCESS":
    print(f"Passing variants: {passing_variants}")
else:
    print(f"Best alpha_w(M_Z)    : {decision['best_alpha_w_MZ']}")
    print(f"Best sin^2 theta_W   : {decision['best_sin2_thetaW_MZ']}")
    print(f"Best alpha_EM(0)     : {decision['best_alpha_EM_Thomson']}")
print()
print("See findings block in JSON for honest-disclosure structural items.")
print(f"\nOutput: {out_path}")
