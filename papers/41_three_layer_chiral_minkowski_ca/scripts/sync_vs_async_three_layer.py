#!/usr/bin/env python3
"""
074-UNIDM1 follow-up — synchronous vs asynchronous three-layer chiral AFCA.

Compares:
  ASYNC (AFCA): inner τ_c clock GATES outer updates (completion event).
  SYNC:         outer layers update every step; inner clock counts in parallel.

Measurements (both modes):
  1. τ_c for ether vs glider cells (inner ticks per outer step)
  2. Glider speed over outer time steps (reference 2/3)
  3. Proper-time dilation ratio τ_glider / τ_ether

Expected:
  ASYNC — τ_glider > τ_ether, dilation tracks γ
  SYNC  — τ_glider ≈ τ_ether ≈ 1, no SR dilation

Output: papers/41_three_layer_chiral_minkowski_ca/scripts/sync_vs_async_three_layer_results.json
Timeout: 300 s
"""

from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

# Import shared infrastructure from the AFCA prototype.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from two_layer_chiral_afca_prototype import (  # noqa: E402
    C_EFF,
    CENTER_110,
    CENTER_124,
    DIFF_THRESHOLD,
    ETHER14,
    ETHER_124_SEQ,
    GAMMA_V23,
    L_DEFAULT,
    M_DEFAULT,
    N_TRANS,
    RULE110_LUT,
    RULE124_LUT,
    SNAP_EVERY,
    SR_ERROR_TOL_PCT,
    SPEED_TOL,
    T_SYNC,
    _apply_rule,
    _json_safe,
    ether_tape,
    glider_mask_from_runs,
    inject_glider_seed,
    measure_sync_glider_speed,
    run_two_layer_chiral_afca,
    step_sync_chiral,
)

TIMEOUT_SECONDS = 300
RESULTS_PATH = Path(__file__).with_name("sync_vs_async_three_layer_results.json")

_t0 = time.time()


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def run_async_outer_snapshots(
    outer_l: int,
    m: int,
    n_transitions: int,
    init_110: np.ndarray,
    init_124: np.ndarray,
) -> dict:
    """ASYNC AFCA with spacetime snapshots taken only on outer completion events."""
    max_inner = m * 10
    n = outer_l

    outer_110 = init_110.astype(np.uint8).copy()
    outer_124 = init_124.astype(np.uint8).copy()
    phases = np.array([(i * m) % 14 for i in range(n)], dtype=np.int32)
    inner = np.zeros((n, m), dtype=np.uint8)

    tau_count = np.zeros(n, dtype=np.int32)
    tau_accum = np.zeros(n, dtype=np.float64)
    n_trans = np.zeros(n, dtype=np.int32)
    needs_check = np.ones(n, dtype=bool)

    spacetime_110: list[np.ndarray] = [outer_110.copy()]
    spacetime_124: list[np.ndarray] = [outer_124.copy()]
    last_min_trans = 0

    def seed(idx: np.ndarray) -> None:
        for i in idx:
            p = int(phases[i])
            for j in range(m):
                inner[i, j] = ETHER14[(p + j) % 14]

    def majority() -> np.ndarray:
        return (inner.sum(axis=1) * 2 > m).astype(np.uint8)

    def targets_110(arr: np.ndarray) -> np.ndarray:
        return _apply_rule(arr, RULE110_LUT)

    def advance_inner(mask: np.ndarray) -> None:
        ni = np.empty_like(inner)
        for j in range(m):
            lj = inner[:, (j - 1) % m].astype(np.int32)
            cj = inner[:, j].astype(np.int32)
            rj = inner[:, (j + 1) % m].astype(np.int32)
            ni[:, j] = RULE110_LUT[(lj << 2) | (cj << 1) | rj]
        inner[mask] = ni[mask]

    targets = targets_110(outer_110)
    seed(np.arange(n))

    def complete(idx: np.ndarray, maj: np.ndarray) -> None:
        nonlocal last_min_trans
        outer_110[idx] = maj[idx]
        outer_124[idx] = _apply_rule(outer_124, RULE124_LUT)[idx]
        tau_accum[idx] += tau_count[idx].astype(np.float64)
        n_trans[idx] += 1
        targets[idx] = targets_110(outer_110)[idx]
        seed(idx)
        tau_count[idx] = 0
        cur_min = int(n_trans.min())
        if cur_min > last_min_trans:
            last_min_trans = cur_min
            spacetime_110.append(outer_110.copy())
            spacetime_124.append(outer_124.copy())

    istep = 0
    while True:
        if time.time() - _t0 > TIMEOUT_SECONDS - 20:
            break

        advance_skip = np.zeros(n, dtype=bool)
        if needs_check.any():
            maj = majority()
            instant = needs_check & (maj == targets)
            if instant.any():
                idx_a = np.where(instant)[0]
                complete(idx_a, maj)
                advance_skip[idx_a] = True
                needs_check[idx_a] = True
            needs_check[needs_check & ~instant] = False

        adv = ~advance_skip
        if adv.any():
            advance_inner(adv)
            tau_count[adv] += 1
        istep += 1

        maj = majority()
        done = adv & ((maj == targets) | (tau_count >= max_inner))
        if done.any():
            idx_c = np.where(done)[0]
            complete(idx_c, maj)
            needs_check[idx_c] = True

        if n_trans.min() >= n_transitions:
            break
        if istep > n_transitions * max_inner * 5:
            break

    tau_c = np.where(n_trans > 0, tau_accum / np.maximum(n_trans, 1), 0.0).astype(np.float32)
    st110 = np.array(spacetime_110, dtype=np.uint8)
    st124 = np.array(spacetime_124, dtype=np.uint8)

    return {
        "mode": "async",
        "spacetime_110": st110,
        "spacetime_124": st124,
        "tau_c": tau_c,
        "n_trans": n_trans,
        "inner_steps": istep,
        "outer_snapshots": len(spacetime_110),
    }


