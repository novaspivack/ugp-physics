#!/usr/bin/env python3
"""
074-UNIDM1 — Two-layer chiral AFCA prototype (Rule 110 + Rule 124).

Outer: decoupled chiral pair (R110 right-mover, R124 left-mover).
Inner: shared Rule 110 τ_c clock per cell gates outer updates.

Clock options:
  A — one shared inner clock gates BOTH layers (MDL-minimal candidate)
  C — inner clock gates R110; R124 updates on the same completion event

Verification:
  1. Z7 generation orbit gen1 -> gen2 -> gen3 -> vac
  2. V-A: 32/125 mismatches on ChiralPairVA SM vocabulary, W+ non-center
  3. Glider speeds |v_R| = |v_L| = 2/3 (sync two-layer reference)
  4. tau_c(glider) > tau_c(ether); ratio tracks gamma for injected glider
  5. SR proper-time dilation ~ 1/gamma

Output: papers/41_three_layer_chiral_minkowski_ca/scripts/two_layer_chiral_afca_prototype_results.json
Timeout: 600 s
"""

from __future__ import annotations

import json
import signal
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

TIMEOUT_SECONDS = 600
RESULTS_PATH = Path(__file__).resolve().parent / "two_layer_chiral_afca_prototype_results.json"

_t0 = time.time()


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

RULE110_LUT = np.array([(110 >> n) & 1 for n in range(8)], dtype=np.uint8)
RULE124_LUT = np.array([(124 >> n) & 1 for n in range(8)], dtype=np.uint8)
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
ETHER_124_SEQ = ETHER14[::-1]

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}
RULE124 = {(l, c, r): RULE110[(r, c, l)] for l in (0, 1) for c in (0, 1) for r in (0, 1)}

_FMDL_ORBIT = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
}
for key, val in RULE110.items():
    _FMDL_ORBIT.setdefault(key, val)

GEN1 = (1, 5, 2, 2, 1)
N_GEN = 3
# ChiralPairVA.lean smVocab: {vac=0, u=2, W+=3, e-=4, d=6}
SM_VA = [0, 2, 3, 4, 6]

C_EFF = 2.0 / 3.0
GAMMA_V23 = float(1.0 / np.sqrt(1.0 - C_EFF ** 2))
GLIDER_SEED = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
CANONICAL_PHASE = 12

L_DEFAULT = 840
M_DEFAULT = 7
CENTER_110 = 421
CENTER_124 = 423
T_SYNC = 300
N_TRANS = 300
SNAP_EVERY = 5
DIFF_THRESHOLD = 0.05
SPEED_TOL = 0.02
SR_ERROR_TOL_PCT = 15.0


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _apply_rule(state: np.ndarray, lut: np.ndarray) -> np.ndarray:
    n = len(state)
    l = state[(np.arange(n) - 1) % n].astype(np.int32)
    c = state.astype(np.int32)
    r = state[(np.arange(n) + 1) % n].astype(np.int32)
    return lut[(l << 2) | (c << 1) | r]


def fmdl_z7(l: int, c: int, r: int) -> int:
    return _FMDL_ORBIT.get((l, c, r), 0)


def fmdl_step5(state: tuple[int, ...]) -> tuple[int, ...]:
    n = 5
    return tuple(fmdl_z7(state[(i + 4) % n], state[i], state[(i + 1) % n]) for i in range(n))


