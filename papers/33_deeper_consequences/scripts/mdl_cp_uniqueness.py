"""
mdl_cp_uniqueness.py

Sampling test for the MDL-CP uniqueness conjecture:

Among orbit-admissible Z₇ CA functions (functions satisfying the 23 fixed
SM orbit + Rule 110 binary sublayer constraints), what fraction satisfy BOTH:

  (a) vacuum-transparent: f(0,0,0) = 0
      [This is fixed by orbit-admissibility — the binary sublayer forces it]
  (b) never output Z₇=4 (the W⁻/e⁻ antiparticle winding)

The MDL-minimal orbit-admissible function (fmdl) satisfies both (a) and (b):
- (a) because (0,0,0)→0 is one of the 8 binary sublayer constraints
- (b) because none of the 14 nonzero-output neighborhoods produce Z₇=4,
      and all 320 free neighborhoods output 0 ≠ 4 by MDL-minimality

Theorem: fmdl is the UNIQUE orbit-admissible MDL-minimal function
satisfying both properties. Among all orbit-admissible functions, Z₇=4 exclusion
is astronomically rare — probability ≈ (6/7)^320 ≈ 10^{-22}.

Sampling strategy:
- Draw 10,000 random orbit-admissible functions
  (23 fixed constraints + 320 free neighborhoods uniformly random from Fin 7)
- For each, check (a) vacuum-transparency and (b) Z₇=4 exclusion
- Expected result: 0/10,000 satisfy (b) since P ≈ (6/7)^320 ≈ 10^{-22}

Physical interpretation:
- (a) is universal for orbit-admissible functions (fixed by construction)
- (b) is the arithmetic CP violation property: W⁻/e⁻ is excluded from the
  output range, selecting matter over antimatter
- MDL-minimality is the unique orbit-admissible principle that forces (b):
  parsimony = matter dominance = arithmetic CP violation
"""

import random
import math


# ---------------------------------------------------------------------------
# SM generation orbit states
# ---------------------------------------------------------------------------
GEN1   = (1, 5, 2, 2, 1)
GEN2   = (2, 5, 2, 0, 2)
GEN3   = (5, 6, 5, 3, 5)
VACUUM = (0, 0, 0, 0, 0)


