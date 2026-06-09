"""
EPIC_049_SCD — Weinberg angle from Haar measure entropy assessment.

Computes all simple ratios of Haar measure entropies for U(1), SU(2), SU(3) and
checks whether any matches sin²θ_W = 0.23122 ± 0.00003 (PDG 2022).

Result: No simple Haar entropy ratio recovers the experimental value.
        Best candidate: H_U1/(H_SU2+H_SU3) ≈ 0.212 (deviation 8.2%).
        Grade: [D→C] — hypothesis tested and falsified at this level.

See P27 §8.4 for the write-up.
"""

import numpy as np

# Haar measure volumes (standard group theory results)
# U(1) ≅ S^1: Vol = 2π (normalized Lebesgue measure)
# SU(2) ≅ S^3: Vol = 2π² (standard S^3 surface area)
# SU(3): Vol = 3π⁴ (from SU(3) Haar measure calculation)
vol_u1  = 2 * np.pi
vol_su2 = 2 * np.pi**2
vol_su3 = 3 * np.pi**4

H_u1  = np.log(vol_u1)
H_su2 = np.log(vol_su2)
H_su3 = np.log(vol_su3)

PDG_sin2_thetaW = 0.23129  # PDG 2024 (was 0.23122 = PDG 2022)
PDG_uncertainty = 0.00004  # PDG 2024 uncertainty

print("=" * 65)
print("Haar measure entropy assessment for Weinberg angle")
print("=" * 65)
print()
print(f"H_Haar(U(1))  = ln(2π)   = {H_u1:.8f}")
print(f"H_Haar(SU(2)) = ln(2π²)  = {H_su2:.8f}")
print(f"H_Haar(SU(3)) = ln(3π⁴)  = {H_su3:.8f}")
print()
print(f"Experimental: sin²θ_W = {PDG_sin2_thetaW} ± {PDG_uncertainty} (PDG 2022)")
print()
print("-" * 65)
print("Candidate expressions:")
print("-" * 65)

candidates = {
    "H_U1 / (H_U1 + H_SU2)  [= ln(2π)/ln(4π³)]":
        H_u1 / (H_u1 + H_su2),
    "H_U1 / H_SU2":
        H_u1 / H_su2,
    "H_U1 / H_SU3":
        H_u1 / H_su3,
    "H_SU2 / H_SU3":
        H_su2 / H_su3,
    "1 / (1 + H_SU2/H_U1 + H_SU3/H_U1)":
        1 / (1 + H_su2/H_u1 + H_su3/H_u1),
    "H_U1 / (H_SU2 + H_SU3)":
        H_u1 / (H_su2 + H_su3),
    "H_U1² / (H_U1² + H_SU2²)":
        H_u1**2 / (H_u1**2 + H_su2**2),
}

best_name, best_val, best_dev = None, None, float('inf')
for name, val in candidates.items():
    dev = abs(val - PDG_sin2_thetaW)
    pct = dev / PDG_sin2_thetaW * 100
    marker = " ← best" if dev < best_dev else ""
    print(f"  {name}")
    print(f"    = {val:.6f}  (Δ = {dev:.5f}, {pct:.1f}%){marker}")
    if dev < best_dev:
        best_dev = dev
        best_name = name
        best_val = val

print()
print("-" * 65)
print("Summary")
print("-" * 65)
print(f"Best candidate : {best_name}")
print(f"               = {best_val:.6f}")
print(f"Experimental   = {PDG_sin2_thetaW}")
print(f"Deviation      = {best_dev:.5f}  ({best_dev/PDG_sin2_thetaW*100:.1f}%)")
print()
print("Conclusion: No simple ratio of Haar measure entropies of U(1), SU(2),")
print("and SU(3) reproduces sin²θ_W = 0.23122 to within 8%. The hypothesis")
print("that sin²θ_W = H_U1 / (H_U1 + H_SU2) (naive entropy-weighted coupling")
print("ratio) deviates by ~65%. The structural mechanism connecting the SRRG")
print("coupling ratio to Haar entropies requires additional machinery beyond")
print("simple entropy ratios — likely the one-loop SRRG β-function.")
print()
print("Grade: [D→C] — structural hypothesis identified and numerically tested.")
