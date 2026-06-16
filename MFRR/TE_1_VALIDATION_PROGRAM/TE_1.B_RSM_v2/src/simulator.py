"""Simulation helpers with optional multiprocessing for TE₁.B_v2.

Specification: docs/TE1B_Minimal_RSM_Spec.md
"""
from __future__ import annotations

import multiprocessing as mp
from dataclasses import dataclass
from typing import Callable, List, Sequence, Tuple

import numpy as np

from .minimal_rsm import ReflexiveChain, build_default_chain

ChainFactory = Callable[[float, float, float, int | None], ReflexiveChain]


def _default_factory(drive_mu: float, intensity_alpha: float, reverse_bias_beta: float, seed: int | None) -> ReflexiveChain:
    return build_default_chain(drive_mu=drive_mu, intensity_alpha=intensity_alpha, reverse_bias_beta=reverse_bias_beta, seed=seed)


@dataclass
class EnsembleConfig:
    forward_mu: float
    reverse_mu: float
    trajectory_length: int
    forward_count: int
    reverse_count: int
    intensity_alpha: float = 1.0
    reverse_bias_beta: float = 0.0
    start_state: str = "S0"
    processes: int | None = None


def run_ensembles(config: EnsembleConfig, chain_factory: ChainFactory | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """Run forward and reverse ensembles, optionally parallelised.

    Returns arrays of ΔS_ref samples for forward and reverse protocols.
    """
    factory = chain_factory or _default_factory
    seeds_forward = _seed_sequence(config.forward_count)
    seeds_reverse = _seed_sequence(config.reverse_count, offset=config.forward_count)
    args_forward = [
        _WorkerArgs(
            factory=factory,
            mu=config.forward_mu,
            start_state=config.start_state,
            trajectory_length=config.trajectory_length,
            seed=seed,
            alpha=config.intensity_alpha,
            beta=config.reverse_bias_beta,
        )
        for seed in seeds_forward
    ]
    args_reverse = [
        _WorkerArgs(
            factory=factory,
            mu=config.reverse_mu,
            start_state=config.start_state,
            trajectory_length=config.trajectory_length,
            seed=seed,
            alpha=config.intensity_alpha,
            beta=config.reverse_bias_beta,
        )
        for seed in seeds_reverse
    ]
    forward_samples = _execute(args_forward, config.processes)
    reverse_samples = _execute(args_reverse, config.processes)
    return forward_samples, reverse_samples


@dataclass
class _WorkerArgs:
    factory: ChainFactory
    mu: float
    start_state: str
    trajectory_length: int
    seed: int
    alpha: float = 1.0
    beta: float = 0.0


def _execute(args: Sequence[_WorkerArgs], processes: int | None) -> np.ndarray:
    if not args:
        return np.empty(0, dtype=np.float64)
    if processes is None or processes <= 1:
        results = [_worker(a) for a in args]
    else:
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=processes) as pool:
            results = pool.map(_worker, args)
    return np.concatenate(results)


def _worker(args: _WorkerArgs) -> np.ndarray:
    chain = args.factory(args.mu, args.alpha, args.beta, args.seed)
    _, entropy = chain.run_trajectory(args.start_state, args.trajectory_length)
    return np.asarray(entropy, dtype=np.float64)


def _seed_sequence(count: int, offset: int = 0) -> List[int]:
    rng = np.random.default_rng()
    seeds = rng.integers(0, 2**32 - 1, size=count, dtype=np.uint32)
    return [int(seed) + offset for seed in seeds]
