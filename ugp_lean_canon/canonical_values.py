"""
ugp_lean_canon/canonical_values.py

Single source of truth for all Lean-certified UGP structural quantities.

Every entry either:
  - is an exact Fraction (for rationals), or
  - is a 60-digit mpmath mpf (for algebraic irrationals), or
  - is computed at module load from the above.

No downstream Python script should hard-code these values; import from here.
Adding a new Lean-certified quantity: add it to PRIMITIVES or compute it in
the DERIVED section, citing the exact Lean file + theorem + zero-sorry status.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

import mpmath as mp

mp.mp.dps = 60  # 60-digit precision throughout


# ── Primitive Lean-certified rationals ────────────────────────────────────────
# Format: (value, "LeanModule.theorem_name")
PRIMITIVES: dict[str, tuple[Any, str]] = {
    # QCD colour rank
    "Nc": (
        3,
        "BraidAtlas.ChargeDerivation.anomaly_cancellation_forces_Nc_3",
    ),
    # Mirror offset: delta = Nc + (Nc^2 - 1)/2
    "delta": (
        7,
        "GaloisStructure.MinimalCyclotomic.delta_from_Nc",
    ),
    # Ridge level: n_ridge = 2 F(5) = 10
    "n_ridge": (
        10,
        "Phase4.AsymptoticSparsity.b1_unique_at_n10 (sieve-forced)",
    ),
    # Sieve-forced lepton seed b1
    "b_1": (
        73,
        "Phase4.AsymptoticSparsity.rsuc_theorem",
    ),
    # UCL curvature k_L^2 = 7/512
    "k_L2": (
        Fraction(7, 512),
        "ElegantKernel.k_L2_eq",
    ),
    # Bare squared gauge couplings (exact rationals)
    "g1Sq_bare": (
        Fraction(16, 125),
        "Phase4.GaugeCouplings.g1Sq_bare_eq",
    ),
    "g2Sq_bare": (
        Fraction(2329, 5400),
        "Phase4.GaugeCouplings.g2Sq_bare_eq",
    ),
    "g3Sq_bare": (
        Fraction(41075281, 27648000),
        "Phase4.GaugeCouplings.g3Sq_bare_eq",
    ),
    # Strand count = (Nc^2 - 1) / 4
    "strand_count": (
        2,
        "MassRelations.KoideAngle.strand_count_eq_su_nc_adj_div_4",
    ),
    # Koide phase theta = (Nc^2 - 1) / (4 Nc^2) = 2/9
    "theta_Koide": (
        Fraction(2, 9),
        "MassRelations.KoideAngle.koide_angle_from_N_c_pure",
    ),
    # Seesaw exponent = Nc + theta_Koide = 29/9
    "seesaw_exponent": (
        Fraction(29, 9),
        "MassRelations.KoideAngle.nuSeesawExponent",
    ),
    # VV down-quark exponents
    "alpha_d": (
        Fraction(13, 9),
        "MassRelations.VVAllCoefficientsFromNc.vv_all_coefficients_from_Nc",
    ),
    "beta_d": (
        Fraction(-7, 6),
        "MassRelations.VVAllCoefficientsFromNc.vv_all_coefficients_from_Nc",
    ),
    "gamma_d": (
        Fraction(-5, 14),
        "MassRelations.VVAllCoefficientsFromNc.vv_all_coefficients_from_Nc",
    ),
    # SM winding numbers at Nc=3: {Nc-1, -1, 0, -Nc} = {2, -1, 0, -3}
    "W_up":      (2,  "BraidAtlas.ChargeDerivation.sm_winding_numbers_from_Nc"),
    "W_down":    (-1, "BraidAtlas.ChargeDerivation.sm_winding_numbers_from_Nc"),
    "W_nu":      (0,  "BraidAtlas.ChargeDerivation.sm_winding_numbers_from_Nc"),
    "W_lepton":  (-3, "BraidAtlas.ChargeDerivation.sm_winding_numbers_from_Nc"),
    # FN texture charges for b^(29/9): (q1, q2) = (Nc, strand)
    "FN_q1": (
        3,
        "MassRelations.NeutrinoFroggattNielsen.fn_texture_3_2_is_unique_singleton_atomic",
    ),
    "FN_q2": (
        2,
        "MassRelations.NeutrinoFroggattNielsen.fn_texture_3_2_is_unique_singleton_atomic",
    ),
    # Cyclotomic conductor
    "zeta_conductor": (
        120,
        "GaloisStructure.MinimalCyclotomic.lcm_20_24_eq_120",
    ),
}


# ── Primitive Lean-certified irrationals ─────────────────────────────────────
PHI = (mp.mpf(1) + mp.sqrt(5)) / 2        # golden ratio; ElegantKernel
K_GEN2 = -PHI / 2                          # thm_ucl1_fully_unconditional


# ── Derived Lean-certified quantities (computed from primitives) ──────────────

def _k_L2() -> mp.mpf:
    frac = PRIMITIVES["k_L2"][0]
    return mp.mpf(frac.numerator) / mp.mpf(frac.denominator)


def C_alg() -> mp.mpf:
    """Quarter-Lock algebraic prefactor.

    Source: UgpLean/Phase4/DeltaUGP.lean line 35 — deltaUGP_numeric_at_73
    Formula: C = -1/(k_gen2 + k_L2/4) + (7/4)(k_L2/k_gen2)
    """
    k = _k_L2()
    return (-1) / (K_GEN2 + k / 4) + (mp.mpf(7) / 4) * (k / K_GEN2)


def delta_UGP(b1: int = 73) -> mp.mpf:
    """delta_UGP(b1) = C_alg / b1.  Source: Phase4.DeltaUGP.deltaUGP_numeric_at_73"""
    return C_alg() / mp.mpf(b1)


def alpha_em_bare() -> mp.mpf:
    """Bare electromagnetic coupling from Lean-certified g1, g2.

    alpha_bare = e^2 / (4 pi) = g1^2 g2^2 / (4 pi (g1^2 + g2^2))
    Source: Phase4.GaugeCouplings.alpha_em_formula_exact
    """
    g1sq = mp.mpf(PRIMITIVES["g1Sq_bare"][0].numerator) / PRIMITIVES["g1Sq_bare"][0].denominator
    g2sq = mp.mpf(PRIMITIVES["g2Sq_bare"][0].numerator) / PRIMITIVES["g2Sq_bare"][0].denominator
    e2 = (g1sq * g2sq) / (g1sq + g2sq)
    return e2 / (4 * mp.pi)


# ── Reference table (computed once) ──────────────────────────────────────────
DERIVED = {
    "phi":              PHI,
    "k_gen2":           K_GEN2,
    "k_L2":             _k_L2(),
    "C_alg":            C_alg(),
    "delta_UGP_at_73":  delta_UGP(73),
    "alpha_em_bare":    alpha_em_bare(),
    "g1Sq_bare_float":  float(PRIMITIVES["g1Sq_bare"][0]),
    "g2Sq_bare_float":  float(PRIMITIVES["g2Sq_bare"][0]),
    "g3Sq_bare_float":  float(PRIMITIVES["g3Sq_bare"][0]),
}


# ── CODATA physics input (not Lean-certified; tagged) ────────────────────────
ALPHA_EM_CODATA = mp.mpf("0.0072973525693")  # CODATA 2018/2022


if __name__ == "__main__":
    print("UGP Lean canonical values (60-digit mpmath)")
    print(f"  C_alg            = {mp.nstr(DERIVED['C_alg'], 20)}")
    print(f"  delta_UGP(73)    = {mp.nstr(DERIVED['delta_UGP_at_73'], 20)}")
    print(f"  phi              = {mp.nstr(DERIVED['phi'], 20)}")
    print(f"  k_gen2           = {mp.nstr(DERIVED['k_gen2'], 20)}")
    print(f"  k_L2             = {mp.nstr(DERIVED['k_L2'], 20)}")
    print(f"  alpha_em_bare    = {mp.nstr(DERIVED['alpha_em_bare'], 20)}")
    print(f"  theta_Koide      = {PRIMITIVES['theta_Koide'][0]}")
    print(f"  seesaw_exponent  = {PRIMITIVES['seesaw_exponent'][0]}")
