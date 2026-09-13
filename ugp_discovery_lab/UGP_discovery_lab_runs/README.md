# Frozen canonical lab runs (shipped with `ugp-physics`)

These directories mirror the **run IDs** referenced by `configs/experiments/*.yaml` and by `papers/04_dynamics/PROVENANCE.md`. They let you **re-run downstream analyses** (statistical mechanics on real GTE trajectories, RG figure export, meta-laws Q4/entropy pipelines) **without** regenerating multi-hour experiments first.

| Directory | Role |
|-----------|------|
| `exp_20250917_112647` … `exp_20250917_203952` | Lawful-evolution **`experiment_results.json`** inputs for `statistical_mechanics_paper.yaml` |
| `exp_20260412_rg_sweep_full` | Full **224-task** RG sweep JSON for `rg_seed_partition_paper.yaml` and `scripts/export_pre_dynamics_paper_figures.py` |
| `exp_20260413_deep_trajectories` | **24 × 50k-step** GTE trajectories (large JSON) feeding `gte_q4_basin_paper.yaml`, `gte_entropy_attractor_paper.yaml`, `gte_gsl_fit_paper.yaml`, `gte_rg_attractor_real_paper.yaml`, plus inline `run_entropy_analysis.py` / `run_gsl_fit.py` |

**Regenerating from scratch:** You may delete these folders and re-run the matching configs (see each paper’s `REPRODUCE.md`), then point YAML `inputs.runs` at your new `.../experiment_results.json` paths.

**Holographic transducer:** Older configs globbed `**/LE_*_summary.json`, but the current lawful-evolution pipeline stores trajectories in **`experiment_results.json`** only — those legacy filenames are not produced or archived. **`configs/experiments/holographic_transducer.yaml`** now points at a **bundled** `exp_20250917_112647/.../experiment_results.json` for path resolution; the transducer experiment still **synthesizes** boundary training data from its YAML (see `ugp_discovery_lab/experiments/holographic_transducer.py`).
