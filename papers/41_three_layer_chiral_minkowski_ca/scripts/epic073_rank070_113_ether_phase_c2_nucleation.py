#!/usr/bin/env python3
"""
EPIC_073 Rank 070-113: Ether-phase C2 nucleation survey (Rule 110 + Rule 124)

Exhaustive classification of which ether phases (0..13) support persistent C2 /
mirror-C2 gliders from a single-bit perturbation on periodic ether backgrounds.

Method: base-vs-perturbed difference (same as rule110_rule124_chiral_pair.py).
Robustness: three tape lengths L ∈ {560, 840, 1260} (all multiples of 14).

Pass criteria for PERSISTENT_C2:
  |v − 2/3| < 0.01, period-3 purity ≥ 0.95, lead still growing at T_end.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import asdict, dataclass
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

TARGET_SPEED = 2 / 3
T_RUN = 300
T_MID = 150
L_VALUES = [560, 840, 1260]

OUT_JSON = Path(__file__).with_name("epic073_rank070_113_ether_phase_c2_nucleation_results.json")


@dataclass
class PhaseResult:
    layer: str
    L: int
    phase: int
    center: int
    final_lead: int
    mid_lead: int
    speed: float
    speed_error: float
    period3_purity: float
    classification: str
    ether_triple: list[int]
    z7_phase: int
    mirror_phase: int


def step_layer(tape: list[int], rule: dict) -> list[int]:
    n = len(tape)
    return [rule[(tape[(i - 1) % n], tape[i], tape[(i + 1) % n])] for i in range(n)]


def center_for_phase(L: int, phase: int) -> int:
    """Place perturbation near tape midpoint to avoid periodic wrap-around in lead tracking."""
    mid = L // 2
    offset = (phase - mid % 14) % 14
    if offset > 7:
        offset -= 14
    center = mid + offset
    assert center % 14 == phase and 0 <= center < L
    return center


def measure_phase(
    rule: dict,
    ether_pattern: list[int],
    L: int,
    phase: int,
    direction: str,
) -> PhaseResult:
    """Single-bit flip at midpoint-aligned cell with i % 14 == phase."""
    center = center_for_phase(L, phase)
    base = [ether_pattern[i % 14] for i in range(L)]
    pert = base[:]
    pert[center] ^= 1

    leads: list[int] = []
    for _t in range(1, T_RUN + 1):
        base = step_layer(base, rule)
        pert = step_layer(pert, rule)
        diff = [base[i] != pert[i] for i in range(L)]
        if direction == "right":
            lead = max((i - center for i in range(center + 1, L) if diff[i]), default=0)
        else:
            lead = max((center - i for i in range(0, center) if diff[i]), default=0)
        leads.append(lead)

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
    elif final_lead <= 5 or (mid_lead > 20 and final_lead < mid_lead * 0.5):
        classification = "TRANSIENT"
    elif growing and speed_error < 0.05:
        classification = "WEAK_PROPAGATING"
    else:
        classification = "OTHER"

    triple = [
        ether_pattern[(phase - 1) % 14],
        ether_pattern[phase % 14],
        ether_pattern[(phase + 1) % 14],
    ]

    return PhaseResult(
        layer="110" if direction == "right" else "124",
        L=L,
        phase=phase,
        center=center,
        final_lead=final_lead,
        mid_lead=mid_lead,
        speed=speed,
        speed_error=speed_error,
        period3_purity=purity,
        classification=classification,
        ether_triple=triple,
        z7_phase=phase % 7,
        mirror_phase=(13 - phase) % 14,
    )


def summarize_layer(results: list[PhaseResult], L: int, layer: str) -> dict:
    subset = [r for r in results if r.L == L and r.layer == layer]
    persistent = sorted(r.phase for r in subset if r.classification == "PERSISTENT_C2")
    z7_persistent = sorted({r.z7_phase for r in subset if r.classification == "PERSISTENT_C2"})
    return {
        "L": L,
        "layer": layer,
        "persistent_phases": persistent,
        "persistent_z7_residues": z7_persistent,
        "n_persistent": len(persistent),
        "by_phase": {r.phase: r.classification for r in subset},
    }


def mirror_consistency(results: list[PhaseResult], L: int) -> dict:
    """Check Rule 124 phase p works iff Rule 110 phase (13-p) works."""
    r110 = {r.phase: r.classification for r in results if r.L == L and r.layer == "110"}
    r124 = {r.phase: r.classification for r in results if r.L == L and r.layer == "124"}
    matches = []
    for p in range(14):
        c110 = r110.get((13 - p) % 14, "")
        c124 = r124.get(p, "")
        ok = (c110 == "PERSISTENT_C2") == (c124 == "PERSISTENT_C2")
        matches.append(ok)
    return {
        "L": L,
        "mirror_pairs_consistent": all(matches),
        "n_consistent": sum(matches),
        "n_total": 14,
    }


def main() -> None:
    t0 = time.time()
    all_results: list[PhaseResult] = []

    for L in L_VALUES:
        for phase in range(14):
            all_results.append(measure_phase(RULE110, ETHER_110, L, phase, "right"))
            all_results.append(measure_phase(RULE124, ETHER_124, L, phase, "left"))

    signal.alarm(0)

    summaries = []
    for L in L_VALUES:
        summaries.append(summarize_layer(all_results, L, "110"))
        summaries.append(summarize_layer(all_results, L, "124"))
        summaries.append(mirror_consistency(all_results, L))

    # Canonical L=840 summary (matches Rank 111)
    s110 = summarize_layer(all_results, 840, "110")
    s124 = summarize_layer(all_results, 840, "124")
    mirror = mirror_consistency(all_results, 840)

    # Ether triple pattern for persistent vs transient at L=840
    persistent_triples_110 = sorted(
        {tuple(r.ether_triple) for r in all_results
         if r.L == 840 and r.layer == "110" and r.classification == "PERSISTENT_C2"}
    )
    transient_triples_110 = sorted(
        {tuple(r.ether_triple) for r in all_results
         if r.L == 840 and r.layer == "110" and r.classification == "TRANSIENT"}
    )

    output = {
        "rank": "070-113",
        "T_run": T_RUN,
        "L_values": L_VALUES,
        "canonical_L840": {
            "rule110_persistent_phases": s110["persistent_phases"],
            "rule124_persistent_phases": s124["persistent_phases"],
            "rule110_z7_residues": s110["persistent_z7_residues"],
            "rule124_z7_residues": s124["persistent_z7_residues"],
            "mirror_symmetry": mirror,
            "persistent_ether_triples_110": persistent_triples_110,
            "transient_ether_triples_110_sample": transient_triples_110[:5],
        },
        "summaries": summaries,
        "results_L840": [asdict(r) for r in all_results if r.L == 840],
        "wall_clock_s": time.time() - t0,
    }

    OUT_JSON.write_text(json.dumps(output, indent=2))
    print(json.dumps(output["canonical_L840"], indent=2))
    print(f"\nWrote {OUT_JSON}")
    print(f"Wall clock: {output['wall_clock_s']:.1f}s")


if __name__ == "__main__":
    main()
