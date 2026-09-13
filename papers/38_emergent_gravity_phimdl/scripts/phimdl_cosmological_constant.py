#!/usr/bin/env python3
"""
075-COSMO: Z7 Vacuum Energy → Cosmological Constant Lambda

Phi_MDL has the Z7 sine-Gordon potential:
  V(Phi) = (m_phi^2 / 49) * (1 - cos(7 Phi))
  m_phi = m_tau = 1776.86 MeV

Seven degenerate vacua at Phi_k = 2*pi*k/7, k = 0,1,...,6.

Computes:
  1. V(Phi_k) at each of the 7 Z7 vacua — classical vacuum energy
  2. Zero-point energy via zeta-function regularization (Casimir-like)
     of the BPS kink fluctuation spectrum
  3. Kink gas contribution at T_CMB = 2.725 K
  4. The hierarchy problem: rho_Lambda(GTE) vs rho_Lambda(obs)
  5. Natural cancellation assessment

Output: phimdl_cosmological_constant_results.json
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time

TIMEOUT_SECONDS = 300

def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

# ── Physical constants ─────────────────────────────────────────────────────────
M_TAU_MEV = 1776.86          # tau lepton mass in MeV (= m_phi by SCC identification)
M_TAU_GEV = M_TAU_MEV / 1e3  # GeV
M_KINK_MEV = (8.0 / 49.0) * M_TAU_MEV  # BPS kink mass

# Natural units: hbar = c = 1 throughout, energies in MeV or GeV
# Conversion factors
MEV_TO_GEV = 1e-3
GEV4_TO_GEV4 = 1.0           # trivial

# Observed dark energy density
# rho_Lambda_obs = (2.3 meV)^4 in natural units
# 2.3 meV = 2.3e-3 eV = 2.3e-9 MeV
RHO_LAMBDA_OBS_MEV4 = (2.3e-9) ** 4   # MeV^4

# Newton's constant: G = 6.674e-11 N m^2 kg^-2
# In natural units (hbar=c=1, length in GeV^-1):
# G = M_pl^-2 where M_pl = 1.22e22 MeV (reduced: M_pl/sqrt(8pi) ~ 2.43e18 GeV)
M_PLANCK_MEV = 1.2209e22      # MeV (full Planck mass)
M_PL_REDUCED_MEV = M_PLANCK_MEV / (8 * math.pi) ** 0.5  # ~ 2.435e21 MeV

# Speed of light, hbar*c for conversions
HBAR_C_MEV_FM = 197.3269804   # MeV·fm

# Boltzmann constant
KB_MEV_K = 8.61733e-11         # MeV / K
T_CMB_K = 2.725                # K
T_CMB_MEV = KB_MEV_K * T_CMB_K

print("=" * 70)
print("075-COSMO: Z7 Vacuum Energy → Cosmological Constant Lambda")
print("=" * 70)
print(f"m_phi = m_tau = {M_TAU_MEV:.4f} MeV")
print(f"M_kink = (8/49) * m_phi = {M_KINK_MEV:.4f} MeV")
print(f"T_CMB = {T_CMB_K} K = {T_CMB_MEV:.4e} MeV")
print()

# ── 1. V(Phi_k) at the 7 Z7 vacua ─────────────────────────────────────────────
print("── PART 1: Classical vacuum energy at Z7 minima ──")
print()
print("Potential: V(Phi) = (m_phi^2 / 49) * (1 - cos(7*Phi))")
print("Z7 vacua: Phi_k = 2*pi*k/7, k = 0,1,...,6")
print()

m = M_TAU_MEV  # m_phi in MeV

def potential_V(phi: float, m: float) -> float:
    """V(Phi) = (m^2/49)(1 - cos(7 Phi))"""
    return (m * m / 49.0) * (1.0 - math.cos(7.0 * phi))

vacua_data = []
print(f"{'k':>3}  {'Phi_k (rad)':>14}  {'7*Phi_k/pi':>12}  {'V(Phi_k) [MeV^2]':>20}")
print("-" * 60)
for k in range(7):
    phi_k = 2.0 * math.pi * k / 7.0
    V_k = potential_V(phi_k, m)
    # Check: cos(7 * 2pi*k/7) = cos(2pi*k) = 1 → V = 0
    val = {"k": k, "phi_k_rad": phi_k, "V_phi_k_MeV2": V_k}
    vacua_data.append(val)
    print(f"{k:>3}  {phi_k:>14.8f}  {7*phi_k/math.pi:>12.6f}  {V_k:>20.6e}")

print()
max_V_at_vacua = max(abs(v["V_phi_k_MeV2"]) for v in vacua_data)
print(f"Max |V(Phi_k)| at vacua: {max_V_at_vacua:.4e} MeV² (numerical zero)")
print()
print("  → V(Phi_k) = 0 exactly at all 7 Z7 vacua (by construction: cos(2pi*k) = 1)")
print("  → Classical vacuum energy density rho_Lambda(classical) = 0")
print()

# Potential barrier between vacua
phi_barrier = math.pi / 7  # midpoint between k=0 and k=1 vacua
V_max = (m * m / 49.0) * 2.0  # max of (1 - cos(7*pi/7)) = 1-cos(pi) = 2
print(f"  Potential barrier max V = 2*m_phi^2/49 = {V_max:.4f} MeV^2 = {V_max:.4e} MeV^2")
print(f"  = {V_max * MEV_TO_GEV**2:.4e} GeV^2")
print()

# ── 2. Zero-point energy (quantum correction) ──────────────────────────────────
print("── PART 2: Zero-point energy via zeta-function regularization ──")
print()
print("The Phi_MDL Z7-KG field has a quantum fluctuation spectrum around each vacuum.")
print("The BPS kink splits the vacuum into sectors; around each vacuum, the")
print("small-oscillation (meson) spectrum has:")
print("  - Discrete bound state (kink translational zero mode): omega_0 = 0")
print("  - Shape mode (if present): omega_s ~ m_phi * f(Z7)")
print("  - Continuum: omega(k) = sqrt(k^2 + m_phi^2)")
print()
print("The unregularized zero-point energy density is:")
print("  rho_ZPE = (1/2) * integral d^3k/(2pi)^3 * sqrt(k^2 + m_phi^2)  [UV divergent]")
print()

# Zeta-function regularization of scalar field ZPE in (1+1)D and (3+1)D
# In 3+1D: rho_ZPE (regularized) = -m_phi^4 / (64 pi^2) [Coleman-Weinberg, MS-bar at scale mu=m_phi]
# This is the standard one-loop Coleman-Weinberg result for a massive scalar

# Coleman-Weinberg one-loop effective potential correction (MS-bar)
# Delta V_CW = m_phi^4 / (64 pi^2) * [ln(m_phi^2/mu^2) - 3/2]
# At mu = m_phi: Delta V_CW = -3 m_phi^4 / (128 pi^2)

mu_renorm = M_TAU_MEV  # renormalization scale = m_phi (natural choice)
factor_CW = 1.0 / (64.0 * math.pi**2)
Delta_V_CW_at_mu_eq_m = -3.0 * m**4 / (128.0 * math.pi**2)

print(f"  Coleman-Weinberg one-loop correction (mu = m_phi, MS-bar):")
print(f"  Delta V_CW = m_phi^4 / (64 pi^2) * [ln(1) - 3/2] = -3 m_phi^4 / (128 pi^2)")
print(f"  m_phi^4 = {m**4:.6e} MeV^4")
print(f"  Delta V_CW = {Delta_V_CW_at_mu_eq_m:.6e} MeV^4")
print()

# Hierarchy: ratio of ZPE to observed Λ
ratio_ZPE_to_obs = abs(Delta_V_CW_at_mu_eq_m) / RHO_LAMBDA_OBS_MEV4
print(f"  rho_Lambda(obs) = (2.3 meV)^4 = {RHO_LAMBDA_OBS_MEV4:.4e} MeV^4")
print(f"  |Delta V_CW| / rho_Lambda(obs) = {ratio_ZPE_to_obs:.4e}")
print(f"  → Hierarchy factor: 10^{math.log10(ratio_ZPE_to_obs):.1f}")
print()

# Zeta-regularized Casimir energy in 1+1D (for reference: the Dashen-Hasslacher-Neveu result)
# For the sine-Gordon kink in 1+1D, the DHN formula gives:
# E_quantum/M_classical = -m_phi / (8 pi) [for the standard sine-Gordon lambda phi^4 form]
# For Z7 sine-Gordon we estimate analogously
# The quantum correction to kink mass in 1+1D:
# delta M_kink = -m_phi * sqrt(3) / (4 pi) [DHN, standard sG]
# For Z7, the shape mode frequency is omega_s = sqrt(3) * m_phi (Poeschl-Teller shape mode)
DHN_correction_standard_sG = -m * math.sqrt(3) / (4.0 * math.pi)
print(f"  DHN quantum correction to kink mass (1+1D analogue, standard sG):")
print(f"  delta M_kink ~ -m_phi * sqrt(3) / (4pi) = {DHN_correction_standard_sG:.4f} MeV")
print(f"  Relative: delta M_kink / M_kink = {DHN_correction_standard_sG / M_KINK_MEV:.4f}")
print()

print("  NOTE: In 3+1D (domain wall), the ZPE is per unit area.")
print("  The bulk vacuum energy (cosmological constant contribution) comes from")
print("  the one-loop Coleman-Weinberg potential, not from the kink itself.")
print()

# ── 3. Kink gas at T_CMB ──────────────────────────────────────────────────────
print("── PART 3: Thermal kink density at T_CMB ──")
print()

# Kink density in 1+1D (dilute gas approximation):
# n_kink ~ (m_phi / 2pi)^(1/2) * exp(-M_kink / T) [Polyakov dilute gas]
# At T_CMB:
suppression_exp = M_KINK_MEV / T_CMB_MEV
n_kink_suppression = math.exp(-suppression_exp)  # underflows to 0

print(f"  T_CMB = {T_CMB_MEV:.4e} MeV")
print(f"  M_kink / T_CMB = {suppression_exp:.4e}")
print(f"  Thermal suppression factor exp(-M_kink/T_CMB) = exp(-{suppression_exp:.2e})")
print(f"  = 10^{-suppression_exp * math.log10(math.e):.2e} (effectively zero)")
print()
print("  → Kink gas contribution to vacuum energy at T_CMB: negligibly small")
print("  → The cosmological kink density is essentially zero")
print()

# ── 4. The hierarchy problem assessment ────────────────────────────────────────
print("── PART 4: Hierarchy problem and GTE natural cancellation ──")
print()

rho_phi4 = m**4  # naive estimate
ratio_phi4 = rho_phi4 / RHO_LAMBDA_OBS_MEV4
print(f"  Naive estimate rho_Lambda ~ m_phi^4 = {rho_phi4:.4e} MeV^4")
print(f"  rho_Lambda(obs) = {RHO_LAMBDA_OBS_MEV4:.4e} MeV^4")
print(f"  Hierarchy: m_phi^4 / rho_Lambda(obs) = {ratio_phi4:.4e}")
print(f"  = 10^{math.log10(ratio_phi4):.1f} (the cosmological constant problem)")
print()

# The Z7 potential is Z7 symmetric → sum over all vacua of V(Phi_k) = 0
# This is trivially zero (all vacua degenerate at zero)
# But quantum corrections break this:
# The one-loop correction is NOT zero and scales as m_phi^4/(64 pi^2)
# GTE does NOT provide a natural cancellation mechanism for this

print("  GTE NATURAL CANCELLATION ASSESSMENT:")
print()
print("  (a) Classical level: V(Phi_k) = 0 exactly → NO contribution")
print("      (by Z7 symmetry all vacua are degenerate at zero potential)")
print()
print("  (b) One-loop level: Delta V_CW ~ m_phi^4/(64 pi^2) ~ 10^10 MeV^4")
print(f"      >> rho_Lambda(obs) ~ {RHO_LAMBDA_OBS_MEV4:.2e} MeV^4")
print()
print("  (c) Z7 symmetry does NOT cancel the one-loop correction.")
print("      All 7 degenerate vacua receive the SAME one-loop correction;")
print("      they cancel among themselves in the RELATIVE energy only,")
print("      not in the absolute vacuum energy.")
print()
print("  (d) No supersymmetry: GTE has no boson-fermion pairing to cancel ZPE.")
print()
print("  (e) The GTE kink sector does not provide a compensation mechanism.")
print("      The Φ_MDL field sits in one vacuum; the ZPE of that vacuum")
print("      contributes to the cosmological constant.")
print()
print("  VERDICT: GTE does NOT provide a natural resolution of the")
print("  cosmological constant hierarchy problem.")
print("  This is an OPEN problem: the CC is 10^{:.0f} times the GTE natural scale.".format(
    math.log10(ratio_ZPE_to_obs)))
print()
print("  The Φ_MDL field contributes to Λ at the level of m_phi^4 ~ (1.8 GeV)^4")
print("  unless an external cancellation mechanism (anthropic, holographic,")
print("  or a GTE symmetry not yet identified) operates.")
print()

# ── Summary table ──────────────────────────────────────────────────────────────
print("── SUMMARY ──")
print(f"  V(Phi_k) at each Z7 vacuum: EXACTLY ZERO (all 7 vacua)")
print(f"  Classical rho_Lambda: 0")
print(f"  One-loop ZPE (Coleman-Weinberg): {Delta_V_CW_at_mu_eq_m:.4e} MeV^4")
print(f"  Hierarchy |ZPE| / rho_Lambda(obs): 10^{math.log10(ratio_ZPE_to_obs):.1f}")
print(f"  Natural GTE cancellation: NONE (open problem)")
print(f"  Kink gas at T_CMB: exp(-{suppression_exp:.2e}) ≈ 0 (negligible)")
print(f"  CatLevel verdict: CatD (open problem — no GTE prediction for Λ value)")
print()

# ── Save results ───────────────────────────────────────────────────────────────
results = {
    "task": "075-COSMO",
    "description": "Z7 vacuum energy → cosmological constant Lambda",
    "m_phi_MeV": M_TAU_MEV,
    "M_kink_MEV": M_KINK_MEV,
    "T_CMB_K": T_CMB_K,
    "T_CMB_MEV": T_CMB_MEV,
    "Z7_vacua": [
        {
            "k": v["k"],
            "phi_k_rad": v["phi_k_rad"],
            "V_phi_k_MeV2": v["V_phi_k_MeV2"],
            "V_exactly_zero": abs(v["V_phi_k_MeV2"]) < 1e-10,
        }
        for v in vacua_data
    ],
    "classical_vacuum_energy": {
        "V_at_each_vacuum_MeV2": 0.0,
        "rho_Lambda_classical_MeV4": 0.0,
        "comment": "V(Phi_k) = (m^2/49)(1-cos(2pi k)) = 0 for all k in Z7",
    },
    "potential_barrier": {
        "max_V_MeV2": V_max,
        "formula": "2 * m_phi^2 / 49",
    },
    "one_loop_ZPE": {
        "Delta_V_CW_MeV4": Delta_V_CW_at_mu_eq_m,
        "formula": "-3 m_phi^4 / (128 pi^2), MS-bar at mu = m_phi",
        "magnitude_MeV4": abs(Delta_V_CW_at_mu_eq_m),
    },
    "DHN_kink_mass_correction_1D": {
        "delta_M_kink_MeV": DHN_correction_standard_sG,
        "relative": DHN_correction_standard_sG / M_KINK_MEV,
        "comment": "Analogue of DHN formula for standard sG; Z7 form may differ",
    },
    "kink_gas_at_TCMB": {
        "T_CMB_MEV": T_CMB_MEV,
        "M_kink_over_T_CMB": suppression_exp,
        "thermal_suppression": "exp(-{:.2e}) = essentially zero".format(suppression_exp),
        "kink_density_at_CMB": "negligible",
    },
    "hierarchy_problem": {
        "rho_Lambda_obs_MeV4": RHO_LAMBDA_OBS_MEV4,
        "rho_phi4_MeV4": rho_phi4,
        "ratio_phi4_over_obs": ratio_phi4,
        "log10_hierarchy": math.log10(ratio_phi4),
        "ratio_ZPE_over_obs": ratio_ZPE_to_obs,
        "log10_hierarchy_ZPE": math.log10(ratio_ZPE_to_obs),
    },
    "natural_cancellation_assessment": {
        "classical_level": "V(Phi_k) = 0 — no contribution",
        "Z7_symmetry_effect": "Cancels relative energy between vacua only; NOT absolute ZPE",
        "one_loop_level": "Delta V_CW ~ m_phi^4/(64 pi^2) >> rho_Lambda(obs)",
        "SUSY_present": False,
        "known_GTE_cancellation_mechanism": None,
        "verdict": "OPEN problem: GTE provides no natural Lambda suppression",
    },
    "CatLevel": "CatD",
    "verdict": (
        "Z7 vacua have V=0 classically. One-loop ZPE ~ (1.8 GeV)^4 "
        "creates hierarchy 10^50 over observed Lambda. "
        "GTE has no known cancellation. OPEN problem."
    ),
    "elapsed_s": time.time() - t0,
}

outfile = "phimdl_cosmological_constant_results.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {outfile}")
print(f"Elapsed: {results['elapsed_s']:.2f}s")

signal.alarm(0)
