"""
Shared meta-learning helpers for PR-0 bootstraps.

Aggregates best-metric tracking utilities used across force-specific bootstraps.
See `SESSION_PR_0_27_1_NEXT_STEPS.md` for the refactoring plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Literal, Mapping, Optional


Goal = Literal["min", "max"]


def _initial_value(goal: Goal) -> float:
    return float("inf") if goal == "min" else float("-inf")


@dataclass
class BestTracker:
    """
    Track the best metric value and associated parameters.

    Args:
        goal: Whether smaller ("min") or larger ("max") metrics are preferred.
        best_metric: Optional initial best metric value. If omitted, the tracker
            starts at ±∞ depending on the goal.
        params: Optional initial parameter snapshot.
    """

    goal: Goal
    best_metric: Optional[float] = None
    params: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.goal not in ("min", "max"):
            raise ValueError(f"Unknown goal: {self.goal}")
        if self.best_metric is None:
            self.best_metric = _initial_value(self.goal)
        else:
            if self.goal == "min" and self.best_metric == float("-inf"):
                self.best_metric = float("inf")
            if self.goal == "max" and self.best_metric == float("inf"):
                self.best_metric = float("-inf")

    def consider(self, metric: float, params: Mapping[str, float]) -> bool:
        """
        Update the tracker if the metric improves.

        Returns:
            True if an improvement was recorded.
        """
        improved = (
            metric < self.best_metric
            if self.goal == "min"
            else metric > self.best_metric
        )
        if improved:
            self.best_metric = float(metric)
            self.params = {k: float(v) for k, v in params.items()}
        return improved

    def restore(self, name: str) -> float:
        """
        Retrieve the stored value for a tracked parameter.
        """
        return self.params[name]


