#!/usr/bin/env python3
"""
COMP-P01-N  —  UGP-anchored + Koide-constrained charged-lepton composite test.

Given the findings of K, L, M:
  (K) m_e = δ·b₁ keV to 2 ppm  (Lean-certified UGP integers; p < 0.01)
  (L) Koide Q = 2/3  ⇔  ||v_trivial||² = ||v_standard||²   (S_3 equal-norm)
  (M) UGP cannot derive keV scale intrinsically; absolute masses require
       at least one dimensional anchor.

This experiment asks:  given ONE UGP structural anchor (m_e = δ·b₁ keV) and
ONE S_3 constraint (Koide equal-norm, which UGP's S_3 structure makes
natural), can we predict m_τ from m_μ (or vice versa), at ppm-class
precision?

  3(r_e² + r_μ² + r_τ²)  =  2 (r_e + r_μ + r_τ)²        [Koide]
  ⇒ r_τ = 2(r_e+r_μ) ± √(6(r_e+r_μ)² − 3r_e² − 3r_μ²)

We test four configurations:
   cfg 1 :  r_e from UGP (δ·b₁), r_μ from CODATA → predict r_τ
   cfg 2 :  r_e from UGP,        r_τ from PDG   → predict r_μ
   cfg 3 :  r_e, r_μ both from CODATA            → predict r_τ   (pure Koide, baseline)
   cfg 4 :  r_e, r_τ both from CODATA            → predict r_μ   (pure Koide, baseline)

The difference  (cfg 1 − cfg 3)  isolates the effect of replacing the
electron CODATA value with the UGP structural value.

Output:  comp_p01_N_koide_anchored_composite.json
"""
from __future__ import annotations
import datetime as _dt, hashlib as _hl, json, math
from pathlib import Path

M_E   =      510.99895069   # CODATA
M_MU  =   105658.3755       # CODATA
M_TAU = 1776860.0           # PDG

UGP_M_E = 7 * 73            # = 511 keV exactly (UGP structural prediction)

def predict_third_via_koide(r_known1: float, r_known2: float,
                            larger: bool = True) -> tuple[float, float]:
    """Given two sqrt-masses, return the two Koide-consistent sqrt-masses.

    Koide:  3(r1² + r2² + r3²)  =  2(r1 + r2 + r3)²
            ⇒  r3² − 4(r1+r2) r3 + (3r1² + 3r2² − 2(r1+r2)²)  = 0
            ⇒  r3 = 2(r1+r2) ± √(6(r1+r2)² − 3r1² − 3r2²)
    """
    S = r_known1 + r_known2
    disc = 6 * S*S - 3 * r_known1*r_known1 - 3 * r_known2*r_known2
    if disc < 0:
        return (float("nan"), float("nan"))
    root = math.sqrt(disc)
    r_plus  = 2 * S + root
    r_minus = 2 * S - root
    return (r_plus, r_minus)

def ppm(pred, ref):
    return 1e6 * abs(pred - ref) / ref

