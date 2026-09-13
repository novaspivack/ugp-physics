#!/usr/bin/env python3
"""
SPEC_051_EWV Phase 0, Task 0.1
Extract g2(M_W) from the UGP two-loop RGE, compute the EW VEV error decomposition,
and show what m_H would be under different v scenarios.

Key structural inputs (NO G_F used):
  - g2_bare = sqrt(2329/5400)  [Lean-certified]
  - lambda_H = phi/(4*pi)       [SM-18, A/D]
  - sin2_theta_W_UGP = 3456/15101  [bare, Lean-adjacent]
  - m_Z = 91.1876 GeV          [one external input — used as alternative to G_F]
  - M2_matching = 37.4 GeV     [from SC-CC 1-loop analysis in ZZ script]
"""
import math, json
import numpy as np
from scipy.integrate import solve_ivp
from datetime import date
import os

os.makedirs("/Users/nova/ugp-physics/data_mining/ew_vev/results", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# UGP Structural constants (Lean-certified or confirmed)
# ─────────────────────────────────────────────────────────────────────────────
g2sq_bare      = 2329.0 / 5400.0                  # Lean: g2Sq_bare_eq
g2_bare        = math.sqrt(g2sq_bare)
phi            = (1 + math.sqrt(5)) / 2
lam_H_ugp      = phi / (4 * math.pi)              # SM-18: lambda_H = phi/(4pi)
sin2_tW_ugp    = 3456.0 / 15101.0                 # SM-08: sin2 theta_W (tree, bare)

# PDG 2024 reference values (for comparison only)
MZ_PDG         = 91.1876       # GeV — used as EW anchor (alternative to G_F)
MT_PDG         = 172.76        # GeV — top for threshold matching
mW_PDG         = 80.3792       # GeV (PDG 2024 world average)
v_PDG          = 246.220       # GeV (from G_F — reference only)
mH_PDG         = 125.20        # GeV
mH_PDG_unc     = 0.11          # GeV

# SM running coupling inputs at M_Z (SM starting point for RGE)
alpha_EM_MZ    = 1.0 / 127.952
sin2_tW_MZ     = 0.23122       # SM MSbar at M_Z
alpha_s_MZ     = 0.1179

# ─────────────────────────────────────────────────────────────────────────────
# SM 2-loop beta function (same as ZZ script, copied for self-containment)
# ─────────────────────────────────────────────────────────────────────────────
b_1L_SM6 = np.array([ 41.0/10.0, -19.0/6.0, -7.0     ])
b_1L_SM5 = np.array([ 21.0/5.0,  -3.0,      -23.0/3.0 ])
b_2L_SM6 = np.array([
    [199/50,  27/10,  44/5],
    [  9/10,  35/6,   12.0],
    [ 11/10,   9/2,  -26.0],
])
b_2L_SM5 = np.array([
    [199/50-17/10, 27/10-3/10, 44/5-4],
    [  9/10-3/10,  35/6-3/2,  12-4  ],
    [ 11/10-11/30,  9/2-1/2, -26+22/3],
])

def rhs_gauge_only(t, y):
    """2-loop SM gauge-only RGE (no Yukawa). t = ln(mu), y = [g1, g2, g3]."""
    g1, g2, g3 = y
    mu = math.exp(t)
    b1L = b_1L_SM6 if mu >= MT_PDG else b_1L_SM5
    b2L = b_2L_SM6 if mu >= MT_PDG else b_2L_SM5
    gsq = np.array([g1*g1, g2*g2, g3*g3])
    dg = np.zeros(3)
    for i, g in enumerate([g1, g2, g3]):
        one_loop = b1L[i] * gsq[i] / (16*math.pi**2)
        two_loop = g * np.dot(b2L[i], gsq) / (16*math.pi**2)**2
        dg[i] = g * (one_loop + two_loop)
    return list(dg)

# SM couplings at M_Z (starting point for running)
g1sq_MZ = (5/3) * 4*math.pi*alpha_EM_MZ / (1 - sin2_tW_MZ)
g2sq_MZ = 4*math.pi*alpha_EM_MZ / sin2_tW_MZ
g3sq_MZ = 4*math.pi*alpha_s_MZ
g1_MZ, g2_MZ, g3_MZ = math.sqrt(g1sq_MZ), math.sqrt(g2sq_MZ), math.sqrt(g3sq_MZ)

def run_couplings_from_MZ_to(mu_target):
    """Run SM couplings from M_Z to mu_target."""
    t_span = (math.log(MZ_PDG), math.log(mu_target))
    if t_span[0] == t_span[1]:
        return [g1_MZ, g2_MZ, g3_MZ]
    y0 = [g1_MZ, g2_MZ, g3_MZ]
    sol = solve_ivp(rhs_gauge_only, t_span, y0, method='RK45', rtol=1e-10, atol=1e-12,
                    dense_output=True, max_step=0.05)
    return sol.y[:, -1]

def run_ugp_from_M2_to(M2, mu_target):
    """
    Run UGP-bare g2 from M2 to mu_target using SM 2-loop RGE.
    At M2: replace g2 with g2_bare; keep g1, g3 from SM running.
    """
    # Step 1: run SM from M_Z down to M2 to get g1, g3 at M2
    couplings_M2 = run_couplings_from_MZ_to(M2)
    g1_M2, _, g3_M2 = couplings_M2
    # Step 2: replace g2 with UGP bare at M2
    y0 = [g1_M2, g2_bare, g3_M2]
    # Step 3: run from M2 up to mu_target
    t_span = (math.log(M2), math.log(mu_target))
    sol = solve_ivp(rhs_gauge_only, t_span, y0, method='RK45', rtol=1e-10, atol=1e-12,
                    dense_output=True, max_step=0.05)
    return sol.y[:, -1]   # [g1, g2, g3] at mu_target

# ─────────────────────────────────────────────────────────────────────────────
# Task 0.1a: Extract g2(M_W) from UGP running
# ─────────────────────────────────────────────────────────────────────────────
M2_ref = 37.4   # GeV — matching scale from SC-CC 1-loop analysis

# Run UGP g2 from M2 to M_W scale (use PDG m_W as the target scale for now)
couplings_at_mW = run_ugp_from_M2_to(M2_ref, mW_PDG)
g1_at_mW, g2_at_mW, g3_at_mW = couplings_at_mW

print(f"=== g2(M_W) from UGP two-loop running ===")
print(f"  M2 matching scale:  {M2_ref} GeV")
print(f"  g2_bare (at M2):    {g2_bare:.8f}")
print(f"  g2_UGP(M_W):        {g2_at_mW:.8f}")
print(f"  g2_SM(M_Z):         {g2_MZ:.8f}")
print()

# What v does this g2(M_W) imply if we use PDG m_W?
v_from_ugp_g2 = 2 * mW_PDG / g2_at_mW
print(f"=== v from UGP g2(M_W) running + PDG m_W ===")
print(f"  v_self = 2*mW_PDG/g2_UGP(M_W) = {v_from_ugp_g2:.4f} GeV  (PDG: {v_PDG:.3f}, dev: {100*(v_from_ugp_g2-v_PDG)/v_PDG:+.3f}%)")

# m_H from this v and lambda_H
mH_self = v_from_ugp_g2 * math.sqrt(2 * lam_H_ugp)
print(f"  m_H = v_self * sqrt(2*lam_H) = {mH_self:.4f} GeV  (PDG: {mH_PDG}, dev: {100*(mH_self-mH_PDG)/mH_PDG:+.3f}%, {(mH_self-mH_PDG)/mH_PDG_unc:.2f}σ)")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Task 0.1b: Alternative — use m_Z as anchor instead of G_F
# v from {m_Z, sin2_tW_UGP} (tree level) + g2_UGP(M_W) running
# ─────────────────────────────────────────────────────────────────────────────
cos_tW_ugp  = math.sqrt(1 - sin2_tW_ugp)
mW_tree_ugp = MZ_PDG * cos_tW_ugp                    # tree-level m_W from UGP sin2θ_W + m_Z
v_from_mZ   = 2 * mW_tree_ugp / g2_at_mW             # v with m_Z as anchor, no G_F

mH_from_mZ  = v_from_mZ * math.sqrt(2 * lam_H_ugp)

print(f"=== Path 1b: v from m_Z (no G_F) ===")
print(f"  sin2_tW_UGP = 3456/15101 = {sin2_tW_ugp:.6f}  (SM-08)")
print(f"  cos_tW_UGP  = {cos_tW_ugp:.6f}")
print(f"  m_W_tree_UGP = m_Z * cos_tW = {mW_tree_ugp:.4f} GeV  (PDG: {mW_PDG:.3f}, dev: {100*(mW_tree_ugp-mW_PDG)/mW_PDG:+.3f}%)")
print(f"  v_from_mZ = 2*m_W_tree/g2_UGP(M_W) = {v_from_mZ:.4f} GeV  (PDG: {v_PDG:.3f}, dev: {100*(v_from_mZ-v_PDG)/v_PDG:+.3f}%)")
print(f"  m_H = {mH_from_mZ:.4f} GeV  (PDG: {mH_PDG}, dev: {100*(mH_from_mZ-mH_PDG)/mH_PDG:+.3f}%, {(mH_from_mZ-mH_PDG)/mH_PDG_unc:.2f}σ)")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Task 0.1c: Error decomposition — where does the 9σ come from?
# ─────────────────────────────────────────────────────────────────────────────
lam_H_sm  = mH_PDG**2 / (2 * v_PDG**2)         # SM target lambda_H
v_ugp_bare = 2 * mW_PDG / g2_bare               # naive: using bare g2, no running
v_ugp_run  = 2 * mW_PDG / g2_at_mW              # self-consistent: using running g2

print(f"=== Error decomposition ===")
print(f"  SM target lambda_H:   {lam_H_sm:.6f}")
print(f"  UGP lambda_H = phi/4pi: {lam_H_ugp:.6f}  (dev: {100*(lam_H_ugp-lam_H_sm)/lam_H_sm:+.3f}%)")
print()
print(f"  v (bare g2):    {v_ugp_bare:.4f} GeV  (dev from PDG: {100*(v_ugp_bare-v_PDG)/v_PDG:+.3f}%)")
print(f"  v (running g2): {v_ugp_run:.4f} GeV  (dev from PDG: {100*(v_ugp_run-v_PDG)/v_PDG:+.3f}%)")
print(f"  v (PDG):        {v_PDG:.4f} GeV")
print()

scenarios = [
    ("PDG v + UGP lambda_H",          v_PDG,     lam_H_ugp, "Shows lambda_H contribution alone"),
    ("UGP v (bare g2) + UGP lambda_H", v_ugp_bare, lam_H_ugp, "Full UGP prediction (bare g2 — P01 direct)"),
    ("UGP v (running g2) + UGP lambda_H", v_ugp_run, lam_H_ugp, "Path 1a: running g2 + PDG m_W (circular)"),
    ("v from m_Z (no G_F) + UGP lambda_H", v_from_mZ, lam_H_ugp, "Path 1b: m_Z anchor (independent of G_F)"),
    ("PDG v + SM lambda_H",           v_PDG,     lam_H_sm,  "SM reference (should give PDG m_H)"),
]

print(f"  {'Scenario':<50} {'m_H (GeV)':<12} {'dev%':<10} {'sigma':<8}")
print(f"  {'-'*50} {'-'*12} {'-'*10} {'-'*8}")
results = []
for label, v, lam, note in scenarios:
    mh = v * math.sqrt(2 * lam)
    dev = 100*(mh - mH_PDG)/mH_PDG
    sig = (mh - mH_PDG)/mH_PDG_unc
    print(f"  {label:<50} {mh:<12.4f} {dev:<10.3f} {sig:<8.2f}  [{note}]")
    results.append({"scenario": label, "v_GeV": v, "lam_H": lam,
                    "mH_GeV": mh, "dev_pct": dev, "sigma": sig, "note": note})
print()

# The KEY question: what v is needed to make m_H exact with UGP lambda_H?
v_needed = mH_PDG / math.sqrt(2 * lam_H_ugp)
print(f"  v needed for m_H=125.20 with UGP lambda_H: {v_needed:.4f} GeV")
print(f"  (PDG v = {v_PDG:.4f}, gap = {v_needed - v_PDG:+.4f} GeV = {100*(v_needed-v_PDG)/v_PDG:+.3f}%)")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Save results
# ─────────────────────────────────────────────────────────────────────────────
output = {
    "date": str(date.today()),
    "spec": "SPEC_051_EWV Phase 0 Task 0.1",
    "g2_bare": g2_bare,
    "g2_at_mW_ugp_running": g2_at_mW,
    "M2_matching_GeV": M2_ref,
    "lam_H_ugp": lam_H_ugp,
    "lam_H_sm": lam_H_sm,
    "v_PDG": v_PDG,
    "v_ugp_bare_g2": v_ugp_bare,
    "v_ugp_running_g2": v_ugp_run,
    "v_from_mZ_no_GF": v_from_mZ,
    "v_needed_for_exact_mH": v_needed,
    "mH_scenarios": results,
    "conclusion": {
        "path1a": f"v from running g2 + PDG m_W = {v_ugp_run:.4f} GeV — CIRCULAR (m_W used PDG v)",
        "path1b": f"v from m_Z + sin2_tW_UGP + running g2 = {v_from_mZ:.4f} GeV → m_H = {mH_from_mZ:.3f} GeV ({(mH_from_mZ-mH_PDG)/mH_PDG_unc:.2f}σ) — uses m_Z not G_F",
        "lam_H_contribution": f"{100*(lam_H_ugp-lam_H_sm)/lam_H_sm:+.3f}% → {(mH_PDG*math.sqrt(lam_H_ugp/lam_H_sm) - mH_PDG)/mH_PDG_unc:.2f}σ residual even with perfect v",
        "v_gap": f"{100*(v_ugp_run-v_PDG)/v_PDG:+.3f}% in v → dominates the m_H error",
    }
}
with open("/Users/nova/ugp-physics/data_mining/ew_vev/results/path0_error_decomposition.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"Saved to data_mining/ew_vev/results/path0_error_decomposition.json")
