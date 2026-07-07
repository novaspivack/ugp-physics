#!/usr/bin/env python3
"""
f_MDL Chirality Eigenstates and 3D Parity Violation

Tests whether f_MDL (Rule 110 extended to Z₇) and f_MDL,3D violate parity
symmetry P, and whether chirality eigenstates can be identified.

Key question: Is f_MDL P-symmetric? That is, does f_MDL(l,c,r) = f_MDL(r,c,l)
for all (l,c,r) ∈ Z₇³?  Since Rule 110 ≠ Rule 124 (its left-right mirror rule),
P-violation is expected.  This script quantifies the P-violation, identifies
the P-violating triples, and checks whether the SM orbit itself is chiral
(i.e., P(gen₁) does not follow the same orbit as gen₁ under f_MDL).

Physical meaning: If the CA rule is P-asymmetric, configurations can be
intrinsically left-handed or right-handed — a CA-level analog of chirality.

Parts:
  A1. 1D P-violation test: count (l,c,r) triples where f_MDL(l,c,r) ≠ f_MDL(r,c,l)
  A2. SM orbit chirality: orbit of gen₁ vs orbit of P(gen₁) under f_MDL
  A3. Binary P-violation: Rule 110 vs Rule 124 minterm comparison
  A4. 3D parity test: f_MDL,3D(P(grid)) vs P(f_MDL,3D(grid)) on small lattice
  A5. Chiral eigenstate search: which 5-ring configurations have |f_MDL^t(c) - P(f_MDL^t(P(c)))| = 0?
"""

import numpy as np
import json
import time
from typing import List, Tuple, Dict

t0 = time.time()
results: Dict = {}

print("=" * 70)
print("f_MDL Chirality and 3D Parity Violation Analysis")
print("=" * 70)
print()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Build the exact f_MDL Z₇ 1D table (same as Round 33 / Spec 10)
# ─────────────────────────────────────────────────────────────────────────────

FMDL_1D = np.zeros(343, dtype=np.int8)

ORBIT_NBHDS = [
    (1,1,5,2), (1,5,2,5), (5,2,2,2), (2,2,1,0), (2,1,1,2),
    (2,2,5,5), (2,5,2,6), (5,2,0,5), (2,0,2,3), (0,2,2,5),
]
for l, c, r, out in ORBIT_NBHDS:
    FMDL_1D[l*49 + c*7 + r] = out

RULE110_NBHDS = [
    (0,0,0,0), (0,0,1,1), (0,1,0,1), (0,1,1,1),
    (1,0,0,0), (1,0,1,1), (1,1,0,1), (1,1,1,0),
]
for l, c, r, out in RULE110_NBHDS:
    FMDL_1D[l*49 + c*7 + r] = out

# Reference SM orbit vectors (on a Z₅ ring)
gen1 = np.array([1,5,2,2,1], dtype=np.int8)
gen2 = np.array([2,5,2,0,2], dtype=np.int8)
gen3 = np.array([5,6,5,3,5], dtype=np.int8)
vac  = np.zeros(5, dtype=np.int8)

def apply_fmdl_1d(row: np.ndarray) -> np.ndarray:
    """Apply f_MDL_1D to a 1D ring (periodic boundary)."""
    L = len(row)
    l = np.roll(row, 1).astype(np.int64)
    c = row.astype(np.int64)
    r = np.roll(row, -1).astype(np.int64)
    return FMDL_1D[l*49 + c*7 + r]

assert np.array_equal(apply_fmdl_1d(gen1), gen2), "gen1→gen2 FAIL"
assert np.array_equal(apply_fmdl_1d(gen2), gen3), "gen2→gen3 FAIL"
assert np.array_equal(apply_fmdl_1d(gen3), vac), "gen3→vac FAIL"

print("f_MDL verified: gen₁→gen₂→gen₃→vacuum ✅")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Part A1: 1D Parity Violation Test
# f_MDL is P-symmetric iff f_MDL(l,c,r) = f_MDL(r,c,l) ∀ (l,c,r)
# ─────────────────────────────────────────────────────────────────────────────

print("-" * 60)
print("Part A1: 1D Parity Violation Test")
print("-" * 60)

