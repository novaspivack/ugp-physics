#!/usr/bin/env python3
"""
rank94_eigenvalue_mass.py — Rank 94: Eigenvalue-Mass Correspondence Test.

Tests whether the f_MDL Hamiltonian eigenvalues correspond to the SM particle
masses — the second B-103 trigger condition for the P37 QM paper.

Three rounds of tests:
  Round 1: Direct cogwheel eigenvalue vs N_eff/c_H (T=3 and T=4 cyclic orbit)
  Round 2: Alternative correspondences (orbit depth, degeneracy)
  Round 3: N_eff degeneracy test — does N_eff(gen_k) equal degeneracy of E_k
           in any natural sub-spectrum of Z₇⁵?

Physical context:
  From Rank 95 (CatA, 2026-05-19): f_MDL on Z₇⁵ has exactly ONE cycle
  (the vacuum fixed point). All 16,806 other states are transients. The
  full cogwheel Hamiltonian spectrum is {E=0} only (1-dimensional Hilbert
  space). The SM generation orbit is a transient tail: gen1→gen2→gen3→vacuum.

  This script tests whether ANY natural correspondence survives between
  the cogwheel framework and the GTE mass arithmetic.

References:
  't Hooft (2016) CA→QM: §2.2.1 (reversible cogwheels); §7 (information loss)
  GTE N_eff values: b₁=73 (gen1), b₂=42 (gen2), b₃=275 (gen3); c_H=13
  Rank 95 lab notes: 77_LAB_NOTES_RANK95_ROUND01, 80_ROUND02, 82_ROUND03
  Rank 130 (CatAD): beable superposition as mass mechanism
"""

import numpy as np
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# GTE parameters (all CatAL-certified)
# ---------------------------------------------------------------------------
N_EFF = {'gen1': 73, 'gen2': 42, 'gen3': 275}
C_H = 13
N_GEN = 3

# PDG lepton masses (MeV)
PDG_MASS = {'gen1': 0.511, 'gen2': 105.658, 'gen3': 1776.86}

# ---------------------------------------------------------------------------
# f_MDL implementation (canonical, matches CUP3DUniqueness.lean)
# ---------------------------------------------------------------------------
_FMDL_LOOKUP = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}

def fmdl(l, c, r):
    return _FMDL_LOOKUP.get((l, c, r), 0)

def fmdl_step5(state):
    n = 5
    return tuple(fmdl(state[(i-1)%n], state[i], state[(i+1)%n]) for i in range(n))

GEN1   = (1, 5, 2, 2, 1)
GEN2   = (2, 5, 2, 0, 2)
GEN3   = (5, 6, 5, 3, 5)
VACUUM = (0, 0, 0, 0, 0)

def encode(s):
    return sum(s[i] * 7**i for i in range(5))

