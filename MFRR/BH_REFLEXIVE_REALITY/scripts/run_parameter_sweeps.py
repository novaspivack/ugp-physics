#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parameter sweep suite for QNM and TOV+Ψ tests.
Generates comprehensive CSV summaries for manuscript tables/figures.

Reference: MFRR Paper, §Black Holes in Reflexive Reality
Date: November 4, 2025
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rr_common.params import QNMParams, TOVPsiParams
from rr_common.io_helpers import write_csv

# Import test functions
import qnm_rr_shift
import tov_psi

def qnm_parameter_sweep():
    """
    Comprehensive QNM sweep:
    - l × n: (2,0..2), (3,0..3)
    - ψ₀: 1e-3 to 5e-2 (8 points, log)
    - Δ: {0.02, 0.05, 0.1, 0.2}
    - r_s: {2.2, 2.4, 3.0}
    - λ_Ψ: {0, 0.1, 0.3, 1, 3}
    """
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  QNM Parameter Sweep".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    P = QNMParams()
    
    # Sweep parameters
    ls_ns = [(2,0), (2,1), (2,2), (3,0), (3,1), (3,2), (3,3)]
    psi0_vals = np.logspace(-3, np.log10(0.05), 8)  # 1e-3 to 5e-2
    dlt_vals = [0.02, 0.05, 0.1, 0.2]
    rs_vals = [2.2, 2.4, 3.0]
    lamPsi_vals = [0.0, 0.1, 0.3, 1.0, 3.0]
    
    rows = []
    total = len(ls_ns) * len(psi0_vals) * len(dlt_vals) * len(rs_vals) * len(lamPsi_vals)
    count = 0
    
    print(f"Total configurations: {total}")
    print(f"Running sweep...\n")
    
    for l, n in ls_ns:
        for psi0 in psi0_vals:
            for dlt in dlt_vals:
                for rs in rs_vals:
                    for lamPsi in lamPsi_vals:
                        P.l = l
                        P.n = n
                        P.psi0 = psi0
                        P.dlt = dlt
                        P.rs = rs
                        P.lamPsi = lamPsi
                        
                        try:
                            r0, w0, dw = qnm_rr_shift.qnm_shift_once(P)
                            rows.append([
                                l, n, P.M, rs, dlt, psi0, lamPsi, P.alpha1, P.alpha2,
                                np.real(w0), np.imag(w0), np.real(dw), np.imag(dw)
                            ])
                            count += 1
                            if count % 100 == 0:
                                print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")
                        except Exception as e:
                            print(f"  Warning: Failed for l={l}, n={n}, rs={rs}, Δ={dlt}, ψ₀={psi0:.2e}: {e}")
    
    write_csv("csv/sweep_qnm_summary.csv",
              ["l","n","M","rs","dlt","psi0","lamPsi","alpha1","alpha2",
               "Re_w0","Im_w0","Re_dw","Im_dw"],
              rows)
    
    print(f"\n✅ QNM sweep complete: {len(rows)} configurations")
    print(f"   Output: csv/sweep_qnm_summary.csv")


def tov_parameter_sweep():
    """
    TOV+Ψ sweep:
    - M: {1.0}
    - r_s: {2.2, 2.4, 3.0}
    - Δ: {0.02, 0.05, 0.1, 0.2}
    - ψ₀: 1e-3 to 5e-2 (8 points)
    - λ_Ψ: {0, 0.1, 0.3, 1, 3}
    - (α₁, α₂): {(1e-6,0), (0,1e-6), (1e-6,1e-6)}
    """
    print("\n╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TOV+Ψ Parameter Sweep".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    P = TOVPsiParams()
    
    # Sweep parameters
    psi0_vals = np.logspace(-3, np.log10(0.05), 8)
    dlt_vals = [0.02, 0.05, 0.1, 0.2]
    rs_vals = [2.2, 2.4, 3.0]
    lamPsi_vals = [0.0, 0.1, 0.3, 1.0, 3.0]
    alpha_combos = [(1e-6, 0), (0, 1e-6), (1e-6, 1e-6)]
    
    rows = []
    total = len(psi0_vals) * len(dlt_vals) * len(rs_vals) * len(lamPsi_vals) * len(alpha_combos)
    count = 0
    
    print(f"Total configurations: {total}")
    print(f"Running sweep...\n")
    
    for psi0 in psi0_vals:
        for dlt in dlt_vals:
            for rs in rs_vals:
                for lamPsi in lamPsi_vals:
                    for alpha1, alpha2 in alpha_combos:
                        P.psi0 = psi0
                        P.dlt = dlt
                        P.rs = rs
                        P.lamPsi = lamPsi
                        P.alpha1 = alpha1
                        P.alpha2 = alpha2
                        
                        # Compute shell integral and shifts
                        r = np.linspace(2.0001*P.M, P.rmax, P.Nr)
                        psi = tov_psi.psi_profile_shell(r, P.rs, P.dlt, P.psi0)
                        Ih = tov_psi.thin_shell_integrals(r, P.M, psi, P.alpha1, P.alpha2, P.lamPsi)
                        drh = tov_psi.horizon_shift(P.M, Ih)
                        drph = tov_psi.photon_sphere_shift(P.M, Ih)
                        dbph = tov_psi.shadow_shift(P.M, Ih)
                        
                        rows.append([
                            P.M, rs, dlt, psi0, lamPsi, alpha1, alpha2,
                            Ih, drh, drph, dbph
                        ])
                        count += 1
                        if count % 50 == 0:
                            print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")
    
    write_csv("csv/sweep_tov_summary.csv",
              ["M","rs","dlt","psi0","lamPsi","alpha1","alpha2",
               "Ih","delta_r_h","delta_r_ph","delta_b_ph"],
              rows)
    
    print(f"\n✅ TOV+Ψ sweep complete: {len(rows)} configurations")
    print(f"   Output: csv/sweep_tov_summary.csv")


def main():
    print("=" * 80)
    print("BH REFLEXIVE REALITY — PARAMETER SWEEP SUITE")
    print("=" * 80)
    print()
    
    # Run sweeps
    qnm_parameter_sweep()
    tov_parameter_sweep()
    
    print("\n" + "=" * 80)
    print("✅ ALL SWEEPS COMPLETE")
    print("=" * 80)
    print("\nOutputs:")
    print("  • csv/sweep_qnm_summary.csv")
    print("  • csv/sweep_tov_summary.csv")
    print("\nUse these for manuscript tables and scaling analysis.")


if __name__ == "__main__":
    main()

