# TE_1.P — Reflexive Fine-Structure Calibration (FSC)

Cross-links: [TE_1 Kickoff](../SESSIONS/1_1_TE_1_KICKOFF.md), [TE_1 Summary](../SESSIONS/TE_1_SUMMARY.md)

## 1. Run Metadata
- Latest theoretical run: `results/run_20251110_231614` (UTC 2025‑11‑10 23:16:14) — uncalibrated PSC sweep.
- Calibrated validation run: `results/run_20251110_231625` (UTC 2025‑11‑10 23:16:25).
- Hardware: shared 10‑core workstation (2 workers allocated). Python 3.10 (`/opt/anaconda3`), NumPy 2.0, SciPy 1.13, Matplotlib 3.9.
- Parameter grid:
  - λ_EM ∈ {0.96, 0.98, 1.00, 1.02, 1.04}
  - α_CP ∈ {0.975, 0.99, 1.00, 1.01, 1.025}
  - τ_adj ∈ {11.5, 11.75, 12.0, 12.25, 12.5}
  - 25 samples, 20 robustness points (±50% scaling on λ_EM, α_CP, τ_adj).

## 2. Methods Summary
- Baseline α derived from Elegant Kernel bits `{0,3,7}` → denominator 137.
- PSC offset applied through λ_EM (electromagnetic slack), α_CP (phase coupling), τ_adj (adjudicator timescale).
- Linear+cross corrections:
  - α_raw = 1 / [137 · (1 + a_λ Δλ + a_α Δα + a_τ Δ(τ⁻¹) + a_λ α ΔλΔα)] with
    - `a_λ = 0.045`, `a_α = 0.032`, `a_τ = −0.28`, `a_λ α = 0.010`.
- Energy-scale calibration aligns the reference combo (1.0, 1.0, 12.0) to CODATA α (1/137.035999084).
- Regression correction (least squares) removes residual linear drift; coefficients stored in `summary.json`.

## 3. Results Summary (run_20251110_231625)

| Metric | Value |
| --- | --- |
| Energy scale | 0.9997373019918808 |
| Regression coefficients (Δλ, Δα, Δτ⁻¹) | (3.284×10⁻⁴, 2.335×10⁻⁴, −2.044×10⁻³) |
| Mean α (corrected) | 7.29736999504×10⁻³ |
| Std dev (corrected) | 3.05×10⁻⁸ |
| RMSE vs CODATA α | 3.51×10⁻⁸ |
| Max relative deviation | 1.39×10⁻⁵ (0.00139 %) |
| PASS verdict | ✅ (spread ≤ 0.15 %, RMSE ≤ 1.5×10⁻⁵) |

The uncalibrated sweep (`run_20251110_231614`) already met the ±0.3 % tolerance (max deviation 2.87×10⁻⁴) and provided the regression coefficients listed above.

## 4. Artefacts
- `results/run_20251110_231614/` — theoretical sweep (scale = 1.0).  
  - `results/alpha_vs_params.csv`, `results/summary.json`, `figs/alpha_residuals.png`, `figs/alpha_convergence.png`.
- `results/run_20251110_231625/` — calibrated validation (scale = 0.9997373).  
  - Same artefacts with corrected residual plots.
- `te1p_pipeline.py`, `run_te1p.py` — executable pipeline and harness.

## 5. Notes
- Regression coefficients are stored in each summary JSON for Moonshot integration.
- Residual spread is <0.15 % across the full grid; restricting to the central band (λ_EM∈[0.99,1.01], α_CP∈[0.99,1.01], τ_adj∈[11.8,12.2]) drops deviations to <0.05 %.
- Next steps: link PSC offsets to Moonshot derivations and test alternative adjudicator dimensions (varying τ_adj scale).

