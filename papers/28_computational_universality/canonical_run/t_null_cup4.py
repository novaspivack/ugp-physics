"""
t_null_cup4.py — CUP-4 Null Test (Round 12)

Statistical null test for the CUP-4 commutativity result from Round 11.

Round 11 found: phi=total_parity=(a+b+c)%2 applied to the SM GTE triples,
with particle ordering [charged_lepton, u_quark, d_quark, neutrino_RH, neutrino_LH]
gives gen1=[1,1,0,0,1] → gen2=[0,1,0,1,1] → gen3=[1,1,1,1,1] under Rule 110
with periodic boundary conditions. Exact 2-step commutativity: 10/10 conditions.

This script asks: is this a genuine structural result or a small-sample coincidence?
Five null tests:
  Part 1: Exhaustive ordering test (all 120 orderings × 256 rules)
  Part 2: Random orbit null — what fraction of Rule 110 orbits end at all-ones?
  Part 3: Row assignment null — does direction of orbit matter?
  Part 4: Random GTE false-positive rate — how often does random data match?
  Part 5: Boundary condition sensitivity — does result hold under all BCs?

Results saved to: t_null_cup4_results.json
"""

import json
import itertools
import random
import numpy as np
from collections import defaultdict

random.seed(42)
np.random.seed(42)

# ── SM GTE Cascade (TRUE T_GTE from SM paper, validated in Round 11) ──────────

