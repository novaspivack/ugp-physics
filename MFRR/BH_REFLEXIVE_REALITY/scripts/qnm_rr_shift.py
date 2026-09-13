#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QNM baseline + RR first-order shift for Schwarzschild axial modes using
Pöschl–Teller near-peak approximation and a thin RR shell.

Reference: MFRR Paper, §Black Holes in Reflexive Reality
Date: November 4, 2025

Outputs:
  - csv/qnm_rr_scan.csv
  - figs/qnm_rr_summary.png
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rr_common.params import QNMParams
from rr_common.numerics import (r_to_rstar, V_schwarzschild_axial,
                                find_peak_uniform, second_derivative_stencil,
                                gaussian_window, poschl_teller_qnm_from_peak)
from rr_common.io_helpers import write_csv

def psi_profile_shell(r, rs, dlt, psi0, mpsi=0.0):
    """
    Simple C1 hat or flat-top profile in [rs, rs+dlt].
    mpsi>0 optionally adds mild decay inside the shell.
    """
    psi = np.zeros_like(r)
    mask = (r >= rs) & (r <= rs + dlt)
    if not np.any(mask):
        return psi
    # flat-top (can be replaced with smooth bump if desired)
    psi[mask] = psi0*np.exp(-mpsi*(r[mask]-rs))
    return psi

def rr_deltaV(r, M, psi, params: QNMParams):
    """
    δV^RR ≈ λΨ (α1 Ψ^2 + α2 e^{-λ} (dΨ/dr)^2), evaluated in r (we integrate over r*).
    """
    f = 1.0 - 2.0*M/r
    # central finite diff in r
    dpsi_dr = np.gradient(psi, r, edge_order=2)
    rho = params.alpha1*(psi**2) + params.alpha2*(f*(dpsi_dr**2))
    return params.lamPsi * rho

def qnm_shift_once(P: QNMParams):
    # radial grid in r:
    r = np.linspace(P.rmin, P.rmax, P.Nr)
    rstar = r_to_rstar(r, P.M)
    # potential
    V = V_schwarzschild_axial(r, P.M, P.l)
    # find peak:
    i0 = find_peak_uniform(r, V)
    r0, rstar0, V0 = r[i0], rstar[i0], V[i0]
    # get V'' wrt r*:
    # resample to nearly uniform r* if needed (rstar is monotonic):
    # We'll just use local stencil on r* grid
    Vpp = second_derivative_stencil(rstar, V, i0)
    w0 = poschl_teller_qnm_from_peak(V0, Vpp, P.n)  # complex baseline
    # thin shell Psi:
    psi = psi_profile_shell(r, P.rs, P.dlt, P.psi0, P.mpsi)
    dV = rr_deltaV(r, P.M, psi, P)
    # estimate δω using local window overlap near r* peak
    sigma = 0.6 * (rstar[i0+50]-rstar[i0-50]) if (i0>50 and i0<P.Nr-50) else 1.0
    win = gaussian_window(rstar, rstar0, sigma)
    # approximate adjoint ~ complex conjugate of localized mode envelope (heuristic)
    num = np.trapz(win * dV, rstar)
    den = 2.0*w0 * np.trapz(win, rstar)
    dw = - num/den
    return r0, w0, dw

def scan_and_plot():
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  QNM Frequency Shifts from Information Sector".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    rows = []
    ls = [2, 3]
    ns = [0, 1]
    P = QNMParams()
    
    print(f"\nConfiguration:")
    print(f"  M = {P.M}, Shell: r_s={P.rs}, Δ={P.dlt}, Ψ₀={P.psi0}")
    print(f"  λ_Ψ={P.lamPsi}, α₁={P.alpha1}, α₂={P.alpha2}")
    print(f"\nComputing QNM shifts...\n")
    
    fig, ax = plt.subplots(1,2, figsize=(11,4.2))
    for l in ls:
        for n in ns:
            P.l = l; P.n = n
            r0, w0, dw = qnm_shift_once(P)
            rows.append([l, n, np.real(w0), np.imag(w0),
                         np.real(dw), np.imag(dw), P.rs, P.dlt, P.psi0,
                         P.lamPsi, P.alpha1, P.alpha2])
            print(f"  l={l}, n={n}: ω₀ = {w0:.6f}, δω = {dw:.2e}")
            ax[0].scatter(np.real(w0), -np.imag(w0), label=f"l={l},n={n}", s=60)
            ax[1].scatter(np.real(dw), -np.imag(dw), label=f"l={l},n={n}", s=60)
    
    write_csv("csv/qnm_rr_scan.csv",
              ["l","n","Re(w0)","Im(w0)","Re(dw)","Im(dw)","rs","dlt","psi0","lamPsi","alpha1","alpha2"],
              rows)
    
    ax[0].set_title("Baseline QNMs (PT estimate)")
    ax[0].set_xlabel("Re(ω₀)"); ax[0].set_ylabel("-Im(ω₀)")
    ax[1].set_title("RR first-order δω (thin shell)")
    ax[1].set_xlabel("Re(δω)"); ax[1].set_ylabel("-Im(δω)")
    for a in ax: a.grid(True, alpha=0.3)
    ax[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    Path("figs").mkdir(exist_ok=True)
    fig.savefig("figs/qnm_rr_summary.png", dpi=160)
    
    print(f"\n✅ Results saved:")
    print(f"   csv/qnm_rr_scan.csv")
    print(f"   figs/qnm_rr_summary.png")

if __name__ == "__main__":
    scan_and_plot()

