#!/usr/bin/env python3
"""
te22_rcc_certificate.py - COMP-P01-G

Formalizes the TE2.2 extended-scan computational certification of the
Residual Classification Conjecture (RCC) within a discretized space
of 34,560 candidate universes.

Loads the canonical extended TE2.2 scan and reports, with explicit
SHAs, the empirical RCC certification: every PSC-passing universe in
the scan carries the Standard-Model signature
(SU(3) x SU(2) x U(1), N_gen = 3, d = 4), and the SM is the global
minimizer of the dissonance functional D.  The continuum extension
of this finite computational certificate is the remaining open RCC
question.

Output: papers/01_SM/canonical_run/te22_rcc_certificate.json
"""
import hashlib
import json
import os
from datetime import datetime, timezone


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCAN_PATH = os.path.join(
    REPO,
    "MFRR",
    "TE_2_Advanced_Explorations",
    "TE_2_2_Minimal_PSC_Universe",
    "results",
    "extended_scan_results.json",
)


def main():
    with open(SCAN_PATH, "r") as f:
        scan = json.load(f)

    with open(SCAN_PATH, "rb") as f:
        scan_sha = hashlib.sha256(f.read()).hexdigest()

    print("=" * 78)
    print("COMP-P01-G: TE2.2 RCC computational certification")
    print("=" * 78)
    print(f"Source: {os.path.relpath(SCAN_PATH, REPO)}")
    print(f"Source SHA-256: {scan_sha}")

    total = scan["total_universes"]
    psc_count = scan["psc_universes"]
    psc_universes = scan["psc_passing_universes"]
    D_sm = scan["D_sm"]
    D_min = scan["D_min"]
    sm_rank = scan["sm_rank"]
    minimizer = scan["global_minimizer"]
    n_groups = scan["n_gauge_groups"]
    n_constraints = scan["n_constraints"]

    sm_signature = (
        minimizer["d"] == 4
        and minimizer["gauge_group"] == "SU(3)xSU(2)xU(1)"
        and minimizer["n_generations"] == 3
    )
    all_psc_are_sm = all(
        (u["d"] == 4 and u["gauge_group"] == "SU(3)xSU(2)xU(1)" and u["n_generations"] == 3)
        for u in psc_universes
    )

    print(f"\nDiscretization parameters:")
    print(f"  Gauge groups scanned             : {n_groups}")
    print(f"  Constraints applied              : {n_constraints}")
    print(f"  Total candidate universes        : {total:,}")
    print(f"\nPSC-Layer-I sieve outcome:")
    print(f"  PSC-passing universes            : {psc_count}")
    print(f"  PSC fraction                     : {psc_count/total:.6e}")
    print(f"  All PSC survivors are SM         : {all_psc_are_sm}")
    print(f"\nLayer-II (D-minimization) outcome:")
    print(f"  Global minimizer SM signature    : {sm_signature}")
    print(f"  D_min                            : {D_min:.6f}")
    print(f"  D_SM                             : {D_sm:.6f}")
    print(f"  SM rank in scan                  : #{sm_rank}")
    print(f"\nGlobal minimizer (full):")
    for k, v in minimizer.items():
        print(f"  {k:18s} = {v}")
    print()

    if all_psc_are_sm and sm_signature and sm_rank == 1:
        verdict_short = "RCC certified within discretized scan"
        verdict_long = (
            "Within the discretized 34,560-universe TE2.2 scan, every "
            "PSC-Layer-I-passing universe (12 of 34,560) carries the "
            "Standard-Model signature, and the SM is the global "
            "minimizer of the dissonance functional D under Layer II.  "
            "This is a finite computational certification of the "
            "Residual Classification Conjecture (RCC) restricted to "
            "the scan's discretization.  The remaining open question "
            "is the analytical extension of this certificate to the "
            "continuous theory space."
        )
    else:
        verdict_short = "RCC NOT certified by this scan"
        verdict_long = (
            "The TE2.2 extended scan does not unambiguously certify "
            "RCC: at least one PSC-passing universe is not SM-signature, "
            "or SM is not the global D-minimizer.  Investigate."
        )

    out = {
        "description": (
            "COMP-P01-G: TE2.2 RCC computational certificate.  Audits the "
            "extended PSC-universe scan results to formally certify "
            "Residual Classification Conjecture (RCC) within the "
            "discretized scan space.  Source: MFRR TE_2_2 extended scan."
        ),
        "source_scan": os.path.relpath(SCAN_PATH, REPO),
        "source_scan_sha256": scan_sha,
        "discretization": {
            "n_gauge_groups": n_groups,
            "n_constraints": n_constraints,
            "total_universes": total,
            "gauge_groups_scanned": scan["gauge_groups"],
        },
        "layer_I_outcome": {
            "psc_passing_count": psc_count,
            "psc_fraction": psc_count / total,
            "all_psc_passing_are_SM_signature": all_psc_are_sm,
        },
        "layer_II_outcome": {
            "global_minimizer_is_SM_signature": sm_signature,
            "D_min": D_min,
            "D_SM": D_sm,
            "sm_rank_in_scan": sm_rank,
            "global_minimizer_full": minimizer,
        },
        "verdict_short": verdict_short,
        "verdict_long": verdict_long,
        "open_problems_remaining": (
            "(a) Analytical extension of the RCC certificate from the "
            "discretized 34,560-universe scan to the continuous theory "
            "space.  (b) Tighter discretization to bound the residual "
            "space density.  Both are research-grade theoretical work."
        ),
        "claim_type_for_paper_1": (
            "[C] computationally certified within discretized scan "
            "(finite computational certificate); the analytical "
            "extension to continuum theory space remains [I] "
            "(interpretive open problem, pending RCC continuum proof)."
        ),
        "implementation_lean_hooks": {
            "nems_lean_module": "NemS.Physics.Rigidity",
            "key_theorem": "gauge_signature_rigidity",
            "rcc_predicate": "ResidualClassificationConjecture",
            "discretized_certification": (
                "TE2.2 scan acts as the computational witness for the "
                "RCC predicate within its discretization; the Lean theorem "
                "remains conditional on RCC, but the conditional is now "
                "computationally certified at the discretized level."
            ),
            "zenodo_doi_nems_05": "10.5281/zenodo.19429721",
        },
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    out_path = os.path.join(HERE, "te22_rcc_certificate.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    print("=" * 78)
    print(f"VERDICT: {verdict_short}")
    print("=" * 78)
    print(f"\nOutput: {out_path}")
    print(f"SHA-256: {sha}")
    return 0 if all_psc_are_sm and sm_signature else 1


if __name__ == "__main__":
    raise SystemExit(main())