p_violating = []
p_symmetric = []

for l in range(7):
    for c in range(7):
        for r in range(7):
            fwd = int(FMDL_1D[l*49 + c*7 + r])
            rev = int(FMDL_1D[r*49 + c*7 + l])   # P-reflected: swap l and r
            if fwd != rev:
                p_violating.append((l, c, r, fwd, rev))
            else:
                p_symmetric.append((l, c, r, fwd))

n_total = 343
n_violating = len(p_violating)
n_symmetric = len(p_symmetric)

print(f"Total (l,c,r) triples: {n_total}")
print(f"P-violating triples [f(l,c,r) ≠ f(r,c,l)]: {n_violating} ({100*n_violating/n_total:.1f}%)")
print(f"P-symmetric triples [f(l,c,r) = f(r,c,l)]: {n_symmetric} ({100*n_symmetric/n_total:.1f}%)")
print()

# Show the P-violating triples sorted by (l,c,r)
p_violating_sorted = sorted(p_violating)
print(f"P-violating triples (l, c, r, f(l,c,r), f(r,c,l)):")
for triple in p_violating_sorted[:20]:
    l, c, r, fwd, rev = triple
    print(f"  ({l},{c},{r}): f(l,c,r)={fwd}  f(r,c,l)={rev}")
if len(p_violating_sorted) > 20:
    print(f"  ... ({len(p_violating_sorted)-20} more)")
print()

# Check: which output values are involved in P-violation?
from collections import Counter
fwd_vals = Counter(fwd for _,_,_,fwd,_ in p_violating)
rev_vals = Counter(rev for _,_,_,_,rev in p_violating)
print(f"P-violating triples: forward output distribution: {dict(sorted(fwd_vals.items()))}")
print(f"P-violating triples: reverse output distribution: {dict(sorted(rev_vals.items()))}")
print()

results['a1_p_violation'] = {
    'n_total': n_total,
    'n_violating': n_violating,
    'n_symmetric': n_symmetric,
    'fraction_violating': n_violating / n_total,
    'p_violating_triples': [(l,c,r,fwd,rev) for l,c,r,fwd,rev in p_violating_sorted],
}

# ─────────────────────────────────────────────────────────────────────────────
# Part A2: SM Orbit Chirality
# Compare orbit of gen₁ vs orbit of P(gen₁) under f_MDL
# ─────────────────────────────────────────────────────────────────────────────

print("-" * 60)
print("Part A2: SM Orbit Chirality")
print("-" * 60)

def p_transform_1d(v: np.ndarray) -> np.ndarray:
    """Parity transform: reverse the array (left-right flip)."""
    return v[::-1].copy()

p_gen1 = p_transform_1d(gen1)
p_gen2 = p_transform_1d(gen2)
p_gen3 = p_transform_1d(gen3)

print(f"gen₁ =   {list(gen1)}")
print(f"P(gen₁) = {list(p_gen1)}")
print(f"gen₂ =   {list(gen2)}")
print(f"P(gen₂) = {list(p_gen2)}")
print(f"gen₃ =   {list(gen3)}")
print(f"P(gen₃) = {list(p_gen3)}")
print()

# Check: P-invariance of the orbit vectors
for name, v, pv in [('gen₁', gen1, p_gen1), ('gen₂', gen2, p_gen2), ('gen₃', gen3, p_gen3)]:
    sym = "P-symmetric" if np.array_equal(v, pv) else "P-asymmetric (CHIRAL)"
    print(f"  {name}: {sym}")
print()

# Orbit of P(gen₁) under f_MDL
orbit_p_gen1 = [p_gen1.copy()]
state = p_gen1.copy()
for t in range(6):
    state = apply_fmdl_1d(state)
    orbit_p_gen1.append(state.copy())

print("Orbit of P(gen₁) under f_MDL:")
for t, s in enumerate(orbit_p_gen1):
    label = ""
    if np.array_equal(s, p_gen2):
        label = " = P(gen₂)"
    elif np.array_equal(s, p_gen3):
        label = " = P(gen₃)"
    elif np.array_equal(s, gen1):
        label = " = gen₁ (!)"
    elif np.array_equal(s, gen2):
        label = " = gen₂ (!)"
    elif np.array_equal(s, gen3):
        label = " = gen₃ (!)"
    elif np.array_equal(s, vac):
        label = " = vacuum"
    print(f"  t={t}: {list(s)}{label}")
