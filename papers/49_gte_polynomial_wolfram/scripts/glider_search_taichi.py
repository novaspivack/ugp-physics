#!/usr/bin/env python3
"""
glider_search_taichi.py — Ether-excluded Z₇ glider search using Taichi parallel CA.

The GTE polynomial: p(L,C,R) = (C + R - C*R - L*C*R) mod 7
Rule: Wolfram k=7, r=1; binary restriction = Rule 110 (Lean-certified, CatAL).

Computes excitation = (perturbed - unperturbed) mod 7 to eliminate ether
autocorrelation artifacts. Sector-dependence tested by pairwise Hamming fractions.

Pass criterion (genuine glider):
  1. Non-zero excitation stripe persists in light cone (not chaotic fill)
  2. Sector-dependent: Hamming > 10% between at least one pair
  3. Measurable propagation speed (stripe slope in excitation spacetime)

Output figures saved to figures/ subdirectory.

DEPENDENCIES
  Required:
    numpy        — pip install numpy
    matplotlib   — pip install matplotlib
    taichi 1.7.3 — pip install "taichi==1.7.3"
      Taichi provides parallelised CA kernels (CPU or GPU backend).
      Tested on Taichi 1.7.3 with CPU and Metal (macOS arm64) backends.
      Earlier versions may have different field API signatures.

  IMPORTANT: do NOT add `from __future__ import annotations` to this file.
  Taichi inspects kernel argument types at import time using the actual type
  objects; the string-annotation deferred evaluation introduced by that import
  breaks its type-inference and causes a runtime TypeError.

EXPECTED RUNTIME
  Small run (L=200, T=100): ~30 seconds on a modern CPU.
  Large run (L=10 000, T=2 000): ~5–10 minutes on CPU; ~30 seconds on GPU.
  Wall-clock timeout: 300 s (configurable via TIMEOUT_SECONDS).

SYSTEM REQUIREMENTS
  Python 3.10+; macOS arm64 or x86_64; Linux x86_64.
  For GPU acceleration: any CUDA-capable GPU or Apple Metal GPU.
  CPU backend works on any platform without a GPU.
"""

import json
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import taichi as ti

# ── Configuration ──────────────────────────────────────────────────────────────
TIMEOUT_SECONDS = 300
SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"

L_SMALL = 200
T_SMALL = 100
L_LARGE = 10_000
T_LARGE = 2_000

INJECTION_VALUES = [2, 3, 4, 5, 6]

# Period-14 Rule 110 ether background (Lean-certified: rule110_z7_poly_rep, CatAL)
ETHER_14 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

# Z7 sector color map
Z7_COLORS = ["#000000", "#ffffff", "#ff0000", "#ff8800",
             "#ffff00", "#00ffff", "#ff00ff"]


# ── Timeout ────────────────────────────────────────────────────────────────────
def _timeout_handler(signum, frame) -> None:
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached. Saving partial results.")
    sys.exit(1)


# ── Taichi initialisation ──────────────────────────────────────────────────────
print("[Taichi] Initialising CPU backend…")
ti.init(arch=ti.cpu)

# Maximum tape size (must be declared before any @ti.kernel / @ti.field)
MAX_CELLS = L_LARGE + 16

# Four fields for double-buffered parallel CA of two tapes (unperturbed + perturbed)
_unp_cur = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))
_unp_nxt = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))
_per_cur = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))
_per_nxt = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))
# Excitation field: (perturbed - unperturbed) mod 7
_exc_cur = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))


@ti.func
def _poly(l, c, r):
    """p(L,C,R) = (C + R - C*R - L*C*R) mod 7 — always positive."""
    raw = c + r - c * r - l * c * r
    return ((raw % 7) + 7) % 7


@ti.kernel
def _step_unp(n: ti.template()):
    for i in range(n):
        l = _unp_cur[(i - 1 + n) % n]
        c = _unp_cur[i]
        r = _unp_cur[(i + 1) % n]
        _unp_nxt[i] = _poly(l, c, r)


@ti.kernel
def _step_per(n: ti.template()):
    for i in range(n):
        l = _per_cur[(i - 1 + n) % n]
        c = _per_cur[i]
        r = _per_cur[(i + 1) % n]
        _per_nxt[i] = _poly(l, c, r)


