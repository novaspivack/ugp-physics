"""
TS1_EXTENDED_GLOBAL: Grand-Tour SRRG Search in GTE Triple Space

Spec reference:
  SRRG_VALIDATION_PROGRAM/SESSIONS/8_1_TS1_EXTENDED_TESTS_PLAN.md

Purpose:
  - Address the "local basin" critique by exploring a much larger region of
    integer GTE triple space, far beyond radius r = 5 around the canonical SM
    triples.
  - Run SRRG flow from many random initial triples and compare their final
    viability F to the SM canonical triples under the pure-GTE functional.
  - Estimate a "viability gap" between SM and the best non-SM attractors
    encountered in the sampled region.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import json
import math

import numpy as np
from tqdm import tqdm

from srrg_core import (
    GTETriple,
    SRRGParameters,
    is_admissible,
    srrg_flow_to_convergence,
)
from srrg_io import (
    load_canonical_sm_triples,
    save_results_with_manifest,
)
from srrg_functional_pure_gte import elegant_palette, viability_functional_pure_gte


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_PARAMS = SRRGParameters()

GLOBAL_CONFIG = {
    # Number of random initial triples to sample in the "grand tour"
    "n_random_starts": 1000,
    # Sampling ranges for (a, b, c); g is chosen from {0,1,2,3}
    "a_min": 1,
    "a_max": 10_000,
    "b_min": 1,
    "b_max": 100_000,
    "c_min": -1,
    "c_max": 100_000,
    # SRRG flow configuration
    "max_iter": 2000,
    "convergence_tol": 1e-3,
    # Random seed for reproducibility
    "seed": 12345,
}


def make_F_fn(ucl_palette, params: SRRGParameters):
    """
    Build a viability functional F(triple) using the pure-GTE structure.
    This mirrors the TS1_FINAL configuration but is factored out so we can
    use the same F in both canonical and random-triple evaluations.
    """

    def F(triple: GTETriple) -> float:
        # Single-particle theory for consistency with TS1
        return viability_functional_pure_gte([triple], ucl_palette, params)

    return F


def sample_random_triple(rng: np.random.Generator, cfg: Dict) -> GTETriple:
    """
    Sample a random admissible GTETriple from the configured global ranges.
    """
    while True:
        a = int(rng.integers(cfg["a_min"], cfg["a_max"] + 1))
        b = int(rng.integers(cfg["b_min"], cfg["b_max"] + 1))
        # c can be -1 (sentinel) or positive
        c_raw = int(rng.integers(cfg["c_min"], cfg["c_max"] + 1))
        c = -1 if c_raw < 1 else c_raw
        g = int(rng.integers(0, 4))  # generations 0,1,2,3

        triple = GTETriple(a, b, c, g, name="random")
        if is_admissible(triple):
            return triple


def is_sm_like(triple: GTETriple, canonical: List[GTETriple], tol: float = 1e-6) -> bool:
    """
    Check whether a triple is effectively equal to any canonical SM triple.
    """
    for t in canonical:
        if (
            triple.a == t.a
            and triple.b == t.b
            and triple.c == t.c
            and triple.g == t.g
        ):
            return True
    return False


def run_ts1_extended_global() -> Dict:
    """
    Execute the TS1_EXTENDED_GLOBAL "grand tour" experiment.

    Steps:
      - Load canonical SM triples and compute their pure-GTE F values.
      - Sample many random admissible triples from a large box in Z^4.
      - For each, run SRRG flow to convergence and record final triple and F.
      - Compare final F values to the canonical SM F values and compute
        a viability gap.
    """
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts1_extended" / "global"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load canonical SM triples
    triples_path = data_dir / "canonical_sm_triples.json"
    particle_dicts = load_canonical_sm_triples(triples_path)
    canonical_triples = [
        GTETriple(
            a=p["triple"]["a"],
            b=p["triple"]["b"],
            c=p["triple"]["c"],
            g=p["triple"]["g"],
            name=p["name"],
        )
        for p in particle_dicts
    ]
    print(f"Loaded {len(canonical_triples)} canonical SM triples")

    # Build pure-GTE functional
    ucl_palette = elegant_palette()
    F_fn = make_F_fn(ucl_palette, DEFAULT_PARAMS)

    # Compute canonical F values for reference
    canonical_F = {t.name: F_fn(t) for t in canonical_triples}
    F_sm_values = list(canonical_F.values())
    F_sm_mean = float(np.mean(F_sm_values))
    F_sm_max = float(np.max(F_sm_values))

    print(f"Canonical SM mean F: {F_sm_mean:.6g}, max F: {F_sm_max:.6g}")

    # Random search configuration
    cfg = GLOBAL_CONFIG
    rng = np.random.default_rng(cfg["seed"])

    n_random = cfg["n_random_starts"]
    random_results: List[Dict] = []

    n_to_sm = 0
    best_alt_F = -math.inf
    best_alt_triples: List[Dict] = []

    print(f"Running TS1_EXTENDED_GLOBAL with {n_random} random starts...")

    for _ in tqdm(range(n_random), desc="Global SRRG flows"):
        # Sample random triple
        triple0 = sample_random_triple(rng, cfg)

        # Run SRRG flow to convergence
        result = srrg_flow_to_convergence(
            triple_init=triple0,
            F_fn=F_fn,
            params=DEFAULT_PARAMS,
            ucl_fn=None,
            max_iter=cfg["max_iter"],
            tol=cfg["convergence_tol"],
        )

        final_triple: GTETriple = result["final_triple"]
        final_F = float(result["final_F"])
        converged = bool(result["converged"])

        sm_like = is_sm_like(final_triple, canonical_triples)
        if sm_like:
            n_to_sm += 1

        if not sm_like and final_F > best_alt_F:
            best_alt_F = final_F
            best_alt_triples = [
                {
                    "final_triple": final_triple.to_dict(),
                    "initial_triple": triple0.to_dict(),
                    "final_F": final_F,
                    "iterations": result["iterations"],
                    "kkt_residual": result["kkt_residual"],
                    "converged": converged,
                }
            ]
        elif not sm_like and math.isclose(final_F, best_alt_F, rel_tol=1e-9, abs_tol=1e-12):
            # Track ties at the top
            best_alt_triples.append(
                {
                    "final_triple": final_triple.to_dict(),
                    "initial_triple": triple0.to_dict(),
                    "final_F": final_F,
                    "iterations": result["iterations"],
                    "kkt_residual": result["kkt_residual"],
                    "converged": converged,
                }
            )

        random_results.append(
            {
                "initial_triple": triple0.to_dict(),
                "final_triple": final_triple.to_dict(),
                "final_F": final_F,
                "converged": converged,
                "iterations": result["iterations"],
                "kkt_residual": result["kkt_residual"],
                "sm_like": sm_like,
            }
        )

    # Summaries
    F_random = [r["final_F"] for r in random_results]
    F_random_max = float(np.max(F_random)) if F_random else float("-inf")
    F_random_mean = float(np.mean(F_random)) if F_random else float("nan")

    viability_gap_vs_max_alt = F_sm_max - best_alt_F if best_alt_F > -math.inf else None

    summary: Dict = {
        "test_name": "TS1_EXTENDED_GLOBAL: Grand-Tour SRRG Search (Pure GTE)",
        "config": cfg,
        "canonical_F": canonical_F,
        "canonical_F_mean": F_sm_mean,
        "canonical_F_max": F_sm_max,
        "n_random_starts": n_random,
        "n_flows_to_sm": n_to_sm,
        "fraction_flows_to_sm": n_to_sm / n_random if n_random > 0 else 0.0,
        "F_random_max": F_random_max,
        "F_random_mean": F_random_mean,
        "best_alt_F": best_alt_F if best_alt_F > -math.inf else None,
        "viability_gap_vs_best_alt": viability_gap_vs_max_alt,
        "best_alt_triples": best_alt_triples,
        # We do not embed all random_results here to keep the JSON manageable;
        # they can be saved separately if needed.
    }

    # Save summary
    results_path = output_dir / "ts1_extended_global_summary.json"
    manifest_path = program_dir / "DATA_MANIFEST.json"

    save_results_with_manifest(
        data=summary,
        path=results_path,
        manifest_path=manifest_path,
        description=(
            "TS1_EXTENDED_GLOBAL: Grand-tour SRRG search over random GTE triples "
            "using the pure GTE functional; records flows to SM and best "
            "non-SM attractors and computes a viability gap."
        ),
    )

    print(f"\n✅ TS1_EXTENDED_GLOBAL summary saved: {results_path}")

    # Optionally also dump the per-run results (without manifest entry, to avoid
    # constantly changing hashes during development).
    full_results_path = output_dir / "ts1_extended_global_full_results.json"
    with full_results_path.open("w", encoding="utf-8") as f:
        json.dump(random_results, f, indent=2)
    print(f"✅ TS1_EXTENDED_GLOBAL full results saved: {full_results_path}")

    return summary


if __name__ == "__main__":
    run_ts1_extended_global()


