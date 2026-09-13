"""
Direction 1 — Genetic Code Phase 2: Prebiotic Chemistry Viability Layer

Phase 2 adds a second, independent Stage 2 viability filter on top of the
wobble admissibility (Stage 1) from Phase 1.

Stage 2 has two components:
  2A. Error-minimization score (Phase 1 — Freeland-Hurst)
  2B. Prebiotic amino acid accessibility — new here

The prebiotic accessibility hypothesis (Wong 1975 co-evolution theory;
Knight-Landweber-Yarus 1999):
  The genetic code was built in stages. Amino acids that were prebiotically
  available (found in Miller-Urey experiments, Murchison meteorite, HCN
  chemistry) were coded first. Later amino acids (biosynthetically derived,
  not prebiotically found) were added later, taking over codons from the
  early set.

  UGP prediction: the code's codon-to-amino-acid assignment minimizes the
  total "accessibility mismatch" — accessible amino acids dominate the most
  decode-efficient codon families, and the late-addition amino acids are
  confined to the more structurally constrained codon regions.

NULL TEST:
  Generate random wobble-admissible codes and compare their joint
  (error_score, accessibility_score) to the standard code. The standard
  code should be in the far tail of the joint distribution.

ALSO: Enumerate the top-k Stage 1 survivors by error score and test
whether the standard code is the unique minimum once we add the
accessibility constraint as a second filter.
"""

from __future__ import annotations
import random
import statistics
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Import from Phase 1
from codon_sieve import (
    CODONS, CODON_INDEX, AMINO_ACIDS, AA_INDEX, N_OUTCOMES, BASES,
    STANDARD_CODE, STANDARD_CODE_RAW, WOBBLE_CLASSES, NEIGHBORS,
    POLAR_REQUIREMENT, is_wobble_admissible, error_minimization_score,
    random_code, analyze_code,
)

# ---------------------------------------------------------------------------
# 1. Prebiotic accessibility scoring
# ---------------------------------------------------------------------------

# Amino acid prebiotic accessibility classification.
# Sources:
#   "Early" (prebiotically available): Miller-Urey products, Murchison meteorite,
#    HCN-chemistry products. These are confirmed in abiotic chemistry.
#   "Late" (biosynthetically derived): not found in prebiotic experiments;
#    require enzymatic biosynthesis from simpler precursors.
# Classification follows Knight, Landweber & Yarus (1999) and Trifonov (2000).

PREBIOTIC_ACCESSIBILITY: Dict[str, float] = {
    # Score 1.0 = highly accessible (found in Miller-Urey + meteorites)
    "Gly": 1.0,   # Simplest; abundant in all prebiotic experiments
    "Ala": 1.0,   # Very abundant in Miller-Urey
    "Val": 1.0,   # Found in Murchison meteorite
    "Asp": 1.0,   # Found in Miller-Urey
    "Glu": 1.0,   # Found in Miller-Urey
    "Ser": 0.9,   # Found in Miller-Urey (some experiments)
    "Ile": 0.9,   # Found in Murchison meteorite
    "Leu": 0.9,   # Found in Murchison meteorite
    "Pro": 0.9,   # Found in Miller-Urey
    "Thr": 0.8,   # Found in some prebiotic experiments

    # Score 0.5 = intermediate (partial prebiotic accessibility)
    "Phe": 0.5,   # Aromatic — some prebiotic routes (HCN + formaldehyde)
    "Tyr": 0.5,   # Aromatic — derived from Phe in biosynthesis
    "Asn": 0.4,   # Biosynthetically derived from Asp
    "Gln": 0.4,   # Biosynthetically derived from Glu

    # Score 0.2 = late additions (not prebiotically accessible)
    "Lys": 0.3,   # Not found in standard prebiotic experiments
    "Arg": 0.2,   # Complex biosynthesis; late addition
    "His": 0.2,   # Not found in Miller-Urey; late addition
    "Trp": 0.1,   # Complex aromatic; biosynthetically late; unique codon
    "Met": 0.3,   # Contains sulfur; some prebiotic routes (sulfur chemistry)
    "Cys": 0.3,   # Contains sulfur; some prebiotic routes

    # Stop codons — neutral (not amino acids)
    "Stop1": 0.5,   # UAA
    "Stop2": 0.5,   # UAG
    "Stop3": 0.5,   # UGA
}

