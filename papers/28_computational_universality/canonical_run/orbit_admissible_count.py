"""
orbit_admissible_count.py

Enumerate the SM orbit neighborhood constraints for fmdl: Z₇³ → Z₇,
counting the number of orbit-admissible Z₇ CA functions.

An orbit-admissible function is one that satisfies the SM generation orbit:
    fmdl_step5(gen₁) = gen₂
    fmdl_step5(gen₂) = gen₃
    fmdl_step5(gen₃) = vacuum

This imposes constraints on the function values at the 15 orbit neighborhoods
(5 ring positions × 3 orbit steps). We identify:
    - How many of these 15 are DISTINCT neighborhoods
    - Which of them have non-zero output (constraining in the MDL sense)
    - How many of the 7³ = 343 total neighborhoods are "free" (unconstrained)

The orbit-admissible count = 7^(number of free neighborhoods), since each free
neighborhood can independently map to any of 7 values.

MDL-minimal orbit-admissible function: all free neighborhoods → 0, giving fmdl.
This is the unique MDL-minimal element (7^0 = 1 choice among MDL-minimal).
"""


# ---------------------------------------------------------------------------
# SM generation orbit states
# ---------------------------------------------------------------------------
GEN1   = (1, 5, 2, 2, 1)
GEN2   = (2, 5, 2, 0, 2)
GEN3   = (5, 6, 5, 3, 5)
VACUUM = (0, 0, 0, 0, 0)

ORBIT_STATES = [GEN1, GEN2, GEN3, VACUUM]
ORBIT_NAMES  = ["gen₁", "gen₂", "gen₃", "vacuum"]


def extract_orbit_neighborhoods(source: tuple, target: tuple) -> list:
    """
    Extract the 5 orbit neighborhoods from source → target under fmdl_step5.
    Returns list of (left, center, right, output) tuples.
    """
    n = 5
    neighborhoods = []
    for i in range(n):
        l = source[(i + 4) % n]
        c = source[i]
        r = source[(i + 1) % n]
        out = target[i]
        neighborhoods.append((l, c, r, out))
    return neighborhoods


