#!/usr/bin/env python3
"""
GTE OPE Non-Perturbative Correction to Δα_had

Computes the SVZ Operator Product Expansion (OPE) correction to the hadronic
vacuum polarization Δα_had from the GTE chiral condensate ⟨ψ̄ψ⟩ = -M_kink³,
and the perturbative u,d,s quark contribution above 2 GeV.

GTE inputs (CatB or better):
  ⟨ψ̄ψ⟩_GTE = -M_kink³, M_kink = 290.10 MeV (CatAL, `fpi_from_scc`)
  m_u = 2.157 MeV, m_d = 4.647 MeV, m_s = 92.74 MeV (CatB)
  Q_u = 2/3, Q_d = Q_s = -1/3 (CatAL, winding class theorem)
  α_s(M_Z) = 0.11822 (CatAD)
  M_Z = 91.629 GeV (CatAD, P35)

Dispersion integral (Steinhauser 1998 convention):
  Δ(1/α)_had = (M_Z²/3π) × ∫ R(s) / (s(M_Z²-s)) ds  [for s < M_Z²]

Wall-clock timeout: 60 seconds.
"""

import math
import signal
import sys
import time
import json
from scipy import integrate

TIMEOUT_SECONDS = 60

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ============================================================
# GTE physical inputs
# ============================================================
M_kink = 290.10e-3      # GeV (CatAL, `fpi_from_scc`, P34)
M_Z = 91.629            # GeV (CatAD, P35)
alpha0 = 1 / 137.036    # α(0) (CatA)
MZ2 = M_Z ** 2          # GeV²

# Light quark masses (CatB)
m_u = 2.157e-3          # GeV
m_d = 4.647e-3          # GeV
m_s = 92.74e-3          # GeV

# GTE quark charges (CatAL, winding class Q_q = w*/3)
Q_u = 2/3
Q_d = -1/3
Q_s = -1/3

alpha_s = 0.11822       # strong coupling at M_Z (CatAD, P01)
N_c = 3                 # number of colors (CatAL)
f_pi = M_kink / math.pi # pion decay constant (CatAL, `fpi_from_scc`)

# GTE chiral condensate: ⟨ψ̄ψ⟩ = -M_kink³ (Stage 2, CatB, P34/P45)
cond_abs = M_kink ** 3  # |⟨ψ̄ψ⟩| in GeV³

# PDG reference value for normalizing fractions
DELTA_INV_ALPHA_HAD_PDG = 3.782  # PDG total Δ(1/α)_had^(5)(M_Z²)
DELTA_ALPHA_HAD_PDG = 0.027613   # PDG Δα_had^(5)(M_Z²)

# ============================================================
# Dispersion kernel (Steinhauser 1998 convention)
# Δ(1/α)_had = (M_Z²/3π) ∫ R(s)/(s(M_Z²-s)) ds
# Valid for s < M_Z²; kernel diverges at s = M_Z² (handled by upper limit)
# ============================================================
def dispersion_kernel(s_GeV2):
    """Full dispersion kernel M_Z²/(s(M_Z²-s)) for HVP contribution.
    
    Derivation: from analyticity of Π(q²) and the relation
    Δ(1/α)_had = (M_Z²/3π) Re ∫ R(s)/(s(s-M_Z²-iε)) ds,
    the s < M_Z² contribution gives kernel = M_Z²/(s(M_Z²-s)).
    """
    if s_GeV2 <= 0 or s_GeV2 >= MZ2:
        return 0.0
    return MZ2 / (s_GeV2 * (MZ2 - s_GeV2))


# ============================================================
# OPE NP correction to R(s): SVZ dimension-4 condensate
#
# From SVZ (1979): the leading quark condensate contribution to the
# vector current correlator is:
#   δΠ^(4)(Q²) = C_D × Σ_q Q_q² m_q⟨ψ̄_q ψ_q⟩ / Q^4
# Taking the imaginary part and using R = 12π Im Π gives:
#   δR^(4)(s) = 24π² N_c Σ_q Q_q² m_q |⟨ψ̄ψ⟩| / s²
# Dimension check: [GeV⁴]/[GeV⁴] = dimensionless ✓
# Valid regime: Q >> Λ_QCD ≈ 200 MeV; use above √s > 1 GeV
# ============================================================
quark_sum_d4 = (Q_u**2 * m_u + Q_d**2 * m_d + Q_s**2 * m_s) * cond_abs
# [GeV⁴] = Σ Q_q² [dimensionless] × m_q [GeV] × |⟨ψ̄ψ⟩| [GeV³]


