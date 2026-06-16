#!/usr/bin/env python3
"""
M_Z ρ̂-corrected prediction using GTE-internal top quark pole mass.

Computes M_Z^GTE(ρ̂-corrected) = M_Z^tree / √ρ̂ where:
  - M_Z^tree = M_W^GTE × √(13/10) = 91629 MeV (CatAL, Weinberg relation)
  - ρ̂ = 1 + 3G_F m_t^2 / (8π²√2) (leading EW self-energy correction)
  - m_t = 172610 MeV (GTE-internal, b_t/b_b ratio from TT+VV cascade, CatAD)
  - G_F = 1.1663788e-5 GeV^-2 = 1.1663788e-11 MeV^-2 (PDG 2024 input)

Expected output:
  M_Z^GTE(ρ̂-corrected) ≈ 91204 MeV
  Gap from PDG M_Z (91188 MeV): +16 MeV = +8σ
"""

import math
import json
import signal
import sys

TIMEOUT_SECONDS = 60


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def compute_mz_rho_corrected():
    """Compute M_Z^GTE after ρ̂ (rho-hat) correction using GTE-internal m_t."""

    # --- GTE-internal inputs ---
    M_W_GTE_MeV = 80364.0          # MeV (GTE two-loop, CatAD)
    m_t_GTE_MeV = 172610.0         # MeV (GTE cascade b_t/b_b = 337920/8191, CatAD)
    sin2_thW_GTE = 3.0 / 13.0      # tree-level (CatAL, algebraic invariant)

    # --- External PDG input (G_F from muon decay) ---
    G_F_GeV2 = 1.1663788e-5        # GeV^-2 (PDG 2024)
    G_F_MeV2 = G_F_GeV2 * 1e-6    # MeV^-2 (1 GeV = 1000 MeV, so 1/GeV^2 = 1e-6/MeV^2)

    # --- PDG reference ---
    M_Z_PDG_MeV = 91188.0          # MeV (PDG 2024: 91.1880 ± 0.0020 GeV)
    M_Z_sigma_MeV = 2.0            # MeV (PDG 1σ)

    # --- Tree-level M_Z ---
    # M_Z^tree = M_W / cos(θ_W) = M_W × √(13/10) since cos²θ_W = 1 - 3/13 = 10/13
    M_Z_tree_MeV = M_W_GTE_MeV * math.sqrt(13.0 / 10.0)

    # --- ρ̂ correction (leading top-quark EW self-energy) ---
    delta_rho = 3 * G_F_MeV2 * m_t_GTE_MeV**2 / (8 * math.pi**2 * math.sqrt(2))
    rho_hat = 1 + delta_rho

    # --- ρ̂-corrected M_Z ---
    M_Z_corrected_MeV = M_Z_tree_MeV / math.sqrt(rho_hat)

    # --- Gap from PDG ---
    gap_MeV = M_Z_corrected_MeV - M_Z_PDG_MeV
    sigma_gap = gap_MeV / M_Z_sigma_MeV

    # --- Comparison with PDG m_t input ---
    m_t_PDG_MeV = 172690.0         # MeV (PDG 2024: 172.57 ± 0.29 GeV)
    delta_rho_PDG = 3 * G_F_MeV2 * m_t_PDG_MeV**2 / (8 * math.pi**2 * math.sqrt(2))
    rho_hat_PDG = 1 + delta_rho_PDG
    M_Z_corrected_PDG_MeV = M_Z_tree_MeV / math.sqrt(rho_hat_PDG)

    results = {
        "description": "M_Z ρ̂-corrected using GTE-internal top pole mass",
        "inputs": {
            "M_W_GTE_MeV": M_W_GTE_MeV,
            "m_t_GTE_MeV": m_t_GTE_MeV,
            "m_t_GTE_source": "b_t/b_b = 337920/8191, TT+VV cascade, CatAD",
            "sin2_theta_W_GTE": sin2_thW_GTE,
            "G_F_GeV2": G_F_GeV2,
            "G_F_source": "PDG 2024 muon decay (external input)",
        },
        "computation": {
            "M_Z_tree_MeV": M_Z_tree_MeV,
            "delta_rho_top": delta_rho,
            "rho_hat": rho_hat,
            "8pi2sqrt2": 8 * math.pi**2 * math.sqrt(2),
        },
        "result": {
            "M_Z_GTE_rho_corrected_MeV": M_Z_corrected_MeV,
            "M_Z_PDG_MeV": M_Z_PDG_MeV,
            "M_Z_sigma_MeV": M_Z_sigma_MeV,
            "gap_MeV": gap_MeV,
            "gap_sigma": sigma_gap,
            "gap_percent": gap_MeV / M_Z_PDG_MeV * 100,
            "within_1sigma": abs(sigma_gap) < 1.0,
            "within_8sigma": abs(sigma_gap) < 8.5,
        },
        "comparison_PDG_mt_input": {
            "m_t_PDG_MeV": m_t_PDG_MeV,
            "M_Z_corrected_MeV": M_Z_corrected_PDG_MeV,
            "gap_MeV": M_Z_corrected_PDG_MeV - M_Z_PDG_MeV,
            "delta_shift_from_GTE_mt": M_Z_corrected_MeV - M_Z_corrected_PDG_MeV,
        },
        "oq_verdict": {
            "OQ_MZ_POLE_MT_part_A": "RESOLVED: GTE gives m_t = 172610 MeV (pole mass, CatAD)",
            "OQ_MZ_POLE_MT_part_B": "OPEN: ρ̂ correction +8.1σ from PDG; not within 1σ",
            "note": "Gap requires full EW oblique corrections (OQ-MZ-FULL-EW), not just ρ̂_top",
        },
    }
    return results


