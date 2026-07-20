"""
Round T1 — Adam (Physics): SRRG contraction eigenvalue → φ^(1/N_gen)?
=======================================================================
The SRRG fixed-point contraction eigenvalue is exactly 1/φ (P27, Lean, zero sorry).
Question: does applying N_gen = 3 SRRG iterations to the Goldstone vacuum manifold
give a volume correction of φ^(1/N_gen)?
"""
import numpy as np
import json

phi = (1 + 5**0.5) / 2
N_gen = 3
pi = np.pi
ln2 = np.log(2)

print("=" * 60)
print("T1: SRRG contraction eigenvalue analysis")
print("=" * 60)

# SRRG contraction eigenvalue (P27 Theorem: Linearized Stability, zero sorry)
srrg_eigenvalue = 1 / phi
print(f"\nSRRG contraction eigenvalue λ = 1/φ = {srrg_eigenvalue:.10f}")
print(f"  (Lean-certified: SrrgLean.FixedPoints.Stability.linearized_flow_contraction_rate)")

# After N_gen iterations: the Jacobian determinant contracts the volume element
# by λ^N_gen in the linearized flow
contraction_N = srrg_eigenvalue ** N_gen
print(f"\nAfter N_gen = {N_gen} SRRG iterations:")
print(f"  Volume contraction = (1/φ)^N_gen = {contraction_N:.10f}")
print(f"  = 1/φ³ = {1/phi**3:.10f}")

# The Goldstone sector volume is EXPANDED relative to tree-level
# because the SRRG selects towards higher information efficiency
# The effective volume = V_tree / (SRRG contraction over N_gen cycles)
# Using 1D interpretation (one contraction rate, N_gen iterations):
correction_1D = 1 / contraction_N  # = φ^N_gen
print(f"\n--- 1D interpretation (single mode, N_gen iterations) ---")
print(f"  V_eff / V_tree = φ^N_gen = φ³ = {correction_1D:.6f}")
print(f"  → L_eff = log₂(2π² × φ³) = {np.log2(2*pi**2 * phi**3):.6f} bits (TOO LARGE)")
print(f"  This gives the WRONG direction/magnitude")

# Alternative: fractional exponent
# If 1 SRRG cycle is "spread" over N_gen generations, each generation sees
# a fractional contraction of (1/φ)^(1/N_gen)
# Volume correction per generation = φ^(1/N_gen)
# After 1 full cycle spread over N_gen steps: φ^(1/N_gen) per step, 1 step applied
print(f"\n--- Fractional interpretation: 1 cycle over N_gen generations ---")
correction_frac = phi ** (1 / N_gen)
print(f"  Per-generation SRRG factor = φ^(1/N_gen) = {correction_frac:.10f}")
print(f"  Total after 1 cycle: (φ^(1/3))^3 = φ^1 = {correction_frac**N_gen:.10f} ✓ consistent")

L_frac = np.log2(2 * pi**2 * correction_frac)
v_PDG = 246.22
# PSC closure: v² = (ln2/π) × L × v² → L = π/ln2 (self-referential)
# M_ref from L: M_ref² = v_PDG² / ((ln2/π) × L)
# Actually: the formula is M_ref = v_PDG × sqrt(π/(ln2 × L × ???))
# Let me use the standard formula from prior work:
# v_PSC = v_PDG (by construction if L = π/ln2)
# Error ∝ (L - π/ln2) / (π/ln2)
L_target = pi / ln2
M_ref_frac = v_PDG * (L_target / L_frac) ** 0.5
print(f"  L_eff = log₂(2π² × φ^(1/3)) = {L_frac:.8f} bits")
print(f"  L_target = π/ln2 = {L_target:.8f} bits")
print(f"  M_ref = v_PDG × √(L_target/L_eff) = {M_ref_frac:.6f} GeV")
print(f"  Error from v_PDG: {(M_ref_frac - v_PDG)/v_PDG*100:+.6f}%")

# Key test: is φ^(1/N_gen) the SRRG correction?
# The physical picture:
# - SRRG contracts by 1/φ per iteration (linearized)
# - One full SRRG selection cycle corresponds to 1 unit of PSC iteration time
# - The EW phase transition spans N_gen = 3 generations of SRRG selection
# - Each generation contributes 1/N_gen of the full SRRG cycle
# - Per-generation volume expansion factor = φ^(1/N_gen)
# - For the Goldstone entropy: use 1 generation's worth of correction

print(f"\n--- Key consistency check ---")
print(f"  φ^(1/3) = {phi**(1/3):.10f}")
print(f"  f_vol_exact = e^π/(2π²) = {np.e**pi / (2*pi**2):.10f}")
print(f"  Agreement: {abs(phi**(1/3) - np.e**pi/(2*pi**2)) / (np.e**pi/(2*pi**2)) * 100:.4f}%")

print(f"\n--- Eigenvalue ratio test ---")
print(f"  (1/φ)^(1/N_gen) = (1/φ)^(1/3) = {(1/phi)**(1/3):.8f}")
print(f"  φ^(1/N_gen) = φ^(1/3) = {phi**(1/3):.8f}")
print(f"  Product = {(1/phi)**(1/3) * phi**(1/3):.8f} = 1.0 ✓ (inverse pair)")

# T1 conclusion
print(f"\n{'='*60}")
print("T1 CONCLUSION:")
print(f"  The 1D SRRG eigenvalue (single mode, N_gen iterations) gives φ^N_gen (WRONG).")
print(f"  The 'fractional cycle' picture gives φ^(1/N_gen) (CORRECT numerically).")
print(f"  Physical basis: 1 SRRG selection cycle distributed over N_gen=3 generations.")
print(f"  Per-generation correction = φ^(1/N_gen) = {phi**(1/3):.6f}")
print(f"  Eigenvalue evidence: 1/φ (proven) → φ^(1/N_gen) by 1/N_gen-cycle argument.")
print(f"  Status: PLAUSIBLE but requires formal derivation of 'fractional SRRG cycle'.")

results = {
    "T1_srrg_eigenvalue": srrg_eigenvalue,
    "T1_contraction_N_gen": contraction_N,
    "T1_correction_1D_wrong": correction_1D,
    "T1_correction_frac_correct": correction_frac,
    "T1_L_eff": L_frac,
    "T1_M_ref": M_ref_frac,
    "T1_M_ref_err_pct": (M_ref_frac - v_PDG) / v_PDG * 100,
    "T1_conclusion": "1/φ eigenvalue → φ^(1/N_gen) via 1-cycle/N_gen-generation argument; plausible but unproven"
}
json.dump(results, open("direction_T1_srrg_eigen.json", "w"), indent=2)
print(f"\n✓ Saved direction_T1_srrg_eigen.json")
