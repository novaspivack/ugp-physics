"""
Quark Koide b² from CKM S₃ breaking — computational analysis.

The lepton sector has Q = 2/3, b² = 2 (S₃ unbroken).
Quarks have Q_up ≈ 0.849 (b² ≈ 3.09) and Q_down ≈ 0.731 (b² ≈ 2.39).
Physical mechanism: CKM matrix V = V_uL† V_dL ≠ 1 breaks the generation
S₃ shared by up/down Yukawa matrices.

Goal: derive b²_up and b²_down from CKM mixing structure.
"""

import numpy as np
import json
import os
from scipy.optimize import minimize

# ----- CKM magnitudes (PDG 2024) -----
V = np.array([
    [0.97373, 0.2243,  0.00382],
    [0.221,   0.975,   0.0408 ],
    [0.00857, 0.0400,  0.9991 ]
])

# ----- PDG quark masses (GeV, MS-bar ~2 GeV / pole for heavy) -----
m_u, m_c, m_t = 2.16e-3, 1.27, 172.69
m_d, m_s, m_b = 4.67e-3, 93.4e-3, 4.18

# =====================================================================
# Helper: standard Koide Q (sqrt-mass form)
# =====================================================================
def koide_Q(m1, m2, m3):
    sm = np.sqrt(m1) + np.sqrt(m2) + np.sqrt(m3)
    return (m1 + m2 + m3) / sm**2

def b2_from_Q(Q):
    """b² = 2(3Q - 1)  (from parametric Koide cone m_k = m0(1 + b cos θ_k)²)"""
    return 2.0 * (3.0 * Q - 1.0)

# =====================================================================
# Section 1: Measure b² for each sector
# =====================================================================
Q_lep  = koide_Q(0.511e-3, 105.658e-3, 1776.86e-3)
Q_up   = koide_Q(m_u, m_c, m_t)
Q_down = koide_Q(m_d, m_s, m_b)

b2_lep  = b2_from_Q(Q_lep)
b2_up   = b2_from_Q(Q_up)
b2_down = b2_from_Q(Q_down)

print("=== Sector Koide parameters ===")
print(f"  Leptons:    Q={Q_lep:.6f}  b²={b2_lep:.4f}  (δb²={b2_lep-2:.4f})")
print(f"  Up quarks:  Q={Q_up:.6f}  b²={b2_up:.4f}  (δb²={b2_up-2:.4f})")
print(f"  Down quarks:Q={Q_down:.6f}  b²={b2_down:.4f}  (δb²={b2_down-2:.4f})")

delta_b2_up   = b2_up   - 2.0
delta_b2_down = b2_down - 2.0

# =====================================================================
# Section 2: CKM structure analysis
# =====================================================================
print("\n=== CKM structure ===")

# Off-diagonal fraction (S₃ breaking measure)
off_diag = V.copy()
np.fill_diagonal(off_diag, 0.0)
S3_breaking = np.sum(off_diag**2) / np.sum(V**2)
print(f"  Off-diagonal fraction (S₃ breaking): {S3_breaking:.6f}")

# Standard CKM angles
theta_12 = np.arcsin(0.2243)          # Cabibbo
theta_13 = np.arcsin(0.00382)
theta_23 = np.arcsin(0.0408)
sin2_12 = np.sin(theta_12)**2
sin2_13 = np.sin(theta_13)**2
sin2_23 = np.sin(theta_23)**2

print(f"  θ₁₂ (Cabibbo) = {np.degrees(theta_12):.4f}°,  sin²θ₁₂ = {sin2_12:.6f}")
print(f"  θ₂₃           = {np.degrees(theta_23):.4f}°,  sin²θ₂₃ = {sin2_23:.6f}")
print(f"  θ₁₃           = {np.degrees(theta_13):.6f}°, sin²θ₁₃ = {sin2_13:.8f}")

# =====================================================================
# Section 3: Test CKM correction formulae for b²
# =====================================================================
print("\n=== Testing CKM correction formulae ===")
print(f"  δb²_up   = {delta_b2_up:.4f}")
print(f"  δb²_down = {delta_b2_down:.4f}")

# --- Method A: single-angle proportionality ---
# δb² = C × sin²θ_ij  →  find C from each sector, cross-check

