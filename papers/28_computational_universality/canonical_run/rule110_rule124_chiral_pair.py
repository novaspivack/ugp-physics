"""
Two-layer chiral CA: Rule 110 (right-mover) + Rule 124 (left-mover)

Tests whether the combined system has a Lorentz-symmetric light cone:
  v_R = +2/3  (from Rule 110 C2 glider, rightward)
  v_L = -2/3  (from Rule 124 mirror-C2 glider, leftward)

NAMING NOTE: "C2 glider" and "mirror-C2 glider" in this script refer to the
rightward/leftward causal fronts with |v| = 2/3 (period 3, |Δx| = 2 per
period). This is the convention used in P28/P36 scripts. In Cook (2004)
Figure 5, "C2" denotes a STATIONARY glider (period 7, Δx = 0); the causal
front at v = +2/3 is Cook's "A-glider". Throughout this codebase, "C2
glider" = Cook's A-type causal front (v = +2/3, period 3).

Also tests:
  - Are the two layers causally decoupled? (no cross-layer signal)

Rule 124 is the spatial mirror of Rule 110: RULE124(l,c,r) = RULE110(r,c,l).

Ether backgrounds (period-14):
  ETHER_110 = [1,1,1,1,1,0,0,0,1,0,0,1,1,0]  drifts LEFTWARD -4/step under Rule 110
  ETHER_124 = [0,1,1,0,0,1,0,0,0,1,1,1,1,1]  drifts RIGHTWARD +4/step under Rule 124
  (ETHER_124 = reversed(ETHER_110), the spatial mirror)

Method: base-vs-perturbed difference. Run a perturbed tape and an unperturbed base
simultaneously; track the difference. This cleanly isolates the causal signal without
depending on ether-drift formula conventions.

Perturbation phases are chosen from an exhaustive search over all 14 ether phases to
find those that nucleate persistent gliders (not all phases do). For Rule 110 on L=840:
  phase 1 (center=421) gives v_R = +2/3 exactly (period-3, 100% purity).
For Rule 124 on L=840:
  phase 3 (center=423) gives |v_L| = 2/3 exactly (period-3, 100% purity).
"""

import numpy as np

# Rule 110 truth table
RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}

# Rule 124 = spatial mirror of Rule 110: RULE124(l,c,r) = RULE110(r,c,l)
RULE124 = {
    (l, c, r): RULE110[(r, c, l)]
    for l in range(2) for c in range(2) for r in range(2)
}

# Verify Wolfram code
wolfram_110 = sum(RULE110[(n >> 2 & 1, n >> 1 & 1, n & 1)] << n for n in range(8))
wolfram_124 = sum(RULE124[(n >> 2 & 1, n >> 1 & 1, n & 1)] << n for n in range(8))
assert wolfram_110 == 110, f"Rule 110 Wolfram code error: {wolfram_110}"
assert wolfram_124 == 124, f"Rule 124 Wolfram code error: {wolfram_124}"
print(f"Rule 110 Wolfram code: {wolfram_110}  ✓")
print(f"Rule 124 Wolfram code: {wolfram_124}  ✓")

# Ether backgrounds
ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
ETHER_124 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]


def step_layer(tape, rule):
    """One step of a 1D CA with periodic boundary conditions."""
    L = len(tape)
    return [rule[(tape[(i - 1) % L], tape[i], tape[(i + 1) % L])] for i in range(L)]


def step_chiral(tape_110, tape_124):
    """One step of the two-layer chiral CA (layers evolve independently)."""
    return step_layer(tape_110, RULE110), step_layer(tape_124, RULE124)


