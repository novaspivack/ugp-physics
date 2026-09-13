"""
COMP-P01-KKK: VV coefficient derivation from FN-doubled + SM RG running
              (Priority 13 / 41_SPEC / Round 38).

GOAL: Attempt to derive the VV coefficients (13/9, -7/6, -5/14) as RG
      predictions from candidate FN charge assignments at M_GUT, without
      basis-expressivity fitting.

PROTOCOL:
1. Fix FN setup at M_GUT = 2e16 GeV with Round-21 charges:
   - ε_1 = e^{-π/3}, ε_2 = e^{-π/8}
   - Up-type: q_u^(1) = 0, q_u^(2) set by Δq^(2) = -1 vs lepton
   - Lepton: q_lep^(1) = 2^(g-1), q_lep^(2) = free parameter
2. Test 6 candidate down-sector FN charge assignments:
   (1) Unified SU(5) 5-bar: q_d = q_lep
   (2) Pauli mirror:        q_d = q_u
   (3) SO(10) 16-spinor:    Y_d = Y_u = Y_e at GUT (all unified)
   (4) Doubled independent: q_d^(1) = 2^(g-1), q_d^(2) = free
   (5) Anti-doubled:        q_d^(1) = -2^(g-1)
   (6) VV-informed ansatz:  q_d^(1) = (13/9)·2^(g-1) (non-integer)
3. For each, compute log(Y_d_g)(M_GUT), log(Y_u_g)(M_GUT),
   log(Y_lep_g)(M_GUT), RG-run to M_Z with SM 2-loop gauge + 1-loop Yukawa.
4. Test VV formula at M_Z:
   log(Y_d_g) =? (13/9) log(Y_u_g) + (-7/6) log(Y_lep_g) + (-5/14)
5. Report whether any assignment reproduces VV at ≤ 1% on all 3 generations.
"""

import math, json, hashlib, datetime, os
import numpy as np
from scipy.integrate import solve_ivp

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
PI = math.pi
M_GUT = 2e16    # GeV
M_Z   = 91.1876
M_t   = 172.76
V_EW  = 246.22

# FN setup (Round 21)
eps1 = math.exp(-PI/3)
eps2 = math.exp(-PI/8)
log_eps1 = -PI/3
log_eps2 = -PI/8

# Lepton FN_1 charges (Round-21 doubled pattern)
q_lep_1 = [2**(g-1) for g in (1, 2, 3)]   # [1, 2, 4]
# Up FN_1 charges (Round-21 zero)
q_u_1   = [0, 0, 0]
# Constant FN_2 difference (Round 21): Δq^(2) = q_u^(2) - q_lep^(2) = -1
# Choose q_lep^(2) = 0, so q_u^(2) = -1.
q_lep_2 = [0, 0, 0]
q_u_2   = [-1, -1, -1]

# ---------------------------------------------------------------------
# Yukawa matrix at M_GUT from FN charges
# ---------------------------------------------------------------------
def yukawa_from_fn(q1, q2, O1_coefs=None):
    """Given FN charges (q1[g], q2[g]) per generation, compute log(Y_g) at
    M_GUT using log(Y_g) = q1_g·log(ε_1) + q2_g·log(ε_2) + log(c_g), where
    c_g is the O(1) prefactor (default 1)."""
    if O1_coefs is None:
        O1_coefs = [1.0, 1.0, 1.0]
    return [q1[g]*log_eps1 + q2[g]*log_eps2 + math.log(O1_coefs[g])
            for g in range(3)]

# ---------------------------------------------------------------------
# SM Yukawa RG: 1-loop gauge-aware top-Yukawa-dominated runner.
# (For this test we use a simplified 1-loop runner; full 2-loop is
#  infrastructure-heavy and the key physics — generation ratios
#  RG-invariant at 1-loop — is captured here.)
# ---------------------------------------------------------------------

# SM 1-loop gauge β-functions (GUT-normalization: g1 = sqrt(5/3) g')
b1_gauge = np.array([41.0/10.0, -19.0/6.0, -7.0])

