"""
rank127_diagonal_coupling.py
Diagonal (offset) coupling between Layer 110 and Layer 124.

Investigates whether a spatial offset delta between the two coupled CA layers
can break the trajectory-orbit no-go (lcm(3,14)=42 does not divide 3).

Tasks:
  A: Symmetric diagonal coupling over delta in {1..7, 14, 21, 28, 35, 42} + negatives
  B: Asymmetric (chirally-motivated) coupling at delta=2
  C: Analytical check — does any delta make the ether-phase sequence seen by
     the glider periodic with period dividing 3?
"""

import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# CA setup
# ---------------------------------------------------------------------------

RULE110 = {
    (1,1,1): 0, (1,1,0): 1, (1,0,1): 1, (1,0,0): 0,
    (0,1,1): 1, (0,1,0): 1, (0,0,1): 1, (0,0,0): 0,
}
RULE124 = {(l,c,r): RULE110[(r,c,l)]
           for l in range(2) for c in range(2) for r in range(2)}

ETHER_110 = [1,1,1,1,1,0,0,0,1,0,0,1,1,0]  # period-14 ground state for Rule 110
ETHER_124 = [0,1,1,0,0,1,0,0,0,1,1,1,1,1]  # period-14 ground state for Rule 124

L = 840   # tape length: 60 × 14 (ether periods)
T = 300   # simulation steps


def make_tape(ether, L):
    return [ether[i % 14] for i in range(L)]


# ---------------------------------------------------------------------------
# Single-layer steps (for calibration)
# ---------------------------------------------------------------------------

def step_110(tape):
    L = len(tape)
    return [RULE110[(tape[(i-1)%L], tape[i], tape[(i+1)%L])] for i in range(L)]

def step_124(tape):
    L = len(tape)
    return [RULE124[(tape[(i-1)%L], tape[i], tape[(i+1)%L])] for i in range(L)]


# ---------------------------------------------------------------------------
# Diagonal symmetric coupling
# ---------------------------------------------------------------------------

def step_diagonal_symmetric(tape_110, tape_124, delta):
    """
    Symmetric diagonal coupling:
      Layer 110 cell i couples to Layer 124 cell (i + delta) % L
      Layer 124 cell i couples to Layer 110 cell (i - delta) % L

    b110_coupled = b110 XOR tape_124[(i + delta) % L]
    b124_coupled = b124 XOR tape_110[(i - delta) % L]
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        b110_coupled = (b110 ^ tape_124[(i + delta) % L]) % 2
        b124_coupled = (b124 ^ tape_110[(i - delta) % L]) % 2
        new_110.append(b110_coupled)
        new_124.append(b124_coupled)
    return new_110, new_124


# ---------------------------------------------------------------------------
# Asymmetric (chirally-motivated) coupling
# ---------------------------------------------------------------------------

def step_diagonal_asymmetric(tape_110, tape_124, delta=2):
    """
    Asymmetric chiral coupling respecting propagation direction:
      Right-mover (Layer 110) reaches FORWARD: 110[i] sees 124[i + delta]
      Left-mover  (Layer 124) reaches FORWARD in its direction: 124[i] sees 110[i + delta]

    This keeps the coupling directional, matching each layer's propagation.
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        b110_coupled = (b110 ^ tape_124[(i + delta) % L]) % 2
        b124_coupled = (b124 ^ tape_110[(i + delta) % L]) % 2
        new_110.append(b110_coupled)
        new_124.append(b124_coupled)
    return new_110, new_124


# ---------------------------------------------------------------------------
# Velocity measurement: right-front tracking in Layer 110
# ---------------------------------------------------------------------------

def measure_vR(delta=0, coupling_type="symmetric", T=T, perturb_phase=1):
    """
    Measure the speed of the C2 glider in Layer 110 under diagonal coupling.

    Approach: base vs perturbed simulation. Track the right-front of the
    perturbation difference.
    """
    base_110 = make_tape(ETHER_110, L)
    base_124 = make_tape(ETHER_124, L)

    # Place a C2 glider seed at position perturb_phase
    pert_110 = base_110[:]
    pert_110[perturb_phase] ^= 1

    # Evolve both
    for _ in range(T):
        if coupling_type == "symmetric":
            base_110, base_124 = step_diagonal_symmetric(base_110, base_124, delta)
            pert_110, _ = step_diagonal_symmetric(pert_110, base_124[:], delta)
        elif coupling_type == "asymmetric":
            base_110, base_124 = step_diagonal_asymmetric(base_110, base_124, delta)
            pert_110, _ = step_diagonal_asymmetric(pert_110, base_124[:], delta)
        elif coupling_type == "none":
            base_110 = step_110(base_110)
            base_124 = step_124(base_124)
            pert_110 = step_110(pert_110)

    diff = [(base_110[i] ^ pert_110[i]) for i in range(L)]
    active = [i for i in range(L) if diff[i] == 1]
    return active


