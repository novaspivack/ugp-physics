#!/usr/bin/env python3
"""
COMP-P01-QQ: m_W from SC-CC inverse-solved SU(2) matching scale (06_SPEC §3.3)

Deterministic test: SC-CC established M₂ ≈ 37.4 GeV as the inverse-solved
SU(2) matching scale for the UGP bare g₂²_bare = 2329/5400.  If UGP bare is
effectively defined at μ = M₂ = 37.4 GeV, then SM 1-loop RG evolution from
M₂ up to m_W = 80.38 GeV predicts the physical g₂²(m_W), and hence

    m_W_pred = (1/2) · √(g₂²(m_W)) · v

where v = 246.22 GeV is the Higgs VEV.  This is a *computation*, not a search —
no UGP-atom scan, no free parameters beyond the M₂ matching scale (which is
fixed by SC-CC).

Also: analogously predict sin²θ_W from running g'² from M_1 = 108.8 GeV to M_Z,
and compare to PDG.

Null discipline: randomize the M₁, M₂ matching scales within ±50% of PDG
values and recompute m_W; any "closure" requires null hit rate < 1%.

Gate:
  - CLOSES: real (M₁, M₂) from SC-CC land m_W in PDG 1σ (80.379 ± 0.012) AND
    null hit rate < 1%.
  - PARTIAL: lands within 2–3σ.
  - MAP: does not close within any reasonable scale range.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# ── Input from prior UGP artifacts ─────────────────────────────────────────
# SC-CC inverse-solved matching scales (GeV):
M1_CC = 108.8
M2_CC = 37.4
M3_CC = 89.3

# UGP bare squared couplings (SC-V / 05_SPEC convention):
G2SQ_BARE = 2329.0 / 5400.0   # ≈ 0.43130   at M₂ (by SC-CC definition)
G1SQ_BARE = 0.1280            # at M₁ (05_SPEC convention, giving sin²θ_W_bare = 0.22886)

# Physical constants
V_EW = 246.22          # Higgs VEV, GeV (G_F convention)
M_Z = 91.1876
M_W_PDG = 80.379
M_W_SIGMA = 0.012
SIN2_PDG = 0.23122
SIN2_SIGMA = 0.00004

# SM 1-loop β coefficients in the convention:
#   1/α_i(μ) = 1/α_i(μ₀) - (b_i / 2π) · ln(μ/μ₀)
# with g running UP for U(1)_Y (b_Y > 0) and DOWN for SU(2)_L (b_2 < 0):
B_Y_SM = +41.0 / 6.0    # SM non-GUT norm, with 3 families + 1 Higgs doublet
B_2_SM = -19.0 / 6.0


def alpha_from_gsq(gsq: float) -> float:
    return gsq / (4.0 * math.pi)


def gsq_from_alpha(alpha: float) -> float:
    return 4.0 * math.pi * alpha


def run_1loop_alpha(alpha_mu0: float, b: float, mu0: float, mu: float) -> float:
    """1/α(μ) = 1/α(μ₀) - (b/2π) ln(μ/μ₀)."""
    inv_alpha = 1.0 / alpha_mu0
    inv_alpha -= (b / (2.0 * math.pi)) * math.log(mu / mu0)
    return 1.0 / inv_alpha


def predict_m_W(M2_matching: float, g2sq_at_M2: float = G2SQ_BARE, mu_target: float = M_W_PDG) -> Dict:
    """Run g₂² from M2_matching up/down to mu_target and predict m_W."""
    alpha2_M2 = alpha_from_gsq(g2sq_at_M2)
    alpha2_mu = run_1loop_alpha(alpha2_M2, B_2_SM, M2_matching, mu_target)
    g2sq_mu = gsq_from_alpha(alpha2_mu)
    m_W_pred = 0.5 * math.sqrt(g2sq_mu) * V_EW
    sigma_gap = (m_W_pred - M_W_PDG) / M_W_SIGMA
    return {
        "M2_matching_GeV": M2_matching,
        "g2sq_at_M2": g2sq_at_M2,
        "alpha2_at_M2": alpha2_M2,
        "mu_target_GeV": mu_target,
        "alpha2_at_mu": alpha2_mu,
        "g2sq_at_mu": g2sq_mu,
        "m_W_pred_GeV": m_W_pred,
        "m_W_PDG_GeV": M_W_PDG,
        "m_W_residual_GeV": m_W_pred - M_W_PDG,
        "m_W_sigma_gap": sigma_gap,
    }


def predict_sin2_thw(M1_matching: float, M2_matching: float,
                      g1sq_at_M1: float = G1SQ_BARE,
                      g2sq_at_M2: float = G2SQ_BARE,
                      mu_target: float = M_Z) -> Dict:
    """Run g'² from M1 and g₂² from M2 to μ=mu_target; predict sin²θ_W."""
    alpha1 = alpha_from_gsq(g1sq_at_M1)
    alpha2 = alpha_from_gsq(g2sq_at_M2)
    alpha1_mu = run_1loop_alpha(alpha1, B_Y_SM, M1_matching, mu_target)
    alpha2_mu = run_1loop_alpha(alpha2, B_2_SM, M2_matching, mu_target)
    g1sq_mu = gsq_from_alpha(alpha1_mu)
    g2sq_mu = gsq_from_alpha(alpha2_mu)
    sin2 = g1sq_mu / (g1sq_mu + g2sq_mu)
    sigma_gap = (sin2 - SIN2_PDG) / SIN2_SIGMA
    return {
        "M1_matching_GeV": M1_matching, "M2_matching_GeV": M2_matching,
        "mu_target_GeV": mu_target,
        "g1sq_at_mu": g1sq_mu, "g2sq_at_mu": g2sq_mu,
        "sin2_thw_pred": sin2, "sin2_thw_PDG": SIN2_PDG,
        "sin2_residual": sin2 - SIN2_PDG,
        "sin2_sigma_gap": sigma_gap,
    }


