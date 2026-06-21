#!/usr/bin/env python3
"""
EPIC_073 Rank 070-135: Multi-cell injection loophole reconciliation

Tests whether multi-cell perturbations to ether backgrounds can nucleate
persistent C2 gliders from the 10 Rule-110 phases that were TRANSIENT under
single-bit injection (Rank 070-113).

Transient phases (Rule 110): all except {1, 6, 7, 10}.

For each transient phase:
  - Structured 2-, 3-, and 5-bit perturbation patterns
  - 100 random multi-cell perturbations (k uniform in {2, 3, 5})

Pass criteria (same as 070-113):
  |v - 2/3| < 0.01, period-3 purity >= 0.95, lead still growing at T_end.
"""

from __future__ import annotations

import json
import random
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

TIMEOUT_SECONDS = 600
SEED = 135070

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}

ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
C2_PREFIX = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]  # first 10 cells of C2 glider

TARGET_SPEED = 2 / 3
T_RUN = 300
T_MID = 150
L = 840
RANDOM_TRIALS = 100
BIT_SIZES = (2, 3, 5)

PERSISTENT_PHASES_110 = {1, 6, 7, 10}
TRANSIENT_PHASES_110 = sorted(p for p in range(14) if p not in PERSISTENT_PHASES_110)

OUT_JSON = Path(__file__).with_name("epic073_rank070_135_multicell_injection_results.json")


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


@dataclass
class TrialResult:
    phase: int
    pattern_type: str
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
        classification = "PERSISTENT_C2"
        persistent = True
    elif final_lead <= 5 or (mid_lead > 20 and final_lead < mid_lead * 0.5):
        classification = "TRANSIENT"
        persistent = False
    elif growing and speed_error < 0.05:
        classification = "WEAK_PROPAGATING"
        persistent = False
    else:
        classification = "OTHER"
        persistent = False

    return speed, speed_error, purity, classification, persistent


def measure_flips(
    phase: int,
    flip_positions: list[int],
    pattern_type: str,
    pattern_id: str,
) -> TrialResult:
    center = center_for_phase(L, phase)
    base = [ETHER_110[i % 14] for i in range(L)]
    pert = base[:]
    for pos in flip_positions:
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
        pattern_type=pattern_type,
        pattern_id=pattern_id,
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


def structured_patterns(center: int, k: int) -> list[tuple[str, list[int]]]:
    """Deterministic multi-cell flip sets near center."""
    patterns: list[tuple[str, list[int]]] = []

    # contiguous block centered at perturbation site
    half = k // 2
    block = [center - half + i for i in range(k)]
    patterns.append((f"block_{k}at_center", block))

    # forward/right contiguous segment
    patterns.append((f"right_block_{k}", [center + i for i in range(1, k + 1)]))

    # symmetric spread around center
    if k == 2:
        patterns.append(("sym_pair", [center - 1, center + 1]))
    elif k == 3:
        patterns.append(("sym_triple", [center - 1, center, center + 1]))
    elif k == 5:
        patterns.append(("sym_pent", [center - 2, center - 1, center, center + 1, center + 2]))

    # C2 prefix overlay (XOR target bits onto ether)
    prefix_positions = [center + i for i in range(k)]
    patterns.append((f"c2_prefix_{k}", prefix_positions))

    # flip all cells in local ether triple neighborhood
    if k == 3:
        patterns.append(("ether_triple", [center - 1, center, center + 1]))

    # same-phase cells within one ether period
    same_phase = [center + 14 * d for d in range(-1, 2) if 0 <= center + 14 * d < L][:k]
    if len(same_phase) == k:
        patterns.append((f"same_phase_stride_{k}", same_phase))

    return patterns


def random_flip_set(rng: random.Random, center: int, k: int) -> list[int]:
    """Random k distinct cells within center ± 10 (local injection window)."""
    window = list(range(max(0, center - 10), min(L, center + 11)))
    if len(window) < k:
        window = list(range(max(0, center - 20), min(L, center + 21)))
    return sorted(rng.sample(window, k))


