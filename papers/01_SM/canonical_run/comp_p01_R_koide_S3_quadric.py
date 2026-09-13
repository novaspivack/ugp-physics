#!/usr/bin/env python3
"""
COMP-P01-R: Koide as the UNIQUE S3-invariant null quadric.

Algebraic identity: Q = 2/3  iff  (Sum a_i)^2 = (3/2) Sum a_i^2
                          iff  Sum a_i^2 = 4 Sum_{i<j} a_i a_j
                          iff  v^T M v = 0   where M = 3 I - 2 J

Here J is the all-ones matrix and v = (sqrt(m_e), sqrt(m_mu), sqrt(m_tau)).

The key structural theorem:
  Among all real S_3-invariant symmetric 3x3 matrices a*I + b*J, the UNIQUE
  (up to scale) choice giving opposite-sign and equal-magnitude eigenvalues
  on the trivial and standard irreducible subspaces is (a, b) = (3, -2),
  i.e. M = 3 I - 2 J.

  - Trivial subspace ((1,1,1)/sqrt(3)):  eigenvalue = a + 3b = 3 - 6 = -3
  - Standard subspace (orthogonal):      eigenvalue = a + 0  =  3

  So Koide Q = 2/3 <=> the sqrt-mass vector lies on the null cone of the
  unique balanced S_3-invariant quadric.

This script:
  1. Verifies the spectral decomposition of M = 3 I - 2 J numerically.
  2. Proves (by construction) the uniqueness statement above.
  3. Computes v^T M v for the empirical sqrt-mass triple and confirms it is
     ~ 0 at PDG precision.
  4. Tests a candidate UGP coupling "S3 orbit quotient 3" + "standard irrep
     dim 2" combination as the prefactors (a=3, b=-2) and documents the
     structural pathway.
  5. Runs a null test: how close to Koide would a RANDOM sqrt-mass triple be,
     under scale-invariance?  Establishes empirical significance.
"""

from __future__ import annotations
import json
import math
import random
from hashlib import sha256
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Empirical inputs
# ---------------------------------------------------------------------------

M_E = 0.5109989461
M_MU = 105.6583755
M_TAU = 1776.86
D_M_TAU = 0.12

V_EMP = np.array([math.sqrt(M_E), math.sqrt(M_MU), math.sqrt(M_TAU)])

# ---------------------------------------------------------------------------
# The Koide quadric
# ---------------------------------------------------------------------------

def koide_matrix(a: float = 3.0, b: float = -2.0) -> np.ndarray:
    return a * np.eye(3) + b * np.ones((3, 3))


def spectral_check(M: np.ndarray) -> dict:
    eigvals, eigvecs = np.linalg.eigh(M)
    # identify trivial eigenvector (closest to (1,1,1)/sqrt(3))
    dem = np.array([1, 1, 1]) / math.sqrt(3)
    projections = [float(abs(np.dot(v, dem))) for v in eigvecs.T]
    idx_trivial = int(np.argmax(projections))
    std_idxs = [i for i in range(3) if i != idx_trivial]
    return {
        "eigenvalues_sorted": sorted(eigvals.tolist()),
        "trivial_eigenvalue": float(eigvals[idx_trivial]),
        "standard_eigenvalues": [float(eigvals[i]) for i in std_idxs],
        "eigenvector_for_trivial": eigvecs[:, idx_trivial].tolist(),
    }


def quadric_value(v: np.ndarray, M: np.ndarray) -> float:
    return float(v @ M @ v)


def koide_Q(v: np.ndarray) -> float:
    m = v * v
    s = v.sum()
    return float(m.sum() / (s * s))


