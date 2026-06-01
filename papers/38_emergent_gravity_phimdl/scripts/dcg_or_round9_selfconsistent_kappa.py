#!/usr/bin/env python3
"""
dcg_or_round9_selfconsistent_kappa.py
EPIC_073 Rank 64-DCG-R9 — Self-consistent Gorard κ iteration

Round 8 found single-pass inv f(κ) weighting does not produce timelike geodesic
convergence. Round 9 iterates: compute κ → w=1/(1+β|κ|) → recompute κ on weighted
graph until fixed point (max|Δκ| < ε), then retest timelike geodesic deviation.

EPIC_073 / Rank 64-DCG-R9
"""

import heapq
import json
import math
import signal
import sys
import time
from collections import defaultdict

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
INITIAL_GLIDER_SEP = 10
INITIAL_PATH_SEP = 2
BETA_VALUES = [0.5, 1.0, 2.0]
BETA_PRIMARY = 1.0
EPS_DEV = 0.1
T_BURN = 10
SD_RADIUS = 8
PATH_RADIUS = 4
MAX_ITER = 20
KAPPA_EPS = 0.01

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


def deviation_masses(t: int, x: int, spacetime: np.ndarray, length: int, eps: float = EPS_DEV):
    """Neighbor deviation masses for OR at spacelike edge (t,x)–(t,x+1)."""
    if t + 1 >= len(spacetime):
        return None, None
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
    return ([w / z1 for w in w1], p1), ([w / z2 for w in w2], p2)


def ollivier_ricci_dev_weighted(
    t: int,
    x: int,
    spacetime: np.ndarray,
    length: int,
    edge_weight: float,
    eps: float = EPS_DEV,
) -> float:
    """Deviation-based OR with metric edge weight d: κ = 1 − W₁/d."""
    masses = deviation_masses(t, x, spacetime, length, eps)
    if masses[0] is None:
        return 0.0
    (m1, p1), (m2, p2) = masses
    w1 = wasserstein1d(m1, p1, m2, p2)
    d = max(edge_weight, 1e-9)
    return 1.0 - w1 / d


def ollivier_ricci_dev(t: int, x: int, spacetime: np.ndarray, length: int, eps: float = EPS_DEV):
    return ollivier_ricci_dev_weighted(t, x, spacetime, length, 1.0, eps)


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


def f_inv(kappa: float, beta: float) -> float:
    return 1.0 / (1.0 + beta * abs(kappa))


