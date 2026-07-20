"""
One-loop Coleman-Weinberg vacuum energy correction in the Phi_MDL theory.

This script computes:
  - The one-loop CW effective potential correction for a scalar of mass m_kink
  - The CC hierarchy ratio |DeltaV_CW| / rho_Lambda_obs
  - A Z7 cancellation analysis (classically all 7 vacua have V=0; quantum correction is universal)
  - A comparison of scale between the CW (UV perturbative) and NRT (IR non-perturbative) mechanisms

Certified values used in P38 (emergent_gravity_gte_phimdl.tex) and P43 (phimdl_completeness_paper.tex).

Physical conventions:
  - All energies in MeV (natural units, hbar=c=1)
  - MS-bar renormalization at mu = m_phi (canonical choice: log term vanishes)
  - Observed CC: rho_Lambda^obs ~ (2.3 meV)^4 ~ 2.80e-35 MeV^4 (Planck 2018)
"""

import math
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Physical constants
# ─────────────────────────────────────────────────────────────────────────────

M_TAU_MEV = 1776.86          # tau lepton mass (MeV) — PDG 2022
M_KINK_MEV = (8 / 49) * M_TAU_MEV   # Phi_MDL BPS kink mass (MeV); P38 Eq.(kink_mass)
M_Z_MEV = 91.2e3             # Z boson mass (MeV)
M_PL_MEV = 2.435e18 * 1e3   # reduced Planck mass (MeV)

# Observed cosmological constant energy density (Planck 2018)
RHO_LAMBDA_OBS_MEV4 = (2.3e-9) ** 4  # (2.3 meV)^4 in MeV^4


def cw_correction_msbar(m_mev: float, mu_mev: float) -> float:
    """
    One-loop Coleman-Weinberg correction to the vacuum energy in MS-bar scheme.

    DeltaV_CW = m^4 / (64 pi^2) * (log(m^2/mu^2) - 3/2)

    At mu = m: log term vanishes, giving DeltaV_CW = -3m^4 / (128 pi^2).

    Args:
        m_mev:  scalar field mass in MeV
        mu_mev: renormalization scale in MeV

    Returns:
        DeltaV_CW in MeV^4
    """
    log_term = math.log(m_mev ** 2 / mu_mev ** 2) - 1.5
    return m_mev ** 4 / (64.0 * math.pi ** 2) * log_term


def z7_vacuum_sum() -> dict:
    """
    Sum and average of V_{Z7}(Phi_k) over all seven Z7 vacua.

    V_{Z7}(Phi_k) = (m^2/49)(1 - cos(7 * 2*pi*k/7))
                  = (m^2/49)(1 - cos(2*pi*k)) = 0  for all k in Z7.

    The classical potential is IDENTICALLY ZERO at each vacuum (not just on average).
    This is the algebraic reason classical Lambda = 0 is topologically protected.

    Returns dict with sum, average, and individual values.
    """
    m_sq = 1.0  # normalized: result is proportional to m^2, factor out
    vals = [m_sq / 49.0 * (1.0 - np.cos(7.0 * 2.0 * np.pi * k / 7.0)) for k in range(7)]
    return {
        "individual": vals,
        "sum": sum(vals),
        "average": sum(vals) / 7.0,
        "all_zero": all(abs(v) < 1e-14 for v in vals),
    }


def z7_character_sum_fails() -> str:
    """
    The Z7 character-sum identity sum_{j=0}^6 zeta_7^j = 0 does NOT cancel the
    one-loop quantum correction.

    Reason: the physical partition function Z(beta) = Tr[e^{-beta H}] is real
    and positive. The combination sum_j Z_j zeta_7^j is complex; its vanishing
    gives an undefined free energy, not a zero vacuum energy. The relevant
    Fourier component is tilde_Z(0) = 7 Z_0 > 0.
    """
    zeta7 = np.exp(2j * np.pi / 7)
    char_sum = sum(zeta7 ** j for j in range(7))
    return (
        f"Character sum Sigma_j zeta_7^j = {char_sum:.2e}  (numerically zero)\n"
        "But Z(beta) > 0 real: complex combination gives undefined free energy,\n"
        "not zero vacuum energy. Z7 character sum does NOT suppress DeltaV_CW."
    )


def mdl_scale_choice_fails(m_mev: float) -> float:
    """
    MDL could in principle select mu* = m * exp(-3/4) where the CW correction
    vanishes term-by-term. But this is a renormalization scheme artifact: the
    physical vacuum energy is mu-independent, and choosing mu* shifts the
    one-loop contribution into the counterterm delta_Lambda(mu*).
    """
    mu_star = m_mev * math.exp(-3.0 / 4.0)
    val_at_mu_star = cw_correction_msbar(m_mev, mu_star)
    return val_at_mu_star  # ≈ 0 by construction, not a physical cancellation