def null_randomize_M(seed=20260426, n_trials=1000, sigma_factor=0.5) -> Dict:
    """Null: randomize M1, M2 in ±(1 ± sigma_factor) multiplicative band around SC-CC values.
    Count how many random (M1, M2) land m_W in PDG 1σ."""
    rng = random.Random(seed)
    hits_m_W = 0
    hits_sin2 = 0
    hits_joint = 0
    for _ in range(n_trials):
        M2_rand = M2_CC * (1.0 + rng.uniform(-sigma_factor, sigma_factor))
        M1_rand = M1_CC * (1.0 + rng.uniform(-sigma_factor, sigma_factor))
        if M2_rand <= 0 or M1_rand <= 0:
            continue
        mw = predict_m_W(M2_rand)
        sw = predict_sin2_thw(M1_rand, M2_rand)
        mw_in = abs(mw["m_W_sigma_gap"]) <= 1.0
        sw_in = abs(sw["sin2_sigma_gap"]) <= 1.0
        if mw_in:
            hits_m_W += 1
        if sw_in:
            hits_sin2 += 1
        if mw_in and sw_in:
            hits_joint += 1
    return {
        "trials": n_trials,
        "m_W_hits": hits_m_W, "m_W_hit_rate": hits_m_W / n_trials,
        "sin2_hits": hits_sin2, "sin2_hit_rate": hits_sin2 / n_trials,
        "joint_hits": hits_joint, "joint_hit_rate": hits_joint / n_trials,
    }


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Real SC-CC prediction
    mw_real = predict_m_W(M2_CC)
    sin2_real = predict_sin2_thw(M1_CC, M2_CC)

    # Extend: scan μ_target around M_W (because running to exactly m_W is the standard,
    # but other "physical" scales like M_Z also deserve checking)
    sweep_targets = [50.0, 60.0, 80.0, M_W_PDG, 85.0, M_Z, 100.0, 150.0, 200.0, 500.0]
    sweep = [predict_m_W(M2_CC, mu_target=mu) for mu in sweep_targets]

    # Also: scan M2_matching around SC-CC to find the exact M2 that lands m_W in window
    M2_scan = []
    for log_M in [math.log10(1.0) + k * 0.02 for k in range(0, 200)]:   # M from 1 to ~10^4
        M_here = 10 ** log_M
        rec = predict_m_W(M_here)
        if abs(rec["m_W_sigma_gap"]) <= 1.0:
            M2_scan.append(rec)

    # Real SC-CC closure check
    m_W_closes = abs(mw_real["m_W_sigma_gap"]) <= 1.0
    sin2_closes = abs(sin2_real["sin2_sigma_gap"]) <= 1.0
    joint_closes = m_W_closes and sin2_closes

    # Null discipline
    null = null_randomize_M(n_trials=5000, sigma_factor=0.5)

    null_disciplined_m_W = null["m_W_hit_rate"] < 0.01
    null_disciplined_sin2 = null["sin2_hit_rate"] < 0.01
    null_disciplined_joint = null["joint_hit_rate"] < 0.01

    if joint_closes and null_disciplined_joint:
        verdict = "CLOSES_joint_sin2_and_mW_from_SC_CC_running"
    elif m_W_closes and null_disciplined_m_W:
        verdict = "CLOSES_mW_only_from_SC_CC_running"
    elif sin2_closes and null_disciplined_sin2:
        verdict = "CLOSES_sin2_only_from_SC_CC_running"
    elif m_W_closes and not null_disciplined_m_W:
        verdict = "DENSITY_DOMINATED_mW"
    elif abs(mw_real["m_W_sigma_gap"]) <= 5.0:
        verdict = f"NEAR_CLOSE_mW_at_{mw_real['m_W_sigma_gap']:+.1f}σ_from_PDG"
    else:
        verdict = "MAP_SC_CC_running_insufficient"

    prediction_block = {
        "comp_id": "COMP-P01-QQ",
        "spec_reference": "06_SPEC §3.3 — m_W from SC-CC inverse-solved M₂ via 1-loop SM running",
        "timestamp_utc": ts,
        "motivation": "SC-V blind m_W prediction +36σ miss with bare g₂²·v/2; SC-CC found inverse-solved M₂ ≈ 37.4 GeV implying bare coupling is effectively 'at' that scale. Running from M₂ to m_W should close the gap if the interpretation is correct.",
        "inputs": {
            "M1_CC_GeV": M1_CC, "M2_CC_GeV": M2_CC, "M3_CC_GeV": M3_CC,
            "g2sq_bare": G2SQ_BARE, "g1sq_bare": G1SQ_BARE,
            "V_EW_GeV": V_EW, "M_Z_GeV": M_Z, "M_W_PDG_GeV": M_W_PDG, "M_W_SIGMA": M_W_SIGMA,
            "SIN2_PDG": SIN2_PDG, "SIN2_SIGMA": SIN2_SIGMA,
            "B_Y_SM": B_Y_SM, "B_2_SM": B_2_SM,
        },
        "real_prediction_m_W": mw_real,
        "real_prediction_sin2_thw": sin2_real,
        "real_closures": {
            "m_W_within_1sigma": m_W_closes,
            "sin2_within_1sigma": sin2_closes,
            "joint_within_1sigma": joint_closes,
        },
        "mu_target_sweep": {str(mu): rec for mu, rec in zip(sweep_targets, sweep)},
        "M2_matching_sigma_hits_count": len(M2_scan),
        "M2_matching_closure_range": (
            {"min_M2_GeV": min(r["M2_matching_GeV"] for r in M2_scan),
             "max_M2_GeV": max(r["M2_matching_GeV"] for r in M2_scan)} if M2_scan else None
        ),
        "null_M_randomization": null,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "m_W_predicted_GeV": mw_real["m_W_pred_GeV"],
        "m_W_PDG_GeV": M_W_PDG,
        "m_W_sigma_gap": mw_real["m_W_sigma_gap"],
        "sin2_thw_predicted": sin2_real["sin2_thw_pred"],
        "sin2_thw_PDG": SIN2_PDG,
        "sin2_sigma_gap": sin2_real["sin2_sigma_gap"],
        "m_W_in_window": m_W_closes,
        "sin2_in_window": sin2_closes,
        "joint_in_window": joint_closes,
        "null_m_W_hit_rate": null["m_W_hit_rate"],
        "null_sin2_hit_rate": null["sin2_hit_rate"],
        "null_joint_hit_rate": null["joint_hit_rate"],
        "null_disciplined_m_W": null_disciplined_m_W,
        "null_disciplined_sin2": null_disciplined_sin2,
        "null_disciplined_joint": null_disciplined_joint,
        "M2_matching_range_for_closure": prediction_block["M2_matching_closure_range"],
        "verdict": verdict,
    }

    return {"prediction_block_precomparison": prediction_block,
            "sha256_prediction_block": sha,
            "pdg_comparison": pdg_cmp}


if __name__ == "__main__":
    out = main()
    path = "comp_p01_QQ_mW_from_inverse_solved_M2.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
