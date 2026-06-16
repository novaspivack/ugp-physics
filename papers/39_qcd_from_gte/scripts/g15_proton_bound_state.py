"""
Proton inter-tape coupling analysis — G15 G_eff assessment.

Extends three_kink_proton_bound_state.py with the inter-tape polynomial
coupling analysis using the ZZ S-matrix insight from G9.

G9 result: Z₇ sine-Gordon is in the repulsive regime (β²=49 > 8π),
so same-tape kinks do not bind. The proton (w_x=2, w_y=2, w_z=6) uses
three kinks on DIFFERENT tapes. Binding comes from inter-tape interactions.

The inter-tape coupling in the Φ_MDL Hamiltonian involves the cross-polynomial:
    p(L, C, R) = C + R - C·R - L·C·R

defined over Z/7Z. For the proton state:
    p(2, 2, 6) = 2+6 - 2·6 - 2·2·6 = -28

The energy contribution of the inter-tape coupling:
    ΔM = G_inter · |p(w_x, w_y, w_z)| / 6

This script:
1. Computes p(2,2,6) and verifies algebraically
2. Determines the G_inter required for 68 MeV binding
3. Compares to G_eff ≈ 0.5 from the Bell-CHSH analysis (G10/BR)
4. Evaluates whether G_eff (Bell) self-consistently gives the proton mass
5. Checks the Z₃ color orbit of the proton winding state
6. Assesses G15 status

References:
  - P42: BPS kink mass M_kink = (8/49)·m_τ (CatAL)
  - P46: proton winding (w_x=2, w_y=2, w_z=6), G14 closure (CatAD)
  - P39/G13: QCD string tension (OPEN prerequisite for G15)
  - G09: ZZ exact S-matrix, repulsive regime β²=49>8π
  - BR (closed): Bell-CHSH S=2.44 from diagonal H_grav, G_eff≈0.5 (CatA)

Epic: EPIC_080, Rank G15 (proton/hadron bound-state dynamics).
"""

import math
import json
import signal
import numpy as np

TIMEOUT_SECONDS = 120
signal.signal(signal.SIGALRM, lambda s, f: None)
signal.alarm(TIMEOUT_SECONDS)

# ── Physical constants ─────────────────────────────────────────────────────────
M_TAU_MEV   = 1776.86    # tau lepton mass, PDG 2024
M_PROTON_MEV = 938.272   # proton mass, PDG 2024
HBAR_C_MEV_FM = 197.3269804  # MeV·fm

# GTE parameters
N_MOD = 7     # Z₇ modulus
BETA_SQ = 49  # β² for Z₇ sine-Gordon = N_MOD²
G_EFF_BELL = 0.5  # from BR (Bell-CHSH CatA, S=2.44)
SIGMA_PDG_GEV2 = 0.18  # QCD string tension, GeV²

# BPS kink mass (P42 CatAL)
M_KINK_MEV = (8.0 / 49.0) * M_TAU_MEV


# ── Core polynomial ────────────────────────────────────────────────────────────
def inter_tape_poly(L: int, C: int, R: int) -> int:
    """
    GTE inter-tape cross-polynomial over Z/7Z integers.
    p(L, C, R) = C + R - C·R - L·C·R
    """
    return C + R - C * R - L * C * R


# ── T1: inter-tape coupling at proton winding ──────────────────────────────────
def compute_proton_polynomial():
    w_x, w_y, w_z = 2, 2, 6
    p_val = inter_tape_poly(w_x, w_y, w_z)

    # Algebraic verification
    L, C, R = w_x, w_y, w_z
    manual = C + R - C * R - L * C * R

    # Continuum version (using phi₀/π as fractional argument)
    phi_x = 2 * np.pi * w_x / N_MOD
    phi_y = 2 * np.pi * w_y / N_MOD
    phi_z = 2 * np.pi * w_z / N_MOD
    p_cont = inter_tape_poly(phi_x / np.pi, phi_y / np.pi, phi_z / np.pi)

    return {
        "w_proton": (w_x, w_y, w_z),
        "p_integer": p_val,
        "p_integer_manual_check": manual,
        "p_abs": abs(p_val),
        "p_over_6": abs(p_val) / 6,
        "p_continuum": float(p_cont),
    }


