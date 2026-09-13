# PROVENANCE — PRE: Dynamics & Universality of the UGP

**Paper:** `ugp_dynamics_universality.tex`  
**Primary code root:** `ugp_discovery_lab/` at the **clone root** of [`ugp-physics`](https://github.com/novaspivack/ugp-physics) (Python ≥ 3.10)  
**Last updated:** 2026-04-13

---

## PART A — Canonical code and artifacts for reproducing every result in the paper

These are the ONLY files needed to reproduce the paper. All others are either deprecated, intermediate, or from other papers.

### A1. Installation

```bash
cd ugp_discovery_lab
python3.10 -m pip install -e ".[plots]"   # matplotlib included
python3.10 -m pip install scipy           # for ANOVA / Mann-Whitney
```

### A2. Experiment entry points (in paper section order)

| Paper section / result | Experiment | Config (canonical) | Run name (frozen) |
|---|---|---|---|
| Pillar I: CA Universality (Theorem 1) | `ca_universality` | `configs/experiments/ca_universality_paper.yaml` | `exp_20260412_ca_paper` |
| Pillar I: Reversible Core (Prop 1) | `reversible_core` | `configs/experiments/gte_reversible_core.yaml` | archived Sep 2025 runs |
| Pillar I: Lawful Evolutions | `lawful_evolution` | `configs/experiments/lawful_evolution.yaml` | archived Sep 2025 runs |
| Pillar II: RG α\* values (Table 1) | `rg_fixedpoint_variational` + `rg_fixedpoint_spectral` | `configs/experiments/rg_fixedpoint_variational.yaml` | `results/reports/rg_fixedpoint_variational_attractor_{b,c}_summary.json` |
| Pillar II: Q4 per basin + ANOVA (Table 2) | `gte_deep_trajectories` + inline analysis | `configs/experiments/gte_deep_trajectories_paper.yaml` + `run_entropy_analysis.py` | `exp_20260413_deep_trajectories` |
| Pillar II: Log-ratio attractor α_geo | same as above | same | same |
| Pillar II: Basin classification 91.7% | `gte_rg_attractor_real` | `configs/experiments/gte_rg_attractor_real_paper.yaml` | `exp_20260413_rg_real` |
| Pillar II: Holographic (Theorem 3) | `holographic_transducer` | `configs/experiments/holographic_transducer.yaml` | `exp_20250917_{123821,124054,124117,125845,130911,135337}` |
| Pillar II: Entropy collapse (Prop 3) | inline script | `configs/experiments/gte_deep_trajectories_paper.yaml` + `run_entropy_analysis.py` | `exp_20260413_deep_trajectories` |
| Pillar II: GSL Remark (Remark 3.1) | inline script | `configs/experiments/gte_deep_trajectories_paper.yaml` + `run_gsl_fit.py` | `exp_20260413_deep_trajectories` |

### A3. Frozen artifact ledger

| Artifact | Path | Role |
|----------|------|------|
| RG α\* variational (A) | `results/reports/rg_fixedpoint_variational_summary.json` | Gold standard α\* for attractor A |
| RG α\* variational (B) | `results/reports/rg_fixedpoint_variational_attractor_b_summary.json` | Gold standard α\* for attractor B |
| RG α\* variational (C) | `results/reports/rg_fixedpoint_variational_attractor_c_summary.json` | Gold standard α\* for attractor C |
| RG α\* spectral | `results/reports/rg_fixedpoint_spectral_summary.json` | Independent spectral confirmation |
| Deep trajectories summary | `results/reports/gte_deep_trajectories_summary.json` | 1.2M step metadata |
| Q4 ANOVA summary | `results/reports/gte_q4_basin_analysis_summary.json` | F=13.7M, p≈0, per-basin stats |
| Entropy attractor summary | `results/reports/gte_entropy_attractor_inline_summary.json` | r=0.9998, 100% collapse, shuffle null |
| GSL fit summary | `results/reports/gte_gsl_fit_inline_summary.json` | Modal C=0.3, p=0.25, improvement 0.6% |
| rg_sweep SHA-256 | `04_PRE_Dynamics_Universality/paper_artifacts/rg_sweep_replication_20260412.json` | Forensic verification of 1080/92.8% |
| Seed partition | `results/reports/rg_seed_partition_paper_summary.json` | Per-seed basin assignment from canonical sweep |

### A4. Paper figures

| Figure file | Source | How generated |
|-------------|---------|---------------|
| `figures/rg_convergence_plot.png` | `exp_20260412_rg_sweep_full` JSON | `scripts/export_pre_dynamics_paper_figures.py` |
| `figures/seed_partition_heatmap.png` | same | same script |
| `figures/entropy_vs_time.png` | `results/artifacts/statistical_mechanics/` | copied from stat_mech run; regenerate via `statistical_mechanics_paper.yaml` |

### A5. Inline analysis scripts (not CLI experiments)

| Script | What it computes |
|--------|-----------------|
| `run_entropy_analysis.py` | Entropy series, peak, slope, shuffle null, attractor convergence r=0.9998 |
| `run_gsl_fit.py` | GSL parameter grid search (C, p) across 24 trajectories |

---

## PART B — Deprecated / superseded code and artifacts

The following exist in the lab but are **NOT used in the paper** for the listed reasons. They are moved to `ugp_discovery_lab/deprecated/` so they do not confuse future work.

### B1. Experiment configs — deprecated

| Config | Status | Reason |
|--------|--------|--------|
| `configs/experiments/statistical_mechanics.yaml` | **DEPRECATED** | Uses glob patterns that match zero real files → silent synthetic fallback. Replaced by `statistical_mechanics_paper.yaml` + inline script. |
| `configs/experiments/holographic_thermodynamics_extended.yaml` | **DEPRECATED** | Requires `pr1_trajectory_data.json` not in repo → unrunnable. Replaced by `run_gsl_fit.py`. |
| `configs/experiments/holographic_thermodynamics.yaml` | **DEPRECATED** | Superseded by inline approach. |
| `configs/experiments/holographic_thermodynamics_refined.yaml` | **DEPRECATED** | Superseded. |

### B2. Frozen run directories — NOT canonical

| Run dir | Status | Reason |
|---------|--------|--------|
| `UGP_discovery_lab_runs/exp_20260412_stat_mech/` | **DEFUNCT** | Synthetic fallback data, not real GTE. 159 violations were from synthetic not real trajectories. |
| `UGP_discovery_lab_runs/exp_20260412_stat_mech_real/` | **DEFUNCT** | Early fix attempt, still had path resolution issue. |
| `UGP_discovery_lab_runs/exp_20260412_stat_mech_paper/` | **DEFUNCT** | Still had int-log bug. |
| `UGP_discovery_lab_runs/exp_20260412_stat_mech_paper2/` | **DEFUNCT** | Same. |
| `UGP_discovery_lab_runs/exp_20260412_stat_mech_paper3/` | **DEFUNCT** | Same. |
| `UGP_discovery_lab_runs/exp_20260412_233946/` | **DEFUNCT** | First 6-task rg_sweep before YAML nesting fix, used default grid. |
| `UGP_discovery_lab_runs/exp_20260412_rg_sweep_full/` | **CANONICAL** | Full 224-task sweep after fix. Used for SHA-256 in paper_artifacts. |
| `UGP_discovery_lab_runs/exp_20260413_deep_trajectories/` | **CANONICAL** | 1.2M real GTE steps, backbone of all strengthening results. |
| `UGP_discovery_lab_runs/exp_20260413_q4/` | Supplementary | Q4 via experiment runner (succeeded but inline script is canonical). |
| `UGP_discovery_lab_runs/exp_20260413_rg_real/` | Supplementary | RG attractor real experiment (showed α→0 in surrogate kernel mapping). |
| `UGP_discovery_lab_runs/exp_20260413_entropy/` | **DEFUNCT** | Experiment hung (50K-step cumulative entropy very slow in runner). Use inline script. |
| `UGP_discovery_lab_runs/exp_20260413_gsl/` | **DEFUNCT** | Experiment hung. Use inline script. |
| `UGP_discovery_lab_runs/exp_20260413_seed_partition/` | **DEFUNCT** | `rg_seed_partition` reads wrong format from our runs → 0 rows. Use `rg_seed_partition_paper_summary.json`. |

### B3. Methodology findings (important for future work)

1. **`rg_sweep` kernel-plane surrogate ≠ real GTE RG.** The `rg_sweep` experiment uses synthetic Gaussian kernel streams. On real GTE, the log-ratio kernel `α_geo = log|c|/(log|a|+log|b|)` is the natural attractor measure. The surrogate α\* values (−0.085, +0.075, +0.264) are valid as self-consistent fixed points of the surrogate operator, but they do not equal the real-GTE α_geo values (0.057, 0.014, 0.133 for A, B, C respectively).

2. **`holographic_thermodynamics_extended` GSL result (60% improvement, C=0.4, p=1.0) is unsubstantiated.** The required input file `pr1_trajectory_data.json` does not exist in the repo. The real-GTE GSL fit gives C=0.3, p=0.25, only 0.6% improvement, and weak ΔS-I_holo correlation (r=0.08). The GSL is demoted to a Remark in the paper.

3. **`statistical_mechanics.py` glob patterns matched zero files.** The patterns `**/LE_*_summary.json`, `**/lawful_evolution_*_summary.json`, `**/gte_*_summary.json` do not exist as files — all results are stored as `experiment_results.json`. The `evolution_history` field was also not handled. Both bugs are fixed in the current version.

---

## PART C — Integrity and config resolution notes

- **YAML `experiment:` block fix (2026-04-12):** `base.Experiment` now extracts `cfg["experiment"]` when present. This fixed `rg_sweep` silently using a 6-task default grid instead of 224 tasks.
- **`statistical_mechanics` registration (2026-04-12):** Module was never imported in `__init__.py`.
- **`statistical_mechanics._coarse_grain_data` bigint fix (2026-04-12):** `np.log` on Python arbitrary-precision ints → `math.log`.
- **Holographic 100% clarification:** Linear model = 100% ✓, Quadratic = 100% ✓, Neural-1layer = 83% mean. Overall mean = 94.4%.
- **1080/92.8% forensics (2026-04-12):** Substantiated from 9 specific archived `rg_sweep` runs. A=408 exact, C=279 exact, B=317 vs 315 (Δ=2, archive variance). 

---

## PART D — Basin fractions from forensic reconstruction (informational)

From 9 archived `rg_sweep` runs (all pre-existing 2025 runs):

| Attractor | Count | Fraction |
|-----------|-------|---------|
| A | 408 | 37.8% |
| B | 317 | 29.3% |
| C | 279 | 25.8% |
| Other | 76 | 7.0% |
| **Total** | **1080** | |

Convergence rate (in A+B+C): 93.0% (paper: 92.8%, Δ=0.2%).

---

## PART E — New Artifacts (Paper 4 Revision 2026-04-20)

| Artifact | Script | SHA-256 | Date | Notes |
|----------|--------|---------|------|-------|
| `exp_holographic_gte/results/experiment_results.json` | `scripts/holographic_transducer_gte.py` | `0d75e90b…` | 2026-04-20 | COMP-P04-A: GTE-native holographic test — R²≈−9.4×10⁹ — claim REMOVED |
| `exp_holographic_gte/results/seed_q4_initial_report.json` | `scripts/seed_q4_initial_vs_basin.py` | `1f6a20c2…` | 2026-04-20 | COMP-P04-B: Q4 at step 0 is PREDICTIVE_INVARIANT (ANOVA p≈0) |
| `computational_concordance/basin_survey_100seeds_report.json` | (COMP-P12-A shared) | `e6999b18…` | (prior) | COMP-P04-C: 98-seed basin survey — C:39, A:34, B:25 |

## Key Revisions
- Holographic claim (previously: "100% reconstruction from synthetic CA data") is **RETRACTED**.
  GTE-native linear reconstruction yields mean R² ≈ −9.4×10⁹ (24 trajectories).
- Q4 confirmed as **predictive invariant** at seed initialization (not only trajectory-average label).
- "Three universal attractors" → "three observed basin clusters" throughout (scoped language).
- Claim-type taxonomy box [T]/[C]/[B]/[I] added to abstract.
- Lean proof appendix added (3 theorems: `uwca_sweep_implements_rule110`, `uwca_augmented_left_inverse`, `gte_entropy_prefix8_gt_prefix9`; ugp-lean 86 modules).
- `holographic_transducer.yaml` labeled: SYNTHETIC CA DATA — NOT GTE DATA.