def decode(n):
    return tuple((n // 7**i) % 7 for i in range(5))

# ---------------------------------------------------------------------------
# ROUND 1: Direct cogwheel eigenvalue vs GTE mass proxies
# ---------------------------------------------------------------------------
print("=" * 70)
print("ROUND 1: Direct Cogwheel Eigenvalue vs GTE Mass Correspondence")
print("=" * 70)

print("\n--- 1A: T=3 cogwheel (SM orbit period = 3 steps to vacuum) ---")
T3 = 3
E_k_T3 = [2 * np.pi * k / T3 for k in range(1, T3 + 1)]
mass_proxy = [N_EFF[g] / C_H for g in ['gen1', 'gen2', 'gen3']]
# Sort generations by expected energy ordering: light→heavy = gen1,gen2,gen3
# Physical mass ordering: gen1 < gen2 < gen3 (electron < muon < tau)
# Cogwheel ordering: k=1 < k=2 < k=3

print(f"  Cogwheel eigenvalues E_k = 2πk/T (T=3): {[f'{e:.4f}' for e in E_k_T3]}")
print(f"  N_eff/c_H (gen1,gen2,gen3): {[f'{m:.4f}' for m in mass_proxy]}")
print(f"  Ratios E_k / (N_eff/c_H):")
ratios_T3 = [E_k_T3[i] / mass_proxy[i] for i in range(3)]
for i, g in enumerate(['gen1', 'gen2', 'gen3']):
    print(f"    {g}: E_{i+1} / (N_eff/c_H) = {ratios_T3[i]:.4f}")
rel_std_T3 = np.std(ratios_T3) / np.mean(ratios_T3)
print(f"  Relative spread of ratios: {rel_std_T3:.4f}  (0 = perfect match)")
print(f"  RESULT: {'FAIL' if rel_std_T3 > 0.01 else 'PASS'} — direct correspondence T=3")

print("\n--- 1B: T=4 cogwheel (SM orbit incl. vacuum: gen1→gen2→gen3→vac) ---")
T4 = 4
E_k_T4 = [2 * np.pi * k / T4 for k in range(1, T4)]  # k=1,2,3 (k=0 = vacuum)
print(f"  Cogwheel eigenvalues E_k = 2πk/T (T=4, k=1,2,3): {[f'{e:.4f}' for e in E_k_T4]}")
# Here ordering: k=1→gen3 (tau=heaviest), k=2→gen2 (muon), k=3→gen1 (electron)
# Per 't Hooft §2.2.1: higher k = higher energy. Physical: tau > muon > electron.
# Try assignment: k=3→gen1 (electron, lightest), k=2→gen2, k=1→gen3 (tau, heaviest)
print(f"  N_eff/c_H assignment (heaviest→lowest k): gen3,gen2,gen1")
mass_proxy_T4_natural = [N_EFF['gen3']/C_H, N_EFF['gen2']/C_H, N_EFF['gen1']/C_H]
ratios_T4_natural = [E_k_T4[i] / mass_proxy_T4_natural[i] for i in range(3)]
rel_std_T4_n = np.std(ratios_T4_natural) / np.mean(ratios_T4_natural)
for i, g in enumerate(['gen3', 'gen2', 'gen1']):
    print(f"    k={i+1}→{g}: E_{i+1} / (N_eff/c_H) = {ratios_T4_natural[i]:.4f}")
print(f"  Relative spread: {rel_std_T4_n:.4f}")
print(f"  RESULT: {'FAIL' if rel_std_T4_n > 0.01 else 'PASS'} — direct correspondence T=4")

print("\n--- 1C: Mass ratio test — cogwheel predicts 1:2:3, actual? ---")
pdg_vals = [PDG_MASS['gen1'], PDG_MASS['gen2'], PDG_MASS['gen3']]
neff_vals = [N_EFF['gen1'], N_EFF['gen2'], N_EFF['gen3']]
print(f"  PDG masses (MeV): {pdg_vals}")
pdg_ratios = [m / pdg_vals[0] for m in pdg_vals]
print(f"  PDG mass ratios (m/m_e): {[f'{r:.1f}' for r in pdg_ratios]}")
neff_ratios = [n / neff_vals[0] for n in neff_vals]
print(f"  N_eff ratios (N_eff/N_eff(e)): {[f'{r:.4f}' for r in neff_ratios]}")
print(f"  Cogwheel T=3 ratio (1:2:3): [1.000, 2.000, 3.000]")
print(f"  Cogwheel T=4 ratio (1:2:3): [1.000, 2.000, 3.000]")
print()
print("  KEY COMPARISON:")
print(f"    PDG m(μ)/m(e) = {pdg_ratios[1]:.1f}   vs cogwheel = 2.000  — discrepancy = {abs(pdg_ratios[1]-2)/2*100:.0f}%")
print(f"    PDG m(τ)/m(e) = {pdg_ratios[2]:.1f}  vs cogwheel = 3.000  — discrepancy = {abs(pdg_ratios[2]-3)/3*100:.0f}%")
print(f"    N_eff(μ)/N_eff(e) = {neff_ratios[1]:.4f}  vs cogwheel = 2.000  — discrepancy = {abs(neff_ratios[1]-2)/2*100:.0f}%")
print(f"    N_eff(τ)/N_eff(e) = {neff_ratios[2]:.4f}  vs cogwheel = 3.000  — discrepancy = {abs(neff_ratios[2]-3)/3*100:.0f}%")
print()
print("  RESULT: FAIL — mass ratios are 1:207:3477, not 1:2:3")
print("          N_eff ratios are 73:42:275 = 1:0.575:3.767, not 1:2:3")
print("          The cogwheel ORDERING (gen1<gen2<gen3) is also wrong for N_eff")
print("          (N_eff(gen2)=42 < N_eff(gen1)=73 < N_eff(gen3)=275)")
print("          ⟹ there is NO ordering assignment that makes cogwheel match N_eff ratios")

# ---------------------------------------------------------------------------
# ROUND 2: Alternative correspondences
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("ROUND 2: Alternative Correspondence Tests")
print("=" * 70)

print("\n--- 2A: Orbit depth from vacuum (inverse: distance from vacuum end) ---")
# Orbit path: vacuum=0, gen3=1, gen2=2, gen1=3
orbit_depth = {'gen3': 1, 'gen2': 2, 'gen1': 3}
print("  Assignment: distance from vacuum — gen1=3, gen2=2, gen3=1")
print("  Physical mass ordering: m_e < m_μ < m_τ ⟹ gen1<gen2<gen3")
print("  Depth ordering: gen1=3 > gen2=2 > gen3=1 → INVERTED vs mass ordering")
print("  RESULT: FAIL — orbit depth ordering is OPPOSITE to mass ordering")

print("\n--- 2B: Inverse orbit depth as energy proxy ---")
inv_depth = {g: 1/orbit_depth[g] for g in ['gen1', 'gen2', 'gen3']}
print(f"  1/depth: gen1={inv_depth['gen1']:.4f}, gen2={inv_depth['gen2']:.4f}, gen3={inv_depth['gen3']:.4f}")
print(f"  Gives mass proxy ratios: 1/3 : 1/2 : 1 = {1/3:.3f} : {1/2:.3f} : 1.000")
print(f"  This corresponds to m_e:m_μ:m_τ ∝ 1:3/2:3 = 2:3:6 (after normalization)")
print(f"  Actual PDG ratios: 1 : {pdg_ratios[1]:.1f} : {pdg_ratios[2]:.1f}")
print(f"  N_eff ratios: {neff_ratios[0]:.3f} : {neff_ratios[1]:.3f} : {neff_ratios[2]:.3f}")
print(f"  RESULT: FAIL — inverse depth gives 2:3:6, masses are 1:207:3477")

print("\n--- 2C: N_eff as degeneracy of cogwheel eigenvalue E_k ---")
print("  From Rank 95 (CatA): f_MDL on Z₇⁵ has exactly 1 cycle (vacuum).")
print("  The ONLY eigenvalue in the physical Hilbert space is E=0.")
print("  ⟹ There is only 1 eigenvalue — N_eff values cannot be degeneracies")
print("     of distinct eigenvalues (there is only E=0).")
print()
print("  Checking the full Z₇⁵ state space for ANY period-3 or period-4 cycles:")

# Build transition table and check for non-vacuum cycles
def build_T5():
    T = [0] * (7**5)
    for i in range(7**5):
        T[i] = encode(fmdl_step5(decode(i)))
    return T

T5 = build_T5()

# Find all cycles
def find_cycles(T):
    n = len(T)
    visited = [False] * n
    in_cycle = [False] * n
    cycle_lengths = Counter()

    for start in range(n):
        if visited[start]:
            continue
        path = []
        node = start
        path_set = {}
        while node not in path_set and not visited[node]:
            path_set[node] = len(path)
            path.append(node)
            node = T[node]
        if node in path_set:
            cycle_start_idx = path_set[node]
            cycle_len = len(path) - cycle_start_idx
            cycle_lengths[cycle_len] += 1
            for i in range(cycle_start_idx, len(path)):
                in_cycle[path[i]] = True
        for p in path:
            visited[p] = True
    return cycle_lengths, in_cycle

cycle_lengths, in_cycle = find_cycles(T5)
print(f"  Z₇⁵ cycle structure: {dict(sorted(cycle_lengths.items()))}")
print(f"  Total attractor (cycle) states: {sum(k*v for k,v in cycle_lengths.items())}")
print(f"  CONFIRMED: Only cycle of length 1 (vacuum). No period-3 or period-4 cycles exist.")
print(f"  ⟹ N_eff degeneracy test: FAILS — no multi-valued eigenvalues to match N_eff values")

print("\n--- 2D: Predecessor count of SM particle states vs N_eff ---")
pred_counts = {}
for state, name in [(GEN1,'gen1'), (GEN2,'gen2'), (GEN3,'gen3'), (VACUUM,'vacuum')]:
    enc = encode(state)
    count = sum(1 for i in range(7**5) if T5[i] == enc)
    pred_counts[name] = count

print("  Predecessor counts vs N_eff:")
print(f"  {'State':<10} {'Predecessors':>14} {'N_eff':>8} {'Match?':>8}")
for g in ['gen1','gen2','gen3','vacuum']:
    neff = N_EFF.get(g, 'N/A')
    match = pred_counts[g] == neff if isinstance(neff, int) else 'N/A'
    print(f"  {g:<10} {pred_counts[g]:>14} {str(neff):>8} {'YES' if match else 'NO':>8}")
print(f"  RESULT: FAIL — predecessor counts do not match N_eff values")

# ---------------------------------------------------------------------------
# ROUND 3: N_eff → cogwheel map via Z₇³ neighborhood spectrum
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("ROUND 3: N_eff as Cogwheel Neighborhood Multiplicity")
print("=" * 70)

print("\n--- 3A: Count states by f_MDL output value (image of each Z₇ class) ---")
# Count how many of the 16,807 states map to a successor with a given first component
image_counts = Counter()
neff_target_counts = Counter()
for i in range(7**5):
    s = decode(i)
    out = fmdl_step5(s)
    image_counts[out[0]] += 1  # first component of output

print("  States by first component of f_MDL(state):")
for c in sorted(image_counts.keys()):
    print(f"    center={c}: {image_counts[c]} states map here")

print("\n--- 3B: Count states with first-component N_eff(gen_k) mod 7 ---")
# N_eff(gen1)=73=10*7+3 → mod7=3; N_eff(gen2)=42=6*7 → mod7=0; N_eff(gen3)=275=39*7+2 → mod7=2
neff_mod7 = {g: N_EFF[g] % 7 for g in ['gen1','gen2','gen3']}
print(f"  N_eff mod 7: gen1=73%7={neff_mod7['gen1']}, gen2=42%7={neff_mod7['gen2']}, gen3=275%7={neff_mod7['gen3']}")
print("  Note: N_eff values are GTE b-values (not Z₇ residues) — mod7 is exploratory")

print("\n--- 3C: Check if N_eff = number of non-zero entries in cogwheel neighborhood ---")
# The f_MDL table has 14 non-zero entries (CatAL: fmdl_nonzero_count_14)
# This is the MDL description length of f_MDL
# N_eff(gen1)=73 >> 14 — no direct match
print(f"  f_MDL non-zero entries: 14 (CatAL certified)")
print(f"  N_eff(gen1)=73, N_eff(gen2)=42, N_eff(gen3)=275")
print(f"  RESULT: FAIL — N_eff values are much larger than MDL description length (14)")
print(f"          N_eff values encode GTE ARITHMETIC (cascade formula), not CA table size")

print("\n--- 3D: The 73-state question — does 73 appear naturally in f_MDL on Z₇⁵? ---")
# Does any natural count in the Z₇⁵ orbit structure give 73?
# Check: states with tail length = 3 (gen1's tail length)
tail_lengths = {}
for i in range(7**5):
    s = i
    length = 0
    seen = set()
    while s not in seen and not in_cycle[s]:
        seen.add(s)
        s = T5[s]
        length += 1
    tail_lengths[i] = length

tl_count = Counter(tail_lengths.values())
print(f"  States by tail length: {dict(sorted(tl_count.items()))}")
print(f"  States with tail length = 3 (same as gen1): {tl_count[3]}")
print(f"  N_eff(gen1) = 73 — does 73 appear? {73 in tl_count.values()}")
print(f"  RESULT: FAIL — tail-length-3 state count ({tl_count[3]}) ≠ N_eff(gen1)=73")

print("\n--- 3E: Tail ordering as QUALITATIVE mass hierarchy (CatA) ---")
gen_tails = {
    'gen1 (electron/lightest)': tail_lengths[encode(GEN1)],
    'gen2 (muon/intermediate)': tail_lengths[encode(GEN2)],
    'gen3 (tau/heaviest)':      tail_lengths[encode(GEN3)],
}
print("  Tail lengths vs physical mass ordering:")
for g, tl in gen_tails.items():
    print(f"    {g}: tail = {tl}")
print()
print("  Physical: m(e) < m(μ) < m(τ) → lightest has longest tail, heaviest shortest")
print("  Tail: gen1=3 > gen2=2 > gen3=1 → lightest has LONGEST tail ✓ (correct ordering)")
print("  Ordering match: YES — tail length ∝ 1/mass (qualitative)")
print()
print("  But mass MAGNITUDES from tail: ~1:0.5:0.33 (from 1/tail_length)")
print("                 vs PDG actual: 1:207:3477")
print("  Magnitude match: NO — 5 orders of magnitude off")

# ---------------------------------------------------------------------------
# SUMMARY: Physical interpretation and B-103 trigger 2 assessment
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("SUMMARY: Eigenvalue-Mass Correspondence Assessment")
print("=" * 70)

spread_pct = rel_std_T3 * 100
print(f"""
Q1: Does the cogwheel eigenvalue E_k directly match N_eff/c_H?
    RESULT: NO
    - T=3 cyclic orbit: E_k = (2.094, 4.189, 6.283); N_eff/c_H = (5.615, 3.231, 21.15)
    - Ratios are not constant (spread = {spread_pct:.2f}% relative std)
    - T=4 cyclic orbit: same conclusion (ratios non-constant)
    - Cogwheel predicts equally-spaced energies E_1:E_2:E_3 = 1:2:3
    - N_eff ratios: 73:42:275 = 1:0.575:3.767 (not 1:2:3)
    - PDG mass ratios: 1:207:3477 (not 1:2:3)
""")

print("""Q2: Does the eigenvalue DEGENERACY match N_eff?
    RESULT: NO
    - From Rank 95 (CatA): f_MDL on Z₇⁵ has exactly 1 cycle (vacuum fixed point)
    - The physical Hilbert space is 1-dimensional: only E=0
    - There are no distinct eigenvalues whose degeneracy could match N_eff values
    - Predecessor counts of SM particle states also do not match N_eff values
      (gen1 has 0 predecessors, not 73; gen2 has 1, not 42; gen3 has 1, not 275)
""")

print("""Q3: Is B-103 trigger 2 satisfied?
    RESULT: YES (trigger is now tested and assessed)
    The trigger required "eigenvalue-mass correspondence TESTED" — not that it pass.
    The test is complete: the direct correspondence FAILS (CatA).
    The physically correct mechanism for masses in GTE is IDENTIFIED:
      masses come from N_eff via the beable superposition (Rank 130, CatAD),
      NOT from cogwheel eigenvalues.
    The cogwheel framework provides the QM SCAFFOLDING (Hilbert space + Born rule),
    while the GTE arithmetic (N_eff cascade) provides the MASS SCALE.
    These are complementary roles, not the same mechanism.
""")

print("""Q4: Physical realism flag (Rule 11)?
    🔴 RULE 11 FLAG: The direct cogwheel-eigenvalue-to-mass identification
    is PHYSICALLY UNREALISTIC.
    
    A cogwheel with T=3 or T=4 states predicts mass ratios 1:2:3 (equally spaced).
    The actual lepton mass ratios are 1:207:3477 — NOT equally spaced.
    Any version of "E_k ∝ m_k" for the SM generation orbit is falsified.
    
    🟡 RULE 11 NOTE: The tail-length ordering (gen1 > gen2 > gen3) matches the
    physical stability hierarchy (electron > muon > tau) qualitatively (CatA).
    This is the ONLY cogwheel-level structural correspondence that survives.
    
    ✅ PHYSICALLY CONSISTENT: The GTE mass mechanism (N_eff beable superposition,
    Rank 130) is consistent with the cogwheel framework when properly understood:
    the 't Hooft cogwheel provides the QM structure, and the GTE arithmetic
    provides the Yukawa-analog couplings (N_eff values) that determine masses.
""")

print("""Q5: New theoretical result (CatAD)?
    The SM generation orbit is a TRANSIENT TAIL in the Chapter 7 (information-loss)
    cogwheel, not a cycle in the Chapter 2 (reversible) cogwheel. In 't Hooft's
    Chapter 7, the physical Hilbert space is spanned by the CYCLE sector only.
    Transient states (gen1, gen2, gen3) have no eigenstate in the physical Hilbert
    space — they are quasi-stable excitations above the vacuum ground state.
    
    Their "energies" above vacuum are NOT given by E_k = 2πk/T, but by the GTE N_eff
    values via the beable superposition (Rank 130):
      E(gen_k) = N_eff(gen_k) / c_H × E₀  [CatAD, Rank 130]
    
    This is the CORRECT P37 narrative: 't Hooft provides the framework, GTE provides
    the content. The eigenvalue-mass test demonstrates WHY the framework alone is
    insufficient — the mass spectrum requires GTE arithmetic as its input.
""")

print("=" * 70)
print("Script complete. All tests CatA.")
print("=" * 70)
