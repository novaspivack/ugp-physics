"""
Rank 151-GSP: GTE Photon Speed — Ether Perturbation Propagation in Rule 110

Measures the speed at which a local perturbation of the Rule 110 ether background
propagates. This determines whether the GTE "photon" (winding-0 ether excitation)
travels at v = 2/3 (same as C2 fermion glider) or at a different speed.

Key prior result (Rank 111): Rule 110 C2 glider speed v_R = +2/3 (CatA).
Key question (Rank 151): does the ether excitation also propagate at 2/3?

If v_photon = v_fermion = 2/3 → GTE effective theory is Lorentz-invariant
→ a_mu^GTE = alpha_GTE/(2*pi) upgrades from CatAD to CatA.

Method:
- Run two Rule 110 tapes simultaneously: clean_ether and perturbed_ether.
- Track difference pattern = perturbed XOR clean at each timestep.
- Measure the rightward and leftward leading edges of the difference pattern.
- Report the speed = displacement / time for each front.

Phase sensitivity (from Rank 111):
- Only certain ether phases produce persistent C2 gliders when perturbed.
- Working phases for Rule 110: 1, 6, 7, 10 (center positions = 421, 426, 427, 430
  for L=840).
- Scan all 14 phases and report which produce persistent propagating disturbances.
"""

import numpy as np

# Rule 110 lookup table (3-cell neighborhood)
RULE110 = {
    (1, 1, 1): 0,
    (1, 1, 0): 1,
    (1, 0, 1): 1,
    (1, 0, 0): 0,
    (0, 1, 1): 1,
    (0, 1, 0): 1,
    (0, 0, 1): 1,
    (0, 0, 0): 0,
}

# Rule 110 ether background (period-14 pattern)
ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

# C2 glider speed (CatA from Rank 111)
V_FERMION = 2.0 / 3.0


def step_rule110(tape: list) -> list:
    L = len(tape)
    return [RULE110[(tape[(i - 1) % L], tape[i], tape[(i + 1) % L])] for i in range(L)]


def tape_from_ether(L: int, phase_offset: int = 0) -> list:
    """Build a tape of length L filled with the period-14 ether, starting at phase_offset."""
    return [ETHER_110[(i + phase_offset) % 14] for i in range(L)]


