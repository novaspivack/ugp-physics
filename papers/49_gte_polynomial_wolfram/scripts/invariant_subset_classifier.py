#!/usr/bin/env python3
"""
invariant_subset_classifier.py — Exhaustive invariant subset classification for p mod 7.

Verifies Theorem 4.2 computationally: among all 128 non-empty subsets of Z₇,
exactly three are closed (invariant) under p(L,C,R) = C + R - C*R - L*C*R (mod 7):

  {0}          — vacuum singleton (trivially closed)
  {0, 1}       — binary sublayer = Rule 110 ether (the unique proper non-trivial invariant set)
  Z₇           — full space (trivially closed)

The uniqueness of {0,1} as the proper non-trivial invariant subset is the
computational certificate for: Rule 110 is the unique maximal proper sub-CA
of the GTE polynomial on Z₇.

Also checks SM-motivated subsets and reports their first failure witness.

Output: printed table (no figure generated — pure computation).

Lean certification: p_poly_invariant_subsets_classification, CatAL
  (UgpLean/Universality/Z7InvariantSubsets.lean)

Dependencies: none (pure Python)
"""

import time
from itertools import combinations
from typing import Optional, Tuple

TIMEOUT_SECONDS = 30


def p_poly(L: int, C: int, R: int) -> int:
    """GTE polynomial p(L,C,R) = C + R - C*R - L*C*R (mod 7)."""
    return (C + R - C * R - L * C * R) % 7


def is_invariant(subset: frozenset) -> bool:
    """Return True iff `subset` is closed under p(L,C,R) for all L,C,R in subset."""
    for L in subset:
        for C in subset:
            for R in subset:
                if p_poly(L, C, R) not in subset:
                    return False
    return True


def first_failure(subset: frozenset) -> Optional[Tuple[int, int, int, int]]:
    """Return the first (L, C, R, output) tuple that escapes `subset`, or None."""
    for L in subset:
        for C in subset:
            for R in subset:
                out = p_poly(L, C, R)
                if out not in subset:
                    return (L, C, R, out)
    return None


def classify_all_subsets():
    """Exhaustively check all 128 non-empty subsets of Z₇."""
    Z7 = list(range(7))
    invariant_subsets = []
    total_checked = 0

    for size in range(1, 8):
        for combo in combinations(Z7, size):
            s = frozenset(combo)
            total_checked += 1
            if is_invariant(s):
                invariant_subsets.append(s)

    return invariant_subsets, total_checked


def check_sm_motivated_subsets():
    """Check physically-motivated subsets and report their failure witnesses."""
    sm_subsets = [
        (frozenset({0, 1, 2}),       "binary + up quark (0,1,2)"),
        (frozenset({0, 1, 2, 3}),    "binary + up + W (0,1,2,3)"),
        (frozenset({0, 1, 2, 5}),    "GEN1 sector: ether values {0,1,2,5}"),
        (frozenset({1, 5, 2, 2, 1}), "GEN1 ring (1,5,2,2,1) — duplicates collapsed"),
        (frozenset({0, 1, 2, 3, 4}), "first five Z₇ values"),
        (frozenset({1, 2, 3, 4, 5}), "non-vacuum non-zero"),
        (frozenset({2, 5, 0, 3}),    "GEN orbit support {0,2,3,5}"),
        (frozenset({0, 1, 2, 3, 4, 5, 6}), "full Z₇ (trivial)"),
    ]

    results = []
    for s, label in sm_subsets:
        inv = is_invariant(s)
        fail = None if inv else first_failure(s)
        results.append((label, sorted(s), inv, fail))
    return results


def main():
    t0 = time.time()

    print("=" * 70)
    print("Invariant Subset Classifier — p(L,C,R) = C+R−CR−LCR (mod 7) on Z₇")
    print("=" * 70)
    print()

    # Part 1: Exhaustive classification
    print("Part 1: Exhaustive classification of all 2^7 - 1 = 127 non-empty subsets")
    print("-" * 70)

    invariant_subsets, total = classify_all_subsets()

    print(f"Total subsets checked: {total}")
    print(f"Invariant subsets found: {len(invariant_subsets)}")
    print()

    for s in sorted(invariant_subsets, key=lambda x: (len(x), sorted(x))):
        label = ""
        ss = frozenset(s)
        if ss == frozenset({0}):
            label = "  ← vacuum singleton (trivial)"
        elif ss == frozenset({0, 1}):
            label = "  ← BINARY SUBLAYER = RULE 110 (unique proper non-trivial invariant set)"
        elif len(ss) == 7:
            label = "  ← full Z₇ (trivial)"
        print(f"  {sorted(s)}{label}")

    print()
    assert len(invariant_subsets) == 3, (
        f"Expected exactly 3 invariant subsets, found {len(invariant_subsets)}: "
        f"{[sorted(s) for s in invariant_subsets]}"
    )
    assert frozenset({0}) in invariant_subsets
    assert frozenset({0, 1}) in invariant_subsets
    assert frozenset(range(7)) in invariant_subsets
    print("PASS: Exactly 3 invariant subsets confirmed: {0}, {0,1}, Z₇")
    print("PASS: {0,1} is the unique proper non-trivial invariant subset")
    print()

    # Part 2: SM-motivated subsets
    print("Part 2: SM-motivated subset failure witnesses")
    print("-" * 70)
    print(f"{'Subset label':<45} {'Elements':<25} {'Invariant?'}")
    print("-" * 70)

    sm_results = check_sm_motivated_subsets()
    for label, elems, inv, fail in sm_results:
        status = "YES" if inv else "NO"
        print(f"  {label:<43} {str(elems):<25} {status}")
        if fail:
            L, C, R, out = fail
            print(f"    Failure witness: p({L},{C},{R}) = {out} ∉ {elems}")

    print()

    # Part 3: Verify the key Lean counterexample cited in Z7InvariantSubsets.lean
    print("Part 3: Key Lean counterexample (from Z7InvariantSubsets.lean)")
    print("-" * 70)
    test_cases = [
        ((1, 1, 5), 2, "f_MDL(1,1,5)=2 but p_poly(1,1,5)"),
        ((1, 5, 2), None, "critical GEN1→GEN2 triple"),
        ((0, 1, 1), None, "binary Rule 110 triple (should match both)"),
    ]
    for (l, c, r), expected_fmdl, note in test_cases:
        out = p_poly(l, c, r)
        print(f"  p_poly({l},{c},{r}) = {out}  [{note}]")

    print()
    elapsed = time.time() - t0
    print(f"Completed in {elapsed:.3f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
