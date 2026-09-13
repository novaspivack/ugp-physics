"""
Z5 Transitivity Check — Rule 110 on p-cell periodic rings
==========================================================
For each prime p in [2, 3, 5, 7, 11, 13, 17, 19, 23]:
  - Enumerate all binary vectors of length p with Hamming weight 3
  - For each such vector v, check whether ALL p cyclic rotations of v
    satisfy: after exactly 2 Rule 110 steps on the p-cell periodic ring,
    the result is the all-ones vector.
  - Report: for which primes does ANY weight-3 vector have this full
    transitivity? For which does EVERY weight-3 vector have it?

This property is the Z5 "full transitivity" in EPIC_070 Spec 06:
  rotate(v, k) → s1 → all-ones  (for ALL k = 0, 1, ..., p-1)
where s1 = Rule110(rotate(v,k)) and 2nd step gives all-ones.

The "3-state orbit" consists of 3 distinct states: rotate(v,k), s1, all-ones.

Reference: CUP-4 / CUP-9 for the p=5 case: smGen1 = [1,1,0,0,1] has
this property. All 5 cyclic rotations of smGen1 satisfy the orbit
smGen1 → smGen2 → smGen3 = all-ones.
"""

import itertools
from typing import Tuple

# Rule 110 lookup table: bit i of 110 gives the output for neighborhood index i
RULE110 = [(110 >> i) & 1 for i in range(8)]


def apply_rule110_periodic(state: Tuple[int, ...]) -> Tuple[int, ...]:
    """Apply Rule 110 to a state on a periodic ring of length len(state)."""
    n = len(state)
    result = []
    for i in range(n):
        l = state[(i - 1) % n]
        c = state[i]
        r = state[(i + 1) % n]
        idx = 4 * l + 2 * c + r
        result.append(RULE110[idx])
    return tuple(result)


def cyclic_shifts(v: Tuple[int, ...]) -> list:
    """Return all cyclic rotations of v (including v itself at shift 0)."""
    n = len(v)
    return [tuple(v[(i + k) % n] for i in range(n)) for k in range(n)]


def all_ones(n: int) -> Tuple[int, ...]:
    return tuple(1 for _ in range(n))


def has_full_transitivity(v: Tuple[int, ...]) -> bool:
    """
    Return True iff ALL cyclic rotations of v reach all-ones in exactly 2
    Rule 110 steps on the periodic ring of length len(v).
    """
    p = len(v)
    target = all_ones(p)
    for shifted in cyclic_shifts(v):
        s1 = apply_rule110_periodic(shifted)
        s2 = apply_rule110_periodic(s1)
        if s2 != target:
            return False
    return True


def canonical(v: Tuple[int, ...]) -> Tuple[int, ...]:
    """Canonical form of a cyclic equivalence class (lexicographic minimum rotation)."""
    return min(cyclic_shifts(v))


def analyze_prime(p: int) -> dict:
    """
    Analyze all weight-3 binary vectors of length p under Rule 110.

    Returns a dict with:
      'total_weight3': total count of weight-3 vectors
      'canonical_count': number of distinct cyclic equivalence classes
      'full_transitivity': number of classes with full transitivity
      'partial_transitivity': number of classes with some (but not all) rotations reaching all-ones
      'none_reach_allones': number of classes where NO rotation reaches all-ones in 2 steps
      'transitive_vectors': list of canonical representatives with full transitivity
      'class_details': list of (canonical, fraction_reaching_allones) per class
    """
    if p < 3:
        # Cannot have Hamming weight 3 with fewer than 3 cells
        return {
            'total_weight3': 0,
            'canonical_count': 0,
            'full_transitivity': 0,
            'partial_transitivity': 0,
            'none_reach_allones': 0,
            'transitive_vectors': [],
            'class_details': [],
        }

    # Enumerate all weight-3 vectors
    transitive_vectors = []
    canonical_classes = {}  # canonical form → list of (vector, fraction)

    for positions in itertools.combinations(range(p), 3):
        v = tuple(1 if i in positions else 0 for i in range(p))
        can = canonical(v)
        if can not in canonical_classes:
            canonical_classes[can] = []
        canonical_classes[can].append(v)

    class_details = []
    full_count = 0
    partial_count = 0
    none_count = 0
    transitive_canonical = []

    for can, vecs in canonical_classes.items():
        # Check the canonical representative
        shifts = cyclic_shifts(can)
        count_reaching = 0
        target = all_ones(p)
        for shifted in shifts:
            s1 = apply_rule110_periodic(shifted)
            s2 = apply_rule110_periodic(s1)
            if s2 == target:
                count_reaching += 1
        fraction = count_reaching / len(shifts)
        class_details.append((can, count_reaching, len(shifts), fraction))

        if count_reaching == p:
            full_count += 1
            transitive_canonical.append(can)
        elif count_reaching > 0:
            partial_count += 1
        else:
            none_count += 1

    return {
        'total_weight3': sum(len(v) for v in canonical_classes.values()),
        'canonical_count': len(canonical_classes),
        'full_transitivity': full_count,
        'partial_transitivity': partial_count,
        'none_reach_allones': none_count,
        'transitive_vectors': transitive_canonical,
        'class_details': sorted(class_details, key=lambda x: -x[2]),
    }