def main():
    print("=" * 65)
    print("CASIMIR ONE-LOOP VACUUM ENERGY — Phi_MDL Theory (G31)")
    print("=" * 65)

    print(f"\nm_kink  = (8/49) x m_tau = {M_KINK_MEV:.2f} MeV")
    print(f"m_tau   = {M_TAU_MEV:.2f} MeV")
    print(f"m_kink / m_tau = 8/49 = {M_KINK_MEV / M_TAU_MEV:.6f}")

    # ── T1: One-loop CW correction at mu = m_kink ──
    print("\n" + "─" * 65)
    print("T1: One-loop Coleman-Weinberg correction")
    print("─" * 65)

    dV_at_m = cw_correction_msbar(M_KINK_MEV, M_KINK_MEV)
    print(f"\n[mu = m_kink = {M_KINK_MEV:.2f} MeV, MS-bar]")
    print(f"  DeltaV_CW = -3*m^4/(128*pi^2) = {dV_at_m:.4e} MeV^4")

    dV_at_mz = cw_correction_msbar(M_KINK_MEV, M_Z_MEV)
    print(f"\n[mu = M_Z = {M_Z_MEV/1e3:.1f} GeV]")
    print(f"  DeltaV_CW = {dV_at_mz:.4e} MeV^4")

    print(f"\nObserved CC:  rho_Lambda^obs = {RHO_LAMBDA_OBS_MEV4:.3e} MeV^4")
    hierarchy = abs(dV_at_m) / RHO_LAMBDA_OBS_MEV4
    print(f"\nCC hierarchy: |DeltaV_CW| / rho_Lambda^obs = {hierarchy:.2e}")
    print(f"              log10 = {math.log10(hierarchy):.1f}  (~10^42)")
    print(f"\n  Phi_MDL mass m_kink = {M_KINK_MEV:.2f} MeV, NOT m_tau = {M_TAU_MEV:.2f} MeV.")
    print(f"  Using m_tau (error) gives {-3*M_TAU_MEV**4/(128*math.pi**2):.3e} MeV^4  (~10^45).")
    print(f"  Correct value: {dV_at_m:.3e} MeV^4  (~10^42).")

    # ── T2: Z7 cancellation analysis ──
    print("\n" + "─" * 65)
    print("T2: Z7 structure — cancellation analysis")
    print("─" * 65)

    z7 = z7_vacuum_sum()
    print(f"\nV_{{Z7}}(Phi_k) for k = 0..6 (normalized m^2=1):")
    for k, v in enumerate(z7["individual"]):
        print(f"  k={k}: V = {v:.2e}")
    print(f"Sum   = {z7['sum']:.2e}  (exact 0)")
    print(f"Average = {z7['average']:.2e}  (exact 0)")
    print(f"All identically zero: {z7['all_zero']}")
    print("\nConclusion: each vacuum has V=0 individually (not just on average).")
    print("Z7 symmetry protects the CLASSICAL Lambda=0 but provides no suppression")
    print("of the QUANTUM one-loop correction, which is a universal UV divergence.")

    print("\n" + z7_character_sum_fails())

    mu_star_val = mdl_scale_choice_fails(M_KINK_MEV)
    print(f"\nMDL scale mu* = m_kink * exp(-3/4) = {M_KINK_MEV * math.exp(-3/4):.2f} MeV")
    print(f"  DeltaV_CW(mu*) = {mu_star_val:.2e} MeV^4  (=0 by construction)")
    print("  This is a renormalization scheme artifact, not a physical cancellation.")

    # ── T3: NRT vs CW ──
    print("\n" + "─" * 65)
    print("T3: NRT mechanism vs CW correction — scale comparison")
    print("─" * 65)
    print(f"\nCW correction scale: m_kink = {M_KINK_MEV:.1f} MeV  [UV perturbative, scheme-dependent]")
    print(f"NRT mechanism scale: H_0 ~ 10^-33 eV  [IR non-perturbative, scheme-independent]")
    print("These operate at opposite ends of the energy spectrum and are ADDITIVE,")
    print("not mutually canceling. The NRT gives the observed Omega_Lambda ~ 0.690")
    print("from PSP halting undecidability (P01/P44); it does not suppress DeltaV_CW.")
    print("The CC hierarchy problem persists at one loop in the Phi_MDL theory.")

    # ── Summary ──
    print("\n" + "=" * 65)
    print("CANONICAL RESULTS (G31)")
    print("=" * 65)
    print(f"  m_kink              = {M_KINK_MEV:.2f} MeV")
    print(f"  DeltaV_CW (mu=m_kink) = {dV_at_m:.4e} MeV^4")
    print(f"  rho_Lambda^obs      = {RHO_LAMBDA_OBS_MEV4:.3e} MeV^4")
    print(f"  Hierarchy           = {hierarchy:.2e}  ~ 10^42")
    print(f"  Z7 cancels CW?      NO (all vacua individually V=0; quantum correction is universal)")
    print(f"  NRT cancels CW?     NO (different scales and mechanisms; additive)")
    print(f"  G31 status:         PARTIAL CatA")
    print(f"    COMPUTED: DeltaV_CW = {dV_at_m:.3e} MeV^4 (mu=m_kink, MS-bar)")
    print(f"    CLOSED: Z7 no-cancel (two mechanisms checked and ruled out)")
    print(f"    OPEN: Physical UV cancellation mechanism unidentified")


if __name__ == "__main__":
    main()
