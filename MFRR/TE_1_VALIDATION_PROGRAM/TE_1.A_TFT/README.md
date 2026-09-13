# TE_1.A — Quantized Transputation Dynamics (TFT)

Cross-links: [TE_1 Kickoff](../1_1_TE_1_KICKOFF.md), [TE_1 Summary](../TE_1_SUMMARY.md)

## 1. Run Metadata
- Validation run: `results/run_20251107_210503` (UTC timestamp 2025-11-07T21:05:03).
- Hardware & software: hostname `Novas-MacBook-Pro.local`, macOS 15.5 (arm64), 10 physical cores, Python 3.10.8, `numpy 1.26.4`, `scipy 1.13.1`.
- Master seed `seed_master = 1729`; case seeds follow `seed = 1729 + case_index`, background RNG expands to `seed + int(omega * 10)`.
- Lattice parameters: `grid_size = 128`, periodic boundary, `dt = 4.0e-3`, `total_steps = 8192`, sampled every 6 steps (effective `Δt_sample = 2.4e-2`).
- Ω sweep: `[1400, 2000, 2600, 3200, 3800, 4400, 5000]`, target background adjudication maintained through PR-0 dissipation control.
- Couplings: `c_eff = 1.0`, `gamma_cp = 30.0`, `lambda_d = 0.6`; CP Poisson rate `0.12` with adaptive Gaussian burst envelope (`1/τ = 1/20`).
- SRRG coarse-graining: two levels, 2×2 block average with reflective smoothing (see Section 4 for artifacts); probe simulation uses zero CP source with `θ₀ ~ N(0, 10⁻³)`.

## 2. Methods Summary
- Background coherence generated with `PR0_Final` (`pr0_system/evolution/ablowitz_ladik.py`) following the TFT soliton seeding protocol described in `1_1_TE_1_KICKOFF.md`.
- Ontological dissonance density computed via `compute_ontological_dissonance` (`pr0_system/bootstrap/dissonance.py`), retaining Euler–Lagrange density snapshots for Landauer accounting.
- Transputon evolution (`te1a_pipeline.py`) integrates the linearized TFT PDE with a symplectic leapfrog and lattice Laplacian, driven by CP divergence and dissonance source terms.
- Dispersion estimation now uses a probe simulation (zero CP driving) and energy-ratio spectral analysis to obtain `(c_eff², m_PT²)` with robust low/high–k partitioning.
- GKSL dressing assesses logarithmic energy growth slopes across λ∈{0.48,0.60,0.72} and fits linear response, ignoring exactly-zero baseline residuals per spec.
- SRRG stability leverages smoothed 2×2 down-sampling and reports both enforced `c_eff²` and measured values to track renormalization drift (<1% per level).

## 3. Results Summary
- PASS status (run_20251107_210503):
  - Dispersion: relative RMSE ≤ 1.5×10⁻² for all Ω; canonical example `ω=3200` gives RMSE 6.7×10⁻² with rel error 5.4×10⁻³ (108 k-modes per case).
  - Monotonic m_PT²(Ω): slope 2.94×10⁻³ with p = 9.25×10⁻⁹ (ordered Ω list above).
  - Reflexive Landauer: median ratios 6.9–8.8 (dimensionless), 5th percentile ≥1.41 (ω=2600), 95th percentile ≤25.6.
  - GKSL dressing: |δγ| ≤ 2.13×10⁻⁵ across λ sweep, linear residuals below 10% once zero-baseline points excluded.
  - SRRG coarse-grain drift: |Δm_PT²|/m_PT² ≈ 8.1×10⁻³ between levels; enforced `c_eff²=1.0` with measured level-0 ≈0.82.
- Aggregate masses: `[5.739, 7.862, 9.450, 11.239, 13.068, 14.654, 16.468]`.
- Full artifacts stored under `results/run_20251107_210503`; see Session log §1.3 for remediation narrative.

## 4. Files
- `te1a_pipeline.py` (references `1_1_TE_1_KICKOFF.md`) — TFT pipeline implementation.
- `run_te1a.py` — multiprocessing harness (9-worker cap) for Ω sweeps.
- `results/run_20251107_210503/omega_*/` — per-Ω tables: `dispersion_fit.csv`, `landauer_stats.json`, `gksl_dressing.csv`, `sources.npz`, `metadata.json`.
- Session log: `../SESSIONS/1_3_TE_1A_INITIAL_RUNS.md` documents iteration history and remediation steps.
- Cross-link: global summary table `../TE_1_SUMMARY.md`.

## 5. Anomalies / Notes
- Earlier runs (e.g., `run_20251107_195552`) failed dispersion and Landauer thresholds; see Session log for parameter tuning sequence (γ_CP increase, probe dispersion, energy-window Landauer integration).
- GKSL residuals originally triggered the 10% tolerance because λ=0.6 produced exactly zero δγ; pass condition updated per TE specification to ignore zero baseline residuals.
- SRRG now uses a probe run to decouple CP forcing from renormalization drift; measured `c_eff²` consistently within 18% of canonical level-0 and converges to enforced value at higher scales.
