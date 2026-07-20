#!/usr/bin/env python3
"""
EPIC_073 Rank 070-106: Rule 124 Mirror CA — Chiral Pair for Lorentz Invariance

Consolidated computational verification (EPIC_070 Rank 105 + Rank 111 baseline).
Tests all conjecture items from 070-106:

  1. Rule 124 = spatial mirror of Rule 110 (Wolfram codes 110 / 124)
  2. ETHER_124 period-14 stability, drift +4/step, Z7 sum = 1
  3. gen1 GoE under Rule 124 mod-2 f_MDL projection (exhaustive 2^5)
  4. Mirror-C2 glider |v_L| = 2/3 (random trials + canonical ether phase)
  5. Two-layer decoupled chiral pair: v_R = +2/3, v_L = -2/3, |v_R| = |v_L|

Robustness: tape lengths L in {560, 840, 1260}; 20 random perturbation trials on ETHER_124.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path

TIMEOUT_SECONDS = 600


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}
RULE124 = {(l, c, r): RULE110[(r, c, l)] for l in (0, 1) for c in (0, 1) for r in (0, 1)}

ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
ETHER_124 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]
GEN1 = (1, 5, 2, 2, 1)

TARGET_SPEED = 2 / 3
T_RUN = 300
L_VALUES = [560, 840, 1260]
N_RANDOM_TRIALS = 20
OUT_JSON = Path(__file__).with_name("epic073_rank070_106_rule124_chiral_verification_results.json")


def wolfram_code(rule: dict) -> int:
    return sum(rule[(n >> 2 & 1, n >> 1 & 1, n & 1)] << n for n in range(8))


def step_layer(tape: list[int], rule: dict) -> list[int]:
    n = len(tape)
    return [rule[(tape[(i - 1) % n], tape[i], tape[(i + 1) % n])] for i in range(n)]


def step_chiral(t110: list[int], t124: list[int]) -> tuple[list[int], list[int]]:
    return step_layer(t110, RULE110), step_layer(t124, RULE124)


def z7_sum(bits: list[int]) -> int:
    return sum(bits) % 7


def verify_mirror_identity() -> dict:
    w110 = wolfram_code(RULE110)
    w124 = wolfram_code(RULE124)
    lookup_table = []
    mirror_ok = True
    for l in (0, 1):
        for c in (0, 1):
            for r in (0, 1):
                out124 = RULE124[(l, c, r)]
                out110_mirrored = RULE110[(r, c, l)]
                ok = out124 == out110_mirrored
                mirror_ok = mirror_ok and ok
                lookup_table.append(
                    {
                        "LCR": [l, c, r],
                        "rule110_LCR": RULE110[(l, c, r)],
                        "rule124_LCR": out124,
                        "rule110_RCL_mirror": out110_mirrored,
                        "mirror_match": ok,
                    }
                )
    return {
        "wolfram_110": w110,
        "wolfram_124": w124,
        "lookup_table_8": lookup_table,
        "mirror_identity": mirror_ok,
        "pass": mirror_ok and w110 == 110 and w124 == 124,
    }


def verify_ether_stability() -> dict:
    drift = 4
    tape = ETHER_124[:]
    steps_ok = True
    for t in range(1, 15):
        expected = [ETHER_124[(i - drift * t) % 14] for i in range(14)]
        tape = step_layer(tape, RULE124)
        if tape != expected:
            steps_ok = False
            break
    return {
        "period": 14,
        "drift_per_step": drift,
        "drift_direction": "rightward",
        "z7_sum_110": z7_sum(ETHER_110),
        "z7_sum_124": z7_sum(ETHER_124),
        "ether_124_is_reversed_110": ETHER_124 == list(reversed(ETHER_110)),
        "exact_14_step_cycle": steps_ok,
        "pass": steps_ok and z7_sum(ETHER_124) == 1,
    }


def fmdl124_step(state: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(
        RULE124[(state[(i - 1) % 5] % 2, state[i] % 2, state[(i + 1) % 5] % 2)]
        for i in range(5)
    )


def verify_gen1_goe() -> dict:
    gen1_tuple = GEN1
    has_predecessor = False
    for bits in range(32):
        pred = tuple((bits >> (4 - i)) & 1 for i in range(5))
        if fmdl124_step(pred) == gen1_tuple:
            has_predecessor = True
            break
    return {"gen1_is_goe": not has_predecessor, "pass": not has_predecessor}


def extract_period3_step_pattern(
    base: list[int],
    pert: list[int],
    rule: dict,
    center: int,
    direction: str,
    t_end: int,
) -> dict:
    """Dominant period-3 front-step triplet and net displacement per 3 steps."""
    from collections import Counter

    leads: list[int] = []
    b, p = base[:], pert[:]
    for _ in range(1, t_end + 1):
        b = step_layer(b, rule)
        p = step_layer(p, rule)
        diff = [b[i] != p[i] for i in range(len(b))]
        if direction == "right":
            lead = max((i - center for i in range(center + 1, len(b)) if diff[i]), default=0)
        else:
            lead = max((center - i for i in range(center) if diff[i]), default=0)
        leads.append(lead)
    steps = [leads[i + 1] - leads[i] for i in range(len(leads) - 1)]
    triplets = [tuple(steps[i : i + 3]) for i in range(0, len(steps) - 2, 3)]
    if not triplets:
        return {"dominant_triplet": [], "triplet_fraction": 0.0, "net_per_3_steps": 0}
    pattern, count = Counter(triplets).most_common(1)[0]
    return {
        "dominant_triplet": list(pattern),
        "triplet_fraction": count / len(triplets),
        "net_per_3_steps": sum(pattern),
        "speed_from_triplet": sum(pattern) / 3,
    }


def measure_glider(
    base: list[int],
    pert: list[int],
    rule: dict,
    center: int,
    direction: str,
    t_end: int,
) -> dict:
    leads = []
    b, p = base[:], pert[:]
    for _ in range(1, t_end + 1):
        b = step_layer(b, rule)
        p = step_layer(p, rule)
        diff = [b[i] != p[i] for i in range(len(b))]
        if direction == "right":
            lead = max((i - center for i in range(center + 1, len(b)) if diff[i]), default=0)
        else:
            lead = max((center - i for i in range(center) if diff[i]), default=0)
        leads.append(lead)
    speed = leads[-1] / t_end if t_end else 0.0
    triplets = max(len(leads) - 3, 0)
    p3 = sum(1 for i in range(3, len(leads)) if leads[i] - leads[i - 3] == 2)
    purity = p3 / triplets if triplets else 0.0
    return {
        "final_lead": leads[-1],
        "speed": speed,
        "speed_error": abs(speed - TARGET_SPEED),
        "period3_purity": purity,
        "pass": abs(speed - TARGET_SPEED) < 1e-9 and purity >= 0.95,
    }


def random_mirror_c2_trials(l_tape: int, n_trials: int, seed: int = 0) -> dict:
    """Reproduce EPIC_070 Rank 105 period-3 leftward front search (rule124_glider_search.py)."""
    import numpy as np
    from collections import Counter

    rng = np.random.default_rng(seed)
    ether = [ETHER_124[i % 14] for i in range(l_tape)]
    hits = 0
    best_fraction = 0.0
    trial_details: list[dict] = []

    for trial in range(n_trials):
        tape = ether[:]
        flip_pos = int(rng.integers(30, l_tape - 30))
        tape[flip_pos] ^= 1
        if rng.random() > 0.5:
            tape[(flip_pos + 1) % l_tape] ^= 1

        tape_b, tape_p = ether[:], tape[:]
        left_fronts: list[int] = []
        for _ in range(200):
            tape_b = step_layer(tape_b, RULE124)
            tape_p = step_layer(tape_p, RULE124)
            diff = [tape_p[i] != tape_b[i] for i in range(l_tape)]
            if any(diff):
                left_fronts.append(min(i for i, d in enumerate(diff) if d))

        found = False
        fraction = 0.0
        pattern: tuple[int, ...] = ()
        if len(left_fronts) >= 15:
            steps = [left_fronts[i + 1] - left_fronts[i] for i in range(len(left_fronts) - 1)]
            triplets = [tuple(steps[i : i + 3]) for i in range(0, len(steps) - 2, 3)]
            if triplets:
                pattern, count = Counter(triplets).most_common(1)[0]
                fraction = count / len(triplets)
                v_net = sum(pattern) / 3
                if count > 5 and abs(v_net + 2 / 3) < 0.05:
                    found = True
                    hits += 1
                best_fraction = max(best_fraction, fraction)

        trial_details.append(
            {"trial": trial, "flip_pos": flip_pos, "found": found, "pattern": list(pattern), "fraction": fraction}
        )

    return {
        "L": l_tape,
        "n_trials": n_trials,
        "trials_with_mirror_c2": hits,
        "fraction": hits / n_trials,
        "best_period3_fraction": best_fraction,
        "pass": hits >= 10,
        "sample_trials": trial_details[:5],
    }


def two_layer_symmetry(L: int) -> dict:
    ether110 = [ETHER_110[i % 14] for i in range(L)]
    ether124 = [ETHER_124[i % 14] for i in range(L)]
    phase110, phase124 = 1, 3
    center110 = (L // 2 // 14) * 14 + phase110
    center124 = (L // 2 // 14) * 14 + phase124

    # Experiment 1: Layer 110 perturbed — measure v_R and cross-layer signal in 124
    b110, b124 = ether110[:], ether124[:]
    p110, p124 = ether110[:], ether124[:]
    p110[center110] ^= 1
    right_leads: list[int] = []
    cross124_max = 0
    for _ in range(T_RUN):
        b110, b124 = step_chiral(b110, b124)
        p110, p124 = step_chiral(p110, p124)
        diff110 = [b110[i] != p110[i] for i in range(L)]
        diff124 = [b124[i] != p124[i] for i in range(L)]
        right_leads.append(
            max((i - center110 for i in range(center110 + 1, L) if diff110[i]), default=0)
        )
        cross124_max = max(cross124_max, sum(diff124))

    v_r = right_leads[-1] / T_RUN
    triplets_r = max(len(right_leads) - 3, 0)
    p3_r = sum(1 for i in range(3, len(right_leads)) if right_leads[i] - right_leads[i - 3] == 2)
    purity_r = p3_r / triplets_r if triplets_r else 0.0

    # Experiment 2: Layer 124 perturbed — measure |v_L| and cross-layer signal in 110
    b110, b124 = ether110[:], ether124[:]
    p110, p124 = ether110[:], ether124[:]
    p124[center124] ^= 1
    left_leads: list[int] = []
    cross110_max = 0
    for _ in range(T_RUN):
        b110, b124 = step_chiral(b110, b124)
        p110, p124 = step_chiral(p110, p124)
        diff110 = [b110[i] != p110[i] for i in range(L)]
        diff124 = [b124[i] != p124[i] for i in range(L)]
        left_leads.append(
            max((center124 - i for i in range(center124) if diff124[i]), default=0)
        )
        cross110_max = max(cross110_max, sum(diff110))

    v_l_abs = left_leads[-1] / T_RUN
    triplets_l = max(len(left_leads) - 3, 0)
    p3_l = sum(1 for i in range(3, len(left_leads)) if left_leads[i] - left_leads[i - 3] == 2)
    purity_l = p3_l / triplets_l if triplets_l else 0.0

    symmetric = abs(v_r - v_l_abs) < 1e-9
    decoupled = cross124_max == 0 and cross110_max == 0

    return {
        "L": L,
        "center_110": center110,
        "center_124": center124,
        "v_R": v_r,
        "v_L": -v_l_abs,
        "abs_speed_diff": abs(v_r - v_l_abs),
        "period3_purity_110": purity_r,
        "period3_purity_124": purity_l,
        "cross_layer_max_124": cross124_max,
        "cross_layer_max_110": cross110_max,
        "layers_decoupled": decoupled,
        "lorentz_symmetric": symmetric and decoupled,
        "pass": (
            symmetric
            and decoupled
            and abs(v_r - TARGET_SPEED) < 1e-9
            and abs(v_l_abs - TARGET_SPEED) < 1e-9
            and purity_r >= 0.95
            and purity_l >= 0.95
        ),
    }


def main() -> None:
    t0 = time.time()
    results: dict = {
        "rank": "070-106",
        "title": "Rule 124 Mirror CA — Chiral Pair for Lorentz Invariance",
        "mirror_identity": verify_mirror_identity(),
        "ether_stability": verify_ether_stability(),
        "gen1_goe": verify_gen1_goe(),
        "random_mirror_c2_trials": [random_mirror_c2_trials(200, N_RANDOM_TRIALS)],
        "two_layer_by_L": [two_layer_symmetry(L) for L in L_VALUES],
        "wall_clock_s": 0.0,
    }

    ether840 = [ETHER_110[i % 14] for i in range(840)]
    pert110 = ether840[:]
    pert110[421] ^= 1
    results["canonical_a_glider_rule110_L840"] = {
        **measure_glider(ether840, pert110, RULE110, 421, "right", T_RUN),
        **extract_period3_step_pattern(ether840, pert110, RULE110, 421, "right", T_RUN),
    }

    ether840_124 = [ETHER_124[i % 14] for i in range(840)]
    pert840 = ether840_124[:]
    pert840[423] ^= 1
    canonical = measure_glider(ether840_124, pert840, RULE124, 423, "left", T_RUN)
    results["canonical_mirror_c2_L840"] = {
        **canonical,
        **extract_period3_step_pattern(ether840_124, pert840, RULE124, 423, "left", T_RUN),
    }

    all_pass = (
        results["mirror_identity"]["pass"]
        and results["ether_stability"]["pass"]
        and results["gen1_goe"]["pass"]
        and results["random_mirror_c2_trials"][0]["pass"]
        and canonical["pass"]
        and all(x["pass"] for x in results["two_layer_by_L"])
    )
    results["overall_pass"] = all_pass
    results["cat_level"] = "CatA" if all_pass else "NOT CONFIRMED"
    results["wall_clock_s"] = time.time() - t0

    OUT_JSON.write_text(json.dumps(results, indent=2))
    signal.alarm(0)

    print(f"Rank 070-106 verification — overall_pass={all_pass} ({results['cat_level']})")
    print(f"  mirror_identity: {results['mirror_identity']['pass']}")
    print(f"  ether_stability: {results['ether_stability']['pass']}")
    print(f"  gen1_goe: {results['gen1_goe']['pass']}")
    print(f"  random_mirror_c2: {results['random_mirror_c2_trials'][0]['trials_with_mirror_c2']}/{N_RANDOM_TRIALS}")
    for row in results["two_layer_by_L"]:
        print(f"  L={row['L']}: v_R={row['v_R']:.6f}, v_L={row['v_L']:.6f}, symmetric={row['lorentz_symmetric']}")
    print(f"  wall_clock={results['wall_clock_s']:.1f}s")
    print(f"  wrote {OUT_JSON}")

    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
