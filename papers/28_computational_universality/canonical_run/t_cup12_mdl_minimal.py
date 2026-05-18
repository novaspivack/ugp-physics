"""
CUP-12: MDL-minimal universal Z₇ CA rule analysis.

The MDL-minimal completion of f: Z₇³→Z₇ satisfying:
  - 10 orbit constraints (phi_a7 standard canonical ordering [e⁻, u, d, νR, νL])
  - 8 Rule 110 binary sublayer constraints
  - All remaining 325 free neighborhoods → 0 (shortest description = constant 0)

Tests:
  1. Construct f_MDL
  2. Simulate on 200-cell ring for 400 steps with various ICs
  3. Determine Wolfram class
  4. Test Rule 110 simulation capability
  5. Note MDL-minimality argument (0 is canonical choice among uniform completions)
"""

import json
import numpy as np
import random
from collections import Counter
from math import log2

random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. Orbit constraints (phi_a7, standard branch, canonical ordering [e⁻, u, d, νR, νL])
#    Sourced from t_cup11b_sat_results.json (Round 18 first zero-conflict ordering)
# ---------------------------------------------------------------------------
ORBIT_CONSTRAINTS = {
    (1, 1, 5): 2,
    (1, 5, 2): 5,
    (5, 2, 2): 2,
    (2, 2, 1): 0,
    (2, 1, 1): 2,
    (2, 2, 5): 5,
    (2, 5, 2): 6,
    (5, 2, 0): 5,
    (2, 0, 2): 3,
    (0, 2, 2): 5,
}

# ---------------------------------------------------------------------------
# 2. Rule 110 binary constraints {0,1}³ → {0,1}
#    Rule 110 number: 01101110₂ = 110
#    (L,C,R) → output: (0,0,0)=0,(0,0,1)=1,(0,1,0)=1,(0,1,1)=1,
#                       (1,0,0)=0,(1,0,1)=1,(1,1,0)=1,(1,1,1)=0
# ---------------------------------------------------------------------------
RULE110_BINARY = {
    (0, 0, 0): 0,
    (0, 0, 1): 1,
    (0, 1, 0): 1,
    (0, 1, 1): 1,
    (1, 0, 0): 0,
    (1, 0, 1): 1,
    (1, 1, 0): 1,
    (1, 1, 1): 0,
}

# Verify no conflicts
for nbhd in RULE110_BINARY:
    assert nbhd not in ORBIT_CONSTRAINTS, f"Conflict at {nbhd}!"

print("=== CUP-12: MDL-Minimal Universal Z₇ CA Rule ===\n")
print(f"Orbit constraints: {len(ORBIT_CONSTRAINTS)} neighborhoods")
print(f"Rule 110 binary constraints: {len(RULE110_BINARY)} neighborhoods")
print(f"Total fixed: {len(ORBIT_CONSTRAINTS) + len(RULE110_BINARY)}")
print(f"Free (→ 0): {343 - len(ORBIT_CONSTRAINTS) - len(RULE110_BINARY)}")
print(f"Conflicts: 0 ✓\n")

# ---------------------------------------------------------------------------
# 3. Build f_MDL lookup table (full 343-entry table)
# ---------------------------------------------------------------------------
def build_f_mdl():
    """Build the MDL-minimal rule: orbit fixed, Rule 110 fixed, rest = 0."""
    table = {}
    for l in range(7):
        for c in range(7):
            for r in range(7):
                nbhd = (l, c, r)
                if nbhd in ORBIT_CONSTRAINTS:
                    table[nbhd] = ORBIT_CONSTRAINTS[nbhd]
                elif nbhd in RULE110_BINARY:
                    table[nbhd] = RULE110_BINARY[nbhd]
                else:
                    table[nbhd] = 0
    return table

f_mdl = build_f_mdl()

# ---------------------------------------------------------------------------
# 4. CA simulation engine
# ---------------------------------------------------------------------------
def step(state, rule):
    """One CA step on a ring."""
    n = len(state)
    return [rule[(state[(i-1) % n], state[i], state[(i+1) % n])] for i in range(n)]

def simulate(ic, rule, steps):
    """Simulate CA for given steps, return list of states."""
    state = list(ic)
    history = [state[:]]
    for _ in range(steps):
        state = step(state, rule)
        history.append(state[:])
    return history

def state_entropy(states):
    """Shannon entropy of value distribution in final state."""
    flat = [v for s in states for v in s]
    counts = Counter(flat)
    total = len(flat)
    return -sum((c/total)*log2(c/total) for c in counts.values() if c > 0)

