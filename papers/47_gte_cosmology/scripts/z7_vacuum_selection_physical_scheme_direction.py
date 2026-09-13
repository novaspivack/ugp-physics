#!/usr/bin/env python3
"""Vacuum-selection direction in the physical (decoupling) scheme.

Canonical Task-2 computation for the Z7 vacuum-selection sector. The companion
script z7_vacuum_selection_one_loop_direction.py documents the fixed-mu
large-log scheme artifacts; THIS script evaluates the one-loop effective
potential difference between vacua in the decoupling scheme (each species'
Coleman-Weinberg term renormalized at mu_i = its reference-vacuum mass, the
large-log-free choice), with scheme band mu_i in {m_i/2, m_i, 2 m_i}, over the
physical coupling window of the GTE color EFT:

    e (gauge)  in [0.2, 2.5]   (CatAL candidate e^2 = g_c^2 = 7/2 -> e = 1.871)
    g (chi)    in [0.2, 2.5]   (chi is an EFT field below Lambda_GTE ~ 2 GeV)

Spectrum per vacuum k: 3 dof vector m_A = e sqrt(Z_k), 1 dof scalar
m_chi = g/sqrt(Z_k); Z_k literal = 1 + 2 eps phi_k^2 and compact completion
Z_k = 1 + 4 eps (1 - cos phi_k); T_G in {0.6999, 1.2435} GeV (f-conventions);
daisy variant adds Pi = e^2 T^2/3 to the longitudinal mode.

Analytic anchors (proved in session, encoded as assertions):
  scalar channel step inward in decoupling scheme: G(r) = 3/2 - (2 ln r + 3/2)/r^2 > 0
  vector channel step: F(r) = r^2(ln r - 5/6) + 5/6 > 0 iff r > 1.81 (0->1 step
  has r = 2.25 literal / 2.17 compact: inward).

Deliverables: per-step direction table, Delta V(0->1), global argmin over
k = 0..6 (and 0..50 literal runaway re-probe), fraction of the physical window
that is inward, and the verdict input for OQ-088-R03a.

Expected: inward (k* = 0) at 100% of the physical window across all scheme
band choices, both readings, both f-conventions, daisy on/off.
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

EPS = 7.0 / 9.0
SQ72 = math.sqrt(3.5)

def Zk(k, reading):
    p = 2.0 * math.pi * k / 7.0
    if reading == "literal":
        return 1.0 + 2.0 * EPS * p * p
    return 1.0 + 4.0 * EPS * (1.0 - math.cos(p))

def J_B(y2, n=4000, xmax=40.0):
    h = xmax / n
    tot = 0.0
    for i in range(1, n + 1):
        x = i * h
        w = 1.0 if i < n else 0.5
        en = math.sqrt(x * x + y2)
        if en < 700:
            tot += w * x * x * math.log1p(-math.exp(-en))
    return tot * h

def F_T(m, T):
    return T ** 4 / (2.0 * math.pi ** 2) * J_B((m / T) ** 2)

def cw_vec(m, mu):
    return 3.0 * m ** 4 * (math.log(m * m / (mu * mu)) - 5.0 / 6.0) / (64.0 * math.pi ** 2)

def cw_sc(m, mu):
    return m ** 4 * (math.log(m * m / (mu * mu)) - 1.5) / (64.0 * math.pi ** 2)

def dV(k1, k0, e, g, T, reading, mu_fac, daisy):
    """V_eff(k1) - V_eff(k0), decoupling scheme: mu_i = mu_fac * m_i(k0)."""
    Z0, Z1 = Zk(k0, reading), Zk(k1, reading)
    mA0, mA1 = e * math.sqrt(Z0), e * math.sqrt(Z1)
    mc0, mc1 = g / math.sqrt(Z0), g / math.sqrt(Z1)
    muA, muc = mu_fac * mA0, mu_fac * mc0
    d = (cw_vec(mA1, muA) - cw_vec(mA0, muA)) + (cw_sc(mc1, muc) - cw_sc(mc0, muc))
    if T > 0:
        if daisy:
            mL0 = math.sqrt(mA0 ** 2 + e * e * T * T / 3.0)
            mL1 = math.sqrt(mA1 ** 2 + e * e * T * T / 3.0)
            d += 2.0 * (F_T(mA1, T) - F_T(mA0, T)) + (F_T(mL1, T) - F_T(mL0, T))
        else:
            d += 3.0 * (F_T(mA1, T) - F_T(mA0, T))
        d += F_T(mc1, T) - F_T(mc0, T)
    return d

# --- analytic anchors ---
G = lambda r: 1.5 - (2.0 * math.log(r) + 1.5) / (r * r)
F = lambda r: r * r * (math.log(r) - 5.0 / 6.0) + 5.0 / 6.0
assert all(G(1.0 + 0.01 * i) > 0 for i in range(1, 600)), "scalar anchor fails"
r01_lit = Zk(1, "literal") / Zk(0, "literal")
r01_cmp = Zk(1, "compact") / Zk(0, "compact")
assert F(r01_lit) > 0 and F(r01_cmp) > 0, "vector 0->1 anchor fails"
print(f"Analytic anchors: G(r)>0 for r in (1,7]; F(r01) lit/cmp = "
      f"{F(r01_lit):+.3f}/{F(r01_cmp):+.3f} (>0: 0->1 vector CW inward)")

results = {"anchors": {"F_r01_literal": F(r01_lit), "F_r01_compact": F(r01_cmp)}}

print("\n=== 1. Canonical points: per-step table and global argmin ===")
canon = {}
for reading in ["literal", "compact"]:
    for TG, fconv in [(0.6999, "f=1GeV"), (1.2435, "f=m_phi")]:
        for name, e, g in [("R03-central", 0.5, 2.0), ("Sylow-Villain", SQ72, SQ72)]:
            v = [0.0]
            for k in range(1, 7):
                v.append(v[-1] + dV(k, k - 1, e, g, TG, reading, 1.0, False))
            kmin = v.index(min(v))
            d1 = v[1]
            canon[f"{reading}:{fconv}:{name}"] = {
                "V_rel": v, "argmin": kmin, "dV01_GeV4": d1}
            print(f"  {reading:<8} {fconv:<8} {name:<14}: dV(0->1) = {d1:+.3e} "
                  f"GeV^4, argmin k = {kmin}, V_rel = "
                  f"{[f'{x:+.2e}' for x in v[:4]]}...")
results["canonical"] = canon

print("\n=== 2. Physical-window scan: inward fraction ===")
grid = [0.2, 0.35, 0.5, 0.75, 1.0, 1.3, 1.6, 1.871, 2.2, 2.5]
n_tot, n_in, worst = 0, 0, None
outward_pts = []
for reading in ["literal", "compact"]:
    for TG in [0.6999, 1.2435]:
        for mu_fac in [0.5, 1.0, 2.0]:
            for daisy in [False, True]:
                for e in grid:
                    for g in grid:
                        n_tot += 1
                        v = [0.0]
                        for k in range(1, 7):
                            v.append(v[-1] + dV(k, k - 1, e, g, TG,
                                                reading, mu_fac, daisy))
                        ok = (v.index(min(v)) == 0) and v[1] > 0
                        if ok:
                            n_in += 1
                        else:
                            outward_pts.append(
                                {"reading": reading, "T_G": TG, "mu_fac": mu_fac,
                                 "daisy": daisy, "e": e, "g": g,
                                 "argmin": v.index(min(v)), "dV01": v[1]})
                        if worst is None or v[1] < worst[0]:
                            worst = (v[1], reading, TG, mu_fac, daisy, e, g)
print(f"  configurations tested: {n_tot}; inward (k*=0): {n_in} "
      f"({100.0*n_in/n_tot:.2f}%)")
print(f"  worst dV(0->1) = {worst[0]:+.3e} GeV^4 at reading={worst[1]}, "
      f"T_G={worst[2]}, mu_fac={worst[3]}, daisy={worst[4]}, e={worst[5]}, "
      f"g={worst[6]}")
if outward_pts:
    print(f"  OUTWARD configurations ({len(outward_pts)}):")
    for o in outward_pts[:10]:
        print(f"    {o}")
results["window_scan"] = {"n_total": n_tot, "n_inward": n_in,
                          "outward": outward_pts[:50],
                          "worst_dV01": {"value": worst[0],
                                         "config": worst[1:]}}

print("\n=== 3. Runaway re-probe in the physical scheme (literal, k<=50) ===")
run = {}
for name, e, g in [("R03-central", 0.5, 2.0), ("Sylow-Villain", SQ72, SQ72)]:
    for T in [0.6999, 0.2, 0.0]:
        v = [0.0]
        for k in range(1, 51):
            v.append(v[-1] + dV(k, k - 1, e, g, T, "literal", 1.0, False))
        kmin = v.index(min(v))
        run[f"{name},T={T}"] = {"argmin": kmin, "V50": v[50]}
        print(f"  {name:<14} T={T:5.3f}: argmin(k<=50) = {kmin}, "
              f"V(50)-V(0) = {v[50]:+.3e} GeV^4")
results["runaway"] = run

all_inward = (n_in == n_tot) and all(c["argmin"] == 0 for c in canon.values()) \
    and all(r["argmin"] == 0 for r in run.values())
print(f"\nDIRECTION VERDICT INPUT (physical scheme, physical window): "
      f"k* = 0 everywhere = {all_inward}")
results["k0_everywhere_physical_window"] = all_inward

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "z7_vacuum_selection_physical_scheme_direction_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved z7_vacuum_selection_physical_scheme_direction_results.json")
signal.alarm(0)
