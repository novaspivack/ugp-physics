"""
Finite-observer deviation analysis for Moonshot 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class DeviationBound:
    samples: int
    observer_complexity: int
    c: float = 1.0
    gamma: float = 1.0

    def limit(self) -> float:
        if self.samples <= 0:
            raise ValueError("samples must be positive.")
        effective_complexity = max(1, self.observer_complexity)
        return self.c / np.sqrt(self.samples) + self.gamma / effective_complexity


class BoundedObserverAnalyzer:
    """
    Evaluate whether empirical deviations remain within the PSC-Born bound.
    """

    def __init__(self, c: float = 1.0, gamma: float = 1.0) -> None:
        self.c = float(c)
        self.gamma = float(gamma)

    def evaluate(
        self,
        empirical: np.ndarray,
        expected: np.ndarray,
        samples: int,
        observer_complexity: int,
    ) -> Dict[str, float | bool]:
        empirical = np.asarray(empirical, dtype=float)
        expected = np.asarray(expected, dtype=float)
        if empirical.shape != expected.shape:
            raise ValueError("Empirical and expected distributions must align.")
        empirical /= empirical.sum()
        expected /= expected.sum()

        tv = 0.5 * np.sum(np.abs(empirical - expected))
        bound = DeviationBound(samples, observer_complexity, self.c, self.gamma).limit()
        within = tv <= bound + 1e-12
        return {
            "tv_distance": tv,
            "bound": bound,
            "within_bound": within,
            "samples": samples,
            "observer_complexity": observer_complexity,
        }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Check PSC-Born finite-observer deviation bound.")
    parser.add_argument("--expected", type=float, nargs="+", required=True)
    parser.add_argument("--empirical", type=float, nargs="+", required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--complexity", type=int, required=True)
    parser.add_argument("--c", type=float, default=1.0)
    parser.add_argument("--gamma", type=float, default=1.0)
    args = parser.parse_args()

    analyzer = BoundedObserverAnalyzer(c=args.c, gamma=args.gamma)
    result = analyzer.evaluate(
        empirical=np.array(args.empirical, dtype=float),
        expected=np.array(args.expected, dtype=float),
        samples=args.samples,
        observer_complexity=args.complexity,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


