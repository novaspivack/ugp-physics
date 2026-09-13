"""
High-level helpers for running PR-0 simulations with observers and logging.

This module is intentionally additive: it does not alter existing evolution
classes, but provides convenience wrappers that build on the observer interface
introduced in ``pr0_system.utils.observers``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from pr0_system.utils.observers import (
    CSVSimulationLogger,
    ObserverRegistry,
    SimulationObserver,
    ensure_registry,
)


class SupportsAttachObserver(Protocol):
    """Protocol for integrators that expose ``attach_observer``."""

    def attach_observer(self, observer: SimulationObserver) -> None: ...
    def step(self, dt: float = 0.01) -> None: ...


@dataclass
class SimulationConfig:
    """Configuration for batch integrations."""

    steps: int
    dt: float = 0.01
    record_every: int = 1
    progress: bool = False


DEFAULT_FIELDS = [
    "timestep",
    "dt",
    "density_sum",
    "density_delta",
    "max_density",
    "mean_coherence",
    "internal_entropy",
    "damping_flux",
    "gamma_mean",
    "gamma_max",
    "support_area",
    "log_support_area",
]


def make_csv_logger(path: str | Path, fields: Iterable[str] = DEFAULT_FIELDS) -> CSVSimulationLogger:
    """Create a CSV logger observer with standard metrics."""
    return CSVSimulationLogger(path=str(path), fieldnames=list(fields))


def run_with_observers(
    integrator: SupportsAttachObserver,
    config: SimulationConfig,
    observers: Iterable[SimulationObserver] | ObserverRegistry | None = None,
) -> None:
    """
    Run a simulation with optional observers attached.

    Parameters
    ----------
    integrator:
        Any object exposing ``step(dt)`` and ``attach_observer``.
    config:
        Integration configuration.
    observers:
        Observer registry or iterable of observer callbacks. Observers are
        attached exactly once and remain active throughout the run.
    """
    registry = ensure_registry(observers)
    for observer in registry.observers:
        integrator.attach_observer(observer)

    for step in range(config.steps):
        integrator.step(dt=config.dt)
        if config.progress and (step + 1) % max(1, config.record_every) == 0:
            print(f"[PR-0] step {step + 1}/{config.steps}", flush=True)


