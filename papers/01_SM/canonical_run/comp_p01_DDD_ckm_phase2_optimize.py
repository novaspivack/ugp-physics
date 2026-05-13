"""
COMP-P01-DDD: CKM Phase 2 via continuous O(1) optimization (Round 30 extension).

Phase 2a (SC-CCC) random-sampled over discrete UGP atom library:
  Best RMS 0.15 (15%), better than null (0.27) but not close to 5%.

Phase 2b (this): use scipy.optimize.minimize with continuous O(1) coefficients
and arbitrary phases to find the GLOBAL BEST achievable at the Round-21
flavon VEVs.  This tells us: is 5% even reachable in principle within the
FN framework at these flavon values, or is the framework fundamentally
limited?

GATES:
  - Continuous optimizer reaches RMS <= 0.05 (5%): Phase 2 FEASIBLE at
    Round-21 flavon VEVs.  Next step: find UGP-atom coefficients close to
    the optimizer's values.
  - Reaches 0.05 < RMS <= 0.10: PARTIAL feasibility.
  - Stalls at RMS > 0.10: fundamental framework limit; FN at these VEVs
    cannot reach 5% on CKM regardless of coefficient freedom.
"""

import math, json, hashlib, datetime, os
import numpy as np
from scipy.optimize import minimize, differential_evolution

# =====================================================================
# Flavon VEVs (Round 21)
# =====================================================================
log_eps_1 = -math.pi / 3
log_eps_2 = -math.pi / 8
eps_1 = math.exp(log_eps_1)
eps_2 = math.exp(log_eps_2)

V_PDG = np.array([
    [0.97373, 0.2243, 0.00382],
    [0.221,   0.975,  0.0408],
    [0.0086,  0.0415, 1.014],
])

a_Q = (-3, -2, 0)
b_Q = (-5, -3, 0)

# =====================================================================
# Unified builder: take vector of 2*9*2 = 36 parameters
#   params[0:9]   -> |c_u_ij|   (magnitudes for Y_u, 9 entries)
#   params[9:18]  -> phi_u_ij   (phases for Y_u, 9 entries)
#   params[18:27] -> |c_d_ij|
#   params[27:36] -> phi_d_ij
# =====================================================================

def build_Y_from_params(c_mag, phi_matrix, aR, bR):
    Y = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            Da = abs(a_Q[i] + aR[j])
            Db = abs(b_Q[i] + bR[j])
            Y[i, j] = c_mag[i, j] * eps_1**Da * eps_2**Db * np.exp(1j * phi_matrix[i, j])
    return Y

def compute_ckm(Y_u, Y_d):
    U_u, _, _ = np.linalg.svd(Y_u)
    U_d, _, _ = np.linalg.svd(Y_d)
    V = U_u.conj().T @ U_d
    return np.abs(V)

def loss(params):
    c_u = np.array(params[0:9]).reshape(3, 3)
    phi_u = np.array(params[9:18]).reshape(3, 3)
    c_d = np.array(params[18:27]).reshape(3, 3)
    phi_d = np.array(params[27:36]).reshape(3, 3)
    Y_u = build_Y_from_params(c_u, phi_u, a_Q, b_Q)
    Y_d = build_Y_from_params(c_d, phi_d, a_Q, b_Q)
    try:
        V = compute_ckm(Y_u, Y_d)
        # Use diagonal penalty (match PDG diagonal near 1) + off-diagonal
        loss = 0.0
        for i in range(3):
            for j in range(3):
                if i == j:
                    # light diagonal penalty
                    loss += 0.1 * (V[i,j] - V_PDG[i,j])**2
                else:
                    if V[i,j] > 1e-6:
                        loss += (math.log(V[i,j] / V_PDG[i,j]))**2
                    else:
                        loss += 100
        return loss
    except Exception:
        return 1e6

def rms_log_residual_matrix(V_pred):
    res = []
    for i in range(3):
        for j in range(3):
            if i != j:
                if V_pred[i, j] > 0:
                    res.append(math.log(V_pred[i, j] / V_PDG[i, j]))
                else:
                    res.append(10.0)
    return math.sqrt(sum(r*r for r in res) / len(res))

def max_off_diag_err(V_pred):
    return max(abs(V_pred[i,j] - V_PDG[i,j]) / V_PDG[i,j]
               for i in range(3) for j in range(3) if i != j)

# =====================================================================
# Global optimization
# =====================================================================
print("=" * 72)
print("COMP-P01-DDD: CKM Phase 2 via continuous O(1) optimization")
print("=" * 72)
print()
print(f"Flavon VEVs: ε_1 = {eps_1:.4f}, ε_2 = {eps_2:.4f}")
print(f"Charges: a_Q = {a_Q}, b_Q = {b_Q}")
print()

# Bounds: |c_ij| in [0.1, 3] (O(1) range), phi_ij in [-pi, pi]
bounds = [(0.1, 3.0)] * 9 + [(-math.pi, math.pi)] * 9 \
       + [(0.1, 3.0)] * 9 + [(-math.pi, math.pi)] * 9

print("Running differential evolution (global optimizer)...")
result = differential_evolution(loss, bounds, seed=42, maxiter=200, popsize=30,
                                tol=1e-8, disp=False, workers=1)

