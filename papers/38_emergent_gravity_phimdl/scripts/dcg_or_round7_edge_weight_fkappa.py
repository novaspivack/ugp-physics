#!/usr/bin/env python3
"""
dcg_or_round7_edge_weight_fkappa.py
EPIC_073 Rank 64-DCG-OR Round 7 — Proper edge-weight f(κ) Sakharov gravity test

Instead of perturbing cell values (Rounds 5–6), modify causal-graph edge weights
w(e) = f(κ(e)) and measure weighted geodesic distance between SD-regions.

Prescriptions:
  f_exp(κ) = exp(α·κ)           for α ∈ {0.1, 0.5, 1.0, 2.0}
  f_inv(κ) = 1/(1 + β·|κ|)      for β ∈ {0.1, 0.5, 1.0}

Null test: same f(κ) weighting on two ETHER (EE) regions at equal Euclidean d.

EPIC_073 / Rank 64-DCG-OR Round 7
"""

import heapq
import json
import math
import signal
import sys
import time
from collections import defaultdict

import numpy as np

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
SD_RADIUS = 8
ALPHA_VALUES = [0.1, 0.5, 1.0, 2.0]
BETA_VALUES = [0.1, 0.5, 1.0]

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
    return embed_glider(embed_glider(tape, center1), center2)


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


def sd_anchor(t: int, spacetime: np.ndarray, length: int, home: int) -> int:
    """Best SD-representative node near fixed glider home position."""
    best_x = home
    best_score = -1.0
    for x in range(length):
        if circular_distance(x, home, length) > SD_RADIUS:
            continue
        if causal_nbhd_type(t, x, spacetime, length) != "SD":
            continue
        # prefer SD edges closest to home
        score = 1.0 / (1.0 + circular_distance(x, home, length))
        if score > best_score:
            best_score = score
            best_x = x
    return best_x


def ee_anchor(t: int, spacetime: np.ndarray, length: int, home: int) -> int:
    """Best EE-representative node near fixed reference position."""
    best_x = home
    best_score = -1.0
    for x in range(length):
        if circular_distance(x, home, length) > SD_RADIUS:
            continue
        if causal_nbhd_type(t, x, spacetime, length) != "EE":
            continue
        score = 1.0 / (1.0 + circular_distance(x, home, length))
        if score > best_score:
            best_score = score
            best_x = x
    return best_x


def build_spacelike_kappa(t: int, spacetime: np.ndarray, length: int):
    """κ and edge endpoints for each spacelike edge at time t."""
    kappa = {}
    for x in range(length):
        k = ollivier_ricci_dev(t, x, spacetime, length)
        if k is None:
            k = 0.0
        kappa[x] = k
    return kappa


def f_exp(kappa: float, alpha: float) -> float:
    return math.exp(alpha * kappa)


def f_inv(kappa: float, beta: float) -> float:
    return 1.0 / (1.0 + beta * abs(kappa))


def build_weighted_ring(length: int, kappa_by_x: dict, weight_fn):
    """Undirected ring at fixed t: edge between x and (x+1)%L with weight from κ at x."""
    adj = defaultdict(list)
    for x in range(length):
        y = (x + 1) % length
        w = weight_fn(kappa_by_x[x])
        adj[x].append((y, w))
        adj[y].append((x, w))
    return adj


def dijkstra_min_dist(adj, sources: set, targets: set) -> float:
    """Minimum weighted distance from any source to any target."""
    if not sources or not targets:
        return float("inf")
    if sources & targets:
        return 0.0
    dist = {s: 0.0 for s in sources}
    heap = [(0.0, s) for s in sources]
    best = float("inf")
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        if u in targets:
            best = min(best, d)
            if d >= best:
                continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return best


def unweighted_ring_dist(length: int, sources: set, targets: set) -> float:
    adj = build_weighted_ring(length, {x: 0.0 for x in range(length)}, lambda k: 1.0)
    return dijkstra_min_dist(adj, sources, targets)


def euclidean_centroid_distance(c1: int, c2: int, length: int) -> int:
    return circular_distance(c1, c2, length)


MIN_SEP = 8
MAX_SEP = 14


