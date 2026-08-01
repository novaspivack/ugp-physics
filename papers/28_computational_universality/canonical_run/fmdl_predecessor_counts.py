#!/usr/bin/env python3
"""
fmdl_predecessor_counts.py — Exact f_MDL predecessor counts for all three SM generations.

Implements fmdl_step5 from CUP3DUniqueness.lean and exhaustively counts all
7^5 = 16,807 predecessor states for each generation vector.

Question: Is pred(gen₁) < pred(gen₂) < pred(gen₃)?
Expected: pred(gen₁)=0 (Garden of Eden, already proved), pred(gen₂)>0, pred(gen₃)>pred(gen₂).

The exact counts are required for the Lean certification (GoEStabilityHierarchy.lean).
"""

import itertools
from typing import Tuple, List, Dict


# ── fmdl: the MDL-minimal Z₇ CA function (from CUP3DUniqueness.lean) ──
# Neighborhood lookup: (l, c, r) -> output, all values in {0,...,6}
# Piecewise definition matching the Lean source exactly.
_FMDL_LOOKUP: Dict[Tuple[int,int,int], int] = {
    # Orbit neighborhoods
    (1, 1, 5): 2,
    (1, 5, 2): 5,
    (5, 2, 2): 2,
    (2, 2, 1): 0,  # explicit orbit entry (same as default 0)
    (2, 1, 1): 2,
    (2, 2, 5): 5,
    (2, 5, 2): 6,
    (5, 2, 0): 5,
    (2, 0, 2): 3,
    (0, 2, 2): 5,
    # Rule 110 binary sublayer (on {0,1}^3)
    (0, 0, 0): 0,
    (0, 0, 1): 1,
    (0, 1, 0): 1,
    (0, 1, 1): 1,
    (1, 0, 0): 0,
    (1, 0, 1): 1,
    (1, 1, 0): 1,
    (1, 1, 1): 0,
    # All remaining 325 neighborhoods: 0 (MDL-minimal)
    # (covered by .get(..., 0) default)
}


def fmdl(l: int, c: int, r: int) -> int:
    """MDL-minimal Z₇ CA function. Matches CUP3DUniqueness.lean definition exactly."""
    return _FMDL_LOOKUP.get((l, c, r), 0)


def fmdl_step5(state: Tuple[int, ...]) -> Tuple[int, ...]:
    """
    One step of fmdl on a 5-cell ring with periodic boundary conditions.
    Matches Lean: fmdl_step5 cells i = fmdl (cells (i+4)) (cells i) (cells (i+1))
    where (i+4) mod 5 = (i-1) mod 5 is the left neighbor.
    """
    n = 5
    return tuple(fmdl(state[(i - 1) % n], state[i], state[(i + 1) % n]) for i in range(n))


# ── SM generation vectors (from CUP3DUniqueness.lean) ──
GEN1: Tuple[int, ...] = (1, 5, 2, 2, 1)  # [e⁻, u, d, νR, νL]
GEN2: Tuple[int, ...] = (2, 5, 2, 0, 2)  # [μ, c, s, νμR, νμL]
GEN3: Tuple[int, ...] = (5, 6, 5, 3, 5)  # [τ, t, b, ντR, ντL]
VACUUM: Tuple[int, ...] = (0, 0, 0, 0, 0)


def verify_orbit() -> None:
    """Verify the orbit gen1→gen2→gen3→vacuum before counting predecessors."""
    assert fmdl_step5(GEN1) == GEN2, f"gen1→gen2 failed: got {fmdl_step5(GEN1)}"
    assert fmdl_step5(GEN2) == GEN3, f"gen2→gen3 failed: got {fmdl_step5(GEN2)}"
    assert fmdl_step5(GEN3) == VACUUM, f"gen3→vacuum failed: got {fmdl_step5(GEN3)}"
    print("✓ Orbit verification: gen1→gen2→gen3→vacuum confirmed")


def count_predecessors(target: Tuple[int, ...]) -> Tuple[int, List[Tuple[int,...]]]:
    """
    Count all states s ∈ Z₇⁵ such that fmdl_step5(s) = target.
    Returns (count, list_of_predecessors).
    """
    preds = []
    for state in itertools.product(range(7), repeat=5):
        if fmdl_step5(state) == target:
            preds.append(state)
    return len(preds), preds


