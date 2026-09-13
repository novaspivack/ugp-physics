#!/usr/bin/env python3
"""Canonical-code sanity check for the kink form-factor measurement.

Imports the canonical CMCA implementations directly (P45 three_tape_cmca.py,
P41 two_layer_chiral_afca_prototype.py) and reproduces five published anchors:

  A1  p(L,C,R) = C+R-CR-LCR mod 7 restricted to {0,1}^3 equals Rule 110 (8/8)
      [Lean: rule110_z7_poly_rep, CatAL]
  A2  GEN1 = (1,5,2,2,1) -> GEN2 -> GEN3 -> VACUUM in exactly 3 f_MDL steps
      [Lean: fmdl_gen1_to_gen2, CatAL]
  A3  Z7 PSC kink orbits = 45; Z5 PSC kink orbits = 0
      [Lean: z5_fmdl_no_psc_kink_orbits, CatAL]
  A4  P42 BPS kink: M_kink = 8 m_phi/49 = 290.10 MeV; pointwise BPS identity
      (1/2)(Phi')^2 = V(Phi_kink) to machine precision
  A5  PT identity: m_eff^2(x) = m_phi^2 [1 - 2 sech^2(m_phi x)] exactly
      [Lean: phimdl_fluctuation_is_poschl_teller, CatAL]

All five must match the published values exactly before any new simulation
is written (understand-code-before-using rule).
"""
import json
import signal
import sys

sys.path.insert(0, "/Users/nova/ugp-physics/papers/45_three_tape_cmca/scripts")
sys.path.insert(0, "/Users/nova/ugp-physics/papers/41_three_layer_chiral_minkowski_ca/scripts")

TIMEOUT_SECONDS = 600


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

import numpy as np

import three_tape_cmca as ttc                      # canonical P45
import two_layer_chiral_afca_prototype as p41      # canonical P41 (arms its own alarm)

signal.signal(signal.SIGALRM, _timeout)            # re-arm ours after p41 import
signal.alarm(TIMEOUT_SECONDS)

results = {}

# A1 — polynomial = Rule 110 on binary (canonical P45 function)
a1 = ttc.verify_polynomial_equals_rule110_on_binary()
print(f"A1 poly|binary = Rule110: {a1['status']} ({a1['checks']} checks, "
      f"{len(a1['failures'])} failures)")
results["A1"] = {"status": a1["status"], "failures": a1["failures"]}
assert a1["status"] == "PASS"

# A2 — GEN orbit (canonical P41 f_MDL)
g1 = p41.GEN1
g2 = p41.fmdl_step5(g1)
g3 = p41.fmdl_step5(g2)
g4 = p41.fmdl_step5(g3)
print(f"A2 GEN orbit: {g1} -> {g2} -> {g3} -> {g4}")
ok2 = (g2 == p41.GEN2 and g3 == p41.GEN3 and g4 == (0, 0, 0, 0, 0))
results["A2"] = {"gen1": g1, "gen2": g2, "gen3": g3, "vac": g4, "pass": ok2}
assert ok2, "GEN orbit failed"
print("   PASS (GEN1->GEN2->GEN3->VACUUM in 3 steps)")

# A3 — Z7 kink orbit count 45, Z5 count 0 (canonical P45 function)
a3 = ttc.verify_z7_kink_orbit_existence_and_z5_absence()
print(f"A3 Z7 kink orbits = {a3['z7_kink_orbit_count']} (expect 45); "
      f"Z5 = {a3['z5_kink_orbit_count']} (expect 0): {a3['status']}")
results["A3"] = {"z7": a3["z7_kink_orbit_count"], "z5": a3["z5_kink_orbit_count"],
                 "status": a3["status"]}
assert a3["z7_kink_orbit_count"] == 45 and a3["z5_kink_orbit_count"] == 0

# A4 — P42 BPS kink mass and pointwise BPS identity (canonical formulas)
m = 1.77686  # GeV
M_kink = 8 * m / 49
x = np.linspace(-25 / m, 25 / m, 400001)  # box must hold the sech e^{-m|x|} tail for <x^2>
Phi = (4.0 / 7.0) * np.arctan(np.exp(m * x))
dPhi = (2 * m / 7) / np.cosh(m * x)
V = (m ** 2 / 49.0) * (1 - np.cos(7 * Phi))
bps_err = float(np.max(np.abs(0.5 * dPhi ** 2 - V)))
E = float(np.trapz(0.5 * dPhi ** 2 + V, x))
rel = abs(E - M_kink) / M_kink
print(f"A4 BPS: max|KE-V| = {bps_err:.2e}; M = {E*1000:.4f} MeV "
      f"(analytic {M_kink*1000:.4f}); rel err {rel:.2e}")
results["A4"] = {"bps_pointwise_err": bps_err, "M_numeric_MeV": E * 1000,
                 "M_analytic_MeV": M_kink * 1000, "rel_err": rel}
assert bps_err < 1e-12 and rel < 1e-6

# A5 — PT identity
m2_direct = m ** 2 * np.cos(7 * Phi)
m2_pt = m ** 2 * (1 - 2 / np.cosh(m * x) ** 2)
pt_err = float(np.max(np.abs(m2_direct - m2_pt)))
print(f"A5 PT identity: max err = {pt_err:.2e}")
results["A5"] = {"pt_identity_err": pt_err}
assert pt_err < 1e-12

# Classical charge-density second moments (the reference values for Task 2)
PB = dPhi ** 2 / np.trapz(dPhi ** 2, x)          # Born density (sech^2)
PT_ = dPhi / np.trapz(dPhi, x)                   # topological density (sech)
x2_born = float(np.trapz(x ** 2 * PB, x)) * m ** 2
x2_top = float(np.trapz(x ** 2 * PT_, x)) * m ** 2
print(f"Classical <x^2> m^2: Born = {x2_born:.6f} (pi^2/12 = {np.pi**2/12:.6f}); "
      f"topological = {x2_top:.6f} (pi^2/4 = {np.pi**2/4:.6f})")
results["classical_moments"] = {
    "x2m2_born": x2_born, "pi2_over_12": np.pi ** 2 / 12,
    "x2m2_top": x2_top, "pi2_over_4": np.pi ** 2 / 4}
assert abs(x2_born - np.pi ** 2 / 12) < 1e-6
assert abs(x2_top - np.pi ** 2 / 4) < 1e-4

results["all_pass"] = True
out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_form_factor_canonical_sanity_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1, default=str)
print(f"\nALL FIVE ANCHORS PASS. Saved {out.split('/')[-1]}")
signal.alarm(0)