def measure_glider_speed(base_tape, pert_tape, rule, center, T, direction='right'):
    """
    Measure glider speed using the base-vs-perturbed difference.
    direction='right': track rightward front (max index > center)
    direction='left':  track leftward front (min index < center)
    Returns (leads list of (t, lead), period-3 purity fraction).
    """
    leads = []
    for t in range(1, T + 1):
        base_tape = step_layer(base_tape, rule)
        pert_tape = step_layer(pert_tape, rule)
        diff = [base_tape[i] != pert_tape[i] for i in range(len(base_tape))]
        if direction == 'right':
            lead = max((i - center for i in range(center + 1, len(base_tape)) if diff[i]), default=0)
        else:
            lead = max((center - i for i in range(0, center) if diff[i]), default=0)
        leads.append(lead)
    # Period-3 purity: fraction of triplets where lead[t] - lead[t-3] == 2
    triplets = len(leads) - 3
    if triplets > 0:
        p3 = sum(1 for i in range(3, len(leads)) if leads[i] - leads[i - 3] == 2)
        purity = p3 / triplets
    else:
        purity = 0.0
    return leads, purity


# -------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------
L = 840     # = 60 * 14; exact ether period multiple for clean tiling
T = 300     # run time

# Perturbation centers chosen for glider nucleation (confirmed by ether-phase scan):
# Rule 110 phase 1 (center=421): v_R = +2/3 exactly
# Rule 124 phase 3 (center=423): |v_L| = 2/3 exactly
CENTER_110 = 421
CENTER_124 = 423

ether_110_full = [ETHER_110[i % 14] for i in range(L)]
ether_124_full = [ETHER_124[i % 14] for i in range(L)]

# -------------------------------------------------------------------
# Experiment 1: Layer 110 perturbed — measure rightward glider speed
# Also check: does Layer 124 pick up any cross-layer signal?
# -------------------------------------------------------------------
print("\n" + "=" * 60)
print("Experiment 1: Layer 110 perturbed (rightward signal)")
print("=" * 60)

# Two-layer base: both layers at ether (unperturbed)
base_110_1 = ether_110_full[:]
base_124_1 = ether_124_full[:]

# Two-layer perturbed: Layer 110 perturbed, Layer 124 unperturbed
pert_110_1 = ether_110_full[:]
pert_110_1[CENTER_110] ^= 1
pert_124_1 = ether_124_full[:]   # identical to base for Layer 124

right_leads = []
cross_124_counts = []

for t in range(1, T + 1):
    base_110_1, base_124_1 = step_chiral(base_110_1, base_124_1)
    pert_110_1, pert_124_1 = step_chiral(pert_110_1, pert_124_1)

    diff_110 = [base_110_1[i] != pert_110_1[i] for i in range(L)]
    diff_124 = [base_124_1[i] != pert_124_1[i] for i in range(L)]

    right_lead = max((i - CENTER_110 for i in range(CENTER_110 + 1, L) if diff_110[i]), default=0)
    cross = sum(diff_124)  # should be 0 (layers decoupled)
    right_leads.append(right_lead)
    cross_124_counts.append(cross)

last_lead = right_leads[-1]
v_R = last_lead / T
p3 = sum(1 for i in range(3, len(right_leads)) if right_leads[i] - right_leads[i - 3] == 2)
p3_frac = p3 / (len(right_leads) - 3)

print(f"  Final right_lead = {last_lead}  at T={T}")
print(f"  v_R = {v_R:.6f}  (expected: +2/3 = {2/3:.6f})")
print(f"  Error = {abs(v_R - 2/3):.6f}")
print(f"  Period-3 purity = {100*p3_frac:.1f}%  (C2 glider: 100%)")
print(f"  Cross-layer signal in Layer 124: max deviation count = {max(cross_124_counts)}")
print(f"  Layers DECOUPLED: {max(cross_124_counts) == 0}")

# -------------------------------------------------------------------
# Experiment 2: Layer 124 perturbed — measure leftward glider speed
# Also check: does Layer 110 pick up any cross-layer signal?
# -------------------------------------------------------------------
print("\n" + "=" * 60)
print("Experiment 2: Layer 124 perturbed (leftward signal)")
print("=" * 60)