C_up_12   = delta_b2_up   / sin2_12
C_up_23   = delta_b2_up   / sin2_23
C_down_12 = delta_b2_down / sin2_12
C_down_23 = delta_b2_down / sin2_23

print(f"\n  [A] δb² = C × sin²θ₁₂:")
print(f"      C from up   = {C_up_12:.4f}")
print(f"      C from down = {C_down_12:.4f}")
print(f"      ratio up/down = {C_up_12/C_down_12:.4f}")

print(f"\n  [B] δb² = C × sin²θ₂₃:")
print(f"      C from up   = {C_up_23:.4f}")
print(f"      C from down = {C_down_23:.4f}")
print(f"      ratio up/down = {C_up_23/C_down_23:.4f}")

# --- Method B: mixing sums ---
# δb² = C × (sin²θ₁₂ + sin²θ₂₃)
sum12_23 = sin2_12 + sin2_23
C_up_sum   = delta_b2_up   / sum12_23
C_down_sum = delta_b2_down / sum12_23
print(f"\n  [C] δb² = C × (sin²θ₁₂ + sin²θ₂₃) = C × {sum12_23:.6f}:")
print(f"      C from up   = {C_up_sum:.4f}")
print(f"      C from down = {C_down_sum:.4f}")
print(f"      ratio up/down = {C_up_sum/C_down_sum:.4f}")

# --- Method C: GTE structural constants ---
# In GTE: N_c = 3 (colors), N_gen = 3 (generations), c_H = 13
N_c   = 3
N_gen = 3
c_H   = 13

# δb²_down ~ N_c × sin²θ₁₂ ?
pred_down_Nc12 = N_c * sin2_12
print(f"\n  [D] N_c × sin²θ₁₂ = {pred_down_Nc12:.4f}  (target δb²_down = {delta_b2_down:.4f})")
print(f"      ratio = {pred_down_Nc12/delta_b2_down:.4f}")

# δb²_up ~ N_c × sin²θ₂₃ ?
pred_up_Nc23 = N_c * sin2_23
print(f"  [E] N_c × sin²θ₂₃  = {pred_up_Nc23:.4f}   (target δb²_up   = {delta_b2_up:.4f})")
print(f"      ratio = {pred_up_Nc23/delta_b2_up:.4f}")

# --- Wolfenstein parameter approach ---
# λ = |V_us| ≈ 0.2243 (Cabibbo / Wolfenstein λ)
lam = 0.2243
A_wolf = 0.0408 / lam**2  # |V_cb| = A λ²

# δb²_down ~ λ²  (leading Wolfenstein)
pred_down_lam2 = lam**2
# δb²_up ~ A²λ⁴  (leading Wolfenstein for up: V_cb/V_cs mix)
pred_up_A2lam4 = A_wolf**2 * lam**4

print(f"\n  [F] Wolfenstein λ = {lam:.4f},  A = {A_wolf:.4f}")
print(f"      λ²             = {pred_down_lam2:.6f}  (target δb²_down = {delta_b2_down:.4f})")
print(f"      ratio δb²_down/λ² = {delta_b2_down/pred_down_lam2:.4f}")
print(f"      A²λ⁴           = {pred_up_A2lam4:.8f}  (target δb²_up   = {delta_b2_up:.4f})")

# δb²_down ~ N_c × λ²
pred_down_Nc_lam2 = N_c * lam**2
print(f"\n  [G] N_c × λ²     = {pred_down_Nc_lam2:.6f}  (target δb²_down = {delta_b2_down:.4f})")
print(f"      ratio = {pred_down_Nc_lam2/delta_b2_down:.4f}")

# =====================================================================
# Section 4: Fit b using the cone parametrization
# =====================================================================
print("\n=== Fitting Koide cone parameters ===")

