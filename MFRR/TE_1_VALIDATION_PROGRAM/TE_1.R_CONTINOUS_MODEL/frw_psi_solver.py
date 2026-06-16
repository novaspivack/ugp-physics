
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Reference: TE_1.R plan (1_1_TE_1R_PLAN.md) for task context.
"""
Minimal FRW + coherence scalar Psi(t) solver (flat FRW).

Equations (MFRR sec. 7.7, 7.19):
  H^2 = (8*pi*G/3) [ rho_m0 / a^3  + rho_Psi + rho_L ],   rho_Psi = 0.5*PsiDot^2 + V_eff(Psi),  rho_L = Lambda_eff/(8*pi*G).
  PsiDDot + 3 H PsiDot + dV_eff/dPsi = 0.

We work in units with 8*pi*G = 1 by default; user may set Gtilde != 1.

V_eff(Psi) can be chosen; default is quadratic + linear (from U0, U1<omega>) as in MFRR sec. 7.19:
  V_eff(Psi) = 0.5*m^2 Psi^2 + beta <omega> Psi  + V0 (constant part can be folded into Lambda_eff).

References:
  - MFRR sec. 7.7 (bundle action; stress tensor), sec. 7.19 (example FRW solutions).
"""
import math
import json

def V_eff(psi: float, m: float, beta: float, omega_bar: float, V0: float) -> float:
    return 0.5*m*m*psi*psi + beta*omega_bar*psi + V0

def dV_dpsi(psi: float, m: float, beta: float, omega_bar: float) -> float:
    return m*m*psi + beta*omega_bar

def frw_psi_evolve(t_max: float = 5.0, dt: float = 1e-3,
                   a0: float = 1.0, psi0: float = 0.1, psidot0: float = 0.0,
                   rho_m0: float = 0.3, Lambda_eff: float = 0.7,
                   m: float = 0.0, beta: float = 0.0, omega_bar: float = 0.0, V0: float = 0.0,
                   Gtilde: float = 1.0):
    """Returns dict with time series of (t, a, H, psi, psidot, rhoPsi, rho_m, rho_L).
    Units: choose such that 8*pi*G = Gtilde (default 1).
    """
    t, a, psi, psidot = 0.0, a0, psi0, psidot0
    out = {"t": [], "a": [], "H": [], "psi": [], "psidot": [], "rhoPsi": [], "rho_m": [], "rho_L": []}
    eight_pi_G_over3 = Gtilde/3.0

    def record():
        rhoPsi = 0.5*psidot*psidot + V_eff(psi, m, beta, omega_bar, V0)
        rhoL   = Lambda_eff / Gtilde if Gtilde != 0 else 0.0
        rho_m  = rho_m0 / (a**3)
        H2 = eight_pi_G_over3 * (rhoPsi + rho_m + rhoL)
        H = math.sqrt(max(H2, 0.0))
        out["t"].append(t); out["a"].append(a); out["H"].append(H)
        out["psi"].append(psi); out["psidot"].append(psidot)
        out["rhoPsi"].append(rhoPsi); out["rho_m"].append(rho_m); out["rho_L"].append(rhoL)
        return H

    H = record()

    def rhs(a, psi, psidot):
        rhoPsi = 0.5*psidot*psidot + V_eff(psi, m, beta, omega_bar, V0)
        rhoL   = Lambda_eff / Gtilde if Gtilde != 0 else 0.0
        rho_m  = rho_m0 / (a**3)
        H2 = eight_pi_G_over3 * (rhoPsi + rho_m + rhoL)
        H = math.sqrt(max(H2, 0.0))
        adot = H*a
        psiddot = -3.0*H*psidot - dV_dpsi(psi, m, beta, omega_bar)
        return adot, psiddot, H

    # 4th-order Runge-Kutta
    while t < t_max:
        # k1
        k1_a, k1_psiddot, H1 = rhs(a, psi, psidot)
        # k2
        a2 = a + 0.5*dt*k1_a
        psidot2 = psidot + 0.5*dt*k1_psiddot
        k2_a, k2_psiddot, _ = rhs(a2, psi + 0.5*dt*psidot, psidot2)
        # k3
        a3 = a + 0.5*dt*k2_a
        psidot3 = psidot + 0.5*dt*k2_psiddot
        k3_a, k3_psiddot, _ = rhs(a3, psi + 0.5*dt*psidot2, psidot3)
        # k4
        a4 = a + dt*k3_a
        psidot4 = psidot + dt*k3_psiddot
        k4_a, k4_psiddot, _ = rhs(a4, psi + dt*psidot3, psidot4)

        a      += dt*(k1_a + 2*k2_a + 2*k3_a + k4_a)/6.0
        psidot += dt*(k1_psiddot + 2*k2_psiddot + 2*k3_psiddot + k4_psiddot)/6.0
        psi    += dt*(psidot)
        t      += dt
        H = record()

    return out

def demo():
    series = frw_psi_evolve(t_max=2.0, dt=1e-3,
                            a0=1.0, psi0=0.05, psidot0=0.0,
                            rho_m0=0.3, Lambda_eff=0.7,
                            m=0.0, beta=0.0, omega_bar=0.0, V0=0.0, Gtilde=1.0)
    with open("frw_psi_series.json", "w") as f:
        json.dump(series, f)
    print("[write] frw_psi_series.json written; fields:", list(series.keys()))

if __name__ == "__main__":
    demo()
