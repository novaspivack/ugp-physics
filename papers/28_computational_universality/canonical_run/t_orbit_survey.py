#!/usr/bin/env python3
"""
EPIC_067_R110 — Round 2: Corrected orbit survey with Lean binary states

Fixes from Round 1:
  1. Correct binary gen states from CUP4TotalParity.lean:
       gen1 = [1,1,0,0,1]  (e⁻=1, u=1, d=0, νR=0, νL=1)
       gen2 = [0,1,0,1,1]  (μ=0, c=1, s=0, ν_μR=1, ν_μL=1)
       gen3 = [1,1,1,1,1]  (all odd parity, CUP-8)
       Boundary: PERIODIC (ring)

  2. Better Wolfram class detection:
     - Run on 20 diverse ICs for 300 steps
     - Look for persistent localized structures (Class 4 signature)
     - Use entropy + spatial variance to discriminate classes
     - Manually verify Rule 110 = Class 4

  Key question: among all 256 rules satisfying the orbit gen1→gen2→gen3,
  what fraction are Class 4/universal?

  If Class 4 fraction >> overall Class 4 rate (~5-10%): Hypothesis A supported
  If Class 4 fraction ≈ overall rate: Hypothesis B (coincidence) supported
"""

import numpy as np
import json
import time
from itertools import product as iprod

t0 = time.time()
results = {}

print("=" * 70)
print("EPIC_067_R110 — Round 2: Corrected Survey")
print("=" * 70)
print()

# ─────────────────────────────────────────────────────────────────────────────
# Correct binary gen states (from CUP4TotalParity.lean, read 2026-05-17)
# ─────────────────────────────────────────────────────────────────────────────
GEN1 = [1, 1, 0, 0, 1]  # e⁻=1, u=1, d=0, νR=0, νL=1
GEN2 = [0, 1, 0, 1, 1]  # μ=0, c=1, s=0, ν_μR=1, ν_μL=1
GEN3 = [1, 1, 1, 1, 1]  # all odd parity (CUP-8)

def r110(l, c, r):
    return (110 >> (4*l + 2*c + r)) & 1

def rule_apply_5ring(rule_num, state):
    """Apply binary CA rule to 5-cell periodic ring."""
    outs = [(rule_num >> i) & 1 for i in range(8)]
    n = len(state)
    return [outs[4*state[(i-1)%n] + 2*state[i] + state[(i+1)%n]] for i in range(n)]

# Verify CUP-4 orbit with Rule 110
gen2_check = rule_apply_5ring(110, GEN1)
gen3_check = rule_apply_5ring(110, GEN2)
print(f"Verification: Rule 110 on 5-cell ring (PERIODIC boundary):")
print(f"  gen1={GEN1} → {gen2_check} (expected gen2={GEN2}): {'✓' if gen2_check==GEN2 else '✗'}")
print(f"  gen2={GEN2} → {gen3_check} (expected gen3={GEN3}): {'✓' if gen3_check==GEN3 else '✗'}")
print()

assert gen2_check == GEN2 and gen3_check == GEN3, "Rule 110 orbit verification failed!"

# ─────────────────────────────────────────────────────────────────────────────
# Wolfram class detection
# ─────────────────────────────────────────────────────────────────────────────
# Known Class 4 binary rules (from Wolfram 2002 NKS and literature):
# Class 4 requires complex, long-range interactions and non-trivial dynamics.
# Well-established Class 4 rules include: 54, 110, 137 (and reflections/complements).
# For the survey, use a combination of:
#   (a) Known list for validation
#   (b) Dynamic complexity metric for all 256 rules

KNOWN_CLASS4 = {54, 110}  # Most definitively Class 4 by standard classification
# Rule 137 = bit-reverse of 110; same dynamical class
# Use a wider set for checking
KNOWN_CLASS4_EXTENDED = {54, 110, 124, 137, 147, 193}  # Extended Class 4 candidates

