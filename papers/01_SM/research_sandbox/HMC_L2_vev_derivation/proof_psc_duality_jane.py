"""
Round P1 — Jane (Math): Jacobian Formula for PSC Entropy Under Contractions

The standard result from measure theory / ergodic theory:
If T is a smooth contracting map and μ is a measure, then for a state ρ with
PSC entropy S(ρ) = -log₂(μ(Ω_ρ)):

    S(T(ρ)) = -log₂(μ(T(Ω_ρ))) = -log₂(|det J_T| × μ(Ω_ρ)) = S(ρ) - log₂(|det J_T|)

For a contraction with |det J_T| = λ < 1:
    S(T(ρ)) = S(ρ) + log₂(1/λ)

For the SRRG with λ = 1/φ (contraction eigenvalue at η*):
    ΔS = log₂(1/(1/φ)) = log₂(φ)

This is pure algebra. The Lean proof reduces to Real.log_mul + ring.
"""
import numpy as np

phi = (1 + 5**0.5) / 2
ln2 = np.log(2)

print("=" * 60)
print("JANE — ROUND P1: Jacobian Formula Verification")
print("=" * 60)

# Core identity: -log₂(λε) = -log₂(ε) + log₂(1/λ)
epsilon = 1.0  # arbitrary positive ε
lambda_SRRG = 1 / phi  # SRRG contraction eigenvalue at η*

S_before = -np.log2(epsilon)
S_after_raw = -np.log2(lambda_SRRG * epsilon)
delta_S_raw = S_after_raw - S_before

log2_inv_lambda = np.log2(1 / lambda_SRRG)
log2_phi = np.log2(phi)

print(f"\nSRRG contraction eigenvalue: λ = 1/φ = {lambda_SRRG:.10f}")
print(f"  Computed ΔS = S(T(ρ)) - S(ρ) = {delta_S_raw:.10f}")
print(f"  Predicted ΔS = log₂(1/λ) = log₂(φ) = {log2_phi:.10f}")
print(f"  Match: {np.isclose(delta_S_raw, log2_phi)}")

print(f"\n  Algebraic identity check: -log₂(λε) = -log₂(ε) + log₂(1/λ)")
lhs = -np.log2(lambda_SRRG * epsilon)
rhs = -np.log2(epsilon) + np.log2(1 / lambda_SRRG)
print(f"  LHS = {lhs:.10f}")
print(f"  RHS = {rhs:.10f}")
print(f"  Identity holds: {np.isclose(lhs, rhs)}")

print(f"\n  Key: this is just Real.log_mul + Real.log_inv in Lean.")
print(f"  Lean path: log(λε) = log(λ) + log(ε), log(1/λ) = -log(λ) → ring closes.")

# Dimensionality check: what if the S³ fiber has k contracting directions?
print(f"\n--- S³ Dimensionality Analysis ---")
print(f"  The S³ Goldstone fiber has dimension 3.")
print(f"  SRRG contracts only in the η-direction (1 effective dimension).")
print(f"  The other 2 directions on S³ are the Goldstone angular modes,")
print(f"  which are NOT contracted by SRRG (they are protected by Goldstone's theorem).")
for k in [1, 2, 3]:
    dS = k * log2_phi
    dS_per_gen = dS / 3
    print(f"  k={k}: ΔS_total = {dS:.6f}, ΔS_per_gen = {dS_per_gen:.6f}")

print(f"\n  CONCLUSION: k=1 is the correct dimensional factor.")
print(f"  ΔS = log₂(φ) = {log2_phi:.8f} bits total")
print(f"  ΔS_per_gen = log₂(φ)/3 = {log2_phi/3:.8f} bits per generation")

# Mathlib Jacobian theorem connection
print(f"\n--- Mathlib Connection ---")
print(f"  The Lean proof uses:")
print(f"  1. psc_entropy_uniform (ε) = -(Real.log ε / Real.log 2)")
print(f"  2. Real.log_mul (ne_of_gt hλ) (ne_of_gt hε)")
print(f"  3. Real.log_inv : log(λ⁻¹) = -log(λ)")
print(f"  4. ring : closes the algebraic identity")
print(f"")
print(f"  NO Jacobian theorem from Mathlib needed — the entropy formula")
print(f"  itself encodes the Jacobian via the -log₂(measure) definition.")
print(f"  This is the Bayesian information-gain formulation.")

# Verify that psc_entropy_contraction_duality (ΔS > 0) holds for all λ ∈ (0,1)
print(f"\n--- psc_entropy_contraction_duality: ΔS > 0 for λ ∈ (0,1) ---")
lambdas = [0.1, 0.5, 1/phi, 0.9, 0.99]
for lam in lambdas:
    dS = np.log2(1 / lam)
    print(f"  λ = {lam:.6f}, ΔS = log₂(1/λ) = {dS:.6f} > 0: {dS > 0}")
print(f"  Lean: Real.logb_pos (by norm_num : 1 < 2) (one_lt_div hlam_pos |>.mpr hlam_lt1)")
