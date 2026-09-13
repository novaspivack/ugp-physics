"""
TS1_EXTENDED_PURE: Clean-Room SRRG Fixed-Point Validation (Pure GTE Functional)

Spec reference:
  SRRG_VALIDATION_PROGRAM/SESSIONS/8_1_TS1_EXTENDED_TESTS_PLAN.md

Purpose:
  - Re-run TS1 using the pure-GTE SRRG functional with an explicit
    "no empirical tuning" constraint.
  - Log the Elegant Kernel / UCL palette and SRRG parameters used,
    to make the theoretical origin of all constants auditable.
  - Write results and plots into `outputs/ts1_extended/pure/` so they
    are cleanly separated from the original TS1 runs.
"""

from pathlib import Path
from typing import Dict

import json

from ts1_final_pure_gte import (
    DEFAULT_PARAMS,
    BASIN_CONFIG,
    N_CORES,
    run_ts1_final,
    plot_results,
)
from srrg_io import (
    load_canonical_sm_triples,
    save_results_with_manifest,
)
from srrg_functional_pure_gte import elegant_palette


def palette_to_dict(palette) -> Dict:
    """
    Convert UCLPalette dataclass to a plain dict for JSON logging.
    We intentionally do not interpret or modify the constants here;
    they are defined theoretically in `srrg_functional_pure_gte`.
    """
    return {
        "k0": palette.k0,
        "k1": palette.k1,
        "k2": palette.k2,
        "k3": palette.k3,
        "k4": palette.k4,
        "k5": palette.k5,
        "k6": palette.k6,
        "k7": palette.k7,
        "k8": palette.k8,
    }


def main() -> Dict:
    """
    Execute the TS1_EXTENDED_PURE validation.

    This is a thin wrapper around `run_ts1_final` that:
      - Uses the pure-GTE SRRG functional.
      - Logs the Elegant UCL palette and SRRG parameters to the manifest.
      - Writes outputs to `outputs/ts1_extended/pure/`.
    """
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts1_extended" / "pure"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load canonical SM triples
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    print(f"Loaded {len(particles)} SM particles for TS1_EXTENDED_PURE")

    # Log the Elegant Kernel / UCL palette used by the pure-GTE functional
    palette = elegant_palette()
    palette_dict = palette_to_dict(palette)

    # Run TS1 using the same configuration as ts1_final_pure_gte
    results = run_ts1_final(
        particles=particles,
        params=DEFAULT_PARAMS,
        basin_config=BASIN_CONFIG,
        n_cores=N_CORES,
        verbose=True,
    )

    # Attach palette and parameter metadata for auditability
    results_extended = {
        "ts1_extended_pure_results": results,
        "ucl_palette_elegant": palette_dict,
        "srrg_parameters": {
            "w_coherence": DEFAULT_PARAMS.w_coherence,
            "w_genon": DEFAULT_PARAMS.w_genon,
            "w_ucl_optimality": DEFAULT_PARAMS.w_ucl_optimality,
            "penalty_qlock": DEFAULT_PARAMS.penalty_qlock,
            "penalty_kernel": DEFAULT_PARAMS.penalty_kernel,
            "penalty_admiss": DEFAULT_PARAMS.penalty_admiss,
            "penalty_mdl": DEFAULT_PARAMS.penalty_mdl,
            "fisher_scale": DEFAULT_PARAMS.fisher_scale,
            "fisher_diagonal_only": DEFAULT_PARAMS.fisher_diagonal_only,
            "projection_tol": DEFAULT_PARAMS.projection_tol,
            "k_M": DEFAULT_PARAMS.k_M,
            "k_gen2": DEFAULT_PARAMS.k_gen2,
            "k_L2": DEFAULT_PARAMS.k_L2,
        },
    }

    # Save results and metadata
    results_path = output_dir / "ts1_extended_pure_results.json"
    manifest_path = program_dir / "DATA_MANIFEST.json"

    save_results_with_manifest(
        data=results_extended,
        path=results_path,
        manifest_path=manifest_path,
        description=(
            "TS1_EXTENDED_PURE: SRRG fixed-point validation using pure GTE "
            "functional with explicit logging of Elegant UCL palette and "
            "SRRG parameters (no empirical tuning)."
        ),
    )

    print(f"\n✅ TS1_EXTENDED_PURE results saved: {results_path}")

    # Generate plots (reuse TS1 final plotting, but write into extended dir)
    plot_results(results, output_dir)

    # Also save the palette alone as a small JSON for quick inspection
    palette_path = output_dir / "ts1_extended_pure_elegant_palette.json"
    with palette_path.open("w", encoding="utf-8") as f:
        json.dump(palette_dict, f, indent=2)
    print(f"✅ Logged Elegant UCL palette: {palette_path}")

    return results_extended


if __name__ == "__main__":
    main()


