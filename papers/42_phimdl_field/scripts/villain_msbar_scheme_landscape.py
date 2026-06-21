#!/usr/bin/env python3
"""Scheme landscape for the Villain->MS-bar conversion (088-R09 / OQ-088-R07b).

Computes the finite scheme constant v (defined by g^2_X(mu) = g^2_MSbar(mu) *
(1 + v g^2_MSbar / 16 pi^2), i.e. v = 2 b0t ln(Lambda_X / Lambda_MSbar)) for every
completion of the under-specified "Villain (heat-kernel)" convention, and compares
each against the required corridor from villain_msbar_required_coefficient.py
(v_req = -2.888 central; c_req = +3.330).

Completions:
  BA-A  heat-kernel (Menotti-Onofri / non-abelian Villain) LATTICE action, bare
        coupling at a^{-1} = Lambda_GTE. Uses the first-principles ratio derived and
        verified in villain_msbar_heatkernel_lambda_ratio.py:
        Lambda_HK/Lambda_W = exp(pi^2 (N^2-3)/(11 N^2)) and the Dashen-Gross constant
        (PRD 23 (1981) 2340): Lambda_MSbar/Lambda_W = 38.852704 exp(-3 pi^2/(11 N^2)).
        => Lambda_MSbar/Lambda_HK = 38.852704 exp(-pi^2/11) = 15.840 (N-independent).
        Two nulls: perturbative control at g^2 = 7/2; scale consistency (what bare
        coupling lives at a^{-1} = 2 GeV; what cutoff would carry g^2 = 7/2).
  BA-B  gradient-flow (heat-kernel smearing) scheme: v = +4 pi k1,
        k1 = 1.0978 + 0.0075 Nf (Luscher JHEP 08 (2010) 071, eq. 2.36 -- verified).
  BA-C  proper-time (DeWitt-Schwinger) scheme, sharp cutoff: v = + b0t * gamma_E
        (uniform per-mode Gamma(0,x) constant -- demonstrated numerically below);
        Pauli-Villars / exponential-smearing variants: v = 0.
  comparator: V-scheme (static potential): v = a1 = 31/3 - 10 Nf/9
        (standard one-loop static-potential constant).
  comparator: plain-MS (non-bar): v = -b0t (ln 4pi - gamma_E).

Expected: no completion lands in the corridor v in [-5.0, -0.6] (the fixed-Lambda
band image of c_req in [1.84, 6.08]); BA-A overshoots x20 and fails both nulls;
BA-B/BA-C have the wrong sign.
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

GAMMA_E = 0.5772156649015329
B0T_GTE = 7.0          # 16 pi^2 b0 for the GTE content (Nf = 6), CatAL
B0T_PURE = 11.0        # pure gauge SU(3)
E2_V = 3.5
E2_MS = 3.7583         # 3-loop PDG run-down at 2.01 GeV (required-coefficient script)
V_REQ = -2.888
C_REQ_BAND_FIXED_LAMBDA = (1.843, 6.080)
# corridor in v units at fixed Lambda (v ~ -c * (e2_V/e2_MS)^2 exactly computed below)
results = {"inputs": {"b0t_GTE": B0T_GTE, "e2_MS_at_2p01": E2_MS, "v_req": V_REQ}}

def v_to_pred_e2(v):
    """Predicted Villain-side value from MS-bar side given scheme constant v."""
    return E2_MS * (1 + v * E2_MS / (16 * math.pi ** 2))

def c_from_v(v):
    """Equivalent c in the R07 parametrization g2_MS = g2_V (1 + c g2_V/16pi^2)."""
    e2v = v_to_pred_e2(v)
    return (E2_MS / e2v - 1) * 16 * math.pi ** 2 / e2v

print("=== 0. corridor (from required-coefficient script) ===")
v_corridor = []
for c in C_REQ_BAND_FIXED_LAMBDA:
    # invert: find v such that c_from_v(v) = c
    lo, hi = -80.0, 80.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if c_from_v(mid) < c:
            hi = mid
        else:
            lo = mid
    v_corridor.append((lo + hi) / 2)
v_corridor = sorted(v_corridor)
print(f"  required corridor at fixed central Lambda_GTE: v in "
      f"[{v_corridor[0]:.2f}, {v_corridor[1]:.2f}]  (central {V_REQ:.3f})")
results["v_corridor_fixed_lambda"] = v_corridor

print("\n=== 1. Gamma(0,x) demonstration of the sharp proper-time constant ===")
def gamma0(x, n=400000):
    # Gamma(0,x) = int_x^inf dt/t e^{-t}, log-spaced trapezoid + tail
    import math as m
    t0, t1 = x, max(50.0, 20 * x)
    s = 0.0
    lt0, lt1 = m.log(t0), m.log(t1)
    h = (lt1 - lt0) / n
    prev = m.exp(-t0)
    for i in range(1, n + 1):
        t = m.exp(lt0 + i * h)
        cur = m.exp(-t)
        s += 0.5 * (prev + cur) * h
        prev = cur
    return s
rows = []
for x in (1e-3, 1e-4, 1e-5):
    g = gamma0(x)
    dev = g - (-math.log(x) - GAMMA_E)
    rows.append({"x": x, "Gamma0_minus_asymptote": dev})
    print(f"  x={x:.0e}: Gamma(0,x) - (ln(1/x) - gamma_E) = {dev:.2e}  -> constant is -gamma_E")
results["proper_time_constant_check"] = rows

print("\n=== 2. The landscape ===")
LAM_MS_OVER_HK = 38.852704 * math.exp(-math.pi ** 2 / 11.0)   # N-independent
landscape = {}

# BA-A: heat-kernel lattice at mu = 1/a (pure-gauge dictionary; fermion part unspecified)
v_baa = -2 * B0T_PURE * math.log(LAM_MS_OVER_HK)
landscape["BA-A heat-kernel lattice (pure gauge)"] = v_baa
# BA-B: gradient flow, Nf = 6 and 4
for nf in (4, 6):
    k1 = 1.0978 + 0.0075 * nf
    landscape[f"BA-B gradient flow (Nf={nf})"] = 4 * math.pi * k1
# BA-C: proper time
landscape["BA-C proper time sharp (b0t=7)"] = B0T_GTE * GAMMA_E
landscape["BA-C proper time PV/exp-smeared"] = 0.0
# comparators
for nf in (4, 6):
    landscape[f"V-scheme static potential (Nf={nf})"] = 31.0 / 3.0 - 10.0 * nf / 9.0
landscape["plain MS (non-bar)"] = -B0T_GTE * (math.log(4 * math.pi) - GAMMA_E)

tab = {}
for name, v in landscape.items():
    e2p = v_to_pred_e2(v)
    in_corr = v_corridor[0] <= v <= v_corridor[1]
    ok_sign = (v < 0)
    tab[name] = {"v": v, "pred_e2_V": e2p, "in_corridor": bool(in_corr)}
    print(f"  {name:42s} v = {v:+8.2f}  pred e2_V(2.01) = {e2p:7.3f}"
          f"  {'<<< IN CORRIDOR' if in_corr else ('(sign ok, magnitude off)' if ok_sign else '(wrong sign)')}")
print(f"  {'REQUIRED':42s} v = {V_REQ:+8.2f}  pred e2_V(2.01) = {v_to_pred_e2(V_REQ):7.3f}  = 7/2")
results["landscape"] = tab

print("\n=== 3. BA-A consistency nulls ===")
# perturbative control
c_baa = 2 * B0T_PURE * math.log(LAM_MS_OVER_HK)
print(f"  null 1: c*g^2/16pi^2 = {c_baa * E2_V / (16 * math.pi ** 2):.2f}  (>1 -> series meaningless)")
# scale consistency: 2-loop GTE-content running in the HK scheme.
# Lambda_MS(eff, nf=4-like GTE content) from e2_MS(2.01) = 3.7583 by downward 2-loop integration of 1/g^2
def run_g2_inv(g2_start, mu_start, mu_end, b0t, b1t, nstep=20000):
    """integrate d(1/g^2)/dln mu = 2 b0/16pi^2 + 2 b1/(16pi^2)^2 g^2 ... in 1/g^2."""
    import math as m
    x = 1.0 / g2_start
    t0, t1 = m.log(mu_start), m.log(mu_end)
    h = (t1 - t0) / nstep
    for _ in range(nstep):
        g2 = 1.0 / x
        dx = 2 * b0t / (16 * m.pi ** 2) + 2 * b1t / (16 * m.pi ** 2) ** 2 * g2
        x += h * dx
        if x <= 0:
            return None
    return 1.0 / x

# find Lambda_MS: scale where 1/g^2 -> 0 going down (bisect)
lo, hi = 0.05, 2.0
for _ in range(60):
    mid = math.sqrt(lo * hi)
    g2 = run_g2_inv(E2_MS, 2.01, mid, B0T_GTE, 26.0)
    if g2 is None or g2 < 0 or g2 > 50:
        lo = mid
    else:
        hi = mid
lam_ms_eff = math.sqrt(lo * hi)
lam_hk_eff = lam_ms_eff / LAM_MS_OVER_HK
print(f"  GTE-content effective Lambda_MS = {lam_ms_eff*1000:.0f} MeV -> "
      f"Lambda_HK = {lam_hk_eff*1000:.1f} MeV")
# bare HK coupling at a^{-1} = 2.01 GeV: standard 2-loop asymptotic formula
def g2_two_loop(mu, lam, b0t, b1t):
    L = math.log(mu ** 2 / lam ** 2)
    if L <= 0:
        return None
    return (16 * math.pi ** 2 / (b0t * L)) * (1 - (b1t / b0t ** 2) * math.log(L) / L)
g2_hk_at_2 = g2_two_loop(2.01, lam_hk_eff, B0T_GTE, 26.0)
print(f"  null 2a: g2_HK(a^-1 = 2.01 GeV) = {g2_hk_at_2:.2f}   (claimed: 3.5)")
# cutoff that would carry g2_HK = 3.5 (1-loop, both b0 readings)
for b0t in (B0T_GTE, B0T_PURE):
    mu = lam_hk_eff * math.exp(8 * math.pi ** 2 / (b0t * 3.5))
    print(f"  null 2b: a^-1 with g2_HK = 3.5 (1-loop, b0t={b0t:.0f}): {mu*1000:.0f} MeV  (claimed: 2010 MeV)")
results["ba_a_nulls"] = {"validity_metric": c_baa * E2_V / (16 * math.pi ** 2),
                         "Lambda_MS_eff_GeV": lam_ms_eff,
                         "Lambda_HK_eff_GeV": lam_hk_eff,
                         "g2_HK_at_2GeV": g2_hk_at_2}

print("\n=== 4. rejected-numerology register ===")
print(f"  v_req / (-gamma_E) = {V_REQ / -GAMMA_E:.3f}  (= 5.004: '-N_fam gamma_E' pattern -- "
      f"REJECTED, no mechanism, post-hoc)")
results["rejected_numerology"] = {"v_req_over_minus_gammaE": V_REQ / -GAMMA_E,
                                  "verdict": "rejected at sight (no mechanism)"}

with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "villain_msbar_scheme_landscape_results.json", "w") as fp:
    json.dump(results, fp, indent=1)
print("\nSaved villain_msbar_scheme_landscape_results.json")
signal.alarm(0)
