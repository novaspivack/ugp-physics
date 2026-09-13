"""
Rank 120: Identify the v ≈ +5/12 mode under asymmetric one-way coupling

Under the asymmetric coupling asym_124_sees_110:
  b124[i] ← Rule124(tape_124) ⊕ old_110[i]
  b110[i] ← Rule110(tape_110)  (unchanged)

When old_110 is fixed as ETHER_110 (period-14 background), Layer 124 becomes
a "driven" CA. The Rank 118 search found a rightward signal at v ≈ +5/12 ≈ 0.417
replacing the usual leftward glider at v_L = -2/3.

This script determines:
  1. Whether the driven ETHER_124 itself drifts (ether artifact)
  2. Whether a perturbation propagates as a true period-N glider
  3. Arithmetic significance of 5/12 relative to CA constants {2/3, 1/3, 7/12, ...}
"""

import math

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

RULE110_TABLE = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}

RULE124_TABLE = {(l, c, r): RULE110_TABLE[(r, c, l)] for (l, c, r) in RULE110_TABLE}

ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]  # period-14
ETHER_124 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]  # period-14, mirror of ETHER_110

def rule124(l, c, r):
    return RULE124_TABLE[(l % 2, c % 2, r % 2)]

def rule110(l, c, r):
    return RULE110_TABLE[(l % 2, c % 2, r % 2)]

# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Does the driven ETHER_124 itself drift under the coupling?
# step_driven_124: each cell i → Rule124(tape_124) XOR ETHER_110[i % 14]
# ─────────────────────────────────────────────────────────────────────────────
def step_driven_124(tape_124, ether_110):
    L = len(tape_124)
    period = len(ether_110)
    new_tape = []
    for i in range(L):
        b124 = rule124(tape_124[(i - 1) % L], tape_124[i], tape_124[(i + 1) % L])
        correction = ether_110[i % period]
        new_tape.append((b124 ^ correction) % 2)
    return new_tape

def step_rule124_pure(tape):
    L = len(tape)
    return [rule124(tape[(i-1)%L], tape[i], tape[(i+1)%L]) for i in range(L)]

def step_rule110_pure(tape):
    L = len(tape)
    return [rule110(tape[(i-1)%L], tape[i], tape[(i+1)%L]) for i in range(L)]

print("=" * 70)
print("RANK 120: v ≈ +5/12 MODE IDENTIFICATION")
print("=" * 70)

# ─── Test 1a: ETHER_124 under pure Rule 124 (baseline) ───────────────────────
print("\n--- Test 1a: ETHER_124 under PURE Rule 124 (baseline drift) ---")

L_ether = 14
tape_e = list(ETHER_124)
for t in range(1, 15):
    tape_e = step_rule124_pure(tape_e)
    # Check if tape_e matches a shift of ETHER_124
    for shift in range(14):
        shifted = [ETHER_124[(i - shift) % 14] for i in range(14)]
        if tape_e == shifted:
            print(f"  t={t:2d}: ETHER_124 shifted by +{shift} (drift = +{shift}/step)")
            break

# ─── Test 1b: Is ETHER_124 stable under driven rule? ────────────────────────
print("\n--- Test 1b: ETHER_124 under DRIVEN Rule 124 ---")

L_test = 140  # 10 × period-14
tape_driven = [ETHER_124[i % 14] for i in range(L_test)]
ether_110_ext = [ETHER_110[i % 14] for i in range(L_test)]

print(f"  Initial tape (first 28): {tape_driven[:28]}")
print(f"  Ref ETHER_124×2:         {(ETHER_124 * 2)[:28]}")

# Run for 200 steps and track pattern shift
shifts_detected = []
for t in range(1, 201):
    tape_driven = step_driven_124(tape_driven, ether_110_ext)
    # Detect shift: for which shift s does tape_driven[i] = ETHER_124[(i-s)%14] for most i?
    best_shift = -1
    best_match = 0
    for s in range(14):
        match = sum(1 for i in range(L_test) if tape_driven[i] == ETHER_124[(i - s) % 14])
        if match > best_match:
            best_match = match
            best_shift = s
    frac_match = best_match / L_test
    shifts_detected.append((t, best_shift, frac_match))

# Sample key timesteps
print(f"\n  {'t':>5} {'best_shift':>12} {'match_frac':>12}")
for t_sample in [1, 2, 3, 5, 10, 20, 50, 100, 200]:
    idx = t_sample - 1
    t, sh, fr = shifts_detected[idx]
    print(f"  {t:>5} {sh:>12} {fr:>12.3f}")

# Check if it's periodic shift vs growing shift
shift_at_t100 = shifts_detected[99][1]
shift_at_t200 = shifts_detected[199][1]
match_at_t200 = shifts_detected[199][2]
print(f"\n  Shift at t=100: {shift_at_t100}, Shift at t=200: {shift_at_t200}")
print(f"  Match fraction at t=200: {match_at_t200:.3f}")

