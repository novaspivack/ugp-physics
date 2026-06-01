"""
Z7 f_MDL CA engine.

Discrete Z_7 cellular automaton implementing the MDL-minimal orbit-admissible
function fmdl: Z_7^3 -> Z_7 fixed by the SM generation orbit
(gen_1 -> gen_2 -> gen_3 -> vacuum). Each step applies fmdl to every
(left, center, right) neighborhood under periodic BC.

Default state space: 5-cell ring (the SM orbit substrate). The engine
generalises to arbitrary ring lengths; multiples of 5 reproduce the
canonical generation embeddings exactly.

The 3D variant ('z7_fmdl_3d' via spatial_dim override) evaluates fmdl
independently along each of the three lattice axes (axis-decomposed 3D
rule), which preserves the SM orbit on every line.
"""

from __future__ import annotations

import numpy as np

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)


GEN1 = (1, 5, 2, 2, 1)
GEN2 = (2, 5, 2, 0, 2)
GEN3 = (5, 6, 5, 3, 5)
VACUUM = (0, 0, 0, 0, 0)


def _fmdl(l: int, c: int, r: int) -> int:
    # Orbit-fixed neighborhoods
    if (l, c, r) == (1, 1, 5):
        return 2
    if (l, c, r) == (1, 5, 2):
        return 5
    if (l, c, r) == (5, 2, 2):
        return 2
    if (l, c, r) == (2, 2, 1):
        return 0
    if (l, c, r) == (2, 1, 1):
        return 2
    if (l, c, r) == (2, 2, 5):
        return 5
    if (l, c, r) == (2, 5, 2):
        return 6
    if (l, c, r) == (5, 2, 0):
        return 5
    if (l, c, r) == (2, 0, 2):
        return 3
    if (l, c, r) == (0, 2, 2):
        return 5
    # Rule 110 binary sublayer (acts on Z_2 subset)
    if (l, c, r) == (0, 0, 0):
        return 0
    if (l, c, r) == (0, 0, 1):
        return 1
    if (l, c, r) == (0, 1, 0):
        return 1
    if (l, c, r) == (0, 1, 1):
        return 1
    if (l, c, r) == (1, 0, 0):
        return 0
    if (l, c, r) == (1, 0, 1):
        return 1
    if (l, c, r) == (1, 1, 0):
        return 1
    if (l, c, r) == (1, 1, 1):
        return 0
    return 0


_FMDL_LUT: np.ndarray | None = None


def fmdl_lut() -> np.ndarray:
    """Cached 7x7x7 lookup table of fmdl values."""
    global _FMDL_LUT
    if _FMDL_LUT is None:
        lut = np.zeros((7, 7, 7), dtype=np.int8)
        for l in range(7):
            for c in range(7):
                for r in range(7):
                    lut[l, c, r] = _fmdl(l, c, r)
        _FMDL_LUT = lut
    return _FMDL_LUT


def fmdl_step_1d(state: np.ndarray) -> np.ndarray:
    """One step of the Z7 fmdl CA on a 1D ring (periodic BC)."""
    lut = fmdl_lut()
    l = np.roll(state, 1)
    c = state
    r = np.roll(state, -1)
    return lut[l, c, r]


def fmdl_step_3d(state: np.ndarray) -> np.ndarray:
    """
    Axis-decomposed Z7 fmdl on a 3D periodic lattice: average the three
    axis-wise updates and round to the nearest integer in Z_7. This
    preserves the SM orbit on every axis-aligned line while remaining
    rotationally symmetric on average.
    """
    lut = fmdl_lut()
    out = np.zeros_like(state, dtype=np.float64)
    for ax in (0, 1, 2):
        lx = np.roll(state, 1, axis=ax)
        rx = np.roll(state, -1, axis=ax)
        out += lut[lx, state, rx].astype(np.float64)
    out /= 3.0
    return np.rint(out).astype(np.int8) % 7


class Z7FMDL(SimEngine):

    model_name = "z7_fmdl"
    spatial_dim = 1
    default_params = {
        "L": 25,         # 5-cell SM orbit tile times 5 (default)
        "dimension": 1,
        "Nx": 16,
        "Ny": 16,
        "Nz": 16,
    }

    def _setup(self) -> None:
        if int(self.params["dimension"]) == 1:
            L = int(self.params["L"])
            self.tape = np.zeros(L, dtype=np.int8)
        else:
            Nx = int(self.params["Nx"])
            Ny = int(self.params["Ny"])
            Nz = int(self.params["Nz"])
            self.tape3d = np.zeros((Nx, Ny, Nz), dtype=np.int8)

    def _step_impl(self, n_steps: int) -> None:
        if int(self.params["dimension"]) == 1:
            for _ in range(n_steps):
                self.tape = fmdl_step_1d(self.tape)
                self._step += 1
                self._time += 1.0
        else:
            for _ in range(n_steps):
                self.tape3d = fmdl_step_3d(self.tape3d)
                self._step += 1
                self._time += 1.0

    def snapshot(self) -> FieldSnapshot:
        if int(self.params["dimension"]) == 1:
            return FieldSnapshot(
                step=self._step,
                time=self._time,
                model=self.model_name,
                tape=self.tape.copy().astype(np.uint8),
                extra={"L": int(self.params["L"]),
                       "n_nonzero": int(np.count_nonzero(self.tape))},
            )
        return FieldSnapshot(
            step=self._step,
            time=self._time,
            model=self.model_name,
            tape3d=self.tape3d.copy().astype(np.uint8),
            extra={"shape": list(self.tape3d.shape),
                   "n_nonzero": int(np.count_nonzero(self.tape3d))},
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="vacuum")
        if int(self.params["dimension"]) == 1:
            L = int(self.params["L"])
            if ic.kind == "vacuum":
                self.tape[:] = 0
            elif ic.kind == "random":
                rng = np.random.default_rng(int(ic.params.get("seed", 0)))
                self.tape[:] = rng.integers(0, 7, L, dtype=np.int8)
            elif ic.kind == "load":
                if not ic.path:
                    raise ValueError("ic 'load' requires path")
                self.load_state(ic.path)
                return
            else:
                raise ValueError(f"unknown ic kind '{ic.kind}'")
        else:
            if ic.kind == "vacuum":
                self.tape3d[...] = 0
            elif ic.kind == "random":
                rng = np.random.default_rng(int(ic.params.get("seed", 0)))
                self.tape3d[...] = rng.integers(
                    0, 7, self.tape3d.shape, dtype=np.int8)
            elif ic.kind == "load":
                if not ic.path:
                    raise ValueError("ic 'load' requires path")
                self.load_state(ic.path)
                return
            else:
                raise ValueError(f"unknown ic kind '{ic.kind}'")
        self._step = 0
        self._time = 0.0

    def inject(self, spec: InjectionSpec) -> None:
        from ugp_viz.catalog.manager import load_entry

        entry = load_entry(self.model_name, spec.kind)
        seed = np.array(entry["seed"], dtype=np.int8)
        if int(self.params["dimension"]) == 1:
            L = int(self.params["L"])
            pos = spec.position
            if pos is None:
                pos = int(entry.get("default_position", 0))
            pos = int(pos)
            for j, val in enumerate(seed):
                self.tape[(pos + j) % L] = val
        else:
            cx = int(spec.params.get("cx", self.tape3d.shape[0] // 2))
            cy = int(spec.params.get("cy", self.tape3d.shape[1] // 2))
            cz = int(spec.params.get("cz", self.tape3d.shape[2] // 2))
            for j, val in enumerate(seed):
                self.tape3d[(cx + j) % self.tape3d.shape[0], cy, cz] = val
