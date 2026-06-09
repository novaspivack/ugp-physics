#!/usr/bin/env python3
"""
Rank 070-110 — f_MDL max orbit depth = ether temporal period = 7 (Z₇ structural identity).

Verifies:
  1. Maximum fmdl_step5 decay depth over Z₇⁵ = 7 (16,807 states)
  2. Ether temporal period = spatial_period / gcd(drift, spatial) = 14/2 = 7
  3. Both equal z7_order = 7

Outputs: epic073_rank070_110_orbit_depth_ether_period_results.json
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time
from itertools import product
from pathlib import Path

TIMEOUT_SECONDS = 120


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# f_MDL lookup (matches CUP3DUniqueness.lean / fmdl_decay_depth.py)
_FMDL_LOOKUP = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}

VACUUM = (0, 0, 0, 0, 0)
Z7_ORDER = 7
ETHER_SPATIAL_PERIOD = 14
ETHER_DRIFT_PER_STEP = 4


def fmdl(l: int, c: int, r: int) -> int:
    return _FMDL_LOOKUP.get((l, c, r), 0)


def fmdl_step5(cells: tuple) -> tuple:
    n = 5
    return tuple(fmdl(cells[(i + 4) % n], cells[i], cells[(i + 1) % n]) for i in range(n))


def decay_depth(state: tuple, max_steps: int = 10) -> int:
    if state == VACUUM:
        return 0
    current = state
    for step in range(1, max_steps + 1):
        current = fmdl_step5(current)
        if current == VACUUM:
            return step
    return max_steps


def max_fmdl_decay_depth() -> tuple[int, dict[int, int], list[tuple]]:
    depth_hist: dict[int, int] = {}
    max_depth = 0
    witnesses: list[tuple] = []
    for cells in product(range(7), repeat=5):
        d = decay_depth(cells, max_steps=10)
        depth_hist[d] = depth_hist.get(d, 0) + 1
        if d > max_depth:
            max_depth = d
            witnesses = [cells]
        elif d == max_depth and d > 0:
            witnesses.append(cells)
    return max_depth, depth_hist, witnesses[:5]


def ether_temporal_period(spatial: int, drift: int) -> int:
    return spatial // math.gcd(drift, spatial)


def main() -> None:
    t0 = time.time()
    max_depth, depth_hist, witnesses = max_fmdl_decay_depth()
    t_ether = ether_temporal_period(ETHER_SPATIAL_PERIOD, ETHER_DRIFT_PER_STEP)
    gcd_drift_spatial = math.gcd(ETHER_DRIFT_PER_STEP, ETHER_SPATIAL_PERIOD)

    identity_holds = (
        max_depth == Z7_ORDER
        and t_ether == Z7_ORDER
        and max_depth == t_ether
    )

    results = {
        "rank": "070-110",
        "title": "Orbit depth bound = ether temporal period = |Z7|",
        "z7_order": Z7_ORDER,
        "fmdl_max_decay_depth": max_depth,
        "fmdl_state_space": 7 ** 5,
        "fmdl_depth_histogram": {str(k): v for k, v in sorted(depth_hist.items())},
        "fmdl_depth7_witness_sample": [list(w) for w in witnesses],
        "ether_spatial_period": ETHER_SPATIAL_PERIOD,
        "ether_drift_per_step": ETHER_DRIFT_PER_STEP,
        "gcd_drift_spatial": gcd_drift_spatial,
        "ether_temporal_period": t_ether,
        "structural_identity_holds": identity_holds,
        "cat_level": "CatAL" if identity_holds else "NOT_CONFIRMED",
        "runtime_seconds": time.time() - t0,
    }

    out_path = Path(__file__).resolve().parent / "epic073_rank070_110_orbit_depth_ether_period_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}")

    signal.alarm(0)
    if not identity_holds:
        sys.exit(1)


if __name__ == "__main__":
    main()
