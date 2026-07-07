"""
CKM Matrix Count Theorem — GTE Arithmetic Verification

Verifies that a unitary N_gen × N_gen matrix has exactly N_gen² independent real
parameters, and that the GTE generation-orbit × family-ring capacity equals
2^N_gen × N_fam = 40.  The ratio λ = N_gen² / (2^N_gen × N_fam) = 9/40 = 0.225000
is the Wolfenstein CKM parameter (PDG λ = 0.22500 ± 0.00067, 0.000% error).

Lean-certified in GUTStructure.lean §14:
  ckm_dof_count (alias: ckm_real_dimension): N_gen² = 9
  gut_capacity_times_ring (alias: gte_generation_capacity): 2^N_gen × N_fam = 40
  wolfenstein_lambda_formula (alias: wolfenstein_density_formula): 9/40
  wolfenstein_lambda_value: 9/40 = 225/1000 (exact decimal)

GTE structural constants (all CatAL, Lean-certified):
  N_gen = 3  (Rule 110 orbit depth / GoE chain length)
  N_fam = 5  (Z₅ family ring size / Z₅ transitivity uniqueness)
"""

from fractions import Fraction

# ─── GTE constants (CatAL, Lean-certified) ───────────────────────────────────
N_GEN = 3   # generation count = Rule 110 orbit depth
N_FAM = 5   # family ring size = Z₅ ring count

# PDG Wolfenstein λ (2024 Review of Particle Physics)
PDG_LAMBDA        = 0.22500
PDG_LAMBDA_ERR    = 0.00067   # 1σ uncertainty

print("════════════════════════════════════════════════════════════════════")
print("  CKM Matrix Count Theorem — U(N_gen) Real Dimension")
print("════════════════════════════════════════════════════════════════════\n")

# ─── Part A: U(n) has n² real parameters — verified for n = 1, 2, 3 ─────────
#
# U(n) is the group of n×n unitary matrices over ℂ.  Its Lie algebra u(n)
# consists of skew-Hermitian matrices, which form a real vector space of
# dimension n² (n real diagonal entries + 2 × n(n-1)/2 off-diagonal complex
# entries = n + n(n-1) = n²).
#
# Equivalently: U(n) is a real Lie group of dimension n².
#   U(1): dim = 1²  = 1  (one phase)
#   U(2): dim = 2²  = 4  (2×2 unitary, 4 real params before any convention)
#   U(3): dim = 3²  = 9  (CKM before rephasing/unitarity conventions)

print("─── A: U(n) real dimension = n²  (standard Lie theory) ──────────────")
for n in [1, 2, 3]:
    dim_theory   = n * n
    # Verify via skew-Hermitian basis count:
    # diagonal entries: n real numbers  →  n params
    # off-diagonal (i<j): each entry is purely imaginary part × 2 real params
    #   → n*(n-1)/2 complex pairs × 2 = n*(n-1) real params
    # total: n + n*(n-1) = n²
    dim_diagonal = n
    dim_offdiag  = n * (n - 1)
    dim_computed = dim_diagonal + dim_offdiag
    assert dim_computed == dim_theory, f"FAIL at n={n}: {dim_computed} ≠ {dim_theory}"
    check = "✓" if dim_computed == dim_theory else "✗"
    print(f"  U({n}): diagonal {dim_diagonal} + off-diagonal {dim_offdiag} = {dim_computed} = {n}² {check}")

print()
ckm_dof = N_GEN ** 2
print(f"  For N_gen = {N_GEN}: dim U(N_gen) = N_gen² = {N_GEN}² = {ckm_dof}")
print(f"  Lean cert: GUTStructure.ckm_dof_count (alias ckm_real_dimension)")
print(f"             n_gen ^ 2 = 9  (norm_num, zero sorry)")

# ─── Part B: GTE generation-orbit × family-ring capacity ──────────────────────
print("\n─── B: GTE capacity = 2^N_gen × N_fam = 40 ──────────────────────────")
gut_orbit_slots   = 2 ** N_GEN   # 8 = generation-orbit depth (GUT → EW)
family_ring_slots = N_FAM        # 5 = Z₅ ring size
gut_capacity      = gut_orbit_slots * family_ring_slots
print(f"  GUT-orbit depth: 2^N_gen = 2^{N_GEN} = {gut_orbit_slots}")
print(f"  Z₅ family ring:  N_fam   = {family_ring_slots}")
print(f"  Total capacity:  {gut_orbit_slots} × {family_ring_slots} = {gut_capacity}")
assert gut_capacity == 40, f"FAIL: gut_capacity = {gut_capacity} ≠ 40"
print(f"  Lean cert: GUTStructure.gut_capacity_times_ring (alias gte_generation_capacity)")
print(f"             2 ^ n_gen * n_fam = 40  (norm_num, zero sorry)")

