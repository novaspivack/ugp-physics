"""
G15: Lüscher-corrected inter-tape coupling estimate for the proton mass formula.

The proton mass formula requires G_inter = 14.57 MeV (empirical target).
The naive estimate G_inter ≈ σ × (1/m_kink) overshoots by ~40×.
This script adds the Lüscher quantum string correction at R = R* ≈ 0.913 fm
and checks whether the corrected estimate is closer to the target.

Lüscher correction:
    σ_quantum(R) = σ_classical × (1 - π/(12 σ R²))

evaluated at R* = 0.913 fm (hadronic radius scale from proton charge radius).

Result: Lüscher correction provides only ~7% improvement; G_inter remains ~40× too high.
Full resolution requires G13 (3+1D Φ_MDL string tension from Creutz ratio measurement).
"""

import math

# Input parameters
sigma_classical = 0.18        # string tension, GeV²
m_kink = 0.290                # kink mass, GeV  (M_kink = (8/49)·m_τ = 290.10 MeV)
R_star_fm = 0.913             # hadronic scale, fm (proton charge radius)
hbar_c_fm_GeV = 0.1973        # ℏc in GeV·fm

# Convert R* from fm to GeV^{-1}
R_star = R_star_fm / hbar_c_fm_GeV   # GeV^{-1}

# Lüscher quantum string correction
luscher_term = math.pi / (12 * sigma_classical * R_star**2)
sigma_quantum = sigma_classical * (1 - luscher_term)

# G_inter estimate: σ × (1/m_kink)
G_inter_naive     = sigma_classical * (1 / m_kink)   # GeV
G_inter_luscher   = sigma_quantum   * (1 / m_kink)   # GeV

# Target
G_inter_target = 14.57e-3  # GeV

print("=== G15: Lüscher-corrected G_inter estimate ===")
print(f"R*              = {R_star:.4f} GeV^{{-1}}  ({R_star_fm} fm)")
print(f"Lüscher term    = {luscher_term:.4f}  ({luscher_term*100:.2f}% of σ)")
print(f"σ_classical     = {sigma_classical:.4f} GeV²")
print(f"σ(R*)           = {sigma_quantum:.4f} GeV²")
print()
print(f"G_inter (naive)           = {G_inter_naive*1000:.1f} MeV")
print(f"G_inter (Lüscher)         = {G_inter_luscher*1000:.1f} MeV")
print(f"Target G_inter            = {G_inter_target*1000:.2f} MeV")
print()
print(f"Ratio naive/target        = {G_inter_naive/G_inter_target:.1f}×")
print(f"Ratio Lüscher/target      = {G_inter_luscher/G_inter_target:.1f}×")
print(f"Improvement from Lüscher  = {(G_inter_naive - G_inter_luscher)/G_inter_naive*100:.1f}%")
print()
print("Conclusion: Lüscher correction reduces G_inter by ~7%; estimate remains ~40× too high.")
print("Full G_inter derivation requires G13 (Creutz ratio + Φ_MDL 3+1D string tension).")