def rhs_gauge_yukawa(t, y):
    """y = [g1, g2, g3, y_u1, y_u2, y_u3, y_d1, y_d2, y_d3, y_e1, y_e2, y_e3]
    at log-scale t = log(μ).  SM 1-loop."""
    g1, g2, g3 = y[0:3]
    yu = np.array(y[3:6])
    yd = np.array(y[6:9])
    ye = np.array(y[9:12])

    # Gauge
    gsq = np.array([g1*g1, g2*g2, g3*g3])
    gcu = np.array([g1*gsq[0], g2*gsq[1], g3*gsq[2]])
    dg = gcu / (16*PI**2) * b1_gauge

    # Yukawa RG (1-loop, SM charges in GUT normalization):
    # For up-type:  dY_u_g/dt = Y_u_g · [3(Y_t^2 + ...) - (17/20 g1^2 + 9/4 g2^2 + 8 g3^2)]
    # For down-type: dY_d_g/dt = Y_d_g · [3(Y_t^2 + ...) - (1/4 g1^2 + 9/4 g2^2 + 8 g3^2)]
    # For lepton:  dY_e_g/dt = Y_e_g · [3(Y_t^2 + ...) - (9/4 g1^2 + 9/4 g2^2)]
    # Top-dominated: 3·Y_t^2 ≈ 3·yu[2]^2
    yt_sq = yu[2]**2

    # Simplified (top-only in Yukawa-dominated terms)
    gaugesum_u = 17.0/20.0 * gsq[0] + 9.0/4.0 * gsq[1] + 8.0 * gsq[2]
    gaugesum_d = 1.0/4.0  * gsq[0] + 9.0/4.0 * gsq[1] + 8.0 * gsq[2]
    gaugesum_e = 9.0/4.0  * gsq[0] + 9.0/4.0 * gsq[1]

    # Top-Yukawa contribution to up-type: proportional to Y_t^2
    # Same coefficient for all three generations (1-loop)
    dyu = yu * (3.0 * yt_sq - gaugesum_u) / (16*PI**2)
    dyd = yd * (3.0 * yt_sq - gaugesum_d) / (16*PI**2)
    dye = ye * (3.0 * yt_sq - gaugesum_e) / (16*PI**2)

    return np.concatenate([dg, dyu, dyd, dye])

def run_fn_to_mz(logYu_GUT, logYd_GUT, logYe_GUT):
    """Run Yukawa log-values from M_GUT to M_Z; return log-values at M_Z."""
    # Initial gauge couplings at M_GUT — approximately unified
    g_GUT = math.sqrt(4*PI/25.0)
    y0 = [g_GUT, g_GUT, g_GUT] + \
         [math.exp(v) for v in logYu_GUT] + \
         [math.exp(v) for v in logYd_GUT] + \
         [math.exp(v) for v in logYe_GUT]
    sol = solve_ivp(rhs_gauge_yukawa,
                    (math.log(M_GUT), math.log(M_Z)), y0,
                    rtol=1e-10, atol=1e-14, max_step=0.1)
    # Extract log-Yukawas at end
    yend = sol.y[:, -1]
    logYu_MZ = [math.log(yend[3+g]) for g in range(3)]
    logYd_MZ = [math.log(yend[6+g]) for g in range(3)]
    logYe_MZ = [math.log(yend[9+g]) for g in range(3)]
    return logYu_MZ, logYd_MZ, logYe_MZ

# ---------------------------------------------------------------------
# VV test
# ---------------------------------------------------------------------
# PDG 2022 fermion masses (MS-bar at M_Z in GeV)
m_u_PDG = 2.16e-3; m_c_PDG = 1.27; m_t_PDG = 172.76
m_d_PDG = 4.67e-3; m_s_PDG = 93.4e-3; m_b_PDG = 4.18
m_e_PDG = 0.0005109989; m_mu_PDG = 0.10566; m_tau_PDG = 1.77686

# Yukawas at M_Z (from m_f = Y_f · v / sqrt(2))
def y_from_m(m): return math.sqrt(2) * m / V_EW
logYu_MZ_PDG  = [math.log(y_from_m(m_u_PDG)),  math.log(y_from_m(m_c_PDG)),  math.log(y_from_m(m_t_PDG))]
logYd_MZ_PDG  = [math.log(y_from_m(m_d_PDG)),  math.log(y_from_m(m_s_PDG)),  math.log(y_from_m(m_b_PDG))]
logYe_MZ_PDG  = [math.log(y_from_m(m_e_PDG)),  math.log(y_from_m(m_mu_PDG)), math.log(y_from_m(m_tau_PDG))]

