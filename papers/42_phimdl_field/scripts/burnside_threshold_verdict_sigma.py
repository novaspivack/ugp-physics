#!/usr/bin/env python3
"""Burnside threshold constant: sigma-accounting and the final coupling verdict.

Combines the CatAL Villain coupling e^2 = 7/2 at Lambda_GTE with the derived
coset-sector threshold constant c_coset = (t_V/3)(21 ln(M_V/Lambda) - 1)
(burnside_threshold_coset_matching.py) and compares against the PDG 2024
alpha_s(M_Z) = 0.1180 +/- 0.0009 run down 3-loop (n_f 5->4 at m_b), with the
Lambda_GTE = 2.01 +0.24/-0.44 GeV scale band. Reports:

  1. c_req reproduction (R09 corridor check);
  2. predicted e^2_MSbar for each gap reading, residuals in sigma_PDG,
     sigma_scale, sigma_combined;
  3. the shifted exact-match scale mu* including c_coset, with z_scale;
  4. the sharpened corridor for the remaining nonperturbative kink
     vacuum-polarization constant c_kink = c_req - c_coset;
  5. the k* = 0 named-condition check (matching-constant size vs the
     30x-generic bound from 088-R07).

Expected output: c_req ~ 3.33; residuals 1.65-2.2 sigma_combined for the
coherent readings; c_kink corridor ~ [+4.3, +5.8].
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

ALPHA_S_MZ, ALPHA_S_MZ_ERR = 0.1180, 0.0009   # PDG 2024
M_Z, M_B = 91.1876, 4.18
E2_V = 3.5
LAM_GTE = 2.01
LAM_BAND = {"minus": 1.57, "central": 2.01, "plus": 2.25}
SIXTEEN_PI2 = 16 * math.pi ** 2


def beta_coeffs(nf):
    b0 = 11.0 - 2.0 * nf / 3.0
    b1 = 102.0 - 38.0 * nf / 3.0
    b2 = 2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf ** 2
    return b0, b1, b2


def run_alpha(a0, mu0, mu1, nf, loops=3, nstep=4000):
    b0, b1, b2 = beta_coeffs(nf)

    def rhs(a):
        d = -(b0 / (2 * math.pi)) * a * a - (b1 / (8 * math.pi ** 2)) * a ** 3
        if loops >= 3:
            d += -(b2 / (32 * math.pi ** 3)) * a ** 4
        return d

    h = (math.log(mu1) - math.log(mu0)) / nstep
    a = a0
    for _ in range(nstep):
        k1 = rhs(a); k2 = rhs(a + 0.5 * h * k1)
        k3 = rhs(a + 0.5 * h * k2); k4 = rhs(a + h * k3)
        a += h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return a


def alpha_s_at(mu, a_mz=ALPHA_S_MZ, loops=3):
    if mu >= M_B:
        return run_alpha(a_mz, M_Z, mu, 5, loops)
    a_thr = run_alpha(a_mz, M_Z, M_B, 5, loops)
    return run_alpha(a_thr, M_B, mu, 4, loops)


# RK4 convergence
a4k = alpha_s_at(LAM_GTE)
a8k = run_alpha(run_alpha(ALPHA_S_MZ, M_Z, M_B, 5, 3, 8000), M_B, LAM_GTE, 4, 3, 8000)
conv = abs(a8k - a4k) / a4k
print(f"RK4 convergence 4000 vs 8000 steps: {conv:.2e} "
      f"({'OK' if conv < 1e-8 else 'CHECK'})")

results = {"rk4_convergence": conv}

# ------------------------------------------------ 1. c_req reproduction
e2_c = 4 * math.pi * alpha_s_at(LAM_GTE)
e2_lo = 4 * math.pi * alpha_s_at(LAM_GTE, ALPHA_S_MZ - ALPHA_S_MZ_ERR)
e2_hi = 4 * math.pi * alpha_s_at(LAM_GTE, ALPHA_S_MZ + ALPHA_S_MZ_ERR)
sig_pdg = (e2_hi - e2_lo) / 2.0
e2_band = {k: 4 * math.pi * alpha_s_at(v) for k, v in LAM_BAND.items()}
sig_scale_up = abs(e2_band["plus"] - e2_band["central"])
sig_comb = math.hypot(sig_pdg, sig_scale_up)
c_req = (e2_c / E2_V - 1.0) * SIXTEEN_PI2 / E2_V
print(f"\n=== 1. Requirement (R09 reproduction) ===")
print(f"  e2_MSbar(2.01) = {e2_c:.4f} +/- {sig_pdg:.4f} (PDG) "
      f"+/- {sig_scale_up:.4f} (scale-up); combined {sig_comb:.4f}")
print(f"  c_req = {c_req:.3f}  (R09: 3.330)")
results["requirement"] = {"e2_MS": e2_c, "sigma_PDG": sig_pdg,
                          "sigma_scale_up": sig_scale_up,
                          "sigma_combined": sig_comb, "c_req": c_req}

# --------------------------------- 2. predicted e^2 and residual sigmas
def c_coset(m_v, lam=LAM_GTE, t_v=3.0):
    return (t_v / 3.0) * (21.0 * math.log(m_v / lam) - 1.0)


readings = {
    "c=0 (R09 baseline, no threshold constant)": 0.0,
    "BA-M1: M_V = Lambda_GTE": c_coset(LAM_GTE),
    "BA-M2: M_V = e*sqrt(Z0) = 1.8708 GeV": c_coset(math.sqrt(3.5)),
    "flagged f=m_phi branch (EFT-incoherent)": c_coset(math.sqrt(3.5) * 1.77686),
}
print("\n=== 2. Predicted e2 and residuals ===")
results["readings"] = {}
for lbl, c in readings.items():
    e2_pred = E2_V * (1.0 + c * E2_V / SIXTEEN_PI2)
    resid = e2_c - e2_pred
    row = {"c_coset": c, "e2_pred": e2_pred, "residual": resid,
           "sigma_PDG_fixed_lambda": resid / sig_pdg,
           "sigma_combined": resid / sig_comb}
    results["readings"][lbl] = row
    print(f"  {lbl}:")
    print(f"    c = {c:+.3f} -> e2_pred = {e2_pred:.4f}; residual = "
          f"{resid:+.4f} = {resid/sig_pdg:+.2f} sigma_PDG / "
          f"{resid/sig_comb:+.2f} sigma_combined")

# ------------------------------------------- 3. shifted mu* with c_coset
print("\n=== 3. Exact-match scale mu* including c_coset ===")
results["mu_star"] = {}
for lbl, c in readings.items():
    target = E2_V * (1.0 + c * E2_V / SIXTEEN_PI2)
    lo, hi = 1.0, 30.0
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if 4 * math.pi * alpha_s_at(mid) > target:
            lo = mid
        else:
            hi = mid
    mu_star = math.sqrt(lo * hi)
    z = (mu_star - LAM_GTE) / (0.24 if mu_star > LAM_GTE else 0.44)
    results["mu_star"][lbl] = {"mu_star_GeV": mu_star, "z_scale": z}
    print(f"  {lbl}: mu* = {mu_star:.3f} GeV (z_scale = {z:+.2f})")

# --------------------------- 4. sharpened corridor for the kink constant
print("\n=== 4. Sharpened corridor for c_kink = c_req - c_coset ===")
corridor_lo, corridor_hi = 1.84, 6.08   # R09 pre-registered band on c_req
results["c_kink_corridor"] = {}
for lbl, c in readings.items():
    if "f=m_phi" in lbl:
        continue
    ck_central = c_req - c
    ck_band = [corridor_lo - c, corridor_hi - c]
    results["c_kink_corridor"][lbl] = {"central": ck_central, "band": ck_band}
    print(f"  {lbl}: c_kink central = {ck_central:+.3f}, band "
          f"[{ck_band[0]:+.2f}, {ck_band[1]:+.2f}]")

# ------------------------------------ 5. k* = 0 named-condition check
print("\n=== 5. k* = 0 named-condition check (088-R07) ===")
generic = E2_V / SIXTEEN_PI2          # generic two-loop size ~ e^2/16pi^2
for lbl, c in readings.items():
    if c == 0.0:
        continue
    ratio = abs(c) * E2_V / SIXTEEN_PI2 / generic
    print(f"  {lbl}: |matching| = {abs(c)*E2_V/SIXTEEN_PI2:.4f} "
          f"= {ratio:.1f} x generic (bound: < ~30x  "
          f"{'OK' if ratio < 30 else 'VIOLATED'})")
results["k_star_condition"] = {
    "generic_size": generic,
    "max_ratio_coherent": max(abs(c) for lbl, c in readings.items()
                              if "f=m_phi" not in lbl)}

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "burnside_threshold_verdict_sigma_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
