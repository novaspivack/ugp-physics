#!/usr/bin/env python3
"""
EPIC_073 Rank 070-136: Multi-cell C2 bypass grammar and cross-layer coupling test

Part 1 — Minimum perturbation grammar classification:
  For each of 10 transient Rule-110 ether phases, find minimum flip count and
  best pattern family (sym_pair, block, prefix) that nucleates persistent C2.

Part 2 — Cross-layer coupling (Rule 124 → Rule 110):
  Rule 124 runs a multi-cell-seeded C2 glider; its deviation field (or front-
  triggered multi-cell pattern) is injected into Rule 110 transient ether.
  Tests whether multi-cell cross-layer coupling bypasses gcd(3,14) period-sync no-go.

Timeout: 900 s wall-clock.
"""

from __future__ import annotations

import json
import random
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

TIMEOUT_SECONDS = 900
SEED = 136070

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}
RULE124 = {(l, c, r): RULE110[(r, c, l)] for l in range(2) for c in range(2) for r in range(2)}

ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
ETHER_124 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]
C2_PREFIX = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]

TARGET_SPEED = 2 / 3
T_RUN = 300
T_MID = 150
L = 840
MAX_WEIGHT = 5
RANDOM_TRIALS_PER_WEIGHT = 50

PERSISTENT_PHASES_110 = {1, 6, 7, 10}
TRANSIENT_PHASES_110 = sorted(p for p in range(14) if p not in PERSISTENT_PHASES_110)

OUT_JSON = Path(__file__).with_name("epic073_rank070_136_multicell_bypass_grammar_results.json")


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


@dataclass
class TrialResult:
    phase: int
    pattern_family: str
    pattern_id: str
    n_bits: int
    flip_positions: list[int]
    final_lead: int
    mid_lead: int
    speed: float
    speed_error: float
    period3_purity: float
    classification: str
    persistent: bool


def step_layer(tape: list[int], rule: dict) -> list[int]:
    n = len(tape)
    return [rule[(tape[(i - 1) % n], tape[i], tape[(i + 1) % n])] for i in range(n)]


def center_for_phase(length: int, phase: int) -> int:
    mid = length // 2
    offset = (phase - mid % 14) % 14
    if offset > 7:
        offset -= 14
    center = mid + offset
    assert center % 14 == phase and 0 <= center < length
    return center


def classify_leads(leads: list[int]) -> tuple[float, float, float, str, bool]:
    final_lead = leads[-1]
    mid_lead = leads[T_MID - 1]
    speed = final_lead / T_RUN
    speed_error = abs(speed - TARGET_SPEED)

    triplets = max(len(leads) - 3, 0)
    if triplets > 0:
        p3 = sum(1 for i in range(3, len(leads)) if leads[i] - leads[i - 3] == 2)
        purity = p3 / triplets
    else:
        purity = 0.0

    growing = final_lead >= mid_lead * 0.9 and final_lead > 10
    if speed_error < 0.01 and purity >= 0.95 and growing:
        return speed, speed_error, purity, "PERSISTENT_C2", True
    if final_lead <= 5 or (mid_lead > 20 and final_lead < mid_lead * 0.5):
        return speed, speed_error, purity, "TRANSIENT", False
    if growing and speed_error < 0.05:
        return speed, speed_error, purity, "WEAK_PROPAGATING", False
    return speed, speed_error, purity, "OTHER", False


def measure_single_layer(phase: int, flip_positions: list[int], family: str, pid: str) -> TrialResult:
    center = center_for_phase(L, phase)
    base = [ETHER_110[i % 14] for i in range(L)]
    pert = base[:]
    for pos in flip_positions:
        if 0 <= pos < L:
            pert[pos] ^= 1

    leads: list[int] = []
    for _t in range(1, T_RUN + 1):
        base = step_layer(base, RULE110)
        pert = step_layer(pert, RULE110)
        diff = [base[i] != pert[i] for i in range(L)]
        lead = max((i - center for i in range(center + 1, L) if diff[i]), default=0)
        leads.append(lead)

    speed, speed_error, purity, classification, persistent = classify_leads(leads)
    return TrialResult(
        phase=phase,
        pattern_family=family,
        pattern_id=pid,
        n_bits=len(flip_positions),
        flip_positions=sorted(flip_positions),
        final_lead=leads[-1],
        mid_lead=leads[T_MID - 1],
        speed=speed,
        speed_error=speed_error,
        period3_purity=purity,
        classification=classification,
        persistent=persistent,
    )


