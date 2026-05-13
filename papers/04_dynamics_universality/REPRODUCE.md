# REPRODUCE — PRE: Dynamics & Universality

**Requires:** Python 3.10+, repository path `ugp_discovery_lab/` at the **clone root** of [`ugp-physics`](https://github.com/novaspivack/ugp-physics).

**Bundled inputs:** The repo ships **`ugp_discovery_lab/UGP_discovery_lab_runs/`** with canonical **`experiment_results.json`** files (RG sweep, deep trajectories, lawful-evolution inputs for statistical mechanics). See `UGP_discovery_lab_runs/README.md`. You can re-run long jobs from scratch instead; then point YAMLs and scripts at your new paths.

```bash
cd ugp_discovery_lab
python3.10 -m pip install -e ".[plots]"
python3.10 -m pip install scipy
```

## 1) CA universality (Rule 110 / 54 / 30)

```bash
python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/ca_universality_paper.yaml --workers 4 \
  --run-name ca_universality_paper_check
```

**Output:** `UGP_discovery_lab_runs/<run>/results/reports/experiment_results.json`

## 2) RG sweep (224 tasks, full grid)

```bash
python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/rg_sweep.yaml --workers 8 \
  --run-name rg_sweep_full
```

**Frozen canonical run (for figures / forensics):** `exp_20260412_rg_sweep_full` (see `paper_artifacts/rg_sweep_replication_20260412.json`).

## 3) Paper figures (`rg_convergence_plot.png`, `seed_partition_heatmap.png`)

From the lab root — default uses the **bundled** RG sweep JSON:

```bash
python3.10 scripts/export_pre_dynamics_paper_figures.py \
  --rg-json UGP_discovery_lab_runs/exp_20260412_rg_sweep_full/results/reports/experiment_results.json \
  --output-dir "../papers/04_dynamics_universality/figures"
```

If you used a different `--run-name` in step 2, point `--rg-json` at that run’s `experiment_results.json`.

## 4) Statistical mechanics (real GTE trajectories)

Use **`statistical_mechanics_paper.yaml`** (not `statistical_mechanics.yaml`, which is deprecated and can fall back to synthetic data — see `PROVENANCE.md`).

The bundled **`UGP_discovery_lab_runs/exp_20250917_*`** directories match the `inputs.runs` paths in the YAML.

```bash
python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/statistical_mechanics_paper.yaml --workers 2 \
  --run-name statistical_mechanics_paper_check
```

**Interpretation:** Compare reported monotonicity / violation counts to `PROVENANCE.md` (do **not** use the obsolete “159 violations” figure from deprecated synthetic runs).

Plots: `results/artifacts/statistical_mechanics/*_entropy_evolution.png` — copy one representative file to `figures/entropy_vs_time.png` if refreshing the manuscript figure.

## 5) Entropy–attractor analysis (inline, canonical)

Uses the bundled **deep trajectories** JSON (same backbone as the paper’s Pillar II entropy results):

```bash
python3.10 run_entropy_analysis.py
```

Writes `results/reports/gte_entropy_attractor_inline_summary.json` (see `PROVENANCE.md`).

## 6) GSL parameter fit (inline, canonical; Remark 3.1)

```bash
python3.10 run_gsl_fit.py
```

Reads `UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json` and writes `results/reports/gte_gsl_fit_inline_summary.json`.

**Do not use** `configs/experiments/holographic_thermodynamics_extended.yaml` — it is deprecated (`pr1_trajectory_data.json` not in repo); see `PROVENANCE.md` B1.

## 7) Holographic transducer (optional)

```bash
python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/holographic_transducer.yaml --workers 4 \
  --run-name holographic_transducer_check
```

**Inputs:** `holographic_transducer.yaml` lists a **bundled** lawful-evolution `experiment_results.json` so paths resolve in a clean clone. The experiment **generates** ridge/mirror boundary data from the YAML (it does not replay `LE_*_summary.json` files — that glob was legacy; the modern pipeline stores trajectories inside `experiment_results.json`).

## 8) Build the PDF

```bash
cd ../papers/04_dynamics_universality
latexmk -pdf -interaction=nonstopmode ugp_dynamics_universality.tex
```

Ensure `figures/` contains the PNGs referenced by `\includegraphics`.