base_110_2 = ether_110_full[:]
base_124_2 = ether_124_full[:]

pert_110_2 = ether_110_full[:]   # identical to base for Layer 110
pert_124_2 = ether_124_full[:]
pert_124_2[CENTER_124] ^= 1

left_leads = []
cross_110_counts = []

for t in range(1, T + 1):
    base_110_2, base_124_2 = step_chiral(base_110_2, base_124_2)
    pert_110_2, pert_124_2 = step_chiral(pert_110_2, pert_124_2)

    diff_110 = [base_110_2[i] != pert_110_2[i] for i in range(L)]
    diff_124 = [base_124_2[i] != pert_124_2[i] for i in range(L)]

    left_lead = max((CENTER_124 - i for i in range(0, CENTER_124) if diff_124[i]), default=0)
    cross = sum(diff_110)  # should be 0
    left_leads.append(left_lead)
    cross_110_counts.append(cross)

last_lead_L = left_leads[-1]
v_L_abs = last_lead_L / T
p3_L = sum(1 for i in range(3, len(left_leads)) if left_leads[i] - left_leads[i - 3] == 2)
p3_frac_L = p3_L / (len(left_leads) - 3)

print(f"  Final left_lead = {last_lead_L}  at T={T}")
print(f"  |v_L| = {v_L_abs:.6f}  (expected: 2/3 = {2/3:.6f})")
print(f"  v_L = -{v_L_abs:.6f}  (leftward)")
print(f"  Error = {abs(v_L_abs - 2/3):.6f}")
print(f"  Period-3 purity = {100*p3_frac_L:.1f}%  (mirror-C2 glider: 100%)")
print(f"  Cross-layer signal in Layer 110: max deviation count = {max(cross_110_counts)}")
print(f"  Layers DECOUPLED: {max(cross_110_counts) == 0}")

# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
print("\n" + "=" * 60)
print("SUMMARY: Two-layer chiral CA — Lorentz symmetry test")
print("=" * 60)
print(f"  v_R (Rule 110 C2 glider, rightward) = +{v_R:.6f}")
print(f"  v_L (Rule 124 mirror-C2, leftward)  = -{v_L_abs:.6f}")
print(f"  |v_R| = {v_R:.6f}")
print(f"  |v_L| = {v_L_abs:.6f}")
symmetric = abs(v_R - v_L_abs) < 0.002
decoupled = max(cross_124_counts) == 0 and max(cross_110_counts) == 0
print(f"  |v_R| = |v_L| (within 0.002)? {symmetric}")
print(f"  Layers causally decoupled?       {decoupled}")
print()
if symmetric and decoupled:
    print("  *** CONFIRMED: The chiral pair {Rule 110, Rule 124} has a")
    print(f"  Lorentz-symmetric light cone with c = 2/3 in both directions.")
    print(f"  The two layers evolve independently (no coupling).")
    print(f"  Period-3 C2 glider purity: {100*p3_frac:.1f}% (Rule 110) / {100*p3_frac_L:.1f}% (Rule 124)")
elif not symmetric:
    print(f"  ASYMMETRIC: |v_R| - |v_L| = {abs(v_R - v_L_abs):.6f}")
else:
    print(f"  Cross-layer coupling detected.")

# -------------------------------------------------------------------
# Velocity table at intermediate times
# -------------------------------------------------------------------
print("\n--- Rightward lead (Rule 110) and leftward lead (Rule 124) vs. time ---")
print(f"{'T':>5} | {'right_lead':>10} | {'v_R_cum':>8} | {'left_lead':>9} | {'|v_L|_cum':>9}")
print("-" * 50)
for t_idx in [29, 59, 89, 119, 149, 179, 209, 239, 269, 299]:
    t = t_idx + 1
    rl = right_leads[t_idx]
    ll = left_leads[t_idx]
    print(f"{t:5d} | {rl:10d} | {rl/t:8.6f} | {ll:9d} | {ll/t:9.6f}")
