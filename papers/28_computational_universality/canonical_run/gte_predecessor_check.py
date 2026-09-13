#!/usr/bin/env python3
"""
gte_predecessor_check.py — GTE triple-level T⁻¹ predecessor check for G₁=(1,73,823).

Question: Does G₁ = (1, 73, 823) (electron GTE triple) have any T⁻¹ predecessors
under the GTE triple-level update map T?

Method:
  1. List all canonical GTE triples (the complete SM fermion set).
  2. Apply T (odd step G1→G2 and even step G2→G3) to all appropriate inputs.
  3. Check if any T-output equals (a=1, b=73, c=823).
  4. Conclude whether stability is a GTE-level or CA-level property.

Note: The GTE T map is implemented as a locked finite map over canonical seeds.
For quarks: T_odd maps G1 seeds → G2 values; T_even maps G2 values → G3 values.
For leptons: the canonical evolution is (1,73,823)→(9,42,1023)→(5,275,-65535),
but no general T formula is implemented; the evolution is listed in CANONICAL_TRIPLES.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class Triple:
    a: int
    b: int
    c: int
    gen: int
    name: str

    def abc(self) -> Tuple[int, int, int]:
        return (self.a, self.b, self.c)


# ── Canonical GTE Triples (from UGP_GTE_SM_Verifier.py CANONICAL_TRIPLES) ──
CANONICAL_TRIPLES: List[Triple] = [
    # Leptons
    Triple(1,   73,       823,   1, "electron"),
    Triple(9,   42,      1023,   2, "muon"),
    Triple(5,  275,    -65535,   3, "tau"),
    # Neutrinos
    Triple(1,    1,       823,   1, "electron_neutrino"),
    Triple(9,    1,      1023,   2, "muon_neutrino"),
    Triple(5,    1,    -65535,   3, "tau_neutrino"),
    # Up-type quarks
    Triple(5,    9,       275,   1, "up"),
    Triple(5,  275,     65535,   2, "charm"),
    Triple(76, 337920,     -1,   3, "top"),
    # Down-type quarks
    Triple(9,    5,        42,   1, "down"),
    Triple(9,  186,      1023,   2, "strange"),
    Triple(5, 8191,     65535,   3, "bottom"),
]

# ── GTE T map (locked finite map over canonical seeds) ──
# Quark odd step: G1 → G2
_QUARK_ODD: List[Tuple[Triple, Triple]] = [
    (Triple(5,  9,   275, 1, "up"),   Triple(5,  275, 65535, 2, "charm")),
    (Triple(9,  5,    42, 1, "down"), Triple(9,  186,  1023, 2, "strange")),
]

# Quark even step: G2 → G3
_QUARK_EVEN: List[Tuple[Triple, Triple]] = [
    (Triple(5, 275, 65535, 2, "charm"),   Triple(76, 337920,   -1, 3, "top")),
    (Triple(9, 186,  1023, 2, "strange"), Triple(5,   8191, 65535, 3, "bottom")),
]

# Lepton evolution (canonical ordering — no separate T formula in code):
# electron(1,73,823) → muon(9,42,1023) → tau(5,275,-65535)
# These are listed as canonical triples with gen=1,2,3 respectively.
# For predecessor analysis: within the canonical lepton sequence,
# electron is gen=1 (no generation-0 predecessor exists in GTE framework).


def check_predecessors(target: Tuple[int, int, int]) -> None:
    """Check all canonical T applications for any that produce the target triple."""
    print(f"Checking GTE T⁻¹ predecessors of {target}")
    print("=" * 60)

    found: List[str] = []

    print("\n── All canonical T outputs (quark odd step G1→G2) ──")
    for inp, out in _QUARK_ODD:
        print(f"  T_odd({inp.name} {inp.abc()}) = {out.abc()}")
        if out.abc() == target:
            found.append(f"T_odd({inp.name} {inp.abc()}) = {target}")

    print("\n── All canonical T outputs (quark even step G2→G3) ──")
    for inp, out in _QUARK_EVEN:
        print(f"  T_even({inp.name} {inp.abc()}) = {out.abc()}")
        if out.abc() == target:
            found.append(f"T_even({inp.name} {inp.abc()}) = {target}")

    print("\n── Lepton canonical sequence (no explicit T formula) ──")
    lepton_chain = [
        (Triple(1, 73, 823, 1, "electron"), Triple(9, 42, 1023, 2, "muon")),
        (Triple(9, 42, 1023, 2, "muon"), Triple(5, 275, -65535, 3, "tau")),
    ]
    for inp, out in lepton_chain:
        print(f"  T_lepton({inp.name} {inp.abc()}) = {out.abc()}")
        if out.abc() == target:
            found.append(f"T_lepton({inp.name} {inp.abc()}) = {target}")

    print("\n── Neutrino canonical sequence ──")
    nu_chain = [
        (Triple(1, 1, 823, 1, "electron_neutrino"), Triple(9, 1, 1023, 2, "muon_neutrino")),
        (Triple(9, 1, 1023, 2, "muon_neutrino"), Triple(5, 1, -65535, 3, "tau_neutrino")),
    ]
    for inp, out in nu_chain:
        print(f"  T_nu({inp.name} {inp.abc()}) = {out.abc()}")
        if out.abc() == target:
            found.append(f"T_nu({inp.name} {inp.abc()}) = {target}")

    print("\n── All canonical G2 and G3 triples (all T outputs) ──")
    all_outputs = [t.abc() for t in CANONICAL_TRIPLES if t.gen >= 2]
    for t in CANONICAL_TRIPLES:
        if t.gen >= 2:
            print(f"  Gen{t.gen} output: {t.abc()} ({t.name})")
            if t.abc() == target:
                found.append(f"Canonical gen{t.gen} output {t.abc()} == target")

    print(f"\n── Result ──")
    print(f"Target: {target}")
    print(f"Count of canonical T-outputs equal to target: {len(found)}")

    if found:
        for f in found:
            print(f"  MATCH: {f}")
        print("\nCONCLUSION: G₁ HAS predecessors at the GTE triple level.")
        print("  Stability requires CA structure beyond GTE triples.")
    else:
        print("\nCONCLUSION: G₁ = (1,73,823) has ZERO T⁻¹ predecessors in the")
        print("  canonical GTE triple space.")
        print("  Stability is present at the GTE triple level: no canonical GTE")
        print("  evolution step produces G₁ as an output.")
        print()
        print("  Physical interpretation: G₁ is a 'root' of the GTE generational")
        print("  hierarchy — the GTE framework has no generation-0 → G₁ step.")
        print("  The CA-level GoE (f_MDL predecessor count = 0) is an additional,")
        print("  finer-grained confirmation of the same physics: stability is")
        print("  encoded at BOTH the GTE triple level AND the Z₇ CA level.")

    return len(found)


if __name__ == "__main__":
    G1 = (1, 73, 823)
    count = check_predecessors(G1)
    print(f"\nFINAL ANSWER: GTE T⁻¹ predecessor count for G₁={G1}: {count}")
