"""
Cosmological-constant power counting with a physical CMCA lattice cutoff.
Hypothesis test (negative result): does a CMCA Planck-scale lattice cutoff
change the leading CC power counting?

Question under test:
  The CMCA carries a physical Planck-scale UV cutoff (lattice spacing a ~ l_Pl).
  Standard QFT with dimensional regularization (the G31 / MS-bar route) keeps only
  the logarithmic running and reports a renormalized residual ~ m_kink^4. A *hard*
  physical cutoff (sharp momentum cutoff OR a lattice Brillouin-zone sum) instead
  retains the power-law (quartic) pieces. We ask whether the lattice cutoff changes
  the leading CC power counting:

    (a) still M_Pl^4/(16 pi^2)  — lattice does not change quartic power counting
    (b) m_kink^2 * M_Pl^2       — quadratic intermediate
    (c) exactly zero            — full cancellation
    (d) m_kink^4/(16 pi^2)      — fully regulated to the field scale

Result (NEGATIVE): candidate (a) is realized — the physical CMCA lattice cutoff
does not resolve the quantum CC problem and does not improve the power counting
beyond the standard EFT renormalization statement. G30 remains Tier 3 / community-blocked.

Energies in GeV (hbar = c = 1).
Output: papers/44_quantum_gravity/data/cc_cmca_cutoff_hypothesis_test_results.json
"""

import numpy as np
import json
from scipy.integrate import quad

# ─────────────────────────────────────────────────────────────────────────────
# Physical parameters (canonical EPIC_080 values; G13 / G31)
# ─────────────────────────────────────────────────────────────────────────────
M_Pl = 1.22e19            # GeV, full Planck mass (1/a_CMCA identification scale)
m_kink_GeV = 0.29010      # GeV, Phi_MDL BPS kink mass = (8/49) m_tau (G07/G31)
sigma_GTE = 0.18920       # GeV^2, GTE string tension = (9/4) m_kink^2 (G13 CatAD)
rho_obs = (2.3e-12) ** 4  # GeV^4, observed CC: rho_Lambda = (2.3 meV)^4 (Planck 2018)

print("=" * 70)
print("G30: CC POWER COUNTING WITH A PHYSICAL CMCA LATTICE CUTOFF")
print("=" * 70)
print(f"\nm_kink   = {m_kink_GeV:.5f} GeV   (Phi_MDL field mass, G31)")
print(f"sigma    = {sigma_GTE:.5f} GeV^2  (GTE string tension, G13)")
print(f"M_Pl     = {M_Pl:.3e} GeV")
print(f"rho_obs  = {rho_obs:.3e} GeV^4")

# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE (a): bare lattice / hard-cutoff zero-point energy  -> ~ M_Pl^4
# ─────────────────────────────────────────────────────────────────────────────
# rho_vac = (1/V) sum_k (1/2) omega_k. In the continuum-limit of the BZ sum with a
# sharp cutoff |k| < k_max = pi/a = pi*M_Pl:
#   rho = int_0^{k_max} (4 pi k^2 dk / (2 pi)^3) * (1/2) sqrt(m^2 + k^2)
#       = (1/(4 pi^2)) int_0^{k_max} k^2 sqrt(m^2 + k^2) dk
print("\n" + "-" * 70)
print("CANDIDATE (a): bare lattice / hard-cutoff zero-point sum")
print("-" * 70)

k_max = np.pi * M_Pl   # Planck-scale BZ edge
def omega(k):
    return np.sqrt(m_kink_GeV ** 2 + k ** 2)
integrand = lambda k: k ** 2 * omega(k) / (4.0 * np.pi ** 2)
rho_3d, err = quad(integrand, 0.0, k_max, limit=200)
rho_quartic_leading = k_max ** 4 / (16.0 * np.pi ** 2)  # leading analytic term
print(f"  k_max = pi*M_Pl = {k_max:.3e} GeV")
print(f"  rho_vac (full BZ integral)     = {rho_3d:.3e} GeV^4")
print(f"  leading analytic k_max^4/(16pi^2) = {rho_quartic_leading:.3e} GeV^4")
print(f"  ratio rho/M_Pl^4               = {rho_3d / M_Pl**4:.4f}")
print(f"  hierarchy rho/rho_obs          = {rho_3d / rho_obs:.2e}  (log10 = {np.log10(rho_3d/rho_obs):.1f})")
print("  => QUARTIC in the cutoff: a lattice/hard cutoff does NOT change the")
print("     leading power counting. The bare sum is ~M_Pl^4, hierarchy ~10^122.")

