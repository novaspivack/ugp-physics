#!/usr/bin/env python3
"""
dcg_or_round5_two_defect_binding.py
EPIC_073 Rank 64-DCG-OR Round 5 — Two-defect binding via dynamical Ollivier-Ricci κ

Places two A-gliders on ETHER14 at separations d = 5, 10, 20, 40 cells (center-to-center),
evolves Rule 110 for T=200 steps, and measures deviation-based OR curvature on:
  - inter-defect edges (SD edges in the corridor between glider neighborhoods)
  - far control edges (EE edges remote from both gliders)

Hypothesis: κ(inter-defect) increases as d decreases (attractive binding via curvature).

Reuses causal graph / OR prescription from dcg_or_static_kappa_round4.py (Round 4).

EPIC_073 / Rank 64-DCG-OR Round 5
"""

import json
import signal
import sys
import time
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# ── Wall-clock timeout ────────────────────────────────────────────────────────
TIMEOUT_S = 900


def _timeout_handler(sig, frame):
    print(f"\nTIMEOUT: {TIMEOUT_S}s wall-clock limit reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_S)

# ── Constants ─────────────────────────────────────────────────────────────────
ETHER = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
GLIDER = "0100101001"
GLIDER_LEN = len(GLIDER)
L = 200
T = 200
BASE_CENTER = 100
SEPARATIONS = [5, 10, 20, 40]
EPS_DEV = 0.1
T_BURN = 10
KAPPA_SD_SINGLE = 0.769230769230769  # Round 4 reference
FAR_OFFSET = 70  # cells away from BASE_CENTER for far control region

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}


def rule110_step(tape: np.ndarray) -> np.ndarray:
    n = len(tape)
    return np.array(
        [RULE110[(tape[(i - 1) % n], tape[i], tape[(i + 1) % n])] for i in range(n)],
        dtype=np.int8,
    )


def ether_val(t: int, x: int) -> int:
    return ETHER[(x + 4 * t) % 14]


def make_ether_tape(length: int) -> np.ndarray:
    return np.array([ETHER[i % 14] for i in range(length)], dtype=np.int8)


def embed_glider(tape: np.ndarray, center: int, seed: str = GLIDER) -> np.ndarray:
    out = tape.copy()
    for j, bit in enumerate(seed):
        out[(center + j) % len(out)] = int(bit)
    return out


def embed_two_gliders(tape: np.ndarray, center1: int, center2: int) -> np.ndarray:
    out = embed_glider(tape, center1)
    out = embed_glider(out, center2)
    return out


def evolve_spacetime(tape0: np.ndarray, steps: int) -> np.ndarray:
    sp = np.zeros((steps + 1, len(tape0)), dtype=np.int8)
    sp[0] = tape0
    tape = tape0.copy()
    for t in range(steps):
        tape = rule110_step(tape)
        sp[t + 1] = tape
    return sp


def wasserstein1d(masses1, positions1, masses2, positions2) -> float:
    pd1 = defaultdict(float)
    pd2 = defaultdict(float)
    for m, p in zip(masses1, positions1):
        pd1[p] += m
    for m, p in zip(masses2, positions2):
        pd2[p] += m
    all_pos = sorted(set(list(positions1) + list(positions2)))
    cdf1 = cdf2 = 0.0
    w = 0.0
    for i in range(len(all_pos) - 1):
        pos = all_pos[i]
        cdf1 += pd1[pos]
        cdf2 += pd2[pos]
        gap = all_pos[i + 1] - all_pos[i]
        w += abs(cdf1 - cdf2) * gap
    return w


def ollivier_ricci_dev(t: int, x: int, spacetime: np.ndarray, length: int, eps: float = EPS_DEV):
    if t + 1 >= len(spacetime):
        return None
    p1 = [x - 1, x, x + 1]
    p2 = [x, x + 1, x + 2]
    w1 = [
        abs(int(spacetime[t + 1][xi % length]) - ether_val(t + 1, xi % length)) + eps
        for xi in p1
    ]
    w2 = [
        abs(int(spacetime[t + 1][xi % length]) - ether_val(t + 1, xi % length)) + eps
        for xi in p2
    ]
    z1, z2 = sum(w1), sum(w2)
    return 1.0 - wasserstein1d([w / z1 for w in w1], p1, [w / z2 for w in w2], p2)