def iterate_kappa_fixed_point(spacetime: np.ndarray, length: int, beta: float):
    """
    Self-consistent Gorard iteration on spacelike edges per time slice.
    Returns per-t kappa, edge weights, and convergence stats.
    """
    t_max = len(spacetime) - 1
    all_kappa = {}
    all_weights = {}
    convergence_log = []

    for t in range(t_max):
        weights_t = {x: 1.0 for x in range(length)}
        kappa_t = {x: ollivier_ricci_dev(t, x, spacetime, length) for x in range(length)}

        converged = False
        n_iters = 0
        final_delta = float("nan")

        for it in range(MAX_ITER):
            n_iters = it + 1
            kappa_old = dict(kappa_t)
            kappa_new = {}
            for x in range(length):
                w_edge = f_inv(kappa_old[x], beta)
                kappa_new[x] = ollivier_ricci_dev_weighted(
                    t, x, spacetime, length, w_edge
                )
            weights_t = {x: f_inv(kappa_new[x], beta) for x in range(length)}
            kappa_t = kappa_new
            final_delta = max(abs(kappa_t[x] - kappa_old[x]) for x in range(length))
            if final_delta < KAPPA_EPS:
                converged = True
                break

        all_kappa[t] = kappa_t
        all_weights[t] = weights_t
        convergence_log.append(
            {
                "t": t,
                "n_iters": n_iters,
                "converged": converged,
                "final_delta_kappa": final_delta,
                "mean_kappa_sd": _mean_kappa_type(t, kappa_t, spacetime, length, "SD"),
                "mean_kappa_ee": _mean_kappa_type(t, kappa_t, spacetime, length, "EE"),
            }
        )

    summary = {
        "max_iter": MAX_ITER,
        "kappa_eps": KAPPA_EPS,
        "n_time_slices": t_max,
        "n_converged": sum(1 for c in convergence_log if c["converged"]),
        "mean_iters": float(np.mean([c["n_iters"] for c in convergence_log])),
        "max_final_delta": max(c["final_delta_kappa"] for c in convergence_log),
        "per_t_sample": convergence_log[:: max(1, t_max // 10)][:11],
    }
    return all_kappa, all_weights, summary


def _mean_kappa_type(t, kappa_t, spacetime, length, target):
    vals = []
    for x in range(length):
        if causal_nbhd_type(t, x, spacetime, length) == target:
            vals.append(kappa_t[x])
    return float(np.mean(vals)) if vals else float("nan")


def build_full_causal_graph(spacetime: np.ndarray, kappa_by_t: dict, weights_by_t: dict, beta: float):
    """Full Lorentzian causal graph with fixed-point inv f(κ) edge weights."""
    T_max, length = spacetime.shape
    T_max -= 1
    adj = defaultdict(list)

    def add_edge(u, v, w):
        adj[u].append((v, w))
        adj[v].append((u, w))

    for t in range(T_max):
        kappa_t = kappa_by_t[t]
        weights_t = weights_by_t[t]
        for x in range(length):
            k = kappa_t[x]
            w = weights_t[x]
            u = (t, x)
            add_edge(u, (t + 1, x), w)
            add_edge(u, (t + 1, (x + 1) % length), w)
            add_edge(u, (t + 1, (x - 1) % length), w)
        for x in range(length):
            add_edge((t, x), (t, (x + 1) % length), weights_t[x])

    return adj


def region_anchor(t: int, spacetime: np.ndarray, length: int, home: int, region_type: str) -> int:
    target = "SD" if region_type == "SD" else "EE"
    best_x = home
    best_score = -1.0
    for x in range(length):
        if circular_distance(x, home, length) > SD_RADIUS:
            continue
        if causal_nbhd_type(t, x, spacetime, length) != target:
            continue
        score = 1.0 / (1.0 + circular_distance(x, home, length))
        if score > best_score:
            best_score = score
            best_x = x
    return best_x


def forward_neighbors(node, adj):
    t, x = node
    nbrs = []
    for v, w in adj.get(node, []):
        if v[0] > t:
            nbrs.append((v, w))
    return nbrs


def trace_timelike_geodesic(
    spacetime: np.ndarray,
    adj,
    start_t: int,
    start_x: int,
    end_t: int,
    home_x: int,
    region_type: str,
    length: int,
):
    path = [(start_t, start_x)]
    current = (start_t, start_x)
    for t in range(start_t, end_t):
        candidates = forward_neighbors(current, adj)
        if not candidates:
            anchor = region_anchor(t + 1, spacetime, length, home_x, region_type)
            path.append((t + 1, anchor))
            current = (t + 1, anchor)
            continue
        best = None
        best_cost = float("inf")
        for v, w in candidates:
            vt, vx = v
            if vt != t + 1:
                continue
            anchor = region_anchor(vt, spacetime, length, home_x, region_type)
            region_penalty = 0.0
            if causal_nbhd_type(vt, vx, spacetime, length) != (
                "SD" if region_type == "SD" else "EE"
            ):
                region_penalty = 0.5
            dist_penalty = 0.1 * circular_distance(vx, anchor, length)
            cost = w + region_penalty + dist_penalty
            if cost < best_cost:
                best_cost = cost
                best = v
        if best is None:
            anchor = region_anchor(t + 1, spacetime, length, home_x, region_type)
            path.append((t + 1, anchor))
            current = (t + 1, anchor)
        else:
            path.append(best)
            current = best
    return path


def build_spacelike_ring_adj(t: int, weights_t: dict, length: int):
    adj = defaultdict(list)
    for x in range(length):
        y = (x + 1) % length
        w = weights_t[x]
        adj[x].append((y, w))
        adj[y].append((x, w))
    return adj


def dijkstra_dist(adj, source, target) -> float:
    if source == target:
        return 0.0
    dist = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        if u == target:
            return d
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return float("inf")


def separation_timeseries(path_a, path_b, spacetime, adj_full, weights_by_t, length):
    series = []
    for node_a, node_b in zip(path_a, path_b):
        t_a, x_a = node_a
        t_b, x_b = node_b
        if t_a != t_b:
            continue
        t = t_a
        ring_adj = build_spacelike_ring_adj(t, weights_by_t[t], length)
        w_sep = dijkstra_dist(ring_adj, x_a, x_b)
        unw_sep = float(circular_distance(x_a, x_b, length))
        causal_sep = dijkstra_dist(adj_full, node_a, node_b)
        series.append(
            {
                "t": t,
                "x_a": x_a,
                "x_b": x_b,
                "spatial_sep": unw_sep,
                "weighted_spacelike_sep": w_sep,
                "weighted_causal_sep": causal_sep,
            }
        )
    return series


def fit_slope(times, values):
    if len(times) < 3:
        return float("nan"), float("nan")
    t_arr = np.array(times, dtype=float)
    v_arr = np.array(values, dtype=float)
    if np.std(t_arr) < 1e-12:
        return 0.0, float("nan")
    slope, intercept, r, p, se = stats.linregress(t_arr, v_arr)
    return float(slope), float(p)


def jacobi_field_series(
    spacetime, adj_full, weights_by_t, length, home_x, region_type, offset, t_start, t_end
):
    x1 = region_anchor(t_start, spacetime, length, home_x, region_type)
    x2 = region_anchor(t_start, spacetime, length, (home_x + offset) % length, region_type)
    path1 = trace_timelike_geodesic(
        spacetime, adj_full, t_start, x1, t_end, home_x, region_type, length
    )
    path2 = trace_timelike_geodesic(
        spacetime,
        adj_full,
        t_start,
        x2,
        t_end,
        (home_x + offset) % length,
        region_type,
        length,
    )
    return separation_timeseries(path1, path2, spacetime, adj_full, weights_by_t, length)


def analyze_path_pair(
    label, spacetime, adj_full, weights_by_t, length, beta, home1, home2, region_type, t_start, t_end
):
    x1 = region_anchor(t_start, spacetime, length, home1, region_type)
    x2 = region_anchor(t_start, spacetime, length, home2, region_type)
    initial_spatial = circular_distance(x1, x2, length)

    path1 = trace_timelike_geodesic(
        spacetime, adj_full, t_start, x1, t_end, home1, region_type, length
    )
    path2 = trace_timelike_geodesic(
        spacetime, adj_full, t_start, x2, t_end, home2, region_type, length
    )
    series = separation_timeseries(path1, path2, spacetime, adj_full, weights_by_t, length)

    times = [s["t"] for s in series]
    w_seps = [s["weighted_spacelike_sep"] for s in series]
    unw_seps = [s["spatial_sep"] for s in series]

    slope_w, p_w = fit_slope(times, w_seps)
    slope_u, p_u = fit_slope(times, unw_seps)

    initial_w = w_seps[0] if w_seps else float("nan")
    final_w = w_seps[-1] if w_seps else float("nan")
    delta_w = final_w - initial_w if w_seps else float("nan")
    convergence = slope_w < -0.001 and delta_w < -0.01

    return {
        "label": label,
        "region_type": region_type,
        "beta": beta,
        "home1": home1,
        "home2": home2,
        "initial_spatial_sep": initial_spatial,
        "n_times": len(series),
        "initial_weighted_sep": initial_w,
        "final_weighted_sep": final_w,
        "delta_weighted_sep": delta_w,
        "slope_weighted_spacelike": slope_w,
        "slope_spatial": slope_u,
        "p_value_slope_weighted": p_w,
        "convergence": convergence,
    }


def evaluate_convergence(matter_results, vacuum_results, beta):
    m = matter_results[beta]["path_pair"]
    v = vacuum_results[beta]["path_pair"]
    m_j = matter_results[beta]["jacobi"]
    v_j = vacuum_results[beta]["jacobi"]

    init_match = abs(m["initial_spatial_sep"] - v["initial_spatial_sep"]) <= 1
    matter_converges = m["convergence"]
    vacuum_flat = abs(v["slope_weighted_spacelike"]) < 0.01 or v["slope_weighted_spacelike"] >= 0
    matter_beats_vacuum = m["slope_weighted_spacelike"] < v["slope_weighted_spacelike"] - 0.005

    jacobi_matter_converges = m_j["slope_weighted_spacelike"] < -0.001
    stat_sig = False
    if math.isfinite(m["p_value_slope_weighted"]):
        stat_sig = m["p_value_slope_weighted"] < 0.05 and matter_beats_vacuum

    catAD = (
        init_match
        and matter_converges
        and vacuum_flat
        and matter_beats_vacuum
        and (stat_sig or abs(m["slope_weighted_spacelike"]) > 0.02)
    )
    catA_partial = matter_beats_vacuum and (matter_converges or jacobi_matter_converges)

    return {
        "beta": beta,
        "initial_sep_match": init_match,
        "matter_slope_dsep_dt": m["slope_weighted_spacelike"],
        "vacuum_slope_dsep_dt": v["slope_weighted_spacelike"],
        "matter_delta_sep": m["delta_weighted_sep"],
        "vacuum_delta_sep": v["delta_weighted_sep"],
        "matter_convergence": matter_converges,
        "vacuum_flat": vacuum_flat,
        "matter_beats_vacuum": matter_beats_vacuum,
        "jacobi_matter_slope": m_j["slope_weighted_spacelike"],
        "jacobi_vacuum_slope": v_j["slope_weighted_spacelike"],
        "jacobi_matter_converges": jacobi_matter_converges,
        "statistically_significant": stat_sig,
        "catAD": catAD,
        "catA_partial": catA_partial,
    }


def run_scenario(scenario_label, tape0, center1, center2, region_type, kappa_by_t, weights_by_t, beta):
    spacetime = evolve_spacetime(tape0, T)
    adj_full = build_full_causal_graph(spacetime, kappa_by_t, weights_by_t, beta)
    t_end = T - 1

    pair = analyze_path_pair(
        f"{scenario_label}_path_pair",
        spacetime,
        adj_full,
        weights_by_t,
        L,
        beta,
        center1,
        center2,
        region_type,
        T_BURN,
        t_end,
    )

    mid = (center1 + center2) // 2
    jacobi = jacobi_field_series(
        spacetime, adj_full, weights_by_t, L, mid, region_type, INITIAL_PATH_SEP, T_BURN, t_end
    )
    j_times = [s["t"] for s in jacobi]
    j_w = [s["weighted_spacelike_sep"] for s in jacobi]
    j_slope, j_p = fit_slope(j_times, j_w)

    return {
        "path_pair": pair,
        "jacobi": {
            "home_mid": mid,
            "offset": INITIAL_PATH_SEP,
            "initial_weighted_sep": j_w[0] if j_w else None,
            "final_weighted_sep": j_w[-1] if j_w else None,
            "slope_weighted_spacelike": j_slope,
            "p_value": j_p,
            "n_times": len(jacobi),
        },
    }


def main():
    t0 = time.time()
    print("=" * 70)
    print("64-DCG-R9: Self-consistent Gorard κ iteration + timelike deviation")
    print("=" * 70)

    d = INITIAL_GLIDER_SEP
    center1 = (BASE_CENTER - d // 2) % L
    center2 = (BASE_CENTER + d // 2) % L
    path_home1 = (center1 - INITIAL_PATH_SEP // 2) % L
    path_home2 = (center1 + INITIAL_PATH_SEP // 2 + 1) % L

    print(f"L={L}, T={T}, glider centers=({center1},{center2}), path homes=({path_home1},{path_home2})")
    print(f"β values: {BETA_VALUES}, MAX_ITER={MAX_ITER}, κ_eps={KAPPA_EPS}")

    tape_matter = embed_two_gliders(make_ether_tape(L), center1, center2)
    tape_vacuum = make_ether_tape(L)
    spacetime_matter = evolve_spacetime(tape_matter, T)
    spacetime_vacuum = evolve_spacetime(tape_vacuum, T)

    all_results = {}
    for beta in BETA_VALUES:
        print(f"\n--- β={beta}: iterating κ on matter graph ---")
        kappa_m, weights_m, conv_m = iterate_kappa_fixed_point(spacetime_matter, L, beta)
        print(
            f"  Matter convergence: {conv_m['n_converged']}/{conv_m['n_time_slices']} slices, "
            f"mean_iters={conv_m['mean_iters']:.2f}, max_Δκ={conv_m['max_final_delta']:.6f}"
        )

        print(f"--- β={beta}: iterating κ on vacuum graph ---")
        kappa_v, weights_v, conv_v = iterate_kappa_fixed_point(spacetime_vacuum, L, beta)
        print(
            f"  Vacuum convergence: {conv_v['n_converged']}/{conv_v['n_time_slices']} slices, "
            f"mean_iters={conv_v['mean_iters']:.2f}, max_Δκ={conv_v['max_final_delta']:.6f}"
        )

        matter_geo = run_scenario(
            "matter_SD", tape_matter, path_home1, path_home2, "SD", kappa_m, weights_m, beta
        )
        vacuum_geo = run_scenario(
            "vacuum_EE", tape_vacuum, path_home1, path_home2, "EE", kappa_v, weights_v, beta
        )
        ev = evaluate_convergence({beta: matter_geo}, {beta: vacuum_geo}, beta)

        print(f"  Matter d(sep)/dt: {ev['matter_slope_dsep_dt']:.6f}, Δsep: {ev['matter_delta_sep']:.4f}")
        print(f"  Vacuum d(sep)/dt: {ev['vacuum_slope_dsep_dt']:.6f}, Δsep: {ev['vacuum_delta_sep']:.4f}")
        print(f"  Matter convergence: {ev['matter_convergence']}, CatAD: {ev['catAD']}")

        all_results[str(beta)] = {
            "kappa_iteration_matter": conv_m,
            "kappa_iteration_vacuum": conv_v,
            "matter_geodesic": matter_geo,
            "vacuum_geodesic": vacuum_geo,
            "evaluation": ev,
        }

    primary = all_results[str(BETA_PRIMARY)]["evaluation"]
    if primary["catAD"]:
        cat_level = "CatAD"
        recommendation = "64-DCG-SAKHAROV: continue — timelike convergence at fixed point"
        follow_on = None
    elif primary["catA_partial"]:
        cat_level = "CatA (partial — weak timelike signal at fixed point)"
        recommendation = "64-DCG-SAKHAROV: provisional — needs stronger confirmation"
        follow_on = None
    else:
        cat_level = "CatA (negative — no timelike convergence at fixed point)"
        recommendation = (
            "Close 64-DCG-SAKHAROV at CatA static (R4); defer dynamical OR gravity to "
            "EPIC_075 Φ_MDL continuum track (075-TMUNU/EFE) as primary gravity path"
        )
        follow_on = None

    results = {
        "rank": "64-DCG-R9",
        "round": 9,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "L": L,
            "T": T,
            "glider_centers": [center1, center2],
            "path_homes": [path_home1, path_home2],
            "initial_glider_sep": d,
            "initial_path_sep": INITIAL_PATH_SEP,
            "beta_values": BETA_VALUES,
            "beta_primary": BETA_PRIMARY,
            "max_iter": MAX_ITER,
            "kappa_eps": KAPPA_EPS,
            "eps_dev": EPS_DEV,
            "t_burn": T_BURN,
            "sd_radius": SD_RADIUS,
            "weight_prescription": "f(κ) = 1/(1 + β|κ|), self-consistent iteration",
            "graph": "spacelike + timelike + lightcone",
            "timeout_s": TIMEOUT_S,
        },
        "results_by_beta": all_results,
        "primary_evaluation": primary,
        "cat_level_round9": cat_level,
        "recommendation_64_DCG_SAKHAROV": recommendation,
        "follow_on_rank": follow_on,
        "runtime_s": time.time() - t0,
    }

    def _json_default(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    out_path = "dcg_or_round9_selfconsistent_kappa_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=_json_default)
    print(f"\nResults written to {out_path}")
    print(f"Runtime: {results['runtime_s']:.1f}s")
    print(f"Round 9 cat level: {cat_level}")
    print(f"Recommendation: {recommendation}")

    signal.alarm(0)


if __name__ == "__main__":
    main()
