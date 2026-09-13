#!/usr/bin/env python3
"""Kink vacuum-polarization constant in the Villain<->MSbar definitional matching.

Computes c_kink = 16pi^2 [Pi_MSbar(0; mu=Lambda_GTE) - Pi_def(0)] for the
F21 EFT, where the kink species enter as six Dirac flavors in the SU(3)
fundamental restricted to the Cartan H_A = (-T3 + sqrt(3) T8)/2 (Sigma q^2 = 3,
abelian beta coefficient -4 = the CatAL b0-continuity value 7 - 11).

Substrate UV definitions (gauge-invariant scheme family, pre-registered):
  S1  Pauli-Villars at Lambda_PV = m_phi          (PRIMARY: PT-threshold dissolution)
  S2  Pauli-Villars at Lambda_PV = 1/r_RMS
  S3  smooth-exponential proper time, sqrt(s0) = 1/m_phi
  S4  smooth-exponential proper time, sqrt(s0) = r_RMS
  S5  sharp proper time, sqrt(s0) = 1/m_phi
  S6  sharp proper time, sqrt(s0) = r_RMS
with r_RMS = pi/(2 sqrt(3) m_phi) the exact RMS radius of the CatAL sech^2
kink charge density. Two Lambda_GTE readings (088-R12 derived band):
  tree: Lambda = (8/7) m_tau, M = M_cl = (8/49) m_tau
  pole: Lambda = 7 M^Q,      M = M^Q = 321.32 MeV

Verification battery: exact one-loop Dirac VP closed form vs proper-time rep;
running slope 8/3 per unit charge^2; E1 implementation vs quadrature;
IR-mass-cancellation lemma; x-integral = 1/6; MSbar-vs-MSbar null = 0.

Expected output range: c_kink in roughly [+1, +4.5] across the family.
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

# ------------------------------------------------------------------ inputs
M_TAU = 1776.86            # MeV, PDG 2024 (CANONICAL_COMPARISON_DATA.md)
M_CL = 8.0 / 49.0 * M_TAU  # = 290.102 MeV, CatAL BPS kink mass
M_Q = 321.32               # MeV, P42 one-loop quantum kink mass (CatA)
M_PHI = M_TAU              # SCC field mass
LAM_TREE = 8.0 / 7.0 * M_TAU   # = 2030.70 MeV (088-R12 tree reading, CatAD)
LAM_POLE = 7.0 * M_Q           # = 2249.24 MeV (088-R12 pole reading, CatA)
R_RMS = math.pi / (2.0 * math.sqrt(3.0))   # in units of 1/m_phi (exact)

results = {"inputs": {"m_tau": M_TAU, "M_cl": M_CL, "M_Q": M_Q,
                      "lam_tree": LAM_TREE, "lam_pole": LAM_POLE,
                      "r_rms_times_mphi": R_RMS}}

# ---------------------------------------------------- E1 (exponential integral)
def expint_e1(x):
    """E1(x) = Gamma(0, x), x > 0. Series for x<=1, continued fraction x>1."""
    if x <= 0:
        raise ValueError("E1 needs x>0")
    if x <= 1.0:
        s, term, k = 0.0, 1.0, 0
        while True:
            k += 1
            term *= -x / k
            add = term / k
            s += add
            if abs(add) < 1e-18 * max(1.0, abs(s)):
                break
        return -EULER_GAMMA - math.log(x) - s
    # Lentz continued fraction for E1
    b = x + 1.0
    c = 1e300
    d = 1.0 / b
    h = d
    for i in range(1, 200):
        a = -i * i
        b += 2.0
        d = 1.0 / (a * d + b)
        c = b + a / c
        delta = c * d
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return h * math.exp(-x)


# battery: E1 vs direct quadrature at x = 0.03, 0.5, 2
def e1_quad(x, n=400000):
    # log substitution t = x e^u: integral exp(-x e^u) du, u in [0, ln(80/x)]
    b = math.log(80.0 / x)
    h = b / n
    s = 0.5 * (math.exp(-x) + math.exp(-80.0))
    for i in range(1, n):
        s += math.exp(-x * math.exp(i * h))
    return s * h


battery = {}
for x in (0.03, 0.5, 2.0):
    err = abs(expint_e1(x) - e1_quad(x)) / expint_e1(x)
    battery[f"E1({x})_rel_err"] = err
    assert err < 1e-9, f"E1 battery fail at {x}: {err}"
print("battery: E1 vs quadrature OK "
      f"(max rel err {max(battery.values()):.1e})")

# x-integral check: int_0^1 x(1-x) dx = 1/6
n = 200000
s = sum(((i + 0.5) / n) * (1 - (i + 0.5) / n) for i in range(n)) / n
battery["x_integral_vs_1_6"] = abs(s - 1.0 / 6.0)
assert abs(s - 1.0 / 6.0) < 1e-9
print(f"battery: int x(1-x) = {s:.12f} (1/6 OK)")

# ------------------------------------------------------- per-unit-q^2 pieces
# 16pi^2 * Pi at Q^2=0, per unit charge^2, one Dirac fermion of mass M:
#   MSbar(mu):        (8/3) ln(mu/M)
#   sharp PT(s0):     (4/3) Gamma(0, M^2 s0)
#   smooth-exp(s0):   (4/3) ln(1 + 1/(M^2 s0))
#   PV(Lpv):          (8/3) ln(Lpv/M)
def pi_msbar(mu, M):
    return (8.0 / 3.0) * math.log(mu / M)


def pi_sharp(s0, M):
    return (4.0 / 3.0) * expint_e1(M * M * s0)


def pi_smooth(s0, M):
    return (4.0 / 3.0) * math.log(1.0 + 1.0 / (M * M * s0))


def pi_pv(lpv, M):
    return (8.0 / 3.0) * math.log(lpv / M)


# battery: proper-time rep with s0->0 must reproduce the MSbar Q^2-dependence
# of the exact one-loop VP (closed form via Feynman parameter):
#   16pi^2 Pi_MSbar(Q^2; mu) = (8/3) int dx 6 x(1-x) * (1/2) ln(mu^2/(M^2+x(1-x)Q^2))
# while sharp-PT gives (8/3) int dx 6x(1-x) (1/2) Gamma(0, s0*(M^2+x(1-x)Q^2)).
# Their difference must be Q^2-INDEPENDENT (= the scheme constant) as s0->0.
def pi_sharp_q2(s0, M, q2, nx=4000):
    tot = 0.0
    for i in range(nx):
        x = (i + 0.5) / nx
        w = x * (1.0 - x)
        tot += w * expint_e1(s0 * (M * M + w * q2))
    return (8.0 / 3.0) * 3.0 * tot / nx  # 6*(1/2)=3 normalization


def pi_msbar_q2(mu, M, q2, nx=4000):
    tot = 0.0
    for i in range(nx):
        x = (i + 0.5) / nx
        w = x * (1.0 - x)
        tot += w * 0.5 * math.log(mu * mu / (M * M + w * q2))
    return (8.0 / 3.0) * 6.0 * tot / nx


s0_test = 1e-8
diffs = []
for q2 in (0.0, 0.25, 1.0, 4.0):
    d = pi_sharp_q2(s0_test, 1.0, q2) - pi_msbar_q2(2.0, 1.0, q2)
    diffs.append(d)
spread = max(diffs) - min(diffs)
battery["q2_independence_spread"] = spread
assert spread < 1e-5, f"scheme constant not Q^2-independent: {spread}"
# the constant itself must equal (8/3)[ln(1/(mu*sqrt(s0))) - gamma/2]
pred_const = (8.0 / 3.0) * (math.log(1.0 / (2.0 * math.sqrt(s0_test)))
                            - EULER_GAMMA / 2.0)
battery["sharp_vs_msbar_const_err"] = abs(diffs[0] - pred_const)
assert abs(diffs[0] - pred_const) < 1e-5
print(f"battery: sharp-PT vs MSbar difference Q^2-independent "
      f"(spread {spread:.1e}), constant matches analytic prediction "
      f"(err {abs(diffs[0]-pred_const):.1e})")

# battery: running slope per unit q^2 = 8/3 per ln mu
slope = (pi_msbar(math.e, 1.0) - pi_msbar(1.0, 1.0))
battery["msbar_slope_minus_8_3"] = abs(slope - 8.0 / 3.0)
assert abs(slope - 8.0 / 3.0) < 1e-12
print("battery: MSbar slope 8/3 per ln mu OK")

# -------------------------------------------- Cartan weights and species sum
# H_A = (-T3 + sqrt(3) T8)/2 with T3 = diag(1,-1,0)/2, T8 = diag(1,1,-2)/(2 sqrt 3)
T3 = [0.5, -0.5, 0.0]
T8 = [1.0 / (2 * math.sqrt(3)), 1.0 / (2 * math.sqrt(3)), -1.0 / math.sqrt(3)]
HA = [(-t3 + math.sqrt(3) * t8) / 2.0 for t3, t8 in zip(T3, T8)]
sum_q2_per_flavor = sum(h * h for h in HA)
T_KINK = 6.0 * sum_q2_per_flavor
B_KINK = -(4.0 / 3.0) * T_KINK
print(f"\nCartan weights on the fundamental: {[round(h,6) for h in HA]}")
print(f"Sigma q^2 per flavor = {sum_q2_per_flavor:.12f} (expect 1/2); "
      f"t_kink = {T_KINK:.12f} (expect 3); b_kink = {B_KINK:.6f} (expect -4 "
      f"= 7 - 11 CatAL continuity)")
assert abs(sum_q2_per_flavor - 0.5) < 1e-14 and abs(T_KINK - 3.0) < 1e-13
results["species"] = {"HA_weights": HA, "t_kink": T_KINK, "b_kink": B_KINK}

# ------------------------------------------------------------ scheme family
def c_kink(scheme, lam, M, m_phi):
    """16pi^2 [Pi_MSbar(0;mu=lam) - Pi_def(0)] * Sigma q^2 (=3)."""
    base = pi_msbar(lam, M)
    if scheme == "S1_PV_mphi":
        d = pi_pv(m_phi, M)
    elif scheme == "S2_PV_invrms":
        d = pi_pv(m_phi / R_RMS, M)
    elif scheme == "S3_smooth_mphi":
        d = pi_smooth(1.0 / m_phi ** 2, M)
    elif scheme == "S4_smooth_rms":
        d = pi_smooth((R_RMS / m_phi) ** 2, M)
    elif scheme == "S5_sharp_mphi":
        d = pi_sharp(1.0 / m_phi ** 2, M)
    elif scheme == "S6_sharp_rms":
        d = pi_sharp((R_RMS / m_phi) ** 2, M)
    elif scheme == "C_msbar_null":
        d = pi_msbar(lam, M)
    else:
        raise ValueError(scheme)
    return T_KINK * (base - d)


READINGS = {
    "tree": {"lam": LAM_TREE, "M": M_CL},
    "pole": {"lam": LAM_POLE, "M": M_Q},
}
SCHEMES = ["S1_PV_mphi", "S2_PV_invrms", "S3_smooth_mphi", "S4_smooth_rms",
           "S5_sharp_mphi", "S6_sharp_rms", "C_msbar_null"]

print("\n=== c_kink scheme family (16pi^2 dictionary units) ===")
results["c_kink"] = {}
for rname, r in READINGS.items():
    results["c_kink"][rname] = {}
    print(f"  reading {rname}: Lambda = {r['lam']:.2f} MeV, M = {r['M']:.2f} MeV")
    for s in SCHEMES:
        c = c_kink(s, r["lam"], r["M"], M_PHI)
        results["c_kink"][rname][s] = c
        print(f"    {s:16s}: c_kink = {c:+.4f}")

# exact-rational-form check for the tree-reading primary scheme
c_s1_tree_exact = 8.0 * math.log(8.0 / 7.0)
err = abs(results["c_kink"]["tree"]["S1_PV_mphi"] - c_s1_tree_exact)
battery["S1_tree_exact_8ln8over7"] = err
assert err < 1e-10
print(f"\nS1 tree reading = 8 ln(8/7) = {c_s1_tree_exact:.6f} exactly "
      f"(Lambda/m_phi = 8/7 from the SCC chain)")

# MSbar-vs-MSbar null
for rname in READINGS:
    assert abs(results["c_kink"][rname]["C_msbar_null"]) < 1e-12
print("Route C null: MSbar-vs-MSbar c = 0 exactly OK")

# ------------------------------------- IR-mass-cancellation lemma (L1) check
print("\n=== L1: IR-mass insensitivity (M varied +/-20%, scheme S5 tree) ===")
base = c_kink("S5_sharp_mphi", LAM_TREE, M_CL, M_PHI)
lemma = {}
for fac in (0.8, 1.2):
    c = c_kink("S5_sharp_mphi", LAM_TREE, M_CL * fac, M_PHI)
    lemma[f"M_x{fac}"] = c - base
    print(f"  M x {fac}: c shifts by {c-base:+.4f} "
          f"(pure-log part cancels; residual = exact-E1 x-correction)")
results["L1_mass_shift"] = lemma
# PV scheme: M must cancel EXACTLY
for fac in (0.5, 2.0):
    d = c_kink("S1_PV_mphi", LAM_TREE, M_CL * fac, M_PHI) - \
        c_kink("S1_PV_mphi", LAM_TREE, M_CL, M_PHI)
    assert abs(d) < 1e-12
print("  PV scheme: exact M-cancellation verified (shifts < 1e-12)")

# ------------------------------------------------- L2 sign criterion check
crit = M_PHI < math.exp(EULER_GAMMA / 2.0) * LAM_TREE
print(f"\nL2 sign criterion: m_phi = {M_PHI:.1f} < e^(gamma/2) Lambda_tree "
      f"= {math.exp(EULER_GAMMA/2)*LAM_TREE:.1f} -> c_kink > 0 "
      f"({'holds' if crit else 'FAILS'}) for every dissolution scale <= m_phi")
results["L2_sign_positive"] = crit
results["battery"] = battery

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "kink_vacuum_polarization_matching_constant_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