# ── T2: G_eff consistency check ────────────────────────────────────────────────
def g_eff_analysis(p_abs: float):
    """
    Formula: ΔM = G_inter · |p| / 6
    where ΔM = M_proton - 3·M_kink (the inter-tape confinement energy addition).

    Sign convention: p(2,2,6) = -28 < 0. The negative p value means the
    inter-tape coupling RAISES the energy (confinement), consistent with
    M_proton > 3·M_kink. We use |p| and positive G_inter.
    """
    three_m_kink = 3.0 * M_KINK_MEV
    delta_M = M_PROTON_MEV - three_m_kink

    # Required G_inter (in MeV) for the formula ΔM = G_inter · |p| / 6
    G_inter_required_MeV = delta_M * 6 / p_abs

    # Prediction using G_eff from Bell (G_eff_Bell ≈ 0.5)
    # Bell G_eff is dimensionless — need to assign an energy scale.
    # Natural GTE scale: G_eff_Bell * M_kink.
    G_inter_Bell_MeV = G_EFF_BELL * M_KINK_MEV
    delta_M_Bell = G_inter_Bell_MeV * p_abs / 6
    M_proton_Bell_pred = three_m_kink + delta_M_Bell

    # Ratio
    ratio = G_inter_required_MeV / G_inter_Bell_MeV

    return {
        "three_M_kink_MeV": three_m_kink,
        "delta_M_MeV": delta_M,
        "delta_M_frac": delta_M / three_m_kink,
        "G_inter_required_MeV": G_inter_required_MeV,
        "G_inter_Bell_MeV": G_inter_Bell_MeV,
        "G_eff_Bell_dimless": G_EFF_BELL,
        "delta_M_from_Bell_Geff_MeV": delta_M_Bell,
        "M_proton_pred_from_Bell_Geff_MeV": M_proton_Bell_pred,
        "deviation_from_PDG_MeV": M_proton_Bell_pred - M_PROTON_MEV,
        "ratio_required_over_Bell": ratio,
        "bell_gives_right_mass": abs(M_proton_Bell_pred - M_PROTON_MEV) < 20,
    }


# ── String tension cross-check ─────────────────────────────────────────────────
def string_tension_estimate():
    l_kink_fm = HBAR_C_MEV_FM / M_KINK_MEV
    sigma_MeV_per_fm = SIGMA_PDG_GEV2 * 1e6 / HBAR_C_MEV_FM
    V_string_MeV = sigma_MeV_per_fm * l_kink_fm
    return {
        "l_kink_fm": l_kink_fm,
        "sigma_MeV_per_fm": sigma_MeV_per_fm,
        "V_string_at_kink_scale_MeV": V_string_MeV,
        "ratio_to_needed": V_string_MeV / (M_PROTON_MEV - 3 * M_KINK_MEV),
    }


# ── Z₃ color orbit ─────────────────────────────────────────────────────────────
def z3_color_orbit():
    """
    The proton winding (w_x, w_y, w_z) = (2, 2, 6).
    Under the Z₃ color rotation w → w+1 mod 7 (applied identically to all tapes
    — this is the simplest color orbit; true color orbit depends on G14/G12 structure):
    """
    base = (2, 2, 6)
    orbit = [(b % N_MOD, b % N_MOD, (base[2] + k) % N_MOD) for k, b in enumerate([2, 3, 4])]
    orbit = [
        (2, 2, 6),
        (3, 3, 0),
        (4, 4, 1),
    ]
    return [
        {"state": list(s), "p_val": inter_tape_poly(*s)}
        for s in orbit
    ]


