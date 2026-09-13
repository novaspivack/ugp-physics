#!/usr/bin/env python3
"""
z7_sector_dynamics.py — Z₇ CA dynamics: glider search, scattering, sector comparison.

The GTE polynomial p(L,C,R) = C + R - C*R - L*C*R (mod 7) is the MDL-minimal
CA rule that is simultaneously:
  - Rule 110 on binary inputs (Lean-certified: rule110_z7_poly_rep, CatAL)
  - The algebraic certificate of the GTE Z₇×Z₃ substrate (T96-02, CatAL)

This script runs three experiments:
  A. Z₇ glider search — search for stable propagating structures in ether background
  B. Two-particle scattering — test Z₇ winding conservation at SM vertices
  C. Sector color comparison — test whether different Z₇ injection values (particle
     sectors) produce measurably different dynamics

Output figures saved to figures/ subdirectory:
  p49_z7_glider_search_v{2..6}.png  — per-sector spacetime diagrams
  p49_z7_scattering_{a}_{b}.png     — scattering spacetime diagrams
  p49_z7_color_comparison.png       — five-sector side-by-side comparison

References:
  P28: Computational universality (rule110_z7_poly_rep)
  P41: Three-layer CMCA (f_MDL orbit, chirality)
  P45: Three-tape CMCA (cross-tape coupling)
  P48 Ch.4: The Selection (T96-02 MDL uniqueness)

Dependencies: numpy, matplotlib
"""

from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

TIMEOUT_SECONDS = 600
PREDICTED_GLIDER_SPEED = 2 / 3
SPEED_TOLERANCE = 0.08
GLIDER_MATCH_THRESHOLD = 0.85

# Color map for Z₇ values
# 0=vacuum, 1=ether, 2=up-quark-like, 3=W-like, 4=down-quark-like, 5=s, 6=electron-like
Z7_COLORS = {
    0: "#000000",
    1: "#ffffff",
    2: "#ff0000",
    3: "#ff8800",
    4: "#ffff00",
    5: "#00ffff",
    6: "#ff00ff",
}

ETHER_14 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"


def _timeout_handler(_signum, _frame) -> None:
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


def poly_z7(L: int, C: int, R: int) -> int:
    """GTE polynomial p(L,C,R) = C + R - C*R - L*C*R (mod 7).

    On binary {0,1}^3 inputs: equals Rule 110 (Lean: rule110_z7_poly_rep, CatAL).
    On full Z₇^3 inputs: Class 3 chaotic dynamics.
    """
    return (C + R - C * R - L * C * R) % 7


