#!/usr/bin/env python3
"""Final coupling verdict with the precision-measured kink broadening factor.

SUPERSEDES kink_form_factor_coupling_verdict.py for the b input (reason:
the parent-session b = 1.37 +/- 0.34 carried three unbudgeted defects, all
exposed by this session's benchmark gates: a recentering-phase sign error
that doubled wall drift in the ensemble profiles — the dominant inflation,
size- and run-length-dependent; an ensemble-mean meson-mass estimator
biased low by well-wandering zero-mode variance; and capillary/excursion
volatility in the small boxes misread as a finite-size systematic).
The sigma-verdict machinery (RGE, dictionary, corridor) is reused verbatim
and re-cross-validated against the published 088-R14 values.

Inputs (from kink_form_factor_precision_extraction_results.json):
  b assembly = b_phys(L=14, mu-cancelling band) + capillary size completion
  error budget: stat, mu-window, size-completion spread, estimator shape,
  spacing fold.

Outputs: c_kink^meas per Lambda reading, corridor adjudication, sigma table
(c = 0 / S1 / S1+measured), Lambda_diss, Route C containment, final labels.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 600


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

SB = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts"
with open(f"{SB}/kink_form_factor_precision_extraction_results.json") as f:
    EX = json.load(f)

ALPHA_S_MZ, ALPHA_S_MZ_ERR = 0.1180, 0.0009
M_Z, M_B, E2_V, M_TAU = 91.1876, 4.18, 3.5, 1.77686
LAM_CL, LAM_CL_ERR = (8.0 / 7.0) * M_TAU, (8.0 / 7.0) * 0.00012
LAM_Q, LAM_Q_ERR = 1.97046, 0.14560


def beta_coeffs(nf):
    return (11.0 - 2.0 * nf / 3.0, 102.0 - 38.0 * nf / 3.0,
            2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf ** 2)


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


def e2_ms(mu, a_mz=ALPHA_S_MZ):
    a_thr = run_alpha(a_mz, M_Z, M_B, 5)
    return 4 * math.pi * run_alpha(a_thr, M_B, mu, 4)


chk1, chk2 = e2_ms(2.0307), e2_ms(1.97046)
assert abs(chk1 - 3.7405) < 0.003 and abs(chk2 - 3.7934) < 0.003
print(f"RGE cross-validation vs 088-R14: e2(2.0307) = {chk1:.4f} [3.7405]; "
      f"e2(1.9705) = {chk2:.4f} [3.7934]  OK")

# ---------- b assembly ----------
b14 = EX["phys14"]["b"]
b14_stat = EX["phys14"]["err"]
size_corr = EX["size_completion"]["delta_rel"] * b14
size_spread = EX["size_completion"]["spread_rel"] * b14
mu_window = abs(EX["mu_window_syst"])
shape_syst = EX["shape_syst"]
spacing_fold = EX["spacing_fold"]
B = b14 + size_corr
B_STAT = b14_stat
B_SYST = math.hypot(math.hypot(size_spread, mu_window),
                    math.hypot(shape_syst, spacing_fold))
B_ERR = math.hypot(B_STAT, B_SYST)
print(f"\nb assembly: b(L14 phys) = {b14:.4f} +/- {b14_stat:.4f} (stat); "
      f"size completion {size_corr:+.4f} +/- {size_spread:.4f}")
print(f"systematics: mu-window {mu_window:.4f}; shape {shape_syst:.4f}; "
      f"spacing fold {spacing_fold:.4f}")
print(f"FINAL: b = {B:.4f} +/- {B_STAT:.4f} (stat) +/- {B_SYST:.4f} (syst)"
      f" = +/- {B_ERR:.4f}  [delta_b/b = {100 * B_ERR / B:.1f}%]")
DC = 8.0 * math.log(B)
DC_ERR = 8.0 * B_ERR / B
print(f"8 ln b = {DC:+.4f} +/- {DC_ERR:.4f}; Lambda_diss = m_phi/b = "
      f"{M_TAU / B * 1000:.0f} +/- {M_TAU * B_ERR / B ** 2 * 1000:.0f} MeV "
      f"({1 / B:.3f} m_phi)")

results = {"b": B, "b_stat": B_STAT, "b_syst": B_SYST, "b_err": B_ERR,
           "rel_err_pct": 100 * B_ERR / B, "delta_c": DC,
           "delta_c_err": DC_ERR,
           "lambda_diss_MeV": M_TAU / B * 1000, "readings": {}}

# ---------- Route C containment ----------
with open(f"{SB}/kink_form_factor_precision_dispersive_bracket_results.json"
          ) as f:
    RC = json.load(f)
born_max = RC["spectral_class_bounds"]["tree"]["b_max_born_floor"]
zz_max = RC["spectral_class_bounds"]["tree"]["b_max_zz_floor"]
print(f"\nRoute C containment: b = {B:.3f} vs hard bounds "
      f"b <= {born_max:.2f} (Born floor) / {zz_max:.2f} (ZZ floor): "
      f"{'INSIDE' if B < born_max else 'OUTSIDE'} "
      f"(margin {(born_max - B) / B_ERR:.1f} sigma_b)")
results["routeC"] = {"b_max_born": born_max, "b_max_zz": zz_max,
                     "inside": bool(B < born_max)}

# ---------- sigma verdicts ----------
print("\n=== sigma-verdicts per reading ===")
for lbl, lam, lam_err in (("tree (8/7) m_tau", LAM_CL, LAM_CL_ERR),
                          ("pole 7 M^Q (088-R14)", LAM_Q, LAM_Q_ERR)):
    e2c = e2_ms(lam)
    e2p = e2_ms(lam, ALPHA_S_MZ + ALPHA_S_MZ_ERR)
    e2m = e2_ms(lam, ALPHA_S_MZ - ALPHA_S_MZ_ERR)
    sig_pdg = 0.5 * abs(e2p - e2m)
    sig_scale = 0.5 * abs(e2_ms(lam + lam_err) - e2_ms(lam - lam_err))
    sig_comb = math.hypot(sig_pdg, sig_scale)
    c_req = (e2c / E2_V - 1.0) * 16 * math.pi ** 2 / E2_V
    ck_req = c_req - (-1.0)
    ck_S1 = 8.0 * math.log(lam / M_TAU)
    ck_meas = ck_S1 + DC

    def sigma_of(ck, ck_err=0.0):
        e2_pred = E2_V * (1 + (-1.0 + ck) * E2_V / (16 * math.pi ** 2))
        e2_pred_err = E2_V * ck_err * E2_V / (16 * math.pi ** 2)
        return (e2c - e2_pred) / math.hypot(sig_comb, e2_pred_err)

    s_c0 = (e2c - E2_V) / sig_comb
    s_S1 = sigma_of(ck_S1)
    s_meas = sigma_of(ck_meas, DC_ERR)
    s_stat = sigma_of(ck_meas, 8.0 * B_STAT / B)
    print(f"\n--- {lbl} ---")
    print(f"  Lambda = {lam:.4f} +/- {lam_err:.4f}; e2_MSbar = {e2c:.4f} "
          f"+/- {sig_pdg:.4f}_PDG +/- {sig_scale:.4f}_scale")
    print(f"  required c_kink (c_coset = -1): {ck_req:.3f}")
    print(f"  c_kink: S1 = {ck_S1:+.3f}; S1+measured = {ck_meas:+.3f} "
          f"+/- {DC_ERR:.3f}")
    print(f"  sigma: c=0: {s_c0:+.2f}; S1: {s_S1:+.2f}; S1+meas: "
          f"{s_meas:+.2f} (stat-only {s_stat:+.2f})")
    results["readings"][lbl] = {
        "Lambda": lam, "e2_ms": e2c, "sig_pdg": sig_pdg,
        "sig_scale": sig_scale, "ck_req": ck_req, "ck_S1": ck_S1,
        "ck_meas": ck_meas, "ck_meas_err": DC_ERR, "sigma_c0": s_c0,
        "sigma_S1": s_S1, "sigma_S1_meas": s_meas,
        "sigma_S1_meas_statonly": s_stat}

ck_tree = results["readings"]["tree (8/7) m_tau"]["ck_meas"]
ck_err = results["readings"]["tree (8/7) m_tau"]["ck_meas_err"]
in_corr = 3.1 <= ck_tree <= 6.8
print(f"\ntree-corridor adjudication: c_kink^meas = {ck_tree:+.3f} +/- "
      f"{ck_err:.3f} -> {'INSIDE' if in_corr else 'OUTSIDE'} [+3.1, +6.8]")
results["tree_corridor"] = {"ck": ck_tree, "inside": bool(in_corr)}

out = f"{SB}/kink_form_factor_precision_coupling_verdict_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
