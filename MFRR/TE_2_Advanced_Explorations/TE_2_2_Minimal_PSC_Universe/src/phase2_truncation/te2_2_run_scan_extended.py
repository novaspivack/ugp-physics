"""
te2_2_run_scan_extended.py — Extended PSC Universe Scan (NW1 + NW4)

Extends the canonical TE2.2 scan (te2_2_run_scan.py) in two ways:

1. NW1: Adds 5 new gauge groups to cover all major BSM candidates:
   - SU(4)xSU(2)xSU(2)  (Pati-Salam)
   - E6                  (exceptional GUT)
   - G2                  (exceptional group)
   - SU(6)               (higher-rank extension)
   - SU(4)               (Pati-Salam color factor)

2. NW4: Adds 3 new UGP-derived coupling ratio constraints:
   - C15: g1^2/g2^2 UGP prediction (1.34% deviation from SM@Mz)
   - C16: g3^2/g2^2 UGP prediction (1.90% deviation from SM@Mz)
   - C4': Quarter-Lock exact g1^2/g2^2 = 1/3 (9.77% deviation from SM@Mz)

3. NW2: C9 and C11 are removed (SM-tautological is_sm_like() proxies).
   C5 is retained but annotated; a principled SRRG replacement is noted.

Output: results/extended_scan_results.json
"""

import sys
import os
import json
import hashlib
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase1_constraints'))

from te2_2_constraint_base import UniverseParams
from te2_2_srrg_constraint import SRRGFixedPointConstraint, SRRGViabilityConstraint, RGFlowStabilityConstraint
from te2_2_dimensional_constraint import DimensionalConstraint
from te2_2_remaining_constraints import (
    KahlerStructureConstraint, AreaLawConstraint, UnitaryEvolutionConstraint,
    EinsteinEquationConstraint, InformationProfitConstraint,
    NecessaryObserversConstraint, LambdaRelationConstraint,
)
from te2_2_ugp_coupling_constraints import (
    C15_G1G2RatioConstraint, C16_G3G2RatioConstraint, C4prime_QuarterLockExact,
)

# ---------------------------------------------------------------------------
# Extended universe parameter space
# ---------------------------------------------------------------------------
EXTENDED_DIMENSIONS = [2, 3, 4, 5, 6]

EXTENDED_GAUGE_GROUPS = [
    # Original 7
    "U(1)",
    "SU(2)",
    "SU(3)",
    "SU(2)xU(1)",
    "SU(3)xSU(2)xU(1)",   # Standard Model ✓
    "SU(5)",
    "SO(10)",
    # New 5 (NW1)
    "SU(4)xSU(2)xSU(2)",  # Pati-Salam
    "E6",
    "G2",
    "SU(6)",
    "SU(4)",
]

SM_GROUP = "SU(3)xSU(2)xU(1)"
BSM_NEW_GROUPS = {"SU(4)xSU(2)xSU(2)", "E6", "G2", "SU(6)", "SU(4)"}

N_GENERATIONS  = [1, 2, 3, 4]
N_OBSERVERS    = [0, 1]
LAMBDAS        = [0.0, 1e-122, 1e-60]
PROFIT_RATIOS  = [0.5, 1.0, 1.13, 1.5]
KAPPAS         = [0.0, 0.01, -0.01]
TOPOLOGIES     = ["flat", "hyperbolic"]


def is_sm_like_extended(universe: UniverseParams, tol: float = 1e-3) -> bool:
    """Extended is_sm_like that also handles new BSM groups (all non-SM)."""
    return universe.gauge_group == SM_GROUP and universe.d == 4


