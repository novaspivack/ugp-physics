#!/usr/bin/env python3
"""
EPIC_067_R110 — Round 3: Perturbed Orbit Test

The decisive test for Hypothesis A vs B:
  If varying the orbit constraints consistently selects Class 4 rules →
  the orbit structure is "attracted" to Class 4 → Hypothesis A (structural)
  
  If varying the orbit constraints sometimes selects Class 1/2/3 rules →
  the SM orbit happens to land on Class 4 → Hypothesis B (coincidental)

Approach:
  1. Start with the SM orbit: gen1=[1,1,0,0,1] → gen2=[0,1,0,1,1] → gen3=[1,1,1,1,1]
  2. Generate perturbed orbits by flipping bits in gen2 or gen3 (one bit at a time)
  3. For each perturbed orbit, find which vacuum-transparent rules satisfy it
  4. Check the Wolfram class of the selected rules
  5. If consistently Class 4: structural. If mixed: coincidental.

Key insight from Round 2: the orbit selects rules by their active minterms {1,2,3,5,6}.
Rules 110 and 111 share minterms {1,2,3,5,6}, differing only on minterm 0.
Perturbing gen2 or gen3 will change which minterms are required.
"""

import numpy as np
import json
import time
from itertools import product as iprod

t0 = time.time()
results = {}

print("=" * 70)
print("EPIC_067_R110 — Round 3: Perturbed Orbit Test")
print("=" * 70)
print()

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────
GEN1 = [1, 1, 0, 0, 1]
GEN2 = [0, 1, 0, 1, 1]
GEN3 = [1, 1, 1, 1, 1]

def rule_apply_5ring(rule_num, state):
    outs = [(rule_num >> i) & 1 for i in range(8)]
    n = len(state)
    return [outs[4*state[(i-1)%n] + 2*state[i] + state[(i+1)%n]] for i in range(n)]

def satisfies_orbit(rule_num, g1, g2, g3):
    return rule_apply_5ring(rule_num, g1) == g2 and rule_apply_5ring(rule_num, g2) == g3

def is_vac_transparent(rule_num):
    return (rule_num & 1) == 0

