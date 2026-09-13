#!/usr/bin/env python3
"""
GTE leptogenesis K-factor and baryon asymmetry analysis.

Derives the washout K-factor and baryon-asymmetry feasibility from GTE
first-principles parameters: g_fund = 49/512 (CatAD), M_R = 1.11×10¹³ GeV
(CatA), and the GTE neutrino mass prediction m_nu1 = 0.679 meV (CatA).

Key findings:
  - Y_nu1 = sqrt(m_nu1 × M_R) / v_ew = 1.577×10⁻² (GTE seesaw, CatA)
  - K1 = Y_nu1² × M_Pl / (1.66 × sqrt(g*) × M_R) = 15.93 (strong washout)
  - κ (NNR fit) ≈ 1.02×10⁻² from K1 = 15.93
  - ε₁_DI ≤ 5.40×10⁻⁴ (Davidson-Ibarra bound, GTE M_R + m_nu3)
  - Leptogenesis feasible: ε₁_needed = 1.80×10⁻⁵ < ε₁_DI
  - Gap: actual ε₁ requires full Y_ν texture (off-diagonal FN structure)

Graduated: 2026-05-30 (EPIC_080, rank 080-CKM-LEPTOGEN)
"""

import numpy as np
import json

# ---------------------------------------------------------------------------
# GTE parameters (CatAD / CatA)
# ---------------------------------------------------------------------------
g_fund = 49 / 512          # Z₇⁴ dark ring Majorana coupling (CatAD)
M_R    = 1.11e13           # GeV — Pati-Salam GUT scale, CatA (G28)
v_H    = 246.16            # GeV — Higgs VEV (CatAD)
v_ew   = v_H / np.sqrt(2)  # 174.06 GeV — Lagrangian VEV convention
M_Pl   = 1.22e19           # GeV — reduced Planck mass
g_star = 106.75            # effective relativistic DOF at T ~ M_R

# Sphaleron conversion factor (B+L violation → B asymmetry)
sphaleron = 28.0 / 79.0

# ---------------------------------------------------------------------------
# GTE neutrino masses — G28 CatA prediction
# ---------------------------------------------------------------------------
m_nu1_GeV = 0.6786490908714047e-3 * 1e-9   # 0.679 meV in GeV
Delta_m21_sq = 7.42e-5  * 1e-18            # GeV² (PDG 2024)
Delta_m31_sq = 2.51e-3  * 1e-18            # GeV²

m_nu2 = np.sqrt(m_nu1_GeV**2 + Delta_m21_sq)
m_nu3 = np.sqrt(m_nu1_GeV**2 + Delta_m31_sq)
sum_m_nu_meV = (m_nu1_GeV + m_nu2 + m_nu3) * 1e12

# ---------------------------------------------------------------------------
# Dirac Yukawa coupling from seesaw (lightest RHN, N₁)
#   m_nu1 = Y_nu1² v_ew² / M_R   →   Y_nu1 = sqrt(m_nu1 M_R) / v_ew
# ---------------------------------------------------------------------------
Y_nu1_sq = m_nu1_GeV * M_R / v_ew**2
Y_nu1    = np.sqrt(Y_nu1_sq)

# ---------------------------------------------------------------------------
# K-factor (Kolb-Roulet-Wolfram decay parameter)
#   K1 = Γ(N₁→ℓH) / H|_{T=M₁}
#      = Y_nu1² M_Pl / (1.66 sqrt(g*) M_R)
# ---------------------------------------------------------------------------
K1 = Y_nu1_sq * M_Pl / (1.66 * np.sqrt(g_star) * M_R)

# ---------------------------------------------------------------------------
# Washout efficiency κ from strong-washout fits (K >> 1)
# NNR: Nardi, Nilles, Roulet (2006)  κ ≈ 0.3 / (K (ln K)^0.6)
# BPY: Buchmuller, Plumacher, Yanagida (2002)  κ ≈ 2 / (K^1.16 (ln K)^0.16)
# ---------------------------------------------------------------------------
kappa_NNR = 0.3  / (K1 * (np.log(K1)**0.6))
kappa_BPY = 2.0  / (K1**1.16 * (np.log(K1))**0.16)