# Cross-check: does a lattice (cos) dispersion change the leading power? No.
N = 256
a = 1.0 / M_Pl
# 3D lattice sum with the standard lattice dispersion omega^2 = m^2 + (4/a^2) sum sin^2(k_i a/2)
ks = 2 * np.pi * np.arange(N) / (N * a)   # one axis
# leading behaviour: sample the 1D contribution magnitude to confirm ~1/a^4 scaling
lat_disp = lambda kx, ky, kz: np.sqrt(
    m_kink_GeV ** 2
    + (4.0 / a ** 2) * (np.sin(kx * a / 2) ** 2 + np.sin(ky * a / 2) ** 2 + np.sin(kz * a / 2) ** 2)
)
# coarse Monte-Carlo estimate of (1/N^3) sum (1/2) omega over BZ, times 1/V normalization
rng = np.random.default_rng(0)
n_samp = 200000
kx = rng.uniform(0, 2 * np.pi / a, n_samp)
ky = rng.uniform(0, 2 * np.pi / a, n_samp)
kz = rng.uniform(0, 2 * np.pi / a, n_samp)
omega_samp = lat_disp(kx, ky, kz)
# rho = (1/(2pi)^3) int_BZ d^3k (1/2) omega  ~ <omega/2> * (2pi/a)^3 / (2pi)^3 = <omega/2> / a^3
rho_lattice = np.mean(omega_samp / 2.0) / a ** 3
print(f"\n  lattice-dispersion MC estimate rho_lat = {rho_lattice:.3e} GeV^4")
print(f"  ratio rho_lat/M_Pl^4 = {rho_lattice / M_Pl**4:.4f}  (still O(1)xM_Pl^4)")

# ─────────────────────────────────────────────────────────────────────────────
# PSC superselection: does removing Z7 modes {1,5} help?  (factor 5/7)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "-" * 70)
print("PSC superselection test: admitted Z7 sectors {0,2,3,4,6} (5 of 7)")
print("-" * 70)
psc_fraction = 5.0 / 7.0
print(f"  best-case multiplicative factor 5/7 = {psc_fraction:.4f}")
print(f"  rho_vac * 5/7 = {rho_3d * psc_fraction:.3e} GeV^4  (still ~M_Pl^4)")
print("  => a rational O(1) factor cannot bridge a 10^122 hierarchy. No help.")

# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE (c): exact cancellation?  Z7 character sum (G31 result) -> NO
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "-" * 70)
print("CANDIDATE (c): exact cancellation via Z7 discrete symmetry")
print("-" * 70)
zeta7 = np.exp(2j * np.pi / 7)
char_sum = sum(zeta7 ** j for j in range(7))
print(f"  Sigma_j zeta_7^j = {char_sum:.2e}  (vanishes as a character sum)")
print("  But Z(beta) = Tr e^{-beta H} is real, positive: the relevant Fourier")
print("  component is Z~(0) = 7 Z_0 > 0. No Bose-Fermi-type cancellation exists")
print("  (all Z7 modes are bosonic). G31 already proved Z7 NON-cancellation.")
print("  => (c) ruled out.")

# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE (d): renormalized residual at the kink scale  -> m_kink^4
# ─────────────────────────────────────────────────────────────────────────────
# After absorbing the cutoff-dependent (quartic, quadratic) pieces into the bare
# CC counterterm delta_Lambda(a), the FINITE renormalized radiative correction is
# set by the heaviest physical field in the Phi_MDL sector: the kink, m_kink.
# This is exactly the MS-bar Coleman-Weinberg result already closed in G31.
print("\n" + "-" * 70)
print("CANDIDATE (d): renormalized residual (cutoff absorbed into counterterm)")
print("-" * 70)
# Coleman-Weinberg residual at mu = m_kink (MS-bar): |DeltaV| = 3 m^4 /(128 pi^2)
rho_kink_CW = 3.0 * m_kink_GeV ** 4 / (128.0 * np.pi ** 2)
rho_kink_naive = m_kink_GeV ** 4 / (16.0 * np.pi ** 2)
print(f"  m_kink^4/(16 pi^2)              = {rho_kink_naive:.3e} GeV^4")
print(f"  CW residual 3 m_kink^4/(128pi^2) = {rho_kink_CW:.3e} GeV^4  (G31 value, MS-bar mu=m_kink)")
print(f"  hierarchy (CW) / rho_obs        = {rho_kink_CW / rho_obs:.2e}  (log10 = {np.log10(rho_kink_CW/rho_obs):.1f})")
print(f"  suppression M_Pl^4 / m_kink^4   = {M_Pl**4 / m_kink_GeV**4:.2e}  (log10 = {np.log10(M_Pl**4/m_kink_GeV**4):.1f})")
print("  => This is NOT produced by the lattice cutoff; it is the standard EFT/")
print("     renormalization statement: cutoff power-law pieces are absorbed by the")
print("     CC counterterm, leaving a residual at the heaviest physical mass m_kink.")
print("     It is exactly G31's already-closed CatA result (hierarchy ~10^42).")

# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE (b)/string-scale check: does sigma_GTE set the scale?  -> still huge
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "-" * 70)
print("String-scale check: rho ~ sigma_GTE^2/(16 pi^2)?")
print("-" * 70)
rho_sigma = sigma_GTE ** 2 / (16.0 * np.pi ** 2)
print(f"  sigma_GTE^2/(16 pi^2) = {rho_sigma:.3e} GeV^4")
print(f"  hierarchy / rho_obs   = {rho_sigma / rho_obs:.2e}  (log10 = {np.log10(rho_sigma/rho_obs):.1f})")
rho_quad = m_kink_GeV ** 2 * M_Pl ** 2 / (16.0 * np.pi ** 2)
print(f"  (b) m_kink^2 M_Pl^2/(16pi^2) = {rho_quad:.3e} GeV^4 -> log10(hier)={np.log10(rho_quad/rho_obs):.1f}")
print("  => string/quadratic scales are far above rho_obs as well. No resolution.")

# ─────────────────────────────────────────────────────────────────────────────
# NRT ratio mechanism: sets Omega_Lambda, not the absolute UV scale
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "-" * 70)
print("NRT mechanism: Omega_Lambda ~ 0.690 is an IR ratio selection")
print("-" * 70)
print("  The NRT / information-theoretic prediction Lambda = (ln2/pi) L_model H_0^2/c^2")
print("  fixes the OBSERVED dark-energy density to 0.31 sigma of Planck 2018 using H_0")
print("  as the sole input (CatAD, P01/P43). It selects WHICH vacuum the universe")
print("  occupies (the IR ratio), and does NOT cancel the UV radiative correction.")
print("  CW (UV, perturbative) and NRT (IR, non-perturbative) are ADDITIVE.")

# ─────────────────────────────────────────────────────────────────────────────
# VERDICT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("VERDICT")
print("=" * 70)
print("  Physically realized power counting with a CMCA lattice cutoff: (a).")
print("  The bare zero-point sum is ~M_Pl^4 (quartic in the cutoff); a lattice")
print("  Brillouin-zone cutoff does NOT change the leading power counting.")
print("  (b) quadratic, (c) exact cancellation: both ruled out.")
print("  (d) m_kink^4 is the RENORMALIZED residual (counterterm absorbs the cutoff)")
print("      = G31's MS-bar result, hierarchy ~10^42. Not a new lattice mechanism.")
print("  => G30 remains Tier 3 / community-blocked. The CMCA lattice cutoff does")
print("     not resolve the quantum CC problem and does not improve the power")
print("     counting beyond the standard EFT renormalization statement.")

results = {
    "candidate_a_bare_lattice_GeV4": float(rho_3d),
    "candidate_a_lattice_disp_MC_GeV4": float(rho_lattice),
    "candidate_a_ratio_to_Mpl4": float(rho_3d / M_Pl ** 4),
    "candidate_a_hierarchy_log10": float(np.log10(rho_3d / rho_obs)),
    "candidate_b_quadratic_GeV4": float(rho_quad),
    "candidate_b_hierarchy_log10": float(np.log10(rho_quad / rho_obs)),
    "candidate_d_CW_residual_GeV4": float(rho_kink_CW),
    "candidate_d_hierarchy_log10": float(np.log10(rho_kink_CW / rho_obs)),
    "psc_5_7_factor": float(psc_fraction),
    "sigma_scale_GeV4": float(rho_sigma),
    "sigma_hierarchy_log10": float(np.log10(rho_sigma / rho_obs)),
    "suppression_Mpl4_to_mkink4_log10": float(np.log10(M_Pl ** 4 / m_kink_GeV ** 4)),
    "rho_obs_GeV4": float(rho_obs),
    "verdict": (
        "Lattice cutoff gives candidate (a): bare zero-point sum ~M_Pl^4, quartic in "
        "cutoff, unchanged power counting. (b),(c) ruled out. (d) m_kink^4 is the "
        "renormalized residual = G31 result (10^42), not a lattice mechanism. "
        "G30 remains Tier 3 / community-blocked."
    ),
}
with open("papers/44_quantum_gravity/data/cc_cmca_cutoff_hypothesis_test_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved papers/44_quantum_gravity/data/cc_cmca_cutoff_hypothesis_test_results.json")
