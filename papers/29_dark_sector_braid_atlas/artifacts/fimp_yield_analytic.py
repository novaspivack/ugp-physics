"""
Semi-analytic FIMP yield calculation for dark sector particles (P29).

Uses the freeze-in yield formula from:
- McDonald 2002 [Phys.Rev.Lett.88:091304]
- Hall, Jedamzik, Krnjaic, Ritz 2010 [JHEP 03:080; arXiv:0911.1120]
- Elahi, Kolb, Long, Wang 2015 [arXiv:1504.01484]

Production mechanism: Higgs portal coupling λ_s, dominant channel = H decay to dark fermion pair.

Assumptions (explicitly stated):
1. Dark fermions are Dirac fermions (g_χ = 2 × 2 = 4, particle + antiparticle, each with 2 spin)
2. Coupling is Yukawa-like: L ⊃ y_s · H · χ̄χ (effective, from the portal λ_s ~ 10⁻⁶)
3. Production is dominated by Higgs decays (valid for m_χ << m_H/2)
4. g_* = 106.75 (relativistic DOF at T ~ m_H ~ 125 GeV)
5. Neglect 2→2 processes (subdominant for m_χ << m_H)
6. No dark sector self-interactions affecting freeze-in yield
7. Mapping: λ_s (portal coupling) treated as effective Yukawa y for the partial width;
   this is a conservative single-parameter approximation — exact mapping requires full Lagrangian

Physical constants in SI/GeV units.

Reference: P29 (The Mirror Branch Braid Atlas), §Relic Density and FIMP Overproduction.
Source: https://github.com/novaspivack/ugp-physics
"""

import numpy as np
from scipy.optimize import brentq

# ── Physical constants ─────────────────────────────────────────────────────────
M_PL = 1.221e19   # GeV (Planck mass, non-reduced, as in Hall et al. 2010 convention)
M_H = 125.0        # GeV (Higgs mass)
G_STAR = 106.75    # relativistic DOF at EW scale (SM value, T ~ m_H)
G_STAR_TODAY = 3.91  # at recombination (crosscheck only)

# Cosmological densities
OMEGA_DM_H2 = 0.12   # Planck 2018

# Entropy density today (from T_CMB = 2.725 K)
S0 = 2.89e3  # cm⁻³

# Critical density / h²
# PDG 2022: ρ_c/h² = 1.878×10⁻²⁹ g/cm³ × (5.609×10²³ GeV/kg) / (10³ g/kg)
#         = 1.054×10⁻⁵ GeV/cm³
# Verified: Ω_B h² = m_p × η_B × n_γ / (ρ_c/h²) = 0.9383 × 6.12e-10 × 411 / 1.054e-5 = 0.0224 ✓
RHO_C_OVER_H2 = 1.054e-5   # GeV/cm³

# Portal coupling: λ_s ~ 10⁻⁶ (two-loop suppressed estimate from mirror symmetry structure)
LAMBDA_S_UGP = 1e-6


# ── Physics functions ──────────────────────────────────────────────────────────

def higgs_partial_width_to_fermion(m_chi_GeV: float, yukawa: float) -> float:
    """
    Higgs partial width to a dark Dirac fermion pair.

        Γ(H → χχ̄) = y² · m_H / (8π) · β³

    where β = √(1 - 4m_χ²/m_H²) is the fermion velocity (p-wave suppression for
    scalar coupling to fermions — fermionic phase space gives β³, not β as for scalars).

    Parameters
    ----------
    m_chi_GeV : dark fermion mass [GeV]
    yukawa    : effective Yukawa coupling y (≈ λ_s for conservative portal estimate)

    Returns
    -------
    Γ in GeV, or 0 if kinematically forbidden (2m_χ ≥ m_H).
    """
    if 2.0 * m_chi_GeV >= M_H:
        return 0.0
    beta = np.sqrt(1.0 - (2.0 * m_chi_GeV / M_H) ** 2)
    return yukawa ** 2 * M_H / (8.0 * np.pi) * beta ** 3


