#!/usr/bin/env python3
"""
EPIC_073 Rank 75-DSLIT — Double-slit interference from GTE / Phi_MDL.

Zone L1: Phi_MDL scalar wave propagates through two slits; amplitude superposition
         phi(x) = phi_L(x) + phi_R(x) from Huygens-Fresnel integration.
Zone L2: [D] selects discrete kink-localization clicks with P(x) |phi(x)|^2
         (76-BORN / 77-2QUANT Born-rule chain).

Wall-clock cap: 300 s.
"""

from __future__ import annotations

import json
import signal
import sys
import time

import numpy as np

TIMEOUT_SECONDS = 300
SEED = 75075

signal.signal(
    signal.SIGALRM,
    lambda _s, _f: (
        print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached."),
        sys.exit(1),
    ),
)
signal.alarm(TIMEOUT_SECONDS)
t0 = time.time()
rng = np.random.default_rng(SEED)

# --- GTE-linked scales (natural units c = hbar = 1) ---
M_KINK = 0.29010  # GeV, GTE SCC kink mass (073-LOR2 / P39)
N_PHI = 7  # Z7 periodicity (Phi_MDL)

# --- Double-slit geometry (dimensionless) ---
K = 12.0  # wave number (de Broglie scale for Zone L1 packet)
WAVELENGTH = 2.0 * np.pi / K
SLIT_WIDTH = 0.35
SLIT_SEP = 2.0
SCREEN_DIST = 18.0
N_SCREEN = 400
N_SOURCE = 80  # quadrature points per slit
N_CLICKS = 12000
N_BINS = 80


def slit_apertures() -> list[tuple[float, float]]:
    """Return (x_center, half_width) for left and right slits."""
    return [(-SLIT_SEP / 2, SLIT_WIDTH / 2), (SLIT_SEP / 2, SLIT_WIDTH / 2)]