# Best result
params = result.x
c_u_best = params[0:9].reshape(3, 3)
phi_u_best = params[9:18].reshape(3, 3)
c_d_best = params[18:27].reshape(3, 3)
phi_d_best = params[27:36].reshape(3, 3)
Y_u_best = build_Y_from_params(c_u_best, phi_u_best, a_Q, b_Q)
Y_d_best = build_Y_from_params(c_d_best, phi_d_best, a_Q, b_Q)
V_best = compute_ckm(Y_u_best, Y_d_best)
rms_best = rms_log_residual_matrix(V_best)
max_err = max_off_diag_err(V_best)

print(f"\nOptimizer converged after {result.nit} iterations. Final loss: {result.fun:.4f}")
print(f"Best RMS log-residual: {rms_best:.4f}")
print(f"Max off-diagonal error: {max_err*100:.2f}%")
print()
print("Best |c_u| matrix:")
print(c_u_best)
print("Best |c_d| matrix:")
print(c_d_best)
print("Best phi_u matrix (rad):")
print(phi_u_best)
print("Best phi_d matrix (rad):")
print(phi_d_best)
print()
print(f"{'element':10s} {'PDG':>10s} {'predicted':>12s} {'err %':>8s}")
for i in range(3):
    for j in range(3):
        print(f"  V[{i}][{j}]    {V_PDG[i,j]:10.5f} {V_best[i,j]:12.5f} "
              f"{(V_best[i,j]-V_PDG[i,j])/V_PDG[i,j]*100:+8.2f}%")

if max_err <= 0.05:
    verdict = "FULL CLOSURE — ≤ 5% max off-diagonal"
elif max_err <= 0.10:
    verdict = "PARTIAL CLOSURE — ≤ 10% max off-diagonal"
elif max_err <= 0.20:
    verdict = "PARTIAL — ≤ 20% max off-diagonal"
else:
    verdict = "STRUCTURAL LIMIT — framework at these VEVs plateaus here"
print(f"\n  VERDICT: {verdict}")

# =====================================================================
# Check: are the optimized O(1) coefficients UGP-atom-matchable?
# =====================================================================
print()
print("=" * 72)
print("STEP 2: are optimizer's |c_ij| values UGP-atom-matchable?")
print("=" * 72)
phi = (1 + math.sqrt(5)) / 2
UGP_ATOMS_signed = {
    '1':       1.0,  '-1':      -1.0,
    'phi':     phi,  '-phi':    -phi,
    '1/phi':   1/phi,'-1/phi':  -1/phi,
    'phi^2':   phi**2, '-phi^2':  -phi**2,
    '1/phi^2': 1/phi**2, '-1/phi^2': -1/phi**2,
    'sqrt2':   math.sqrt(2), '-sqrt2':  -math.sqrt(2),
    'sqrt3':   math.sqrt(3), '-sqrt3':  -math.sqrt(3),
    '2':       2.0,    '-2':      -2.0,
    '1/2':     0.5,    '-1/2':    -0.5,
    '3':       3.0,    '-3':      -3.0,
    '1/3':     1/3,    '-1/3':    -1/3,
    '2/3':     2/3,    '-2/3':    -2/3,
    '3/2':     1.5,    '-3/2':    -1.5,
}

def closest_atom(value):
    best = (float('inf'), None)
    for name, v in UGP_ATOMS_signed.items():
        err = abs(abs(v) - abs(value))/abs(value) if abs(value) > 1e-6 else 10
        if err < best[0]:
            best = (err, name)
    return best

print("Optimizer |c_u| → closest UGP atom (magnitude-match within 15%):")
matches_u = []
for i in range(3):
    row_m = []
    for j in range(3):
        err, name = closest_atom(c_u_best[i,j])
        row_m.append(f"{name:7s} ({err*100:+5.1f}%)")
    print(f"  row {i}: {' | '.join(row_m)}")

print()
print("Optimizer |c_d| → closest UGP atom (magnitude-match within 15%):")
for i in range(3):
    row_m = []
    for j in range(3):
        err, name = closest_atom(c_d_best[i,j])
        row_m.append(f"{name:7s} ({err*100:+5.1f}%)")
    print(f"  row {i}: {' | '.join(row_m)}")

# =====================================================================
# Artifact
# =====================================================================
prediction = {
    "experiment_id": "COMP-P01-DDD",
    "title": "CKM Phase 2b: continuous optimization of O(1) coefficients + phases at Round-21 flavon VEVs",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "flavon_vevs": {"eps_1": eps_1, "eps_2": eps_2},
    "charge_assignment": {"a_Q": list(a_Q), "b_Q": list(b_Q)},
    "optimizer": {
        "method": "differential_evolution",
        "bounds_c_ij": [0.1, 3.0],
        "bounds_phi_ij": [-math.pi, math.pi],
        "iterations": result.nit,
    },
    "best_result": {
        "c_u": c_u_best.tolist(),
        "c_d": c_d_best.tolist(),
        "phi_u": phi_u_best.tolist(),
        "phi_d": phi_d_best.tolist(),
        "V_predicted": V_best.tolist(),
        "V_PDG": V_PDG.tolist(),
        "rms_log_residual": rms_best,
        "max_off_diagonal_error_pct": max_err * 100,
        "final_loss": result.fun,
    },
    "verdict": verdict,
}
block = json.dumps(prediction, sort_keys=True, indent=2, default=str)
prediction["pre_commit_sha256"] = hashlib.sha256(block.encode("utf-8")).hexdigest()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "comp_p01_DDD_ckm_phase2_optimize.json")
with open(out, "w") as f:
    json.dump(prediction, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print()
print(f"Pre-commit SHA-256: {prediction['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
