#!/usr/bin/env python3
"""
COMP-P01-RC1: CKM with UGP-restricted O(1) coefficients.

SP-C of EPIC 13.  Reframed target from EPIC 7 Round 30 productive-negative:
  Phase 2b continuous 36-dim optimisation reached 1.77% but was over-parameterised
  (all null trials reach the same 1.77%, structural content lost).
  Phase 1 per-element 4--6% lattice match with charges from Frogatt-Nielsen
  hierarchy and O(1) = 1 coefficients was the honest structural content.

Question for SP-C:
  If the O(1) coefficients are restricted to a UGP-structural atom library
  (rather than free continuous reals), can the null-disciplined improvement
  over Phase 1's 4--6% per-element match be achieved?

Method:
  - Fix FN charge assignments at Phase 1 structurally-valid values:
      a_Q = (-3, -2, 0),  b_Q = (-5, -3, 0)    [up-type]
      a_D = ( 0,  0, 0),  b_D = ( 0,  0, 0)    [down-type: trivial; pattern on up-type carries]
  - O(1) library (UGP-structural):
      moduli: {1, 2, 3, 7, 9, 13/9, 7/6, 5/14, 45/126, 1/3, 2/3, 1/9, 2/9}
      signs:   {+1, -1}
      phases:  Z_6 phases {0, pi/3, 2pi/3, pi, 4pi/3, 5pi/3}
  - CKM up-type matrix M_u_ij = c_u_ij * eps_u^(|a_i - a_j|)
    where c_u_ij is a complex O(1) coefficient (|c| from library, phase from library)
  - Same for down-type
  - CKM = U_u_L.H @ U_d_L  where U_u_L, U_d_L are left-diagonalising of M_u M_u.H, M_d M_d.H
  - Sample N=20000 random UGP-restricted (c_u, c_d) combinations
  - Report best-case max |V_ij| off-diagonal error (percentage of PDG)
  - Null discipline: replace UGP moduli library with random rationals of matching
    magnitude; re-run; compare null-best to UGP-best.

Gate A (structural signal): UGP-best <= 5% AND null-best / UGP-best >= 3 (3x margin)
Gate B (partial): UGP-best <= 15% AND null-best / UGP-best >= 2
Gate C: otherwise (upholds R30 over-parameterisation conclusion)
"""

from __future__ import annotations
import hashlib
import json
import math
import os
import random
import sys
import time
import numpy as np


# ---------------------------------------------------------------------------
# PDG CKM central values (Wolfenstein-parameterized to magnitudes)
# ---------------------------------------------------------------------------
# PDG 2024 CKM magnitudes
V_CKM_PDG = np.array([
    [0.97435, 0.22500, 0.00369],
    [0.22486, 0.97349, 0.04182],
    [0.00857, 0.04110, 0.99911],
])


# ---------------------------------------------------------------------------
# FN charges and flavon VEV ratios (Phase 1 structurally valid)
# ---------------------------------------------------------------------------
A_Q = np.array([-3, -2, 0])    # up-type: generation-1,2,3
B_Q = np.array([-5, -3, 0])

# Froggatt-Nielsen flavon VEV ratios from Round 21 (TT-derived)
# epsilon_1 ~ sin(Cabibbo) and epsilon_2 smaller; use structurally-derived values
EPS_1 = 0.228    # ~ Cabibbo
EPS_2 = 0.70     # smaller hierarchy


# ---------------------------------------------------------------------------
# UGP-restricted O(1) coefficient library
# ---------------------------------------------------------------------------
UGP_MODULI = [1.0, 2.0, 3.0, 7.0, 9.0,
              13.0/9.0, 7.0/6.0, 5.0/14.0, 45.0/126.0,
              1.0/3.0, 2.0/3.0, 1.0/9.0, 2.0/9.0]
SIGNS = [+1.0, -1.0]

# Z_6 phases + 0 + pi
Z6_PHASES = [0.0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3]


