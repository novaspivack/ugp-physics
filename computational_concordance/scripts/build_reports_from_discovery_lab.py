#!/usr/bin/env python3
"""
Regenerate basin / perturbation summaries from frozen ugp_discovery_lab JSON exports.

Inputs (paths relative to ugp-physics repository root):
  - ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json
  - ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260412_rg_sweep_full/results/reports/experiment_results.json

Outputs (under computational_concordance/):
  - canonical_seed_basin_report.json
  - generated/run_manifest.json (hashes + counts)
  - figures/three_filters_one_survivor.png

Run from repo root:  python3 computational_concordance/scripts/build_reports_from_discovery_lab.py
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _mean_abs_q_early(eh: list[dict], n: int = 5000) -> float | None:
    qs = []
    for row in eh[1 : min(n + 1, len(eh))]:
        q = row.get("q")
        if q is not None:
            qs.append(abs(float(q)))
    return statistics.mean(qs) if qs else None


def main() -> int:
    root = _repo_root()
    out_dir = root / "computational_concordance"
    gen_dir = out_dir / "generated"
    fig_dir = out_dir / "figures"
    gen_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    deep_path = (
        root
        / "ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json"
    )
    rg_path = (
        root
        / "ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260412_rg_sweep_full/results/reports/experiment_results.json"
    )

    if not deep_path.is_file():
        print("Missing deep trajectory export:", deep_path, file=sys.stderr)
        return 1
    if not rg_path.is_file():
        print("Missing RG sweep export:", rg_path, file=sys.stderr)
        return 1

    deep_sha = _sha256_file(deep_path)
    rg_sha = _sha256_file(rg_path)

    with deep_path.open() as f:
        deep_doc = json.load(f)
    with rg_path.open() as f:
        rg_doc = json.load(f)

    deep_results = deep_doc["data"]["results"]
    rg_results = rg_doc["data"]["results"]

    # --- Deep trajectories: basin + early |q| proxy ---
    rows = []
    for t in deep_results:
        seed = t["seed"]
        eh = t.get("evolution_history") or []
        rows.append(
            {
                "task_id": t["task_id"],
                "seed": seed,
                "basin": t.get("basin"),
                "window": t.get("window"),
                "law": t.get("law"),
                "steps": len(eh),
                "q_early_mean_abs": _mean_abs_q_early(eh),
            }
        )

    df = pd.DataFrame(rows)
    canon = df[df["seed"].apply(lambda s: tuple(s) == (1, 73, 823))]
    mirror = df[df["seed"].apply(lambda s: tuple(s) == (1, 73, 2137))]
    other = df[~df["seed"].apply(lambda s: tuple(s) in ((1, 73, 823), (1, 73, 2137)))]

    stability = []
    for w in sorted(df["window"].unique()):
        sub = canon[canon["window"] == w]
        if len(sub) == 0:
            continue
        stability.append(
            {
                "window_size": int(w),
                "basin_assignment": sub["basin"].iloc[0],
                "q_early_mean_abs_pool": float(sub["q_early_mean_abs"].mean()),
                "n_laws": int(len(sub)),
            }
        )

    basin_counts_canon = Counter(canon["basin"].tolist())
    basin_counts_all = Counter(df["basin"].tolist())

    nearby_comparison = []
    for seed_s, label in [
        ([1, 73, 2137], "mirror_c_slot"),
        ([2, 89, 1597], "off_residual_seed_2"),
        ([3, 97, 2203], "off_residual_seed_3"),
    ]:
        sub = df[df["seed"].apply(lambda s: s == seed_s)]
        if len(sub) == 0:
            continue
        nearby_comparison.append(
            {
                "seed": seed_s,
                "label": label,
                "basin_counts": dict(Counter(sub["basin"].tolist())),
                "same_basin_as_canonical_lepton": bool(
                    set(sub["basin"].unique()) == set(canon["basin"].unique())
                    and len(set(canon["basin"].unique())) == 1
                ),
                "q_early_mean_abs_mean": float(sub["q_early_mean_abs"].mean()),
            }
        )

    report = {
        "study_description": (
            "Basin concordance from exp_20260413_deep_trajectories (50k-step GTE trajectories). "
            "Basin labels A/B/C are taken from the experiment export. "
            "q_early_mean_abs is a reproducible proxy: mean of |q| over evolution steps 1..5000 "
            "(step-0 initial rows excluded)."
        ),
        "canonical_seed": [1, 73, 823],
        "source_exports": {
            "deep_trajectories_json": str(deep_path.relative_to(root)),
            "deep_trajectories_sha256": deep_sha,
            "rg_sweep_json": str(rg_path.relative_to(root)),
            "rg_sweep_sha256": rg_sha,
            "deep_provenance": deep_doc.get("provenance"),
            "rg_provenance": rg_doc.get("provenance"),
        },
        "canonical_seed_basin_assignment": {
            "basin_id": canon["basin"].mode().iloc[0] if len(canon) else None,
            "basin_counts_across_runs": dict(basin_counts_canon),
            "q4_proxy": {
                "name": "q_early_mean_abs",
                "value_pooled_canonical": float(canon["q_early_mean_abs"].mean())
                if len(canon)
                else None,
                "interpretation": "Empirical complexity proxy from exported GTE q-traces; not identical to paper Q4 definition — align symbols in final manuscript.",
            },
            "stability_across_window_sizes": stability,
        },
        "global_basin_counts_all_tasks": dict(basin_counts_all),
        "nearby_seed_comparison": nearby_comparison,
        "nearby_law_policy_comparison": [],
        "conclusion": (
            "For the tested law/window grid, seeds (1,73,823) and (1,73,2137) land in basin A; "
            "seeds (2,89,1597) land in C and (3,97,2203) in B — deterministic basin assignment "
            "separates canonical-family seeds from the off-residual probes in this export."
        ),
        "finite_range_caveat": (
            "Finite experiment grid: 4 seeds × 3 laws × 2 windows; 50k steps; laws are mersenne_fib, "
            "mersenne_lucas, repunit_fib as exported."
        ),
    }

    (out_dir / "canonical_seed_basin_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=False) + "\n"
    )

    # --- RG sweep: fixed-point alpha dispersion by seed ---
    rg_by = defaultdict(list)
    for t in rg_results:
        seed = tuple(t["seeds"])
        fp = (t.get("analysis") or {}).get("fixed_point") or {}
        a = fp.get("alpha")
        if a is not None:
            rg_by[seed].append(float(a))

    rg_summary = {
        str(k): {"n": len(v), "alpha_mean": statistics.mean(v), "alpha_stdev": statistics.stdev(v) if len(v) > 1 else 0.0}
        for k, v in rg_by.items()
    }

    manifest = {
        "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "inputs": {"deep_sha256": deep_sha, "rg_sha256": rg_sha},
        "deep_tasks": len(deep_results),
        "rg_tasks": len(rg_results),
        "rg_alpha_by_seed": rg_summary,
    }
    (gen_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # --- Figure: candidate × filter survival (illustrative, from master table) ---
    tbl = pd.read_csv(out_dir / "master_concordance_table.csv")
    # Normalize PASS/TRUE -> 1, else 0 for numeric columns
    cols = [
        "psc_layer_I",
        "psc_layer_II",
        "ugp_arith_sieve",
        "ugp_phys_filter",
        "canonical_attractor_basin",
        "canonical_orbit_preserved",
    ]
    mat = []
    labels = []
    for _, row in tbl.iterrows():
        labels.append(row["candidate_id"][:28])
        r = []
        for c in cols:
            v = str(row[c]).upper()
            r.append(1.0 if v == "PASS" else 0.0)
        mat.append(r)
    M = np.array(mat)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.35 * len(labels))))
    im = ax.imshow(M, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c.replace("_", "\n") for c in cols], fontsize=8)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_title("Filter survival (green=PASS) — master_concordance_table.csv")
    fig.colorbar(im, ax=ax, fraction=0.02)
    fig.tight_layout()
    fig_path = fig_dir / "three_filters_one_survivor.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    print("Wrote", fig_path)

    print("Wrote", out_dir / "canonical_seed_basin_report.json")
    print("Wrote", gen_dir / "run_manifest.json")

    # LaTeX snippet for the capstone paper (requires booktabs)
    tbl_path = out_dir / "master_concordance_table.csv"
    if tbl_path.is_file():
        tdf = pd.read_csv(tbl_path)
        tcols = [
            "candidate_id",
            "psc_layer_I",
            "psc_layer_II",
            "ugp_arith_sieve",
            "ugp_phys_filter",
            "canonical_attractor_basin",
            "final_status",
        ]
        sub = tdf[tcols].head(16)
        tex = sub.to_latex(index=False, escape=True, column_format="l" + "c" * (len(tcols) - 1))
        tex_path = root / "papers/12_unified_rigidity/tables/master_concordance_snippet.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(
            "% Auto-generated from computational_concordance/master_concordance_table.csv\n" + tex
        )
        print("Wrote", tex_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