def fit_koide_cone(masses, n_tries=8):
    """
    Fit m_k = m₀(1 + b cos(θ + 2πk/3))²  for k=0,1,2.
    Returns best-fit (m0, b, theta).
    """
    m1, m2, m3 = sorted(masses)

    def objective(params):
        m0, b_raw, theta = params[0], params[1], params[2]
        b = abs(b_raw)
        pred = sorted([m0 * (1 + b * np.cos(theta + 2*np.pi*k/3))**2 for k in range(3)])
        return sum((np.log(p/m))**2 for p, m in zip(pred, [m1, m2, m3]))

    best = None
    for b0 in [1.0, np.sqrt(2), 1.8, 2.2]:
        for th0 in [2*np.pi/9, np.pi/4, np.pi/6, 0.1]:
            m0_init = (m1*m2*m3)**(1/3)
            try:
                res = minimize(objective, [m0_init, b0, th0], method='Nelder-Mead',
                               options={'maxiter': 100000, 'xatol': 1e-14, 'fatol': 1e-14})
                if best is None or res.fun < best.fun:
                    best = res
            except Exception:
                pass
    m0, b, theta = best.x[0], abs(best.x[1]), best.x[2]
    return m0, b, theta, best.fun

sectors = {
    "Leptons":    [0.511e-3, 105.658e-3, 1776.86e-3],
    "Up quarks":  [m_u, m_c, m_t],
    "Down quarks":[m_d, m_s, m_b],
}
cone_fits = {}
for label, masses in sectors.items():
    m0, b, theta, residual = fit_koide_cone(masses)
    Q = koide_Q(*masses)
    b2 = b**2
    print(f"  {label}: b={b:.6f}  b²={b2:.6f}  θ={theta:.6f} rad  residual={residual:.2e}")
    cone_fits[label] = {"Q": Q, "b": b, "b2": b2, "theta_rad": theta, "residual": residual}

# =====================================================================
# Section 5: Correlation analysis — does |V|² structure explain b²?
# =====================================================================
print("\n=== CKM-b² correlation tests ===")

# The key structural observation:
# For the DOWN sector: the dominant CKM mixing into the down sector is
#   driven by V_us = λ (Cabibbo angle, 1↔2 mixing)
#   The 2-3 mixing (V_cb) is subleading.
# For the UP sector: the CKM effects on the up sector arise because
#   V = V_uL† V_dL, so up mixes by V†, with dominant (1,2) = V_us
#   and dominant (2,3) = V_cb.

# Key test: does δb² track the "generational mixing power" in |V|?
# Generational mixing power for sector q:
#   sum over i≠j of |V_ij|^2 weighted by the sector contribution

# For down sector: the physical quark mass eigenstates couple to up
#   via rows of V (for d_R = d_L situation)
# Sum of squared off-diagonals per row:
row_off_sq = [
    V[0,1]**2 + V[0,2]**2,   # 1st generation mixes with 2nd, 3rd
    V[1,0]**2 + V[1,2]**2,   # 2nd
    V[2,0]**2 + V[2,1]**2,   # 3rd
]
col_off_sq = [
    V[1,0]**2 + V[2,0]**2,
    V[0,1]**2 + V[2,1]**2,
    V[0,2]**2 + V[1,2]**2,
]
print(f"  Off-diag row sums (down mixing via V rows): {[f'{x:.6f}' for x in row_off_sq]}")
print(f"  Off-diag col sums (up mixing via V† cols):  {[f'{x:.6f}' for x in col_off_sq]}")

mixing_down = sum(row_off_sq)
mixing_up   = sum(col_off_sq)
print(f"  Total mixing_down = {mixing_down:.6f}, mixing_up = {mixing_up:.6f}")
print(f"  Both equal S₃_breaking × N = {S3_breaking * 3:.6f}")

# The generation-averaged mixing strength:
mix_avg_down = mixing_down / 3.0
mix_avg_up   = mixing_up   / 3.0
print(f"\n  Per-generation mixing: down={mix_avg_down:.6f}, up={mix_avg_up:.6f}")

# Proportionality check: δb² = C × (per-generation mixing)
C_down_mix = delta_b2_down / mix_avg_down
C_up_mix   = delta_b2_up   / mix_avg_up
print(f"  C = δb²/mixing:  down: {C_down_mix:.4f},  up: {C_up_mix:.4f}")
print(f"  Ratio C_up/C_down = {C_up_mix/C_down_mix:.4f}")

# =====================================================================
# Section 6: The GTE formula hypothesis
# =====================================================================
print("\n=== GTE structural formula hypothesis ===")
# GTE interpretation:
# In the symmetric limit (S₃ unbroken): b² = 2, Q = 2/3 for all sectors.
# CKM breaks S₃ by inducing off-diagonal mixing of the Yukawa eigenstates.
# The leading mixing is the Cabibbo angle (1-2 sector).
#
# Simplest formula with GTE quantum numbers:
# b²_down = 2 + N_c × λ²  where λ = |V_us|, N_c = 3
# b²_up   = 2 + N_c × (λ² + A²λ⁴)  (up sees both Cabibbo and 2-3 mixing)
#
# Let's test precisely:

