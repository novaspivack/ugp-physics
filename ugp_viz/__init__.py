"""
UGP Visualization Lab (VIZLAB)

Unified interactive environment for running, visualizing, and exploring GTE
simulations: Phi_MDL (Z7-KG kink field, 1D and 3D), f_MDL CA (sync CA, AFCA),
Z7 f_MDL orbit CA, and Z7-KG wave packets.

Modules
-------
engines      : Physics engines (one per model) implementing the SimEngine interface.
catalog      : Kink / glider / orbit catalog (JSON-backed library of canonical configs).
viz          : Matplotlib figure routines + MP4 video export.
experiments  : YAML batch experiment runner and cross-run comparison.
cli          : `ugpviz` command-line interface entry point.
app          : Taichi GGUI real-time application entry point.

Usage
-----
    python -m ugp_viz.cli run --model phimdl_1d --inject gen1_kink@256 --steps 5000
    python -m ugp_viz.app          # launches GUI
"""

__version__ = "0.1.0"

from ugp_viz.engines.base import (
    SimEngine,
    FieldSnapshot,
    InjectionSpec,
    InitialCondition,
    KnownModels,
)
from ugp_viz.engines.registry import build_engine, list_models

__all__ = [
    "SimEngine",
    "FieldSnapshot",
    "InjectionSpec",
    "InitialCondition",
    "KnownModels",
    "build_engine",
    "list_models",
]
