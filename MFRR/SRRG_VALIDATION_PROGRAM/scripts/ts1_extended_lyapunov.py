"""
TS1_EXTENDED_LYAPUNOV: Discrete Monotonicity Analysis of SRRG Flow (TS1)

Spec reference:
  SRRG_VALIDATION_PROGRAM/SESSIONS/8_1_TS1_EXTENDED_TESTS_PLAN.md

Purpose:
  - Quantify how close the SRRG discrete flow used in TS1 is to a true
    Lyapunov ascent on the pure-GTE viability functional F.
  - Analyze F-traces along SRRG trajectories for canonical SM triples and
    representative off-SM initial conditions, computing:
      * Fraction of steps with ΔF >= 0.
      * Distribution of ΔF violations (magnitude and frequency).
  - This complements TS9 (c-function monotonicity) with a TS1-focused
    view of monotonicity for single-particle flows under the same
    pure-GTE functional used in TS1_FINAL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import json

import numpy as np
from tqdm import tqdm

from srrg_core import (
    GTETriple,
    SRRGParameters,
    is_admissible,
    srrg_flow_to_convergence,
)
from srrg_io import load_canonical_sm_triples, save_results_with_manifest
from srrg_functional_pure_gte import elegant_palette, viability_functional_pure_gte


DEFAULT_PARAMS = SRRGParameters()

LYAPUNOV_CONFIG = {
    "max_iter": 2000,
    "tol": 1e-8,
    "n_off_sm_starts_per_particle": 32,
    "off_sm_radius": 10.0,
    "seed": 20251119,
}


def make_F_fn(ucl_palette, params: SRRGParameters):
    """Pure-GTE viability functional F(triple) for use in flow and analysis."""

    def F(triple: GTETriple) -> float:
        return viability_functional_pure_gte([triple], ucl_palette, params)

    return F


def analyze_F_trace(F_trace: List[float]) -> Dict:
    """
    Compute monotonicity statistics for a single F-trace.

    Returns:
      - n_steps: number of steps
      - n_monotone: number with ΔF >= 0
      - frac_monotone: n_monotone / n_steps (if n_steps>0)
      - max_drop: largest negative ΔF
      - mean_drop_negative: mean of negative ΔF values (0 if none)
    """
    if len(F_trace) < 2:
        return {
            "n_steps": 0,
            "n_monotone": 0,
            "frac_monotone": 1.0,
            "max_drop": 0.0,
            "mean_drop_negative": 0.0,
        }

    deltas = np.diff(np.array(F_trace, dtype=float))
    n_steps = len(deltas)
    monotone_mask = deltas >= 0.0
    n_monotone = int(np.sum(monotone_mask))
    frac_monotone = float(n_monotone) / float(n_steps)

    negative_deltas = deltas[deltas < 0.0]
    max_drop = float(negative_deltas.min()) if negative_deltas.size > 0 else 0.0
    mean_drop_negative = float(negative_deltas.mean()) if negative_deltas.size > 0 else 0.0

    return {
        "n_steps": n_steps,
        "n_monotone": n_monotone,
        "frac_monotone": frac_monotone,
        "max_drop": max_drop,
        "mean_drop_negative": mean_drop_negative,
    }


def sample_off_sm_initials(
    rng: np.random.Generator,
    canonical: GTETriple,
    n_samples: int,
    radius: float,
) -> List[GTETriple]:
    """
    Sample off-SM initial conditions in a Gaussian neighborhood around a
    canonical triple, but with a constraint that we do not start exactly
    on the canonical triple.
    """
    initials: List[GTETriple] = []

    while len(initials) < n_samples:
        delta_a = rng.normal(0.0, radius)
        delta_b = rng.normal(0.0, radius)
        delta_c = rng.normal(0.0, radius) if canonical.c > 0 else 0.0

        a_new = int(round(canonical.a + delta_a))
        b_new = int(round(canonical.b + delta_b))
        c_new = canonical.c
        if canonical.c > 0:
            c_new = int(round(canonical.c + delta_c))

        trial = GTETriple(a_new, b_new, c_new, canonical.g, name=f"{canonical.name}_off")

        if not is_admissible(trial):
            continue
        if (trial.a == canonical.a) and (trial.b == canonical.b) and (trial.c == canonical.c):
            continue

        initials.append(trial)

    return initials


def run_ts1_extended_lyapunov() -> Dict:
    """
    Execute TS1_EXTENDED_LYAPUNOV analysis.

    For each canonical SM triple:
      - Run SRRG flow from the canonical triple itself (idealized case).
      - Run SRRG flows from multiple nearby off-SM initial triples.
      - For each flow, compute monotonicity statistics on F_trace.
    Aggregate results across all particles and write a summary JSON.
    """
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts1_extended" / "lyapunov"
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

    cfg = LYAPUNOV_CONFIG
    rng = np.random.default_rng(cfg["seed"])

    per_particle_results: Dict[str, Dict] = {}

    # Storage for global aggregates
    frac_monotone_all = []
    max_drop_all = []
    mean_drop_neg_all = []

    for triple in tqdm(canonical_triples, desc="Analyzing Lyapunov traces"):
        particle_name = triple.name

        # 1. Flow starting exactly at the canonical triple
        result_canonical = srrg_flow_to_convergence(
            triple_init=triple,
            F_fn=F_fn,
            params=DEFAULT_PARAMS,
            ucl_fn=None,
            max_iter=cfg["max_iter"],
            tol=cfg["tol"],
        )
        stats_canonical = analyze_F_trace(result_canonical["F_trace"])

        # 2. Off-SM initial conditions around this triple
        initials_off = sample_off_sm_initials(
            rng=rng,
            canonical=triple,
            n_samples=cfg["n_off_sm_starts_per_particle"],
            radius=cfg["off_sm_radius"],
        )

        off_stats_list = []
        for init_triple in initials_off:
            result_off = srrg_flow_to_convergence(
                triple_init=init_triple,
                F_fn=F_fn,
                params=DEFAULT_PARAMS,
                ucl_fn=None,
                max_iter=cfg["max_iter"],
                tol=cfg["tol"],
            )
            stats_off = analyze_F_trace(result_off["F_trace"])
            off_stats_list.append(
                {
                    "initial_triple": init_triple.to_dict(),
                    "flow_stats": stats_off,
                }
            )

        # Aggregate for this particle
        frac_monotone_all.append(stats_canonical["frac_monotone"])
        max_drop_all.append(stats_canonical["max_drop"])
        mean_drop_neg_all.append(stats_canonical["mean_drop_negative"])

        for entry in off_stats_list:
            s = entry["flow_stats"]
            frac_monotone_all.append(s["frac_monotone"])
            max_drop_all.append(s["max_drop"])
            mean_drop_neg_all.append(s["mean_drop_negative"])

        per_particle_results[particle_name] = {
            "canonical_triple": triple.to_dict(),
            "canonical_flow_stats": stats_canonical,
            "off_sm_flows": off_stats_list,
        }

    # Global aggregates
    frac_monotone_arr = np.array(frac_monotone_all, dtype=float)
    max_drop_arr = np.array(max_drop_all, dtype=float)
    mean_drop_neg_arr = np.array(mean_drop_neg_all, dtype=float)

    summary: Dict = {
        "test_name": "TS1_EXTENDED_LYAPUNOV: Discrete SRRG monotonicity analysis (pure GTE)",
        "config": cfg,
        "global_statistics": {
            "mean_frac_monotone": float(frac_monotone_arr.mean()) if frac_monotone_arr.size > 0 else 1.0,
            "min_frac_monotone": float(frac_monotone_arr.min()) if frac_monotone_arr.size > 0 else 1.0,
            "max_frac_monotone": float(frac_monotone_arr.max()) if frac_monotone_arr.size > 0 else 1.0,
            "max_negative_drop": float(max_drop_arr.min()) if max_drop_arr.size > 0 else 0.0,
            "mean_negative_drop": float(mean_drop_neg_arr.mean()) if mean_drop_neg_arr.size > 0 else 0.0,
        },
        "per_particle_results": per_particle_results,
    }

    # Save summary
    results_path = output_dir / "ts1_extended_lyapunov_summary.json"
    manifest_path = program_dir / "DATA_MANIFEST.json"

    save_results_with_manifest(
        data=summary,
        path=results_path,
        manifest_path=manifest_path,
        description=(
            "TS1_EXTENDED_LYAPUNOV: Monotonicity statistics for SRRG flows "
            "under the pure GTE functional, for canonical SM triples and "
            "nearby off-SM initial conditions."
        ),
    )

    print(f"\n✅ TS1_EXTENDED_LYAPUNOV summary saved: {results_path}")

    # Also save a standalone JSON (without manifest metadata) for detailed inspection
    full_results_path = output_dir / "ts1_extended_lyapunov_full_results.json"
    with full_results_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ TS1_EXTENDED_LYAPUNOV full results saved: {full_results_path}")

    return summary


if __name__ == "__main__":
    run_ts1_extended_lyapunov()