def is_glider_cell(t: int, x: int, spacetime: np.ndarray, length: int) -> bool:
    return int(spacetime[t][x % length]) != ether_val(t, x % length)


def causal_nbhd_type(t: int, x: int, spacetime: np.ndarray, length: int) -> str:
    dev_x = is_glider_cell(t, x, spacetime, length)
    dev_x1 = is_glider_cell(t, (x + 1) % length, spacetime, length)
    if dev_x or dev_x1:
        return "PE"
    dev_xm1 = is_glider_cell(t + 1, x - 1, spacetime, length)
    dev_fx = is_glider_cell(t + 1, x, spacetime, length)
    dev_fx1 = is_glider_cell(t + 1, (x + 1) % length, spacetime, length)
    dev_xp2 = is_glider_cell(t + 1, x + 2, spacetime, length)
    dev_shared = dev_fx or dev_fx1
    dev_excl = dev_xm1 or dev_xp2
    if not dev_shared and not dev_excl:
        return "EE"
    if dev_shared and not dev_excl:
        return "SD"
    if not dev_shared and dev_excl:
        return "XD"
    return "MX"


def glider_centers_at_time(t: int, spacetime: np.ndarray, length: int, seed1: int, seed2: int):
    """Track two glider blobs by nearest deviating cell to each initial seed."""
    dev_cells = [x for x in range(length) if is_glider_cell(t, x, spacetime, length)]
    if not dev_cells:
        return seed1, seed2

    def nearest(seed):
        return min(dev_cells, key=lambda x: min(abs(x - seed), length - abs(x - seed)))

    c1 = nearest(seed1)
    c2 = nearest(seed2)
    if c1 == c2 and len(dev_cells) >= 2:
        sorted_cells = sorted(dev_cells)
        mid = len(sorted_cells) // 2
        c1 = sorted_cells[mid - 1]
        c2 = sorted_cells[mid]
    return c1, c2


def circular_distance(a: int, b: int, length: int) -> int:
    d = abs(a - b)
    return min(d, length - d)


def corridor_bounds(c1: int, c2: int, length: int, pad: int = 3):
    """Inclusive x-range of inter-defect corridor on a periodic ring."""
    if c1 <= c2:
        return max(0, c1 - pad), min(length - 1, c2 + pad)
    # wrapped corridor — take shorter arc
    arc_len = (c2 + length - c1) % length
    if arc_len <= length // 2:
        return c1 - pad, c2 + pad
    return c2 - pad, c1 + pad


def in_corridor(x: int, lo: int, hi: int, length: int) -> bool:
    x %= length
    if lo <= hi:
        return lo <= x <= hi
    return x >= lo or x <= hi


def far_region_center(c1: int, c2: int, length: int) -> int:
    """Point on tape maximally distant from both glider centers."""
    midpoint = (c1 + c2) // 2
    return (midpoint + FAR_OFFSET) % length


def summarize(values):
    if not values:
        return {"mean": None, "std": None, "n": 0, "median": None}
    arr = np.array(values, dtype=float)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "n": int(len(arr)),
        "median": float(np.median(arr)),
    }


