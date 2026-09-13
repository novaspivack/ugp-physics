"""
Numerical utilities for verifying PSC-induced Kähler structures.

This module supports Moonshot 1 (PSC Completeness).  It provides helpers to
load metric bundles, derive complex structures, and verify the key Kähler
conditions numerically.  The functions are designed to operate on data exported
from PR-0/PR-1 simulations or synthetic test fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


def load_metric_bundle(path: str | Path) -> Dict[str, np.ndarray]:
    """
    Load a metric bundle from JSON.

    The JSON file must contain three top-level keys:
        - "metric": symmetric positive-definite matrix (list of lists).
        - "symplectic": antisymmetric matrix representing the 2-form ω.
        - "complex_structure" (optional): J matrix. If absent, it will be
          computed using `compute_complex_structure`.
    """
    file_path = Path(path).expanduser().resolve()
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    metric = np.array(payload["metric"], dtype=float)
    symplectic = np.array(payload["symplectic"], dtype=float)
    if "complex_structure" in payload:
        complex_structure = np.array(payload["complex_structure"], dtype=float)
    else:
        complex_structure = compute_complex_structure(metric, symplectic)

    return {
        "metric": metric,
        "symplectic": symplectic,
        "complex_structure": complex_structure,
    }


def compute_complex_structure(metric: np.ndarray, symplectic: np.ndarray) -> np.ndarray:
    """
    Given a Riemannian metric g and symplectic form ω, compute the complex structure J.

    Uses the relation g(Ju, v) = ω(u, v), which implies g · J = ω.
    """
    metric = np.asarray(metric, dtype=float)
    symplectic = np.asarray(symplectic, dtype=float)
    if metric.shape != symplectic.shape:
        raise ValueError("Metric and symplectic form must share the same shape.")

    if not np.allclose(metric, metric.T, atol=1e-10):
        raise ValueError("Metric must be symmetric.")

    return np.linalg.solve(metric, symplectic)


def verify_kaehler_conditions(
    metric: np.ndarray,
    symplectic: np.ndarray,
    complex_structure: np.ndarray,
    atol: float = 1e-8,
) -> Dict[str, bool]:
    """
    Check standard Kähler conditions numerically.

    Returns dictionary with boolean results for:
        - symmetric_metric
        - positive_definite_metric
        - symplectic_antisymmetric
        - kaehler_compatibility (g(Ju,Jv)=g(u,v))
        - complex_structure_squared (-I)
        - symplectic_from_metric (g·J=ω)
    """
    g = np.asarray(metric, dtype=float)
    omega = np.asarray(symplectic, dtype=float)
    j = np.asarray(complex_structure, dtype=float)

    symmetric_metric = np.allclose(g, g.T, atol=atol)

    try:
        eigenvalues = np.linalg.eigvalsh(g)
        positive_definite = bool(np.all(eigenvalues > 0))
    except np.linalg.LinAlgError:
        positive_definite = False

    symplectic_antisymmetric = np.allclose(omega, -omega.T, atol=atol)

    # Compatibility: g(Ju, Jv) = g(u, v) ⇒ Jᵀ g J = g
    kaehler_compatibility = np.allclose(j.T @ g @ j, g, atol=atol)

    complex_structure_squared = np.allclose(j @ j, -np.eye(j.shape[0]), atol=atol)

    symplectic_from_metric = np.allclose(g @ j, omega, atol=atol)

    return {
        "symmetric_metric": symmetric_metric,
        "positive_definite_metric": positive_definite,
        "symplectic_antisymmetric": symplectic_antisymmetric,
        "kaehler_compatibility": kaehler_compatibility,
        "complex_structure_squared": complex_structure_squared,
        "symplectic_from_metric": symplectic_from_metric,
    }


def summarize_checks(results: Dict[str, bool]) -> str:
    """
    Format verification results for CLI output.
    """
    lines = ["Kähler verification results:"]
    for name, value in results.items():
        status = "PASS" if value else "FAIL"
        lines.append(f"  - {name}: {status}")
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Verify Kähler structure from JSON bundle.")
    parser.add_argument("bundle", help="Path to JSON file containing metric, symplectic, (optional) complex structure.")
    parser.add_argument("--atol", type=float, default=1e-8, help="Numerical tolerance for checks.")
    args = parser.parse_args()

    bundle = load_metric_bundle(args.bundle)
    # Ensure complex structure is consistent with metric/symplectic if recomputation desired
    complex_structure = compute_complex_structure(bundle["metric"], bundle["symplectic"])

    results = verify_kaehler_conditions(
        bundle["metric"],
        bundle["symplectic"],
        complex_structure,
        atol=args.atol,
    )
    print(summarize_checks(results))


if __name__ == "__main__":
    main()