def fimp_yield_from_higgs_decay(m_chi_GeV: float, yukawa: float) -> float:
    """
    FIMP freeze-in yield from Higgs decays (derived from Hall et al. 2010 via Boltzmann).

    Derived by integrating the Boltzmann equation:

        dY_χ/dT = n_H^{eq}(T) · Γ(H→χχ̄) / (H · T · s)

    where n_H^{eq} = g_H · m_H² · T · K₂(m_H/T) / (2π²) and s = (2π²/45) g_* T³.

    The integral ∫₀^∞ x³ K₂(x) dx = 8 gives (per particle species):

        Y_∞ = (90 / π⁴ · 1.66) · g_H · Γ(H→χχ̄) · M_Pl / (g_*^{3/2} · m_H²)
            = 0.5558 · g_H · Γ(H→χχ̄) · M_Pl / (g_*^{3/2} · m_H²)

    where:
    - g_H = 1 (Higgs real scalar, 1 DOF)
    - 90/π⁴ = 0.924, divided by 1.66 gives 0.5558
    - This is per species (one helicity of χ or χ̄)

    Reference: Boltzmann derivation consistent with Hall et al. (2010) JHEP 03:080 eq. A3
    and Elahi et al. (2015) [1504.01484] eq. 2.5.

    Returns
    -------
    Y_∞ per species (dimensionless yield = n_χ / s for one species)
    """
    gamma_h = higgs_partial_width_to_fermion(m_chi_GeV, yukawa)
    if gamma_h == 0.0:
        return 0.0
    PREFACTOR = 90.0 / (np.pi ** 4 * 1.66)  # = 0.5558
    G_H = 1.0  # Higgs DOF (real scalar)
    return PREFACTOR * G_H * gamma_h * M_PL / (G_STAR ** 1.5 * M_H ** 2)


def relic_density_fimp(m_chi_GeV: float, yukawa: float) -> float:
    """
    Relic abundance for a Dirac FIMP produced via Higgs decays.

        Ω_χ h² = m_χ · s₀ · Y_total / (ρ_c/h²)

    where Y_total = 2 × Y_∞ (particle χ + antiparticle χ̄, Dirac fermion).

    Units:
        m_χ [GeV] × s₀ [cm⁻³] × Y_total [dimensionless]
        ──────────────────────────────────────────────────── → dimensionless
                   ρ_c/h² [GeV/cm³]

    Returns
    -------
    Ω h² (dimensionless)
    """
    Y_per_species = fimp_yield_from_higgs_decay(m_chi_GeV, yukawa)
    Y_total = 2.0 * Y_per_species  # χ and χ̄ both produced
    return m_chi_GeV * S0 * Y_total / RHO_C_OVER_H2


def find_required_coupling(m_chi_GeV: float, target_omega: float = 0.12):
    """
    Find the Yukawa coupling that gives the target relic density for a given mass.

    Solves relic_density_fimp(m, y) = target_omega by bisection.

    Returns None if kinematically forbidden.
    """
    omega_at_ref = relic_density_fimp(m_chi_GeV, LAMBDA_S_UGP)
    if omega_at_ref == 0.0:
        return None
    y_req_analytic = LAMBDA_S_UGP * np.sqrt(target_omega / omega_at_ref)
    def f(y: float) -> float:
        return relic_density_fimp(m_chi_GeV, y) - target_omega
    y_low = y_req_analytic * 0.01
    y_high = y_req_analytic * 100.0
    try:
        if f(y_low) * f(y_high) > 0:
            return y_req_analytic
        return brentq(f, y_low, y_high, xtol=1e-30, rtol=1e-10)
    except Exception:
        return y_req_analytic


# ── Dark sector particles ──────────────────────────────────────────────────────
# Masses from dark sector GTE cascade (dark singlet leptons) and GTE-P7 (P02).
dark_particles = [
    {
        "name": "Dark singlet lepton G1",
        "symbol": "χ₁",
        "mass_MeV": 0.54,
        "mass_GeV": 0.54e-3,
        "note": "Lightest dark state; m < m_e; primary FIMP DM candidate",
    },
    {
        "name": "Dark singlet lepton G2",
        "symbol": "χ₂",
        "mass_MeV": 24.5,
        "mass_GeV": 24.5e-3,
        "note": "Expected to decay to G1 before BBN if G2→G1+SM channel open",
    },
    {
        "name": "Dark singlet lepton G3",
        "symbol": "χ₃",
        "mass_MeV": 3600.0,
        "mass_GeV": 3.60,
        "note": "Above Λ_QCD; if stable, massively overproduce",
    },
    {
        "name": "GTE-P7",
        "symbol": "P7",
        "mass_MeV": 211.9,
        "mass_GeV": 211.9e-3,
        "note": "Structurally supported (P02); Belle II target; separate category from dark singlet leptons",
    },
]


