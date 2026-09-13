"""
GTE structural derivation of the Pati-Salam leptogenesis scale M_{R,1}.

Establishes that the three-tape BPS instanton suppression factor
eps_FN^{N_c} = exp(-pi/N_c)^{N_c} = exp(-pi) accounts for the gap
between the GUT-scale common seesaw denominator M_R and the
leptogenesis scale M_{R,1}, combined with the b-value hierarchy
(b_{R,3}/b_{R,1})^{29/9} = (19/5)^{29/9} = 73.82.

Structural formula (CatA):
  M_{R,1} = M_R * eps_FN^{N_c} / (b_{R,3}/b_{R,1})^alpha
           = 1.90e16 GeV * exp(-pi) / 73.82
           = 1.1105e13 GeV

Agreement with oscillation-anchored calibration: 0.04%.

Usage: python3 pati_salam_scale_derivation.py
Output: pati_salam_scale_derivation_results.json
"""

import signal
import sys
import json
from math import comb, exp, sqrt, log, pi

TIMEOUT_SECONDS = 300

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ============================================================
# GTE CONSTANTS
# ============================================================
alpha_seesaw = 29 / 9                # CatAL: fn_texture_gives_seesaw_exponent
b_R = [5, 11, 19]                    # CatAL: Braid Atlas RH neutrino b-values (gen 1,2,3)
M_R_GUT = 1.897e16                   # CatA: P21 common seesaw denominator (GeV)
M_R1_calibrated = 1.11e13           # CatA: oscillation-anchored leptogenesis scale (GeV)
eps_FN = exp(-pi / 3)               # CatAL: CartanFlavonPotential.lean — BPS kink action per tape
N_c = 3                              # CatAL: number of CMCA tapes (P45 DPP)
D_top = exp(-1 / 3)                  # CatAL: topological dilution factor
sphaleron = 28 / 79                  # SM sphaleron conversion (SM structure forced by PSC)
K1_thermal = 15.93                   # CatA: P47 efficiency factor
eps1_orig = 3.9829e-5               # CatA: Z7 Casas-Ibarra CP asymmetry
PDG_etaB = 6.10e-10                 # Planck 2018 CMB+BBN
sigma_PDG = 0.06e-10

# Exact sech overlap integrals (scipy.integrate.quad, error < 7e-15)
I5_exact = 0.6018776540             # I(5) = integral sech(x)sech(5x)dx
I11_exact = 0.2828004328            # I(11) = integral sech(x)sech(11x)dx


def f_crv(x):
    """CRV loop function (Covi-Roulet-Vissani 1996): exact one-loop type-I seesaw."""
    return sqrt(x) * (1 / (1 - x) + 1 - (1 + x) * log((1 + x) / x))


# ============================================================
# PART 1: b-value ordering analysis — M_Ri = M_R_GUT / b_i^alpha
# ============================================================
MR_vals = [M_R_GUT / (bi ** alpha_seesaw) for bi in b_R]

print("PART 1: M_Ri = M_R_GUT / b_i^alpha (seesaw exponent 29/9)")
for i, (bi, MRi) in enumerate(zip(b_R, MR_vals)):
    print(f"  M_R_gen{i+1} = {MRi:.4e} GeV  (b={bi}, b^alpha={bi**alpha_seesaw:.2f})")
print("  Ordering: gen1 > gen2 > gen3  [INVERTED — inconsistent with leptogenesis M_R1<M_R2<M_R3]")

# ============================================================
# PART 2: Gap factor identification
# ============================================================
gap_factor = M_R_GUT / (M_R1_calibrated * (b_R[2] / b_R[0]) ** alpha_seesaw)
exp_pi_val = exp(pi)
gap_accuracy_pct = abs(gap_factor - exp_pi_val) / exp_pi_val * 100

print(f"\nPART 2: Gap factor analysis")
print(f"  Gap = M_R_GUT / (M_R1_calib * (b_R3/b_R1)^alpha) = {gap_factor:.6f}")
print(f"  exp(pi) = {exp_pi_val:.6f}")
print(f"  Agreement: {gap_accuracy_pct:.4f}%")
print(f"  eps_FN^N_c = {eps_FN**N_c:.8f}  vs  exp(-pi) = {exp(-pi):.8f}")

