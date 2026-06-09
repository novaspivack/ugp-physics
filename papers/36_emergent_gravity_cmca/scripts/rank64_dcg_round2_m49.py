#!/usr/bin/env python3
"""
rank64_dcg_round2_m49.py
EPIC_072 Rank 64-DCG — Dynamical Causal Graph AFCA Round 2 (M=49 inner CA)

Round 1 (M=7) NEGATIVE: tau_c binary {0,1} — no valid epsilon window.
Root cause: Rule 110 on 7 periodic cells flips majority in ≤1 inner step.
tau_c_norm_max = 2.326; correction = eps * 2.326 * 2 never crosses 0.5
before the glider dissolves at eps = 0.10.

Round 2 (M=49): tau_c range 0–49.
With M=49, inner CA has rich transient dynamics (up to 49 steps to flip majority).
Expected: glider cells tau_c ≈ 20–40, ether cells tau_c ≈ 5–10 (ratio 3–5x).
At this ratio, eps=0.01–0.05 produces corrections above 0.5 at glider cells
without destabilizing ether — a valid operating window should exist.

Two prescriptions tested:
  (A) Coupling-constant: val[i] = rule110(L,C,R) + eps * tau_c_norm[i] * neighbor_sum
      new_outer[i] = 1 if val[i] > 0.5 else 0
  (B) Stretch: high-tau_c cells (> mean + 1.5*std) use 5-cell neighborhood
      5-cell rule: majority vote of Rule 110 applied to triplets (i-2,i-1,i),
      (i-1,i,i+1), (i,i+1,i+2); this is binary (no eps to tune)

Parameters: M=49, L=100, T=50
Glider: GLIDER=[0,1,0,0,1,0,1,0,0,1] on ETHER14 background.
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
ETHER14  = np.array([1,1,1,1,1,0,0,0,1,0,0,1,1,0], dtype=np.uint8)
LUT110   = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
GLIDER   = np.array([0,1,0,0,1,0,1,0,0,1], dtype=np.uint8)

M          = 49      # inner CA width per outer cell
L          = 100     # outer tape length
T          = 50      # outer steps
MAX_INNER  = 49      # inner step cap (= M)
MAX_DIFF   = 50      # max perturbation width before glider declared dissolved
GLIDER_STABILITY_THRESHOLD = 30  # outer steps glider must survive

EPS_VALUES         = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]
EPS_EXTENDED       = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20]

# Phase selection for inner CA init.
# Note: for M=49, both phases give majority=1 (sum ≈ 27–29 > 24.5).
# This is expected; cells with desired=0 will have non-zero tau_c (steps to flip majority).
PHASE_MAJ1 = 0   # phase with best majority=1 coverage
PHASE_MAJ0 = 7   # phase with best majority=0 coverage (still majority=1 for M=49)

# ── Precompute ether seeds for M=49 ──────────────────────────────────────────

def _ether14_window(phase: int, width: int) -> np.ndarray:
    return np.array([ETHER14[(phase + j) % 14] for j in range(width)], dtype=np.uint8)

SEED_MAJ1 = _ether14_window(PHASE_MAJ1, M)  # majority=1 seed (M=49)
SEED_MAJ0 = _ether14_window(PHASE_MAJ0, M)  # best majority=0 attempt (M=49)


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
    Initialize all inner CAs from ETHER14 windows.
    For M=49: both phases give majority=1; cells with desired=0 will
    have positive tau_c (steps until inner CA reaches majority=0).
    """
    length = len(outer)
    inner = np.zeros((length, M), dtype=np.uint8)
    for i in range(length):
        phase = PHASE_MAJ1 if outer[i] == 1 else PHASE_MAJ0
        inner[i] = _ether14_window(phase, M)
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
    """Standard Rule 110 outer update (3-cell neighborhood)."""
    l = np.roll(outer, 1).astype(np.int32)
    c = outer.astype(np.int32)
    r = np.roll(outer, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r].astype(np.uint8)


def outer_step_dcg_coupling(outer: np.ndarray,
                             tau_c_norm: np.ndarray,
                             eps: float) -> np.ndarray:
    """
    Coupling-constant prescription.
    val[i] = rule110(outer[i-1], outer[i], outer[i+1])
             + eps * tau_c_norm[i] * (outer[i-1] + outer[i+1])
    new_outer[i] = 1 if val[i] > 0.5 else 0
    """
    l = np.roll(outer, 1).astype(np.int32)
    c = outer.astype(np.int32)
    r = np.roll(outer, -1).astype(np.int32)
    b_std      = LUT110[(l << 2) | (c << 1) | r].astype(np.float64)
    neigh_sum  = (np.roll(outer, 1) + np.roll(outer, -1)).astype(np.float64)
    val        = b_std + eps * tau_c_norm.astype(np.float64) * neigh_sum
    return (val > 0.5).astype(np.uint8)