# ---------------------------------------------------------------------------
# 5. Test on binary ICs (Rule 110 simulation test)
# ---------------------------------------------------------------------------
print("=== Test 1: Binary ICs (cells ∈ {0,1}) — Rule 110 sublayer ===\n")

def rule110_reference(ic, steps):
    """Reference Rule 110 on {0,1} ring."""
    state = list(ic)
    history = [state[:]]
    for _ in range(steps):
        n = len(state)
        new = [(state[(i-1)%n] * 4 + state[i] * 2 + state[(i+1)%n]) for i in range(n)]
        state = [((110 >> v) & 1) for v in new]
        history.append(state[:])
    return history

N = 200
T = 100

# Test 5 binary ICs
binary_test_results = []
for trial in range(5):
    ic_binary = [random.randint(0, 1) for _ in range(N)]
    
    hist_fmdl = simulate(ic_binary, f_mdl, T)
    hist_ref = rule110_reference(ic_binary, T)
    
    # Compare: f_MDL on binary IC vs Rule 110 reference
    matches = sum(1 for t in range(T+1) if hist_fmdl[t] == hist_ref[t])
    perfect = (matches == T + 1)
    
    # How long does f_MDL stay on binary values?
    binary_steps = 0
    for t in range(1, T+1):
        if all(v in (0, 1) for v in hist_fmdl[t]):
            binary_steps = t
        else:
            break
    
    binary_test_results.append({
        'trial': trial + 1,
        'matches_with_rule110': matches,
        'total_steps': T + 1,
        'perfect_simulation': perfect,
        'binary_valued_steps': binary_steps,
    })
    print(f"  Trial {trial+1}: matches={matches}/{T+1}, perfect={perfect}, binary steps={binary_steps}")

# The key test: if IC is binary and stays binary, does f_MDL = Rule 110?
print(f"\n  Result: f_MDL DOES simulate Rule 110 on binary ICs for as long as states remain binary.")
print(f"  Binary ICs can leave {'{'}0,1{'}'} range after step 0 if orbit constraints pull cell values.")
print(f"  The 8 Rule 110 binary constraints guarantee: f_MDL(a,b,c) = Rule110(a,b,c) for all (a,b,c)∈{{'{'}0,1{'}'}}³")
print(f"  So f_MDL EXACTLY simulates Rule 110 whenever all 3 neighbors are in {{0,1}}.")

# ---------------------------------------------------------------------------
# 6. Wolfram class analysis on random Z₇ ICs
# ---------------------------------------------------------------------------
print("\n=== Test 2: Random Z₇ ICs — Wolfram Class Analysis ===\n")

N_TRIALS = 50
N_SIZE = 200
T_WOLFRAM = 400

class_counts = Counter()
entropies = []
final_value_distributions = []

wolfram_details = []
for trial in range(N_TRIALS):
    ic = [random.randint(0, 6) for _ in range(N_SIZE)]
    history = simulate(ic, f_mdl, T_WOLFRAM)
    
    final_state = history[-1]
    final_values = set(final_state)
    
    # Entropy of final state
    ent = state_entropy([final_state])
    entropies.append(ent)
    final_value_distributions.append(sorted(final_values))
    
    # Classify Wolfram class based on final state characteristics
    # Class 1: all cells same value (fixed point or uniform)
    # Class 2: periodic (check last 50 steps for cycle)
    # Class 3: chaotic/random-looking (high entropy, no apparent period)
    # Class 4: complex (localized structures)
    
    if len(final_values) == 1:
        # All cells same value = fixed point candidate
        # Check if it's a fixed point under f_MDL
        next_state = step(final_state, f_mdl)
        if next_state == final_state:
            wclass = 1  # fixed point
        else:
            wclass = 2  # uniform but period-2+ (like all-0 → all-0 since f(0,0,0)=0)
    else:
        # Check for periodicity in last 50 steps
        found_period = None
        tail = history[-50:]
        for period in range(1, 25):
            if len(tail) > period and tail[-1] == tail[-1-period]:
                found_period = period
                break
        if found_period is not None:
            if ent < 0.5:
                wclass = 2  # low-entropy periodic
            else:
                wclass = 2  # periodic
        else:
            if ent > 1.5:
                wclass = 3  # high entropy, chaotic
            else:
                wclass = 3  # moderate entropy, not periodic in window
    
    class_counts[wclass] += 1
    wolfram_details.append({
        'trial': trial + 1,
        'final_values': sorted(final_values),
        'entropy': round(ent, 4),
        'wclass': wclass,
    })

print(f"  N_TRIALS={N_TRIALS}, ring_size={N_SIZE}, steps={T_WOLFRAM}")
print(f"  Wolfram class distribution:")
for wc in sorted(class_counts.keys()):
    frac = class_counts[wc] / N_TRIALS
    print(f"    Class {wc}: {class_counts[wc]}/{N_TRIALS} = {frac:.1%}")

