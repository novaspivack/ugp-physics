"""
Synchronous 2-level FCA engine.

Pure-NumPy 2-level synchronous fractal cellular automaton. At each step:

  1. The inner CA (Rule 110 by default) advances one step in every outer cell
     window, seeded from the ETHER14 vacuum tiling.
  2. The outer CA advances one step using the chosen outer rule.
  3. The local clock-rate observable tau_c(t, i) records how many inner steps
     a majority-vote coarse-graining of the inner window would have required
     to match the outer transition.

This is the canonical "ontological time" engine: tau_c is the matter-induced
clock dilation field, and the AFCA visualization wraps this with a region
detection layer to compare against the ether reference run.
"""

from __future__ import annotations

import numpy as np

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)


ETHER14 = np.array(
    [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8
)


def make_rule_table(rule_num: int) -> np.ndarray:
    return np.array(
        [(rule_num >> n) & 1 for n in range(8)], dtype=np.uint8
    )


def apply_rule(state: np.ndarray, rule_table: np.ndarray) -> np.ndarray:
    """One step of a binary 1D CA with periodic BC."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return rule_table[(l << 2) | (c << 1) | r]


def build_tau_phase_table(inner_M: int, cap: int) -> np.ndarray:
    """
    Precompute tau_c[phase, target] for each (phase, target) pair where
    phase in [0, 13] is the ETHER14 phase offset and target in {0, 1} is
    the requested outer-cell post-image. The returned table has shape
    (14, 2) float32 with cap as the sentinel for unreachable transitions.
    """
    table = np.full((14, 2), cap, dtype=np.float32)
    rule110 = make_rule_table(110)
    for phase in range(14):
        window = np.array(
            [ETHER14[(phase + j) % 14] for j in range(inner_M)],
            dtype=np.uint8,
        )
        for step in range(cap):
            maj = 1 if window.sum() * 2 > inner_M else 0
            for tgt in (0, 1):
                if table[phase, tgt] == cap and maj == tgt:
                    table[phase, tgt] = float(step)
            if table[phase, 0] < cap and table[phase, 1] < cap:
                break
            window = apply_rule(window, rule110)
    return table


def ether_tape(length: int) -> np.ndarray:
    return np.array(
        [ETHER14[i % 14] for i in range(length)], dtype=np.uint8
    )


class FCASync(SimEngine):

    model_name = "fca_sync"
    spatial_dim = 1
    supported_ic_kinds = ("ether", "vacuum", "random", "load")
    default_params = {
        "rule": 110,
        "L": 500,
        "inner_M": 7,
        "inner_rule": 110,
    }

    def _setup(self) -> None:
        L = int(self.params["L"])
        inner_M = int(self.params["inner_M"])
        self.tape = ether_tape(L)
        self._ref_tape = ether_tape(L)
        self._outer_rule_table = make_rule_table(int(self.params["rule"]))
        self._tau_phase = build_tau_phase_table(inner_M, inner_M * 5)
        self._phases = np.arange(L, dtype=np.int32) % 14
        self._last_tau = np.zeros(L, dtype=np.float32)

    def _step_impl(self, n_steps: int) -> None:
        for _ in range(n_steps):
            next_tape = apply_rule(self.tape, self._outer_rule_table)
            self._last_tau = self._tau_phase[self._phases, next_tape.astype(np.int32)]
            self.tape = next_tape
            self._step += 1
            self._time += 1.0

    def snapshot(self) -> FieldSnapshot:
        return FieldSnapshot(
            step=self._step,
            time=self._time,
            model=self.model_name,
            tape=self.tape.copy(),
            tau_c=self._last_tau.copy(),
            extra={
                "L": int(self.params["L"]),
                "inner_M": int(self.params["inner_M"]),
                "rule": int(self.params["rule"]),
                "density": float(self.tape.mean()),
            },
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="ether")
        L = int(self.params["L"])
        if ic.kind == "ether" or ic.kind == "vacuum":
            self.tape = ether_tape(L)
        elif ic.kind == "random":
            rng = np.random.default_rng(int(ic.params.get("seed", 0)))
            self.tape = rng.integers(0, 2, L, dtype=np.uint8)
        elif ic.kind == "load":
            if not ic.path:
                raise ValueError("ic 'load' requires path")
            self.load_state(ic.path)
            return
        else:
            raise ValueError(f"unknown ic kind '{ic.kind}'")
        self._step = 0
        self._time = 0.0
        self._last_tau[:] = 0.0

    def inject(self, spec: InjectionSpec) -> None:
        from ugp_viz.catalog.manager import load_entry

        entry = load_entry(self.model_name, spec.kind)
        seed = _coerce_seed(entry)
        L = int(self.params["L"])
        pos = spec.position
        if pos is None:
            pos = int(entry.get("default_position", L // 2))
        pos = int(pos)
        for j, b in enumerate(seed):
            self.tape[(pos + j) % L] = b

    @property
    def ref_tape(self) -> np.ndarray:
        return self._ref_tape

    def set_ref_tape(self, tape: np.ndarray) -> None:
        self._ref_tape = np.asarray(tape, dtype=np.uint8).copy()


def _coerce_seed(entry: dict) -> np.ndarray:
    """Build a uint8 seed array from a catalog entry.

    Supports three field encodings (in order of preference):

    * ``"seed": [0, 1, 1, ...]`` — explicit cell list (legacy entries).
    * ``"bits": "01101..."`` — Martinez-style bit string for the glider
      core pattern (no ether padding).
    * ``"tape": "..."`` — Cook/Martinez-style padded tape ready to drop
      onto the lattice (default for the R110 catalog).
    """
    if "seed" in entry:
        return np.array(entry["seed"], dtype=np.uint8)
    for key in ("tape", "bits"):
        s = entry.get(key)
        if isinstance(s, str) and s:
            return np.array([1 if c == "1" else 0 for c in s], dtype=np.uint8)
    raise ValueError(
        f"catalog entry '{entry.get('kind') or entry.get('name')}' "
        f"has no usable seed/bits/tape field"
    )