print()

# Key check: does P(gen₁) → P(gen₂) → P(gen₃) → vacuum?
# That would mean P maps the orbit to itself (P-covariant orbit)
f_p_gen1 = apply_fmdl_1d(p_gen1)
p_covariant_step1 = np.array_equal(f_p_gen1, p_gen2)

f_p_gen2 = apply_fmdl_1d(p_gen2)
p_covariant_step2 = np.array_equal(f_p_gen2, p_gen3)

print(f"f_MDL(P(gen₁)) = {list(f_p_gen1)}")
print(f"P(gen₂)        = {list(p_gen2)}")
print(f"Step 1 P-covariant: {p_covariant_step1}")
print()
print(f"f_MDL(P(gen₂)) = {list(f_p_gen2)}")
print(f"P(gen₃)        = {list(p_gen3)}")
print(f"Step 2 P-covariant: {p_covariant_step2}")
print()

# P-covariance would mean f_MDL(P(c)) = P(f_MDL(c))
# i.e., P commutes with f_MDL evolution
f_gen1 = apply_fmdl_1d(gen1)  # should be gen2
p_f_gen1 = p_transform_1d(f_gen1)  # P(f(gen1)) = P(gen2)
f_p_gen1_2 = apply_fmdl_1d(p_gen1)  # f(P(gen1))

parity_commutes_gen1 = np.array_equal(f_p_gen1_2, p_f_gen1)
print(f"Does f_MDL commute with P on gen₁?")
print(f"  P(f_MDL(gen₁)) = {list(p_f_gen1)}")
print(f"  f_MDL(P(gen₁)) = {list(f_p_gen1_2)}")
print(f"  f_MDL ∘ P = P ∘ f_MDL on gen₁: {parity_commutes_gen1}")
print()

results['a2_orbit_chirality'] = {
    'gen1': list(map(int, gen1)),
    'p_gen1': list(map(int, p_gen1)),
    'f_mdl_p_gen1': list(map(int, f_p_gen1_2)),
    'p_f_mdl_gen1': list(map(int, p_f_gen1)),
    'parity_commutes_on_gen1': bool(parity_commutes_gen1),
    'p_covariant_step1': bool(p_covariant_step1),
    'p_covariant_step2': bool(p_covariant_step2),
    'orbit_of_p_gen1': [list(map(int, s)) for s in orbit_p_gen1],
}

# ─────────────────────────────────────────────────────────────────────────────
# Part A3: Binary P-violation — Rule 110 vs Rule 124
# Rule 110 has bits (MSB to LSB for input 7→0): 01101110
# Rule 124 has bits: 01111100  (the left-right mirror of Rule 110)
# ─────────────────────────────────────────────────────────────────────────────

print("-" * 60)
print("Part A3: Binary P-violation (Rule 110 vs Rule 124)")
print("-" * 60)

rule110_bits = [(110 >> i) & 1 for i in range(8)]   # bit i = output for input i
rule124_bits = [(124 >> i) & 1 for i in range(8)]

print(f"Rule 110 outputs (input 0..7): {rule110_bits}")
print(f"Rule 124 outputs (input 0..7): {rule124_bits}")

# For binary 3-cell neighborhoods (l,c,r) ∈ {0,1}³:
# Input index = 4l + 2c + r
# P-reflected input index = 4r + 2c + l
binary_p_violating = []
for l in range(2):
    for c in range(2):
        for r in range(2):
            idx_fwd = 4*l + 2*c + r
            idx_rev = 4*r + 2*c + l
            if rule110_bits[idx_fwd] != rule110_bits[idx_rev]:
                binary_p_violating.append((l, c, r, rule110_bits[idx_fwd], rule110_bits[idx_rev]))

print(f"\nBinary P-violating neighborhoods (Rule 110):")
for l, c, r, fwd, rev in binary_p_violating:
    print(f"  ({l},{c},{r}): Rule110({l},{c},{r})={fwd}, Rule110({r},{c},{l})={rev}")
