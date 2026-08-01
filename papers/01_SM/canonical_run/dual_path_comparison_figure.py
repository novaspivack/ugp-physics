#!/usr/bin/env python3
"""
dual_path_comparison_figure.py — COMP-P01-B

Produces Figure 1 for Paper 1: theoretical vs empirical UCL coefficients.

Input:  canonical_run/dual_path_comparison.json (canonical SD5 run, 2026-04-11)
Output: canonical_run/dual_path_comparison_figure.png
        canonical_run/dual_path_comparison_figure.json (numbers backing the figure)

All 9 UCL coefficients are plotted: theoretical (x, first-principles Elegant
Kernel) vs empirical (y, calibrated to data).  Perfect agreement lies on the
y=x diagonal.  Max relative deviation is 1.83 % (const); RMS is computed
below.

No new calibration; this is a visualization of the frozen canonical run.
"""
import json
import math
import os
import hashlib
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, "dual_path_comparison.json")
PNG = os.path.join(HERE, "dual_path_comparison_figure.png")
OUT = os.path.join(HERE, "dual_path_comparison_figure.json")


PRETTY = {
    "const": r"$k_{\mathrm{const}}$",
    "L": r"$k_L$",
    "L2": r"$k_{L^2}$",
    "gen": r"$k_{\mathrm{gen}}$",
    "gen2": r"$k_{\mathrm{gen}^2}$",
    "M": r"$k_M$",
    "mu_a": r"$k_{\mu_a}$",
    "mu_b": r"$k_{\mu_b}$",
    "mu_c": r"$k_{\mu_c}$",
}


def main() -> int:
    with open(INPUT) as f:
        data = json.load(f)
    rows = data["coefficient_comparison"]

    theo = [r["theoretical"] for r in rows]
    emp = [r["empirical"] for r in rows]
    names = [r["coeff"] for r in rows]
    rel = [abs(r["rel_diff_percent"]) for r in rows]

    rms = math.sqrt(sum(v * v for v in rel) / len(rel))
    max_dev = max(rel)
    max_idx = rel.index(max_dev)

    # ------------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.4, 6.0))

    lo = min(min(theo), min(emp))
    hi = max(max(theo), max(emp))
    pad = 0.08 * max(1.0, hi - lo)
    lo -= pad
    hi += pad
    ax.plot([lo, hi], [lo, hi], color="0.65", lw=1.2, ls="--",
            label=r"$y = x$ (perfect agreement)")

    sizes = [24 + 18 * math.sqrt(v) for v in rel]
    sc = ax.scatter(theo, emp, s=sizes, c=rel, cmap="viridis",
                    edgecolor="black", lw=0.6, zorder=3)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.85)
    cbar.set_label("Relative deviation (%)")

    for x, y, n in zip(theo, emp, names):
        ax.annotate(PRETTY.get(n, n), (x, y), xytext=(4, 4),
                    textcoords="offset points", fontsize=9)

    ax.set_xlabel("Theoretical coefficient (from Elegant Kernel)")
    ax.set_ylabel("Empirical coefficient (calibrated to data)")
    ax.set_title(
        "Dual-path UCL coefficient agreement "
        f"(max dev = {max_dev:.2f}% at {names[max_idx]}; RMS = {rms:.2f}%)",
        fontsize=11,
    )
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25, ls=":")
    ax.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    plt.savefig(PNG, dpi=160)
    plt.close(fig)

    # ------------------------------------------------------------------
    # Structured JSON artifact
    # ------------------------------------------------------------------
    out = {
        "description": (
            "COMP-P01-B: Dual-path UCL coefficient comparison.  Theoretical "
            "values derive from the Elegant Kernel (first principles: pi, "
            "golden ratio, small rationals); empirical values are calibrated "
            "to the SM fermion mass spectrum via the UCL2.3 frozen decimals. "
            "Perfect agreement would lie on the y=x diagonal."
        ),
        "source_json": os.path.relpath(INPUT, os.path.dirname(HERE) + "/.."),
        "coefficients": rows,
        "n": len(rows),
        "max_rel_deviation_percent": max_dev,
        "max_rel_deviation_coeff": names[max_idx],
        "rms_rel_deviation_percent": rms,
        "mean_rel_deviation_percent": sum(rel) / len(rel),
        "all_within_2_percent": all(v < 2.0 for v in rel),
        "figure_path": os.path.relpath(PNG, os.path.dirname(HERE) + "/.."),
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)

    with open(PNG, "rb") as f:
        png_sha = hashlib.sha256(f.read()).hexdigest()
    with open(OUT, "rb") as f:
        json_sha = hashlib.sha256(f.read()).hexdigest()

    print("COMP-P01-B dual-path comparison complete")
    print(f"  N coefficients:       {len(rows)}")
    print(f"  max rel deviation:    {max_dev:.3f}%  ({names[max_idx]})")
    print(f"  RMS rel deviation:    {rms:.3f}%")
    print(f"  all within 2%:        {all(v < 2.0 for v in rel)}")
    print(f"  figure: {PNG}")
    print(f"    SHA-256: {png_sha}")
    print(f"  json:   {OUT}")
    print(f"    SHA-256: {json_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
