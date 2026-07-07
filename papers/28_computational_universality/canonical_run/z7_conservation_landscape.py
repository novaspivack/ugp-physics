#!/usr/bin/env python3
"""
z7_conservation_landscape.py — Z₇ sum conservation structure for all seven sum values.

Spec 01 (SPEC_070_01_QKR) characterized sum-4-conserving states:
exactly 10 out of 2401 sum-4 states conserve (5 rotations of gen1 + 5 rotations of alt=[0,2,5,2,2]).

This script extends the analysis to ALL 7 sum values (0-6):
  conserving_count(v) = |{s ∈ Z₇⁵ : z7_sum(s) = v ∧ z7_sum(fmdl_step5(s)) = v}|

Key questions:
  (a) Is sum=4 uniquely sparse among all sum values?
  (b) What conserving states exist for other sum values?
  (c) Are the SM orbit states (gen2, gen3) in the non-conserving majority?

Results feed into Rank 27 Lean certification.
"""

import itertools
from collections import defaultdict
from typing import Dict, List, Tuple

# ── fmdl and fmdl_step5 (matching CUP3DUniqueness.lean exactly) ──
_FMDL_LOOKUP: Dict[Tuple[int,int,int], int] = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}

def fmdl(l: int, c: int, r: int) -> int:
    return _FMDL_LOOKUP.get((l, c, r), 0)

def fmdl_step5(state: Tuple[int,...]) -> Tuple[int,...]:
    n = 5
    return tuple(fmdl(state[(i-1)%n], state[i], state[(i+1)%n]) for i in range(n))

def z7_sum(s: Tuple[int,...]) -> int:
    return sum(s) % 7

GEN1:   Tuple[int,...] = (1, 5, 2, 2, 1)
GEN2:   Tuple[int,...] = (2, 5, 2, 0, 2)
GEN3:   Tuple[int,...] = (5, 6, 5, 3, 5)
VACUUM: Tuple[int,...] = (0, 0, 0, 0, 0)
ALT:    Tuple[int,...] = (0, 2, 5, 2, 2)   # secondary sum-4 orbit (from Spec 01)

def cyclic_rotations(s: Tuple[int,...]) -> List[Tuple[int,...]]:
    return [tuple(s[(i+k)%5] for i in range(5)) for k in range(5)]

def identify_state(s: Tuple[int,...]) -> str:
    """Return a human-readable label for special states."""
    for k in range(5):
        if s == tuple(GEN1[(i+k)%5] for i in range(5)):
            return f"gen1 rotation k={k}"
    for k in range(5):
        if s == tuple(GEN2[(i+k)%5] for i in range(5)):
            return f"gen2 rotation k={k}"
    for k in range(5):
        if s == tuple(GEN3[(i+k)%5] for i in range(5)):
            return f"gen3 rotation k={k}"
    for k in range(5):
        if s == tuple(ALT[(i+k)%5] for i in range(5)):
            return f"alt=[0,2,5,2,2] rotation k={k}"
    if s == VACUUM:
        return "vacuum"
    return ""


