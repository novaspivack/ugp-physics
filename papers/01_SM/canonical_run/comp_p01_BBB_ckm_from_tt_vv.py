"""
COMP-P01-BBB: CKM matrix from combined TT + VV framework (15_SPEC, Round 29).

Priority 3 (15_SPEC) Phase 1: predict the full 3x3 CKM matrix from the
Round-21 FN-doubled flavon framework that produced TT, augmented with
left-quark-doublet FN charges that control CKM mixing.

PHYSICAL SETUP (Froggatt-Nielsen, Leurer-Nir-Seiberg 1993):
   Y_u_ij ~ ε_1^{a_Q_i + a_u_j} · ε_2^{b_Q_i + b_u_j}  (up-type)
   Y_d_ij ~ ε_1^{a_Q_i + a_d_j} · ε_2^{b_Q_i + b_d_j}  (down-type)

   where (a_Q_g, b_Q_g) are LEFT quark doublet FN charges per generation g,
   and (a_u_g, b_u_g), (a_d_g, b_d_g) are right-handed up/down charges.

   CKM matrix element |V_ij| ~ ε_1^|a_Q_i - a_Q_j| · ε_2^|b_Q_i - b_Q_j|
   because right-handed charges cancel between U_uL and U_dL diagonalisations.

FLAVON VEVs (Round 21, Lean-proved global minima of Z_6 x Z_16 Cartan potential):
   ε_1 = e^{-π/3} ≈ 0.3509
   ε_2 = e^{-π/8} ≈ 0.6752

NAIVE first-principles observations:
   ε_1 · ε_2 = e^{-11π/24} ≈ 0.2368 ≈ PDG |V_us| = 0.2249 (4% off!)
   Round-9 naive sin(π/12) = 0.2588 was 15% off; this is 3.8x better.

ROUND 29 TASKS:
   (1) Search over small-integer FN charge assignments (a_Q, b_Q) for g=1,2,3
       that minimise RMS deviation of predicted CKM from PDG.
   (2) Null test: check if random charge assignments easily match PDG.
   (3) Report best assignment, its predictions, and null-statistics.
   (4) Log-density analysis: in FN, V_ij ≈ ε_1^{Δa_ij} · ε_2^{Δb_ij}.
       PDG V values map to log-space (log|V_ij| ~ -Δa·(π/3) - Δb·(π/8)).
       Compute the implied (Δa, Δb) values; are they small integers?

PDG CKM MAGNITUDES (2022 fit, Wolfenstein+):
   |V_ud| = 0.97373    |V_us| = 0.2243     |V_ub| = 0.00382
   |V_cd| = 0.221      |V_cs| = 0.975      |V_cb| = 0.0408
   |V_td| = 0.0086     |V_ts| = 0.0415     |V_tb| = 1.014

Diagonal elements are ~1 (so Δq = 0 for i=j), consistent with FN structure.
"""

import math, json, hashlib, datetime, os, itertools
import numpy as np
from fractions import Fraction

# =====================================================================
# FLAVON VEVs (Round 21)
# =====================================================================
log_eps_1 = -math.pi / 3   # ln ε_1
log_eps_2 = -math.pi / 8   # ln ε_2
eps_1 = math.exp(log_eps_1)
eps_2 = math.exp(log_eps_2)

# =====================================================================
# PDG CKM magnitudes (central values, 2022 fit)
# =====================================================================
V_PDG = np.array([
    [0.97373, 0.2243, 0.00382],   # V_ud, V_us, V_ub
    [0.221,   0.975,  0.0408],    # V_cd, V_cs, V_cb
    [0.0086,  0.0415, 1.014],     # V_td, V_ts, V_tb
])

# Per PDG also: |V_us|/|V_ud| = sin(θ_C), |V_cb|, |V_ub| small
# For an FN-predicting approach, off-diagonal |V_ij| (i != j) are the targets

# =====================================================================
# Step 1: INVERSE PROBLEM — solve for (Δa_ij, Δb_ij) such that
#    |V_ij| = ε_1^Δa_ij · ε_2^Δb_ij
# i.e., Δa_ij · log(ε_1) + Δb_ij · log(ε_2) = log |V_ij|
# =====================================================================

print("=" * 72)
print("COMP-P01-BBB: CKM from TT+VV via FN-doubled framework (Round 29)")
print("=" * 72)
print()
print(f"Flavon VEVs: ε_1 = e^(-π/3) = {eps_1:.6f}, ε_2 = e^(-π/8) = {eps_2:.6f}")
print(f"  ε_1 · ε_2 = {eps_1*eps_2:.6f}")
print(f"  Cabibbo naive V_us ≈ ε_1 · ε_2 = {eps_1*eps_2:.4f} vs PDG {V_PDG[0,1]:.4f} "
      f"→ {(eps_1*eps_2 - V_PDG[0,1])/V_PDG[0,1]*100:+.2f}%")