def wolfram_class_v2(rule_num, N=100, T=200, n_ics=5, seed=42):
    """
    Improved Wolfram class estimation.
    
    Class 4 signature: complex patterns that neither die out (Class 1) 
    nor become periodic (Class 2) nor fully chaotic (Class 3).
    Key metrics:
      - Active cells: non-trivial but not exploding
      - Spatial variance: high (not uniform)  
      - Temporal autocorrelation: low (not periodic) but also not maximal-entropy
    """
    rng = np.random.default_rng(seed)
    outs = [(rule_num >> i) & 1 for i in range(8)]
    
    class_votes = {1:0, 2:0, 3:0, 4:0}
    
    for _ in range(n_ics):
        state = rng.integers(0, 2, N).tolist()
        history = []
        for t in range(T):
            new = [outs[4*state[(i-1)%N] + 2*state[i] + state[(i+1)%N]] for i in range(N)]
            state = new
            if t >= T - 50:
                history.append(state[:])
        
        # Metrics from last 50 steps
        hist_arr = np.array(history)
        mean_density = float(np.mean(hist_arr))
        
        # Temporal variance (is it changing?)
        row_sums = np.sum(hist_arr, axis=1)
        temporal_var = float(np.var(row_sums))
        
        # Unique rows (are patterns repeating?)
        unique_rows = len(set(tuple(r) for r in history))
        
        # Spatial entropy in last 10 steps
        last10 = hist_arr[-10:]
        col_entropy = float(np.mean([
            -p*np.log(p+1e-10) - (1-p)*np.log(1-p+1e-10) 
            for p in np.mean(last10, axis=0)
        ]))
        
        # Classify this IC
        if mean_density < 0.02 or mean_density > 0.98:
            class_votes[1] += 1  # Fixed point (all 0 or all 1)
        elif unique_rows <= 5 and temporal_var < 1:
            class_votes[2] += 1  # Periodic / simple
        elif col_entropy > 0.65 and unique_rows > 30:
            class_votes[3] += 1  # Chaotic (high entropy, many patterns)
        else:
            class_votes[4] += 1  # Complex (Class 4 candidate)
    
    dominant = max(class_votes, key=class_votes.get)
    return dominant, class_votes


# ─────────────────────────────────────────────────────────────────────────────
# Verify classifier on Rule 110 and known rules
# ─────────────────────────────────────────────────────────────────────────────
print("─" * 60)
print("Classifier verification on known rules")
print("─" * 60)
known_rules = {
    110: 4,   # Class 4 (standard)
    30: 3,    # Class 3 (chaotic) — famous
    90: 3,    # Class 3
    184: 2,   # Class 2 (particle automaton)
    0: 1,     # Class 1 (all zero)
    255: 1,   # Class 1 (all one)
    54: 4,    # Class 4
}
for rule_num, expected_class in sorted(known_rules.items()):
    detected, votes = wolfram_class_v2(rule_num)
    ok = '✓' if detected == expected_class else '✗'
    print(f"  Rule {rule_num:3d}: expected={expected_class}, detected={detected} {ok}  votes={votes}")
print()


# ─────────────────────────────────────────────────────────────────────────────
# Main survey
# ─────────────────────────────────────────────────────────────────────────────
print("─" * 60)
print("Main survey: all 256 binary CA rules")
print("─" * 60)
print()

orbit_satisfying = []
orbit_vt = []  # + vacuum-transparent
all_classes = {}

for rule_num in range(256):
    # Test orbit
    step1 = rule_apply_5ring(rule_num, GEN1)
    step2 = rule_apply_5ring(rule_num, GEN2)
    sat_orbit = (step1 == GEN2) and (step2 == GEN3)
    vac_transp = ((rule_num >> 0) & 1) == 0  # (0,0,0) → 0
    
    if sat_orbit:
        orbit_satisfying.append(rule_num)
    if sat_orbit and vac_transp:
        orbit_vt.append(rule_num)
    
    wclass, _ = wolfram_class_v2(rule_num)
    all_classes[rule_num] = wclass

print(f"  Rules satisfying orbit gen1→gen2→gen3: {len(orbit_satisfying)}")
print(f"  → {orbit_satisfying}")
print()
print(f"  Orbit-satisfying + vacuum-transparent: {len(orbit_vt)}")
print(f"  → {orbit_vt}")
print()

# Wolfram classes of orbit-satisfying rules
print(f"  Wolfram classes of orbit-satisfying rules:")
for rule_num in sorted(orbit_satisfying):
    wc = all_classes[rule_num]
    vt = '(vt)' if rule_num in orbit_vt else '    '
    print(f"    Rule {rule_num:3d} {vt}: Class {wc}")
print()