def measure_at_time(
    t: int,
    spacetime: np.ndarray,
    length: int,
    center1: int,
    center2: int,
    region_type: str,
):
    """Weighted and unweighted geodesics between fixed-home region anchors at time t."""
    kappa_by_x = build_spacelike_kappa(t, spacetime, length)

    if region_type == "SD":
        anchor1 = sd_anchor(t, spacetime, length, center1)
        anchor2 = sd_anchor(t, spacetime, length, center2)
    else:
        anchor1 = ee_anchor(t, spacetime, length, center1)
        anchor2 = ee_anchor(t, spacetime, length, center2)

    eucl_d = euclidean_centroid_distance(anchor1, anchor2, length)
    if eucl_d < MIN_SEP or eucl_d > MAX_SEP:
        return None

    sources = {anchor1}
    targets = {anchor2}

    d_unweighted = dijkstra_min_dist(
        build_weighted_ring(length, kappa_by_x, lambda k: 1.0),
        sources,
        targets,
    )

    results = {
        "t": t,
        "anchor1": anchor1,
        "anchor2": anchor2,
        "euclidean_d": eucl_d,
        "d_unweighted": d_unweighted,
        "mean_kappa_sd_region": float(
            np.mean([kappa_by_x[x] for x in range(length)
                     if causal_nbhd_type(t, x, spacetime, length) == "SD"])
        ) if any(causal_nbhd_type(t, x, spacetime, length) == "SD" for x in range(length)) else 0.0,
        "weighted": {},
    }

    for alpha in ALPHA_VALUES:
        wfn = lambda k, a=alpha: f_exp(k, a)
        d_w = dijkstra_min_dist(build_weighted_ring(length, kappa_by_x, wfn), sources, targets)
        results["weighted"][f"exp_alpha_{alpha}"] = {
            "d_w": d_w,
            "delta_vs_unweighted": d_w - d_unweighted,
            "shorter_than_unweighted": d_w < d_unweighted,
        }

    for beta in BETA_VALUES:
        wfn = lambda k, b=beta: f_inv(k, b)
        d_w = dijkstra_min_dist(build_weighted_ring(length, kappa_by_x, wfn), sources, targets)
        results["weighted"][f"inv_beta_{beta}"] = {
            "d_w": d_w,
            "delta_vs_unweighted": d_w - d_unweighted,
            "shorter_than_unweighted": d_w < d_unweighted,
        }

    return results


def aggregate_time_series(series: list, label: str):
    """Aggregate per-time measurements into summary statistics."""
    if not series:
        return {"label": label, "n_times": 0}

    eucl_d = series[0]["euclidean_d"]
    d_unw = [s["d_unweighted"] for s in series if math.isfinite(s["d_unweighted"])]
    summary = {
        "label": label,
        "n_times": len(series),
        "euclidean_d": eucl_d,
        "d_unweighted_mean": float(np.mean(d_unw)) if d_unw else None,
        "d_unweighted_min": float(np.min(d_unw)) if d_unw else None,
        "couplings": {},
    }

    all_keys = set()
    for s in series:
        all_keys.update(s["weighted"].keys())

    for key in sorted(all_keys):
        d_ws = [s["weighted"][key]["d_w"] for s in series if key in s["weighted"]]
        shorts = [s["weighted"][key]["shorter_than_unweighted"] for s in series if key in s["weighted"]]
        summary["couplings"][key] = {
            "d_w_mean": float(np.mean(d_ws)),
            "d_w_min": float(np.min(d_ws)),
            "d_w_max": float(np.max(d_ws)),
            "delta_vs_unweighted_mean": float(np.mean([w - u for w, u in zip(d_ws, d_unw)])),
            "any_shorter_than_unweighted": any(shorts),
            "fraction_shorter": float(np.mean(shorts)),
        }

    return summary


def evaluate_differential(matter_summary, ether_summary, euclidean_d: int):
    """Check whether matter geodesics shorten differentially vs ether null."""
    evaluation = {
        "euclidean_d": euclidean_d,
        "matter": matter_summary,
        "ether_null": ether_summary,
        "per_coupling": {},
        "differential_shortening_confirmed": False,
        "best_matter_shortening": None,
    }

    matter_keys = set(matter_summary.get("couplings", {}))
    for key in sorted(matter_keys):
        m = matter_summary["couplings"][key]
        e = ether_summary["couplings"].get(key, {})
        m_mean = m["d_w_mean"]
        e_mean = e.get("d_w_mean", float("inf"))
        d_unw_m = matter_summary["d_unweighted_mean"]
        d_unw_e = ether_summary.get("d_unweighted_mean")
        matter_shortens = (
            m_mean < d_unw_m - 0.01
            if d_unw_m is not None and math.isfinite(d_unw_m)
            else False
        )
        ether_shortens = (
            e_mean < d_unw_e - 0.01
            if d_unw_e is not None and math.isfinite(d_unw_e)
            else False
        )
        matter_beats_ether = m_mean < e_mean - 0.01

        differential = matter_shortens and matter_beats_ether and not (
            ether_shortens and e_mean <= m_mean
        )

        evaluation["per_coupling"][key] = {
            "matter_d_w_mean": m_mean,
            "matter_d_unweighted_mean": d_unw_m,
            "ether_d_w_mean": e_mean,
            "ether_d_unweighted_mean": d_unw_e,
            "matter_shorter_than_unweighted": matter_shortens,
            "ether_shorter_than_unweighted": ether_shortens,
            "matter_beats_ether_null": matter_beats_ether,
            "differential_shortening": differential,
        }

        if differential and (
            evaluation["best_matter_shortening"] is None
            or m_mean < evaluation["best_matter_shortening"]["d_w_mean"]
        ):
            evaluation["best_matter_shortening"] = {
                "coupling": key,
                "d_w_mean": m_mean,
                "d_unweighted_mean": d_unw_m,
            }

    evaluation["differential_shortening_confirmed"] = any(
        v["differential_shortening"] for v in evaluation["per_coupling"].values()
    )
    return evaluation