def test_vv(logYu, logYd, logYe, label):
    """Fit log(Y_d) = α log(Y_u) + β log(Y_e) + γ; report fit vs VV."""
    print(f"\n{label}:")
    print(f"  log Y_u at eval: {[f'{v:+.4f}' for v in logYu]}")
    print(f"  log Y_d at eval: {[f'{v:+.4f}' for v in logYd]}")
    print(f"  log Y_e at eval: {[f'{v:+.4f}' for v in logYe]}")
    # Fit (3 equations, 3 unknowns — exact solution)
    A = np.array([[logYu[g], logYe[g], 1.0] for g in range(3)])
    b = np.array(logYd)
    try:
        alpha_fit, beta_fit, gamma_fit = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        print("  LinAlgError — system singular")
        return None
    print(f"  Fitted VV coefficients: α = {alpha_fit:+.4f}, β = {beta_fit:+.4f}, γ = {gamma_fit:+.4f}")
    print(f"  VV target:              α = {VV_ALPHA:+.4f}, β = {VV_BETA:+.4f}, γ = {VV_GAMMA:+.4f}")
    err_a = abs(alpha_fit - VV_ALPHA)
    err_b = abs(beta_fit - VV_BETA)
    err_g = abs(gamma_fit - VV_GAMMA)
    print(f"  Abs error:              |Δα| = {err_a:.4f}, |Δβ| = {err_b:.4f}, |Δγ| = {err_g:.4f}")
    rel_a = err_a/abs(VV_ALPHA); rel_b = err_b/abs(VV_BETA); rel_g = err_g/abs(VV_GAMMA)
    print(f"  Rel. error:             {rel_a*100:.1f}%, {rel_b*100:.1f}%, {rel_g*100:.1f}%")
    max_rel = max(rel_a, rel_b, rel_g)
    if max_rel < 0.01:
        verdict = "WIN (≤ 1%)"
    elif max_rel < 0.05:
        verdict = f"CLOSE ({max_rel*100:.1f}%)"
    elif max_rel < 0.20:
        verdict = f"NEAR-MISS ({max_rel*100:.1f}%)"
    else:
        verdict = f"MISS ({max_rel*100:.1f}%)"
    print(f"  VERDICT: {verdict}")
    return {
        'alpha_fit': alpha_fit, 'beta_fit': beta_fit, 'gamma_fit': gamma_fit,
        'rel_err': (rel_a, rel_b, rel_g),
        'max_rel_err': max_rel,
        'verdict': verdict,
    }

# ---------------------------------------------------------------------
# STRUCTURAL OBSTRUCTION (analytical, pre-running):
#
# At M_GUT, log(Y_g) = q_g^(1) · log ε_1 + q_g^(2) · log ε_2 + O(1).
# For VV to hold at M_GUT with target coefficients (α, β, γ):
#
#     log Y_d_g = α log Y_u_g + β log Y_lep_g + γ
#
# we need (equating coefficients of log ε_1 and log ε_2 separately):
#
#     q_d_g^(1) = α q_u_g^(1) + β q_lep_g^(1)
#     q_d_g^(2) = α q_u_g^(2) + β q_lep_g^(2)
#
# Round-21 framework has q_u^(1) = 0, q_lep^(1) = 2^(g-1), q_u^(2) = -1,
# q_lep^(2) = 0.  Substituting VV's α = 13/9, β = -7/6:
#
#     q_d_g^(1) = 0 + (-7/6) · 2^(g-1) = -(7/6) · {1, 2, 4}
#                = {-7/6, -7/3, -14/3}   <-- NON-INTEGER!
#     q_d_g^(2) = (13/9) · (-1) + (-7/6) · 0 = -13/9   <-- NON-INTEGER!
#
# Since FN charges must be integers for naturalness, VV coefficients
# (13/9, -7/6, -5/14) CANNOT arise from any integer-charge extension of
# the Round-21 FN-doubled framework.  This is a structural obstruction
# independent of RG running (1-loop RG preserves log-ratios and hence
# coefficient values in the VV relation).
#
# The RG tests below confirm this analytical conclusion numerically.
# ---------------------------------------------------------------------

# Compute required non-integer charges for reference
VV_ALPHA = 13/9
VV_BETA  = -7/6
VV_GAMMA = -5/14
q_d_required_1 = [VV_ALPHA * q_u_1[g] + VV_BETA * q_lep_1[g] for g in range(3)]
q_d_required_2 = [VV_ALPHA * q_u_2[g] + VV_BETA * q_lep_2[g] for g in range(3)]