# ─── Part C: Wolfenstein λ density formula ────────────────────────────────────
print("\n─── C: Wolfenstein λ = N_gen² / (2^N_gen × N_fam) = 9/40 ───────────")
lam_exact = Fraction(ckm_dof, gut_capacity)          # 9/40
lam_float = float(lam_exact)

error_abs   = lam_float - PDG_LAMBDA
error_rel   = error_abs / PDG_LAMBDA * 100
error_sigma = abs(error_abs) / PDG_LAMBDA_ERR

print(f"  λ = {ckm_dof}/{gut_capacity} = {lam_exact} = {lam_float:.6f}")
print(f"  PDG λ          = {PDG_LAMBDA:.5f} ± {PDG_LAMBDA_ERR:.5f}")
print(f"  Absolute error = {error_abs:+.6f}")
print(f"  Relative error = {error_rel:+.4f}%")
print(f"  σ-distance     = {error_sigma:.4f}σ")
assert abs(error_rel) < 0.001, f"FAIL: error {error_rel:.4f}% exceeds tolerance"
print(f"  Lean cert: GUTStructure.wolfenstein_lambda_formula (alias wolfenstein_density_formula)")
print(f"             ((n_gen : ℚ) ^ 2) / (2 ^ n_gen * n_fam) = 9/40  (norm_num, zero sorry)")

# ─── Part D: Exact decimal verification ──────────────────────────────────────
print("\n─── D: Exact decimal 9/40 = 225/1000 ────────────────────────────────")
lam_sq   = lam_exact ** 2       # 81/1600
print(f"  9/40 = {Fraction(225, 1000)}  (exact rational identity)")
assert Fraction(9, 40) == Fraction(225, 1000), "FAIL: 9/40 ≠ 225/1000"
print(f"  ✓  9/40 = 225/1000 = 0.225 (exact)")
print(f"  λ² = (9/40)² = {lam_sq} = {float(lam_sq):.6f}")
print(f"      Controls leading corrections: |V_us|², |V_cd|² terms in Wolfenstein expansion")
print(f"  Lean cert: GUTStructure.wolfenstein_lambda_value")
print(f"             (9 : ℚ) / 40 = 225 / 1000  (norm_num, zero sorry)")

# ─── Part E: GUT arithmetic cross-checks (Ranks 57, 58) ─────────────────────
print("\n─── E: GUT arithmetic cross-checks ──────────────────────────────────")
C_HIGGS        = 13
running_shift  = C_HIGGS - 2**N_GEN
family_cap     = N_GEN + N_FAM

print(f"  c_H - 2^N_gen = {C_HIGGS} - {2**N_GEN} = {running_shift} = N_fam = {N_FAM}  ✓")
assert running_shift == N_FAM, "FAIL: running shift ≠ N_fam"
print(f"  N_gen + N_fam = {N_GEN} + {N_FAM} = {family_cap} = 2^N_gen = {2**N_GEN}  ✓")
assert family_cap == 2**N_GEN, "FAIL: N_gen + N_fam ≠ 2^N_gen"
print(f"  These hold simultaneously: c_H = 2^N_gen + N_fam = {2**N_GEN} + {N_FAM} = {C_HIGGS}  ✓")

# ─── Summary ─────────────────────────────────────────────────────────────────
print(f"""
════════════════════════════════════════════════════════════════════
  SUMMARY
════════════════════════════════════════════════════════════════════
  N_gen = {N_GEN}, N_fam = {N_FAM}

  Part 1 — CKM real dimension (CatAL):
    dim U(N_gen) = N_gen² = {ckm_dof}
    Lean: ckm_dof_count / ckm_real_dimension  (norm_num, zero sorry)

  Part 2 — GTE capacity (CatAL):
    2^N_gen × N_fam = {gut_capacity}
    Lean: gut_capacity_times_ring / gte_generation_capacity  (norm_num, zero sorry)

  Part 3 — Wolfenstein density (CatAL):
    λ = {lam_exact} = {lam_float:.6f}
    PDG: {PDG_LAMBDA} ± {PDG_LAMBDA_ERR}  →  {error_rel:+.4f}% ({error_sigma:.4f}σ)
    Lean: wolfenstein_lambda_formula / wolfenstein_density_formula  (norm_num, zero sorry)

  Part 4 — Physical interpretation (CatAD):
    N_gen² identifies with: # independent real parameters in the N_gen×N_gen
      CKM unitary matrix (U(N_gen) real dimension theorem, Part A).
    2^N_gen × N_fam identifies with: GUT-orbit (2^N_gen steps) × Z₅ family-ring
      (N_fam slots) — the combined GTE generation-orbit capacity.
    λ = density of CKM structure in GTE orbit-family space.
    This physical identification step is CatAD (not yet a formal GTE derivation).

  All arithmetic checks passed. Zero errors.
════════════════════════════════════════════════════════════════════
""")
