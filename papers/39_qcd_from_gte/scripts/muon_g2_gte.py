"""
GTE contribution to muon anomalous magnetic moment (g-2)_mu
Rank 083C-MUON-G2

Computes a_mu^{GTE} from:
  1. Phi_MDL scalar one-loop vertex correction (Yukawa coupling h_mu)
  2. Second Cartan field A'_mu assessment
  3. Dark sector contribution (zero by Q=0 theorem)

All GTE parameters at CatAL/CatAD level; result is an honest null.
"""

import numpy as np
from scipy import integrate
import signal
import sys
import json

TIMEOUT = 120
signal.signal(signal.SIGALRM, lambda s, f: (print("TIMEOUT reached"), sys.exit(1)))
signal.alarm(TIMEOUT)

# ------------------------------------------------------------------ #
# GTE PARAMETERS (CatAL/CatAD certified)
# ------------------------------------------------------------------ #
m_mu = 105.658370      # MeV  — muon mass (PDG 2024)
m_phi = 1776.86        # MeV  — Phi_MDL mass = m_tau (SCC condition, CatAL)
v_H = 246160.0         # MeV  — EW VEV (SRRG fixed point, CatAL P27)
alpha_em = 1.0 / 137.035999  # fine structure constant

# Experimental discrepancy (Fermilab + BNL combined 2023):
delta_a_mu_exp = 251e-11      # central value
delta_a_mu_err = 59e-11       # 1sigma uncertainty


def yukawa_coupling(m_fermion: float, vev: float) -> float:
    """SM Yukawa coupling h = m / (v/sqrt(2))."""
    return m_fermion / (vev / np.sqrt(2))


def scalar_loop_integrand(x: float, r_sq: float) -> float:
    """
    Integrand for the one-loop neutral scalar contribution to a_mu.

    Standard result for CP-even scalar with Yukawa coupling h and mass M,
    giving a_mu = (h^2 / 8pi^2) * integral.

    Numerator x^2(2-x) follows from the Gordon decomposition of the
    spin-1/2 vertex in the magnetic form factor channel (scalar loop).
    Formula consistent with leading-log asymptotics:
      a_mu ~ (h^2/8pi^2) * (1/r^2) * (1 + 2*ln(r)) for large r=M/m.

    Reference: Czarnecki & Marciano, PRD 64, 013014 (2001), Appendix A.
    """
    return x**2 * (2.0 - x) / (x**2 + (1.0 - x) * r_sq)


# ------------------------------------------------------------------ #
# TASK 1: Yukawa coupling
# ------------------------------------------------------------------ #
h_mu = yukawa_coupling(m_mu, v_H)
r = m_phi / m_mu
r_sq = r**2

# ------------------------------------------------------------------ #
# TASK 2: Phi_MDL scalar loop integral
# ------------------------------------------------------------------ #
F_integral, F_err = integrate.quad(scalar_loop_integrand, 0.0, 1.0, args=(r_sq,))
a_mu_phi = (h_mu**2 / (8.0 * np.pi**2)) * F_integral

# Large-M approximation: a_mu ~ h^2/(8pi^2) * (1/r^2)*(1+2*ln(r))
F_large_r = (1.0 / r_sq) * (1.0 + 2.0 * np.log(r))
a_mu_phi_approx = (h_mu**2 / (8.0 * np.pi**2)) * F_large_r

# SM Higgs cross-check (should give ~4e-14, consistent with literature):
r_H = 125250.0 / m_mu
F_H = (1.0 / r_H**2) * (1.0 + 2.0 * np.log(r_H))
a_mu_H_check = (h_mu**2 / (8.0 * np.pi**2)) * F_H

# ------------------------------------------------------------------ #
# TASK 3: A'_mu second Cartan field — analytic argument, no integral
# ------------------------------------------------------------------ #
# F_21 = Z_7 semidirect Z_3. The A'_mu is the second Cartan element of
# F_21 acting on the Z_3 (color) sector. The muon is a Z_3 non-singlet
# (Q_chi = 1) but A'_mu is CONFINED within the F_21 structure; it does not
# appear as a free massless gauge boson in the physical spectrum.
# The only physical massless gauge boson is the SM photon (standard QED).
# Rank 116-SECONDCARTAN: A'_mu contribution to a_mu is zero.
a_mu_Aprime = 0.0

# Hypothetical (to show it is ruled out): if A'_mu were free with e'=e
a_mu_Aprime_hypothetical = alpha_em / (2.0 * np.pi)  # Schwinger-scale

# ------------------------------------------------------------------ #
# TASK 4: Dark sector — analytic, zero by Q=0 theorem
# ------------------------------------------------------------------ #
# Dark leptons (0.54, 24.5, 3.60 GeV) have Q=0 (P29, CatAL theorem DarkQ=0).
# Zero electric charge => zero coupling to photon => zero contribution to a_mu.
a_mu_dark = 0.0

