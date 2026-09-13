#!/usr/bin/env python3
"""Charged-channel (Omnes-constrained) kink dissolution constant (088-R11a).

Constructs the timelike kink form factor F(s) on the Cartan current channel
from corpus-exact objects:
  - elastic region [4M^2, (2M+m_phi)^2]: Watson's theorem with the EXACT
    ZZ kink-antikink phase  delta(theta) = -arctan(1/sinh theta)
    (S(theta) = (sinh-i)/(sinh+i), CatAD, pole-free: no breathers at B=1),
    via the Omnes representation, F(0) = 1 (charge normalization);
  - inelastic dissolution onset s_inel = (2M + m_phi)^2 (one-kink
    Poschl-Teller continuum threshold in the pair channel, CatAL-anchored);
  - decay above onset: pre-registered bracket
      D1 exp[-(rt_s - rt_onset) * pi/(2 m_phi)]  (sech^2-FT crossing scale)
      D2 exp[-(rt_s - rt_onset) / m_phi]
      D3 (s_inel/s)
      D4 (s_inel/s)^2.
Then  g(s) = (|Omega(s)| D(s))^2  and
  c = 8 ln(Lambda/M) - 3 int (ds/s) K(s) g(s),
  Lambda_diss = Lambda exp(-c/8).

Verification: Omnes threshold exponent |F| ~ beta^(-2 delta_thr/pi) = beta^1
(from delta_thr = -pi/2); PV bookkeeping reproduced (script 1);
grid-doubling convergence.

Expected: c in roughly [-2, +1] per reading; no bracket member reaches the
tree-rescue region c >= +3.1 (pre-registered prediction P3).
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 600


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

M_TAU = 1776.86
M_PHI = M_TAU
READINGS = {"tree": {"lam": 8.0 / 7.0 * M_TAU, "M": 8.0 / 49.0 * M_TAU},
            "pole": {"lam": 7.0 * 321.32, "M": 321.32}}

results = {}


def delta_zz(theta):
    """Exact ZZ kink-antikink phase shift, delta(0+) = -pi/2, delta(inf) = 0."""
    if theta <= 0.0:
        return -math.pi / 2.0
    return -math.atan(1.0 / math.sinh(theta))


def kernel(s, M):
    if s <= 4.0 * M * M:
        return 0.0
    beta = math.sqrt(1.0 - 4.0 * M * M / s)
    return (4.0 / 3.0) * (1.0 + 2.0 * M * M / s) * beta


def ln_omega(s, M, n=6000, theta_max=40.0):
    """ln|Omega(s)| = (s/pi) PV int delta(s')/(s'(s'-s)) ds', s on the cut.

    PV handled by subtracting delta(s) and adding the analytic remainder
    PV int_{s_th}^inf ds'/(s'(s'-s)) = -(1/s) ln((s-s_th)/s_th).
    """
    s_th = 4.0 * M * M
    ds = delta_zz(2.0 * math.acosh(math.sqrt(s / s_th))) if s > s_th else delta_zz(0.0)
    h = theta_max / n
    tot = 0.0
    for i in range(n):
        th = (i + 0.5) * h
        sp = s_th * math.cosh(th / 2.0) ** 2
        w = math.tanh(th / 2.0) * sp          # ds' = w dtheta / ... : ds' = sp tanh dtheta
        dpr = delta_zz(th)
        tot += (dpr - ds) / (sp * (sp - s)) * sp * math.tanh(th / 2.0) * h
    pv_rem = -(1.0 / s) * math.log((s - s_th) / s_th) if s > s_th else \
        (1.0 / s) * math.log(s_th / (s_th - s))
    return (s / math.pi) * (tot + ds * pv_rem)


# --- battery: threshold exponent |F| ~ beta^(1/2)
M = READINGS["tree"]["M"]
s_th = 4.0 * M * M
exps = []
for eps in (1e-3, 1e-4):
    b1 = math.sqrt(1.0 - s_th / (s_th * (1 + eps)))
    b2 = math.sqrt(1.0 - s_th / (s_th * (1 + eps / 4)))
    l1 = ln_omega(s_th * (1 + eps), M)
    l2 = ln_omega(s_th * (1 + eps / 4), M)
    exps.append((l1 - l2) / (math.log(b1) - math.log(b2)))
print(f"battery: Omnes threshold exponent = {exps} "
      f"(theory -2 delta_thr/pi = +1)")
results["threshold_exponent"] = exps
assert abs(exps[-1] - 1.0) < 0.05, "threshold exponent check failed"

# --- battery: Omnes spacelike normalization Omega(0) = 1 by construction;
# check |Omega| at large s approaches a constant (delta -> 0)
lo_hi = [ln_omega(s_th * x, M) for x in (1e2, 1e4, 1e6)]
print(f"battery: ln|Omega| at s/s_th = 1e2,1e4,1e6: "
      f"{[f'{v:.4f}' for v in lo_hi]} (must flatten)")
results["ln_omega_large_s"] = lo_hi
assert abs(lo_hi[2] - lo_hi[1]) < abs(lo_hi[1] - lo_hi[0]), "no flattening"


def compute_c(rname, decay, n=4000, theta_max=24.0):
    r = READINGS[rname]
    lam, M = r["lam"], r["M"]
    s_inel = (2.0 * M + M_PHI) ** 2
    rt_onset = 2.0 * M + M_PHI
    lam_dec_d1 = 2.0 * M_PHI / math.pi
    h = theta_max / n
    tot = 0.0
    for i in range(n):
        th = (i + 0.5) * h
        s = 4.0 * M * M * math.cosh(th / 2.0) ** 2
        om2 = math.exp(2.0 * ln_omega(s, M, n=1500))
        rt = math.sqrt(s)
        if rt <= rt_onset:
            d = 1.0
        elif decay == "D1":
            d = math.exp(-(rt - rt_onset) / lam_dec_d1)
        elif decay == "D2":
            d = math.exp(-(rt - rt_onset) / M_PHI)
        elif decay == "D3":
            d = s_inel / s
        elif decay == "D4":
            d = (s_inel / s) ** 2
        else:
            raise ValueError(decay)
        g = om2 * d * d
        tot += math.tanh(th / 2.0) * kernel(s, M) * g * h
    c = 8.0 * math.log(lam / M) - 3.0 * tot
    return c, lam * math.exp(-c / 8.0)


print("\n=== Omnes-constrained constant, decay bracket ===")
results["constrained"] = {}
for rname in READINGS:
    results["constrained"][rname] = {}
    for decay in ("D1", "D2", "D3", "D4"):
        c, ldiss = compute_c(rname, decay)
        # convergence: half resolution
        c2, _ = compute_c(rname, decay, n=2000, theta_max=24.0)
        conv = abs(c - c2)
        results["constrained"][rname][decay] = {
            "c": c, "lambda_diss_MeV": ldiss,
            "lambda_diss_over_mphi": ldiss / M_PHI, "conv": conv}
        print(f"  {rname} {decay}: c = {c:+.4f} (conv {conv:.1e}); "
              f"Lambda_diss = {ldiss:7.1f} MeV = {ldiss/M_PHI:.4f} m_phi")

# band summary + P3 adjudication
print("\n=== band summary ===")
results["band"] = {}
for rname in READINGS:
    vals = [results["constrained"][rname][d]["c"] for d in ("D1", "D2", "D3", "D4")]
    band = (min(vals), max(vals))
    results["band"][rname] = band
    rescue = 3.1
    print(f"  {rname}: c in [{band[0]:+.3f}, {band[1]:+.3f}]; "
          f"reaches tree-rescue (>= +{rescue})? "
          f"{'YES' if band[1] >= rescue else 'NO (P3 confirmed)' if rname=='tree' else 'NO'}")

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "dissolution_constant_exact_pt_spectral_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