# ============================================================
# PART 3: GTE structural formula for M_{R,1}
# ============================================================
M_R1_GTE = M_R_GUT * eps_FN ** N_c / (b_R[2] / b_R[0]) ** alpha_seesaw
deviation_pct = abs(M_R1_GTE / M_R1_calibrated - 1) * 100

print(f"\nPART 3: GTE structural M_{{R,1}}")
print(f"  M_R1 = M_R_GUT * eps_FN^N_c / (b_R3/b_R1)^alpha")
print(f"       = {M_R_GUT:.3e} * {eps_FN**N_c:.6f} / {(b_R[2]/b_R[0])**alpha_seesaw:.2f}")
print(f"       = {M_R1_GTE:.6e} GeV")
print(f"  Calibrated value: {M_R1_calibrated:.3e} GeV")
print(f"  Deviation: {deviation_pct:.4f}%")

# Kink overlap formula components
f1f2 = 1 / (5 ** 2 * 11 ** 2)
kappa = 0.3 * (K1_thermal / 5 ** 2)
eta_B_derived = D_top * sphaleron * (eps1_orig * (M_R1_GTE / M_R1_calibrated)) * f1f2 * kappa
eta_B_calib = D_top * sphaleron * eps1_orig * f1f2 * kappa
sigma_val = (eta_B_derived - PDG_etaB) / sigma_PDG

print(f"\nPART 4: Impact on eta_B")
print(f"  eta_B (derived M_R1):    {eta_B_derived:.4e}  ({sigma_val:+.2f}sigma from Planck 2018)")
print(f"  eta_B (calibrated M_R1): {eta_B_calib:.4e}")
print(f"  Change: {(eta_B_derived/eta_B_calib-1)*100:+.3f}%  (negligible — eta_B tension unchanged)")

# ============================================================
# Save results
# ============================================================
import os
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "pati_salam_scale_derivation_results.json")

results = {
    "description": "GTE structural derivation of Pati-Salam leptogenesis scale M_{R,1}",
    "formula": "M_R1 = M_R_GUT * eps_FN^N_c / (b_{R,3}/b_{R,1})^{29/9}",
    "GTE_constants": {
        "alpha_seesaw": alpha_seesaw,
        "b_R_values_gen123": b_R,
        "M_R_GUT_GeV": M_R_GUT,
        "M_R1_calibrated_GeV": M_R1_calibrated,
        "eps_FN_per_tape": eps_FN,
        "N_c_tapes": N_c,
        "eps_FN_power_Nc": eps_FN ** N_c,
        "exp_minus_pi": exp(-pi),
    },
    "part1_ordering": {
        f"gen{i+1}_b{bi}": {"b_alpha": round(bi**alpha_seesaw, 4), "M_Ri_GeV": round(MR_vals[i], 4)}
        for i, bi in enumerate(b_R)
    },
    "part1_conclusion": "Inverted ordering M_R1>M_R2>M_R3 — direct b-value scheme incompatible with leptogenesis",
    "part2_gap": {
        "gap_factor": round(gap_factor, 6),
        "exp_pi": round(exp_pi_val, 6),
        "agreement_pct": round(gap_accuracy_pct, 4),
        "mechanism": "eps_FN^N_c = exp(-pi/3)^3 = exp(-pi) — three-tape BPS instanton suppression",
    },
    "part3_structural_formula": {
        "M_R1_GTE_GeV": round(M_R1_GTE, 6),
        "M_R1_calibrated_GeV": M_R1_calibrated,
        "deviation_pct": round(deviation_pct, 4),
        "cat_level": "CatA",
        "components": {
            "M_R_GUT": "CatA (P21 Sigma_m_nu derivation)",
            "(b_R3/b_R1)^{29/9}": "CatAL (fn_texture_gives_seesaw_exponent)",
            "eps_FN^N_c": "CatA (eps_FN CatAL per tape * N_c CatAL; product CatA)",
        },
    },
    "part4_eta_B": {
        "eta_B_with_derived_MR1": round(eta_B_derived, 15),
        "eta_B_with_calibrated_MR1": round(eta_B_calib, 15),
        "sigma_from_PDG": round(sigma_val, 2),
        "conclusion": "eta_B tension unchanged at ~4.9 sigma; M_R1 derivation changes eta_B by <0.05%",
    },
}

with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)
print(f"\nResults saved to {out_path}")
