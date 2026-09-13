"""
Parallel adjudication experiments combining Moonshot 2 components.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Literal

import numpy as np

from .bounded_observer import BoundedObserverAnalyzer
from .omega_harness import MeasurementResult, ProviderName, sample_measurements


def run_parallel_experiment(
    amplitudes: Iterable[complex | float],
    samples: int,
    provider_a: ProviderName = "pcg64",
    provider_b: ProviderName = "omega",
    observer_complexity: int = 1024,
    seed_a: int | None = 0,
    seed_b: int | None = None,
) -> Dict[str, object]:
    """
    Execute two adjudication arms and compare empirical distributions.
    """
    res_a = sample_measurements(amplitudes, samples, provider=provider_a, seed=seed_a)
    res_b = sample_measurements(amplitudes, samples, provider=provider_b, seed=seed_b)

    diff_tv = 0.5 * np.sum(np.abs(res_a.empirical_probabilities - res_b.empirical_probabilities))

    analyzer = BoundedObserverAnalyzer()
    bound_report = analyzer.evaluate(
        empirical=res_b.empirical_probabilities,
        expected=res_a.empirical_probabilities,
        samples=samples,
        observer_complexity=observer_complexity,
    )

    return {
        "arm_a": _result_to_dict(res_a),
        "arm_b": _result_to_dict(res_b),
        "tv_between_arms": diff_tv,
        "bounded_observer": bound_report,
    }


def _result_to_dict(result: MeasurementResult) -> Dict[str, object]:
    return {
        "provider": result.provider,
        "bit_hash": result.bit_hash,
        "probabilities": result.probabilities.tolist(),
        "empirical_counts": result.empirical_counts.tolist(),
        "empirical_probabilities": result.empirical_probabilities.tolist(),
        "metrics": result.metrics,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run parallel adjudication experiment.")
    parser.add_argument("--amplitudes", type=float, nargs="+", required=True)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--provider-a", choices=["omega", "pcg64", "deterministic"], default="pcg64")
    parser.add_argument("--provider-b", choices=["omega", "pcg64", "deterministic"], default="omega")
    parser.add_argument("--observer-complexity", type=int, default=1024)
    parser.add_argument("--seed-a", type=int, help="Seed for provider A.")
    parser.add_argument("--seed-b", type=int, help="Seed for provider B.")
    parser.add_argument("--output", type=str, help="Optional JSON output path.")
    args = parser.parse_args()

    result = run_parallel_experiment(
        amplitudes=args.amplitudes,
        samples=args.samples,
        provider_a=args.provider_a,
        provider_b=args.provider_b,
        observer_complexity=args.observer_complexity,
        seed_a=args.seed_a,
        seed_b=args.seed_b,
    )
    payload = json.dumps(result, indent=2)
    print(payload)
    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()


