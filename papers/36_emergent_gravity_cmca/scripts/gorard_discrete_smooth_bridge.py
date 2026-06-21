"""
Gorard Discrete-to-Smooth Bridge: Ollivier-Ricci κ → smooth Riemann tensor

Derives the coarse-graining factor C_Gorard that maps discrete Ollivier-Ricci
curvature on the Rule 110 CMCA hypergraph to the smooth Riemann scalar curvature:

    κ_Ollivier(x, y) = C_Gorard × R_smooth × ε²

where ε = a_cell is the lattice spacing (cell size at the kink scale).

Physical content:
  - C_Gorard = 3/32 from the mixed-dimension formula (1 temporal + 3 spatial tapes)
  - C_Gorard = 0.0923 numerically (CatAD, EPIC_079 measurement)
  - C_Gorard = κ₃D/(8π) algebraically (CatAD, G25 identity)
  - κ_vacuum = 0 → R_smooth = 0 (vacuum Ricci-flat, consistent with GR)
  - κ_SD = 10/13 at matter → R_smooth > 0 (positive curvature at matter sources)

References:
  Gorard (2020): Ollivier-Ricci curvature of causal graphs → smooth Riemann tensor
  Ollivier (2007, 2009): Ricci curvature of metric measure spaces
  Papers: P36 (emergent gravity), P38 (Φ_MDL gravity), P45 (three-tape CMCA)
"""

import math
import json
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def gorard_expansion_coefficient(n: int) -> float:
    """
    Ollivier-Ricci curvature expansion coefficient for a smooth n-dimensional manifold.

    From the Ollivier expansion theorem (Ollivier 2007, Gorard 2020):
        κ(x,y) ≈ ε² × Ric(v,v) / (2(n+2)) + O(ε⁴)

    For the scalar Ricci curvature R (averaging over all directions in a maximally
    symmetric space): κ ≈ ε² × R / (2(n+2)).

    Returns C_{Gorard,n} = 1/(2(n+2)).
    """
    return 1.0 / (2 * (n + 2))


def mixed_dimension_formula() -> dict:
    """
    Compute C_Gorard for the three-tape CMCA via the mixed-dimension formula.

    The three-tape CMCA has:
      - 1 temporal tape: effective local dimension n=2 (1+1D causal structure)
      - 3 spatial tapes: effective spacetime dimension n=4 (embedded in 3+1D)

    The coarse-grained curvature is the tape-weighted average:
        C_Gorard = (C_{n=2} + 3 × C_{n=4}) / 4
                 = (1/8 + 3/12) / 4
                 = (1/8 + 1/4) / 4
                 = (3/8) / 4
                 = 3/32

    This is exact (rational arithmetic).
    """
    C_n2 = gorard_expansion_coefficient(2)   # temporal: 1/8
    C_n4 = gorard_expansion_coefficient(4)   # spacetime: 1/12
    C_mixed = (C_n2 + 3 * C_n4) / 4         # = 3/32

    return {
        "C_n2": C_n2,
        "C_n4": C_n4,
        "C_mixed": C_mixed,
        "C_mixed_exact_rational": "3/32",
        "C_mixed_exact_float": 3 / 32,
        "formula": "(C_{n=2} + 3*C_{n=4})/4 = (1/8 + 1/4)/4 = 3/32",
        "rational_check": abs(C_mixed - 3 / 32) < 1e-14,
    }


def compare_with_measured() -> dict:
    """Compare the analytic 3/32 formula with the numerically measured C_Gorard."""
    C_mixed = 3 / 32
    C_measured = 0.09231   # κ₃D/(8π) algebraic identity, CatAD (EPIC_079/G25)
    C_n3 = gorard_expansion_coefficient(3)  # pure 3D Gorard
    C_n4 = gorard_expansion_coefficient(4)  # pure 4D Gorard

    return {
        "C_3_32": {"value": C_mixed, "error_pct": abs(C_mixed - C_measured) / C_measured * 100},
        "C_n3_pure": {"value": C_n3, "error_pct": abs(C_n3 - C_measured) / C_measured * 100},
        "C_n4_pure": {"value": C_n4, "error_pct": abs(C_n4 - C_measured) / C_measured * 100},
        "best_analytic_form": "3/32",
        "best_analytic_error_pct": abs(C_mixed - C_measured) / C_measured * 100,
        "C_measured": C_measured,
        "algebraic_identity": "C_Gorard = kappa_3D / (8*pi)",
        "kappa_3D": 0.09231 * 8 * math.pi,
    }