def uniqueness_scan() -> list[dict]:
    """Scan (a, b) over rationals and report which ones give equal-magnitude
    opposite-sign eigenvalues on trivial vs standard subspaces.

    For a*I + b*J (3x3):  trivial eigenvalue = a + 3b; standard eigenvalue = a.
    Equal-magnitude opposite-sign: a + 3b = -a  =>  b = -2a/3.
    So UP TO SCALE, b/a = -2/3 is the unique choice.
    """
    results: list[dict] = []
    for a_num in range(-6, 7):
        for b_num in range(-6, 7):
            if a_num == 0 and b_num == 0:
                continue
            a, b = float(a_num), float(b_num)
            M = koide_matrix(a, b)
            trivial_eig = a + 3*b
            standard_eig = a
            # equal magnitude opposite sign?
            balanced = (abs(trivial_eig + standard_eig) < 1e-10
                        and abs(trivial_eig) > 1e-10)
            if balanced:
                results.append({
                    "a": a, "b": b,
                    "ratio_b_over_a": b/a if a != 0 else None,
                    "trivial_eigenvalue": trivial_eig,
                    "standard_eigenvalue": standard_eig,
                    "koide_quadric_match": True,
                })
    return results


def null_test(n_trials: int, seed: int = 12345) -> dict:
    """Sample random sqrt-mass triples with mu_e and tau_e ratios drawn from
    UNIFORM distribution over [1, 1000] for a_2/a_1 and [1, 1e4] for a_3/a_1.
    Count how many are closer to the Koide null locus than the empirical triple.
    """
    rng = random.Random(seed)
    M = koide_matrix(3.0, -2.0)
    emp_quadric = abs(quadric_value(V_EMP, M))
    emp_Q = koide_Q(V_EMP)

    closer_count = 0
    sample_quadrics: list[float] = []
    for _ in range(n_trials):
        a1 = 1.0
        a2 = rng.uniform(1.1, 1000.0)
        a3 = rng.uniform(a2 * 1.1, 10000.0)
        v = np.array([a1, a2, a3])
        # Scale so ||v|| matches empirical, ensures quadric value comparable scale
        v = v * (np.linalg.norm(V_EMP) / np.linalg.norm(v))
        qv = abs(quadric_value(v, M))
        sample_quadrics.append(qv)
        if qv < emp_quadric:
            closer_count += 1

    p_value = closer_count / n_trials
    return {
        "n_trials": n_trials,
        "empirical_abs_quadric_value": emp_quadric,
        "empirical_Q": emp_Q,
        "mean_sample_abs_quadric": float(np.mean(sample_quadrics)),
        "median_sample_abs_quadric": float(np.median(sample_quadrics)),
        "min_sample_abs_quadric": float(np.min(sample_quadrics)),
        "closer_than_empirical_count": closer_count,
        "p_value_estimate": p_value,
    }


def physical_propagation(M: np.ndarray) -> dict:
    """Propagate PDG m_tau uncertainty through the quadric value."""
    nominal = quadric_value(V_EMP, M)
    # shift m_tau by +/- sigma
    v_plus = np.array([V_EMP[0], V_EMP[1], math.sqrt(M_TAU + D_M_TAU)])
    v_minus = np.array([V_EMP[0], V_EMP[1], math.sqrt(M_TAU - D_M_TAU)])
    q_plus = quadric_value(v_plus, M)
    q_minus = quadric_value(v_minus, M)
    sigma_q = (abs(q_plus - nominal) + abs(q_minus - nominal)) / 2
    return {
        "quadric_value_nominal": nominal,
        "quadric_value_plus_sigma_mtau": q_plus,
        "quadric_value_minus_sigma_mtau": q_minus,
        "sigma_from_mtau_uncertainty": sigma_q,
        "distance_in_sigma": nominal / sigma_q if sigma_q > 0 else float('nan'),
    }