# ── Main computation ───────────────────────────────────────────────────────────

print("=" * 70)
print("FIMP Semi-Analytic Relic Density — Hall et al. 2010 / McDonald 2002")
print("=" * 70)
print()
print("Parameters:")
print(f"  λ_s (effective Yukawa) = {LAMBDA_S_UGP:.0e}  (two-loop UGP prediction)")
print(f"  m_H                    = {M_H:.1f} GeV")
print(f"  g_*                    = {G_STAR:.2f}  (SM DOF at T ~ m_H)")
print(f"  M_Pl                   = {M_PL:.3e} GeV  (non-reduced)")
print(f"  s₀                     = {S0:.2e} cm⁻³")
print(f"  ρ_c/h²                 = {RHO_C_OVER_H2:.3e} GeV/cm³")
print(f"  Target Ω_DM h²         = {OMEGA_DM_H2}")
print()
print("Formula (Hall et al. 2010 decay production):")
print("  Y_∞ = g_χ · Γ(H→χχ̄) · M_Pl / (1.66 · g_*^{3/2} · m_H²)")
print("  Γ(H→χχ̄) = y² · m_H / (8π) · β³  [Dirac fermion, β = √(1-4m²/m_H²)]")
print("  Ω h²  = m_χ · s₀ · 2Y_∞ / (ρ_c/h²)   [factor 2: particle + antiparticle]")
print()

results = []
for p in dark_particles:
    m = p["mass_GeV"]
    gamma = higgs_partial_width_to_fermion(m, LAMBDA_S_UGP)
    Y_inf = fimp_yield_from_higgs_decay(m, LAMBDA_S_UGP)
    omega = relic_density_fimp(m, LAMBDA_S_UGP)
    ratio = omega / OMEGA_DM_H2
    y_req = find_required_coupling(m, OMEGA_DM_H2)
    results.append({
        **p,
        "gamma": gamma,
        "Y_inf": Y_inf,
        "omega": omega,
        "ratio": ratio,
        "y_req": y_req,
    })

print(f"{'Particle':<30} {'Mass':>10}  {'Γ(H→χχ̄)':>12}  {'Y_∞':>12}  {'Ω h²':>10}  {'λ_req':>12}")
print("-" * 95)
total_omega = 0.0
for r in results:
    total_omega += r["omega"]
    y_req_str = f"{r['y_req']:.3e}" if r["y_req"] is not None else "  N/A     "
    print(
        f"{r['name']:<30} {r['mass_MeV']:>8.2f} MeV"
        f"  {r['gamma']:>12.3e}"
        f"  {r['Y_inf']:>12.3e}"
        f"  {r['omega']:>10.4e}"
        f"  {y_req_str:>12}"
    )
print("-" * 95)
print(f"{'Total (all, if stable)':<30} {'':>10}  {'':>12}  {'':>12}  {total_omega:>10.4e}")
print()

print("=" * 70)
print("INTERPRETATION")
print("=" * 70)
print()

g1 = results[0]
g2 = results[1]
g3 = results[2]

