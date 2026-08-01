#!/usr/bin/env python3
"""Spectral-class reformulation of the kink VP dissolution constant (088-R11a).

Recasts every substrate UV definition as a charged-channel spectral
suppression g(s) in

  16pi^2 Pi_def(0) = int_{4M^2}^inf (ds/s) K(s) g(s),
  K(s) = (4/3)(1 + 2M^2/s) sqrt(1 - 4M^2/s),

so that  c(g) = 8 ln(Lambda/M) - 3 int (ds/s) K g = 8 ln(Lambda/Lambda_diss(g))
with Lambda_diss(g) = M exp[(3/8) int (ds/s) K g].  The sharp-vs-smooth
gamma_E residual is then exposed as a pure log-centroid statement:
Lambda_diss(sharp@m_phi) = e^{-gamma/2} m_phi vs Lambda_diss(PV@m_phi) = m_phi.

Also computes the Krein/heat-kernel candidate: the exact s=1 Poschl-Teller
relative trace  DeltaTr(t) = erf(m_phi sqrt(t))  taken as a proper-time
dissolution weight gives the closed form
  c_erf = 8 ln[Lambda/(m_phi + sqrt(m_phi^2 + M^2))].

Verification battery: PV reproduction from the spectral kernel; MSbar
threshold constant C_inf stability; R11 family values reproduced and
converted to Lambda_diss; erf closed form vs direct quadrature.

Expected: battery green; c_erf ~ -4.5 (tree) / -3.7 (pole);
Lambda_diss(S5) = e^{-gamma/2} m_phi confirmed.
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 300


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

EULER_GAMMA = 0.5772156649015329

M_TAU = 1776.86
M_CL = 8.0 / 49.0 * M_TAU
M_Q = 321.32
M_PHI = M_TAU
LAM_TREE = 8.0 / 7.0 * M_TAU
LAM_POLE = 7.0 * M_Q
READINGS = {"tree": {"lam": LAM_TREE, "M": M_CL},
            "pole": {"lam": LAM_POLE, "M": M_Q}}

results = {"preregistered_predictions": {
    "P1": "c_tape > -1.00 (compositeness removes UV support vs point lattice)",
    "P2": "c_unique < c_S1 per reading (pair-channel onset 2M+m_phi > m_phi)",
    "P3": "no substrate profile reaches the tree-rescue region c >= +3.1",
}}


def kernel(s, M):
    if s <= 4.0 * M * M:
        return 0.0
    beta = math.sqrt(1.0 - 4.0 * M * M / s)
    return (4.0 / 3.0) * (1.0 + 2.0 * M * M / s) * beta


def spectral_integral(g, M, theta_max=40.0, n=200000):
    """int (ds/s) K(s) g(s) via s = 4M^2 cosh^2(theta/2), ds/s = tanh dtheta."""
    h = theta_max / n
    tot = 0.0
    for i in range(n):
        th = (i + 0.5) * h
        t2 = math.tanh(th / 2.0)
        s = 4.0 * M * M * math.cosh(th / 2.0) ** 2
        tot += t2 * kernel(s, M) * g(s)
    return tot * h


battery = {}

# --- (i) PV reproduction: int ds/s [K(s;M) - K(s;Lpv)] = (8/3) ln(Lpv/M)
for (M, lpv) in ((M_CL, M_PHI), (M_Q, M_PHI)):
    # integrate the difference on a common s grid (log grid, wide range)
    smin, smax, n = 4.0 * M * M * 1e-6, (200.0 * lpv) ** 2, 400000
    lmin, lmax = math.log(4.0 * M * M), math.log(smax)
    h = (lmax - lmin) / n
    tot = 0.0
    for i in range(n):
        s = math.exp(lmin + (i + 0.5) * h)
        tot += (kernel(s, M) - kernel(s, lpv)) * h
    pred = (8.0 / 3.0) * math.log(lpv / M)
    err = abs(tot - pred) / abs(pred)
    battery[f"PV_reproduction_M{M:.0f}"] = err
    assert err < 2e-3, f"PV spectral reproduction failed: {tot} vs {pred}"
print(f"battery: PV reproduced from spectral kernel "
      f"(max rel err {max(v for k, v in battery.items()):.1e})")

# --- (ii) MSbar threshold constant C_inf: int_{4M^2}^{S} ds/s K = (4/3)ln(S/M^2) + C_inf
def c_inf(M, S):
    lmin, lmax, n = math.log(4.0 * M * M), math.log(S), 400000
    h = (lmax - lmin) / n
    tot = 0.0
    for i in range(n):
        s = math.exp(lmin + (i + 0.5) * h)
        tot += kernel(s, M) * h
    return tot - (4.0 / 3.0) * math.log(S / (M * M))


cvals = [c_inf(1.0, S) for S in (1e8, 1e10, 1e12)]
battery["C_inf_stability"] = max(cvals) - min(cvals)
C_INF = cvals[-1]
assert battery["C_inf_stability"] < 1e-3
print(f"battery: C_inf = {C_INF:.6f} (stable to {battery['C_inf_stability']:.1e})")
results["C_inf"] = C_INF

# --- (iii) R11 family -> Lambda_diss conversion (closed forms, then check)
def expint_e1(x):
    if x <= 1.0:
        s_, term, k = 0.0, 1.0, 0
        while True:
            k += 1
            term *= -x / k
            add = term / k
            s_ += add
            if abs(add) < 1e-18 * max(1.0, abs(s_)):
                break
        return -EULER_GAMMA - math.log(x) - s_
    b = x + 1.0
    c = 1e300
    d = 1.0 / b
    hh = d
    for i in range(1, 200):
        a = -i * i
        b += 2.0
        d = 1.0 / (a * d + b)
        c = b + a / c
        delta = c * d
        hh *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return hh * math.exp(-x)


R_RMS = math.pi / (2.0 * math.sqrt(3.0))   # x m_phi
results["family_lambda_diss"] = {}
print("\n=== R11 family re-expressed as Lambda_diss (pure log-centroid) ===")
for rname, r in READINGS.items():
    lam, M = r["lam"], r["M"]
    fam = {
        "S1_PV_mphi": 3.0 * (8.0 / 3.0) * math.log(lam / M_PHI),
        "S2_PV_invrms": 3.0 * (8.0 / 3.0) * math.log(lam * R_RMS / M_PHI),
        "S3_smooth_mphi": 3.0 * ((8.0 / 3.0) * math.log(lam / M)
                                 - (4.0 / 3.0) * math.log(1.0 + (M_PHI / M) ** 2)),
        "S4_smooth_rms": 3.0 * ((8.0 / 3.0) * math.log(lam / M)
                                - (4.0 / 3.0) * math.log(1.0 + (M_PHI / (R_RMS * M)) ** 2)),
        "S5_sharp_mphi": 3.0 * ((8.0 / 3.0) * math.log(lam / M)
                                - (4.0 / 3.0) * expint_e1((M / M_PHI) ** 2)),
        "S6_sharp_rms": 3.0 * ((8.0 / 3.0) * math.log(lam / M)
                               - (4.0 / 3.0) * expint_e1((R_RMS * M / M_PHI) ** 2)),
    }
    results["family_lambda_diss"][rname] = {}
    for sname, c in fam.items():
        ldiss = lam * math.exp(-c / 8.0)
        results["family_lambda_diss"][rname][sname] = {
            "c": c, "lambda_diss_MeV": ldiss, "lambda_diss_over_mphi": ldiss / M_PHI}
        print(f"  {rname} {sname:16s}: c = {c:+.4f}  ->  "
              f"Lambda_diss = {ldiss:7.1f} MeV = {ldiss/M_PHI:.4f} m_phi")

# sharp asymptotic check: Lambda_diss(S5) -> e^{-gamma/2} m_phi as M -> 0
ld_s5 = results["family_lambda_diss"]["tree"]["S5_sharp_mphi"]["lambda_diss_over_mphi"]
pred = math.exp(-EULER_GAMMA / 2.0)
battery["S5_lambda_diss_vs_egamma"] = abs(ld_s5 - pred)
print(f"\nLambda_diss(S5,tree)/m_phi = {ld_s5:.4f} vs e^(-gamma/2) = {pred:.4f} "
      f"(diff {ld_s5-pred:+.4f} = finite-M correction)")
# residual identity: c_S5 - c_S1 -> 4 gamma_E as M -> 0
res_tree = (results["family_lambda_diss"]["tree"]["S5_sharp_mphi"]["c"]
            - results["family_lambda_diss"]["tree"]["S1_PV_mphi"]["c"])
print(f"sharp-vs-smooth residual (tree) = {res_tree:+.4f} "
      f"(asymptotic 4 gamma_E = {4*EULER_GAMMA:.4f})")
results["residual_tree"] = res_tree
results["residual_asymptotic_4gamma"] = 4 * EULER_GAMMA

# --- (iv) Krein/heat-kernel candidate: closed form + quadrature check
print("\n=== Krein spectral-shift candidate: f(t) = erf(m_phi sqrt(t)) ===")
results["krein_erf"] = {}
for rname, r in READINGS.items():
    lam, M = r["lam"], r["M"]
    ldiss = M_PHI + math.sqrt(M_PHI ** 2 + M ** 2)
    c_closed = 8.0 * math.log(lam / ldiss)
    # direct quadrature of (4/3) int dt/t e^{-M^2 t} erf(m sqrt t), log grid
    lmin, lmax, n = math.log(1e-12 / (M_PHI ** 2)), math.log(60.0 / (M * M)), 300000
    h = (lmax - lmin) / n
    tot = 0.0
    for i in range(n):
        t = math.exp(lmin + (i + 0.5) * h)
        tot += math.exp(-M * M * t) * math.erf(M_PHI * math.sqrt(t)) * h
    c_quad = 8.0 * math.log(lam / M) - 3.0 * (4.0 / 3.0) * tot
    err = abs(c_quad - c_closed)
    battery[f"erf_closedform_{rname}"] = err
    assert err < 5e-3, f"erf closed form check failed: {c_quad} vs {c_closed}"
    results["krein_erf"][rname] = {"c": c_closed,
                                   "lambda_diss_MeV": ldiss,
                                   "lambda_diss_over_mphi": ldiss / M_PHI}
    print(f"  {rname}: c_erf = {c_closed:+.4f} (quadrature {c_quad:+.4f}); "
          f"Lambda_diss = {ldiss:.1f} MeV = {ldiss/M_PHI:.4f} m_phi")

# spectral landmarks per reading (for P2/P3 adjudication)
print("\n=== substrate spectral landmarks ===")
results["landmarks"] = {}
for rname, r in READINGS.items():
    M, lam = r["M"], r["lam"]
    lm = {"pair_threshold_2M": 2 * M, "inelastic_onset_2M_plus_mphi": 2 * M + M_PHI,
          "Lambda": lam, "tree_rescue_needs_lambda_diss_below":
              lam * math.exp(-3.1 / 8.0)}
    results["landmarks"][rname] = lm
    print(f"  {rname}: 2M = {2*M:.1f}; 2M+m_phi = {2*M+M_PHI:.1f}; "
          f"Lambda = {lam:.1f}; rescue needs Lambda_diss <= {lm['tree_rescue_needs_lambda_diss_below']:.1f} MeV")

results["battery"] = battery
out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "dissolution_constant_spectral_class_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
