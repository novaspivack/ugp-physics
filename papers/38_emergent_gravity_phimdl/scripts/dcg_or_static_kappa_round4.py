#!/usr/bin/env python3
"""
dcg_or_static_kappa_round4.py
EPIC_073 Rank 64-DCG-OR Round 4 — Static Ollivier-Ricci κ on Rule 110 causal graph

Computes static κ (fixed-time spacelike edges on the causal graph) for:
  1. Pure ETHER14 background (L=200, T=50)
  2. A-glider on ETHER14 background (L=200, T=100)

Compares mean κ(glider region) vs mean κ(ether region) with Welch t-test.

Methods:
  A. Gorard/P36 deviation-based OR (rule110_ricci_scaling prescription):
     κ = 1 − W₁(μ_x, μ_{x+1}) with neighbor weights from ether deviation at t+1.
     Pure ether → κ_EE = 0 exactly; glider neighborhoods → κ > 0.
  B. Standard lazy OR on causal-graph spacelike edges:
     κ = 1 − W₁(m_x, m_{x+1}) with lazy random-walk measures (α=0.5).

Glider region: cells where tape ≠ drifting-ether reference (diff-from-reference).
Ether region: cells matching reference at the same (t, x).

EPIC_073 / Rank 64-DCG-OR Round 4
"""

import json
import signal
import sys
import time
from collections import defaultdict

import numpy as np
from scipy import stats
from scipy.optimize import linprog

# ── Wall-clock timeout ────────────────────────────────────────────────────────
TIMEOUT_S = 600


def _timeout_handler(sig, frame):
    print(f"\nTIMEOUT: {TIMEOUT_S}s wall-clock limit reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_S)

# ── Constants ─────────────────────────────────────────────────────────────────
ETHER = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
GLIDER = "0100101001"
L_ETHER = 200
T_ETHER = 50
L_GLIDER = 200
T_GLIDER = 100
GLIDER_CENTER = 100
EPS_DEV = 0.1
ALPHA_LAZY = 0.5
T_BURN = 10  # exclude initial transient from statistics

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}


def rule110_step(tape: np.ndarray) -> np.ndarray:
    L = len(tape)
    return np.array(
        [RULE110[(tape[(i - 1) % L], tape[i], tape[(i + 1) % L])] for i in range(L)],
        dtype=np.int8,
    )


def ether_val(t: int, x: int) -> int:
    """Expected ether value at (t, x) with rightward drift 4 cells/step."""
    return ETHER[(x + 4 * t) % 14]


def make_ether_tape(L: int) -> np.ndarray:
    return np.array([ETHER[i % 14] for i in range(L)], dtype=np.int8)


def embed_glider(tape: np.ndarray, center: int, seed: str = GLIDER) -> np.ndarray:
    out = tape.copy()
    for j, bit in enumerate(seed):
        out[(center + j) % len(out)] = int(bit)
    return out


def evolve_spacetime(tape0: np.ndarray, T: int) -> np.ndarray:
    sp = np.zeros((T + 1, len(tape0)), dtype=np.int8)
    sp[0] = tape0
    tape = tape0.copy()
    for t in range(T):
        tape = rule110_step(tape)
        sp[t + 1] = tape
    return sp


def wasserstein1d(masses1, positions1, masses2, positions2) -> float:
    """Exact W₁ on 1D integer positions via CDF integration."""
    pd1 = defaultdict(float)
    pd2 = defaultdict(float)
    for m, p in zip(masses1, positions1):
        pd1[p] += m
    for m, p in zip(masses2, positions2):
        pd2[p] += m
    all_pos = sorted(set(list(positions1) + list(positions2)))
    cdf1 = cdf2 = 0.0
    W = 0.0
    for i in range(len(all_pos) - 1):
        pos = all_pos[i]
        cdf1 += pd1[pos]
        cdf2 += pd2[pos]
        gap = all_pos[i + 1] - all_pos[i]
        W += abs(cdf1 - cdf2) * gap
    return W