b2_down_pred_A = 2 + N_c * lam**2
b2_up_pred_A   = 2 + N_c * (lam**2 + A_wolf**2 * lam**4)

print(f"  Formula A: b²_down = 2 + N_c λ²")
print(f"    Predicted: {b2_down_pred_A:.4f}  Measured: {b2_down:.4f}  Error: {(b2_down_pred_A/b2_down-1)*100:+.2f}%")
print(f"  Formula A: b²_up = 2 + N_c(λ² + A²λ⁴)")
print(f"    Predicted: {b2_up_pred_A:.4f}   Measured: {b2_up:.4f}   Error: {(b2_up_pred_A/b2_up-1)*100:+.2f}%")

# Alternative: use sin²θ₁₂ not λ² (they differ slightly)
b2_down_pred_B = 2 + N_c * sin2_12
b2_up_pred_B   = 2 + N_c * (sin2_12 + sin2_23)

print(f"\n  Formula B: b²_down = 2 + N_c sin²θ₁₂")
print(f"    Predicted: {b2_down_pred_B:.4f}  Measured: {b2_down:.4f}  Error: {(b2_down_pred_B/b2_down-1)*100:+.2f}%")
print(f"  Formula B: b²_up = 2 + N_c (sin²θ₁₂ + sin²θ₂₃)")
print(f"    Predicted: {b2_up_pred_B:.4f}   Measured: {b2_up:.4f}   Error: {(b2_up_pred_B/b2_up-1)*100:+.2f}%")

# Try: b²_up = 2 + N_c × sin²θ₂₃ only (if dominant up mixing is 2-3)
b2_up_pred_C = 2 + N_c * sin2_23
print(f"\n  Formula C: b²_up = 2 + N_c sin²θ₂₃ (2-3 only)")
print(f"    Predicted: {b2_up_pred_C:.4f}   Measured: {b2_up:.4f}   Error: {(b2_up_pred_C/b2_up-1)*100:+.2f}%")

# Try: b²_up = 2 + N_c × (λ² + A²λ⁴) / (1 - A²λ⁴)  (Wolfenstein unitarity)
# Leading next correction: CKM row normalization
# Actually let's try: b²_down = 2 + N_c × (sin²θ₁₂ + sin²θ₁₃)
b2_down_pred_D = 2 + N_c * (sin2_12 + sin2_13)
print(f"\n  Formula D: b²_down = 2 + N_c (sin²θ₁₂ + sin²θ₁₃)")
print(f"    Predicted: {b2_down_pred_D:.4f}  Measured: {b2_down:.4f}  Error: {(b2_down_pred_D/b2_down-1)*100:+.2f}%")

# Full off-diagonal content
b2_down_pred_E = 2 + N_c * mixing_down / 3.0
b2_up_pred_E   = 2 + N_c * mixing_up   / 3.0
print(f"\n  Formula E: b²_down = 2 + N_c × (per-gen off-diag mixing, down)")
print(f"    Predicted: {b2_down_pred_E:.4f}  Measured: {b2_down:.4f}  Error: {(b2_down_pred_E/b2_down-1)*100:+.2f}%")
print(f"  Formula E: b²_up   = 2 + N_c × (per-gen off-diag mixing, up)")
print(f"    Predicted: {b2_up_pred_E:.4f}   Measured: {b2_up:.4f}   Error: {(b2_up_pred_E/b2_up-1)*100:+.2f}%")

# =====================================================================
# Section 7: Check key ratios
# =====================================================================
print("\n=== Ratio analysis ===")
ratio_delta = delta_b2_up / delta_b2_down
print(f"  δb²_up / δb²_down = {ratio_delta:.4f}")
print(f"  sin²θ₂₃ / sin²θ₁₂ = {sin2_23/sin2_12:.4f}")
print(f"  mixing_up / mixing_down = {mixing_up/mixing_down:.4f}")
print(f"  (λ²+A²λ⁴)/λ² = {1 + A_wolf**2 * lam**2:.4f}")

