"""
Ω-driven measurement harness for Moonshot 2.

Provides utilities to sample measurement outcomes using different bitstream
providers (Ω sieve, PCG64, deterministic control) and compute statistical
distances against Born-rule expectations.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Literal, Tuple

import numpy as np
import hashlib

ProviderName = Literal["omega", "pcg64", "deterministic"]


@dataclass
class MeasurementResult:
    probabilities: np.ndarray
    empirical_counts: np.ndarray
    empirical_probabilities: np.ndarray
    provider: ProviderName
    bit_hash: str
    metrics: Dict[str, float]


def _omega_cached_uniform(samples: int, bits_per_float: int = 53) -> Tuple[np.ndarray, str]:
    """
    Deterministic Ω-like bitstream derived from SHA3 hashing.

    Provides a reproducible high-complexity sequence without invoking the
    heavy halting-sieve generator (suitable for PSC experiments).
    """
    total_bits = samples * bits_per_float
    seed = b"PSC_MOONSHOT2_OMEGA_PREFIX_V1"
    bit_buffer: list[int] = []
    while len(bit_buffer) < total_bits:
        seed = hashlib.sha3_512(seed).digest()
        for byte in seed:
            for shift in range(7, -1, -1):
                bit_buffer.append((byte >> shift) & 1)
                if len(bit_buffer) >= total_bits:
                    break
            if len(bit_buffer) >= total_bits:
                break
    bits = np.array(bit_buffer[:total_bits], dtype=np.uint8)
    chunks = bits.reshape(samples, bits_per_float)
    powers = 2.0 ** -np.arange(1, bits_per_float + 1, dtype=float)
    uniforms = chunks @ powers
    bit_hash = hashlib.sha256(bits.tobytes()).hexdigest()
    return uniforms, bit_hash


def _pcg64_uniform(samples: int, seed: int) -> Tuple[np.ndarray, str]:
    generator = np.random.default_rng(seed)
    uniforms = generator.random(samples, dtype=float)
    payload = uniforms.tobytes()
    return uniforms, hashlib.sha256(payload).hexdigest()


def _deterministic_uniform(samples: int) -> Tuple[np.ndarray, str]:
    # van der Corput base-2 sequence
    def van_der_corput(n: int) -> float:
        result = 0.0
        denom = 1.0
        while n:
            n, remainder = divmod(n, 2)
            denom *= 2.0
            result += remainder / denom
        return result

    uniforms = np.array([van_der_corput(i + 1) for i in range(samples)], dtype=float)
    payload = uniforms.tobytes()
    return uniforms, hashlib.sha256(payload).hexdigest()


def get_uniform_provider(name: ProviderName, seed: int | None = None) -> Callable[[int], Tuple[np.ndarray, str]]:
    if name == "omega":
        return lambda samples: _omega_cached_uniform(samples)
    if name == "omega_cached":  # alias for explicit selection
        return lambda samples: _omega_cached_uniform(samples)
    if name == "pcg64":
        actual_seed = int(seed if seed is not None else 0)
        return lambda samples: _pcg64_uniform(samples, actual_seed)
    if name == "deterministic":
        return lambda samples: _deterministic_uniform(samples)
    raise ValueError(f"Unknown provider: {name}")


def sample_measurements(
    amplitudes: Iterable[complex | float],
    samples: int,
    provider: ProviderName = "omega",
    seed: int | None = None,
) -> MeasurementResult:
    amplitudes_array = np.asarray(list(amplitudes), dtype=complex)
    probabilities = (np.abs(amplitudes_array) ** 2).astype(float)
    probabilities /= probabilities.sum()

    uniforms, bit_hash = get_uniform_provider(provider, seed)(samples)
    cumulative = np.cumsum(probabilities)
    cumulative[-1] = 1.0  # guard against rounding error
    outcomes = np.searchsorted(cumulative, uniforms, side="left")
    counts = np.bincount(outcomes, minlength=probabilities.size)
    empirical_probabilities = counts / samples

    metrics = compute_metrics(probabilities, empirical_probabilities)

    return MeasurementResult(
        probabilities=probabilities,
        empirical_counts=counts,
        empirical_probabilities=empirical_probabilities,
        provider=provider,
        bit_hash=bit_hash,
        metrics=metrics,
    )


def compute_metrics(expected: np.ndarray, empirical: np.ndarray) -> Dict[str, float]:
    tv = 0.5 * np.sum(np.abs(expected - empirical))

    eps = 1e-12
    kl = float(np.sum(empirical * np.log((empirical + eps) / (expected + eps))))
    chi_square = float(np.sum(((empirical - expected) ** 2) / (expected + eps)))
    l2 = float(np.sum((empirical - expected) ** 2))

    return {
        "tv_distance": tv,
        "kl_divergence": kl,
        "chi_square": chi_square,
        "l2_error": l2,
    }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run Ω/PRNG measurement harness.")
    parser.add_argument("--amplitudes", type=float, nargs="+", required=True, help="Amplitude magnitudes (will be normalized).")
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--provider", choices=["omega", "pcg64", "deterministic"], default="omega")
    parser.add_argument("--seed", type=int, help="Seed for PCG64 provider.")
    args = parser.parse_args()

    amplitudes = np.array(args.amplitudes, dtype=float)
    result = sample_measurements(amplitudes, args.samples, provider=args.provider, seed=args.seed)
    payload = {
        "provider": result.provider,
        "bit_hash": result.bit_hash,
        "probabilities": result.probabilities.tolist(),
        "empirical_counts": result.empirical_counts.tolist(),
        "empirical_probabilities": result.empirical_probabilities.tolist(),
        "metrics": result.metrics,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


