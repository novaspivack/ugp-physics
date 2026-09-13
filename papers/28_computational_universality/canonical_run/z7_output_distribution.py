"""
Z₇ f_MDL output distribution analysis.

Computes:
  - The exact preimage count for each Z₇ output value 0–6 under fmdl (7³ = 343 inputs)
  - Comparison of charge-conjugate pairs (v, 7−v mod 7)
  - Verification that W⁺ (Z₇=3) outputs outnumber W⁻/e⁻ (Z₇=4) outputs
  - Complete matter vs antimatter breakdown using Z₇ conjugation structure

The fmdl function is the MDL-minimal Z₇ CA satisfying the 18 orbit + Rule 110
neighborhood constraints (25 fixed, 325 free→0). See P28 §6.2.

Saves results to z7_output_distribution_results.json.
"""

import json
from itertools import product
from pathlib import Path

# ─── fmdl: MDL-minimal Z₇ CA function ────────────────────────────────────────
# 10 orbit neighborhoods (gen₁→gen₂ and gen₂→gen₃ transitions on 5-cell ring)
# 8 Rule 110 binary neighborhoods
# 325 free neighborhoods → 0
def fmdl(l: int, c: int, r: int) -> int:
    """MDL-minimal Z₇ CA function. Inputs and output are in {0,...,6}."""
    # Orbit neighborhoods (gen₁→gen₂)
    if l == 1 and c == 1 and r == 5: return 2
    if l == 1 and c == 5 and r == 2: return 5
    if l == 5 and c == 2 and r == 2: return 2
    if l == 2 and c == 2 and r == 1: return 0
    if l == 2 and c == 1 and r == 1: return 2
    # Orbit neighborhoods (gen₂→gen₃)
    if l == 2 and c == 2 and r == 5: return 5
    if l == 2 and c == 5 and r == 2: return 6   # quark flavor-change
    if l == 5 and c == 2 and r == 0: return 5
    if l == 2 and c == 0 and r == 2: return 3   # W⁺ emission
    if l == 0 and c == 2 and r == 2: return 5
    # Rule 110 binary neighborhoods (values in {0,1})
    if l == 0 and c == 0 and r == 0: return 0
    if l == 0 and c == 0 and r == 1: return 1
    if l == 0 and c == 1 and r == 0: return 1
    if l == 0 and c == 1 and r == 1: return 1
    if l == 1 and c == 0 and r == 0: return 0
    if l == 1 and c == 0 and r == 1: return 1
    if l == 1 and c == 1 and r == 0: return 1
    if l == 1 and c == 1 and r == 1: return 0
    # All remaining 325 neighborhoods: 0 (MDL-minimal)
    return 0


def z7_conj(v: int) -> int:
    """Z₇ charge conjugation: C(v) = (7 − v) % 7."""
    return (7 - v) % 7


def compute_preimage_counts() -> dict[int, int]:
    """Count how many of the 343 input triples map to each Z₇ output value."""
    counts: dict[int, int] = {v: 0 for v in range(7)}
    for l, c, r in product(range(7), repeat=3):
        counts[fmdl(l, c, r)] += 1
    return counts


def preimage_set(v: int) -> list[tuple[int, int, int]]:
    """Return all (l, c, r) triples for which fmdl(l, c, r) = v."""
    return [(l, c, r) for l, c, r in product(range(7), repeat=3) if fmdl(l, c, r) == v]


def compute_conjugate_pair_analysis(counts: dict[int, int]) -> list[dict]:
    """For each Z₇ conjugate pair, report both members' counts and asymmetry."""
    # Conjugate pairs: (0,0), (1,6), (2,5), (3,4)
    pairs = [
        (0, 0, "ν (self-conj)", "ν (self-conj)"),
        (1, 6, "anti-d (binary sublayer)", "d-quark"),
        (2, 5, "u-quark", "anti-u"),
        (3, 4, "W⁺/e⁺", "W⁻/e⁻"),
    ]
    result = []
    for v, cv, v_name, cv_name in pairs:
        n_v = counts[v]
        n_cv = counts[cv]
        if n_cv == 0:
            ratio_str = "∞ (hard exclusion)"
        elif n_v == 0:
            ratio_str = "0 (fully antimatter)"
        else:
            ratio_str = f"{n_v / n_cv:.3f}"
        result.append({
            "v": v,
            "conj_v": cv,
            "v_name": v_name,
            "cv_name": cv_name,
            "count_v": n_v,
            "count_conj_v": n_cv,
            "ratio_v_to_cv": ratio_str,
            "symmetric": n_v == n_cv,
            "cv_excluded": n_cv == 0,
        })
    return result