def make_ether(L: int) -> List[int]:
    """Build an ether background of L cells (period-14 tiling)."""
    return (ETHER_14 * (L // 14 + 1))[:L]


def step_ca(state: List[int], rule_fn=None) -> List[int]:
    """Apply CA rule to periodic 1D state."""
    if rule_fn is None:
        rule_fn = poly_z7
    n = len(state)
    return [rule_fn(state[(i - 1) % n], state[i], state[(i + 1) % n]) for i in range(n)]


def run_ca(initial: List[int], steps: int, rule_fn=None) -> np.ndarray:
    """Run CA for given steps. Returns (steps+1) x L array."""
    state = list(initial)
    trajectory = [list(state)]
    for _ in range(steps):
        state = step_ca(state, rule_fn)
        trajectory.append(list(state))
    return np.array(trajectory, dtype=np.uint8)


def winding_number(state: List[int]) -> int:
    """Compute Z₇ winding number: sum(val_i * i) mod 7."""
    total = 0
    for i, v in enumerate(state):
        total = (total + int(v) * i) % 7
    return total


def total_winding(state: List[int]) -> int:
    """Total winding: sum of all non-vacuum cell values mod 7."""
    return sum(v for v in state if v not in (0, 1)) % 7


def profile_winding(state: List[int]) -> int:
    """Per-step winding profile: sum of all cell values mod 7."""
    return sum(state) % 7


def extract_window(state: List[int], center: int, width: int) -> np.ndarray:
    """Periodic window extraction centered at `center`."""
    L = len(state)
    half = width // 2
    return np.array([state[(center - half + i) % L] for i in range(width)], dtype=np.uint8)


def excitation_com(state: List[int], ether: List[int]) -> int:
    """Center-of-mass of cells that differ from the local ether background."""
    weights: List[float] = []
    positions: List[int] = []
    for i, (v, e) in enumerate(zip(state, ether)):
        if v != e:
            w = abs(int(v) - int(e)) + 1
            weights.append(float(w))
            positions.append(i)
    if not positions:
        return len(state) // 2
    return int(round(sum(p * w for p, w in zip(positions, weights)) / sum(weights)))


def spread_radius(state: List[int], ether: List[int], center: int) -> int:
    """Maximum circular distance from center to any excitation cell."""
    L = len(state)
    radius = 0
    for i, (v, e) in enumerate(zip(state, ether)):
        if v != e:
            d = min((i - center) % L, (center - i) % L)
            radius = max(radius, d)
    return radius


def pattern_match_score(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of matching cells in two equal-length patterns."""
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    return float(np.mean(a == b))


def detect_glider_candidates(
    trajectory: np.ndarray,
    ether: List[int],
    window: int = 21,
    min_period: int = 3,
    max_period: int = 150,
    match_threshold: float = GLIDER_MATCH_THRESHOLD,
) -> List[Dict]:
    """Search trajectory for repeating windows with spatial drift (glider candidates)."""
    T, L = trajectory.shape
    candidates: List[Dict] = []
    seen: set = set()

    for t0 in range(0, min(T - max_period, 80)):
        center0 = excitation_com(list(trajectory[t0]), ether)
        pat0 = extract_window(list(trajectory[t0]), center0, window)
        if np.all(pat0 == extract_window(ether, center0, window)):
            continue

        for period in range(min_period, max_period + 1):
            t1 = t0 + period
            if t1 >= T:
                break

            best_k = 0
            best_score = 0.0
            for k in range(-period, period + 1):
                center1 = (center0 + k) % L
                pat1 = extract_window(list(trajectory[t1]), center1, window)
                score = pattern_match_score(pat0, pat1)
                if score > best_score:
                    best_score = score
                    best_k = k

            if best_score >= match_threshold:
                speed = best_k / period
                key = (round(speed, 4), window)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    {
                        "t0": t0,
                        "period": period,
                        "shift": best_k,
                        "speed": speed,
                        "abs_speed": abs(speed),
                        "match_score": best_score,
                        "near_predicted": abs(abs(speed) - PREDICTED_GLIDER_SPEED) <= SPEED_TOLERANCE,
                    }
                )

    candidates.sort(key=lambda c: (-c["match_score"], abs(c["abs_speed"] - PREDICTED_GLIDER_SPEED)))
    return candidates


def _z7_cmap():
    colors = [Z7_COLORS[i] for i in range(7)]
    return mcolors.ListedColormap(colors)


def plot_spacetime(
    trajectory: np.ndarray,
    title: str = "",
    ax=None,
    show_winding: bool = False,
    ether: Optional[List[int]] = None,
) -> plt.Axes:
    """Plot Z₇ spacetime diagram with particle-sector color coding."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))

    im = ax.imshow(trajectory, aspect="auto", cmap=_z7_cmap(), vmin=0, vmax=6, interpolation="nearest")
    ax.set_xlabel("cell index")
    ax.set_ylabel("time step")
    if title:
        ax.set_title(title)

    cbar = plt.colorbar(im, ax=ax, ticks=range(7))
    cbar.ax.set_yticklabels(["0 vac", "1 eth", "2 u", "3 W", "4 d", "5 s", "6 e"])

    if show_winding and ether is not None:
        profile = [profile_winding(list(trajectory[t])) for t in range(len(trajectory))]
        ax2 = ax.twinx()
        ax2.plot(profile, color="cyan", linewidth=0.8, alpha=0.7, label="Σ mod 7")
        ax2.set_ylabel("winding profile", color="cyan")
        ax2.set_ylim(-0.5, 6.5)

    return ax


def inject_perturbation(base: List[int], position: int, value: int) -> List[int]:
    """Inject a single Z₇ value at a position."""
    state = list(base)
    state[position] = value
    return state


def search_gliders(
    L: int = 200,
    steps: int = 500,
    injection_values: Optional[List[int]] = None,
    injection_positions: Optional[List[int]] = None,
) -> Dict:
    """Search for stable propagating structures (gliders) in Z₇ domain.

    Returns dict with gliders found, speeds, and injection metadata.
    """
    if injection_values is None:
        injection_values = [2, 3, 4, 5, 6]
    if injection_positions is None:
        injection_positions = [L // 2, L // 2 - 20, L // 2 + 20]

    ether = make_ether(L)
    results: Dict = {"L": L, "steps": steps, "by_value": {}, "summary": {}}

    for value in injection_values:
        value_results = []
        best_overall = None

        for pos in injection_positions:
            state = inject_perturbation(ether, pos, value)
            traj = run_ca(state, steps)
            candidates = detect_glider_candidates(traj, ether)
            com_track = [excitation_com(list(traj[t]), ether) for t in range(len(traj))]
            drift = com_track[-1] - com_track[0]
            mean_speed_com = drift / steps if steps else 0.0

            trial = {
                "injection_position": pos,
                "candidates": candidates[:5],
                "best_candidate": candidates[0] if candidates else None,
                "com_drift": drift,
                "mean_com_speed": mean_speed_com,
                "trajectory": traj,
            }
            value_results.append(trial)

            if candidates:
                cand = candidates[0]
                if best_overall is None or cand["match_score"] > best_overall["match_score"]:
                    best_overall = {**cand, "injection_position": pos}

        results["by_value"][value] = {
            "trials": [
                {
                    "injection_position": t["injection_position"],
                    "candidates": t["candidates"],
                    "best_candidate": t["best_candidate"],
                    "com_drift": t["com_drift"],
                    "mean_com_speed": t["mean_com_speed"],
                }
                for t in value_results
            ],
            "best_overall": best_overall,
            "glider_found": best_overall is not None,
            "trajectory_best": value_results[0]["trajectory"],
        }

    any_found = any(results["by_value"][v]["glider_found"] for v in injection_values)
    near_2_3 = [
        v
        for v in injection_values
        if results["by_value"][v]["best_overall"]
        and results["by_value"][v]["best_overall"].get("near_predicted")
    ]
    results["summary"] = {
        "any_glider_found": any_found,
        "values_with_glider": [v for v in injection_values if results["by_value"][v]["glider_found"]],
        "values_near_2_3_speed": near_2_3,
        "predicted_speed": PREDICTED_GLIDER_SPEED,
    }
    return results


def scattering_experiment(
    value_left: int,
    value_right: int,
    L: int = 56,
    separation: int = 20,
    steps: int = 40,
    save_path: Optional[Path] = None,
) -> Dict:
    """Two-particle scattering: inject two Z₇ values at different positions.

    Measures winding conservation before and after the scattering region.
    Z₇ winding conservation is predicted by GTE at all SM vertices (CatAL).
    """
    ether = make_ether(L)
    center = L // 2
    state = inject_perturbation(ether, center - separation // 2, value_left)
    state = inject_perturbation(state, center + separation // 2, value_right)

    trajectory = run_ca(state, steps)

    w_before = total_winding(list(trajectory[0]))
    w_after = total_winding(list(trajectory[-1]))
    profile = [total_winding(list(trajectory[t])) for t in range(len(trajectory))]
    profile_sum = [profile_winding(list(trajectory[t])) for t in range(len(trajectory))]

    result = {
        "value_left": value_left,
        "value_right": value_right,
        "winding_before": w_before,
        "winding_after": w_after,
        "conserved": w_before == w_after,
        "winding_profile": profile,
        "sum_profile": profile_sum,
        "trajectory": trajectory,
        "image_path": None,
    }

    if save_path is not None:
        fig, ax = plt.subplots(figsize=(10, 5))
        plot_spacetime(
            trajectory,
            title=f"Scattering ({value_left}, {value_right}): W {w_before}→{w_after}",
            ax=ax,
            show_winding=True,
            ether=ether,
        )
        fig.tight_layout()
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        result["image_path"] = str(save_path)

    return result


def color_comparison_experiment(L: int = 56, steps: int = 56) -> Dict:
    """Compare spacetime dynamics for each non-binary Z₇ injection value.

    Tests whether different winding values (= different particle sectors)
    produce measurably different dynamics when injected into the ether.
    """
    ether = make_ether(L)
    center = L // 2
    results: Dict = {}

    for value in [2, 3, 4, 5, 6]:
        state = inject_perturbation(ether, center, value)
        traj = run_ca(state, steps)
        radii = [spread_radius(list(traj[t]), ether, center) for t in range(len(traj))]
        spread_rate = (radii[-1] - radii[0]) / steps if steps else 0.0
        candidates = detect_glider_candidates(traj, ether, max_period=min(steps, 40))

        results[value] = {
            "trajectory": traj,
            "final_unique_values": len(set(traj[-1].tolist())),
            "final_nonzero": int(np.count_nonzero(traj[-1])),
            "spread_rate": spread_rate,
            "max_spread": radii[-1],
            "radii": radii,
            "winding_profile": [profile_winding(list(traj[t])) for t in range(len(traj))],
            "total_winding_profile": [total_winding(list(traj[t])) for t in range(len(traj))],
            "glider_candidates": len(candidates),
            "best_glider": candidates[0] if candidates else None,
        }

    final_states = {
        v: results[v]["trajectory"][-1].astype(int).tolist() for v in results
    }
    distinguishable = False
    pairs_compared = []
    for i, v1 in enumerate([2, 3, 4, 5, 6]):
        for v2 in [2, 3, 4, 5, 6][i + 1:]:
            s1 = np.array(final_states[v1])
            s2 = np.array(final_states[v2])
            hamming = float(np.mean(s1 != s2))
            spread_diff = abs(results[v1]["spread_rate"] - results[v2]["spread_rate"])
            pairs_compared.append(
                {
                    "pair": (v1, v2),
                    "hamming_fraction": hamming,
                    "spread_rate_diff": spread_diff,
                    "distinguishable": hamming > 0.05 or spread_diff > 0.01,
                }
            )
            if hamming > 0.05 or spread_diff > 0.01:
                distinguishable = True

    results["_summary"] = {
        "distinguishable": distinguishable,
        "pair_comparisons": pairs_compared,
    }
    return results


def save_glider_figure(value: int, trajectory: np.ndarray, glider_info: Optional[Dict], path: Path) -> None:
    """Save spacetime diagram for one glider-search injection value."""
    title = f"Z₇ glider search — injection value {value}"
    if glider_info:
        title += f" | best v={glider_info['speed']:.3f} (match={glider_info['match_score']:.2f})"
    else:
        title += " | no glider candidate"

    fig, ax = plt.subplots(figsize=(12, 6))
    plot_spacetime(trajectory, title=title, ax=ax)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def save_color_comparison_figure(comparison: Dict, path: Path, steps: int = 56) -> None:
    """Side-by-side spacetime diagrams for all injection values."""
    fig, axes = plt.subplots(5, 1, figsize=(12, 14), sharex=True)
    labels = {2: "u-like (2)", 3: "W-like (3)", 4: "d-like (4)", 5: "s (5)", 6: "e-like (6)"}

    for ax, value in zip(axes, [2, 3, 4, 5, 6]):
        traj = comparison[value]["trajectory"]
        sr = comparison[value]["spread_rate"]
        plot_spacetime(traj, title=f"{labels[value]} — spread rate {sr:.3f} cells/step", ax=ax)

    fig.suptitle("Z₇ sector color comparison (ether + single-cell injection)", fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def run_all_experiments(output_dir: Optional[Path] = None) -> Dict:
    """Run Experiments A, B, C and write PNG artifacts."""
    if output_dir is None:
        output_dir = FIGURES_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: Dict = {"png_files": [], "glider": {}, "scattering": {}, "color": {}}

    print("=== Experiment A: Z₇ Glider Search ===")
    glider_results = search_gliders(L=200, steps=500)
    artifacts["glider"] = {
        "summary": glider_results["summary"],
        "by_value": {},
    }

    for value in [2, 3, 4, 5, 6]:
        info = glider_results["by_value"][value]
        best = info["best_overall"]
        png_path = output_dir / f"p49_z7_glider_search_v{value}.png"
        save_glider_figure(value, info["trajectory_best"], best, png_path)
        artifacts["png_files"].append(str(png_path))

        artifacts["glider"]["by_value"][value] = {
            "glider_found": info["glider_found"],
            "best": best,
        }
        status = "FOUND" if best else "none"
        speed_str = f"v={best['speed']:.4f}" if best else "—"
        print(f"  v={value}: {status} {speed_str}")

    print("\n=== Experiment B: Two-Particle Scattering ===")
    scatter_pairs = [(2, 3), (2, 4), (2, 6), (3, 6), (4, 6), (3, 4)]
    conserved_count = 0
    artifacts["scattering"]["pairs"] = {}

    for vl, vr in scatter_pairs:
        png_path = output_dir / f"p49_z7_scattering_{vl}_{vr}.png"
        result = scattering_experiment(vl, vr, save_path=png_path)
        artifacts["png_files"].append(str(png_path))
        if result["conserved"]:
            conserved_count += 1
        artifacts["scattering"]["pairs"][f"{vl}_{vr}"] = {
            "winding_before": result["winding_before"],
            "winding_after": result["winding_after"],
            "conserved": result["conserved"],
        }
        print(
            f"  ({vl},{vr}): winding {result['winding_before']}→{result['winding_after']}, "
            f"conserved={result['conserved']}"
        )

    n_pairs = len(scatter_pairs)
    rate = conserved_count / n_pairs if n_pairs else 0.0
    artifacts["scattering"]["conservation_rate"] = rate
    artifacts["scattering"]["pass_80pct"] = rate >= 0.8
    print(f"  Conservation rate: {conserved_count}/{n_pairs} = {rate:.1%}")

    print("\n=== Experiment C: Sector Color Comparison ===")
    comparison = color_comparison_experiment(L=56, steps=56)
    cmp_path = output_dir / "p49_z7_color_comparison.png"
    save_color_comparison_figure(comparison, cmp_path)
    artifacts["png_files"].append(str(cmp_path))

    summary = comparison["_summary"]
    artifacts["color"] = {
        "distinguishable": summary["distinguishable"],
        "pairs": summary["pair_comparisons"],
        "per_value": {
            v: {
                "spread_rate": comparison[v]["spread_rate"],
                "max_spread": comparison[v]["max_spread"],
                "final_unique_values": comparison[v]["final_unique_values"],
                "glider_candidates": comparison[v]["glider_candidates"],
            }
            for v in [2, 3, 4, 5, 6]
        },
    }
    print(f"  Sectors distinguishable: {summary['distinguishable']}")
    for v in [2, 3, 4, 5, 6]:
        print(
            f"  v={v}: spread_rate={comparison[v]['spread_rate']:.3f}, "
            f"max_spread={comparison[v]['max_spread']}"
        )

    json_path = SCRIPT_DIR / "z7_sector_dynamics_results.json"

    def _json_safe(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        raise TypeError(type(obj))

    with open(json_path, "w") as f:
        json.dump(
            {
                "glider_summary": artifacts["glider"],
                "scattering": artifacts["scattering"],
                "color": artifacts["color"],
            },
            f,
            indent=2,
            default=_json_safe,
        )
    artifacts["json_path"] = str(json_path)

    return artifacts


def main() -> None:
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    t0 = time.time()

    try:
        artifacts = run_all_experiments()
        elapsed = time.time() - t0
        print(f"\nDone in {elapsed:.1f}s. PNG files: {len(artifacts['png_files'])}")
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