print(f"\nTotal binary P-violating neighborhoods: {len(binary_p_violating)} / 8")
print()

results['a3_binary_p_violation'] = {
    'rule110': rule110_bits,
    'rule124': rule124_bits,
    'binary_p_violating': binary_p_violating,
    'n_binary_p_violating': len(binary_p_violating),
}

# ─────────────────────────────────────────────────────────────────────────────
# Part A4: 3D Parity Test on Small Lattice
# f_MDL,3D is P-symmetric iff step_fmdl3d(P(grid)) = P(step_fmdl3d(grid))
# 3D P: grid[x,y,z] → grid[-x,-y,-z] (equiv. flip all three axes)
# ─────────────────────────────────────────────────────────────────────────────

print("-" * 60)
print("Part A4: 3D Parity Violation Test")
print("-" * 60)

def step_fmdl3d(grid: np.ndarray) -> np.ndarray:
    """One step of f_MDL,3D with Z₇-additive cross-dimensional coupling."""
    lx = np.roll(grid, 1,  axis=0).astype(np.int64)
    rx = np.roll(grid, -1, axis=0).astype(np.int64)
    ly = np.roll(grid, 1,  axis=1).astype(np.int64)
    ry = np.roll(grid, -1, axis=1).astype(np.int64)
    lz = np.roll(grid, 1,  axis=2).astype(np.int64)
    rz = np.roll(grid, -1, axis=2).astype(np.int64)
    c  = grid.astype(np.int64)

    fx = FMDL_1D[lx*49 + c*7 + rx]
    fy = FMDL_1D[ly*49 + c*7 + ry]
    fz = FMDL_1D[lz*49 + c*7 + rz]

    x_only = ((ly==0) & (ry==0) & (lz==0) & (rz==0))
    y_only = ((lx==0) & (rx==0) & (lz==0) & (rz==0))
    z_only = ((ly==0) & (ry==0) & (lx==0) & (rx==0))
    multi  = ~(x_only | y_only | z_only)

    out = np.zeros_like(grid)
    out[x_only] = fx[x_only]
    out[y_only] = fy[y_only]
    out[z_only] = fz[z_only]
    out[multi]  = (fx[multi].astype(np.int64) + fy[multi].astype(np.int64) +
                   fz[multi].astype(np.int64)) % 7
    return out.astype(np.int8)

def p_transform_3d(grid: np.ndarray) -> np.ndarray:
    """3D parity transform: flip all three axes."""
    return grid[::-1, ::-1, ::-1].copy()

# Test on a small L=6 lattice with asymmetric initial condition
L = 6
np.random.seed(42)
# Use a chirally asymmetric IC: non-symmetric along x-axis
grid_ic = np.zeros((L, L, L), dtype=np.int8)
# Put gen1 pattern along x-axis at center
cx, cy, cz = L//2, L//2, L//2
for i, v in enumerate(gen1):
    grid_ic[(cx + i - 2) % L, cy, cz] = v

p_grid_ic = p_transform_3d(grid_ic)

# One step evolution of original and P-reflected
grid_t1 = step_fmdl3d(grid_ic)
p_grid_t1 = step_fmdl3d(p_grid_ic)

# P-covariance check: does step(P(grid)) = P(step(grid))?
p_step_grid = p_transform_3d(grid_t1)
step_p_grid = p_grid_t1

p_covariant_3d = np.array_equal(p_step_grid, step_p_grid)
n_differing_3d = np.sum(p_step_grid != step_p_grid)
total_cells_3d = L**3

print(f"3D lattice size: {L}³ = {total_cells_3d} cells")
print(f"IC: gen₁ pattern along x-axis at center, all other cells = 0")
print(f"  P(step(IC))  vs  step(P(IC)):")
print(f"  P-covariant: {p_covariant_3d}")
print(f"  Differing cells: {n_differing_3d} / {total_cells_3d} ({100*n_differing_3d/total_cells_3d:.1f}%)")
print()