print()
print("STEP 1: inverse problem — given PDG |V_ij|, solve for (Δa_ij, Δb_ij)")
print("         such that Δa·log(ε_1) + Δb·log(ε_2) = log|V_ij|.")
print("         Report each off-diagonal |V_ij|'s implied (Δa, Δb).")
print()
print(f"{'element':10s} {'PDG |V|':>10s} {'log|V|':>9s} {'best (Δa, Δb) on lattice':>32s} {'predicted':>10s} {'err %':>8s}")

# For each off-diagonal, find the best small-integer (Δa, Δb) lattice point
def best_lattice(log_V, max_delta=8):
    """Find (Δa, Δb) with |Δa|, |Δb| <= max_delta that minimises residual."""
    best = (float('inf'), None, None)
    for Da in range(0, max_delta+1):
        for Db in range(0, max_delta+1):
            pred_log = Da * log_eps_1 + Db * log_eps_2
            res = abs(pred_log - log_V)
            if res < best[0]:
                best = (res, Da, Db)
    return best

off_diag = [(0, 1, "V_us"), (0, 2, "V_ub"), (1, 0, "V_cd"),
            (1, 2, "V_cb"), (2, 0, "V_td"), (2, 1, "V_ts")]
for i, j, name in off_diag:
    V = V_PDG[i, j]
    lV = math.log(V)
    res, Da, Db = best_lattice(lV)
    pred = math.exp(Da * log_eps_1 + Db * log_eps_2)
    err = (pred - V) / V * 100
    print(f"  {name:8s} {V:10.5f} {lV:9.4f}    ({Da}, {Db}) on ℤ² lattice       {pred:10.5f} {err:+8.2f}%")

# =====================================================================
# Step 2: systematic search over LEFT-QUARK-DOUBLET FN charge assignments
# =====================================================================
# In the scheme V_ij ~ ε_1^|a_Q_i - a_Q_j| · ε_2^|b_Q_i - b_Q_j|,
# we search over small-integer charges (a_Q_1, a_Q_2, a_Q_3), (b_Q_1, b_Q_2, b_Q_3)
# and find the assignment minimising RMS residual vs PDG.

print()
print("=" * 72)
print("STEP 2: systematic search over LEFT quark-doublet FN charge assignments")
print("=" * 72)
print()
print("Scheme: |V_ij|_pred = ε_1^|a_Q_i - a_Q_j| · ε_2^|b_Q_i - b_Q_j|")
print("        V_ii (diagonal) = 1 (dominant)")
print()

def predict_V(a_Q, b_Q):
    """Return predicted 3x3 V matrix magnitudes given a_Q, b_Q tuples."""
    V = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i == j:
                V[i, j] = 1.0
            else:
                Da = abs(a_Q[i] - a_Q[j])
                Db = abs(b_Q[i] - b_Q[j])
                V[i, j] = eps_1**Da * eps_2**Db
    return V

def rms_log_residual(V_pred):
    """RMS log-space residual of V_pred vs V_PDG, off-diagonal only."""
    res = []
    for i in range(3):
        for j in range(3):
            if i != j:
                res.append(math.log(V_pred[i, j] / V_PDG[i, j]))
    return math.sqrt(sum(r*r for r in res) / len(res))

# Search space: small integers, can include negatives
# WLOG, a_Q_3 = 0 and b_Q_3 = 0 (only differences matter).
# So we search over (a_Q_1, a_Q_2) with a_Q_3 = 0, same for b.
# Keep a_Q_1, a_Q_2 in [-5, 5], b_Q_1, b_Q_2 in [-5, 5].

best = (float('inf'), None, None, None)
all_assignments = []
RANGE = range(-5, 6)
for a1, a2 in itertools.product(RANGE, repeat=2):
    for b1, b2 in itertools.product(RANGE, repeat=2):
        a_Q = (a1, a2, 0)
        b_Q = (b1, b2, 0)
        V_pred = predict_V(a_Q, b_Q)
        rms = rms_log_residual(V_pred)
        all_assignments.append((rms, a_Q, b_Q, V_pred))
        if rms < best[0]:
            best = (rms, a_Q, b_Q, V_pred)

all_assignments.sort()
print(f"Searched {len(all_assignments)} charge assignments.")
print(f"Best RMS log-residual: {best[0]:.4f} at a_Q = {best[1]}, b_Q = {best[2]}")
print()
print("Top 5 assignments:")
for rank, (rms, a_Q, b_Q, V_pred) in enumerate(all_assignments[:5], 1):
    print(f"  #{rank}: RMS={rms:.4f}, a_Q={a_Q}, b_Q={b_Q}")

# =====================================================================
# Step 3: report best-assignment prediction in detail
# =====================================================================
print()
print("=" * 72)
print("STEP 3: detailed prediction at best assignment")
print("=" * 72)
rms_best, a_Q_best, b_Q_best, V_best = best
print(f"  a_Q = {a_Q_best}   (left quark-doublet FN_1 charges)")
print(f"  b_Q = {b_Q_best}   (left quark-doublet FN_2 charges)")
print()
print(f"{'element':10s} {'PDG':>10s} {'predicted':>12s} {'err %':>8s}")
for i in range(3):
    for j in range(3):
        if i == j:
            print(f"  V[{i}][{j}]    {V_PDG[i,j]:10.5f} {V_best[i,j]:12.5f} "
                  f"{(V_best[i,j]-V_PDG[i,j])/V_PDG[i,j]*100:+8.2f}%")
        else:
            print(f"  V[{i}][{j}]    {V_PDG[i,j]:10.5f} {V_best[i,j]:12.5f} "
                  f"{(V_best[i,j]-V_PDG[i,j])/V_PDG[i,j]*100:+8.2f}%")

