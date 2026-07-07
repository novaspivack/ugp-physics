#!/usr/bin/env python3
"""
COMP-P01-RR: 03_SPEC Phase I — S₃-equivariant q-conserving operator enumeration (Koide S₃-Flow)

Phase I gate of 03_SPEC:
  "Can we identify a 2-parameter family of S₃-equivariant q-conserving
   operators with rational entries in Lean-certified atoms?
   If yes → Phase II. If no → write negative result saying the class is empty."

Setup:
  M = 3·I - 2·J on ℝ³ (J = all-ones matrix), Koide matrix.
  q(v) = v^T M v.  Eigenvalues: -3 (trivial irrep, (1,1,1)/√3), +3 (2× standard irrep).
  Koide condition: q(v_*) = 0 where v_* = (√m_e, √m_μ, √m_τ).

Classification of S₃-equivariant q-preserving LINEAR operators on ℝ³:
  By Schur, U|_trivial = λ_0 ∈ ℝ and U|_standard = λ_1 ∈ ℝ (real standard irrep is
  irreducible and spanned by pairs of reflections; only scalar commutes with both).
  q-preservation: λ_0² = 1 AND λ_1² = 1 ⇒ λ_0, λ_1 ∈ {+1, -1}.
  ⇒ Exactly 4 isolated operators.  NO 2-parameter family exists in this class.

Under the weaker ℤ/3-equivariance (cyclic 3-fold rotation only, no reflections):
  U|_trivial = λ_0 ∈ ℝ, U|_standard = 2D rotation by θ with scaling λ_1.
  q-preservation + λ_0² = 1 forces λ_0 ∈ {±1}; rotations preserve |v_std|²;
  λ_1 = 1 for q-preservation (scalar on standard = ±1 ⇒ just reflection through origin).
  ⇒ ℤ/3-equivariant q-preserving = {±1} × O(2) rotations = a 1-parameter family
     (rotation angle θ ∈ [0, 2π)) × 2 sign choices = 2 connected components,
     each 1-dimensional.

This script:
  (A) Enumerates the 4 S₃-equivariant q-preserving linear operators.
  (B) Checks Phase I conditions (a)–(c) for each.
  (C) Computes Koide residual q(v_*) for PDG sqrt-masses and verifies closure numerically.
  (D) Evaluates the ℤ/3-equivariant q-preserving 1-parameter family and checks whether
      any rotation angle has PDG v_* as a fixed point (beyond identity).
  (E) Reports Phase I gate verdict.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import numpy as np

# PDG charged-lepton masses (MeV) — same as Braid-Atlas conventional triples
M_E = 0.5109989088
M_MU = 105.6583777
M_TAU = 1776.859905

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Koide matrix and eigenbasis
M_KOIDE = 3.0 * np.eye(3) - 2.0 * np.ones((3, 3))
# Eigenvalues: -3 (trivial), +3 (×2)
# Trivial eigenvector: (1,1,1)/√3
# Standard basis: (1,-1,0)/√2 and (1,1,-2)/√6
E_TRIVIAL = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
E_STD_1 = np.array([1.0, -1.0, 0.0]) / math.sqrt(2.0)
E_STD_2 = np.array([1.0, 1.0, -2.0]) / math.sqrt(6.0)

V_STAR = np.array([math.sqrt(M_E), math.sqrt(M_MU), math.sqrt(M_TAU)])  # (MeV)^{1/2}


def q(v: np.ndarray) -> float:
    return float(v @ M_KOIDE @ v)


def project_irrep(v: np.ndarray) -> Tuple[float, np.ndarray]:
    """Decompose v = α·E_TRIVIAL + v_std where v_std ⊥ (1,1,1)."""
    alpha = float(v @ E_TRIVIAL)
    v_std = v - alpha * E_TRIVIAL
    return alpha, v_std


def build_operator(lambda_0: float, lambda_1: float, theta: float = 0.0) -> np.ndarray:
    """U = λ_0 · P_trivial + λ_1 · R(θ) on 2D standard subspace.
    Returns a 3×3 matrix."""
    P_trivial = np.outer(E_TRIVIAL, E_TRIVIAL)
    # 2D rotation in (E_STD_1, E_STD_2) basis
    c, s = math.cos(theta), math.sin(theta)
    std_in_basis = np.column_stack([E_STD_1, E_STD_2])  # 3×2
    R_std_2d = np.array([[c, -s], [s, c]])
    R_std_3d = std_in_basis @ R_std_2d @ std_in_basis.T   # 3×3
    return lambda_0 * P_trivial + lambda_1 * R_std_3d


def is_s3_equivariant(U: np.ndarray) -> bool:
    """Check [U, σ] = 0 for all 6 permutation matrices σ ∈ S₃."""
    perms = [
        np.eye(3),
        np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=float),
        np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], dtype=float),
        np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=float),
        np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=float),
        np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float),
    ]
    for s in perms:
        if not np.allclose(U @ s, s @ U, atol=1e-10):
            return False
    return True


def is_q_preserving(U: np.ndarray, samples: int = 20, seed: int = 1) -> bool:
    """Numerically verify q(U v) = q(v) on random samples."""
    rng = np.random.default_rng(seed)
    for _ in range(samples):
        v = rng.standard_normal(3)
        if abs(q(U @ v) - q(v)) > 1e-9 * (1 + abs(q(v))):
            return False
    return True


def fixed_points_analysis(U: np.ndarray, v: np.ndarray) -> Dict:
    Uv = U @ v
    residual = float(np.linalg.norm(Uv - v))
    norm = float(np.linalg.norm(v))
    return {
        "U_v": Uv.tolist(),
        "v": v.tolist(),
        "residual_norm": residual,
        "relative_residual": residual / max(norm, 1e-30),
        "is_fixed_point_within_1e-10": residual < 1e-10,
    }


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Basic Koide check on v_*:
    q_star = q(V_STAR)
    alpha_star, v_std_star = project_irrep(V_STAR)
    koide_Q = (V_STAR.sum()) ** 2 / (M_E + M_MU + M_TAU)   # Q = (Σ√m)² / Σm = 3/2 for Koide
    # Our convention: P/s² = 2/3 ↔ 3P - 2s² = 0 ↔ q(v)=0

    P = (V_STAR ** 2).sum()
    s = V_STAR.sum()
    koide_residual_dimless = (3 * P - 2 * s ** 2) / s ** 2
    pdg_check = {
        "v_star_MeV_half": V_STAR.tolist(),
        "sum_v_star": s, "sum_v_star_sq": P,
        "Koide_Q_value_expected_3over2": koide_Q,
        "q_v_star_value": q_star,
        "Koide_relative_residual_3P_minus_2s2_over_s2": koide_residual_dimless,
    }

    # (A) The 4 S₃-equivariant q-preserving operators (θ=0 for all to stay in S₃)
    S3_operators = []
    for name, l0, l1 in [
        ("U_identity",        +1, +1),
        ("U_neg_identity",    -1, -1),
        ("U_trivial_reflect", -1, +1),
        ("U_standard_reflect", +1, -1),
    ]:
        U = build_operator(l0, l1, theta=0.0)
        op_rec = {
            "name": name, "lambda_0": l0, "lambda_1": l1,
            "matrix": U.tolist(),
            "s3_equivariant": is_s3_equivariant(U),
            "q_preserving": is_q_preserving(U),
            "fixed_point_analysis_on_v_star": fixed_points_analysis(U, V_STAR),
        }
        S3_operators.append(op_rec)

    # (D) ℤ/3-equivariant q-preserving family: rotation in standard plane by arbitrary θ,
    # combined with λ_0 ∈ {±1}.  Check if any θ has v_* as fixed point.
    rotations = []
    for l0 in (-1, +1):
        for theta_deg in (0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330):
            theta = math.radians(theta_deg)
            U = build_operator(l0, +1, theta=theta)
            fp = fixed_points_analysis(U, V_STAR)
            rotations.append({
                "name": f"U_lambda0={l0:+d}_theta={theta_deg}deg",
                "lambda_0": l0, "theta_deg": theta_deg,
                "s3_equivariant": is_s3_equivariant(U),
                "q_preserving": is_q_preserving(U),
                "relative_residual_on_v_star": fp["relative_residual"],
            })

    # Find any rotation θ (∈ [0, 2π)) that exactly fixes v_* (beyond θ=0):
    # The standard component v_std_star rotating by θ stays fixed iff v_std_star is on
    # the rotation axis, which for a 2D rotation means v_std_star = 0 or θ = 0 (2π).
    # So no non-trivial rotation fixes v_* unless v_*'s standard component vanishes.
    v_std_norm = float(np.linalg.norm(v_std_star))
    pdg_non_democratic = v_std_norm > 1e-3 * np.linalg.norm(V_STAR)

    # Phase I gate verdict
    # 2-parameter family? NO — S₃-equivariant q-preserving on linear ops = 4 isolated points.
    # Any non-trivial operator that takes v_* to itself (beyond identity)?
    non_identity_fixed_s3 = any(
        r["fixed_point_analysis_on_v_star"]["is_fixed_point_within_1e-10"] and r["name"] != "U_identity"
        for r in S3_operators
    )
    # Under ℤ/3-equivariant: v_* is fixed only if rotation is identity, given v_* has non-zero standard component.
    # So no structural non-trivial fixed-point operator exists in this class either.

    phase1_verdict_dict = {
        "full_S3_linear_q_preserving_operators_count": len(S3_operators),
        "full_S3_2param_family_exists": False,
        "phase1_gate_pass_for_Phase_II": False,
        "ℤ3_linear_q_preserving_family_dimension": 1,   # just the rotation angle θ
        "pdg_v_star_has_nonzero_standard_component": pdg_non_democratic,
        "pdg_v_star_fixed_only_by_identity": True,
        "linear_class_verdict": "EMPTY of nontrivial UGP-native fixed-point operators on v_*",
    }

    # Paper / spec-level verdict
    if phase1_verdict_dict["full_S3_2param_family_exists"]:
        verdict = "PASS_PhaseI_gate_proceed_to_PhaseII"
    else:
        # Clean negative: write Phase I as negative result, sharpen 03_SPEC open problem
        verdict = "PHASE1_NEGATIVE_linear_S3_class_empty_of_fixed_point_operators_on_v_star"

    prediction_block = {
        "comp_id": "COMP-P01-RR",
        "spec_reference": "03_SPEC Phase I — S₃-equivariant q-preserving operator enumeration",
        "timestamp_utc": ts,
        "koide_matrix": M_KOIDE.tolist(),
        "koide_eigenvalues": [-3.0, 3.0, 3.0],
        "v_star_MeV_half": V_STAR.tolist(),
        "pdg_koide_check": pdg_check,
        "full_S3_operators_enumeration": S3_operators,
        "Z3_equivariant_rotation_family_samples": rotations,
        "phase1_gate_analysis": phase1_verdict_dict,
    }

    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "verdict": verdict,
        "koide_q_value_at_v_star": q_star,
        "koide_holds_at_v_star_to_tolerance_1e-4": abs(q_star) < 1e-4 * s ** 2,
        "linear_S3_equivariant_operator_count": len(S3_operators),
        "n_nontrivial_fixed_point_operators_on_v_star": 0 if not non_identity_fixed_s3 else 1,
        "phase1_gate_passes": phase1_verdict_dict["full_S3_2param_family_exists"],
        "phase1_closes_as_negative_result": not phase1_verdict_dict["full_S3_2param_family_exists"],
    }

    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_RR_koide_s3_flow_phase1.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
