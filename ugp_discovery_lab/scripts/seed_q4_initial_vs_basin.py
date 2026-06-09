"""
seed_q4_initial_vs_basin.py — COMP-P04-B
=========================================
Compute Q4 at step 0 (seed initialization) for each seed in the deep-trajectory
study and compare to final basin assignment.

Q4 = log(|a|+1) + log(|b|+1) + log(|c|+1)

If seed-initial Q4 separates basins: Q4 is a genuine predictive invariant.
If not: Q4 is a trajectory-average label (post-hoc characterization).

Output: ugp_discovery_lab/UGP_discovery_lab_runs/exp_holographic_gte/results/seed_q4_initial_report.json
"""

from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEEP_TRAJ_JSON = (
    REPO_ROOT
    / "ugp_discovery_lab"
    / "UGP_discovery_lab_runs"
    / "exp_20260413_deep_trajectories"
    / "results"
    / "reports"
    / "experiment_results.json"
)
OUT_DIR = (
    REPO_ROOT
    / "ugp_discovery_lab"
    / "UGP_discovery_lab_runs"
    / "exp_holographic_gte"
    / "results"
)


def _q4(a, b, c) -> float:
    try:
        return math.log(abs(int(a)) + 1) + math.log(abs(int(b)) + 1) + math.log(abs(int(c)) + 1)
    except Exception:
        return float("nan")


def _q4_traj_mean(evo: List[dict]) -> float:
    vals = [_q4(e["a"], e["b"], e["c"]) for e in evo if e.get("step_type") != "initial"]
    valid = [v for v in vals if not math.isnan(v)]
    if not valid:
        return float("nan")
    return sum(valid) / len(valid)


def main():
    print("COMP-P04-B: Seed-initial Q4 vs basin assignment")
    print(f"Loading: {DEEP_TRAJ_JSON}")

    if not DEEP_TRAJ_JSON.exists():
        raise FileNotFoundError(f"Deep trajectory data not found at:\n  {DEEP_TRAJ_JSON}")

    raw = json.loads(DEEP_TRAJ_JSON.read_text())
    results_list = raw.get("data", raw).get("results", [])
    print(f"  {len(results_list)} trajectory entries.")

    records = []
    for entry in results_list:
        if not entry.get("success", True):
            continue
        evo   = entry.get("evolution_history", [])
        basin = entry.get("basin", "?")
        seed  = entry.get("seed", [])
        if not evo:
            continue

        # Step 0 = seed initialization
        step0 = evo[0]
        q4_initial = _q4(step0["a"], step0["b"], step0["c"])

        # Also compute trajectory-averaged Q4 for comparison
        q4_traj_avg = _q4_traj_mean(evo)

        rec = {
            "seed": seed,
            "basin": basin,
            "q4_initial": q4_initial,
            "q4_traj_avg": q4_traj_avg,
            "step0": {"a": step0["a"], "b": step0["b"], "c": step0["c"]},
        }
        records.append(rec)
        print(f"  seed={seed}  basin={basin}  Q4_initial={q4_initial:.4f}  Q4_avg={q4_traj_avg:.4f}")

    # Group by basin
    basin_q4_init: Dict[str, List[float]] = {}
    for r in records:
        b = r["basin"]
        v = r["q4_initial"]
        if not math.isnan(v):
            basin_q4_init.setdefault(b, []).append(v)

    basin_stats = {}
    for b, vals in sorted(basin_q4_init.items()):
        mu = sum(vals) / len(vals)
        variance = sum((x - mu) ** 2 for x in vals) / max(1, len(vals) - 1)
        basin_stats[b] = {
            "n": len(vals),
            "mean_q4_initial": mu,
            "std_q4_initial": variance ** 0.5,
            "values": vals,
        }

    # Statistical test: do basins differ at seed initialization?
    all_basins = sorted(basin_q4_init.keys())
    separates = False
    anova_p = None
    anova_note = "insufficient groups or samples for ANOVA"

    if HAS_SCIPY and HAS_NUMPY and len(all_basins) >= 2:
        groups = [basin_q4_init[b] for b in all_basins if len(basin_q4_init[b]) >= 2]
        if len(groups) >= 2:
            try:
                if len(groups) >= 3:
                    stat, p = scipy_stats.f_oneway(*groups)
                else:
                    stat, p = scipy_stats.mannwhitneyu(groups[0], groups[1],
                                                        alternative="two-sided")
                anova_p = float(p)
                separates = anova_p < 0.05
                anova_note = (f"One-way ANOVA / Mann-Whitney p = {anova_p:.4f} "
                              f"({'separates' if separates else 'does not separate'} basins at α=0.05)")
            except Exception as e:
                anova_note = f"Test failed: {e}"

    if separates:
        claim = "PREDICTIVE_INVARIANT"
        verdict = (
            f"Q4 computed at seed initialization separates basin assignments "
            f"(p={anova_p:.4f} < 0.05). Q4 is a genuine predictive invariant: "
            f"the seed's arithmetic complexity predicts its dynamical fate."
        )
    else:
        claim = "POST_HOC_LABEL"
        verdict = (
            f"Q4 at seed initialization does NOT statistically separate basin "
            f"assignments ({anova_note}). Q4 should be framed as a trajectory-averaged "
            f"basin label, not a seed-level predictor."
        )

    print(f"\nBasin Q4 (initial) stats: {basin_stats}")
    print(f"\nRESULT: {claim}")
    print(f"Verdict: {verdict}")

    output = {
        "experiment": "COMP-P04-B: seed_q4_initial_vs_basin",
        "date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_trajectories": len(records),
        "basin_stats_initial_q4": basin_stats,
        "statistical_test": anova_note,
        "anova_p": anova_p,
        "separates_basins": separates,
        "claim": claim,
        "verdict": verdict,
        "per_trajectory": records,
    }

    payload = json.dumps(output, sort_keys=True).encode()
    output["sha256"] = hashlib.sha256(payload).hexdigest()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "seed_q4_initial_report.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nOutput written to: {out_path}")
    print(f"SHA-256: {output['sha256']}")


if __name__ == "__main__":
    main()