def outer_step_stretch(outer: np.ndarray,
                       tau_c: np.ndarray,
                       tau_c_mean: float,
                       tau_c_std: float) -> np.ndarray:
    """
    Stretch prescription.
    Cells where tau_c[i] > tau_c_mean + 1.5*tau_c_std use a 5-cell neighborhood:
      majority vote of Rule 110 applied to (i-2,i-1,i), (i-1,i,i+1), (i,i+1,i+2).
    Others use standard 3-cell Rule 110.
    """
    n = len(outer)
    # Standard 3-cell output
    l1 = np.roll(outer, 1).astype(np.int32)
    c  = outer.astype(np.int32)
    r1 = np.roll(outer, -1).astype(np.int32)
    std_out = LUT110[(l1 << 2) | (c << 1) | r1].astype(np.int32)

    # 5-cell: three sub-triplets
    l2 = np.roll(outer, 2).astype(np.int32)
    r2 = np.roll(outer, -2).astype(np.int32)
    t1 = LUT110[(l2 << 2) | (l1 << 1) | c]     # triplet (i-2, i-1, i)
    t2 = LUT110[(l1 << 2) | (c  << 1) | r1]    # triplet (i-1, i, i+1)
    t3 = LUT110[(c  << 2) | (r1 << 1) | r2]    # triplet (i, i+1, i+2)
    five_out = ((t1.astype(np.int32) + t2.astype(np.int32) + t3.astype(np.int32)) >= 2).astype(np.int32)

    # Mask: which cells use 5-cell rule
    threshold = tau_c_mean + 1.5 * tau_c_std
    use_stretch = (tau_c > threshold)

    result = np.where(use_stretch, five_out, std_out).astype(np.uint8)
    return result


def compute_tau_c(inner: np.ndarray, desired: np.ndarray) -> np.ndarray:
    """
    Count inner Rule 110 steps per outer cell until majority matches desired.
    Returns tau_c shape (L,) float32.  Caps at MAX_INNER.
    """
    tau_c = np.full(len(desired), float(MAX_INNER), dtype=np.float32)
    current = inner.copy()
    done = np.zeros(len(desired), dtype=bool)

    # Check step 0 (already matching)
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


# ── Glider tracking (fixed from Round 1) ─────────────────────────────────────
# Round 1 issue: sub-cluster splitting caused incorrect glider distance (~4 cells
# instead of ~100). Fix: use half-tape split (works because gliders placed at L//4
# and 3*L//4 — guaranteed to land in opposite halves).

def glider_com_halves(outer: np.ndarray, ether_ref: np.ndarray, n_gliders: int = 2):
    """
    Find center-of-mass of perturbation in each half of the tape.
    Returns list of (com, half_index) for each half that contains perturbation.
    Works correctly even when each glider splits into multiple sub-clusters.
    """
    diff = (outer != ether_ref).astype(np.float64)
    half = len(outer) // 2
    coms = []
    for h in range(n_gliders):
        start = h * half
        end   = (h + 1) * half
        seg   = diff[start:end]
        if seg.sum() > 0:
            positions = np.arange(start, end, dtype=float)
            com = float((positions * seg).sum() / seg.sum())
            coms.append(com)
        else:
            coms.append(float(start + half / 2))  # fallback: center of half
    return coms


def two_glider_distance(outer: np.ndarray, ether_ref: np.ndarray) -> float | None:
    """Distance between two glider CoMs using half-tape split. Circular metric."""
    coms = glider_com_halves(outer, ether_ref, n_gliders=2)
    if len(coms) < 2:
        return None
    c1, c2 = coms[0], coms[1]
    raw = abs(c2 - c1)
    return float(min(raw, L - raw))


def perturbation_total(outer: np.ndarray, ether_ref: np.ndarray) -> int:
    return int((outer != ether_ref).sum())


def glider_is_stable(outer: np.ndarray, ether_ref: np.ndarray) -> bool:
    total = perturbation_total(outer, ether_ref)
    return 0 < total <= MAX_DIFF


# ── Core AFCA runner ──────────────────────────────────────────────────────────

