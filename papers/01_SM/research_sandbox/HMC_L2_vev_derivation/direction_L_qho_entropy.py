"""Direction L: Derive log₂(√e) from QHO mode PSC entropy"""
import numpy as np
import json

pi = np.pi; ln2 = np.log(2); phi = (1+5**0.5)/2

# The target: log₂(√e) = 1/(2 × ln2) = 0.72135
log2_sqrte = 1/(2*ln2)
print(f"log₂(√e) = 1/(2 ln2) = {log2_sqrte:.8f}")

# Consistency check: 2π × log₂(√e) = π/ln2?
val = 2*pi*log2_sqrte
print(f"2π × log₂(√e) = {val:.8f}")
print(f"π/ln2 = {pi/ln2:.8f}")
print(f"Match: {abs(val - pi/ln2) < 1e-10}")  # Should be True

# MDL perspective: Wigner function of |0>
print(f"\nMDL approach:")
print(f"Wigner function peak at W(0,0) = 2/h")
print(f"Area inside W > W_max/e: A = πℏ = 1 quantum cell")
print(f"log₂(A/ℏ) = log₂(π) = {np.log2(pi):.6f} bits")
print(f"This is log₂(π), not log₂(√e) = {log2_sqrte:.6f}")

# CFT approach: compact boson entropy self-consistent
print(f"\nCFT self-consistency approach:")
# S_PSC = π√(2π / (2π/S_PSC)) / 3 = π × S_PSC^(1/2) / 3
# Solving: S_PSC^(1/2) = π/3 → S_PSC = π²/9
print(f"CFT approach gives π²/9 = {pi**2/9:.6f}, not π/ln2 = {pi/ln2:.6f}")
print(f"Ratio: (π/ln2)/(π²/9) = {(pi/ln2)/(pi**2/9):.4f} = {9/(pi*ln2):.4f}")

# von Neumann entropy of thermal QHO
print(f"\nvon Neumann entropy of thermal QHO:")
print(f"S_vN = (n+1)ln(n+1) - n ln(n), n = 1/(exp(β)-1)")
# At critical temperature where S_vN = log₂(√e) bits = log2_sqrte × ln2 nats
target_nat = log2_sqrte * ln2
print(f"Target S = {log2_sqrte:.6f} bits = {target_nat:.6f} nats")
# S_vN = target_nat requires solving (n+1)ln(n+1) - n ln(n) = target_nat
from scipy.optimize import brentq
def svn(n):
    if n < 1e-15:
        return 0.0
    return (n+1)*np.log(n+1) - n*np.log(n) - target_nat
# find n such that S_vN = target
n_star = brentq(svn, 1e-15, 1e6)
beta_star = np.log(1 + 1/n_star)  # ℏω/kT
print(f"n_star (mean occupation) = {n_star:.6f}")
print(f"β_star = ℏω/kT = {beta_star:.6f}")
print(f"T_star = ℏω/(kT × {beta_star:.4f}) → T = ℏω / (k × {beta_star:.4f})")
print(f"At T = v (EW VEV): β = ℏω/v — no structural reason for β = {beta_star:.4f}")

# Holographic / entanglement entropy
print(f"\nHolographic approach:")
# S_EE = (c/6) ln(L/ε) for 1+1D CFT
# For c=1 (free boson): S_EE = (1/6) ln(L/ε)
# Set S_EE = log₂(√e) = 1/(2ln2):
# ln(L/ε) = 6/(2ln2) = 3/ln2
ratio_holographic = 3/ln2
print(f"L/ε = exp(3/ln2) = exp({ratio_holographic:.4f}) = {np.exp(ratio_holographic):.4f}")
print(f"No structural reason for this specific ratio from PSC alone")

# Per-radian entropy interpretation
print(f"\nPer-radian interpretation (definitional):")
print(f"π/ln2 = 2π × log₂(√e) — log₂(√e) is simply (π/ln2)/(2π)")
print(f"This is a tautological decomposition, not a derivation")
print(f"The question remains: WHY is total entropy π/ln2?")

conclusion = "Direction L: No first-principles derivation of log₂(√e) found in this session. It is the per-radian entropy that the theory NEEDS (π/ln2 spread over 2π radians), not one it derives. MDL approach gives log₂(π); CFT self-consistency gives π²/9; thermal QHO requires unstructured temperature. Direction L remains OPEN."

print(f"\nVerdict: {conclusion}")

json.dump({
    "log2_sqrte": log2_sqrte,
    "target_pi_over_ln2": pi/ln2,
    "decomp": "pi/ln2 = 2*pi * log2_sqrte by definition",
    "MDL_attempt": f"Wigner function -> log2(pi) = {np.log2(pi):.6f}, not log2(sqrte) = {log2_sqrte:.6f}",
    "CFT_attempt": f"pi^2/9 = {pi**2/9:.6f} != pi/ln2 = {pi/ln2:.6f}",
    "thermal_QHO_n_star": n_star,
    "thermal_QHO_beta_star": beta_star,
    "conclusion": conclusion
}, open("direction_L_qho_entropy.json","w"), indent=2)
