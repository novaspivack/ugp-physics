"""
Shared annealing utilities for PR-0 bootstraps.

This module consolidates the simulated annealing helpers that previously lived
inside each force bootstrap. Refactoring plan tracked in
`SESSION_PR_0_27_1_NEXT_STEPS.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


def _ensure_rng(rng: Optional[np.random.Generator] = None) -> np.random.Generator:
    """Return a generator, creating a default one if necessary."""
    return rng if rng is not None else np.random.default_rng()


@dataclass
class AnnealingController:
    """
    Convenience wrapper for temperature schedules and multiplicative noise.

    Attributes:
        total_steps: Nominal length of the annealing schedule. Used to compute
            progress; does not enforce a hard cutoff.
        min_temperature: Lower bound for the temperature scaling.
        rng: Random number generator used for perturbations.
    """

    total_steps: float
    min_temperature: float = 0.05
    rng: np.random.Generator = field(default_factory=np.random.default_rng)

    def temperature(self, step: int) -> float:
        """
        Compute the current temperature based on progress through the schedule.

        Args:
            step: Current timestep.

        Returns:
            Temperature in [min_temperature, 1.0].
        """
        if self.total_steps <= 0:
            return self.min_temperature
        progress = min(max(step / self.total_steps, 0.0), 1.0)
        return max(self.min_temperature, 1.0 - progress)

    def random_factor(self, temperature: float, magnitude: float) -> float:
        """
        Draw a multiplicative factor for a parameter update.

        Args:
            temperature: Current temperature scalar.
            magnitude: Maximum relative adjustment when temperature == 1.0.

        Returns:
            Uniform factor in [1/(1 + temperature*magnitude), 1 + temperature*magnitude].
        """
        scale = 1.0 + temperature * magnitude
        return float(self.rng.uniform(1.0 / scale, scale))

    def perturb(
        self,
        value: float,
        temperature: float,
        magnitude: float,
        bounds: Optional[Tuple[float, float]] = None,
    ) -> float:
        """
        Apply a temperature-scaled perturbation and optionally clip the result.
        """
        updated = value * self.random_factor(temperature, magnitude)
        if bounds is not None:
            updated = float(np.clip(updated, bounds[0], bounds[1]))
        return float(updated)

    def revert_to_best(
        self,
        best_value: float,
        temperature: float,
        magnitude: float,
        bounds: Optional[Tuple[float, float]] = None,
    ) -> float:
        """
        Draw a new candidate near the best-known value.
        """
        candidate = best_value * self.random_factor(temperature, magnitude)
        if bounds is not None:
            candidate = float(np.clip(candidate, bounds[0], bounds[1]))
        return float(candidate)


def annealing_controller(
    total_steps: float,
    min_temperature: float = 0.05,
    rng: Optional[np.random.Generator] = None,
) -> AnnealingController:
    """
    Helper factory mirroring older in-class construction.
    """
    return AnnealingController(
        total_steps=total_steps,
        min_temperature=min_temperature,
        rng=_ensure_rng(rng),
    )


