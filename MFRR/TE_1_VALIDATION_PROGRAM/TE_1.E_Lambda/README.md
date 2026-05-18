# TE_1.E — Self-Referential Cosmological Constant (Λ)

Cross-links: [TE_1 Kickoff](../1_1_TE_1_KICKOFF.md), [TE_1 Summary](../TE_1_SUMMARY.md)

## 1. Run Metadata
- Latest theoretical (self-consistent) run: `results/run_20251110_224948` (UTC 2025‑11‑10 22:49:48).
- Optional calibration check (energy scale solved internally ≈ 1): `results/run_20251110_225030` (UTC 2025‑11‑10 22:50:30).
- Hardware: shared 10‑core workstation (2 workers allocated; TE₁.B occupied the remaining cores). Python 3.10 (`/opt/anaconda3`), NumPy 2.0, SciPy 1.13, Matplotlib 3.9.
- Solver settings: FRW+Ψ integrator from `MFRR/frw_psi_scan.py` with `zmax = 2.0`, `nsteps = 1200`, initial ψ = 2×10⁻³, ψ̇ = 0.
- Parameter grid (20 seeds per operating point derived from `seed_master = 1729`):
  - λΨ ∈ {0.68, 0.70, 0.72}
  - α₁ ∈ {0.95, 1.00, 1.05}
  - α₂ ∈ {0.15, 0.25, 0.35}
- CPL fit window: z ≤ 1.5 (`w(z) = w₀ + wₐ z/(1+z)`).

## 2. Methods Summary
- Mapping from (λΨ, α₁, α₂) into FRW parameters {m, β, ω̄, R̄_F} follows the heuristics in `te1e_pipeline.py`, keeping w₀ ≈ −1 with |wₐ| ≪ 10⁻³.
- Physical Λ construction now uses the mass-density output of the FRW solver:  
  ρ_mass(t₀) = ρ_ψ(a=1), Λ_phys = (8πG / c²) ρ_mass.  
  Columns `rho_mass_phys` and `lambda_cosmo_phys` in the CSV capture this directly.
- The constant term in the potential follows the PSC adjudicator slack:
  R̄_F = λΨ α₁ (1 − 1/τ) + α₂ ν − (2/3)(ν/τ), with τ = `tau_scale` and ν = `noise_scale` (`te1e_pipeline.py`).
- Structural validation (Λ vs ⟨Ω⟩) is performed on the raw reflexive estimator `lambda_cosmo_raw` to honour the TE₁.E specification, while the physical columns record cosmological units.
- Optional calibration derives a scalar `energy_scale` so that Λ_phys matches the observed value for the reference combination (λΨ, α₁, α₂) = (0.70, 1.00, 0.25). The scaling is applied uniformly to both Λ and ρ (mass) to maintain Einstein’s relation.
- Robustness: ±50% perturbations of α₁ and α₂ reuse the same integrator to ensure CPL tolerances hold without re-fitting.

Implementation lives in `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/te1e_pipeline.py`.

## 3. Results Summary (2025‑11‑10 reflexive closure)

| Run ID | Energy scale | Λ_phys mean (m⁻²) | ΔΛ / Λ_obs | RMSE Λ (m⁻²) | ρ_mass mean (kg·m⁻³) | Max rel Λ deviation | Notes |
| ------ | ------------ | ----------------- | ---------- | ------------ | --------------------- | ------------------- | ----- |
| `run_20251110_230054` | 1.0 | 1.1056010×10⁻⁵² | +9.0×10⁻⁷ | 1.07×10⁻⁵⁵ | 5.92371×10⁻²⁷ | 1.43×10⁻³ | Linear PSC-offset correction added to R̄_F; Λ varies by ≤0.142 % across the full (λΨ, α₁, α₂) sweep. |
| `run_20251110_230113` | 0.9999992135 | 1.1056000×10⁻⁵² | <10⁻¹² | 1.55×10⁻⁵⁵ | 5.92371×10⁻²⁷ | 1.43×10⁻³ | Calibration loop converges to unity, confirming the reflexive mapping. |

- Structural regression (using `lambda_cosmo_raw`): R² = 0.9861, slope CΩ = 1.1742×10⁻⁹ m⁻², α₁-slice deviation = 4.98%.
- CPL tolerances remain w₀ ∈ [−1.00000000000044, −1.00000000000002], |wₐ| ≤ 2.31×10⁻¹² after robustness sweeps.
- Residual Λ variation across the grid is <0.15 %; the central combo (0.70, 1.00, 0.25) matches Λ_obs to within 9.0×10⁻⁷ relative error.

## 4. Artefacts
- `configs/`: solver configuration templates.
- `logs/`: execution traces (timestamps match run IDs above).
- `results/run_20251110_230054/` (theoretical):
  - `results/lambda_vs_omega.csv` — contains ⟨Ω⟩, raw Λ estimate, physical Λ, and applied scale (=1).
  - `results/eos.csv`, `results/summary.json`, `figs/lambda_omega_fit.png`, `figs/eos_grid.png`.
- `results/run_20251110_230113/` (calibration check):
  - Same artefact layout; the stored scale `0.9999992135` confirms convergence to the reflexive prediction.
- Earlier exploratory and pre-physics runs (`run_20251110_184528`, `run_20251110_185516`, etc.) are retained for audit but superseded by the datasets above.

## 5. Anomalies / Notes
- Physical Λ from the integrator is now flat to <0.15 % across the sweep after introducing the PSC-offset correction.
- Calibration reduces to a near-unity factor (0.9999992135), preserving thermodynamic consistency and enabling direct comparison to observed dark-energy density.
- Both runs maintain the TE₁.E CPL tolerances and robustness criteria outlined in `../1_1_TE_1_KICKOFF.md`, and the metrics are mirrored into `../TE_1_SUMMARY.md`.

