"""
Kink detection and inter-kink force readout for 1D continuum runs.

Definitions
-----------
A *kink* is a localized topological soliton of a periodic-potential KG
field — for the Z_N sine-Gordon family used by VIZLAB, the field jumps
by ``2π/N`` across the kink core. Visually it shows up as a sharp
plateau in ``φ(x)`` and a Gaussian-like bump in the energy density.

Detection algorithm
-------------------
1. Compute the local energy density ``e(x)`` once per snapshot.
2. Pad/wrap for periodic boundary conditions.
3. Smooth ``e`` with a small window (Gaussian, σ = 2 cells) so that
   each kink contributes one connected peak.
4. Identify local maxima above ``threshold * max(e)`` (default 30%).
5. For each peak, refine the center using a parabolic fit through
   the three surrounding samples (sub-grid resolution).

The detector intentionally ignores the *type* (kink vs antikink vs
chi-mode); downstream code can classify based on local ``φ`` and ``χ``
slopes if needed.

Inter-kink force
----------------
For a pair of marked kinks at ``x_L < x_R``, define a half-plane
boundary ``x_mid = (x_L + x_R) / 2``. The (instantaneous) force on the
right kink from the left kink is

        F = - dV_pair / dx_R    ≈    [Π(x_R) − Π(x_mid)] / Δx

where ``Π = -dE/dx`` is the local stress (= negative spatial gradient
of total energy density). In practice we use the discrete derivative
of the energy density evaluated at ``x_R`` — this matches the standard
sine-Gordon kink-antikink force formula in the well-separated limit
where ``F ∝ e^{-m(x_R - x_L)}``.

This module is engine-agnostic; the runner / GUI feeds it raw field
arrays plus the dx spacing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


@dataclass
class KinkSite:
    """A tracked kink — center in lattice coordinates, plus a label.

    ``index`` is the integer cell holding the peak; ``position`` is the
    sub-cell refined center (``index * dx`` in physical units).
    """
    label: str
    index: int
    position: float
    energy_peak: float
    history: list[tuple[float, float]] = field(default_factory=list)  # (t, x)


def _smooth_periodic(x: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    """Wrap-aware Gaussian smoothing for periodic 1D arrays."""
    if sigma <= 0:
        return x
    half = int(np.ceil(3.0 * sigma))
    k = np.arange(-half, half + 1, dtype=np.float64)
    kernel = np.exp(-0.5 * (k / sigma) ** 2)
    kernel /= kernel.sum()
    N = x.shape[0]
    padded = np.concatenate([x[-half:], x, x[:half]])
    return np.convolve(padded, kernel, mode="valid")[:N]


def _parabolic_refine(y: np.ndarray, i: int) -> float:
    """Return a fractional offset δ ∈ [-1, 1] s.t. the peak is at i + δ."""
    N = y.shape[0]
    y0 = y[(i - 1) % N]
    y1 = y[i]
    y2 = y[(i + 1) % N]
    denom = (y0 - 2.0 * y1 + y2)
    if abs(denom) < 1e-12:
        return 0.0
    return 0.5 * (y0 - y2) / denom


def detect_kinks_1d(
    energy_density: np.ndarray,
    *,
    dx: float = 1.0,
    threshold_rel: float = 0.30,
    min_separation: int = 8,
    smooth_sigma: float = 2.0,
) -> list[KinkSite]:
    """Locate kinks on a periodic 1D lattice.

    Returns at most ``len(e)`` sites sorted by descending peak height.
    Adjacent peaks closer than ``min_separation`` cells collapse into a
    single site (keep the larger one).
    """
    e = np.asarray(energy_density, dtype=np.float64)
    if e.size == 0:
        return []
    smooth = _smooth_periodic(e, sigma=smooth_sigma)
    max_e = float(smooth.max())
    if max_e <= 0:
        return []
    threshold = threshold_rel * max_e
    rolled_p = np.roll(smooth, -1)
    rolled_m = np.roll(smooth, 1)
    candidate = (smooth > threshold) & (smooth >= rolled_p) & (smooth > rolled_m)
    idx = np.nonzero(candidate)[0].tolist()
    idx.sort(key=lambda i: -smooth[i])
    kept: list[int] = []
    for i in idx:
        if all(_periodic_dist(i, j, e.shape[0]) >= min_separation for j in kept):
            kept.append(i)
    kept.sort()
    sites: list[KinkSite] = []
    for n, i in enumerate(kept):
        delta = _parabolic_refine(smooth, i)
        pos = (i + delta) * dx
        sites.append(KinkSite(
            label=f"K{n+1}",
            index=int(i),
            position=float(pos),
            energy_peak=float(smooth[i]),
        ))
    return sites


def _periodic_dist(a: int, b: int, N: int) -> int:
    d = abs(a - b)
    return min(d, N - d)


def inter_kink_force_1d(
    energy_density: np.ndarray,
    site_a: KinkSite,
    site_b: KinkSite,
    *,
    dx: float = 1.0,
) -> tuple[float, float]:
    """Estimate the instantaneous force on each of two marked kinks.

    Returns ``(F_on_a_from_b, F_on_b_from_a)`` in units of energy per
    unit length. By Newton's third law the two values should differ by
    sign (small numerical drift due to the discrete gradient is
    expected); reporting both is more useful for diagnostics than
    asserting parity.
    """
    e = np.asarray(energy_density, dtype=np.float64)
    if e.size < 4:
        return (0.0, 0.0)
    # Central-difference Π = -dE/dx, periodic BC
    grad_e = (np.roll(e, -1) - np.roll(e, 1)) / (2.0 * dx)
    F_b = -float(grad_e[site_b.index])
    F_a = -float(grad_e[site_a.index])
    # Convention: F_b should pull kink b toward kink a when they attract.
    # The sign of F_a / F_b distinguishes attractive vs repulsive
    # (attractive => F_a * F_b < 0 with x_a < x_b).
    return (F_a, F_b)


class KinkTracker:
    """Stateful tracker for a small set of marked kinks.

    Usage from the GUI: a user clicks a viewport position; we map that
    to the nearest cell index and append a ``KinkSite``. On each
    snapshot we re-detect peaks and reassign each marked site to the
    closest current peak (so the labels follow individual solitons
    across the run).
    """

    def __init__(self, dx: float = 1.0) -> None:
        self.dx = float(dx)
        self.sites: list[KinkSite] = []

    def mark_at(self, cell_index: int, energy_density: np.ndarray,
                label: str | None = None) -> KinkSite:
        candidates = detect_kinks_1d(energy_density, dx=self.dx)
        if not candidates:
            site = KinkSite(
                label=label or f"K{len(self.sites)+1}",
                index=int(cell_index),
                position=float(cell_index) * self.dx,
                energy_peak=float(energy_density[int(cell_index)]),
            )
            self.sites.append(site)
            return site
        # Snap to nearest detected peak (within 0.25 * grid length).
        N = energy_density.shape[0]
        site = min(candidates, key=lambda s: _periodic_dist(s.index, int(cell_index), N))
        site.label = label or f"K{len(self.sites)+1}"
        self.sites.append(site)
        return site

    def clear(self) -> None:
        self.sites = []

    def update(self, energy_density: np.ndarray, *, sim_time: float) -> None:
        """Reassign each marked site to its current peak."""
        if not self.sites:
            return
        candidates = detect_kinks_1d(energy_density, dx=self.dx)
        if not candidates:
            return
        N = energy_density.shape[0]
        used: set[int] = set()
        for s in self.sites:
            # Find nearest unused candidate
            best = None
            best_d = N + 1
            for c in candidates:
                if c.index in used:
                    continue
                d = _periodic_dist(c.index, s.index, N)
                if d < best_d:
                    best = c
                    best_d = d
            if best is None:
                continue
            used.add(best.index)
            s.index = best.index
            s.position = best.position
            s.energy_peak = best.energy_peak
            s.history.append((sim_time, s.position))

    def report(self, energy_density: np.ndarray) -> dict:
        """Return a serializable summary of all sites + pairwise forces."""
        sites = [
            {
                "label": s.label,
                "index": s.index,
                "position": s.position,
                "energy_peak": s.energy_peak,
            }
            for s in self.sites
        ]
        pairs = []
        for i, a in enumerate(self.sites):
            for b in self.sites[i + 1:]:
                F_a, F_b = inter_kink_force_1d(energy_density, a, b, dx=self.dx)
                pairs.append({
                    "a": a.label, "b": b.label,
                    "separation": abs(b.position - a.position),
                    "F_on_a": F_a, "F_on_b": F_b,
                })
        return {"sites": sites, "pairs": pairs}


def auto_track_iter(
    energy_densities: Iterable[np.ndarray],
    *,
    dx: float = 1.0,
    max_kinks: int = 4,
) -> list[list[KinkSite]]:
    """Convenience: run an offline pass over a sequence of energy snapshots
    and return the kink list at every step (sorted by position).

    Used by the experiment runner for batch reports where the user does
    not want to interact with the GUI.
    """
    out: list[list[KinkSite]] = []
    for e in energy_densities:
        sites = detect_kinks_1d(e, dx=dx)
        sites.sort(key=lambda s: s.position)
        out.append(sites[:max_kinks])
    return out