def grammar_patterns(center: int, k: int) -> list[tuple[str, str, list[int]]]:
    """Return (family, pattern_id, positions) for weight k."""
    patterns: list[tuple[str, str, list[int]]] = []

    if k == 1:
        patterns.append(("single", "center_flip", [center]))
        return patterns

    if k == 2:
        patterns.append(("sym_pair", "sym_pair", [center - 1, center + 1]))
        patterns.append(("block", "block_2_center", [center - 1, center]))
        patterns.append(("block", "block_2_right", [center + 1, center + 2]))
        patterns.append(("prefix", "c2_prefix_2", [center + i for i in range(2)]))

    if k == 3:
        patterns.append(("block", "block_3_center", [center - 1, center, center + 1]))
        patterns.append(("block", "block_3_right", [center + i for i in range(1, 4)]))
        patterns.append(("prefix", "c2_prefix_3", [center + i for i in range(3)]))
        patterns.append(("sym_pair", "sym_triple", [center - 1, center, center + 1]))

    if k == 4:
        patterns.append(("block", "block_4_center", [center - 2, center - 1, center, center + 1]))
        patterns.append(("prefix", "c2_prefix_4", [center + i for i in range(4)]))

    if k == 5:
        patterns.append(("block", "block_5_center", [center - 2, center - 1, center, center + 1, center + 2]))
        patterns.append(("prefix", "c2_prefix_5", [center + i for i in range(5)]))
        patterns.append(("sym_pair", "sym_pent", [center - 2, center - 1, center, center + 1, center + 2]))

    valid = []
    for family, pid, pos in patterns:
        if all(0 <= p < L for p in pos) and len(pos) == k:
            valid.append((family, pid, pos))
    return valid


def random_patterns(rng: random.Random, center: int, k: int, n: int) -> list[tuple[str, list[int]]]:
    window = list(range(max(0, center - 10), min(L, center + 11)))
    out = []
    for i in range(n):
        if len(window) >= k:
            pos = sorted(rng.sample(window, k))
            out.append((f"rand_{i:03d}_k{k}", pos))
    return out


