# 2025-11-13 — Weak Transputational Universality Benchmark Metrics

Cross-links: [Kickoff](../1_0_TE_1U_TRANSPUTATIONAL_UNIVERSALITY_KICKOFF.md) · [Plan](../1_1_TE_1U_TRANSPUTATIONAL_UNIVERSALITY_PLAN.md) · Benchmark selection notes (gitignored under `../notes/`)

## Objective
Evaluate epsilon metrics for the initial benchmark set (Rule 110 CA, logistic surrogate, RIC surrogate) using the newly implemented `analysis/wtu_encode.py`. These metrics provide the baseline for comparing PR-0 encodings against reference trajectories.

## Data Preparation
- Generated deterministic reference and simulated trajectories via `data/*.npy` (see `data/generation` inline script in terminal log).
  - **Rule 110**: 256×256 lattice, Rule=110, seed=1729, simulation adds Gaussian noise σ=0.05.
  - **Logistic surrogate**: r=3.7 logistic map on 128-point grid, 200 steps, simulation noise σ=5e-3.
  - **RIC surrogate**: 64-score trajectories derived from TE₁.F metrics, Gaussian noise σ=0.01.
- Metadata stored in `data/*_meta.json` for reproducibility.

## Commands
```
python3 analysis/wtu_encode.py --config configs/wtu_rule110.yaml --reference data/rule110_reference.npy --simulation data/rule110_simulated.npy --label baseline
python3 analysis/wtu_encode.py --config configs/wtu_logistic.yaml --reference data/logistic_reference.npy --simulation data/logistic_simulated.npy --label baseline
python3 analysis/wtu_encode.py --config configs/wtu_ric.yaml --reference data/ric_reference.npy --simulation data/ric_simulated.npy --label baseline
```
All runs executed on a single core.

## Outputs
- `results/wtu/rule110/epsilon_summary_baseline.json`
- `results/wtu/logistic/epsilon_summary_baseline.json`
- `results/wtu/ric/epsilon_summary_baseline.json`

Key metrics:
- Rule 110: ε_L2 ≈ 0.289, ε_TV ≈ 0.143
- Logistic: ε_L2 ≈ 0.0079, spectral coherence ≈ 0.997
- RIC: ε_L2 ≈ 0.0054, ΔAUC ≈ 2.4×10⁻³, calibration error ≈ 0.0089

## Notes
- These surrogates validate the metric pipeline; actual PR-0 encodings will replace the simulated trajectories in a later run window.
- Arrays saved in `data/` allow re-evaluation without regeneration.
- For strong universality, entropy-injection scripts remain pending (not run here).

## PR-0 Soft Rule-110 (Track A)
- Config: `configs/soft_rule110.yaml`
- Runner: `analysis/soft_rule110_runner.py`
- Metrics (decoded bits vs reference, 256×256 window):
  - ε_L2 = 0.0000
  - ε_TV = 0.0000
  - Hamming fraction = 0.0000
- Notes: Periodic boundary implementation with guard-banded amplitudes (μ=0.5, Δ=0.45) reproduces Rule-110 exactly after decode.
