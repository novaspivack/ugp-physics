"""
Unified SimEngine interface for all VIZLAB physics models.

Every model (Phi_MDL 1D/3D, sync FCA, AFCA, Z7 f_MDL, Z7-KG) implements the
same public surface so the GUI, CLI, and experiment runner can treat them
interchangeably. Fields, parameters, injections, and snapshots are described
by lightweight dataclasses to keep serialization (JSON, YAML) trivial.

The base class itself is abstract: it specifies the contract, supplies
defaults for trivial methods, and centralizes parameter validation.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Mapping

import numpy as np


KnownModels = (
    "phimdl_1d",
    "phimdl_3d",
    "fca_sync",
    "afca",
    "z7_fmdl",
    "z7_kg",
)


@dataclass
class FieldSnapshot:
    """
    Self-describing snapshot of the simulation state at a single time slice.

    Continuous-field models (Phi_MDL, Z7-KG) populate `phi` and optionally
    `chi`. Discrete CA models (FCA sync, AFCA, Z7 f_MDL) populate `tape` for
    1D or `tape3d` for higher-dimensional grids. The `tau_c` field is the
    local clock-rate observable (inner-CA steps per outer step) for AFCA-type
    models; for continuum models it is the τ_c proxy from the phase table.
    """

    step: int
    time: float
    model: str
    phi: np.ndarray | None = None
    chi: np.ndarray | None = None
    tape: np.ndarray | None = None
    tape3d: np.ndarray | None = None
    tau_c: np.ndarray | None = None
    energy_density: np.ndarray | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def asdict_lite(self) -> dict[str, Any]:
        """Lightweight dict for JSON (omits ndarrays)."""
        out = {"step": self.step, "time": self.time, "model": self.model}
        out.update({k: v for k, v in self.extra.items() if _json_safe(v)})
        return out


@dataclass
class InjectionSpec:
    """
    Description of a kink / glider / perturbation to inject into the field.

    `kind` is a catalog key (e.g. "gen1_kink", "canonical_glider"). `position`
    and `velocity` are optional overrides; if not given the catalog defaults
    apply. `params` is a free-form mapping for catalog-specific knobs (mass,
    width, phase, charge).
    """

    kind: str
    position: float | tuple[float, ...] | None = None
    velocity: float | tuple[float, ...] | None = None
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_string(cls, spec: str) -> "InjectionSpec":
        """
        Parse a compact CLI spec like 'gen1_kink@256' or 'meson@250,v=0.3'.

        Format: kind[@pos[,key=val[,key=val...]]]
        """
        if "@" in spec:
            kind, rest = spec.split("@", 1)
        else:
            kind, rest = spec, ""
        position: float | tuple[float, ...] | None = None
        velocity: float | tuple[float, ...] | None = None
        params: dict[str, Any] = {}
        if rest:
            parts = rest.split(",")
            try:
                position = float(parts[0])
            except ValueError as exc:
                raise ValueError(
                    f"injection position '{parts[0]}' is not a number"
                ) from exc
            for kv in parts[1:]:
                if "=" not in kv:
                    raise ValueError(
                        f"injection param '{kv}' must have form key=value"
                    )
                key, val = kv.split("=", 1)
                if key == "v":
                    velocity = float(val)
                else:
                    params[key] = _coerce_scalar(val)
        return cls(kind=kind.strip(), position=position, velocity=velocity,
                   params=params)

    def asdict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "position": self.position,
            "velocity": self.velocity,
            "params": dict(self.params),
        }


@dataclass
class InitialCondition:
    """
    Description of the field's initial state. `kind` is either 'vacuum',
    'ether', 'random' or 'load'. For 'load', `path` points to a saved state.
    """

    kind: str = "vacuum"
    path: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


def _coerce_scalar(val: str) -> Any:
    val = val.strip()
    try:
        if "." in val or "e" in val.lower():
            return float(val)
        return int(val)
    except ValueError:
        return val


def _json_safe(v: Any) -> bool:
    return isinstance(v, (str, int, float, bool, type(None), list, tuple, dict))


class SimEngine(ABC):
    """
    Abstract base class. Subclasses must implement the simulation primitives
    `_step_impl`, `snapshot`, `inject`, and `reset`. `model_name` and
    `default_params` are declared as class attributes so the registry can
    introspect models without instantiating them.
    """

    model_name: ClassVar[str] = "abstract"
    default_params: ClassVar[Mapping[str, Any]] = {}
    spatial_dim: ClassVar[int] = 1
    # Initial-condition kinds recognized by reset(). Subclasses override.
    supported_ic_kinds: ClassVar[tuple[str, ...]] = ("vacuum", "random", "load")

    def __init__(self, params: Mapping[str, Any] | None = None):
        merged: dict[str, Any] = dict(self.default_params)
        if params:
            for key, val in params.items():
                if key not in merged:
                    raise KeyError(
                        f"{self.model_name}: unknown parameter '{key}'. "
                        f"Known: {sorted(merged)}"
                    )
                merged[key] = val
        self.params: dict[str, Any] = merged
        self._step: int = 0
        self._time: float = 0.0
        self._setup()

    @abstractmethod
    def _setup(self) -> None:
        """Allocate fields and apply the default initial condition."""

    @abstractmethod
    def _step_impl(self, n_steps: int) -> None:
        """Advance the simulation by `n_steps` discrete steps."""

    @abstractmethod
    def snapshot(self) -> FieldSnapshot:
        """Return a snapshot of the current state."""

    @abstractmethod
    def inject(self, spec: InjectionSpec) -> None:
        """Inject a catalog kink / glider into the field."""

    @abstractmethod
    def reset(self, ic: InitialCondition | None = None) -> None:
        """Reset to a fresh initial condition."""

    def step(self, n_steps: int = 1) -> None:
        if n_steps <= 0:
            return
        self._step_impl(n_steps)

    @property
    def step_count(self) -> int:
        return self._step

    @property
    def sim_time(self) -> float:
        return self._time

    def get_tau_c(self) -> np.ndarray | None:
        """Optional: return current τ_c array."""
        snap = self.snapshot()
        return snap.tau_c

    def get_energy(self) -> float:
        """Optional: return total energy. Subclasses may override."""
        snap = self.snapshot()
        if snap.energy_density is not None:
            return float(snap.energy_density.sum())
        return float("nan")

    def save_state(self, path: str | Path) -> None:
        """Save state as compressed NumPy archive + JSON metadata.

        Writes ``<path>.npz`` and ``<path>.json`` literally — the suffixes
        are appended to ``path`` rather than substituted. Pass a path
        without an extension when bundling alongside other artifacts.
        """
        p = Path(path)
        snap = self.snapshot()
        np_payload = {}
        for name in ("phi", "chi", "tape", "tape3d", "tau_c", "energy_density"):
            arr = getattr(snap, name, None)
            if arr is not None:
                np_payload[name] = np.asarray(arr)
        npz_path = p.with_name(p.name + ".npz")
        json_path = p.with_name(p.name + ".json")
        np.savez_compressed(npz_path, **np_payload)
        meta = {
            "model": self.model_name,
            "step": int(self._step),
            "time": float(self._time),
            "params": _json_serializable(self.params),
            "extra": _json_serializable(snap.extra),
        }
        json_path.write_text(json.dumps(meta, indent=2))

    def load_state(self, path: str | Path) -> None:
        """Inverse of save_state. Subclasses may override for richer support."""
        p = Path(path)
        npz_path = p.with_name(p.name + ".npz")
        json_path = p.with_name(p.name + ".json")
        npz = np.load(npz_path)
        meta = json.loads(json_path.read_text())
        if meta["model"] != self.model_name:
            raise ValueError(
                f"saved model '{meta['model']}' != engine '{self.model_name}'"
            )
        self._step = int(meta["step"])
        self._time = float(meta["time"])
        self._apply_loaded_arrays({k: npz[k] for k in npz.files})

    def _apply_loaded_arrays(self, arrays: dict[str, np.ndarray]) -> None:
        """Default implementation assigns to engine attributes if present."""
        for name, arr in arrays.items():
            if hasattr(self, name):
                setattr(self, name, arr)


def _json_serializable(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, dict):
        return {str(k): _json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_serializable(v) for v in obj]
    return obj


def asdict_safe(obj: Any) -> dict[str, Any]:
    """asdict that survives numpy scalars in dataclasses."""
    return _json_serializable(asdict(obj))
