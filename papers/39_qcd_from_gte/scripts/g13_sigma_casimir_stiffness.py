"""
QCD string tension from the GTE kink condensate: corrected prefactor.

The string tension scale is set by the kink condensate m_kink^2 times the
ratio of the colour-flux state count N_c^2 to the Wilson-loop quadratic
stiffness at the identity C_F * N_c (the Burnside coset-filling stiffness):

    sigma_GTE = (N_c^2 / (C_F * N_c)) * m_kink^2 = (N_c / C_F) * m_kink^2 = (9/4) m_kink^2.

This replaces the earlier prefactor log2(N_c^2) = log2(9). The MDL gap
DeltaK = log2(N_c^2) bits is the *confinement criterion* (it proves free
quarks cost infinite description length) and is NOT the string-tension scale.
Using it as a linear prefactor overpredicts sigma by log2(9)/(9/4) = 1.409
(40.8%). The scale is the colour-flux multiplicity normalised by the Wilson
stiffness, both already established in the F21->SU(3) Burnside analysis.

Compares against the L=16, beta=6.0, N=80 symmetric-Creutz lattice measurement
sigma_phys = 0.18930 +/- 0.00245 GeV^2.
"""
import json
import numpy as np

# --- Lattice measurement (L=16, beta=6.0, N=80 configs; symmetric Creutz) ---
SIGMA_PHYS = 0.18930297624589001   # GeV^2
SIGMA_ERR = 0.002451892937034941   # GeV^2

# --- GTE structural constants ---
V_H = 246.16          # Higgs VEV (GeV), from SRRG
N_C = 3               # number of colours
C_F = 4.0 / 3.0       # fundamental quadratic Casimir of SU(3)

# BPS kink mass: M_kink = 4 v_H / (7^4 sqrt(2))
m_kink = 4 * V_H / (49**2 * np.sqrt(2))
mk2 = m_kink**2

# Corrected prefactor: F = N_c^2 / (C_F N_c) = N_c / C_F
F_correct = N_C / C_F                  # = 9/4 = 2.25
F_prior = np.log2(N_C**2)              # = log2(9) = 3.1699 (incorrect: bit-count)

sigma_correct = F_correct * mk2
sigma_prior = F_prior * mk2

F_measured = SIGMA_PHYS / mk2
F_err = SIGMA_ERR / mk2

results = {
    "measurement": {
        "sigma_phys_GeV2": SIGMA_PHYS,
        "sigma_err_GeV2": SIGMA_ERR,
        "source": "g13_su3_l16_results.json (L=16, beta=6.0, N=80)",
    },
    "m_kink_GeV": m_kink,
    "m_kink2_GeV2": mk2,
    "target_factor_F": {"value": F_measured, "err": F_err, "rel_err_pct": 100 * F_err / F_measured},
    "corrected_formula": {
        "expression": "sigma = (N_c^2/(C_F*N_c)) m_kink^2 = (N_c/C_F) m_kink^2 = (9/4) m_kink^2",
        "F": F_correct,
        "sigma_pred_GeV2": sigma_correct,
        "pull_sigma": (sigma_correct - SIGMA_PHYS) / SIGMA_ERR,
        "rel_err_pct": 100 * (sigma_correct - SIGMA_PHYS) / SIGMA_PHYS,
        "numerator_N_c2": N_C**2,
        "denominator_C_F_N_c": C_F * N_C,
    },
    "prior_formula": {
        "expression": "sigma = log2(N_c^2) m_kink^2 = log2(9) m_kink^2",
        "F": F_prior,
        "sigma_pred_GeV2": sigma_prior,
        "pull_sigma": (sigma_prior - SIGMA_PHYS) / SIGMA_ERR,
        "rel_err_pct": 100 * (sigma_prior - SIGMA_PHYS) / SIGMA_PHYS,
    },
    "f_quant_resolution": {
        "f_quant_old": SIGMA_PHYS / sigma_prior,
        "f_quant_old_as_ratio": F_correct / F_prior,           # (9/4)/log2(9)
        "f_quant_corrected": SIGMA_PHYS / sigma_correct,        # ~ 1
        "note": "f_quant=0.710 was (N_c/C_F)/log2(N_c^2), an artifact of the wrong prior normalisation; with the corrected formula no quantum suppression factor is needed.",
    },
    "null_tests": {},
}

# Null test: neighbour-atom perturbations must fail
neighbours = {
    "N_c/C_F=9/4 [PROPOSED]": N_C / C_F,
    "(N_c-1)/C_F": (N_C - 1) / C_F,
    "(N_c+1)/C_F": (N_C + 1) / C_F,
    "N_c^2/(C_F N_c -1)": N_C**2 / (C_F * N_C - 1),
    "N_c^2/(C_F N_c +1)": N_C**2 / (C_F * N_C + 1),
    "(N_c^2-1)/(C_F N_c)": (N_C**2 - 1) / (C_F * N_C),
    "(N_c^2+1)/(C_F N_c)": (N_C**2 + 1) / (C_F * N_C),
}
results["null_tests"]["neighbours"] = {
    k: {"F": v, "pull_sigma": (v - F_measured) / F_err} for k, v in neighbours.items()
}

# Null test: dense rational grid (how many a/b within 1 sigma?)
hits = []
for b in range(1, 9):
    for a in range(1, 30):
        v = a / b
        if abs((v - F_measured) / F_err) < 1.0:
            hits.append({"a": a, "b": b, "value": v, "pull_sigma": (v - F_measured) / F_err})
results["null_tests"]["rationals_within_1sigma"] = hits

if __name__ == "__main__":
    print(json.dumps(results, indent=2))
    out = "g13_sigma_casimir_stiffness_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out}")