def verify_sec9_3_comparison(counts: dict[int, int]) -> dict:
    """
    Verify §9.3 of P28: W⁺ (Z₇=3) vs W⁻/e⁻ (Z₇=4) direct f_MDL output comparison.

    §9.3 discusses the steady-state distribution from a 3D simulation (T=500),
    not direct f_MDL output counts. This function checks the DIRECT f_MDL output
    distribution and compares to the §9.3 claims.
    """
    w_plus_count = counts[3]   # Z₇=3: W⁺/e⁺
    w_minus_count = counts[4]  # Z₇=4: W⁻/e⁻

    # §9.3 claims W⁺ (Z₇=3) at 4.1% vs W⁻/electron (Z₇=4) at 1.3% in simulation
    # Direct f_MDL output: W⁺ at 1 neighborhood, W⁻/e⁻ at 0 neighborhoods
    # → The structural claim (Z₇=4 completely excluded from direct output) is STRONGER
    #   than the simulation result (1.3% via cross-dimensional addition)

    matter_dominant = w_plus_count > w_minus_count
    z4_completely_excluded = w_minus_count == 0

    # Check full conjugate picture for §9.3 context
    # §9.3 says "positive-winding {2,3} dominate over negative-winding {4,6}"
    # Under C: C(2)=5 (not 4 or 6), C(3)=4 ✓
    # Note: d-quark at Z₇=6 is MATTER (W=-1), not antimatter; anti-d is Z₇=1
    # The grouping {2,3} vs {4,6} mixes the particle/antiparticle distinction
    # with winding sign; true C-conjugate pairs are (2,5) and (3,4).
    positive_winding_total = counts[2] + counts[3]  # u + W⁺ (P28 §9.3 "matter")
    negative_winding_total = counts[4] + counts[6]  # W⁻/e⁻ + d (P28 §9.3 "antimatter")

    # True C-conjugate comparison (correct matter/antimatter pairs)
    true_matter_total = counts[2] + counts[3]          # u (Z₇=2) + W⁺ (Z₇=3)
    true_antimatter_total = counts[5] + counts[4]      # anti-u (Z₇=5) + W⁻/e⁻ (Z₇=4)

    return {
        "section_93_w_plus_count": w_plus_count,
        "section_93_w_minus_count": w_minus_count,
        "w_plus_dominant_in_fmdl_outputs": matter_dominant,
        "z4_completely_excluded": z4_completely_excluded,
        "p28_matter_winding_group_2_3": positive_winding_total,
        "p28_antimatter_winding_group_4_6": negative_winding_total,
        "true_conj_matter_2_3": true_matter_total,
        "true_conj_antimatter_5_4": true_antimatter_total,
        "note": (
            "§9.3 compares positive-winding {Z₇=2,3} vs negative-winding {Z₇=4,6}. "
            "Under Z₇ charge conjugation C(v)=7-v, the correct conjugate pairs are "
            "(2,5) and (3,4) — not (2,6). The d-quark (Z₇=6) has conjugate anti-d "
            "at Z₇=1, not Z₇=2. The §9.3 comparison is physically motivated by "
            "winding sign (positive vs negative) but differs from C-conjugate pairs. "
            "The strongest arithmetic claim remains: Z₇=4 is COMPLETELY EXCLUDED "
            "from direct f_MDL output (confirmed: count=0), while Z₇=3 appears once."
        ),
        "correction_needed": (
            "The §9.3 W⁺ vs W⁻/electron comparison is valid FOR THAT PAIR (3,4) — "
            "count(3)=1 vs count(4)=0 confirms matter dominance for the (W⁺,W⁻/e⁻) "
            "pair. However, the broader claim 'positive-winding {2,3} dominates "
            "negative-winding {4,6}' is conflating winding sign with C-conjugation. "
            "The d-quark (Z₇=6) is matter (C(6)=1=anti-d), and anti-u (Z₇=5) is "
            "the true C-conjugate of u (Z₇=2). The corrected arithmetic statement "
            "should focus on the (3,4) pair specifically."
        ),
    }