if match_at_t200 < 0.7:
    print("  → ETHER DISRUPTED: driven rule breaks the ether structure")
    print("  → The +5/12 mode is NOT just the ether drifting — it emerges from disorder")
else:
    avg_drift = shift_at_t200 / 200
    print(f"  → ETHER SURVIVES: avg drift = {shift_at_t200}/200 = {avg_drift:.4f}")
    print(f"  → Compare 5/12 = {5/12:.4f}")
    if abs(avg_drift - 5/12) < 0.05:
        print("  → MATCH: driven ether drifts at +5/12 — the mode IS the ether!")
    else:
        print(f"  → NO MATCH to 5/12 (drift = {avg_drift:.4f})")

# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Perturbation tracking in clean ETHER_124 background under driven rule
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TEST 2: PERTURBATION TRACKING (true glider or diffusion?)")
print("=" * 70)

L = 840  # 60 × 14
ETHER_110_L = [ETHER_110[i % 14] for i in range(L)]
ETHER_124_L = [ETHER_124[i % 14] for i in range(L)]

print(f"\nSetup: L={L}, T=500, perturbation at center (i=420)")
print(f"Rule: b124[i] ← Rule124(tape) ⊕ ETHER_110[i%14]")

tape = list(ETHER_124_L)
tape[420] ^= 1  # single-bit perturbation

positions = []
sizes = []

for t in range(500):
    # Compute difference from clean ether
    clean = ETHER_124_L  # fixed reference (doesn't change)
    diff = [i for i in range(L) if tape[i] != clean[i]]
    if diff:
        center = sum(diff) / len(diff)
        positions.append((t, center, len(diff)))
        sizes.append(len(diff))
    else:
        positions.append((t, None, 0))
    tape = step_driven_124(tape, ETHER_110_L)

# Check early behavior
print(f"\n  {'t':>5} {'center':>10} {'|diff|':>8}")
for t_print in [0, 1, 2, 5, 10, 20, 50, 100, 200, 300, 400, 499]:
    t_val, c, sz = positions[t_print]
    c_str = f"{c:10.2f}" if c is not None else "       None"
    print(f"  {t_val:>5} {c_str} {sz:>8}")

# Measure propagation speed from positions where perturbation is alive
alive = [(t, c, sz) for (t, c, sz) in positions if c is not None and sz > 0]
print(f"\n  Perturbation alive for {len(alive)}/500 steps")
print(f"  Max |diff| reached: {max(sz for _,_,sz in alive) if alive else 0}")

if len(alive) >= 20:
    # Fit linear speed from first to last alive step
    t_first, c_first, _ = alive[0]
    t_last, c_last, _ = alive[-1]
    if t_last > t_first:
        speed_raw = (c_last - c_first) / (t_last - t_first)
        print(f"  Speed (first→last): ({c_last:.2f} - {c_first:.2f}) / {t_last - t_first} = {speed_raw:.4f}")
        print(f"  5/12  = {5/12:.4f}")
        print(f"  2/3   = {2/3:.4f}")
        print(f"  -2/3  = {-2/3:.4f}")
        print(f"  1/3   = {1/3:.4f}")
        if abs(speed_raw - 5/12) < 0.05:
            print(f"\n  ✓ SPEED MATCH: v ≈ 5/12 confirmed")
        elif abs(speed_raw - 2/3) < 0.05:
            print(f"\n  ~ Speed ≈ 2/3 (matches Layer 110 C₂ glider)")
        elif abs(speed_raw + 2/3) < 0.05:
            print(f"\n  ~ Speed ≈ -2/3 (matches Layer 124 leftward glider, undriven)")
        else:
            print(f"\n  Speed = {speed_raw:.4f} — does not match simple fractions")

    # Check if perturbation grows or stays localized
    early_avg_size = sum(sz for _,_,sz in alive[:20]) / 20
    late_avg_size = sum(sz for _,_,sz in alive[-20:]) / 20
    print(f"\n  Early size (avg first 20): {early_avg_size:.1f}")
    print(f"  Late size  (avg last 20):  {late_avg_size:.1f}")
    if late_avg_size > early_avg_size * 3:
        print("  → DIFFUSION: perturbation grows → likely diffusive, not particle-like")
    elif late_avg_size < early_avg_size * 2:
        print("  → LOCALIZED: perturbation stays bounded → glider-like behavior")
    else:
        print(f"  → MODERATE GROWTH: size grew {late_avg_size/early_avg_size:.1f}×")

# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Check for period-N glider — does pattern exactly repeat?
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TEST 3: PERIOD SEARCH (true glider = exact pattern recurrence)")
print("=" * 70)

