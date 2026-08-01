"""
COMP-P01-CCC: CKM Phase 2 via full Yukawa-matrix diagonalisation with
              O(1) complex coefficients (15_SPEC Phase 2, Round 30).

Phase 1 (SC-BBB) established that the Round-21 FN-doubled flavon lattice
matches all 6 CKM off-diagonals individually at 4-6%, but a single global
charge assignment gives 30% RMS (max 58.8% on |V_ub|).

Phase 2 adds TWO structurally-motivated ingredients:

(a) O(1) UGP-native coefficients per Yukawa element.  Instead of
    |Y_u_ij| ~ ε_1^{Δa} · ε_2^{Δb} alone, we allow
    Y_u_ij = c_u_ij · ε_1^{Δa} · ε_2^{Δb} · e^{i φ_u_ij}
    where c_u_ij is an O(1) coefficient from the UGP atom library
    (Fibonacci, golden-ratio powers, small rationals) and φ_u_ij is
    a phase drawn from a small structural library (0, π/2, π, π/4 etc.).

(b) Full matrix diagonalisation: compute U_uL and U_dL from the full
    complex Y_u and Y_d via singular value decomposition, then
    V_CKM = U_uL^† · U_dL.  This is the exact CKM derivation (not the
    approximate "V_ij ~ ε^|Δq|" formula of Phase 1).

APPROACH:
  Fix the charge assignment (a_Q, b_Q) at the Phase-1 best-global value
  (or a neighbourhood thereof).
  Generate Y_u, Y_d matrices with UGP-atom magnitudes and structural
  phases.  Compute V = U_uL^† · U_dL via SVD.
  Search over charge-and-coefficient combinations; null-test vs random.

GATES:
  - Global RMS log-residual <= 0.05 (5% per element average): FULL CLOSURE
  - <= 0.10 (10%):                                              PARTIAL
  - > 0.10:                                                     MAP
"""

import math, json, hashlib, datetime, os, itertools
import numpy as np
from fractions import Fraction

# =====================================================================
# Flavon VEVs (Round 21)
# =====================================================================
log_eps_1 = -math.pi / 3
log_eps_2 = -math.pi / 8
eps_1 = math.exp(log_eps_1)
eps_2 = math.exp(log_eps_2)

# PDG CKM magnitudes (2022 fit)
V_PDG = np.array([
    [0.97373, 0.2243, 0.00382],
    [0.221,   0.975,  0.0408],
    [0.0086,  0.0415, 1.014],
])

# UGP atom library for O(1) coefficients
phi = (1 + math.sqrt(5)) / 2
UGP_ATOMS = {
    '1':       1.0,
    'phi':     phi,
    '1/phi':   1/phi,
    'phi^2':   phi**2,
    '1/phi^2': 1/phi**2,
    'sqrt2':   math.sqrt(2),
    'sqrt3':   math.sqrt(3),
    '1/sqrt2': 1/math.sqrt(2),
    '1/sqrt3': 1/math.sqrt(3),
    '2':       2.0,
    '1/2':     0.5,
    '3':       3.0,
    '1/3':     1/3,
    '2/3':     2/3,
    '3/2':     1.5,
    'e':       math.e,
    '1/e':     1/math.e,
}

# Structural phase library
STRUCT_PHASES = {
    '0':      0.0,
    'pi/2':   math.pi/2,
    '-pi/2': -math.pi/2,
    'pi':     math.pi,
    'pi/4':   math.pi/4,
    '-pi/4': -math.pi/4,
    'pi/3':   math.pi/3,
    '-pi/3': -math.pi/3,
    'pi/6':   math.pi/6,
    '-pi/6': -math.pi/6,
    'pi/8':   math.pi/8,
    '-pi/8': -math.pi/8,
}

# =====================================================================
# Step 1: construct full Y matrices given charges + O(1) coefficients
# =====================================================================

def build_Y(a_Q, b_Q, a_R, b_R, c_matrix, phi_matrix, eps1=eps_1, eps2=eps_2):
    """
    Build 3x3 Yukawa matrix from FN charges + O(1) coefficients + phases.

    Y_ij = c_matrix[i,j] * eps1^|a_Q[i]+a_R[j]| * eps2^|b_Q[i]+b_R[j]| * exp(1j*phi_matrix[i,j])
    """
    Y = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            Da = abs(a_Q[i] + a_R[j])
            Db = abs(b_Q[i] + b_R[j])
            Y[i, j] = c_matrix[i, j] * eps1**Da * eps2**Db * np.exp(1j * phi_matrix[i, j])
    return Y