def run_sync_mode_chiral(
    outer_l: int,
    m: int,
    n_transitions: int,
    init_110: np.ndarray,
    init_124: np.ndarray,
    snapshot_every: int = SNAP_EVERY,
) -> dict:
    """
    SYNC three-layer mode: outer layers update every step.
    Inner Rule 110 advances in parallel; tau counter modulo m (no gating).
    """
    n = outer_l
    inner_period = m

    outer_110 = init_110.astype(np.uint8).copy()
    outer_124 = init_124.astype(np.uint8).copy()
    phases = np.array([(i * m) % 14 for i in range(n)], dtype=np.int32)
    inner = np.zeros((n, m), dtype=np.uint8)

    tau_accum = np.zeros(n, dtype=np.float64)
    n_trans = np.zeros(n, dtype=np.int32)
    tau_mod = np.zeros(n, dtype=np.int32)

    spacetime_110: list[np.ndarray] = []
    spacetime_124: list[np.ndarray] = []

    def seed(idx: np.ndarray) -> None:
        for i in idx:
            p = int(phases[i])
            for j in range(m):
                inner[i, j] = ETHER14[(p + j) % 14]

    def advance_inner_all() -> None:
        ni = np.empty_like(inner)
        for j in range(m):
            lj = inner[:, (j - 1) % m].astype(np.int32)
            cj = inner[:, j].astype(np.int32)
            rj = inner[:, (j + 1) % m].astype(np.int32)
            ni[:, j] = RULE110_LUT[(lj << 2) | (cj << 1) | rj]
        inner[:] = ni

    seed(np.arange(n))

    for ostep in range(n_transitions):
        if time.time() - _t0 > TIMEOUT_SECONDS - 20:
            break

        # Inner clock runs in parallel (one tick per outer step).
        advance_inner_all()
        tau_mod = (tau_mod + 1) % inner_period
        tau_accum += 1.0
        n_trans += 1

        # Outer layers always update — no gating.
        outer_110 = _apply_rule(outer_110, RULE110_LUT)
        outer_124 = _apply_rule(outer_124, RULE124_LUT)

        if ostep % snapshot_every == 0:
            spacetime_110.append(outer_110.copy())
            spacetime_124.append(outer_124.copy())

    tau_c = np.where(n_trans > 0, tau_accum / np.maximum(n_trans, 1), 0.0).astype(np.float32)
    st110 = np.array(spacetime_110, dtype=np.uint8) if spacetime_110 else np.zeros((1, n), dtype=np.uint8)
    st124 = np.array(spacetime_124, dtype=np.uint8) if spacetime_124 else np.zeros((1, n), dtype=np.uint8)

    return {
        "mode": "sync",
        "spacetime_110": st110,
        "spacetime_124": st124,
        "tau_c": tau_c,
        "n_trans": n_trans,
        "outer_steps": int(n_transitions),
        "inner_period": inner_period,
        "tau_mod_final_mean": float(tau_mod.mean()),
    }