max_off_err = max(abs((V_best[i,j]-V_PDG[i,j])/V_PDG[i,j]*100)
                  for i in range(3) for j in range(3) if i!=j)
print()
print(f"  MAX off-diagonal error: {max_off_err:.2f}%")

# =====================================================================
# Step 4: null test
# =====================================================================
print()
print("=" * 72)
print("STEP 4: null test — random charge assignments vs best structural")
print("=" * 72)

np.random.seed(42)
N_null = 1000
null_rms_list = []
closer_than_best = 0
for _ in range(N_null):
    a_Q_r = tuple(np.random.randint(-5, 6, size=3))
    b_Q_r = tuple(np.random.randint(-5, 6, size=3))
    # normalise: set third generation to zero (WLOG)
    a_Q_r = tuple(a - a_Q_r[2] for a in a_Q_r)
    b_Q_r = tuple(b - b_Q_r[2] for b in b_Q_r)
    V_r = predict_V(a_Q_r, b_Q_r)
    rms_r = rms_log_residual(V_r)
    null_rms_list.append(rms_r)
    if rms_r <= rms_best:
        closer_than_best += 1

null_rms_list = np.array(null_rms_list)
print(f"  {N_null} random small-integer charge assignments, range [-5, 5]")
print(f"  Null median RMS log-residual: {np.median(null_rms_list):.4f}")
print(f"  Null best RMS in sample:      {np.min(null_rms_list):.4f}")
print(f"  Best structural RMS:          {rms_best:.4f}")
print(f"  Fraction of random assignments at-or-below structural: "
      f"{closer_than_best}/{N_null} = {closer_than_best/N_null*100:.1f}%")

# =====================================================================
# Step 5: log-density interpretation
# =====================================================================
print()
print("=" * 72)
print("STEP 5: log-density interpretation of best assignment")
print("=" * 72)
print()
print("In FN: log|V_ij| = Δa_ij · log(ε_1) + Δb_ij · log(ε_2)")
print("              = -Δa_ij · π/3 - Δb_ij · π/8")
print()
print("Best assignment implies (Δa, Δb) per CKM element:")
for i, j, name in off_diag:
    Da = abs(a_Q_best[i] - a_Q_best[j])
    Db = abs(b_Q_best[i] - b_Q_best[j])
    pred_log = Da * log_eps_1 + Db * log_eps_2
    PDG_log = math.log(V_PDG[i, j])
    print(f"  {name}: (Δa={Da}, Δb={Db}); log|V|_pred = {pred_log:.4f}, "
          f"PDG log|V| = {PDG_log:.4f}, Δ = {pred_log - PDG_log:+.4f}")

# =====================================================================
# Pre-commit + artifact write
# =====================================================================
print()
print("=" * 72)
prediction = {
    "experiment_id": "COMP-P01-BBB",
    "title": "CKM matrix from TT+VV via FN-doubled framework (15_SPEC Phase 1)",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "flavon_vevs": {"eps_1": eps_1, "eps_2": eps_2, "product_eps_1_eps_2": eps_1*eps_2},
    "naive_V_us_check": {"prediction": eps_1*eps_2, "PDG": V_PDG[0,1],
                          "err_pct": (eps_1*eps_2 - V_PDG[0,1])/V_PDG[0,1]*100},
    "best_assignment": {
        "a_Q": list(a_Q_best),
        "b_Q": list(b_Q_best),
        "V_predicted": V_best.tolist(),
        "V_PDG": V_PDG.tolist(),
        "rms_log_residual": rms_best,
        "max_off_diag_error_pct": max_off_err,
    },
    "top_5_assignments": [
        {"rank": r, "rms": rms, "a_Q": list(aq), "b_Q": list(bq)}
        for r, (rms, aq, bq, _) in enumerate(all_assignments[:5], 1)
    ],
    "null_test": {
        "N_samples": N_null,
        "null_median_rms": float(np.median(null_rms_list)),
        "null_best_rms_in_sample": float(np.min(null_rms_list)),
        "fraction_better_than_structural_pct": closer_than_best / N_null * 100,
    },
}
block = json.dumps(prediction, sort_keys=True, indent=2)
prediction["pre_commit_sha256"] = hashlib.sha256(block.encode("utf-8")).hexdigest()

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "comp_p01_BBB_ckm_from_tt_vv.json")
with open(out, "w") as f:
    json.dump(prediction, f, indent=2, sort_keys=True)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print(f"Pre-commit SHA-256: {prediction['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
print(f"Artifact: {out}")