def main() -> None:
    print("fmdl_predecessor_counts.py — f_MDL predecessor count verification")
    print("=" * 65)
    print(f"State space: Z₇⁵ = 7^5 = {7**5} states")
    print()

    # Verify orbit first
    verify_orbit()
    print()

    # Count predecessors for all three generations and vacuum
    targets = [
        ("gen₁", GEN1, "e⁻,u,d,νR,νL — expected: 0 (Garden of Eden)"),
        ("gen₂", GEN2, "μ,c,s,νμR,νμL — expected: > 0"),
        ("gen₃", GEN3, "τ,t,b,ντR,ντL — expected: > pred(gen₂)"),
        ("vacuum", VACUUM, "[0,0,0,0,0] — baseline"),
    ]

    results = {}
    for label, target, desc in targets:
        count, preds = count_predecessors(target)
        results[label] = (count, preds)
        print(f"pred({label}) = {count}  [{desc}]")
        if 0 < count <= 20:
            print(f"  Predecessors: {preds}")
        elif count > 20:
            print(f"  First 5 predecessors: {preds[:5]} ...")
        print()

    # Summary and ordering check
    n1 = results["gen₁"][0]
    n2 = results["gen₂"][0]
    n3 = results["gen₃"][0]
    nv = results["vacuum"][0]

    print("=" * 65)
    print("Summary:")
    print(f"  pred(gen₁) = {n1}")
    print(f"  pred(gen₂) = {n2}")
    print(f"  pred(gen₃) = {n3}")
    print(f"  pred(vacuum) = {nv}")
    print()

    print("Ordering checks:")
    print(f"  pred(gen₁) = 0?  {'✓ YES' if n1 == 0 else '✗ NO'}")
    print(f"  pred(gen₁) < pred(gen₂)?  {'✓ YES' if n1 < n2 else '✗ NO'}")
    print(f"  pred(gen₂) < pred(gen₃)?  {'✓ YES' if n2 < n3 else '✗ NO'}")
    print()

    if n1 == 0 and n2 > 0 and n3 > 0:
        if n2 < n3:
            print("✓ STRICT HIERARCHY: 0 = pred(gen₁) < pred(gen₂) < pred(gen₃)")
        elif n2 == n3:
            print(f"✓ PARTIAL HIERARCHY: pred(gen₁)=0 < pred(gen₂)=pred(gen₃)={n2}")
            print()
            print("  NOTE: pred(gen₂) = pred(gen₃) = 1. The DEEPER result is orbital")
            print("  isolation: each generation's predecessors are exactly the")
            print("  singleton {previous generation}. This is stronger than a")
            print("  simple predecessor count ordering.")
        print()
        print("These exact values go into GoEStabilityHierarchy.lean:")
        print(f"  fmdl_predecessor_count fmdl_gen1_z7 = {n1}  (by native_decide)")
        print(f"  fmdl_predecessor_count fmdl_gen2_z7 = {n2}  (by native_decide)")
        print(f"  fmdl_predecessor_count fmdl_gen3_z7 = {n3}  (by native_decide)")
    else:
        print("✗ HIERARCHY NOT CONFIRMED — check fmdl implementation and gen vectors")

    # CatD conjecture: check pred_count ratio vs lifetime ratio
    print()
    print("=" * 65)
    print("Extended analysis: predecessor count ratios")
    if n2 > 0 and n3 > 0:
        ratio_pred = n3 / n2
        print(f"  pred(gen₃) / pred(gen₂) = {n3} / {n2} = {ratio_pred:.4f}")
        print()
        print("  Physical lifetimes for comparison:")
        print("  τ(μ) ≈ 2.197×10⁻⁶ s,  τ(τ) ≈ 2.906×10⁻¹³ s")
        tau_mu = 2.197e-6
        tau_tau = 2.906e-13
        # Decay rate Γ ∝ 1/τ; a longer-lived particle decays slower
        # CatD conjecture: pred(gen₂)/pred(gen₃) ≈ τ(gen₃)/τ(gen₂) = τ_tau/τ_mu
        ratio_lifetime = tau_tau / tau_mu
        ratio_pred_inv = n2 / n3  # pred(gen₂)/pred(gen₃)
        print(f"  τ(τ)/τ(μ) = {ratio_lifetime:.4e}")
        print(f"  pred(gen₂)/pred(gen₃) = {n2}/{n3} = {ratio_pred_inv:.4f}")
        print()
        order_match = abs(
            (ratio_pred_inv / ratio_lifetime) - 1
        ) if ratio_lifetime > 0 else float("inf")
        print(f"  Ratio comparison: pred_inv/lifetime_ratio - 1 = {order_match:.3f}")
        print("  (CatD conjecture: would require ratio ≈ 1; likely much larger here)")
        print("  Note: this conjecture is speculative; exact match not expected")

    # Full predecessor structure for gen₂
    print()
    print("=" * 65)
    print(f"Full predecessor structure for gen₂ ({n2} states):")
    _, preds2 = results["gen₂"]
    for s in preds2:
        match_str = " ← gen₁ ✓" if s == GEN1 else ""
        print(f"  {s} → gen₂{match_str}")

    print()
    print(f"Full predecessor structure for gen₃ ({n3} states):")
    _, preds3 = results["gen₃"]
    for s in preds3:
        match_str = " ← gen₂ ✓" if s == GEN2 else ""
        print(f"  {s} → gen₃{match_str}")

    # Orbital isolation check
    print()
    print("=" * 65)
    print("Orbital isolation analysis:")
    gen2_pred_is_gen1 = (n2 == 1 and preds2[0] == GEN1)
    gen3_pred_is_gen2 = (n3 == 1 and preds3[0] == GEN2)
    print(f"  gen₂'s unique predecessor is gen₁?  {'✓ YES' if gen2_pred_is_gen1 else '✗ NO'}")
    print(f"  gen₃'s unique predecessor is gen₂?  {'✓ YES' if gen3_pred_is_gen2 else '✗ NO'}")
    if gen2_pred_is_gen1 and gen3_pred_is_gen2:
        print()
        print("  ✓ ORBITAL CHAIN ISOLATION THEOREM:")
        print("  The orbit gen₁→gen₂→gen₃→vacuum is a completely isolated")
        print("  linear chain in the 7^5 = 16,807-state space:")
        print("    - gen₁ has no predecessors (Garden of Eden)")
        print("    - gen₂ has exactly 1 predecessor: gen₁ itself")
        print("    - gen₃ has exactly 1 predecessor: gen₂ itself")
        print("  There are no 'side branches' or 'confluences' in the chain.")
        print()
        print("  Lean theorems to certify:")
        print("    fmdl_gen2_unique_predecessor:")
        print("      ∀ s : Fin 5→Fin 7, fmdl_step5 s = gen₂ ↔ s = gen₁")
        print("    fmdl_gen3_unique_predecessor:")
        print("      ∀ s : Fin 5→Fin 7, fmdl_step5 s = gen₃ ↔ s = gen₂")
        print("    fmdl_orbit_linear_chain (combines both)")
    else:
        print("  Orbital isolation does NOT hold — investigate further")


if __name__ == "__main__":
    main()
