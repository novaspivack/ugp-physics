"""
tests/lean_python_consistency/test_ugp_core.py

Verify that papers/24_deeper_theory/ugp_core.py uses Lean-authoritative
formulas and reproduces every Lean-certified canonical value within 1e-15
relative tolerance (10^-15 < epsilon of 60-digit mpmath).

Acceptance criteria (per SPEC_028_LXC):
  A1 — catches the EPIC 24 Round 8 chimera bug (Form B C_alg would fail
       test_C_algebraic_matches_lean)
  A2 — passes against current ugp_core.py (Form A, post-fix)
  A4 — runs in < 10 s
"""
from __future__ import annotations

import os
import sys

import mpmath as mp
import pytest

# Locate ugp_core relative to repo root regardless of CWD
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "papers", "24_deeper_theory"))

from ugp_lean_canon.canonical_values import DERIVED, PRIMITIVES  # noqa: E402
import ugp_core  # noqa: E402

mp.mp.dps = 60
TOL = mp.mpf("1e-15")  # 60-digit precision; allow last-bit float roundoff


def _rel(a: float, b: mp.mpf) -> mp.mpf:
    return abs(mp.mpf(str(a)) - mp.mpf(b)) / abs(mp.mpf(b))


# ── Core formula consistency ─────────────────────────────────────────────────

def test_C_algebraic_matches_lean():
    """A1: catches Form B chimera.  C_ALGEBRAIC must match Lean Form A to 1e-15."""
    assert _rel(ugp_core.C_ALGEBRAIC, DERIVED["C_alg"]) < TOL, (
        f"C_ALGEBRAIC = {ugp_core.C_ALGEBRAIC} differs from Lean Form A "
        f"{mp.nstr(DERIVED['C_alg'], 20)} by {_rel(ugp_core.C_ALGEBRAIC, DERIVED['C_alg'])}\n"
        "This may indicate a formula mismatch between ugp_core.py and "
        "UgpLean/Phase4/DeltaUGP.lean line 35."
    )


def test_phi_matches():
    assert _rel(ugp_core.PHI, DERIVED["phi"]) < TOL


def test_k_gen2_matches():
    assert _rel(ugp_core.K_GEN2_exact, DERIVED["k_gen2"]) < TOL


def test_k_L2_matches():
    assert _rel(float(ugp_core.K_L2), DERIVED["k_L2"]) < TOL


# ── Integer primitive consistency ────────────────────────────────────────────

def test_Nc():
    assert ugp_core.Nc == PRIMITIVES["Nc"][0]


def test_delta():
    assert ugp_core.delta == PRIMITIVES["delta"][0]


def test_n_ridge():
    assert ugp_core.n_ridge == PRIMITIVES["n_ridge"][0]


def test_strand_count():
    assert ugp_core.strand_count == PRIMITIVES["strand_count"][0]


# ── Derived quantity sanity ──────────────────────────────────────────────────

def test_b1_required_within_5ppm_of_73():
    """b1_required must be 73 within ≤ 5 ppm.  Real residual is 2.39 ppm."""
    rel = abs(mp.mpf(str(ugp_core.B1_REQUIRED)) - 73) / 73
    assert rel < mp.mpf("5e-6"), (
        f"B1_REQUIRED = {ugp_core.B1_REQUIRED} differs from 73 by {rel} "
        "(expected ≤ 5 ppm; real residual is 2.39 ppm)"
    )


def test_b1_required_matches_C_over_delta_target():
    """B1_REQUIRED == C_ALGEBRAIC / DELTA_TARGET (self-consistency)."""
    expected = ugp_core.C_ALGEBRAIC / ugp_core.DELTA_TARGET
    rel = abs(mp.mpf(str(ugp_core.B1_REQUIRED)) - mp.mpf(str(expected))) / mp.mpf(str(expected))
    assert rel < TOL


def test_delta_UGP_at_73_matches():
    """delta_UGP(73) = C_alg / 73."""
    if hasattr(ugp_core, "DELTA_UGP_AT_73"):
        assert _rel(ugp_core.DELTA_UGP_AT_73, DERIVED["delta_UGP_at_73"]) < TOL
    else:
        # Check indirectly via C_ALGEBRAIC
        derived = ugp_core.C_ALGEBRAIC / 73
        assert _rel(derived, DERIVED["delta_UGP_at_73"]) < TOL
