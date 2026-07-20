"""
Z7 sine-Gordon exact S-matrix analysis.

The Φ_MDL Z₇ potential V(Φ) = (m²/49)(1 - cos 7Φ) is a sine-Gordon model
with β² = 49. The Zamolodchikov-Zamolodchikov (1979) exact S-matrix applies
because sine-Gordon is classically and quantum-mechanically exactly integrable.

Key result: β² = 49 > 8π ≈ 25.13, placing the Z₇ theory firmly in the
REPULSIVE regime (ξ = β²/(8π - β²) < 0).

Consequences:
- No breather/bion bound states in the kink sector (consistent with earlier
  G36 bion ruling-out from the topological L2 binary structure).
- The kink-kink S-matrix is analytically known for all rapidities.
- Full quantum scattering matrix available without loop integrals.

References:
  Zamolodchikov, A.B. and Zamolodchikov, Al.B. (1979).
  "Factorized S-matrices in two dimensions as the exact solutions of certain
  relativistic quantum field theory models." Annals of Physics 120(2), 253-291.

Epic: EPIC_080, Rank G09 (S-matrix / QFT closure path).
"""

import math


def compute_xi(beta_sq: float) -> float:
    """Compute sine-Gordon coupling parameter ξ = β²/(8π - β²)."""
    denominator = 8 * math.pi - beta_sq
    if abs(denominator) < 1e-10:
        raise ValueError("beta^2 = 8*pi: free fermion point, xi diverges")
    return beta_sq / denominator


def classify_regime(beta_sq: float) -> str:
    """Classify sine-Gordon regime from β²."""
    threshold = 8 * math.pi
    if beta_sq < threshold:
        return "ATTRACTIVE (beta^2 < 8*pi: breathers exist)"
    elif beta_sq > threshold:
        return "REPULSIVE (beta^2 > 8*pi: no bound states)"
    else:
        return "FREE FERMION POINT (beta^2 = 8*pi)"


def tree_level_amplitude(m_mev: float) -> dict:
    """
    Tree-level 2→2 scattering amplitude from G27 propagator + LSZ.

    From the Z₇ potential expansion:
      V(η) = m²η²/2 - m²·49η⁴/4! + m²·7⁴η⁶/6! - ...
    The quartic coupling is λ₄ = m²×49 (G27, CatAD).
    Tree-level connected 4-point function from LSZ:
      iM_{2→2} = -iλ₄ = -im²×49  (contact interaction, tree level).
    """
    lambda_4 = m_mev**2 * 49
    return {
        "lambda_4_MeV2": lambda_4,
        "iM_tree_contact": -lambda_4,
        "amplitude_description": "iM = -i*m^2*49 (tree-level contact, Z7 fingerprint)",
        "note": "Full momentum-dependent amplitude requires loop corrections beyond tree level.",
    }


def main():
    beta_sq = 49  # Z7: beta = 7, beta^2 = 49
    m_tau_mev = 1776.86
    m_kink_mev = (8.0 / 49.0) * m_tau_mev  # BPS kink mass

    xi = compute_xi(beta_sq)
    regime = classify_regime(beta_sq)

    print("=" * 60)
    print("Z7 SINE-GORDON EXACT S-MATRIX ANALYSIS")
    print("=" * 60)
    print(f"\nPotential: V(Φ) = (m²/49)(1 - cos 7Φ)")
    print(f"  β  = 7")
    print(f"  β² = {beta_sq}")
    print(f"  8π = {8 * math.pi:.6f}")
    print(f"  ξ  = β²/(8π - β²) = {xi:.6f}")
    print(f"\nRegime: {regime}")
    print(f"\nS-matrix conclusions:")
    print(f"  - Exact S-matrix: known analytically (Zamolodchikov 1979)")
    print(f"  - No loop integrals required for kink sector")
    print(f"  - No breather bound states (ξ = {xi:.4f} < 0)")
    print(f"  - Kink-kink: purely elastic, S_kk(θ) given by ZZ integral formula")
    print(f"  - Kink-antikink: transmission and reflection amplitudes known")
    print()

    # Tree-level perturbative sector
    amp = tree_level_amplitude(m_kink_mev)
    print(f"Tree-level (perturbative) sector:")
    print(f"  m_kink = {m_kink_mev:.2f} MeV")
    print(f"  λ₄ = m²×49 = {amp['lambda_4_MeV2']:.4f} MeV²")
    print(f"  iM (tree, 2→2 contact) = {amp['iM_tree_contact']:.4f} MeV²")
    print()

    # G9 closure assessment
    print("G9 CLOSURE ASSESSMENT:")
    print("  Particle sector: G27 (CatAD) → LSZ → tree-level iM = -im²×49")
    print("  Kink sector:     Z7 integrability → exact quantum S-matrix (Zamolodchikov 1979)")
    print("  Status:          PARTIAL CatAD path established")
    print("  Remaining:       formal LSZ derivation from Z[J]; Lean cert")
    print()

    # G15 implication
    print("G15 IMPLICATION (proton bound state):")
    print(f"  Repulsive regime (ξ = {xi:.4f} < 0) => same-field kinks REPEL")
    print("  Proton ≠ 3 same-field sine-Gordon kinks in 1D")
    print("  => G15 requires multi-tape (3D) binding mechanism")
    print("  => See three_kink_proton_bound_state.py for mass estimate")


if __name__ == "__main__":
    main()