def get_constraints_extended():
    """
    Extended constraint set: original 14 minus C9/C11, plus C15/C16/C4'.

    Removed (NW2): C9 (RIETEquivalenceConstraint), C11 (CoherenceFieldConstraint)
    — both use is_sm_like() as SM-tautological proxies.

    Added (NW4): C15, C16, C4'  — UGP-derived coupling ratio predictions.

    Result: 15 constraints (14 - 2 + 3).
    """
    return [
        DimensionalConstraint(),            # C1
        SRRGFixedPointConstraint(),         # C2 — SM-targeted (disclosed)
        SRRGViabilityConstraint(),          # C3 — SM-targeted (disclosed)
        # C4 QuarterLock is embedded in the SRRG constraint file;
        # C4' below is the new exact version
        RGFlowStabilityConstraint(),        # C5 — SM-targeted via is_sm_like (disclosed)
        KahlerStructureConstraint(),        # C6
        AreaLawConstraint(),               # C7
        UnitaryEvolutionConstraint(),       # C8
        # C9 REMOVED (SM-tautological proxy)
        EinsteinEquationConstraint(),       # C10
        # C11 REMOVED (SM-tautological proxy)
        InformationProfitConstraint(),      # C12
        NecessaryObserversConstraint(),     # C13
        LambdaRelationConstraint(),         # C14 — PSC-conditional (disclosed)
        C15_G1G2RatioConstraint(),          # C15 — NEW: UGP g1^2/g2^2 prediction
        C16_G3G2RatioConstraint(),          # C16 — NEW: UGP g3^2/g2^2 prediction
        C4prime_QuarterLockExact(),         # C4' — NEW: exact Quarter-Lock 1/3
    ]


def get_hard_constraints():
    """Hard PSC constraints — pass/fail gates."""
    return [
        DimensionalConstraint(),
        KahlerStructureConstraint(),
        UnitaryEvolutionConstraint(),
        InformationProfitConstraint(),
        NecessaryObserversConstraint(),
    ]


def compute_dissonance(universe: UniverseParams, constraints) -> dict:
    """Compute full dissonance D[Psi] and per-constraint breakdown."""
    total = 0.0
    breakdown = {}
    for c in constraints:
        val = c.evaluate(universe)
        weighted = c.weight * val
        breakdown[c.name] = {"raw": float(val), "weighted": float(weighted)}
        total += weighted
    return {"total": float(total), "breakdown": breakdown}


def passes_hard_constraints(universe: UniverseParams, hard_constraints) -> bool:
    """Return True if universe passes all hard constraints."""
    for c in hard_constraints:
        if not c.is_satisfied(universe):
            return False
    return True


def enumerate_universes():
    """Generate all universe parameter combinations."""
    universes = []
    for d in EXTENDED_DIMENSIONS:
        for g in EXTENDED_GAUGE_GROUPS:
            for n_gen in N_GENERATIONS:
                for n_obs in N_OBSERVERS:
                    for lam in LAMBDAS:
                        for rho in PROFIT_RATIOS:
                            for kap in KAPPAS:
                                for tau in TOPOLOGIES:
                                    universes.append(UniverseParams(
                                        d=d, gauge_group=g,
                                        n_generations=n_gen, n_observers=n_obs,
                                        Lambda=lam, profit_ratio=rho,
                                        kappa=kap, topology=tau,
                                    ))
    return universes