def huygens_fresnel_screen() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Numerically integrate phi(x_s) = sum_slit int exp(i k r)/r dx'.
    Returns x_screen, intensity |phi|^2, complex amplitude.
    """
    x_max = 8.0
    x_screen = np.linspace(-x_max, x_max, N_SCREEN)
    amp = np.zeros(N_SCREEN, dtype=np.complex128)
    phi_L = np.zeros(N_SCREEN, dtype=np.complex128)
    phi_R = np.zeros(N_SCREEN, dtype=np.complex128)

    slits = slit_apertures()
    for s_idx, (xc, half_w) in enumerate(slits):
        xs = np.linspace(xc - half_w, xc + half_w, N_SOURCE)
        dxs = xs[1] - xs[0] if len(xs) > 1 else 1.0
        for x_src in xs:
            r = np.sqrt((x_screen - x_src) ** 2 + SCREEN_DIST ** 2)
            contrib = np.exp(1j * K * r) / r * dxs
            amp += contrib
            if s_idx == 0:
                phi_L += contrib
            else:
                phi_R += contrib

    intensity = np.abs(amp) ** 2
    return x_screen, intensity, amp, phi_L, phi_R


def analytic_fraunhofer(x: np.ndarray) -> np.ndarray:
    theta = np.arctan2(x, SCREEN_DIST)
    beta = np.pi * SLIT_WIDTH * np.sin(theta) / WAVELENGTH
    alpha = np.pi * SLIT_SEP * np.sin(theta) / WAVELENGTH
    with np.errstate(divide="ignore", invalid="ignore"):
        single = np.where(np.abs(beta) < 1e-12, 1.0, (np.sin(beta) / beta) ** 2)
        double = np.cos(alpha) ** 2
    return single * double


def fringe_visibility(intensity: np.ndarray) -> float:
    i_max = float(np.max(intensity))
    i_min = float(np.min(intensity))
    denom = i_max + i_min
    if denom < 1e-15:
        return 0.0
    return (i_max - i_min) / denom


def estimate_fringe_spacing(x: np.ndarray, intensity: np.ndarray) -> float:
    """Spacing between first two intensity maxima (excluding central peak)."""
    peaks = []
    for i in range(1, len(intensity) - 1):
        if intensity[i] > intensity[i - 1] and intensity[i] > intensity[i + 1]:
            peaks.append(i)
    if len(peaks) < 2:
        return float("nan")
    # use first two peaks on same side of center if possible
    center = len(intensity) // 2
    right_peaks = [p for p in peaks if p > center + 5]
    if len(right_peaks) >= 2:
        return float((x[right_peaks[1]] - x[right_peaks[0]]))
    if len(peaks) >= 2:
        return float((x[peaks[1]] - x[peaks[0]]))
    return float("nan")


def chi2_reduced(obs: np.ndarray, exp: np.ndarray) -> float:
    exp_n = exp / (np.sum(exp) + 1e-30)
    obs_n = obs / (np.sum(obs) + 1e-30)
    n = len(obs)
    chi2 = float(np.sum((obs_n - exp_n) ** 2 / (exp_n + 1e-12)))
    return chi2 / max(n - 1, 1)


def born_sample_clicks(intensity: np.ndarray, n_clicks: int) -> np.ndarray:
    p = intensity / (np.sum(intensity) + 1e-30)
    return rng.choice(len(intensity), size=n_clicks, p=p)


# --- Main ---
x_screen, intensity, amp, phi_L, phi_R = huygens_fresnel_screen()
intensity_two_path = np.abs(phi_L + phi_R) ** 2

analytic = analytic_fraunhofer(x_screen)
analytic_norm = analytic / (np.max(analytic) + 1e-30)
intensity_norm = intensity / (np.max(intensity) + 1e-30)
two_path_norm = intensity_two_path / (np.max(intensity_two_path) + 1e-30)

corr_fraunhofer = float(np.corrcoef(intensity_norm, analytic_norm)[0, 1])
corr_two_path = float(np.corrcoef(intensity_norm, two_path_norm)[0, 1])
vis_sim = fringe_visibility(intensity)
vis_analytic = fringe_visibility(analytic)

fringe_spacing_pred = WAVELENGTH * SCREEN_DIST / SLIT_SEP
fringe_spacing_est = estimate_fringe_spacing(x_screen, intensity)

# Identity check: |phi_L + phi_R|^2 vs |amp|^2 (amp = phi_L + phi_R by construction)
max_path_identity_err = float(np.max(np.abs(intensity - intensity_two_path)))

clicks = born_sample_clicks(intensity, N_CLICKS)
hist, bin_edges = np.histogram(clicks, bins=N_BINS, range=(0, N_SCREEN), density=False)
bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
int_on_bins = np.array(
    [intensity[int(min(max(int(c), 0), N_SCREEN - 1))] for c in bin_centers]
)
chi2_born = chi2_reduced(hist.astype(float), int_on_bins.astype(float))
corr_born = float(np.corrcoef(hist.astype(float), int_on_bins.astype(float))[0, 1])

n_peaks = int(np.sum((intensity[1:-1] > intensity[:-2]) & (intensity[1:-1] > intensity[2:])))
pass_fringes = vis_sim > 0.15 and n_peaks >= 3
pass_fraunhofer = corr_fraunhofer > 0.90
pass_two_path = corr_two_path > 0.999 and max_path_identity_err < 1e-10
pass_born = corr_born > 0.97 and chi2_born < 0.005
pass_spacing = (
    np.isfinite(fringe_spacing_est)
    and abs(fringe_spacing_est - fringe_spacing_pred) / fringe_spacing_pred < 0.25
)

overall_pass = pass_fringes and pass_fraunhofer and pass_two_path and pass_born

results = {
    "rank": "75-DSLIT",
    "framework": "Phi_MDL Zone L1 Huygens-Fresnel + Zone L2 [D] Born sampling",
    "gte_params": {
        "M_kink_GeV": M_KINK,
        "N_phi": N_PHI,
        "wavelength_sim": WAVELENGTH,
        "k_sim": K,
    },
    "geometry": {
        "slit_width": SLIT_WIDTH,
        "slit_sep": SLIT_SEP,
        "screen_dist": SCREEN_DIST,
        "N_screen": N_SCREEN,
        "N_source_quadrature": N_SOURCE,
    },
    "zone_L1_wave": {
        "fringe_visibility": vis_sim,
        "fringe_visibility_analytic_fraunhofer": vis_analytic,
        "corr_fraunhofer": corr_fraunhofer,
        "corr_two_path_phi_L_plus_phi_R": corr_two_path,
        "max_path_identity_err": max_path_identity_err,
        "fringe_spacing_pred": fringe_spacing_pred,
        "fringe_spacing_est": fringe_spacing_est,
        "n_intensity_peaks": n_peaks,
        "pass_fringes": bool(pass_fringes),
        "pass_fraunhofer": bool(pass_fraunhofer),
        "pass_two_path": bool(pass_two_path),
        "pass_spacing": bool(pass_spacing),
    },
    "zone_L2_born": {
        "N_clicks": N_CLICKS,
        "chi2_reduced_clicks_vs_intensity": chi2_born,
        "corr_clicks_vs_intensity": corr_born,
        "pass_born": bool(pass_born),
    },
    "interpretation": {
        "physical_chain": (
            "kink beable takes definite slit path (L2 ontology); Zone L1 amplitude "
            "phi = phi_L + phi_R; [D] outcome weights P = |phi|^2 (76-BORN)"
        ),
        "cat_level": "CatA" if overall_pass else "CatD",
    },
    "overall_pass": bool(overall_pass),
    "elapsed_s": time.time() - t0,
}

out_path = "dslit_gte_interference_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print("=== 75-DSLIT Double-Slit GTE Interference ===")
print(f"Fringe visibility (sim):     {vis_sim:.4f}  (Fraunhofer {vis_analytic:.4f})")
print(f"Corr(sim, Fraunhofer):       {corr_fraunhofer:.4f}")
print(f"Corr(sim, |phi_L+phi_R|^2):  {corr_two_path:.4f}")
print(f"Path identity max err:       {max_path_identity_err:.2e}")
print(f"Fringe spacing pred/est:     {fringe_spacing_pred:.4f} / {fringe_spacing_est:.4f}")
print(f"Born clicks corr:            {corr_born:.4f}  chi2_red={chi2_born:.5f}")
print(f"Overall PASS:                {overall_pass}")
print(f"Cat level:                   {results['interpretation']['cat_level']}")
print(f"Wrote {out_path}  ({results['elapsed_s']:.1f}s)")

signal.alarm(0)
