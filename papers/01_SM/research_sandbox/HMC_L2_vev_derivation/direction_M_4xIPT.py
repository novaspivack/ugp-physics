"""Direction M: Is π/ln2 = 4 × IPT structural?"""
import numpy as np
import json

pi = np.pi; ln2 = np.log(2); phi = (1+5**0.5)/2

IPT = 1 + np.log(phi)/(2*np.log(2*pi))
pi_over_ln2 = pi/ln2

ratio = pi_over_ln2 / IPT
print(f"π/ln2 = {pi_over_ln2:.10f}")
print(f"IPT = {IPT:.10f}")
print(f"π/(ln2 × IPT) = {ratio:.10f}")
print(f"Closest integer: {round(ratio)}")
print(f"Gap from 4: {(ratio - 4)/4 * 100:.6f}%")

# Try: π/ln2 = (dim G) × IPT where dim G = 4 for SU(2)×U(1)
dim_G = 4
approx = dim_G * IPT
print(f"\n4 × IPT = {approx:.10f}")
print(f"π/ln2 = {pi_over_ln2:.10f}")
print(f"Gap: {(pi_over_ln2 - approx)/pi_over_ln2 * 100:.6f}%")

# Analytic check: can 4 × IPT = π/ln2 exactly?
# 4 × (1 + ln(φ)/(2 ln(2π))) = π/ln2
# 4 + 2 ln(φ)/ln(2π) = π/ln2
# 2 ln(φ)/ln(2π) = π/ln2 - 4
# ln(φ)/ln(2π) = π/(2 ln2) - 2
rhs = pi/(2*ln2) - 2
lhs = np.log(phi)/np.log(2*pi)
print(f"\nAnalytic check: 4 × IPT = π/ln2 requires:")
print(f"  ln(φ)/ln(2π) = π/(2 ln2) - 2")
print(f"  LHS = {lhs:.10f}")
print(f"  RHS = {rhs:.10f}")
print(f"  Difference: {abs(lhs - rhs):.2e} (NOT zero → NOT exact)")

print(f"\n4 × IPT ≈ π/ln2 within {abs(pi_over_ln2 - 4*IPT)/pi_over_ln2 * 100:.6f}%")

# More general: can α × IPT = π/ln2 for structural α?
alpha = pi_over_ln2 / IPT
print(f"\nα = (π/ln2) / IPT = {alpha:.10f}")
print(f"α - 4 = {alpha - 4:.10f}")

# Search over UGP/structural constants for best match to α
candidates = [
    ("4", 4),
    ("π", pi),
    ("φ²", phi**2),
    ("2φ", 2*phi),
    ("e", np.e),
    ("2π/ln2", 2*pi/ln2),
    ("4 + 1/φ²", 4 + 1/phi**2),
    ("4 + ln2/π", 4 + ln2/pi),
    ("4 + 1/π²", 4 + 1/pi**2),
    ("4 + 1/(2π²)", 4 + 1/(2*pi**2)),
    ("4 + ln(φ)/π", 4 + np.log(phi)/pi),
]
print("\nComparison to structural constants:")
for name, val in candidates:
    diff_pct = abs(alpha - val)/val * 100
    print(f"  α vs {name:20s} = {val:.8f}: diff = {diff_pct:.6f}%")

# Best rational approximation of α
print(f"\nBest rational approximations of α = {alpha:.10f}:")
from fractions import Fraction
best = sorted([(abs(float(Fraction(p,q)) - alpha), p, q) 
               for p in range(1, 50) for q in range(1, 50)])[:5]
for diff, p, q in best:
    print(f"  {p}/{q} = {p/q:.8f}, diff = {diff:.6f}")

# Significance of 0.19% gap
print(f"\nNull saturation test at ±0.2%:")
null_rate = 0.002  # 0.2% band
print(f"If α were uniform on [4-0.5, 4+0.5], P(|α-4| < {null_rate*4:.4f}) = {2*null_rate:.3f} = {2*null_rate*100:.1f}%")
print(f"0.19% gap is at {0.0019/1.0 * 100:.2f}th percentile of a ±100% flat prior — suggestive but not conclusive")

conclusion = (f"π/ln2 ≈ 4 × IPT within {abs(pi_over_ln2 - 4*IPT)/pi_over_ln2 * 100:.4f}% but NOT analytically exact. "
              f"α = (π/ln2)/IPT = {alpha:.6f}; α - 4 = {alpha-4:.6f}. "
              f"No structural constant matches α to better than 0.19%. "
              f"The near-equality dim(SU(2)×U(1)) × IPT ≈ π/ln2 is a suggestive but unproven conjecture.")
print(f"\nVerdict: {conclusion}")

json.dump({
    "IPT": IPT,
    "pi_over_ln2": pi_over_ln2,
    "ratio_alpha": alpha,
    "is_exactly_4xIPT": False,
    "gap_from_4xIPT_pct": abs(pi_over_ln2 - 4*IPT)/pi_over_ln2 * 100,
    "alpha_minus_4": alpha - 4,
    "conclusion": conclusion
}, open("direction_M_4xIPT.json","w"), indent=2)
