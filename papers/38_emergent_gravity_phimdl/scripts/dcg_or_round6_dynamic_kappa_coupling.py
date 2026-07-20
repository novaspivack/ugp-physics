#!/usr/bin/env python3
"""
dcg_or_round6_dynamic_kappa_coupling.py
EPIC_073 Rank 64-DCG-OR Round 6 — Dynamical f(κ) edge-weight coupling

Tests Sakharov-style discrete gravity: local OR curvature κ backreacts on Rule 110
dynamics via κ-weighted update rules. Two A-gliders at d=10 separation evolved for
T=100 steps under:
  - standard Rule 110 (control)
  - κ-XOR coupling: c'(x) = f(...) XOR (κ(x,t) > threshold)
  - κ-probabilistic coupling: flip standard outcome with p=0.01 when κ > threshold

κ computed from deviation-based OR (Round 4 prescription) using standard one-step
lookahead on the causal graph.

Observables: tracked glider separation, geodesic deviation (graph distance between
SD-region centroids), attraction vs standard control.

EPIC_073 / Rank 64-DCG-OR Round 6
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
L = 200
T = 100
BASE_CENTER = 100
INITIAL_SEPARATION = 10
EPS_DEV = 0.1
T_BURN = 10
KAPPA_THRESHOLD = 0.5  # matter vs vacuum discriminator (EE=0, SD≈0.769)
P_FLIP = 0.01
RNG_SEED = 42

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}


def rule110_out(tape: np.ndarray, x: int) -> int:
    n = len(tape)
    return RULE110[(tape[(x - 1) % n], tape[x], tape[(x + 1) % n])]


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
    return embed_glider(out, center2)


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
    """P36/Gorard deviation-based OR on spacelike edge (t,x)–(t,x+1)."""
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
    if t + 1 >= len(spacetime):
        return "PE" if is_glider_cell(t, x, spacetime, length) else "EE"
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


def circular_distance(a: int, b: int, length: int) -> int:
    d = abs(a - b)
    return min(d, length - d)


def glider_centers_at_time(t: int, spacetime: np.ndarray, length: int, seed1: int, seed2: int):
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


def sd_region_centroid(t: int, spacetime: np.ndarray, length: int, seed: int) -> int:
    """Centroid of SD-type edges near a glider seed at time t."""
    c, _ = glider_centers_at_time(t, spacetime, length, seed, (seed + 50) % length)
    sd_cells = []
    for x in range(length):
        if causal_nbhd_type(t, x, spacetime, length) == "SD":
            if circular_distance(x, c, length) <= 6:
                sd_cells.append(x)
    if not sd_cells:
        return c
    return int(round(float(np.mean(sd_cells)))) % length


def compute_kappa_field(t: int, tape: np.ndarray, tape_next_std: np.ndarray) -> np.ndarray:
    """κ(x) at time t using standard one-step lookahead for OR weights."""
    sp = np.zeros((2, len(tape)), dtype=np.int8)
    sp[0] = tape
    sp[1] = tape_next_std
    kappa = np.zeros(len(tape), dtype=float)
    for x in range(len(tape)):
        k = ollivier_ricci_dev(0, x, sp, len(tape))
        kappa[x] = k if k is not None else 0.0
    return kappa


def rule110_step_standard(tape: np.ndarray) -> np.ndarray:
    n = len(tape)
    return np.array([rule110_out(tape, i) for i in range(n)], dtype=np.int8)


def rule110_step_kappa_xor(tape: np.ndarray, t: int, threshold: float = KAPPA_THRESHOLD) -> np.ndarray:
    tape_next_std = rule110_step_standard(tape)
    kappa = compute_kappa_field(t, tape, tape_next_std)
    n = len(tape)
    out = np.zeros(n, dtype=np.int8)
    for x in range(n):
        std = rule110_out(tape, x)
        if kappa[x] > threshold:
            out[x] = std ^ 1
        else:
            out[x] = std
    return out


def rule110_step_kappa_prob(
    tape: np.ndarray, t: int, rng: np.random.Generator, threshold: float = KAPPA_THRESHOLD, p_flip: float = P_FLIP
) -> np.ndarray:
    tape_next_std = rule110_step_standard(tape)
    kappa = compute_kappa_field(t, tape, tape_next_std)
    n = len(tape)
    out = np.zeros(n, dtype=np.int8)
    for x in range(n):
        std = rule110_out(tape, x)
        if kappa[x] > threshold and rng.random() < p_flip:
            out[x] = std ^ 1
        else:
            out[x] = std
    return out


def evolve(mode: str, tape0: np.ndarray, steps: int, center1: int, center2: int, rng=None):
    """Evolve tape and record separation / geodesic observables."""
    spacetime = np.zeros((steps + 1, len(tape0)), dtype=np.int8)
    spacetime[0] = tape0
    tape = tape0.copy()

    separations = []
    geodesic_distances = []
    kappa_at_centers = []

    for t in range(steps):
        if mode == "standard":
            tape = rule110_step_standard(tape)
        elif mode == "kappa_xor":
            tape = rule110_step_kappa_xor(tape, t)
        elif mode == "kappa_prob":
            tape = rule110_step_kappa_prob(tape, t, rng)
        else:
            raise ValueError(f"unknown mode: {mode}")

        spacetime[t + 1] = tape

        c1, c2 = glider_centers_at_time(t + 1, spacetime, L, center1, center2)
        sep = circular_distance(c1, c2, L)
        separations.append(sep)

        sd1 = sd_region_centroid(t + 1, spacetime, L, center1)
        sd2 = sd_region_centroid(t + 1, spacetime, L, center2)
        geodesic_distances.append(circular_distance(sd1, sd2, L))

        if t + 1 < steps:
            tape_next_std = rule110_step_standard(tape)
            k1 = ollivier_ricci_dev(0, c1, np.vstack([tape, tape_next_std]), L)
            k2 = ollivier_ricci_dev(0, c2, np.vstack([tape, tape_next_std]), L)
            kappa_at_centers.append({"t": t + 1, "kappa_c1": k1, "kappa_c2": k2})

    return {
        "spacetime_shape": list(spacetime.shape),
        "separations": separations,
        "geodesic_distances": geodesic_distances,
        "initial_separation": separations[0] if separations else None,
        "final_separation": separations[-1] if separations else None,
        "mean_separation_post_burn": float(np.mean(separations[T_BURN:])) if len(separations) > T_BURN else None,
        "std_separation_post_burn": float(np.std(separations[T_BURN:], ddof=1)) if len(separations[T_BURN:]) > 1 else 0.0,
        "initial_geodesic": geodesic_distances[0] if geodesic_distances else None,
        "final_geodesic": geodesic_distances[-1] if geodesic_distances else None,
        "mean_geodesic_post_burn": float(np.mean(geodesic_distances[T_BURN:])) if len(geodesic_distances) > T_BURN else None,
        "separation_delta": (separations[-1] - separations[0]) if separations else None,
        "geodesic_delta": (geodesic_distances[-1] - geodesic_distances[0]) if geodesic_distances else None,
        "separation_trend_slope": float(np.polyfit(range(len(separations[T_BURN:])), separations[T_BURN:], 1)[0])
        if len(separations[T_BURN:]) > 1
        else None,
        "geodesic_trend_slope": float(np.polyfit(range(len(geodesic_distances[T_BURN:])), geodesic_distances[T_BURN:], 1)[0])
        if len(geodesic_distances[T_BURN:]) > 1
        else None,
    }


def evaluate_attraction(standard, kappa_xor, kappa_prob, initial_d: int):
    """Compare κ-weighted dynamics against standard control."""

    def attraction_metrics(run, label):
        sep_delta = run["separation_delta"]
        geo_delta = run["geodesic_delta"]
        sep_slope = run["separation_trend_slope"]
        geo_slope = run["geodesic_trend_slope"]
        final_sep = run["final_separation"]
        attracted = (
            sep_delta is not None
            and sep_delta < 0
            and sep_slope is not None
            and sep_slope < 0
        )
        geodesic_converging = (
            geo_delta is not None
            and geo_delta < 0
            and geo_slope is not None
            and geo_slope < 0
        )
        return {
            "mode": label,
            "initial_separation": run["initial_separation"],
            "final_separation": final_sep,
            "separation_delta": sep_delta,
            "separation_trend_slope": sep_slope,
            "initial_geodesic": run["initial_geodesic"],
            "final_geodesic": run["final_geodesic"],
            "geodesic_delta": geo_delta,
            "geodesic_trend_slope": geo_slope,
            "mean_separation_post_burn": run["mean_separation_post_burn"],
            "mean_geodesic_post_burn": run["mean_geodesic_post_burn"],
            "attraction_by_separation": attracted,
            "geodesic_convergence": geodesic_converging,
        }

    std_m = attraction_metrics(standard, "standard")
    xor_m = attraction_metrics(kappa_xor, "kappa_xor")
    prob_m = attraction_metrics(kappa_prob, "kappa_prob")

    std_sep_delta = std_m["separation_delta"]
    xor_sep_delta = xor_m["separation_delta"]
    prob_sep_delta = prob_m["separation_delta"]

    xor_beats_std = (
        xor_sep_delta is not None
        and std_sep_delta is not None
        and xor_sep_delta < std_sep_delta - 1.0
    )
    prob_beats_std = (
        prob_sep_delta is not None
        and std_sep_delta is not None
        and prob_sep_delta < std_sep_delta - 1.0
    )

    binding_confirmed = bool(
        (xor_m["attraction_by_separation"] and xor_beats_std)
        or (prob_m["attraction_by_separation"] and prob_beats_std)
    )

    geodesic_confirmed = bool(
        (xor_m["geodesic_convergence"] and xor_m["geodesic_delta"] < std_m["geodesic_delta"] - 1.0)
        or (prob_m["geodesic_convergence"] and prob_m["geodesic_delta"] < std_m["geodesic_delta"] - 1.0)
    )

    print("\n=== Attraction evaluation ===")
    for m in [std_m, xor_m, prob_m]:
        print(
            f"  {m['mode']:12s}: sep {m['initial_separation']}→{m['final_separation']} "
            f"(Δ={m['separation_delta']}, slope={m['separation_trend_slope']:.4f}); "
            f"geo {m['initial_geodesic']}→{m['final_geodesic']} "
            f"(Δ={m['geodesic_delta']}, slope={m['geodesic_trend_slope']:.4f}); "
            f"attraction={m['attraction_by_separation']}"
        )
    print(f"  κ-weighted beats standard (sep Δ > 1 cell): xor={xor_beats_std}, prob={prob_beats_std}")
    print(f"  Binding confirmed (CatAD gate): {binding_confirmed}")
    print(f"  Geodesic convergence confirmed: {geodesic_confirmed}")

    return {
        "standard": std_m,
        "kappa_xor": xor_m,
        "kappa_prob": prob_m,
        "kappa_xor_beats_standard": xor_beats_std,
        "kappa_prob_beats_standard": prob_beats_std,
        "binding_confirmed": binding_confirmed,
        "geodesic_convergence_confirmed": geodesic_confirmed,
        "cat_level_if_confirmed": "CatAD",
        "cat_level_if_not_confirmed": "CatA",
    }


def plot_trajectories(standard, kappa_xor, kappa_prob, out_path):
    t_axis = np.arange(1, T + 1)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    for run, label, color in [
        (standard, "standard", "C0"),
        (kappa_xor, "κ-XOR", "C1"),
        (kappa_prob, "κ-prob", "C2"),
    ]:
        axes[0].plot(t_axis, run["separations"], label=label, color=color, linewidth=1.5)
        axes[1].plot(t_axis, run["geodesic_distances"], label=label, color=color, linewidth=1.5)

    axes[0].axhline(INITIAL_SEPARATION, color="gray", linestyle=":", alpha=0.6, label="initial d=10")
    axes[0].set_ylabel("Glider center separation (cells)")
    axes[0].set_title("64-DCG-OR Round 6: Dynamical κ-weighted Rule 110 coupling")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].set_ylabel("SD-region centroid graph distance (cells)")
    axes[1].set_xlabel("Time step t")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Plot saved to {out_path}")


def main():
    t0 = time.time()
    print("=" * 70)
    print("64-DCG-OR Round 6: Dynamical κ-weighted Rule 110 coupling")
    print("=" * 70)

    d = INITIAL_SEPARATION
    center1 = (BASE_CENTER - d // 2) % L
    center2 = (BASE_CENTER + d // 2) % L
    tape0 = embed_two_gliders(make_ether_tape(L), center1, center2)
    rng = np.random.default_rng(RNG_SEED)

    print(f"Initial glider centers: {center1}, {center2} (d={d})")
    print(f"κ threshold={KAPPA_THRESHOLD}, p_flip={P_FLIP}, T={T}, t_burn={T_BURN}")

    standard = evolve("standard", tape0, T, center1, center2)
    kappa_xor = evolve("kappa_xor", tape0, T, center1, center2)
    kappa_prob = evolve("kappa_prob", tape0, T, center1, center2, rng=rng)

    evaluation = evaluate_attraction(standard, kappa_xor, kappa_prob, d)

    plot_path = "dcg_or_round6_dynamic_kappa_coupling.png"
    plot_trajectories(standard, kappa_xor, kappa_prob, plot_path)

    results = {
        "rank": "64-DCG-OR",
        "round": 6,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "ETHER": ETHER,
            "GLIDER": GLIDER,
            "L": L,
            "T": T,
            "initial_separation_d": d,
            "base_center": BASE_CENTER,
            "glider_center1": center1,
            "glider_center2": center2,
            "kappa_threshold": KAPPA_THRESHOLD,
            "p_flip": P_FLIP,
            "eps_dev": EPS_DEV,
            "t_burn": T_BURN,
            "rng_seed": RNG_SEED,
            "timeout_s": TIMEOUT_S,
            "coupling_variants": ["standard", "kappa_xor", "kappa_prob"],
        },
        "runs": {
            "standard": standard,
            "kappa_xor": kappa_xor,
            "kappa_prob": kappa_prob,
        },
        "evaluation": evaluation,
        "runtime_s": time.time() - t0,
    }

    out_path = "dcg_or_round6_dynamic_kappa_coupling_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Runtime: {results['runtime_s']:.1f}s")

    signal.alarm(0)


if __name__ == "__main__":
    main()
