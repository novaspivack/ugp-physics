"""Reflexive controller for the minimal TE₁.B_v2 testbed.

Specification: docs/TE1B_Minimal_RSM_Spec.md
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Tuple

from .minimal_rsm import ReflexiveChain


@dataclass
class ControllerConfig:
    window_size: int
    jarzynski_band: float
    crooks_band: float
    learning_rate_alpha: float
    learning_rate_beta: float
    steady_windows: int
    alpha_min: float = 0.1
    alpha_max: float = 5.0
    beta_min: float = -2.0
    beta_max: float = 2.0


class ReflexiveController:
    """Proportional controller enforcing fluctuation tolerances."""

    def __init__(self, config: ControllerConfig, chain: ReflexiveChain) -> None:
        self._cfg = config
        self._chain = chain
        self._windows_js: Deque[float] = deque(maxlen=config.window_size)
        self._windows_cs: Deque[float] = deque(maxlen=config.window_size)
        self._steady = 0

    @property
    def parameters(self) -> Tuple[float, float]:
        return self._chain.parameters

    def update(self, jarzynski_residual: float, crooks_slope: float) -> Tuple[float, float]:
        """Process new stats and return the updated (alpha, beta)."""
        self._windows_js.append(jarzynski_residual)
        self._windows_cs.append(crooks_slope)

        alpha, beta = self._chain.parameters
        if not self._within_band(jarzynski_residual, self._cfg.jarzynski_band):
            alpha -= self._cfg.learning_rate_alpha * jarzynski_residual
        if not self._within_band(crooks_slope - 1.0, self._cfg.crooks_band):
            beta -= self._cfg.learning_rate_beta * (crooks_slope - 1.0)
        alpha = float(min(max(alpha, self._cfg.alpha_min), self._cfg.alpha_max))
        beta = float(min(max(beta, self._cfg.beta_min), self._cfg.beta_max))
        self._chain.set_parameters(alpha, beta)

        if self._window_within_tolerance():
            self._steady += 1
        else:
            self._steady = 0
        return self._chain.parameters

    def frozen(self) -> bool:
        """Return True once tolerances held for steady_windows windows."""
        return self._steady >= self._cfg.steady_windows

    def _within_band(self, value: float, band: float) -> bool:
        return abs(value) <= band

    def _window_within_tolerance(self) -> bool:
        if len(self._windows_js) < self._cfg.window_size:
            return False
        js_ok = all(self._within_band(v, self._cfg.jarzynski_band) for v in self._windows_js)
        cs_ok = all(self._within_band(v - 1.0, self._cfg.crooks_band) for v in self._windows_cs)
        return js_ok and cs_ok