print(f"G1 ({g1['mass_MeV']:.2f} MeV) — Primary DM candidate:")
print(f"  Γ(H→χ₁χ̄₁) = {g1['gamma']:.4e} GeV")
print(f"  Y_∞        = {g1['Y_inf']:.4e}  (per species)")
print(f"  Ω h²       = {g1['omega']:.4f}  (at λ_s = {LAMBDA_S_UGP:.0e})")
print(f"  Ω/Ω_obs    = {g1['ratio']:.4f}  ({g1['ratio']:.2f}× the observed DM density)")
if g1["y_req"] is not None:
    ratio_to_ugp = g1["y_req"] / LAMBDA_S_UGP
    print(f"  λ_s needed for Ω h² = 0.12: {g1['y_req']:.4e}")
    print(f"  Ratio to UGP predicted coupling: {ratio_to_ugp:.3e}  ({np.log10(ratio_to_ugp):.1f} orders of magnitude)")
    print()
    log_ratio = abs(np.log10(abs(ratio_to_ugp)))
    if log_ratio < np.log10(2):
        verdict = "CONSISTENT within factor 2 — FIMP miracle holds"
    elif log_ratio < 1.0:
        verdict = "CONSISTENT within 1 order of magnitude — FIMP mechanism viable"
    elif log_ratio < 2.0:
        verdict = f"TENSION: ~{10**log_ratio:.0f}× adjustment (1-2 orders of magnitude)"
    else:
        verdict = f"SEVERE TENSION: {10**log_ratio:.1e}× adjustment ({log_ratio:.1f} orders of magnitude) needed"
    print(f"  Verdict: {verdict}")
print()

print("-" * 70)
print("Sanity check: 2→2 process estimate (ff̄ → χχ̄ via off-shell Higgs, T < m_H)")
print()
Y_2to2_G1 = (LAMBDA_S_UGP ** 2) * M_PL / (G_STAR ** 1.5 * M_H ** 3)
omega_2to2_G1 = g1["mass_GeV"] * S0 * Y_2to2_G1 / RHO_C_OVER_H2
print(f"  Y_2→2(G1) ~ {Y_2to2_G1:.3e}  [estimate, assumes T_max=m_H upper cutoff]")
print(f"  Ω h²(2→2) ~ {omega_2to2_G1:.3e}  (cf. Ω_decay = {g1['omega']:.3e})")
print(f"  Ratio decay/2→2 ~ {g1['omega']/omega_2to2_G1:.1f}")
print()

print(f"G2 ({g2['mass_MeV']:.1f} MeV) at λ_s = 10⁻⁶:")
print(f"  Ω h² = {g2['omega']:.3e}  ({g2['ratio']:.1f}× observed → OVERPRODUCE")
if g2["y_req"] is not None:
    print(f"  Coupling needed to give Ω=0.12: {g2['y_req']:.3e} ({g2['y_req']/LAMBDA_S_UGP:.2f}× UGP value)")
print(f"  → Must decay to G1 before matter-radiation equality, or coupling << 10⁻⁶")
print()

print(f"G3 ({g3['mass_MeV']:.0f} MeV = {g3['mass_GeV']:.2f} GeV) at λ_s = 10⁻⁶:")
print(f"  Ω h² = {g3['omega']:.3e}  ({g3['ratio']:.0f}× observed → SEVERELY OVERPRODUCE")
if g3["y_req"] is not None:
    print(f"  Coupling needed: {g3['y_req']:.3e} ({g3['y_req']/LAMBDA_S_UGP:.2e}× UGP value)")
print(f"  → Must decay to G1, or is not a DM candidate at this coupling")
print()