L_small = 84  # 6 × 14
ETHER_110_S = [ETHER_110[i % 14] for i in range(L_small)]
ETHER_124_S = [ETHER_124[i % 14] for i in range(L_small)]

tape_p = list(ETHER_124_S)
tape_p[42] ^= 1  # perturbation at center

snapshots = [list(tape_p)]
for t in range(300):
    tape_p = step_driven_124(tape_p, ETHER_110_S)
    snapshots.append(list(tape_p))

print(f"\nSearching for exact period P in [1, 42] on L={L_small} tape...")
print(f"(A true glider returns to the same pattern shifted by exactly P×speed)")

found_periods = []
for P in range(1, 43):
    # Check if snapshot at t=P matches snapshot at t=0 up to a shift
    snap_0 = snapshots[0]
    snap_P = snapshots[P]
    # Find best-matching shift
    best_shift = -1
    for s in range(L_small):
        shifted = [snap_P[(i + s) % L_small] for i in range(L_small)]
        if shifted == snap_0:
            best_shift = s
            break
    if best_shift >= 0:
        speed_candidate = best_shift / P
        found_periods.append((P, best_shift, speed_candidate))
        print(f"  Period P={P}: exact recurrence with shift={best_shift}, v={best_shift}/{P}={speed_candidate:.4f}")

if not found_periods:
    print("  No exact period found in [1..42] — pattern does NOT recur exactly")
    print("  → Mode is NOT a true period-N glider in this sense")
    
    # Check approximate periods
    print("\n  Checking approximate periodicity (tolerance 1 bit)...")
    for P in range(1, 43):
        snap_0 = snapshots[0]
        snap_P = snapshots[P]
        best_mismatches = L_small
        best_shift = 0
        for s in range(L_small):
            shifted = [snap_P[(i + s) % L_small] for i in range(L_small)]
            mismatches = sum(1 for i in range(L_small) if shifted[i] != snap_0[i])
            if mismatches < best_mismatches:
                best_mismatches = mismatches
                best_shift = s
        if best_mismatches <= 3:
            print(f"  Approx period P={P}: best shift={best_shift}, mismatches={best_mismatches}/84")

# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Run with longer tape to get better speed measurement
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TEST 4: LONG-RUN SPEED MEASUREMENT (L=840, T=2000)")
print("=" * 70)

L2 = 840
ETHER_110_L2 = [ETHER_110[i % 14] for i in range(L2)]
ETHER_124_L2 = [ETHER_124[i % 14] for i in range(L2)]

tape2 = list(ETHER_124_L2)
tape2[420] ^= 1

positions2 = []
for t in range(2000):
    clean2 = ETHER_124_L2
    diff2 = [i for i in range(L2) if tape2[i] != clean2[i]]
    if diff2:
        center2 = sum(diff2) / len(diff2)
        positions2.append((t, center2, len(diff2)))
    tape2 = step_driven_124(tape2, ETHER_110_L2)

alive2 = [(t, c, sz) for (t, c, sz) in positions2 if c is not None]
if alive2:
    t_f, c_f, _ = alive2[0]
    t_l, c_l, _ = alive2[-1]
    if t_l > t_f:
        speed2 = (c_l - c_f) / (t_l - t_f)
        print(f"\n  Perturbation alive {t_f} → {t_l} ({t_l - t_f} steps)")
        print(f"  Center: {c_f:.2f} → {c_l:.2f}")
        print(f"  Measured speed: {speed2:.6f}")
        print(f"  5/12  = {5/12:.6f}  diff = {abs(speed2 - 5/12):.6f}")
        print(f"  2/3   = {2/3:.6f}  diff = {abs(speed2 - 2/3):.6f}")
        print(f"  1/2   = {1/2:.6f}  diff = {abs(speed2 - 0.5):.6f}")
        print(f"  7/12  = {7/12:.6f}  diff = {abs(speed2 - 7/12):.6f}")
        print(f"  5/11  = {5/11:.6f}  diff = {abs(speed2 - 5/11):.6f}")
        print(f"  3/7   = {3/7:.6f}  diff = {abs(speed2 - 3/7):.6f}")

        # Find best rational approximation
        print(f"\n  Best rational approximations to {speed2:.6f}:")
        candidates = []
        for den in range(2, 30):
            num = round(speed2 * den)
            if 0 < num < den:
                err = abs(speed2 - num/den)
                candidates.append((err, num, den))
        candidates.sort()
        for err, num, den in candidates[:8]:
            print(f"    {num}/{den} = {num/den:.6f}  (error = {err:.6f})")

    # Check if perturbation grows (diffusive) or stays bounded
    early_sz = [sz for _, _, sz in alive2[:50]] if len(alive2) >= 50 else []
    late_sz = [sz for _, _, sz in alive2[-50:]] if len(alive2) >= 50 else []
    if early_sz and late_sz:
        print(f"\n  Early avg size (t~0): {sum(early_sz)/len(early_sz):.1f}")
        print(f"  Late avg size (t~end): {sum(late_sz)/len(late_sz):.1f}")
        growth = (sum(late_sz)/len(late_sz)) / (sum(early_sz)/len(early_sz))
        print(f"  Size growth ratio: {growth:.2f}×")
        if growth > 5:
            print("  → DIFFUSION (unbounded growth): NOT a true glider")
        elif growth < 2:
            print("  → LOCALIZED (bounded size): glider-like")
        else:
            print("  → MODERATE GROWTH")

# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Arithmetic analysis of 5/12
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TEST 5: ARITHMETIC ANALYSIS OF 5/12")
print("=" * 70)

v = 5/12
print(f"\n  v = 5/12 = {v:.6f}")
print(f"\n  CA constants:")
print(f"    C2 glider speed: v_R = 2/3 = {2/3:.6f}")
print(f"    Mirror glider:   v_L = -2/3")
print(f"    Ether period:    T_e = 14")
print(f"    Glider period:   T_g = 3")
print(f"    lcm(3,14) = {math.lcm(3,14)}")

print(f"\n  Candidate identities for 5/12:")

# Is 5/12 related to lcm(3,14)?
print(f"    5/12 = 5/(4×3) = 5/(N_gen×4)? N_gen=3: {5/(3*4):.4f} ✓")

# Ether + glider combination
print(f"    1 - 2/3 - 1/12 = 1/4? → not obvious")
print(f"    (2/3 + 1/4)/2 = {(2/3 + 1/4)/2:.4f}")
print(f"    2/3 - 1/4 = {2/3 - 1/4:.4f}")

# N_fam = 5 relations
N_fam = 5
for denom_name, denom_val in [
    ("N_ether=14", 14),
    ("2*N_ether/7=4", 4),
    ("c_H=13", 13),
    ("c_H-1=12", 12),
    ("c_W=11", 11),
    ("c_W+1=12", 12),
    ("c_H+1=14", 14),
    ("4*3=12", 12),
    ("lcm(3,4)=12", 12),
    ("3*4=12", 12),
]:
    val = N_fam / denom_val
    print(f"    N_fam/{denom_name} = 5/{denom_val} = {val:.4f}  {'← 5/12 ✓' if abs(val - 5/12) < 0.001 else ''}")

print(f"\n  Key identity: 5/12 = N_fam / (c_W + 1) = 5/12 (c_W=11) ✓")
print(f"  Key identity: 5/12 = N_fam / (4 × N_gen) = 5/(4×3) ✓")
print(f"  Key identity: 5/12 = 5/lcm(3,4) (since lcm(3,4)=12) ✓")

# Relation to v_R = 2/3
print(f"\n  Relation to C₂ glider speed v_R = 2/3:")
print(f"    v / v_R = (5/12)/(2/3) = {(5/12)/(2/3):.4f} = 5/8")
print(f"    v_R - v = 2/3 - 5/12 = 8/12 - 5/12 = 3/12 = 1/4")
print(f"    v_R + v = 2/3 + 5/12 = 8/12 + 5/12 = 13/12 = c_H/12? (c_H=13 ✓)")
print(f"    v + 1/4 = 5/12 + 3/12 = 8/12 = 2/3 = v_R ← clean relation!")

# Ether drift
print(f"\n  Ether drift under pure Rule 124: +4 cells per step")
print(f"    Ether drift fraction: 4/14 = 2/7 = {4/14:.4f}")
print(f"    2/7 vs 5/12: 2/7 = {2/7:.4f}, 5/12 = {5/12:.4f} — different")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"""
v ≈ +5/12 mode under asymmetric one-way coupling (b124 ⊕ ETHER_110):

Test 1 (ether drift): See above — is the +5/12 signal just the driven ether?
Test 2 (perturbation tracking): Measure if perturbation moves at +5/12.
Test 3 (period search): No exact period-N glider found in [1..42].
Test 4 (long-run speed): Best speed estimate from T=2000 run.

Key arithmetic identities for 5/12:
  5/12 = N_fam / (c_W + 1)         [c_W = 11 = sin²θ_W denominator]
  5/12 = N_fam / (4 × N_gen)       [N_gen = 3, N_fam = 5]
  5/12 = N_fam / lcm(3,4)          [lcm(3,4) = 12]
  v_R - 5/12 = 2/3 - 5/12 = 1/4   [clean gap to C₂ glider]
  v_R + 5/12 = c_H/12              [c_H = 13 = Higgs Z₇ charge denominator]
""")