# ---------------------------------------------------------------------------
# Davidson-Ibarra upper bound on CP asymmetry ε₁
# (using v = v_H = 246 GeV convention, consistent with DI 2002)
#   |ε₁| ≤ 3/(16π) × M_R × (m_nu3 − m_nu1) / v_H²
# ---------------------------------------------------------------------------
epsilon_DI = 3.0 / (16.0 * np.pi) * M_R * (m_nu3 - m_nu1_GeV) / v_H**2

# ---------------------------------------------------------------------------
# Baryon asymmetry if ε₁ = ε₁_DI_max
#   η_B = (28/79) × ε₁ × κ / g*
# ---------------------------------------------------------------------------
eta_B_NNR = sphaleron * kappa_NNR * epsilon_DI / g_star
eta_B_BPY = sphaleron * kappa_BPY * epsilon_DI / g_star

# ---------------------------------------------------------------------------
# Required ε₁ for η_B_obs = 6.1×10⁻¹⁰ with GTE-derived κ
# ---------------------------------------------------------------------------
eta_B_obs = 6.1e-10
eps_needed_NNR = eta_B_obs * g_star / (sphaleron * kappa_NNR)
eps_needed_BPY = eta_B_obs * g_star / (sphaleron * kappa_BPY)

# ---------------------------------------------------------------------------
# Froggatt-Nielsen texture estimate for off-diagonal suppression
# FN charges (q₁, q₂) = (3, 2)  →  λ_FN ≈ g_fund² ≈ 0.0092
# Y_12 ~ λ_FN^|q₁−q₂| = g_fund²   (Δq = 1)
# ---------------------------------------------------------------------------
lambda_FN = g_fund**2    # FN expansion parameter
Y_12      = lambda_FN    # leading off-diagonal Yukawa element
eps_FN_estimate = epsilon_DI * (Y_12 / Y_nu1)**2

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------
print("=== GTE LEPTOGENESIS: K-FACTOR AND FEASIBILITY ===\n")

print("--- GTE neutrino masses (G28 CatA) ---")
print(f"m_nu1 = {m_nu1_GeV*1e12:.4f} meV  (GTE prediction)")
print(f"m_nu2 = {m_nu2*1e12:.4f} meV")
print(f"m_nu3 = {m_nu3*1e12:.4f} meV")
print(f"Σm_ν  = {sum_m_nu_meV:.2f} meV  (G28: 59.4 meV)")

print(f"\n--- Yukawa coupling from GTE seesaw ---")
print(f"Y_nu1² = m_nu1 M_R / v_ew² = {Y_nu1_sq:.4e}")
print(f"Y_nu1  = {Y_nu1:.4e}  (CatA, from GTE m_nu1 and M_R)")

print(f"\n--- K-factor (Task 1 result) ---")
print(f"K1 = Y_nu1² M_Pl / (1.66 √g* M_R) = {K1:.6f}")
print(f"Strong washout (K >> 1):  {'YES' if K1 > 1 else 'NO'}")

print(f"\n--- Washout efficiency from K1 = {K1:.4f} ---")
print(f"κ (NNR 2006 fit)  = {kappa_NNR:.4e}")
print(f"κ (BPY 2002 fit)  = {kappa_BPY:.4e}")

print(f"\n--- Davidson-Ibarra CP asymmetry bound ---")
print(f"ε₁_DI = {epsilon_DI:.4e}  (v = v_H = 246 GeV convention)")

print(f"\n--- η_B if ε₁ = ε₁_DI_max ---")
print(f"η_B (NNR) = {eta_B_NNR:.4e}  [overproduction ×{eta_B_NNR/eta_B_obs:.1f}]")
print(f"η_B (BPY) = {eta_B_BPY:.4e}  [overproduction ×{eta_B_BPY/eta_B_obs:.1f}]")
print(f"η_B_obs   = 6.1×10⁻¹⁰")

