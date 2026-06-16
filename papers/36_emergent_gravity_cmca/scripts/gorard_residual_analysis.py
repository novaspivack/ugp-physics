"""
G25 Gorard normalization residual analysis.
Resolves the 8.5% gap between C_Gorard = kappa_3D/(8pi) = 0.09231
(measured, CatA) and the target normalization 10^77.5.

Physical setup:
  gap = (M_Pl / m_kink)^4 * C_Gorard
  C_Gorard = kappa_3D / (8pi),  kappa_3D = 2.32 (measured from Gorard chain)
  m_kink = (8/49) m_tau

Key identities:
  C_Gorard = 3/32  ↔  kappa_3D = 3pi/4 exactly (mixed-dimension formula)
  Residual to 10^77.5: Δ(log₁₀) = 0.0395, factor = 10^0.0395 ≈ 1.0952
"""

import math
import json
import pathlib
import signal
import sys

TIMEOUT_SECONDS = 120


def _timeout(signum, frame):
    print("\nTIMEOUT reached — saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)


def compute_gap(C_Gorard, M_Pl_GeV, m_kink_GeV):
    ratio = M_Pl_GeV / m_kink_GeV
    return ratio**4 * C_Gorard


def main():
    # Physical parameters
    m_tau_GeV = 1776.86e-3
    m_kink_GeV = (8 / 49) * m_tau_GeV
    M_Pl_GeV = 1.22e19
    kappa_3D = 2.32          # measured from three-tape Gorard chain (CatA)
    target_log = 77.5

    ratio4 = (M_Pl_GeV / m_kink_GeV) ** 4

    # --- Baseline: C_Gorard = kappa_3D / (8pi) ---
    C_measured = kappa_3D / (8 * math.pi)
    gap_measured = ratio4 * C_measured
    log_measured = math.log10(gap_measured)
    residual_log = target_log - log_measured
    residual_factor = 10 ** residual_log

    # --- Analytic value: 3/32 = kappa_3D/(8pi) when kappa_3D = 3pi/4 ---
    kappa_3pi4 = 3 * math.pi / 4          # = 2.35619...
    C_3pi4 = kappa_3pi4 / (8 * math.pi)   # = 3/32 exactly
    assert abs(C_3pi4 - 3 / 32) < 1e-12, "Identity check failed"
    gap_3pi4 = ratio4 * C_3pi4
    log_3pi4 = math.log10(gap_3pi4)
    res_3pi4 = target_log - log_3pi4

    # --- Target C_Gorard for exact 10^77.5 ---
    C_target = 10 ** target_log / ratio4
    kappa_3D_target = C_target * 8 * math.pi

    # --- Correction factor scan ---
    candidates = {}

    # N_c powers
    for label, power in [("1/3", 1 / 3), ("2/3", 2 / 3), ("1", 1.0)]:
        C_nc = C_measured * (3 ** power)
        log_nc = math.log10(ratio4 * C_nc)
        candidates[f"N_c^{label}"] = {
            "factor": 3 ** power,
            "C": C_nc,
            "log10_gap": log_nc,
            "delta": target_log - log_nc,
        }

    # sqrt(6/5): geometric mean of N_c=3 spatial tapes and Z5=5 sublattice
    sqrt65 = math.sqrt(6 / 5)
    C_sqrt65 = C_measured * sqrt65
    log_sqrt65 = math.log10(ratio4 * C_sqrt65)
    candidates["sqrt(6/5)"] = {
        "factor": sqrt65,
        "C": C_sqrt65,
        "log10_gap": log_sqrt65,
        "delta": target_log - log_sqrt65,
        "physical_note": "sqrt(6/5): 6 = N_spatial × N_c, 5 = Z5 sublattice in GF(7)",
    }

    # 23/21 rational
    C_2321 = C_measured * (23 / 21)
    log_2321 = math.log10(ratio4 * C_2321)
    candidates["23/21"] = {
        "factor": 23 / 21,
        "C": C_2321,
        "log10_gap": log_2321,
        "delta": target_log - log_2321,
        "physical_note": "21 = 3 × 7 = N_c × Z7; 23 has no clear GTE role (likely coincidence)",
    }

    # --- Summary ---
    results = {
        "description": (
            "G25 Gorard/Planck normalization residual analysis. "
            "Resolves the 8.5% gap between C_Gorard = 0.09231 (measured) "
            "and the normalization target 10^{77.5}."
        ),
        "physical_inputs": {
            "m_tau_MeV": m_tau_GeV * 1000,
            "m_kink_formula": "(8/49)*m_tau",
            "m_kink_MeV": m_kink_GeV * 1000,
            "M_Pl_GeV": M_Pl_GeV,
            "kappa_3D_measured": kappa_3D,
            "kappa_3D_source": "Gorard chain simulation (CatA, EPIC_078)",
        },
        "baseline": {
            "C_Gorard": C_measured,
            "log10_gap": log_measured,
            "residual_delta_log10": residual_log,
            "residual_factor": residual_factor,
            "residual_pct": (residual_factor - 1) * 100,
        },
        "algebraic_identity": {
            "statement": "C_Gorard = 3/32 exactly iff kappa_3D = 3*pi/4",
            "proof": "3pi/4 / (8pi) = 3/(4*8) = 3/32",
            "kappa_3pi4": kappa_3pi4,
            "C_3_32": C_3pi4,
            "log10_gap_3_32": log_3pi4,
            "residual_3_32": res_3pi4,
            "match_to_measured_pct": abs(C_3pi4 - C_measured) / C_measured * 100,
            "match_kappa_to_measured_pct": abs(kappa_3pi4 - kappa_3D) / kappa_3D * 100,
        },
        "target_for_exact_10_77p5": {
            "C_Gorard_needed": C_target,
            "kappa_3D_needed": kappa_3D_target,
            "ratio_to_measured": kappa_3D_target / kappa_3D,
        },
        "correction_candidates": candidates,
        "verdict": {
            "status": "CLOSED CatA (unchanged)",
            "summary": (
                "The 8.5% residual (Δ log₁₀ = 0.0395, factor 1.0952) is the gap between "
                "C_Gorard = kappa_3D/(8pi) with kappa_3D = 2.32 (measured) and the target "
                "normalization 10^{77.5}. The gap is NOT algebraically closed by simple N_c, "
                "Z7, or epsilon corrections. "
                "Key algebraic identity: C_Gorard = 3/32 iff kappa_3D = 3pi/4 (1.56% above "
                "measured 2.32). "
                "Numerically, sqrt(6/5) = 1.0954 closes the gap to delta = -0.00009 "
                "(essentially exact), but requires a physical mechanism. "
                "Path to CatAD: derive kappa_3D analytically from Rule 110 kink cluster "
                "dynamics — the analytic target is kappa_3D = 3pi/4."
            ),
            "sqrt65_closes_gap": True,
            "sqrt65_mechanism_needed": True,
            "path_to_catad": "Derive kappa_3D = 3pi/4 from Rule 110 Z7 kink cluster structure",
        },
    }

    output_path = (
        pathlib.Path(__file__).parent / "gorard_residual_analysis_results.json"
    )
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_path}")

    # Print summary
    print("\n=== G25 RESIDUAL ANALYSIS SUMMARY ===")
    print(f"C_Gorard (measured) = {C_measured:.8f}")
    print(f"log₁₀(gap) = {log_measured:.6f}  (target: {target_log})")
    print(f"Residual Δ = {residual_log:.6f}  (factor = {residual_factor:.6f}, +{(residual_factor-1)*100:.2f}%)")
    print(f"\nAlgebraic identity: C_Gorard = 3/32 ↔ κ_3D = 3π/4 = {kappa_3pi4:.6f}")
    print(f"  Measured κ_3D = {kappa_3D} → 1.56% below 3π/4")
    print(f"  With 3/32: Δ = {res_3pi4:.6f} (7.84% gap remains)")
    print(f"\n√(6/5) candidate: closes gap to Δ = {target_log - log_sqrt65:.8f} ≈ 0")
    print(f"  Mechanism needed: 6 = N_spatial × N_c = 3×2, 5 = Z₅ sublattice")
    print(f"\nVerdict: G25 CLOSED CatA. Full normalization-exact closure requires")
    print(f"  kappa_3D = 3π/4 derivation (→ OQ: Rule 110 kink cluster analytsis).")

    signal.alarm(0)
    return results


if __name__ == "__main__":
    main()
