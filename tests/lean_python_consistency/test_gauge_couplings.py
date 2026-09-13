"""
tests/lean_python_consistency/test_gauge_couplings.py

Verify that bare gauge couplings in ugp_core.py match the Lean-certified
exact rationals (Phase4.GaugeCouplings).

ugp_core.py uses attribute names G1_SQ / G2_SQ / G3_SQ.
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction

import mpmath as mp
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "papers", "24_deeper_theory"))

from ugp_lean_canon.canonical_values import PRIMITIVES  # noqa: E402
import ugp_core  # noqa: E402

mp.mp.dps = 60


# ── Rational invariance ──────────────────────────────────────────────────────

def test_G1_SQ_is_fraction():
    """g1Sq_bare must be stored as an exact Fraction."""
    assert isinstance(ugp_core.G1_SQ, Fraction), (
        f"G1_SQ must be a Fraction, got {type(ugp_core.G1_SQ)}"
    )


def test_G2_SQ_is_fraction():
    assert isinstance(ugp_core.G2_SQ, Fraction)


def test_G3_SQ_is_fraction():
    assert isinstance(ugp_core.G3_SQ, Fraction)


# ── Exact values match Lean theorem literals ─────────────────────────────────

def test_G1_SQ_exact():
    """Lean: g1Sq_bare_eq  →  16/125."""
    canon = PRIMITIVES["g1Sq_bare"][0]
    assert ugp_core.G1_SQ == canon, (
        f"G1_SQ = {ugp_core.G1_SQ} != Lean canonical {canon}"
    )


def test_G2_SQ_exact():
    """Lean: g2Sq_bare_eq  →  2329/5400."""
    canon = PRIMITIVES["g2Sq_bare"][0]
    assert ugp_core.G2_SQ == canon


def test_G3_SQ_exact():
    """Lean: g3Sq_bare_eq  →  41075281/27648000."""
    canon = PRIMITIVES["g3Sq_bare"][0]
    assert ugp_core.G3_SQ == canon, (
        f"G3_SQ = {ugp_core.G3_SQ} != Lean canonical {canon}\n"
        "Note: g3Sq = 41075281/27648000 = (13*17*29)^2/27648000."
    )