def main():
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]

    print("=" * 70)
    print("Z5 TRANSITIVITY CHECK — Rule 110 on p-cell periodic rings")
    print("Condition: ALL cyclic rotations of v reach all-ones in 2 Rule 110 steps")
    print("=" * 70)
    print()

    print(f"{'p':>4} | {'C(p,3)':>7} | {'classes':>7} | {'full':>6} | {'partial':>8} | {'none':>5} | Transitive canonical vectors")
    print("-" * 90)

    results = {}
    for p in primes:
        r = analyze_prime(p)
        results[p] = r
        trans = r['transitive_vectors']
        trans_str = str(trans[:3]) + ("..." if len(trans) > 3 else "") if trans else "—"
        print(f"{p:>4} | {r['total_weight3']:>7} | {r['canonical_count']:>7} | {r['full_transitivity']:>6} | {r['partial_transitivity']:>8} | {r['none_reach_allones']:>5} | {trans_str}")

    print()
    print("Columns: full = classes where ALL rotations reach all-ones in 2 steps")
    print("         partial = some rotations reach all-ones, not all")
    print("         none = no rotation reaches all-ones in 2 steps")
    print()

    print("=" * 70)
    print("DETAILED RESULTS BY PRIME")
    print("=" * 70)
    for p in primes:
        r = results[p]
        print(f"\np={p}:")
        if r['total_weight3'] == 0:
            print("  No weight-3 vectors exist (p < 3)")
            continue

        print(f"  Total weight-3 vectors: {r['total_weight3']} in {r['canonical_count']} cyclic equivalence classes")
        print(f"  Full transitivity (ALL {p} rotations reach all-ones in 2 steps): {r['full_transitivity']} class(es)")
        print(f"  Partial transitivity: {r['partial_transitivity']} class(es)")
        print(f"  No transitivity: {r['none_reach_allones']} class(es)")

        if r['transitive_vectors']:
            print(f"  FULL-TRANSITIVE canonical representatives:")
            for can in r['transitive_vectors']:
                print(f"    {list(can)}")
            # Show the orbit for p=5 explicitly
            if p == 5:
                print(f"  Verifying p=5 orbit for smGen1=[1,1,0,0,1]:")
                smgen1 = (1, 1, 0, 0, 1)
                for k, shifted in enumerate(cyclic_shifts(smgen1)):
                    s1 = apply_rule110_periodic(shifted)
                    s2 = apply_rule110_periodic(s1)
                    ok = "✓" if s2 == all_ones(p) else "✗"
                    print(f"    k={k}: {list(shifted)} → {list(s1)} → {list(s2)} {ok}")

        # Show details for partial-transitivity classes if any
        partial_classes = [(can, rc, total, frac)
                           for (can, rc, total, frac) in r['class_details']
                           if 0 < rc < total]
        if partial_classes and p <= 7:
            print(f"  Partial-transitivity details:")
            for can, rc, total, frac in partial_classes[:5]:
                print(f"    {list(can)}: {rc}/{total} rotations reach all-ones")

    print()
    print("=" * 70)
    print("SUMMARY: Which primes have at least one full-transitivity class?")
    print("=" * 70)
    for p in primes:
        r = results[p]
        status = "YES — FULL TRANSITIVITY" if r['full_transitivity'] > 0 else "no"
        print(f"  p={p}: {status} ({r['full_transitivity']} class(es))")

    print()
    print("=" * 70)
    print("UNIQUENESS VERDICT")
    print("=" * 70)
    primes_with_full = [p for p in primes if results[p]['full_transitivity'] > 0]
    if primes_with_full == [5]:
        print("✓ p=5 is the UNIQUE prime ≤ 23 with a Hamming-3 full-transitivity vector")
        print("  under Rule 110. The uniqueness theorem (z5_transitivity_uniqueness) is TRUE.")
    else:
        print(f"✗ Primes with full transitivity: {primes_with_full}")
        print("  The theorem as stated is FALSE. Reformulation needed.")
        print("  See partial results and check for alternative unique property.")

    # Extra analysis: check 1-step orbit (reaches all-ones in 1 step)
    print()
    print("=" * 70)
    print("BONUS: Hamming-3 vectors reaching all-ones in EXACTLY 1 Rule 110 step")
    print("=" * 70)
    for p in primes:
        if p < 3:
            continue
        target = all_ones(p)
        one_step_classes = set()
        for positions in itertools.combinations(range(p), 3):
            v = tuple(1 if i in positions else 0 for i in range(p))
            s1 = apply_rule110_periodic(v)
            if s1 == target:
                one_step_classes.add(canonical(v))
        if one_step_classes:
            print(f"  p={p}: {len(one_step_classes)} class(es) reach all-ones in 1 step: {[list(c) for c in sorted(one_step_classes)]}")
        else:
            print(f"  p={p}: none reach all-ones in 1 step")


if __name__ == "__main__":
    main()