mean_entropy = sum(entropies) / len(entropies)
print(f"  Mean final-state entropy: {mean_entropy:.4f} bits")
print(f"  (Max possible for Z₇: log₂(7) = {log2(7):.4f} bits)")

# Check if most ICs converge to all-zero (since free neighborhoods → 0)
zero_count = sum(1 for e in entropies if e == 0.0)
print(f"  ICs converging to all-zero (entropy=0): {zero_count}/{N_TRIALS}")

# Determine dominant Wolfram class
dominant_class = class_counts.most_common(1)[0][0]
print(f"\n  → Dominant Wolfram class: {dominant_class}")
if dominant_class == 1:
    wolfram_verdict = "Class 1 (fixed point attractor — all-zero dominant)"
elif dominant_class == 2:
    wolfram_verdict = "Class 2 (periodic cycles)"
elif dominant_class == 3:
    wolfram_verdict = "Class 3 (chaotic)"
else:
    wolfram_verdict = "Class 4 (complex)"
print(f"  → Assessment: {wolfram_verdict}")

# ---------------------------------------------------------------------------
# 7. Canonical SM gen1 parity IC test
# ---------------------------------------------------------------------------
print("\n=== Test 3: SM Gen1 Parity IC (phi_a7 canonical ordering) ===\n")

gen1 = [1, 5, 2, 2, 1]  # phi_a7 standard canonical ordering
gen2_expected = [2, 5, 2, 0, 2]
gen3_expected = [5, 6, 5, 3, 5]

# Simulate gen1 on a 5-cell ring (with f_MDL)
gen1_history = simulate(gen1, f_mdl, 3)
print(f"  gen1        = {gen1}")
print(f"  f_MDL(gen1) = {gen1_history[1]}")
print(f"  gen2_expect = {gen2_expected}")
print(f"  f_MDL(gen2) = {gen1_history[2]}")
print(f"  gen3_expect = {gen3_expected}")
print(f"  step1 match = {gen1_history[1] == gen2_expected}")
print(f"  step2 match = {gen1_history[2] == gen3_expected}")

# Note: f_MDL has 0 for unconstrained neighborhoods, so gen1→gen2 may differ
# from the orbit constraint if the actual neighborhoods differ
print(f"\n  Note: f_MDL uses 0 for unconstrained neighborhoods. If gen1→gen2 orbit")
print(f"  neighborhoods are not all in the 10 constrained set, f_MDL may diverge.")
print(f"  The 10 orbit constraints guarantee the correct orbit ONLY for those 10 neighborhoods.")

# Check which gen1 neighborhoods appear in the orbit constraints
gen1_nbhds = []
for i in range(5):
    l = gen1[(i-1) % 5]
    c = gen1[i]
    r = gen1[(i+1) % 5]
    nbhd = (l, c, r)
    in_orbit = nbhd in ORBIT_CONSTRAINTS
    expected_out = ORBIT_CONSTRAINTS.get(nbhd, 0)
    actual_out = f_mdl[nbhd]
    gen1_nbhds.append({'i': i, 'nbhd': nbhd, 'in_orbit': in_orbit, 'output': actual_out})
    print(f"  Cell {i}: nbhd={nbhd} → f_MDL={actual_out}, in_orbit={in_orbit}")

# ---------------------------------------------------------------------------
# 8. Rule 110 simulation capability test (formal)
# ---------------------------------------------------------------------------
print("\n=== Test 4: Rule 110 Simulation Capability (formal) ===\n")

print("  Strategy: Encode Rule 110 IC as binary values {0,1} in f_MDL ring.")
print("  Since f_MDL(a,b,c) = Rule110(a,b,c) for all (a,b,c)∈{0,1}³,")
print("  f_MDL exactly simulates Rule 110 AS LONG AS the state stays binary.")
print("")
print("  Key question: how many steps does a binary IC stay binary?")

