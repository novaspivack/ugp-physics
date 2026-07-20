#!/usr/bin/env python3
"""
rank64_dcg_dynamical_causal_graph.py
EPIC_072 Rank 64-DCG — Dynamical Causal Graph AFCA

Tests the coupling-constant prescription for τ_c-weighted outer Rule 110.
The key question: does matter (gliders) cluster near other matter when
the outer CA rule depends on the local τ_c field?

Discrete analog of G_μν = 8πT_μν:
  LHS (geometry modification): τ_c-dependent outer rule
  RHS (matter content): τ_c field elevated at gliders

Prescription (coupling-constant):
  val[i] = rule110(L,C,R)[i] + ε · τ_c_norm[i] · (outer[i-1] + outer[i+1])
  new_outer[i] = 1 if val[i] > 0.5 else 0

where τ_c_norm = τ_c / τ_c_mean (normalized so ether ≈ 1.0).

Parameters: L=200, T=100, M=7, ε in [0.0, 0.01, 0.05, 0.10]
Glider: 0100101001 on ETHER14 background.

EPIC_072 / Rank 64-DCG
"""

import signal
import sys
import time
import json
import numpy as np
from pathlib import Path

# ── Wall-clock timeout ────────────────────────────────────────────────────────
TIMEOUT_S = 600

