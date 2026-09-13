"""
GTE Triple Discrimination of Neutral Particles (Z₇=0 sector)

Investigates whether GTE triples (a, b, c) can discriminate ν, γ, Z, and other
Z₇=0 particles where the Z₇ projection loses discriminating power.

Key question from P28 §11.4:
  ν (neutrino), γ (photon), and Z boson all have Z₇ winding = 0 in the f_MDL
  framework. This makes them indistinguishable by Z₇ arithmetic alone. Do their
  full GTE triples (a, b, c) distinguish them?

Results documented in:
  specs/IN-PROCESS/epic_070_universality_new_frontiers/07_LAB_NOTES_RANK11_gte_triple_discrimination.md
"""

from dataclasses import dataclass
from typing import Optional, List, Dict

# ---------------------------------------------------------------------------
# GTE Triple datatype (mirrors CANONICAL_TRIPLES in UGP_GTE_SM_Verifier)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GTETriple:
    """GTE triple (a, b, c; gen) with particle label.

    a = interaction complexity (distinct interaction channels)
    b = ladder index (particle informational N-value)
    c = branch capacity (dominant frequency * phase; c < 0 for chiral particles)
    gen = generation index (1, 2, or 3)
    """
    a: int
    b: int
    c: int
    gen: int
    name: str

    def abc(self):
        return (self.a, self.b, self.c)

    def __str__(self):
        return f"{self.name}: (a={self.a}, b={self.b}, c={self.c}, gen={self.gen})"


# ---------------------------------------------------------------------------
# Canonical triples — from CANONICAL_TRIPLES in UGP_GTE_SM_Verifier.py
# Photon and gluon are fixed_zero (no mass-cascade triple defined)
# ---------------------------------------------------------------------------

# All SM particles with GTE triples
CANONICAL_TRIPLES = [
    # Charged leptons
    GTETriple(1,   73,        823,     1, "electron"),
    GTETriple(9,   42,       1023,     2, "muon"),
    GTETriple(5,  275,     -65535,     3, "tau"),
    # Neutrinos (N=1 for all)
    GTETriple(1,    1,        823,     1, "electron_neutrino"),
    GTETriple(9,    1,       1023,     2, "muon_neutrino"),
    GTETriple(5,    1,     -65535,     3, "tau_neutrino"),
    # Up-type quarks
    GTETriple(5,    9,        275,     1, "up"),
    GTETriple(5,  275,      65535,     2, "charm"),
    GTETriple(76, 337920,      -1,     3, "top"),
    # Down-type quarks
    GTETriple(9,    5,         42,     1, "down"),
    GTETriple(9,  186,       1023,     2, "strange"),
    GTETriple(5, 8191,      65535,     3, "bottom"),
    # Electroweak bosons (electroweak ρ-law, N=3)
    GTETriple(5,    3,         11,     1, "W_boson"),
    GTETriple(5,    3,         12,     1, "Z_boson"),
    GTETriple(5,    3,         13,     1, "Higgs_boson"),
    # Composite baryons
    GTETriple(5, 11459,        15,     3, "proton"),
    GTETriple(5, 11441,        15,     3, "neutron"),
]

# Massless gauge bosons: no GTE triple in the mass-cascade framework
FIXED_ZERO_PARTICLES = ["photon", "gluon"]

# Build lookup by name
TRIPLE_BY_NAME: Dict[str, GTETriple] = {t.name: t for t in CANONICAL_TRIPLES}


# ---------------------------------------------------------------------------
# Z₇ winding assignment (from P28 and ugp-vocabulary)
# These are the winding numbers in the f_MDL ring framework
# ---------------------------------------------------------------------------

Z7_WINDING = {
    # Z₇ = 0: vacuum/neutrino sector/photon/Z boson
    "vacuum":             0,
    "electron_neutrino":  0,
    "muon_neutrino":      0,
    "tau_neutrino":       0,
    "photon":             0,
    "Z_boson":            0,
    "Higgs_boson":        0,   # neutral scalar — not in P28's original Z₇=0 triplet but also W=0
    "gluon":              0,   # color-neutral superposition; W=0 in SU(3) sector
    # Z₇ = 2: up-quark sector
    "up":                 2,
    "charm":              2,
    "top":                2,
    # Z₇ = 3: W⁺ boson / positive-winding
    "W_boson":            3,
    # Z₇ = 4: electron/W⁻ sector (= -3 mod 7)
    "electron":           4,
    "muon":               4,
    "tau":                4,
    # Z₇ = 6: down-quark sector (= -1 mod 7)
    "down":               6,
    "strange":            6,
    "bottom":             6,
}