def main():
    counts = compute_preimage_counts()

    # Sanity check: total must be 343 = 7³
    total = sum(counts.values())
    assert total == 343, f"Expected 343 total inputs, got {total}"

    # Get preimage sets for non-zero values
    preimage_sets = {str(v): preimage_set(v) for v in range(1, 7)}

    conjugate_analysis = compute_conjugate_pair_analysis(counts)
    sec93_check = verify_sec9_3_comparison(counts)

    # Summary statistics
    non_vacuum_outputs = {v: counts[v] for v in range(1, 7)}
    matter_like = counts[2] + counts[3] + counts[6]    # u, W⁺, d (positive or matter winding)
    antimatter_like = counts[1] + counts[4] + counts[5]  # anti-d, W⁻/e⁻, anti-u

    # True C-conjugate matter vs antimatter (non-vacuum)
    # Using the three conjugate pairs: (1,6), (2,5), (3,4)
    # Convention: "matter" = lower-index of each pair = {1, 2, 3} (by winding sign)
    # Actually: u (Z₇=2, W=+2) and W⁺ (Z₇=3, W=+3) have positive winding
    # d (Z₇=6, W=-1) and e⁻ (Z₇=4, W=-3) have negative winding
    # ν (Z₇=0, W=0) is self-conjugate
    # anti-u (Z₇=5), anti-d (Z₇=1) are antiparticles of quarks

    output_range = sorted([v for v in range(7) if counts[v] > 0])
    conj_closed = all(
        counts[z7_conj(v)] > 0 for v in output_range
    )

    results = {
        "description": "Z₇ f_MDL output distribution — preimage counts for each Z₇ value",
        "total_inputs": total,
        "fmdl_description": "MDL-minimal Z₇ CA: 10 orbit + 8 Rule110 + 325 free→0 neighborhoods",
        "preimage_counts": counts,
        "output_range": output_range,
        "output_range_conj_closed": conj_closed,
        "missing_from_range": [v for v in range(7) if counts[v] == 0],
        "preimage_sets_nonzero": preimage_sets,
        "conjugate_pair_analysis": conjugate_analysis,
        "nonvacuum_counts": non_vacuum_outputs,
        "matter_like_total_2_3_6": matter_like,
        "antimatter_like_total_1_4_5": antimatter_like,
        "section_93_verification": sec93_check,
        "key_findings": [
            "Z₇=4 (W⁻/e⁻) has ZERO preimage under fmdl: completely excluded from direct f_MDL output",
            "Z₇=3 (W⁺) has exactly 1 preimage: the W⁺ emission neighborhood (2,0,2)",
            "The (3,4) conjugate pair is the UNIQUE pair with one side completely excluded",
            "Output range {0,1,2,3,5,6} is NOT closed under charge conjugation C(v)=7-v",
            "Other conjugate pairs: (1,6) both in range (5:1 count ratio), (2,5) both in range (3:4)",
            "The d-quark (Z₇=6, count=1) via quark flavor-change neighborhood (2,5,2)",
            "Z₇=1 appears 5 times from the Rule 110 binary sublayer (binary '1' outputs)",
        ],
    }

    output_path = Path(__file__).parent / "z7_output_distribution_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print("Z₇ f_MDL Output Distribution")
    print("=" * 50)
    print(f"Total inputs: {total} (7³ = 343)")
    print()
    print("Preimage counts by Z₇ value:")
    physical_names = {0: "vacuum/ν", 1: "anti-d (binary)", 2: "u-quark",
                      3: "W⁺/e⁺", 4: "W⁻/e⁻", 5: "anti-u", 6: "d-quark"}
    for v in range(7):
        bar = "█" * counts[v] if counts[v] <= 30 else "█" * 30 + "…"
        excl = " ← EXCLUDED (Lean-certified)" if v == 4 else ""
        print(f"  Z₇={v} ({physical_names[v]:18s}): {counts[v]:3d}  {bar}{excl}")

    print()
    print("Conjugate pair analysis (C(v) = 7−v mod 7):")
    for entry in conjugate_analysis:
        v, cv = entry["v"], entry["conj_v"]
        n_v, n_cv = entry["count_v"], entry["count_conj_v"]
        ratio = entry["ratio_v_to_cv"]
        flag = " *** MAXIMAL CP ASYMMETRY ***" if entry["cv_excluded"] and v != cv else ""
        if v == cv:
            print(f"  ({v},{cv}) self-conjugate: count={n_v}")
        else:
            print(f"  ({v},{cv}) {entry['v_name']} vs {entry['cv_name']}: "
                  f"{n_v} vs {n_cv}, ratio {ratio}{flag}")

    print()
    print("§9.3 W⁺ vs W⁻/e⁻ verification:")
    print(f"  W⁺ (Z₇=3) direct f_MDL count: {counts[3]}")
    print(f"  W⁻/e⁻ (Z₇=4) direct f_MDL count: {counts[4]}")
    print(f"  Z₇=4 completely excluded: {counts[4] == 0}")
    print(f"  (§9.3's 4.1%:1.3% is from 3D simulation steady-state, not direct f_MDL)")

    print()
    print(f"Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    main()