def compute_ckm(Y_u, Y_d):
    """Compute CKM magnitudes |V_ij| = |U_uL^† U_dL| via SVD."""
    U_u, _, _ = np.linalg.svd(Y_u)  # U_u is left-singular vector matrix
    U_d, _, _ = np.linalg.svd(Y_d)
    V = U_u.conj().T @ U_d
    return np.abs(V)

# =====================================================================
# Step 2: diagonal-only Y (i.e., generation-diagonal) -- gives V=I
# To get CKM, need OFF-DIAGONAL Y elements.
# Choose charges so that Y has hierarchical structure matching FN hierarchy.
# =====================================================================

# Phase 1 best: a_Q = (-3, -2, 0), b_Q = (-5, -3, 0)
# For right-handed charges, use a minimal assumption that Y is hermitian-like
# (same magnitudes on both sides of diagonal).  Standard FN for up-type:
# a_u, b_u ~ minimal so Y_u_33 ~ y_top ~ O(1).
# For CKM, the LEFT charges (a_Q, b_Q) dominate; right-handed charges set the
# per-column scale.  A clean choice: a_u = (0, 0, 0), b_u = (0, 0, 0)  gives
# Y_u_ij = eps1^|a_Q[i]| * eps2^|b_Q[i]|  if right is zero.
# But this makes Y_u rank-1 (same value per column j up to a_R_j), not hierarchical.
# Need right-handed hierarchy too.

# Standard FN (Leurer-Nir-Seiberg):
# a_u_g and a_d_g chosen so diagonal masses match.
# From TT (Round 21): q_u_g^(1) = 0, q_lep_g^(1) = 2^(g-1), Y_u_gg / Y_lep_gg = eps^(−2^(g−1)).
# For CKM we need full matrix structure.

# PRACTICAL CHOICE: set right-handed charges to MIRROR left-handed charges
# (symmetric FN).  a_u = a_Q, b_u = b_Q.  Then Y_u_ij = eps1^|a_Q_i+a_Q_j| etc.
# This gives hierarchical upper-triangular (and lower-triangular) structure.

print("=" * 72)
print("COMP-P01-CCC: CKM Phase 2 via full Y matrix diagonalisation")
print("=" * 72)
print()
print(f"Flavon VEVs: ε_1 = {eps_1:.4f}, ε_2 = {eps_2:.4f}")
print()
print("STEP 1: test baseline — Phase-1 best charges with all c_ij = 1, phi_ij = 0")
print()

a_Q_base = (-3, -2, 0)
b_Q_base = (-5, -3, 0)
# Simplest symmetric right-handed: a_u = a_d = a_Q, b_u = b_d = b_Q.
# This gives |Y_ij| = eps_1^|a_Q_i + a_Q_j| * eps_2^|b_Q_i + b_Q_j| (sum, not difference)
# For CKM to come from Y, we need DIFFERENCES. So use a_u = -a_Q_rev (mirror).
# Actually with symmetric a_u = a_Q, |Y_u_ij| = eps_1^|a_Q_i+a_Q_j| * eps_2^|b_Q_i+b_Q_j|.
# e.g. Y_u_33 = eps_1^0 * eps_2^0 = 1 (top), Y_u_11 = eps_1^6 * eps_2^10 (up).
# Then |V_ij| from diagonalisation of Y_u, Y_d ~ eps_1^|a_Q_i-a_Q_j| * eps_2^|b_Q_i-b_Q_j|
# matches Phase 1's formula.

c_matrix_baseline = np.ones((3, 3))
phi_matrix_zero = np.zeros((3, 3))
Y_u_base = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_matrix_baseline, phi_matrix_zero)
# For Y_d, right-handed down charges differ from right-handed up; for simplicity
# use same magnitudes (standard minimal FN).
Y_d_base = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_matrix_baseline, phi_matrix_zero)

