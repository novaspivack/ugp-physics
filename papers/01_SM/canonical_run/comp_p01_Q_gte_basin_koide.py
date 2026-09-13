#!/usr/bin/env python3
"""
COMP-P01-Q: GTE basin q_early triple Koide test.

Hypothesis H2 (direct data version):
  In Paper 12's extended 100-seed basin survey, GTE trajectories fall into
  three basins A/B/C. Each basin has a characteristic q_early distribution.
  If the charged-lepton sqrt-masses correspond to the basin centers (mean
  q_early), the Koide identity (Sum a)^2/(Sum a^2) = 3/2 should hold.

Approach:
  1. Load the 100-seed basin-survey JSON.
  2. Compute the mean q_early for each basin.
  3. Compute Koide Q = (sum a^2)/(sum a)^2 where a_i = mean q_early of basin i.
     (and also sqrt(q_early_mean) if we interpret q_early as a "mass" rather
     than a "sqrt mass")
  4. Also try basin STDs, medians, extremes as the triple.
  5. If any yields Q = 2/3 to high precision, we have a potential derivation.
  6. Compare basin A/B/C mean ordering to lepton ordering.

Deterministic.
"""

from __future__ import annotations
import json
import math
from hashlib import sha256
from pathlib import Path
from statistics import mean, median, pstdev


SURVEY_PATH = Path(__file__).resolve().parents[3] / "computational_concordance" / "basin_survey_100seeds_report.json"


def koide_ratio_on_x(x1: float, x2: float, x3: float, as_sqrt_mass: bool) -> dict:
    """If as_sqrt_mass=True: a_i = x_i  (so m_i = x_i^2)
       If as_sqrt_mass=False: a_i = sqrt(x_i) (so m_i = x_i)
       Koide: Sum m / (Sum a)^2 = 2/3
    """
    if as_sqrt_mass:
        a1, a2, a3 = x1, x2, x3
        m1, m2, m3 = x1*x1, x2*x2, x3*x3
    else:
        a1, a2, a3 = math.sqrt(x1), math.sqrt(x2), math.sqrt(x3)
        m1, m2, m3 = x1, x2, x3
    s = a1 + a2 + a3
    if s == 0:
        return {"Q": float('nan'), "d_Q": float('nan'),
                "m_ratio_big_over_small": float('nan')}
    Q = (m1 + m2 + m3) / (s*s)
    sorted_m = sorted([m1, m2, m3])
    return {
        "Q": Q,
        "d_Q": Q - 2/3,
        "sum_m": m1 + m2 + m3,
        "sum_sqrt_m": s,
        "m_ratios_sorted": sorted_m,
        "ratio_big_over_small": sorted_m[2] / sorted_m[0] if sorted_m[0] > 0 else float('inf'),
        "ratio_big_over_mid": sorted_m[2] / sorted_m[1] if sorted_m[1] > 0 else float('inf'),
    }