def w1_lp(w_src, w_dst, pos_src, pos_dst) -> float:
    """W₁ via LP for small discrete supports."""
    n_s, n_d = len(w_src), len(w_dst)
    C = np.abs(pos_src[:, None] - pos_dst[None, :]).astype(float)
    n_vars = n_s * n_d
    c_vec = C.flatten()
    A_rows, b_rows = [], []
    for i in range(n_s):
        row = np.zeros(n_vars)
        row[i * n_d : (i + 1) * n_d] = 1.0
        A_rows.append(row)
        b_rows.append(w_src[i])
    for j in range(n_d):
        row = np.zeros(n_vars)
        for i in range(n_s):
            row[i * n_d + j] = 1.0
        A_rows.append(row)
        b_rows.append(w_dst[j])
    res = linprog(
        c_vec,
        A_eq=np.array(A_rows),
        b_eq=np.array(b_rows),
        bounds=[(0, None)] * n_vars,
        method="highs",
    )
    return float(res.fun) if res.success else float("nan")


def ollivier_ricci_dev(t: int, x: int, spacetime: np.ndarray, L: int, eps: float = EPS_DEV):
    """P36/Gorard deviation-based OR on spacelike edge (t,x)–(t,x+1)."""
    if t + 1 >= len(spacetime):
        return None
    p1 = [x - 1, x, x + 1]
    p2 = [x, x + 1, x + 2]
    w1 = [
        abs(int(spacetime[t + 1][xi % L]) - ether_val(t + 1, xi % L)) + eps
        for xi in p1
    ]
    w2 = [
        abs(int(spacetime[t + 1][xi % L]) - ether_val(t + 1, xi % L)) + eps
        for xi in p2
    ]
    Z1, Z2 = sum(w1), sum(w2)
    return 1.0 - wasserstein1d(
        [w / Z1 for w in w1], p1, [w / Z2 for w in w2], p2
    )


def build_spacelike_adj(spacetime: np.ndarray) -> dict:
    """Undirected spacelike adjacency at each time slice: (t,x)–(t,x±1)."""
    T, L = spacetime.shape
    T -= 1
    adj = defaultdict(set)
    for t in range(T + 1):
        for x in range(L):
            u = (t, x)
            v = (t, (x + 1) % L)
            adj[u].add(v)
            adj[v].add(u)
    return adj


def lazy_measure(node, adj, alpha=ALPHA_LAZY):
    """Lazy random-walk measure on graph neighbors."""
    neighbors = list(adj[node])
    deg = len(neighbors)
    mass = {node: 1.0 - alpha}
    if deg > 0:
        share = alpha / deg
        for z in neighbors:
            mass[z] = mass.get(z, 0.0) + share
    return mass


def graph_distance_matrix(nodes, adj, max_hops=4):
    """BFS distances among a small node set."""
    dist = {n: {n: 0} for n in nodes}
    for src in nodes:
        frontier = {src}
        seen = {src}
        for hop in range(1, max_hops + 1):
            nxt = set()
            for u in frontier:
                for v in adj[u]:
                    if v not in seen:
                        seen.add(v)
                        nxt.add(v)
                        dist[src][v] = hop
            frontier = nxt
            if not frontier:
                break
    return dist


def w1_graph(mu_a, mu_b, dist_ab) -> float:
    """W₁ between two discrete measures using precomputed distances."""
    keys_a = list(mu_a.keys())
    keys_b = list(mu_b.keys())
    w_a = np.array([mu_a[k] for k in keys_a])
    w_b = np.array([mu_b[k] for k in keys_b])
    C = np.array([[dist_ab[a].get(b, 4.0) for b in keys_b] for a in keys_a], dtype=float)
    n_s, n_d = len(keys_a), len(keys_b)
    n_vars = n_s * n_d
    c_vec = C.flatten()
    A_rows, b_rows = [], []
    for i in range(n_s):
        row = np.zeros(n_vars)
        row[i * n_d : (i + 1) * n_d] = 1.0
        A_rows.append(row)
        b_rows.append(w_a[i])
    for j in range(n_d):
        row = np.zeros(n_vars)
        for i in range(n_s):
            row[i * n_d + j] = 1.0
        A_rows.append(row)
        b_rows.append(w_b[j])
    res = linprog(
        c_vec,
        A_eq=np.array(A_rows),
        b_eq=np.array(b_rows),
        bounds=[(0, None)] * n_vars,
        method="highs",
    )
    return float(res.fun) if res.success else float("nan")