def measure_afca_glider_speed(
    init_110: np.ndarray,
    init_124: np.ndarray,
    mode: str,
    center_110: int,
    center_124: int,
    n_outer: int,
) -> dict:
    """Measure right-mover speed over outer transitions in ASYNC or SYNC AFCA."""
    if mode == "async":
        run_fn = lambda i110, i124: run_async_outer_snapshots(
            len(i110), M_DEFAULT, n_outer, i110, i124
        )
    else:
        run_fn = lambda i110, i124: run_sync_mode_chiral(
            len(i110), M_DEFAULT, n_outer, i110, i124, snapshot_every=1
        )

    base = run_fn(init_110, init_124)
    pert_110, glider_center = inject_glider_seed(init_110, len(init_110))
    pert = run_fn(pert_110, init_124)

    st_b = base["spacetime_110"]
    st_p = pert["spacetime_110"]
    n_snaps = min(len(st_b), len(st_p))
    if n_snaps < 2:
        return {"v_r": 0.0, "pass": False, "n_snaps": n_snaps}

    right_leads = []
    for t in range(n_snaps):
        diff = st_b[t] != st_p[t]
        right_leads.append(
            max((i - glider_center for i in range(glider_center + 1, len(st_b[t])) if diff[i]), default=0)
        )
    v_r = right_leads[-1] / max(n_snaps - 1, 1)

    base2 = run_fn(init_110, init_124)
    pert_124 = init_124.copy()
    pert_124[center_124] ^= 1
    pert2 = run_fn(init_110, pert_124)

    st_b2 = base2["spacetime_124"]
    st_p2 = pert2["spacetime_124"]
    n_snaps2 = min(len(st_b2), len(st_p2))
    left_leads = []
    for t in range(n_snaps2):
        diff = st_b2[t] != st_p2[t]
        left_leads.append(
            max((center_124 - i for i in range(0, center_124) if diff[i]), default=0)
        )
    v_l = left_leads[-1] / max(n_snaps2 - 1, 1)

    return {
        "v_r": float(v_r),
        "v_l": float(v_l),
        "v_r_error": float(abs(v_r - C_EFF)),
        "v_l_error": float(abs(v_l - C_EFF)),
        "pass": bool(abs(v_r - C_EFF) < SPEED_TOL and abs(v_l - C_EFF) < SPEED_TOL),
        "n_snaps": n_snaps,
        "glider_center": int(glider_center),
    }


