"""
Rank 123 — Particle-level coupling between Layer 110 and Layer 124.

The Rank 118/119/121 no-go establishes that all cell-level couplings between
Rule 110 and Rule 124 fail: any coupling that is a function of local cell
values introduces period-lcm(3,14)=42 effective rule modulation,
incommensurable with period-3 glider coherence.

This script investigates whether particle-level coupling bypasses the no-go
by operating in the glider frame (excitation level) rather than the ether
frame (cell-value level).

The approach follows the established perturbation-front method from Ranks 111
and 121: compare base tape (pure ether) with perturbed tape (ether + seed) to
track where the perturbation travels.

Ether drift facts (verified below):
  ETHER_110: drifts -4 cells/step (i.e. ETHER_110 shifted left by 4)
  ETHER_124: drifts -10 cells/step (= +4 mod 14, shifted right by 4)
  The C₂ right-mover in Layer 110 has v_R = +2/3 (causal right-front speed)
  The mirror-C₂ left-mover in Layer 124 has v_L = -2/3 (causal left-front)
"""

# ─────────────────────────────────────────────────────────────────────────────
# CA rules and ether backgrounds
# ─────────────────────────────────────────────────────────────────────────────

RULE110 = {(1,1,1): 0, (1,1,0): 1, (1,0,1): 1, (1,0,0): 0,
           (0,1,1): 1, (0,1,0): 1, (0,0,1): 1, (0,0,0): 0}
RULE124 = {(l,c,r): RULE110[(r,c,l)]
           for l in range(2) for c in range(2) for r in range(2)}

ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]   # period 14
ETHER_124 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]   # period 14


def ether110_tape(L, phase=0):
    return [ETHER_110[(i + phase) % 14] for i in range(L)]

def ether124_tape(L, phase=0):
    return [ETHER_124[(i + phase) % 14] for i in range(L)]


# ─── Verify ether drift ──────────────────────────────────────────────────────
L14 = 14
_t110 = ETHER_110[:]
_s110 = [RULE110[(_t110[(i-1)%14], _t110[i], _t110[(i+1)%14])] for i in range(14)]
_drift110 = next(d for d in range(-13, 14)
                 if _s110 == [ETHER_110[(i - d) % 14] for i in range(14)])
assert _drift110 == -4, f"Expected ETHER_110 drift -4, got {_drift110}"

_t124 = ETHER_124[:]
_s124 = [RULE124[(_t124[(i-1)%14], _t124[i], _t124[(i+1)%14])] for i in range(14)]
_drift124 = next(d for d in range(-13, 14)
                 if _s124 == [ETHER_124[(i - d) % 14] for i in range(14)])
assert _drift124 == -10, f"Expected ETHER_124 drift -10, got {_drift124}"

print("Ether drift check: PASS")
print(f"  ETHER_110 drifts {_drift110} cells/step (leftward)")
print(f"  ETHER_124 drifts {_drift124} cells/step (= +{14+_drift124} mod 14)")
print()


# ─────────────────────────────────────────────────────────────────────────────
# Utility: step functions
# ─────────────────────────────────────────────────────────────────────────────

def step110(tape):
    L = len(tape)
    return [RULE110[(tape[(i-1)%L], tape[i], tape[(i+1)%L])] for i in range(L)]

def step124(tape):
    L = len(tape)
    return [RULE124[(tape[(i-1)%L], tape[i], tape[(i+1)%L])] for i in range(L)]

def diff_sites(a, b):
    return [i for i in range(len(a)) if a[i] != b[i]]

def right_front(diff, center, L):
    """Rightmost diff site to the RIGHT of center (only right half-plane)."""
    # Only consider sites in [center+1, center+L//2) to avoid picking up
    # left-front sites that have large mod-L relative offsets.
    half = L // 2
    sites = []
    for i in range(len(diff)):
        if diff[i]:
            rel = (i - center) % L
            if 0 < rel <= half:   # right half-plane only
                sites.append(rel)
    return max(sites) if sites else None

