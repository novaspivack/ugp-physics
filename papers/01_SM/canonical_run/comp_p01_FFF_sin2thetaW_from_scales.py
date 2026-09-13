"""
COMP-P01-FFF: sin^2(theta_W) via 2-loop + threshold-matched SM RG from
              SC-CC inverse-solved matching scales (Priority 6 / 05_SPEC /
              02_SPEC §E.1 / 08A_NOTE Candidate D, Round 32).

PIPELINE (Candidate D: continuous scale axis):
  1. Start at SC-CC Lean-certified bare couplings at their inverse-solved
     matching scales:
       g_1^2(M_1) from Lean (GUT-normalised); M_1 = 108.8 GeV
       g_2^2(M_2) = 2329/5400;                M_2 = 37.4 GeV
       g_3^2(M_3) from Lean;                  M_3 = 89.3 GeV
  2. Run each coupling via 2-loop + 6->5 flavour threshold SM RG from
     M_G to M_Z = 91.1876 GeV (same runner as Round 27 / SC-ZZ).
  3. Compute sin^2(theta_W) = g_1^2 / (g_1^2 + g_2^2) at M_Z (standard
     GUT->SM conversion: g'^2 = (3/5) g_1^2 in GUT-norm).
  4. Compare to PDG 0.23122.

SUCCESS GATES:
  - sin^2(theta_W)_predicted within PDG 1sigma (0.23122 +- 0.00004):
    FULL CLOSURE of OP(v')
  - Within 10sigma (0.2308 - 0.2316): PARTIAL CLOSURE
  - Beyond 10sigma: MAP; try Candidate E or F

NULL DISCIPLINE: repeat with randomised M_G values in a natural range;
if random M_G also closes at <=10sigma, the prediction is not
structurally distinguished.
"""

import math, json, hashlib, datetime, os
import numpy as np
from scipy.integrate import solve_ivp

# =====================================================================
# PDG 2022 central values
# =====================================================================
MZ_PDG = 91.1876
MW_PDG = 80.379
MT_PDG = 172.76
V_HIGGS = 246.22

ALPHA_EM_MZ = 1.0 / 127.952
SIN2_THETAW_PDG    = 0.23122
SIN2_THETAW_PDG_err = 0.00004   # experimental sigma
ALPHA_S_MZ = 0.1179

# =====================================================================
# Lean-certified bare squared couplings (from paper 1 Appendix F item 5)
# CONVENTION: paper uses SM normalization g_1 = g' (NOT GUT-normalised).
# Verified: g_1^2_SM = 16/125 = 0.128 matches PDG g'^2(M_Z) = 0.128 at 0.3%.
# Internal 2-loop runner uses GUT normalization (β_1 = 41/10).
# Conversion: g_1^2_GUT = (5/3) g_1^2_SM.
# =====================================================================
g1Sq_bare_SM  = 16.0 / 125.0
g1Sq_bare_GUT = (5.0/3.0) * g1Sq_bare_SM    # = 16/75, for internal runner
g2Sq_bare = 2329.0 / 5400.0
g3Sq_bare = 41075281.0 / 27648000.0

# SC-CC inverse-solved matching scales
M_1_SC_CC = 108.8   # GeV
M_2_SC_CC = 37.4
M_3_SC_CC = 89.3

# =====================================================================
# 2-loop + 6->5 flavour threshold-matched RG (same as SC-ZZ / Round 27)
# =====================================================================
b_1L_SM6 = np.array([ 41.0/10.0, -19.0/6.0, -7.0    ])
b_1L_SM5 = np.array([ 21.0/5.0,  -3.0,      -23.0/3.0 ])
b_2L_SM6 = np.array([
    [199.0/50.0, 27.0/10.0, 44.0/5.0],
    [  9.0/10.0, 35.0/6.0, 12.0],
    [ 11.0/10.0,  9.0/2.0, -26.0],
])
b_2L_SM5 = np.array([
    [199.0/50.0 - 17.0/10.0,  27.0/10.0 - 3.0/10.0, 44.0/5.0 - 4.0],
    [  9.0/10.0 - 3.0/10.0,  35.0/6.0 - 3.0/2.0,  12.0 - 4.0],
    [ 11.0/10.0 - 11.0/30.0,  9.0/2.0 - 1.0/2.0,  -26.0 + 22.0/3.0],
])
c_yuk_SM6 = np.array([
    [17.0/10.0, 1.0/2.0, 3.0/2.0],
    [3.0/2.0,   3.0/2.0, 1.0/2.0],
    [2.0,       2.0,     0.0],
])
c_yuk_SM5 = c_yuk_SM6.copy()
c_yuk_SM5[:, 0] = 0.0