V_base = compute_ckm(Y_u_base, Y_d_base)
print(f"  baseline: V_us = {V_base[0,1]:.4f} vs PDG {V_PDG[0,1]:.4f}")
print(f"  (baseline has Y_u = Y_d so V should be ~I; this is a sanity check)")

# For actual CKM, Y_u and Y_d must differ. Standard approach: Y_u and Y_d have
# different O(1) coefficients. Random sampling:

def rms_log_residual_matrix(V_pred):
    res = []
    for i in range(3):
        for j in range(3):
            if i != j:
                if V_pred[i, j] > 0:
                    res.append(math.log(V_pred[i, j] / V_PDG[i, j]))
                else:
                    res.append(10.0)  # penalty for zero
    return math.sqrt(sum(r*r for r in res) / len(res))

def max_off_diag_err(V_pred):
    return max(abs(V_pred[i,j] - V_PDG[i,j]) / V_PDG[i,j]
               for i in range(3) for j in range(3) if i != j)

# =====================================================================
# Step 3: search over O(1) coefficient + phase combinations
# =====================================================================
print()
print("STEP 2: random-sample O(1) coefficients from UGP atom library + phases")
print()

np.random.seed(42)
N_trials = 5000
best = (float('inf'), None, None, None, None)
hits_5pct = 0
hits_10pct = 0

atom_names = list(UGP_ATOMS.keys())
atom_values = list(UGP_ATOMS.values())
phase_values = list(STRUCT_PHASES.values())

for trial in range(N_trials):
    # Generate O(1) coefficients from UGP atoms (with random signs)
    c_u = np.ones((3, 3))
    c_d = np.ones((3, 3))
    phi_u = np.zeros((3, 3))
    phi_d = np.zeros((3, 3))

    for i in range(3):
        for j in range(3):
            c_u[i, j] = atom_values[np.random.randint(len(atom_values))]
            c_d[i, j] = atom_values[np.random.randint(len(atom_values))]
            # Sign
            if np.random.random() < 0.5: c_u[i, j] *= -1
            if np.random.random() < 0.5: c_d[i, j] *= -1
            # Phase
            phi_u[i, j] = phase_values[np.random.randint(len(phase_values))]
            phi_d[i, j] = phase_values[np.random.randint(len(phase_values))]

    Y_u = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_u, phi_u)
    Y_d = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_d, phi_d)

    try:
        V = compute_ckm(Y_u, Y_d)
        rms = rms_log_residual_matrix(V)
        max_err = max_off_diag_err(V)

        if max_err <= 0.05: hits_5pct += 1
        if max_err <= 0.10: hits_10pct += 1

        if rms < best[0]:
            best = (rms, c_u.copy(), c_d.copy(), phi_u.copy(), phi_d.copy())
    except Exception:
        continue

print(f"Sampled {N_trials} (coefficient, phase) combinations at fixed charges.")
print(f"Best RMS log-residual: {best[0]:.4f}")
print(f"Hits within 5% max off-diagonal: {hits_5pct}/{N_trials} = {hits_5pct/N_trials*100:.2f}%")
print(f"Hits within 10% max off-diagonal: {hits_10pct}/{N_trials} = {hits_10pct/N_trials*100:.2f}%")

# =====================================================================
# Step 3: Report best result
# =====================================================================
rms_best, c_u_best, c_d_best, phi_u_best, phi_d_best = best
Y_u_best = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_u_best, phi_u_best)
Y_d_best = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_d_best, phi_d_best)
V_best = compute_ckm(Y_u_best, Y_d_best)
max_err_best = max_off_diag_err(V_best)

print()
print("=" * 72)
print("STEP 3: best CKM prediction")
print("=" * 72)
print(f"{'element':10s} {'PDG':>10s} {'predicted':>12s} {'err %':>8s}")
for i in range(3):
    for j in range(3):
        print(f"  V[{i}][{j}]    {V_PDG[i,j]:10.5f} {V_best[i,j]:12.5f} "
              f"{(V_best[i,j]-V_PDG[i,j])/V_PDG[i,j]*100:+8.2f}%")
print()
print(f"  MAX off-diagonal error: {max_err_best*100:.2f}%")
print(f"  RMS log-residual: {rms_best:.4f}")

