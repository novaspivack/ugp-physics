#!/usr/bin/env python3
"""
rank64_dcg_round3_noreinit.py
EPIC_072 Rank 64-DCG — Dynamical Causal Graph AFCA Round 3 (no-reinit prescription)

Rounds 1+2 NEGATIVE (fresh-reinit inner CA):
- M=7 (Round 1): τ_c binary {0,1}; no valid ε window.
- M=49 (Round 2): inner CA re-seeded from ETHER14 each outer step. Glider/ether
  τ_c ratio = 0.90 (inverted). Root cause: fresh reinit erases all glider
  information — inner CA sees only ether-initialized state regardless of outer
  dynamics.

Round 3: No-reinit prescription.
- Inner CA persists across outer steps (NO ETHER14 reinit per step).
- After each outer step, outer[i] is injected into the center column of inner[i],
  coupling ongoing outer dynamics into inner CA state.
- Glider cells: outer[i] changes as the glider moves through → injection sequence
  differs from ether → inner CA develops a distinct persistent trajectory.
- New τ_c observable (stability measure): steps from current inner CA state until
  majority changes. High τ_c = stable majority; low τ_c = volatile majority.

Expected outcome (hypothesis): glider cells under persistent non-ether injection
develop HIGHER τ_c than ether cells (larger τ_c = more coherent/stable inner state
due to glider's structured pattern), enabling the original coupling-constant
DCG prescription to produce attraction. Alternatively, glider cells may develop
LOWER τ_c (more volatile), which is tested via inverse-activity coupling.

Step 1: Characterise τ_c distribution under no-reinit.
Step 2: Two-glider clustering (if ratio > 1.2, standard coupling; if < 0.8,
         inverse-activity coupling).
Step 3: Null tests.
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
    print(f"\nTIMEOUT: {TIMEOUT_S}s wall-clock limit reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_S)

# ── Constants ─────────────────────────────────────────────────────────────────
ETHER14  = np.array([1,1,1,1,1,0,0,0,1,0,0,1,1,0], dtype=np.uint8)
LUT110   = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
GLIDER   = np.array([0,1,0,0,1,0,1,0,0,1], dtype=np.uint8)

M          = 7      # inner CA width
L_CHAR     = 100    # outer tape length for characterization (Steps 0–1)
L_FULL     = 200    # outer tape length for two-glider test (Step 2)
T_BURN     = 20     # burn-in outer steps before τ_c measurement
T_CHAR     = 100    # measurement outer steps (Step 1)
T_FULL     = 100    # outer steps for clustering and null tests

# Stability probe parameters: how many inner steps to probe from current state.
# For M=7, the inner CA has ≤2^7=128 states; majority should flip within MAX_PROBE
# steps for most states. Capped at MAX_PROBE if majority never changes.
MAX_PROBE  = 100

MAX_DIFF   = 50     # max perturbation width before glider declared dissolved
GLIDER_STABILITY_THRESHOLD = 30

INJECT_COL = M // 2  # column where outer[i] is injected into inner CA (= 3 for M=7)

PHASE_MAJ1 = 0  # ETHER14 phase → majority=1 for M=7
PHASE_MAJ0 = 7  # ETHER14 phase → majority=0 for M=7

EPS_STANDARD = [0.0, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20]
EPS_EXTENDED = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20]


# ── CA primitives ─────────────────────────────────────────────────────────────

def _ether14_window(phase: int, width: int) -> np.ndarray:
    return np.array([ETHER14[(phase + j) % 14] for j in range(width)], dtype=np.uint8)


def make_ether_tape(length: int) -> np.ndarray:
    return np.array([ETHER14[i % 14] for i in range(length)], dtype=np.uint8)


def embed_glider(tape: np.ndarray, pos: int) -> np.ndarray:
    t = tape.copy()
    for j, bit in enumerate(GLIDER):
        t[(pos + j) % len(t)] = bit
    return t


def init_inner_consistent(outer: np.ndarray, width: int = M) -> np.ndarray:
    """Initialize inner CAs from ETHER14 windows, phase chosen by outer bit."""
    length = len(outer)
    inner = np.zeros((length, width), dtype=np.uint8)
    for i in range(length):
        phase = PHASE_MAJ1 if outer[i] == 1 else PHASE_MAJ0
        inner[i] = _ether14_window(phase, width)
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


def normalize_tau_c(tau_c: np.ndarray) -> np.ndarray:
    """Normalize by mean; return ones if mean is zero."""
    m = float(tau_c.mean())
    return (tau_c / m).astype(np.float32) if m > 1e-12 else np.ones(len(tau_c), dtype=np.float32)


# ── No-reinit inner CA update ─────────────────────────────────────────────────

def advance_inner_noreinit(inner: np.ndarray, outer: np.ndarray) -> np.ndarray:
    """
    Run 1 Rule 110 step, then inject outer[i] into center column of inner CA.
    This couples ongoing outer dynamics to the persistent inner CA state.
    Cells where outer[i] changes over time (glider positions) receive a different
    injection sequence from static ether cells.
    """
    inner_new = inner_step_all(inner)
    inner_new[:, INJECT_COL] = outer
    return inner_new


# ── τ_c stability observable ──────────────────────────────────────────────────

def compute_tau_c_stability(inner: np.ndarray) -> np.ndarray:
    """
    From current inner CA state, count steps until majority changes.
    High τ_c = stable (majority persists for many steps).
    Low τ_c = volatile (majority flips quickly).
    Caps at MAX_PROBE if majority never changes within probe window.
    """
    current_maj = majority_vote(inner)
    tau_c = np.full(len(inner), float(MAX_PROBE), dtype=np.float32)
    done = np.zeros(len(inner), dtype=bool)
    current = inner.copy()

    for step in range(1, MAX_PROBE + 1):
        if done.all():
            break
        current = inner_step_all(current)
        maj = majority_vote(current)
        flipped = (~done) & (maj != current_maj)
        tau_c[flipped] = float(step)
        done |= flipped

    return tau_c


# ── DCG outer step prescriptions ──────────────────────────────────────────────

def outer_step_dcg_stability(outer: np.ndarray,
                              tau_c_norm: np.ndarray,
                              eps: float) -> np.ndarray:
    """
    Stability coupling: cells with HIGH τ_c (stable) get larger correction.
    Use if glider cells have τ_c ratio > 1 (glider more stable than ether).
    val[i] = rule110(outer) + eps * τ_c_norm[i] * neighbor_sum
    """
    l = np.roll(outer, 1).astype(np.int32)
    c = outer.astype(np.int32)
    r = np.roll(outer, -1).astype(np.int32)
    b_std = LUT110[(l << 2) | (c << 1) | r].astype(np.float64)
    neigh_sum = (np.roll(outer, 1) + np.roll(outer, -1)).astype(np.float64)
    val = b_std + eps * tau_c_norm.astype(np.float64) * neigh_sum
    return (val > 0.5).astype(np.uint8)


def outer_step_dcg_activity(outer: np.ndarray,
                             activity_norm: np.ndarray,
                             eps: float) -> np.ndarray:
    """
    Activity coupling: cells with LOW τ_c (volatile, activity = MAX_PROBE - τ_c)
    get larger correction. Use if glider cells have τ_c ratio < 1 (glider more volatile).
    val[i] = rule110(outer) + eps * activity_norm[i] * neighbor_sum
    """
    l = np.roll(outer, 1).astype(np.int32)
    c = outer.astype(np.int32)
    r = np.roll(outer, -1).astype(np.int32)
    b_std = LUT110[(l << 2) | (c << 1) | r].astype(np.float64)
    neigh_sum = (np.roll(outer, 1) + np.roll(outer, -1)).astype(np.float64)
    val = b_std + eps * activity_norm.astype(np.float64) * neigh_sum
    return (val > 0.5).astype(np.uint8)


# ── Glider tracking (same half-tape CoM method as Round 2) ───────────────────

def glider_com_halves(outer: np.ndarray, ether_ref: np.ndarray, n_gliders: int = 2):
    diff = (outer != ether_ref).astype(np.float64)
    half = len(outer) // 2
    coms = []
    for h in range(n_gliders):
        start = h * half
        end   = (h + 1) * half
        seg   = diff[start:end]
        if seg.sum() > 0:
            positions = np.arange(start, end, dtype=float)
            coms.append(float((positions * seg).sum() / seg.sum()))
        else:
            coms.append(float(start + half / 2))
    return coms


def two_glider_distance(outer: np.ndarray, ether_ref: np.ndarray, L: int) -> float | None:
    coms = glider_com_halves(outer, ether_ref, n_gliders=2)
    if len(coms) < 2:
        return None
    raw = abs(coms[1] - coms[0])
    return float(min(raw, L - raw))


def glider_is_stable(outer: np.ndarray, ether_ref: np.ndarray) -> bool:
    total = int((outer != ether_ref).sum())
    return 0 < total <= MAX_DIFF


def distance_stats(dists):
    valid = [d for d in dists if d is not None]
    if len(valid) < 10:
        return None, None, 0.0
    n = len(valid)
    init_mean  = float(np.mean(valid[:max(1, n // 5)]))
    final_mean = float(np.mean(valid[-max(1, n // 5):]))
    slope      = float(np.polyfit(np.arange(n, dtype=float), valid, 1)[0])
    return init_mean, final_mean, slope


# ── Step 0 (pre-check): τ_c orbit audit on pure ether ────────────────────────

def audit_ether_tau_c_orbit():
    """
    Sanity check: measure τ_c stability distribution in pure ether under no-reinit.
    Also check whether inner CAs ever flip majority at all (detect all-cap case).
    Returns (mean, std, frac_capped) where frac_capped = fraction of measurements
    hitting MAX_PROBE without a majority flip.
    """
    L = L_CHAR
    outer = make_ether_tape(L)
    inner = init_inner_consistent(outer)

    all_tc = []
    for t in range(T_BURN + 30):
        tc = compute_tau_c_stability(inner)
        if t >= T_BURN:
            all_tc.extend(tc.tolist())
        outer_new = outer_step_standard(outer)
        inner = advance_inner_noreinit(inner, outer_new)
        outer = outer_new

    arr = np.array(all_tc)
    frac_capped = float((arr >= MAX_PROBE).mean())
    return {
        "mean": float(arr.mean()),
        "std":  float(arr.std()),
        "min":  float(arr.min()),
        "max":  float(arr.max()),
        "frac_capped": frac_capped,
        "n": int(len(arr)),
    }


# ── Step 1: τ_c characterization ─────────────────────────────────────────────

def characterize_tau_c_noreinit():
    """
    Compare τ_c distribution at glider positions vs ether positions under no-reinit.
    - Burn-in T_BURN outer steps (inner CA accumulates state).
    - Measure τ_c for T_CHAR outer steps.
    - Glider cells: outer tape diff vs simultaneously-evolved pure-ether reference.
    Returns stats and ratio.
    """
    L = L_CHAR

    # Pure ether tape (reference)
    outer_e = make_ether_tape(L)
    inner_e = init_inner_consistent(outer_e)

    # Glider tape
    outer_g = embed_glider(make_ether_tape(L), L // 2)
    inner_g = init_inner_consistent(outer_g)

    # Burn-in: no-reinit inner CA accumulates state
    for _ in range(T_BURN):
        outer_e_new = outer_step_standard(outer_e)
        outer_g_new = outer_step_standard(outer_g)
        inner_e = advance_inner_noreinit(inner_e, outer_e_new)
        inner_g = advance_inner_noreinit(inner_g, outer_g_new)
        outer_e = outer_e_new
        outer_g = outer_g_new

    # Measurement phase
    ether_tc_all  = []
    glider_tc_all = []
    bg_tc_all     = []

    for _ in range(T_CHAR):
        tc_g = compute_tau_c_stability(inner_g)
        tc_e = compute_tau_c_stability(inner_e)

        ether_tc_all.extend(tc_e.tolist())

        diff_mask = (outer_g != outer_e)
        if diff_mask.sum() > 0 and diff_mask.sum() <= MAX_DIFF:
            glider_tc_all.extend(tc_g[diff_mask].tolist())
            bg_tc_all.extend(tc_g[~diff_mask].tolist())

        outer_e_new = outer_step_standard(outer_e)
        outer_g_new = outer_step_standard(outer_g)
        inner_e = advance_inner_noreinit(inner_e, outer_e_new)
        inner_g = advance_inner_noreinit(inner_g, outer_g_new)
        outer_e = outer_e_new
        outer_g = outer_g_new

    ether_arr  = np.array(ether_tc_all)
    glider_arr = np.array(glider_tc_all) if glider_tc_all else np.array([float(MAX_PROBE)])
    bg_arr     = np.array(bg_tc_all) if bg_tc_all else ether_arr

    ratio = (float(glider_arr.mean() / ether_arr.mean())
             if ether_arr.mean() > 1e-12 else 1.0)

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
        "glider_bg": {
            "mean": float(bg_arr.mean()),
            "std":  float(bg_arr.std()),
        },
        "glider_ether_ratio": ratio,
    }


# ── Core no-reinit AFCA runner ────────────────────────────────────────────────

def run_noreinit_afca(L: int,
                      glider_positions: list,
                      eps: float,
                      prescription: str,
                      n_steps: int,
                      burn_in: int = T_BURN) -> tuple:
    """
    Run no-reinit AFCA.
    prescription: 'baseline' | 'stability' (high τ_c → larger correction)
                             | 'activity' (low τ_c / high volatility → larger correction)

    burn_in: outer steps before applying DCG correction (inner CA accumulates state).
    Returns (outer_hist, ether_hist, tau_c_hist).
    """
    outer_g = make_ether_tape(L)
    for pos in glider_positions:
        outer_g = embed_glider(outer_g, pos)
    outer_e = make_ether_tape(L)

    inner_g = init_inner_consistent(outer_g)
    inner_e = init_inner_consistent(outer_e)

    # Burn-in: no DCG coupling, inner CA accumulates
    for _ in range(burn_in):
        outer_g = outer_step_standard(outer_g)
        outer_e = outer_step_standard(outer_e)
        inner_g = advance_inner_noreinit(inner_g, outer_g)
        inner_e = advance_inner_noreinit(inner_e, outer_e)

    outer_hist  = np.zeros((n_steps + 1, L), dtype=np.uint8)
    ether_hist  = np.zeros((n_steps + 1, L), dtype=np.uint8)
    tau_c_hist  = np.zeros((n_steps, L), dtype=np.float32)

    outer_hist[0] = outer_g
    ether_hist[0] = outer_e

    tau_c_norm_g   = np.ones(L, dtype=np.float32)
    activity_norm_g = np.ones(L, dtype=np.float32)

    for t in range(n_steps):
        # Measure τ_c from current inner CA state
        if prescription != 'baseline':
            tc_g = compute_tau_c_stability(inner_g)
            tau_c_hist[t] = tc_g
            tau_c_norm_g    = normalize_tau_c(tc_g)
            # Activity = inverse of stability
            activity = (MAX_PROBE - tc_g).astype(np.float32)
            activity = np.clip(activity, 0.0, None)
            activity_norm_g = normalize_tau_c(activity)

        # Outer step
        if prescription == 'baseline' or eps == 0.0:
            new_outer_g = outer_step_standard(outer_g)
        elif prescription == 'stability':
            new_outer_g = outer_step_dcg_stability(outer_g, tau_c_norm_g, eps)
        elif prescription == 'activity':
            new_outer_g = outer_step_dcg_activity(outer_g, activity_norm_g, eps)

        new_outer_e = outer_step_standard(outer_e)

        # No-reinit inner update (inject new outer values)
        inner_g = advance_inner_noreinit(inner_g, new_outer_g)
        inner_e = advance_inner_noreinit(inner_e, new_outer_e)

        outer_g = new_outer_g
        outer_e = new_outer_e
        outer_hist[t + 1] = outer_g
        ether_hist[t + 1] = outer_e

    return outer_hist, ether_hist, tau_c_hist


# ── Step 2 helpers ────────────────────────────────────────────────────────────

def test_single_glider_noreinit(L: int, eps: float, prescription: str):
    outer_hist, ether_hist, _ = run_noreinit_afca(L, [L // 2], eps, prescription, T_FULL)
    com_history = []
    survived_steps = 0
    for t in range(1, T_FULL + 1):
        if not glider_is_stable(outer_hist[t], ether_hist[t]):
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


def test_two_glider_noreinit(L: int, eps: float, prescription: str):
    pos1, pos2 = L // 4, 3 * L // 4
    outer_hist, ether_hist, tc_hist = run_noreinit_afca(L, [pos1, pos2], eps, prescription, T_FULL)
    distances = []
    glider_tc_means = []
    bg_tc_means     = []
    for t in range(1, T_FULL + 1):
        dist = two_glider_distance(outer_hist[t], ether_hist[t], L)
        distances.append(float(dist) if dist is not None else None)
        diff_mask = (outer_hist[t] != ether_hist[t])
        if diff_mask.sum() > 0 and diff_mask.sum() < MAX_DIFF and t > 0:
            tc = tc_hist[t - 1]
            glider_tc_means.append(float(tc[diff_mask].mean()))
            bg_tc_means.append(float(tc[~diff_mask].mean()))
    tc_ratio = (float(np.mean(glider_tc_means) / np.mean(bg_tc_means))
                if bg_tc_means and np.mean(bg_tc_means) > 0 else 1.0)
    return distances, tc_ratio


# ── Main ──────────────────────────────────────────────────────────────────────

t_start = time.time()
print(f"Rank 64-DCG Round 3: Dynamical Causal Graph AFCA (no-reinit prescription)")
print(f"Parameters: M={M}, L_char={L_CHAR}, L_full={L_FULL}, T_burn={T_BURN}, "
      f"T_char={T_CHAR}, T_full={T_FULL}, MAX_PROBE={MAX_PROBE}")
print(f"Injection: outer[i] → inner[i][{INJECT_COL}] after each outer step")
print(f"Started at {time.strftime('%H:%M:%S')}\n")

results = {
    "experiment": "64-DCG Round 3",
    "round": 3,
    "prescription": "no-reinit",
    "M": M, "L_char": L_CHAR, "L_full": L_FULL,
    "T_burn": T_BURN, "T_char": T_CHAR, "T_full": T_FULL,
    "MAX_PROBE": MAX_PROBE,
    "inject_col": INJECT_COL,
    "inner_reinit_policy": "no_reinit_injection_at_center_column",
    "glider_seed": list(map(int, GLIDER)),
}

# ── Step 0: Orbit audit (sanity check) ───────────────────────────────────────
print("=== Step 0: Ether τ_c stability audit (inner CA majority-flip rate) ===")
print("  Running pure ether under no-reinit to check τ_c distribution...", flush=True)
orbit_audit = audit_ether_tau_c_orbit()
results["ether_orbit_audit"] = orbit_audit
print(f"  τ_c stability: mean={orbit_audit['mean']:.2f}, std={orbit_audit['std']:.2f}, "
      f"min={orbit_audit['min']:.0f}, max={orbit_audit['max']:.0f}")
print(f"  Fraction capped at MAX_PROBE={MAX_PROBE}: {orbit_audit['frac_capped']:.3f}")
if orbit_audit["frac_capped"] > 0.95:
    print("  WARNING: >95% of inner CAs never flip majority under no-reinit ether.")
    print("  τ_c will be near-uniform; glider/ether discrimination may be impossible.")
elif orbit_audit["frac_capped"] < 0.20:
    print("  GOOD: Most inner CAs do flip majority — valid τ_c spread observed.")
else:
    print(f"  PARTIAL: {orbit_audit['frac_capped']:.1%} capped — some τ_c spread available.")

# ── Step 1: τ_c characterization ─────────────────────────────────────────────
print("\n=== Step 1: τ_c characterization — glider vs ether cells (no-reinit) ===")
print("  Burn-in 20 outer steps, then measure for 100 outer steps...", flush=True)
tc_char = characterize_tau_c_noreinit()
results["tau_c_ether"]        = tc_char["ether"]
results["tau_c_glider"]       = tc_char["glider_cells"]
results["tau_c_glider_bg"]    = tc_char["glider_bg"]
results["tau_c_glider_ether_ratio"] = tc_char["glider_ether_ratio"]

ratio = tc_char["glider_ether_ratio"]
print(f"  Ether reference: mean={tc_char['ether']['mean']:.2f}, "
      f"std={tc_char['ether']['std']:.2f}, max={tc_char['ether']['max']:.0f}")
print(f"  Glider cells:    mean={tc_char['glider_cells']['mean']:.2f}, "
      f"std={tc_char['glider_cells']['std']:.2f}, max={tc_char['glider_cells']['max']:.0f}, "
      f"n={tc_char['glider_cells']['n']}")
print(f"  Glider/ether τ_c stability ratio: {ratio:.4f}")

if tc_char["glider_cells"]["n"] < 10:
    ratio_verdict = "INSUFFICIENT_DATA"
    print("  WARNING: < 10 glider-cell measurements — glider may have dissolved or diff_mask empty.")
elif ratio > 1.2:
    ratio_verdict = "RATIO_HIGH"
    print(f"  RATIO > 1.2: Glider cells more stable → stability coupling applies.")
elif ratio < 0.8:
    ratio_verdict = "RATIO_LOW"
    print(f"  RATIO < 0.8: Glider cells more volatile → activity coupling applies.")
else:
    ratio_verdict = "RATIO_FLAT"
    print(f"  RATIO ≈ 1.0 (range 0.8–1.2): No significant τ_c discrimination. Prescriptions likely ineffective.")

results["ratio_verdict"] = ratio_verdict
results["ratio_exceeds_threshold"] = bool(ratio > 1.2)

# ── Step 1b: Single-glider speed measurement at ε=0 (baseline) ───────────────
print("\n=== Step 1b: Single-glider speed (baseline, no-reinit, ε=0) ===")
surv_base, nstep_base, speed_base = test_single_glider_noreinit(L_CHAR, 0.0, 'baseline')
print(f"  Survived: {surv_base} for {nstep_base} steps, speed = "
      f"{speed_base:.4f} cells/step" if not np.isnan(speed_base) else
      f"  Survived: {surv_base} for {nstep_base} steps, speed = n/a")
results["baseline_glider_survived"] = surv_base
results["baseline_glider_speed"]    = round(float(speed_base) if not np.isnan(speed_base) else -99.0, 4)

# ── Step 2: Two-glider clustering ────────────────────────────────────────────
L = L_FULL

proceed_step2 = (ratio_verdict in ("RATIO_HIGH", "RATIO_LOW") and
                 tc_char["glider_cells"]["n"] >= 10 and surv_base)

two_glider_result = "SKIPPED"

if not proceed_step2:
    reason = ("τ_c ratio in dead-zone [0.8, 1.2]" if ratio_verdict == "RATIO_FLAT"
              else "glider unstable or insufficient data at ε=0")
    print(f"\n=== Step 2: Two-glider clustering — SKIPPED ({reason}) ===")
    results["two_glider_result"] = two_glider_result
    results["step2_skip_reason"] = reason
else:
    # Choose prescription based on ratio
    primary_prescription = 'stability' if ratio_verdict == "RATIO_HIGH" else 'activity'
    print(f"\n=== Step 2: Two-glider clustering (L={L}, prescription={primary_prescription}) ===")

    # Single-glider stability sweep to find max stable ε
    print("  Sweeping ε for single-glider stability...", flush=True)
    stability = {}
    max_stable_eps = 0.0
    for eps in EPS_STANDARD:
        surv, nstep, spd = test_single_glider_noreinit(L, eps, primary_prescription)
        stability[f"eps_{eps}"] = {
            "survived": surv,
            "steps_survived": nstep,
            "speed": round(float(spd) if not np.isnan(spd) else -99.0, 4),
        }
        print(f"    ε={eps:.3f}: {'STABLE' if surv else f'DISSOLVED(t={nstep})'}, "
              f"speed={spd:.4f}" if not np.isnan(spd) else
              f"    ε={eps:.3f}: {'STABLE' if surv else f'DISSOLVED(t={nstep})'}, speed=n/a")
        if surv:
            max_stable_eps = eps
    results["single_glider_stability"] = stability
    results["max_stable_eps"] = max_stable_eps
    print(f"  Max stable ε: {max_stable_eps}")

    eps_test = min(max_stable_eps, 0.10)
    if eps_test == 0.0 and max_stable_eps == 0.0:
        print("  No stable ε found — all eps dissolve glider. Skipping two-glider test.")
        results["two_glider_result"] = "SKIPPED_no_stable_eps"
        two_glider_result = "SKIPPED"
    else:
        # Baseline (ε=0)
        print(f"  Baseline (ε=0.0): ...", flush=True)
        dist_base, ratio_base = test_two_glider_noreinit(L, 0.0, 'baseline')
        b_init, b_final, b_slope = distance_stats(dist_base)
        print(f"    init={b_init:.1f}, final={b_final:.1f}, slope={b_slope:+.4f}")

        # DCG coupling at primary prescription
        print(f"  DCG {primary_prescription} (ε={eps_test:.3f}): ...", flush=True)
        dist_dcg, ratio_dcg = test_two_glider_noreinit(L, eps_test, primary_prescription)
        d_init, d_final, d_slope = distance_stats(dist_dcg)
        sep_delta = (d_slope - b_slope) if b_slope is not None else 0.0
        print(f"    init={d_init:.1f}, final={d_final:.1f}, slope={d_slope:+.4f}")
        print(f"  Separation slope change: {sep_delta:+.4f} cells/step")

        # Assessment
        if sep_delta < -2.0:
            two_glider_result = "CONFIRMED"
        elif sep_delta < -0.50:
            two_glider_result = "WEAK"
        elif sep_delta < 0.0:
            two_glider_result = "INCONCLUSIVE"
        else:
            two_glider_result = "NEGATIVE"

        print(f"  Two-glider verdict: {two_glider_result}")

        results["two_glider"] = {
            "eps_tested": eps_test,
            "prescription": primary_prescription,
            "baseline_slope": b_slope,
            "dcg_slope": d_slope,
            "sep_delta": round(sep_delta, 6),
            "baseline_stats": {"initial": b_init, "final": b_final, "slope": b_slope},
            "dcg_stats": {"initial": d_init, "final": d_final, "slope": d_slope},
            "tau_c_ratio_dcg": round(ratio_dcg, 4),
            "two_glider_result": two_glider_result,
        }
        results["two_glider_result"] = two_glider_result

# ── Step 3: Null tests ────────────────────────────────────────────────────────
print("\n=== Step 3: Null tests ===")

# N1: single-glider speed ratio at ε=0 — should be ~1.0 relative to Round 2
print("  N1: Single-glider speed baseline check (ε=0, no-reinit vs Round 2)...")
round2_speed = -0.2512  # from Round 2 results
speed_nr = results["baseline_glider_speed"]
if speed_nr == -99.0:
    n1_pass = False
    n1_ratio = float('nan')
else:
    n1_ratio = abs(speed_nr / round2_speed) if abs(round2_speed) > 0.01 else 1.0
    n1_pass = bool(0.75 <= n1_ratio <= 1.30)
print(f"    No-reinit speed: {speed_nr:.4f}, Round 2: {round2_speed:.4f}, "
      f"ratio: {n1_ratio:.3f}  {'PASS' if n1_pass else 'WARN'}")

# N2: pure ether with no-reinit + DCG at primary prescription, ε=0.10
# Should not create spontaneous structure (τ_c std should remain low)
print("  N2: Pure ether vacuum under no-reinit (τ_c should be homogeneous)...", flush=True)
L_null = L_CHAR
outer_null = make_ether_tape(L_null)
inner_null = init_inner_consistent(outer_null)
vac_tc_stds = []
for t in range(T_BURN + 30):
    tc_n = compute_tau_c_stability(inner_null)
    if t >= T_BURN:
        vac_tc_stds.append(float(tc_n.std()))
    outer_null_new = outer_step_standard(outer_null)
    inner_null = advance_inner_noreinit(inner_null, outer_null_new)
    outer_null = outer_null_new
vac_std = float(np.mean(vac_tc_stds))
ether_std_ref = tc_char["ether"]["std"]
n2_pass = bool(vac_std <= 2.0 * ether_std_ref + 1.0)
print(f"    Vacuum τ_c std: {vac_std:.4f} (ether ref std={ether_std_ref:.2f}) "
      f"{'PASS' if n2_pass else 'WARN (structure may be spontaneously generated)'}")

# N3: wrong-target null — if ratio > 1.2, does applying DCG to inverted cells (activity)
#     give WORSE or no attraction? (Tests that coupling direction matters.)
n3_result = "N/A"
if proceed_step2 and two_glider_result != "SKIPPED":
    other_presc = 'activity' if primary_prescription == 'stability' else 'stability'
    eps_null = eps_test
    print(f"  N3: Wrong-prescription null (ε={eps_null:.3f}, {other_presc}) ...", flush=True)
    dist_null, _ = test_two_glider_noreinit(L, eps_null, other_presc)
    _, _, null_slope = distance_stats(dist_null)
    # If wrong prescription gives STRONGER attraction than correct one, that's suspicious
    if null_slope is not None:
        sep_null = null_slope - (distance_stats(dist_base)[2] if 'dist_base' in dir() else 0.0)
        n3_pass = sep_null > sep_delta  # wrong prescription should do worse (less negative slope)
        n3_result = f"slope_delta={sep_null:+.4f} vs correct={sep_delta:+.4f}  {'PASS' if n3_pass else 'WARN'}"
        print(f"    {n3_result}")
    else:
        n3_result = "INSUFFICIENT_DATA"
        n3_pass = True
else:
    n3_pass = True

results["null_tests"] = {
    "N1_speed_ratio":      round(n1_ratio, 4) if not np.isnan(n1_ratio) else -99.0,
    "N1_pass":             n1_pass,
    "N2_vacuum_tau_c_std": round(vac_std, 4),
    "N2_pass":             n2_pass,
    "N3_wrong_presc":      n3_result,
    "N3_pass":             n3_pass,
}
all_nulls_pass = n1_pass and n2_pass and n3_pass

# ── Conclusion ────────────────────────────────────────────────────────────────
print("\n=== Conclusion ===")

if two_glider_result == "CONFIRMED" and all_nulls_pass:
    conclusion = "CONFIRMED"
elif two_glider_result == "WEAK" and all_nulls_pass:
    conclusion = "WEAK"
elif ratio_verdict == "RATIO_FLAT" or tc_char["glider_cells"]["n"] < 10:
    conclusion = "NEGATIVE"
    next_round = (
        "No τ_c discrimination between glider and ether cells under no-reinit "
        "with center-column injection (M=7). Root cause: Rule 110 on M=7 cells "
        "with periodic injection converges to the same attractor regardless of "
        "initial seed — the injection sequence differences between glider and ether "
        "cells are too weak to distinguish. All three prescriptions (fresh-reinit R1/R2, "
        "no-reinit R3) are definitively NEGATIVE for the coupling-constant framework. "
        "64-DCG CLOSED CatD (final). Ollivier-Ricci curvature prescription (Round 4) "
        "requires different architecture (optimal transport per step) — multi-week effort, "
        "not a quick experiment. Flag for EPIC_073."
    )
elif two_glider_result == "NEGATIVE" or two_glider_result == "INCONCLUSIVE":
    conclusion = "NEGATIVE"
    next_round = (
        "No-reinit prescription: glider/ether τ_c ratio = "
        f"{ratio:.3f} ({ratio_verdict}) but two-glider test shows no attraction "
        f"({two_glider_result}). Three rounds of AFCA experiments (fresh-reinit M=7, "
        "fresh-reinit M=49, no-reinit M=7) all NEGATIVE for coupling-constant prescription. "
        "64-DCG CLOSED CatD (final). Ollivier-Ricci prescription remains as possible "
        "Round 4 — requires different computational architecture."
    )
elif two_glider_result == "SKIPPED":
    conclusion = "NEGATIVE"
    next_round = (
        "τ_c ratio inadequate or glider unstable under no-reinit. "
        "64-DCG CLOSED CatD (final) — three prescription variants all fail."
    )
else:
    conclusion = "INCONCLUSIVE"
    next_round = "Diagnostic pass needed — check single-glider stability and ratio consistency."

if conclusion == "CONFIRMED":
    next_round = "Graduate script; full paper pass on P36; update all docs."
elif conclusion == "WEAK":
    next_round = (
        f"WEAK signal (sep_delta < -0.5 but > -2.0). "
        "Parameters needed for decisive test: larger L (≥ 400), larger T (≥ 200), "
        "multiple glider pairs averaged. Do not graduate yet."
    )

print(f"  τ_c ratio: {ratio:.4f} ({ratio_verdict})")
print(f"  τ_c glider cells measured: {tc_char['glider_cells']['n']}")
print(f"  Two-glider result: {two_glider_result}")
print(f"  Null tests: all_pass={all_nulls_pass}")
print(f"  Conclusion: {conclusion}")
print(f"  Next round: {next_round[:100]}...")

results["tau_c_ratio_glider_ether"] = round(ratio, 6)
results["conclusion"]   = conclusion
results["next_round"]   = next_round
results["all_nulls_pass"] = all_nulls_pass
results["elapsed_s"]    = round(time.time() - t_start, 1)

# ── Save results ──────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SCRIPT_DIR.parent / "data"
out_path = _DATA_DIR / "rank64_dcg_round3_noreinit_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved → {out_path}")
signal.alarm(0)
print(f"Done. Elapsed: {results['elapsed_s']:.1f}s")
