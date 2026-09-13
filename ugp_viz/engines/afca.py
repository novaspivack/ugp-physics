"""
AFCA (asynchronous fractal CA) engine.

Same outer/inner-CA decomposition as the synchronous FCA, but the outer cell
ticks only when a coarse-graining of the inner CA confirms the new outer
state. Cells with elevated tau_c (matter regions) advance in global time
more slowly than the ether vacuum; the difference is the matter-induced
clock dilation field that the AFCA construction interprets as emergent
gravitational time dilation.

The engine runs a sync trajectory for both the active tape and a pure-ether
reference, identifies the glider region, and produces the warp spacetime by
sampling each cell at its locally warped time index.

Because AFCA observables are global properties of the whole trajectory
rather than instantaneous fields, the engine exposes a `run` helper for
batch experiments alongside the standard step / snapshot interface.

APPROXIMATION SCOPE:
    This engine implements an ether-phase τ_c proxy, not true P41 M-bit inner-CA
    gating.

    In P41, each cell runs an M-bit inner Rule 110 CA until a majority vote
    reaches the target state; the outer cell updates only at that completion
    event.  In P45, the outer cell gates on a single inner-clock bit.  This
    engine approximates both with a precomputed ether-phase lookup table
    (tau_phase_table), which is exact on the ether background but departs from
    true inner-CA dynamics in matter / glider regions where the inner CA leaves
    the ether orbit.

    As a result:
      - τ_c values in matter regions are approximate ether-phase surrogates.
      - SR time-dilation ratios produced here are NOT directly comparable to P41
        quantitative results; use papers/41.../two_layer_chiral_afca_prototype.py
        for canonical P41 AFCA dynamics.
      - The warp-spacetime visualization is qualitatively correct for ether
        backgrounds; use it for exploratory visualization, not for physics-unit
        SR clock-rate measurements.
"""

from __future__ import annotations

import numpy as np

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)
from ugp_viz.engines.fca_sync import (
    apply_rule,
    build_tau_phase_table,
    ether_tape,
    make_rule_table,
)


class AFCA(SimEngine):

    model_name = "afca"
    spatial_dim = 1
    supported_ic_kinds = ("ether", "vacuum", "random", "load")
    default_params = {
        "rule": 110,
        "L": 500,
        "inner_M": 7,
        "warp_min": 0.5,
        "warp_max": 2.0,
        "glider_threshold": 0.05,
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
        self._spacetime_sync: list[np.ndarray] = []
        self._spacetime_tau: list[np.ndarray] = []
        self._spacetime_ref: list[np.ndarray] = []

    def _step_impl(self, n_steps: int) -> None:
        """Advance the AFCA by n_steps outer-CA ticks.

        The τ_c field is computed from an ether-phase lookup table, not from
        live inner-CA dynamics.  In glider / matter regions the inner CA departs
        from the ether orbit, so the τ_c values are approximations.  SR
        time-dilation ratios derived from these steps are not directly comparable
        to P41 canonical quantitative results.
        """
        rng = self._outer_rule_table
        for _ in range(n_steps):
            next_tape = apply_rule(self.tape, rng)
            self._last_tau = self._tau_phase[self._phases, next_tape.astype(np.int32)]
            self.tape = next_tape
            next_ref = apply_rule(self._ref_tape, rng)
            self._spacetime_sync.append(self.tape.copy())
            self._spacetime_tau.append(self._last_tau.copy())
            self._spacetime_ref.append(self._ref_tape.copy())
            self._ref_tape = next_ref
            self._step += 1
            self._time += 1.0

    def _build_warp_view(self) -> tuple[np.ndarray, np.ndarray]:
        """Construct the τ_c-warped spacetime view.

        The warp field is derived from the ether-phase τ_c proxy; it is an
        approximation in matter regions.  This view is suitable for qualitative
        visualization of clock-dilation structure, not for quantitative SR
        clock-rate comparisons against P41 numerical results.
        """
        if not self._spacetime_sync:
            L = int(self.params["L"])
            return (np.zeros((0, L), np.uint8), np.zeros(L, dtype=bool))
        outer_sync = np.stack(self._spacetime_sync, axis=0)
        ref_sync = np.stack(self._spacetime_ref, axis=0)
        tau_sync = np.stack(self._spacetime_tau, axis=0)
        diff_frac = (outer_sync != ref_sync).mean(axis=0)
        is_glider = diff_frac > float(self.params["glider_threshold"])
        tau_ether_mean = float(tau_sync[:, ~is_glider].mean()) if (~is_glider).any() else float(tau_sync.mean())
        tau_cell_mean = tau_sync.mean(axis=0)
        warp = np.ones(outer_sync.shape[1], dtype=np.float64)
        warp[is_glider] = tau_cell_mean[is_glider] / max(tau_ether_mean, 1e-6)
        warp = np.clip(warp, float(self.params["warp_min"]),
                       float(self.params["warp_max"]))
        steps = outer_sync.shape[0]
        afca = np.zeros_like(outer_sync)
        t_idx = np.arange(steps, dtype=np.float64)
        for i in range(outer_sync.shape[1]):
            local_ts = np.clip(
                np.round(t_idx / warp[i]).astype(np.int32), 0, steps - 1)
            afca[:, i] = outer_sync[local_ts, i]
        return afca, is_glider

    def get_spacetime(self) -> dict[str, np.ndarray]:
        """Return full spacetime arrays accumulated so far."""
        afca, is_glider = self._build_warp_view()
        return {
            "sync": (np.stack(self._spacetime_sync, axis=0)
                     if self._spacetime_sync else np.zeros((0, int(self.params["L"])), np.uint8)),
            "ref": (np.stack(self._spacetime_ref, axis=0)
                    if self._spacetime_ref else np.zeros((0, int(self.params["L"])), np.uint8)),
            "tau_c": (np.stack(self._spacetime_tau, axis=0)
                      if self._spacetime_tau else np.zeros((0, int(self.params["L"])), np.float32)),
            "afca": afca,
            "is_glider": is_glider,
        }

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
                "ref_density": float(self._ref_tape.mean()),
                "density": float(self.tape.mean()),
            },
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="ether")
        L = int(self.params["L"])
        if ic.kind in ("ether", "vacuum"):
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
        self._ref_tape = ether_tape(L)
        self._step = 0
        self._time = 0.0
        self._last_tau[:] = 0.0
        self._spacetime_sync.clear()
        self._spacetime_tau.clear()
        self._spacetime_ref.clear()

    def inject(self, spec: InjectionSpec) -> None:
        from ugp_viz.catalog.manager import load_entry
        from ugp_viz.engines.fca_sync import _coerce_seed

        entry = load_entry(self.model_name, spec.kind)
        seed = _coerce_seed(entry)
        L = int(self.params["L"])
        pos = spec.position
        if pos is None:
            pos = int(entry.get("default_position", L // 2))
        pos = int(pos)
        for j, b in enumerate(seed):
            self.tape[(pos + j) % L] = b
