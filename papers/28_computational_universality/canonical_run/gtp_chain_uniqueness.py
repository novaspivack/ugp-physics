#!/usr/bin/env python3
"""
gtp_chain_uniqueness.py — Exhaustive search for GoE-rooted Terminating Paths (GTP-n).

A GoE-rooted Terminating Path of length n (GTP-n) is a chain
    s1 → s2 → ... → sn → vacuum
where:
  - pred_count(s1) = 0  (GoE: no predecessor)
  - pred_count(si) = 1 for i ≥ 2  (unique predecessor at each step)
  - all si are distinct non-vacuum states
  - fmdl_step5(sn) = vacuum

Spec 05 proved the SM orbit gen1→gen2→gen3→vacuum is a GTP-3.
This script asks: is the SM orbit the UNIQUE GTP-3 (up to cyclic ring rotation)?
And: do any GTP-4 or longer chains exist?

Key result feeds into Rank 23 Lean certification.
"""

import itertools
from typing import Dict, List, Set, Tuple, Optional

# ── fmdl: MDL-minimal Z₇ CA function (from CUP3DUniqueness.lean) ──
_FMDL_LOOKUP: Dict[Tuple[int,int,int], int] = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}

def fmdl(l: int, c: int, r: int) -> int:
    return _FMDL_LOOKUP.get((l, c, r), 0)

def fmdl_step5(state: Tuple[int, ...]) -> Tuple[int, ...]:
    n = 5
    return tuple(fmdl(state[(i-1)%n], state[i], state[(i+1)%n]) for i in range(n))

GEN1: Tuple[int,...] = (1, 5, 2, 2, 1)
GEN2: Tuple[int,...] = (2, 5, 2, 0, 2)
GEN3: Tuple[int,...] = (5, 6, 5, 3, 5)
VACUUM: Tuple[int,...] = (0, 0, 0, 0, 0)

def cyclic_rotations(s: Tuple[int,...]) -> List[Tuple[int,...]]:
    """All 5 cyclic rotations of a 5-tuple."""
    return [tuple(s[(i+k)%5] for i in range(5)) for k in range(5)]

def all_sm_orbit_rotations() -> Set[Tuple[int,...]]:
    """All 5 cyclic rotations of gen1 (which are the GTP-3 starts)."""
    return set(cyclic_rotations(GEN1))

def build_predecessor_table() -> Dict[Tuple[int,...], List[Tuple[int,...]]]:
    """Build the complete predecessor map for the 7^5 state space."""
    pred_map: Dict[Tuple[int,...], List[Tuple[int,...]]] = {
        s: [] for s in itertools.product(range(7), repeat=5)
    }
    for state in itertools.product(range(7), repeat=5):
        img = fmdl_step5(state)
        pred_map[img].append(state)
    return pred_map

def find_gtp_chains(pred_map: Dict) -> Dict[int, List[List[Tuple[int,...]]]]:
    """
    Find all GTP-n chains for all n ≥ 1.
    Returns dict: n → list of chains [s1, s2, ..., sn] (before vacuum).
    """
    results: Dict[int, List] = {}

    # Find all GoE states (pred_count = 0, not vacuum)
    goe_states = [s for s, preds in pred_map.items()
                  if len(preds) == 0 and s != VACUUM]

    print(f"Total GoE states (excluding vacuum): {len(goe_states)}")
    print()

    # For each GoE state, trace the chain
    for s1 in goe_states:
        chain = [s1]
        current = s1
        max_depth = 20  # sanity cap

        for _ in range(max_depth):
            nxt = fmdl_step5(current)
            if nxt == VACUUM:
                # Chain terminates: length = len(chain)
                n = len(chain)
                if n not in results:
                    results[n] = []
                results[n].append(list(chain))
                break
            elif len(pred_map[nxt]) != 1:
                # nxt has ≠ 1 predecessor → chain condition violated; not a GTP
                # (nxt is either GoE or confluent; GTP requires pred_count=1 for all i≥2)
                break
            else:
                if nxt in chain:
                    # Cycle detected → not a GTP
                    break
                chain.append(nxt)
                current = nxt
        # If we hit max_depth without termination → not recorded (not a GTP by finite bound)

    return results