@ti.kernel
def _swap_unp(n: ti.template()):
    for i in range(n):
        _unp_cur[i] = _unp_nxt[i]


@ti.kernel
def _swap_per(n: ti.template()):
    for i in range(n):
        _per_cur[i] = _per_nxt[i]


@ti.kernel
def _compute_exc(n: ti.template()):
    """Compute excitation = (per - unp + 7) % 7 in-place."""
    for i in range(n):
        _exc_cur[i] = (_per_cur[i] - _unp_cur[i] + 7) % 7


# (cone fill is computed in Python/numpy after to_numpy() for efficiency)


# ── Pure-Python helpers ────────────────────────────────────────────────────────
def _poly_np(L: int, C: int, R: int) -> int:
    return (C + R - C * R - L * C * R) % 7


def make_ether(L: int) -> np.ndarray:
    """Tile ETHER_14 to fill L cells."""
    reps = L // 14 + 2
    return np.array(ETHER_14 * reps, dtype=np.int32)[:L]


def verify_ether_period(L: int = 280, max_steps: int = 100) -> dict:
    """Check the temporal period of the tiled ether under p."""
    ether = make_ether(L)
    state = ether.copy()
    for t in range(1, max_steps + 1):
        new = np.array([_poly_np(state[(i-1)%L], state[i], state[(i+1)%L])
                        for i in range(L)], dtype=np.int32)
        state = new
        if np.array_equal(state, ether):
            return {"period_found": t, "verified": True}
    # Check if spatial pattern repeats with a cyclic shift
    for shift in range(1, 15):
        rolled = np.roll(ether, shift)
        if np.array_equal(state, rolled):
            return {"period_not_found_but_shifted": shift,
                    "after_steps": max_steps, "verified_shift": True}
    return {"period_not_found": True, "after_steps": max_steps}


def _load_tape(field_cur, arr: np.ndarray) -> None:
    """Load L-cell array into a MAX_CELLS Taichi field (zero-padded)."""
    padded = np.zeros(MAX_CELLS, dtype=np.int32)
    padded[:len(arr)] = arr
    field_cur.from_numpy(padded)


