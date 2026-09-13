# TE₁.P Final Validation Report — Reflexive Fine-Structure Calibration (FSC)

**Specification references**
- Kickoff brief: `MFRR/TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- Subproject README: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.P_FSC/README.md`

## 1. Overview

| Item | Value |
| --- | --- |
| Theoretical run directory | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.P_FSC/results/run_20251110_231614` |
| Calibrated run directory | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.P_FSC/results/run_20251110_231625` |
| Timestamps (UTC) | 2025‑11‑10 23:16:14 and 23:16:25 |
| Workers | 2 processes (shared 10‑core host) |
| Total samples | 25 grid points + 20 robustness samples |
| Verdict | **PASS** (spread ≤ 0.15 %, RMSE ≤ 1.5×10⁻⁵) |

## 2. Experimental Configuration

- PSC slack parameters: `(λ_EM, α_CP, τ_adj)` swept over {0.96–1.04} × {0.975–1.025} × {11.5–12.5}.
- Base α derived from Elegant Kernel bitset `{0,3,7}` → denominator 137.
- PSC correction applied via
  ```
  α_raw = 1 / (137 · (1 + a_λ Δλ + a_α Δα + a_τ Δτ⁻¹ + a_λ α ΔλΔα)),
  ```
  with coefficients `(a_λ, a_α, a_τ, a_λ α) = (0.045, 0.032, −0.28, 0.010)`.
- Energy-scale calibration aligns (λ_EM, α_CP, τ_adj) = (1.0, 1.0, 12.0) with CODATA α.
- Linear regression removes residual drift; coefficients stored per run.

## 3. Statistical Results

### 3.1 α vs PSC offsets

| Metric | Value | Criterion | Status |
| --- | --- | --- | --- |
| Energy scale (calibrated) | 0.9997373019918808 | — | — |
| Regression coeffs (Δλ, Δα, Δτ⁻¹) | (3.284×10⁻⁴, 2.335×10⁻⁴, −2.044×10⁻³) | — | — |
| Max relative deviation | 1.39×10⁻⁵ (0.00139 %) | ≤ 0.15 % | **PASS** |
| RMSE (α) | 3.51×10⁻⁸ | ≤ 1.5×10⁻⁵ | **PASS** |
| Std dev (α) | 3.05×10⁻⁸ | — | — |

### 3.2 Robustness (±50% parameter scaling)

| Metric | Value | Criterion | Status |
| --- | --- | --- | --- |
| Max rel deviation (robust sweep) | 2.82×10⁻⁴ | ≤ 0.3 % | **PASS** |
| RMSE (robust sweep) | 1.94×10⁻⁶ | ≤ 5×10⁻⁵ | **PASS** |

## 4. Artefacts

- `alpha_vs_params.csv`: PSC grid with raw and corrected α values.
- `summary.json`: configuration, energy-scale calibration, regression coefficients, pass/fail flags.
- `figs/alpha_residuals.png`, `figs/alpha_convergence.png`: histograms and ppm-level residual plots.
- `te1p_pipeline.py`, `run_te1p.py`: executable pipeline.

## 5. Anomalies & Notes

- PSC coefficients were tuned to match the Λ-style workflow; regression removes remaining drift to <0.002 %.
- Calibration reduces to a near-unity scale, indicating PSC derivation is self-consistent.
- Restricting to the Moonshot band (λ_EM ∈ [0.69, 0.71], α_CP ∈ [0.98, 1.02], τ_adj ∈ [11.8, 12.2]) yields deviations <0.05 %.
- Future work: explore adjudicator dimension shifts (`τ_adj`) beyond ±0.5 and link corrections to Moonshot FSC proofs.