def run_extended_scan():
    """Run the extended scan over all universe descriptions."""
    t0 = time.time()
    constraints = get_constraints_extended()
    hard_constraints = get_hard_constraints()
    universes = enumerate_universes()

    print(f"Extended PSC Universe Scan")
    print(f"  Gauge groups: {len(EXTENDED_GAUGE_GROUPS)} "
          f"(original 7 + {len(BSM_NEW_GROUPS)} new BSM)")
    print(f"  Total universes: {len(universes):,}")
    print(f"  Constraints: {len(constraints)} "
          f"(15 = original 14 - C9 - C11 + C15 + C16 + C4')")
    print()

    # Identify SM universe
    sm_univ = UniverseParams(d=4, gauge_group=SM_GROUP, n_generations=3,
                              n_observers=1, Lambda=1e-122, profit_ratio=1.13,
                              kappa=0.0, topology="flat")
    sm_D = compute_dissonance(sm_univ, constraints)["total"]
    sm_passes_hard = passes_hard_constraints(sm_univ, hard_constraints)

    results = []
    psc_passing = []
    new_group_results = []

    for univ in universes:
        D = compute_dissonance(univ, constraints)
        passes = passes_hard_constraints(univ, hard_constraints)
        entry = {
            "d": univ.d,
            "gauge_group": univ.gauge_group,
            "n_generations": univ.n_generations,
            "n_observers": univ.n_observers,
            "Lambda": univ.Lambda,
            "profit_ratio": univ.profit_ratio,
            "kappa": univ.kappa,
            "topology": univ.topology,
            "D": D["total"],
            "is_psc": passes,
            "is_sm": univ.gauge_group == SM_GROUP and univ.d == 4,
            "is_new_bsm": univ.gauge_group in BSM_NEW_GROUPS,
        }
        results.append(entry)
        if passes:
            psc_passing.append(entry)
        if univ.gauge_group in BSM_NEW_GROUPS:
            new_group_results.append(entry)

    elapsed = time.time() - t0

    # Sort by D
    results.sort(key=lambda x: x["D"])

    # Find global minimizer
    global_min = results[0]
    D_min = global_min["D"]

    # Find SM rank
    sm_rank = next((i+1 for i, r in enumerate(results)
                    if r["gauge_group"] == SM_GROUP and r["d"] == 4
                    and r["n_generations"] == 3 and r["is_psc"]), None)

    # BSM summary: min D per new group
    bsm_summary = {}
    for g in BSM_NEW_GROUPS:
        group_res = [r for r in results if r["gauge_group"] == g]
        if group_res:
            min_D = min(r["D"] for r in group_res)
            any_psc = any(r["is_psc"] for r in group_res)
            bsm_summary[g] = {"min_D": float(min_D), "any_psc": bool(any_psc)}

    # SM per-constraint breakdown
    sm_breakdown = compute_dissonance(sm_univ, constraints)

    print(f"RESULTS ({elapsed:.2f}s):")
    print(f"  Total universes: {len(universes):,}")
    print(f"  PSC-passing:     {len(psc_passing):,} "
          f"({100*len(psc_passing)/len(universes):.2f}%)")
    print(f"  D_SM  = {sm_D:.6f}")
    print(f"  D_min = {D_min:.6f}")
    print(f"  SM passes hard PSC: {sm_passes_hard}")
    print()
    print("BSM New Groups — all fail PSC? (expected yes):")
    for g, s in bsm_summary.items():
        print(f"  {g:30s}: min_D={s['min_D']:.4f}, any_psc={s['any_psc']}")
    print()
    print("SM Constraint Breakdown (extended):")
    for name, vals in sm_breakdown["breakdown"].items():
        if vals["weighted"] > 0:
            print(f"  {name:25s}: raw={vals['raw']:.6f}, weighted={vals['weighted']:.4f}")
    print()
    print("Top 5 universes by D:")
    for i, r in enumerate(results[:5]):
        print(f"  #{i+1}: d={r['d']}, G={r['gauge_group']}, "
              f"n_gen={r['n_generations']}, D={r['D']:.6f}, psc={r['is_psc']}")

    output = {
        "description": "Extended PSC universe scan (NW1+NW4: 12 gauge groups, 15 constraints)",
        "gauge_groups": EXTENDED_GAUGE_GROUPS,
        "n_gauge_groups": len(EXTENDED_GAUGE_GROUPS),
        "new_bsm_groups": list(BSM_NEW_GROUPS),
        "n_constraints": len(constraints),
        "constraints_removed": ["C9_RIETEquivalence", "C11_CoherenceField"],
        "constraints_added": ["C15_G1G2Ratio", "C16_G3G2Ratio", "C4prime_QuarterLockExact"],
        "total_universes": len(universes),
        "psc_universes": len(psc_passing),
        "psc_fraction": float(len(psc_passing) / len(universes)),
        "D_sm": float(sm_D),
        "D_min": float(D_min),
        "sm_rank": sm_rank,
        "sm_passes_hard": bool(sm_passes_hard),
        "global_minimizer": global_min,
        "top_10": results[:10],
        "psc_passing_universes": psc_passing,
        "bsm_new_group_summary": bsm_summary,
        "sm_constraint_breakdown": sm_breakdown,
        "elapsed_seconds": float(elapsed),
        "throughput": float(len(universes) / elapsed),
    }
    return output


if __name__ == "__main__":
    results = run_extended_scan()

    out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'results')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'extended_scan_results.json')

    sha = hashlib.sha256(
        json.dumps(results, sort_keys=True, default=float).encode()
    ).hexdigest()
    results["sha256"] = sha

    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=float)

    print(f"\nSaved: {out_path}")
    print(f"SHA-256: {sha}")