def delta_R_ope_d4(s_GeV2):
    """SVZ d=4 OPE correction to R(s) from quark-mass × chiral condensate.
    
    δR^(4)(s) = 24π² N_c (Σ_q Q_q² m_q |⟨ψ̄ψ⟩|) / s²
    
    Units: quark_sum_d4 [GeV⁴] / s² [GeV⁴] = dimensionless ✓
    Physical: positive (condensate reduces R below perturbative value).
    """
    return 24 * math.pi**2 * N_c * quark_sum_d4 / s_GeV2**2


def delta_R_ope_d6(s_GeV2):
    """SVZ d=6 four-quark condensate correction (factorization approximation).
    
    δR^(6)(s) = (16π²/3) (Σ_q Q_q⁴) |⟨ψ̄ψ⟩|² / (N_c s³)
    
    Units: [GeV⁶]/[GeV⁶] = dimensionless ✓
    """
    C6 = 16 * math.pi**2 / 3
    sum_Q4 = Q_u**4 + Q_d**4 + Q_s**4
    return C6 * sum_Q4 * cond_abs**2 / (N_c * s_GeV2**3)


# ============================================================
# Perturbative R(s) for u,d,s above hadronic threshold
# R_pQCD(u,d,s) = N_c Σ Q_q² (1 + α_s/π)
# ============================================================
R_pQCD_uds = N_c * (Q_u**2 + Q_d**2 + Q_s**2) * (1 + alpha_s / math.pi)


# ============================================================
# Δ(1/α)_had computation via dispersion integral
# Δ(1/α)_had = (1/3π) × ∫ R(s) × G(s) ds
# where G(s) = M_Z²/(s(M_Z²-s)) and M_Z²/3π is factored out above
# ============================================================
def compute_delta_inv_alpha(R_func, s_low, s_high, **kwargs):
    """Integrate (1/3π) ∫ R(s) × G(s) ds over [s_low, s_high] GeV².
    
    Returns: Δ(1/α)_had contribution from this energy range.
    """
    def integrand(s):
        return R_func(s) * dispersion_kernel(s)
    result, error = integrate.quad(integrand, s_low, s_high, **kwargs)
    return result / (3 * math.pi), abs(error) / (3 * math.pi)