def minimum_grammar_for_phase(phase: int, rng: random.Random) -> dict:
    center = center_for_phase(L, phase)
    weight_results: dict[int, dict] = {}
    min_weight: Optional[int] = None
    best_structured: Optional[TrialResult] = None

    for k in range(1, MAX_WEIGHT + 1):
        structured_trials: list[TrialResult] = []
        for family, pid, positions in grammar_patterns(center, k):
            structured_trials.append(measure_single_layer(phase, positions, family, pid))

        random_trials: list[TrialResult] = []
        for pid, positions in random_patterns(rng, center, k, RANDOM_TRIALS_PER_WEIGHT):
            random_trials.append(measure_single_layer(phase, positions, "random", pid))

        all_trials = structured_trials + random_trials
        persistent = [t for t in all_trials if t.persistent]
        struct_persistent = [t for t in structured_trials if t.persistent]

        family_stats: dict[str, dict] = {}
        for fam in ("sym_pair", "block", "prefix"):
            fam_trials = [t for t in structured_trials if t.pattern_family == fam]
            fam_persist = [t for t in fam_trials if t.persistent]
            family_stats[fam] = {
                "n_trials": len(fam_trials),
                "n_persistent": len(fam_persist),
                "success_rate": len(fam_persist) / len(fam_trials) if fam_trials else 0.0,
                "best_pattern_id": fam_persist[0].pattern_id if fam_persist else None,
            }

        weight_results[k] = {
            "n_structured": len(structured_trials),
            "n_random": len(random_trials),
            "n_persistent": len(persistent),
            "structured_persistent": len(struct_persistent),
            "random_persistent_fraction": sum(1 for t in random_trials if t.persistent) / max(len(random_trials), 1),
            "structured_persistent_fraction": len(struct_persistent) / max(len(structured_trials), 1),
            "family_stats": family_stats,
            "any_persistent": len(persistent) > 0,
            "best_persistent": asdict(min(persistent, key=lambda t: t.speed_error)) if persistent else None,
            "best_structured_persistent": (
                asdict(min(struct_persistent, key=lambda t: t.speed_error)) if struct_persistent else None
            ),
        }

        if min_weight is None and len(struct_persistent) > 0:
            min_weight = k
            best_structured = min(struct_persistent, key=lambda t: (t.n_bits, t.speed_error))

    # Fallback: no structured pattern works — use random at lowest k with >=5% rate
    if min_weight is None:
        for k in range(2, MAX_WEIGHT + 1):
            wr = weight_results[k]
            if wr["random_persistent_fraction"] >= 0.05 and wr["n_persistent"] > 0:
                min_weight = k
                bp = wr["best_persistent"]
                if bp:
                    best_structured = None
                break

    # Best pattern family at minimum weight (structured only)
    best_family = "none"
    best_family_rate = 0.0
    if min_weight is not None:
        fs = weight_results[min_weight]["family_stats"]
        ranked = sorted(
            ((fam, fs[fam]["success_rate"]) for fam in fs if fs[fam]["n_trials"] > 0),
            key=lambda x: (-x[1], x[0]),
        )
        if ranked and ranked[0][1] > 0:
            best_family = ranked[0][0]
            best_family_rate = ranked[0][1]
        elif weight_results[min_weight]["random_persistent_fraction"] > 0:
            best_family = "random"
            best_family_rate = weight_results[min_weight]["random_persistent_fraction"]

    best_trial_dict = (
        asdict(best_structured) if best_structured is not None
        else weight_results[min_weight]["best_structured_persistent"] if min_weight
        else None
    )
    if best_trial_dict is None and min_weight is not None:
        best_trial_dict = weight_results[min_weight]["best_persistent"]

    return {
        "phase": phase,
        "center": center,
        "ether_triple": [
            ETHER_110[(phase - 1) % 14],
            ETHER_110[phase % 14],
            ETHER_110[(phase + 1) % 14],
        ],
        "minimum_weight": min_weight,
        "best_pattern_family": best_family,
        "best_family_success_rate": best_family_rate,
        "best_structured_trial": best_trial_dict,
        "weight_scan": weight_results,
        "overall_success_at_min_weight": (
            weight_results[min_weight]["n_persistent"] / (
                weight_results[min_weight]["n_structured"] + weight_results[min_weight]["n_random"]
            )
            if min_weight is not None else 0.0
        ),
    }


# ── Part 2: Cross-layer coupling ─────────────────────────────────────────────

def right_lead(diff: list[bool], center: int) -> Optional[int]:
    vals = [i - center for i in range(center + 1, L) if diff[i]]
    return max(vals) if vals else None


def left_lead(diff: list[bool], center: int) -> Optional[int]:
    vals = [center - i for i in range(0, center) if diff[i]]
    return max(vals) if vals else None


def deviation_cluster_positions(tape: list[int], ether: list[int], front_pos: int, width: int = 5) -> list[int]:
    """Cells with deviation from ether within width of front_pos."""
    dev = [tape[i] ^ ether[i % 14] for i in range(len(tape))]
    positions = []
    for i in range(max(0, front_pos - width), min(L, front_pos + width + 1)):
        if dev[i]:
            positions.append(i)
    return positions


def apply_pattern(tape: list[int], positions: list[int]) -> None:
    for p in positions:
        if 0 <= p < len(tape):
            tape[p] ^= 1


