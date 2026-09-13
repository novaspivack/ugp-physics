# Reproducing concordance artifacts

## One-command regeneration (recommended)

From the **repository root**:

```bash
python3 computational_concordance/scripts/build_reports_from_discovery_lab.py
```

This reads frozen JSON exports:

- `ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json`
- `ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260412_rg_sweep_full/results/reports/experiment_results.json`

and writes / refreshes:

- `canonical_seed_basin_report.json` (SHA-256 of inputs embedded)
- `generated/run_manifest.json` (RG `α` summary by seed)
- `figures/three_filters_one_survivor.png`
- `papers/12_unified_rigidity/tables/master_concordance_snippet.tex`

Requires: `pandas`, `matplotlib`, `numpy` (see root `requirements.txt`).

## Git LFS and large experiment data

`exp_20260413_deep_trajectories/results/reports/experiment_results.json` is large and is
tracked by Git LFS (see root `.gitattributes`). It is **not pushed** to the public GitHub
repository; it is held locally. Its SHA-256 hash is recorded in `canonical_seed_basin_report.json`
for auditability.

A compact human-readable summary of the key results is in:
`computational_concordance/data/deep_trajectories_basin_summary.csv`

This CSV is the git-tracked evidence artifact. The SHA-256 of the full JSON is the cryptographic
anchor. See `ugp_discovery_lab/UGP_discovery_lab_runs/exp_20260413_deep_trajectories/PROVENANCE.md`
for reproduction instructions.

## Ledger

`residuals_ledger.md` is maintained alongside `unified-rigidity-lean/ASSUMPTION_LEDGER.md` and the
capstone trust boundary; update when exports change.

## Tables

`master_concordance_table.csv` is the **editorial** source for candidate rows (RSUC family, theory-space probes).
Re-run the script after editing the CSV to refresh the LaTeX snippet and figure.

## Basin / perturbation notes

- `basin_concordance_note.md` — narrative summary of basin A/B/C split in the deep export.
- `perturbation_study_note.md` — elimination logic + pointers to `run_manifest.json`.
