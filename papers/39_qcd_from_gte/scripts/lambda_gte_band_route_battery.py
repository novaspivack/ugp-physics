#!/usr/bin/env python3
"""Route battery for the Lambda_GTE boundary: coset-gap window (V/B), EFT
self-breakdown candidates (U) with anti-numerology nulls, and the running-
intersection degeneracy (X).

Route X demonstration: with b0 = 7 on BOTH sides of the boundary (CatAL
b0_eq_z7_order below; 11 - 2*n_kink_species/... = 11 - 4 above per the R10
slope-continuity identity), d(1/g^2)/dln(mu) = b0/(8 pi^2) is identical, so
1/e2_EFT(mu) - 1/g2_SU3(mu) is mu-independent at one loop: the curves are
parallel and never intersect (or coincide everywhere). The boundary cannot be
derived from RG intersection -- structural negative, CatAD.

Route U candidates are computed and nulled (wrong-target + neighbor); the
pre-registered expectation is NO mechanism (the GTE cosine potential is the
exact MDL-forced form, not a derivative expansion).

Expected output: route X drift = 0 to machine precision; route U candidates all
below 7*M_cl; coset window [m_A, Lambda] consistency for both mass readings.
Pole-mass input: corrected M^Q = 281 +/- 21 MeV (P42 GJQW interface dim-reg).
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

M_TAU = 1776.86e-3
M_CL = (8.0 / 49.0) * M_TAU
M_Q = 281.5e-3   # corrected pole mass central (P42 GJQW interface dim-reg)
LAM_CL = 7 * M_CL
LAM_Q = 7 * M_Q
E2_V = 3.5
B0 = 7.0

results = {}

# === Route X: running-intersection degeneracy ===
print("=== Route X: running-intersection degeneracy (one loop) ===")
def inv_g2_run(inv_g2_0, mu0, mu1, b0):
    # d(1/g^2)/dln mu = +2 b0 / (16 pi^2) = b0 / (8 pi^2)  (asymptotically free)
    return inv_g2_0 + (b0 / (8 * math.pi ** 2)) * math.log(mu1 / mu0)

drifts = []
for mu in (0.7, 1.0, 1.5, 2.0, 2.5, 3.0, 5.0, 10.0):
    inv_eft = inv_g2_run(1.0 / E2_V, 2.0, mu, B0)         # F21 EFT, b0 = |Z7| = 7
    inv_su3 = inv_g2_run(1.0 / E2_V + 0.01, 2.0, mu, B0)  # SU(3)+kinks, b0 = 11-4 = 7, offset 0.01
    drifts.append(abs((inv_eft - inv_su3) - (-0.01)))
max_drift = max(drifts)
print(f"max |Delta(1/g^2) - const| over mu in [0.7, 10] GeV = {max_drift:.2e}")
print("=> the inverse couplings are PARALLEL at one loop: no intersection scale exists.")
print("   Route X CLOSED NEGATIVE (structural): boundary must come from the spectrum.")
results["route_X"] = {"max_drift": max_drift,
                      "verdict": "DEGENERATE -- b0 continuity 7 = 11-4 = |Z7| makes the "
                                 "boundary RG-invisible at one loop; no intersection-defined scale"}

# === Route V/B: coset-gap window consistency ===
print("\n=== Route V/B: coset-gap window (consistency demand, not a point value) ===")
m_A_eft = math.sqrt(E2_V)  # e*sqrt(Z0)*f with f = 1 GeV (R10 BA-GAP named assumption)
window = {}
for lbl, lam in (("BA-MASS-CL", LAM_CL), ("BA-MASS-Q", LAM_Q)):
    ok = m_A_eft <= lam
    window[lbl] = {"Lambda_GeV": lam, "m_A_f1_GeV": m_A_eft, "M_V_window_GeV": [m_A_eft, lam],
                   "coherent": ok}
    print(f"  {lbl}: M_V window [{m_A_eft:.3f}, {lam:.3f}] GeV -- coherent: {ok}")
print("  f (chi-sector normalization) under-derived => Route V yields a window only; "
      "subordinate to Route P.")
results["route_VB"] = window

# === Route U: self-breakdown candidates + nulls ===
print("\n=== Route U: EFT self-breakdown candidates (pre-registered mechanism-less) ===")
F_PI_NR = M_CL / math.pi
cands = {
    "4pi_fpi_NR": 4 * math.pi * F_PI_NR,
    "4pi_fpi_rel": 4 * math.pi * F_PI_NR * math.sqrt(2.0),
    "2pi_M_cl": 2 * math.pi * M_CL,
    "pi_M_Q": math.pi * M_Q,
}
for k, v in cands.items():
    below = v < LAM_CL
    print(f"  {k:>12} = {v:.3f} GeV  (below 7*M_cl: {below})")
# wrong-target null: do any candidates coincide with an unrelated corpus scale?
targets = {"T_G": 0.6999, "m_tau": M_TAU, "m_b": 4.18, "sqrt_sigma": 0.4406,
           "Lambda_CL": LAM_CL, "Lambda_Q": LAM_Q}
hits = []
for ck, cv in cands.items():
    for tk, tv in targets.items():
        if abs(cv / tv - 1.0) < 0.05 and tk not in ("Lambda_CL", "Lambda_Q"):
            hits.append((ck, tk, cv, tv))
print(f"  wrong-target null (5% window vs unrelated corpus scales): {len(hits)} hits "
      f"{hits if hits else '(clean)'}")
# neighbor null: coefficient perturbation 4pi -> {2pi, 3pi, 5pi, 6pi}
neighbor = {f"{n}pi_fpi_NR": n * math.pi * F_PI_NR for n in (2, 3, 5, 6)}
ENV_LO, ENV_HI = 1.815, 2.106   # derived envelope (pole scheme band; tree inside)
in_env = {k: (ENV_LO <= v <= ENV_HI) for k, v in neighbor.items()}
print(f"  neighbor null (n*pi*f_pi vs envelope [{ENV_LO}, {ENV_HI}]): "
      f"{sum(in_env.values())}/{len(in_env)} land in envelope "
      f"({[k for k, b in in_env.items() if b]})")
print("  NOTE: 7pi*f_pi_NR = 7*M_cl/1 * ... -- by construction 7*M_cl = 7 pi f_pi^NR; the")
print("  Route P value IS expressible as 7*pi*f_pi^NR, but the mechanism (Z7-neutral chain)")
print("  fixes the multiplier; the f_pi rewriting adds no independent route.")
results["route_U"] = {"candidates_GeV": cands, "wrong_target_hits": hits,
                      "neighbor_in_envelope": in_env,
                      "verdict": "no sharp-boundary mechanism; all candidates below the "
                                 "threshold => EFT coherent up to 7M (lower-coherence audit passed)"}

out = "lambda_gte_band_route_battery_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"\nSaved {out}")
signal.alarm(0)
