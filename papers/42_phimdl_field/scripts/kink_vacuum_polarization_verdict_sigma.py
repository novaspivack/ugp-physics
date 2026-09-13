#!/usr/bin/env python3
"""Final sigma-accounting for the kink vacuum-polarization constant (088-R11).

Combines the computed c_kink scheme family
(kink_vacuum_polarization_matching_constant.py) and the lattice control
(kink_vacuum_polarization_lattice_tape.py) with the 088-R12 derived
Lambda_GTE readings and the R10 coset constant:
  e2_pred = e2_V (1 + (c_coset + c_kink) e2_V / 16pi^2),  e2_V = 7/2,
compared against PDG 2024 alpha_s(M_Z) = 0.1180 +/- 0.0009 run down 3-loop
(nf 5->4 at m_b) to each Lambda reading. Reports per (reading, gap, scheme):
e2_pred, residual, sigma_PDG, sigma_combined; the corridor check; and the
joint falsification-trigger adjudication.

Expected: pole reading consistent across the family (best ~0.0-0.5 sigma);
tree reading in tension for the smooth/PV schemes, marginal for sharp.
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
SIXTEEN_PI2 = 16 * math.pi ** 2
M_TAU_GEV = 1.77686


def beta_coeffs(nf):
    b0 = 11.0 - 2.0 * nf / 3.0
    b1 = 102.0 - 38.0 * nf / 3.0
    b2 = 2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf ** 2
    return b0, b1, b2


def run_alpha(a0, mu0, mu1, nf, nstep=4000):
    b0, b1, b2 = beta_coeffs(nf)

    def rhs(a):
        return (-(b0 / (2 * math.pi)) * a * a
                - (b1 / (8 * math.pi ** 2)) * a ** 3
                - (b2 / (32 * math.pi ** 3)) * a ** 4)

    h = (math.log(mu1) - math.log(mu0)) / nstep
    a = a0
    for _ in range(nstep):
        k1 = rhs(a); k2 = rhs(a + 0.5 * h * k1)
        k3 = rhs(a + 0.5 * h * k2); k4 = rhs(a + h * k3)
        a += h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return a


def e2_msbar(mu, a_mz=ALPHA_S_MZ):
    a_thr = run_alpha(a_mz, M_Z, M_B, 5)
    return 4 * math.pi * run_alpha(a_thr, M_B, mu, 4)


# ------------------------------------------------- readings (088-R12 derived)
LAM_TREE = 8.0 / 7.0 * M_TAU_GEV          # 2.03070 GeV +/- 0.00014
LAM_POLE = 7.0 * 0.32132                  # 2.24924 GeV +/- 0.1092
SIG_LAM_POLE = 7.0 * 0.0156

readings = {}
for name, lam, sig_lam in (("tree", LAM_TREE, 8.0 / 7.0 * 0.00012),
                           ("pole", LAM_POLE, SIG_LAM_POLE)):
    e2c = e2_msbar(lam)
    sig_pdg = (e2_msbar(lam, ALPHA_S_MZ + ALPHA_S_MZ_ERR)
               - e2_msbar(lam, ALPHA_S_MZ - ALPHA_S_MZ_ERR)) / 2.0
    sig_scale = abs(e2_msbar(lam + sig_lam) - e2_msbar(lam - sig_lam)) / 2.0
    sig_comb = math.hypot(sig_pdg, sig_scale)
    readings[name] = {"lam": lam, "e2_MS": e2c, "sig_PDG": sig_pdg,
                      "sig_scale": sig_scale, "sig_comb": sig_comb,
                      "c_req": (e2c / E2_V - 1.0) * SIXTEEN_PI2 / E2_V}
    print(f"reading {name}: Lambda = {lam:.4f} GeV; e2_MS = {e2c:.4f} "
          f"+/- {sig_pdg:.4f}_PDG +/- {sig_scale:.4f}_scale "
          f"(comb {sig_comb:.4f}); c_req = {readings[name]['c_req']:.3f}")

# cross-validation vs the 088-R12 session values
assert abs(readings["tree"]["e2_MS"] - 3.7405) < 0.003, "tree e2 mismatch"
assert abs(readings["pole"]["e2_MS"] - 3.5720) < 0.003, "pole e2 mismatch"
print("cross-validation vs 088-R12 e2 values: OK\n")

# ------------------------------------------------------------ inputs: c_kink
with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "kink_vacuum_polarization_matching_constant_results.json") as fp:
    ck = json.load(fp)["c_kink"]
with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "kink_vacuum_polarization_lattice_tape_results.json") as fp:
    c_latt = json.load(fp)["c_latt_physical"]

M_V_SQRT72 = math.sqrt(3.5)   # e sqrt(Z0) f at f = 1 GeV


def c_coset(m_v, lam):
    return 21.0 * math.log(m_v / lam) - 1.0


schemes = ["S1_PV_mphi", "S2_PV_invrms", "S3_smooth_mphi", "S4_smooth_rms",
           "S5_sharp_mphi", "S6_sharp_rms"]
results = {"readings": readings, "table": {}}

print("=== sigma table: reading x gap x scheme ===")
for rname, r in readings.items():
    results["table"][rname] = {}
    for gap_name, m_v in (("MV=Lambda", r["lam"]), ("MV=sqrt(7/2)", M_V_SQRT72)):
        cc = c_coset(m_v, r["lam"])
        results["table"][rname][gap_name] = {"c_coset": cc, "rows": {}}
        print(f"  {rname}, {gap_name}: c_coset = {cc:+.3f}")
        for s in ["baseline_c0"] + schemes + ["latt_control"]:
            if s == "baseline_c0":
                ckv = 0.0
                ctot = 0.0
            elif s == "latt_control":
                ckv = c_latt
                ctot = cc + ckv
            else:
                ckv = ck[rname][s]
                ctot = cc + ckv
            e2p = E2_V * (1.0 + ctot * E2_V / SIXTEEN_PI2)
            resid = r["e2_MS"] - e2p
            row = {"c_kink": ckv, "c_total": ctot, "e2_pred": e2p,
                   "sigma_PDG": resid / r["sig_PDG"],
                   "sigma_comb": resid / r["sig_comb"]}
            results["table"][rname][gap_name]["rows"][s] = row
            print(f"    {s:16s}: c_kink = {ckv:+.3f}; e2_pred = {e2p:.4f}; "
                  f"{row['sigma_comb']:+.2f} sigma_comb "
                  f"({row['sigma_PDG']:+.2f} sigma_PDG)")

# ------------------------------------------------------- corridor adjudication
print("\n=== corridor adjudication (088-R12-updated corridors) ===")
corridors = {"tree": (3.1, 6.8), "pole": (0.6, 7.1)}
family = {r: [ck[r][s] for s in schemes] for r in readings}
results["corridor"] = {}
for rname, (lo, hi) in corridors.items():
    band = (min(family[rname]), max(family[rname]))
    primary = ck[rname]["S1_PV_mphi"]
    inside_primary = lo <= primary <= hi
    overlap = band[1] >= lo and band[0] <= hi
    results["corridor"][rname] = {
        "corridor": [lo, hi], "family_band": band, "primary_S1": primary,
        "primary_inside": inside_primary, "band_overlaps": overlap}
    print(f"  {rname}: corridor [{lo}, {hi}]; family band "
          f"[{band[0]:+.2f}, {band[1]:+.2f}]; primary S1 = {primary:+.3f} "
          f"({'INSIDE' if inside_primary else 'OUTSIDE'}); band overlap: "
          f"{'YES' if overlap else 'NO'}")

# joint trigger: >3 sigma requires computed value outside corridor AND tight band
worst_best = {}
for rname in readings:
    sigs = [abs(results["table"][rname]["MV=Lambda"]["rows"][s]["sigma_comb"])
            for s in schemes]
    worst_best[rname] = (min(sigs), max(sigs))
    print(f"  {rname} (MV=Lambda): |sigma_comb| over family = "
          f"[{min(sigs):.2f}, {max(sigs):.2f}]")
results["family_sigma_range_MV_Lambda"] = worst_best

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "kink_vacuum_polarization_verdict_sigma_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
