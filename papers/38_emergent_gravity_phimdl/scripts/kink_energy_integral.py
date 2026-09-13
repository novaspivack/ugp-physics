"""
BPS kink mass integral for the Phi_MDL Z7 sine-Gordon theory.

Computes M_kink = integral T_00 dz for the BPS kink solution connecting
adjacent Z7 vacua.  Verifies the analytic result M_kink = 8m/49.

Theory:
    V(Phi) = (m^2/49)(1 - cos 7*Phi)
    BPS equation: d_z Phi = sqrt(2*V(Phi))
    Kink solution: Phi traverses one vacuum step, 0 -> 2*pi/7

Analytic derivation:
    M_kink = integral_0^{2pi/7} sqrt(2*V) d_Phi
           = integral_0^{2pi/7} (2m/7)|sin(7*Phi/2)| d_Phi
    Sub u = 7*Phi/2, du = 7/2 d_Phi, range [0, pi]:
           = (4m/49) integral_0^pi sin(u) du = (4m/49)*2 = 8m/49

Reference: EPIC_080 G7 — kink energy integral.
Script location: papers/38_emergent_gravity_phimdl/scripts/kink_energy_integral.py
"""

import math
import signal
import sys
import json
import os

import numpy as np
import scipy.integrate as integrate

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


# ---- Potential and BPS integrand ----

def z7_potential(phi: float, m: float = 1.0) -> float:
    """Z7 sine-Gordon potential V(Phi) = (m^2/49)(1 - cos 7*Phi)."""
    return (m**2 / 49.0) * (1.0 - math.cos(7.0 * phi))


def bps_integrand(phi: float, m: float = 1.0) -> float:
    """BPS integrand sqrt(2*V(Phi)) for the kink mass integral."""
    return math.sqrt(max(0.0, 2.0 * z7_potential(phi, m)))


# ---- Numerical integration ----

def compute_kink_mass_numerical(m: float = 1.0) -> tuple[float, float]:
    """
    Numerically integrate M_kink = integral_0^{2pi/7} sqrt(2V) d_Phi.
    Returns (M_kink, error_estimate).
    """
    phi_max = 2.0 * math.pi / 7.0
    result, err = integrate.quad(
        bps_integrand, 0.0, phi_max,
        args=(m,), limit=500, epsabs=1e-14
    )
    return result, err


def compute_kink_mass_analytic(m: float = 1.0) -> float:
    """Analytic result M_kink = 8m/49."""
    return 8.0 * m / 49.0


# ---- Main ----

def main() -> None:
    print("=" * 64)
    print("BPS KINK MASS INTEGRAL — Z7 sine-Gordon (Phi_MDL)")
    print("=" * 64)
    print("V(Phi) = (m^2/49)(1 - cos(7*Phi))")
    print("BPS range: Phi in [0, 2*pi/7]  (one vacuum step)")
    print()

    m = 1.0
    M_num, err = compute_kink_mass_numerical(m)
    M_ana = compute_kink_mass_analytic(m)
    rel_err_pct = abs(M_num - M_ana) / M_ana * 100.0

    print(f"Numerical  M_kink = {M_num:.12f}  (m=1)")
    print(f"Analytic   M_kink = {M_ana:.12f}  (m=1, exact: 8/49)")
    print(f"Agreement: {rel_err_pct:.2e}%  |  quad error: {err:.2e}")
    print()

    # Physical units
    m_tau_MeV  = 1776.86    # PDG 2024
    v_H_MeV    = 246.16e3   # SRRG fixed point (independent)
    M_kink_MeV = (8.0 / 49.0) * m_tau_MeV
    y_tau      = m_tau_MeV / (v_H_MeV / math.sqrt(2.0))

    print("Physical values (m = m_tau identification):")
    print(f"  m_tau      = {m_tau_MeV:.2f} MeV  (PDG)")
    print(f"  M_kink     = (8/49) * m_tau = {M_kink_MeV:.4f} MeV")
    print(f"  v_H (SRRG) = {v_H_MeV:.2f} MeV = {v_H_MeV/1000:.4f} GeV")
    print(f"  y_tau      = m_tau / (v_H/sqrt(2)) = {y_tau:.6f}")
    print()

    print("CatLevel summary:")
    print("  CatAL — M_kink = 8m/49  (analytic BPS integral, exact)")
    print("  CatA  — m = m_tau  (tau sector w=4 identification)")
    print("  CatAD — m_tau = y_tau * v_H/sqrt(2), v_H from SRRG")
    print()
    print("Scale-anchor conclusion:")
    print("  GTE arithmetic is dimensionless; one physical unit calibration")
    print("  (one particle mass in MeV) is irreducible.  The tau lepton mass")
    print("  serves as this anchor for the kink sector.")

    results = {
        "computation": "BPS kink mass integral, Z7 sine-Gordon theory",
        "potential": "V(Phi) = (m^2/49)*(1 - cos(7*Phi))",
        "bps_range_phi": [0.0, 2.0 * math.pi / 7.0],
        "analytic_derivation": (
            "u = 7*Phi/2 substitution: (4m/49)*int_0^pi sin(u) du = 8m/49"
        ),
        "M_kink_numerical": M_num,
        "M_kink_analytic": M_ana,
        "quad_error": err,
        "agreement_pct": rel_err_pct,
        "physical": {
            "m_tau_MeV": m_tau_MeV,
            "M_kink_MeV": M_kink_MeV,
            "v_H_MeV": v_H_MeV,
            "y_tau": y_tau,
        },
        "cat_levels": {
            "CatAL": "M_kink = 8m/49 from BPS integral (analytic, exact, zero free params)",
            "CatA":  "m = m_tau identification (tau sector w=4)",
            "CatAD": "m_tau = y_tau * v_H/sqrt(2) where v_H from SRRG",
        },
        "scale_anchor": (
            "ONE irreducible scale anchor: the physical unit (MeV). "
            "m_tau serves as this anchor; GTE integers alone are dimensionless."
        ),
    }

    out_path = "papers/38_emergent_gravity_phimdl/scripts/kink_energy_integral_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
    signal.alarm(0)