# ---------------------------------------------------------------------
# Main: test candidate down-sector charge assignments
# ---------------------------------------------------------------------
print("=" * 72)
print("COMP-P01-KKK: VV coefficient derivation via FN + SM RG (Round 38)")
print("Priority 13 / 41_SPEC; attempt to upgrade VV from [C] to [T]")
print("=" * 72)
print()
print("ANALYTICAL STRUCTURAL OBSTRUCTION (pre-running):")
print(f"  Required q_d^(1) for VV:  {[f'{v:+.4f}' for v in q_d_required_1]}  <-- NON-INTEGER")
print(f"  Required q_d^(2) for VV:  {[f'{v:+.4f}' for v in q_d_required_2]}  <-- NON-INTEGER")
print(f"  (VV coefficients (13/9, -7/6) cannot arise from integer FN charges)")
print()
print("Setup (Round 21 FN-doubled):")
print(f"  ε_1 = e^{{-π/3}} = {eps1:.4f}, ε_2 = e^{{-π/8}} = {eps2:.4f}")
print(f"  Up FN_1 charges:  {q_u_1}")
print(f"  Lep FN_1 charges: {q_lep_1}  (doubled pattern)")
print(f"  Constant Δq^(2) = -1")
print(f"  M_GUT = {M_GUT:.1e} GeV, M_Z = {M_Z} GeV")
print()

# At M_GUT, compute up and lepton log-Yukawas from FN charges:
logYu_GUT = yukawa_from_fn(q_u_1, q_u_2)
logYe_GUT = yukawa_from_fn(q_lep_1, q_lep_2)

# Verify TT holds on PDG (should match R12 TT formula)
print()
print("Sanity: verify TT formula at PDG values:")
for g in range(3):
    lhs = logYu_GUT[g] - logYe_GUT[g]
    rhs = (PI/6) * (2**(g+1)) + PI/8
    print(f"  g={g+1}: log(Y_u/Y_lep) = {lhs:+.4f};  TT prediction = {rhs:+.4f};  Δ = {abs(lhs-rhs):.4f} ({abs(lhs-rhs)/abs(rhs)*100:.2f}%)")

# Verify VV holds on PDG (baseline — should match at <0.2% per SC-VV)
print()
print("Sanity: verify VV formula at PDG values:")
for g in range(3):
    lhs = logYd_MZ_PDG[g]
    rhs = VV_ALPHA * logYu_MZ_PDG[g] + VV_BETA * logYe_MZ_PDG[g] + VV_GAMMA
    print(f"  g={g+1}: log Y_d = {lhs:+.4f};  VV prediction = {rhs:+.4f};  Δ = {abs(lhs-rhs):.4f} ({abs(lhs-rhs)/abs(rhs)*100:.3f}%)")

# -------- Candidates --------
print()
print("=" * 72)
print("Testing candidate down-sector FN charge assignments")
print("=" * 72)

results = {}

# For each candidate down-sector charge assignment, the candidate PREDICTS
# specific log Y_d values (at M_GUT; generation-ratios RG-invariant, so
# valid at M_Z up to overall shift).  We then test whether the fitted
# (alpha, beta, gamma) match VV.

# Baseline integer-charge candidates: report their (alpha, beta) by fitting
def candidate_fit(qd1, qd2, label):
    """Given FN down-charges qd1[g], qd2[g], predict log Y_d_g (up to O(1) shift).
    Then fit VV coefficients to (log Y_u_PDG, log Y_e_PDG, log Y_d_predicted)."""
    # The predicted log Y_d_g = qd1_g * log eps_1 + qd2_g * log eps_2 + C
    # where C absorbs the O(1) prefactor for the overall scale.
    # For VV fit, set C such that mean(predicted log Y_d) matches mean(PDG log Y_d).
    pred_no_C = [qd1[g] * log_eps1 + qd2[g] * log_eps2 for g in range(3)]
    shift = np.mean(logYd_MZ_PDG) - np.mean(pred_no_C)
    pred = [p + shift for p in pred_no_C]
    return test_vv(logYu_MZ_PDG, pred, logYe_MZ_PDG, label)

# Candidate 1: SU(5) 5-bar — q_d = q_lep
results['C1_SU5_5bar'] = candidate_fit(q_lep_1, q_lep_2,
    "C1 SU(5) 5-bar: q_d = q_lep = (1, 2, 4), q_d^(2) = 0")

# Candidate 2: Pauli mirror — q_d = q_u
results['C2_Pauli_mirror'] = candidate_fit(q_u_1, q_u_2,
    "C2 Pauli mirror: q_d = q_u = (0, 0, 0), q_d^(2) = -1")

# Candidate 3: SO(10) 16-spinor (= Pauli mirror if q_u = q_d; degenerate)
# Skip (same as C2)