# Systematic test: random asymmetric ICs
np.random.seed(123)
n_p_tests = 100
p_violations_3d = []
for trial in range(n_p_tests):
    grid_r = np.random.randint(0, 3, (L, L, L), dtype=np.int8)  # sparse random IC
    p_grid_r = p_transform_3d(grid_r)
    step_r = step_fmdl3d(grid_r)
    step_p_r = step_fmdl3d(p_grid_r)
    p_step_r = p_transform_3d(step_r)
    n_diff = int(np.sum(step_p_r != p_step_r))
    p_violations_3d.append(n_diff)

n_p_violating_trials = sum(1 for x in p_violations_3d if x > 0)
avg_diff = np.mean(p_violations_3d)

print(f"Systematic 3D P-test ({n_p_tests} random ICs):")
print(f"  Trials with P-violation: {n_p_violating_trials}/{n_p_tests} ({100*n_p_violating_trials/n_p_tests:.0f}%)")
print(f"  Mean differing cells per trial: {avg_diff:.1f}")
print()

results['a4_3d_parity'] = {
    'p_covariant_gen1_ic': bool(p_covariant_3d),
    'n_differing_gen1_ic': int(n_differing_3d),
    'n_p_violating_random_trials': n_p_violating_trials,
    'n_random_trials': n_p_tests,
    'avg_diff_random': float(avg_diff),
}

# ─────────────────────────────────────────────────────────────────────────────
# Part A5: Chiral Eigenstate Search
# Find 5-ring configurations c where f_MDL^t(c) = P(f_MDL^t(P(c))) for t=1..3
# These are "P-covariant" states under f_MDL: their orbit IS symmetric under P
# ─────────────────────────────────────────────────────────────────────────────

print("-" * 60)
print("Part A5: Chiral Eigenstate Search on Z₅ Ring")
print("-" * 60)

# Search: for each 5-cell configuration in a manageable subset,
# check if it's P-covariant under f_MDL evolution.
# Due to Z₇^5 = 16807 states, we search a random subset and the orbit states.

def is_p_covariant_orbit(c: np.ndarray, steps: int = 3) -> bool:
    """Check if f_MDL^t(P(c)) = P(f_MDL^t(c)) for t=1..steps."""
    state = c.copy()
    p_state = p_transform_1d(c)
    for _ in range(steps):
        state = apply_fmdl_1d(state)
        p_state = apply_fmdl_1d(p_state)
        if not np.array_equal(p_state, p_transform_1d(state)):
            return False
    return True

# Check the SM orbit vectors
sm_vectors = {'gen1': gen1, 'gen2': gen2, 'gen3': gen3, 'vac': vac,
              'P(gen1)': p_gen1, 'P(gen2)': p_gen2, 'P(gen3)': p_gen3}

print("P-covariance of SM orbit vectors (3 steps):")
for name, v in sm_vectors.items():
    cov = is_p_covariant_orbit(v, 3)
    sym = "P-symmetric" if np.array_equal(v, p_transform_1d(v)) else "P-asymmetric"
    print(f"  {name}: {sym}, P-covariant orbit: {cov}")
print()

# Check P-symmetric configurations (those where P(c) = c)
# For a 5-cell ring with periodic BC, P-symmetric means c is a palindrome
# c = [a, b, c_mid, b, a] — only 7^3 = 343 such configs
n_p_sym_configs = 0
n_p_covariant_from_p_sym = 0
print("Sampling P-symmetric 5-ring configurations (palindromes):")
p_covariant_examples = []
for a in range(7):
    for b in range(7):
        for m in range(7):
            c = np.array([a, b, m, b, a], dtype=np.int8)
            n_p_sym_configs += 1
            if is_p_covariant_orbit(c, 3):
                n_p_covariant_from_p_sym += 1
                if len(p_covariant_examples) < 5:
                    p_covariant_examples.append(list(map(int, c)))

print(f"  Total palindrome configs: {n_p_sym_configs}")
print(f"  P-covariant (3-step orbit): {n_p_covariant_from_p_sym} ({100*n_p_covariant_from_p_sym/n_p_sym_configs:.1f}%)")
print(f"  Examples of P-covariant palindromes: {p_covariant_examples[:5]}")
print()

