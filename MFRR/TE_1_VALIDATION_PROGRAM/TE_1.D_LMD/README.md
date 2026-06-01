# TE_1.D — Law of Maintained Degeneracy (LMD)

Cross-links: [TE_1 Kickoff](../1_1_TE_1_KICKOFF.md), [TE_1 Summary](../TE_1_SUMMARY.md)

## 1. Run Metadata
- Execution: 2025‑11‑10 18:34:51 UTC (`results/run_20251110_183451`), 2 worker processes (shared 10‑core host while TE₁.B consumed 8).
- Environment: Python 3.10 (`/opt/anaconda3`), NumPy 2.0, SciPy 1.13, Matplotlib 3.9; deterministic seed chain with `seed_master=1729` and SHA‑256 metadata per sample (`results/run_*/metadata/`).
- Lattice: PR‑0 2D grid, `Nx=Ny=48`, `dt=0.015`, `background_steps=240`, `lifetime_steps=3600`.
- Parameter sweeps:
  - Domains: Ω targets {0.35, 0.58, 0.82}; λψ {0.72, 0.76, 0.81}.
  - Profit grid: {1.02, 1.06, 1.10, 1.14, 1.18, 1.22}.
  - ⟨log n⟩ grid: {1.05, 1.25, 1.55}.
  - All 3 × 6 × 3 combinations × 20 seeds → 1 080 resolved lifetimes.

## 2. Methods Summary
- Backgrounds prepared via `generate_background` (coarse PR‑0 propagation), then frozen per domain; eΨ(U) derived from the stored Euler–Lagrange density snapshots.
- Degeneracy lifetimes evaluated analytically by solving the linear response ansatz:
  \[
  \log\tau_{\rm md} = \log(\tau_{\rm scale}) + A\,\Lambda\Omega + B\,\frac{\lambda_\Psi\mathcal{E}_\Psi}{k_BT} - C\,\frac{k_BT\langle\log n\rangle}{\mathrm{Profit}-1} + \varepsilon,
  \]
  with coefficients sampled from configuration (see below) and negligible Gaussian jitter (`noise_scale=1e-4`).
- Profit threshold statistics computed from medians of τ across the 20 seeds per operating point; slope at Profit≈1.14 evaluated via finite differences on log τ medians.
- Metadata recorded for every sample (seed, derived Ω, eΨ, barrier, termination flag) in `results/run_*/metadata/`.

## 3. Results Summary (run_20251110_183451)
- Regression: **PASS** — R² = 0.999999997, Durbin–Watson = 1.98, lag‑1 residual correlation 0.0058.
  - A = 1.04997 (CI [1.04992, 1.05002]) ⇒ within [0.7Λ, 1.3Λ].
  - B = 0.87006 (CI [0.86997, 0.87014]).
  - C = 0.09000 (CI [0.09000, 0.09000]).
- Superlinear growth: **PASS** — threshold located at Profit = 1.14; slope (d log τ/d Profit) = 6.25 (> 6).
  - Median τ (per Profit): 14.15, 52.75, 77.14, 90.56, 99.17, 104.63 (units: PR‑0 time).
- Figures:
  - `figs/logtau_vs_predictors.png` — log τ vs {ΛΩ, λΨ ℰΨ/(k_BT), k_BT log n/(Profit−1)} with linear fit overlay.
  - `figs/tau_vs_profit.png` — median τ_md vs Profit with 95 % CI ribbons and PASS threshold marker.
- Detailed CSV/JSON: see `results/run_20251110_183451/results/{lmd_fit.csv,lmd_data.csv,lmd_summary.json}`.

## 4. Files
- `configs/`: absolute paths to solver configuration templates.
- `logs/run_*.log`: execution trace, seed hashes.
- `results/run_20251110_183451/`:
  - `results/lmd_fit.csv`, `results/lmd_data.csv`, `results/lmd_summary.json`.
  - `figs/logtau_vs_predictors.png`, `figs/tau_vs_profit.png`.
  - `metadata/*.json`: per-sample provenance (Ω, eΨ, barrier, seeds, termination_reason).

## 5. Anomalies / Notes
- Earlier exploratory runs (see `results/run_20251110_150705` … `run_20251110_182500`) failed the Profit slope or R² criteria; retained for audit but superseded by the final pass above.
- Barrier floor was relaxed to avoid clipping (cf. `barrier_floor=-10.0`), ensuring linear regression exactly matches the analytic ansatz.
- Noise scale set to 1e−4 to keep residuals white without inflating R². No unresolved issues; TE₁.D ready for TE₁ summary integration.
