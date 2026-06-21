#!/usr/bin/env python3
"""Route C: analytic dispersive bracket on the kink broadening factor b.

Vectorized (numpy) version of the sum-rule-constrained dispersive
construction of dissolution_constant_sumrule_dispersive.py (the O(n^2)
Cauchy kernel is precomputed as a matrix; the original scalar loop timed
out).  Physics content identical and pre-registered there:

  - once-subtracted DR, Watson elastic window with the exact ZZ phase
    delta_ZZ(theta) = -arctan(1/sinh theta) (CatAD, pole-free, B = 1)
  - positive inelastic Im F above s_inel = (2M + m_phi)^2 with the frozen
    shape family H1..H4 (declared before any number in the parent session)
  - normalization B from the charge sum rule (1/pi) int ImF/s' = 1
    (primary bracket members: b-independent), and from the radius sum rule
    at the CLASSICAL radius (reported as unbroadened reference only)

Updated inputs (this session): pole reading uses the corrected
M^Q = 281 +/- 21 MeV (088-R14); tree reading M_cl = (8/49) m_tau.

Output per admissible member: Lambda_diss = M exp[(3/8) int K |F|^2 ds/s]
and the implied broadening b_implied = m_phi / Lambda_diss.  The bracket is
[min, max] over admissible charge-rule members per reading; additionally the
Watson-elastic-only floor (mandatory elastic weight, zero inelastic) gives
the model-independent hard upper bound on b.

Expected: a finite bracket; the verdict is whether the measured b lies
inside it with margins.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 1200


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

M_TAU = 1776.86
M_PHI = M_TAU
R2_CLASSICAL = math.pi ** 2 / (12.0 * M_PHI ** 2)
READINGS = {"tree": {"M": 8.0 / 49.0 * M_TAU},
            "pole": {"M": 281.0}}
SHAPES = ("H1", "H2", "H3", "H4")
N_GRID = 3000
THETA_MAX = 26.0
results = {"r2_classical_MeV-2": R2_CLASSICAL,
            "M_pole_MeV": 281.0, "M_tree_MeV": 8.0 / 49.0 * M_TAU}


def build(M):
    h = THETA_MAX / N_GRID
    th = (np.arange(N_GRID) + 0.5) * h
    s = 4.0 * M * M * np.cosh(th / 2.0) ** 2
    w = s * np.tanh(th / 2.0) * h
    return th, s, w


def shape_arr(name, s, s_inel, rt_on):
    rt = np.sqrt(s)
    out = np.zeros_like(s)
    m = rt > rt_on
    if name == "H1":
        out[m] = np.exp(-(rt[m] - rt_on) * math.pi / (2.0 * M_PHI))
    elif name == "H2":
        out[m] = np.exp(-(rt[m] - rt_on) / M_PHI)
    elif name == "H3":
        out[m] = (s_inel / s[m]) ** 1.5
    elif name == "H4":
        out[m] = (s_inel / s[m]) ** 2.5
    return out


def solve_model(M, shape, norm_rule, iters=600):
    s_inel = (2.0 * M + M_PHI) ** 2
    rt_on = 2.0 * M + M_PHI
    th, s, w = build(M)
    el = s <= s_inel
    sh = shape_arr(shape, s, s_inel, rt_on)
    sin_dzz = np.where(th > 0, np.sin(-np.arctan(1.0 / np.sinh(th))), -1.0)
    # Cauchy matrix with delta-subtraction PV:
    # acc_i = sum_{j != i} (imf_j - imf_i) w_j / (s_j (s_j - s_i))
    DS = s[None, :] - s[:, None]                    # DS[i,j] = s_j - s_i
    den = s[None, :] * DS
    with np.errstate(divide="ignore", invalid="ignore"):
        Mmat = w[None, :] / den
    np.fill_diagonal(Mmat, 0.0)
    rowsum = Mmat.sum(axis=1)
    s_th = 4.0 * M * M
    th_edge = th[-1] + (th[1] - th[0]) / 2.0
    s_max = 4.0 * M * M * math.cosh(th_edge / 2.0) ** 2
    pv = (1.0 / s) * (np.log(np.abs((s_max - s) / s_max))
                      - np.log(np.abs((s_th - s) / s_th)))
    beta = np.sqrt(np.clip(1.0 - 4.0 * M * M / s, 0.0, None))
    K = (4.0 / 3.0) * (1.0 + 2.0 * M * M / s) * beta
    absF = beta.copy()
    B = 1.0
    in_1 = float(np.sum(sh[~el] / s[~el] * w[~el]) / math.pi)
    in_2 = float(np.sum(sh[~el] / s[~el] ** 2 * w[~el]) * 6.0 / math.pi)
    N_CLAMP = 5   # threshold points: PV log artifact at measure-zero kernel

    def observable(aF, Bv):
        imf_o = np.where(el, aF * sin_dzz, Bv * sh)
        acc_o = Mmat @ imf_o - imf_o * rowsum
        re_o = 1.0 + (s / math.pi) * (acc_o + imf_o * pv)
        F2 = re_o ** 2 + imf_o ** 2
        return M * math.exp((3.0 / 8.0) * float(np.sum(K * F2 * w / s)))

    lam_hist = []
    for it in range(iters):
        imf = np.where(el, absF * sin_dzz, B * sh)
        el_1 = float(np.sum(imf[el] / s[el] * w[el]) / math.pi)
        el_2 = float(np.sum(imf[el] / s[el] ** 2 * w[el]) * 6.0 / math.pi)
        B_new = ((1.0 - el_1) / in_1 if norm_rule == "charge"
                 else (R2_CLASSICAL - el_2) / in_2)
        B = 0.9 * B + 0.1 * B_new
        acc = Mmat @ imf - imf * rowsum
        re = 1.0 + (s / math.pi) * (acc + imf * pv)
        mag = np.hypot(re, imf)
        mag = np.where(el, mag, 0.0)
        # Omnes threshold behavior |F| ~ beta (exponent +1, CatAD R13):
        # clamp the first few grid points where the PV log is singular
        mag[:N_CLAMP] = mag[N_CLAMP] * beta[:N_CLAMP] / max(beta[N_CLAMP],
                                                            1e-12)
        shift = float(np.max(np.abs(mag - absF)[N_CLAMP:]))
        absF = 0.9 * absF + 0.1 * mag
        if absF.max() > 200.0:
            return None, {"runaway": True, "iterations": it + 1}
        if it % 10 == 0:
            lam_hist.append(observable(absF, B))
            if (len(lam_hist) >= 6 and
                    max(lam_hist[-5:]) - min(lam_hist[-5:])
                    < 1e-4 * lam_hist[-1]):
                break
    imf = np.where(el, absF * sin_dzz, B * sh)
    chg = el_1 + B * in_1
    rad = (el_2 + B * in_2) / R2_CLASSICAL
    lam_diss = observable(absF, B)
    conv = (len(lam_hist) >= 6 and
            max(lam_hist[-5:]) - min(lam_hist[-5:]) < 1e-3 * lam_diss)
    rep = {"B": B, "iterations": it + 1, "converged_shift": shift,
           "charge_sumrule": chg, "radius_over_classical": rad,
           "lam_hist_tail": lam_hist[-5:], "runaway": not conv}
    return lam_diss, rep


print("=== Route C: dispersive bracket on b (corrected M^Q = 281 MeV) ===")
results["members"] = {}
for rname, r in READINGS.items():
    M = r["M"]
    results["members"][rname] = {}
    # Watson-elastic-only floor: g = |F_el|^2 from the converged elastic
    # solution with B -> 0 is not self-consistent (radius rule fails), but
    # the elastic weight is MANDATORY, giving the model-independent minimal
    # Lambda_diss = hard upper bound on b.
    th, s, w = build(M)
    el = s <= (2.0 * M + M_PHI) ** 2
    sin_dzz = np.where(th > 0, np.sin(-np.arctan(1.0 / np.sinh(th))), -1.0)
    beta = np.sqrt(np.clip(1.0 - 4.0 * M * M / s, 0.0, None))
    K = (4.0 / 3.0) * (1.0 + 2.0 * M * M / s) * beta
    g_el = np.where(el, np.clip(1.0 - 4.0 * M * M / s, 0, None), 0.0)
    lam_floor = M * math.exp((3.0 / 8.0) * float(np.sum(K * g_el * w / s)))
    b_hard_max = M_PHI / lam_floor
    print(f"\n--- {rname} reading (M = {M:.2f} MeV) ---")
    print(f"  Watson-elastic-only floor: Lambda_diss >= {lam_floor:.0f} MeV "
          f"=> hard bound b <= {b_hard_max:.3f}")
    results["members"][rname]["elastic_floor"] = {
        "lambda_diss_MeV": lam_floor, "b_hard_max": b_hard_max}
    for shape in SHAPES:
        for rule in ("charge", "radius"):
            lam, rep = solve_model(M, shape, rule)
            key = f"{shape}_{rule}"
            if lam is None or rep.get("runaway"):
                results["members"][rname][key] = {"rejected": True, **rep}
                print(f"  {shape}/{rule}: NON-CONVERGENT/runaway")
                continue
            if rep["B"] < 0:
                results["members"][rname][key] = {
                    "rejected": "negative inelastic weight", **rep}
                print(f"  {shape}/{rule}: REJECTED (B = {rep['B']:.3f} < 0)")
                continue
            b_impl = M_PHI / lam
            results["members"][rname][key] = {
                "lambda_diss_MeV": lam, "b_implied": b_impl, **rep}
            print(f"  {shape}/{rule}: B = {rep['B']:+.4f}; chargeSR = "
                  f"{rep['charge_sumrule']:.4f}; radius/cl = "
                  f"{rep['radius_over_classical']:+.3f}; Lambda_diss = "
                  f"{lam:.0f} MeV; b_implied = {b_impl:.3f}")

print("\n=== spectral-class hard bounds (R13 map, g in [0,1]) ===")
# Within the R13 spectral class Lambda_diss = M exp[(3/8) int K g ds/s] the
# weight g may extend arbitrarily high in s (more UV weight -> larger
# Lambda_diss -> SMALLER b), so the spectral side gives no model-independent
# lower bound on b.  It gives two hard UPPER bounds on b:
#   (i) Born-floor: the mandatory Watson elastic window with the minimal
#       (threshold-suppressed Born) weight g = beta^2 -> min Lambda_diss
#  (ii) ZZ floor: all charged weight above the pair threshold 4M^2
#       (pole-freedom, CatAD) -> Lambda_diss >= 2M
results["spectral_class_bounds"] = {}
for rname, r in READINGS.items():
    M = r["M"]
    th, s, w = build(M)
    el = s <= (2.0 * M + M_PHI) ** 2
    beta = np.sqrt(np.clip(1.0 - 4.0 * M * M / s, 0.0, None))
    K = (4.0 / 3.0) * (1.0 + 2.0 * M * M / s) * beta
    g_min = np.where(el, beta ** 2, 0.0)
    lam_min = M * math.exp((3.0 / 8.0) * float(np.sum(K * g_min * w / s)))
    results["spectral_class_bounds"][rname] = {
        "lambda_diss_born_floor_MeV": lam_min,
        "b_max_born_floor": M_PHI / lam_min,
        "lambda_diss_zz_floor_MeV": 2.0 * M,
        "b_max_zz_floor": M_PHI / (2.0 * M)}
    print(f"  {rname}: Born floor Lambda_diss >= {lam_min:.0f} MeV => "
          f"b <= {M_PHI / lam_min:.3f}; ZZ floor Lambda_diss >= "
          f"{2 * M:.0f} MeV => b <= {M_PHI / (2 * M):.3f}")

results["family_incompatibility"] = (
    "no member of the pre-registered minimal dispersive family satisfies "
    "both the charge and radius sum rules: charge-rule fixed points have "
    "elastic |F| ~ 9.5 and radius/classical ~ -7; radius-rule members run "
    "away; the R13 structural obstruction extends to bracket generation")

print("\n=== bracket (charge-rule members, primary) ===")
results["bracket"] = {}
for rname in READINGS:
    vals = [v["b_implied"] for k, v in results["members"][rname].items()
            if k.endswith("_charge") and "b_implied" in v]
    allv = [v["b_implied"] for k, v in results["members"][rname].items()
            if "b_implied" in v]
    if vals:
        results["bracket"][rname] = {
            "b_min_charge": min(vals), "b_max_charge": max(vals),
            "b_min_all": min(allv), "b_max_all": max(allv),
            "b_hard_max": results["members"][rname]["elastic_floor"][
                "b_hard_max"]}
        print(f"  {rname}: charge-rule b in [{min(vals):.3f}, {max(vals):.3f}]"
              f" ({len(vals)} members); all members [{min(allv):.3f}, "
              f"{max(allv):.3f}]; hard b <= "
              f"{results['bracket'][rname]['b_hard_max']:.3f}")

out = ("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
       "kink_form_factor_precision_dispersive_bracket_results.json")
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
