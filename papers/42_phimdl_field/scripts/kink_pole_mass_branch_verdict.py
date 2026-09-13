#!/usr/bin/env python3
"""kink_pole_mass_branch_verdict.py

Final tree/pole branch decision for Lambda_GTE = 7 M_kink and the e^2 = 7/2
sigma-verdict, using the corrected independent quantum kink mass

    M^Q = 281 +/- 21 MeV   (this session: on-shell 282.9 / MSbar@m_phi 280.1;
                            envelope [259.3, 300.9] over the scheme family;
                            supersedes the P42 value 321.32 +/- 15.6 MeV)

RGE machinery reused verbatim from lambda_gte_band_sigma_verdict.py (088-R12):
PDG 2024 alpha_s(M_Z) = 0.1180 +/- 0.0009, 3-loop RK4, n_f 5->4 at m_b.
Dictionary (088-R09/R10/R11): e2_MSbar(Lambda) = e2_V (1 + c e2_V/16pi^2),
c = c_coset + c_kink; c_coset(M_V = Lambda) = -1; kink-VP scheme family shifts
exactly as c(scheme, Lambda) = c(scheme, Lambda_tree) + 8 ln(Lambda/Lambda_tree)
(all 088-R11 schemes are 8 ln(Lambda sqrt(s0)) + constant).

Scenarios per reading: c = 0; c = c_coset; c = c_coset + c_kink(S1 primary);
c_kink family band; required c_kink corridor. Plus mu* z-scores.

Expected: the corrected pole reading collapses onto the tree reading
(Lambda ~ 1.97-2.03 GeV); the +0.03 sigma pole closure of 088-R11 is retracted.
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

LAM_CL = (8.0 / 7.0) * M_TAU              # 2.030697 GeV (tree, CatAD)
LAM_CL_ERR = (8.0 / 7.0) * 0.00012

# Corrected independent M^Q (this session, GeV):
MQ_OS   = 0.282891     # on-shell scheme (primary physical condition)
MQ_MS   = 0.280098     # MSbar at mu = m_phi
MQ_LO   = 0.259299     # envelope edges (MSbar mu = 2m / mu = m/2)
MQ_HI   = 0.300896
MQ_CEN  = 0.5 * (MQ_OS + MQ_MS)            # 0.281495
MQ_ERR  = 0.5 * (MQ_HI - MQ_LO)            # 0.0208

LAM_Q_NEW     = 7.0 * MQ_CEN               # 1.97046 GeV
LAM_Q_NEW_ERR = 7.0 * MQ_ERR               # 0.1456 GeV
LAM_Q_OLD     = 7.0 * 0.32132              # 2.24924 (superseded P42 value)
LAM_Q_OLD_ERR = 0.1092

M_V_LO = math.sqrt(E2_V)

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

def e2_ms(mu, a_mz=ALPHA_S_MZ):
    return 4 * math.pi * alpha_s_at(mu, a_mz)

conv = abs(alpha_s_at(LAM_Q_NEW, nstep=8000) - alpha_s_at(LAM_Q_NEW)) / alpha_s_at(LAM_Q_NEW)
print(f"RK4 convergence: {conv:.2e}")

# machinery cross-validation against 088-R12 published values
e2_cl_check = e2_ms(LAM_CL)
e2_q_old = e2_ms(LAM_Q_OLD)
print(f"cross-validation: e2(2.0307) = {e2_cl_check:.4f} [R12: 3.7405]; "
      f"e2(2.2492) = {e2_q_old:.4f} [R12: 3.5720]")

def c_req_of(e2):
    return (e2 / E2_V - 1.0) * 16 * math.pi ** 2 / E2_V

def c_kink_S1(lam):
    return 8.0 * math.log(lam / M_TAU)     # PV at the PT threshold m_phi (R11 primary)

# R11 family relative offsets (tree values minus S1 tree value 1.0683)
FAMILY_REL = {"S1": 0.0, "S2": 0.2865 - 1.0683, "S3": 0.9630 - 1.0683,
              "S4": 0.1997 - 1.0683, "S5": 3.2712 - 1.0683, "S6": 2.5081 - 1.0683}

# mu*
lo, hi = 1.5, 4.0
for _ in range(60):
    mid = 0.5 * (lo + hi)
    if e2_ms(mid) > E2_V:
        lo = mid
    else:
        hi = mid
mu_star = 0.5 * (lo + hi)
print(f"mu* = {mu_star:.4f} GeV")

results = {"rk4_convergence": conv, "mu_star_GeV": mu_star,
           "MQ_corrected_GeV": {"central": MQ_CEN, "err": MQ_ERR,
                                "on_shell": MQ_OS, "MSbar_mphi": MQ_MS,
                                "envelope": [MQ_LO, MQ_HI]},
           "readings": {}}

print("\n=== sigma-verdicts per reading (corrected M^Q) ===")
for lbl, lam, lam_err in (("BA-MASS-CL (tree, unchanged)", LAM_CL, LAM_CL_ERR),
                          ("BA-MASS-Q corrected (7 M^Q = 1.970 +/- 0.146)", LAM_Q_NEW, LAM_Q_NEW_ERR),
                          ("BA-MASS-Q superseded (P42 321.32)", LAM_Q_OLD, LAM_Q_OLD_ERR)):
    e2c = e2_ms(lam)
    e2p = e2_ms(lam, ALPHA_S_MZ + ALPHA_S_MZ_ERR)
    e2m = e2_ms(lam, ALPHA_S_MZ - ALPHA_S_MZ_ERR)
    sig_pdg = 0.5 * abs(e2p - e2m)
    e2hi, e2lo = e2_ms(lam + lam_err), e2_ms(lam - lam_err)
    sig_scale = 0.5 * abs(e2hi - e2lo)
    sig_comb = math.hypot(sig_pdg, sig_scale)
    c_req = c_req_of(e2c)
    c_coset = -1.0                                  # M_V = Lambda (preferred, R11/R12)
    c_coset_lo = 21.0 * math.log(M_V_LO / lam) - 1.0
    ck_S1 = c_kink_S1(lam)
    fam = {k: ck_S1 + v for k, v in FAMILY_REL.items()}

    dev_c0 = (e2c - E2_V) / sig_comb
    e2_pred_S1 = E2_V * (1 + (c_coset + ck_S1) * E2_V / (16 * math.pi ** 2))
    dev_S1 = (e2c - e2_pred_S1) / sig_comb
    devs_fam = {}
    for k, ck in fam.items():
        e2_pred = E2_V * (1 + (c_coset + ck) * E2_V / (16 * math.pi ** 2))
        devs_fam[k] = (e2c - e2_pred) / sig_comb
    ck_req = c_req - c_coset                        # required kink VP for exact closure
    sig_c = c_req_of(e2c + sig_comb) - c_req
    mu_star_z = (mu_star - lam) / lam_err if lam_err > 1e-6 else float("inf")

    print(f"\n--- {lbl} ---")
    print(f"  Lambda = {lam:.4f} +/- {lam_err:.4f} GeV")
    print(f"  e2_MSbar = {e2c:.4f} +/- {sig_pdg:.4f}_PDG +/- {sig_scale:.4f}_scale "
          f"(comb {sig_comb:.4f}); offset vs 7/2: {100*(e2c/E2_V-1):+.2f}%")
    print(f"  c_req = {c_req:.3f} +/- {sig_c:.3f}; c_kink required (c_coset=-1): "
          f"{ck_req:.2f} +/- {sig_c:.2f}")
    print(f"  c_kink available: S1 = {ck_S1:+.3f}; family [{min(fam.values()):+.2f}, {max(fam.values()):+.2f}]")
    print(f"  sigma(c=0) = {dev_c0:+.2f}; sigma(S1 primary, c_coset=-1) = {dev_S1:+.2f}")
    print(f"  family sigmas: " + ", ".join(f"{k}:{v:+.2f}" for k, v in devs_fam.items()))
    print(f"  mu* z-score: {mu_star_z:+.2f}")

    results["readings"][lbl] = {
        "Lambda_GeV": lam, "Lambda_err_GeV": lam_err,
        "e2_MSbar": e2c, "sig_pdg": sig_pdg, "sig_scale": sig_scale,
        "sig_comb": sig_comb, "offset_percent": 100*(e2c/E2_V-1),
        "c_req": c_req, "c_req_err": sig_c,
        "c_kink_required_corridor": [ck_req - sig_c, ck_req + sig_c],
        "c_kink_S1": ck_S1, "c_kink_family": fam,
        "sigma_c0": dev_c0, "sigma_S1_primary": dev_S1,
        "sigma_family": devs_fam, "mu_star_z": mu_star_z,
    }

# branch separation statement
sep = (LAM_CL - LAM_Q_NEW) / LAM_Q_NEW_ERR
print(f"\nBranch separation: (Lambda_tree - Lambda_pole_corrected)/sigma_pole = {sep:+.2f}")
print("=> the tree reading lies INSIDE the corrected pole band: the R12 bifurcation dissolves.")
results["branch_separation_sigma"] = sep

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_pole_mass_branch_verdict_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {out}")

signal.alarm(0)
print("Done.")
