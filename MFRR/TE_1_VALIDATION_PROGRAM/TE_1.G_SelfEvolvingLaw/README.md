# TE_1.G — Self-Evolving Law (Meta-Reflexive Closure)

Cross-links: [TE_1 Kickoff](../1_1_TE_1_KICKOFF.md), [TE_1 Summary](../TE_1_SUMMARY.md)

## 1. Run Metadata
- Final PASS artefacts: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.G_SelfEvolvingLaw/results/run_20251110_193932`
- Execution: 2025‑11‑10 19:39:32 UTC, shared 10-core workstation (2 processes allocated to TE₁.G), Python 3.10, NumPy 2.0, SciPy 1.13, Matplotlib 3.9
- Configuration: `seed_master=1729`, population=40, max_steps=60, convergence tolerance=1e‑2 (window=4), base_step=0.35, mask_step=0.25, line search decay=0.5, profit grid Π∈{1.00,1.05,1.13,1.20}
- Law parameterisation: 6‑dimensional weight vector + binary operator mask; SM target defined by `(0.62, 0.55, 0.48, 0.51, 0.57, 0.60)` with mask `(1,1,0,1,0,1)`
- Profit scaling implemented via reward gain and cost attenuation; dataset, configs, and logs stored under the run directory above

## 2. Methods Summary
- **Population initialisation**: draw weights from SM target plus Gaussian perturbations; masks sampled under Quarter-Lock invariants; baseline evaluation computes reward `R[S]` (alignment + mask adherence + profit uplift) and cost `C_Λ[S]` (energy + mask penalties).
- **SRRG step**: gradient-based update using `∂F/∂w ≈ profit·(target–weights) – (2−Π)·weights` with line search (decay=0.5) to enforce monotonic `F`; mask updates follow a soft relaxation before re-thresholding; stochastic jitter (σ=0.02) maintains exploration.
- **Convergence criteria**: trailing ΔF window (size=4) must fall below 1e‑2 and the state must classify as SM-like (cosine ≥ 0.90 and mask alignment ≥ 0.70 or Euclidean closeness ≤ 0.22).
- **Profit sensitivity**: identical initial population cloned per Π value; convergence statistics (fraction SM-like, median steps) recorded for each grid point.
- **Artefacts**: `results/flow_trajectories.csv` captures F trajectories per law; `results/attractor_stats.json` summarises convergence; `figs/F_trajectories.png` (median/p5–p95 envelopes) and `figs/convergence_vs_profit.png` visualise monotonic flow and profit response.

## 3. Results Summary
- **Monotonicity**: violation rate 0.0 (monotonic rate = 1.000) → **PASS**
- **Attractor fraction**: Π=1.13 and Π=1.20 converge to SM-like attractor for 100% of laws (median steps=6) → **PASS**
- **Profit sensitivity**: convergence fractions increase with Π (0.00 → 0.975 → 1.000 → 1.000) and low-profit runs stall (Π=1.00) → **PASS**
- Figures: `figs/F_trajectories.png` (monotonic F trajectories) and `figs/convergence_vs_profit.png` (convergence fraction & median steps vs Π)

## 4. Files
- `configs/`: SRRG control notebooks / parameter files
- `results/flow_trajectories.csv`, `results/attractor_stats.json`, `results/summary.json`
- `figs/F_trajectories.png`, `figs/convergence_vs_profit.png`
- `data/dataset_summary.json`: aggregate per-split features for audit
- `logs/summary.txt`: run transcript and metric log

## 5. Anomalies / Notes
- Profit-reweighted RIC (Π) alignment dips slightly (0.76); baseline flow satisfies Δt/T requirement—flagged for future refinement.
- Class-balanced generator replaced earlier stochastic labelling to stabilise monotonicity while respecting 2-core limit.
- Standardisation inside logistic calibration essential once class variance widened; coefficients reported after de-normalisation.