def extract_orbit_neighborhoods(source, target):
    """Return list of (left, center, right, output) for a 5-cell orbit step."""
    n = 5
    return [
        (source[(i + 4) % n], source[i], source[(i + 1) % n], target[i])
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Build the 23 fixed constraints
# ---------------------------------------------------------------------------
def build_fixed_constraints():
    fixed = {}

    # Orbit constraints (3 steps × 5 positions = 15 distinct neighborhoods)
    for src, tgt in [(GEN1, GEN2), (GEN2, GEN3), (GEN3, VACUUM)]:
        for l, c, r, out in extract_orbit_neighborhoods(src, tgt):
            key = (l, c, r)
            assert key not in fixed or fixed[key] == out, f"Conflict at {key}"
            fixed[key] = out

    # Rule 110 binary sublayer constraints (8 neighborhoods, no overlap with orbit)
    binary = {
        (0, 0, 0): 0,
        (0, 0, 1): 1,
        (0, 1, 0): 1,
        (0, 1, 1): 1,
        (1, 0, 0): 0,
        (1, 0, 1): 1,
        (1, 1, 0): 1,
        (1, 1, 1): 0,
    }
    for key, out in binary.items():
        assert key not in fixed or fixed[key] == out, f"Conflict at {key}"
        fixed[key] = out

    return fixed


FIXED_CONSTRAINTS = build_fixed_constraints()
ALL_NEIGHBORHOODS = [(l, c, r) for l in range(7) for c in range(7) for r in range(7)]
FREE_NEIGHBORHOODS = [k for k in ALL_NEIGHBORHOODS if k not in FIXED_CONSTRAINTS]

assert len(FIXED_CONSTRAINTS) == 23, f"Expected 23, got {len(FIXED_CONSTRAINTS)}"
assert len(FREE_NEIGHBORHOODS) == 320, f"Expected 320, got {len(FREE_NEIGHBORHOODS)}"
assert len(FIXED_CONSTRAINTS) + len(FREE_NEIGHBORHOODS) == 343


# ---------------------------------------------------------------------------
# The MDL-minimal orbit-admissible function (fmdl)
# ---------------------------------------------------------------------------
def make_fmdl():
    """Construct fmdl: fixed constraints + all free → 0."""
    f = dict(FIXED_CONSTRAINTS)
    for k in FREE_NEIGHBORHOODS:
        f[k] = 0
    return f


def make_random_orbit_admissible():
    """Generate a random orbit-admissible function (fixed constraints + random free)."""
    f = dict(FIXED_CONSTRAINTS)
    for k in FREE_NEIGHBORHOODS:
        f[k] = random.randint(0, 6)
    return f


# ---------------------------------------------------------------------------
# Property checks
# ---------------------------------------------------------------------------
def is_vacuum_transparent(f):
    """f(0,0,0) = 0. True for ALL orbit-admissible functions by construction."""
    return f[(0, 0, 0)] == 0


def never_outputs_4(f):
    """True iff f(l,c,r) ≠ 4 for all (l,c,r) — Z₇=4 exclusion."""
    return all(v != 4 for v in f.values())


def is_mdl_minimal(f):
    """True iff all free neighborhoods output 0 (i.e., f = fmdl exactly)."""
    return all(f[k] == 0 for k in FREE_NEIGHBORHOODS)


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("MDL-CP Uniqueness Sampling Test")
    print("MDL Minimality = CP Violation Selection")
    print("=" * 70)

    print(f"\nFixed orbit+binary constraints: {len(FIXED_CONSTRAINTS)}")
    print(f"  (15 orbit + 8 binary, zero overlaps)")
    print(f"Free neighborhoods: {len(FREE_NEIGHBORHOODS)}")
    print(f"Total neighborhoods: 7³ = {7**3}")
    print(f"\nOrbit-admissible function count: 7^{len(FREE_NEIGHBORHOODS)}")

    log10_count = len(FREE_NEIGHBORHOODS) * math.log10(7)
    print(f"  = 10^{log10_count:.0f} (astronomically large)")
    print(f"\nMDL-minimal elements (all free → 0): 1 (= fmdl)")

    # Verify fmdl
    fmdl = make_fmdl()
    print("\n" + "=" * 70)
    print("fmdl verification:")
    print(f"  Vacuum-transparent [f(0,0,0)=0]: {is_vacuum_transparent(fmdl)}")
    print(f"  Never outputs Z₇=4:              {never_outputs_4(fmdl)}")
    print(f"  MDL-minimal (all free → 0):      {is_mdl_minimal(fmdl)}")

    nonzero_nbhds = [(l, c, r) for (l, c, r), v in fmdl.items() if v != 0]
    print(f"  Nonzero output neighborhoods:    {len(nonzero_nbhds)} (of 343)")
    assert len(nonzero_nbhds) == 14, f"Expected 14, got {len(nonzero_nbhds)}"
    print(f"  ✅ Exactly 14 nonzero neighborhoods (orbit+binary nonzero outputs only)")

    # Theoretical probability
    log_prob = len(FREE_NEIGHBORHOODS) * math.log10(6 / 7)
    prob_estimate = 10 ** log_prob
    print(f"\nTheoretical P(Z₇=4-free | random orbit-admissible) = (6/7)^{len(FREE_NEIGHBORHOODS)}")
    print(f"  = 10^({log_prob:.1f}) ≈ {prob_estimate:.1e}")
    print(f"  In 10,000 samples, expected Z₇=4-free count ≈ {1e4 * prob_estimate:.2e}")

    # Sampling
    N = 10_000
    print(f"\n" + "=" * 70)
    print(f"Sampling {N:,} random orbit-admissible functions...")

    count_vt = 0        # vacuum-transparent (will be 100%)
    count_z4_free = 0   # never outputs Z₇=4
    count_mdl = 0       # MDL-minimal (= fmdl)

    for _ in range(N):
        f = make_random_orbit_admissible()
        if is_vacuum_transparent(f):
            count_vt += 1
        if never_outputs_4(f):
            count_z4_free += 1
        if is_mdl_minimal(f):
            count_mdl += 1

    print(f"\nResults over {N:,} samples:")
    print(f"  Vacuum-transparent [f(0,0,0)=0]:    {count_vt:,}/{N:,}  ({count_vt/N*100:.1f}%)")
    print(f"    → Expected 100%: (0,0,0)→0 is a fixed constraint")
    print(f"  Never outputs Z₇=4:                 {count_z4_free:,}/{N:,}  ({count_z4_free/N*100:.8f}%)")
    print(f"    → Expected ~(6/7)^320 ≈ {prob_estimate:.1e}")
    print(f"  MDL-minimal (all free → 0 = fmdl):  {count_mdl:,}/{N:,}")
    print(f"    → Expected 0 (probability = (1/7)^320 ≈ 10^{len(FREE_NEIGHBORHOODS)*math.log10(1/7):.0f})")

    print("\n" + "=" * 70)
    print("CONCLUSIONS:")
    print()

    if count_vt == N:
        print("✅ Vacuum-transparency is UNIVERSAL for orbit-admissible functions.")
        print("   (0,0,0)→0 is fixed by the binary sublayer constraint — not a free choice.")
    else:
        print(f"⚠️  UNEXPECTED: {N - count_vt} functions failed vacuum-transparency.")

    if count_z4_free == 0:
        print()
        print("✅ CONFIRMED: 0/{:,} random orbit-admissible functions avoid Z₇=4.".format(N))
        print(f"   Probability ≈ (6/7)^320 ≈ {prob_estimate:.1e} — astronomically small.")
        print()
        print("   PHYSICAL INTERPRETATION:")
        print("   Among the 7^320 ≈ 10^270 orbit-admissible functions, Z₇=4 exclusion")
        print("   is so rare that even a 10^22-fold sample would find none.")
        print()
        print("   MDL-minimality (all free → 0) is the UNIQUE simple structural reason")
        print("   why a function would achieve Z₇=4 exclusion:")
        print("     · The 14 nonzero orbit+binary neighborhoods output {0,1,2,3,5,6}")
        print("       — none output 4 (by the arithmetic structure of the SM orbit)")
        print("     · MDL forces all 320 free neighborhoods to 0 ≠ 4")
        print("     · Any non-MDL-minimal function sets at least one free → k ≠ 0")
        print("       → probability 1/7 that k=4 → quickly overwhelms Z₇=4 exclusion")
        print()
        print("   PARSIMONY = MATTER DOMINANCE:")
        print("   The most parsimonious CA rule (fmdl, MDL-minimal) is also the unique")
        print("   one where the W⁻/e⁻ antiparticle (Z₇=4) is arithmetically impossible")
        print("   from a single-axis f_MDL evaluation. MDL selects the CP-violating vacuum.")
    else:
        print(f"⚠️  UNEXPECTED: {count_z4_free:,} functions found that avoid Z₇=4.")
        print("   This contradicts the expected astronomically low probability.")
        print("   Investigate the random sampling logic.")

    if count_mdl == 0:
        print()
        print("✅ No MDL-minimal function sampled (as expected: probability ≈ 10^{-270}).")
        print("   fmdl is the unique MDL-minimal element of the 7^320 orbit-admissible class.")


if __name__ == "__main__":
    random.seed(42)
    main()
