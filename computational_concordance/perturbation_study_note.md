# Perturbation / nearby-alternative elimination (summary)

## Neighborhood tested

1. **Seed probes (dynamics export):** `(1,73,823)`, `(1,73,2137)`, `(2,89,1597)`, `(3,97,2203)` under the law/window grid in `exp_20260413_deep_trajectories`.
2. **RG fixed-point dispersion:** `exp_20260412_rg_sweep_full` — 224 tasks (4 seeds × 7 windows × 8 law variants) recording RG map fixed-point `α` per configuration.

## Elimination pattern

- **Canonical-family seeds** `(1,73,*)` share **basin A** in the deep export; **off-residual** seeds land in **B** or **C**, so they fail “same basin class as the canonical family” when that class is defined as **A** for this probe set.
- **RG α statistics** (see `generated/run_manifest.json`): the Lepton Seed row has lower mean `|α|` drift band than `(2,89,1597)` in the sweep — use as a **secondary** separation statistic alongside basins.

## Figure

`figures/three_filters_one_survivor.png` summarizes pass/fail columns from `master_concordance_table.csv` (green = PASS).

## Finite-range statement

This is **not** an all-policies / all-seeds proof. The elimination ledger is valid relative to the **frozen JSON exports** (SHA-256 recorded in `canonical_seed_basin_report.json`).
