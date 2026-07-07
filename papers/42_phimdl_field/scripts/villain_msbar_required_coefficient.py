#!/usr/bin/env python3
"""Required Villain->MS-bar conversion coefficient c_req with full uncertainty budget.

The CatAL color coupling is e^2 = 7/2 at Lambda_GTE = 2.01 (+0.24/-0.44) GeV in the
"Villain (heat-kernel)" convention (SylowIndexCouplingHierarchy.lean). PDG 2024
alpha_s(M_Z) = 0.1180 +/- 0.0009 run down to mu gives e^2_MSbar(mu). The one-loop
conversion g^2_MSbar = g^2_V (1 + c g_V^2 / 16 pi^2) absorbs the offset iff

    c_req = (e^2_MSbar / e^2_V - 1) * 16 pi^2 / e^2_V .

This script computes c_req across: loop order (2/3), PDG +/- 1 sigma, n_f threshold
variant (m_b vs 2 m_b matching point), and the Lambda_GTE band {1.57, 2.01, 2.25} GeV.
It also computes the exact-match scale mu* (where 4 pi alpha_s = 7/2), its z-score in
Lambda_GTE scale units, the reverse-parametrized requirement
v_req = (e^2_V/e^2_MS - 1) * 16 pi^2 / e^2_MS (finite part the Villain scheme must
have relative to MS-bar), and same-scheme sigma equivalents.

Expected output: c_req(central) ~ 3.3; mu* ~ 2.36 GeV (z ~ +1.4 sigma_scale);
same-scheme offset ~ 10-15 sigma_PDG at central Lambda_GTE.
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

ALPHA_S_MZ = 0.1180          # PDG 2024 (CANONICAL_COMPARISON_DATA.md)
ALPHA_S_MZ_ERR = 0.0009
M_Z = 91.1876
M_B = 4.18
E2_V = 3.5                   # CatAL g_c^2 = 7/2
LAM_GTE = 2.01               # GeV (P39)
LAM_BAND = {"minus": 2.01 - 0.44, "central": 2.01, "plus": 2.01 + 0.24}

def beta_coeffs(nf):
    b0 = 11.0 - 2.0 * nf / 3.0
    b1 = 102.0 - 38.0 * nf / 3.0
    b2 = 2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf ** 2
    return b0, b1, b2

def run_alpha(a0, mu0, mu1, nf, loops, nstep=4000):
    b0, b1, b2 = beta_coeffs(nf)
    def rhs(a):
        d = -(b0 / (2 * math.pi)) * a * a - (b1 / (8 * math.pi ** 2)) * a ** 3
        if loops >= 3:
            d += -(b2 / (32 * math.pi ** 3)) * a ** 4
        return d
    t0, t1 = math.log(mu0), math.log(mu1)
    h = (t1 - t0) / nstep
    a = a0
    for _ in range(nstep):
        k1 = rhs(a); k2 = rhs(a + 0.5 * h * k1)
        k3 = rhs(a + 0.5 * h * k2); k4 = rhs(a + h * k3)
        a += h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return a

def alpha_s_at(mu, a_mz, loops, thr=M_B):
    if mu >= thr:
        return run_alpha(a_mz, M_Z, mu, 5, loops)
    a_thr = run_alpha(a_mz, M_Z, thr, 5, loops)
    return run_alpha(a_thr, thr, mu, 4, loops)

# convergence check on RK step count
a_4000 = alpha_s_at(LAM_GTE, ALPHA_S_MZ, 3)
a_8000 = run_alpha(ALPHA_S_MZ, M_Z, M_B, 5, 3, 8000)
a_8000 = run_alpha(a_8000, M_B, LAM_GTE, 4, 3, 8000)
conv_rel = abs(a_8000 - a_4000) / a_4000
print(f"RK4 convergence: nstep 4000 vs 8000 rel diff = {conv_rel:.2e}  "
      f"({'OK' if conv_rel < 1e-8 else 'CHECK'})")

results = {"inputs": {"alpha_s_MZ": ALPHA_S_MZ, "err": ALPHA_S_MZ_ERR,
                      "e2_villain": E2_V, "Lambda_GTE_band_GeV": LAM_BAND},
           "rk4_convergence_rel": conv_rel}

def c_req_of(e2_ms):
    return (e2_ms / E2_V - 1.0) * 16 * math.pi ** 2 / E2_V

def v_req_of(e2_ms):
    return (E2_V / e2_ms - 1.0) * 16 * math.pi ** 2 / e2_ms

print("\n=== 1. c_req across the systematic battery ===")
battery = {}
for loops in (2, 3):
    for pdg_lbl, a_mz in [("-1s", ALPHA_S_MZ - ALPHA_S_MZ_ERR),
                          ("c", ALPHA_S_MZ), ("+1s", ALPHA_S_MZ + ALPHA_S_MZ_ERR)]:
        for thr_lbl, thr in [("mb", M_B), ("2mb", 2 * M_B)]:
            for lam_lbl, lam in LAM_BAND.items():
                a = alpha_s_at(lam, a_mz, loops, thr)
                e2 = 4 * math.pi * a
                battery[f"{loops}loop_{pdg_lbl}_{thr_lbl}_{lam_lbl}"] = {
                    "e2_MS": e2, "c_req": c_req_of(e2), "v_req": v_req_of(e2)}
central = battery["3loop_c_mb_central"]
print(f"  central (3-loop, PDG c, thr m_b, Lambda 2.01): e2_MS = {central['e2_MS']:.4f}, "
      f"c_req = {central['c_req']:.3f}, v_req = {central['v_req']:.3f}")
c_vals_fixed_lam = [v["c_req"] for k, v in battery.items() if k.endswith("_central")]
print(f"  c_req at central Lambda over loops x PDG x thr: "
      f"[{min(c_vals_fixed_lam):.3f}, {max(c_vals_fixed_lam):.3f}]")
c_vals_all = [v["c_req"] for v in battery.values()]
print(f"  c_req over FULL battery incl. Lambda band:      "
      f"[{min(c_vals_all):.3f}, {max(c_vals_all):.3f}]")
results["battery"] = battery
results["c_req_central"] = central["c_req"]
results["c_req_band_fixed_lambda"] = [min(c_vals_fixed_lam), max(c_vals_fixed_lam)]
results["c_req_band_full"] = [min(c_vals_all), max(c_vals_all)]

print("\n=== 2. Exact-match scale mu* and scale-unit z-score ===")
lo, hi = 1.0, 20.0
for _ in range(80):
    mid = math.sqrt(lo * hi)
    if 4 * math.pi * alpha_s_at(mid, ALPHA_S_MZ, 3) > E2_V:
        lo = mid
    else:
        hi = mid
mu_star = math.sqrt(lo * hi)
z_scale = (mu_star - LAM_GTE) / 0.24      # upper error bar (mu* > central)
print(f"  mu* = {mu_star:.3f} GeV; Lambda_GTE = 2.01 +0.24/-0.44 GeV; "
      f"z_scale = +{z_scale:.2f} (within the +1 sigma...+2 sigma scale band)")
results["mu_star_GeV"] = mu_star
results["z_scale_upper_err"] = z_scale

print("\n=== 3. Same-scheme sigma equivalents ===")
a_c = alpha_s_at(LAM_GTE, ALPHA_S_MZ, 3)
a_lo = alpha_s_at(LAM_GTE, ALPHA_S_MZ - ALPHA_S_MZ_ERR, 3)
a_hi = alpha_s_at(LAM_GTE, ALPHA_S_MZ + ALPHA_S_MZ_ERR, 3)
e2_c, e2_lo, e2_hi = (4 * math.pi * x for x in (a_c, a_lo, a_hi))
sig_pdg = (e2_hi - e2_lo) / 2.0
offset = e2_c - E2_V
print(f"  e2_MS(2.01) = {e2_c:.4f} +/- {sig_pdg:.4f} (PDG-only)")
print(f"  same-scheme offset = {offset:.4f} -> {offset/sig_pdg:.1f} sigma_PDG "
      f"(at FIXED central Lambda_GTE)")
# scale-dominated sigma: e2 at Lambda band edges
e2_at = {lbl: 4 * math.pi * alpha_s_at(lam, ALPHA_S_MZ, 3)
         for lbl, lam in LAM_BAND.items()}
sig_scale_up = abs(e2_at["plus"] - e2_at["central"])
sig_scale_dn = abs(e2_at["minus"] - e2_at["central"])
print(f"  e2_MS at Lambda band: minus(1.57)={e2_at['minus']:.4f}, "
      f"central={e2_at['central']:.4f}, plus(2.25)={e2_at['plus']:.4f}")
print(f"  scale-induced sigma on e2: +{sig_scale_dn:.4f}/-{sig_scale_up:.4f} "
      f"-> offset = {offset/sig_scale_up:.2f} sigma_scale(up)")
results["sigma_equivalents"] = {
    "e2_MS_central": e2_c, "sigma_PDG": sig_pdg,
    "offset": offset, "offset_over_sigma_PDG": offset / sig_pdg,
    "e2_MS_at_band": e2_at,
    "offset_over_sigma_scale_up": offset / sig_scale_up}

with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "villain_msbar_required_coefficient_results.json", "w") as fp:
    json.dump(results, fp, indent=1)
print("\nSaved villain_msbar_required_coefficient_results.json")
signal.alarm(0)