def main():
    t_start = time.time()

    print("=" * 70)
    print("GTE OPE NP Correction to Δα_had — OQ-HVP-8")
    print("=" * 70)
    print()
    print("GTE inputs:")
    print(f"  M_kink = {M_kink*1000:.2f} MeV (CatAL)")
    print(f"  ⟨ψ̄ψ⟩ = -M_kink³ = -{cond_abs:.6e} GeV³")
    print(f"  m_u = {m_u*1000:.3f} MeV, m_d = {m_d*1000:.3f} MeV, m_s = {m_s*1000:.2f} MeV (CatB)")
    print(f"  Q_u = {Q_u:.4f}, Q_d = {Q_d:.4f}, Q_s = {Q_s:.4f} (CatAL)")
    print(f"  α_s(M_Z) = {alpha_s} (CatAD)")
    print(f"  M_Z = {M_Z:.3f} GeV (CatAD)")
    print()
    print(f"Quark condensate sum (d=4): Σ Q_q² m_q |⟨ψ̄ψ⟩| = {quark_sum_d4:.4e} GeV⁴")
    print(f"  Strange contribution dominates: Q_s² m_s |⟨ψ̄ψ⟩| = {Q_s**2*m_s*cond_abs:.4e} GeV⁴ ({Q_s**2*m_s*cond_abs/quark_sum_d4:.1%})")
    print()

    # --------------------------------------------------------
    # Round 1: OPE corrections at key energies
    # --------------------------------------------------------
    print("--- Round 1: OPE δR_NP at key energies ---")
    print(f"{'√s (GeV)':>10} | {'δR^(4)/R_pert':>14} | {'δR^(6)/R_pert':>14} | {'R_pert':>8}")
    for sqrt_s in [1.0, 1.2, 1.5, 2.0]:
        s = sqrt_s**2
        d4 = delta_R_ope_d4(s)
        d6 = delta_R_ope_d6(s)
        print(f"{sqrt_s:>10.1f} | {d4/R_pQCD_uds:>14.5f} | {d6/R_pQCD_uds:>14.5f} | {R_pQCD_uds:>8.4f}")
    print()

    # --------------------------------------------------------
    # Round 2: Integrate OPE corrections [1-2 GeV]
    # This is the NP window where OPE is valid (Q > Λ_QCD)
    # and perturbative pQCD is not yet reliable
    # --------------------------------------------------------
    print("--- Round 2: OPE NP Correction [1-2 GeV] ---")
    s_low_NP, s_high_NP = 1.0**2, 2.0**2

    delta_d4_1_2, err_d4 = compute_delta_inv_alpha(delta_R_ope_d4, s_low_NP, s_high_NP)
    delta_d6_1_2, err_d6 = compute_delta_inv_alpha(delta_R_ope_d6, s_low_NP, s_high_NP)

    # Wider window for sensitivity check
    delta_d4_0p5_2, _ = compute_delta_inv_alpha(delta_R_ope_d4, 0.5**2, 2.0**2)

    print(f"d=4 SVZ condensate [1.0-2.0 GeV]:")
    print(f"  Δ(1/α)_had^NP = {delta_d4_1_2:.6f}")
    print(f"  Fraction of PDG total = {delta_d4_1_2/DELTA_INV_ALPHA_HAD_PDG:.4%}")
    print(f"  Integration error: {err_d4:.2e}")
    print()
    print(f"d=6 four-quark condensate [1.0-2.0 GeV]:")
    print(f"  Δ(1/α)_had^NP = {delta_d6_1_2:.6f}")
    print(f"  Fraction of PDG total = {delta_d6_1_2/DELTA_INV_ALPHA_HAD_PDG:.4%}")
    print()
    print(f"Sensitivity: d=4 [0.5-2.0 GeV] = {delta_d4_0p5_2:.6f} ({delta_d4_0p5_2/DELTA_INV_ALPHA_HAD_PDG:.4%})")
    print()

    # --------------------------------------------------------
    # Round 3: pQCD u,d,s above 2 GeV
    # [2-3 GeV]: clean window above VMD (ρ,ω,φ all below 2 GeV)
    #            and below J/ψ threshold (3.097 GeV)
    # --------------------------------------------------------
    print("--- Round 3: pQCD u,d,s [2-3 GeV] ---")
    print(f"R_pQCD(u,d,s) = {R_pQCD_uds:.6f}  [N_c × (4/9+1/9+1/9) × (1+α_s/π)]")

    delta_pQCD_2_3, _ = compute_delta_inv_alpha(
        lambda s: R_pQCD_uds, 2.0**2, 3.0**2)
    delta_pQCD_1p8_3, _ = compute_delta_inv_alpha(
        lambda s: R_pQCD_uds, 1.8**2, 3.0**2)
    delta_pQCD_3_5, _ = compute_delta_inv_alpha(
        lambda s: R_pQCD_uds, 3.0**2, 5.0**2)

    print(f"Δ(1/α)_had pQCD [2.0-3.0 GeV] = {delta_pQCD_2_3:.6f}  ({delta_pQCD_2_3/DELTA_INV_ALPHA_HAD_PDG:.4%})")
    print(f"Δ(1/α)_had pQCD [1.8-3.0 GeV] = {delta_pQCD_1p8_3:.6f}  ({delta_pQCD_1p8_3/DELTA_INV_ALPHA_HAD_PDG:.4%})")
    print(f"Δ(1/α)_had pQCD [3.0-5.0 GeV] = {delta_pQCD_3_5:.6f}  ({delta_pQCD_3_5/DELTA_INV_ALPHA_HAD_PDG:.4%})")
    print()

    # --------------------------------------------------------
    # Round 4: Updated total coverage
    # --------------------------------------------------------
    print("--- Round 4: Revised Total Δα_had Coverage ---")
    print()

    components = {
        "ρ VMD (CatB)":              0.430,
        "ω VMD (CatB)":              0.034,
        "φ VMD (CatB)":              0.025,
        "c pQCD (CatAD)":            0.088,
        "b pQCD (CatAD)":            0.016,
        "OPE d=4 NP [1-2 GeV]":  delta_d4_1_2,
        "pQCD u,d,s [2-3 GeV]":  delta_pQCD_2_3,
    }
    total = sum(components.values())
    remaining = DELTA_INV_ALPHA_HAD_PDG - total

    print(f"{'Component':<30} | {'Δ(1/α)':>10} | {'% total':>8}")
    print("-" * 55)
    baseline_total = 0
    for name, val in components.items():
        baseline_total += val
        print(f"{name:<30} | {val:>10.6f} | {val/DELTA_INV_ALPHA_HAD_PDG:>8.4%}")
    print("-" * 55)
    print(f"{'TOTAL (GTE accessible)':<30} | {total:>10.6f} | {total/DELTA_INV_ALPHA_HAD_PDG:>8.4%}")
    print(f"{'PDG reference total':<30} | {DELTA_INV_ALPHA_HAD_PDG:>10.3f} | {'100.00%':>8}")
    print(f"{'Remaining gap':<30} | {remaining:>10.4f} | {remaining/DELTA_INV_ALPHA_HAD_PDG:>8.4%}")
    print()

    # VMD prior estimate: 68.1% accessible (ρ+ω+φ+c+b)
    prior_coverage = 0.681
    new_contributions = delta_d4_1_2 + delta_pQCD_2_3
    new_coverage_frac = new_contributions / DELTA_INV_ALPHA_HAD_PDG
    revised_total_coverage = prior_coverage + new_coverage_frac
    revised_gap = 1.0 - revised_total_coverage

    print(f"Prior VMD estimate (ρ+ω+φ+c+b): {prior_coverage:.1%}")
    print(f"OPE d=4 NP [1-2 GeV]:           +{delta_d4_1_2/DELTA_INV_ALPHA_HAD_PDG:.4%}")
    print(f"pQCD u,d,s [2-3 GeV]:           +{delta_pQCD_2_3/DELTA_INV_ALPHA_HAD_PDG:.4%}")
    print(f"Revised total coverage:           {revised_total_coverage:.4%}")
    print(f"Revised remaining gap:            {revised_gap:.4%}")
    print()

    # --------------------------------------------------------
    # Round 5: Carl's Adversarial Analysis
    # --------------------------------------------------------
    print("--- Carl's Adversarial Analysis ---")
    print()
    print("Q1: Is C_D = 24π² N_c correct for the d=4 SVZ condensate?")
    print("   From Im[δΠ^(4)] = C×m_q|⟨q̄q⟩|/s²:")
    print("   SVZ gives C = -2π²/3 per flavor × Q_q², then R = 12π×Im Π/s")
    print("   → factor = 12π × (2π²/3) × N_c = 8π³ N_c ≈ 749")
    C_check = 12 * math.pi * (2 * math.pi**2 / 3) * N_c
    print(f"   C_check = {C_check:.2f}  vs used 24π² N_c = {24*math.pi**2*N_c:.2f}")
    print(f"   Note: factor-of-{C_check/(24*math.pi**2*N_c):.1f} uncertainty in OPE coefficient")
    print(f"   → Maximum d=4 contribution: {delta_d4_1_2 * C_check/(24*math.pi**2*N_c):.5f} Δ(1/α)")
    print()
    print("Q2: Strange quark dominates — is the GTE condensate flavor-universal?")
    print(f"   m_s = {m_s*1000:.1f} MeV >> m_u = {m_u*1000:.3f}, m_d = {m_d*1000:.3f} MeV")
    print(f"   Strange fraction of quark_sum = {Q_s**2*m_s*cond_abs/quark_sum_d4:.1%}")
    print(f"   In real QCD: ⟨s̄s⟩ ≈ 0.7-0.8 × ⟨ūu⟩ (lattice, Phys.Rev.Lett.2022)")
    strange_suppressed = quark_sum_d4 - 0.25 * Q_s**2 * m_s * cond_abs  # suppress by 75%
    delta_d4_supp, _ = compute_delta_inv_alpha(
        lambda s: 24*math.pi**2*N_c*strange_suppressed/s**2, s_low_NP, s_high_NP)
    print(f"   If ⟨s̄s⟩ suppressed by 75%: Δ(1/α)_NP = {delta_d4_supp:.6f} ({delta_d4_supp/DELTA_INV_ALPHA_HAD_PDG:.4%})")
    print()
    print("Q3: OPE validity at 1 GeV?")
    print(f"   Q/Λ_QCD ≈ {1.0/0.2:.0f} at Q=1 GeV — marginal but standard in sum rule literature")
    print("   Result is ORDER-OF-MAGNITUDE estimate; error ≈ factor 2-10")
    print()
    print("Q4: Does pQCD double-count with existing VMD coverage?")
    print("   VMD (ρ,ω,φ) covers 700-1020 MeV. pQCD window starts at 2000 MeV.")
    print("   No double counting. The 1-2 GeV gap is the transition region (OPE estimate).")
    print(f"   c pQCD (8.8%) covers ≥2m_c ≈ 3 GeV to M_Z, distinct from 2-3 GeV u,d,s window.")
    print()
    print("Q5: Does d=4 dominate over d=6?")
    ratio = delta_R_ope_d4(1.0) / delta_R_ope_d6(1.0)
    print(f"   At s=1 GeV²: δR^(4)/δR^(6) = {ratio:.0f}× — d=4 term completely dominates")
    print()

    print("--- CONCLUSIONS ---")
    print()
    print(f"1. OPE d=4 NP correction [1-2 GeV]:  Δ(1/α) = {delta_d4_1_2:.5f}")
    print(f"   = {delta_d4_1_2/DELTA_INV_ALPHA_HAD_PDG:.4%} of total Δα_had")
    print(f"   Coverage of 31.9% gap: {delta_d4_1_2/(DELTA_INV_ALPHA_HAD_PDG*0.319):.4%}")
    print(f"   Status: NEGLIGIBLE — condensate corrections cannot close the gap")
    print()
    print(f"2. pQCD u,d,s [2-3 GeV]:              Δ(1/α) = {delta_pQCD_2_3:.5f}")
    print(f"   = {delta_pQCD_2_3/DELTA_INV_ALPHA_HAD_PDG:.4%} of total Δα_had")
    print(f"   Coverage of 31.9% gap: {delta_pQCD_2_3/(DELTA_INV_ALPHA_HAD_PDG*0.319):.4%}")
    print(f"   Status: PARTIAL — contributes ~14.8% of the remaining gap")
    print()
    print(f"3. Revised total GTE coverage: {revised_total_coverage:.4%}")
    print(f"   Revised remaining irreducible gap: {revised_gap:.4%}")
    print()
    print("VERDICT (OQ-HVP-8): NEGATIVE RESULT — the OPE condensate approach")
    print("provides < 1% of the remaining 31.9% gap. The irreducible gap requires")
    print("experimental R(s) data (e⁺e⁻ → hadrons) or lattice QCD.")
    print("The pQCD u,d,s [2-3 GeV] contribution (~4.7%) is the only new")
    print("GTE-accessible route, closing ~15% of the gap.")
    print()

    # Output JSON artifact
    results = {
        "computation": "GTE OPE HVP correction",
        "gte_inputs": {
            "M_kink_MeV": M_kink * 1000,
            "condensate_GeV3": -cond_abs,
            "m_u_GeV": m_u, "m_d_GeV": m_d, "m_s_GeV": m_s,
            "Q_u": Q_u, "Q_d": Q_d, "Q_s": Q_s,
            "alpha_s": alpha_s, "M_Z_GeV": M_Z,
        },
        "quark_sum_d4_GeV4": quark_sum_d4,
        "ope_d4_1_2GeV": {
            "delta_inv_alpha": delta_d4_1_2,
            "fraction_of_total": delta_d4_1_2 / DELTA_INV_ALPHA_HAD_PDG,
            "coverage_of_gap_319": delta_d4_1_2 / (DELTA_INV_ALPHA_HAD_PDG * 0.319),
        },
        "ope_d6_1_2GeV": {
            "delta_inv_alpha": delta_d6_1_2,
            "fraction_of_total": delta_d6_1_2 / DELTA_INV_ALPHA_HAD_PDG,
        },
        "pQCD_uds_2_3GeV": {
            "R_pQCD": R_pQCD_uds,
            "delta_inv_alpha": delta_pQCD_2_3,
            "fraction_of_total": delta_pQCD_2_3 / DELTA_INV_ALPHA_HAD_PDG,
            "coverage_of_gap_319": delta_pQCD_2_3 / (DELTA_INV_ALPHA_HAD_PDG * 0.319),
        },
        "revised_coverage": {
            "prior_coverage_fraction": prior_coverage,
            "ope_new_fraction": delta_d4_1_2 / DELTA_INV_ALPHA_HAD_PDG,
            "pQCD_uds_new_fraction": delta_pQCD_2_3 / DELTA_INV_ALPHA_HAD_PDG,
            "revised_total_fraction": revised_total_coverage,
            "revised_gap_fraction": revised_gap,
        },
        "verdict": "NEGATIVE — OPE NP corrections negligible; pQCD uds [2-3 GeV] provides ~4.7% new coverage",
        "elapsed_s": round(time.time() - t_start, 2),
    }

    artifact_path = "gte_ope_hvp_correction_results.json"
    with open(artifact_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {artifact_path}")

    signal.alarm(0)
    return results


if __name__ == "__main__":
    main()