def main():
    print("=" * 60)
    print("SM Orbit-Admissible Z₇ Function Count")
    print("=" * 60)

    # Extract all orbit neighborhood constraints
    orbit_steps = [
        ("gen₁ → gen₂", GEN1, GEN2),
        ("gen₂ → gen₃", GEN2, GEN3),
        ("gen₃ → vacuum", GEN3, VACUUM),
    ]

    all_orbit_neighborhoods = []  # (l, c, r, output)
    print("\nOrbit neighborhood constraints:")
    for step_name, src, tgt in orbit_steps:
        nbhds = extract_orbit_neighborhoods(src, tgt)
        print(f"\n  {step_name}:")
        for l, c, r, out in nbhds:
            print(f"    f({l},{c},{r}) = {out}  {'(non-zero)' if out != 0 else '(zero = free default)'}")
        all_orbit_neighborhoods.extend(nbhds)

    # Check for overlapping neighborhoods
    print("\n" + "=" * 60)
    print("Overlap analysis:")
    seen = {}  # (l,c,r) → output
    conflicts = []
    for l, c, r, out in all_orbit_neighborhoods:
        key = (l, c, r)
        if key in seen:
            if seen[key] != out:
                conflicts.append((key, seen[key], out))
                print(f"  CONFLICT at ({l},{c},{r}): output {seen[key]} vs {out}")
            # else: same output, no conflict
        else:
            seen[key] = out

    if not conflicts:
        print("  No conflicts — all orbit constraints are self-consistent.")

    distinct_orbit_neighborhoods = len(seen)
    print(f"\nDistinct orbit neighborhoods: {distinct_orbit_neighborhoods}  (from 3 × 5 = 15 total, with overlaps removed)")

    # Count by output type
    nonzero_orbit = {k: v for k, v in seen.items() if v != 0}
    zero_orbit    = {k: v for k, v in seen.items() if v == 0}
    print(f"  → Non-zero output (genuinely constraining): {len(nonzero_orbit)}")
    print(f"  → Zero output (compatible with MDL free default): {len(zero_orbit)}")

    # The Rule 110 binary constraint neighborhoods (from fmdl definition)
    binary_neighborhoods = {
        (0, 0, 0): 0,
        (0, 0, 1): 1,
        (0, 1, 0): 1,
        (0, 1, 1): 1,
        (1, 0, 0): 0,
        (1, 0, 1): 1,
        (1, 1, 0): 1,
        (1, 1, 1): 0,
    }
    print(f"\nRule 110 binary neighborhoods: {len(binary_neighborhoods)}")

    # Union of all fixed neighborhoods (orbit ∪ binary)
    all_fixed = dict(seen)
    binary_overlap = 0
    for k, v in binary_neighborhoods.items():
        if k in all_fixed:
            binary_overlap += 1
            if all_fixed[k] != v:
                print(f"  CONFLICT: binary neighborhood {k} has orbit output {all_fixed[k]} vs binary {v}")
        else:
            all_fixed[k] = v

    total_fixed = len(all_fixed)
    total_neighborhoods = 7 ** 3
    free_neighborhoods = total_neighborhoods - total_fixed
    orbit_binary_overlap = binary_overlap

    print(f"\n  Binary neighborhoods also in orbit constraints: {binary_overlap}")
    print(f"  Union (orbit ∪ binary): {total_fixed}")

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total Z₇³ neighborhoods: 7³ = {total_neighborhoods}")
    print(f"  Fixed by orbit constraints alone: {distinct_orbit_neighborhoods}")
    print(f"  Fixed by binary (Rule 110) constraints alone: {len(binary_neighborhoods)}")
    print(f"  Fixed by orbit + binary (union): {total_fixed}")
    print(f"  Free neighborhoods: {total_neighborhoods} - {total_fixed} = {free_neighborhoods}")
    print(f"\n  Orbit-admissible function count: 7^{free_neighborhoods}")
    print(f"  MDL-minimal element count: 7^0 = 1 (all free → 0, i.e., fmdl)")

    # Verify fmdl satisfies all orbit constraints
    print("\n" + "=" * 60)
    print("Verification: does fmdl satisfy all orbit constraints?")
    from itertools import product as iproduct

    # Reconstruct fmdl
    def fmdl(l, c, r):
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
        if l == 0 and c == 0 and r == 0: return 0
        if l == 0 and c == 0 and r == 1: return 1
        if l == 0 and c == 1 and r == 0: return 1
        if l == 0 and c == 1 and r == 1: return 1
        if l == 1 and c == 0 and r == 0: return 0
        if l == 1 and c == 0 and r == 1: return 1
        if l == 1 and c == 1 and r == 0: return 1
        if l == 1 and c == 1 and r == 1: return 0
        return 0

    def fmdl_step5(cells):
        n = 5
        return tuple(fmdl(cells[(i+4)%n], cells[i], cells[(i+1)%n]) for i in range(n))

    all_pass = True
    for l, c, r, expected in all_orbit_neighborhoods:
        got = fmdl(l, c, r)
        if got != expected:
            print(f"  FAIL: fmdl({l},{c},{r}) = {got}, expected {expected}")
            all_pass = False

    if all_pass:
        print("  ✅ fmdl satisfies all orbit constraints.")

    # Count actual zero/non-zero outputs of fmdl
    fmdl_nonzero = [(l, c, r) for l, c, r in iproduct(range(7), repeat=3) if fmdl(l, c, r) != 0]
    print(f"\nfmdl non-zero output neighborhoods: {len(fmdl_nonzero)}")
    print(f"fmdl zero output neighborhoods: {total_neighborhoods - len(fmdl_nonzero)}")

    # Show which fixed neighborhoods have non-zero output
    print("\nFixed neighborhoods with non-zero output (sorted by value):")
    nonzero_fixed = sorted([(k, v) for k, v in all_fixed.items() if v != 0], key=lambda x: x[1])
    for (l, c, r), v in nonzero_fixed:
        print(f"  f({l},{c},{r}) = {v}")

    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print(f"  The SM orbit (3 steps × 5 positions) gives {distinct_orbit_neighborhoods} distinct neighborhood constraints.")
    print(f"  Of these, {len(nonzero_orbit)} have non-zero output (genuinely pin the function).")
    print(f"  The Rule 110 binary sublayer adds {len(binary_neighborhoods) - binary_overlap} more distinct constraints.")
    print(f"  Total fixed neighborhoods (orbit + binary): {total_fixed}")
    print(f"  Free neighborhoods: {free_neighborhoods}")
    print(f"  Orbit-admissible function count: 7^{free_neighborhoods} ≈ 10^{int(free_neighborhoods * 0.845)}")
    print(f"  MDL-minimal selection: the UNIQUE function with all free → 0 is fmdl.")


if __name__ == "__main__":
    main()