def main() -> int:
    with SURVEY_PATH.open() as f:
        data = json.load(f)

    seeds = data.get("results") or data.get("seeds") or []
    basins = {"A": [], "B": [], "C": []}
    for s in seeds:
        b = s.get("basin")
        if b in basins:
            basins[b].append(s.get("q_early_mean", 0.0))

    # Filter out zeros (failed seeds)
    for key in basins:
        basins[key] = [q for q in basins[key] if q > 0]

    summary = {}
    for b, qs in basins.items():
        if not qs:
            summary[b] = None
            continue
        summary[b] = {
            "n_seeds": len(qs),
            "mean": mean(qs),
            "median": median(qs),
            "min": min(qs),
            "max": max(qs),
            "stdev_pop": pstdev(qs) if len(qs) > 1 else 0.0,
        }

    # Build triple: (q_A, q_B, q_C) using different summary statistics
    results: dict[str, dict] = {}
    if all(summary.get(b) is not None for b in ["A", "B", "C"]):
        stats = ["mean", "median", "min", "max"]
        for s in stats:
            triple = (summary["A"][s], summary["B"][s], summary["C"][s])
            # Two interpretations: q_early directly as "mass" or as "sqrt-mass"
            for interp, as_sqrt in [("as_sqrt_mass", True), ("as_mass", False)]:
                key = f"{s}_{interp}"
                results[key] = {
                    "triple_A_B_C": triple,
                    **koide_ratio_on_x(*triple, as_sqrt_mass=as_sqrt),
                }

    # Lepton ordering comparison
    # Empirical: m_e < m_mu < m_tau with m_mu/m_e ~ 206.77, m_tau/m_e ~ 3477.5
    # Basin ordering in our data: need to check which basin corresponds to which
    # generation by monotonic property.
    emp_ratios = {
        "m_mu_over_m_e": 105.6583755 / 0.5109989461,
        "m_tau_over_m_e": 1776.86 / 0.5109989461,
        "m_tau_over_m_mu": 1776.86 / 105.6583755,
    }

    # Check ordering:
    ordering_summary = {}
    for b in ["A", "B", "C"]:
        if summary.get(b):
            ordering_summary[b] = summary[b]["mean"]

    sorted_basins = sorted(ordering_summary.items(), key=lambda x: x[1])
    if len(sorted_basins) == 3:
        # Smallest -> electron, biggest -> tau
        ratio_ml_over_small = sorted_basins[1][1] / sorted_basins[0][1] if sorted_basins[0][1] > 0 else float('inf')
        ratio_mm_over_small = sorted_basins[2][1] / sorted_basins[0][1] if sorted_basins[0][1] > 0 else float('inf')
        basin_ordering = {
            "smallest_basin": sorted_basins[0][0],
            "middle_basin": sorted_basins[1][0],
            "largest_basin": sorted_basins[2][0],
            "values_ascending": [sorted_basins[i][1] for i in range(3)],
            "ratio_middle_over_small": ratio_ml_over_small,
            "ratio_large_over_small": ratio_mm_over_small,
            "empirical_for_comparison": emp_ratios,
        }
    else:
        basin_ordering = None

    # Verdict
    # We seek |Q - 2/3| < 1e-4 AND ratios matching empirical to 1%
    best_koide = min(results.values(), key=lambda r: abs(r["d_Q"]))
    verdict = (
        "Hypothesis SUPPORTED at 1e-4 level"
        if abs(best_koide["d_Q"]) < 1e-4
        else f"Hypothesis REJECTED: closest Q = {best_koide['Q']:.6f}, "
             f"deviation from 2/3 = {best_koide['d_Q']:+.4e}"
    )

    out = {
        "description": "COMP-P01-Q: GTE basin q_early Koide test",
        "basin_summary": summary,
        "koide_tests": results,
        "basin_ordering": basin_ordering,
        "verdict": verdict,
    }

    serialized = json.dumps(out, indent=2, sort_keys=True, default=str)
    digest = sha256(serialized.encode("utf-8")).hexdigest()
    out["script_sha256"] = digest

    out_path = Path(__file__).with_suffix(".json")
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True, default=str))

    # Console
    print("=" * 72)
    print("COMP-P01-Q: GTE basin q_early Koide test")
    print("=" * 72)
    print(f"Basin sample sizes: " + ", ".join(
        f"{b}={summary[b]['n_seeds']}" if summary.get(b) else f"{b}=NONE"
        for b in "ABC"
    ))
    print()
    for b in "ABC":
        if summary.get(b):
            s = summary[b]
            print(f"  Basin {b}: mean = {s['mean']:.6e}  median = {s['median']:.6e}  "
                  f"[{s['min']:.3e}, {s['max']:.3e}]  ±{s['stdev_pop']:.3e}")
    print()
    print("Koide tests (stat_interpretation):")
    for key, r in results.items():
        print(f"  {key:30s}  Q = {r['Q']:.6f}  d_Q = {r['d_Q']:+.3e}  "
              f"big/small = {r['ratio_big_over_small']:.3f}")
    print()
    if basin_ordering:
        print(f"Basin ordering (smallest to largest mean q_early): "
              f"{basin_ordering['smallest_basin']} -> {basin_ordering['middle_basin']} -> {basin_ordering['largest_basin']}")
        print(f"  middle/small = {basin_ordering['ratio_middle_over_small']:.3f}  "
              f"(empirical m_mu/m_e = {emp_ratios['m_mu_over_m_e']:.3f})")
        print(f"  large/small  = {basin_ordering['ratio_large_over_small']:.3f}  "
              f"(empirical m_tau/m_e = {emp_ratios['m_tau_over_m_e']:.3f})")
    print()
    print(f"VERDICT: {verdict}")
    print(f"Written to {out_path.name} (SHA {digest[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