def main() -> int:
    r_e_codata = math.sqrt(M_E)
    r_mu_codata = math.sqrt(M_MU)
    r_tau_pdg = math.sqrt(M_TAU)
    r_e_ugp = math.sqrt(UGP_M_E)

    configs = {}

    # --- cfg 1: r_e from UGP, r_μ from CODATA → predict r_τ
    plus, minus = predict_third_via_koide(r_e_ugp, r_mu_codata)
    # For charged leptons τ >> μ > e, pick the larger root (plus)
    m_tau_pred = plus * plus
    configs["cfg1_ugp_e_+_codata_mu_predict_tau"] = {
        "inputs":           {"r_e": r_e_ugp,  "r_mu": r_mu_codata},
        "prediction_mass":  m_tau_pred,
        "pdg_value":        M_TAU,
        "ppm_deviation":    ppm(m_tau_pred, M_TAU),
    }

    # --- cfg 2: r_e from UGP, r_τ from PDG → predict r_μ
    plus, minus = predict_third_via_koide(r_e_ugp, r_tau_pdg)
    # μ < τ, but the quadratic is symmetric — both roots are real candidates.
    # The PHYSICAL root: for given r_e, r_τ, the small-root is r_μ (< r_τ).
    # After solving,  r_plus > r_τ  (too large),  r_minus  is the physical μ.
    # But actually: solving for the "third" given two known is symmetric;
    # the two roots correspond to two different "third lepton" values.
    # Pick the root that is positive and < r_tau_pdg.
    if 0 < minus < r_tau_pdg:
        m_mu_pred = minus * minus
    else:
        m_mu_pred = plus * plus
    configs["cfg2_ugp_e_+_pdg_tau_predict_mu"] = {
        "inputs":           {"r_e": r_e_ugp,  "r_tau": r_tau_pdg},
        "prediction_mass":  m_mu_pred,
        "codata_value":     M_MU,
        "ppm_deviation":    ppm(m_mu_pred, M_MU),
    }

    # --- cfg 3: r_e, r_μ both CODATA → predict r_τ   (baseline pure Koide)
    plus, minus = predict_third_via_koide(r_e_codata, r_mu_codata)
    m_tau_pred_baseline = plus * plus
    configs["cfg3_codata_e_mu_predict_tau_baseline"] = {
        "inputs":           {"r_e": r_e_codata, "r_mu": r_mu_codata},
        "prediction_mass":  m_tau_pred_baseline,
        "pdg_value":        M_TAU,
        "ppm_deviation":    ppm(m_tau_pred_baseline, M_TAU),
    }

    # --- cfg 4: r_e, r_τ both CODATA → predict r_μ
    plus, minus = predict_third_via_koide(r_e_codata, r_tau_pdg)
    if 0 < minus < r_tau_pdg:
        m_mu_pred_baseline = minus * minus
    else:
        m_mu_pred_baseline = plus * plus
    configs["cfg4_codata_e_tau_predict_mu_baseline"] = {
        "inputs":           {"r_e": r_e_codata, "r_tau": r_tau_pdg},
        "prediction_mass":  m_mu_pred_baseline,
        "codata_value":     M_MU,
        "ppm_deviation":    ppm(m_mu_pred_baseline, M_MU),
    }

    # --- Compare: does swapping CODATA r_e for UGP r_e significantly change
    #     the predicted third mass?
    delta_tau_ppm = configs["cfg1_ugp_e_+_codata_mu_predict_tau"]["ppm_deviation"] - configs["cfg3_codata_e_mu_predict_tau_baseline"]["ppm_deviation"]
    delta_mu_ppm  = configs["cfg2_ugp_e_+_pdg_tau_predict_mu"]["ppm_deviation"] - configs["cfg4_codata_e_tau_predict_mu_baseline"]["ppm_deviation"]

    # --- How tight is the composite prediction?
    #
    # To be a win, cfg 1 (UGP e + CODATA μ → τ) must match m_τ at ppm-class.
    # If it's within ~1 σ of the PDG tau uncertainty (~68 ppm at 120 keV / 1.78 GeV),
    # that is a non-trivial success for UGP + Koide.
    pdg_tau_uncertainty_ppm = 1e6 * 120.0 / M_TAU  # ~67.5 ppm

    # --- Composite null: how would random integer anchors for r_e perform?
    # Replace r_e_ugp with r_e_trial = √(some_random_product), run Koide-based
    # prediction, compare to PDG.  Quantifies the "UGP-specific" advantage.
    import random
    rng = random.Random(20260417)
    null_predictions = []
    for _ in range(2000):
        # Random integer m in same magnitude window as δ·b₁ = 511
        m_trial = 511.0 * (0.95 + 0.10 * rng.random())
        r_trial = math.sqrt(m_trial)
        plus, minus = predict_third_via_koide(r_trial, r_mu_codata)
        pred = plus * plus
        null_predictions.append(ppm(pred, M_TAU))
    null_predictions.sort()
    null_median_ppm = null_predictions[len(null_predictions)//2]
    real_ppm        = configs["cfg1_ugp_e_+_codata_mu_predict_tau"]["ppm_deviation"]
    rank            = sum(1 for p in null_predictions if p < real_ppm)
    p_value         = (rank + 1) / (len(null_predictions) + 1)

    # Interpretation
    cfg1_ppm = configs["cfg1_ugp_e_+_codata_mu_predict_tau"]["ppm_deviation"]
    if cfg1_ppm < pdg_tau_uncertainty_ppm:
        label = "WITHIN PDG τ UNCERTAINTY: UGP δ·b₁ + Koide + CODATA μ is statistically indistinguishable from the measured τ mass"
    elif cfg1_ppm < 3 * pdg_tau_uncertainty_ppm:
        label = "WITHIN 3σ: promising"
    else:
        label = "OUTSIDE 3σ: not supported at current precision"

    report = {
        "experiment_id": "COMP-P01-N",
        "question":      "Does UGP anchor m_e=δ·b₁·keV + Koide 2/3 (an S_3 constraint) + ONE of (m_μ, m_τ) correctly predict the third charged-lepton mass at PDG-class precision?",
        "inputs": {
            "M_E_codata":  M_E,
            "M_MU_codata": M_MU,
            "M_TAU_pdg":   M_TAU,
            "UGP_M_E_structural_keV": UGP_M_E,
        },
        "configs": configs,
        "comparison": {
            "delta_tau_ppm_from_UGP_vs_CODATA_e": delta_tau_ppm,
            "delta_mu_ppm_from_UGP_vs_CODATA_e":  delta_mu_ppm,
            "pdg_tau_uncertainty_ppm":           pdg_tau_uncertainty_ppm,
            "label":                             label,
        },
        "null_test": {
            "n_trials":         len(null_predictions),
            "null_median_ppm":  null_median_ppm,
            "real_cfg1_ppm":    real_ppm,
            "p_value":          p_value,
            "interpretation":
                "If we replace UGP's δ·b₁ anchor with a random mass in ±5% of 511 keV and "
                "run the same Koide-based prediction, what fraction of trials predicts τ "
                "better than the UGP anchor?  A low p-value (p<0.05) indicates the UGP "
                "anchor is a *specific* good choice, not just a typical random choice.",
        },
        "verdict":
            f"With m_e=δ·b₁ (Lean-certified) + Koide 2/3 (S_3 equal-norm) + CODATA m_μ, "
            f"UGP predicts m_τ = {configs['cfg1_ugp_e_+_codata_mu_predict_tau']['prediction_mass']:.1f} keV "
            f"against PDG m_τ = {M_TAU:.1f} keV, residual {cfg1_ppm:.1f} ppm.  "
            f"PDG uncertainty is {pdg_tau_uncertainty_ppm:.1f} ppm, so the prediction is "
            f"{'INSIDE' if cfg1_ppm < pdg_tau_uncertainty_ppm else 'OUTSIDE'} current experimental precision.  "
            f"This is a one-parameter UGP+Koide model of the charged-lepton spectrum: the entire "
            f"triple is pinned by (δ, b₁, m_μ) with Koide as a rigid structural constraint.",
        "timestamp_utc": _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }

    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(report, indent=2))
    sha = _hl.sha256(out.read_bytes()).hexdigest()

    print("="*72)
    print("COMP-P01-N: UGP + Koide composite lepton prediction")
    print("="*72)
    for name, c in configs.items():
        ref_key = "pdg_value" if "predict_tau" in name else "codata_value"
        print(f"\n{name}:")
        print(f"  predicted  = {c['prediction_mass']:12.3f} keV")
        print(f"  reference  = {c[ref_key]:12.3f} keV")
        print(f"  residual   = {c['ppm_deviation']:9.3f} ppm")
    print(f"\nPDG m_τ uncertainty  ≈ {pdg_tau_uncertainty_ppm:.2f} ppm")
    print(f"cfg1 (UGP e + Koide)   = {cfg1_ppm:.2f} ppm → {label}")
    print(f"\nNull test (random anchors ±5% of 511 keV):")
    print(f"  n trials  = {len(null_predictions)}")
    print(f"  real ppm  = {real_ppm:.3f}")
    print(f"  null med  = {null_median_ppm:.3f}")
    print(f"  p-value   = {p_value:.4f}")
    print(f"\n[write] {out.name}")
    print(f"[sha]   {sha}")


if __name__ == "__main__":
    main()