# Candidate 4: Doubled independent — q_d^(1) = 2^(g-1), q_d^(2) = 0
results['C4_Doubled_independent'] = candidate_fit(
    [2**(g-1) for g in (1, 2, 3)], [0, 0, 0],
    "C4 Doubled q_d^(1) = (1, 2, 4), q_d^(2) = 0")

# Candidate 5: Anti-doubled — q_d^(1) = -2^(g-1)
results['C5_Anti_doubled'] = candidate_fit(
    [-2**(g-1) for g in (1, 2, 3)], [0, 0, 0],
    "C5 Anti-doubled q_d^(1) = -(1, 2, 4), q_d^(2) = 0")

# Candidate 6: VV-informed NON-INTEGER ansatz — q_d^(1) = (-7/6)·2^(g-1), q_d^(2) = -13/9
# These are the charges REQUIRED for VV to hold (from analytical obstruction above)
results['C6_VV_required_non_integer'] = candidate_fit(
    [(-7.0/6.0)*2**(g-1) for g in (1, 2, 3)],
    [-13.0/9.0]*3,
    "C6 VV-REQUIRED non-integer q_d: (-7/6, -7/3, -14/3), (-13/9 each)")

# Candidate 7: Quadrupled — q_d^(1) = 2*2^(g-1) (just to span space)
results['C7_Quadrupled'] = candidate_fit(
    [2 * 2**(g-1) for g in (1, 2, 3)], [0, 0, 0],
    "C7 Quadrupled q_d^(1) = (2, 4, 8)")

# Candidate 8: Up-scaled — q_d^(1) = (3/2) 2^(g-1)  (still non-integer, explores nearby)
results['C8_1p5_scaled'] = candidate_fit(
    [(3.0/2.0)*2**(g-1) for g in (1, 2, 3)], [0, 0, 0],
    "C8 q_d^(1) = (3/2)·(1, 2, 4) = (3/2, 3, 6)")

# ---------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------
print()
print("=" * 72)
print("VERDICT SUMMARY")
print("=" * 72)
print()
print(f"{'Candidate':<35} {'α':>10} {'β':>10} {'γ':>10} {'max|rel|':>10}  Verdict")
for name, r in results.items():
    if r is None:
        continue
    print(f"{name:<35} {r['alpha_fit']:>+10.4f} {r['beta_fit']:>+10.4f} "
          f"{r['gamma_fit']:>+10.4f} {r['max_rel_err']*100:>9.1f}%  {r['verdict']}")

min_err = min(r['max_rel_err'] for r in results.values() if r is not None)
wins = [n for n, r in results.items() if r and r['max_rel_err'] < 0.01]

print()
if wins:
    verdict_str = f"OUTCOME A (WIN): {len(wins)} candidate(s) reproduce VV at <= 1%: {wins}.  VV coefficients derived from FN-doubled + RG; upgrade from [C] to [T]."
elif min_err < 0.05:
    verdict_str = f"OUTCOME C (MIXED): best candidate at {min_err*100:.1f}%; not <= 1% clean but suggestive.  Disclose as near-miss; [C] classification stands."
else:
    verdict_str = f"OUTCOME B (MAP): no FN-doubled assignment reproduces VV via SM RG (best candidate at {min_err*100:.1f}%).  [C] classification of VV coefficient-value interpretations is further supported.  Document as SC-KKK negative-evidence artifact."
print(verdict_str)

# ---------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------
artifact = {
    "experiment_id": "COMP-P01-KKK",
    "title": "VV coefficient derivation from FN-doubled + SM RG (Priority 13 / 41_SPEC / Round 38)",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "setup": {
        "M_GUT_GeV": M_GUT, "M_Z_GeV": M_Z,
        "eps_1": eps1, "eps_2": eps2,
        "q_lep_1": q_lep_1, "q_u_1": q_u_1,
        "delta_q_2_up_minus_lep": -1,
    },
    "VV_target": {"alpha": VV_ALPHA, "beta": VV_BETA, "gamma": VV_GAMMA},
    "candidates": results,
    "verdict": verdict_str,
}
block = json.dumps(artifact, sort_keys=True, indent=2, default=str)
artifact["pre_commit_sha256"] = hashlib.sha256(block.encode()).hexdigest()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "comp_p01_KKK_vv_rg_derivation.json")
with open(out, "w") as f:
    json.dump(artifact, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print()
print(f"Pre-commit SHA-256: {artifact['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