def main() -> None:
    print("z7_conservation_landscape.py — Complete Z₇ sum conservation analysis")
    print("=" * 75)
    print(f"State space: Z₇⁵ = 7^5 = {7**5} states")
    print()

    # Verify Spec 01 orbit results
    assert fmdl_step5(GEN1) == GEN2
    assert fmdl_step5(GEN2) == GEN3
    assert fmdl_step5(GEN3) == VACUUM
    assert z7_sum(GEN1) == 4, f"gen1 sum = {z7_sum(GEN1)}, expected 4"
    assert z7_sum(GEN2) == 4, f"gen2 sum = {z7_sum(GEN2)}, expected 4"
    assert z7_sum(GEN3) == 3, f"gen3 sum = {z7_sum(GEN3)}, expected 3"
    assert z7_sum(VACUUM) == 0
    print("✓ Orbit and sum values verified")
    print(f"  z7_sum(gen1)={z7_sum(GEN1)}, z7_sum(gen2)={z7_sum(GEN2)}, "
          f"z7_sum(gen3)={z7_sum(GEN3)}, z7_sum(vacuum)={z7_sum(VACUUM)}")
    print()

    # Full sweep: compute conservation landscape for all sum values
    print("Running exhaustive sweep over all 16,807 states...")

    # For each sum value v: count of states with that sum, and count conserving
    by_sum: Dict[int, List[Tuple[int,...]]] = defaultdict(list)
    conserving: Dict[int, List[Tuple[int,...]]] = defaultdict(list)

    for state in itertools.product(range(7), repeat=5):
        v = z7_sum(state)
        by_sum[v].append(state)
        output = fmdl_step5(state)
        v_out = z7_sum(output)
        if v_out == v:
            conserving[v].append(state)

    print("✓ Sweep complete")
    print()

    # Report
    print("=" * 75)
    print("Z₇ Sum Conservation Landscape:")
    print(f"{'Sum v':8} {'Total states':14} {'Conserving':12} {'Fraction (%)':14} {'Remark'}")
    print("-" * 75)

    for v in range(7):
        total = len(by_sum[v])
        n_con = len(conserving[v])
        frac = 100 * n_con / total if total > 0 else 0
        remark = ""
        if v == 4:
            remark = "← SM gen1/gen2 sum (Spec 01: RAREST)"
        elif v == 3:
            remark = "← SM gen3 sum"
        elif v == 0:
            remark = "← vacuum sum"
        print(f"  v={v}      {total:8d}        {n_con:8d}      {frac:6.2f}%     {remark}")

    print()

    # Check Spec 01 result: sum=4, count=10
    spec01_count = len(conserving[4])
    spec01_states = conserving[4]
    print(f"✓ Spec 01 cross-check: sum-4 conserving count = {spec01_count} (expected 10)")
    assert spec01_count == 10, f"ERROR: expected 10, got {spec01_count}"
    gen1_rots = set(cyclic_rotations(GEN1))
    alt_rots = set(cyclic_rotations(ALT))
    for s in spec01_states:
        assert tuple(s) in gen1_rots or tuple(s) in alt_rots, \
            f"Unexpected sum-4 conserving state: {s}"
    print("✓ Spec 01 characterization confirmed: exactly gen1 rotations + alt rotations")
    print()

    # Detailed analysis of each sum value
    print("=" * 75)
    print("Detailed analysis by sum value:")
    print()

    for v in range(7):
        con_states = conserving[v]
        n = len(con_states)
        print(f"  Sum v={v}: {n} conserving states out of {len(by_sum[v])}")

        # Identify any special states
        special = [(s, identify_state(s)) for s in con_states if identify_state(s)]
        if special:
            for s, label in special:
                print(f"    → {s}  [{label}]")

        # Orbit structure: group by cyclic equivalence class
        seen = set()
        orbit_classes = []
        for s in con_states:
            st = tuple(s)
            if st not in seen:
                rots = set(cyclic_rotations(st))
                orbit_classes.append(rots)
                seen.update(rots)
        orbit_classes_in_conserving = []
        for cls in orbit_classes:
            members_in_conserving = [s for s in cls if tuple(s) in [tuple(x) for x in con_states]]
            if members_in_conserving:
                orbit_classes_in_conserving.append(members_in_conserving)

        if n > 0 and n <= 50:
            n_full_orbits = sum(1 for cls in orbit_classes
                                if all(tuple(r) in [tuple(x) for x in con_states] for r in cls))
            print(f"    Cyclic orbit classes (fully conserving): ~{n_full_orbits}")
        print()

    # Key structural findings
    print("=" * 75)
    print("KEY STRUCTURAL FINDINGS (Rank 27):")
    print()

    counts = {v: len(conserving[v]) for v in range(7)}
    min_v = min(counts, key=lambda v: counts[v] if v != 0 else 999999)
    # Note: sum=0 has vacuum which contributes many states
    print(f"  Conservation counts: {counts}")
    print()

    # Is sum=4 uniquely sparse among non-zero sums?
    non_zero_counts = {v: counts[v] for v in range(1, 7)}
    min_nonzero_v = min(non_zero_counts, key=non_zero_counts.get)
    print(f"  Minimum conserving count among non-zero sums: v={min_nonzero_v} ({non_zero_counts[min_nonzero_v]} states)")
    is_unique_min = sum(1 for v, c in non_zero_counts.items() if c == min(non_zero_counts.values())) == 1
    print(f"  Sum=4 is uniquely sparse? {'✓ YES' if min_nonzero_v == 4 else '✗ NO (v=' + str(min_nonzero_v) + ' is sparser)'}")
    print()

    # Gen3 (sum=3): any conserving states besides...
    con3 = conserving[3]
    gen3_rots = set(cyclic_rotations(GEN3))
    gen3_in_con3 = [s for s in con3 if tuple(s) in gen3_rots]
    non_gen3_con3 = [s for s in con3 if tuple(s) not in gen3_rots]
    print(f"  Sum=3 conserving states: {len(con3)} total")
    print(f"    gen3 rotations conserving: {len(gen3_in_con3)}")
    print(f"    Other states conserving: {len(non_gen3_con3)}")
    if gen3_in_con3:
        print(f"    Note: gen3 is NOT a conserving state (gen3 maps to vacuum with sum=0 ≠ 3)")
    print()
    # Actually verify gen3 is NOT sum-conserving
    assert z7_sum(GEN3) != z7_sum(VACUUM), "gen3→vacuum breaks sum conservation"
    gen3_conserves = any(tuple(s) == GEN3 for s in con3)
    print(f"  gen3 is a conserving state for sum=3? {'YES' if gen3_conserves else '✓ NO (gen3 maps to vacuum, sum breaks 3→0)'}")
    print()

    # Lean theorem targets
    print("=" * 75)
    print("LEAN CERTIFICATION TARGETS (CatAL via native_decide):")
    print()
    print("  theorem z7_conservation_count_table :")
    for v in range(7):
        print(f"    z7_conserving_count {v} = {counts[v]} ∧")
    print("    True := by native_decide")
    print()
    print("  theorem z7_sum4_is_uniquely_sparse_nonzero :")
    print("    ∀ v : Fin 7, v ≠ 0 → v ≠ 4 →")
    print(f"      z7_conserving_count v > {counts[4]} := by native_decide")
    print()
    print("  theorem z7_gen3_not_sum_conserving :")
    print("    z7_sum (fmdl_step5 fmdl_gen3_z7) ≠ z7_sum fmdl_gen3_z7 := by decide")
    print()
    print("  theorem z7_vacuum_sum_conservation :")
    print("    z7_sum (fmdl_step5 fmdl_vacuum_z7) = z7_sum fmdl_vacuum_z7 := by decide")


if __name__ == "__main__":
    main()
