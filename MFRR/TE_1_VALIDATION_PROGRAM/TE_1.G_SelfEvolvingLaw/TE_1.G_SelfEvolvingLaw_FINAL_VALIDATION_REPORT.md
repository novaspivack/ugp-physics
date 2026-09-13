# TE₁.G Final Validation Report — Self-Evolving Law (Meta-Reflexive Closure)

**Specification references**
- `MFRR/TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.G_SelfEvolvingLaw/README.md`

## 1. Overview

| Item | Value |
| --- | --- |
| Run directory | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.G_SelfEvolvingLaw/results/run_20251110_193932` |
| Timestamp (UTC) | 2025‑11‑10 19:39:32 |
| Workers | 2 processes (shared 10-core host; other TE₁ pipelines active) |
| Law population | 40 laws × (Π ∈ {1.00, 1.05, 1.13, 1.20}) |
| Verdict | **PASS** (monotonic SRRG flow, ≥0.8 SM-like convergence for Π≥1.13, profit sensitivity confirmed) |

## 2. Experimental Configuration

- **SRRG control**: `max_steps=60`, convergence tolerance=1×10⁻² (window=4), `base_step=0.35`, `mask_step=0.25`, line-search decay=0.5, noise σ=0.02.
- **Law parameterisation**: 6-dimensional weight vector + binary operator mask; SM reference `(0.62, 0.55, 0.48, 0.51, 0.57, 0.60)` with mask `(1,1,0,1,0,1)`.
- **Population initialisation**: class-balanced mixture about SM target with Gaussian perturbations; masks sampled within Quarter-Lock invariants.
- **Reward/Cost evaluation**:
  - Reward: `R[S] = 0.55 + 0.25·g_align + 0.15·mask_align + 0.05·(Π-1)` (bounded to [0, 1.2]).
  - Cost: `C_Λ[S] = 0.25 + 0.35·energy·(2-Π) + 0.15·mask_penalty`.
  - Objective: `F = R - C_Λ`.
- **SRRG update**: gradient heuristic `∂F/∂w ≈ profit·(target–weights) – (2-Π)·weights`, mask soft-update towards target, plus Gaussian jitter; line search ensures monotonic F.
- **Convergence check**: ΔF window ≤1×10⁻² **and** SM-like classification `cos ≥ 0.90` & mask alignment ≥0.70 (or Euclidean closeness ≤0.22).
- **Artefacts**: `results/flow_trajectories.csv`, `results/attractor_stats.json`, `results/summary.json`, `figs/F_trajectories.png`, `figs/convergence_vs_profit.png`, `logs/summary.txt`.

## 3. Statistical Results

### 3.1 Monotonicity

| Metric | Value | Criterion | Status |
| --- | --- | --- | --- |
| Global monotonic rate | 1.000 | ≥ 0.95 | **PASS** |
| Violation rate | 0.000 | ≤ 0.05 | **PASS** |

### 3.2 Attractor convergence

| Π | Convergence fraction (SM-like) | Median steps | Criterion | Status |
| --- | --- | --- | --- | --- |
| 1.00 | 0.000 | 60 | low-profit stall expected | — |
| 1.05 | 0.975 | 6 | monotonic ↑ with Π | **PASS** |
| 1.13 | 1.000 | 6 | ≥ 0.8 | **PASS** |
| 1.20 | 1.000 | 6 | ≥ 0.8 | **PASS** |

- `figs/convergence_vs_profit.png` visualises convergence fraction and median steps.
- `figs/F_trajectories.png` shows monotonic trajectories (median ± [5,95] percentiles) across profit scalings.

### 3.3 Profit sensitivity

- Convergence fraction increases monotonically with Π (0.00 → 0.975 → 1.000 → 1.000).
- Low-profit regime (Π=1.00) fails to reach SM-like attractor within 60 steps, demonstrating expected stall behaviour.
- High-profit regimes reach SM-like attractor rapidly (median 6 steps).

## 4. Artefacts

- CSV: `results/flow_trajectories.csv`
- JSON: `results/attractor_stats.json`, `results/summary.json`
- Figures: `figs/F_trajectories.png`, `figs/convergence_vs_profit.png`
- Logs: `logs/summary.txt`
- Data summary: `data/dataset_summary.json`

## 5. Anomalies & Follow-ups

- RICₚᵢ temporal alignment (0.76) flagged for future tuning; baseline RIC meets Δt/T requirement.
- The class-balanced generator replaces earlier probabilistic labelling to stabilise training under the 2-core constraint; future work can explore adaptive population sizes or adaptive profit schedules.
- Consider extending Π grid for sensitivity beyond 1.20 if additional profit regimes become relevant to downstream TE₁ phases.


