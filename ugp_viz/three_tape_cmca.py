"""
ThreeTapeCMCA engine stub — wraps the canonical P45 implementation.

This module provides a thin SimEngine wrapper around the canonical P45
ThreeTapeCMCA class located at:

    papers/45_three_tape_cmca/scripts/three_tape_cmca.py

The P45 class implements the full three-tape CMCA with:
  - Three parallel 1+1D tapes (x, y, z) with three-layer chiral structure.
  - Shared global outer clock τ_c^out (Dimensional Protocol Principle, CatAL:
    dimensional_protocol_principle_master).
  - Gorard curvature calculator (CatAL: three_tape_gorard_vacuum_ricci_flat).
  - Gravity source, Bell test, and born-rule verification.

This stub does NOT duplicate the P45 code; it imports from the canonical
script.  If the papers/ directory is not present on the current installation,
the import fails with an actionable error message.

Engine registry name: "three_tape_cmca"
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)

# Canonical P45 script path (relative to the ugp-physics repo root)
_P45_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "papers" / "45_three_tape_cmca" / "scripts" / "three_tape_cmca.py"
)

_P45_CLASS: type | None = None
_P45_LOAD_ERROR: str | None = None


def _load_p45() -> type:
    """Import ThreeTapeCMCA from the canonical P45 script."""
    global _P45_CLASS, _P45_LOAD_ERROR
    if _P45_CLASS is not None:
        return _P45_CLASS
    if _P45_LOAD_ERROR is not None:
        raise ImportError(_P45_LOAD_ERROR)

    if not _P45_SCRIPT.exists():
        _P45_LOAD_ERROR = (
            f"Canonical P45 three_tape_cmca.py not found at:\n"
            f"  {_P45_SCRIPT}\n"
            "Ensure the papers/45_three_tape_cmca/scripts/ directory is present "
            "in the ugp-physics checkout.  The ThreeTapeCMCA engine requires the "
            "canonical P45 implementation; this stub does not duplicate its code."
        )
        raise ImportError(_P45_LOAD_ERROR)

    spec = importlib.util.spec_from_file_location("p45_three_tape_cmca", _P45_SCRIPT)
    if spec is None or spec.loader is None:
        _P45_LOAD_ERROR = f"Could not load module spec from {_P45_SCRIPT}"
        raise ImportError(_P45_LOAD_ERROR)

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:
        _P45_LOAD_ERROR = f"Error loading P45 three_tape_cmca.py: {exc}"
        raise ImportError(_P45_LOAD_ERROR) from exc

    cls = getattr(module, "ThreeTapeCMCA", None)
    if cls is None:
        _P45_LOAD_ERROR = (
            f"ThreeTapeCMCA class not found in {_P45_SCRIPT}.  "
            "The P45 script may have been refactored; update this stub accordingly."
        )
        raise ImportError(_P45_LOAD_ERROR)

    _P45_CLASS = cls
    return cls


class ThreeTapeCMCAEngine(SimEngine):
    """
    SimEngine wrapper for the canonical P45 ThreeTapeCMCA.

    Wraps papers/45_three_tape_cmca/scripts/three_tape_cmca.py.
    All quantitative results (Gorard curvature, DPP coupling, gravity source,
    Bell test) are delegated to the canonical P45 implementation unchanged.

    Engine registry name: "three_tape_cmca"

    NOTE: This engine is suitable for reproducing P45 canonical results.
    It is NOT a reimplementation — it is a thin dispatch layer.
    """

    model_name = "three_tape_cmca"
    spatial_dim = 1
    default_params: dict[str, Any] = {
        "L": 128,
        "native_geodesic": True,
    }

    def _setup(self) -> None:
        cls = _load_p45()
        L = int(self.params["L"])
        native_geodesic = bool(self.params.get("native_geodesic", True))
        self._p45 = cls(L=L, native_geodesic=native_geodesic)

    def _step_impl(self, n_steps: int) -> None:
        for _ in range(n_steps):
            self._p45.step()
            self._step += 1
            self._time += 1.0

    def snapshot(self) -> FieldSnapshot:
        p45 = self._p45
        # Extract x-tape outer_plus state as the primary tape for visualization.
        tape = p45.tapes["x"]["outer_plus"].astype("uint8")
        return FieldSnapshot(
            step=self._step,
            time=self._time,
            model=self.model_name,
            tape=tape,
            extra={
                "L": int(self.params["L"]),
                "gorard_curvature": float(p45.gorard_curvature("x").mean())
                if hasattr(p45, "gorard_curvature") else None,
            },
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="ether")
        self._p45.reset()
        self._step = 0
        self._time = 0.0

    def inject(self, spec: InjectionSpec) -> None:
        from ugp_viz.catalog.manager import load_entry
        entry = load_entry(self.model_name, spec.kind)
        seed = entry.get("seed", [])
        if not seed:
            return
        pos = int(spec.position or entry.get("default_position", 0))
        L = int(self.params["L"])
        for tape_name in ("x", "y", "z"):
            tape = self._p45.tapes[tape_name]["outer_plus"]
            for j, val in enumerate(seed):
                tape[(pos + j) % L] = int(val)