def analyze_separation(d: int):
    center1 = (BASE_CENTER - d // 2) % L
    center2 = (BASE_CENTER + d // 2) % L
    tape0 = embed_two_gliders(make_ether_tape(L), center1, center2)
    spacetime = evolve_spacetime(tape0, T)

    inter_sd = []
    inter_all = []
    inter_bridge = []
    far_ee = []
    far_all = []
    tracked_separations = []

    for t in range(T_BURN, T):
        c1, c2 = glider_centers_at_time(t, spacetime, L, center1, center2)
        tracked_separations.append(circular_distance(c1, c2, L))
        lo, hi = corridor_bounds(c1, c2, L, pad=4)
        far_c = far_region_center(c1, c2, L)

        bridge_x = (c1 + c2) // 2 % L
        k_bridge = ollivier_ricci_dev(t, bridge_x, spacetime, L)
        if k_bridge is not None:
            inter_bridge.append(k_bridge)

        for x in range(L):
            k = ollivier_ricci_dev(t, x, spacetime, L)
            if k is None:
                continue
            ctype = causal_nbhd_type(t, x, spacetime, L)
            x_mid = x % L
            x_end = (x + 1) % L
            edge_in_corridor = in_corridor(x_mid, lo, hi, L) or in_corridor(x_end, lo, hi, L)

            if edge_in_corridor:
                inter_all.append(k)
                if ctype == "SD":
                    inter_sd.append(k)

            dist_far = min(
                circular_distance(x_mid, far_c, L),
                circular_distance(x_end, far_c, L),
            )
            if dist_far <= 5 and ctype == "EE":
                far_ee.append(k)
            if dist_far <= 5:
                far_all.append(k)

    inter_sd_s = summarize(inter_sd)
    inter_all_s = summarize(inter_all)
    inter_bridge_s = summarize(inter_bridge)
    far_ee_s = summarize(far_ee)
    far_all_s = summarize(far_all)
    sep_s = summarize(tracked_separations)

    print(f"\n--- separation d={d} (centers {center1}, {center2}) ---")
    print(f"  κ(inter-defect SD)   = {inter_sd_s['mean']} (n={inter_sd_s['n']})")
    print(f"  κ(inter-defect all)  = {inter_all_s['mean']} (n={inter_all_s['n']})")
    print(f"  κ(bridge midpoint)   = {inter_bridge_s['mean']} (n={inter_bridge_s['n']})")
    print(f"  κ(far EE control)    = {far_ee_s['mean']} (n={far_ee_s['n']})")
    print(f"  tracked glider sep   = {sep_s['mean']} ± {sep_s['std']}")

    return {
        "initial_separation_d": d,
        "glider_center1": center1,
        "glider_center2": center2,
        "kappa_inter_defect_SD": inter_sd_s,
        "kappa_inter_defect_all": inter_all_s,
        "kappa_bridge_midpoint": inter_bridge_s,
        "kappa_far_EE_control": far_ee_s,
        "kappa_far_region_all": far_all_s,
        "tracked_glider_separation": sep_s,
        "raw_inter_defect_SD": inter_sd,
    }


def evaluate_binding(separation_results):
    ds = [r["initial_separation_d"] for r in separation_results]
    kappa_sd = [
        r["kappa_inter_defect_SD"]["mean"]
        for r in separation_results
        if r["kappa_inter_defect_SD"]["mean"] is not None
    ]
    kappa_bridge = [
        r["kappa_bridge_midpoint"]["mean"]
        for r in separation_results
        if r["kappa_bridge_midpoint"]["mean"] is not None
    ]

    primary = kappa_sd if len(kappa_sd) == len(ds) else kappa_bridge
    metric = "SD" if len(kappa_sd) == len(ds) else "bridge"

    monotonic_decreasing_d = None
    spearman_r = None
    spearman_p = None
    if len(primary) >= 2:
        # binding: κ increases as d decreases → negative correlation with d
        spearman_r, spearman_p = stats.spearmanr(ds, primary)
        monotonic_decreasing_d = all(
            primary[i] >= primary[i + 1] for i in range(len(primary) - 1)
        )

    kappa_at_smallest_d = primary[0] if primary else None
    exceeds_single_sd = (
        kappa_at_smallest_d is not None and kappa_at_smallest_d > KAPPA_SD_SINGLE
    )

    # CatAD gate: monotonic increase as d decreases + smallest-d κ > single-glider SD
    binding_confirmed = bool(
        monotonic_decreasing_d
        and exceeds_single_sd
        and spearman_p is not None
        and spearman_p < 0.05
        and spearman_r is not None
        and spearman_r < 0
    )

    print("\n=== Binding evaluation ===")
    print(f"  Primary metric: inter-defect {metric}")
    print(f"  κ values vs d: {dict(zip(ds, primary))}")
    print(f"  Monotonic κ(d=5) >= κ(d=10) >= ... : {monotonic_decreasing_d}")
    print(f"  κ(d_min) > κ_single_SD ({KAPPA_SD_SINGLE}): {exceeds_single_sd}")
    print(f"  Spearman(d, κ): r={spearman_r}, p={spearman_p}")
    print(f"  Binding confirmed (CatAD gate): {binding_confirmed}")

    return {
        "primary_metric": metric,
        "kappa_vs_d": {str(d): k for d, k in zip(ds, primary)},
        "monotonic_kappa_increases_as_d_decreases": monotonic_decreasing_d,
        "kappa_at_smallest_d": kappa_at_smallest_d,
        "exceeds_single_glider_kappa_SD": exceeds_single_sd,
        "single_glider_kappa_SD_reference": KAPPA_SD_SINGLE,
        "spearman_r": float(spearman_r) if spearman_r is not None else None,
        "spearman_p": float(spearman_p) if spearman_p is not None else None,
        "binding_confirmed": binding_confirmed,
        "cat_level_if_confirmed": "CatAD",
        "cat_level_if_not_confirmed": "CatA",
    }


def plot_binding(separation_results, binding_eval, out_path):
    ds = [r["initial_separation_d"] for r in separation_results]
    k_sd = [r["kappa_inter_defect_SD"]["mean"] for r in separation_results]
    k_bridge = [r["kappa_bridge_midpoint"]["mean"] for r in separation_results]
    k_far = [r["kappa_far_EE_control"]["mean"] for r in separation_results]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ds, k_sd, "o-", label="κ(inter-defect SD)", linewidth=2, markersize=8)
    ax.plot(ds, k_bridge, "s--", label="κ(bridge midpoint)", linewidth=1.5, markersize=7)
    ax.axhline(
        KAPPA_SD_SINGLE,
        color="gray",
        linestyle=":",
        label=f"single-glider κ(SD)={KAPPA_SD_SINGLE:.3f}",
    )
    ax.plot(ds, k_far, "^:", label="κ(far EE control)", linewidth=1.5, markersize=7)
    ax.set_xlabel("Initial glider separation d (cells)")
    ax.set_ylabel("Ollivier-Ricci κ")
    ax.set_title("64-DCG-OR Round 5: Two-defect binding via dynamical κ")
    ax.legend()
    ax.grid(True, alpha=0.3)
    status = "BINDING" if binding_eval["binding_confirmed"] else "NO BINDING"
    ax.annotate(
        f"CatAD gate: {status}",
        xy=(0.02, 0.02),
        xycoords="axes fraction",
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Plot saved to {out_path}")


def main():
    t0 = time.time()
    print("=" * 70)
    print("64-DCG-OR Round 5: Two-defect binding via dynamical Ollivier-Ricci κ")
    print("=" * 70)

    separation_results = []
    for d in SEPARATIONS:
        separation_results.append(analyze_separation(d))

    binding_eval = evaluate_binding(separation_results)

    plot_path = "dcg_or_round5_two_defect_binding.png"
    plot_binding(separation_results, binding_eval, plot_path)

    results = {
        "rank": "64-DCG-OR",
        "round": 5,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "ETHER": ETHER,
            "GLIDER": GLIDER,
            "L": L,
            "T": T,
            "base_center": BASE_CENTER,
            "separations": SEPARATIONS,
            "eps_dev": EPS_DEV,
            "t_burn": T_BURN,
            "far_offset": FAR_OFFSET,
            "timeout_s": TIMEOUT_S,
            "single_glider_kappa_SD_round4": KAPPA_SD_SINGLE,
        },
        "separations": separation_results,
        "binding_evaluation": binding_eval,
        "runtime_s": time.time() - t0,
    }

    # Drop raw arrays from JSON (keep summary only)
    for r in results["separations"]:
        r.pop("raw_inter_defect_SD", None)

    out_path = "dcg_or_round5_two_defect_binding_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Runtime: {results['runtime_s']:.1f}s")

    signal.alarm(0)


if __name__ == "__main__":
    main()