def _timeout_handler(sig, frame):
    print(f"\nTIMEOUT: {TIMEOUT_S}s wall-clock limit reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_S)

# ── Constants ─────────────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110  = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
GLIDER  = np.array([0, 1, 0, 0, 1, 0, 1, 0, 0, 1], dtype=np.uint8)  # canonical seed

L          = 200     # outer tape length
T          = 100     # outer steps
M          = 7       # inner CA width per outer cell
EPS_VALUES = [0.0, 0.01, 0.05, 0.10]
MAX_INNER  = 70      # inner step cap (τ_c cap)
MAX_DIFF   = 50      # max perturbation width before "glider dissolved"

# ETHER14 phases with majority = 1 and majority = 0 for M=7 windows
# Phase 0: [1,1,1,1,1,0,0] sum=5 → majority=1
# Phase 7: [0,1,0,0,1,1,0] sum=3 → majority=0
PHASE_MAJ1 = 0
PHASE_MAJ0 = 7

# ── CA primitives ─────────────────────────────────────────────────────────────

def make_ether_tape(length: int) -> np.ndarray:
    return np.array([ETHER14[i % 14] for i in range(length)], dtype=np.uint8)


def embed_glider(tape: np.ndarray, pos: int) -> np.ndarray:
    t = tape.copy()
    for j, bit in enumerate(GLIDER):
        t[(pos + j) % len(t)] = bit
    return t


def init_inner_consistent(outer: np.ndarray, M: int) -> np.ndarray:
    """
    Initialize all inner CAs from ETHER14 windows, choosing a phase whose
    majority matches the outer cell's state.  Avoids immediate inconsistency.
    """
    length = len(outer)
    inner = np.zeros((length, M), dtype=np.uint8)
    for i in range(length):
        phase = PHASE_MAJ1 if outer[i] == 1 else PHASE_MAJ0
        for j in range(M):
            inner[i, j] = ETHER14[(phase + j) % 14]
    return inner


def inner_step_all(inner: np.ndarray) -> np.ndarray:
    """One Rule 110 step for all L inner CAs simultaneously. Shape (L, M)."""
    l = np.roll(inner, 1, axis=1).astype(np.int32)
    c = inner.astype(np.int32)
    r = np.roll(inner, -1, axis=1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r].astype(np.uint8)


def majority_vote(inner: np.ndarray) -> np.ndarray:
    """Majority bit for each row. Returns shape (L,) uint8."""
    return (inner.sum(axis=1) * 2 > inner.shape[1]).astype(np.uint8)


def outer_step_standard(outer: np.ndarray) -> np.ndarray:
    """Standard Rule 110 outer update."""
    l = np.roll(outer, 1).astype(np.int32)
    c = outer.astype(np.int32)
    r = np.roll(outer, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r].astype(np.uint8)


def outer_step_dcg(outer: np.ndarray, tau_c_norm: np.ndarray, eps: float) -> np.ndarray:
    """
    τ_c-weighted Rule 110 (coupling-constant prescription).
    val[i] = rule110(L,C,R) + ε · τ_c_norm[i] · (outer[i-1] + outer[i+1])
    new_outer[i] = 1 if val[i] > 0.5 else 0
    """
    l = np.roll(outer, 1).astype(np.int32)
    c = outer.astype(np.int32)
    r = np.roll(outer, -1).astype(np.int32)
    b_std = LUT110[(l << 2) | (c << 1) | r].astype(np.float64)
    neighbor_sum = (np.roll(outer, 1) + np.roll(outer, -1)).astype(np.float64)
    val = b_std + eps * tau_c_norm.astype(np.float64) * neighbor_sum
    return (val > 0.5).astype(np.uint8)


def compute_tau_c(inner: np.ndarray, desired: np.ndarray) -> np.ndarray:
    """
    Count inner Rule 110 steps per outer cell until majority matches desired.
    Returns tau_c shape (L,) float32.  Cap at MAX_INNER.
    """
    tau_c = np.full(len(desired), float(MAX_INNER), dtype=np.float32)
    current = inner.copy()
    done = np.zeros(len(desired), dtype=bool)

    # Check if already matching at step 0
    match = (majority_vote(current) == desired)
    tau_c[match] = 0.0
    done |= match

    for step in range(1, MAX_INNER + 1):
        if done.all():
            break
        current = inner_step_all(current)
        maj = majority_vote(current)
        newly = (~done) & (maj == desired)
        tau_c[newly] = float(step)
        done |= newly

    return tau_c


def normalize_tau_c(tau_c: np.ndarray) -> np.ndarray:
    """Normalize by mean; return ones if mean is zero."""
    m = float(tau_c.mean())
    return (tau_c / m).astype(np.float32) if m > 1e-12 else np.ones(len(tau_c), dtype=np.float32)


# ── Glider tracking ───────────────────────────────────────────────────────────

def perturbation_clusters(outer: np.ndarray, ether_ref: np.ndarray):
    """
    Find connected clusters of cells where outer ≠ ether_ref.
    Returns list of (center_of_mass, size) sorted by CoM.
    """
    diff = (outer != ether_ref).astype(np.int32)
    if diff.sum() == 0:
        return []

    length = len(outer)
    used = np.zeros(length, dtype=bool)
    clusters = []

    for p in np.where(diff)[0]:
        if used[p]:
            continue
        cluster = [p]
        used[p] = True
        frontier = [p]
        while frontier:
            nf = []
            for q in frontier:
                for nb in [(q - 1) % length, (q + 1) % length]:
                    if diff[nb] and not used[nb]:
                        used[nb] = True
                        cluster.append(nb)
                        nf.append(nb)
            frontier = nf
        arr = np.array(cluster, dtype=float)
        com = float(arr.mean()) % length
        clusters.append((com, len(cluster)))

    clusters.sort(key=lambda x: x[0])
    return clusters


def glider_distance(clusters):
    """Distance between first two clusters (circular metric)."""
    if len(clusters) < 2:
        return None
    c1, c2 = clusters[0][0], clusters[1][0]
    return min(abs(c2 - c1), L - abs(c2 - c1))


def glider_is_stable(clusters):
    """True if total perturbation cells ≤ MAX_DIFF (glider localized)."""
    total = sum(sz for _, sz in clusters)
    return 0 < total <= MAX_DIFF


# ── Core experiment runner ────────────────────────────────────────────────────

def run_afca(glider_positions, eps: float, n_steps: int = T, track_tau_c: bool = False):
    """
    Run AFCA for n_steps outer steps with gliders at given positions.

    Both the glider tape and a pure-ether reference tape evolve under the same
    rule (eps=0 → standard; eps>0 → DCG).  The difference isolates glider dynamics.

    Returns:
        outer_hist: (n_steps+1, L) uint8
        ether_hist: (n_steps+1, L) uint8
        tau_c_hist: (n_steps, L) float32
        tau_c_norm_hist: (n_steps, L) float32  [only if track_tau_c]
    """
    outer_g = make_ether_tape(L)
    for pos in glider_positions:
        outer_g = embed_glider(outer_g, pos)

    outer_e = make_ether_tape(L)  # pure ether reference

    inner_g = init_inner_consistent(outer_g, M)
    inner_e = init_inner_consistent(outer_e, M)

    tau_c_norm_g = np.ones(L, dtype=np.float32)
    tau_c_norm_e = np.ones(L, dtype=np.float32)

    outer_hist = np.zeros((n_steps + 1, L), dtype=np.uint8)
    ether_hist = np.zeros((n_steps + 1, L), dtype=np.uint8)
    tau_c_hist = np.zeros((n_steps, L), dtype=np.float32)

    outer_hist[0] = outer_g
    ether_hist[0] = outer_e

    for t in range(n_steps):
        if eps == 0.0:
            desired_g = outer_step_standard(outer_g)
            desired_e = outer_step_standard(outer_e)
        else:
            desired_g = outer_step_dcg(outer_g, tau_c_norm_g, eps)
            desired_e = outer_step_dcg(outer_e, tau_c_norm_e, eps)

        tau_c_g = compute_tau_c(inner_g, desired_g)
        tau_c_e = compute_tau_c(inner_e, desired_e)

        tau_c_hist[t] = tau_c_g
        tau_c_norm_g = normalize_tau_c(tau_c_g)
        tau_c_norm_e = normalize_tau_c(tau_c_e)

        outer_g = desired_g
        outer_e = desired_e
        # Reinitialize inner CA from the new outer state (approximation):
        # each inner CA starts fresh from the majority-consistent ether window.
        inner_g = init_inner_consistent(outer_g, M)
        inner_e = init_inner_consistent(outer_e, M)

        outer_hist[t + 1] = outer_g
        ether_hist[t + 1] = outer_e

    return outer_hist, ether_hist, tau_c_hist


# ── Experiment 1: single-glider stability ─────────────────────────────────────

def test_single_glider_stability(eps: float):
    """
    Run single glider at position 50 for T steps.
    Returns (survived_50_steps: bool, speed: float cells/outer-step).
    """
    outer_hist, ether_hist, _ = run_afca([50], eps)
    com_history = []
    survived = True

    for t in range(1, T + 1):
        clusters = perturbation_clusters(outer_hist[t], ether_hist[t])
        if not glider_is_stable(clusters):
            survived = (t >= 50)  # survived if held for ≥50 steps
            break
        if clusters:
            com_history.append(clusters[0][0])

    # Estimate speed via linear fit on unwrapped CoM
    speed = float('nan')
    if len(com_history) >= 10:
        xs = np.array(com_history, dtype=float)
        # Unwrap periodic coordinate
        xs_uw = np.unwrap(xs * 2 * np.pi / L) * L / (2 * np.pi)
        ts = np.arange(len(xs_uw), dtype=float)
        speed = float(np.polyfit(ts, xs_uw, 1)[0])

    return survived, speed


# ── Experiment 2: two-glider distance ────────────────────────────────────────

def test_two_glider_distance(eps: float, pos1: int = 50, pos2: int = 150):
    """
    Run two gliders and track inter-glider distance over T steps.
    Returns list of distances (None if < 2 clusters detected).
    """
    outer_hist, ether_hist, tau_c_hist = run_afca([pos1, pos2], eps)
    distances = []
    tau_c_glider_means = []
    tau_c_bg_means = []

    for t in range(1, T + 1):
        clusters = perturbation_clusters(outer_hist[t], ether_hist[t])
        dist = glider_distance(clusters)
        distances.append(float(dist) if dist is not None else None)

        # τ_c concentration: glider cells vs background
        diff_mask = (outer_hist[t] != ether_hist[t])
        if diff_mask.sum() > 0 and diff_mask.sum() < MAX_DIFF and t > 0:
            tc = tau_c_hist[t - 1]
            if diff_mask.any():
                tau_c_glider_means.append(float(tc[diff_mask].mean()))
                tau_c_bg_means.append(float(tc[~diff_mask].mean()))

    conc = float(np.mean(tau_c_glider_means) / np.mean(tau_c_bg_means)) \
        if tau_c_bg_means and np.mean(tau_c_bg_means) > 0 else 1.0

    return distances, conc


# ── Experiment 3: vacuum null test ────────────────────────────────────────────

def test_vacuum_null(eps: float, n_steps: int = 50):
    """
    Pure ether run under DCG rule.  τ_c std should remain low (homogeneous vacuum).
    Returns mean τ_c std over n_steps.
    """
    outer = make_ether_tape(L)
    inner = init_inner_consistent(outer, M)
    tau_c_norm = np.ones(L, dtype=np.float32)
    stds = []

    for _ in range(n_steps):
        if eps == 0.0:
            desired = outer_step_standard(outer)
        else:
            desired = outer_step_dcg(outer, tau_c_norm, eps)

        tau_c = compute_tau_c(inner, desired)
        stds.append(float(tau_c.std()))
        tau_c_norm = normalize_tau_c(tau_c)
        outer = desired
        inner = init_inner_consistent(outer, M)

    return float(np.mean(stds))


# ── Distance trend analysis ───────────────────────────────────────────────────

def distance_stats(dists):
    """Returns (initial_mean, final_mean, slope_cells_per_step)."""
    valid = [d for d in dists if d is not None]
    if len(valid) < 20:
        return None, None, 0.0
    n = len(valid)
    init_mean = float(np.mean(valid[:max(1, n // 5)]))
    final_mean = float(np.mean(valid[-max(1, n // 5):]))
    ts = np.arange(n, dtype=float)
    slope = float(np.polyfit(ts, valid, 1)[0])
    return init_mean, final_mean, slope


# ── Main ──────────────────────────────────────────────────────────────────────

t_start = time.time()
print(f"Rank 64-DCG: Dynamical Causal Graph AFCA")
print(f"Parameters: L={L}, T={T}, M={M}, ε={EPS_VALUES}")
print(f"Glider: {list(GLIDER)}")
print(f"Started at {time.strftime('%H:%M:%S')}\n")

results = {
    "parameters": {
        "L": L, "T": T, "M": M,
        "eps_values": EPS_VALUES,
        "glider_seed": list(map(int, GLIDER)),
        "max_inner_steps": MAX_INNER,
        "prescription": "coupling_constant",
        "inner_init": "ether_consistent_majority",
    },
    "glider_stability": {},
    "single_glider_speeds": {},
    "max_stable_eps": 0.0,
    "two_glider_distance": {},
    "tau_c_concentration": {},
    "null_tests": {},
    "conclusion": "PENDING",
}

# ── Step 1: Glider stability ──────────────────────────────────────────────────
print("=== Step 1: Single-glider stability ===")
max_stable_eps = 0.0

for eps in EPS_VALUES:
    print(f"  ε={eps:.2f}: running ...", end=" ", flush=True)
    survived, speed = test_single_glider_stability(eps)
    results["glider_stability"][f"eps_{eps}"] = survived
    results["single_glider_speeds"][f"eps_{eps}"] = round(float(speed) if not (isinstance(speed, float) and np.isnan(speed)) else -99.0, 4)
    flag = "STABLE" if survived else "DISSOLVED"
    spd_str = f"{speed:.4f}" if not (isinstance(speed, float) and np.isnan(speed)) else "n/a"
    print(f"{flag}  speed={spd_str} cells/step")
    if survived:
        max_stable_eps = eps

results["max_stable_eps"] = max_stable_eps
print(f"  → Max stable ε: {max_stable_eps}")

# ── Step 2: Two-glider distance experiment ────────────────────────────────────
print("\n=== Step 2: Two-glider distance (pos1=50, pos2=150) ===")

eps_dyn = max_stable_eps if max_stable_eps > 0.0 else 0.01

print(f"  Baseline (ε=0.0): running ...", flush=True)
dist_base, conc_base = test_two_glider_distance(0.0)

print(f"  Dynamical (ε={eps_dyn}): running ...", flush=True)
dist_dyn, conc_dyn = test_two_glider_distance(eps_dyn)

b_init, b_final, b_slope = distance_stats(dist_base)
d_init, d_final, d_slope = distance_stats(dist_dyn)

results["two_glider_distance"]["baseline"]  = [round(d, 2) if d is not None else None for d in dist_base]
results["two_glider_distance"]["dynamical"] = [round(d, 2) if d is not None else None for d in dist_dyn]
results["two_glider_distance"]["baseline_stats"]  = {"initial": b_init, "final": b_final, "slope": b_slope}
results["two_glider_distance"]["dynamical_stats"] = {"initial": d_init, "final": d_final, "slope": d_slope}

print(f"  Baseline: init={b_init:.1f}, final={b_final:.1f}, slope={b_slope:.4f} cells/step")
print(f"  Dynamical: init={d_init:.1f}, final={d_final:.1f}, slope={d_slope:.4f} cells/step")

results["tau_c_concentration"]["baseline"]  = round(conc_base, 4)
results["tau_c_concentration"]["dynamical"] = round(conc_dyn, 4)
print(f"  τ_c concentration — baseline: {conc_base:.4f}, dynamical: {conc_dyn:.4f}")

# ── Step 2b: Close-pair two-glider test (pos1=85, pos2=115, separation=30) ───
print("\n=== Step 2b: Close-pair gliders (pos1=85, pos2=115, separation=30) ===")

print(f"  Baseline (ε=0.0): running ...", flush=True)
dist_close_base, _ = test_two_glider_distance(0.0, 85, 115)

print(f"  Dynamical (ε={eps_dyn}): running ...", flush=True)
dist_close_dyn, _ = test_two_glider_distance(eps_dyn, 85, 115)

cb_init, cb_final, cb_slope = distance_stats(dist_close_base)
cd_init, cd_final, cd_slope = distance_stats(dist_close_dyn)

results["two_glider_distance"]["close_baseline_stats"]  = {"initial": cb_init, "final": cb_final, "slope": cb_slope}
results["two_glider_distance"]["close_dynamical_stats"] = {"initial": cd_init, "final": cd_final, "slope": cd_slope}
results["two_glider_distance"]["close_baseline"]  = [round(d, 2) if d is not None else None for d in dist_close_base]
results["two_glider_distance"]["close_dynamical"] = [round(d, 2) if d is not None else None for d in dist_close_dyn]

print(f"  Close baseline: init={cb_init}, final={cb_final}, slope={cb_slope:.4f}")
print(f"  Close dynamical: init={cd_init}, final={cd_final}, slope={cd_slope:.4f}")

# ── Step 3: Null tests ────────────────────────────────────────────────────────
print("\n=== Step 3: Null tests ===")

# N1: single-glider speed ratio (should be ~1.0)
spd_base = results["single_glider_speeds"].get("eps_0.0", 0.0)
spd_dyn  = results["single_glider_speeds"].get(f"eps_{eps_dyn}", 0.0)
speed_ratio = (spd_dyn / spd_base) if (spd_base and abs(spd_base) > 0.01) else 1.0
speed_null_pass = bool(0.80 <= abs(speed_ratio) <= 1.20)
print(f"  N1 single-glider speed ratio: {speed_ratio:.4f}  → {'PASS' if speed_null_pass else 'FAIL'}")

# N2: vacuum τ_c std under DCG
print(f"  N2 vacuum τ_c std (ε={eps_dyn}): running ...", end=" ", flush=True)
vac_std = test_vacuum_null(eps_dyn)
vac_null_pass = bool(vac_std < 0.5)
print(f"{vac_std:.6f}  → {'PASS' if vac_null_pass else 'WARN'}")

results["null_tests"]["single_glider_speed_ratio"] = round(speed_ratio, 4)
results["null_tests"]["single_glider_speed_pass"]  = speed_null_pass
results["null_tests"]["vacuum_tau_c_std"]           = round(vac_std, 6)
results["null_tests"]["vacuum_null_pass"]           = vac_null_pass

# ── Conclusion ────────────────────────────────────────────────────────────────
print("\n=== Conclusion ===")

null_pass = speed_null_pass and vac_null_pass
sep_delta = (d_slope - b_slope) if (b_slope is not None and d_slope is not None) else 0.0
close_sep_delta = (cd_slope - cb_slope) if (cb_slope is not None and cd_slope is not None) else 0.0

# Use both distance tests: far-pair and close-pair
attraction_signal = min(sep_delta, close_sep_delta)

if attraction_signal < -0.50 and null_pass:
    conclusion = "CONFIRMED"
elif attraction_signal < -0.10 and null_pass:
    conclusion = "WEAK"
elif attraction_signal < 0.0 and not null_pass:
    conclusion = "INCONCLUSIVE"
elif attraction_signal >= 0.0:
    conclusion = "NEGATIVE"
else:
    conclusion = "INCONCLUSIVE"

results["conclusion"]              = conclusion
results["separation_delta_slope"]  = round(sep_delta, 6)
results["close_sep_delta_slope"]   = round(close_sep_delta, 6)
results["null_tests_pass"]         = null_pass
results["elapsed_s"]               = round(time.time() - t_start, 1)

print(f"  Far-pair separation slope change:   {sep_delta:+.4f} cells/step")
print(f"  Close-pair separation slope change: {close_sep_delta:+.4f} cells/step")
print(f"  Null tests pass: {null_pass}")
print(f"  τ_c concentration ratio: baseline={conc_base:.4f}, dynamical={conc_dyn:.4f}")
print(f"  Conclusion: {conclusion}")
print(f"  Elapsed: {results['elapsed_s']:.1f}s")

# ── Save results ──────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SCRIPT_DIR.parent / "data"
out_path = _DATA_DIR / "rank64_dcg_dynamical_causal_graph_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(results, f)

print(f"\nResults saved → {out_path}")
signal.alarm(0)
print("Done.")
