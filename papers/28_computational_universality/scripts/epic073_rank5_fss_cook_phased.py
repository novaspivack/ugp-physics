#!/usr/bin/env python3
"""
Rank 5-FSS-COOK-PHASED: phased CTS + ossifier scaffold for R110-in-R110.

Constructs phase-aligned Rule 110 tapes via `gliders_to_tape_phased` /
`cts_word_to_placements_phased_with_support_idx` (mirroring
`rule110-lean/Rule110/CTStoRule110.lean`), simulates bounded list evolution,
and checks CTS readback after one Cook §1.4 cycle.

Cases
-----
1. Simple M=30: empty appendant, word [Y] → post-word [] (vacuous readback).
2. L=6 M=390: cook_min_len6_cts, word [Y] → post-word NNNNNN (Lean #14/#15 certs).

Wall-clock cap: 600 s.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TIMEOUT_SECONDS = 600
T_START = time.time()

REPO = Path(__file__).resolve().parents[1]
COOK_BLOCKS_PATH = Path(__file__).with_name("cook_blocks.json")
LEN6_INIT_JSON = REPO / "papers/30_cook_theorem/data/len6_true_phased_support_init.json"
OUT_JSON = Path(__file__).with_name("epic073_rank5_fss_cook_phased_results.json")

# Lean CTStoRule110 / CookC2BoundedSim constants
C2_SIM_BOUND = 2500
CTS_TAPE_ORIGIN = 1000
CTS_GLIDER_SPACING = 42
CTS_OSSIFIER_ORIGIN = 500
CTS_LEADER_ORIGIN = 8000
CONE_RADIUS = 30
NUM_DATA_CONE_CELLS = 61

COOK_ETHER_BITS = (
    True, False, False, True, True, False, True, True,
    True, True, True, False, False, False,
)

RULE110 = (
    False, True, True, True, False, True, True, False,
)

C2_GLIDER_CYCLE: Tuple[Tuple[bool, ...], ...] = (
    (True, True, False, False, False, True),    # phase 0, lp=2 mod 14
    (False, True, False, False, True, True),    # phase 1
    (True, True, False, True, True, False),     # phase 2
    (False, True, True, True, True, True),      # phase 3
    (True, True, False, False, False, False),  # phase 4
    (True, True, False, False, False, False),  # phase 5
    (False, True, False, False, False, False), # phase 6
)

C2_CYCLE_PHASE_MAP = {2: 0, 6: 1, 10: 2, 0: 3, 4: 4, 8: 5, 12: 6}

_RESULTS: Dict[str, Any] = {
    "rank": "5-FSS-COOK-PHASED",
    "title": "Phased CTS + ossifier scaffold for R110-in-R110",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "status": "RUNNING",
}


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.", flush=True)
    _save_results(_RESULTS)
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def _save_results(data: Dict[str, Any]) -> None:
    with open(OUT_JSON, "w") as f:
        json.dump(data, f, indent=2)


def cook_ether(i: int) -> bool:
    return COOK_ETHER_BITS[i % 14]


def phase_ether(i: int, accum: int) -> bool:
    return cook_ether(i + accum)


def c2_cycle_phase(origin_plus_accum: int) -> int:
    return C2_CYCLE_PHASE_MAP.get(origin_plus_accum % 14, 0)


def cts_slot_origin(slot: int) -> int:
    return CTS_TAPE_ORIGIN + slot * CTS_GLIDER_SPACING


def c2_sim_origin(slot: int) -> int:
    return cts_slot_origin(slot)


def cook_m_for_appendant_len(length: int) -> int:
    if length == 0:
        return 30
    if length % 6 != 0:
        raise ValueError(f"Nonempty appendant length must be multiple of 6; got {length}")
    return 30 * (2 * length + 1)


def cook_total_m_from(appendants: List[List[bool]], n: int, idx0: int = 0) -> int:
    if not appendants:
        return 0
    k = len(appendants)
    total = 0
    for step in range(n):
        app = appendants[(idx0 + step) % k]
        total += cook_m_for_appendant_len(len(app))
    return total


@dataclass(frozen=True)
class GliderPlacement:
    origin: int
    cook_width: int
    bits: Tuple[bool, ...]


def accum_phase_at(placements: List[GliderPlacement], i: int) -> int:
    total = 0
    for g in placements:
        if g.origin + len(g.bits) <= i:
            total += g.cook_width
    return total


def gliders_to_tape_phased(placements: List[GliderPlacement], i: int) -> bool:
    for g in placements:
        if g.origin <= i < g.origin + len(g.bits):
            return g.bits[i - g.origin]
    return phase_ether(i, accum_phase_at(placements, i))


def build_phased_tape(placements: List[GliderPlacement], bound: int = C2_SIM_BOUND) -> List[bool]:
    return [gliders_to_tape_phased(placements, i) for i in range(bound)]


def cts_word_to_placements_phased(word: List[bool]) -> List[GliderPlacement]:
    placements: List[GliderPlacement] = []
    for slot, bit in enumerate(word):
        if not bit:
            continue
        origin = CTS_TAPE_ORIGIN + slot * CTS_GLIDER_SPACING
        accum = 3 * len(placements)
        phase = c2_cycle_phase(origin + accum)
        placements.append(
            GliderPlacement(origin=origin, cook_width=3, bits=C2_GLIDER_CYCLE[phase])
        )
    return placements


def load_block_row0(blocks_data: Dict[str, Any], name: str) -> Tuple[bool, ...]:
    row = blocks_data[name]["rows"][0]
    return tuple(bool(x) for x in row)


def cts_support_placements(blocks_data: Dict[str, Any]) -> List[GliderPlacement]:
    a_row0 = load_block_row0(blocks_data, "A")
    l_row0 = load_block_row0(blocks_data, "L")
    return [
        GliderPlacement(origin=CTS_OSSIFIER_ORIGIN, cook_width=6, bits=tuple(a_row0[:6])),
        GliderPlacement(origin=CTS_LEADER_ORIGIN, cook_width=30, bits=l_row0),
    ]


def cts_support_placements_for_idx(
    blocks_data: Dict[str, Any], appendants: List[List[bool]], idx: int
) -> List[GliderPlacement]:
    a_row0 = load_block_row0(blocks_data, "A")
    k_row0 = load_block_row0(blocks_data, "K")
    h_row0 = load_block_row0(blocks_data, "H")
    ossifier = GliderPlacement(
        origin=CTS_OSSIFIER_ORIGIN, cook_width=6, bits=tuple(a_row0[:6])
    )
    if not appendants:
        raise ValueError("appendants list empty")
    app = appendants[idx % len(appendants)]
    if not app:
        l_row0 = load_block_row0(blocks_data, "L")
        return [
            ossifier,
            GliderPlacement(origin=CTS_LEADER_ORIGIN, cook_width=30, bits=l_row0),
        ]
    h_origin = CTS_LEADER_ORIGIN + len(k_row0)
    return [
        ossifier,
        GliderPlacement(origin=CTS_LEADER_ORIGIN, cook_width=30, bits=k_row0),
        GliderPlacement(origin=h_origin, cook_width=30, bits=h_row0),
    ]


def cts_word_to_placements_phased_with_support_idx(
    blocks_data: Dict[str, Any],
    appendants: List[List[bool]],
    idx: int,
    word: List[bool],
) -> List[GliderPlacement]:
    support = cts_support_placements_for_idx(blocks_data, appendants, idx)
    data = cts_word_to_placements_phased(word)
    return sorted(support + data, key=lambda g: g.origin)


def cts_step(appendants: List[List[bool]], idx: int, word: List[bool]) -> Tuple[List[bool], int]:
    if not word:
        return [], idx
    head, rest = word[0], word[1:]
    if not appendants:
        return rest, idx
    k = len(appendants)
    app = appendants[idx % k]
    idx1 = (idx + 1) % k
    if head:
        return rest + app, idx1
    return rest, idx1


def cts_eval_with_idx(
    appendants: List[List[bool]], n: int, word: List[bool], idx0: int = 0
) -> Tuple[List[bool], int]:
    w, idx = word, idx0
    for _ in range(n):
        w, idx = cts_step(appendants, idx, w)
    return w, idx


def c2_sim_left(tape: List[bool], i: int) -> bool:
    return False if i == 0 else tape[i - 1]


def c2_sim_right(tape: List[bool], i: int) -> bool:
    return tape[i + 1] if i + 1 < len(tape) else cook_ether(i + 1)


def rule110_output(left: bool, center: bool, right: bool) -> bool:
    idx = (4 * int(left)) + (2 * int(center)) + int(right)
    return RULE110[idx]


def c2_sim_step(tape: List[bool]) -> List[bool]:
    return [
        rule110_output(c2_sim_left(tape, i), tape[i], c2_sim_right(tape, i))
        for i in range(len(tape))
    ]


def c2_sim_run(n: int, tape: List[bool]) -> List[bool]:
    out = tape
    for _ in range(n):
        out = c2_sim_step(out)
    return out


def list_phased_glider_at(
    placements: List[GliderPlacement], tape: List[bool], slot: int
) -> bool:
    origin = c2_sim_origin(slot)
    accum = accum_phase_at(placements, origin)
    return tape[origin] != phase_ether(origin, accum)


def check_phased_post_decode(
    fin: List[bool],
    post_placements: List[GliderPlacement],
    post_word: List[bool],
) -> Dict[str, Any]:
    slots = []
    ok = True
    for slot in range(len(post_word)):
        decoded = list_phased_glider_at(post_placements, fin, slot)
        expected = post_word[slot]
        match = decoded == expected
        ok = ok and match
        slots.append(
            {
                "slot": slot,
                "origin": c2_sim_origin(slot),
                "decoded": decoded,
                "expected": expected,
                "match": match,
            }
        )
    return {"ok": ok, "slots": slots}


def check_origin_cells(
    fin: List[bool], target_tape: List[bool], n_slots: int
) -> Dict[str, Any]:
    slots = []
    ok = True
    for slot in range(n_slots):
        origin = c2_sim_origin(slot)
        got = fin[origin]
        expected = target_tape[origin]
        match = got == expected
        ok = ok and match
        slots.append(
            {"slot": slot, "origin": origin, "got": got, "expected": expected, "match": match}
        )
    return {"ok": ok, "slots": slots}


def check_data_cones(
    fin: List[bool], target_tape: List[bool], n_slots: int
) -> Dict[str, Any]:
    slots = []
    ok = True
    for slot in range(n_slots):
        cone_ok = True
        mismatches = 0
        for d in range(NUM_DATA_CONE_CELLS):
            k = cts_slot_origin(slot) - CONE_RADIUS + d
            if fin[k] != target_tape[k]:
                cone_ok = False
                mismatches += 1
        ok = ok and cone_ok
        slots.append(
            {
                "slot": slot,
                "cone_lo": cts_slot_origin(slot) - CONE_RADIUS,
                "all_match": cone_ok,
                "mismatch_count": mismatches,
            }
        )
    return {"ok": ok, "slots": slots}


def verify_init_against_lean_export(
    python_tape: List[bool], json_path: Path
) -> Dict[str, Any]:
    if not json_path.is_file():
        return {"skipped": True, "reason": f"missing {json_path}"}
    exported = [bool(x) for x in json.loads(json_path.read_text())]
    if len(exported) != len(python_tape):
        return {
            "skipped": False,
            "match": False,
            "reason": f"length mismatch export={len(exported)} python={len(python_tape)}",
        }
    mismatches = sum(1 for a, b in zip(exported, python_tape) if a != b)
    return {
        "skipped": False,
        "match": mismatches == 0,
        "mismatch_count": mismatches,
        "mismatch_fraction": mismatches / len(exported),
    }


def run_case(
    case_id: str,
    blocks_data: Dict[str, Any],
    appendants: List[List[bool]],
    word0: List[bool],
    idx0: int,
    n_cts_steps: int,
) -> Dict[str, Any]:
    post_word, post_idx = cts_eval_with_idx(appendants, n_cts_steps, word0, idx0)
    m_steps = cook_total_m_from(appendants, n_cts_steps, idx0)

    init_placements = cts_word_to_placements_phased_with_support_idx(
        blocks_data, appendants, idx0, word0
    )
    post_placements = cts_word_to_placements_phased_with_support_idx(
        blocks_data, appendants, post_idx, post_word
    )
    init_tape = build_phased_tape(init_placements)
    target_tape = build_phased_tape(post_placements)
    fin = c2_sim_run(m_steps, init_tape)

    phased_post = check_phased_post_decode(fin, post_placements, post_word)
    origin = check_origin_cells(fin, target_tape, len(post_word))
    cones = check_data_cones(fin, target_tape, len(post_word))

    return {
        "case_id": case_id,
        "appendants": ["".join("Y" if b else "N" for b in a) for a in appendants],
        "word0": word0,
        "idx0": idx0,
        "n_cts_steps": n_cts_steps,
        "m_r110_steps": m_steps,
        "post_word": post_word,
        "post_idx": post_idx,
        "post_word_str": "".join("Y" if b else "N" for b in post_word) if post_word else "(empty)",
        "init_placements_count": len(init_placements),
        "phased_post_decode": phased_post,
        "origin_cell_match": origin,
        "data_cone_match": cones,
    }


def main() -> None:
    print("Rank 5-FSS-COOK-PHASED — phased CTS scaffold", flush=True)

    if not COOK_BLOCKS_PATH.exists():
        raise FileNotFoundError(f"Missing Cook blocks: {COOK_BLOCKS_PATH}")

    blocks_data = json.loads(COOK_BLOCKS_PATH.read_text())

    # Sanity: Python init matches Lean-exported len6TruePhasedSupportInit
    len6_appendants = [[False] * 6]
    len6_word = [True]
    len6_init_placements = cts_word_to_placements_phased_with_support_idx(
        blocks_data, len6_appendants, 0, len6_word
    )
    len6_python_init = build_phased_tape(len6_init_placements)
    init_check = verify_init_against_lean_export(len6_python_init, LEN6_INIT_JSON)
    _RESULTS["len6_init_lean_export_check"] = init_check

    # Case 1: simple M=30 — empty appendant, word [Y] (task example)
    case_simple = run_case(
        case_id="simple_empty_appendant_Y",
        blocks_data=blocks_data,
        appendants=[[]],
        word0=[True],
        idx0=0,
        n_cts_steps=1,
    )

    # Case 2: L=6 canonical — [Y] → NNNNNN, M=390 (Lean #14/#15)
    case_len6 = run_case(
        case_id="cook_min_len6_true_to_nnnnnn",
        blocks_data=blocks_data,
        appendants=len6_appendants,
        word0=len6_word,
        idx0=0,
        n_cts_steps=1,
    )

    _RESULTS["cases"] = [case_simple, case_len6]

    # Verdict
    len6_phased_ok = case_len6["phased_post_decode"]["ok"]
    len6_origin_ok = case_len6["origin_cell_match"]["ok"]
    len6_cones_ok = case_len6["data_cone_match"]["ok"]
    simple_phased_ok = case_simple["phased_post_decode"]["ok"]

    init_matches_lean = init_check.get("match", False)

    if len6_phased_ok and len6_origin_ok and init_matches_lean:
        cat_level = "CatA partial"
        interpretation = (
            "Phased CTS scaffold reproduces Lean len6TruePhasedSupportInit and certifies "
            "one-step phased post-decode + origin-cell readback for cook_min_len6 ([Y]→NNNNNN, "
            "M=390). Full 61-cell data-cone agreement fails (consistent with Lean "
            "len6_one_step_data_cones_not_ok). Simple M=30 empty-appendant case passes vacuous "
            "phased readback (post-word empty) but does not exercise substantive glider dynamics."
        )
        follow_on = "5-FSS-COOK-CENTRAL"
    else:
        cat_level = "CatD"
        failures = []
        if not init_matches_lean:
            failures.append("Python phased init ≠ Lean export")
        if not len6_phased_ok:
            failures.append("L=6 phased post-decode FAIL")
        if not len6_origin_ok:
            failures.append("L=6 origin-cell readback FAIL")
        interpretation = (
            "Phased CTS scaffold failed verification: " + "; ".join(failures)
        )
        follow_on = "5-FSS-COOK-PHASED-2"

    _RESULTS["verdict"] = {
        "init_matches_lean_export": init_matches_lean,
        "simple_m30_phased_post_decode": simple_phased_ok,
        "len6_phased_post_decode": len6_phased_ok,
        "len6_origin_cell_match": len6_origin_ok,
        "len6_data_cone_match": len6_cones_ok,
        "phased_cts_one_step_works": len6_phased_ok and len6_origin_ok,
        "full_data_cone_cts_step": len6_cones_ok,
        "central_region_block_stack": False,
        "cat_level": cat_level,
        "interpretation": interpretation,
        "follow_on_rank": follow_on,
        "failure_locus": (
            None
            if len6_phased_ok and len6_origin_ok
            else "phased tape construction or c2SimRun readback mismatch vs Lean witnesses"
        ),
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