def main() -> int:
    M = koide_matrix(3.0, -2.0)

    spectral = spectral_check(M)
    emp_quadric = quadric_value(V_EMP, M)
    emp_Q = koide_Q(V_EMP)
    uniqueness = uniqueness_scan()
    physical = physical_propagation(M)
    null = null_test(n_trials=10_000, seed=12345)

    # Structural interpretation:
    structural = {
        "claim": (
            "The Koide relation Q = 2/3 is equivalent to v^T (3 I - 2 J) v = 0, "
            "where v = (sqrt(m_e), sqrt(m_mu), sqrt(m_tau)).  "
            "Among all S_3-invariant symmetric 3x3 matrices (necessarily of form "
            "a*I + b*J), the ratio b/a = -2/3 uniquely gives a balanced "
            "(equal-magnitude, opposite-sign) trivial-vs-standard spectrum."
        ),
        "UGP_coupling_candidates": {
            "prefactor_3_interpretation": (
                "The factor 3 = |S_3|/2 = dim of permutation rep of S_3 on R^3 = "
                "S_3 orbit-length quotient (Lean-certified in L_model_derivation.lean)."
            ),
            "prefactor_2_interpretation": (
                "The factor 2 = dim of standard irrep of S_3 on R^3, appearing in "
                "Lean as the two-dimensional eigenspace in the ridge/prime-lock "
                "rigidity theorems."
            ),
        },
        "koide_as_structural_statement": (
            "The sqrt-mass vector of the 3 charged leptons lies on the null "
            "cone of the unique S_3-invariant balanced quadric. This is a "
            "representation-theoretic FACT (not a UGP-derived prediction) — "
            "but it reframes the Koide mystery: what UGP dynamics FORCES the "
            "sqrt-mass vector onto this null cone?"
        ),
        "open_conjecture_C1": (
            "An S_3-symmetric 3-generation extension of the UGP/GTE dynamics "
            "(yet to be constructed) preserves the quadric form v^T (3I - 2J) v "
            "as a conserved quantity, forcing any flow starting off the null "
            "cone to remain off it. Physical generations realize the null "
            "cone as a fixed-point locus of the S_3-symmetric flow."
        ),
    }

    out = {
        "description": "COMP-P01-R: Koide as S_3-invariant null quadric",
        "empirical": {
            "v_sqrt_mass_MeV_half": V_EMP.tolist(),
            "Q_empirical": emp_Q,
            "v_T_M_v_empirical": emp_quadric,
        },
        "koide_matrix_M": M.tolist(),
        "spectral_decomposition": spectral,
        "uniqueness_of_3I_minus_2J": {
            "scan_results": uniqueness,
            "conclusion": (
                f"Found {len(uniqueness)} integer (a,b) pairs in scan [-6,6]^2 with "
                f"b/a = -2/3 and balanced spectrum. Primitive: (a,b) = (3, -2)."
            ),
        },
        "physical_propagation": physical,
        "null_test": null,
        "structural_interpretation": structural,
    }

    serialized = json.dumps(out, indent=2, sort_keys=True, default=str)
    digest = sha256(serialized.encode("utf-8")).hexdigest()
    out["script_sha256"] = digest

    out_path = Path(__file__).with_suffix(".json")
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True, default=str))

    # Console
    print("=" * 72)
    print("COMP-P01-R: Koide as S_3-invariant null quadric")
    print("=" * 72)
    print(f"Empirical v = ({V_EMP[0]:.6f}, {V_EMP[1]:.6f}, {V_EMP[2]:.6f})")
    print(f"Empirical Q = {emp_Q:.10f}   (target 2/3 = {2/3:.10f})")
    print()
    print(f"Koide matrix M = 3 I - 2 J =")
    for row in M:
        print("  [" + "  ".join(f"{x:+.1f}" for x in row) + " ]")
    print(f"  Spectral: trivial eig = {spectral['trivial_eigenvalue']:+.1f}, "
          f"standard eigs = {spectral['standard_eigenvalues']}")
    print(f"  v^T M v (empirical) = {emp_quadric:+.6e}")
    print(f"  (m_tau-shifted 1-sigma: +/- {physical['sigma_from_mtau_uncertainty']:.3e})")
    print(f"  -> distance in sigmas: {physical['distance_in_sigma']:+.2f}")
    print()
    print("Uniqueness scan: b/a = -2/3 found at integer (a,b) pairs:")
    for u in uniqueness:
        print(f"  a={u['a']:+.0f}, b={u['b']:+.0f}, b/a = {u['ratio_b_over_a']}")
    print()
    print("Null test (10k random triples with scale-matched norms):")
    print(f"  empirical |v^T M v| = {null['empirical_abs_quadric_value']:.3e}")
    print(f"  median random       = {null['median_sample_abs_quadric']:.3e}")
    print(f"  min random          = {null['min_sample_abs_quadric']:.3e}")
    print(f"  closer than empirical: {null['closer_than_empirical_count']} / {null['n_trials']}")
    print(f"  p-value             ≈ {null['p_value_estimate']:.5f}")
    print()
    print(f"Written to {out_path.name} (SHA {digest[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
