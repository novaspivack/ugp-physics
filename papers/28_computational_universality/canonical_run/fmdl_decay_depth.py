"""
fmdl_decay_depth.py

Compute the decay depth of every state in Z₇⁵ under fmdl_step5.
Decay depth = minimum number of fmdl_step5 applications to reach the vacuum (all-zeros).

Reports:
- Full depth distribution (histogram)
- Maximum depth across all 16,807 states
- The specific states achieving maximum depth (if max > 3, print them)
- Depth profile for the SM generation orbit states (gen₁, gen₂, gen₃, vacuum)

Key question for Rank 30 / T1 conjecture:
  Is the maximum depth exactly 3 (= N_gen = number of SM generations)?
"""

from itertools import product


# ---------------------------------------------------------------------------
# fmdl: the MDL-minimal Z₇ CA function (exact match to Lean definition)
# ---------------------------------------------------------------------------

def fmdl(l: int, c: int, r: int) -> int:
    """MDL-minimal Z₇ CA function: 10 orbit + 8 binary constraints; all others → 0."""
    # Orbit neighborhoods (gen₁→gen₂ and gen₂→gen₃)
    if l == 1 and c == 1 and r == 5: return 2
    if l == 1 and c == 5 and r == 2: return 5
    if l == 5 and c == 2 and r == 2: return 2
    if l == 2 and c == 2 and r == 1: return 0
    if l == 2 and c == 1 and r == 1: return 2
    if l == 2 and c == 2 and r == 5: return 5
    if l == 2 and c == 5 and r == 2: return 6
    if l == 5 and c == 2 and r == 0: return 5
    if l == 2 and c == 0 and r == 2: return 3
    if l == 0 and c == 2 and r == 2: return 5
    # Rule 110 binary sublayer constraints
    if l == 0 and c == 0 and r == 0: return 0
    if l == 0 and c == 0 and r == 1: return 1
    if l == 0 and c == 1 and r == 0: return 1
    if l == 0 and c == 1 and r == 1: return 1
    if l == 1 and c == 0 and r == 0: return 0
    if l == 1 and c == 0 and r == 1: return 1
    if l == 1 and c == 1 and r == 0: return 1
    if l == 1 and c == 1 and r == 1: return 0
    # All remaining 325 free neighborhoods → 0 (MDL-minimal)
    return 0


def fmdl_step5(cells: tuple) -> tuple:
    """One step of fmdl on a 5-cell periodic ring. cells is a tuple of 5 Z₇ values."""
    n = 5
    return tuple(fmdl(cells[(i + 4) % n], cells[i], cells[(i + 1) % n]) for i in range(n))


# ---------------------------------------------------------------------------
# SM generation orbit states (from CUP3DUniqueness.lean definitions)
# ---------------------------------------------------------------------------
GEN1   = (1, 5, 2, 2, 1)
GEN2   = (2, 5, 2, 0, 2)
GEN3   = (5, 6, 5, 3, 5)
VACUUM = (0, 0, 0, 0, 0)


def compute_decay_depth(state: tuple, max_steps: int = 20) -> int:
    """
    Return the decay depth of `state` under fmdl_step5.
    Depth = number of applications of fmdl_step5 needed to reach VACUUM.
    Returns max_steps if VACUUM is not reached within max_steps applications.
    """
    current = state
    for step in range(1, max_steps + 1):
        current = fmdl_step5(current)
        if current == VACUUM:
            return step
    return max_steps  # Did not reach vacuum in time


def main():
    print("=" * 60)
    print("fmdl Decay Depth Analysis — Z₇⁵ full state space")
    print(f"Total states: 7^5 = {7**5:,}")
    print("=" * 60)

    # Sanity check: verify orbit
    assert fmdl_step5(GEN1) == GEN2, f"gen₁→gen₂ failed: {fmdl_step5(GEN1)}"
    assert fmdl_step5(GEN2) == GEN3, f"gen₂→gen₃ failed: {fmdl_step5(GEN2)}"
    assert fmdl_step5(GEN3) == VACUUM, f"gen₃→vacuum failed: {fmdl_step5(GEN3)}"
    print("Orbit sanity check passed: gen₁→gen₂→gen₃→vacuum ✓")

    # Depth profile for SM orbit states
    print("\nSM orbit depth profile:")
    for name, state in [("vacuum", VACUUM), ("gen₃", GEN3), ("gen₂", GEN2), ("gen₁", GEN1)]:
        if state == VACUUM:
            print(f"  {name}: depth = 0 (IS vacuum)")
        else:
            depth = compute_decay_depth(state)
            print(f"  {name}: depth = {depth}")

    # Full state space sweep
    print("\nComputing depth for all 7^5 = 16,807 states...")
    depth_distribution = {}
    max_depth_states = []
    max_depth = 0

    for cells in product(range(7), repeat=5):
        if cells == VACUUM:
            depth = 0
        else:
            depth = compute_decay_depth(cells, max_steps=20)

        depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        if depth > max_depth:
            max_depth = depth
            max_depth_states = [cells]
        elif depth == max_depth and depth > 0:
            max_depth_states.append(cells)

    print("\nDepth distribution:")
    for d in sorted(depth_distribution):
        count = depth_distribution[d]
        print(f"  depth {d}: {count:6,} states  ({100*count/7**5:.2f}%)")

    print(f"\nMaximum decay depth: {max_depth}")

    if max_depth <= 3:
        print(f"\n✅ CONJECTURE CONFIRMED: max depth = {max_depth} ≤ 3")
        print("   Universal 3-step decay theorem is TRUE.")
        print("   Lean cert target: fmdl_universal_3step_decay by native_decide")
        if max_depth < 3:
            print(f"   NOTE: actual max = {max_depth}, even shaper than conjectured max = 3")
    else:
        print(f"\n❌ CONJECTURE REFUTED: max depth = {max_depth} > 3")
        print(f"   States achieving depth {max_depth}:")
        for s in max_depth_states[:20]:
            print(f"     {list(s)}")
        if len(max_depth_states) > 20:
            print(f"     ... and {len(max_depth_states) - 20} more")

    # Report states at each depth > 0 (for physical interpretation)
    print("\nStates at each depth (up to depth 5):")
    for d in sorted(depth_distribution):
        if 0 < d <= 5:
            states_at_d = [cells for cells in product(range(7), repeat=5)
                           if cells != VACUUM and compute_decay_depth(cells, max_steps=20) == d]
            print(f"  depth {d}: {len(states_at_d)} states")
            if len(states_at_d) <= 10:
                for s in states_at_d:
                    print(f"    {list(s)}")
            else:
                print(f"    (showing first 5)")
                for s in states_at_d[:5]:
                    print(f"    {list(s)}")


if __name__ == "__main__":
    main()