def rhs_2L_thr(t, y):
    """2-loop SM gauge + 1-loop Yukawa with m_t threshold."""
    g1, g2, g3, yt, yb, yta = y
    mu = math.exp(t)
    if mu >= MT_PDG:
        b1, bij, cy = b_1L_SM6, b_2L_SM6, c_yuk_SM6
    else:
        b1, bij, cy = b_1L_SM5, b_2L_SM5, c_yuk_SM5
    g1_2, g2_2, g3_2 = g1*g1, g2*g2, g3*g3
    gsq = np.array([g1_2, g2_2, g3_2])
    gc = np.array([g1*g1_2, g2*g2_2, g3*g3_2])
    one_loop = gc / (16*math.pi**2) * b1
    yuk = np.array([yt*yt, yb*yb, yta*yta])
    two_loop = gc / (16*math.pi**2)**2 * (bij @ gsq - cy @ yuk)
    dg = one_loop + two_loop
    if mu >= MT_PDG:
        dyt = yt * (9/2*yt*yt - 8*g3_2 - 9/4*g2_2 - 17/20*g1_2) / (16*math.pi**2)
    else:
        dyt = 0.0
    dyb = yb * (3/2*yb*yb + yta*yta + (yt*yt if mu >= MT_PDG else 0)
                - 8*g3_2 - 9/4*g2_2 - 1/4*g1_2) / (16*math.pi**2)
    dyt_a = yta * (5/2*yta*yta + 3*yb*yb + (3*yt*yt if mu >= MT_PDG else 0)
                  - 9/4*g2_2 - 9/4*g1_2) / (16*math.pi**2)
    return [dg[0], dg[1], dg[2], dyt, dyb, dyt_a]

def run_single_coupling(g_sq_start, M_start, M_end, which='g2', loop_order=2, threshold=True):
    """Run one gauge coupling from M_start to M_end; other couplings held at SM values."""
    # Get SM values at M_Z for the other couplings (used as 'backdrop'):
    # g_1, g_2, g_3 at M_Z from PDG:
    e2 = 4 * math.pi * ALPHA_EM_MZ
    g2sq_mz_sm = e2 / SIN2_THETAW_PDG
    gpsq_mz_sm = e2 / (1 - SIN2_THETAW_PDG)
    g1sq_mz_sm = (5.0/3.0) * gpsq_mz_sm
    g3sq_mz_sm = 4 * math.pi * ALPHA_S_MZ
    yt_mz = math.sqrt(2) * MT_PDG / V_HIGGS
    yb_mz = math.sqrt(2) * 4.18 / V_HIGGS
    yta_mz = math.sqrt(2) * 1.77686 / V_HIGGS

    # Run SM backdrop from M_Z to M_start to get the backdrop at M_start:
    y_sm_mz = [math.sqrt(g1sq_mz_sm), math.sqrt(g2sq_mz_sm), math.sqrt(g3sq_mz_sm),
               yt_mz, yb_mz, yta_mz]
    sol_back = solve_ivp(rhs_2L_thr, (math.log(MZ_PDG), math.log(M_start)),
                         y_sm_mz, rtol=1e-11, atol=1e-13, max_step=0.05)
    y_at_start = list(sol_back.y[:, -1])

    # Now REPLACE the chosen coupling with the UGP-bare value:
    idx_map = {'g1': 0, 'g2': 1, 'g3': 2}
    idx = idx_map[which]
    y_at_start[idx] = math.sqrt(g_sq_start)

    # Run from M_start to M_end:
    sol_fwd = solve_ivp(rhs_2L_thr, (math.log(M_start), math.log(M_end)),
                        y_at_start, rtol=1e-11, atol=1e-13, max_step=0.05)
    return sol_fwd.y[idx, -1] ** 2   # return squared coupling at M_end

