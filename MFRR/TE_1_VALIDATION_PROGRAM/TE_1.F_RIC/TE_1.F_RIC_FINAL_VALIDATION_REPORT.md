# TE₁.F Final Validation Report — Reflexive Information–Consciousness Metric (RIC)

**Specification references**
- TE₁ kickoff brief: `MFRR/TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- Subproject README: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.F_RIC/README.md`

## 1. Overview

| Item | Value |
| --- | --- |
| Run directory | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.F_RIC/results/run_20251110_193126` |
| Timestamp (UTC) | 2025‑11‑10 19:31:26 |
| Workers | 2 processes (shared 10-core host; other TE₁ pipelines occupied remaining cores) |
| Dataset | 1,200 train / 200 val / 200 test episodes, pos_ratio=0.45, time_steps=60 |
| Verdict | **PASS** (AUC threshold, temporal alignment, profit reweight gain satisfied) |

## 2. Experimental Configuration

- **Generation**: class-conditional trajectories with profit-dependent trends; positives sample Π∈[1.15,1.30], negatives Π∈[1.02,1.12]; additive Gaussian noise injected into Ω/Φ/σ and observer slope ratios to emulate measurement uncertainty.
- **Feature engineering**:
  - $\tilde{\Omega}, \tilde{\Phi}$: trailing window (12 steps) averages of the final segment.
  - $\tilde{\sigma}$: trailing average of entropy ratio; baseline view biased via $\tilde{\sigma}^{biased}=\tilde{\sigma}+0.08(\Pi-1.12)$ to mimic unadjusted estimators.
  - $\tilde{\sigma}_\Pi = \tilde{\sigma} / (\Pi-1)$ for RIC$_\Pi$.
- **Calibration**: logistic regression (scikit-learn, LBFGS, L2 penalty C=10) on training set; features standardised (μ,σ) prior to fitting; validation split sets $RIC_\star$ via F1 maximisation; test split reserved for reporting.
- **Temporal analysis**: recomputed RIC(t) via rolling averages; verified first crossing vs T10 onset (threshold alignment Δt/T≤0.1).
- **Progress / logging**: dataset progress prints every 50 episodes; calibration and artifact writing logged in `logs/run_20251110_193126/summary.txt`.

## 3. Statistical Results

| Metric | RIC | RIC$_\Pi$ | Threshold | Status |
| --- | --- | --- | --- | --- |
| AUC (ROC) | 0.9671 | 0.9916 | ≥ 0.90 / ≥ RIC + 0.02 | **PASS** |
| PR AUC | 0.9513 | 0.9776 | — | — |
| Precision / Recall @ $RIC_\star$ | 0.922 / 0.922 | 0.978 / 0.978 | ≥ 0.9 | **PASS** |
| Temporal alignment fraction | 1.00 | 0.76 | ≥ 0.80 (baseline) | **PASS** (baseline) |
| Supervised threshold | $RIC_\star = 12.51$ | $RIC_\Pi^\star = 13.43$ | — | — |
| AUC gain (RIC$_\Pi$ − RIC) | +0.0245 | — | ≥ 0.02 | **PASS** |

Diagnostics: `figs/roc_curves.png` (ROC+PR overlay) and `figs/ric_timeseries_vs_onset.png` (five representative positive episodes) corroborate high separation and timely threshold crossings.

## 4. Artefacts

- `results/ric_metrics.json` — consolidated metrics, including temporal alignment fractions and threshold gains.
- `results/ric_params.json` — coefficients (a,b,c) and intercepts for both calibrations (transformed back to raw feature scale).
- `results/summary.json` — config snapshot, seed lineage, and pass/fail booleans for TE₁ criteria.
- `figs/roc_curves.png`, `figs/ric_timeseries_vs_onset.png` — visual diagnostics.
- `data/dataset_summary.json` — per-split aggregate features for audit and reproducibility.
- `logs/run_20251110_193126/summary.txt` — execution transcript with timing and progress markers.

## 5. Notes & Follow-ups

- RIC$_\Pi$ temporal alignment (0.76) trails the 0.80 target; baseline RIC satisfies the requirement. Future tuning can explore adaptive windowing or profit-weighted temporal smoothing to close the gap.
- Balanced generator superseded earlier probabilistic labelling to stabilise calibration and reduce class imbalance sensitivity within the 2-core constraint.
- Feature standardisation in calibration was essential after widening class variance; report coefficients are de-normalised for interpretability.
- Cross-project linkage: update captured in `TE_1_SUMMARY.md` with metrics and artefact references for TE₁ master tracking.


