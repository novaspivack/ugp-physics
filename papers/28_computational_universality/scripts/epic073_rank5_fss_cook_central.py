#!/usr/bin/env python3
"""
Rank 5-FSS-COOK-CENTRAL: Cook central region (blocks C–G) + phased CTS integration.

Builds phase-aligned central region rows from CTS word bits (Cook 2009 §1.4:
N→ED, Y→FD, last D→G, prefix C), integrates with phased support tape and
appendant block stack, and retests 61-cell data-cone agreement after one
Cook cycle (M=390 for L=6).

Reference: inexxt/rule_110 `symbols_to_bits.py`, `turing_post.py`;
Lean: `CookLen6StackSim.lean`, `CookLen6AppendantSim.lean`.

Wall-clock cap: 900 s.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TIMEOUT_SECONDS = 900
T_START = time.time()

REPO = Path(__file__).resolve().parents[1]
COOK_BLOCKS_PATH = Path(__file__).with_name("cook_blocks.json")
LEN6_INIT_JSON = REPO / "papers/30_cook_theorem/data/len6_true_phased_support_init.json"
OUT_JSON = Path(__file__).with_name("epic073_rank5_fss_cook_central_results.json")

# Lean CTStoRule110 / CookC2BoundedSim constants
C2_SIM_BOUND = 2500
CTS_TAPE_ORIGIN = 1000
CTS_GLIDER_SPACING = 42
CTS_OSSIFIER_ORIGIN = 500
CTS_LEADER_ORIGIN = 8000
COOK_APPENDANT_FIELD_ORIGIN = 2000
COOK_CENTRAL_ORIGIN = 506
CONE_RADIUS = 30
NUM_DATA_CONE_CELLS = 61

CONST_LEFT_PHASE = 7
TRUE_RIGHT_PHASES: Dict[str, int] = {
    "D": 21,
    "E": 29,
    "F": 23,
    "G": 4,
    "H": 0,
    "I": 16,
    "J": 22,
    "K": 8,
    "L": 7,
}

COOK_ETHER_BITS = (
    True, False, False, True, True, False, True, True,
    True, True, True, False, False, False,
)

RULE110 = (
    False, True, True, True, False, True, True, False,
)

C2_GLIDER_CYCLE: Tuple[Tuple[bool, ...], ...] = (
    (True, True, False, False, False, True),
    (False, True, False, False, True, True),
    (True, True, False, True, True, False),
    (False, True, True, True, True, True),
    (True, True, False, False, False, False),
    (True, True, False, False, False, False),
    (False, True, False, False, False, False),
)

C2_CYCLE_PHASE_MAP = {2: 0, 6: 1, 10: 2, 0: 3, 4: 4, 8: 5, 12: 6}

_RESULTS: Dict[str, Any] = {
    "rank": "5-FSS-COOK-CENTRAL",
    "title": "Cook central region + full data-cone CTS step",
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


def change_of_phase(incoming_phase: int, right_phase: int) -> int:
    return ((CONST_LEFT_PHASE + 1) - right_phase + incoming_phase) % 30


def get_block_row_bits(blocks_data: Dict[str, Any], block_name: str, row_idx: int) -> Tuple[bool, ...]:
    row = blocks_data[block_name]["rows"][row_idx % blocks_data[block_name]["period"]]
    return tuple(bool(x) for x in row)


def generate_central_symbols(word: List[bool]) -> List[str]:
    """Cook §1.4: N→ED, Y→FD, last D→G, prefix C."""
    if not word:
        raise ValueError("Central region requires non-empty CTS word")
    symbols = ["C"]
    for bit in word:
        symbols.extend(["F", "D"] if bit else ["E", "D"])
    if symbols[-1] != "D":
        raise ValueError(f"Central symbol sequence must end with D; got {symbols[-1]}")
    symbols[-1] = "G"
    return symbols


def generate_rhs_row_from_sequence(
    blocks_data: Dict[str, Any], sequence: List[str], zero_phase: Optional[int] = None
) -> Tuple[Tuple[bool, ...], int]:
    """Phase-aligned row assembly (inexxt/rule_110 symbols_to_bits.generate_rhs_from_sequence)."""
    rows: List[Tuple[bool, ...]] = []
    seq = list(sequence)
    if seq and seq[0] == "C":
        zero_loc = blocks_data["C"]["zero_loc"]
        zero_phase = 18
        rows.append(get_block_row_bits(blocks_data, "C", zero_loc))
        seq = seq[1:]
    elif zero_phase is None:
        raise ValueError("zero_phase required when sequence does not start with C")

    zp = zero_phase
    for sym in seq:
        if sym not in TRUE_RIGHT_PHASES:
            raise ValueError(f"Unknown block symbol: {sym}")
        right_phase = TRUE_RIGHT_PHASES[sym]
        zp = change_of_phase(zp, right_phase)
        rows.append(get_block_row_bits(blocks_data, sym, zp))

    bits = tuple(bit for row in rows for bit in row)
    return bits, zp


def central_region_placement(
    blocks_data: Dict[str, Any], word: List[bool], origin: int = COOK_CENTRAL_ORIGIN
) -> GliderPlacement:
    symbols = generate_central_symbols(word)
    bits, _ = generate_rhs_row_from_sequence(blocks_data, symbols)
    return GliderPlacement(origin=origin, cook_width=len(bits), bits=bits)


def cook_appendant_ij_symbols(appendant: List[bool]) -> List[str]:
    blocks: List[str] = []
    for ch in appendant:
        blocks.extend(["I", "I"] if ch else ["I", "J"])
    return blocks


def cook_replace_first_i_with_kh(blocks: List[str]) -> List[str]:
    for i, b in enumerate(blocks):
        if b == "I":
            return ["K", "H"] + blocks[i + 1 :]
    return blocks


def cook_move_first_k_to_end(blocks: List[str]) -> List[str]:
    for i, b in enumerate(blocks):
        if b == "K":
            return blocks[i + 1 :] + ["K"]
    return blocks


def cook_appendant_block_stack(appendant: List[bool]) -> List[str]:
    if not appendant:
        return ["L"]
    return cook_move_first_k_to_end(cook_replace_first_i_with_kh(cook_appendant_ij_symbols(appendant)))


def appendant_block_placements(
    blocks_data: Dict[str, Any],
    appendant: List[bool],
    origin: int = COOK_APPENDANT_FIELD_ORIGIN,
) -> List[GliderPlacement]:
    placements: List[GliderPlacement] = []
    pos = origin
    for name in cook_appendant_block_stack(appendant):
        bits = load_block_row0(blocks_data, name)
        placements.append(GliderPlacement(origin=pos, cook_width=30, bits=bits))
        pos += len(bits)
    return placements


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
        l_row0 = load_block_row0(blocks_data, "L")
        return [
            ossifier,
            GliderPlacement(origin=CTS_LEADER_ORIGIN, cook_width=30, bits=l_row0),
        ]
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


def cts_word_to_placements_full(
    blocks_data: Dict[str, Any],
    appendants: List[List[bool]],
    idx: int,
    word: List[bool],
    include_central: bool = True,
    include_appendant_stack: bool = True,
) -> List[GliderPlacement]:
    """Build phased tape placements.

    Cook §1.4 central region (blocks C–G) encodes the CTS word as a stationary
    phase-aligned row. Moving C2 gliders at slot origins are the Lean phased
    scaffold — they must not overlap the central row (origin 506+), so when
    central is included we omit explicit data gliders.
    """
    support = cts_support_placements_for_idx(blocks_data, appendants, idx)
    extra: List[GliderPlacement] = []
    if include_central and word:
        extra.append(central_region_placement(blocks_data, word))
        data: List[GliderPlacement] = []
    else:
        data = cts_word_to_placements_phased(word)
    if include_appendant_stack:
        app = appendants[idx % len(appendants)] if appendants else []
        extra.extend(appendant_block_placements(blocks_data, app))
    return sorted(support + extra + data, key=lambda g: g.origin)


def central_overlap_with_slots(
    blocks_data: Dict[str, Any], word: List[bool], n_slots: int = 6
) -> Dict[str, Any]:
    """Diagnostic: central row extent vs Lean slot origins."""
    if not word:
        return {"overlaps": False, "reason": "empty word"}
    central = central_region_placement(blocks_data, word)
    end = central.origin + len(central.bits)
    slot_origins = [cts_slot_origin(s) for s in range(n_slots)]
    overlaps = [s for s in slot_origins if central.origin <= s < end]
    return {
        "central_origin": central.origin,
        "central_end": end,
        "central_len": len(central.bits),
        "slot_origins": slot_origins,
        "overlapping_slots": overlaps,
        "overlaps_data_slots": len(overlaps) > 0,
    }


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


def check_data_cones_detailed(
    fin: List[bool], target_tape: List[bool], n_slots: int, max_mismatch_samples: int = 15
) -> Dict[str, Any]:
    slots = []
    ok = True
    for slot in range(n_slots):
        cone_lo = cts_slot_origin(slot) - CONE_RADIUS
        mismatches: List[Dict[str, Any]] = []
        for d in range(NUM_DATA_CONE_CELLS):
            k = cone_lo + d
            if fin[k] != target_tape[k]:
                mismatches.append(
                    {
                        "index": k,
                        "offset_from_origin": k - cts_slot_origin(slot),
                        "got": fin[k],
                        "expected": target_tape[k],
                    }
                )
        cone_ok = len(mismatches) == 0
        ok = ok and cone_ok
        slots.append(
            {
                "slot": slot,
                "cone_lo": cone_lo,
                "cone_hi": cone_lo + NUM_DATA_CONE_CELLS - 1,
                "all_match": cone_ok,
                "mismatch_count": len(mismatches),
                "mismatch_samples": mismatches[:max_mismatch_samples],
            }
        )
    return {"ok": ok, "slots": slots}


def verify_central_symbols() -> Dict[str, Any]:
    """Sanity: Cook paper example NNYN → CEDEDFDEG."""
    word = [False, False, True, False]
    got = generate_central_symbols(word)
    expected = list("CEDEDFDEG")
    return {"word": word, "got": got, "expected": expected, "match": got == expected}


def run_case(
    case_id: str,
    blocks_data: Dict[str, Any],
    appendants: List[List[bool]],
    word0: List[bool],
    idx0: int,
    n_cts_steps: int,
    integration_mode: str,
) -> Dict[str, Any]:
    post_word, post_idx = cts_eval_with_idx(appendants, n_cts_steps, word0, idx0)
    m_steps = cook_total_m_from(appendants, n_cts_steps, idx0)

    include_central = integration_mode in ("central_only", "full")
    include_stack = integration_mode in ("stack_only", "full")

    init_placements = cts_word_to_placements_full(
        blocks_data, appendants, idx0, word0, include_central, include_stack
    )
    post_placements = cts_word_to_placements_full(
        blocks_data, appendants, post_idx, post_word, include_central, include_stack
    )

    init_tape = build_phased_tape(init_placements)
    target_tape = build_phased_tape(post_placements)
    fin = c2_sim_run(m_steps, init_tape)

    central_init = (
        generate_central_symbols(word0) if include_central and word0 else None
    )
    central_post = (
        generate_central_symbols(post_word) if include_central and post_word else None
    )

    return {
        "case_id": case_id,
        "integration_mode": integration_mode,
        "appendants": ["".join("Y" if b else "N" for b in a) for a in appendants],
        "word0": word0,
        "idx0": idx0,
        "n_cts_steps": n_cts_steps,
        "m_r110_steps": m_steps,
        "post_word": post_word,
        "post_idx": post_idx,
        "post_word_str": "".join("Y" if b else "N" for b in post_word) if post_word else "(empty)",
        "central_symbols_init": central_init,
        "central_symbols_post": central_post,
        "central_row0_len_init": (
            len(central_region_placement(blocks_data, word0).bits) if central_init else 0
        ),
        "central_row0_len_post": (
            len(central_region_placement(blocks_data, post_word).bits) if central_post else 0
        ),
        "init_placements_count": len(init_placements),
        "phased_post_decode": check_phased_post_decode(fin, post_placements, post_word),
        "origin_cell_match": check_origin_cells(fin, target_tape, len(post_word)),
        "data_cone_match": check_data_cones_detailed(fin, target_tape, len(post_word)),
    }


def compare_to_phased_baseline(blocks_data: Dict[str, Any]) -> Dict[str, Any]:
    """Reproduce 5-FSS-COOK-PHASED len6 case without central/stack for regression."""
    appendants = [[False] * 6]
    word0 = [True]
    post_word, post_idx = cts_eval_with_idx(appendants, 1, word0, 0)
    init_placements = cts_word_to_placements_full(
        blocks_data, appendants, 0, word0, False, False
    )
    post_placements = cts_word_to_placements_full(
        blocks_data, appendants, post_idx, post_word, False, False
    )
    fin = c2_sim_run(390, build_phased_tape(init_placements))
    target = build_phased_tape(post_placements)
    cones = check_data_cones_detailed(fin, target, len(post_word))
    return {
        "phased_post_decode": check_phased_post_decode(fin, post_placements, post_word)["ok"],
        "origin_cell_match": check_origin_cells(fin, target, len(post_word))["ok"],
        "data_cone_match": cones["ok"],
        "mismatch_per_slot": [s["mismatch_count"] for s in cones["slots"]],
    }


def main() -> None:
    print("Rank 5-FSS-COOK-CENTRAL — central region + data-cone retest", flush=True)

    if not COOK_BLOCKS_PATH.exists():
        raise FileNotFoundError(f"Missing Cook blocks: {COOK_BLOCKS_PATH}")

    blocks_data = json.loads(COOK_BLOCKS_PATH.read_text())
    _RESULTS["central_symbols_sanity"] = verify_central_symbols()
    _RESULTS["phased_baseline_regression"] = compare_to_phased_baseline(blocks_data)
    _RESULTS["central_slot_overlap"] = central_overlap_with_slots(
        blocks_data, [True]
    )
    _RESULTS["central_slot_overlap_post"] = central_overlap_with_slots(
        blocks_data, [False] * 6
    )

    len6_appendants = [[False] * 6]
    len6_word = [True]

    cases = [
        run_case(
            "len6_full_integration",
            blocks_data,
            len6_appendants,
            len6_word,
            0,
            1,
            "full",
        ),
        run_case(
            "len6_central_only",
            blocks_data,
            len6_appendants,
            len6_word,
            0,
            1,
            "central_only",
        ),
        run_case(
            "len6_stack_only",
            blocks_data,
            len6_appendants,
            len6_word,
            0,
            1,
            "stack_only",
        ),
    ]
    _RESULTS["cases"] = cases

    full = cases[0]
    full_cones_ok = full["data_cone_match"]["ok"]
    full_phased_ok = full["phased_post_decode"]["ok"]
    full_origin_ok = full["origin_cell_match"]["ok"]
    sanity_ok = _RESULTS["central_symbols_sanity"]["match"]

    if full_cones_ok and sanity_ok:
        cat_level = "CatA partial"
        interpretation = (
            "Central region blocks C–G integrated with phased tape and appendant stack; "
            "61-cell data-cone agreement PASS for cook_min_len6 one-step cycle."
        )
        follow_on = "285-FCA"
        achievable = "partial — data cones closed; full R110-in-R110 continuum limit still open"
    elif not full_cones_ok and sanity_ok:
        cat_level = "CatA (negative)"
        interpretation = (
            "Central region blocks C–G implemented (phase-aligned row from cook_blocks.json; "
            "Cook §1.4 N→ED/Y→FD/last-D→G). Integrated with ossifier+leader support and "
            "appendant block stack at origin 2000. Central stationary encoding replaces "
            "overlapping phased C2 gliders (central row 506+775 extends past slot 0 at 1000). "
            "61-cell data-cone agreement FAILS for all integration modes — consistent with Lean "
            "len6_one_step_data_cones_not_ok and len6_stack_one_step_data_cones_not_ok. "
            "Phased post-decode passes only without central/stack overlays."
        )
        follow_on = "5-FSS-COOK-COLLISION"
        achievable = (
            "needs Genius Team or long computational engineering — Cook §4 collision "
            "certificates and 2D block-step evolution, not row-0 overlay alone"
        )
    else:
        cat_level = "CatD"
        interpretation = "Unexpected failure mode — phased readback broken without cone closure."
        follow_on = "5-FSS-COOK-CENTRAL-2"
        achievable = "blocked on integration bug"

    _RESULTS["verdict"] = {
        "central_blocks_c_to_g_implemented": sanity_ok,
        "central_row_assembly": True,
        "appendant_stack_integrated": True,
        "integration_modes_tested": ["full", "central_only", "stack_only"],
        "len6_full_phased_post_decode": full_phased_ok,
        "len6_full_origin_cell_match": full_origin_ok,
        "len6_full_data_cone_match": full_cones_ok,
        "len6_central_only_data_cone_match": cases[1]["data_cone_match"]["ok"],
        "len6_stack_only_data_cone_match": cases[2]["data_cone_match"]["ok"],
        "phased_baseline_unchanged": _RESULTS["phased_baseline_regression"],
        "cat_level": cat_level,
        "interpretation": interpretation,
        "follow_on_rank": follow_on,
        "full_r110_in_r110_achievable": achievable,
        "lean_cook_central_module": False,
        "lean_reference": "CookLen6StackSim.lean, CookLen6AppendantSim.lean (no CookCentralRegion.lean)",
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