# =====================================================================
# Step 1: run each coupling from its inverse-solved scale to M_Z
# =====================================================================
print("=" * 72)
print("COMP-P01-FFF: sin^2(theta_W) via 2-loop + threshold running from SC-CC")
print("=" * 72)
print()
print("Lean-certified bare couplings (Appendix F item 5):")
print(f"  g_1^2 = 16/125 (SM) = {g1Sq_bare_SM:.6f}, GUT-norm g_1^2 = {g1Sq_bare_GUT:.6f}")
print(f"  g_2^2 = 2329/5400   = {g2Sq_bare:.6f}")
print(f"  g_3^2 = 41075281/27648000 = {g3Sq_bare:.6f}")
print()
print("SC-CC inverse-solved matching scales:")
print(f"  M_1 = {M_1_SC_CC} GeV, M_2 = {M_2_SC_CC} GeV, M_3 = {M_3_SC_CC} GeV")
print()
print(f"Run each coupling from M_G to M_Z = {MZ_PDG} GeV (2-loop + threshold):")

g1sq_mz_GUT = run_single_coupling(g1Sq_bare_GUT, M_1_SC_CC, MZ_PDG, 'g1')
g2sq_mz = run_single_coupling(g2Sq_bare, M_2_SC_CC, MZ_PDG, 'g2')
g3sq_mz = run_single_coupling(g3Sq_bare, M_3_SC_CC, MZ_PDG, 'g3')

# Convert g_1 GUT back to SM (= g' hypercharge)
gp_sq_mz = (3.0/5.0) * g1sq_mz_GUT   # = g'^2 in SM-norm
g1sq_mz_SM = gp_sq_mz                 # equivalent notation

print(f"  g_1^2(M_Z, SM=g'^2) = {g1sq_mz_SM:.6f} (from M_1 = {M_1_SC_CC} GeV; GUT value {g1sq_mz_GUT:.6f})")
print(f"  g_2^2(M_Z) = {g2sq_mz:.6f} (from M_2 = {M_2_SC_CC} GeV)")
print(f"  g_3^2(M_Z) = {g3sq_mz:.6f} (from M_3 = {M_3_SC_CC} GeV)")

# sin^2(theta_W) = g'^2 / (g'^2 + g_2^2) in SM normalization
sin2_pred = gp_sq_mz / (gp_sq_mz + g2sq_mz)

# Also for alpha_EM check
e_sq_pred = g2sq_mz * sin2_pred  # = g_2^2 * sin^2(theta_W)
alpha_em_pred = e_sq_pred / (4 * math.pi)

print()
print(f"PREDICTIONS at M_Z (2-loop + threshold):")
print(f"  sin^2(theta_W) = {sin2_pred:.5f}  (PDG: {SIN2_THETAW_PDG:.5f} +- {SIN2_THETAW_PDG_err:.5f})")
print(f"  Residual: {(sin2_pred - SIN2_THETAW_PDG):+.5f} = {(sin2_pred-SIN2_THETAW_PDG)/SIN2_THETAW_PDG_err:+.2f} sigma")
print(f"  alpha_EM = {alpha_em_pred:.6f}  (PDG: {ALPHA_EM_MZ:.6f})")
print(f"  Rel. err alpha_EM: {(alpha_em_pred - ALPHA_EM_MZ)/ALPHA_EM_MZ*1e6:+.1f} ppm")

# Baseline reference: paper's current 1-loop-ish value
sin2_tree_level = g1Sq_bare_SM / (g1Sq_bare_SM + g2Sq_bare)
print()
print(f"Comparison with tree-level (no running):")
print(f"  sin^2(theta_W) = {sin2_tree_level:.5f}  (deviation: {(sin2_tree_level-SIN2_THETAW_PDG)/SIN2_THETAW_PDG_err:+.1f} sigma)")

residual_sigma = abs((sin2_pred - SIN2_THETAW_PDG)/SIN2_THETAW_PDG_err)
tree_sigma = abs((sin2_tree_level-SIN2_THETAW_PDG)/SIN2_THETAW_PDG_err)
improvement = tree_sigma / residual_sigma if residual_sigma > 1e-9 else float('inf')
print()
print(f"IMPROVEMENT tree -> 2-loop+threshold: {tree_sigma:.1f}sigma -> {residual_sigma:.1f}sigma = {improvement:.2f}x")

if residual_sigma <= 1.0: verdict = "FULL CLOSURE (within PDG 1 sigma)"
elif residual_sigma <= 10.0: verdict = f"PARTIAL CLOSURE ({residual_sigma:.1f} sigma)"
else: verdict = f"MAP ({residual_sigma:.1f} sigma remaining)"
print(f"  VERDICT: {verdict}")