def accessibility_score(code: Dict[int, int]) -> float:
    """
    Prebiotic accessibility score for a codon-to-AA mapping.

    A code scores high if it assigns the MOST prebiotically accessible amino
    acids to the LARGEST codon families (most codons per AA). The logic:
    early amino acids should "dominate" the codon space because they were
    available first and could capture the most codon real estate.

    Score = sum over all codons of (accessibility of assigned AA) / 64
    Weighted by how much codon space the AA captures (family size).

    Higher is better (more prebiotically consistent).
    """
    total = sum(PREBIOTIC_ACCESSIBILITY[AMINO_ACIDS[code[ci]]] for ci in range(64))
    return total / 64.0

def joint_viability_score(code: Dict[int, int],
                           w_error: float = 0.5,
                           w_access: float = 0.5) -> float:
    """
    Combined Stage 2 viability score.
    Lower error + higher accessibility = better code.
    Normalized: combine as (1 - norm_error) + norm_access, but since
    we're comparing within a distribution, use weighted combination.

    Returns a HIGHER value for BETTER codes (unlike error score alone).
    """
    err = error_minimization_score(code)
    acc = accessibility_score(code)
    # Invert error so higher = better, then combine
    # Range of error is roughly [1.5, 3.5]; accessibility in [0.3, 1.0]
    return -w_error * err + w_access * acc

# ---------------------------------------------------------------------------
# 2. Codon-family accessibility analysis
# ---------------------------------------------------------------------------

def codon_family_accessibility(code: Dict[int, int]) -> Dict[Tuple[str, str], float]:
    """
    For each family box (NN**), compute the accessibility score of the
    amino acid assigned to the majority of codons in that family.
    """
    family_access: Dict[Tuple[str, str], float] = {}
    for b1 in BASES:
        for b2 in BASES:
            family_codons = [CODON_INDEX[(b1, b2, b3)] for b3 in BASES]
            # Most common outcome in family
            outcome_counts: Dict[int, int] = defaultdict(int)
            for ci in family_codons:
                outcome_counts[code[ci]] += 1
            dominant_outcome = max(outcome_counts, key=lambda k: outcome_counts[k])
            aa_name = AMINO_ACIDS[dominant_outcome]
            family_access[(b1, b2)] = PREBIOTIC_ACCESSIBILITY[aa_name]
    return family_access

def analyze_codon_family_pattern(code: Dict[int, int], label: str) -> None:
    """Print the accessibility pattern across family boxes."""
    family_acc = codon_family_accessibility(code)
    # Rank families by accessibility
    sorted_fam = sorted(family_acc.items(), key=lambda x: -x[1])
    print(f"  {label} — codon family accessibility ranking:")
    for (b1, b2), acc in sorted_fam[:8]:
        family_codons = [CODON_INDEX[(b1, b2, b3)] for b3 in BASES]
        aa_set = {AMINO_ACIDS[code[ci]] for ci in family_codons}
        print(f"    {b1}{b2}**: {list(aa_set)} → accessibility={acc:.2f}")

# ---------------------------------------------------------------------------
# 3. Null test: joint distribution of (error, accessibility)
# ---------------------------------------------------------------------------

def joint_null_test(n_random: int = 200_000, rng_seed: int = 42) -> Dict:
    rng = random.Random(rng_seed)
    print(f"  Sampling {n_random:,} random wobble-admissible codes...")

    err_scores = []
    acc_scores = []
    joint_scores = []

    for _ in range(n_random):
        rc = random_code(rng)
        err = error_minimization_score(rc)
        acc = accessibility_score(rc)
        err_scores.append(err)
        acc_scores.append(acc)
        joint_scores.append(-err + acc)  # combined, higher is better

    std_err  = error_minimization_score(STANDARD_CODE)
    std_acc  = accessibility_score(STANDARD_CODE)
    std_joint = -std_err + std_acc

    # Count how many random codes beat the standard on each metric
    n_better_err    = sum(1 for e in err_scores   if e < std_err)
    n_better_acc    = sum(1 for a in acc_scores   if a > std_acc)
    n_better_joint  = sum(1 for j in joint_scores if j > std_joint)
    n_better_both   = sum(
        1 for e, a in zip(err_scores, acc_scores)
        if e < std_err and a > std_acc
    )

    return {
        "n_random": n_random,
        "std_err": std_err, "std_acc": std_acc, "std_joint": std_joint,
        "err_mean": statistics.mean(err_scores),
        "err_stdev": statistics.stdev(err_scores),
        "acc_mean": statistics.mean(acc_scores),
        "acc_stdev": statistics.stdev(acc_scores),
        "joint_mean": statistics.mean(joint_scores),
        "joint_stdev": statistics.stdev(joint_scores),
        "n_better_err": n_better_err,
        "n_better_acc": n_better_acc,
        "n_better_both": n_better_both,
        "n_better_joint": n_better_joint,
    }

