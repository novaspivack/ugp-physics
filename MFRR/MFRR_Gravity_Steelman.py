"""Thin entrypoint: monograph Part V cites this path at MFRR root."""

from pathlib import Path

import runpy

_IMPL = (
    Path(__file__).resolve().parent
    / "TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/STEELMAN_V3/MFRR_Gravity_Steelman.py"
)
if not _IMPL.is_file():
    raise FileNotFoundError(f"Missing steel-man implementation: {_IMPL}")
runpy.run_path(str(_IMPL), run_name="__main__")
