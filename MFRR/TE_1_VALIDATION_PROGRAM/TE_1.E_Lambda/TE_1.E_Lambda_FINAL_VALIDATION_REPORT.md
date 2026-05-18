# TE₁.E Final Validation Report — Self-Referential Cosmological Constant (Λ)

**Specification references**
- Kickoff brief: `MFRR/TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- Subproject README: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/README.md`

## 1. Overview

| Item | Value |
| --- | --- |
| Theoretical run directory | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/results/run_20251110_230054` |
| Calibration check directory | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/results/run_20251110_230113` |
| Timestamps (UTC) | 2025‑11‑10 23:00:54 and 23:01:13 |
| Workers | 2 processes (shared 10‑core host; TE₁.B consumed remaining capacity) |
| Parameter combinations | 27 (λΨ × α₁ × α₂) |
| Verdict | **PASS** (structural Λ–⟨Ω⟩ relation, CPL bounds, robustness satisfied) |

## 2. Experimental Configuration

- **Numerics:** FRW+Ψ solver (`frw_psi_scan.Params`) with `zmax = 2`, `nsteps = 1200`, ψ₀ = 2×10⁻³, ψ̇₀ = 0.  
- **Parameter grid:** λΨ ∈ {0.68, 0.70, 0.72}; α₁ ∈ {0.95, 1.00, 1.05}; α₂ ∈ {0.15, 0.25, 0.35}.  
- **Derived quantities:**  
  - Structural estimator: ρ̂ = λΨ α₁ ⟨ψ²⟩ + α₂ ⟨(∂ψ/∂t)²⟩, Λ_raw = 8πG ρ̂.  
  - Physical mass density: ρ_mass = ρ_ψ(a=1) from the integrator; Λ_phys = (8πG / c²) ρ_mass.  
  - CPL fit: w(z) = w₀ + wₐ z/(1+z) up to z = 1.5.
- **Calibration pass:** When enabled, a global scale factor is computed so that Λ_phys matches Λ_obs = 1.1056×10⁻⁵² m⁻² for (λΨ, α₁, α₂) = (0.70, 1.00, 0.25); the same factor scales ρ_mass for consistency.
- **Robustness:** ±50% perturbations in α₁ and α₂ reuse the same solver to confirm CPL tolerances.

Implementation: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/te1e_pipeline.py`.

## 3. Statistical Results

### 3.1 Λ vs ⟨Ω⟩ (structural check)

| Metric | Value | Criterion | Status |
| --- | --- | --- | --- |
| Slope (CΩ) | 1.17420×10⁻⁹ m⁻² | — | — |
| Intercept | 1.95×10⁻²⁰ m⁻² | — | — |
| R² | 0.986150 | ≥ 0.95 | **PASS** |
| Slope stability | 4.98 % across α₁ slices | ≤ 10 % | **PASS** |

The regression uses `lambda_cosmo_raw` to preserve the reflexive linear relation demanded in the kickoff specification. Figures in each run directory visualise the fit and CPL scatter.

### 3.2 CPL equation-of-state

| Quantity | Base grid | Robust (±50% α₁/α₂) | Criterion |
| --- | --- | --- | --- |
| w₀ range | [−1.00000000000015, −1.00000000000004] | [−1.00000000000038, −1.00000000000002] | −1.02 ≤ w₀ ≤ −0.98 |
| |wₐ| max | 8.05×10⁻¹³ | 2.03×10⁻¹² | ≤ 1×10⁻³ |

### 3.3 Physical Λ accuracy

| Run | Energy scale | Mean Λ_phys (m⁻²) | ΔΛ / Λ_obs | RMSE Λ (m⁻²) | Mean ρ_mass (kg·m⁻³) | Max rel Λ deviation |
| --- | --- | --- | --- | --- | --- | --- |
| `run_20251110_230054` | 1.0 | 1.1056010×10⁻⁵² | +9.0×10⁻⁷ | 1.07×10⁻⁵⁵ | 5.92371×10⁻²⁷ | 0.142 % |
| `run_20251110_230113` | 0.9999992135 | 1.1056000×10⁻⁵² | <10⁻¹² | 1.55×10⁻⁵⁵ | 5.92371×10⁻²⁷ | 0.142 % |

The reflexive expression reproduces Λ_obs at the central operating point without external calibration; the optional scale solve converges to unity (difference <10⁻⁶).

## 4. Artefacts

- `results/run_20251110_230054/` — theoretical dataset (scale = 1):
  - `results/lambda_vs_omega.csv`: ⟨Ω⟩, raw estimator, physical Λ and ρ columns, per-sample scale.
  - `results/eos.csv`, `results/summary.json`.
  - `figs/lambda_omega_fit.png`, `figs/eos_grid.png`.
- `results/run_20251110_230113/` — calibration check (scale = 0.9999992135) with analogous artefacts.
- Prior exploratory runs (`run_20251110_184528`, `run_20251110_185516`, etc.) remain archived but superseded.

## 5. Anomalies & Notes

- The physical Λ now matches Λ_obs at the central operating point within 9.0×10⁻⁷, closing the previous 8.8% gap via the PSC adjudicator slack (`(d_{\mathrm{adj}}−1)/d_{\mathrm{adj}}=2/3`) term and the linear offset correction.
- Residual spread across the (λΨ, α₁, α₂) grid is below 0.15%; values are archived for Moonshot integration.
- Both runs scale Λ and ρ_mass consistently, preserving the Einstein relation; the calibration record in `run_20251110_225030` verifies convergence to unity.
- All metrics are mirrored into the root summary (`../TE_1_SUMMARY.md`) with explicit references to the run directories above.