if max_err_best <= 0.05:
    verdict = "FULL CLOSURE (<=5% on all off-diagonals)"
elif max_err_best <= 0.10:
    verdict = "PARTIAL CLOSURE (<=10% on all off-diagonals)"
else:
    verdict = "MAP (random search with UGP atoms does not reach 10%)"
print(f"  VERDICT: {verdict}")

# =====================================================================
# Null test: RANDOM ε values (not the UGP-structural eps_1, eps_2)
# =====================================================================
print()
print("=" * 72)
print("STEP 4: null test — same search with RANDOM (eps_1, eps_2)")
print("=" * 72)
print()

np.random.seed(43)
N_null_flavons = 20
null_bests = []
for trial_null in range(N_null_flavons):
    eps_r1 = np.random.uniform(0.2, 0.5)
    eps_r2 = np.random.uniform(0.5, 0.8)
    best_null = float('inf')
    for _ in range(N_trials // 10):  # fewer samples per null test
        c_u = np.array([[atom_values[np.random.randint(len(atom_values))]*(1 if np.random.random()<0.5 else -1) for _ in range(3)] for _ in range(3)])
        c_d = np.array([[atom_values[np.random.randint(len(atom_values))]*(1 if np.random.random()<0.5 else -1) for _ in range(3)] for _ in range(3)])
        phi_u = np.array([[phase_values[np.random.randint(len(phase_values))] for _ in range(3)] for _ in range(3)])
        phi_d = np.array([[phase_values[np.random.randint(len(phase_values))] for _ in range(3)] for _ in range(3)])
        Y_u = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_u, phi_u, eps1=eps_r1, eps2=eps_r2)
        Y_d = build_Y(a_Q_base, b_Q_base, a_Q_base, b_Q_base, c_d, phi_d, eps1=eps_r1, eps2=eps_r2)
        try:
            V = compute_ckm(Y_u, Y_d)
            rms = rms_log_residual_matrix(V)
            if rms < best_null: best_null = rms
        except: pass
    null_bests.append(best_null)

null_bests = np.array(null_bests)
print(f"Ran {N_null_flavons} null trials (random eps_1 in [0.2, 0.5], eps_2 in [0.5, 0.8])")
print(f"Null best RMS (median of 20 trials): {np.median(null_bests):.4f}")
print(f"Structural best RMS:                  {rms_best:.4f}")
print(f"Fraction of null trials at/below structural: "
      f"{sum(1 for n in null_bests if n <= rms_best)}/{N_null_flavons}")

# =====================================================================
# Artifact
# =====================================================================
print()
prediction = {
    "experiment_id": "COMP-P01-CCC",
    "title": "CKM Phase 2: full Y diagonalisation with UGP-atom O(1) coefficients + structural phases",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "flavon_vevs": {"eps_1": eps_1, "eps_2": eps_2},
    "charge_assignment": {
        "a_Q": list(a_Q_base),
        "b_Q": list(b_Q_base),
        "a_R_eq_a_Q": True,
        "b_R_eq_b_Q": True,
        "notes": "Symmetric FN with right-handed charges mirroring left-handed",
    },
    "search": {
        "N_trials": N_trials,
        "atom_library": atom_names,
        "phase_library": list(STRUCT_PHASES.keys()),
    },
    "best_result": {
        "V_predicted": V_best.tolist(),
        "V_PDG": V_PDG.tolist(),
        "rms_log_residual": rms_best,
        "max_off_diagonal_error_pct": max_err_best * 100,
        "hits_within_5pct": hits_5pct,
        "hits_within_10pct": hits_10pct,
    },
    "null_test": {
        "N_null_trials": N_null_flavons,
        "null_median_rms": float(np.median(null_bests)),
        "structural_beats_null_count": int(sum(1 for n in null_bests if n > rms_best)),
    },
    "verdict": verdict,
}
block = json.dumps(prediction, sort_keys=True, indent=2, default=str)
prediction["pre_commit_sha256"] = hashlib.sha256(block.encode("utf-8")).hexdigest()

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "comp_p01_CCC_ckm_phase2_full_diag.json")
with open(out, "w") as f:
    json.dump(prediction, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print(f"Pre-commit SHA-256: {prediction['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
print(f"Artifact: {out}")