def main():
    results = compute_mz_rho_corrected()

    print("=== M_Z ρ̂-Corrected Prediction (GTE-Internal m_t) ===\n")
    comp = results["computation"]
    res = results["result"]

    print(f"Tree-level M_Z:    {comp['M_Z_tree_MeV']:.2f} MeV = {comp['M_Z_tree_MeV']/1000:.4f} GeV")
    print(f"Δρ_top:            {comp['delta_rho_top']:.6f}")
    print(f"ρ̂:                 {comp['rho_hat']:.6f}")
    print(f"8π²√2:             {comp['8pi2sqrt2']:.4f}")
    print(f"\nρ̂-corrected M_Z:  {res['M_Z_GTE_rho_corrected_MeV']:.2f} MeV")
    print(f"PDG M_Z:           {res['M_Z_PDG_MeV']:.2f} ± {res['M_Z_sigma_MeV']:.1f} MeV")
    print(f"Gap:               {res['gap_MeV']:+.2f} MeV = {res['gap_sigma']:+.1f}σ = {res['gap_percent']:+.4f}%")
    print(f"\nWithin 1σ:  {res['within_1sigma']}")
    print(f"\n--- m_t substitution sensitivity ---")
    cmp = results["comparison_PDG_mt_input"]
    print(f"With PDG m_t = {cmp['m_t_PDG_MeV']:.0f} MeV: M_Z = {cmp['M_Z_corrected_MeV']:.2f} MeV")
    print(f"Shift from using GTE vs PDG m_t: {cmp['delta_shift_from_GTE_mt']:+.2f} MeV")
    print(f"\n=== OQ-MZ-POLE-MT Verdict ===")
    verd = results["oq_verdict"]
    print(f"Part A: {verd['OQ_MZ_POLE_MT_part_A']}")
    print(f"Part B: {verd['OQ_MZ_POLE_MT_part_B']}")
    print(f"Note:   {verd['note']}")

    out_path = "/Users/nova/ugp-physics/papers/48_gte_complete_theory/scripts/mz_rho_corrected_gteinternal_mt_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nArtifact: {out_path}")


if __name__ == "__main__":
    main()
    signal.alarm(0)