def measure_mode_tau_dilation(
    ether_110: np.ndarray,
    ether_124: np.ndarray,
    mode: str,
    use_c2_flip: bool = False,
) -> dict:
    """Measure τ_c ether vs glider and dilation ratio for one mode."""
    if use_c2_flip:
        glider_110 = ether_110.copy()
        glider_110[CENTER_110] ^= 1
        v_used = C_EFF
        gamma_target = GAMMA_V23
        seed_label = "C2_center_flip_v23"
    else:
        glider_110, _ = inject_glider_seed(ether_110, len(ether_110))
        v_used = 0.532
        gamma_target = float(1.0 / np.sqrt(1.0 - (v_used / C_EFF) ** 2))
        seed_label = "round19_glider_seed"

    if mode == "async":
        run_fn = lambda i110, i124: run_two_layer_chiral_afca(
            len(i110), M_DEFAULT, N_TRANS, i110, i124, "A"
        )
    else:
        run_fn = lambda i110, i124: run_sync_mode_chiral(
            len(i110), M_DEFAULT, N_TRANS, i110, i124
        )

    ether_run = run_fn(ether_110, ether_124)
    glider_run = run_fn(glider_110, ether_124)

    tau_ether = ether_run["tau_c"]
    tau_glider_tape = glider_run["tau_c"]
    is_glider = glider_mask_from_runs(ether_run, glider_run, len(ether_110), DIFF_THRESHOLD)

    tau_bg = float(tau_ether.mean())
    tau_g = float(tau_glider_tape[is_glider].mean()) if is_glider.any() else tau_bg
    tau_e = float(tau_glider_tape[~is_glider].mean()) if (~is_glider).any() else tau_bg
    ratio = tau_g / max(tau_e, 1e-9)
    sr_error_pct = abs(ratio - gamma_target) / gamma_target * 100.0
    dilation_factor = tau_e / max(tau_g, 1e-9)
    expected_dilation = 1.0 / gamma_target

    no_dilation = abs(ratio - 1.0) < 0.05
    has_dilation = ratio > 1.02 and tau_g > tau_e

    return {
        "mode": mode,
        "seed_label": seed_label,
        "velocity_used": float(v_used),
        "tau_c_ether_mean": tau_bg,
        "tau_c_glider_region_mean": tau_g,
        "tau_c_ether_nearby_mean": tau_e,
        "tau_c_ratio_glider_over_ether": float(ratio),
        "gamma_target": float(gamma_target),
        "sr_error_pct": float(sr_error_pct),
        "proper_time_dilation_measured": float(dilation_factor),
        "proper_time_dilation_expected": float(expected_dilation),
        "dilation_error_pct": float(abs(dilation_factor - expected_dilation) / expected_dilation * 100),
        "n_glider_cells": int(is_glider.sum()),
        "tau_c_glider_gt_ether": bool(tau_g > tau_e),
        "has_sr_dilation": bool(has_dilation),
        "no_dilation_sync_expected": bool(no_dilation) if mode == "sync" else None,
        "pass_tau_c_elevated": bool(tau_g > tau_e) if mode == "async" else bool(abs(tau_g - tau_e) < 0.05),
        "pass_tau_c_gamma": bool(sr_error_pct < SR_ERROR_TOL_PCT) if mode == "async" else bool(no_dilation),
    }