def main() -> None:
    print("gtp_chain_uniqueness.py — GoE-Rooted Terminating Path (GTP-n) exhaustive search")
    print("=" * 80)
    print(f"State space: Z₇⁵ = 7^5 = {7**5} states")
    print()

    # Verify SM orbit
    assert fmdl_step5(GEN1) == GEN2
    assert fmdl_step5(GEN2) == GEN3
    assert fmdl_step5(GEN3) == VACUUM
    print("✓ SM orbit verified: gen1→gen2→gen3→vacuum")
    print(f"  gen1 = {GEN1}")
    print(f"  gen2 = {GEN2}")
    print(f"  gen3 = {GEN3}")
    print()

    # Build predecessor table
    print("Building predecessor table (exhaustive, 7^5 = 16,807 states)...")
    pred_map = build_predecessor_table()
    print("✓ Predecessor table built")
    print()

    # Verify Spec 05 results
    assert len(pred_map[GEN1]) == 0, "gen1 should be GoE"
    assert len(pred_map[GEN2]) == 1, "gen2 should have 1 predecessor"
    assert len(pred_map[GEN3]) == 1, "gen3 should have 1 predecessor"
    assert pred_map[GEN2][0] == GEN1, "gen2's predecessor should be gen1"
    assert pred_map[GEN3][0] == GEN2, "gen3's predecessor should be gen2"
    print("✓ Spec 05 results confirmed: pred(gen1)=0, pred(gen2)=1, pred(gen3)=1")
    print()

    # Find all GTP chains
    print("Finding all GTP-n chains (GoE → ... → vacuum, all steps with pred=1)...")
    gtp_chains = find_gtp_chains(pred_map)
    print("✓ GTP chain search complete")
    print()

    # Report results
    print("=" * 80)
    print("GTP-n chain counts:")
    for n in sorted(gtp_chains.keys()):
        chains = gtp_chains[n]
        print(f"  GTP-{n}: {len(chains)} chains")
    print()

    # Detailed GTP-3 analysis (the main question)
    if 3 in gtp_chains:
        gtp3_chains = gtp_chains[3]
        print(f"GTP-3 chains ({len(gtp3_chains)} total):")
        sm_rotations = all_sm_orbit_rotations()
        non_sm_gtp3 = []
        for chain in gtp3_chains:
            s1 = tuple(chain[0])
            is_sm_rotation = s1 in sm_rotations
            rot_idx = next((k for k in range(5) if tuple(GEN1[(k+i)%5] for i in range(5)) == s1), None)
            if is_sm_rotation:
                label = f"✓ SM orbit rotation k={rot_idx}"
            else:
                label = "✗ NOT a rotation of gen1"
                non_sm_gtp3.append(chain)
            print(f"  {chain[0]} → {chain[1]} → {chain[2]} → vacuum  [{label}]")
        print()
        if not non_sm_gtp3:
            print("✓ RESULT: ALL GTP-3 chains are cyclic rotations of the SM orbit (gen1).")
            print("  The SM orbit is the UNIQUE GTP-3 (up to cyclic ring rotation).")
            print()
            print("  Physical interpretation:")
            print("  Three generations is FORCED by Z₇⁵ topology under f_MDL_ring:")
            print("  the CA graph has exactly one 3-step GoE-rooted terminating path")
            print("  (up to ring symmetry), and that path IS the SM generation orbit.")
        else:
            print(f"✗ RESULT: {len(non_sm_gtp3)} non-SM GTP-3 chains found:")
            for chain in non_sm_gtp3:
                print(f"  {chain}")
    else:
        print("No GTP-3 chains found — unexpected!")

    print()
    print("=" * 80)

    # GTP-4 check (expected: none)
    if 4 in gtp_chains:
        print(f"WARNING: GTP-4 chains found ({len(gtp_chains[4])}):")
        for chain in gtp_chains[4]:
            print(f"  {chain}")
    else:
        print("✓ No GTP-4 chains exist.")

    if 5 in gtp_chains:
        print(f"WARNING: GTP-5 chains found ({len(gtp_chains[5])}):")
    else:
        print("✓ No GTP-5 chains exist.")

    any_longer = any(n >= 4 for n in gtp_chains)
    if not any_longer:
        print("✓ No GTP-n chains exist for n ≥ 4.")
        print("  Maximum GTP chain length is 3 — a deep arithmetic bound on generation count.")

    print()
    print("=" * 80)

    # GTP-1 and GTP-2 analysis
    if 1 in gtp_chains:
        print(f"GTP-1 chains ({len(gtp_chains[1])} total — GoE → vacuum directly):")
        for chain in gtp_chains[1][:10]:
            print(f"  {chain[0]} → vacuum")
        if len(gtp_chains[1]) > 10:
            print(f"  ... ({len(gtp_chains[1])} total)")
        print()

    if 2 in gtp_chains:
        print(f"GTP-2 chains ({len(gtp_chains[2])} total):")
        for chain in gtp_chains[2][:10]:
            print(f"  {chain[0]} → {chain[1]} → vacuum")
        if len(gtp_chains[2]) > 10:
            print(f"  ... ({len(gtp_chains[2])} total)")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY FOR RANK 23 (GTP-3 UNIQUENESS):")
    n_gtp3 = len(gtp_chains.get(3, []))
    sm_rotations = all_sm_orbit_rotations()
    gtp3_starts = set(tuple(c[0]) for c in gtp_chains.get(3, []))
    all_are_sm = gtp3_starts.issubset(sm_rotations)

    print(f"  Total GTP-3 chains: {n_gtp3}")
    print(f"  All are SM orbit rotations: {'✓ YES' if all_are_sm else '✗ NO'}")
    print(f"  Any GTP-n for n≥4: {'YES (UNEXPECTED)' if any_longer else '✓ NO'}")

    if n_gtp3 == 5 and all_are_sm and not any_longer:
        print()
        print("  ✓ CONJECTURE CONFIRMED (Rank 23):")
        print("  The SM orbit is the UNIQUE GTP-3 in Z₇⁵ under f_MDL_ring (5 chains = 5 rotations).")
        print("  No GTP-n exists for n ≥ 4.")
        print("  CatA confirmed. CatAL route: native_decide in GoEStabilityHierarchy.lean §§7-8.")
        print()
        print("  Lean theorem target:")
        print("  theorem sm_orbit_unique_gtp3 : ∀ s1 s2 s3 : Fin 5 → Fin 7,")
        print("    fmdl_predecessor_count s1 = 0 →")
        print("    fmdl_step5 s1 = s2 → fmdl_predecessor_count s2 = 1 →")
        print("    fmdl_step5 s2 = s3 → fmdl_predecessor_count s3 = 1 →")
        print("    fmdl_step5 s3 = fmdl_vacuum_z7 →")
        print("    ∃ k : Fin 5, (fun i => fmdl_gen1_z7 ⟨(i + k) % 5, ...⟩) = s1")
        print("  by native_decide")
    elif n_gtp3 == 5 and all_are_sm:
        print()
        print(f"  ✓ SM orbit is unique GTP-3 but GTP-{max(gtp_chains)} exists!")


if __name__ == "__main__":
    main()