def ollivier_ricci_lazy(u, v, adj) -> float:
    """Standard lazy OR on graph edge (u,v) with d(u,v)=1."""
    mu_u = lazy_measure(u, adj)
    mu_v = lazy_measure(v, adj)
    nodes = set(mu_u) | set(mu_v)
    dist = graph_distance_matrix(nodes, adj)
    w1 = w1_graph(mu_u, mu_v, dist)
    return 1.0 - w1


def is_glider_cell(t: int, x: int, spacetime: np.ndarray, L: int) -> bool:
    return int(spacetime[t][x % L]) != ether_val(t, x % L)


def classify_spacelike_edge(t: int, x: int, spacetime: np.ndarray, L: int) -> str:
    """Classify spacelike edge (t,x)–(t,x+1) as glider or ether."""
    g0 = is_glider_cell(t, x, spacetime, L)
    g1 = is_glider_cell(t, (x + 1) % L, spacetime, L)
    if g0 or g1:
        return "glider"
    return "ether"


def causal_nbhd_type(t: int, x: int, spacetime: np.ndarray, L: int) -> str:
    """P36 causal neighborhood type for spacelike edge at (t,x)."""
    dev_x = is_glider_cell(t, x, spacetime, L)
    dev_x1 = is_glider_cell(t, (x + 1) % L, spacetime, L)
    if dev_x or dev_x1:
        return "PE"
    dev_xm1 = is_glider_cell(t + 1, x - 1, spacetime, L)
    dev_fx = is_glider_cell(t + 1, x, spacetime, L)
    dev_fx1 = is_glider_cell(t + 1, (x + 1) % L, spacetime, L)
    dev_xp2 = is_glider_cell(t + 1, x + 2, spacetime, L)
    dev_shared = dev_fx or dev_fx1
    dev_excl = dev_xm1 or dev_xp2
    if not dev_shared and not dev_excl:
        return "EE"
    if dev_shared and not dev_excl:
        return "SD"
    if not dev_shared and dev_excl:
        return "XD"
    return "MX"


def compute_kappa_fields(spacetime: np.ndarray, adj, T_use: int, t_start: int):
    """Compute deviation-based and lazy OR κ on spacelike edges, classified."""
    T, L = spacetime.shape
    T -= 1
    dev_kappa = {"glider": [], "ether": [], "EE": [], "SD": [], "XD": [], "MX": [], "PE": []}
    lazy_kappa = {"glider": [], "ether": []}

    for t in range(t_start, min(T_use, T)):
        for x in range(L):
            k_dev = ollivier_ricci_dev(t, x, spacetime, L)
            if k_dev is None:
                continue
            region = classify_spacelike_edge(t, x, spacetime, L)
            dev_kappa[region].append(k_dev)
            ctype = causal_nbhd_type(t, x, spacetime, L)
            dev_kappa[ctype].append(k_dev)

            u = (t, x)
            v = (t, (x + 1) % L)
            k_lazy = ollivier_ricci_lazy(u, v, adj)
            lazy_kappa[region].append(k_lazy)

    return dev_kappa, lazy_kappa


def summarize(values):
    if not values:
        return {"mean": None, "std": None, "n": 0}
    arr = np.array(values, dtype=float)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "n": int(len(arr)),
        "median": float(np.median(arr)),
    }