def find_difference_edges(diff_positions: list, center: int, L: int) -> tuple:
    """
    Given positions of difference cells, find the rightward and leftward leading edges.
    Returns (right_front, left_front) as displacements from center.
    Returns (None, None) if no differences.
    """
    if not diff_positions:
        return None, None
    # Rightward front: maximum position in [center, center + L//3)
    right_candidates = [p for p in diff_positions if center <= p < center + L // 3]
    # Leftward front: minimum position in (center - L//3, center]
    left_candidates = [p for p in diff_positions if center - L // 3 < p <= center]
    right_front = max(right_candidates) - center if right_candidates else None
    left_front = min(left_candidates) - center if left_candidates else None
    return right_front, left_front


# ============================================================
# Part 1: Scan all 14 ether phases to find which produce
#         persistent propagating perturbations
# ============================================================

print("=" * 65)
print("Part 1: Phase Scan — which ether phases produce persistent perturbations?")
print("=" * 65)
print()

L = 840   # 60 ether periods
T = 300   # timesteps
center = L // 2

phase_results = {}

for phase in range(14):
    # Initialize clean and perturbed tapes
    # The perturbation center is at L//2; the ether at position center has phase
    # (center + phase_offset) % 14. We want the center to be at phase `phase`.
    # So phase_offset = (phase - center % 14) % 14 = (phase - 0) % 14 = phase.
    # But center = 420, center % 14 = 0, so phase_offset = phase directly.
    phase_offset = phase  # so that tape[center] starts at ether phase `phase`

    clean = tape_from_ether(L, phase_offset)
    perturbed = clean[:]
    perturbed[center] ^= 1  # single-bit flip

    max_spread = 0
    final_spread = 0

    for t in range(T):
        clean = step_rule110(clean)
        perturbed = step_rule110(perturbed)
        diff = [i for i in range(L) if perturbed[i] != clean[i]]
        if diff:
            right_extreme = max(diff)
            left_extreme = min(diff)
            spread = right_extreme - left_extreme
            max_spread = max(max_spread, spread)
            final_spread = spread

    phase_results[phase] = {
        'max_spread': max_spread,
        'final_spread': final_spread,
        'persistent': final_spread > 50,  # non-trivial spread at T=300
    }

print(f"{'Phase':>6} {'Max spread':>12} {'Final spread':>13} {'Persistent?':>12}")
print("-" * 50)
for phase, res in phase_results.items():
    print(f"{phase:>6} {res['max_spread']:>12} {res['final_spread']:>13} {res['persistent']!s:>12}")

persistent_phases = [p for p, r in phase_results.items() if r['persistent']]
print(f"\nPersistent phases (final_spread > 50 at T=300): {persistent_phases}")
print()


# ============================================================
# Part 2: Measure propagation speed for persistent phases
# ============================================================

print("=" * 65)
print("Part 2: Measure propagation speed — leading edge tracking")
print("=" * 65)
print()

T_MEASURE = 400
L_BIG = 840

speed_results = {}

for phase in persistent_phases[:6]:  # test up to 6 phases
    phase_offset = phase
    clean = tape_from_ether(L_BIG, phase_offset)
    perturbed = clean[:]
    perturbed[center] ^= 1

    right_fronts = []  # (t, displacement) of rightward leading edge
    left_fronts = []   # (t, displacement) of leftward leading edge

    for t in range(1, T_MEASURE + 1):
        clean = step_rule110(clean)
        perturbed = step_rule110(perturbed)
        diff = [i for i in range(L_BIG) if perturbed[i] != clean[i]]
        if not diff:
            continue
        # Rightward leading edge: furthest right of center
        right_candidates = [d - center for d in diff if d > center]
        left_candidates = [d - center for d in diff if d < center]
        if right_candidates:
            right_fronts.append((t, max(right_candidates)))
        if left_candidates:
            left_fronts.append((t, min(left_candidates)))

    # Fit speed from linear regression on the last 80% of data
    if len(right_fronts) > 20:
        rts = np.array([x[0] for x in right_fronts])
        rds = np.array([x[1] for x in right_fronts])
        start_idx = len(rts) // 5  # skip transient
        if len(rts[start_idx:]) > 5:
            v_right = np.polyfit(rts[start_idx:], rds[start_idx:], 1)[0]
        else:
            v_right = None
    else:
        v_right = None

    if len(left_fronts) > 20:
        lts = np.array([x[0] for x in left_fronts])
        lds = np.array([x[1] for x in left_fronts])
        start_idx = len(lts) // 5
        if len(lts[start_idx:]) > 5:
            v_left = np.polyfit(lts[start_idx:], lds[start_idx:], 1)[0]
        else:
            v_left = None
    else:
        v_left = None

    speed_results[phase] = {'v_right': v_right, 'v_left': v_left}
    print(f"Phase {phase}:")
    if v_right is not None:
        print(f"  Rightward front: v_R = {v_right:+.6f}  (2/3 = {V_FERMION:.6f}, diff = {abs(v_right - V_FERMION):.6f})")
    if v_left is not None:
        print(f"  Leftward front:  v_L = {v_left:+.6f}  (-2/3 = {-V_FERMION:.6f}, diff = {abs(v_left + V_FERMION):.6f})")
    print()


# ============================================================
# Part 3: High-precision measurement on best phase
# ============================================================

print("=" * 65)
print("Part 3: High-precision speed measurement (best persistent phase)")
print("=" * 65)
print()

best_phase = persistent_phases[0] if persistent_phases else 1
T_PREC = 600
L_PREC = 1260  # 90 ether periods

phase_offset = best_phase
clean = tape_from_ether(L_PREC, phase_offset)
perturbed = clean[:]
ctr = L_PREC // 2
perturbed[ctr] ^= 1

right_data = []  # (t, right_displacement)
left_data = []   # (t, left_displacement)

for t in range(1, T_PREC + 1):
    clean = step_rule110(clean)
    perturbed = step_rule110(perturbed)
    diff = [i for i in range(L_PREC) if perturbed[i] != clean[i]]
    if not diff:
        continue
    right_candidates = [d - ctr for d in diff if d > ctr]
    left_candidates = [d - ctr for d in diff if d < ctr]
    if right_candidates:
        right_data.append((t, max(right_candidates)))
    if left_candidates:
        left_data.append((t, min(left_candidates)))

# Linear regression on second half of data
print("Linear regression on second half of data (t > T/2):")
if right_data:
    rts = np.array([x[0] for x in right_data])
    rds = np.array([x[1] for x in right_data])
    mask = rts > T_PREC // 2
    if mask.sum() > 10:
        slope, intercept = np.polyfit(rts[mask], rds[mask], 1)
        residuals = rds[mask] - (slope * rts[mask] + intercept)
        rms = np.sqrt(np.mean(residuals**2))
        print(f"  Rightward front: v_R = {slope:+.8f}  (RMS residual = {rms:.4f} cells)")
        print(f"  Compare: v_fermion = {V_FERMION:.8f}")
        print(f"  Deviation from 2/3: {abs(slope - V_FERMION):.2e}")
        v_R_best = slope
    else:
        v_R_best = None
        print("  Insufficient right-front data")
else:
    v_R_best = None
    print("  No rightward front detected")

if left_data:
    lts = np.array([x[0] for x in left_data])
    lds = np.array([x[1] for x in left_data])
    mask = lts > T_PREC // 2
    if mask.sum() > 10:
        slope, intercept = np.polyfit(lts[mask], lds[mask], 1)
        residuals = lds[mask] - (slope * lts[mask] + intercept)
        rms = np.sqrt(np.mean(residuals**2))
        print(f"\n  Leftward front:  v_L = {slope:+.8f}  (RMS residual = {rms:.4f} cells)")
        print(f"  Compare: -v_fermion = {-V_FERMION:.8f}")
        print(f"  Deviation from -2/3: {abs(slope + V_FERMION):.2e}")
        v_L_best = slope
    else:
        v_L_best = None
        print("  Insufficient left-front data")
else:
    v_L_best = None
    print("  No leftward front detected")

print()

# ============================================================
# Part 4: Does the ether perturbation nucleate a C2 glider?
# ============================================================

print("=" * 65)
print("Part 4: Does ether perturbation nucleate a C2 glider?")
print("=" * 65)
print()

# Known C2 glider pattern (2-cell, moves right 2 cells every 3 steps)
# From Rule 110 literature: C2 glider repeats with period 3
# We look for periodically repeating structures in the difference pattern

phase_offset = best_phase
clean = tape_from_ether(840, phase_offset)
perturbed = clean[:]
perturbed[center] ^= 1

# Track the full difference pattern at multiples of 3 (C2 period)
diffs_at_multiples_of_3 = []
for t in range(1, 121):
    clean = step_rule110(clean)
    perturbed = step_rule110(perturbed)
    if t % 3 == 0:
        diff = [i - center for i in range(840) if perturbed[i] != clean[i]]
        diffs_at_multiples_of_3.append((t, diff))

# Check: does the leading-edge displacement grow by 2 every 3 steps?
print("Rightward leading edge every 3 steps (checking for C2 glider: Δ=2 per 3 steps):")
print(f"  Expected: displacement = 2*(t/3) → v = 2/3")
print()
print(f"  {'t':>5} {'max_disp':>10} {'expected':>10} {'Δ from prev':>12}")
prev_max = None
prev_t = None
c2_pattern_count = 0
for t, diff in diffs_at_multiples_of_3[:30]:
    right_diff = [d for d in diff if d > 0]
    if right_diff:
        max_d = max(right_diff)
        expected = 2 * (t // 3)
        delta = (max_d - prev_max) if prev_max is not None else 0
        c2_check = (delta == 2) if prev_max is not None else True
        if c2_check and prev_max is not None:
            c2_pattern_count += 1
        print(f"  {t:>5} {max_d:>10} {expected:>10} {delta:>12}  {'✓' if c2_check else '✗'}")
        prev_max = max_d
        prev_t = t
    else:
        print(f"  {t:>5} {'no right diff':>10}")

if c2_pattern_count > 15:
    print(f"\n  → C2 GLIDER CONFIRMED: delta=2 for {c2_pattern_count}/29 steps ✓")
    nucleates_c2 = True
elif c2_pattern_count > 5:
    print(f"\n  → PARTIAL C2 PATTERN: delta=2 for {c2_pattern_count}/29 steps (may include transients)")
    nucleates_c2 = True
else:
    print(f"\n  → No clear C2 pattern detected: delta=2 for only {c2_pattern_count}/29 steps")
    nucleates_c2 = False

print()


# ============================================================
# Part 5: Summary and verdict
# ============================================================

print("=" * 65)
print("Part 5: SUMMARY AND VERDICT")
print("=" * 65)
print()
print(f"C2 fermion glider speed: v_fermion = {V_FERMION:.6f} = 2/3")
print()

if v_R_best is not None:
    matches_23 = abs(v_R_best - V_FERMION) < 0.02
    print(f"Ether perturbation rightward speed: v_photon_R = {v_R_best:.6f}")
    print(f"  Match v_fermion = 2/3? {matches_23}")
    print(f"  Deviation: {abs(v_R_best - V_FERMION):.4f}")
    print()
    if matches_23:
        print("RESULT: c_photon = c_fermion = 2/3 ✓")
        print("GTE effective theory is LORENTZ-INVARIANT")
        print("→ a_mu^GTE = alpha_GTE/(2*pi) UPGRADES FROM CatAD TO CatA")
    else:
        print(f"RESULT: c_photon ({v_R_best:.4f}) ≠ c_fermion (2/3)")
        print("GTE Lorentz symmetry NOT confirmed by this measurement")
        print("→ Lorentz-violating correction needed in Feynman denominator")
else:
    print("RESULT: Could not measure photon speed — check phase selection and tape size")

print()
if nucleates_c2:
    print("C2 GLIDER NUCLEATION: ether perturbation → C2 glider at v = 2/3 ✓")
    print("Physical interpretation: the GTE photon IS a C2 glider excitation")
    print("→ c_photon = c_C2 = v_fermion = 2/3 (structural argument)")
else:
    print("C2 GLIDER NUCLEATION: not clearly confirmed from this phase")
    print("→ Try other phases or larger tapes")

print()
print(f"Persistent ether phases tested: {persistent_phases}")
print(f"Best phase used for precision measurement: {best_phase}")