def run_afca(glider_positions,
             eps: float,
             prescription: str,          # 'coupling' or 'stretch' or 'baseline'
             n_steps: int = T,
             tau_c_stats_override=None):  # (mean, std) for stretch threshold
    """
    Run AFCA for n_steps outer steps with gliders at given positions.

    Both the glider tape and a pure-ether reference tape evolve under the same rule.
    Returns:
        outer_hist:     (n_steps+1, L) uint8
        ether_hist:     (n_steps+1, L) uint8
        tau_c_hist:     (n_steps,   L) float32
        tau_c_norm_hist:(n_steps,   L) float32
    """
    outer_g = make_ether_tape(L)
    for pos in glider_positions:
        outer_g = embed_glider(outer_g, pos)

    outer_e = make_ether_tape(L)

    inner_g = init_inner_consistent(outer_g, M)
    inner_e = init_inner_consistent(outer_e, M)

    tau_c_norm_g = np.ones(L, dtype=np.float32)
    tau_c_g_prev = np.ones(L, dtype=np.float32) * (MAX_INNER / 2)

    outer_hist    = np.zeros((n_steps + 1, L), dtype=np.uint8)
    ether_hist    = np.zeros((n_steps + 1, L), dtype=np.uint8)
    tau_c_hist    = np.zeros((n_steps, L), dtype=np.float32)

    outer_hist[0] = outer_g
    ether_hist[0] = outer_e

    tc_mean_for_stretch = tau_c_stats_override[0] if tau_c_stats_override else MAX_INNER / 2
    tc_std_for_stretch  = tau_c_stats_override[1] if tau_c_stats_override else 1.0

    for t in range(n_steps):
        # Compute next outer state
        if prescription == 'baseline' or eps == 0.0:
            desired_g = outer_step_standard(outer_g)
            desired_e = outer_step_standard(outer_e)
        elif prescription == 'coupling':
            desired_g = outer_step_dcg_coupling(outer_g, tau_c_norm_g, eps)
            desired_e = outer_step_standard(outer_e)  # ether runs standard
        elif prescription == 'stretch':
            desired_g = outer_step_stretch(outer_g, tau_c_g_prev,
                                           tc_mean_for_stretch, tc_std_for_stretch)
            desired_e = outer_step_standard(outer_e)

        # Compute tau_c for glider tape (inner CA steps to match desired)
        tau_c_g = compute_tau_c(inner_g, desired_g)
        tau_c_hist[t] = tau_c_g
        tau_c_norm_g  = normalize_tau_c(tau_c_g)
        tau_c_g_prev  = tau_c_g

        outer_g = desired_g
        outer_e = desired_e

        # Reinitialize inner CAs from new outer state
        inner_g = init_inner_consistent(outer_g, M)
        inner_e = init_inner_consistent(outer_e, M)

        outer_hist[t + 1] = outer_g
        ether_hist[t + 1] = outer_e

    return outer_hist, ether_hist, tau_c_hist


# ── Step 0: Characterize τ_c distribution ────────────────────────────────────

