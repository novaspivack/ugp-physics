#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thin-shell and simple ODE backreaction estimates for a coherence shell
outside a Schwarzschild BH: δr_h, δr_ph, δb_ph scalings.

Reference: MFRR Paper, §Static Spherical Configurations with Coherence Shell
Date: November 4, 2025

Outputs:
  - csv/tov_psi_shell.csv
  - figs/tov_psi_summary.png
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rr_common.params import TOVPsiParams
from rr_common.numerics import r_to_rstar
from rr_common.io_helpers import write_csv

def psi_profile_shell(r, rs, dlt, psi0):
    psi = np.zeros_like(r)
    mask = (r>=rs) & (r<=rs+dlt)
    psi[mask] = psi0
    return psi

def thin_shell_integrals(r, M, psi, alpha1, alpha2, lamPsi):
    f = 1.0 - 2.0*M/r
    dpsi_dr = np.gradient(psi, r, edge_order=2)
    integrand = alpha1*(psi**2) + alpha2*(f*(dpsi_dr**2))
    return lamPsi * np.trapz(integrand, r)

def horizon_shift(M, Ih):
    """δr_h ~ 8πG r_h^2 * ∫(coherence energy density) dr ; G=1 units."""
    r_h = 2.0*M
    return 8.0*np.pi * (r_h**2) * Ih

def photon_sphere_shift(M, Ih):
    """Scaling proxy: δr_ph ∝ Ih; set coefficient for order-of-mag."""
    # r_ph = 3M for Schwarzschild
    c = 2.0*np.pi * (3.0*M)**2
    return c * Ih * 0.1

def shadow_shift(M, Ih):
    """Shadow impact parameter b_ph = 3√3 M; δb ~ κ Ih."""
    return (3.0*np.sqrt(3.0)*M) * (0.05 * Ih)

def run_scan():
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  Static Spherical Configurations with Coherence Shell".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    P = TOVPsiParams()
    r = np.linspace(2.0001*P.M, P.rmax, P.Nr)
    psi = psi_profile_shell(r, P.rs, P.dlt, P.psi0)
    Ih = thin_shell_integrals(r, P.M, psi, P.alpha1, P.alpha2, P.lamPsi)
    drh = horizon_shift(P.M, Ih)
    drph = photon_sphere_shift(P.M, Ih)
    dbph = shadow_shift(P.M, Ih)
    
    print(f"\nConfiguration:")
    print(f"  M = {P.M}, r_s = {P.rs}, Δ = {P.dlt}, Ψ₀ = {P.psi0}")
    print(f"  λ_Ψ = {P.lamPsi}, α₁ = {P.alpha1}, α₂ = {P.alpha2}")
    print(f"\nResults:")
    print(f"  Shell integral I_h = {Ih:.4e}")
    print(f"  δr_h  = {drh:.4e}")
    print(f"  δr_ph = {drph:.4e}")
    print(f"  δb_ph = {dbph:.4e}")
    
    write_csv("csv/tov_psi_shell.csv",
              ["M","rs","dlt","psi0","lamPsi","alpha1","alpha2","Ih","delta_r_h","delta_r_ph","delta_b_ph"],
              [[P.M,P.rs,P.dlt,P.psi0,P.lamPsi,P.alpha1,P.alpha2,Ih,drh,drph,dbph]])
    
    # quick bar view
    vals = [abs(drh), abs(drph), abs(dbph)]
    labels = [r"$|\delta r_h|$", r"$|\delta r_{\rm ph}|$", r"$|\delta b_{\rm ph}|$"]
    plt.figure(figsize=(6.2,3.6))
    plt.bar(labels, vals)
    plt.title("Thin-shell backreaction magnitudes (scaling proxies)")
    plt.ylabel("Geometric units")
    plt.tight_layout()
    Path("figs").mkdir(exist_ok=True)
    plt.savefig("figs/tov_psi_summary.png", dpi=160)
    
    print(f"\n✅ Results saved:")
    print(f"   csv/tov_psi_shell.csv")
    print(f"   figs/tov_psi_summary.png")

if __name__ == "__main__":
    run_scan()