def run_excitation_small(ether: np.ndarray, w: int, T: int) -> np.ndarray:
    """
    Full trajectory: run perturbed and unperturbed for T steps.
    Returns excitation array of shape (T+1, L).
    """
    L = len(ether)
    per_init = ether.copy()
    per_init[L // 2] = w

    _load_tape(_unp_cur, ether)
    _load_tape(_per_cur, per_init)

    exc_traj = np.zeros((T + 1, L), dtype=np.int32)
    exc_traj[0] = (per_init - ether + 7) % 7

    for t in range(T):
        _step_unp(L)
        _step_per(L)
        _swap_unp(L)
        _swap_per(L)
        _compute_exc(L)
        exc_traj[t + 1] = _exc_cur.to_numpy()[:L]

    return exc_traj


def run_excitation_large(ether: np.ndarray, w: int, T: int,
                         t_global_start: float,
                         snapshot_interval: int = 100) -> dict:
    """
    Large run: compute excitation on-the-fly without storing full trajectory.
    Returns statistics + sampled snapshots + final excitation state.
    """
    L = len(ether)
    center = L // 2
    per_init = ether.copy()
    per_init[center] = w

    _load_tape(_unp_cur, ether)
    _load_tape(_per_cur, per_init)
    _compute_exc(L)

    # Initial excitation
    exc0 = _exc_cur.to_numpy()[:L]

    cone_fills: List[float] = []
    snapshots: List[Tuple[int, np.ndarray]] = []
    snapshots.append((0, exc0.copy()))
    exc_np = exc0

    for t in range(1, T + 1):
        if time.time() - t_global_start > TIMEOUT_SECONDS - 20:
            return {"timeout": True, "completed_steps": t,
                    "cone_fills": cone_fills, "snapshots": snapshots}

        _step_unp(L)
        _step_per(L)
        _swap_unp(L)
        _swap_per(L)
        _compute_exc(L)

        # Extract excitation for this step
        exc_np = _exc_cur.to_numpy()[:L]

        # Light-cone fill fraction (numpy — fast for this array size)
        radius = min(t, center)
        lo, hi = max(0, center - radius), min(L, center + radius + 1)
        cone_region = exc_np[lo:hi]
        cone_fills.append(float(np.mean(cone_region != 0)) if len(cone_region) > 0 else 0.0)

        if t % snapshot_interval == 0:
            snapshots.append((t, exc_np.copy()))

    final_exc = exc_np.copy()  # exc_np is the last step's excitation

    return {
        "timeout": False,
        "completed_steps": T,
        "cone_fill_mean": float(np.mean(cone_fills[10:])) if len(cone_fills) > 10 else 0.0,
        "cone_fills": cone_fills,
        "final_excitation": final_exc,
        "snapshots": snapshots,
    }


def pairwise_hamming(arrays: Dict[int, np.ndarray]) -> Dict[Tuple[int, int], float]:
    """Pairwise Hamming fractions between excitation arrays."""
    ws = sorted(arrays.keys())
    result = {}
    for i, w1 in enumerate(ws):
        for w2 in ws[i + 1:]:
            s1, s2 = arrays[w1].ravel(), arrays[w2].ravel()
            min_len = min(len(s1), len(s2))
            result[(w1, w2)] = float(np.mean(s1[:min_len] != s2[:min_len]))
    return result


def compute_stripe_score(exc_traj: np.ndarray, center: int) -> Dict[float, float]:
    """
    For each speed v = k/T_SMALL (k integer), compute the fraction of steps
    where excitation is non-zero at position center + round(v * t).
    Returns {speed: fill_fraction}.
    """
    T, L = exc_traj.shape[0] - 1, exc_traj.shape[1]
    scores = {}
    # Sample speeds: v = k/T for k in dense range
    for k in range(-T, T + 1):
        v = k / T
        count = 0
        valid = 0
        for t in range(T + 1):
            pos = center + round(v * t)
            if 0 <= pos < L:
                valid += 1
                if exc_traj[t, pos] != 0:
                    count += 1
        if valid > 0:
            scores[v] = count / valid
    return scores


# ── Visualisation ──────────────────────────────────────────────────────────────
def _z7_cmap() -> mcolors.ListedColormap:
    return mcolors.ListedColormap(Z7_COLORS)


def plot_excitation_field(exc: np.ndarray, title: str, path: Path,
                          center: Optional[int] = None,
                          zoom_cone: bool = True) -> None:
    """Spacetime diagram of the excitation field."""
    T, L = exc.shape[0] - 1, exc.shape[1]
    if zoom_cone and center is not None:
        lo = max(0, center - T - 5)
        hi = min(L, center + T + 6)
        data = exc[:, lo:hi]
    else:
        data = exc

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(data, aspect="auto", cmap=_z7_cmap(),
                   vmin=0, vmax=6, interpolation="nearest", origin="upper")
    ax.set_xlabel("cell (light-cone window)")
    ax.set_ylabel("time step")
    ax.set_title(title, fontsize=11)
    cb = plt.colorbar(im, ax=ax, ticks=range(7))
    cb.ax.set_yticklabels(["0 vac", "1 eth", "2 u", "3 W",
                           "4 d", "5 s", "6 e"])
    cb.set_label("excitation (perturbed − unperturbed) mod 7")
    # Draw light-cone boundaries
    if center is not None and zoom_cone:
        origin = center - lo
        cone_lo = [origin - t for t in range(T + 1)]
        cone_hi = [origin + t for t in range(T + 1)]
        ax.plot(cone_lo, range(T + 1), "w--", linewidth=0.6, alpha=0.5)
        ax.plot(cone_hi, range(T + 1), "w--", linewidth=0.6, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_excitation_panel(exc_dict: Dict[int, np.ndarray],
                          L: int, T: int, path: Path) -> None:
    """5-panel side-by-side excitation diagrams."""
    labels = {2: "w=2 (u)", 3: "w=3 (W)", 4: "w=4 (d)", 5: "w=5 (s)", 6: "w=6 (e)"}
    center = L // 2
    fig, axes = plt.subplots(1, 5, figsize=(22, 8), sharey=True)
    cmap = _z7_cmap()
    for ax, w in zip(axes, [2, 3, 4, 5, 6]):
        exc = exc_dict[w]
        lo = max(0, center - T - 2)
        hi = min(L, center + T + 3)
        im = ax.imshow(exc[:, lo:hi], aspect="auto", cmap=cmap,
                       vmin=0, vmax=6, interpolation="nearest", origin="upper")
        ax.set_title(labels[w], fontsize=11)
        ax.set_xlabel("cell (light-cone)")
        if w == 2:
            ax.set_ylabel("time step")
        # Light-cone lines
        origin = center - lo
        ax.plot([origin - t for t in range(T + 1)], range(T + 1),
                "w--", linewidth=0.7, alpha=0.5)
        ax.plot([origin + t for t in range(T + 1)], range(T + 1),
                "w--", linewidth=0.7, alpha=0.5)
    fig.suptitle(
        "Z7 excitation fields (perturbed − unperturbed) mod 7 | "
        f"L={L}, T={T} | ether-excluded detector",
        fontsize=12
    )
    plt.colorbar(im, ax=axes[-1], ticks=range(7), label="excitation")
    plt.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_cone_fill(cone_fills_dict: Dict[int, List[float]], path: Path) -> None:
    """Plot light-cone fill fraction vs. time step for each injection value."""
    fig, ax = plt.subplots(figsize=(10, 5))
    colors_per_w = {2: "red", 3: "orange", 4: "yellow", 5: "cyan", 6: "magenta"}
    for w in INJECTION_VALUES:
        if w in cone_fills_dict:
            ax.plot(cone_fills_dict[w], color=colors_per_w[w],
                    label=f"w={w}", linewidth=1.2, alpha=0.85)
    ax.axhline(0.5, color="white", linestyle=":", linewidth=0.8, alpha=0.5,
               label="0.5 threshold")
    ax.set_xlabel("time step")
    ax.set_ylabel("excitation fill fraction (light cone)")
    ax.set_title("Light-cone excitation fill fraction vs. time\n"
                 "(< 0.5 sustained → localized structure / glider candidate)")
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.set_facecolor("#111111")
    fig.patch.set_facecolor("#222222")
    ax.tick_params(colors="white")
    ax.title.set_color("white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("gray")
    ax.legend(facecolor="#333333", labelcolor="white")
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── Main analysis passes ───────────────────────────────────────────────────────
def run_small_pass() -> dict:
    """L=200, T=100 validation: full trajectory storage, all visualisations."""
    L, T = L_SMALL, T_SMALL
    print(f"\n=== Small validation: L={L}, T={T} ===")
    ether = make_ether(L)
    center = L // 2

    exc_dict: Dict[int, np.ndarray] = {}
    cone_fill_dict: Dict[int, List[float]] = {}
    t0 = time.time()

    for w in INJECTION_VALUES:
        exc = run_excitation_small(ether, w, T)
        exc_dict[w] = exc

        # Light-cone fill per step
        fills = []
        for t in range(T + 1):
            radius = min(t, center)
            lo, hi = max(0, center - radius), min(L, center + radius + 1)
            region = exc[t, lo:hi]
            fills.append(float(np.mean(region != 0)) if len(region) > 0 else 0.0)
        cone_fill_dict[w] = fills

        print(f"  w={w}: mean cone fill={np.mean(fills[5:]):.3f}, "
              f"final nz={np.mean(exc[-1] != 0):.3f}")

        # Save individual excitation diagram
        out_path = FIGURES_DIR / f"p49_z7_excitation_w{w}.png"
        plot_excitation_field(
            exc,
            f"Z7 excitation (perturbed − unperturbed) mod 7 | w={w} | L={L}, T={T}",
            out_path, center=center, zoom_cone=True
        )

    elapsed = time.time() - t0
    print(f"  Small run wall time: {elapsed:.1f}s")

    # Panel plot
    panel_path = FIGURES_DIR / "p49_z7_excitation_panel.png"
    plot_excitation_panel(exc_dict, L, T, panel_path)

    # Cone fill plot
    fill_path = FIGURES_DIR / "p49_z7_cone_fill.png"
    plot_cone_fill(cone_fill_dict, fill_path)

    # Stripe scores for each w (only small run, full trajectory available)
    stripe_scores: Dict[int, dict] = {}
    for w in INJECTION_VALUES:
        scores = compute_stripe_score(exc_dict[w], center)
        best_speed = max(scores, key=scores.get)
        stripe_scores[w] = {
            "best_speed": best_speed,
            "best_score": scores[best_speed],
            "score_at_zero": scores.get(0.0, 0.0),
            "score_at_2_3": scores.get(round(2 / 3, 6), 0.0),
        }

    # Pairwise Hamming (full excitation trajectory, flattened)
    hamming_full = pairwise_hamming({w: exc_dict[w] for w in INJECTION_VALUES})
    # Also compare final states only
    hamming_final = pairwise_hamming({w: exc_dict[w][-1] for w in INJECTION_VALUES})

    print(f"\n  Pairwise Hamming (full trajectory):")
    for (w1, w2), h in sorted(hamming_full.items()):
        print(f"    ({w1},{w2}): {h:.4f}")
    print(f"\n  Pairwise Hamming (final state):")
    for (w1, w2), h in sorted(hamming_final.items()):
        print(f"    ({w1},{w2}): {h:.4f}")

    # Mean cone fill per w
    mean_fills = {w: float(np.mean(cone_fill_dict[w][5:])) for w in INJECTION_VALUES}

    # Glider test: any w with mean cone fill < 0.5 → localized structure
    glider_candidates = [w for w, f in mean_fills.items() if f < 0.5]
    min_hamming = min(hamming_full.values())
    sector_dependent = min_hamming > 0.10

    print(f"\n  Mean cone fills: {mean_fills}")
    print(f"  Glider candidates (fill < 0.5): {glider_candidates}")
    print(f"  Sector-dependent (min Hamming > 10%): {sector_dependent} "
          f"(min={min_hamming:.4f})")

    return {
        "L": L, "T": T, "wall_time_s": elapsed,
        "mean_cone_fills": mean_fills,
        "hamming_full": {str(k): v for k, v in hamming_full.items()},
        "hamming_final": {str(k): v for k, v in hamming_final.items()},
        "stripe_scores": {str(w): v for w, v in stripe_scores.items()},
        "glider_candidates": glider_candidates,
        "sector_dependent": sector_dependent,
        "min_hamming": min_hamming,
        "exc_dict": exc_dict,
        "cone_fill_dict": cone_fill_dict,
    }


def run_large_pass(t_global_start: float) -> dict:
    """L=10000, T=2000 large-scale run using Taichi parallel kernels."""
    L, T = L_LARGE, T_LARGE
    print(f"\n=== Large-scale run: L={L}, T={T} ===")
    ether = make_ether(L)
    center = L // 2

    final_excs: Dict[int, np.ndarray] = {}
    large_stats: Dict[int, dict] = {}
    cone_fill_large: Dict[int, List[float]] = {}

    t0 = time.time()
    completed_ws = []

    for w in INJECTION_VALUES:
        elapsed_total = time.time() - t_global_start
        if elapsed_total > TIMEOUT_SECONDS - 30:
            print(f"  Approaching timeout ({elapsed_total:.0f}s), stopping large run early.")
            break

        print(f"  w={w}…", end=" ", flush=True)
        tw = time.time()

        result = run_excitation_large(
            ether, w, T, t_global_start, snapshot_interval=100
        )

        elapsed_w = time.time() - tw

        if result.get("timeout"):
            print(f"TIMEOUT at step {result['completed_steps']}")
            large_stats[w] = {"timeout": True, "completed_steps": result["completed_steps"]}
            break

        final_excs[w] = result["final_excitation"]
        large_stats[w] = {
            "cone_fill_mean": result["cone_fill_mean"],
            "final_nz_fraction": float(np.mean(result["final_excitation"] != 0)),
            "completed_steps": result["completed_steps"],
        }
        cone_fill_large[w] = result["cone_fills"]
        completed_ws.append(w)
        print(f"done in {elapsed_w:.1f}s | cone_fill_mean={result['cone_fill_mean']:.3f}")

    elapsed_total_run = time.time() - t0
    print(f"  Large run wall time: {elapsed_total_run:.1f}s")

    # Hamming fractions on final excitation states
    hamming_large: dict = {}
    if len(final_excs) > 1:
        hamming_large = pairwise_hamming(final_excs)
        print(f"\n  Large run pairwise Hamming (final excitation state, L={L}):")
        for (w1, w2), h in sorted(hamming_large.items()):
            print(f"    ({w1},{w2}): {h:.4f}")

    # Cone fill plot for large run
    if cone_fill_large:
        fill_path_large = FIGURES_DIR / "p49_z7_cone_fill_large.png"
        plot_cone_fill(cone_fill_large, fill_path_large)

    min_h = min(hamming_large.values()) if hamming_large else None
    max_h = max(hamming_large.values()) if hamming_large else None
    glider_candidates_large = [
        w for w, s in large_stats.items()
        if isinstance(s.get("cone_fill_mean"), float) and s["cone_fill_mean"] < 0.5
    ]

    return {
        "L": L, "T": T,
        "wall_time_s": elapsed_total_run,
        "completed_ws": completed_ws,
        "stats": large_stats,
        "hamming_final": {str(k): v for k, v in hamming_large.items()},
        "min_hamming": min_h,
        "max_hamming": max_h,
        "glider_candidates": glider_candidates_large,
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    t_global = time.time()

    print("=" * 65)
    print("Z₇ Ether-Excluded Glider Search — Taichi large-scale run")
    print(f"Rule: p(L,C,R) = (C+R-C*R-L*C*R) mod 7")
    print(f"Taichi version: {ti.__version__}")
    print("=" * 65)

    # Verify ether period
    ether_check = verify_ether_period(280)
    print(f"\nEther period check (L=280, max 100 steps): {ether_check}")

    # Small validation pass
    small = run_small_pass()

    # Large-scale pass
    large = run_large_pass(t_global)

    # ── Verdict ────────────────────────────────────────────────────────────────
    small_candidates = small["glider_candidates"]
    large_candidates = large["glider_candidates"]
    any_candidate = bool(small_candidates or large_candidates)

    small_sector_dep = small["sector_dependent"]
    large_min_h = large.get("min_hamming")
    large_sector_dep = large_min_h is not None and large_min_h > 0.10

    print("\n" + "=" * 65)
    print("GLIDER SEARCH VERDICT")
    print("=" * 65)

    if any_candidate:
        print(f"CANDIDATE DETECTED")
        print(f"  Small run candidates (cone fill < 0.5): {small_candidates}")
        print(f"  Large run candidates (cone fill < 0.5): {large_candidates}")
        verdict = "CANDIDATE"
    else:
        # Chaotic fill (expected for Class 3 CA)
        print(f"FAIL — No localized glider detected.")
        print(f"  Excitation fills the entire light cone (chaotic Class 3 dynamics)")
        print(f"  Mean cone fills (small): {small['mean_cone_fills']}")
        verdict = "FAIL"

    print(f"\nSECTOR-DEPENDENCE TEST:")
    print(f"  Small Hamming (full traj, min/max): "
          f"{small['min_hamming']:.4f} / {max(float(v) for v in small['hamming_full'].values()):.4f}")
    if large_min_h is not None:
        print(f"  Large Hamming (final state, min/max): "
              f"{large_min_h:.4f} / {large['max_hamming']:.4f}")

    sector_dep_result = "PASS" if (small_sector_dep or large_sector_dep) else "FAIL"
    print(f"  Sector-dependent verdict: {sector_dep_result}")

    # ── Save results JSON ──────────────────────────────────────────────────────
    elapsed = time.time() - t_global

    results = {
        "verdict": verdict,
        "sector_dependence": sector_dep_result,
        "small": {k: v for k, v in small.items() if k not in ("exc_dict", "cone_fill_dict")},
        "large": large,
        "total_wall_time_s": elapsed,
        "taichi_version": ti.__version__,
    }

    def _json_safe(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        raise TypeError(type(obj))

    json_path = SCRIPT_DIR / "glider_search_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=_json_safe)

    print(f"\nResults written to {json_path.name}")
    print(f"Total wall time: {elapsed:.1f}s")

    signal.alarm(0)


if __name__ == "__main__":
    main()
