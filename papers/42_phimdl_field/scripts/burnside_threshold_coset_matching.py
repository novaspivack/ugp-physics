#!/usr/bin/env python3
"""Burnside-boundary threshold constant: coset-sector one-loop matching at Lambda_GTE.

At Lambda_GTE the F21 abelian EFT (below) matches to full SU(3) YM (above) via
Burnside coset-filling. The modes that switch on are the six coset vectors
(3 + 3bar of F21), each eating one Phi_MDL coset-scalar fluctuation. The one-loop
MS-bar decoupling constant for heavy gauge bosons (Weinberg PLB 91 (1980) 51,
eq. 12; Hall NPB 178 (1981) 75 as quoted in arXiv:1502.01362 eqs. 2-3, 7):

    1/g_EFT^2(mu) = 1/g_full^2(mu) - (t_V/48pi^2) (1 - 21 ln(M_V/mu)),

so in the R09 dictionary c = 16pi^2 [1/e_V^2 - 1/g_MSbar^2] evaluated at
mu = Lambda_GTE:

    c_coset = (t_V/3) (21 ln(M_V/Lambda_GTE) - 1).

This script:
  1. verifies t_V = 3 and the coset charge spectrum {+-1/2, +-1/2, +-1} under
     H_A = (-T3 + sqrt3 T8)/2 from explicit Gell-Mann matrices (adjoint trace,
     Cartan neutrality, A-A' kinetic-mixing cancellation);
  2. evaluates c_coset on the pre-registered gap set and the structural window;
  3. runs the RG matching-scale consistency test (standard-EFT cancellation vs
     the GTE structural-beta non-cancellation, quantified);
  4. reduces the formula to the QCD quark threshold as a structural control.

Expected output: t_V = 3.000 exactly; c_coset(M_V = Lambda) = -1.0;
c_coset(M_V = sqrt(7/2) GeV) = -2.51; f = m_phi branch +9.56 (flagged).
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 300


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

results = {}

# ---------------------------------------------------------------- inputs
LAM_GTE = 2.01            # GeV (P39 eq. lambdagte)
LAM_BAND = {"minus": 1.57, "central": 2.01, "plus": 2.25}
E2_V = 3.5                # CatAL g_c^2 = 7/2 (Villain normalization)
M_PHI = 1.77686           # GeV (SCC m_phi = m_tau)
M_A_F1 = math.sqrt(7.0 / 2.0)          # e*sqrt(Z0)*f, f = 1 GeV, Z0 = 1
M_A_FMPHI = math.sqrt(7.0 / 2.0) * M_PHI

# ------------------------------------------------- 1. group theory block
lam3 = np.diag([1.0, -1.0, 0.0])
lam8 = np.diag([1.0, 1.0, -2.0]) / math.sqrt(3.0)
T3, T8 = lam3 / 2.0, lam8 / 2.0
H_A = (-T3 + math.sqrt(3.0) * T8) / 2.0
H_Ap = (math.sqrt(3.0) * T3 + T8) / 2.0

tr_f_HA2 = float(np.trace(H_A @ H_A).real)
tr_f_HAp2 = float(np.trace(H_Ap @ H_Ap).real)
tr_f_mix = float(np.trace(H_A @ H_Ap).real)

# coset generators = matrix units e_ij (i != j); ad(H) eigenvalue = H_ii - H_jj
coset_pairs = [(0, 1), (0, 2), (1, 2)]
charges_HA, charges_HAp = [], []
for (i, j) in coset_pairs:
    qA = float((H_A[i, i] - H_A[j, j]).real)
    qAp = float((H_Ap[i, i] - H_Ap[j, j]).real)
    charges_HA += [qA, -qA]
    charges_HAp += [qAp, -qAp]
t_V = sum(q * q for q in charges_HA)
t_V_Ap = sum(q * q for q in charges_HAp)
mix_sum = sum(a * b for a, b in zip(charges_HA, charges_HAp))

# adjoint-trace cross-check: tr_adj(H^2) = 3 * (2 tr_f H^2) for su(3)
tr_adj_HA2 = 3.0 * 2.0 * tr_f_HA2

print("=== 1. Group theory (explicit Gell-Mann matrices) ===")
print(f"  tr_f H_A^2  = {tr_f_HA2:.12f}  (canonical 1/2: "
      f"{'OK' if abs(tr_f_HA2 - 0.5) < 1e-12 else 'FAIL'})")
print(f"  tr_f H_A'^2 = {tr_f_HAp2:.12f}; tr_f(H_A H_A') = {tr_f_mix:.2e} "
      f"(Killing-orthogonal: {'OK' if abs(tr_f_mix) < 1e-12 else 'FAIL'})")
print(f"  coset charges under H_A: "
      f"{sorted(round(q, 6) for q in charges_HA)}")
print(f"  t_V = sum q^2 = {t_V:.12f}  (= tr_adj H_A^2 = {tr_adj_HA2:.1f}: "
      f"{'OK' if abs(t_V - 3.0) < 1e-12 else 'FAIL'})")
print(f"  t_V under H_A' = {t_V_Ap:.12f} (e' = e consistency: "
      f"{'OK' if abs(t_V_Ap - 3.0) < 1e-12 else 'FAIL'})")
print(f"  kinetic mixing sum q_A q_A' = {mix_sum:.2e} "
      f"({'OK no mixing' if abs(mix_sum) < 1e-12 else 'FAIL'})")
assert abs(t_V - 3.0) < 1e-12 and abs(mix_sum) < 1e-12

results["group_theory"] = {
    "tr_f_HA2": tr_f_HA2, "t_V": t_V, "t_V_Aprime": t_V_Ap,
    "coset_charges_HA": sorted(round(q, 6) for q in charges_HA),
    "mixing_sum": mix_sum}

# ----------------------------------- 2. matching constant on the gap set
def c_coset(m_v, lam=LAM_GTE, t_v=3.0):
    """Weinberg eq. (12) / Hall lambda_i^V, in the R09 dictionary."""
    return (t_v / 3.0) * (21.0 * math.log(m_v / lam) - 1.0)


print("\n=== 2. c_coset on the pre-registered gap set ===")
gap_set = {
    "BA-M1 boundary gap (M_V = Lambda_GTE)": LAM_GTE,
    "BA-M2 Lagrangian gap e*sqrt(Z0), f=1 GeV": M_A_F1,
    "f=m_phi branch (EFT-INCOHERENT, flagged)": M_A_FMPHI,
}
results["c_coset_gap_set"] = {}
for lbl, mv in gap_set.items():
    c = c_coset(mv)
    print(f"  {lbl}: M_V = {mv:.4f} GeV -> c_coset = {c:+.4f}")
    results["c_coset_gap_set"][lbl] = {"M_V_GeV": mv, "c_coset": c}

print("\n  structural window sweep (coherent readings M_V in "
      "[e*sqrt(Z0), Lambda]):")
window = []
for frac in np.linspace(0.0, 1.0, 11):
    mv = M_A_F1 + frac * (LAM_GTE - M_A_F1)
    window.append({"M_V": float(mv), "c_coset": c_coset(float(mv))})
print(f"    c_coset in [{window[0]['c_coset']:+.3f}, "
      f"{window[-1]['c_coset']:+.3f}]  -- always negative")
results["window_sweep"] = window

print("\n  Lambda_GTE band variation (M_V tied to each reading):")
band_var = {}
for lbl, lam in LAM_BAND.items():
    band_var[lbl] = {
        "M_V=Lambda": c_coset(lam, lam=lam),
        "M_V=e_f1": c_coset(M_A_F1, lam=lam)}
    print(f"    Lambda = {lam:.2f}: c(M_V=Lambda) = "
          f"{band_var[lbl]['M_V=Lambda']:+.3f}, c(M_V=1.871) = "
          f"{band_var[lbl]['M_V=e_f1']:+.3f}")
results["lambda_band_variation"] = band_var

# --------------------- 3. matching-scale consistency (structural beta)
print("\n=== 3. Matching-scale dependence test ===")
# Standard-EFT case: EFT beta = full beta minus heavy contribution; the
# mu_m-dependence of the matching constant cancels against the running
# difference. GTE case: EFT b0 = 7 is structural (b0_eq_z7_order), naive
# light-loop sum would be ~ -4 (kink screening; Cartans/phi neutral, chi
# eaten); the non-cancellation per ln mu_m is 2*(b0_GTE - b0_naive).
B0_ABOVE = 7.0
B0_GTE = 7.0
B0_NAIVE_EFT = -4.0
drift_structural = 2.0 * (B0_GTE - B0_NAIVE_EFT)
drift_certified = 2.0 * (B0_GTE - B0_ABOVE)
for fac in (0.8, 1.0, 1.2):
    print(f"  mu_m = {fac:.1f} x Lambda: certified-running drift of c = "
          f"{drift_certified * math.log(fac):+.3f}; naive-light-loop drift = "
          f"{drift_structural * math.log(fac):+.3f}")
print("  -> with the certified b0 = 7 on both sides the matching constant is")
print("     scale-stable (drift 0); the would-be ambiguity (22 ln-units) is")
print("     resolved by the theory-supplied MDL matching condition mu_m =")
print("     Lambda_GTE exactly (136-VCOUP completeness; same as R07).")
results["matching_scale_test"] = {
    "drift_per_ln_mu_certified": drift_certified,
    "drift_per_ln_mu_naive_lightloop": drift_structural}

# ------------------------------ 4. QCD quark-threshold structural control
print("\n=== 4. Structural control: QCD quark threshold reduction ===")
# Weinberg eq. (12) traces: t_F = T(R) per Dirac flavor (1/2, fundamental);
# fermion log coefficient in Delta(1/g^2)*16pi^2 per ln: (8 t_F)*(2/96pi^2)
# *16pi^2 = (8/3) t_F = 4/3 per Dirac flavor = 2*Delta(b0) across one quark
# threshold (known QCD decoupling). Vector check: 21 t_V -> 7 t_V per ln =
# 2*(21/6) t_V; SU(2) W pair t_V = 2 gives the famous 14 = 2*7.
t_F_dirac = 0.5
log_coeff_per_flavor = 8.0 * t_F_dirac * 2.0 / 96.0 / math.pi**2 * 16 * math.pi**2
known_b_step = 2.0 * (2.0 / 3.0)  # 2*Delta(b0) across one Dirac flavor
vec_log_coeff = 21.0 * 2.0 / 96.0 / math.pi**2 * 16 * math.pi**2  # per t_V
print(f"  Weinberg fermion log coefficient (16pi^2 units, per Dirac flavor): "
      f"{log_coeff_per_flavor:.6f}")
print(f"  known threshold step 2*Delta(b0) = {known_b_step:.6f}  "
      f"({'OK' if abs(log_coeff_per_flavor - known_b_step) < 1e-12 else 'FAIL'})")
print(f"  Weinberg vector log coefficient per unit t_V: {vec_log_coeff:.6f} "
      f"(= 2*(21/6) = 7: {'OK' if abs(vec_log_coeff - 7.0) < 1e-12 else 'FAIL'}; "
      f"SU(2) W-pair t_V = 2 -> {2*vec_log_coeff:.0f} = famous 14)")
assert abs(log_coeff_per_flavor - known_b_step) < 1e-12
assert abs(vec_log_coeff - 7.0) < 1e-12
results["qcd_reduction_check"] = {
    "weinberg_fermion_log_coeff": log_coeff_per_flavor,
    "known_2_delta_b0": known_b_step,
    "vector_log_coeff_per_tV": vec_log_coeff}

# ------------------------------------------------- 5. honest sign summary
print("\n=== 5. Sign summary ===")
print("  Required corridor (R09 pre-registered): c in [+1.84, +6.08]")
print(f"  Derived coset constant, coherent readings: c in "
      f"[{c_coset(M_A_F1):+.3f}, {c_coset(LAM_GTE):+.3f}]  -- WRONG SIGN")
print("  Rejected numerology (Round 1 register): ln|F21| = "
      f"{math.log(21.0):.4f} (in corridor; no mechanism; REJECTED)")
results["verdict_inputs"] = {
    "corridor": [1.84, 6.08],
    "c_coset_coherent_range": [c_coset(M_A_F1), c_coset(LAM_GTE)],
    "ln_21_rejected": math.log(21.0)}

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "burnside_threshold_coset_matching_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