def run_comparison() -> dict:
    e110 = ether_tape(ETHER14, L_DEFAULT)
    e124 = ether_tape(ETHER_124_SEQ, L_DEFAULT)

    sync_ref = measure_sync_glider_speed(e110, e124, CENTER_110, CENTER_124, T_SYNC)

    async_tau = measure_mode_tau_dilation(e110, e124, "async", use_c2_flip=False)
    sync_tau = measure_mode_tau_dilation(e110, e124, "sync", use_c2_flip=False)
    async_tau_c2 = measure_mode_tau_dilation(e110, e124, "async", use_c2_flip=True)

    async_speed = measure_afca_glider_speed(e110, e124, "async", CENTER_110, CENTER_124, 120)
    sync_speed = measure_afca_glider_speed(e110, e124, "sync", CENTER_110, CENTER_124, 120)

    async_confirms_dilation = (
        async_tau["tau_c_glider_gt_ether"]
        and async_tau["tau_c_ratio_glider_over_ether"] > 1.02
        and async_tau["sr_error_pct"] < SR_ERROR_TOL_PCT
    )
    sync_no_dilation = abs(sync_tau["tau_c_ratio_glider_over_ether"] - 1.0) < 0.05
    asynchrony_mechanism = async_confirms_dilation and sync_no_dilation

    return {
        "rank": "074-UNIDM1-sync-vs-async",
        "date": time.strftime("%Y-%m-%d"),
        "script": "papers/41_three_layer_chiral_minkowski_ca/scripts/sync_vs_async_three_layer.py",
        "parameters": {
            "L": L_DEFAULT,
            "M": M_DEFAULT,
            "n_transitions": N_TRANS,
            "gamma_v23": GAMMA_V23,
            "c_eff": C_EFF,
        },
        "sync_two_layer_reference": sync_ref,
        "async_mode": {
            "tau_dilation_glider_seed": async_tau,
            "tau_dilation_c2_v23": async_tau_c2,
            "glider_speed": async_speed,
        },
        "sync_mode": {
            "tau_dilation": sync_tau,
            "glider_speed": sync_speed,
        },
        "conclusions": {
            "async_tau_ratio": async_tau["tau_c_ratio_glider_over_ether"],
            "async_sr_error_pct": async_tau["sr_error_pct"],
            "sync_tau_ratio": sync_tau["tau_c_ratio_glider_over_ether"],
            "async_has_dilation": async_confirms_dilation,
            "sync_no_dilation": sync_no_dilation,
            "asynchrony_causes_sr_dilation": asynchrony_mechanism,
        },
        "all_pass": bool(async_confirms_dilation and sync_no_dilation),
        "elapsed_seconds": time.time() - _t0,
    }


def main() -> dict:
    print("=" * 70)
    print("074-UNIDM1 — SYNC vs ASYNC three-layer chiral AFCA")
    print(f"L={L_DEFAULT}, M={M_DEFAULT}, N_trans={N_TRANS}, timeout={TIMEOUT_SECONDS}s")
    print("=" * 70)

    result = run_comparison()

    a = result["async_mode"]["tau_dilation_glider_seed"]
    ac2 = result["async_mode"]["tau_dilation_c2_v23"]
    s = result["sync_mode"]["tau_dilation"]
    asp = result["async_mode"]["glider_speed"]
    ssp = result["sync_mode"]["glider_speed"]

    print("\n--- ASYNC (AFCA: inner clock gates outer) ---")
    print(f"  [glider seed] τ_glider/τ_ether: {a['tau_c_ratio_glider_over_ether']:.4f}  (γ={a['gamma_target']:.4f})")
    print(f"  [glider seed] SR error:         {a['sr_error_pct']:.2f}%")
    print(f"  [C2 v=2/3]    τ_glider/τ_ether: {ac2['tau_c_ratio_glider_over_ether']:.4f}")
    print(f"  Glider speed v_R (outer steps):  {asp['v_r']:.4f}  (target {C_EFF})")

    print("\n--- SYNC (outer always updates; clock counts only) ---")
    print(f"  τ_c ether (bg):     {s['tau_c_ether_mean']:.4f}")
    print(f"  τ_c glider region:  {s['tau_c_glider_region_mean']:.4f}")
    print(f"  τ_glider/τ_ether:   {s['tau_c_ratio_glider_over_ether']:.4f}  (expect ~1.0)")
    print(f"  Glider speed v_R:   {ssp['v_r']:.4f}  (target {C_EFF})")

    c = result["conclusions"]
    print("\n--- Conclusion ---")
    print(f"  ASYNC dilation confirmed:  {c['async_has_dilation']}")
    print(f"  SYNC no dilation:          {c['sync_no_dilation']}")
    print(f"  Asynchrony → SR dilation:  {c['asynchrony_causes_sr_dilation']}")

    with open(RESULTS_PATH, "w") as f:
        json.dump(_json_safe(result), f, indent=2)
    print(f"\nResults saved: {RESULTS_PATH}")
    return result


if __name__ == "__main__":
    out = main()
    signal.alarm(0)
    sys.exit(0 if out.get("all_pass") else 1)
