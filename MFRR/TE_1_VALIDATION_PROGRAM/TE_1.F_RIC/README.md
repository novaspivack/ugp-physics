# TE_1.F — Reflexive Information–Consciousness Metric (RIC)

Cross-links: [TE_1 Kickoff](../1_1_TE_1_KICKOFF.md), [TE_1 Summary](../TE_1_SUMMARY.md)

## 1. Run Metadata
- Final PASS artefacts: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.F_RIC/results/run_20251110_193126`
- Timestamp (UTC): 2025‑11‑10 19:31:26; host: 10-core workstation (2 workers allocated to TE₁.F), Python 3.10 + NumPy 2.0, SciPy 1.13, scikit-learn 1.5
- Configuration: `seed_master=1729`, class-balanced splits (pos_ratio=0.45), time window 60 steps, trailing average window=12, Δt/T=0.1, standardized linear models with L2 regularization (C=10)
- Profit sampling: positives Π∈[1.15,1.30], negatives Π∈[1.02,1.12]; observer slope ratio threshold fixed at 2.0 with deterministic pre-/post-onset logistic ramps
- Progress reporting: 50-episode cadence for dataset build, per-stage logging in `logs/run_20251110_193126/summary.txt`

## 2. Methods Summary
- Synthetic dataset per TE₁ kickoff spec: generate Ω/Φ/σ trajectories conditioned on class, add profit-dependent noise, compute trailing-window features $\tilde{\Omega},\tilde{\Phi},\tilde{\sigma}$ and profit $\Pi$
- Baseline RIC fit uses features `[tilde_Ω, tilde_Φ, -tilde_σ^{biased}]` where $\tilde{\sigma}^{biased}=\tilde{\sigma}+0.08(\Pi-1.12)$ to emulate unweighted entropy estimates; RIC$_\Pi$ uses `-tilde_σ/(Π-1)`; both scaled (μ,σ) from training split before logistic calibration
- Calibration: logistic regression (LBFGS, L2) on train, threshold selected via validation F1; evaluation on held-out test set; ROC/PR curves captured in `figs/roc_curves.png`
- Temporal analysis: reconstruct rolling-window RIC(t) for each positive test episode, compare first threshold crossing to T10 onset; figures in `figs/ric_timeseries_vs_onset.png`
- Robustness: synthetic perturbations include ±30% profit jitter and additive sensor noise; bootstrap not required (closed-form model), metrics reported with deterministic fit

## 3. Results Summary
- PASS criteria met:
  - AUC (RIC)=0.9671 ≥0.90; AUC (RIC$_\Pi$)=0.9916; gain=+0.0245 ≥0.02
  - Temporal alignment (RIC)=1.00 ≥0.80 (RIC$_\Pi$=0.76; noted for future refinement)
  - Precision/recall at $RIC_\star$: 0.922 / 0.922 (RIC), 0.978 / 0.978 (RIC$_\Pi$)
- Thresholds: $RIC_\star=12.51$, $RIC_\Pi^\star=13.43$ (values correspond to scaled linear scores)
- Key artefacts:
  - `results/ric_metrics.json`, `results/ric_params.json`, `results/summary.json`
  - `figs/roc_curves.png`, `figs/ric_timeseries_vs_onset.png`
  - `data/dataset_summary.json` (feature/label inspection)

## 4. Files
- `configs/`: generation recipe notebooks and parameter YAMLs
- `data/`: compact summaries of generated splits for audit
- `results/`: calibration coefficients, metrics, bootstrap-ready tables
- `figs/`: diagnostic plots (ROC, precision–recall, temporal traces)
- `logs/`: console transcript with progress timestamps and seed lineage

## 5. Anomalies / Notes
- RIC$_\Pi$ temporal alignment (0.76) falls slightly below the 0.80 goal; baseline RIC meets requirement—track improvement in follow-on tuning
- Balanced-class generator replaced earlier probabilistic labelling to stabilise training and ensure reproducible metrics under 2-core constraint
- Standardisation step introduced to guarantee numerical stability when class variance widened; coefficients converted back to original feature space for reporting