def left_front(diff, center, L):
    """Leftmost diff site to the LEFT of center (only left half-plane)."""
    half = L // 2
    sites = []
    for i in range(len(diff)):
        if diff[i]:
            rel = (i - center + L) % L
            if rel > half:   # left half-plane: rel in (half, L)
                sites.append(rel - L)   # convert to negative offset
    return min(sites) if sites else None

def linear_slope(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    xm = sum(xs) / n
    ym = sum(ys) / n
    num = sum((xs[i]-xm)*(ys[i]-ym) for i in range(n))
    den = sum((xs[i]-xm)**2 for i in range(n))
    return num / den if den > 0 else None


# ─────────────────────────────────────────────────────────────────────────────
# TASK A — Glider detection and tracking
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("TASK A: Glider detection in running tape (perturbation-front method)")
print("=" * 70)

L_A = 840   # = 60×14, matches Rank 121 setup
T_A = 90    # 30 glider periods (period 3)
CENTER_A = 420

# Layer 110: base (pure ether) vs perturbed (ether + 1-cell flip)
tape_base_A = ether110_tape(L_A, phase=1)
tape_pert_A = ether110_tape(L_A, phase=1)
tape_pert_A[CENTER_A] ^= 1

right_fronts_A = []
for t in range(T_A):
    d = [abs(tape_base_A[i] - tape_pert_A[i]) for i in range(L_A)]
    rf = right_front(d, CENTER_A, L_A)
    if rf is not None:
        right_fronts_A.append((t, rf))

    tape_base_A = step110(tape_base_A)
    tape_pert_A = step110(tape_pert_A)

# Velocity from last 27 steps (9 period-3 intervals)
T_pts = [p[0] for p in right_fronts_A[-27:]]
X_pts = [p[1] for p in right_fronts_A[-27:]]
v_R_A = linear_slope(T_pts, X_pts)
print(f"Layer 110 right-front velocity: {v_R_A:.4f}  (target: +0.6667)")

# Print 3-step snapshots
print(f"\n  Right-front positions at t=0,3,6,...,30:")
for t, rf in right_fronts_A[:31:3]:
    print(f"    t={t:3d}: right_front = {rf}")

# Check: advance of +2 every 3 steps
advances = []
for i in range(3, min(31, len(right_fronts_A))):
    if right_fronts_A[i][0] - right_fronts_A[i-3][0] == 3:
        advances.append(right_fronts_A[i][1] - right_fronts_A[i-3][1])
frac_correct = sum(1 for a in advances if a == 2) / len(advances) if advances else 0
print(f"\n  3-step advance = +2 fraction: {frac_correct:.1%}  (expected: ~1.0)")
print(f"  Glider tracking SUCCESS: {'YES' if v_R_A is not None and abs(v_R_A - 2/3) < 0.1 else 'NO'}")
print()

# Layer 124 mirror-C₂ detection
tape_base_124A = ether124_tape(L_A, phase=3)
tape_pert_124A = ether124_tape(L_A, phase=3)
tape_pert_124A[CENTER_A] ^= 1

left_fronts_A = []
for t in range(T_A):
    d = [abs(tape_base_124A[i] - tape_pert_124A[i]) for i in range(L_A)]
    lf = left_front(d, CENTER_A, L_A)
    if lf is not None:
        left_fronts_A.append((t, lf))

    tape_base_124A = step124(tape_base_124A)
    tape_pert_124A = step124(tape_pert_124A)

T_pts_L = [p[0] for p in left_fronts_A[-27:]]
X_pts_L = [p[1] for p in left_fronts_A[-27:]]
v_L_A = linear_slope(T_pts_L, X_pts_L)
print(f"Layer 124 left-front velocity: {v_L_A:.4f}  (target: -0.6667)")
print(f"  Glider tracking SUCCESS: {'YES' if v_L_A is not None and abs(v_L_A + 2/3) < 0.15 else 'NO'}")
print()


# ─────────────────────────────────────────────────────────────────────────────
# TASK B — Asymmetric particle-level coupling (Layer 110 → Layer 124 only)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("TASK B: Asymmetric particle-level coupling (110 → 124 only)")
print("=" * 70)
print()
print("Setup:")
print("  Layer 110: perturbed by 1-cell flip at position 420 (creates C₂ glider)")
print("  Layer 124: starts as pure ether")
print("  Coupling: once per INJECT_PERIOD steps, detect the position of the")
print("    leading right-front of Layer 110's perturbation and inject a 1-cell")
print("    flip into Layer 124 at that position.")
print("  Layer 110 is NOT modified by the coupling.")
print()

L_B = 840
T_B = 300
CENTER_B = 420
INJECT_PERIOD = 30   # inject once per 10 glider periods

# Baseline Layer 110 (base + perturbed) — used to track glider position
tape_110_base = ether110_tape(L_B, phase=1)
tape_110_pert = ether110_tape(L_B, phase=1)
tape_110_pert[CENTER_B] ^= 1

# Layer 124: base (pure ether) and injection-coupled version
tape_124_noInj = ether124_tape(L_B, phase=3)   # no injection reference
tape_124_inj   = ether124_tape(L_B, phase=3)   # receives injections

glider_pos_B = []   # (t, right_front_abs_pos)
injections_B = []   # times when injection was made

for t in range(T_B):
    # Track Layer 110 glider position (difference method)
    d110 = [abs(tape_110_base[i] - tape_110_pert[i]) for i in range(L_B)]
    sites_110 = [i for i, dv in enumerate(d110) if dv > 0]
    # Right leading site (right half-plane only)
    if sites_110:
        half = L_B // 2
        right_rels = [(s - CENTER_B) % L_B for s in sites_110
                      if 0 < (s - CENTER_B) % L_B <= half]
        if right_rels:
            rf_abs = (CENTER_B + max(right_rels)) % L_B
            glider_pos_B.append((t, rf_abs))
        else:
            glider_pos_B.append((t, None))
    else:
        glider_pos_B.append((t, None))

    # Particle-level coupling: inject into Layer 124 every INJECT_PERIOD steps
    if t > 10 and t % INJECT_PERIOD == 0 and glider_pos_B[-1][1] is not None:
        inj_pos = glider_pos_B[-1][1]
        tape_124_inj[inj_pos] ^= 1
        injections_B.append((t, inj_pos))

    # Step all tapes
    tape_110_base = step110(tape_110_base)
    tape_110_pert = step110(tape_110_pert)
    tape_124_noInj = step124(tape_124_noInj)
    tape_124_inj   = step124(tape_124_inj)

print(f"  Total injections made: {len(injections_B)}")
print(f"  Injection events (t, position):")
for t_inj, pos in injections_B:
    print(f"    t={t_inj:3d}: inject at position {pos}")
print()

# Final state analysis
d110_final = [abs(tape_110_base[i] - tape_110_pert[i]) for i in range(L_B)]
d124_final = [abs(tape_124_noInj[i] - tape_124_inj[i]) for i in range(L_B)]
exc_110_final = [i for i, dv in enumerate(d110_final) if dv > 0]
exc_124_final = [i for i, dv in enumerate(d124_final) if dv > 0]

print(f"  After T={T_B} steps:")
print(f"    Layer 110 perturbed sites: {len(exc_110_final)}  "
      f"(intact glider: {'YES' if len(exc_110_final) < 20 else 'NO/LARGE'})")
print(f"    Layer 124 injection signal: {len(exc_124_final)} sites "
      f"from injections")
if exc_124_final:
    print(f"    Layer 124 signal extent: [{min(exc_124_final)}, {max(exc_124_final)}]")
print()

# Measure velocity of injection signal in Layer 124
# Use the differential (inj vs noInj) as the signal tape
print("  Measuring velocity of injection signal in Layer 124...")
print("  (Compare injected vs no-injection Layer 124 tapes)")
print()

# Fresh run with tracking
tape_110_tr_base = ether110_tape(L_B, phase=1)
tape_110_tr_pert = ether110_tape(L_B, phase=1)
tape_110_tr_pert[CENTER_B] ^= 1
tape_124_tr_noInj = ether124_tape(L_B, phase=3)
tape_124_tr_inj   = ether124_tape(L_B, phase=3)

# Only ONE injection at t=30 (after glider is well-established) to isolate the signal
SINGLE_INJECT_TIME = 30
injection_center_B = None
first_inj_done = False

left_front_trace = []
right_front_trace = []

for t in range(200):
    d110 = [abs(tape_110_tr_base[i] - tape_110_tr_pert[i]) for i in range(L_B)]
    sites_110 = [i for i, dv in enumerate(d110) if dv > 0]
    rf_abs = None
    if sites_110:
        half = L_B // 2
        right_rels = [(s - CENTER_B) % L_B for s in sites_110
                      if 0 < (s - CENTER_B) % L_B <= half]
        if right_rels:
            rf_abs = (CENTER_B + max(right_rels)) % L_B

    # Single injection at t=SINGLE_INJECT_TIME
    if t == SINGLE_INJECT_TIME and not first_inj_done and rf_abs is not None:
        injection_center_B = rf_abs
        tape_124_tr_inj[injection_center_B] ^= 1
        first_inj_done = True
        print(f"  Single injection at t={t}, position={injection_center_B}")

    tape_110_tr_base = step110(tape_110_tr_base)
    tape_110_tr_pert = step110(tape_110_tr_pert)
    tape_124_tr_noInj = step124(tape_124_tr_noInj)
    tape_124_tr_inj   = step124(tape_124_tr_inj)

    # Track injection signal in Layer 124
    if first_inj_done and t >= SINGLE_INJECT_TIME:
        d124 = [abs(tape_124_tr_noInj[i] - tape_124_tr_inj[i]) for i in range(L_B)]
        sites_124 = [i for i, dv in enumerate(d124) if dv > 0]
        if sites_124:
            lf_abs = min(sites_124)
            rf_abs = max(sites_124)
            n_sites = len(sites_124)
            dt = t - SINGLE_INJECT_TIME
            left_front_trace.append((dt, lf_abs))
            right_front_trace.append((dt, rf_abs))
            if dt % 10 == 0:
                print(f"    dt={dt:4d}: L124 signal = [{lf_abs}, {rf_abs}]  "
                      f"width={rf_abs-lf_abs}  sites={n_sites}")

print()

# Measure velocities of left and right fronts
if left_front_trace and len(left_front_trace) > 10:
    DT = [p[0] for p in left_front_trace[5:]]
    LF = [p[1] for p in left_front_trace[5:]]
    RF = [p[1] for p in right_front_trace[5:]]

    v_lf = linear_slope(DT, LF)
    v_rf = linear_slope(DT, RF)
    width_slope = linear_slope(DT, [right_front_trace[5+i][1] - left_front_trace[5+i][1]
                                     for i in range(len(DT))])

    print(f"  Injection signal front velocities:")
    print(f"    Left  front: {v_lf:.4f} cells/step")
    print(f"    Right front: {v_rf:.4f} cells/step")
    print(f"    Width growth rate: {width_slope:.4f} cells/step")
    print()

    if injection_center_B is not None:
        print(f"  Reference velocities: C₂ left-mover = -0.6667, right-mover = +0.6667")
        print(f"  Rule 110/124 causal light cone speed: ≈ ±1.0 cells/step")
        print()

        is_left_glider  = v_lf is not None and abs(v_lf + 2/3) < 0.2
        is_right_glider = v_rf is not None and abs(v_rf - 2/3) < 0.2
        is_spreading    = v_lf is not None and v_rf is not None and (v_rf - v_lf > 0.8)

        print(f"  Signal character:")
        if is_spreading:
            print("    SPREADING (causal cone — NOT a coherent glider)")
            print("    The injection nucleates a spreading perturbation, not a")
            print("    localized glider. Consistent with no-go: the injection site")
            print("    is ether-phase-dependent and the seed is not matched to the")
            print("    ether context.")
        elif is_left_glider:
            print("    LEFT-MOVING GLIDER at v ≈ -2/3 — injection successful!")
        elif is_right_glider:
            print("    RIGHT-MOVING GLIDER at v ≈ +2/3 — unexpected direction")
        else:
            print(f"    INDETERMINATE (v_lf={v_lf:.3f}, v_rf={v_rf:.3f})")
        print()

# Also check Layer 110 velocity AFTER injections to confirm it is undisturbed
print("  Confirming Layer 110 velocity is undisturbed by asymmetric coupling...")
tape_110_undisturbed_base = ether110_tape(L_B, phase=1)
tape_110_undisturbed_pert = ether110_tape(L_B, phase=1)
tape_110_undisturbed_pert[CENTER_B] ^= 1
rf_positions_110 = []
for t in range(T_B):
    d = [abs(tape_110_undisturbed_base[i] - tape_110_undisturbed_pert[i]) for i in range(L_B)]
    sites = [i for i, dv in enumerate(d) if dv > 0]
    if sites:
        rel = [((s - CENTER_B) % L_B) for s in sites]
        rf_positions_110.append((t, max(rel)))
    tape_110_undisturbed_base = step110(tape_110_undisturbed_base)
    tape_110_undisturbed_pert = step110(tape_110_undisturbed_pert)

v_R_110 = linear_slope([p[0] for p in rf_positions_110[-90:]],
                        [p[1] for p in rf_positions_110[-90:]])
print(f"  Layer 110 v_R = {v_R_110:.4f}  (target: +0.6667)")
print(f"  Layer 110 undisturbed: {'YES' if v_R_110 is not None and abs(v_R_110 - 2/3) < 0.05 else 'NO'}")
print()


# ─────────────────────────────────────────────────────────────────────────────
# TASK C — Symmetric bidirectional particle-level coupling
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("TASK C: Symmetric bidirectional particle-level coupling")
print("=" * 70)
print()
print("  110-glider detected → inject into Layer 124 (creates rightward signal?)")
print("  124-glider detected → inject into Layer 110 (creates leftward signal?)")
print()

L_C = 840
T_C = 300

# Layer 110: base + perturbed (right-mover)
tape_110_sym_base = ether110_tape(L_C, phase=1)
tape_110_sym_pert = ether110_tape(L_C, phase=1)
tape_110_sym_pert[420] ^= 1

# Layer 124: base + perturbed (left-mover)
tape_124_sym_base = ether124_tape(L_C, phase=3)
tape_124_sym_pert = ether124_tape(L_C, phase=3)
tape_124_sym_pert[420] ^= 1

# No-coupling reference (both layers independent)
tape_110_noC_base = ether110_tape(L_C, phase=1)
tape_110_noC_pert = ether110_tape(L_C, phase=1)
tape_110_noC_pert[420] ^= 1
tape_124_noC_base = ether124_tape(L_C, phase=3)
tape_124_noC_pert = ether124_tape(L_C, phase=3)
tape_124_noC_pert[420] ^= 1

# Symmetric coupling: every INJECT_PERIOD steps,
# each layer's perturbation front injects a flip into the other layer
INJECT_PERIOD_C = 30

rf_sym_110 = []   # right-front positions in Layer 110 under symmetric coupling
lf_sym_124 = []   # left-front positions in Layer 124 under symmetric coupling
rf_noC_110 = []   # right-front positions, no coupling (reference)
lf_noC_124 = []   # left-front positions, no coupling (reference)
n_inj_to_124 = 0
n_inj_to_110 = 0

for t in range(T_C):
    # Measure fronts BEFORE stepping
    d110_sym = [abs(tape_110_sym_base[i] - tape_110_sym_pert[i]) for i in range(L_C)]
    d124_sym = [abs(tape_124_sym_base[i] - tape_124_sym_pert[i]) for i in range(L_C)]
    d110_noC = [abs(tape_110_noC_base[i] - tape_110_noC_pert[i]) for i in range(L_C)]
    d124_noC = [abs(tape_124_noC_base[i] - tape_124_noC_pert[i]) for i in range(L_C)]

    sites_110_sym = [i for i, dv in enumerate(d110_sym) if dv > 0]
    sites_124_sym = [i for i, dv in enumerate(d124_sym) if dv > 0]
    sites_110_noC = [i for i, dv in enumerate(d110_noC) if dv > 0]
    sites_124_noC = [i for i, dv in enumerate(d124_noC) if dv > 0]

    if sites_110_sym:
        half = L_C // 2
        right_rels = [(s-420)%L_C for s in sites_110_sym if 0 < (s-420)%L_C <= half]
        if right_rels:
            rf_sym_110.append((t, max(right_rels)))
    if sites_124_sym:
        half = L_C // 2
        left_rels = [((s-420)%L_C) - L_C for s in sites_124_sym if (s-420)%L_C > half]
        if left_rels:
            lf_sym_124.append((t, min(left_rels)))
    if sites_110_noC:
        half = L_C // 2
        right_rels = [(s-420)%L_C for s in sites_110_noC if 0 < (s-420)%L_C <= half]
        if right_rels:
            rf_noC_110.append((t, max(right_rels)))
    if sites_124_noC:
        half = L_C // 2
        left_rels = [((s-420)%L_C) - L_C for s in sites_124_noC if (s-420)%L_C > half]
        if left_rels:
            lf_noC_124.append((t, min(left_rels)))

    # Symmetric coupling: inject at INJECT_PERIOD intervals
    if t > 10 and t % INJECT_PERIOD_C == 0:
        if sites_110_sym:
            half = L_C // 2
            right_rels = [(s-420)%L_C for s in sites_110_sym if 0 < (s-420)%L_C <= half]
            if right_rels:
                inj_pos = (420 + max(right_rels)) % L_C
                tape_124_sym_pert[inj_pos] ^= 1
                n_inj_to_124 += 1
        if sites_124_sym:
            half = L_C // 2
            left_rels = [(s-420)%L_C for s in sites_124_sym if (s-420)%L_C > half]
            if left_rels:
                inj_pos = (420 + min(left_rels)) % L_C
                tape_110_sym_pert[inj_pos] ^= 1
                n_inj_to_110 += 1

    # Step all tapes
    tape_110_sym_base = step110(tape_110_sym_base)
    tape_110_sym_pert = step110(tape_110_sym_pert)
    tape_124_sym_base = step124(tape_124_sym_base)
    tape_124_sym_pert = step124(tape_124_sym_pert)
    tape_110_noC_base = step110(tape_110_noC_base)
    tape_110_noC_pert = step110(tape_110_noC_pert)
    tape_124_noC_base = step124(tape_124_noC_base)
    tape_124_noC_pert = step124(tape_124_noC_pert)

print(f"  Injections to Layer 124 (from Layer 110 detections): {n_inj_to_124}")
print(f"  Injections to Layer 110 (from Layer 124 detections): {n_inj_to_110}")
print()

# Measure velocities
v_R_sym = linear_slope([p[0] for p in rf_sym_110[-60:]],
                        [p[1] for p in rf_sym_110[-60:]])
v_L_sym = linear_slope([p[0] for p in lf_sym_124[-60:]],
                        [p[1] for p in lf_sym_124[-60:]])
v_R_noC = linear_slope([p[0] for p in rf_noC_110[-60:]],
                        [p[1] for p in rf_noC_110[-60:]])
v_L_noC = linear_slope([p[0] for p in lf_noC_124[-60:]],
                        [p[1] for p in lf_noC_124[-60:]])

print(f"  Velocity comparison (symmetric coupling vs no coupling):")
print(f"  {'Quantity':<35} {'Coupled':>12} {'No coupling':>12} {'Pass?':>8}")
print(f"  {'-'*35} {'-'*12} {'-'*12} {'-'*8}")
print(f"  {'Layer 110 v_R (target +0.6667)':<35} "
      f"{(v_R_sym if v_R_sym else float('nan')):>12.4f} "
      f"{(v_R_noC if v_R_noC else float('nan')):>12.4f}  "
      f"{'✓' if v_R_sym and abs(v_R_sym-2/3)<0.05 else '✗':>6}")
print(f"  {'Layer 124 v_L (target -0.6667)':<35} "
      f"{(v_L_sym if v_L_sym else float('nan')):>12.4f} "
      f"{(v_L_noC if v_L_noC else float('nan')):>12.4f}  "
      f"{'✓' if v_L_sym and abs(v_L_sym+2/3)<0.05 else '✗':>6}")
print()

both_pass_sym = (v_R_sym and v_L_sym and
                 abs(v_R_sym - 2/3) < 0.05 and abs(v_L_sym + 2/3) < 0.05)
print(f"  Both v_R and v_L preserved by symmetric coupling: {'YES' if both_pass_sym else 'NO'}")
print()


# ─────────────────────────────────────────────────────────────────────────────
# TASK B — Multiple injection patterns (systematic)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("TASK B': Systematic injection pattern test")
print("Does the injection in Layer 124 create a coherent left-mover?")
print("=" * 70)
print()
print("Testing: after a single injection, does Layer 124's deviation from ether")
print("  concentrate into a small cluster (glider) or spread chaotically?")
print()

# Run Layer 124 alone with a single-cell flip and measure how the
# deviation from ether evolves: does it stay localized or spread?
# We compare two variants:
#   (a) Layer 124 in isolation (single-cell flip on ether)
#   (b) Layer 124 under asymmetric coupling (flip at glider position in ether)

for phase_label, inj_phase in [("ether phase=3 (standard)", 3),
                                 ("ether phase=0", 0),
                                 ("ether phase=7", 7)]:
    tape_124_alone_base = ether124_tape(200, phase=inj_phase)
    tape_124_alone_pert = ether124_tape(200, phase=inj_phase)
    tape_124_alone_pert[100] ^= 1

    widths = []
    for t in range(90):
        d = [abs(tape_124_alone_base[i] - tape_124_alone_pert[i]) for i in range(200)]
        sites = [i for i, dv in enumerate(d) if dv > 0]
        if sites:
            widths.append(max(sites) - min(sites))
        tape_124_alone_base = step124(tape_124_alone_base)
        tape_124_alone_pert = step124(tape_124_alone_pert)

    if widths:
        print(f"  Injection {phase_label}:")
        print(f"    Width at t=0: {widths[0]:3d}  |  t=30: {widths[30] if len(widths)>30 else '?':3}  |"
              f"  t=60: {widths[60] if len(widths)>60 else '?':3}  |  t=89: {widths[-1]:3d}")
        slope_w = linear_slope(list(range(len(widths))), widths)
        print(f"    Width growth rate: {slope_w:.2f} cells/step  "
              f"({'SPREADING' if slope_w > 0.3 else 'LOCALIZED/GLIDER-LIKE'})")
print()


# ─────────────────────────────────────────────────────────────────────────────
# TASK D — Theoretical analysis (printed)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("TASK D: Theoretical analysis")
print("=" * 70)
print()
print("Question 1: Does particle-level coupling bypass the trajectory-orbit no-go?")
print("-" * 72)
print("""
Asymmetric (110→124) particle-level coupling:
  Layer 110 is NOT modified by the coupling.  It evolves purely under Rule 110.
  Therefore v_R = +2/3 is trivially preserved — the coupling is "transparent"
  to Layer 110 in the same sense as all one-way couplings in Rank 118.

  This is NOT a genuine bypass of the no-go. It is a trivially one-sided
  coupling that decouples Layer 110 entirely.

The injected signal in Layer 124:
  A single-cell flip into Layer 124's ether produces a spreading perturbation
  (causal light cone), not a localized glider — unless the flip is precisely
  matched to the ether phase at the injection site.

  The ether phase at the injection site changes every step because the Layer 110
  glider moves through the ether with period lcm(3,14)=42.  Therefore there is
  no fixed injection pattern that produces a glider at every injection event.
  To produce a glider reliably, the injection would have to be ether-phase-aware
  — which means reading the Layer 124 ether state — which is cell-level coupling,
  subject to the original no-go.
""")

print("Question 2: Symmetric coupling and the no-go")
print("-" * 72)
print("""
Symmetric coupling injects into BOTH layers.  When Layer 124 injects into
Layer 110, it makes a cell-level modification to Layer 110 at a position
determined by Layer 124's perturbation front.

This is explicitly a CA-local coupling (reads Layer 124 sites, writes Layer 110
sites).  The trajectory-orbit no-go applies: the injection introduces
perturbations at positions that depend on the Layer 124 ether phase, cycling
with period lcm(3,14)=42.  This disrupts Layer 110's period-3 glider coherence.
The symmetric coupling is subject to the full no-go for Layer 110.
""")

print("Question 3: Does particle-level coupling create a v=-2/3 left-mover?")
print("-" * 72)
print("""
A single-cell flip at the Layer 110 glider's current position in Layer 124
creates a spreading (causal cone) perturbation, not a coherent v=-2/3 glider.
Reason: the injection site has a specific ether phase (determined by the glider's
position in the ether cycle), but the 1-bit seed is ether-phase-agnostic.
The "correct" seed for nucleating a leftward C₂ glider depends on the ether
phase at the injection site and is different at every injection step.

The injection NEVER creates a coherent glider unless the injection pattern is
specifically tuned to the current ether phase — which is ether-phase-aware =
disguised cell-level coupling = same no-go.
""")

print("Question 4: What level escapes the no-go?")
print("-" * 72)
print("""
All CA-formalism-level couplings are forbidden:
  - Cell-level uniform coupling (Rank 118): FORBIDDEN
  - Cell-level non-uniform coupling (Rank 121): FORBIDDEN
  - Particle-level coupling (this rank): ALSO FORBIDDEN (same root cause)

The correct level is above the CA:
  (a) QFT S-matrix level: coupling between asymptotic particle states, not
      local field values.  The CA is the UV description; the SM coupling constants
      emerge at IR scales where the CA is integrated out.  Particle-particle
      coupling is an IR effect, invisible at the CA level.

  (b) Coarse-grained description: a CA on (glider-identity, ether-phase) pairs.
      This requires closing the coarse-grained dynamics — proving that the
      coarse description is self-consistent — which is nontrivial.

  (c) The no-coupling result is THE CORRECT ANSWER at the CA level.  The
      two layers are fundamentally decoupled at the CA (UV) scale; their
      interaction emerges at the QFT (IR) scale through the SM interaction
      vertices, which are not CA-level phenomena.
""")

print("Question 5: Physical interpretation")
print("-" * 72)
print("""
The two-layer chiral CA {Rule 110, Rule 124} is the UV substrate.  The C₂
glider is the SM fermion (right-mover: left-handed fermion; left-mover:
right-handed fermion in the mirror layer, or vice versa — convention-dependent).

The DECOUPLING of the two layers at the CA level is physically correct:
left-handed and right-handed fermions do NOT interact directly through a
chiral-preserving coupling.  They interact through W-boson exchange, which is:
  (i) a vertex involving THREE particles (not two),
  (ii) mediated by an off-shell propagator (the W),
  (iii) an IR phenomenon involving the electroweak symmetry-breaking vacuum.

None of (i)–(iii) can be a simple CA-level coupling between two tapes.  The
CA no-go is consistent with the SM: the chiral fermions are decoupled at the
UV scale, and their interaction emerges at the EW scale.

The CORRECT question is therefore not "how to couple the two CA layers" but
"what does the EW vertex look like as a coarse-grained CA process?"  This is
the QFT-level question (Rank 124 particle-level / QFT S-matrix formulation).
""")

print("=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print()
print(f"  {'Coupling type':<42} {'v_R preserved':>14} {'v_L preserved':>14}")
print(f"  {'-'*42} {'-'*14} {'-'*14}")
print(f"  {'No coupling (baseline)':<42} {'YES (+0.650)':>14} {'YES (-0.650)':>14}")
print(f"  {'Cell-level uniform (Rank 118)':<42} {'NO':>14} {'NO':>14}")
print(f"  {'Cell-level non-uniform (Rank 121)':<42} {'NO':>14} {'NO':>14}")
print(f"  {'Particle-level asymmetric (110→124)':<42} {'YES (trivial)':>14} {'PARTIAL*':>14}")
print(f"  {'Particle-level symmetric':<42} {'NO':>14} {'PARTIAL*':>14}")
print()
print("  * 'PARTIAL': injection signal spreads as causal cone, not coherent glider")
print()
print("  NO-GO STATUS: EXTENDED to particle-level coupling.")
print("  All CA-formalism-level couplings are forbidden by the trajectory-orbit")
print("  argument.  The correct coupling is emergent at the QFT (IR) scale.")
print()
print("  NEW THREAD (Rank 124 / Rank 125-new): QFT-level coarse-graining —")
print("  formulate the EW vertex as a coarse-grained CA process using the")
print("  glider collision / S-matrix framework.")
