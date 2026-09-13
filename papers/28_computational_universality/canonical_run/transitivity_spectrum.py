"""
Rule 110 Transitivity Spectrum — full (p, w, t) sweep
======================================================
Extends z5_transitivity_check.py to enumerate ALL (p, w, t) triples where
Rule 110 exhibits full cyclic transitivity on a p-cell periodic ring:

  For a weight-w binary vector v of length p:
  "full transitivity at (p, w, t)" means ALL p cyclic rotations of v
  reach the all-ones vector in exactly t Rule 110 steps.

Sweep parameters:
  p ∈ {2, 3, 5, 7, 11}   (primes; 11 is the limit for practical computation)
  w ∈ {1, 2, 3, 4}        (Hamming weights)
  t ∈ {1, 2, 3, 4}        (step counts)

The key question: is p=5 the unique prime with ANY full-transitivity class
across ALL (w, t) pairs?
"""

import itertools
from typing import Tuple, Dict, List, Optional

RULE110 = [(110 >> i) & 1 for i in range(8)]


def apply_rule110_periodic(state: Tuple[int, ...]) -> Tuple[int, ...]:
    n = len(state)
    result = []
    for i in range(n):
        l = state[(i - 1) % n]
        c = state[i]
        r = state[(i + 1) % n]
        idx = 4 * l + 2 * c + r
        result.append(RULE110[idx])
    return tuple(result)


def apply_t_steps(state: Tuple[int, ...], t: int) -> Tuple[int, ...]:
    s = state
    for _ in range(t):
        s = apply_rule110_periodic(s)
    return s


