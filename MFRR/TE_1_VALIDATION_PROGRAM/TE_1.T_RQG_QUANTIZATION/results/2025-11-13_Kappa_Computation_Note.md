# 2025-11-13 — κ Tensor Baseline Computation

Cross-links: [Kickoff](../1_0_TE_1T_RQG_QUANTIZATION_KICKOFF.md) · [Plan](../1_1_TE_1T_RQG_QUANTIZATION_PLAN.md) · Green-function plan (gitignored under `../notes/`)

## Objective
Evaluate the regulated Green-function gradient norms (κ₀₀, κ_spatial) for the 64³ lattice baseline, feeding the variance term in the curvature quantization theorem.

## Configuration
- Script: `analysis/compute_kappa.py`
- Config: `configs/lattice_baseline.yaml`
- Command: `python3 analysis/compute_kappa.py --config configs/lattice_baseline.yaml --max-workers 2`
- Lattice dimensions: 64 × 64 × 64
- Spacing: 0.125 (comoving units)
- Regulator σ: 0.0530826125 (auto-derived)
- Chunk size: 8 `kₓ` slices
- Workers: 2 (per user allocation)

## Output
- `results/kappa_baseline.json`
  ```json
  {
    "dimensions": [64, 64, 64],
    "spacing": 0.125,
    "sigma": 0.05308261251800119,
    "chunks": 8,
    "max_workers": 2,
    "kappa_00": 1.3610835678647495e+07,
    "kappa_spatial": 2.722167135729499e+07,
    "notes": "Verify against lattice simulation before final use."
  }
  ```

## Observations
- κ_spatial ≈ 2 × κ₀₀ as expected for isotropic FRW symmetry.
- Memory footprint stayed below 120 MB; runtime ~2 minutes.
- Next step: plug κ values into lattice simulator and compare against Monte Carlo curvature variance.