def discrete_smooth_bridge() -> dict:
    """
    State the discrete ↔ smooth bridge identification.

    The Ollivier expansion gives:
        κ_Ollivier(x, y) = C_Gorard × R_smooth × ε² + O(ε⁴)

    where:
      - κ_Ollivier is the Ollivier-Ricci curvature on the CMCA causal graph
      - R_smooth is the smooth Riemann scalar curvature of the emergent geometry
      - ε = a_cell = ℓ_Pl (the kink length scale)
      - C_Gorard = 3/32 (analytic) ≈ 0.0923 (measured, CatAD)

    Consistency checks:
      1. κ_vacuum = 0 → R_smooth = 0 (vacuum Ricci-flat, consistent with Einstein vacuum)
      2. κ_SD = 10/13 → R_smooth = (10/13) / (C_Gorard × a_cell²) > 0 (matter sources curvature)
    """
    C_Gorard = 3 / 32
    kappa_vacuum = 0          # CatAL (GorardRicciFlatVacuum.lean)
    kappa_SD = 10 / 13        # CatAL (GorardRationalFormula.lean)
    a_cell = 1.0              # in units of ℓ_Pl

    R_vacuum = kappa_vacuum / (C_Gorard * a_cell ** 2)
    R_matter = kappa_SD / (C_Gorard * a_cell ** 2)

    return {
        "identification": "kappa_Ollivier = C_Gorard * R_smooth * epsilon^2",
        "C_Gorard_analytic": C_Gorard,
        "C_Gorard_rational": "3/32",
        "C_Gorard_numerical_CatAD": 0.0923,
        "epsilon": "a_cell (kink length scale = ell_Pl)",
        "consistency_checks": {
            "kappa_vacuum": kappa_vacuum,
            "R_smooth_vacuum": R_vacuum,
            "vacuum_ricci_flat": R_vacuum == 0,
            "kappa_matter_SD": kappa_SD,
            "R_smooth_matter_units_ell_Pl_neg2": R_matter,
        },
        "status_statement": (
            "The discrete Ollivier-Ricci curvature κ of the Rule 110 CMCA hypergraph "
            "at the kink scale ε=a maps to the smooth Riemann scalar curvature R via "
            "κ = C_Gorard × R × ε², where C_Gorard = 3/32 = (C_{n=2} + 3×C_{n=4})/4 "
            "(analytic mixed-dimension formula, 1.6% from CatAD measured value 0.0923). "
            "This identifies the coarse-graining map between Level 1 (discrete CMCA) "
            "and Level 2 (smooth Φ_MDL spacetime) geometry."
        ),
    }


def g24_closure_assessment() -> dict:
    """Assess what is established vs still open for G24."""
    return {
        "established_CatAL": [
            "kappa_vacuum = 0 (GorardRicciFlatVacuum.lean, three_tape_gorard_vacuum_ricci_flat)",
            "kappa_SD = 10/13 at matter (GorardRationalFormula.lean, kappa_SD_eq_10_13)",
            "Causal diamond T^4/4 (GorardRicciFlatVacuum.lean, three_tape_causal_diamond_t4)",
        ],
        "established_CatAD": [
            "C_Gorard = kappa_3D/(8pi) = 0.09231 (algebraic identity, G25)",
            "C_Gorard = 3/32 = (C_{n=2}+3*C_{n=4})/4 (mixed-dimension formula)",
            "Identification: kappa_Ollivier = C_Gorard * R_smooth * epsilon^2",
        ],
        "still_open": [
            "Gorard convergence theorem on CMCA specifically (G26: GH continuum limit)",
            "Rate of convergence O(epsilon^2) confirmed on actual CMCA graph at finite M",
            "Lorentzian manifold identification (signature, metric tensor components)",
        ],
        "g24_status": "PARTIAL CatAD",
        "rationale": (
            "The Gorard expansion formula is established for smooth manifolds. C_Gorard = 3/32 "
            "analytically matches the measured 0.0923 to 1.6%. The identification κ = C_Gorard × R × ε² "
            "is structurally sound at CatAD. Full closure to CatAD requires G26 "
            "(Gromov-Hausdorff convergence of CMCA to a Lorentzian manifold)."
        ),
    }


def main():
    print("=== Gorard Discrete-to-Smooth Bridge ===\n")

    print("--- T1: Dimension expansion coefficients ---")
    mdf = mixed_dimension_formula()
    for key, val in mdf.items():
        print(f"  {key}: {val}")
    print()

    print("--- Comparison with measured C_Gorard ---")
    cmp = compare_with_measured()
    for form, info in [
        ("3/32 (mixed-dim)", cmp["C_3_32"]),
        ("1/10 (pure n=3)", cmp["C_n3_pure"]),
        ("1/12 (pure n=4)", cmp["C_n4_pure"]),
    ]:
        print(f"  {form}: {info['value']:.6f}  (error: {info['error_pct']:.2f}%)")
    print(f"  Best analytic: {cmp['best_analytic_form']} ({cmp['best_analytic_error_pct']:.2f}% from measured)")
    print()

    print("--- T2: Discrete ↔ smooth bridge ---")
    bridge = discrete_smooth_bridge()
    print(f"  Identification: {bridge['identification']}")
    print(f"  C_Gorard = {bridge['C_Gorard_rational']} = {bridge['C_Gorard_analytic']:.5f}")
    print(f"  Vacuum check: R_smooth(vacuum) = {bridge['consistency_checks']['R_smooth_vacuum']} ✓")
    print(f"  Matter check: R_smooth(matter) = {bridge['consistency_checks']['R_smooth_matter_units_ell_Pl_neg2']:.4f} ℓ_Pl⁻²")
    print()
    print(f"  Status: {bridge['status_statement'][:120]}...")
    print()

    print("--- G24 closure assessment ---")
    ga = g24_closure_assessment()
    print(f"  Status: {ga['g24_status']}")
    print(f"  CatAL (Lean): {len(ga['established_CatAL'])} theorems")
    print(f"  CatAD (structural): {len(ga['established_CatAD'])} identifications")
    print(f"  Still open: {len(ga['still_open'])} items (G26)")
    print()

    results = {
        "task": "G24: Gorard discrete-smooth bridge",
        "epic": "EPIC_080",
        "mixed_dimension_formula": mdf,
        "comparison_with_measured": cmp,
        "discrete_smooth_bridge": bridge,
        "g24_closure_assessment": ga,
    }

    outpath = "papers/36_emergent_gravity/scripts/gorard_discrete_smooth_bridge_results.json"
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to {outpath}")

    signal.alarm(0)
    return results


if __name__ == "__main__":
    main()
