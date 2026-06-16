"""
Diagnostics utilities for PR-0 analysis.

Cross-reference:
- `SESSIONS/SESSION_26_COMPLETE_STANDARD_MODEL`
- `SESSION_PR_0_27_1_NEXT_STEPS.md` (Session 27 diagnostics extensions)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


def find_top_k_peaks(density: np.ndarray, k: int = 2) -> List[Tuple[int, int]]:
    """Return coordinates (y, x) of top-k density peaks."""
    flat = density.flatten()
    idx = np.argsort(flat)[::-1][:k]
    L_y, L_x = density.shape
    return [divmod(int(i), L_x) for i in idx]


def torus_distance(a: Tuple[int, int], b: Tuple[int, int], L_x: int, L_y: int) -> float:
    """Periodic (toroidal) distance between two lattice points."""
    y1, x1 = a
    y2, x2 = b
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) > L_x // 2:
        dx = dx - int(np.sign(dx)) * L_x
    if abs(dy) > L_y // 2:
        dy = dy - int(np.sign(dy)) * L_y
    return float(np.sqrt(dx * dx + dy * dy))


def order_three_by_x(coords: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Order three (y,x) coords by ascending x coordinate."""
    return sorted(coords, key=lambda c: c[1])


# ---------------------------------------------------------------------------
# Session 27 diagnostics extensions
# ---------------------------------------------------------------------------

def curvature_heatmap(
    curvature: np.ndarray,
    *,
    normalize: bool = True,
    smoothing_sigma: Optional[float] = 1.0,
) -> np.ndarray:
    """
    Produce a curvature heatmap for visualization or export.

    Args:
        curvature: Raw curvature field (e.g., `BootstrapGravity.curvature`).
        normalize: When True, rescale result to [-1, 1] by the maximum absolute
            value; if the field is identically zero the original array is returned.
        smoothing_sigma: Optional Gaussian smoothing factor. Set to `None` to
            return the unsmoothed field.

    Returns:
        Heatmap as `np.ndarray` with dtype float64.
    """
    field = np.asarray(curvature, dtype=np.float64)
    if smoothing_sigma is not None:
        try:
            from scipy.ndimage import gaussian_filter  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "scipy is required for smoothing curvature heatmaps"
            ) from exc
        field = gaussian_filter(field, sigma=smoothing_sigma)

    if not normalize:
        return field

    max_abs = float(np.max(np.abs(field)))
    if max_abs <= 0.0:
        return field
    return field / max_abs


def export_heatmap_csv(
    heatmap: np.ndarray,
    output_path: Path | str,
    metadata: Optional[Dict[str, float]] = None,
) -> Path:
    """
    Export a curvature heatmap to CSV with optional metadata header.

    Args:
        heatmap: 2D array returned by :func:`curvature_heatmap`.
        output_path: Destination filename. Parent directories are created if needed.
        metadata: Optional dictionary to serialize as a JSON header row.

    Returns:
        Absolute :class:`~pathlib.Path` to the written CSV file.
    """
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        if metadata:
            writer.writerow(["# metadata", repr(metadata)])
        for row in np.asarray(heatmap, dtype=np.float64):
            writer.writerow(row.tolist())
    return path


def compute_dissonance_timeseries(
    psi_history: Sequence[np.ndarray],
    chi_history: Sequence[np.ndarray],
    compute_dissonance_fn: Callable[[np.ndarray, np.ndarray, Sequence[np.ndarray]], float],
    *,
    window: Optional[int] = 16,
    stride: int = 1,
) -> np.ndarray:
    """
    Generate a dissonance time-series from stored field histories.

    Args:
        psi_history: Sequence of ψ snapshots.
        chi_history: Sequence of χ snapshots.
        compute_dissonance_fn: Callable compatible with
            `bootstrap.dissonance.compute_ontological_dissonance`.
        window: Number of recent ψ samples to pass as history; `None` uses the
            entire accumulated history.
        stride: Evaluate every `stride` samples to reduce cost.

    Returns:
        1D numpy array of dissonance values ordered by evaluation time.
    """
    size = min(len(psi_history), len(chi_history))
    if size == 0:
        return np.zeros(0, dtype=np.float64)

    results: List[float] = []
    recent: List[np.ndarray] = []
    for idx in range(0, size, max(1, stride)):
        psi = psi_history[idx]
        chi = chi_history[idx]
        recent.append(psi)
        if window is not None and len(recent) > window:
            recent.pop(0)
        value = compute_dissonance_fn(psi, chi, list(recent))
        results.append(float(value))
    return np.asarray(results, dtype=np.float64)


def export_timeseries_csv(
    timeseries: Iterable[float],
    output_path: Path | str,
    *,
    metadata: Optional[Dict[str, float]] = None,
) -> Path:
    """
    Export a time-series (e.g., dissonance values) to CSV.

    Args:
        timeseries: Iterable of scalar samples.
        output_path: Destination filename. Parent directories are created if needed.
        metadata: Optional dictionary recorded in the header for TE₁ provenance.

    Returns:
        Absolute :class:`~pathlib.Path` to the written CSV file.
    """
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        if metadata:
            writer.writerow(["# metadata", repr(metadata)])
        for idx, value in enumerate(timeseries):
            writer.writerow([idx, float(value)])
    return path

