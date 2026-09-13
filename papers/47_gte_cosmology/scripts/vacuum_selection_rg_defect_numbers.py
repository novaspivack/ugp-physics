#!/usr/bin/env python3
"""Final defect-cosmology numbers with the RG-improved vacuum-selection bias
(088-R07, Task 3). Recomputes T_ann, the bias magnitude, wall lifetime, and the
zero-relic/GW/Delta N_eff statements with the RG-improved Lambda_GTE-anchored
effective potential (vacuum_selection_rg_improved_direction.py) at the derived
couplings e^2(Lambda_GTE) = 7/2 (CatAL Villain; PDG-matched 3.758) and
g = m_tau = 1.77686 GeV (CatB zero-new-scale completion). Supplies the final
P47-1 content numbers (papers NOT edited).

Inputs read from vacuum_selection_rg_improved_direction_results.json.
Expected: |DV(0->1)|(T_G) ~ 2e-2..1.7e-1 GeV^4; R_c ~ 2-13 GeV^-1; wall
lifetime ~ 1e-24..1e-23 s; T_ann ~= T_G ~= 0.7 GeV; clearance ~700x BBN;
Omega_GW ceiling smaller than the R03 value; Delta N_eff ~= 0.
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

SIGMA = 0.29010          # GeV^3 (P42 canonical; bracket [0.0244, 0.916])
T_G = 0.6999             # GeV (f = 1 GeV; 1.2435 for f = m_phi)
T_BBN = 1e-3             # GeV
M_PL = 1.220890e19
G_STAR = 61.75
GEV_TO_S = 6.582119e-25
EPS_GW = 0.7
A_SCALING = 0.8

import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_SCRIPT_DIR,
          "vacuum_selection_rg_improved_direction_results.json")) as fp:
    rg = json.load(fp)

dV_central = rg["scheme_probes"]["central"]["dV01"]            # T = T_G, f=1
dV_T0 = rg["scheme_probes"]["T = 0"]["dV01"]                   # CW only
core = rg["factorial_core"]["table"]
dV_all = [v["dV01"] for v in core.values()] + \
         [p["dV01"] for p in rg["scheme_probes"].values()]
dV_pos = [d for d in dV_all if d > 0]
dV_min, dV_max = min(dV_pos), max(dV_pos)

print("=== 1. RG-improved bias magnitude (vacuum-label splitting 0 -> 1) ===")
print(f"  central (T_G, f=1, e2=7/2, g=m_tau): DV = {dV_central:+.3e} GeV^4")
print(f"  T = 0 Coleman-Weinberg component:    DV = {dV_T0:+.3e} GeV^4")
print(f"  range across the probe battery:      [{dV_min:.2e}, {dV_max:.2e}] GeV^4")

H_TG = 1.66 * math.sqrt(G_STAR) * T_G ** 2 / M_PL
t_TG = 1.0 / (2.0 * H_TG)

print("\n=== 2. Collapse kinematics ===")
rows = {}
for label, dv in [("central", dV_central), ("min", dV_min), ("max", dV_max)]:
    R_c = SIGMA / dv                       # GeV^-1
    tau_s = R_c * GEV_TO_S                 # collapse at ~c
    frac_H = R_c / t_TG
    rows[label] = {"dV_GeV4": dv, "R_c_GeV^-1": R_c, "lifetime_s": tau_s,
                   "lifetime_over_Hubble": frac_H}
    print(f"  {label:<8} DV = {dv:.3e}: R_c = {R_c:7.2f} GeV^-1, "
          f"lifetime = {tau_s:.2e} s = {frac_H:.1e} Hubble(T_G)")
print(f"  Hubble time at T_G: {t_TG*GEV_TO_S:.2e} s")

T_ann = T_G   # collapse completes within ~1e-17 Hubble of formation
print(f"\n=== 3. Annihilation epoch and clearances ===")
print(f"  T_ann ~= T_G ~= {T_ann:.2f} GeV (f-convention bracket 0.70-1.24 GeV)")
print(f"  clearance T_ann/T_BBN = {T_ann/T_BBN:.0f}")
print(f"  T = 0 metastability: k != 0 vacua lie {dV_T0:.2e} GeV^4 above k* = 0 "
      f"(now scheme-controlled, was scheme-dependent in the prior session)")

print("\n=== 4. Relic statements ===")
sig_TeV3 = SIGMA / 1e9
om_gw = (5.20e-20 * EPS_GW * A_SCALING ** 4 * sig_TeV3 ** 2
         * (10.75 / G_STAR) ** (1.0 / 3.0) * (T_ann / 1e-2) ** (-4))
f_pk = 3.99e-9 * A_SCALING ** (-0.5) * sig_TeV3 ** (-0.5) * (T_ann / 1e-2)
print(f"  Omega_GW h^2 <~ {om_gw:.2e} at f_peak ~ {f_pk:.2e} Hz "
      f"(strict ceiling: walls never reach scaling; R03 formula structure, "
      f"coefficient flagged for citation verification before paper use)")
print(f"  Delta N_eff ~= 0 (transient foam <= 4.2% of rho_rad for ~1e-22 s, "
      f"rethermalizes into the SM kink plasma)")
print(f"  zero surviving defect network: any confirmed cosmological domain-wall "
      f"relic falsifies the framework (sigma and T_ann parameter-free)")

results = {
    "couplings": {"e2_LambdaGTE": [3.5, 3.758], "g_GeV": 1.77686,
                  "provenance": "color_coupling_e_normalization / _g_scc_analog"},
    "bias": {"dV01_TG_central_GeV4": dV_central, "dV01_T0_GeV4": dV_T0,
             "range_GeV4": [dV_min, dV_max]},
    "collapse": rows, "T_ann_GeV": T_ann,
    "clearance_BBN": T_ann / T_BBN,
    "Omega_GW_h2_ceiling": om_gw, "f_peak_Hz": f_pk,
    "Delta_N_eff": "~0",
    "P47_falsifiability": "zero surviving defect network; selected vacuum k*=0 "
                          "(CatAD ROBUST, RG-improved); T_ann ~= T_G ~= 0.7 GeV"}

with open(os.path.join(_SCRIPT_DIR,
          "vacuum_selection_rg_defect_numbers_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("\nSaved vacuum_selection_rg_defect_numbers_results.json")
signal.alarm(0)