def random_coeff(rng: random.Random, moduli=UGP_MODULI) -> complex:
    m = rng.choice(moduli)
    s = rng.choice(SIGNS)
    p = rng.choice(Z6_PHASES)
    return s * m * (math.cos(p) + 1j * math.sin(p))


# ---------------------------------------------------------------------------
# Mass matrix → CKM
# ---------------------------------------------------------------------------

def build_mass_matrix(a: np.ndarray, b: np.ndarray, eps1: float, eps2: float, coeffs: np.ndarray) -> np.ndarray:
    """coeffs is 3x3 complex O(1)."""
    M = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            delta_a = abs(a[i] - a[j])
            delta_b = abs(b[i] - b[j])
            M[i, j] = coeffs[i, j] * (eps1**delta_a) * (eps2**delta_b)
    return M


def compute_ckm(M_u: np.ndarray, M_d: np.ndarray) -> np.ndarray:
    """CKM = U_u_L^dagger U_d_L where U_*_L are left-diagonalising of M * M^dagger."""
    # Hermitian squared matrices
    Hu = M_u @ M_u.conj().T
    Hd = M_d @ M_d.conj().T
    # Diagonalize
    _, U_u = np.linalg.eigh(Hu)
    _, U_d = np.linalg.eigh(Hd)
    # Sort by eigenvalue descending
    # (eigh returns ascending; flip)
    U_u = U_u[:, ::-1]
    U_d = U_d[:, ::-1]
    V = U_u.conj().T @ U_d
    return np.abs(V)


def ckm_residual(V_abs: np.ndarray) -> float:
    """Return max percentage residual over all 9 elements vs PDG."""
    residuals = np.abs(V_abs - V_CKM_PDG) / V_CKM_PDG
    return 100.0 * np.max(residuals)


# ---------------------------------------------------------------------------
# UGP search vs null search
# ---------------------------------------------------------------------------