GTE_CASCADE = {
    'charged_lepton': [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    'u_quark':        [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    'd_quark':        [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    'neutrino_RH':    [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    'neutrino_LH':    [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}

FAMILY_NAMES = list(GTE_CASCADE.keys())  # canonical order
UNIVERSAL_RULES = {110, 124, 137, 193}

# phi = total_parity = (a+b+c) mod 2
def total_parity(a, b, c):
    return (int(a) + int(b) + int(c)) % 2

# Precompute family bit patterns: FAMILY_BITS[family] = [bit_gen1, bit_gen2, bit_gen3]
FAMILY_BITS = {
    family: [total_parity(*t) for t in triples]
    for family, triples in GTE_CASCADE.items()
}

# Winning ordering from Round 11: [lep, u, d, nuR, nuL]
WINNING_ORDER_FAMILIES = ['charged_lepton', 'u_quark', 'd_quark', 'neutrino_RH', 'neutrino_LH']
GEN1_ROW = [FAMILY_BITS[f][0] for f in WINNING_ORDER_FAMILIES]  # [1, 1, 0, 0, 1]
GEN2_ROW = [FAMILY_BITS[f][1] for f in WINNING_ORDER_FAMILIES]  # [0, 1, 0, 1, 1]
GEN3_ROW = [FAMILY_BITS[f][2] for f in WINNING_ORDER_FAMILIES]  # [1, 1, 1, 1, 1]


# ── CA rule functions ──────────────────────────────────────────────────────────

def rule_step(rule_num, cells, boundary='periodic'):
    """Apply elementary CA rule_num to a list of cells with given boundary condition."""
    n = len(cells)
    new_cells = []
    for i in range(n):
        if boundary == 'periodic':
            left  = cells[(i - 1) % n]
            right = cells[(i + 1) % n]
        elif boundary == 'zero':
            left  = 0 if i == 0     else cells[i - 1]
            right = 0 if i == n - 1 else cells[i + 1]
        elif boundary == 'one':
            left  = 1 if i == 0     else cells[i - 1]
            right = 1 if i == n - 1 else cells[i + 1]
        else:
            raise ValueError(f"Unknown boundary: {boundary}")
        center = cells[i]
        bit_idx = (left << 2) | (center << 1) | right
        new_cells.append((rule_num >> bit_idx) & 1)
    return new_cells


def check_2step(gen1, gen2, gen3, rule_num=110, boundary='periodic'):
    """Return True if rule_num maps gen1→gen2 AND gen2→gen3."""
    pred2 = rule_step(rule_num, gen1, boundary)
    if pred2 != gen2:
        return False
    pred3 = rule_step(rule_num, gen2, boundary)
    return pred3 == gen3


# ── PART 1: Exhaustive ordering × 256-rule test ────────────────────────────────

def part1_exhaustive_ordering_test():
    """
    For each of 5!=120 orderings of the 5 particle families into 5 cell positions,
    and each of 256 CA rules: check 2-step commutativity with periodic BCs.

    Returns dict with results.
    """
    print("\n" + "=" * 62)
    print("PART 1: Exhaustive Ordering Test (120 orderings × 256 rules)")
    print("=" * 62)

    all_orderings = list(itertools.permutations(range(5)))

    # rule_winners[r] = list of orderings (as index tuples) achieving 2-step commutativity
    rule_winners = {r: [] for r in range(256)}
    rule110_winner_details = []

    for ordering in all_orderings:
        ordered_families = [FAMILY_NAMES[i] for i in ordering]
        gen1 = [FAMILY_BITS[f][0] for f in ordered_families]
        gen2 = [FAMILY_BITS[f][1] for f in ordered_families]
        gen3 = [FAMILY_BITS[f][2] for f in ordered_families]

        for r in range(256):
            pred2 = rule_step(r, gen1, 'periodic')
            if pred2 != gen2:
                continue
            pred3 = rule_step(r, gen2, 'periodic')
            if pred3 == gen3:
                rule_winners[r].append(ordering)
                if r == 110:
                    rule110_winner_details.append({
                        'ordering_indices': list(ordering),
                        'ordered_families': ordered_families,
                        'gen1': gen1,
                        'gen2': gen2,
                        'gen3': gen3,
                    })

    n110 = len(rule_winners[110])
    print(f"\n  Rule 110 winning orderings: {n110} / 120 = {n110/120:.2%}")
    print(f"  Winning orderings (Rule 110):")
    for det in rule110_winner_details:
        print(f"    {det['ordered_families']}")
        print(f"      gen1={det['gen1']}, gen2={det['gen2']}, gen3={det['gen3']}")

    # Rule-level survey
    winner_counts = {r: len(rule_winners[r]) for r in range(256)}
    n_zero     = sum(1 for r in range(256) if winner_counts[r] == 0)
    n_positive = 256 - n_zero

    # Rank Rule 110: how many rules have >= n110 winning orderings?
    rule110_rank = sum(1 for r in range(256) if winner_counts[r] >= n110)

    print(f"\n  Rules with 0 winning orderings: {n_zero} / 256")
    print(f"  Rules with 1+ winning orderings: {n_positive} / 256")
    print(f"  Rule 110 rank: #{rule110_rank} of 256 (top {rule110_rank/256:.1%})")

    # Top 10 rules
    top_rules = sorted(range(256), key=lambda r: -winner_counts[r])
    print(f"\n  Top 10 rules by winning orderings:")
    for r in top_rules[:10]:
        tag = " [UNIVERSAL]" if r in UNIVERSAL_RULES else ""
        print(f"    Rule {r:>3}{tag}: {winner_counts[r]} winning orderings")

    return {
        'n_rule110_winning_orderings': n110,
        'fraction_rule110': n110 / 120,
        'rule110_winner_details': rule110_winner_details,
        'rules_with_zero_winners': n_zero,
        'rules_with_positive_winners': n_positive,
        'rule110_rank_of_256': rule110_rank,
        'winner_counts_all_rules': {str(r): winner_counts[r] for r in range(256)},
        'top_10_rules': [(r, winner_counts[r]) for r in top_rules[:10]],
    }


# ── PART 2: Random orbit null (CUP-8) ─────────────────────────────────────────

def part2_random_orbit_null(N=100_000):
    """
    Generate N random binary 5-vectors as 'gen1', apply Rule 110 twice,
    check what fraction end at gen3=[1,1,1,1,1].

    Also do exact enumeration over all 32 possible gen1 vectors.
    """
    print("\n" + "=" * 62)
    print("PART 2: Random Orbit Null (CUP-8 — gen3=all-ones prevalence)")
    print("=" * 62)

    all_ones = [1, 1, 1, 1, 1]

    # --- Exact enumeration (all 32 gen1 vectors) ---
    exact_all_ones = 0
    exact_gen1_to_gen3 = {}  # (gen1 tuple) -> gen3 tuple
    for gen1_tup in itertools.product([0, 1], repeat=5):
        gen1 = list(gen1_tup)
        gen2 = rule_step(110, gen1, 'periodic')
        gen3 = rule_step(110, gen2, 'periodic')
        exact_gen1_to_gen3[gen1_tup] = tuple(gen3)
        if gen3 == all_ones:
            exact_all_ones += 1

    # --- Monte Carlo confirmation ---
    mc_count = 0
    for _ in range(N):
        gen1 = [random.randint(0, 1) for _ in range(5)]
        gen2 = rule_step(110, gen1, 'periodic')
        gen3 = rule_step(110, gen2, 'periodic')
        if gen3 == all_ones:
            mc_count += 1

    exact_frac = exact_all_ones / 32
    mc_frac    = mc_count / N

    print(f"\n  Exact enumeration (all 32 gen1 vectors):")
    print(f"    gen3=all-ones: {exact_all_ones}/32 = {exact_frac:.4%}")
    gen1_to_allones = [g for g, g3 in exact_gen1_to_gen3.items() if list(g3) == all_ones]
    print(f"    gen1 vectors that produce all-ones gen3:")
    for g in gen1_to_allones:
        print(f"      {list(g)}")

    print(f"\n  Monte Carlo (N={N:,}):")
    print(f"    gen3=all-ones: {mc_count}/{N} = {mc_frac:.4%}")
    print(f"    (Consistent with exact: {abs(mc_frac - exact_frac) < 0.02})")

    return {
        'exact_gen1_count_to_allones': exact_all_ones,
        'exact_fraction': exact_frac,
        'exact_gen1_vectors_to_allones': [list(g) for g in gen1_to_allones],
        'monte_carlo_N': N,
        'monte_carlo_count': mc_count,
        'monte_carlo_fraction': mc_frac,
    }


# ── PART 3: Row assignment null ────────────────────────────────────────────────

def part3_row_assignment_null():
    """
    The 5 families each have bits (gen1_bit, gen2_bit, gen3_bit).
    A 'row assignment' permutes which generation slot is used as (row_a, row_b, row_c).
    For each of 3!=6 assignments, test all 120 family orderings for Rule 110 commutativity.

    Identity (0,1,2) = natural forward evolution (Round 11 result).
    Tests whether the direction of the orbit matters.
    """
    print("\n" + "=" * 62)
    print("PART 3: Row Assignment Null (3!=6 generation permutations)")
    print("=" * 62)

    gen_labels = ['gen1', 'gen2', 'gen3']
    gen_perms  = list(itertools.permutations([0, 1, 2]))  # 6 permutations

    results = []
    n_with_winners = 0

    for gen_perm in gen_perms:
        label = (f"({gen_labels[gen_perm[0]]}→row_a, "
                 f"{gen_labels[gen_perm[1]]}→row_b, "
                 f"{gen_labels[gen_perm[2]]}→row_c)")
        is_identity = gen_perm == (0, 1, 2)

        winning_orderings = []
        for ordering in itertools.permutations(range(5)):
            fam_list = [FAMILY_NAMES[i] for i in ordering]
            row_a = [FAMILY_BITS[f][gen_perm[0]] for f in fam_list]
            row_b = [FAMILY_BITS[f][gen_perm[1]] for f in fam_list]
            row_c = [FAMILY_BITS[f][gen_perm[2]] for f in fam_list]

            pred_b = rule_step(110, row_a, 'periodic')
            if pred_b == row_b:
                pred_c = rule_step(110, row_b, 'periodic')
                if pred_c == row_c:
                    winning_orderings.append(list(ordering))

        n_win = len(winning_orderings)
        if n_win > 0:
            n_with_winners += 1

        flag = " ← NATURAL (Round 11 result)" if is_identity else ""
        print(f"  {label}: {n_win}/120 winners{flag}")

        results.append({
            'gen_perm': list(gen_perm),
            'label': label,
            'is_identity': is_identity,
            'n_winning_orderings': n_win,
            'winning_orderings': winning_orderings,
        })

    print(f"\n  Row assignments with any winning ordering: {n_with_winners} / 6")

    return {
        'n_assignments_tested': 6,
        'n_assignments_with_winners': n_with_winners,
        'results': results,
    }


# ── PART 4: Random GTE false-positive rate ────────────────────────────────────

def part4_random_gte_false_positive(N=10_000):
    """
    Generate N random GTE-like 5×3 parity matrices.
    For each: test all 120 orderings for Rule 110 2-step commutativity.
    Report the fraction (false-positive rate).

    Random triples: a in [1,10], b in [1,1000000], c in [1,10000].
    phi = (a+b+c) % 2.
    """
    print("\n" + "=" * 62)
    print("PART 4: Random GTE False-Positive Rate")
    print("=" * 62)

    all_orderings = list(itertools.permutations(range(5)))
    false_positives = 0

    for _ in range(N):
        # Generate 5 families × 3 generations of random (a,b,c) triples
        # bits[gen_idx][family_idx] = phi bit
        bits = []
        for _g in range(3):
            row = []
            for _f in range(5):
                a = random.randint(1, 10)
                b = random.randint(1, 1_000_000)
                c = random.randint(1, 10_000)
                row.append((a + b + c) % 2)
            bits.append(row)

        # Test all 120 orderings for Rule 110 commutativity
        found = False
        for ordering in all_orderings:
            gen1 = [bits[0][i] for i in ordering]
            gen2 = [bits[1][i] for i in ordering]
            gen3 = [bits[2][i] for i in ordering]

            pred2 = rule_step(110, gen1, 'periodic')
            if pred2 != gen2:
                continue
            pred3 = rule_step(110, gen2, 'periodic')
            if pred3 == gen3:
                found = True
                break

        if found:
            false_positives += 1

    fpr = false_positives / N
    # Theoretical union bound: 120 × (1/2)^10 ≈ 11.7%
    theoretical = 120 / 1024

    print(f"\n  N = {N:,} random GTE parity assignments tested")
    print(f"  Experiments with >= 1 winning Rule 110 ordering: {false_positives}")
    print(f"  Empirical false-positive rate: {fpr:.4%}")
    print(f"  Theoretical union bound (120 × (1/2)^10): {theoretical:.4%}")

    return {
        'N': N,
        'false_positives': false_positives,
        'false_positive_rate': fpr,
        'theoretical_union_bound': theoretical,
    }


# ── PART 5: Boundary condition sensitivity ────────────────────────────────────

def part5_boundary_sensitivity():
    """
    Test the winning ordering [lep, u, d, nuR, nuL] under three boundary conditions:
    periodic (wrap), zero (fixed-0), one (fixed-1).
    """
    print("\n" + "=" * 62)
    print("PART 5: Boundary Condition Sensitivity")
    print("=" * 62)

    gen1 = GEN1_ROW  # [1, 1, 0, 0, 1]
    gen2 = GEN2_ROW  # [0, 1, 0, 1, 1]
    gen3 = GEN3_ROW  # [1, 1, 1, 1, 1]

    print(f"\n  Winning ordering: {WINNING_ORDER_FAMILIES}")
    print(f"  gen1 = {gen1}")
    print(f"  gen2 = {gen2} (expected)")
    print(f"  gen3 = {gen3} (expected)")

    bc_results = {}
    working_bcs = []

    for bc in ('periodic', 'zero', 'one'):
        pred2 = rule_step(110, gen1, bc)
        pred3 = rule_step(110, gen2, bc)
        ok12 = pred2 == gen2
        ok23 = pred3 == gen3
        full = ok12 and ok23
        if full:
            working_bcs.append(bc)

        print(f"\n  Boundary = {bc}:")
        print(f"    Rule110({gen1}) = {pred2}")
        print(f"    Expected gen2:   {gen2}  → {'✓ MATCH' if ok12 else '✗ MISMATCH'}")
        print(f"    Rule110({gen2}) = {pred3}")
        print(f"    Expected gen3:   {gen3}  → {'✓ MATCH' if ok23 else '✗ MISMATCH'}")
        print(f"    Full 2-step commutativity: {'YES' if full else 'NO'}")

        bc_results[bc] = {
            'pred_gen2': pred2,
            'pred_gen3': pred3,
            'gen1_to_gen2_ok': ok12,
            'gen2_to_gen3_ok': ok23,
            'full_commutativity': full,
        }

    print(f"\n  Winning ordering works under BCs: {working_bcs}")
    print(f"  Specificity: {'ALL 3 BCs work' if len(working_bcs) == 3 else f'Only {working_bcs}'}")

    return {
        'gen1': gen1,
        'gen2': gen2,
        'gen3': gen3,
        'winning_ordering': WINNING_ORDER_FAMILIES,
        'boundary_results': bc_results,
        'working_boundaries': working_bcs,
    }


# ── Main orchestrator ──────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("CUP-4 NULL TEST — Round 12")
    print("=" * 62)
    print()
    print("Parity rows under total_parity phi=(a+b+c)%2:")
    print(f"  Winning ordering: {WINNING_ORDER_FAMILIES}")
    print(f"  gen1 = {GEN1_ROW}")
    print(f"  gen2 = {GEN2_ROW}")
    print(f"  gen3 = {GEN3_ROW}")
    print()
    print("Family bit patterns [gen1_bit, gen2_bit, gen3_bit]:")
    for f in FAMILY_NAMES:
        print(f"  {f}: {FAMILY_BITS[f]}")

    # ── Run all 5 parts ────────────────────────────────────────────────────────
    r1 = part1_exhaustive_ordering_test()
    r2 = part2_random_orbit_null(N=100_000)
    r3 = part3_row_assignment_null()
    r4 = part4_random_gte_false_positive(N=10_000)
    r5 = part5_boundary_sensitivity()

    # ── Compute p-value estimate ───────────────────────────────────────────────
    # p-value: probability that random GTE-like data gives >= n110 winning orderings
    # for Rule 110. From Part 4: empirical false-positive rate.
    fpr         = r4['false_positive_rate']
    n110        = r1['n_rule110_winning_orderings']
    r110_rank   = r1['rule110_rank_of_256']
    n_working   = len(r5['working_boundaries'])
    gen3_allones_frac = r2['exact_fraction']

    # Structural p-value components:
    # 1. P(random data gives Rule 110 commutativity for any ordering) ≈ fpr
    # 2. P(Rule 110 is at its observed rank among 256 rules) ≈ r110_rank / 256
    # 3. P(gen3=all-ones) from exact enumeration = gen3_allones_frac
    # Combined structural p-value (approximately, ignoring correlations):
    p_combined = fpr * (r110_rank / 256) * gen3_allones_frac

    # ── Summary report ─────────────────────────────────────────────────────────
    print("\n\n" + "=" * 62)
    print("=== CUP-4 NULL TEST RESULTS ===")
    print("=" * 62)
    print()
    print(f"Part 1: Ordering exhaustion (Rule 110, periodic BC)")
    print(f"  Orderings giving exact 2-step commutativity: {n110} / 120")
    print(f"  Fraction: {n110}/120 = {n110/120:.2%}")
    print(f"  Winning orderings:")
    for det in r1['rule110_winner_details']:
        print(f"    {det['ordered_families']}")
    print(f"")
    print(f"  Rules with 0 winning orderings: {r1['rules_with_zero_winners']} / 256")
    print(f"  Rules with 1+ winning orderings: {r1['rules_with_positive_winners']} / 256")
    print(f"  Rule 110 rank: #{r110_rank} of 256 (top {r110_rank/256:.1%})")
    top10 = r1['top_10_rules']
    print(f"  Top rules: {[(r, n) for r, n in top10[:5]]}")
    print()
    print(f"Part 2: Random orbit null (CUP-8)")
    print(f"  Exact fraction of Rule 110 orbits with gen3=all-ones: "
          f"{r2['exact_gen1_count_to_allones']}/32 = {gen3_allones_frac:.4%}")
    print(f"  gen1 vectors that produce all-ones gen3: {r2['exact_gen1_vectors_to_allones']}")
    print()
    print(f"Part 3: Row assignment null")
    print(f"  Assignments allowing any commutativity: "
          f"{r3['n_assignments_with_winners']} / 6")
    for res in r3['results']:
        flag = " ← natural (Round 11)" if res['is_identity'] else ""
        print(f"    {res['label']}: {res['n_winning_orderings']}/120 winners{flag}")
    print()
    print(f"Part 4: Random GTE false-positive rate")
    print(f"  Fraction of random GTE assignments with >= 1 winning ordering: "
          f"{r4['false_positive_rate']:.4%}")
    print(f"  (N={r4['N']:,}; theoretical union bound: "
          f"{r4['theoretical_union_bound']:.2%})")
    print()
    print(f"Part 5: Boundary condition sensitivity")
    print(f"  Winning ordering works under: {r5['working_boundaries']}")
    print()
    print(f"=== VERDICT ===")
    print(f"  False-positive rate (raw, any rule 110 + any ordering): {fpr:.4%}")
    print(f"  Rule 110 percentile rank (top {r110_rank/256:.1%}): rank #{r110_rank}/256")
    print(f"  Gen3=all-ones prevalence: {gen3_allones_frac:.4%} ({r2['exact_gen1_count_to_allones']}/32 orbits)")
    print(f"  BC specificity: works under {n_working}/3 boundary conditions")
    print()
    print(f"  Naive p-value (raw false-positive rate): {fpr:.4%}")
    print(f"  Structural p-value (raw × rule rank × gen3 prevalence): {p_combined:.6f}")
    print()
    if n110 == 2 and r110_rank <= 10 and gen3_allones_frac < 0.5:
        print("  Interpretation: The false-positive rate (~10%) is NOT small enough to")
        print("  claim statistical significance on brute-force grounds alone.")
        print("  However, the STRUCTURAL constraints (gen3=all-ones, Rule 110 top rank,")
        print("  specific phi=total_parity, UWCA bisimulation theorem) lower the effective")
        print("  p-value substantially. Significance depends on whether the test was")
        print("  conducted prospectively (low effective p) or post-hoc (high effective p).")
    else:
        print("  Interpretation: [see raw numbers above]")

    # ── Save results ───────────────────────────────────────────────────────────
    output = {
        'round': 12,
        'test': 'CUP-4 null test',
        'summary': {
            'gen1_row': GEN1_ROW,
            'gen2_row': GEN2_ROW,
            'gen3_row': GEN3_ROW,
            'winning_ordering': WINNING_ORDER_FAMILIES,
            'family_bits': FAMILY_BITS,
        },
        'part1_exhaustive_ordering': r1,
        'part2_random_orbit_null': r2,
        'part3_row_assignment_null': r3,
        'part4_random_gte_fpr': r4,
        'part5_boundary_sensitivity': r5,
        'verdict': {
            'n_rule110_winning_orderings': n110,
            'rule110_rank_of_256': r110_rank,
            'gen3_allones_exact_fraction': gen3_allones_frac,
            'false_positive_rate_empirical': fpr,
            'theoretical_union_bound': r4['theoretical_union_bound'],
            'n_working_boundary_conditions': n_working,
            'naive_p_value': fpr,
            'structural_p_value': p_combined,
        },
    }

    with open('t_null_cup4_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("\nResults saved to t_null_cup4_results.json")


if __name__ == '__main__':
    main()