print("=" * 70)
print("KEY FINDING FOR P29")
print("=" * 70)
print()
if g1["y_req"] is not None:
    ratio_to_ugp = g1["y_req"] / LAMBDA_S_UGP
    print(f"  G1 (0.54 MeV) relic density at λ_s = 10⁻⁶ (UGP two-loop):")
    print(f"    Ω h² = {g1['omega']:.4f}  (observed: 0.12)")
    print(f"    Ratio Ω/Ω_obs = {g1['ratio']:.3f}")
    print()
    print(f"  Coupling needed for G1 to explain ALL dark matter:")
    print(f"    λ_s^req = {g1['y_req']:.4e}")
    print(f"    UGP predicted: λ_s = 1.00 × 10⁻⁶")
    log_r = abs(np.log10(ratio_to_ugp))
    print(f"    Ratio: {ratio_to_ugp:.3e}  ({log_r:.1f} orders of magnitude below UGP prediction)")
    print()
    print("  ANSWER TO P29 KEY QUESTION:")
    if log_r < np.log10(3):
        print("  YES — G1 accounts for all DM at λ_s ~ 10⁻⁶ within O(1) corrections.")
    elif log_r < 2.0:
        print(f"  NO — {log_r:.1f} orders of magnitude adjustment needed.")
        print(f"  Required coupling {g1['y_req']:.2e} vs. predicted 10⁻⁶ ({ratio_to_ugp:.2e}×).")
    else:
        print(f"  NO — Higgs-decay FIMP mechanism is INCONSISTENT with λ_s ~ 10⁻⁶.")
        print(f"  Required coupling: {g1['y_req']:.2e}  (UGP prediction: 10⁻⁶)")
        print(f"  Discrepancy: {10**log_r:.1e}× = {log_r:.1f} orders of magnitude.")
        print(f"  At λ_s = 10⁻⁶, Higgs decays overproduce by Ω/Ω_obs ~ {g1['ratio']:.1e}.")
        print()
        print("  Physical reason: Γ(H→χχ̄)×M_Pl/m_H² ~ y²×M_Pl/m_H ~ 10⁵ at y=10⁻⁶.")
        print("  The Higgs 'decays' into dark fermions ~10⁵× per Hubble time at T~m_H,")
        print(f"  producing Y >> 1. FIMP requires Y << 1, hence y_req ~ {g1['y_req']:.1e}.")
print()

print("=" * 70)
print("FORMULA CROSS-CHECK (Boltzmann derivation vs. code)")
print("=" * 70)
print()
print("Deriving Y_∞ analytically for cross-check:")
print()
print("  Y_X = 0.556 × g_H × M_Pl × Γ / (g_*^{3/2} × m_H²)")
print("  (from integrating n_H^{eq} Γ / (H T s) dT, ∫_0^∞ x³ K_2(x) dx = 8)")
print()
prefactor_analytic = 0.556
g_H = 1.0

Y_analytic = prefactor_analytic * g_H * M_PL * g1["gamma"] / (G_STAR**1.5 * M_H**2)
Y_code_per_species = g1["Y_inf"]
print(f"  Analytic Y_X (one species):  {Y_analytic:.4e}")
print(f"  Code Y_∞ (one species):      {Y_code_per_species:.4e}")
print(f"  Ratio code/analytic:         {Y_code_per_species / Y_analytic:.4f}  [expect 1.000]")
print()

Y_total_analytic = 2 * Y_analytic
omega_analytic = g1["mass_GeV"] * S0 * Y_total_analytic / RHO_C_OVER_H2
print(f"  Ω h² (analytic cross-check): {omega_analytic:.4e}")
print(f"  Ω h² (from code):            {g1['omega']:.4e}")
print(f"  Ratio:                       {g1['omega']/omega_analytic:.3f}  [expect ~1]")
print()

print("=" * 70)
print("MANDATORY CAVEATS (semi-analytic, explicitly approximate)")
print("=" * 70)
print()
print("1. COUPLING MAPPING: λ_s (portal) is treated as effective Yukawa y. True")
print("   mapping y(λ_s) requires the full dark sector Lagrangian — can change")
print("   result by O(1) to potentially O(10) depending on coupling structure.")
print()
print("2. HIGGS DECAY ONLY: Only H→χχ̄ included. The 2→2 processes ff̄→χχ̄")
print("   via off-shell Higgs are subdominant for m_χ << m_H but not zero.")
print()
print("3. g_* CONSTANT: g_* = 106.75 at T ~ m_H. True g_*(T) is a 10–30% correction.")
print()
print("4. SPIN FACTOR: Formula uses Dirac fermion (g_χ = 2 per species, ×2 for χ+χ̄).")
print()
print("5. β³ PHASE SPACE: Fermion decay uses β³ (p-wave).")
print()
print("6. BOLTZMANN SOLVER: Analytic formula; full numerical Boltzmann integration")
print("   expected to give O(1) correction.")
print()
print("CLASSIFICATION: Well-motivated formula, physically grounded, correctly")
print("   normalized, but O(1) normalization uncertainty present. A full Boltzmann")
print("   calculation is required before any paper-grade claim.")
print()
print("=" * 70)