def sample_coefficients_matrix(rng: random.Random, moduli) -> np.ndarray:
    """Return 3x3 complex O(1) matrix from given moduli library."""
    mat = np.empty((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            mat[i, j] = random_coeff(rng, moduli=moduli)
    return mat


def run_search(rng: random.Random, n_trials: int, moduli) -> tuple[float, list[float]]:
    """Run the search; return best residual and full residual list."""
    residuals = []
    for _ in range(n_trials):
        c_u = sample_coefficients_matrix(rng, moduli)
        c_d = sample_coefficients_matrix(rng, moduli)
        M_u = build_mass_matrix(A_Q, B_Q, EPS_1, EPS_2, c_u)
        M_d = build_mass_matrix(A_Q, B_Q, EPS_1, EPS_2, c_d)
        V_abs = compute_ckm(M_u, M_d)
        r = ckm_residual(V_abs)
        if math.isfinite(r):
            residuals.append(r)
    residuals.sort()
    return residuals[0] if residuals else float("inf"), residuals


def random_null_moduli(rng: random.Random, n: int = 13) -> list[float]:
    """Random rationals in [0.1, 10] replacing UGP moduli."""
    mods = []
    for _ in range(n):
        p = rng.randint(1, 15)
        q = rng.randint(1, 15)
        mods.append(p / q)
    return mods


def source_sha256() -> str:
    with open(__file__, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    t0 = time.time()
    precommit_sha = source_sha256()

    n_per_search = 20000
    n_null_trials = 10

    results = {
        "experiment_id": "COMP-P01-RC1-CKM",
        "title": "CKM with UGP-restricted O(1) coefficients",
        "epic": "EPIC_CLUSTER13_REFEREE_CLOSURE / SP-C",
        "pre_commit_sha256": precommit_sha,
        "config": {
            "A_Q": A_Q.tolist(),
            "B_Q": B_Q.tolist(),
            "EPS_1": EPS_1,
            "EPS_2": EPS_2,
            "ugp_moduli_library": UGP_MODULI,
            "signs": SIGNS,
            "Z6_phases_rad": Z6_PHASES,
            "n_per_search": n_per_search,
            "n_null_trials": n_null_trials,
        },
        "PDG_V_CKM": V_CKM_PDG.tolist(),
    }

    # Baseline -- all coefficients = 1
    print(f"[{time.time()-t0:.1f}s] Baseline: c_u = c_d = 1...", file=sys.stderr)
    c_ones = np.ones((3, 3), dtype=complex)
    M_u_base = build_mass_matrix(A_Q, B_Q, EPS_1, EPS_2, c_ones)
    M_d_base = build_mass_matrix(A_Q, B_Q, EPS_1, EPS_2, c_ones)
    V_base = compute_ckm(M_u_base, M_d_base)
    results["baseline_O1_equal_1"] = {
        "V_abs": V_base.tolist(),
        "max_percent_residual": ckm_residual(V_base),
    }

    # UGP-restricted search
    print(f"[{time.time()-t0:.1f}s] UGP-restricted search ({n_per_search} trials)...", file=sys.stderr)
    ugp_rng = random.Random(20260423)
    ugp_best, ugp_residuals = run_search(ugp_rng, n_per_search, UGP_MODULI)
    ugp_top10 = ugp_residuals[:10]
    results["ugp_restricted_search"] = {
        "moduli_library_size": len(UGP_MODULI),
        "best_max_percent_residual": ugp_best,
        "top_10_residuals": ugp_top10,
        "fraction_under_10pct": sum(1 for r in ugp_residuals if r <= 10.0) / max(len(ugp_residuals), 1),
        "fraction_under_5pct": sum(1 for r in ugp_residuals if r <= 5.0) / max(len(ugp_residuals), 1),
    }
    print(f"[{time.time()-t0:.1f}s]   UGP best: {ugp_best:.3f}% max residual", file=sys.stderr)

    # Null discipline: random moduli
    print(f"[{time.time()-t0:.1f}s] Null discipline ({n_null_trials} trials with random moduli)...", file=sys.stderr)
    null_bests = []
    null_rng = random.Random(20260424)
    for k in range(n_null_trials):
        mods = random_null_moduli(null_rng, n=len(UGP_MODULI))
        _, null_res = run_search(null_rng, n_per_search, mods)
        nb = null_res[0] if null_res else float("inf")
        null_bests.append(nb)
        print(f"[{time.time()-t0:.1f}s]   null {k+1}/{n_null_trials}: best {nb:.3f}%", file=sys.stderr)
    null_bests.sort()
    null_median_best = null_bests[len(null_bests)//2]

    results["null"] = {
        "n_trials": n_null_trials,
        "null_best_residuals_sorted": null_bests,
        "null_median_best": null_median_best,
        "null_min_best": null_bests[0],
        "null_max_best": null_bests[-1],
        "null_median_over_ugp_ratio": null_median_best / ugp_best if ugp_best > 0 else None,
    }

    # Gate
    ratio = results["null"]["null_median_over_ugp_ratio"]
    if ugp_best <= 5.0 and ratio is not None and ratio >= 3.0:
        gate = "A"
    elif ugp_best <= 15.0 and ratio is not None and ratio >= 2.0:
        gate = "B"
    else:
        gate = "C"
    results["gate"] = gate
    results["runtime_seconds"] = time.time() - t0

    tmp = json.dumps(results, sort_keys=True, default=str).encode("utf-8")
    results["post_commit_sha256"] = hashlib.sha256(tmp).hexdigest()

    out_path = os.path.join(os.path.dirname(__file__), "comp_p01_RC1_ckm_ugp_restricted_search.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{time.time()-t0:.1f}s] Wrote {out_path}", file=sys.stderr)

    print(json.dumps({
        "pre_commit_sha256": precommit_sha,
        "post_commit_sha256": results["post_commit_sha256"],
        "gate": gate,
        "baseline_O1_eq_1_max_percent_residual": results["baseline_O1_equal_1"]["max_percent_residual"],
        "ugp_best_max_percent_residual": ugp_best,
        "null_median_best_max_percent_residual": null_median_best,
        "null_median_over_ugp_ratio": ratio,
        "ugp_top_10_residuals": ugp_top10,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