print(f"\n--- Required ε₁ for η_B = 6.1×10⁻¹⁰ ---")
print(f"ε₁_needed (NNR κ) = {eps_needed_NNR:.4e}  (= {eps_needed_NNR/epsilon_DI:.3e} × ε₁_DI)  ✓ feasible")
print(f"ε₁_needed (BPY κ) = {eps_needed_BPY:.4e}  (= {eps_needed_BPY/epsilon_DI:.3e} × ε₁_DI)  ✓ feasible")

print(f"\n--- FN texture estimate for ε₁_actual ---")
print(f"λ_FN = g_fund² = {lambda_FN:.4e}")
print(f"Y_12 ~ λ_FN^Δq = {Y_12:.4e}  (Δq = 1)")
print(f"ε₁_FN_estimate = {eps_FN_estimate:.4e}  (vs ε₁_needed = {eps_needed_NNR:.4e})")
print(f"Ratio ε₁_FN / ε₁_needed = {eps_FN_estimate/eps_needed_NNR:.2f}")

print(f"\n=== FINAL ASSESSMENT ===")
print(f"K1 = {K1:.4f}  ← GTE-DERIVED from m_nu1 (CatA) + M_R (CatA)")
print(f"κ ≈ {kappa_NNR:.3e}  ← DERIVED from K1 (NNR fit, strong washout)")
print(f"ε₁_DI = {epsilon_DI:.3e}  ← UPPER BOUND (GTE-derived, CatA)")
print(f"ε₁_needed = {eps_needed_NNR:.3e}  ← WELL BELOW ε₁_DI  → FEASIBLE ✓")
print(f"Gap: ε₁_actual requires full Y_ν texture; FN estimate within factor ~10×")
print(f"Status: 080-CKM-LEPTOGEN upgraded — K1 derived, κ derived; ε₁ texture OPEN")

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------
results = {
    "description": "GTE leptogenesis K-factor and baryon asymmetry feasibility",
    "epic": "EPIC_080",
    "rank": "080-CKM-LEPTOGEN",
    "date": "2026-05-30",
    "gte_inputs": {
        "g_fund": g_fund,
        "g_fund_exact": "49/512 = 7^2/2^9",
        "M_R_GeV": M_R,
        "v_H_GeV": v_H,
        "m_nu1_meV": float(m_nu1_GeV * 1e12),
        "cat_level": "CatAD/CatA (G28)"
    },
    "k_factor": {
        "Y_nu1": float(Y_nu1),
        "Y_nu1_sq": float(Y_nu1_sq),
        "K1": float(K1),
        "strong_washout": bool(K1 > 1)
    },
    "washout": {
        "kappa_NNR": float(kappa_NNR),
        "kappa_BPY": float(kappa_BPY)
    },
    "cp_asymmetry": {
        "epsilon_DI_max": float(epsilon_DI),
        "epsilon_needed_NNR": float(eps_needed_NNR),
        "epsilon_needed_BPY": float(eps_needed_BPY),
        "feasible": bool(float(eps_needed_NNR) < float(epsilon_DI))
    },
    "baryon_asymmetry": {
        "eta_B_if_DI_max_NNR": float(eta_B_NNR),
        "eta_B_if_DI_max_BPY": float(eta_B_BPY),
        "eta_B_obs": 6.1e-10,
        "overproduction_NNR": float(eta_B_NNR / 6.1e-10),
        "overproduction_BPY": float(eta_B_BPY / 6.1e-10)
    },
    "fn_texture": {
        "lambda_FN": float(lambda_FN),
        "Y_12_estimate": float(Y_12),
        "eps1_FN_estimate": float(eps_FN_estimate),
        "ratio_to_needed": float(eps_FN_estimate / eps_needed_NNR)
    },
    "conclusion": (
        "K1 = 15.93 (GTE-derived). Strong washout confirmed. "
        "κ ≈ 0.010 (NNR fit). ε₁_needed = 1.8e-5 < ε₁_DI = 5.4e-4. "
        "Channel FEASIBLE. Open: full Y_ν texture for ε₁_actual derivation."
    )
}

output_path = "papers/21_neutrino_masses/scripts/gte_leptogenesis_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    pass
