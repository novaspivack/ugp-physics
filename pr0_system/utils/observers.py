"""
Observer utilities for PR-0 simulations.

Designed to be additive and non-breaking: existing PR-0 APIs remain unchanged,
while callers can attach observers / loggers to collect metrics without
modifying the evolution core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Protocol


class SimulationObserver(Protocol):
    """Protocol for observer callbacks."""

    def __call__(self, metrics: Dict[str, Any]) -> None: ...


@dataclass
class ObserverRegistry:
    """Light-weight registry to manage simulation observers."""

    observers: List[SimulationObserver] = field(default_factory=list)

    def add(self, observer: SimulationObserver) -> None:
        if observer not in self.observers:
            self.observers.append(observer)

    def remove(self, observer: SimulationObserver) -> None:
        if observer in self.observers:
            self.observers.remove(observer)

    def extend(self, observers: Iterable[SimulationObserver]) -> None:
        for obs in observers:
            self.add(obs)

    def notify(self, metrics: Dict[str, Any]) -> None:
        for observer in list(self.observers):
            observer(metrics)


def ensure_registry(
    observers: Iterable[SimulationObserver] | ObserverRegistry | None
) -> ObserverRegistry:
    """Utility to normalize observer inputs."""
    if observers is None:
        return ObserverRegistry()
    if isinstance(observers, ObserverRegistry):
        return observers
    registry = ObserverRegistry()
    registry.extend(observers)
    return registry


@dataclass
class CSVSimulationLogger:
    """
    Simple CSV logger observer.

    Parameters
    ----------
    path:
        Destination file. Created if missing; headers written automatically.
    fieldnames:
        Metrics to persist. Missing keys are written as blank strings.
    flush_interval:
        Optional flush interval (number of rows). Defaults to 100.
    """

    path: str
    fieldnames: List[str]
    flush_interval: int = 100

    def __post_init__(self) -> None:
        import csv
        from pathlib import Path

        self._path = Path(self.path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._path.open("w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=self.fieldnames)
        self._writer.writeheader()
        self._rows_written = 0

    def __call__(self, metrics: Dict[str, Any]) -> None:
        row = {name: metrics.get(name, "") for name in self.fieldnames}
        self._writer.writerow(row)
        self._rows_written += 1
        if self.flush_interval and self._rows_written % self.flush_interval == 0:
            self._file.flush()

    def close(self) -> None:
        self._file.flush()
        self._file.close()

    def __del__(self) -> None:  # pragma: no cover - defensive
        try:
            self._file.close()
        except Exception:  # noqa: BLE001
            pass