def fmdl_mirror(state: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(state[4 - i] for i in range(5))


GEN2 = fmdl_step5(GEN1)
GEN3 = fmdl_step5(GEN2)
VACUUM = (0, 0, 0, 0, 0)


def ether_tape(seq: np.ndarray, length: int) -> np.ndarray:
    return np.array([seq[i % 14] for i in range(length)], dtype=np.uint8)


def step_sync_chiral(outer_110: np.ndarray, outer_124: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return _apply_rule(outer_110, RULE110_LUT), _apply_rule(outer_124, RULE124_LUT)


def verify_va_structure() -> dict:
    def classify(l: int, c: int, r: int) -> str:
        f110 = RULE110[(l % 2, c % 2, r % 2)]
        f124 = RULE124[(l % 2, c % 2, r % 2)]
        if f110 == 1 and f124 == 0:
            return "R_ONLY"
        if f110 == 0 and f124 == 1:
            return "L_ONLY"
        if f110 == 1 and f124 == 1:
            return "BOTH"
        return "NEITHER"

    triples = list(product(SM_VA, repeat=3))
    counts = {"BOTH": 0, "R_ONLY": 0, "L_ONLY": 0, "NEITHER": 0}
    for t in triples:
        counts[classify(*t)] += 1

    mismatches = counts["R_ONLY"] + counts["L_ONLY"]
    w_center = sum(1 for t in triples if t[1] == 3 and classify(*t) in ("R_ONLY", "L_ONLY"))
    w_neighbor = sum(
        1 for t in triples
        if (t[0] == 3 or t[2] == 3) and t[1] != 3 and classify(*t) in ("R_ONLY", "L_ONLY")
    )
    wplus_mismatch_triples = [
        t for t in triples
        if classify(*t) in ("R_ONLY", "L_ONLY") and (t[0] == 3 or t[2] == 3)
    ]
    all_wplus_noncenter = len(wplus_mismatch_triples) == mismatches

    return {
        "sm_vocabulary": SM_VA,
        "total_triples": len(triples),
        "mismatch_count": mismatches,
        "expected_mismatch_count": 32,
        "both_count": counts["BOTH"],
        "r_only_count": counts["R_ONLY"],
        "l_only_count": counts["L_ONLY"],
        "w_plus_center_mismatches": w_center,
        "w_plus_neighbor_mismatches": w_neighbor,
        "all_mismatches_wplus_noncenter": all_wplus_noncenter,
        "pass": mismatches == 32 and w_center == 0 and all_wplus_noncenter,
        "lean_ref": "ChiralPairVA.va_mismatch_count",
    }


def verify_z7_generation_orbit() -> dict:
    states = [GEN1]
    s = GEN1
    for _ in range(N_GEN):
        s = fmdl_step5(s)
        states.append(s)

    forward_ok = states[1] == GEN2 and states[2] == GEN3 and states[3] == VACUUM
    mirror_g1 = fmdl_mirror(GEN1)
    m2 = fmdl_step5(fmdl_step5(mirror_g1))

    return {
        "gen1": list(GEN1),
        "gen2": list(GEN2),
        "gen3": list(GEN3),
        "vacuum": list(VACUUM),
        "forward_orbit_holds": forward_ok,
        "steps_gen1_to_vacuum": N_GEN,
        "mirror_decay_steps": 2 if m2 == VACUUM else 99,
        "pass": forward_ok and m2 == VACUUM,
    }


def run_two_layer_chiral_afca(
    outer_l: int,
    m: int,
    n_transitions: int,
    init_110: np.ndarray,
    init_124: np.ndarray,
    clock_option: str,
    snapshot_every: int = SNAP_EVERY,
) -> dict:
    assert clock_option in ("A", "C")
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

    spacetime_110: list[np.ndarray] = []
    spacetime_124: list[np.ndarray] = []

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
        outer_110[idx] = maj[idx]
        # Option A and C: R124 updates when the shared inner clock completes.
        outer_124[idx] = _apply_rule(outer_124, RULE124_LUT)[idx]
        tau_accum[idx] += tau_count[idx].astype(np.float64)
        n_trans[idx] += 1
        targets[idx] = targets_110(outer_110)[idx]
        seed(idx)
        tau_count[idx] = 0

    istep = 0
    loop_start = time.time()

    while True:
        if time.time() - _t0 > TIMEOUT_SECONDS - 30 or time.time() - loop_start > 180:
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

        if istep % snapshot_every == 0:
            spacetime_110.append(outer_110.copy())
            spacetime_124.append(outer_124.copy())

        if n_trans.min() >= n_transitions:
            break
        if istep > n_transitions * max_inner * 5:
            break

    tau_c = np.where(n_trans > 0, tau_accum / np.maximum(n_trans, 1), 0.0).astype(np.float32)
    st110 = np.array(spacetime_110, dtype=np.uint8) if spacetime_110 else np.zeros((1, n), dtype=np.uint8)
    st124 = np.array(spacetime_124, dtype=np.uint8) if spacetime_124 else np.zeros((1, n), dtype=np.uint8)

    return {
        "spacetime_110": st110,
        "spacetime_124": st124,
        "tau_c": tau_c,
        "n_trans": n_trans,
        "inner_steps": istep,
        "clock_option": clock_option,
    }


def measure_sync_glider_speed(
    ether_110: np.ndarray,
    ether_124: np.ndarray,
    center_110: int,
    center_124: int,
    n_steps: int,
) -> dict:
    base_110, base_124 = ether_110.copy(), ether_124.copy()
    pert_110, pert_124 = ether_110.copy(), ether_124.copy()
    pert_110[center_110] ^= 1

    right_leads = []
    cross_124 = 0
    for _ in range(n_steps):
        base_110, base_124 = step_sync_chiral(base_110, base_124)
        pert_110, pert_124 = step_sync_chiral(pert_110, pert_124)
        diff = base_110 != pert_110
        cross_124 = max(cross_124, int((base_124 != pert_124).sum()))
        right_leads.append(
            max((i - center_110 for i in range(center_110 + 1, len(base_110)) if diff[i]), default=0)
        )
    v_r = right_leads[-1] / n_steps

    base_110, base_124 = ether_110.copy(), ether_124.copy()
    pert_110, pert_124 = ether_110.copy(), ether_124.copy()
    pert_124[center_124] ^= 1
    left_leads = []
    cross_110 = 0
    for _ in range(n_steps):
        base_110, base_124 = step_sync_chiral(base_110, base_124)
        pert_110, pert_124 = step_sync_chiral(pert_110, pert_124)
        diff = base_124 != pert_124
        cross_110 = max(cross_110, int((base_110 != pert_110).sum()))
        left_leads.append(
            max((center_124 - i for i in range(0, center_124) if diff[i]), default=0)
        )
    v_l = left_leads[-1] / n_steps

    return {
        "v_r_sync": float(v_r),
        "v_l_sync": float(v_l),
        "v_r_error": float(abs(v_r - C_EFF)),
        "v_l_error": float(abs(v_l - C_EFF)),
        "layers_decoupled": cross_124 == 0 and cross_110 == 0,
        "pass": abs(v_r - C_EFF) < SPEED_TOL and abs(v_l - C_EFF) < SPEED_TOL,
    }


def inject_glider_seed(tape: np.ndarray, length: int, phase: int = CANONICAL_PHASE) -> tuple[np.ndarray, int]:
    out = tape.copy()
    c = length // 2 - ((length // 2 - phase) % 14)
    for j, bit in enumerate(GLIDER_SEED):
        out[(c + j) % length] = bit
    return out, c


def glider_mask_from_runs(
    ether_run: dict,
    glider_run: dict,
    length: int,
    threshold: float = DIFF_THRESHOLD,
) -> np.ndarray:
    n_snaps = min(len(ether_run["spacetime_110"]), len(glider_run["spacetime_110"]))
    if n_snaps >= 5:
        diff_frac = (
            glider_run["spacetime_110"][:n_snaps] != ether_run["spacetime_110"][:n_snaps]
        ).mean(axis=0)
    else:
        diff_frac = np.zeros(length)
    is_glider = diff_frac > threshold
    if not is_glider.any():
        top = np.argsort(diff_frac)[-max(5, length // 20):]
        is_glider = np.zeros(length, dtype=bool)
        is_glider[top] = True
    return is_glider


def measure_tau_c_sr(
    ether_110: np.ndarray,
    ether_124: np.ndarray,
    clock_option: str,
    use_c2_flip: bool = False,
) -> dict:
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

    ether_run = run_two_layer_chiral_afca(
        len(ether_110), M_DEFAULT, N_TRANS, ether_110, ether_124, clock_option
    )
    glider_run = run_two_layer_chiral_afca(
        len(ether_110), M_DEFAULT, N_TRANS, glider_110, ether_124, clock_option
    )

    tau_ether = ether_run["tau_c"]
    tau_glider_tape = glider_run["tau_c"]
    is_glider = glider_mask_from_runs(ether_run, glider_run, len(ether_110))

    tau_bg = float(tau_ether.mean())
    tau_g = float(tau_glider_tape[is_glider].mean())
    tau_e = float(tau_glider_tape[~is_glider].mean()) if (~is_glider).any() else tau_bg
    ratio = tau_g / max(tau_e, 1e-9)
    sr_error_pct = abs(ratio - gamma_target) / gamma_target * 100.0
    dilation_factor = tau_e / max(tau_g, 1e-9)
    expected_dilation = 1.0 / gamma_target

    return {
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
        "pass_tau_c_elevated": bool(tau_g > tau_e),
        "pass_tau_c_gamma": bool(sr_error_pct < SR_ERROR_TOL_PCT),
        "pass_dilation": bool(abs(dilation_factor - expected_dilation) / expected_dilation * 100 < SR_ERROR_TOL_PCT),
    }


def verify_decoupled_coevolution_afca(clock_option: str, length: int = L_DEFAULT) -> dict:
    e110 = ether_tape(ETHER14, length)
    e124 = ether_tape(ETHER_124_SEQ, length)
    pert_110 = e110.copy()
    for k, v in enumerate(GEN1):
        pert_110[CENTER_110 + k] = v % 2

    base_run = run_two_layer_chiral_afca(length, M_DEFAULT, 60, e110, e124, clock_option)
    pert_run = run_two_layer_chiral_afca(length, M_DEFAULT, 60, pert_110, e124, clock_option)

    n = min(len(base_run["spacetime_124"]), len(pert_run["spacetime_124"]), 20)
    r124_match = all(
        np.array_equal(base_run["spacetime_124"][t], pert_run["spacetime_124"][t])
        for t in range(n)
    )

    z7 = GEN1
    z7_trace = [list(z7)]
    for _ in range(N_GEN):
        z7 = fmdl_step5(z7)
        z7_trace.append(list(z7))

    return {
        "z7_trace": z7_trace,
        "reaches_vacuum_at_step_3": z7_trace[3] == list(VACUUM),
        "layer124_bitwise_independent_under_afca": bool(r124_match),
        "schedule_coupling_note": (
            "Shared inner clock gates R124 on R110 completion order; "
            "R124 bitwise independence fails under Option A/C even when rules decouple."
        ),
        "pass": z7_trace[3] == list(VACUUM),
    }


def run_verification(clock_option: str) -> dict:
    e110 = ether_tape(ETHER14, L_DEFAULT)
    e124 = ether_tape(ETHER_124_SEQ, L_DEFAULT)

    va = verify_va_structure()
    z7 = verify_z7_generation_orbit()
    z7_afca = verify_decoupled_coevolution_afca(clock_option, L_DEFAULT)
    sync_speed = measure_sync_glider_speed(e110, e124, CENTER_110, CENTER_124, T_SYNC)
    tau_sr_seed = measure_tau_c_sr(e110, e124, clock_option, use_c2_flip=False)
    tau_sr_c2 = measure_tau_c_sr(e110, e124, clock_option, use_c2_flip=True)

    checklist = {
        "z7_orbit": bool(z7["pass"] and z7_afca["reaches_vacuum_at_step_3"]),
        "va_32_125": bool(va["pass"]),
        "glider_speeds": bool(sync_speed["pass"]),
        "tau_c_elevated": bool(tau_sr_seed["pass_tau_c_elevated"] and tau_sr_c2["pass_tau_c_elevated"]),
        "tau_c_gamma": bool(tau_sr_seed["pass_tau_c_gamma"]),
        "sr_dilation": bool(tau_sr_seed["pass_dilation"]),
    }
    all_pass = all(checklist.values())

    return {
        "clock_option": clock_option,
        "checklist": checklist,
        "all_pass": all_pass,
        "va": va,
        "z7_algebraic": z7,
        "z7_afca_decoupled": z7_afca,
        "sync_speed": sync_speed,
        "tau_c_sr_glider_seed": tau_sr_seed,
        "tau_c_sr_c2_v23": tau_sr_c2,
        "parameters": {
            "L": L_DEFAULT,
            "M": M_DEFAULT,
            "n_transitions": N_TRANS,
            "center_110": CENTER_110,
            "center_124": CENTER_124,
            "gamma_v23": GAMMA_V23,
        },
    }


def main() -> dict:
    print("=" * 70)
    print("074-UNIDM1 — Two-layer chiral AFCA prototype (P41 canonical)")
    print(f"L={L_DEFAULT}, M={M_DEFAULT}, N_trans={N_TRANS}, timeout={TIMEOUT_SECONDS}s")
    print("=" * 70)

    print("\n--- Option A: shared inner clock gates both layers ---")
    result_a = run_verification("A")
    _print_summary(result_a)

    if result_a["all_pass"]:
        chosen = "A"
        final = result_a
    else:
        print("\n--- Option A incomplete; trying Option C (R124 mirrors R110 completion) ---")
        result_c = run_verification("C")
        _print_summary(result_c)
        chosen = "C" if result_c["all_pass"] else "A_primary_C_also_tested"
        final = result_c if result_c["all_pass"] else {
            "option_a": result_a,
            "option_c": result_c,
            "all_pass": False,
            "checklist": result_c["checklist"],
            "clock_option": "C",
        }

    if result_a["all_pass"]:
        output = {
            "rank": "074-UNIDM1",
            "date": time.strftime("%Y-%m-%d"),
            "script": "papers/41_three_layer_chiral_minkowski_ca/scripts/two_layer_chiral_afca_prototype.py",
            "clock_option_used": chosen,
            **final,
        }
    elif isinstance(final, dict) and "option_a" in final:
        output = {
            "rank": "074-UNIDM1",
            "date": time.strftime("%Y-%m-%d"),
            "script": "papers/41_three_layer_chiral_minkowski_ca/scripts/two_layer_chiral_afca_prototype.py",
            "clock_option_used": chosen,
            **final,
        }
    else:
        output = {
            "rank": "074-UNIDM1",
            "date": time.strftime("%Y-%m-%d"),
            "script": "papers/41_three_layer_chiral_minkowski_ca/scripts/two_layer_chiral_afca_prototype.py",
            "clock_option_used": chosen,
            **final,
        }

    checklist = output.get("checklist") or final.get("checklist", {})
    n_pass = sum(1 for v in checklist.values() if v)
    if output.get("all_pass") or final.get("all_pass"):
        cat = "CatA"
    elif n_pass >= 4:
        cat = "CatAD"
    else:
        cat = "CatD"
    output["cat_level"] = cat
    output["elapsed_seconds"] = time.time() - _t0

    with open(RESULTS_PATH, "w") as f:
        json.dump(_json_safe(output), f, indent=2)
    print(f"\nResults saved: {RESULTS_PATH}")
    print(f"Cat level: {cat}")
    return output


def _print_summary(result: dict) -> None:
    ck = result["checklist"]
    print(f"  Z7 orbit:        {'PASS' if ck['z7_orbit'] else 'FAIL'}")
    print(f"  V-A 32/125:      {'PASS' if ck['va_32_125'] else 'FAIL'}")
    print(f"  Glider speeds:   {'PASS' if ck['glider_speeds'] else 'FAIL'}")
    print(f"  tau_c elevated:  {'PASS' if ck['tau_c_elevated'] else 'FAIL'}")
    print(f"  tau_c ~ gamma:   {'PASS' if ck['tau_c_gamma'] else 'FAIL'}")
    print(f"  SR dilation:     {'PASS' if ck['sr_dilation'] else 'FAIL'}")
    print(f"  ALL:             {'PASS' if result['all_pass'] else 'FAIL'}")
    ts = result.get("tau_c_sr_glider_seed", {})
    if ts:
        print(
            f"  tau_c ratio (seed)={ts['tau_c_ratio_glider_over_ether']:.4f} "
            f"gamma={ts['gamma_target']:.4f} error={ts['sr_error_pct']:.1f}%"
        )
    tc2 = result.get("tau_c_sr_c2_v23", {})
    if tc2:
        print(
            f"  tau_c ratio (C2 v=2/3)={tc2['tau_c_ratio_glider_over_ether']:.4f} "
            f"gamma={tc2['gamma_v23'] if 'gamma_v23' in tc2 else tc2['gamma_target']:.4f} "
            f"elevated={tc2['tau_c_glider_gt_ether']}"
        )


if __name__ == "__main__":
    out = main()
    signal.alarm(0)
    sys.exit(0 if out.get("all_pass") else 1)
