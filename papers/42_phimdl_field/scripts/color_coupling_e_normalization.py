#!/usr/bin/env python3
"""Physical normalization of the GTE color gauge coupling e (OQ-088-R06a, e-part).

The CatAL color coupling is g_c^2 = N_7/SylowIndex = 7/2 in the Villain
(heat-kernel) lattice convention (SylowIndexCouplingHierarchy.lean,
colorCouplingSquared; beta_color = 2/7). The open question is whether e^2 = 7/2
at the EFT boundary Lambda_GTE = 2.01 GeV (P39 sigma_GTE anchor scale) equals
the physical color coupling, i.e. whether

    alpha_c^{Villain}(Lambda_GTE) = (7/2)/(4 pi) = 0.27852

matches alpha_s^{MSbar}(Lambda_GTE) obtained by running PDG 2024
alpha_s(M_Z) = 0.1180 +/- 0.0009 down to Lambda_GTE (2-loop and 3-loop QCD,
n_f = 5 -> 4 threshold at m_b).

Pre-registered tests:
  T1 (match):    |4 pi alpha_s(Lambda_GTE) - 7/2| / (7/2) <= 0.15
                 (one-loop scheme-conversion size for lattice<->MSbar).
  T2 (neighbor): 7/2 is the unique closest member of the Sylow rational family
                 {7/1, 7/2, 7/3, 7/6, 3/2, 5/2, 9/2, 21/2} to 4 pi alpha_s(Lambda_GTE).
  T3 (scale):    the scale mu* where 4 pi alpha_s(mu*) = 7/2 exactly lies in
                 [1.5, 3.5] GeV (the EFT-boundary neighborhood), not at an
                 unrelated scale.

Also computes the IR running of e^2 in the GTE EFT below Lambda_GTE with the
CatAL coefficients b0 = 7, b1 = 26 (variant b0 = 9 i.e. QCD n_f = 3 as a
systematic), for use in the RG-improved vacuum-selection computation.

Expected output: alpha_s(2.01 GeV) ~ 0.29-0.31; ratio to Villain ~ 1.04-1.10;
T1-T3 PASS; e^2(T_G = 0.70 GeV) ~ 5-6 (GTE running).
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

# --- PDG 2024 inputs (CANONICAL_COMPARISON_DATA.md) ---
ALPHA_S_MZ = 0.1180
ALPHA_S_MZ_ERR = 0.0009
M_Z = 91.1876
M_B = 4.18           # MSbar b-quark threshold
LAMBDA_GTE = 2.01    # GeV (P39)
VILLAIN_E2 = 3.5     # CatAL g_c^2 = 7/2
ALPHA_VILLAIN = VILLAIN_E2 / (4.0 * math.pi)

def beta_coeffs_qcd(nf):
    """Standard SU(3) coefficients: d alpha/d ln mu = -(b0/2pi) a^2 - (b1/8pi^2) a^3 - (b2/32pi^3) a^4."""
    b0 = 11.0 - 2.0 * nf / 3.0
    b1 = 102.0 - 38.0 * nf / 3.0
    b2 = 2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf ** 2
    return b0, b1, b2

def run_alpha(a0, mu0, mu1, nf, loops=2, nstep=4000):
    """RK4 integration of the QCD RGE in t = ln mu."""
    b0, b1, b2 = beta_coeffs_qcd(nf)
    def rhs(a):
        d = -(b0 / (2.0 * math.pi)) * a * a - (b1 / (8.0 * math.pi ** 2)) * a ** 3
        if loops >= 3:
            d += -(b2 / (32.0 * math.pi ** 3)) * a ** 4
        return d
    t0, t1 = math.log(mu0), math.log(mu1)
    h = (t1 - t0) / nstep
    a = a0
    for _ in range(nstep):
        k1 = rhs(a)
        k2 = rhs(a + 0.5 * h * k1)
        k3 = rhs(a + 0.5 * h * k2)
        k4 = rhs(a + h * k3)
        a += h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return a

def alpha_s_at(mu, a_mz, loops):
    """PDG running M_Z -> mu with nf = 5 -> 4 threshold at m_b (mu >= 1.3)."""
    if mu >= M_B:
        return run_alpha(a_mz, M_Z, mu, 5, loops)
    a_mb = run_alpha(a_mz, M_Z, M_B, 5, loops)
    return run_alpha(a_mb, M_B, mu, 4, loops)

results = {"inputs": {"alpha_s_MZ": ALPHA_S_MZ, "err": ALPHA_S_MZ_ERR,
                      "Lambda_GTE": LAMBDA_GTE, "villain_e2": VILLAIN_E2,
                      "alpha_villain": ALPHA_VILLAIN}}

print("=== 1. PDG alpha_s run down to Lambda_GTE ===")
tab = {}
for loops in (2, 3):
    a_c = alpha_s_at(LAMBDA_GTE, ALPHA_S_MZ, loops)
    a_lo = alpha_s_at(LAMBDA_GTE, ALPHA_S_MZ - ALPHA_S_MZ_ERR, loops)
    a_hi = alpha_s_at(LAMBDA_GTE, ALPHA_S_MZ + ALPHA_S_MZ_ERR, loops)
    tab[loops] = (a_c, a_lo, a_hi)
    print(f"  {loops}-loop: alpha_s({LAMBDA_GTE}) = {a_c:.5f}  "
          f"[{a_lo:.5f}, {a_hi:.5f}];  e^2 = 4 pi alpha = {4*math.pi*a_c:.4f}")
results["alpha_s_LambdaGTE"] = {f"{k}loop": v for k, v in tab.items()}

a_central = tab[3][0]
e2_pdg = 4.0 * math.pi * a_central
ratio = a_central / ALPHA_VILLAIN
conv_needed = (ratio - 1.0)
# size of a generic one-loop scheme conversion: c * g^2/(16 pi^2) with c = O(1..5)
c_oneloop = conv_needed * 16.0 * math.pi ** 2 / VILLAIN_E2
print(f"\n=== 2. Villain comparison ===")
print(f"  alpha_Villain = (7/2)/(4pi) = {ALPHA_VILLAIN:.5f}")
print(f"  alpha_s^PDG(Lambda_GTE) 3-loop = {a_central:.5f}")
print(f"  ratio = {ratio:.4f}  (relative offset {100*conv_needed:.2f}%)")
print(f"  required one-loop conversion coefficient c (g^2_phys = g^2_V(1 + c g_V^2/16pi^2)): c = {c_oneloop:.2f}")
T1 = abs(e2_pdg - VILLAIN_E2) / VILLAIN_E2 <= 0.15
print(f"  T1 (match within 15%): {'PASS' if T1 else 'FAIL'}")
results["villain_match"] = {"e2_pdg_3loop": e2_pdg, "ratio": ratio,
                            "conversion_coefficient_c": c_oneloop, "T1_pass": bool(T1)}

print(f"\n=== 3. T2 neighbor null: Sylow rational family ===")
family = {"7/1": 7.0, "7/2": 3.5, "7/3": 7.0/3.0, "7/6": 7.0/6.0,
          "3/2": 1.5, "5/2": 2.5, "9/2": 4.5, "21/2": 10.5}
dist = {k: abs(v - e2_pdg) for k, v in family.items()}
order = sorted(dist, key=dist.get)
for k in order:
    print(f"  {k:>5} = {family[k]:7.4f}   |e2 - cand| = {dist[k]:.4f}")
T2 = order[0] == "7/2"
print(f"  T2 (7/2 unique closest): {'PASS' if T2 else 'FAIL'}")
results["neighbor_null"] = {"distances": dist, "closest": order[0], "T2_pass": bool(T2)}

print(f"\n=== 4. T3 wrong-scale null: where does 4 pi alpha_s(mu) = 7/2 exactly? ===")
lo, hi = 1.0, 20.0
for _ in range(80):
    mid = math.sqrt(lo * hi)
    if 4.0 * math.pi * alpha_s_at(mid, ALPHA_S_MZ, 3) > VILLAIN_E2:
        lo = mid
    else:
        hi = mid
mu_star = math.sqrt(lo * hi)
T3 = 1.5 <= mu_star <= 3.5
print(f"  mu* = {mu_star:.3f} GeV  (Lambda_GTE = {LAMBDA_GTE});  "
      f"T3 (mu* in [1.5, 3.5]): {'PASS' if T3 else 'FAIL'}")
results["scale_null"] = {"mu_star_GeV": mu_star, "T3_pass": bool(T3)}

print(f"\n=== 5. GTE-EFT IR running of e^2 below Lambda_GTE (b0=7, b1=26 CatAL) ===")
A_CAP = 2.0  # non-perturbative flag value (IR Landau-pole guard)

def run_gte(a0, mu0, mu1, b0, b1, nstep=4000):
    def rhs(a):
        return -(b0 / (2.0 * math.pi)) * a * a - (b1 / (8.0 * math.pi ** 2)) * a ** 3
    t0, t1 = math.log(mu0), math.log(mu1)
    h = (t1 - t0) / nstep
    a = a0
    for _ in range(nstep):
        k1 = rhs(a); k2 = rhs(a + 0.5*h*k1); k3 = rhs(a + 0.5*h*k2); k4 = rhs(a + h*k3)
        a += h / 6.0 * (k1 + 2*k2 + 2*k3 + k4)
        if a >= A_CAP:
            return A_CAP  # IR pole reached: flagged, not used quantitatively
    return a

ir_tab = {}
for label, anchor in [("villain", ALPHA_VILLAIN), ("pdg_matched", a_central)]:
    row = {}
    for mu in [2.01, 1.5, 1.0, 0.7, 0.5, 0.3]:
        a = run_gte(anchor, LAMBDA_GTE, mu, 7.0, 26.0) if mu != LAMBDA_GTE else anchor
        row[mu] = 4.0 * math.pi * a
    ir_tab[label] = row
    print(f"  anchor={label:<12}: " + "  ".join(
        f"e2({mu})={row[mu]:.3f}" for mu in row))
# b0=9 systematic
row9 = {}
for mu in [2.01, 0.7, 0.3]:
    a = run_gte(ALPHA_VILLAIN, LAMBDA_GTE, mu, 9.0, 64.0) if mu != LAMBDA_GTE else ALPHA_VILLAIN
    row9[mu] = 4.0 * math.pi * a
print(f"  systematic (b0=9, nf=3 QCD): " + "  ".join(
    f"e2({mu})={row9[mu]:.3f}" for mu in row9))
results["ir_running"] = {"gte_b0_7": ir_tab, "qcd_nf3_b0_9": row9}

verdict = T1 and T2 and T3
print(f"\nVERDICT INPUT: e^2(Lambda_GTE) = 7/2 (Villain, CatAL) physically normalized by "
      f"PDG matching: {'CONSISTENT' if verdict else 'TENSION'}; "
      f"physical bracket e^2(Lambda_GTE) in [{VILLAIN_E2:.2f}, {e2_pdg:.2f}]")
results["verdict"] = {"all_pass": bool(verdict),
                      "e2_bracket_LambdaGTE": [VILLAIN_E2, e2_pdg]}

with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "color_coupling_e_normalization_results.json", "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved color_coupling_e_normalization_results.json")
signal.alarm(0)