def run_scenario(label: str, tape0: np.ndarray, center1: int, center2: int, region_type: str):
    spacetime = evolve_spacetime(tape0, T)
    series = []
    for t in range(T_BURN, T):
        m = measure_at_time(t, spacetime, L, center1, center2, region_type)
        if m is not None and math.isfinite(m["d_unweighted"]):
            series.append(m)
    return aggregate_time_series(series, label), series


def main():
    t0 = time.time()
    print("=" * 70)
    print("64-DCG-OR Round 7: Edge-weight f(κ) Sakharov gravity test")
    print("=" * 70)

    d = INITIAL_SEPARATION
    center1 = (BASE_CENTER - d // 2) % L
    center2 = (BASE_CENTER + d // 2) % L

    print(f"Glider centers: {center1}, {center2} (d={d})")
    print(f"α ∈ {ALPHA_VALUES}, β ∈ {BETA_VALUES}")
    print(f"T={T}, t_burn={T_BURN}, SD_radius={SD_RADIUS}")

    # ── Matter scenario: two A-gliders ───────────────────────────────────────
    tape_matter = embed_two_gliders(make_ether_tape(L), center1, center2)
    matter_summary, matter_series = run_scenario(
        "two_gliders_SD", tape_matter, center1, center2, "SD"
    )

    # ── Null test: pure ether, EE regions at same separation ───────────────────
    tape_ether = make_ether_tape(L)
    ether_summary, ether_series = run_scenario(
        "ether_EE_null", tape_ether, center1, center2, "EE"
    )

    evaluation = evaluate_differential(matter_summary, ether_summary, d)

    print("\n=== Matter (two gliders, SD regions) ===")
    print(f"  Euclidean d = {matter_summary['euclidean_d']}")
    print(f"  d_unweighted mean = {matter_summary['d_unweighted_mean']}")
    for key, c in sorted(matter_summary["couplings"].items()):
        print(
            f"  {key}: d_w_mean={c['d_w_mean']:.4f}, "
            f"Δ={c['delta_vs_unweighted_mean']:.4f}, "
            f"shorter={c['any_shorter_than_unweighted']}"
        )

    print("\n=== Null (pure ether, EE regions) ===")
    print(f"  d_unweighted mean = {ether_summary['d_unweighted_mean']}")
    for key, c in sorted(ether_summary["couplings"].items()):
        print(
            f"  {key}: d_w_mean={c['d_w_mean']:.4f}, "
            f"Δ={c['delta_vs_unweighted_mean']:.4f}, "
            f"shorter={c['any_shorter_than_unweighted']}"
        )

    print("\n=== Differential shortening evaluation ===")
    for key, ev in sorted(evaluation["per_coupling"].items()):
        print(
            f"  {key}: matter_d_w={ev['matter_d_w_mean']:.4f}, "
            f"ether_d_w={ev['ether_d_w_mean']:.4f}, "
            f"differential={ev['differential_shortening']}"
        )
    print(f"  CONFIRMED: {evaluation['differential_shortening_confirmed']}")

    inv_confirmed = any(
        evaluation["per_coupling"].get(k, {}).get("differential_shortening", False)
        for k in evaluation["per_coupling"]
        if k.startswith("inv_beta")
    )
    exp_confirmed = any(
        evaluation["per_coupling"].get(k, {}).get("differential_shortening", False)
        for k in evaluation["per_coupling"]
        if k.startswith("exp_alpha")
    )
    if inv_confirmed and not exp_confirmed:
        cat_level = "CatA (partial — inv f(κ) static metric signal; exp f(κ) negative)"
    elif evaluation["differential_shortening_confirmed"]:
        cat_level = "CatAD"
    else:
        cat_level = "CatA (negative)"

    results = {
        "rank": "64-DCG-OR",
        "round": 7,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "ETHER": ETHER,
            "GLIDER": GLIDER,
            "L": L,
            "T": T,
            "initial_separation_d": d,
            "center1": center1,
            "center2": center2,
            "alpha_values": ALPHA_VALUES,
            "beta_values": BETA_VALUES,
            "eps_dev": EPS_DEV,
            "t_burn": T_BURN,
            "sd_radius": SD_RADIUS,
            "timeout_s": TIMEOUT_S,
            "weight_prescriptions": {
                "exp": "f(κ) = exp(α·κ)",
                "inv": "f(κ) = 1/(1 + β·|κ|)",
            },
        },
        "matter_two_gliders_SD": matter_summary,
        "ether_null_EE": ether_summary,
        "evaluation": evaluation,
        "cat_level_round7": cat_level,
        "static_or_cat_a_unchanged": True,
        "runtime_s": time.time() - t0,
    }

    out_path = "dcg_or_round7_edge_weight_fkappa_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Runtime: {results['runtime_s']:.1f}s")
    print(f"Round 7 cat level: {cat_level}")

    signal.alarm(0)


if __name__ == "__main__":
    main()