# Also check P-antisymmetric configurations: P(c) = 7-c (C-conjugate)
# These would be "purely chiral" configurations
n_chiral = 0
chiral_examples = []
for a in range(1, 7):
    for b in range(1, 7):
        for m in range(7):
            c = np.array([a, b, m, (7-b)%7, (7-a)%7], dtype=np.int8)
            p_c = p_transform_1d(c)
            c_conj = np.array([(7-x)%7 for x in c], dtype=np.int8)
            if np.array_equal(p_c, c_conj) and not np.array_equal(c, p_c):
                if is_p_covariant_orbit(c, 2):
                    n_chiral += 1
                    if len(chiral_examples) < 5:
                        chiral_examples.append(list(map(int, c)))

print(f"Checking P-C-dual configs (P(c) = C(c) = 7-c):")
print(f"  P-covariant chiral configs found: {n_chiral}")
print(f"  Examples: {chiral_examples[:5]}")
print()

results['a5_chiral_eigenstates'] = {
    'n_palindrome_p_covariant': n_p_covariant_from_p_sym,
    'total_palindromes': n_p_sym_configs,
    'fraction_palindrome_p_covariant': n_p_covariant_from_p_sym / n_p_sym_configs,
    'palindrome_p_covariant_examples': p_covariant_examples[:5],
    'sm_orbit_p_covariant': {
        name: {'p_covariant': bool(is_p_covariant_orbit(v, 3)),
               'p_symmetric': bool(np.array_equal(v, p_transform_1d(v)))}
        for name, v in sm_vectors.items()
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("Summary: f_MDL Chirality and P-Violation")
print("=" * 70)
print()

pv_frac = n_violating / n_total
print(f"1D f_MDL P-violation:")
print(f"  {n_violating}/{n_total} = {100*pv_frac:.1f}% of Z₇³ triples are P-violating")
print(f"  f_MDL has INTRINSIC PARITY VIOLATION (Rule 110 ≠ Rule 124)")
print()

print(f"SM orbit chirality:")
print(f"  gen₁ = {list(gen1)} is P-ASYMMETRIC (chiral): P(gen₁) = {list(p_gen1)} ≠ gen₁")
if not p_covariant_step1:
    print(f"  f_MDL(P(gen₁)) ≠ P(f_MDL(gen₁)) — orbit is NOT P-covariant!")
    print(f"  The SM orbit breaks parity at each step.")
else:
    print(f"  f_MDL(P(gen₁)) = P(f_MDL(gen₁)) — orbit IS P-covariant (unexpected)")
print()

print(f"3D f_MDL,3D parity:")
print(f"  {n_p_violating_trials}/{n_p_tests} random trials are P-violating in 3D")
print(f"  Average {avg_diff:.1f} differing cells per step")
print()

chirality_found = n_p_covariant_from_p_sym > 0
print(f"Chirality eigenstates (P-symmetric palindromes with P-covariant orbit):")
print(f"  Found {n_p_covariant_from_p_sym}/{n_p_sym_configs} ({100*n_p_covariant_from_p_sym/n_p_sym_configs:.1f}%)")
print()

# The key result: is parity-VIOLATION confirmed and does it classify the orbit?
if not p_covariant_step1:
    verdict = (
        "RESULT: f_MDL violates parity at the CA level. The SM generation orbit\n"
        "  gen₁=[1,5,2,2,1] is a chiral object: P(gen₁)≠gen₁ and P does not map\n"
        "  the orbit to itself. This is a CA-level analog of L/R chirality."
    )
else:
    verdict = "RESULT: f_MDL orbit is P-covariant (unexpected — check carefully)."
print(verdict)
print()

results['summary'] = {
    'p_violation_fraction_1d': pv_frac,
    'orbit_is_chiral': not bool(p_covariant_step1),
    'chirality_eigenstates_found': chirality_found,
    'n_p_violating_3d': n_p_violating_trials,
}

elapsed = time.time() - t0
results['elapsed_s'] = round(elapsed, 2)
print(f"Elapsed: {elapsed:.2f}s")

with open("fmdl3d_chirality_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Results saved to fmdl3d_chirality_results.json")