def track_front_velocity(delta=0, coupling_type="symmetric", T=T):
    """
    Track the rightmost front of the perturbation difference to measure v_R.
    Returns slope from linear regression over the last 9 tracked front positions.
    """
    base_110 = make_tape(ETHER_110, L)
    base_124 = make_tape(ETHER_124, L)
    pert_110 = base_110[:]
    pert_110[1] ^= 1

    front_positions = []
    for t in range(T):
        if coupling_type == "symmetric":
            base_110, base_124 = step_diagonal_symmetric(base_110, base_124, delta)
            pert_110, _ = step_diagonal_symmetric(pert_110, base_124[:], delta)
        elif coupling_type == "asymmetric":
            base_110, base_124 = step_diagonal_asymmetric(base_110, base_124, delta)
            pert_110, _ = step_diagonal_asymmetric(pert_110, base_124[:], delta)
        elif coupling_type == "none":
            base_110 = step_110(base_110)
            base_124 = step_124(base_124)
            pert_110 = step_110(pert_110)

        diff = [(base_110[i] ^ pert_110[i]) for i in range(L//2)]  # avoid wrap
        active = [i for i in range(L//2) if diff[i] == 1]
        if active:
            front_positions.append((t+1, max(active)))

    if len(front_positions) < 9:
        return None

    pts = front_positions[-9:]
    ts = [p[0] for p in pts]
    xs = [p[1] for p in pts]
    n = len(ts)
    t_mean = sum(ts)/n
    x_mean = sum(xs)/n
    num = sum((ts[i]-t_mean)*(xs[i]-x_mean) for i in range(n))
    den = sum((ts[i]-t_mean)**2 for i in range(n))
    if den == 0:
        return None
    return num/den


def track_front_velocity_L124(delta=0, coupling_type="symmetric", T=T):
    """
    Track the leftmost front of the perturbation difference in Layer 124 to measure v_L.
    """
    base_110 = make_tape(ETHER_110, L)
    base_124 = make_tape(ETHER_124, L)
    pert_124 = base_124[:]
    pert_124[L//2 + 3] ^= 1   # perturb near center, track leftward movement

    front_positions = []
    for t in range(T):
        if coupling_type == "symmetric":
            base_110, base_124 = step_diagonal_symmetric(base_110, base_124, delta)
            _, pert_124 = step_diagonal_symmetric(base_110[:], pert_124, delta)
        elif coupling_type == "asymmetric":
            base_110, base_124 = step_diagonal_asymmetric(base_110, base_124, delta)
            _, pert_124 = step_diagonal_asymmetric(base_110[:], pert_124, delta)
        elif coupling_type == "none":
            base_110 = step_110(base_110)
            base_124 = step_124(base_124)
            pert_124 = step_124(pert_124)

        diff = [(base_124[i] ^ pert_124[i]) for i in range(L//2)]
        active = [i for i in range(L//2) if diff[i] == 1]
        if active:
            front_positions.append((t+1, min(active)))  # leftmost front

    if len(front_positions) < 9:
        return None

    pts = front_positions[-9:]
    ts = [p[0] for p in pts]
    xs = [p[1] for p in pts]
    n = len(ts)
    t_mean = sum(ts)/n
    x_mean = sum(xs)/n
    num = sum((ts[i]-t_mean)*(xs[i]-x_mean) for i in range(n))
    den = sum((ts[i]-t_mean)**2 for i in range(n))
    if den == 0:
        return None
    return num/den


# ---------------------------------------------------------------------------
# Task C: Analytical ether-phase sequence check
# ---------------------------------------------------------------------------

def find_sequence_period(seq):
    """Find the minimal period of a sequence."""
    n = len(seq)
    for p in range(1, n+1):
        if all(seq[k] == seq[k % p] for k in range(n)):
            return p
    return n


def analyze_ether_phase_sequences():
    """
    For each delta in 0..13, compute the sequence of ether phases that the C2 glider
    (advancing 2 cells per 3 steps) sees when coupling is diagonal with offset delta.

    The glider at position x sees Layer 124 at position (x + delta) % 14.
    As the glider advances 2 cells each step (in glider-frame time), it samples:
    ether phase at (x + delta + 2*k) % 14 for k = 0, 1, 2, ...

    We compute this sequence over 42 steps (= lcm(3,14)) and find its period.
    """
    print("\n" + "="*60)
    print("TASK C: Analytical ether-phase sequence analysis")
    print("="*60)
    print(f"ETHER_124 = {ETHER_124}")
    print()
    print("For each delta, the glider at position x sees ether phase at (x+delta+2k) % 14.")
    print("Sequence over 42 steps (= lcm(3,14)), starting at x=0:")
    print()

    escape_deltas = []
    for delta in range(14):
        phases = [ETHER_124[(0 + delta + 2*k) % 14] for k in range(42)]
        period = find_sequence_period(phases)
        divides_3 = (3 % period == 0)
        status = "*** PERIOD DIVIDES 3 — NO-GO ESCAPE ***" if divides_3 else ""
        print(f"  delta={delta:2d}: period={period:2d}  phases(first 14)={phases[:14]}  {status}")
        if divides_3:
            escape_deltas.append(delta)

    print()
    if escape_deltas:
        print(f"ESCAPE DELTAS (period divides 3): {escape_deltas}")
        print("These offsets make the glider sample an ether sub-sequence with period 1 or 3.")
        print("The trajectory-orbit no-go does NOT apply to these deltas.")
    else:
        print("NO ESCAPE DELTAS: for all delta in 0..13, the ether-phase sequence has period > 3.")
        print("Trajectory-orbit no-go extends to ALL diagonal offsets.")

    print()
    print("Full analysis — for all delta in 0..13, what is the period of the 42-step sequence?")
    for delta in range(14):
        phases = [ETHER_124[(0 + delta + 2*k) % 14] for k in range(42)]
        period = find_sequence_period(phases)
        # Also check what period it is modulo 3 coherence requirement
        # For period-3 coherence we need period | 3, i.e., period in {1, 3}
        print(f"  delta={delta:2d}: period={period:2d}  {'ESCAPE' if 3 % period == 0 else 'no-go applies'}")

    return escape_deltas


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main():
    print("="*60)
    print("Rank 127: Diagonal (offset) coupling — Layer 110 / Layer 124")
    print("="*60)
    print(f"Tape length L={L}, Steps T={T}")
    print()

    # ---- Calibration: no coupling ----
    print("CALIBRATION (no coupling):")
    vR_cal = track_front_velocity(delta=0, coupling_type="none")
    vL_cal = track_front_velocity_L124(delta=0, coupling_type="none")
    print(f"  v_R (Layer 110, no coupling) = {vR_cal:.6f}  (target: +0.667)")
    print(f"  v_L (Layer 124, no coupling) = {vL_cal:.6f}  (target: -0.667)")
    print()

    # ---- Task A: Symmetric diagonal coupling ----
    deltas_to_test = [1, 2, 3, 4, 5, 6, 7, -1, -2, -3, 14, 21, 28, 35, 42]
    # Also add the negative of important ones explicitly (mod L they are the same as L-delta)
    # but for clarity we test them directly as given

    print("="*60)
    print("TASK A: Symmetric diagonal coupling — v_R and v_L scan")
    print("="*60)
    print(f"{'delta':>8}  {'v_R':>10}  {'v_L':>10}  {'pass_R?':>8}  {'pass_L?':>8}  {'BOTH?':>6}")
    print("-"*60)

    TARGET_R = 2/3
    TARGET_L = -2/3
    TOL = 0.05

    results = {}
    for delta in deltas_to_test:
        vR = track_front_velocity(delta=delta, coupling_type="symmetric")
        vL = track_front_velocity_L124(delta=delta, coupling_type="symmetric")
        if vR is None:
            vR_str = "    None"
            pass_R = False
        else:
            vR_str = f"{vR:+.6f}"
            pass_R = abs(vR - TARGET_R) < TOL
        if vL is None:
            vL_str = "    None"
            pass_L = False
        else:
            vL_str = f"{vL:+.6f}"
            pass_L = abs(vL - TARGET_L) < TOL
        both = pass_R and pass_L
        marker = " *** PASS ***" if both else ""
        print(f"  delta={delta:+4d}:  {vR_str}  {vL_str}  {'✓' if pass_R else '✗':>8}  {'✓' if pass_L else '✗':>8}  {'YES' if both else 'NO':>6}{marker}")
        results[delta] = (vR, vL, pass_R, pass_L, both)

    print()
    passing = [d for d, (vR, vL, pR, pL, b) in results.items() if b]
    if passing:
        print(f"PASSING DELTAS (both v_R and v_L preserved): {passing}")
    else:
        print("NO PASSING DELTAS — no symmetric diagonal coupling preserves both gliders.")

    # ---- Task B: Physically motivated deltas ----
    print()
    print("="*60)
    print("TASK B: Physically motivated offsets")
    print("="*60)

    b_deltas = [2, 7, 14, 42]
    print(f"{'delta':>8}  {'v_R':>10}  {'v_L':>10}  {'BOTH?':>6}  Notes")
    print("-"*70)

    for delta in b_deltas:
        vR = track_front_velocity(delta=delta, coupling_type="symmetric")
        vL = track_front_velocity_L124(delta=delta, coupling_type="symmetric")
        if vR is None:
            vR_str = "    None"
            pass_R = False
        else:
            vR_str = f"{vR:+.6f}"
            pass_R = abs(vR - TARGET_R) < TOL
        if vL is None:
            vL_str = "    None"
            pass_L = False
        else:
            vL_str = f"{vL:+.6f}"
            pass_L = abs(vL - TARGET_L) < TOL
        both = pass_R and pass_L
        notes = ""
        if delta == 2:
            notes = "1 glider-period displacement"
        elif delta == 7:
            notes = "half ether period"
        elif delta == 14:
            notes = "full ether period (should ≈ delta=0)"
        elif delta == 42:
            notes = "lcm(3,14) — should ≡ delta=0"
        print(f"  delta={delta:+4d}:  {vR_str}  {vL_str}  {'YES' if both else 'NO':>6}  {notes}")

    print()
    print("Asymmetric chiral coupling (delta=2):")
    vR_asym = track_front_velocity(delta=2, coupling_type="asymmetric")
    vL_asym = track_front_velocity_L124(delta=2, coupling_type="asymmetric")
    vR_asym_str = f"{vR_asym:+.6f}" if vR_asym is not None else "    None"
    vL_asym_str = f"{vL_asym:+.6f}" if vL_asym is not None else "    None"
    pass_R_asym = vR_asym is not None and abs(vR_asym - TARGET_R) < TOL
    pass_L_asym = vL_asym is not None and abs(vL_asym - TARGET_L) < TOL
    print(f"  v_R = {vR_asym_str}  ({'✓' if pass_R_asym else '✗'})")
    print(f"  v_L = {vL_asym_str}  ({'✓' if pass_L_asym else '✗'})")
    print(f"  Both: {'YES' if pass_R_asym and pass_L_asym else 'NO'}")

    # ---- Task C: Analytical check ----
    escape_deltas = analyze_ether_phase_sequences()

    # ---- Summary ----
    print()
    print("="*60)
    print("SUMMARY")
    print("="*60)
    all_passing = [d for d, (vR, vL, pR, pL, b) in results.items() if b]
    print(f"Deltas with both v_R and v_L preserved: {all_passing if all_passing else 'NONE'}")
    print(f"Escape deltas from no-go (period divides 3): {escape_deltas if escape_deltas else 'NONE'}")
    if not all_passing and not escape_deltas:
        print()
        print("CONCLUSION: Trajectory-orbit no-go extends to ALL tested diagonal offsets.")
        print("No diagonal coupling preserves both gliders. The no-go is FULLY GENERAL")
        print("for any cell-level coupling (vertical or diagonal).")
    elif escape_deltas and not all_passing:
        print()
        print("NOTE: Analytical escape deltas found but computational test still fails.")
        print("This would indicate the escape is theoretical but practically ineffective —")
        print("or that the delta-specific ether-phase reduction is insufficient alone.")
    elif all_passing:
        print()
        print("*** COUP DE GRÂCE: DIAGONAL COUPLING ESCAPE FOUND ***")
        print(f"Deltas {all_passing} preserve both gliders!")


if __name__ == "__main__":
    main()