# =====================================================================
# Null test: randomise M_G in plausible ranges
# =====================================================================
print()
print("=" * 72)
print("Null test: randomise M_G in plausible ranges [20, 200] GeV")
print("=" * 72)
np.random.seed(42)
N_null = 200
null_sigmas = []
close_1 = 0; close_10 = 0
for _ in range(N_null):
    M1_r = np.random.uniform(20, 200)
    M2_r = np.random.uniform(20, 200)
    M3_r = np.random.uniform(20, 200)
    try:
        g1_r_GUT = run_single_coupling(g1Sq_bare_GUT, M1_r, MZ_PDG, 'g1')
        g2_r = run_single_coupling(g2Sq_bare, M2_r, MZ_PDG, 'g2')
        gp_sq_r = (3/5)*g1_r_GUT
        sin2_r = gp_sq_r / (gp_sq_r + g2_r)
        sig = abs((sin2_r - SIN2_THETAW_PDG)/SIN2_THETAW_PDG_err)
        null_sigmas.append(sig)
        if sig <= 1: close_1 += 1
        if sig <= 10: close_10 += 1
    except Exception:
        pass

print(f"  {N_null} random (M_1, M_2, M_3) values in [20, 200] GeV:")
print(f"  Close within 1 sigma: {close_1}/{N_null} = {100*close_1/N_null:.1f}%")
print(f"  Close within 10 sigma: {close_10}/{N_null} = {100*close_10/N_null:.1f}%")
null_sigmas = np.array(null_sigmas)
print(f"  Null median |sigma|: {np.median(null_sigmas):.1f}")
print(f"  Null best sigma: {np.min(null_sigmas):.2f}")
print()
print(f"  Structural (SC-CC M_G) sigma: {residual_sigma:.2f}")
print(f"  Fraction of null trials at/below structural: "
      f"{sum(1 for s in null_sigmas if s <= residual_sigma)}/{N_null}")

# =====================================================================
# Artifact
# =====================================================================
prediction = {
    "experiment_id": "COMP-P01-FFF",
    "title": "sin^2(theta_W) via 2-loop + threshold-matched running from SC-CC inverse-solved scales (Priority 6)",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "inputs": {
        "g1Sq_bare_lean": "16/125",
        "g2Sq_bare_lean": "2329/5400",
        "g3Sq_bare_lean": "41075281/27648000",
        "M_1_SC_CC_GeV": M_1_SC_CC,
        "M_2_SC_CC_GeV": M_2_SC_CC,
        "M_3_SC_CC_GeV": M_3_SC_CC,
    },
    "predictions": {
        "g1sq_MZ_GUT": g1sq_mz_GUT,
        "g1sq_MZ_SM": g1sq_mz_SM,
        "g2sq_MZ": g2sq_mz,
        "g3sq_MZ": g3sq_mz,
        "sin2_thetaW_predicted": sin2_pred,
        "sin2_thetaW_PDG": SIN2_THETAW_PDG,
        "residual_sigma": (sin2_pred - SIN2_THETAW_PDG)/SIN2_THETAW_PDG_err,
        "alpha_EM_predicted": alpha_em_pred,
        "alpha_EM_PDG": ALPHA_EM_MZ,
        "alpha_EM_rel_err_ppm": (alpha_em_pred - ALPHA_EM_MZ)/ALPHA_EM_MZ*1e6,
    },
    "comparisons": {
        "sin2_tree_level": sin2_tree_level,
        "tree_level_sigma": tree_sigma,
        "improvement_factor": improvement,
    },
    "null_test": {
        "N_samples": N_null,
        "M_G_range_GeV": [20, 200],
        "closures_1sigma": close_1,
        "closures_10sigma": close_10,
        "null_median_sigma": float(np.median(null_sigmas)),
        "null_best_sigma": float(np.min(null_sigmas)),
        "fraction_at_or_below_structural": sum(1 for s in null_sigmas if s <= residual_sigma) / len(null_sigmas),
    },
    "verdict": verdict,
}
block = json.dumps(prediction, sort_keys=True, indent=2, default=str)
prediction["pre_commit_sha256"] = hashlib.sha256(block.encode("utf-8")).hexdigest()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "comp_p01_FFF_sin2thetaW_from_scales.json")
with open(out, "w") as f:
    json.dump(prediction, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print()
print(f"Pre-commit SHA-256: {prediction['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