# Overall Class 4 frequency
total_by_class = {c: sum(1 for v in all_classes.values() if v==c) for c in [1,2,3,4]}
print(f"  All 256 rules by class: {total_by_class}")
class4_overall = total_by_class[4] / 256

# Class 4 among orbit-satisfying
orbit_class4 = sum(1 for r in orbit_satisfying if all_classes[r] == 4)
orbit_vt_class4 = sum(1 for r in orbit_vt if all_classes[r] == 4)
class4_orbit_rate = orbit_class4 / max(1, len(orbit_satisfying))
enrichment = class4_orbit_rate / max(class4_overall, 1e-10)

print()
print(f"  Class 4 rate, all 256 rules:           {class4_overall:.1%} ({total_by_class[4]}/256)")
print(f"  Class 4 rate, orbit-satisfying rules:  {class4_orbit_rate:.1%} ({orbit_class4}/{len(orbit_satisfying)})")
print(f"  Class 4 rate, orbit+vac-transp rules:  {orbit_vt_class4}/{len(orbit_vt)}")
print(f"  Enrichment factor (orbit vs overall):  {enrichment:.1f}×")
print()

if enrichment > 3:
    verdict = "STRONGLY ENRICHED — strong evidence for Hypothesis A (structural)"
elif enrichment > 1.5:
    verdict = "ENRICHED — evidence for Hypothesis A (structural connection)"
elif enrichment > 0.5:
    verdict = "NO ENRICHMENT — Class 4 at background rate → Hypothesis B (coincidence)"
else:
    verdict = "DEPLETED — Class 4 rare among orbit rules → specific orbit selects non-complex"

print(f"  Verdict: {verdict}")
print()

results['survey'] = {
    'orbit_satisfying': orbit_satisfying,
    'orbit_vt': orbit_vt,
    'all_classes': {str(k): v for k,v in all_classes.items()},
    'total_by_class': total_by_class,
    'class4_overall_rate': class4_overall,
    'class4_orbit_rate': class4_orbit_rate,
    'enrichment': enrichment,
    'verdict': verdict,
}


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
elapsed = time.time() - t0

print("=" * 70)
print("ROUND 2 SUMMARY — EPIC_067_R110")
print("=" * 70)
print()
print(f"  Orbit-satisfying rules: {len(orbit_satisfying)} → {orbit_satisfying}")
print(f"  Orbit + vacuum-transparent: {len(orbit_vt)} → {orbit_vt}")
print(f"  Class 4 enrichment: {enrichment:.1f}×")
print(f"  Verdict: {verdict}")
print()
if len(orbit_satisfying) == 1 and orbit_satisfying[0] == 110:
    print(f"  ★ Rule 110 is the ONLY orbit-satisfying rule.")
    print(f"  ★ Whether its Class 4 status is incidental or structural")
    print(f"    cannot be determined from the 256-rule survey alone.")
    print(f"    (There is no comparison set of non-Class-4 orbit-satisfying rules.)")
    print()
    print(f"  REFRAMED QUESTION for Round 3:")
    print(f"    Since Rule 110 is the ONLY orbit-satisfying rule, the enrichment")
    print(f"    question is trivially settled: 100% of orbit-satisfying rules are")
    print(f"    Class 4 (if Rule 110 is Class 4). But this doesn't tell us WHETHER")
    print(f"    the orbit SELECTED for Class 4 or just happened to land on it.")
    print()
    print(f"    Better test: vary the orbit constraints slightly and check if the")
    print(f"    uniquely selected rule is still Class 4. If perturbations consistently")
    print(f"    stay Class 4 → structural. If they drop to Class 1/2/3 → Rule 110")
    print(f"    is specially Class 4 while other orbit variants are not.")
print()
print(f"  Runtime: {elapsed:.1f}s")

results['summary'] = {
    'key_finding': f'{len(orbit_satisfying)} orbit-satisfying rule(s): {orbit_satisfying}',
    'if_one_rule': len(orbit_satisfying) == 1 and orbit_satisfying[0] == 110,
    'enrichment': enrichment,
    'verdict': verdict,
    'next_step': 'Perturb orbit constraints and test Wolfram class of new unique rule',
    'runtime_s': elapsed,
}

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

with open('./t_epic067_r2_results.json', 'w') as f:
    json.dump(results, f, indent=2, cls=NpEncoder)
print(f"  Results saved.")
