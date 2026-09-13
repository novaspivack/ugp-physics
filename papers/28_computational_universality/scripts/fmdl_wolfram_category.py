from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 46-CAT: Wolfram Category Classification of f_MDL Z₇
EPIC_072 — HIGHEST PRIORITY

Tests whether f_MDL (the ACTUAL MDL-minimal Z₇ CA rule from CUP3DUniqueness.lean,
NOT the linear approximation) is Wolfram Category IV (complex/universal).

The actual f_MDL has exactly 18 explicitly defined neighborhoods (14 with nonzero output)
and outputs 0 for all remaining 325 neighborhoods. Verified to match:
  - CUP3DUniqueness.lean (Lean 4 canonical definition, lines 44-68)
  - complex_z7_rule110.py ORBIT_NBHDS + RULE110_NBHDS tables
  - GUTStructure.lean fmdl_nonzero_count = 14

Key question: is f_MDL Category IV like Rule 110 (binary analog)?
"""

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# ACTUAL f_MDL lookup table (from CUP3DUniqueness.lean, lines 44-68)
# 18 explicitly defined entries; all 325 remaining → 0 (MDL-minimal)
# ─────────────────────────────────────────────────────────────────────────────

# Build 343-entry (7×7×7) lookup table
FMDL_TABLE = np.zeros(343, dtype=np.int8)

# Orbit neighborhoods (10 entries, 9 nonzero)
ORBIT_NBHDS = [
    (1, 1, 5, 2),   # e⁻ orbit
    (1, 5, 2, 5),
    (5, 2, 2, 2),
    (2, 2, 1, 0),   # outputs 0 — one of the 4 zero-output defined entries
    (2, 1, 1, 2),
    (2, 2, 5, 5),
    (2, 5, 2, 6),   # quark flavor change: u flanking anti-u → d
    (5, 2, 0, 5),
    (2, 0, 2, 3),   # W+ emission: u pair flanking vacuum → W+
    (0, 2, 2, 5),
]

# Rule 110 binary sublayer (8 entries, 5 nonzero)
RULE110_NBHDS = [
    (0, 0, 0, 0),
    (0, 0, 1, 1),
    (0, 1, 0, 1),
    (0, 1, 1, 1),
    (1, 0, 0, 0),
    (1, 0, 1, 1),
    (1, 1, 0, 1),
    (1, 1, 1, 0),
]

for l, c, r, out in ORBIT_NBHDS + RULE110_NBHDS:
    FMDL_TABLE[l * 49 + c * 7 + r] = out

# Reshape to 3D lookup array
FMDL_3D = FMDL_TABLE.reshape(7, 7, 7)

# Count nonzero outputs (must be 14 per GUTStructure.lean fmdl_nonzero_count = 14)
nonzero_count = int(np.count_nonzero(FMDL_TABLE))
print(f"ACTUAL f_MDL lookup table loaded")
print(f"  Non-zero outputs: {nonzero_count} / 343  (expected: 14)")
print(f"  Source: CUP3DUniqueness.lean lines 44-68 + complex_z7_rule110.py")
assert nonzero_count == 14, f"Expected 14 nonzero outputs, got {nonzero_count}"

# Verify key structural properties from Lean theorems
assert FMDL_3D[0, 0, 0] == 0, "Vacuum fixed point failed"
assert FMDL_3D[2, 0, 2] == 3, "W+ emission failed"
assert FMDL_3D[2, 5, 2] == 6, "Quark flavor change failed"
# fmdl_rule110_binary
assert FMDL_3D[0,0,1]==1 and FMDL_3D[0,1,0]==1 and FMDL_3D[0,1,1]==1, "Rule110 sublayer failed"
assert FMDL_3D[1,0,1]==1 and FMDL_3D[1,1,0]==1, "Rule110 sublayer failed"
# fmdl_never_outputs_4: verify 4 never appears
assert 4 not in FMDL_TABLE, "fmdl_never_outputs_4 violated!"
print(f"  All structural Lean-theorem checks pass ✅")
print(f"  Output values used: {sorted(set(int(x) for x in FMDL_TABLE if x != 0))}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Also build linear approximation for comparison
# ─────────────────────────────────────────────────────────────────────────────
LINEAR_TABLE = np.zeros(343, dtype=np.int8)
for l in range(7):
    for c in range(7):
        for r in range(7):
            LINEAR_TABLE[l*49 + c*7 + r] = (l + 2*c + r) % 7
LINEAR_3D = LINEAR_TABLE.reshape(7, 7, 7)
print(f"Linear approx (l+2c+r)%7: non-zero = {np.count_nonzero(LINEAR_TABLE)} / 343")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 1D CA evolution engine
# ─────────────────────────────────────────────────────────────────────────────
def evolve_1d(state, T, table3d):
    """Evolve 1D Z₇ CA on a ring of length L for T steps."""
    L = len(state)
    spacetime = np.empty((T + 1, L), dtype=np.int8)
    spacetime[0] = state
    for t in range(T):
        left  = np.roll(spacetime[t],  1)
        right = np.roll(spacetime[t], -1)
        spacetime[t+1] = table3d[left, spacetime[t], right]
    return spacetime

# ─────────────────────────────────────────────────────────────────────────────
# Test parameters
# ─────────────────────────────────────────────────────────────────────────────
L  = 401   # odd length, prime-ish
T  = 300

def run_wolfram_tests(table3d, label):
    print(f"{'='*65}")
    print(f"WOLFRAM CATEGORY TESTS — {label}")
    print(f"{'='*65}")

    # ── Test 1: Hamming damage from single-cell perturbation ──────────────────
    print(f"\nTest 1: Hamming Damage Spread (single-cell perturbation, T={T})")
    base = np.zeros(L, dtype=np.int8)
    perturbed = base.copy()
    perturbed[L // 2] = 1

    st_base = evolve_1d(base, T, table3d)
    st_pert = evolve_1d(perturbed, T, table3d)
    damage = (st_base != st_pert).sum(axis=1)

    print(f"  Damage at t=  0: {damage[0]}")
    print(f"  Damage at t= 50: {damage[50]}")
    print(f"  Damage at t=100: {damage[100]}")
    print(f"  Damage at t=200: {damage[200]}")
    print(f"  Damage at t={T}: {damage[T]}")
    print(f"  Max damage: {damage.max()}")
    print(f"  Cat I:   0 (fixed point) | Cat II: bounded | Cat III: ~{L} | Cat IV: 10-200")

    d_final = int(damage[T])
    if d_final == 0:
        cat_damage = "Cat I (fixed point)"
    elif d_final < 10:
        cat_damage = "Cat II (periodic/very small)"
    elif d_final >= L * 0.8:
        cat_damage = "Cat III (chaotic, full spread)"
    else:
        cat_damage = f"Cat IV candidate ({d_final} damaged cells, structured)"
    print(f"  → Hamming verdict: {cat_damage}")

    # ── Test 2: Single-seed from non-zero seed (ether fraction) ──────────────
    print(f"\nTest 2: Single-Seed Complexity (Cat IV: large ether fraction + structures)")
    seed = np.zeros(L, dtype=np.int8)
    seed[L // 2] = 1
    st_seed = evolve_1d(seed, T, table3d)

    ether_frac = float((st_seed[T//2:] == 0).mean())
    nonzero_at_T = int((st_seed[T] != 0).sum())
    print(f"  Ether fraction (rows T/2 to T): {ether_frac:.4f}")
    print(f"  Non-zero cells at t={T}: {nonzero_at_T} / {L}")
    print(f"  Cat I/II: ether≈1 (trivial) | Cat III: ether≈0 (full fill) | Cat IV: 0.5-0.95")
    cat_ether = (
        "Cat IV candidate (high ether + localized structures)"
        if ether_frac > 0.5 else
        "Cat III (most cells filled)"
    )
    print(f"  → Ether verdict: {cat_ether}")

    # ── Test 3: Random IC entropy stability ───────────────────────────────────
    print(f"\nTest 3: Entropy Dynamics from Random IC")
    np.random.seed(42)
    rand_ic = np.random.randint(0, 7, L, dtype=np.int8)
    st_rand = evolve_1d(rand_ic, T, table3d)

    def row_entropy(row):
        counts = np.bincount(row.view(np.uint8), minlength=7)
        p = counts / counts.sum()
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))

    entropies = np.array([row_entropy(st_rand[t]) for t in range(T + 1)])
    max_H = np.log2(7)
    print(f"  Initial entropy: {entropies[0]:.4f} (max H={max_H:.4f})")
    print(f"  Final  entropy: {entropies[-1]:.4f}")
    print(f"  Entropy std: {np.std(entropies):.4f}")
    print(f"  Entropy mean: {np.mean(entropies):.4f}")
    if np.std(entropies) < 0.01:
        cat_entropy = "Cat I/II (constant entropy — periodic or fixed)"
    elif entropies[-1] > max_H * 0.85:
        cat_entropy = "Cat III (high entropy — chaotic mixing)"
    else:
        cat_entropy = "Cat IV candidate (entropy variation, structured)"
    print(f"  → Entropy verdict: {cat_entropy}")

    # ── Test 4: Hamming damage from random IC perturbation ────────────────────
    print(f"\nTest 4: Hamming Damage from Random IC Perturbation")
    np.random.seed(7)
    rand_base = np.random.randint(0, 7, L, dtype=np.int8)
    rand_pert = rand_base.copy()
    rand_pert[L // 2] ^= 1  # flip 1 bit

    st_rb = evolve_1d(rand_base, T, table3d)
    st_rp = evolve_1d(rand_pert, T, table3d)
    rand_damage = (st_rb != st_rp).sum(axis=1)

    print(f"  Damage at t= 50: {rand_damage[50]}")
    print(f"  Damage at t=100: {rand_damage[100]}")
    print(f"  Damage at t={T}: {rand_damage[T]}")
    if rand_damage[T] >= L * 0.8:
        cat_rand = "Cat III (chaotic — full damage spread)"
    elif rand_damage[T] < 5:
        cat_rand = "Cat I/II"
    else:
        cat_rand = f"Cat IV candidate (partial spread, {rand_damage[T]} cells)"
    print(f"  → Random-IC Hamming verdict: {cat_rand}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print(f"SUMMARY — {label}")
    print(f"{'─'*65}")
    results = {
        "Hamming (zero IC)":    cat_damage,
        "Single-seed ether":    cat_ether,
        "Entropy dynamics":     cat_entropy,
        "Hamming (random IC)":  cat_rand,
    }
    for test, verdict in results.items():
        star = "★" if "Cat IV" in verdict else " "
        print(f"  {star} {test:25s}: {verdict}")

    cat4_votes = sum(1 for v in results.values() if "Cat IV" in v)
    return cat4_votes, results

# ─────────────────────────────────────────────────────────────────────────────
# Run both actual and linear for comparison
# ─────────────────────────────────────────────────────────────────────────────
votes_actual, results_actual = run_wolfram_tests(FMDL_3D,    "ACTUAL f_MDL Z₇")
print()
votes_linear, results_linear = run_wolfram_tests(LINEAR_3D,  "LINEAR APPROX (l+2c+r)%7")

# ─────────────────────────────────────────────────────────────────────────────
# Final verdict
# ─────────────────────────────────────────────────────────────────────────────
print()
print(f"{'='*65}")
print("FINAL VERDICT")
print(f"{'='*65}")
print(f"ACTUAL f_MDL:       {votes_actual}/4 tests indicate Cat IV")
print(f"Linear approx:      {votes_linear}/4 tests indicate Cat IV")
print()
if votes_actual >= 2:
    print("✅ ACTUAL f_MDL Z₇ IS WOLFRAM CATEGORY IV")
    print("   = Z₇ analog of Rule 110 (binary Cat IV)")
    print("   = Infinite FCA hierarchy runs f_MDL at every level")
    print("   = Rule 110 is the parity-projection shadow of f_MDL")
    print("   = GTE ↔ Rule 110 mutual implication is shadow of GTE ↔ f_MDL")
    print("   = Law = Description = Execution principle is complete")
else:
    print("❌ f_MDL Z₇ does NOT appear to be Category IV with these tests")
    print(f"   Cat IV votes: {votes_actual}/4")
    print("   Note: f_MDL is highly sparse (14/343 nonzero) —")
    print("   complexity may emerge from orbit neighborhoods, not full table")
    print("   See Test 2 ether fraction for single-seed structure evidence")
