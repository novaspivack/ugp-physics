#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JT island toy: RR dressing f(Ψ)=1+λΨ γ1 Ψ^2 and Page-time fractional shift.

Reference: MFRR Paper, §JT Island Toy Model with Coherence-Dressed Entropy
Date: November 4, 2025

Outputs:
  - csv/jt_rr_page.csv
  - figs/jt_rr_page.png
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rr_common.params import JTParams
from rr_common.io_helpers import write_csv

def page_shift_fraction(p: JTParams):
    """
    δ = (t_Page^RR - t_Page^semi)/t_Page^semi
      = λΨ γ1 <Ψ^2> / φ_QES * (∂φ/∂log A)|semi  + O(λΨ^2).
    """
    return p.lamPsi * p.gamma1 * (p.psi2_bar / p.phi_QES) * p.dlogphi_dlogA

def main():
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  JT Island + Coherence-Dressed Horizon Entropy".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    p = JTParams()
    lam_vals = np.logspace(-2, +1, 30)  # 0.01 .. 10
    rows = []
    fracs = []
    
    print(f"\nConfiguration:")
    print(f"  γ₁ = {p.gamma1}, ⟨Ψ²⟩_QES = {p.psi2_bar:.2e}")
    print(f"  φ_QES = {p.phi_QES}, ∂φ/∂logA = {p.dlogphi_dlogA}")
    print(f"\nScanning λ_Ψ ∈ [0.01, 10.0]...\n")
    
    for lam in lam_vals:
        p.lamPsi = lam
        d = page_shift_fraction(p)
        rows.append([lam, p.gamma1, p.psi2_bar, p.phi_QES, p.dlogphi_dlogA, d])
        fracs.append(d)
    
    write_csv("csv/jt_rr_page.csv",
              ["lamPsi","gamma1","psi2_bar","phi_QES","dlogphi_dlogA","delta_fraction"],
              rows)
    
    print(f"  Page-time shift range: [{min(fracs):.4e}, {max(fracs):.4e}]")
    
    plt.figure(figsize=(6.0,3.6))
    plt.loglog(lam_vals, np.abs(fracs))
    plt.xlabel(r"$\lambda_\Psi$")
    plt.ylabel(r"$|(t_{\rm Page}^{\rm RR}-t_{\rm Page}^{\rm semi})/t_{\rm Page}^{\rm semi}|$")
    plt.title("JT Page-time shift (RR toy)")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    Path("figs").mkdir(exist_ok=True)
    plt.savefig("figs/jt_rr_page.png", dpi=160)
    
    print(f"\n✅ Results saved:")
    print(f"   csv/jt_rr_page.csv")
    print(f"   figs/jt_rr_page.png")

if __name__ == "__main__":
    main()