def cyclic_shifts(v: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    n = len(v)
    return [tuple(v[(i + k) % n] for i in range(n)) for k in range(n)]


def canonical(v: Tuple[int, ...]) -> Tuple[int, ...]:
    return min(cyclic_shifts(v))


def all_ones(n: int) -> Tuple[int, ...]:
    return tuple(1 for _ in range(n))


def hamming_weight(v: Tuple[int, ...]) -> int:
    return sum(v)


def has_full_transitivity_t(v: Tuple[int, ...], t: int) -> bool:
    """All cyclic rotations of v reach all-ones in exactly t steps."""
    p = len(v)
    target = all_ones(p)
    for shifted in cyclic_shifts(v):
        if apply_t_steps(shifted, t) != target:
            return False
    return True


def analyze_spectrum_entry(p: int, w: int, t: int) -> Dict:
    """
    Find all cyclic equivalence classes of weight-w vectors on the p-ring
    with full transitivity at step t.

    Returns: {'full': count, 'partial': count, 'none': count,
              'transitive_canonical': list of canonical representatives}
    """
    if p < w:
        return {'full': 0, 'partial': 0, 'none': 0, 'transitive_canonical': []}

    target = all_ones(p)
    canonical_seen = set()
    full_count = 0
    partial_count = 0
    none_count = 0
    transitive_canonical = []

    for positions in itertools.combinations(range(p), w):
        v = tuple(1 if i in positions else 0 for i in range(p))
        can = canonical(v)
        if can in canonical_seen:
            continue
        canonical_seen.add(can)

        shifts = cyclic_shifts(can)
        reach_count = sum(1 for s in shifts if apply_t_steps(s, t) == target)

        if reach_count == p:
            full_count += 1
            transitive_canonical.append(can)
        elif reach_count > 0:
            partial_count += 1
        else:
            none_count += 1

    return {
        'full': full_count,
        'partial': partial_count,
        'none': none_count,
        'transitive_canonical': transitive_canonical,
    }


def main():
    primes = [2, 3, 5, 7, 11]
    weights = [1, 2, 3, 4]
    steps = [1, 2, 3, 4]

    print("=" * 80)
    print("RULE 110 TRANSITIVITY SPECTRUM — full (p, w, t) sweep")
    print("Full transitivity: ALL p cyclic rotations of a weight-w length-p vector")
    print("reach the all-ones vector in exactly t Rule 110 steps.")
    print("=" * 80)
    print()

    # Collect all (p, w, t) with at least one full-transitive class
    hits = []

    print(f"{'p':>4} {'w':>3} {'t':>3} | {'full':>6} {'partial':>8} | Canonical transitive vectors")
    print("-" * 80)

    for p in primes:
        for w in weights:
            if w >= p:
                continue  # weight must be < p (all-ones is target so w < p needed)
            for t in steps:
                r = analyze_spectrum_entry(p, w, t)
                if r['full'] > 0 or r['partial'] > 0:
                    trans_str = str([list(c) for c in r['transitive_canonical'][:2]])
                    if len(r['transitive_canonical']) > 2:
                        trans_str += f"... ({r['full']} total)"
                    print(f"{p:>4} {w:>3} {t:>3} | {r['full']:>6} {r['partial']:>8} | {trans_str}")
                    if r['full'] > 0:
                        hits.append((p, w, t, r['full'], r['transitive_canonical']))
                # Always store result for the summary table
            # Separator between weight blocks
        print()

    print()
    print("=" * 80)
    print("FULL TRANSITIVITY HITS (p, w, t) WITH AT LEAST ONE FULL-TRANSITIVE CLASS")
    print("=" * 80)
    if not hits:
        print("  None found.")
    else:
        for p, w, t, count, canon_list in hits:
            print(f"  p={p}, w={w}, t={t}: {count} class(es) — canonical: {[list(c) for c in canon_list[:3]]}")

    print()
    print("=" * 80)
    print("SUMMARY TABLE: full-transitive (p, w, t) pairs")
    print("Row = prime p, Col = (w, t), cell = # full-transitive classes")
    print("=" * 80)
    print()

    # Summary table
    header = "p \\ (w,t) |"
    cols = [(w, t) for w in weights for t in steps]
    print(header + " ".join(f"({w},{t})" for w, t in cols))
    print("-" * (len(header) + 7 * len(cols)))
    for p in primes:
        row = f"p={p}       |"
        for w, t in cols:
            if w >= p:
                row += "  -  "
            else:
                r = analyze_spectrum_entry(p, w, t)
                if r['full'] > 0:
                    row += f"  {r['full']}  "
                else:
                    row += "  .  "
        print(row)

    print()
    print("=" * 80)
    print("UNIQUENESS VERDICT")
    print("=" * 80)
    primes_with_any_full = set(p for p, w, t, count, _ in hits)
    if primes_with_any_full == {5} or primes_with_any_full.issubset({5}):
        print("✓ p=5 is the UNIQUE prime (among p ≤ 11) with ANY full-transitivity class")
        print("  across ALL (w, t) combinations tested.")
        print("  This strongly suggests: Rule 110 full Z_p transitivity is exclusive to Z₅.")
    else:
        other = primes_with_any_full - {5}
        print(f"✗ Other primes with full transitivity: {sorted(other)}")
        print("  p=5 is NOT universally unique.")
        if 5 in primes_with_any_full:
            p5_hits = [(w, t, count) for pp, w, t, count, _ in hits if pp == 5]
            print(f"  p=5 full-transitivity triples: {p5_hits}")
        other_hits = [(pp, w, t, count) for pp, w, t, count, _ in hits if pp != 5]
        print(f"  Other hits: {other_hits}")

    print()
    print("=" * 80)
    print("DETAILED p=5 SPECTRUM (all (w,t) pairs)")
    print("=" * 80)
    for w in weights:
        if w >= 5:
            continue
        for t in steps:
            r = analyze_spectrum_entry(5, w, t)
            status = "FULL" if r['full'] > 0 else ("PARTIAL" if r['partial'] > 0 else "none")
            canonical_str = [list(c) for c in r['transitive_canonical'][:3]]
            print(f"  (w={w}, t={t}): {r['full']} full, {r['partial']} partial, {r['none']} none — {status}"
                  + (f" {canonical_str}" if r['full'] > 0 else ""))

    print()
    print("=" * 80)
    print("PARTIAL TRANSITIVITY DETAILS FOR p=5 (some but not all rotations reach all-ones)")
    print("(these are the 'weak' transitivity classes that Rank 25 asked about)")
    print("=" * 80)
    for w in weights:
        if w >= 5:
            continue
        for t in steps:
            r = analyze_spectrum_entry(5, w, t)
            if r['partial'] > 0:
                print(f"\n  p=5, w={w}, t={t}: {r['partial']} partial-transitive class(es)")
                # Find them
                target = all_ones(5)
                seen = set()
                for positions in itertools.combinations(range(5), w):
                    v = tuple(1 if i in positions else 0 for i in range(5))
                    can = canonical(v)
                    if can in seen:
                        continue
                    seen.add(can)
                    shifts = cyclic_shifts(can)
                    reach_count = sum(1 for s in shifts if apply_t_steps(s, t) == target)
                    if 0 < reach_count < 5:
                        print(f"    {list(can)}: {reach_count}/5 rotations reach all-ones")
                        for k, s in enumerate(shifts):
                            result = apply_t_steps(s, t)
                            ok = "✓" if result == target else "✗"
                            print(f"      k={k}: {list(s)} →^{t} {list(result)} {ok}")


if __name__ == "__main__":
    main()