def z7_winding(name: str) -> Optional[int]:
    return Z7_WINDING.get(name)


# ---------------------------------------------------------------------------
# Step 1: Collect all Z₇=0 particles and their GTE triple status
# ---------------------------------------------------------------------------

Z7_ZERO_PARTICLES_WITH_TRIPLES = [
    "electron_neutrino",
    "muon_neutrino",
    "tau_neutrino",
    "Z_boson",
    "Higgs_boson",
]

Z7_ZERO_PARTICLES_WITHOUT_TRIPLES = [
    "photon",
    "gluon",
]

# Note: vacuum is Z₇=0 but is not a particle — it's the null state


def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def check_triples_distinct(names: List[str], label: str) -> bool:
    """Check whether the GTE triples of named particles are pairwise distinct."""
    triples = [(n, TRIPLE_BY_NAME[n]) for n in names if n in TRIPLE_BY_NAME]
    all_distinct = True
    for i in range(len(triples)):
        for j in range(i + 1, len(triples)):
            n1, t1 = triples[i]
            n2, t2 = triples[j]
            if t1.abc() == t2.abc():
                print(f"  ❌ COLLISION: {n1} == {n2}: {t1.abc()}")
                all_distinct = False
            else:
                print(f"  ✓ DISTINCT: {n1} vs {n2}: {t1.abc()} ≠ {t2.abc()}")
    if all_distinct:
        print(f"\n  ✅ All {label} triples are pairwise distinct.")
    else:
        print(f"\n  ❌ COLLISION found in {label} triples!")
    return all_distinct