# =====================================================================
# Section 8: Summary and verdict
# =====================================================================
print("\n=== SUMMARY ===")
print(f"  b²_up   = {b2_up:.4f}   (S₃-symmetric value = 2.0000, δb² = {delta_b2_up:.4f})")
print(f"  b²_down = {b2_down:.4f}   (S₃-symmetric value = 2.0000, δb² = {delta_b2_down:.4f})")

# Best formula candidates
formulas_down = {
    "2 + N_c λ²": b2_down_pred_A,
    "2 + N_c sin²θ₁₂": b2_down_pred_B,
    "2 + N_c sin²θ₁₂ + N_c sin²θ₁₃": b2_down_pred_D,
    "2 + N_c × avg_offdiag_down": b2_down_pred_E,
}
formulas_up = {
    "2 + N_c(λ² + A²λ⁴)": b2_up_pred_A,
    "2 + N_c(sin²θ₁₂ + sin²θ₂₃)": b2_up_pred_B,
    "2 + N_c sin²θ₂₃": b2_up_pred_C,
    "2 + N_c × avg_offdiag_up": b2_up_pred_E,
}

print("\nDown-quark formula accuracy:")
for name, pred in formulas_down.items():
    err = (pred / b2_down - 1) * 100
    print(f"  {name:40s}: {pred:.4f}  err={err:+.2f}%")

print("\nUp-quark formula accuracy:")
for name, pred in formulas_up.items():
    err = (pred / b2_up - 1) * 100
    print(f"  {name:40s}: {pred:.4f}  err={err:+.2f}%")

# =====================================================================
# Save results
# =====================================================================
results = {
    "sector_Koide": {
        "leptons":    {"Q": Q_lep,  "b2": b2_lep,  "delta_b2": b2_lep  - 2},
        "up_quarks":  {"Q": Q_up,   "b2": b2_up,   "delta_b2": delta_b2_up},
        "down_quarks":{"Q": Q_down, "b2": b2_down, "delta_b2": delta_b2_down},
    },
    "CKM_angles": {
        "lambda_Wolfenstein": lam,
        "A_Wolfenstein": A_wolf,
        "theta_12_deg": float(np.degrees(theta_12)),
        "theta_23_deg": float(np.degrees(theta_23)),
        "theta_13_deg": float(np.degrees(theta_13)),
        "sin2_theta12": sin2_12,
        "sin2_theta23": sin2_23,
        "sin2_theta13": sin2_13,
    },
    "S3_breaking": {
        "off_diagonal_fraction": S3_breaking,
        "per_gen_mixing_down": mix_avg_down,
        "per_gen_mixing_up":   mix_avg_up,
    },
    "formula_tests": {
        "down_quark": {name: {"pred": v, "err_pct": (v/b2_down-1)*100}
                       for name, v in formulas_down.items()},
        "up_quark":   {name: {"pred": v, "err_pct": (v/b2_up-1)*100}
                       for name, v in formulas_up.items()},
    },
    "cone_fits": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in cone_fits.items()},
    "GTE_constants": {"N_c": N_c, "N_gen": N_gen, "c_H": c_H},
    "verdict": {
        "formula_found": bool(
            abs(b2_down_pred_A / b2_down - 1) < 0.05 or
            abs(b2_down_pred_B / b2_down - 1) < 0.05
        ),
        "best_error_down_pct": float((b2_down_pred_A / b2_down - 1) * 100),
        "best_error_up_pct": float((b2_up_pred_A / b2_up - 1) * 100),
        "best_formula_down": "2 + N_c × λ²  or  2 + N_c × sin²θ₁₂  (error ~10%)",
        "best_formula_up": "2 + N_c × (λ² + A²λ⁴)  (error ~30% — no simple CKM formula)",
        "closure_status": "OPEN CatB — CKM contributes directionally but no single-angle formula closes within 5%; deviations 10-30% indicate additional Yukawa structure beyond CKM alone",
        "delta_b2_ratio": float(delta_b2_up / delta_b2_down),
        "note": "Up-quark b² deviation is ~2.8x the down-quark deviation; this ratio has no simple CKM angle explanation (sin²θ₂₃/sin²θ₁₂ = 0.033, not 2.8). CKM alone is insufficient.",
    },
}

out_path = os.path.join(os.path.dirname(__file__), "quark_koide_ckm_analysis_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {out_path}")
