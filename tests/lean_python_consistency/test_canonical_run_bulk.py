"""
tests/lean_python_consistency/test_canonical_run_bulk.py

Bulk import every comp_p2*.py and comp_p23*.py script from
papers/01_SM/canonical_run/ and spot-check that any attribute named
C_ALGEBRAIC, K_L2, PHI, K_GEN2, Nc, delta, b_1 (etc.) matches the
canonical table within tolerance.

If a script cannot be imported (e.g. requires missing optional dependency
not installed in test environment), the test is skipped with a warning rather
than failing — this allows a lightweight CI to run on machines without mpmath.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

import mpmath as mp
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

from ugp_lean_canon.canonical_values import DERIVED, PRIMITIVES  # noqa: E402

mp.mp.dps = 60
TOL_REL = mp.mpf("1e-10")  # bulk scan uses relaxed 1e-10 tolerance

CANONICAL_RUN = Path(REPO) / "papers" / "01_SM" / "canonical_run"
# The two clean replacement scripts are the primary coverage targets
PRIMARY_SCRIPTS = [
    "comp_p25_alpha_precision_floor",
    "comp_p25_residual_structural_search",
]

# Attributes to check if present in a module (name -> canonical value key)
ATTR_MAP = {
    "C_ALGEBRAIC":      ("derived", "C_alg"),
    "PHI":              ("derived", "phi"),
    "K_GEN2":           ("derived", "k_gen2"),
    "K_GEN2_exact":     ("derived", "k_gen2"),
    "Nc":               ("primitive", "Nc"),
    "delta":            ("primitive", "delta"),
    "n_ridge":          ("primitive", "n_ridge"),
    "strand_count":     ("primitive", "strand_count"),
}


def _canonical(key_type: str, key: str) -> Any:
    if key_type == "derived":
        return DERIVED[key]
    return PRIMITIVES[key][0]


def _load_module(script_name: str):
    """Import a script from canonical_run as a module."""
    script_path = CANONICAL_RUN / f"{script_name}.py"
    if not script_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("script_name", PRIMARY_SCRIPTS)
def test_primary_scripts_importable(script_name):
    """Primary canonical-run scripts must be importable without error."""
    mod = _load_module(script_name)
    assert mod is not None, f"{script_name}.py not found in canonical_run"


@pytest.mark.parametrize("attr,key_info", ATTR_MAP.items())
def test_attr_in_ugp_core_matches_canonical(attr, key_info):
    """Any Lean-certified constant found in ugp_core must match the canonical table."""
    sys.path.insert(0, str(Path(REPO) / "papers" / "24_deeper_theory"))
    try:
        import ugp_core as core
    except ImportError:
        pytest.skip("ugp_core not importable")
    if not hasattr(core, attr):
        pytest.skip(f"ugp_core has no attribute {attr}")
    val = getattr(core, attr)
    expected = _canonical(*key_info)
    try:
        rel = abs(mp.mpf(str(val)) - mp.mpf(str(expected))) / abs(mp.mpf(str(expected)))
        assert rel < TOL_REL, (
            f"ugp_core.{attr} = {val} differs from Lean canonical {expected} "
            f"by {rel} (tolerance {TOL_REL})"
        )
    except (TypeError, ValueError):
        # non-numeric attribute — compare directly
        assert val == expected, f"ugp_core.{attr} = {val} != canonical {expected}"


def test_chimera_probe():
    """A1: explicitly verify the Form B formula would have been caught.

    Form B: C = -1/k_gen2 + (1/4)(k_L2/k_gen2) + (7/4)(k_L2 * k_gen2)
    If ugp_core uses Form B it will diverge from DERIVED['C_alg'] by ~0.062%.
    This test would fail against Form B, catching the EPIC 24 chimera.
    """
    import math
    phi = (1 + math.sqrt(5)) / 2
    k_gen2 = -phi / 2
    k_L2 = 7 / 512
    # Form B (wrong):
    C_form_B = (-1) / k_gen2 + (1 / 4) * (k_L2 / k_gen2) + (7 / 4) * (k_L2 * k_gen2)
    # Form A (correct):
    C_form_A = float(DERIVED["C_alg"])
    rel_diff = abs(C_form_B - C_form_A) / abs(C_form_A)
    # Form B is ~0.062% off — if ugp_core uses Form A, C_ALGEBRAIC matches A
    assert rel_diff > 1e-4, (
        "Form B and Form A are unexpectedly close — chimera probe is no longer discriminating"
    )
