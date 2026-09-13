#!/usr/bin/env python3
"""Z7 domain-wall sector: CatAD tension, formation, and domination computation.

Computes, from the canonical Phi_MDL Lagrangian (P42):
  1. Wall tension sigma: canonical P42 value sigma = (8/49) m_tau f^2 with the
     paper normalization f = 1 GeV (P42 eq. tension: sigma = 0.29010 GeV^3),
     plus the two bracket variants f = m_phi (sigma = (8/49) m_phi^3) and the
     scout's M_kink^3. BPS integral cross-checked numerically.
  2. Z7 ordering (Ginzburg/formation) temperature T_G from the Debye-Waller
     melting criterion (49/2)<(phi/f)^2>_T = 1 with <phi^2>_T = T^2/12.
  3. Thermalization check: quartic coupling of the cosine potential and
     Gamma_th / H at T_G; comparison with T_reh = 6.49e8 GeV (P44).
  4. Wall-domination epoch from the Friedmann equation directly
     (rho_wall = A sigma / t vs LCDM rho_tot(z)) -- no literature scaling
     formula; cross-checked against the classic Zel'dovich MeV^3 statement.
  5. Zel'dovich CMB anisotropy bound: delta T / T ~ G sigma t at recombination
     and today; violation factor vs 1e-5.
  6. Frozen (locked, non-scaling) network variant.

Expected output: sigma ~ 0.3 GeV^3, T_G ~ 0.7 GeV, domination near
recombination (z ~ 1e3), Zel'dovich violation ~1e3-1e8.
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

# --- GTE inputs (all derived; sources noted) ---
m_tau = 1.77686           # GeV  (m_phi = m_tau, SCC, P42)
M_kink = 8.0 * m_tau / 49.0   # = 0.29010 GeV (BPS, CatAL)
f_paper = 1.0             # GeV; P42 eq. tension normalization (sigma = 0.29010 GeV^3)
f_mphi = m_tau            # variant: decay constant = m_phi

# --- physical constants (PDG 2024 / Planck 2018 via CANONICAL_COMPARISON_DATA) ---
G_N = 6.70883e-39         # GeV^-2
M_Pl = 1.220890e19        # GeV
T0_GeV = 2.7255 * 8.617333e-14   # K -> GeV = 2.3487e-13
s_to_GeVinv = 1.519268e24
t0_s = 4.35e17
t_rec_s = 1.16e13
H0 = 67.66 / (3.0857e19) * 1.0   # km/s/Mpc -> 1/s
H0_GeV = H0 / s_to_GeVinv * 1.0  # careful: H0 [1/s] -> GeV via 1 s^-1 = 1/1.519e24 GeV
H0_GeV = (67.66 / 3.0857e19) / s_to_GeVinv * s_to_GeVinv**0  # recompute cleanly below
H0_GeV = (67.66 / 3.0857e19) * (1.0 / s_to_GeVinv)  # (1/s)*(GeV per 1/s)
Omega_m, Omega_L, Omega_r = 0.3111, 0.6889, 9.2e-5
A_area = 0.8              # HKS area parameter (sim-derived; used for the scaling network)

results = {}

# 1. tension table + BPS cross-check ------------------------------------------
def bps_sigma(m, f, n=200000):
    # sigma = int_0^{2 pi f/7} sqrt(2 V) dphi,  V = (m^2 f^2/49)(1 - cos(7 phi/f))
    h = (2.0 * math.pi * f / 7.0) / n
    tot = 0.0
    for i in range(n + 1):
        phi = i * h
        w = 0.5 if i in (0, n) else 1.0
        V = (m * m * f * f / 49.0) * (1.0 - math.cos(7.0 * phi / f))
        tot += w * math.sqrt(2.0 * V)
    return tot * h

sig_canon = bps_sigma(m_tau, f_paper)
sig_fmphi = bps_sigma(m_tau, f_mphi)
sig_scout = M_kink ** 3
print("=== 1. Wall tension (GeV^3) ===")
print(f"  canonical P42 (f = 1 GeV):  sigma = {sig_canon:.5f}  "
      f"(analytic 8 m f^2/49 = {8*m_tau*f_paper**2/49:.5f}; paper value 0.29010)")
print(f"  variant  f = m_phi:         sigma = {sig_fmphi:.5f}  (= (8/49) m_phi^3)")
print(f"  scout    M_kink^3:          sigma = {sig_scout:.5f}")
results["sigma_GeV3"] = {"canonical_P42": sig_canon, "f_mphi": sig_fmphi,
                         "scout_Mkink3": sig_scout}

# 2. formation temperature -----------------------------------------------------
print("\n=== 2. Z7 ordering (formation) temperature ===")
tg = {}
for label, f in [("f=1GeV(P42)", f_paper), ("f=m_phi", f_mphi)]:
    T_G = math.sqrt(24.0 / 49.0) * f   # (49/2)(T^2/12 f^2) = 1
    tg[label] = T_G
    print(f"  {label}: T_G = {T_G:.4f} GeV  (Debye-Waller melting criterion)")
results["T_G_GeV"] = tg

# 3. thermalization vs reheating ------------------------------------------------
print("\n=== 3. Thermalization at T_G; reheating comparison ===")
T_reh = 6.49e8   # GeV (P44 eq. Treh)
lam4 = 49.0 * m_tau ** 2 / f_paper ** 2   # |V''''(0)| f-units: quartic scale
T_G0 = tg["f=1GeV(P42)"]
Gamma_th = lam4 ** 2 * T_G0 / 1.0e3       # conservative O(lambda^2 T/1000)
g_star_TG = 61.75
H_TG = 1.66 * math.sqrt(g_star_TG) * T_G0 ** 2 / M_Pl
print(f"  T_reh (P44) = {T_reh:.3e} GeV  >>  T_G = {T_G0:.3f} GeV "
      f"(ratio {T_reh/T_G0:.2e}) -> Z7 order is thermally erased after reheating")
print(f"  quartic scale lambda_4 = 49 m^2/f^2 = {lam4:.1f} (strongly coupled)")
print(f"  Gamma_th ~ lambda^2 T/1e3 = {Gamma_th:.3e} GeV vs H(T_G) = {H_TG:.3e} GeV "
      f"-> Gamma/H ~ {Gamma_th/H_TG:.2e} (phi zero mode fully thermalized)")
results["thermalization"] = {"T_reh_GeV": T_reh, "T_G_GeV": T_G0,
                             "lambda4": lam4, "Gamma_over_H": Gamma_th / H_TG}

# 4. wall domination from Friedmann ---------------------------------------------
print("\n=== 4. Wall domination epoch (first-principles Friedmann) ===")
rho_crit0 = 3.0 * H0_GeV ** 2 / (8.0 * math.pi * G_N)   # GeV^4

def H_of_z(z):
    return H0_GeV * math.sqrt(Omega_r * (1 + z) ** 4 + Omega_m * (1 + z) ** 3 + Omega_L)

def t_of_z(z, n=4000):
    # t = int_z^inf dz'/((1+z') H(z'))  via substitution u = ln(1+z')
    u0 = math.log(1.0 + z)
    tot, umax = 0.0, u0 + 30.0
    h = (umax - u0) / n
    for i in range(n + 1):
        u = u0 + i * h
        w = 0.5 if i in (0, n) else 1.0
        tot += w / (H_of_z(math.exp(u) - 1.0))
    return tot * h

def domination_z(sigma):
    lo, hi = 0.0, 1e9   # bisect on rho_wall(z) - rho_tot(z)
    def excess(z):
        t = t_of_z(z)
        rho_wall = A_area * sigma / t
        rho_tot = rho_crit0 * (Omega_r * (1+z)**4 + Omega_m * (1+z)**3 + Omega_L)
        return rho_wall - rho_tot
    if excess(0.0) < 0:
        return None
    for _ in range(200):
        mid = math.sqrt(max(lo, 1e-6) * hi) if lo > 0 else hi / 2
        if excess(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi / max(lo, 1e-30) < 1.0001:
            break
    return lo

print("  (scaling network rho_wall = A sigma/t vs LCDM rho_tot)")
dom = {}
for label, s in [("canonical", sig_canon), ("f=m_phi", sig_fmphi), ("Mkink^3", sig_scout)]:
    z_dom = domination_z(s)
    T_dom = T0_GeV * (1 + z_dom)
    t_dom_s = t_of_z(z_dom) / s_to_GeVinv
    dom[label] = {"z_dom": z_dom, "T_dom_GeV": T_dom, "t_dom_s": t_dom_s}
    print(f"  sigma = {s:.4f} GeV^3 [{label}]: z_dom = {z_dom:.3e}, "
          f"T_dom = {T_dom:.3e} GeV = {T_dom*1e9:.3f} eV, t_dom = {t_dom_s:.3e} s")
print("  NOTE: scout's T_dom = 4.2e-7 GeV (keV) is SUPERSEDED -- its scaling-"
      "formula coefficient could not be reproduced from the Friedmann equation.")
print("  Cross-check vs classic Zel'dovich: sigma = (1 MeV)^3 should dominate "
      "only in the far future:")
z_mev = domination_z(1e-9)
print(f"    sigma = 1e-9 GeV^3 -> z_dom = {z_mev}  (None/negative = future) OK"
      if z_mev is None else f"    sigma = 1e-9 GeV^3 -> z_dom = {z_mev:.3f} (must be ~0/future)")
results["domination"] = dom

# 5. Zel'dovich anisotropy bound -------------------------------------------------
print("\n=== 5. Zel'dovich CMB anisotropy bound (if walls survive) ===")
t_rec = t_rec_s * s_to_GeVinv
t0 = t0_s * s_to_GeVinv
zel = {}
for label, s in [("canonical", sig_canon), ("Mkink^3", sig_scout)]:
    dTT_rec = G_N * s * t_rec
    dTT_0 = G_N * s * t0
    zel[label] = {"dT_over_T_rec": dTT_rec, "dT_over_T_today": dTT_0,
                  "violation_factor_rec": dTT_rec / 1e-5}
    print(f"  sigma = {s:.4f} [{label}]: dT/T ~ G sigma t = {dTT_rec:.3e} (recomb), "
          f"{dTT_0:.3e} (today); violation vs 1e-5: x{dTT_rec/1e-5:.2e}")
results["zeldovich"] = zel

# 6. frozen (locked) network variant ---------------------------------------------
print("\n=== 6. Frozen-network variant (P50 locking scenario) ===")
# rho_wall = sigma/L_form * (a_form/a) ; ratio to radiation ~ a^3 growth
T_G_ = T_G0
rho_wall_form = sig_canon * T_G_          # L_form ~ 1/T_G
rho_rad_form = (math.pi ** 2 / 30.0) * g_star_TG * T_G_ ** 4
ratio_form = rho_wall_form / rho_rad_form
a_dom_over_a_form = (1.0 / ratio_form) ** (1.0 / 3.0)
T_dom_frozen = T_G_ / a_dom_over_a_form
print(f"  rho_wall/rho_rad at formation = {ratio_form:.3f}; "
      f"frozen network dominates at T = {T_dom_frozen:.3f} GeV "
      f"(a/a_form = {a_dom_over_a_form:.2f}) -- IMMEDIATE catastrophe if locked")
results["frozen_network"] = {"ratio_at_formation": ratio_form,
                             "T_dom_frozen_GeV": T_dom_frozen}

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "z7_domain_wall_tension_consistency_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("\nSaved z7_domain_wall_tension_consistency_results.json")
signal.alarm(0)