# ---------------------------------------------------------------------------
# 4. Top-k search: find the best wobble-admissible codes by joint score
# ---------------------------------------------------------------------------

def find_top_k_codes(k: int = 20, n_sample: int = 500_000,
                     rng_seed: int = 123) -> List[Tuple[float, Dict[int, int]]]:
    """
    Sample n_sample random wobble-admissible codes and return the top k
    by joint viability score. Used to test whether the standard code
    is near-unique at the intersection of error and accessibility.
    """
    rng = random.Random(rng_seed)
    top_k: List[Tuple[float, Dict[int, int]]] = []
    std_joint = joint_viability_score(STANDARD_CODE)

    for _ in range(n_sample):
        rc = random_code(rng)
        j = joint_viability_score(rc)
        top_k.append((j, rc))
        top_k.sort(reverse=True, key=lambda x: x[0])
        top_k = top_k[:k + 1]  # keep k+1 so we can check if standard is in top k

    return top_k[:k]

# ---------------------------------------------------------------------------
# 5. Variant code comparison
# ---------------------------------------------------------------------------

VARIANT_CODES: Dict[str, Dict[str, str]] = {
    "Mammalian mitochondrial": {
        "UGA": "Trp",    # standard: Stop3
        "AUA": "Met",    # standard: Ile
        "AGA": "Stop1",  # standard: Arg
        "AGG": "Stop2",  # standard: Arg
    },
    "Yeast mitochondrial": {
        "UGA": "Trp",    # standard: Stop3
        "CUA": "Thr",    # standard: Leu
        "AUA": "Met",    # standard: Ile
    },
    "Mycoplasma / Spiroplasma": {
        "UGA": "Trp",    # standard: Stop3
    },
    "Ciliate nuclear": {
        "UAA": "Gln",    # standard: Stop1
        "UAG": "Gln",    # standard: Stop2
    },
}

def build_variant(modifications: Dict[str, str]) -> Dict[int, int]:
    from codon_sieve import _build_code_map
    raw = dict(STANDARD_CODE_RAW)
    raw.update(modifications)
    return _build_code_map(raw)

def compare_variant_codes() -> None:
    std_err  = error_minimization_score(STANDARD_CODE)
    std_acc  = accessibility_score(STANDARD_CODE)
    std_joint = joint_viability_score(STANDARD_CODE)
    print(f"  Standard code:  err={std_err:.4f}, acc={std_acc:.4f}, joint={std_joint:.4f}")
    print()

    for name, mods in VARIANT_CODES.items():
        from codon_sieve import _build_code_map
        raw = dict(STANDARD_CODE_RAW)
        raw.update(mods)
        code = _build_code_map(raw)

        admissible = is_wobble_admissible(code)
        err  = error_minimization_score(code)
        acc  = accessibility_score(code)
        joint = joint_viability_score(code)
        d_err   = err - std_err
        d_acc   = acc - std_acc
        d_joint = joint - std_joint

        status = "LOCAL MIN ✓" if d_joint < 0 else "BETTER? ✗" if d_joint > 0 else "TIED"
        print(f"  {name}:")
        print(f"    admissible={admissible}, err={err:.4f}({d_err:+.4f}), "
              f"acc={acc:.4f}({d_acc:+.4f}), joint={joint:.4f}({d_joint:+.4f})  [{status}]")

# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("DIRECTION 1 — GENETIC CODE PHASE 2: PREBIOTIC CHEMISTRY VIABILITY")
    print("=" * 70)
    print()

    # Standard code scores
    std_err  = error_minimization_score(STANDARD_CODE)
    std_acc  = accessibility_score(STANDARD_CODE)
    std_joint = joint_viability_score(STANDARD_CODE)

    print("[1] Standard code scores")
    print(f"    Error minimization:    {std_err:.4f}  (lower=better)")
    print(f"    Prebiotic accessibility: {std_acc:.4f}  (higher=better)")
    print(f"    Joint viability score: {std_joint:.4f}  (higher=better)")
    print()

    # Codon family pattern
    analyze_codon_family_pattern(STANDARD_CODE, "Standard code")
    print()

    # Joint null test
    print("[2] Joint null test (error × accessibility) — {n_random:,} random codes")
    stats = joint_null_test(n_random=200_000, rng_seed=42)

    print(f"    Standard code error:        {stats['std_err']:.4f}")
    print(f"    Random mean ± stdev:        {stats['err_mean']:.4f} ± {stats['err_stdev']:.4f}")
    z_err = (stats['std_err'] - stats['err_mean']) / stats['err_stdev']
    print(f"    Error z-score:              {z_err:.2f}σ")
    print()
    print(f"    Standard code accessibility: {stats['std_acc']:.4f}")
    print(f"    Random mean ± stdev:         {stats['acc_mean']:.4f} ± {stats['acc_stdev']:.4f}")
    z_acc = (stats['std_acc'] - stats['acc_mean']) / stats['acc_stdev']
    print(f"    Accessibility z-score:       {z_acc:.2f}σ  (positive=better)")
    print()
    print(f"    Joint score — standard:      {stats['std_joint']:.4f}")
    print(f"    Joint score — random mean:   {stats['joint_mean']:.4f} ± {stats['joint_stdev']:.4f}")
    z_joint = (stats['std_joint'] - stats['joint_mean']) / stats['joint_stdev']
    print(f"    Joint score z-score:         {z_joint:.2f}σ  (positive=better)")
    print()
    n = stats["n_random"]
    print(f"    Random codes beating standard on BOTH criteria:  "
          f"{stats['n_better_both']:,}/{n:,}  ({100*stats['n_better_both']/n:.3f}%)")
    print(f"    Random codes beating standard on joint score:    "
          f"{stats['n_better_joint']:,}/{n:,}  ({100*stats['n_better_joint']/n:.3f}%)")
    print()

    # Variant code comparison
    print("[3] Variant code comparison — are they local minima?")
    print("    UGP prediction: all variants should have LOWER joint viability score")
    print("    (worse than standard on at least one metric, confirming local-min status)")
    print()
    compare_variant_codes()
    print()

    # Top-k search
    print("[4] Top-k search among 500k random codes")
    print("    Looking for codes that beat or match the standard on both metrics")
    top_k = find_top_k_codes(k=20, n_sample=500_000, rng_seed=999)
    std_joint = joint_viability_score(STANDARD_CODE)

    print(f"    Standard code joint score:  {std_joint:.4f}")
    print(f"    Top-20 best random codes:")
    for rank, (j, rc) in enumerate(top_k, 1):
        err = error_minimization_score(rc)
        acc = accessibility_score(rc)
        is_std = (rc == STANDARD_CODE)
        marker = " ← STANDARD" if is_std else ""
        print(f"      #{rank:2d}: joint={j:.4f} (err={err:.4f}, acc={acc:.4f}){marker}")

    # Check if standard code is in the top 20
    std_in_top20 = any(rc == STANDARD_CODE for _, rc in top_k)
    print()
    if std_in_top20:
        print("    Standard code IS in top 20 — near-unique at the intersection. ✓")
    else:
        print("    Standard code NOT in sampled top 20.")
        n_better_joint_than_std = sum(1 for j, _ in top_k if j > std_joint)
        print(f"    {n_better_joint_than_std} sampled codes have better joint score.")
        print("    Need to examine whether they use chemically distinct AA assignments.")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"  Error z-score:       {z_err:.2f}σ")
    print(f"  Accessibility z-score: {z_acc:.2f}σ")
    print(f"  Joint z-score:       {z_joint:.2f}σ")
    print()
    print("  UGP prediction check:")
    print(f"  - Standard code is better than random on BOTH metrics:")
    better_both = (z_err < 0 and z_acc > 0)
    print(f"    {'✓' if better_both else '✗'} (z_err={z_err:.2f}<0 AND z_acc={z_acc:.2f}>0)")
    print()
    print("  NEXT STEPS:")
    print("  - Phase 3: Add syntactic chemistry layer (amino acid size/charge clustering)")
    print("  - Phase 4: Full MDL over reaction networks (computationally intensive)")
    print("  - Phase 5: Enumerate ALL Stage 1 ∩ Stage 2 survivors (requires exact Stage 2)")


if __name__ == "__main__":
    main()