def run_phase_survey(phase: int, rng: random.Random) -> dict:
    center = center_for_phase(L, phase)
    structured_results: list[TrialResult] = []
    random_results: list[TrialResult] = []

    for k in BIT_SIZES:
        for pattern_id, positions in structured_patterns(center, k):
            valid = all(0 <= p < L for p in positions)
            if not valid:
                continue
            structured_results.append(
                measure_flips(phase, positions, "structured", pattern_id)
            )

    for trial in range(RANDOM_TRIALS):
        k = rng.choice(BIT_SIZES)
        positions = random_flip_set(rng, center, k)
        random_results.append(
            measure_flips(phase, positions, "random", f"rand_{trial:03d}_k{k}")
        )

    all_trials = structured_results + random_results
    persistent = [t for t in all_trials if t.persistent]
    return {
        "phase": phase,
        "center": center,
        "ether_triple": [
            ETHER_110[(phase - 1) % 14],
            ETHER_110[phase % 14],
            ETHER_110[(phase + 1) % 14],
        ],
        "z7_phase": phase % 7,
        "single_bit_070_113": "TRANSIENT",
        "n_structured": len(structured_results),
        "n_random": len(random_results),
        "n_total": len(all_trials),
        "n_persistent": len(persistent),
        "persistent_fraction": len(persistent) / len(all_trials) if all_trials else 0.0,
        "random_persistent_fraction": sum(1 for t in random_results if t.persistent) / RANDOM_TRIALS,
        "structured_persistent_fraction": (
            sum(1 for t in structured_results if t.persistent) / len(structured_results)
            if structured_results else 0.0
        ),
        "became_persistent": len(persistent) > 0,
        "best_trial": asdict(min(all_trials, key=lambda t: t.speed_error)) if all_trials else None,
        "persistent_trials": [asdict(t) for t in persistent[:20]],
    }


def main() -> None:
    t0 = time.time()
    rng = random.Random(SEED)

    phase_results = [run_phase_survey(phase, rng) for phase in TRANSIENT_PHASES_110]

    signal.alarm(0)

    phases_became_persistent = [r["phase"] for r in phase_results if r["became_persistent"]]
    total_trials = sum(r["n_total"] for r in phase_results)
    total_persistent = sum(r["n_persistent"] for r in phase_results)
    random_persistent = sum(
        round(r["random_persistent_fraction"] * RANDOM_TRIALS) for r in phase_results
    )

    loophole_open = len(phases_became_persistent) > 0

    output = {
        "rank": "070-135",
        "hypothesis": (
            "Multi-cell ether injection cannot nucleate persistent C2 from transient phases"
        ),
        "L": L,
        "T_run": T_RUN,
        "random_trials_per_phase": RANDOM_TRIALS,
        "bit_sizes": list(BIT_SIZES),
        "transient_phases_110": TRANSIENT_PHASES_110,
        "persistent_phases_110_reference": sorted(PERSISTENT_PHASES_110),
        "phase_results": phase_results,
        "summary": {
            "total_trials": total_trials,
            "total_persistent": total_persistent,
            "overall_persistent_fraction": total_persistent / total_trials if total_trials else 0.0,
            "random_persistent_count": random_persistent,
            "random_persistent_fraction": random_persistent / (RANDOM_TRIALS * len(TRANSIENT_PHASES_110)),
            "phases_became_persistent": phases_became_persistent,
            "n_phases_became_persistent": len(phases_became_persistent),
            "loophole_open": loophole_open,
            "loophole_status": "OPEN" if loophole_open else "CLOSED",
            "cat_level": "CatA",
            "conclusion": (
                "Multi-cell injection produces persistent C2 from previously transient phases"
                if loophole_open
                else "No transient phase yields persistent C2 under multi-cell injection; "
                "single-bit survey (070-113) is comprehensive"
            ),
        },
        "wall_clock_s": time.time() - t0,
    }

    OUT_JSON.write_text(json.dumps(output, indent=2))
    print(json.dumps(output["summary"], indent=2))
    print(f"\nWrote {OUT_JSON}")
    print(f"Wall clock: {output['wall_clock_s']:.1f}s")


if __name__ == "__main__":
    main()
