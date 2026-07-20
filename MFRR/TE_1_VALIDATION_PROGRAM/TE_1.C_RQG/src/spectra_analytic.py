"""Analytic slow-roll spectra evaluation for TE_1.C backgrounds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np

try:
    from .constants import CONSTS
    from .frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        FRWRunResult,
        integrate_background,
    )
except ImportError:  # pragma: no cover
    import sys

    PACKAGE_ROOT = Path(__file__).resolve().parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.append(str(PACKAGE_ROOT))
    from constants import CONSTS
    from frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        FRWRunResult,
        integrate_background,
    )


@dataclass
class SpectrumPoint:
    k: float
    frequency_hz: float
    ln_a_exit: float
    z_exit: float
    hubble_exit: float
    epsilon_exit: float
    eta_exit: float
    scalar_amp_rel: float
    tensor_amp_rel: float
    n_s: float
    r: float

    def to_row(self) -> Dict[str, float]:
        return {
            "k_m_inv": self.k,
            "frequency_hz": self.frequency_hz,
            "ln_a_exit": self.ln_a_exit,
            "z_exit": self.z_exit,
            "hubble_exit": self.hubble_exit,
            "epsilon_exit": self.epsilon_exit,
            "eta_exit": self.eta_exit,
            "scalar_amp_rel": self.scalar_amp_rel,
            "tensor_amp_rel": self.tensor_amp_rel,
            "n_s": self.n_s,
            "r": self.r,
        }


def compute_slow_roll_spectra(
    run: FRWRunResult,
    k_values: Iterable[float],
) -> List[SpectrumPoint]:
    ln_a = run.ln_a
    a = run.scale_factor
    hubble = run.hubble
    epsilon_source = run.epsilon_potential
    eta_source = run.eta_potential
    if np.isfinite(epsilon_source).any() and np.isfinite(eta_source).any():
        epsilon = epsilon_source
        eta_ln = eta_source
    else:
        epsilon = run.epsilon
        eta_ln = run.eta_sr

    k_grid = a * hubble
    ln_k_grid = np.log(k_grid)
    sort_idx = np.argsort(ln_k_grid)
    ln_k_sorted = ln_k_grid[sort_idx]
    ln_a_sorted = ln_a[sort_idx]
    hubble_sorted = hubble[sort_idx]
    epsilon_sorted = epsilon[sort_idx]
    eta_sorted = eta_ln[sort_idx]

    # enforce strict monotonicity by removing duplicates
    ln_k_unique, unique_idx = np.unique(ln_k_sorted, return_index=True)
    ln_a_sorted = ln_a_sorted[unique_idx]
    hubble_sorted = hubble_sorted[unique_idx]
    epsilon_sorted = epsilon_sorted[unique_idx]
    eta_sorted = eta_sorted[unique_idx]

    results: List[SpectrumPoint] = []
    for k in k_values:
        if k <= 0:
            continue
        ln_k = np.log(k)
        if not (ln_k_unique.min() <= ln_k <= ln_k_unique.max()):
            continue
        ln_a_exit = float(np.interp(ln_k, ln_k_unique, ln_a_sorted))
        a_exit = np.exp(ln_a_exit)
        z_exit = 1.0 / a_exit - 1.0
        hubble_exit = float(np.interp(ln_a_exit, run.ln_a, run.hubble))
        epsilon_exit = float(np.interp(ln_a_exit, run.ln_a, epsilon))
        eta_exit = float(np.interp(ln_a_exit, run.ln_a, eta_ln))

        epsilon_floor = max(epsilon_exit, 1.0e-12)
        scalar_amp_rel = (hubble_exit**2) / epsilon_floor
        tensor_amp_rel = hubble_exit**2

        n_s = 1.0 - 2.0 * epsilon_exit - eta_exit
        r = 16.0 * epsilon_exit

        frequency = CONSTS.speed_of_light * k / (2.0 * np.pi)
        results.append(
            SpectrumPoint(
                k=k,
                frequency_hz=frequency,
                ln_a_exit=ln_a_exit,
                z_exit=z_exit,
                hubble_exit=hubble_exit,
                epsilon_exit=epsilon_exit,
                eta_exit=eta_exit,
                scalar_amp_rel=scalar_amp_rel,
                tensor_amp_rel=tensor_amp_rel,
                n_s=n_s,
                r=r,
            )
        )
    return results


def run_background_for_spectra(
    cfg: FRWModelConfig,
    ic: FRWInitialConditions,
    min_ln_a: Optional[float] = None,
) -> FRWRunResult:
    return integrate_background(cfg, ic, rtol=1.0e-7, atol=1.0e-9, min_ln_a=min_ln_a)


def save_spectrum_points(
    points: List[SpectrumPoint],
    output_dir: Path,
    stem: str = "spectra_slow_roll",
) -> Dict[str, float]:
    import pandas as pd

    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([point.to_row() for point in points])
    csv_path = output_dir / f"{stem}.csv"
    df.to_csv(csv_path, index=False)
    summary = summarize_spectra(points)
    summary_path = output_dir / f"{stem}_summary.json"
    summary_path.write_text(json_dumps(summary), encoding="utf-8")
    return summary


def plot_spectrum_points(
    points: List[SpectrumPoint],
    figs_dir: Path,
    stem: str = "spectra_slow_roll",
) -> None:
    import matplotlib.pyplot as plt

    figs_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = figs_dir / "spectra"
    fig_dir.mkdir(exist_ok=True)

    freq = np.array([p.frequency_hz for p in points])
    scalar_amp = np.array([p.scalar_amp_rel for p in points])
    tensor_amp = np.array([p.tensor_amp_rel for p in points])
    n_s = np.array([p.n_s for p in points])
    r = np.array([p.r for p in points])

    order = np.argsort(freq)
    freq = freq[order]
    scalar_amp = scalar_amp[order]
    tensor_amp = tensor_amp[order]
    n_s = n_s[order]
    r = r[order]

    plt.figure(figsize=(6, 4))
    plt.loglog(freq, scalar_amp, marker="o", label="Scalar")
    plt.loglog(freq, tensor_amp, marker="s", label="Tensor")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Relative amplitude")
    plt.title("Analytic slow-roll spectra")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / f"{stem}_amplitudes.png", dpi=160)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.semilogx(freq, n_s, marker="o")
    plt.axhline(1.0, color="gray", linestyle="--")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("n_s")
    plt.title("Scalar spectral index vs frequency")
    plt.tight_layout()
    plt.savefig(fig_dir / f"{stem}_ns.png", dpi=160)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.semilogx(freq, r, marker="o", color="darkred")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("r")
    plt.title("Tensor-to-scalar ratio vs frequency")
    plt.tight_layout()
    plt.savefig(fig_dir / f"{stem}_r.png", dpi=160)
    plt.close()


def summarize_spectra(points: List[SpectrumPoint]) -> Dict[str, float]:
    if not points:
        return {
            "count": 0,
            "n_s_mean": float("nan"),
            "n_s_min": float("nan"),
            "n_s_max": float("nan"),
            "r_mean": float("nan"),
            "r_max": float("nan"),
        }

    n_s = np.array([p.n_s for p in points])
    r = np.array([p.r for p in points])
    epsilon = np.array([p.epsilon_exit for p in points])
    summary = {
        "count": int(len(points)),
        "n_s_mean": float(np.mean(n_s)),
        "n_s_min": float(np.min(n_s)),
        "n_s_max": float(np.max(n_s)),
        "r_mean": float(np.mean(r)),
        "r_max": float(np.max(r)),
        "epsilon_min": float(np.min(epsilon)),
        "epsilon_max": float(np.max(epsilon)),
    }
    return summary


def json_dumps(data: Dict[str, float]) -> str:
    import json

    return json.dumps(data, indent=2, sort_keys=True)

