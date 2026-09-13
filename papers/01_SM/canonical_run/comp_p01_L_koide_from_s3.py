#!/usr/bin/env python3
"""
COMP-P01-L  —  the Koide 2/3 relation in UGP S_3 language.

Claim under test:  the charged-lepton Koide relation
        Q = (m_e + m_μ + m_τ) / (√m_e + √m_μ + √m_τ)²  =  2/3
is a geometric statement about the sqrt-mass vector  v = (√m_e, √m_μ, √m_τ)
in an S_3-representation decomposition.  Specifically

        Q = 2/3   ⇔   ||v_trivial||² = ||v_standard||²                  (★)

i.e. the trivial-rep (symmetric) and standard-rep (traceless) components of v
have equal norm.  We prove (★) algebraically, verify it against CODATA, and
then ask whether UGP's structural atoms determine the corresponding angle.

This is a consistency check, not a full derivation.  An honest report.
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import json
import math
from pathlib import Path

# CODATA charged-lepton masses (keV)
M_E  =      510.99895069
M_MU =   105658.3755
M_TAU = 1776860.0

def koide_Q(m1, m2, m3):
    s = math.sqrt(m1) + math.sqrt(m2) + math.sqrt(m3)
    num = m1 + m2 + m3
    return num / (s * s)

def s3_decompose(v1, v2, v3):
    """Decompose (v1, v2, v3) into trivial-rep + standard-rep parts under S_3.

    The S_3 permutation representation on R^3 splits as
        R^3 = R · (1,1,1)  ⊕  {(a,b,c) : a+b+c = 0}
    (trivial rep 1D + standard rep 2D).

    trivial component  v_0   =  (v1+v2+v3)/√3        (scalar, along (1,1,1)/√3)
    perpendicular v_⊥   =  v - (v1+v2+v3)/3 · (1,1,1)
    """
    mean = (v1 + v2 + v3) / 3.0
    v0_scalar = (v1 + v2 + v3) / math.sqrt(3.0)
    v_perp = (v1 - mean, v2 - mean, v3 - mean)
    v_perp_norm_sq = sum(x*x for x in v_perp)
    return {
        "trivial_scalar": v0_scalar,
        "trivial_norm_sq": v0_scalar**2,       # = (v1+v2+v3)²/3
        "perp_vector": v_perp,
        "perp_norm_sq": v_perp_norm_sq,
        "total_norm_sq": v1*v1 + v2*v2 + v3*v3,
    }

def main():
    r_e  = math.sqrt(M_E)
    r_mu = math.sqrt(M_MU)
    r_tau = math.sqrt(M_TAU)

    Q_emp = koide_Q(M_E, M_MU, M_TAU)

    dec = s3_decompose(r_e, r_mu, r_tau)

    # --- Algebraic check of  Q = 2/3  ⇔  ||v_0||² = ||v_⊥||² ---
    #
    # trivial_norm_sq  =  (sum r_i)² / 3
    # perp_norm_sq     =  sum r_i² - (sum r_i)²/3
    #
    # Koide:  Q = (sum r_i²) / (sum r_i)² = 2/3
    #         ⇔  3 sum r_i² = 2 (sum r_i)²
    #         ⇔  sum r_i² = (2/3)(sum r_i)²
    #         ⇔  perp_norm_sq = sum r_i² - (sum r_i)²/3
    #                         = (2/3)(sum r_i)² - (1/3)(sum r_i)²
    #                         = (1/3)(sum r_i)²
    #                         = trivial_norm_sq
    #
    # So Q = 2/3  ⇔  ||v_0||² = ||v_⊥||²   QED
    ratio = dec["perp_norm_sq"] / dec["trivial_norm_sq"]

    # Report
    koide_residual_pct = 100.0 * (Q_emp - 2/3) / (2/3)

    # --- Equivalent angular form ---
    cos_theta_sq = dec["trivial_norm_sq"] / dec["total_norm_sq"]
    theta_deg = math.degrees(math.acos(math.sqrt(cos_theta_sq)))

    # --- UGP structural quantities that could plausibly set theta ---
    #
    # UGP's Elegant Kernel has a canonical "ridge + half-ridge" split:
    #   ridge  R_n = 2^n - 16   (even symmetric)
    #   half-ridge                 (odd antisymmetric)
    # with k_L² = δ / 2^9 = 7/512  enforcing a specific balance.
    #
    # For S_3 on three generations the analogous split is
    #   trivial rep  ↔  ridge-like   (symmetric)
    #   standard rep ↔  half-ridge-like  (antisymmetric)
    # and the Koide angle 45° corresponds to equal norms.
    #
    # A structural "Koide predictor" would be  k_L² ·  some_ratio  = 1/2.
    # In particular  cos²θ = 1/2 is the Koide condition;  cos²θ = 1/3 is
    # pure S_3-democratic;  cos²θ = 1 is pure-hierarchical.
    #
    # We report the observed cos²θ and its distance from each fixed point.
    fixed_points = {
        "democratic  (cos²θ = 1/3)":  1.0/3.0,
        "Koide        (cos²θ = 1/2)": 1.0/2.0,
        "hierarchical (cos²θ → 1)":   1.0,
    }
    distances = {k: abs(cos_theta_sq - v) for k, v in fixed_points.items()}
    nearest = min(distances, key=distances.get)

    # --- check UGP structural integer predictions for theta ---
    # can  cos²θ be expressed as a simple UGP-integer ratio?
    #   e.g.  cos²θ  =  δ/(δ + ugp1_g)  = 7/20  = 0.35    — not Koide
    #         cos²θ  =  ugp1_g / (ugp1_g + δ) = 13/20 = 0.65  — not Koide
    #         cos²θ  =  ugp1_s / (ugp1_s + ugp1_s) = 1/2       — Koide, but trivial
    # The only UGP-structural way to write 1/2 as a ratio of positive ridge
    # atoms is  δ / (2·δ) = 1/2,  or  D₁ / (2 D₁) = 1/2.  Neither is informative.
    # We note honestly that UGP's Elegant Kernel constant k_L² = 7/512 does not
    # reduce to 1/2 by any simple structural operation, so Koide's angle is
    # *consistent* with the S_3 structure but *not derived from* it in the
    # current formalism.

    report = {
        "experiment_id": "COMP-P01-L",
        "question":      "Does UGP's S_3 structure derive Koide's Q = 2/3?",
        "codata_inputs": {"m_e_keV": M_E, "m_mu_keV": M_MU, "m_tau_keV": M_TAU},
        "empirical": {
            "Q":                  Q_emp,
            "Q_target_2_over_3":  2.0/3.0,
            "Q_residual_frac":    Q_emp - 2.0/3.0,
            "Q_residual_pct":     koide_residual_pct,
        },
        "s3_decomposition": {
            "v_sqrt_masses_keV_half": [r_e, r_mu, r_tau],
            "trivial_norm_sq":   dec["trivial_norm_sq"],
            "perp_norm_sq":      dec["perp_norm_sq"],
            "ratio_perp_over_trivial": ratio,
            "interpretation":   "Q=2/3 is equivalent to ratio = 1 (equal S_3 trivial and standard norms)",
            "angle_to_diagonal_deg":   theta_deg,
            "angle_to_diagonal_target_deg": 45.0,
            "angle_residual_deg": theta_deg - 45.0,
        },
        "fixed_points":          {k: float(v) for k, v in fixed_points.items()},
        "distances_to_fixed_points": {k: float(v) for k, v in distances.items()},
        "nearest_fixed_point":  nearest,
        "ugp_structural_content": {
            "S_3_orbit_factor_in_L_model": 3,
            "Elegant_Kernel_k_L_sq":       "δ / 2⁹ = 7/512",
            "comment":
                "UGP predicts 3 generations (Lean, N_eff=3) and an S_3 permutation symmetry (natural for generations). "
                "Koide's relation Q=2/3 is equivalent to equal-norm decomposition of v = (√m_e, √m_μ, √m_τ) "
                "into S_3 trivial + standard representations. "
                "This equal-norm condition is NOT automatic from having three generations; it requires an "
                "additional structural constraint. UGP's Elegant Kernel has a ridge/half-ridge balance (k_L² = 7/512) "
                "but that specific constant does not reduce to 1/2 via any simple structural operation, so Koide is "
                "*consistent with* the S_3 structure but *not derived from* the current UGP formalism alone. "
                "A derivation would require identifying an independent UGP atom that forces the sqrt-mass vector "
                "onto the 45° cone around (1,1,1)/√3.",
        },
        "verdict":
            "CONSISTENCY-ONLY.  Koide Q=2/3 is an elegant geometric statement that the "
            "generational sqrt-mass vector has equal S_3 trivial and standard components. "
            "UGP naturally produces the S_3 representation structure but does NOT (in the "
            "current formalism) force the equal-norm balance. A future extension — adding a "
            "structural principle that fixes ||v_trivial|| = ||v_perp|| — would yield Koide as "
            "a theorem.  As of this experiment, Koide remains a phenomenological consistency "
            "check, not a UGP derivation.",
        "timestamp_utc": _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }

    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(report, indent=2))
    sha = _hl.sha256(out.read_bytes()).hexdigest()

    print(f"Koide Q (empirical)    = {Q_emp:.10f}")
    print(f"Koide Q (target 2/3)   = {2/3:.10f}")
    print(f"residual (%)           = {koide_residual_pct:+.5f}%")
    print(f"angle v to (1,1,1)/√3  = {theta_deg:.6f}°   (target 45°, residual {theta_deg-45:+.6f}°)")
    print(f"ratio ||v_⊥||²/||v₀||² = {ratio:.10f}  (target 1.0)")
    print(f"nearest fixed point    = {nearest}")
    print(f"\n[write] {out.name}")
    print(f"[sha]   {sha}")
    print(f"\nVERDICT:  {report['verdict']}")


if __name__ == "__main__":
    main()