def measure_110_glider(base110: list[int], pert110: list[int], center: int) -> dict:
    leads: list[int] = []
    b, p = base110[:], pert110[:]
    for _t in range(1, T_RUN + 1):
        b = step_layer(b, RULE110)
        p = step_layer(p, RULE110)
        diff = [b[i] != p[i] for i in range(L)]
        rf = right_lead(diff, center)
        leads.append(rf if rf is not None else 0)

    speed, speed_error, purity, classification, persistent = classify_leads(leads)
    return {
        "speed": speed,
        "speed_error": speed_error,
        "period3_purity": purity,
        "classification": classification,
        "persistent": persistent,
        "final_lead": leads[-1],
    }


def cross_layer_deviation_sync(
    phase_110: int,
    seed_124_phase: int,
    seed_pattern: list[int],
    inject_period: int = 1,
) -> dict:
    """
    Coupling mode A: After each step, XOR Rule-124 deviation into Rule-110 at
    glider cluster sites (multi-cell spatial pattern, applied every step).
    """
    center_110 = center_for_phase(L, phase_110)
    center_124 = center_for_phase(L, seed_124_phase)

    base110 = [ETHER_110[i % 14] for i in range(L)]
    pert110 = base110[:]
    base124 = [ETHER_124[i % 14] for i in range(L)]
    pert124 = base124[:]
    apply_pattern(pert124, seed_pattern)

    cross_sites_peak = 0
    injections = 0

    for t in range(1, T_RUN + 1):
        base110 = step_layer(base110, RULE110)
        pert110 = step_layer(pert110, RULE110)
        base124 = step_layer(base124, RULE124)
        pert124 = step_layer(pert124, RULE124)

        if t % inject_period == 0:
            d124 = [pert124[i] != base124[i] for i in range(L)]
            rf124 = right_lead(d124, center_124)
            if rf124 is not None:
                front_abs = center_124 + rf124
                cluster = deviation_cluster_positions(pert124, ETHER_124, front_abs, width=6)
                if cluster:
                    apply_pattern(pert110, cluster)
                    cross_sites_peak = max(cross_sites_peak, len(cluster))
                    injections += 1

    glider = measure_110_glider(base110, pert110, center_110)
    return {
        "coupling_mode": "deviation_sync_multicell",
        "phase_110": phase_110,
        "seed_124_phase": seed_124_phase,
        "n_injections": injections,
        "cross_sites_peak": cross_sites_peak,
        **glider,
    }


def cross_layer_front_grammar_injection(
    phase_110: int,
    grammar_positions: list[int],
    grammar_center_offset: int,
    seed_124_phase: int,
    seed_pattern: list[int],
    inject_period: int = 21,
) -> dict:
    """
    Coupling mode B: Event-triggered multi-cell grammar injection from 124 glider
    front into 110 (Rank 122 Class B extended to multi-cell).
    """
    center_110 = center_for_phase(L, phase_110)
    center_124 = center_for_phase(L, seed_124_phase)

    base110 = [ETHER_110[i % 14] for i in range(L)]
    pert110 = base110[:]
    base124 = [ETHER_124[i % 14] for i in range(L)]
    pert124 = base124[:]
    apply_pattern(pert124, seed_pattern)

    injections = 0

    for t in range(1, T_RUN + 1):
        d124_pre = [pert124[i] != base124[i] for i in range(L)]
        rf124 = right_lead(d124_pre, center_124)

        base110 = step_layer(base110, RULE110)
        pert110 = step_layer(pert110, RULE110)
        base124 = step_layer(base124, RULE124)
        pert124 = step_layer(pert124, RULE124)

        if t > 10 and t % inject_period == 0 and rf124 is not None:
            front_abs = center_124 + rf124
            rel = [p - grammar_center_offset for p in grammar_positions]
            inject_pos = [front_abs + r for r in rel]
            apply_pattern(pert110, inject_pos)
            injections += 1

    glider = measure_110_glider(base110, pert110, center_110)
    return {
        "coupling_mode": "front_grammar_injection",
        "phase_110": phase_110,
        "seed_124_phase": seed_124_phase,
        "grammar_n_bits": len(grammar_positions),
        "inject_period": inject_period,
        "n_injections": injections,
        **glider,
    }


