#!/usr/bin/env python3
"""e^2 = 7/2 <-> PDG sigma-verdict under the derived Lambda_GTE readings.

Readings (from lambda_gte_band_threshold_derivation.py; pole-mass input is the
corrected M^Q = 281 +/- 21 MeV, P42 GJQW interface dim-reg):
  BA-MASS-CL: Lambda = (8/7) m_tau = 2.03070 +/- 0.00014 GeV   (tree identities)
  BA-MASS-Q : Lambda = 7 M^Q      = 1.9705  +/- 0.1456  GeV   (pole/threshold)
  Envelope  : 1.96 +/- 0.15 GeV (pole scheme band; tree value inside)

Machinery: PDG 2024 alpha_s(M_Z) = 0.1180 +/- 0.0009, 3-loop RK4 run-down with
n_f 5->4 at m_b (identical to villain_msbar_required_coefficient.py; convergence
checked). Dictionary: e2_MSbar = e2_V (1 + c e2_V/16pi^2), c = c_coset + c_kink,
c_coset = 21 ln(M_V/Lambda) - 1 (t_V = 3; 088-R10), M_V in [sqrt(7/2), Lambda].

Scenarios per reading: (a) c = 0; (b) c_kink = 0 (c = c_coset); (c) corridor for
c_kink that closes the match exactly. Also: mu* z-scores; alpha_s(M_Z) anchor-chain
sensitivity to the boundary location (fixed anchor value, moved start scale).

Expected: BA-Q -> ~+1.9 sigma at c = 0; BA-CL -> ~+3.1 sigma at c = 0 (no robust
>3 sigma anomaly across the scheme family); closure corridors per reading.
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

ALPHA_S_MZ = 0.1180
ALPHA_S_MZ_ERR = 0.0009
M_Z = 91.1876
M_B = 4.18
E2_V = 3.5
M_TAU = 1.77686
LAM_CL = (8.0 / 7.0) * M_TAU          # 2.030697...
LAM_CL_ERR = (8.0 / 7.0) * 0.00012
LAM_Q = 7 * 0.2815                     # 1.9705 (corrected pole mass, P42)
LAM_Q_ERR = 7 * 0.0208                 # 0.1456 (scheme envelope half-width)
M_V_LO = math.sqrt(E2_V)               # sqrt(7/2) = 1.8708 (R10 BA-GAP lower edge)

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
    t0, t1 = math.log(mu0), math.log(mu1)
    h = (t1 - t0) / nstep
    a = a0
    for _ in range(nstep):
        k1 = rhs(a); k2 = rhs(a + 0.5 * h * k1)
        k3 = rhs(a + 0.5 * h * k2); k4 = rhs(a + h * k3)
        a += h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return a

def alpha_s_at(mu, a_mz=ALPHA_S_MZ, loops=3, nstep=4000):
    a_thr = run_alpha(a_mz, M_Z, M_B, 5, loops, nstep)
    return run_alpha(a_thr, M_B, mu, 4, loops, nstep)

# convergence diagnostic
conv = abs(alpha_s_at(LAM_Q, nstep=8000) - alpha_s_at(LAM_Q)) / alpha_s_at(LAM_Q)
print(f"RK4 convergence (4000 vs 8000 steps at Lambda_Q): rel diff = {conv:.2e}")

def e2_ms(mu, a_mz=ALPHA_S_MZ):
    return 4 * math.pi * alpha_s_at(mu, a_mz)

def c_req_of(e2):
    return (e2 / E2_V - 1.0) * 16 * math.pi ** 2 / E2_V

results = {"rk4_convergence": conv, "readings": {}}

# mu* : exact-match scale (bisection on e2_ms(mu) = 3.5)
lo, hi = 1.5, 4.0
for _ in range(60):
    mid = 0.5 * (lo + hi)
    if e2_ms(mid) > E2_V:
        lo = mid
    else:
        hi = mid
mu_star = 0.5 * (lo + hi)
print(f"mu* (e2_MSbar = 7/2 exactly): {mu_star:.4f} GeV")
results["mu_star_GeV"] = mu_star

print("\n=== sigma-verdicts per reading ===")
for lbl, lam, lam_err in (("BA-MASS-CL", LAM_CL, LAM_CL_ERR),
                          ("BA-MASS-Q", LAM_Q, LAM_Q_ERR)):
    e2c = e2_ms(lam)
    # PDG error via +/-1 sigma alpha_s(M_Z)
    e2p = e2_ms(lam, ALPHA_S_MZ + ALPHA_S_MZ_ERR)
    e2m = e2_ms(lam, ALPHA_S_MZ - ALPHA_S_MZ_ERR)
    sig_pdg = 0.5 * abs(e2p - e2m)
    # scale error via Lambda band edges
    e2hi = e2_ms(lam + lam_err)
    e2lo = e2_ms(lam - lam_err)
    sig_scale = 0.5 * abs(e2hi - e2lo)
    sig_comb = math.hypot(sig_pdg, sig_scale)
    c_req = c_req_of(e2c)
    sig_c = c_req_of(e2c + sig_comb) - c_req     # corridor half-width from combined error
    # coset constant window: M_V in [sqrt(7/2), Lambda]
    c_coset_hi = -1.0                                       # M_V = Lambda
    c_coset_lo = 21.0 * math.log(M_V_LO / lam) - 1.0        # M_V = sqrt(7/2)
    # scenarios
    dev_c0 = (e2c - E2_V) / sig_comb
    dev_c0_pdgonly = (e2c - E2_V) / sig_pdg
    e2_pred_cosethi = E2_V * (1 + c_coset_hi * E2_V / (16 * math.pi ** 2))
    e2_pred_cosetlo = E2_V * (1 + c_coset_lo * E2_V / (16 * math.pi ** 2))
    dev_coset_hi = (e2c - e2_pred_cosethi) / sig_comb
    dev_coset_lo = (e2c - e2_pred_cosetlo) / sig_comb
    # kink-VP closure corridor: c_kink = c_req - c_coset, +/- sig_c
    ck_lo = c_req - c_coset_hi - sig_c
    ck_hi = c_req - c_coset_lo + sig_c
    ck_central = (c_req - c_coset_hi, c_req - c_coset_lo)
    z_mu_star = (mu_star - lam) / lam_err
    print(f"\n[{lbl}]  Lambda = {lam:.4f} +/- {lam_err:.4f} GeV")
    print(f"  e2_MSbar(Lambda) = {e2c:.4f} +/- {sig_pdg:.4f}_PDG +/- {sig_scale:.4f}_scale "
          f"(combined {sig_comb:.4f})")
    print(f"  offset vs 7/2: {100*(e2c/E2_V-1):+.2f}%  | c_req = {c_req:.3f} +/- {sig_c:.3f}")
    print(f"  scenario (a) c = 0          : {dev_c0:+.2f} sigma_comb  ({dev_c0_pdgonly:+.2f} sigma_PDG-only)")
    print(f"  scenario (b) c_kink = 0     : {dev_coset_hi:+.2f} sigma (M_V = Lambda) ... "
          f"{dev_coset_lo:+.2f} sigma (M_V = sqrt(7/2))")
    print(f"  scenario (c) closure corridor: c_kink in [{ck_lo:.2f}, {ck_hi:.2f}] "
          f"(centrals {ck_central[0]:.2f}/{ck_central[1]:.2f})")
    print(f"  mu* z-score in this reading : {z_mu_star:+.2f} sigma_scale")
    results["readings"][lbl] = {
        "Lambda_GeV": lam, "Lambda_err_GeV": lam_err,
        "e2_MS": e2c, "sig_pdg": sig_pdg, "sig_scale": sig_scale, "sig_comb": sig_comb,
        "offset_pct": 100 * (e2c / E2_V - 1), "c_req": c_req, "c_req_err": sig_c,
        "dev_c0_sigma_comb": dev_c0, "dev_c0_sigma_pdg_only": dev_c0_pdgonly,
        "dev_ckink0_sigma": [dev_coset_hi, dev_coset_lo],
        "c_coset_window": [c_coset_lo, c_coset_hi],
        "c_kink_corridor": [ck_lo, ck_hi], "c_kink_centrals": list(ck_central),
        "mu_star_z": z_mu_star}

# === alpha_s(M_Z) anchor-chain sensitivity (P39 G10 chain) ===
# The sigma_GTE chain anchors alpha_s at Lambda_GTE and runs UP. Holding the anchor
# VALUE fixed and moving the start scale 2.01 -> {2.031, 1.970} shifts alpha_s(M_Z).
print("\n=== P39 alpha_s(M_Z) anchor-chain sensitivity ===")
a_anchor = alpha_s_at(2.01)   # representative anchor value at the published scale
sens = {}
for lbl, lam in (("published_2.01", 2.01), ("BA-MASS-CL", LAM_CL), ("BA-MASS-Q", LAM_Q)):
    a4 = run_alpha(a_anchor, lam, M_B, 4)
    a_mz = run_alpha(a4, M_B, M_Z, 5)
    sens[lbl] = a_mz
    print(f"  anchor at {lam:.3f} GeV -> alpha_s(M_Z) = {a_mz:.5f} "
          f"({100*(a_mz/sens['published_2.01']-1):+.2f}% vs published-scale chain)"
          if lbl != "published_2.01" else
          f"  anchor at {lam:.3f} GeV -> alpha_s(M_Z) = {a_mz:.5f} (reference)")
results["alpha_s_MZ_anchor_sensitivity"] = sens

out = "lambda_gte_band_sigma_verdict_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"\nSaved {out}")
signal.alarm(0)
