"""Minimal reflexive fluctuation testbed implementation.

Specification: docs/TE1B_Minimal_RSM_Spec.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import math
import numpy as np


@dataclass
class State:
    """State node with coherence metadata."""

    label: str
    coherence: float


@dataclass
class Transition:
    """Directed transition describing base rate and entropy components."""

    source: str
    target: str
    base_rate: float
    logical_entropy: float
    coherence_entropy: float
    mu_coupling: float = 0.0
    bias_sign: float = 0.0
    coherence_gain: float = 0.0


@dataclass
class ReflexiveChainConfig:
    """Configuration bundle for the minimal reflexive chain."""

    states: List[State]
    transitions: List[Transition]
    drive_mu: float
    intensity_alpha: float
    reverse_bias_beta: float
    coherence_relax: float = 0.0


class ReflexiveChain:
    """Reflexive Markov simulator for TE₁.B_v2.

    Implements CP-style jumps and tracks ΔS_ref per Specification §2.
    """

    def __init__(self, config: ReflexiveChainConfig, seed: int | None = None) -> None:
        self._states: Dict[str, State] = {s.label: s for s in config.states}
        self._transitions: List[Transition] = list(config.transitions)
        self._drive_mu = config.drive_mu
        self._alpha = config.intensity_alpha
        self._beta = config.reverse_bias_beta
        self._coherence_relax = config.coherence_relax
        self._rng = np.random.default_rng(seed)

    def step(self, current: str) -> Tuple[str, float]:
        """Perform a jump from the current state and return (next_state, ΔS_ref)."""
        outgoing = self._outgoing(current)
        if not outgoing:
            return current, 0.0
        dyn_terms = [self._dynamic_term(t) for t in outgoing]
        rates = np.array([self._effective_rate(t, dyn) for t, dyn in zip(outgoing, dyn_terms)], dtype=np.float64)
        total = float(np.sum(rates))
        if total <= 0.0:
            return current, 0.0
        probabilities = rates / total
        idx = int(self._rng.choice(len(outgoing), p=probabilities))
        transition = outgoing[idx]
        dynamic = dyn_terms[idx]
        delta_s = transition.logical_entropy + transition.coherence_entropy + dynamic
        self._update_coherence(transition)
        return transition.target, delta_s

    def run_trajectory(self, start: str, length: int) -> Tuple[List[str], List[float]]:
        """Simulate a trajectory of given length, returning states and ΔS_ref increments."""
        states = [start]
        entropy = []
        current = start
        for _ in range(length):
            current, delta_s = self.step(current)
            states.append(current)
            entropy.append(delta_s)
        return states, entropy

    def step_with_mu(self, current: str) -> Tuple[str, float, float]:
        """Perform a step and return (next_state, ΔS_ref, μ observable)."""
        next_state, delta_s = self.step(current)
        mu_obs = delta_s * self._drive_mu
        return next_state, delta_s, mu_obs

    def set_parameters(self, intensity_alpha: float, reverse_bias_beta: float) -> None:
        """Update controller-managed parameters."""
        self._alpha = intensity_alpha
        self._beta = reverse_bias_beta

    def set_drive_mu(self, drive_mu: float) -> None:
        self._drive_mu = drive_mu

    @property
    def parameters(self) -> Tuple[float, float]:
        return self._alpha, self._beta

    def _outgoing(self, label: str) -> List[Transition]:
        return [t for t in self._transitions if t.source == label]

    def _dynamic_term(self, transition: Transition) -> float:
        mu_term = transition.mu_coupling * self._drive_mu
        bias_term = transition.bias_sign * self._beta
        source_coh = self._states[transition.source].coherence
        target_coh = self._states[transition.target].coherence
        coherence_term = transition.coherence_gain * (target_coh - source_coh)
        return 0.5 * (mu_term + bias_term + coherence_term)

    def _effective_rate(self, transition: Transition, dynamic_term: float) -> float:
        """Compute rate with reflexive adjustments for μ, bias, and coherence."""
        base = max(transition.base_rate, 1e-9)
        log_rate = math.log(self._alpha) + math.log(base) + dynamic_term
        return float(math.exp(log_rate))

    def _update_coherence(self, transition: Transition) -> None:
        if self._coherence_relax <= 0.0:
            return
        source = self._states[transition.source]
        target = self._states[transition.target]
        delta = transition.coherence_entropy
        relax = self._coherence_relax
        source.coherence = (1.0 - relax) * source.coherence - relax * delta
        target.coherence = (1.0 - relax) * target.coherence + relax * delta


def jarzynski_estimator(entropy_samples: Iterable[float]) -> float:
    """Compute the Jarzynski estimator for a collection of ΔS_ref samples."""
    samples = np.array(list(entropy_samples), dtype=np.float64)
    if samples.size == 0:
        return float("nan")
    return float(np.mean(np.exp(-samples)))


def build_default_chain(drive_mu: float = 0.15, intensity_alpha: float = 1.0, reverse_bias_beta: float = 0.0, seed: int | None = None) -> ReflexiveChain:
    """Construct the default minimal reflexive chain described in the spec."""
    states = [
        State(label="S0", coherence=0.0),
        State(label="S1", coherence=0.04),
        State(label="S2", coherence=-0.04),
    ]
    transitions = [
        Transition("S0", "S1", base_rate=1.0, logical_entropy=0.12, coherence_entropy=0.02, mu_coupling=1.0, bias_sign=1.0, coherence_gain=0.25),
        Transition("S1", "S0", base_rate=1.0, logical_entropy=-0.12, coherence_entropy=-0.02, mu_coupling=-1.0, bias_sign=-1.0, coherence_gain=0.25),
        Transition("S1", "S2", base_rate=0.9, logical_entropy=0.08, coherence_entropy=0.015, mu_coupling=0.6, bias_sign=1.0, coherence_gain=0.2),
        Transition("S2", "S1", base_rate=0.9, logical_entropy=-0.08, coherence_entropy=-0.015, mu_coupling=-0.6, bias_sign=-1.0, coherence_gain=0.2),
        Transition("S2", "S0", base_rate=0.95, logical_entropy=0.05, coherence_entropy=0.01, mu_coupling=0.3, bias_sign=1.0, coherence_gain=0.15),
        Transition("S0", "S2", base_rate=0.95, logical_entropy=-0.05, coherence_entropy=-0.01, mu_coupling=-0.3, bias_sign=-1.0, coherence_gain=0.15),
    ]
    config = ReflexiveChainConfig(
        states=states,
        transitions=transitions,
        drive_mu=drive_mu,
        intensity_alpha=intensity_alpha,
        reverse_bias_beta=reverse_bias_beta,
        coherence_relax=0.05,
    )
    return ReflexiveChain(config=config, seed=seed)
