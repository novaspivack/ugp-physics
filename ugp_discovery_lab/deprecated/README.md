# UGP Discovery Lab — Deprecated

This directory holds code and configs that are **known to be wrong, incomplete, or superseded** for the PRE Dynamics & Universality paper. They are preserved for historical reference but **must not be used** for paper reproduction.

## configs_pre_epic04_fixes/

Experiment YAML configs that produced bad results or were superseded.

| File | Why deprecated |
|------|---------------|
| `statistical_mechanics.yaml` | Glob patterns match zero real files → silent synthetic fallback. 159 violations were from synthetic data, not real GTE. Replaced by `configs/experiments/statistical_mechanics_paper.yaml` + `run_entropy_analysis.py`. |
| `holographic_thermodynamics_extended.yaml` | Requires `pr1_trajectory_data.json` (not in repo) → unrunnable. Replaced by `run_gsl_fit.py`. |
| `holographic_thermodynamics.yaml` | Superseded by inline approach. |
| `holographic_thermodynamics_refined.yaml` | Superseded. |

## runs_defunct/

Archived run output directories from failed or superseded experiments. These live in `UGP_discovery_lab_runs/` by their original names (we don't move run dirs to avoid breaking git history). The following run names are known-defunct:

- `exp_20260412_stat_mech` — synthetic fallback, not real GTE
- `exp_20260412_stat_mech_real` — early fix, still had path resolution bug
- `exp_20260412_stat_mech_paper` — still had int→float bigint bug
- `exp_20260412_stat_mech_paper2` — fixed path but missed some trajectories
- `exp_20260412_stat_mech_paper3` — partial fix only
- `exp_20260412_233946` — 6-task rg_sweep before YAML base.py fix (used default grid)
- `exp_20260413_entropy` — CLI runner hung on 50K-step cumulative entropy; use `run_entropy_analysis.py` instead
- `exp_20260413_gsl` — CLI runner hung; use `run_gsl_fit.py` instead
- `exp_20260413_seed_partition` — `rg_seed_partition` reads wrong field structure from our runs → 0 rows; use `results/reports/rg_seed_partition_paper_summary.json`

## Key methodology finding (important!)

The `rg_sweep` kernel-plane surrogate is NOT the same as the real-GTE RG.
- Surrogate α\* (A/B/C): −0.0850, +0.0754, +0.2644 (kernel-plane Gaussian streams)
- Real GTE α_geo (A/B/C): 0.0571, 0.0141, 0.1326 (log-ratio kernel on actual (a,b,c))
Both sets are reproducible; they measure different things. The paper Table 1 reports the surrogate values (canonical from variational derivation); Table 2 reports real-GTE Q4 and α_geo.
