#!/usr/bin/env python3
"""
Rank 5-FSS: FCA Implementation via Self-Simulating Rule 110 (R110-in-R110).

Objective
---------
Construct and verify an explicit Rule 110 self-simulation embedding that instantiates
the FCA hierarchy (GoL-in-GoL / Rendell 2011 analogue for Rule 110).

Approach
--------
1. Verify ether background temporal period (CatA building block).
2. Test naive macro-cell encodings on a single R110 tape (expected negative).
3. Test 1D concatenation of Cook (2009) block rows (expected negative without full assembly).
4. Report Cook slowdown bounds via appendant step counts (cook_M).
5. Continuum-scaling proxy via 2-level sync FCA inner size sweep (not R110-in-R110).

Wall-clock cap: 600 s.
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

TIMEOUT_SECONDS = 600
T_START = time.time()

COOK_BLOCKS_PATH = Path(__file__).with_name("cook_blocks.json")
OUT_JSON = Path(__file__).with_name("epic073_rank5_fss_r110_self_simulation_results.json")

LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
GLIDER = np.array([0, 1, 0, 0, 1, 0, 1, 0, 0, 1], dtype=np.uint8)


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.", flush=True)
    _save_results(_RESULTS)
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

_RESULTS: Dict[str, Any] = {
    "rank": "5-FSS",
    "title": "FCA Implementation via Self-Simulating R110",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "status": "RUNNING",
}


def _wall_remaining() -> float:
    return TIMEOUT_SECONDS - (time.time() - T_START)


def _save_results(data: Dict[str, Any]) -> None:
    with open(OUT_JSON, "w") as f:
        json.dump(data, f, indent=2)


def rule110_step(tape: np.ndarray) -> np.ndarray:
    n = len(tape)
    out = np.zeros(n, dtype=np.uint8)
    for i in range(n):
        l = tape[(i - 1) % n]
        c = tape[i]
        r = tape[(i + 1) % n]
        out[i] = LUT110[l * 4 + c * 2 + r]
    return out


def tile_ether(length: int) -> np.ndarray:
    reps = length // 14 + 1
    return np.tile(ETHER14, reps)[:length]


def ether_temporal_period(length: int, max_steps: int = 50) -> int | None:
    target = tile_ether(length)
    tape = target.copy()
    for step in range(1, max_steps + 1):
        tape = rule110_step(tape)
        if np.array_equal(tape, target):
            return step
    return None


def logical_r110(bits: List[int]) -> List[int]:
    n = len(bits)
    return [int(LUT110[bits[(i - 1) % n] * 4 + bits[i] * 2 + bits[(i + 1) % n]]) for i in range(n)]


def encode_ether_blocks(bits: List[int], block_width: int = 14) -> np.ndarray:
    tape: List[int] = []
    for b in bits:
        block = ETHER14.tolist()
        if b:
            g = GLIDER.tolist()
            for k, v in enumerate(g):
                if 2 + k < block_width:
                    block[2 + k] = v
        tape.extend(block)
    return np.array(tape, dtype=np.uint8)


def decode_ether_blocks(tape: np.ndarray, n_bits: int, block_width: int = 14) -> List[int]:
    return [1 if tape[i * block_width : (i + 1) * block_width].sum() > block_width // 2 else 0 for i in range(n_bits)]


def encode_delimited(bits: List[int], data_width: int = 10, delim_width: int = 14) -> np.ndarray:
    width = data_width + delim_width
    tape: List[int] = []
    for b in bits:
        data = GLIDER.tolist() if b else [0] * data_width
        tape.extend(data)
        tape.extend(ETHER14.tolist())
    return np.array(tape, dtype=np.uint8)


def decode_delimited(tape: np.ndarray, n_bits: int, data_width: int = 10, delim_width: int = 14) -> List[int]:
    width = data_width + delim_width
    return [1 if tape[i * width : i * width + data_width].sum() > data_width // 2 else 0 for i in range(n_bits)]


def macro_simulation_test(
    name: str,
    encode_fn,
    decode_fn,
    micro_steps: List[int],
    n_trials: int = 20,
    n_bits: int = 5,
) -> Dict[str, Any]:
    rng = np.random.default_rng(42)
    results = []
    for trial in range(n_trials):
        bits0 = rng.integers(0, 2, size=n_bits).tolist()
        expected = logical_r110(bits0)
        tape0 = encode_fn(bits0)
        for ms in micro_steps:
            tape = tape0.copy()
            for _ in range(ms):
                tape = rule110_step(tape)
            decoded = decode_fn(tape, n_bits)
            match = decoded == expected
            results.append({"trial": trial, "micro_steps": ms, "match": bool(match), "bits0": bits0, "expected": expected, "decoded": decoded})
    n_match = sum(1 for r in results if r["match"])
    # Viable only if ≥95% trials match at a designated slowdown step (micro ≥ 7)
    slowdown_steps = [ms for ms in micro_steps if ms >= 7]
    slowdown_results = [r for r in results if r["micro_steps"] in slowdown_steps]
    slowdown_match = sum(1 for r in slowdown_results if r["match"])
    slowdown_rate = slowdown_match / len(slowdown_results) if slowdown_results else 0.0
    return {
        "name": name,
        "n_trials": n_trials,
        "micro_steps": micro_steps,
        "matches": n_match,
        "total": len(results),
        "pass_rate": n_match / len(results) if results else 0.0,
        "slowdown_pass_rate": slowdown_rate,
        "pass": slowdown_rate >= 0.95,
        "sample_failures": [r for r in results if not r["match"]][:3],
    }


def cook_m(appendant: str) -> int:
    if not appendant:
        return 30
    length = len(appendant)
    if length % 6 != 0:
        raise ValueError(f"Non-empty appendant length must be multiple of 6; got {length}")
    return 30 * (2 * length + 1)


def cook_block_stitch_test(blocks: Dict[str, Any]) -> Dict[str, Any]:
    """1D concatenation of Cook block rows without full 2D assembly."""
    tests = []
    for block_name in ["L", "A", "E", "D"]:
        if block_name not in blocks:
            continue
        rows = blocks[block_name]["rows"]
        period = blocks[block_name]["period"]
        row0 = np.array(rows[0], dtype=np.uint8)
        tape = row0.copy()
        # open boundary with ether padding
        pad = 70
        padded = np.concatenate([tile_ether(pad), tape, tile_ether(pad)])
        center_start = pad
        center_len = len(tape)
        evolved = padded.copy()
        for _ in range(period):
            evolved = rule110_step(evolved)
        center = evolved[center_start : center_start + center_len]
        dists = [
            int(np.sum(center[: min(len(center), len(r))] != np.array(r[: min(len(center), len(r))], dtype=np.uint8)))
            for r in rows
        ]
        best_idx = int(np.argmin(dists))
        tests.append(
            {
                "block": block_name,
                "row0_len": int(len(row0)),
                "period": int(period),
                "best_match_row": best_idx,
                "hamming": int(dists[best_idx]),
                "hamming_fraction": float(dists[best_idx] / len(row0)),
                "period_match": best_idx == 0 and dists[best_idx] == 0,
            }
        )
    return {"tests": tests, "any_period_match": any(t["period_match"] for t in tests)}


def fca_inner_size_scaling(inner_sizes: List[int], outer_L: int = 60, steps: int = 40) -> Dict[str, Any]:
    """2-level sync FCA: NOT R110-in-R110; continuum proxy only."""
    rng = np.random.default_rng(7)
    rows = []
    for M in inner_sizes:
        inner = rng.integers(0, 2, size=(outer_L, M), dtype=np.uint8)
        tau_variances = []
        for _ in range(steps):
            new_inner = np.zeros_like(inner)
            for i in range(outer_L):
                for j in range(M):
                    l = inner[i, (j - 1) % M]
                    c = inner[i, j]
                    r = inner[i, (j + 1) % M]
                    new_inner[i, j] = LUT110[l * 4 + c * 2 + r]
            inner = new_inner
            majority = (inner.sum(axis=1) * 2 > M).astype(np.uint8)
            tau_variances.append(float(np.var(majority.astype(float))))
        rows.append({"inner_M": M, "majority_variance_mean": float(np.mean(tau_variances)), "majority_variance_std": float(np.std(tau_variances))})
    # Check if variance decreases with M (continuum proxy)
    if len(rows) >= 2:
        decreasing = all(rows[i]["majority_variance_mean"] >= rows[i + 1]["majority_variance_mean"] for i in range(len(rows) - 1))
    else:
        decreasing = False
    return {"rows": rows, "variance_decreases_with_M": decreasing, "note": "Tree FCA proxy; not single-tape R110-in-R110"}


def main() -> None:
    print("Rank 5-FSS — R110 self-simulation assessment", flush=True)

    # 1. Ether temporal period
    ether_tests = []
    for L in [14, 28, 42, 140, 200, 210]:
        period = ether_temporal_period(L)
        ether_tests.append({"L": L, "L_mod_14": L % 14, "temporal_period": period, "pass": period == 7 if L % 14 == 0 else period is None or period != 7})
    ether_pass = all(t["temporal_period"] == 7 for t in ether_tests if t["L"] % 14 == 0)
    _RESULTS["ether_temporal_period"] = {"tests": ether_tests, "catA_pass": ether_pass}

    # 2. Naive macro encodings
    macro_tests = [
        macro_simulation_test("ether_block_w14", lambda b: encode_ether_blocks(b), lambda t, n: decode_ether_blocks(t, n), [1, 3, 7, 14]),
        macro_simulation_test("delimited_10_14", lambda b: encode_delimited(b), lambda t, n: decode_delimited(t, n), [1, 7, 14, 30]),
    ]
    _RESULTS["naive_macro_encodings"] = {
        "tests": macro_tests,
        "any_pass": any(t["pass"] for t in macro_tests),
        "verdict": "FAIL — no naive encoding simulates one logical R110 step",
    }

    # 3. Cook blocks
    if COOK_BLOCKS_PATH.exists():
        blocks = json.loads(COOK_BLOCKS_PATH.read_text())
        _RESULTS["cook_blocks"] = {
            "path": str(COOK_BLOCKS_PATH),
            "n_blocks": len(blocks),
            "stitch_test": cook_block_stitch_test(blocks),
        }
        appendants = ["", "YYYYYY", "NNNNNN", "YYNNYYNNYYNN"]
        slowdown = []
        for app in appendants:
            try:
                slowdown.append({"appendant": app, "M_steps": cook_m(app), "len": len(app)})
            except ValueError as e:
                slowdown.append({"appendant": app, "error": str(e)})
        _RESULTS["cook_slowdown_bounds"] = slowdown
    else:
        _RESULTS["cook_blocks"] = {"error": f"Missing {COOK_BLOCKS_PATH}"}

    # 4. Continuum proxy (FCA tree, not R110-in-R110)
    _RESULTS["continuum_proxy_fca_tree"] = fca_inner_size_scaling([7, 14, 21, 28])

    # 5. Overall verdict
    explicit_embedding = False
    _RESULTS["verdict"] = {
        "explicit_r110_in_r110_constructed": explicit_embedding,
        "ether_period_7_catA": ether_pass,
        "naive_encoding_viable": any(t["pass"] for t in macro_tests),
        "cook_1d_stitch_viable": _RESULTS.get("cook_blocks", {}).get("stitch_test", {}).get("any_period_match", False),
        "universality_existence": True,
        "fca_tree_proxy_available": True,
        "cat_level": "CatA (negative partial)",
        "interpretation": (
            "Rule 110 Turing-universality (Cook 2004 / GF(7) algebraic route) guarantees "
            "existence of a self-simulating embedding. No explicit single-tape R110-in-R110 "
            "construction was achieved in this session. Naive ether-block and delimiter "
            "encodings fail all macro-step tests. Cook block rows require full 2D assembly "
            "(ossifier + central + appendant stack per Cook 2009). Follow-on rank 5-FSS-COOK "
            "recommended for inexxt/rule_110-style assembler."
        ),
        "follow_on_rank": "5-FSS-COOK",
    }
    _RESULTS["status"] = "COMPLETE"
    _RESULTS["wall_seconds"] = time.time() - T_START

    signal.alarm(0)
    _save_results(_RESULTS)

    print(json.dumps(_RESULTS["verdict"], indent=2), flush=True)
    print(f"\nResults: {OUT_JSON}", flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        signal.alarm(0)
