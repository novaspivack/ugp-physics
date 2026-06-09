"""
Engine registry.

Models are registered lazily (imported on demand) so that touching the
registry does not pull every backend (Taichi, scipy, matplotlib) into
memory.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from ugp_viz.engines.base import KnownModels, SimEngine


_LOADERS: dict[str, Callable[[], type[SimEngine]]] = {}


def register(model_name: str, loader: Callable[[], type[SimEngine]]) -> None:
    _LOADERS[model_name] = loader


def _register_defaults() -> None:
    def _load_phimdl_1d() -> type[SimEngine]:
        from ugp_viz.engines.phimdl_1d import PhiMDL1D
        return PhiMDL1D

    def _load_phimdl_3d() -> type[SimEngine]:
        from ugp_viz.engines.phimdl_3d import PhiMDL3D
        return PhiMDL3D

    def _load_fca_sync() -> type[SimEngine]:
        from ugp_viz.engines.fca_sync import FCASync
        return FCASync

    def _load_afca() -> type[SimEngine]:
        from ugp_viz.engines.afca import AFCA
        return AFCA

    def _load_z7_fmdl() -> type[SimEngine]:
        from ugp_viz.engines.z7_fmdl import Z7FMDL
        return Z7FMDL

    def _load_z7_kg() -> type[SimEngine]:
        from ugp_viz.engines.z7_kg import Z7KG
        return Z7KG

    register("phimdl_1d", _load_phimdl_1d)
    register("phimdl_3d", _load_phimdl_3d)
    register("fca_sync", _load_fca_sync)
    register("afca", _load_afca)
    register("z7_fmdl", _load_z7_fmdl)
    register("z7_kg", _load_z7_kg)


_register_defaults()


def list_models() -> list[str]:
    return list(KnownModels)


def build_engine(model: str, params: Mapping[str, Any] | None = None) -> SimEngine:
    if model not in _LOADERS:
        raise KeyError(
            f"unknown model '{model}'. Known: {sorted(_LOADERS)}"
        )
    cls = _LOADERS[model]()
    return cls(params=params)


def model_defaults(model: str) -> dict[str, Any]:
    if model not in _LOADERS:
        raise KeyError(f"unknown model '{model}'")
    cls = _LOADERS[model]()
    return dict(cls.default_params)
