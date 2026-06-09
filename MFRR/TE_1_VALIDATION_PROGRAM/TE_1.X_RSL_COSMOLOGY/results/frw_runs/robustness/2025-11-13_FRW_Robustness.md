# 2025-11-13 — FRW+Ψ Robustness Sweep (TE₁.X)

Cross-links: [Kickoff](../1_0_TE_1X_RSL_COSMOLOGY_KICKOFF.md) · [Plan](../1_1_TE_1X_RSL_COSMOLOGY_PLAN.md) · Sweep outline (gitignored under `../notes/`)

## Run Details
- Command: `python3 analysis/frw_rsl_runner.py --config configs/frw_rsl_robustness.yaml --entropy ../../TE_1.R_CONTINOUS_MODEL/results/fluctuation/summary.json --max-workers 4`
- Grid: λ_ψ ∈ {0.66, 0.70, 0.74}, α₁ ∈ {0.5, 1.0, 1.5}, α₂ ∈ {0.125, 0.25, 0.5} (27 combinations)
- Outputs: `results/frw_runs/robustness/lambda_*/summary.json` + aggregate `summary.json`

## Observables
- `mean_w0 = -1.0000000000001688`
- `max|w_a| = 2.14×10⁻¹²`
- Λ_phys variation: within 2.4×10⁻³ fractional deviation of target (see `lambda_residual` entries)

## Notes
- Even under 50% scalings of α parameters and ±0.04 shifts in λ_ψ, the equation-of-state remains pinned near -1 with negligible running.
- Next phase: run entropy coupling script once additional robustness sweeps (if any) are added, and propagate the results into the TE₁.X theorem draft.