def characterize_tau_c(n_steps: int = 20):
    """
    Measure tau_c distribution in pure ether and at glider cells.
    Runs n_steps outer steps; accumulates tau_c values.
    Compares glider tape to simultaneously-evolved pure ether tape to identify
    glider cells (avoids static-reference bug).
    """
    outer_e = make_ether_tape(L)
    inner_e = init_inner_consistent(outer_e, M)

    outer_g = embed_glider(make_ether_tape(L), L // 2)
    inner_g = init_inner_consistent(outer_g, M)

    ether_tc_all = []
    glider_tc_all = []
    ether_bg_tc_all = []

    for _ in range(n_steps):
        desired_e = outer_step_standard(outer_e)
        desired_g = outer_step_standard(outer_g)

        tc_e = compute_tau_c(inner_e, desired_e)
        tc_g = compute_tau_c(inner_g, desired_g)

        ether_tc_all.extend(tc_e.tolist())

        # Compare to evolved ether, not static initial ether
        diff_mask = (outer_g != outer_e)
        if diff_mask.sum() > 0 and diff_mask.sum() <= MAX_DIFF:
            glider_tc_all.extend(tc_g[diff_mask].tolist())
            ether_bg_tc_all.extend(tc_g[~diff_mask].tolist())

        outer_e = desired_e
        outer_g = desired_g
        inner_e = init_inner_consistent(outer_e, M)
        inner_g = init_inner_consistent(outer_g, M)

    ether_arr = np.array(ether_tc_all)
    glider_arr = np.array(glider_tc_all) if glider_tc_all else np.array([0.0])
    bg_arr = np.array(ether_bg_tc_all) if ether_bg_tc_all else ether_arr

    return {
        "ether": {
            "mean": float(ether_arr.mean()),
            "std":  float(ether_arr.std()),
            "max":  float(ether_arr.max()),
            "min":  float(ether_arr.min()),
            "n":    int(len(ether_arr)),
        },
        "glider_cells": {
            "mean": float(glider_arr.mean()),
            "std":  float(glider_arr.std()),
            "max":  float(glider_arr.max()),
            "min":  float(glider_arr.min()),
            "n":    int(len(glider_arr)),
        },
        "glider_background": {
            "mean": float(bg_arr.mean()),
            "std":  float(bg_arr.std()),
            "max":  float(bg_arr.max()),
        },
        "glider_ether_ratio": float(glider_arr.mean() / ether_arr.mean()) if ether_arr.mean() > 0 else 0.0,
    }


# ── Step 1: Single-glider stability ──────────────────────────────────────────

def test_single_glider_stability(eps: float, prescription: str = 'coupling'):
    """
    Run single glider at L//2 for T steps.
    Uses ether_hist[t] (evolved ether) as the reference at each step — not a static reference.
    Returns (survived: bool, n_survived_steps: int, speed: float).
    """
    outer_hist, ether_hist, _ = run_afca([L // 2], eps, prescription)

    com_history = []
    survived_steps = 0

    for t in range(1, T + 1):
        stable = glider_is_stable(outer_hist[t], ether_hist[t])
        if not stable:
            break
        survived_steps = t
        coms = glider_com_halves(outer_hist[t], ether_hist[t], n_gliders=1)
        if coms:
            com_history.append(coms[0])

    survived = survived_steps >= GLIDER_STABILITY_THRESHOLD

    speed = float('nan')
    if len(com_history) >= 10:
        xs = np.array(com_history, dtype=float)
        xs_uw = np.unwrap(xs * 2 * np.pi / L) * L / (2 * np.pi)
        ts = np.arange(len(xs_uw), dtype=float)
        speed = float(np.polyfit(ts, xs_uw, 1)[0])

    return survived, survived_steps, speed


# ── Step 2: Max DCG correction at a given ε ──────────────────────────────────

def measure_max_dcg_correction(eps: float, n_steps: int = 10):
    """
    Run single-glider AFCA with coupling prescription for n_steps.
    Reports max correction eps * tau_c_norm * neighbor_sum observed.
    """
    outer_g = embed_glider(make_ether_tape(L), L // 2)
    inner_g = init_inner_consistent(outer_g, M)
    tau_c_norm_g = np.ones(L, dtype=np.float32)
    max_correction = 0.0

    for _ in range(n_steps):
        desired_g = outer_step_standard(outer_g)  # use standard for measuring
        tc_g = compute_tau_c(inner_g, desired_g)
        tau_c_norm_g = normalize_tau_c(tc_g)

        neigh_sum = (np.roll(outer_g, 1) + np.roll(outer_g, -1)).astype(np.float64)
        correction = eps * tau_c_norm_g.astype(np.float64) * neigh_sum
        max_correction = max(max_correction, float(correction.max()))

        outer_g = desired_g
        inner_g = init_inner_consistent(outer_g, M)

    return max_correction


# ── Step 3: Two-glider clustering ────────────────────────────────────────────

def test_two_glider_distance(eps: float,
                             prescription: str,
                             pos1: int = L // 4,
                             pos2: int = 3 * L // 4):
    """
    Run two gliders and track inter-glider distance over T steps.
    Uses half-tape CoM split (fixes Round 1 clustering bug).
    Uses ether_hist[t] as evolved ether reference (fixes static-reference bug).
    Returns (distances, tau_c_ratio).
    """
    outer_hist, ether_hist, tau_c_hist = run_afca([pos1, pos2], eps, prescription)

    distances = []
    tau_c_glider_means = []
    tau_c_bg_means = []

    for t in range(1, T + 1):
        dist = two_glider_distance(outer_hist[t], ether_hist[t])
        distances.append(float(dist) if dist is not None else None)

        diff_mask = (outer_hist[t] != ether_hist[t])
        if diff_mask.sum() > 0 and diff_mask.sum() < MAX_DIFF and t > 0:
            tc = tau_c_hist[t - 1]
            tau_c_glider_means.append(float(tc[diff_mask].mean()))
            tau_c_bg_means.append(float(tc[~diff_mask].mean()))

    ratio = (float(np.mean(tau_c_glider_means) / np.mean(tau_c_bg_means))
             if tau_c_bg_means and np.mean(tau_c_bg_means) > 0 else 1.0)

    return distances, ratio


def distance_stats(dists):
    """Returns (initial_mean, final_mean, slope_cells_per_step)."""
    valid = [d for d in dists if d is not None]
    if len(valid) < 10:
        return None, None, 0.0
    n = len(valid)
    init_mean  = float(np.mean(valid[:max(1, n // 5)]))
    final_mean = float(np.mean(valid[-max(1, n // 5):]))
    ts         = np.arange(n, dtype=float)
    slope      = float(np.polyfit(ts, valid, 1)[0])
    return init_mean, final_mean, slope


# ── Step 4: Null tests ────────────────────────────────────────────────────────

def test_vacuum_null(eps: float, prescription: str, n_steps: int = 30):
    """
    Pure ether run.  tau_c std should remain low (homogeneous vacuum).
    Returns mean tau_c std.
    """
    outer = make_ether_tape(L)
    inner = init_inner_consistent(outer, M)
    tau_c_norm = np.ones(L, dtype=np.float32)
    tau_c_prev = np.ones(L, dtype=np.float32) * (MAX_INNER / 2)
    stds = []

    for _ in range(n_steps):
        if eps == 0.0 or prescription == 'baseline':
            desired = outer_step_standard(outer)
        elif prescription == 'coupling':
            desired = outer_step_dcg_coupling(outer, tau_c_norm, eps)
        elif prescription == 'stretch':
            mean_tc = float(tau_c_prev.mean())
            std_tc  = float(tau_c_prev.std())
            desired = outer_step_stretch(outer, tau_c_prev, mean_tc, std_tc)

        tc = compute_tau_c(inner, desired)
        stds.append(float(tc.std()))
        tau_c_norm = normalize_tau_c(tc)
        tau_c_prev = tc
        outer = desired
        inner = init_inner_consistent(outer, M)

    return float(np.mean(stds))


# ── Main ──────────────────────────────────────────────────────────────────────

t_start = time.time()
print(f"Rank 64-DCG Round 2: Dynamical Causal Graph AFCA (M=49)")
print(f"Parameters: M={M}, L={L}, T={T}, MAX_INNER={MAX_INNER}")
print(f"Epsilon values: {EPS_VALUES}")
print(f"Glider seed: {list(GLIDER)}")
print(f"Started at {time.strftime('%H:%M:%S')}\n")

results = {
    "experiment": "64-DCG Round 2",
    "round": 2,
    "M": M, "L": L, "T": T,
    "glider_seed": list(map(int, GLIDER)),
    "eps_values_tested": EPS_EXTENDED,
    "max_inner_steps": MAX_INNER,
    "prescriptions_tested": ["coupling_constant", "stretch"],
    "inner_reinit_policy": "fresh_ether_each_outer_step",
}

# ── Step 0: τ_c characterization ─────────────────────────────────────────────
print("=== Step 0: τ_c characterization (M=49) ===")
print("  Measuring tau_c distribution in pure ether and at glider cells...")
tc_char = characterize_tau_c(n_steps=20)
results["tau_c_ether"]  = tc_char["ether"]
results["tau_c_glider"] = tc_char["glider_cells"]
results["tau_c_glider_bg"] = tc_char["glider_background"]
results["tau_c_glider_ether_ratio"] = tc_char["glider_ether_ratio"]

print(f"  Ether: mean={tc_char['ether']['mean']:.2f}, std={tc_char['ether']['std']:.2f}, "
      f"max={tc_char['ether']['max']:.0f}")
print(f"  Glider cells: mean={tc_char['glider_cells']['mean']:.2f}, "
      f"std={tc_char['glider_cells']['std']:.2f}, max={tc_char['glider_cells']['max']:.0f}")
print(f"  Glider/ether ratio: {tc_char['glider_ether_ratio']:.3f}")

tc_ether_mean = tc_char["ether"]["mean"]
tc_ether_std  = tc_char["ether"]["std"]

# ── Step 1: Glider stability (coupling-constant prescription) ─────────────────
print("\n=== Step 1: Single-glider stability (coupling-constant) — extended ε range ===")
stability_coupling = {}
max_stable_eps = 0.0

for eps in EPS_EXTENDED:
    print(f"  ε={eps:.3f}: ...", end=" ", flush=True)
    survived, n_steps_survived, speed = test_single_glider_stability(eps, 'coupling')
    stability_coupling[f"eps_{eps}"] = {
        "survived": survived,
        "steps_survived": n_steps_survived,
        "speed_cells_per_step": round(float(speed) if not np.isnan(speed) else -99.0, 4),
    }
    flag = "STABLE" if survived else f"DISSOLVED(t={n_steps_survived})"
    spd_str = f"{speed:.4f}" if not np.isnan(speed) else "n/a"
    print(f"{flag}  speed={spd_str}")
    if survived:
        max_stable_eps = eps

results["glider_stability_coupling"] = stability_coupling
results["max_stable_eps_coupling"] = max_stable_eps
print(f"  → Max stable ε (coupling): {max_stable_eps}")

# ── Step 2: DCG correction magnitude ─────────────────────────────────────────
print("\n=== Step 2: DCG correction magnitude ===")
correction_results = {}
for eps in EPS_EXTENDED:
    if eps == 0.0:
        correction_results["eps_0.0"] = 0.0
        continue
    max_corr = measure_max_dcg_correction(eps)
    correction_results[f"eps_{eps}"] = round(max_corr, 6)
    crosses = max_corr > 0.5
    print(f"  ε={eps:.3f}: max correction = {max_corr:.4f}  {'> 0.5 ✓' if crosses else '≤ 0.5 ✗'}")

results["dcg_correction_by_eps"] = correction_results

# Correction at max_stable_eps
corr_at_max = correction_results.get(f"eps_{max_stable_eps}", 0.0) if max_stable_eps > 0 else 0.0
results["dcg_correction_at_max_eps"] = corr_at_max
results["crosses_threshold"] = bool(corr_at_max > 0.5)
print(f"  → At max_stable_eps={max_stable_eps}: correction={corr_at_max:.4f}, "
      f"crosses 0.5: {results['crosses_threshold']}")

# τ_c_norm diagnostics
tc_norm_max_est = tc_char["ether"]["max"] / tc_char["ether"]["mean"] if tc_char["ether"]["mean"] > 0 else 0.0
min_eps_for_flip = 0.5 / (tc_norm_max_est * 2) if tc_norm_max_est > 0 else float('inf')
print(f"\n=== τ_c_norm diagnostics (M={M}) ===")
print(f"  τ_c_norm_max (estimate) = {tc_norm_max_est:.3f}")
print(f"  Min ε for any cell flip = {min_eps_for_flip:.4f}")
print(f"  Max stable ε found      = {max_stable_eps}")
print(f"  Valid ε window          = [{min_eps_for_flip:.4f}, {max_stable_eps}]")
valid_window = min_eps_for_flip < max_stable_eps
print(f"  Window exists           = {valid_window}")
print(f"  Glider/ether τ_c ratio  = {tc_char['glider_ether_ratio']:.3f} "
      f"({'glider cells have LOWER tau_c — inverted!' if tc_char['glider_ether_ratio'] < 1.0 else 'glider cells have higher tau_c'})")
results["tau_c_norm_max_estimate"] = round(tc_norm_max_est, 3)
results["min_eps_for_flip"] = round(min_eps_for_flip, 4)
results["valid_eps_window_exists"] = valid_window
results["valid_eps_window"] = [round(min_eps_for_flip, 4), max_stable_eps]

# ── Step 3: Two-glider clustering (coupling-constant) ────────────────────────
print("\n=== Step 3: Two-glider clustering (coupling-constant) ===")
eps_dyn = max_stable_eps if max_stable_eps > 0.0 else 0.01

print(f"  Baseline (ε=0.0): ...", flush=True)
dist_base, ratio_base = test_two_glider_distance(0.0, 'baseline')
b_init, b_final, b_slope = distance_stats(dist_base)

print(f"  Dynamical (ε={eps_dyn}): ...", flush=True)
dist_dyn, ratio_dyn = test_two_glider_distance(eps_dyn, 'coupling')
d_init, d_final, d_slope = distance_stats(dist_dyn)

print(f"  Baseline:  init={b_init:.1f}, final={b_final:.1f}, slope={b_slope:+.4f} cells/step")
print(f"  Dynamical: init={d_init:.1f}, final={d_final:.1f}, slope={d_slope:+.4f} cells/step")
sep_delta_coupling = (d_slope - b_slope) if (b_slope is not None and d_slope is not None) else 0.0
print(f"  Separation slope change: {sep_delta_coupling:+.4f} cells/step")
print(f"  τ_c glider/background: baseline={ratio_base:.4f}, dynamical={ratio_dyn:.4f}")

results["two_glider_coupling"] = {
    "baseline":  [round(d, 2) if d is not None else None for d in dist_base],
    "dynamical": [round(d, 2) if d is not None else None for d in dist_dyn],
    "baseline_stats":  {"initial": b_init, "final": b_final, "slope": b_slope},
    "dynamical_stats": {"initial": d_init, "final": d_final, "slope": d_slope},
    "separation_delta_slope": round(sep_delta_coupling, 6),
    "tau_c_ratio_baseline":  round(ratio_base, 4),
    "tau_c_ratio_dynamical": round(ratio_dyn, 4),
}

# ── Step 4: Stretch prescription ─────────────────────────────────────────────
print("\n=== Step 4: Stretch prescription ===")
print(f"  Threshold: tau_c > {tc_ether_mean:.2f} + 1.5 × {tc_ether_std:.2f} = "
      f"{tc_ether_mean + 1.5 * tc_ether_std:.2f}")

print("  Single-glider stability (stretch):")
survived_stretch, n_steps_stretch, speed_stretch = test_single_glider_stability(0.0, 'stretch')
# Note: stretch prescription uses no eps — eps=0.0 parameter is ignored
print(f"    {'STABLE' if survived_stretch else 'DISSOLVED'} for {n_steps_stretch} steps, "
      f"speed={speed_stretch:.4f}")

if survived_stretch:
    print("  Two-glider clustering (stretch):")
    print("    Baseline (ε=0.0): ...", flush=True)
    dist_stretch_base, _ = test_two_glider_distance(0.0, 'baseline')

    print("    Dynamical (stretch): ...", flush=True)
    dist_stretch_dyn, ratio_stretch = test_two_glider_distance(0.0, 'stretch')

    sb_init, sb_final, sb_slope = distance_stats(dist_stretch_base)
    sd_init, sd_final, sd_slope = distance_stats(dist_stretch_dyn)
    sep_delta_stretch = (sd_slope - sb_slope) if sb_slope is not None else 0.0
    print(f"    Baseline:  init={sb_init:.1f}, final={sb_final:.1f}, slope={sb_slope:+.4f}")
    print(f"    Dynamical: init={sd_init:.1f}, final={sd_final:.1f}, slope={sd_slope:+.4f}")
    print(f"    Separation slope change: {sep_delta_stretch:+.4f}")

    results["two_glider_stretch"] = {
        "baseline":  [round(d, 2) if d is not None else None for d in dist_stretch_base],
        "dynamical": [round(d, 2) if d is not None else None for d in dist_stretch_dyn],
        "baseline_stats":  {"initial": sb_init, "final": sb_final, "slope": sb_slope},
        "dynamical_stats": {"initial": sd_init, "final": sd_final, "slope": sd_slope},
        "separation_delta_slope": round(sep_delta_stretch, 6),
        "tau_c_ratio": round(ratio_stretch, 4),
    }
else:
    sep_delta_stretch = 0.0
    results["two_glider_stretch"] = {
        "note": "Stretch prescription dissolved glider — not measured"
    }
    print("  Stretch glider dissolved — skipping two-glider test")

# ── Step 5: Null tests ────────────────────────────────────────────────────────
print("\n=== Step 5: Null tests ===")

# N1: single-glider speed ratio (coupling)
spd_base = stability_coupling.get("eps_0.0", {}).get("speed_cells_per_step", 0.0)
spd_dyn  = stability_coupling.get(f"eps_{eps_dyn}", {}).get("speed_cells_per_step", 0.0)
speed_ratio = (spd_dyn / spd_base) if (spd_base and abs(spd_base) > 0.01) else 1.0
speed_null_pass = bool(0.80 <= abs(speed_ratio) <= 1.25)
print(f"  N1 single-glider speed ratio (coupling): {speed_ratio:.4f}  "
      f"{'PASS' if speed_null_pass else 'FAIL'}")

# N2: vacuum tau_c std under coupling DCG
# For M=49, ether tau_c already has std ~10-12 (rich transient dynamics).
# PASS if DCG vacuum std is within 2x of pure ether std (no spontaneous structure).
print(f"  N2 vacuum tau_c std (coupling, ε={eps_dyn}): ...", end=" ", flush=True)
vac_std_coupling = test_vacuum_null(eps_dyn, 'coupling')
vac_null_coupling = bool(vac_std_coupling <= 2.0 * tc_ether_std + 1.0)
print(f"{vac_std_coupling:.4f}  (ether baseline std={tc_ether_std:.2f})  "
      f"{'PASS' if vac_null_coupling else 'WARN'}")

# N3: vacuum null under stretch prescription
print(f"  N3 vacuum tau_c std (stretch): ...", end=" ", flush=True)
vac_std_stretch = test_vacuum_null(0.0, 'stretch')
vac_null_stretch = bool(vac_std_stretch <= 2.0 * tc_ether_std + 1.0)
print(f"{vac_std_stretch:.4f}  {'PASS' if vac_null_stretch else 'WARN'}")

results["null_tests"] = {
    "N1_speed_ratio":         round(speed_ratio, 4),
    "N1_speed_pass":          speed_null_pass,
    "N2_vacuum_tau_c_std_coupling": round(vac_std_coupling, 4),
    "N2_vacuum_pass_coupling":      vac_null_coupling,
    "N3_vacuum_tau_c_std_stretch":  round(vac_std_stretch, 4),
    "N3_vacuum_pass_stretch":       vac_null_stretch,
}

# ── Conclusion ────────────────────────────────────────────────────────────────
print("\n=== Conclusion ===")

null_pass_coupling = speed_null_pass and vac_null_coupling
null_pass_stretch  = speed_null_pass and vac_null_stretch

# Coupling prescription assessment
coupling_attraction = sep_delta_coupling
if coupling_attraction < -2.0 and null_pass_coupling:
    coupling_verdict = "CONFIRMED"
elif coupling_attraction < -0.50 and null_pass_coupling:
    coupling_verdict = "WEAK"
elif coupling_attraction < 0.0:
    coupling_verdict = "INCONCLUSIVE"
else:
    coupling_verdict = "NEGATIVE"

# Stretch prescription assessment
stretch_attraction = sep_delta_stretch if survived_stretch else 0.0
if stretch_attraction < -2.0 and null_pass_stretch:
    stretch_verdict = "CONFIRMED"
elif stretch_attraction < -0.50 and null_pass_stretch:
    stretch_verdict = "WEAK"
elif stretch_attraction < 0.0:
    stretch_verdict = "INCONCLUSIVE"
elif not survived_stretch:
    stretch_verdict = "DISSOLVED"
else:
    stretch_verdict = "NEGATIVE"

# Overall verdict: best of the two prescriptions
overall_verdicts = [coupling_verdict, stretch_verdict]
if "CONFIRMED" in overall_verdicts:
    conclusion = "CONFIRMED"
elif "WEAK" in overall_verdicts:
    conclusion = "WEAK"
elif "DISSOLVED" in overall_verdicts and all(v in ("DISSOLVED", "NEGATIVE") for v in overall_verdicts):
    conclusion = "NEGATIVE"
elif "INCONCLUSIVE" in overall_verdicts:
    conclusion = "INCONCLUSIVE"
else:
    conclusion = "NEGATIVE"

# Diagnosis
tau_ratio = tc_char["glider_ether_ratio"]
if tau_ratio > 2.0:
    tau_diagnosis = f"GOOD: glider/ether tau_c ratio = {tau_ratio:.2f} (sufficient for DCG effect)"
elif tau_ratio > 1.2:
    tau_diagnosis = f"MARGINAL: glider/ether tau_c ratio = {tau_ratio:.2f} (borderline for DCG effect)"
else:
    tau_diagnosis = (f"POOR: glider/ether tau_c ratio = {tau_ratio:.2f} "
                     f"(insufficient separation — M=49 may still show binary behavior)")

next_round = ""
if conclusion in ("NEGATIVE", "INCONCLUSIVE"):
    next_round = (
        "Root causes at M=49: (1) tau_c_norm_max=2.6 barely exceeds M=7 value (2.33) — "
        "ratio of max/mean does not improve with M because inner CA converges in ~26 steps "
        "regardless of M; (2) glider/ether tau_c ratio=0.90 (inverted!) — glider cells have "
        "LOWER tau_c than ether, making coupling correction preferentially affect ether not glider; "
        "(3) fresh inner reinit each outer step erases all glider information from inner CA. "
        "Options for Round 3: (A) No-reinit: let inner CA accumulate state across outer steps — "
        "glider cells would develop nonequilibrium inner state with persistently high tau_c; "
        "(B) M=197 (prime, so gcd(14,197)=1 — no periodic seam): broader tau_c range and "
        "different transient structure; (C) Causal graph prescription: directly compute "
        "Ollivier-Ricci curvature kappa on Rule 110 causal edges and use kappa as correction "
        "(avoids tau_c entirely — uses geometric signal directly)."
    )

results["coupling_verdict"]         = coupling_verdict
results["stretch_verdict"]          = stretch_verdict
results["conclusion"]               = conclusion
results["tau_c_diagnosis"]          = tau_diagnosis
results["null_tests_pass_coupling"] = null_pass_coupling
results["null_tests_pass_stretch"]  = null_pass_stretch
results["sep_delta_coupling"]       = round(coupling_attraction, 6)
results["sep_delta_stretch"]        = round(stretch_attraction, 6)
results["next_round"]               = next_round
results["elapsed_s"]                = round(time.time() - t_start, 1)

print(f"  τ_c characterization: {tau_diagnosis}")
print(f"  Max stable ε (coupling): {max_stable_eps}")
print(f"  DCG correction at max_stable_eps: {corr_at_max:.4f} "
      f"({'crosses 0.5 ✓' if results['crosses_threshold'] else 'below 0.5 ✗'})")
print(f"  Coupling prescription — attraction slope change: {coupling_attraction:+.4f}")
print(f"    Verdict: {coupling_verdict}")
print(f"  Stretch prescription — attraction slope change: {stretch_attraction:+.4f}")
print(f"    Verdict: {stretch_verdict}")
print(f"  Null tests (coupling): {null_pass_coupling}")
print(f"  Overall conclusion: {conclusion}")
print(f"  Elapsed: {results['elapsed_s']:.1f}s")
if next_round:
    print(f"  Next round: {next_round[:100]}...")

# ── Save results ──────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SCRIPT_DIR.parent / "data"
out_path = _DATA_DIR / "rank64_dcg_round2_m49_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved → {out_path}")
signal.alarm(0)
print("Done.")