# ── All states with |p| = 28 ───────────────────────────────────────────────────
def states_with_max_poly():
    p28 = []
    for L in range(N_MOD):
        for C in range(N_MOD):
            for R in range(N_MOD):
                v = inter_tape_poly(L, C, R)
                if abs(v) == 28:
                    p28.append({"state": [L, C, R], "p": v})
    return p28


# ── T3: proton mass formula ────────────────────────────────────────────────────
def proton_mass_formula(G_inter_MeV: float, p_abs: float):
    """
    M_proton = 3 × M_kink + G_inter × |p(2,2,6)| / 6

    With G_inter = 14.57 MeV (empirically fixed to PDG proton mass):
      M_proton = 870.30 + 14.57 × 28/6 = 870.30 + 68.0 = 938.3 MeV ✓

    G_inter needs to be derived from G13 (QCD string tension, OPEN).
    """
    M_pred = 3 * M_KINK_MEV + G_inter_MeV * p_abs / 6
    return {
        "formula": "M_proton = 3 × M_kink + G_inter × |p(2,2,6)| / 6",
        "M_kink_MeV": M_KINK_MEV,
        "three_M_kink_MeV": 3 * M_KINK_MEV,
        "G_inter_MeV": G_inter_MeV,
        "p_abs": p_abs,
        "M_proton_predicted_MeV": M_pred,
        "M_proton_PDG_MeV": M_PROTON_MEV,
        "error_MeV": M_pred - M_PROTON_MEV,
        "error_pct": 100 * (M_pred - M_PROTON_MEV) / M_PROTON_MEV,
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("G15: PROTON INTER-TAPE COUPLING — G_eff ANALYSIS")
    print("=" * 65)

    # T1
    poly = compute_proton_polynomial()
    print(f"\nT1: Inter-tape polynomial p(w_x, w_y, w_z)")
    print(f"  Proton winding: (w_x, w_y, w_z) = {poly['w_proton']}")
    print(f"  p(L,C,R) = C+R - C·R - L·C·R")
    print(f"  p(2,2,6) = 2+6 - 2·6 - 2·2·6 = {poly['p_integer']}")
    print(f"  |p(2,2,6)| = {poly['p_abs']}")
    print(f"  |p|/6 = {poly['p_over_6']:.4f}")
    print(f"  Continuum value (at phi₀/π): {poly['p_continuum']:.4f}")

    # T2
    ga = g_eff_analysis(poly['p_abs'])
    print(f"\nT2: G_eff analysis for 68 MeV inter-tape confinement energy")
    print(f"  3 × M_kink = {ga['three_M_kink_MeV']:.1f} MeV")
    print(f"  M_proton   = {M_PROTON_MEV:.1f} MeV")
    print(f"  ΔM needed  = {ga['delta_M_MeV']:.1f} MeV ({ga['delta_M_frac']*100:.2f}% of 3·M_kink)")
    print(f"")
    print(f"  Formula: ΔM = G_inter × |p| / 6")
    print(f"  Required G_inter = {ga['G_inter_required_MeV']:.2f} MeV")
    print(f"")
    print(f"  Bell G_eff = {G_EFF_BELL} → G_inter (Bell) = G_eff × M_kink = {ga['G_inter_Bell_MeV']:.1f} MeV")
    print(f"  Predicted ΔM (Bell G_eff) = {ga['delta_M_from_Bell_Geff_MeV']:.1f} MeV")
    print(f"  Predicted M_proton (Bell) = {ga['M_proton_pred_from_Bell_Geff_MeV']:.1f} MeV")
    print(f"  Deviation from PDG: {ga['deviation_from_PDG_MeV']:.1f} MeV")
    print(f"  Bell G_eff gives correct proton mass: {ga['bell_gives_right_mass']}")
    print(f"  Ratio G_inter_required / G_inter_Bell = {ga['ratio_required_over_Bell']:.4f}")

    # String tension
    st = string_tension_estimate()
    print(f"\n  String tension cross-check:")
    print(f"  l_kink = {st['l_kink_fm']:.3f} fm")
    print(f"  σ = 0.18 GeV² = {st['sigma_MeV_per_fm']:.1f} MeV/fm")
    print(f"  V_string(l_kink) = {st['V_string_at_kink_scale_MeV']:.1f} MeV (ratio to needed: {st['ratio_to_needed']:.2f})")

    # Z3 orbit
    orbit = z3_color_orbit()
    print(f"\n  Z₃ color orbit of proton state:")
    for entry in orbit:
        print(f"  p({entry['state']}) = {entry['p_val']}")
    print(f"  (Note: Z₃ orbit is NOT closed under p — orbit elements have different |p|)")

    # States with |p|=28
    max_states = states_with_max_poly()
    print(f"\n  States with |p| = 28: {len(max_states)}")
    for s in max_states:
        print(f"    {s}")

    # T3: Mass formula
    G_inter_empirical = ga['G_inter_required_MeV']
    mf = proton_mass_formula(G_inter_empirical, poly['p_abs'])
    print(f"\nT3: Proton mass formula")
    print(f"  {mf['formula']}")
    print(f"  = {mf['three_M_kink_MeV']:.2f} + {mf['G_inter_MeV']:.2f} × {int(mf['p_abs'])}/6")
    print(f"  = {mf['three_M_kink_MeV']:.2f} + {mf['G_inter_MeV'] * mf['p_abs'] / 6:.2f}")
    print(f"  = {mf['M_proton_predicted_MeV']:.2f} MeV (PDG: {mf['M_proton_PDG_MeV']:.2f} MeV)")
    print(f"  Error: {mf['error_MeV']:.3f} MeV ({mf['error_pct']:.4f}%)")
    print(f"  G_inter = {G_inter_empirical:.2f} MeV is EMPIRICAL — requires G13 derivation")

    print(f"\n{'=' * 65}")
    print("CONCLUSIONS")
    print(f"{'=' * 65}")
    print(f"1. p(2,2,6) = -28  [algebraically exact]")
    print(f"2. Required G_inter = {G_inter_empirical:.2f} MeV for 68 MeV binding")
    print(f"3. Bell G_eff (0.5) gives ΔM = {ga['delta_M_from_Bell_Geff_MeV']:.1f} MeV → M_proton = {ga['M_proton_pred_from_Bell_Geff_MeV']:.1f} MeV (WRONG by {ga['deviation_from_PDG_MeV']:.0f} MeV)")
    print(f"4. Bell G_eff does NOT give the proton mass — different physics scales")
    print(f"5. G15 remains OPEN (G13 prerequisite unresolved)")
    print()
    print("Physical interpretation:")
    print("  The Bell G_eff governs quantum entanglement at the Planck/kink scale.")
    print("  The proton inter-tape binding is a hadronic-scale QCD confinement effect.")
    print("  These are different phenomena requiring different coupling strengths.")
    print("  G_inter_proton / (G_eff_Bell × M_kink) = 1/10 — a suppression factor")
    print("  that needs a GTE derivation from G13 (string tension).")

    return {
        "poly": poly,
        "g_eff_analysis": ga,
        "string_tension": st,
        "z3_orbit": orbit,
        "states_with_max_poly": max_states,
        "mass_formula": mf,
        "conclusion": {
            "p_proton": poly['p_integer'],
            "G_inter_required_MeV": G_inter_empirical,
            "G_eff_Bell_works": False,
            "G15_status": "OPEN — G_inter formula established; G_inter=14.57 MeV empirical; G13 required for derivation",
        },
    }


if __name__ == "__main__":
    results = main()
    signal.alarm(0)

    out_path = __file__.replace(".py", "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {out_path}")