def compare_ee_vs_matter(dev_kappa, label: str):
    """Gorard-aligned comparison: EE (vacuum) vs PE+SD (matter-associated edges)."""
    ee = dev_kappa.get("EE", [])
    pe = dev_kappa.get("PE", [])
    sd = dev_kappa.get("SD", [])
    matter = pe + sd
    es = summarize(ee)
    ms = summarize(matter)
    ps = summarize(pe)
    ss = summarize(sd)
    ratio = ms["mean"] / es["mean"] if ms["mean"] is not None and es["mean"] not in (None, 0.0) else float("inf")
    diff = ms["mean"] - es["mean"] if ms["mean"] is not None and es["mean"] is not None else None
    if len(matter) >= 2 and len(ee) >= 2:
        t_stat, p_val = stats.ttest_ind(matter, ee, equal_var=False)
    else:
        t_stat, p_val = float("nan"), float("nan")
    sig = bool(p_val < 0.01 and diff is not None and diff > 0)
    print(f"\n{label}")
    print(f"  κ(EE vacuum)     = {es['mean']:.6f} ± {es['std']:.6f}  (n={es['n']})")
    print(f"  κ(PE glider edge)= {ps['mean']:.6f} ± {ps['std']:.6f}  (n={ps['n']})")
    print(f"  κ(SD matter nbhd)= {ss['mean']:.6f} ± {ss['std']:.6f}  (n={ss['n']})")
    print(f"  κ(matter=PE+SD)  = {ms['mean']:.6f} ± {ms['std']:.6f}  (n={ms['n']})")
    if ratio == float("inf"):
        print(f"  ratio matter/EE = ∞ (EE mean = 0)")
    elif ratio is not None:
        print(f"  ratio matter/EE = {ratio:.6f}")
    if diff is not None:
        print(f"  difference matter−EE = {diff:.6f}")
    print(f"  Welch t-test (matter vs EE): t={t_stat:.4f}, p={p_val:.4e}, significant={sig}")
    return {
        "EE": es,
        "PE": ps,
        "SD": ss,
        "matter_PE_SD": ms,
        "ratio_matter_over_EE": ratio if ratio != float("inf") else None,
        "ratio_matter_over_EE_infinite": ratio == float("inf"),
        "difference": diff,
        "t_stat": float(t_stat),
        "p_value": float(p_val),
        "significant_p001": sig,
    }


def compare_regions(kappa_dict, label: str):
    g = kappa_dict.get("glider", [])
    e = kappa_dict.get("ether", [])
    gs = summarize(g)
    es = summarize(e)
    ratio = gs["mean"] / es["mean"] if gs["mean"] is not None and es["mean"] not in (None, 0.0) else None
    diff = gs["mean"] - es["mean"] if gs["mean"] is not None and es["mean"] is not None else None
    if len(g) >= 2 and len(e) >= 2:
        t_stat, p_val = stats.ttest_ind(g, e, equal_var=False)
    else:
        t_stat, p_val = float("nan"), float("nan")
    sig = bool(p_val < 0.01 and diff is not None and diff > 0)
    print(f"\n{label}")
    print(f"  κ(glider) = {gs['mean']:.6f} ± {gs['std']:.6f}  (n={gs['n']})")
    print(f"  κ(ether)  = {es['mean']:.6f} ± {es['std']:.6f}  (n={es['n']})")
    if ratio is not None:
        print(f"  ratio glider/ether = {ratio:.6f}")
    if diff is not None:
        print(f"  difference = {diff:.6f}")
    print(f"  Welch t-test: t={t_stat:.4f}, p={p_val:.4e}, significant (p<0.01, glider>ether)={sig}")
    return {
        "glider": gs,
        "ether": es,
        "ratio": ratio,
        "difference": diff,
        "t_stat": float(t_stat),
        "p_value": float(p_val),
        "significant_p001": sig,
    }