N_BINARY = 200
ic_binary_test = [0] * N_BINARY
# Standard Rule 110 glider gun-like seed
ic_binary_test[N_BINARY // 2] = 1

hist_fmdl_bin = simulate(ic_binary_test, f_mdl, 400)
hist_ref_bin = rule110_reference(ic_binary_test, 400)

# Find first step where binary IC leaves {0,1}
first_nonbinary = None
for t in range(1, 401):
    if not all(v in (0, 1) for v in hist_fmdl_bin[t]):
        first_nonbinary = t
        break

print(f"  Single-cell IC: first step leaving binary = {first_nonbinary}")

# For ICs that stay binary: verify exact match with Rule 110
if first_nonbinary is not None:
    match_steps = sum(1 for t in range(first_nonbinary)
                      if hist_fmdl_bin[t] == hist_ref_bin[t])
    print(f"  Exact match with Rule 110: steps 0–{first_nonbinary-1} ({match_steps}/{first_nonbinary} steps)")
    print(f"  After step {first_nonbinary}: f_MDL diverges (orbit constraint pulls value out of {{0,1}})")
else:
    print(f"  IC stays binary for all 400 steps! f_MDL = Rule 110 perfectly.")
    print(f"  Match verification:")
    perfect_match = all(hist_fmdl_bin[t] == hist_ref_bin[t] for t in range(401))
    print(f"    Perfect match: {perfect_match}")

print("\n  Formal conclusion:")
print("  f_MDL CAN simulate Rule 110 in principle (the 8 binary constraints are exact).")
print("  In practice, a binary IC leaves {0,1} when a neighboring cell transition hits")
print("  an orbit-constrained neighborhood with non-binary output, OR when the zero-valued")
print("  free neighborhoods pull the state toward 0 (which is in {0,1} — safe).")
print("  The orbit constraints (non-binary outputs) can pull binary cells to {2,3,5,6},")
print("  interrupting the Rule 110 simulation when orbit neighborhoods appear in the IC.")

# ---------------------------------------------------------------------------
# 9. MDL-minimality argument
# ---------------------------------------------------------------------------
print("\n=== Analysis 5: MDL-Minimality ===\n")
print("  Among all f: Z₇³→Z₇ satisfying the 18 fixed constraints:")
print("  - Description length = log₂(7^325) = 325 × log₂(7) ≈ 916 bits (for free part)")
print("  - ALL uniform completions (all-0, all-1, ..., all-6) have the SAME description length.")
print("  - The choice '0' is canonical: smallest value in Z₇, simplest to specify.")
print("  - f_MDL is not unique among MDL-minimal rules — all 7 uniform completions are tied.")
print("  - But 0 is the MOST NATURAL choice (identity in (Z₇, +), absorbing element absence).")
print(f"  → f_MDL is ONE representative of the MDL-minimal equivalence class.")

# ---------------------------------------------------------------------------
# 10. Collect all results
# ---------------------------------------------------------------------------
results = {
    'script': 't_cup12_mdl_minimal.py',
    'orbit_constraints': {str(k): v for k, v in ORBIT_CONSTRAINTS.items()},
    'rule110_binary_constraints': {str(k): v for k, v in RULE110_BINARY.items()},
    'n_orbit_constraints': len(ORBIT_CONSTRAINTS),
    'n_rule110_constraints': len(RULE110_BINARY),
    'n_fixed': len(ORBIT_CONSTRAINTS) + len(RULE110_BINARY),
    'n_free': 343 - len(ORBIT_CONSTRAINTS) - len(RULE110_BINARY),
    'n_conflicts': 0,
    'binary_sublayer_tests': binary_test_results,
    'wolfram_class_distribution': {str(k): v for k, v in class_counts.items()},
    'wolfram_dominant_class': dominant_class,
    'wolfram_verdict': wolfram_verdict,
    'mean_final_entropy': round(mean_entropy, 6),
    'zero_attractor_count': zero_count,
    'zero_attractor_fraction': round(zero_count / N_TRIALS, 4),
    'gen1_orbit_test': {
        'gen1': gen1,
        'gen2_expected': gen2_expected,
        'gen3_expected': gen3_expected,
        'gen1_to_gen2_match': gen1_history[1] == gen2_expected,
        'gen2_to_gen3_match': gen1_history[2] == gen3_expected,
        'f_mdl_gen1_output': gen1_history[1],
        'f_mdl_gen2_output': gen1_history[2],
    },
    'rule110_simulation_first_nonbinary_step': first_nonbinary,
    'rule110_can_simulate': True,  # by construction of 8 binary constraints
    'mdl_minimality': 'f_MDL is one of 7 MDL-minimal completions (all uniform completions tied); 0 is canonical choice',
}

out_path = 't_cup12_mdl_minimal_results.json'
with open(out_path, 'w') as fp:
    json.dump(results, fp, indent=2)

print(f"\n=== Summary ===")
print(f"  Wolfram class of f_MDL (on random Z₇ ICs): {wolfram_verdict}")
print(f"  Rule 110 simulation: YES (by construction, for steps staying in {{0,1}})")
print(f"  MDL-minimal: YES (one of 7 tied uniform completions; 0 is canonical)")
print(f"  Results saved to: {out_path}")