def describe_discriminant(names: List[str]):
    """Describe which triple components discriminate each particle."""
    triples = [(n, TRIPLE_BY_NAME[n]) for n in names if n in TRIPLE_BY_NAME]
    print("\n  Triple component analysis:")
    print(f"  {'Particle':<22} {'a':>6} {'b':>8} {'c':>10}  {'Discriminating feature'}")
    print(f"  {'-'*22} {'-'*6} {'-'*8} {'-'*10}  {'-'*30}")
    for n, t in triples:
        if n in ("Z_boson", "Higgs_boson"):
            feature = "b=3 (EW N=3 level)"
        elif n == "electron_neutrino":
            feature = "a=1 (νₑ unique a-value)"
        elif n == "muon_neutrino":
            feature = "a=9 (νμ unique a-value)"
        elif n == "tau_neutrino":
            feature = "a=5, c<0 (chirality)"
        else:
            feature = ""
        print(f"  {n:<22} {t.a:>6} {t.b:>8} {t.c:>10}  {feature}")


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  GTE Triple Discrimination of Z₇=0 Neutral Particles")
    print("  Rank 11 — EPIC_070 New Frontiers")
    print("="*70)

    # Step 1: Show all Z₇=0 particles and their GTE status
    print_section("Step 1: Z₇=0 Particle Inventory")
    print("\n  Particles with Z₇ winding = 0:")
    for name in Z7_ZERO_PARTICLES_WITH_TRIPLES + Z7_ZERO_PARTICLES_WITHOUT_TRIPLES:
        w = z7_winding(name)
        if name in TRIPLE_BY_NAME:
            t = TRIPLE_BY_NAME[name]
            print(f"    {name:<22}  Z₇={w}  GTE triple: (a={t.a}, b={t.b}, c={t.c}, gen={t.gen})")
        else:
            print(f"    {name:<22}  Z₇={w}  GTE triple: NONE (fixed_zero — no mass cascade triple)")

    # Step 2: Check pairwise distinction for the 3 P28 particles (ν, γ, Z)
    print_section("Step 2: P28 §11.4 Particles — ν/γ/Z")
    print("\n  The P28 §11.4 open problem concerns 3 particles: νₑ, γ, Z")
    print("  Of these, photon (γ) has NO GTE triple (fixed_zero).")
    print("  For νₑ and Z_boson (both have triples):")
    nu_e = TRIPLE_BY_NAME["electron_neutrino"]
    z = TRIPLE_BY_NAME["Z_boson"]
    print(f"    electron_neutrino: (a={nu_e.a}, b={nu_e.b}, c={nu_e.c})")
    print(f"    Z_boson:           (a={z.a}, b={z.b}, c={z.c})")
    print(f"    DISTINCT: {nu_e.abc() != z.abc()} (differ in all three components)")

    # Step 3: Full Z₇=0 sector — all particles with GTE triples
    print_section("Step 3: Full Z₇=0 GTE-Triple Sector")
    print("\n  Checking pairwise distinctness of all Z₇=0 particles with GTE triples:")
    print(f"  Particles: {Z7_ZERO_PARTICLES_WITH_TRIPLES}\n")
    result = check_triples_distinct(Z7_ZERO_PARTICLES_WITH_TRIPLES, "Z₇=0")

    # Step 4: Describe the discriminant
    print_section("Step 4: Triple Discriminant Analysis")
    describe_discriminant(Z7_ZERO_PARTICLES_WITH_TRIPLES)
    print("""
  Key discriminating structure:
    (A) b-component separates EW bosons (b=3) from neutrinos (b=1):
        Z_boson:   b=3  ← uniquely identifies the EW sector among Z₇=0
        Higgs:     b=3  ← also EW sector
        νₑ, νμ, ντ: b=1 ← neutrino sector (uniform b)

    (B) a-component separates neutrino generations:
        νₑ: a=1  ← unique
        νμ: a=9  ← unique
        ντ: a=5  ← shared with Z, Higgs (but b differs)

    (C) c-component provides final disambiguation:
        ντ: c=-65535 (c<0 from chirality) ← uniquely identifies τ-neutrino

    Summary: (b=3) → EW sector; within EW: c distinguishes Z (c=12) from Higgs (c=13).
             (b=1) → neutrino sector; within ν: a distinguishes all 3 generations.
    """)

    # Step 5: f_MDL extension concept
    print_section("Step 5: f_MDL Extension to Triple Space")
    print("""
  Natural extension:
    Standard f_MDL: maps Z₇ winding value → Z₇ output (5-cell ring)
    Extended f_MDL: maps (a, b, c) triple → particle label

    The simplest discriminant on the full triple space is:
        disc(a, b, c) = b mod 3   [separates EW sector (b=3→0) from ν (b=1→1)]

    For full discrimination of all Z₇=0 particles:
        if b == 3:
            if c == 12: label = "Z_boson"
            elif c == 13: label = "Higgs_boson"
        elif b == 1:
            if a == 1:   label = "electron_neutrino"
            elif a == 9: label = "muon_neutrino"
            elif a == 5: label = "tau_neutrino"
        [photon and gluon: not in GTE triple space — fixed_zero; no triple to inspect]

  This discriminant is computable, finite, and exact.
    """)

    # Step 6: Photon analysis — honest limitation
    print_section("Step 6: Photon — Honest Limitation")
    print("""
  The photon (γ) is handled as 'fixed_zero' in the GTE framework:
    - It is a massless U(1) gauge boson with no GTE mass-cascade triple
    - The GTE triple framework is built on the mass cascade T^-1 evolution
    - Massless particles (photon, gluon) do not participate in this cascade
    - Therefore, they have NO (a, b, c) triple to inspect

  Consequence:
    - The GTE triple framework PARTIALLY resolves P28 §11.4:
      * νₑ, νμ, ντ, Z_boson (and Higgs) are all mutually distinguishable ✅
      * Photon discrimination requires physics BEYOND GTE triples (as P28 §11.4 notes)
    - The Z₇=0 open problem is PARTIALLY closed by GTE triple space:
      * 5 of the 6 Z₇=0 particles are distinguishable by their triples
      * Photon remains outside the GTE triple framework

  Clarification on P28 §11.4 scope:
    The open problem concerns "additional arithmetic structure (spin, isospin)"
    to distinguish ν/γ/Z. GTE triples provide a partial solution:
    they distinguish ν vs Z (and Higgs) but cannot address the photon.
    """)

    # Step 7: Summary table
    print_section("Summary Table: Z₇=0 Particles")
    print(f"\n  {'Particle':<22} {'Z₇':>4} {'GTE Triple (a,b,c)':<25} {'Distinguishable?'}")
    print(f"  {'-'*22} {'-'*4} {'-'*25} {'-'*20}")
    all_z7_zero = Z7_ZERO_PARTICLES_WITH_TRIPLES + Z7_ZERO_PARTICLES_WITHOUT_TRIPLES
    for name in all_z7_zero:
        w = z7_winding(name)
        if name in TRIPLE_BY_NAME:
            t = TRIPLE_BY_NAME[name]
            triple_str = f"({t.a}, {t.b}, {t.c})"
            dist = "✅ Yes (unique triple)"
        else:
            triple_str = "NONE (fixed_zero)"
            dist = "❌ Not by GTE triple"
        print(f"  {name:<22} {w:>4}  {triple_str:<25} {dist}")

    print(f"\n  Photon, gluon: Z₇=0 but no GTE triple — require isospin/spin structure")
    print(f"  All GTE-triple-bearing Z₇=0 particles: 5/5 mutually distinguishable ✅")

    # Verify using a simple discriminant function
    print_section("Verification: Discriminant Function")
    def neutral_disc(t: GTETriple) -> int:
        """Simple discriminant for Z₇=0 GTE-triple-bearing particles."""
        if t.b == 3:
            if t.c == 12: return 3  # Z_boson
            if t.c == 13: return 4  # Higgs_boson
        elif t.b == 1:
            if t.a == 1: return 0   # electron_neutrino
            if t.a == 9: return 1   # muon_neutrino
            if t.a == 5: return 2   # tau_neutrino
        return -1  # unknown

    label_map = {0: "electron_neutrino", 1: "muon_neutrino", 2: "tau_neutrino",
                 3: "Z_boson", 4: "Higgs_boson"}

    print("\n  Discriminant output for each Z₇=0 particle:")
    all_correct = True
    for name in Z7_ZERO_PARTICLES_WITH_TRIPLES:
        t = TRIPLE_BY_NAME[name]
        d = neutral_disc(t)
        expected = label_map.get(d, "UNKNOWN")
        match = "✓" if expected == name else "✗"
        print(f"    {match} {name:<22} → disc={d} (label: {expected})")
        if expected != name:
            all_correct = False

    if all_correct:
        print("\n  ✅ Discriminant function correctly identifies all 5 Z₇=0 GTE-triple-bearing particles.")
    else:
        print("\n  ❌ Discriminant function has errors!")

    # Check for label collisions
    labels = {neutral_disc(TRIPLE_BY_NAME[n]) for n in Z7_ZERO_PARTICLES_WITH_TRIPLES}
    if len(labels) == len(Z7_ZERO_PARTICLES_WITH_TRIPLES):
        print("  ✅ All discriminant labels are distinct (no collisions).")
    else:
        print("  ❌ Discriminant label collision found!")

    print("\n" + "="*70)
    print("  CONCLUSION")
    print("="*70)
    print("""
  1. All Z₇=0 particles with GTE triples are pairwise distinguishable:
     νₑ (1,1,823), νμ (9,1,1023), ντ (5,1,-65535), Z (5,3,12), H (5,3,13)

  2. Key discriminant: b-component separates EW sector (b=3) from neutrinos (b=1).
     Within sectors: a-component (neutrinos) or c-component (bosons) finalizes.

  3. This PARTIALLY resolves P28 §11.4:
     - ν vs Z discrimination: ✅ RESOLVED by GTE triples
     - Three neutrino generations: ✅ mutually distinguishable
     - ν/γ/Z (full P28 problem): PARTIALLY resolved
       (ν vs Z ✅; photon remains outside GTE triple framework ⚠️)

  4. Photon limitation: γ has no GTE triple (fixed_zero). The photon discrimination
     problem is a genuine open problem requiring spin or isospin structure beyond
     the mass cascade framework.
""")