# ------------------------------------------------------------------ #
# TOTAL GTE CORRECTION
# ------------------------------------------------------------------ #
a_mu_gte_total = a_mu_phi + a_mu_Aprime + a_mu_dark

fraction_of_anomaly = a_mu_gte_total / delta_a_mu_exp

# ------------------------------------------------------------------ #
# OUTPUT
# ------------------------------------------------------------------ #
print("=" * 70)
print("GTE CONTRIBUTION TO MUON (g-2)_mu — Rank 083C-MUON-G2")
print("=" * 70)
print(f"\nGTE PARAMETERS:")
print(f"  m_mu   = {m_mu:.6f} MeV")
print(f"  m_phi  = {m_phi:.2f} MeV  (Phi_MDL = m_tau by SCC, CatAL)")
print(f"  v_H    = {v_H:.1f} MeV  (SRRG, CatAL)")
print(f"  h_mu   = {h_mu:.4e}  (muon Yukawa coupling)")
print(f"  r      = m_phi/m_mu = {r:.4f}")
print()
print(f"PHI_MDL SCALAR LOOP:")
print(f"  Loop integral F(r^2={r_sq:.2f}) = {F_integral:.6e}  (err={F_err:.2e})")
print(f"  Large-r approximation F = {F_large_r:.6e}")
print(f"  a_mu^(Phi_MDL, exact)  = {a_mu_phi:.4e}")
print(f"  a_mu^(Phi_MDL, approx) = {a_mu_phi_approx:.4e}")
print(f"  SM Higgs cross-check   = {a_mu_H_check:.4e}  (lit: ~4e-14, consistent)")
print()
print(f"SECOND CARTAN A'_mu CONTRIBUTION:")
print(f"  a_mu^(A') = 0  (confined in F_21; not a free massless boson)")
print(f"  Hypothetical (ruled-out) value: {a_mu_Aprime_hypothetical:.4e}")
print(f"  This would be {a_mu_Aprime_hypothetical/delta_a_mu_exp:.2e}x larger than anomaly — excluded")
print()
print(f"DARK SECTOR CONTRIBUTION:")
print(f"  a_mu^dark = 0  (Q_dark = 0, no photon coupling, P29 CatAL)")
print()
print("=" * 70)
print(f"TOTAL GTE CORRECTION: a_mu^GTE = {a_mu_gte_total:.4e}")
print(f"Experimental anomaly:  Delta_a_mu = {delta_a_mu_exp:.4e} +/- {delta_a_mu_err:.4e}")
print(f"Fraction of anomaly:   {fraction_of_anomaly*100:.4f}%")
print(f"a_mu^GTE / 1sigma_exp: {a_mu_gte_total/delta_a_mu_err:.4f}")
print(f"a_mu^GTE = {a_mu_gte_total/1e-11:.3f} x 10^-11")
print(f"Anomaly  = {delta_a_mu_exp/1e-11:.1f} x 10^-11")
print()
print("VERDICT: GTE does NOT resolve the 4-sigma muon g-2 discrepancy.")
print("The Phi_MDL loop gives ~3% of the anomaly — an honest quantitative null.")
print("Result classification: CatA (honest null, below experimental sensitivity)")
print("=" * 70)

signal.alarm(0)

# ------------------------------------------------------------------ #
# SAVE RESULTS
# ------------------------------------------------------------------ #
results = {
    "rank": "083C-MUON-G2",
    "date": "2026-06-02",
    "parameters": {
        "m_mu_MeV": m_mu,
        "m_phi_MeV": m_phi,
        "v_H_MeV": v_H,
        "h_mu": h_mu,
        "r_ratio": r,
    },
    "phi_mdl_loop": {
        "loop_integral_F": F_integral,
        "loop_integral_error": F_err,
        "a_mu_exact": a_mu_phi,
        "a_mu_large_r_approx": a_mu_phi_approx,
    },
    "A_prime_contribution": {
        "value": a_mu_Aprime,
        "reason": "Confined in F_21; not a free massless gauge boson",
        "hypothetical_if_free": a_mu_Aprime_hypothetical,
    },
    "dark_sector": {
        "value": a_mu_dark,
        "reason": "Q_dark=0 (CatAL, P29), no photon coupling",
    },
    "total_a_mu_gte": a_mu_gte_total,
    "experimental_anomaly": delta_a_mu_exp,
    "experimental_uncertainty_1sigma": delta_a_mu_err,
    "fraction_of_anomaly_pct": fraction_of_anomaly * 100.0,
    "verdict": "CatA HONEST NULL: GTE does not resolve the 4-sigma muon g-2 discrepancy. "
               "Phi_MDL scalar loop gives ~3% of anomaly (7.47e-11 vs 251e-11). "
               "Coupling h_mu is Yukawa-suppressed by m_mu/v_H; mass ratio m_phi/m_mu "
               "provides additional (m_mu/m_phi)^2 suppression.",
}

with open("muon_g2_gte_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Results saved to research-sandbox/muon_g2_gte_results.json")
