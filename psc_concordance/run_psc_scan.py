"""
PSC Universe Scan — wrapper for the psc_concordance paper companion.

Imports the TE2.2 scan implementation from its source directory, runs the
full 20,160-universe enumeration, and saves results to psc_concordance/results/.

Primary scan code:
  MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/src/

Expected results:
  total_universes : 20160
  psc_universes   : 12   (0.06%)
  sm_rank         : 1
  D_SM            : 1.066657903568035
"""

import sys
import os
import json
import time

# Locate the TE2.2 source directories relative to this file.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
_TE22_BASE = os.path.join(
    _REPO_ROOT,
    "MFRR", "TE_2_Advanced_Explorations",
    "TE_2_2_Minimal_PSC_Universe", "src",
)
_PHASE2 = os.path.join(_TE22_BASE, "phase2_truncation")
_PHASE1 = os.path.join(_TE22_BASE, "phase1_constraints")

for _path in (_PHASE2, _PHASE1):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from te2_2_universe_enumerator import UniverseSpace, UniverseScanner  # noqa: E402


def run_scan():
    print("PSC Universe Scan")
    print("=" * 60)

    space = UniverseSpace()
    scanner = UniverseScanner(space)

    start = time.time()
    stats = scanner.scan_all(psc_only=False)
    elapsed = time.time() - start

    total = stats["total_universes"]
    psc_count = stats["psc_universes"]
    sm_rank = stats["sm_rank"]
    d_sm = stats["D_sm"]
    d_min = stats["D_min"]
    gmin = stats["global_min"]["universe"]

    print(f"Total universes:  {total}")
    print(f"PSC-passing:      {psc_count}  ({100*psc_count/total:.2f}%)")
    print(f"SM rank:          {sm_rank}")
    print(f"D_SM:             {d_sm:.6f}")
    print(f"D_min:            {d_min:.6f}")
    print(
        f"Global minimizer: d={gmin.d}, G={gmin.gauge_group}, "
        f"N_gen={gmin.n_generations}"
    )
    print(f"Elapsed:          {elapsed:.3f}s")
    print("=" * 60)

    results = {
        "total_universes": total,
        "psc_universes": psc_count,
        "D_sm": d_sm,
        "D_min": d_min,
        "sm_rank": sm_rank,
        "elapsed_seconds": elapsed,
        "throughput": total / elapsed,
        "global_minimizer": {
            "d": gmin.d,
            "gauge_group": gmin.gauge_group,
            "n_generations": gmin.n_generations,
            "n_observers": gmin.n_observers,
            "Lambda": gmin.Lambda,
            "profit_ratio": gmin.profit_ratio,
            "kappa": gmin.kappa,
            "topology": gmin.topology,
            "D": stats["global_min"]["D"],
            "is_psc": stats["global_min"]["is_psc"],
        },
        "top_10": [
            {
                "d": r["universe"].d,
                "gauge_group": r["universe"].gauge_group,
                "n_generations": r["universe"].n_generations,
                "n_observers": r["universe"].n_observers,
                "Lambda": r["universe"].Lambda,
                "profit_ratio": r["universe"].profit_ratio,
                "kappa": r["universe"].kappa,
                "topology": r["universe"].topology,
                "D": r["D"],
                "is_psc": r["is_psc"],
            }
            for r in stats["all_results"][:10]
        ],
    }

    results_dir = os.path.join(_HERE, "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "psc_scan_results.json")
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"Results saved to: {out_path}")
    return results


if __name__ == "__main__":
    run_scan()