def main():
    t0 = time.time()
    print("=" * 70)
    print("64-DCG-OR Round 4: Static Ollivier-Ricci κ on Rule 110 causal graph")
    print("=" * 70)

    # ── Pure ether background ─────────────────────────────────────────────────
    print("\n--- Pure ETHER14 background ---")
    sp_ether = evolve_spacetime(make_ether_tape(L_ETHER), T_ETHER)
    adj_ether = build_spacelike_adj(sp_ether)
    dev_ether, lazy_ether = compute_kappa_fields(sp_ether, adj_ether, T_ETHER, T_BURN)
    print(f"Spacetime shape: {sp_ether.shape}")
    print(f"P36 EE edges: n={len(dev_ether['EE'])}, mean κ={np.mean(dev_ether['EE']) if dev_ether['EE'] else 'N/A'}")

    # ── A-glider on ether ─────────────────────────────────────────────────────
    print("\n--- A-glider on ETHER14 background ---")
    tape0 = embed_glider(make_ether_tape(L_GLIDER), GLIDER_CENTER)
    sp_ref = evolve_spacetime(make_ether_tape(L_GLIDER), T_GLIDER)
    sp_glider = evolve_spacetime(tape0, T_GLIDER)
    adj_glider = build_spacelike_adj(sp_glider)
    dev_glider, lazy_glider = compute_kappa_fields(sp_glider, adj_glider, T_GLIDER, T_BURN)

    # Glider occupancy check
    n_glider_cells = sum(
        1
        for t in range(T_BURN, T_GLIDER)
        for x in range(L_GLIDER)
        if is_glider_cell(t, x, sp_glider, L_GLIDER)
    )
    print(f"Glider-region cell-steps (t>{T_BURN}): {n_glider_cells}")

    # ── Comparisons ───────────────────────────────────────────────────────────
    cmp_gorard = compare_ee_vs_matter(
        dev_glider, "Method A — P36/Gorard deviation-based OR (EE vs matter)"
    )
    cmp_dev = compare_regions(dev_glider, "Method A — spatial glider/ether edge classification")
    cmp_lazy = compare_regions(lazy_glider, "Method B — Lazy OR on causal spacelike edges")

    # P36 typed neighborhoods (glider tape)
    p36_types = {}
    for ctype in ("EE", "SD", "XD", "PE", "MX"):
        p36_types[ctype] = summarize(dev_glider.get(ctype, []))
        if dev_glider.get(ctype):
            print(f"  P36 {ctype}: mean κ = {p36_types[ctype]['mean']:.6f} (n={p36_types[ctype]['n']})")

    # CatA gate: Gorard-aligned EE vs matter (PE+SD)
    cat_a_gate = cmp_gorard["significant_p001"] and (
        cmp_gorard["ratio_matter_over_EE_infinite"]
        or (cmp_gorard["ratio_matter_over_EE"] or 0) > 1.0
    )

    results = {
        "rank": "64-DCG-OR",
        "round": 4,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "ETHER": ETHER,
            "GLIDER": GLIDER,
            "L_ether": L_ETHER,
            "T_ether": T_ETHER,
            "L_glider": L_GLIDER,
            "T_glider": T_GLIDER,
            "glider_center": GLIDER_CENTER,
            "eps_dev": EPS_DEV,
            "alpha_lazy": ALPHA_LAZY,
            "t_burn": T_BURN,
            "timeout_s": TIMEOUT_S,
        },
        "ether_background": {
            "p36_EE": summarize(dev_ether["EE"]),
            "lazy_ether_only": summarize(lazy_ether["ether"]),
        },
        "glider_on_ether": {
            "method_a_gorard_EE_vs_matter": cmp_gorard,
            "method_a_spatial_glider_ether": cmp_dev,
            "method_b_lazy_or": cmp_lazy,
            "p36_neighborhood_types": p36_types,
            "n_glider_cell_steps": n_glider_cells,
        },
        "cat_a_gate": {
            "method": "P36 deviation-based OR (EE vs PE+SD matter edges)",
            "criterion": "κ(matter) > κ(EE), ratio > 1 or EE=0, p < 0.01",
            "passed": cat_a_gate,
        },
        "interpretation": {
            "gorard_sign": "κ(EE/vacuum) ≈ 0, κ(SD/matter) > 0, κ(XD/flank) < 0",
            "kappa_EE": p36_types["EE"]["mean"],
            "kappa_SD": p36_types["SD"]["mean"],
            "kappa_XD": p36_types["XD"]["mean"],
            "kappa_PE": p36_types["PE"]["mean"],
        },
        "runtime_s": time.time() - t0,
    }

    out_path = "dcg_or_static_kappa_round4_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Runtime: {results['runtime_s']:.1f}s")
    print(f"CatA gate (Method A): {'PASS' if cat_a_gate else 'NOT CONFIRMED'}")

    signal.alarm(0)


if __name__ == "__main__":
    main()
