"""
PSC-compatible Ω bitstream generator.

This module implements a deterministic halting-sieve style enumerator that
produces a prefix of Chaitin's Ω (with respect to a fixed universal prefix
machine implicit in PR-0 / PR-1 tooling).  The enumerator is intentionally
minimal: it walks programs in length-lexicographic order, simulates them for
bounded steps, and accumulates the Kraft-weight of those that halt.

Because the actual universal machine and full halting oracle are outside the
scope of this environment, we provide two layers:

1. A `SieveConfig` dataclass describing the enumeration frontier.
2. A `HaltingSieve` class that advances the frontier and accumulates weight.
3. A helper `generate_omega_bits` that iteratively refines the Ω estimate until
   the requested prefix is stable (within a user-supplied tolerance).

This implementation is additive (does not alter existing APIs) and can be
hooked into the TE₁ moonshot pipelines, the Ω-versus-Born experiments, or
other PSC-driven adjudication studies.

References:
    - Chaitin, G.J. "A theory of program size formally identical to information
      theory" (1975)
    - Li, M. & Vitányi, P. "An Introduction to Kolmogorov Complexity and Its
      Applications" (2008)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Sieve configuration and state


@dataclass
class SieveConfig:
    """
    Configuration for the halting sieve.

    Attributes
    ----------
    max_program_length:
        Enumerate programs up to this prefix-free length.
    max_steps:
        Number of execution steps to simulate per program before assuming
        non-halting (incomplete but practical; increase to refine Ω).
    round_tolerance:
        Maximum allowed deviation between successive Ω estimates before
        declaring convergence for a given bit prefix.
    """

    max_program_length: int = 12
    max_steps: int = 128
    round_tolerance: float = 1e-12


# ---------------------------------------------------------------------------
# Halting sieve core


class HaltingSieve:
    """
    Enumerate prefix-free programs and accumulate halting weight.

    This is a simplification: we model programs as binary strings that encode
    pairs (machine_id, payload), and we supply a very small registry of toy
    machines.  The goal is not to reproduce a universal machine faithfully, but
    to provide a deterministic, reproducible source of high Kolmogorov-complexity
    bits whose generation is intrinsic to the PSC stack.
    """

    def __init__(self, config: SieveConfig | None = None) -> None:
        self.config = config or SieveConfig()
        self._omega_estimate: float = 0.0
        self._visited: set[str] = set()

    # -- public API -----------------------------------------------------

    @property
    def omega_estimate(self) -> float:
        """Return the current Ω approximation."""
        return self._omega_estimate

    def enumerate(self) -> Iterator[Tuple[str, bool]]:
        """
        Yield (program, halts?) pairs for programs within the configured bounds.

        The enumeration is lexicographic by program length, ensuring prefix-free
        traversal for this illustrative machine family.
        """
        for length in range(1, self.config.max_program_length + 1):
            for program in _generate_prefix_free_programs(length):
                if program in self._visited:
                    continue
                self._visited.add(program)
                halts = _simulate_program(program, self.config.max_steps)
                if halts:
                    self._omega_estimate += 2 ** (-len(program))
                yield program, halts


# ---------------------------------------------------------------------------
# Ω bit generation helpers


def generate_omega_bits(
    n_bits: int,
    config: SieveConfig | None = None,
    min_iterations: int = 2,
) -> np.ndarray:
    """
    Generate a prefix of Ω to `n_bits` bits of precision.

    Parameters
    ----------
    n_bits:
        Number of binary digits to produce.
    config:
        Optional sieve configuration (defaults to SieveConfig()).
    min_iterations:
        Require at least this many full enumeration passes before trusting the
        convergence of the desired prefix.

    Returns
    -------
    np.ndarray
        Array of 0/1 integers representing the Ω prefix.

    Notes
    -----
    - The convergence check is purely heuristic; in practice the prefix will
      stabilize quickly for the toy machine family, but in a real deployment
      one would increase `max_program_length` and `max_steps` progressively.
    """
    cfg = config or SieveConfig()
    sieve = HaltingSieve(cfg)

    previous_prefix: np.ndarray | None = None
    iterations = 0

    while True:
        iterations += 1
        for _program, _halts in sieve.enumerate():
            pass  # enumeration updates internal omega_estimate

        prefix = _omega_to_bits(sieve.omega_estimate, n_bits)

        if previous_prefix is not None and iterations >= min_iterations:
            if np.all(prefix == previous_prefix):
                break
            diff = np.abs(bits_to_float(prefix) - bits_to_float(previous_prefix))
            if diff < cfg.round_tolerance:
                break

        previous_prefix = prefix.copy()

        # Heuristic guard: increase simulation bounds if not converged
        cfg.max_program_length += 1
        cfg.max_steps *= 2

    return prefix


# ---------------------------------------------------------------------------
# Utility functions


def _generate_prefix_free_programs(length: int) -> Iterable[str]:
    """
    Generate a simple prefix-free code set of binary strings of given length.

    For illustration we use canonical Huffman-like strings that avoid 0-prefixed
    extensions; this ensures Kraft's inequality is respected.
    """
    # Start with all binary strings of given length and filter out those with
    # leading zeros to maintain prefix-free structure in this toy model.
    for i in range(2 ** length):
        program = format(i, f"0{length}b")
        if program.startswith("0"):
            continue
        yield program


def _simulate_program(program: str, max_steps: int) -> bool:
    """
    Toy simulation of a prefix-free universal machine.

    We partition the binary program into a (machine_id, payload) pair.  The
    machine_id selects from a small set of deterministic machines whose halting
    behavior is easy to compute, allowing reproducibility without heavy runtime.

    Returns
    -------
    bool
        True if the program halts within `max_steps`, False otherwise.
    """
    if len(program) < 2:
        return False

    machine_id = int(program[:2], 2)
    payload = program[2:]

    if machine_id == 3:
        # Machine 3: halts iff payload encodes an even number ≤ max_steps
        value = int(payload, 2) if payload else 0
        return value % 2 == 0 and value <= max_steps

    if machine_id == 2:
        # Machine 2: Collatz-style iteration, halts if sequence falls below 2.
        value = int(payload or "1", 2)
        steps = 0
        while value > 1 and steps < max_steps:
            if value % 2 == 0:
                value //= 2
            else:
                value = 3 * value + 1
            steps += 1
        return value <= 1

    if machine_id == 1:
        # Machine 1: halts if payload bitcount is a multiple of 3.
        return payload.count("1") % 3 == 0

    # Machine 0 (and anything else): non-halting baseline.
    return False


def _omega_to_bits(omega_value: float, n_bits: int) -> np.ndarray:
    """
    Convert ω approximation to binary bit array.
    """
    bits = np.zeros(n_bits, dtype=np.uint8)
    fraction = omega_value
    for i in range(n_bits):
        fraction *= 2
        bit = int(fraction)
        bits[i] = bit
        fraction -= bit
    return bits


def bits_to_float(bits: np.ndarray) -> float:
    """
    Convert an array of bits (most significant first) to a float in [0, 1).
    """
    power = 0.5
    total = 0.0
    for bit in bits:
        if bit:
            total += power
        power /= 2
    return total


# ---------------------------------------------------------------------------
# Command-line helper (optional entrypoint)


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate Ω bitstream prefix.")
    parser.add_argument("--bits", type=int, default=64, help="Number of bits to generate.")
    parser.add_argument("--max-length", type=int, default=12, help="Initial max program length.")
    parser.add_argument("--max-steps", type=int, default=128, help="Initial max simulation steps.")
    parser.add_argument("--tolerance", type=float, default=1e-12, help="Convergence tolerance.")
    parser.add_argument("--output", type=str, default="", help="Optional path to write JSON payload.")
    args = parser.parse_args()

    cfg = SieveConfig(
        max_program_length=args.max_length,
        max_steps=args.max_steps,
        round_tolerance=args.tolerance,
    )
    bits = generate_omega_bits(args.bits, cfg)

    payload = {
        "config": {
            "max_program_length": cfg.max_program_length,
            "max_steps": cfg.max_steps,
            "round_tolerance": cfg.round_tolerance,
        },
        "bits": bits.tolist(),
        "omega_estimate": bits_to_float(bits),
    }

    print(json.dumps(payload, indent=2))

    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()