# For Wolfram class: use a simpler but more focused test for Class 4
# Class 4 signature: persistent localized structures (gliders) that survive for many steps
# We'll run on a single-cell IC (seed) and check if complex patterns emerge
def has_complex_dynamics(rule_num, N=100, T=300):
    """
    Test for Class 4 / complex behavior using a single-seed IC.
    Returns True if the rule shows complex long-range behavior.
    """
    outs = [(rule_num >> i) & 1 for i in range(8)]
    
    # Single seed in the middle
    state = [0]*N
    state[N//2] = 1
    
    patterns = set()
    for _ in range(T):
        new = [outs[4*state[(i-1)%N] + 2*state[i] + state[(i+1)%N]] for i in range(N)]
        state = new
        patterns.add(tuple(state))
    
    alive = sum(state)
    n_unique = len(patterns)
    
    # Class 1: dies out
    if alive < 3: return 'C1'
    # Class 2: becomes periodic (few unique patterns)
    if n_unique < 20: return 'C2'
    # Class 3 vs 4: hard to distinguish simply
    # Class 4 tends to have structured patterns; we'll use density heuristic
    density = alive / N
    if density > 0.4: return 'C3'  # high density = chaotic fill
    return 'C4_candidate'  # structured, low density → likely complex


# ─────────────────────────────────────────────────────────────────────────────
# Generate perturbed orbits
# ─────────────────────────────────────────────────────────────────────────────
print("─" * 60)
print("Perturbed orbit analysis")
print("─" * 60)
print()

all_perturbed_results = []

# Perturb gen2: flip one bit at a time
print("  Flipping gen2 bits:")
print()
for pos in range(5):
    gen2_perturbed = GEN2.copy()
    gen2_perturbed[pos] = 1 - gen2_perturbed[pos]  # flip
    
    # Find all rules satisfying orbit with perturbed gen2
    satisfying = [r for r in range(256) if satisfies_orbit(r, GEN1, gen2_perturbed, GEN3)]
    vt_rules = [r for r in satisfying if is_vac_transparent(r)]
    
    # Wolfram class of each
    classes = {r: has_complex_dynamics(r) for r in vt_rules}
    complex_count = sum(1 for c in classes.values() if 'C4' in c)
    
    bit_desc = f"gen2[{pos}]: {GEN2[pos]}→{gen2_perturbed[pos]}"
    print(f"    {bit_desc}: {len(satisfying)} orbit-satisfying, {len(vt_rules)} vac-transp")
    if vt_rules:
        for r in vt_rules:
            print(f"      Rule {r:3d}: {classes[r]}")
    else:
        print(f"      No vacuum-transparent orbit-satisfying rule exists")
    
    all_perturbed_results.append({
        'perturbation': f'gen2[{pos}] flipped',
        'perturbed_state': gen2_perturbed,
        'orbit_satisfying': satisfying,
        'vt_rules': vt_rules,
        'classes': {str(r): c for r,c in classes.items()},
        'complex_count': complex_count,
    })

print()
print("  Flipping gen3 bits (one at a time):")
print()

for pos in range(5):
    gen3_perturbed = GEN3.copy()
    gen3_perturbed[pos] = 1 - gen3_perturbed[pos]
    
    satisfying = [r for r in range(256) if satisfies_orbit(r, GEN1, GEN2, gen3_perturbed)]
    vt_rules = [r for r in satisfying if is_vac_transparent(r)]
    classes = {r: has_complex_dynamics(r) for r in vt_rules}
    complex_count = sum(1 for c in classes.values() if 'C4' in c)
    
    bit_desc = f"gen3[{pos}]: {GEN3[pos]}→{gen3_perturbed[pos]}"
    print(f"    {bit_desc}: {len(satisfying)} orbit-satisfying, {len(vt_rules)} vac-transp")
    if vt_rules:
        for r in vt_rules:
            print(f"      Rule {r:3d}: {classes[r]}")
    else:
        print(f"      No vacuum-transparent orbit-satisfying rule exists")
    
    all_perturbed_results.append({
        'perturbation': f'gen3[{pos}] flipped',
        'perturbed_state': gen3_perturbed,
        'orbit_satisfying': satisfying,
        'vt_rules': vt_rules,
        'classes': {str(r): c for r,c in classes.items()},
        'complex_count': complex_count,
    })

results['perturbed_orbits'] = all_perturbed_results


# ─────────────────────────────────────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────────────────────────────────────
print()
print("─" * 60)
print("Analysis: What class do perturbed orbit rules have?")
print("─" * 60)
print()

# Aggregate results
total_perturbed = len(all_perturbed_results)
has_vt_rule = sum(1 for r in all_perturbed_results if r['vt_rules'])
all_rules_found = []
for r in all_perturbed_results:
    all_rules_found.extend(r['vt_rules'])

class_tally = {'C1': 0, 'C2': 0, 'C3': 0, 'C4_candidate': 0, 'none': 0}
for r in all_perturbed_results:
    if not r['vt_rules']:
        class_tally['none'] += 1
    else:
        for c in r['classes'].values():
            if c in class_tally:
                class_tally[c] += 1

print(f"  Total perturbations tested: {total_perturbed}")
print(f"  Perturbations with a vac-transparent rule: {has_vt_rule}")
print(f"  Class distribution of selected rules:")
for cls, count in sorted(class_tally.items()):
    if count > 0:
        label = {'C1':'fixed point', 'C2':'periodic', 'C3':'chaotic',
                 'C4_candidate':'complex (Class 4 candidate)', 'none':'no rule exists'}
        print(f"    {cls} ({label[cls]}): {count}")

print()

# Key summary
complex_rate = class_tally.get('C4_candidate', 0) / max(has_vt_rule, 1)
print(f"  Fraction of perturbed orbits selecting a complex (C4-candidate) rule: {complex_rate:.0%}")
print()

if complex_rate > 0.7:
    verdict = "HIGH — perturbed orbits consistently select complex rules → Hypothesis A (structural)"
elif complex_rate > 0.3:
    verdict = "MODERATE — perturbed orbits often select complex rules → weak Hypothesis A"
else:
    verdict = "LOW — perturbed orbits often select non-complex rules → Hypothesis B (coincidental)"

print(f"  Verdict: {verdict}")
print()

# Unique rules selected across all perturbations
unique_selected = sorted(set(all_rules_found))
if unique_selected:
    print(f"  All rules selected across perturbations: {unique_selected}")
    print(f"  Rule 110 appears: {110 in unique_selected}")

results['analysis'] = {
    'total_perturbations': total_perturbed,
    'has_vt_rule': has_vt_rule,
    'class_tally': class_tally,
    'complex_rate': complex_rate,
    'verdict': verdict,
    'all_rules_found': unique_selected,
}


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
elapsed = time.time() - t0

print("=" * 70)
print("ROUND 3 SUMMARY — EPIC_067_R110")
print("=" * 70)
print()
print(f"  10 perturbed orbits tested (5 gen2 flips + 5 gen3 flips)")
print(f"  Orbits with a unique vacuum-transparent rule: {has_vt_rule}/10")
print(f"  Fraction selecting complex (C4-candidate) rules: {complex_rate:.0%}")
print(f"  Verdict: {verdict}")
print()
print(f"  Runtime: {elapsed:.1f}s")

results['summary'] = {
    'perturbations': total_perturbed,
    'with_vt_rule': has_vt_rule,
    'complex_rate': complex_rate,
    'verdict': verdict,
    'runtime_s': elapsed,
}

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

with open('./t_epic067_r3_results.json', 'w') as f:
    json.dump(results, f, indent=2, cls=NpEncoder)
print(f"  Results saved.")