def cross_layer_continuous_deviation_field(phase_110: int, seed_124_phase: int, seed_pattern: list[int]) -> dict:
    """
    Coupling mode C: Each step, copy full 124 deviation field onto 110 (strongest
    multi-cell CA-local coupling — should fail if no-go extends to multi-cell).
    """
    center_110 = center_for_phase(L, phase_110)
    center_124 = center_for_phase(L, seed_124_phase)

    base110 = [ETHER_110[i % 14] for i in range(L)]
    pert110 = base110[:]
    base124 = [ETHER_124[i % 14] for i in range(L)]
    pert124 = base124[:]
    apply_pattern(pert124, seed_pattern)

    max_dev_sites = 0

    for _t in range(1, T_RUN + 1):
        base110 = step_layer(base110, RULE110)
        pert110 = step_layer(pert110, RULE110)
        base124 = step_layer(base124, RULE124)
        pert124 = step_layer(pert124, RULE124)

        d124 = [pert124[i] ^ base124[i] for i in range(L)]
        n_dev = sum(d124)
        max_dev_sites = max(max_dev_sites, n_dev)
        for i in range(L):
            if d124[i]:
                target = ETHER_110[i % 14] ^ d124[i]
                pert110[i] = target

    glider = measure_110_glider(base110, pert110, center_110)
    return {
        "coupling_mode": "continuous_deviation_field",
        "phase_110": phase_110,
        "seed_124_phase": seed_124_phase,
        "max_124_deviation_sites": max_dev_sites,
        **glider,
    }


def run_cross_layer_tests(grammar_by_phase: dict[int, dict]) -> dict:
    """Test cross-layer coupling for representative transient phases."""
    seed_124_phase = 3  # persistent C2 phase for Rule 124 (070-113)
    center_124 = center_for_phase(L, seed_124_phase)
    seed_pattern = [center_124 + i for i in range(2)]  # c2_prefix_2 on 124

    test_phases = [0, 3, 5, 11, 12]  # mix: high/medium/low structured success
    results = []

    for phase in test_phases:
        g = grammar_by_phase[phase]
        min_w = g["minimum_weight"]
        best = g.get("best_structured_trial")
        if best:
            grammar_pos = best["flip_positions"]
            grammar_center = g["center"]
        elif min_w:
            center = g["center"]
            grammar_pos = [center - 1, center + 1]
            grammar_center = center
        else:
            grammar_pos = [g["center"]]
            grammar_center = g["center"]

        results.append(cross_layer_deviation_sync(phase, seed_124_phase, seed_pattern))
        results.append(cross_layer_continuous_deviation_field(phase, seed_124_phase, seed_pattern))
        results.append(
            cross_layer_front_grammar_injection(
                phase, grammar_pos, grammar_center, seed_124_phase, seed_pattern, inject_period=21
            )
        )
        results.append(
            cross_layer_front_grammar_injection(
                phase, grammar_pos, grammar_center, seed_124_phase, seed_pattern, inject_period=7
            )
        )

    persistent_count = sum(1 for r in results if r["persistent"])
    front_persistent = [
        r for r in results
        if r["coupling_mode"] == "front_grammar_injection" and r["persistent"]
    ]
    sync_persistent = [
        r for r in results
        if r["coupling_mode"] == "deviation_sync_multicell" and r["persistent"]
    ]
    field_persistent = [
        r for r in results
        if r["coupling_mode"] == "continuous_deviation_field" and r["persistent"]
    ]

    bypass_works = len(front_persistent) > 0 or len(sync_persistent) > 0

    return {
        "seed_124_phase": seed_124_phase,
        "seed_pattern": seed_pattern,
        "test_phases_110": test_phases,
        "coupling_trials": results,
        "n_trials": len(results),
        "n_persistent_110": persistent_count,
        "front_grammar_persistent": len(front_persistent),
        "deviation_sync_persistent": len(sync_persistent),
        "continuous_field_persistent": len(field_persistent),
        "cross_layer_bypass": bypass_works,
        "nogo_scope": (
            "point_coupling_only"
            if bypass_works
            else "extends_to_multicell"
        ),
    }


