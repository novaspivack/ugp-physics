# 2025-11-13 — RIET Phase A Perturbation Batch Generation

Cross-links: [Kickoff](../1_0_TE_1S_RIET_KICKOFF.md) · [Plan](../1_1_TE_1S_RIET_PLAN.md) · [Audit 1_8](../../SESSIONS/1_8_NEW_SUB-PROJECTS.md)

## Objective
Generate perturbation batches for Phase A variational checks using `analysis/data_harness.py`, populated with current TE₁.C/TE₁.R/TE₁.E/TE₁.O datasets. This prepares inputs for subsequent residual convergence runs.

## Configuration
- Script: `analysis/data_harness.py`
- Command: `python3 analysis/data_harness.py` (invoked via inline runner — see terminal log)
- Batch size: 8 samples per configuration
- RNG seed: 42 (documented in script output)
- Datasets referenced:
  - TE₁.C slow-roll summary: `../TE_1.C_RQG/results/phase1_summary.json`
  - TE₁.R PT selector summaries: `../TE_1.R_CONTINOUS_MODEL/results/pt_selector/*_summary.json`
  - TE₁.R fluctuation summary: `../TE_1.R_CONTINOUS_MODEL/results/fluctuation/summary.json`
  - TE₁.E Λ baseline: `../TE_1.E_Lambda/results/run_20251110_230054/results/summary.json`
  - TE₁.O fast-win invariants: `../TE_1.O_ABSOLUTE_GAUGE/results/fast_win_summary.json`

## Outputs
- `results/perturbation_batch_00.npz` + JSON summary (`label=baseline`)
- `results/perturbation_batch_01.npz` + JSON summary (`label=stress`)
- `results/perturbation_batch_02.npz` + JSON summary (`label=lambda-omega`)
- `results/perturbation_summary.json` aggregating per-batch statistics

Key statistics (std-dev values):
- Baseline: δg≈7.4e-06, δI≈1.2e-03, δψ≈9.4e-04
- Stress: δg≈3.7e-05, δI≈2.4e-03, δψ≈4.7e-03
- Lambda-Omega: δg≈1.1e-52, δI≈2.6e-02, δψ≈1.1e-04

## Notes
- No variational residuals computed yet; this run strictly prepares inputs.
- Paths captured in `perturbation_summary.json` for reproducibility.
- Next step: feed batches into variational evaluation once compute window opens.