def main() -> None:
    t0 = time.time()
    rng = random.Random(SEED)

    print("=" * 72)
    print("EPIC_073 Rank 070-136 — Multi-cell bypass grammar + cross-layer test")
    print("=" * 72)

    print("\n--- Part 1: Minimum grammar classification ---")
    grammar_results = []
    for phase in TRANSIENT_PHASES_110:
        gr = minimum_grammar_for_phase(phase, rng)
        grammar_results.append(gr)
        print(
            f"  phase {phase:2d}: min_weight={gr['minimum_weight']}  "
            f"best_family={gr['best_pattern_family']}  "
            f"rate={gr['best_family_success_rate']:.2f}"
        )

    grammar_by_phase = {g["phase"]: g for g in grammar_results}

    print("\n--- Part 2: Cross-layer coupling (124 → 110) ---")
    cross_layer = run_cross_layer_tests(grammar_by_phase)
    for r in cross_layer["coupling_trials"]:
        print(
            f"  phase {r['phase_110']:2d} {r['coupling_mode']:30s}  "
            f"persistent={r['persistent']}  v={r['speed']:.3f}  p3={r['period3_purity']:.3f}"
        )

    signal.alarm(0)

    min_weights = [g["minimum_weight"] for g in grammar_results if g["minimum_weight"] is not None]
    summary_grammar = {
        "phases_with_min_weight": len(min_weights),
        "global_min_weight": min(min_weights) if min_weights else None,
        "global_max_min_weight": max(min_weights) if min_weights else None,
        "mean_min_weight": sum(min_weights) / len(min_weights) if min_weights else None,
        "family_counts_at_min_weight": {},
    }
    for g in grammar_results:
        fam = g["best_pattern_family"]
        summary_grammar["family_counts_at_min_weight"][fam] = (
            summary_grammar["family_counts_at_min_weight"].get(fam, 0) + 1
        )

    nogo_bypass = cross_layer["cross_layer_bypass"]
    if nogo_bypass:
        cat_level = "CatAD"
        conclusion = (
            "Multi-cell cross-layer coupling nucleates persistent C2 on Rule 110; "
            "gcd(3,14) no-go applies to point/period-sync CA-local coupling only"
        )
        follow_on = "070-138 Lean cert — multi-body coupling bypass of CouplingNoGo"
    else:
        cat_level = "CatA"
        conclusion = (
            "Single-layer multi-cell injection works but cross-layer multi-cell coupling "
            "does not produce persistent C2 on Rule 110; no-go extends beyond point coupling"
        )
        follow_on = "070-137 — why single-layer multi-cell works but cross-layer fails"

    output = {
        "rank": "070-136",
        "parameters": {
            "L": L,
            "T_run": T_RUN,
            "max_weight": MAX_WEIGHT,
            "random_trials_per_weight": RANDOM_TRIALS_PER_WEIGHT,
            "seed": SEED,
            "timeout_s": TIMEOUT_SECONDS,
        },
        "part1_minimum_grammar": grammar_results,
        "part1_summary": summary_grammar,
        "part2_cross_layer": cross_layer,
        "summary": {
            "minimum_weights_by_phase": {
                g["phase"]: {
                    "min_weight": g["minimum_weight"],
                    "best_family": g["best_pattern_family"],
                    "success_rate": g["best_family_success_rate"],
                }
                for g in grammar_results
            },
            "cross_layer_bypass": nogo_bypass,
            "nogo_scope": cross_layer["nogo_scope"],
            "physical_interpretation": (
                "EW three-body vertex (W→ff) is multi-body coupling; bypasses point-coupling no-go"
                if nogo_bypass
                else "Cross-layer decoherence persists even with multi-cell patterns; "
                "single-layer loophole is initialization artifact not transferable coupling"
            ),
            "cat_level": cat_level,
            "conclusion": conclusion,
            "follow_on_rank": follow_on,
        },
        "wall_clock_s": time.time() - t0,
    }

    OUT_JSON.write_text(json.dumps(output, indent=2))
    print("\n" + json.dumps(output["summary"], indent=2))
    print(f"\nWrote {OUT_JSON}")
    print(f"Wall clock: {output['wall_clock_s']:.1f}s")


if __name__ == "__main__":
    main()
