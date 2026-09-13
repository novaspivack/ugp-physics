# UGP Discovery Lab

YAML-driven experiment framework for exploring the **Universal Generative Principle (UGP)**: RG attractor discovery, law discovery (Quarter-Lock, Dihedral, Noether scans), cellular automaton universality, and rigorous statistical validation.

Optional author-local notebooks may live in `lab_notebooks/` (gitignored). See `README_NEW.md` for extended documentation.

---

## Installation

```bash
# From the ugp-physics repository root
pip install -e ugp_discovery_lab/
```

This installs the `ugp` CLI entry point and the `ugp_discovery_lab` Python package.

---

## Requirements

```bash
pip install numpy scipy sympy PyYAML
pip install matplotlib   # optional — for plots
pip install psutil       # optional — worker diagnostics (non-Windows)
```

All packages are listed in `requirements.txt` at the repository root.

---

## Quick start

```bash
# Run a single experiment
ugp run-experiment -c configs/experiments/quarterlock_anchor.yaml

# Run a suite of experiments
ugp run-suite -c configs/suites/validation_suite.yaml

# List what's available
ugp list-experiments
ugp list-suites
ugp list-checkpoints
```

---

## CLI reference

All commands run from the `ugp_discovery_lab/` directory (or anywhere if the package is installed).

### `ugp run-experiment`

```
ugp run-experiment -c/--config CONFIG.yaml
    [--workers N]         parallel workers (default: cpu_count/2)
    [--run-name NAME]     label for the run directory
    [--analysis-only]     analyze existing real data only; no synthetic generation
    [--plots]             emit matplotlib figures (requires matplotlib)
    [-v/--verbose]        detailed logging
```

### `ugp run-suite`

Same flags as `run-experiment`. Runs every experiment listed in the suite YAML.

### `ugp resume`

```
ugp resume -c CONFIG.yaml [--workers N] [-v]
```

Resumes from the most recent checkpoint for that config.

### `ugp clean`

```
ugp clean [--checkpoints] [--logs] [--artifacts] [--all]
          [--max-age-days N] [--dry-run]
```

### `ugp docs`

```
ugp docs [--output DIR]    generate HTML docs (default: docs/)
```

---

## Data modes

### Analysis-only (real UGP data)

Use `--analysis-only` to analyze existing run results without generating synthetic data. The config must specify `inputs.runs` pointing to real result files.

```bash
ugp run-experiment -c configs/experiments/equivalence_test_attractor_b.yaml --analysis-only
```

### Normal mode (synthetic data)

Default. Generates neutral synthetic data when no real data sources are found. Use for initial hypothesis testing and CI.

```bash
ugp run-experiment -c configs/experiments/quarterlock_anchor.yaml
```

---

## Key experiment categories

### RG attractor validation

Three universal RG attractors have been confirmed across 1,002 runs with machine-precision reproducibility:

| Attractor | Value | Basin fraction |
|---|---|---|
| A | −0.08503468530335825 | 37.8% |
| B | +0.07541304042454709 | 29.2% |
| C | +0.2644176695649741 | 25.8% |

```bash
ugp run-suite -c configs/suites/validation_suite.yaml --analysis-only
ugp run-experiment -c configs/experiments/equivalence_test_attractor_b.yaml --analysis-only
ugp run-experiment -c configs/experiments/rg_sweep.yaml
```

### Law discovery

```bash
# Quarter-Lock validation
ugp run-experiment -c configs/experiments/quarterlock_anchor.yaml

# Dihedral lock search
ugp run-suite -c configs/suites/dihedral_search.yaml

# Noether conservation scan
ugp run-experiment -c configs/experiments/noether_cubic_scan.yaml
```

### Cellular automaton universality

```bash
ugp run-experiment -c configs/experiments/ca_universality_test.yaml
```

### Full validation suite

```bash
ugp run-suite -c configs/suites/full_lab.yaml
```

---

## Package structure

```
ugp_discovery_lab/
├── cli/              ugp CLI (ugp.py)
├── core/             config loading, registry, checkpointing, workers, logging
├── experiments/      ~38 registered experiment classes
├── diagnostics/      metrics, stats, algebraic basis, data linter, plotting
├── engines/          UWCA (cellular automaton), reversible core
└── utils/            shared utilities
configs/
├── experiments/      ~42 per-experiment YAML configs
└── suites/           ~12 suite YAMLs
```

---

## Scientific integrity features

- **Data integrity linter** — automatically detects and blocks biased synthetic data generators (forbidden imports, suspicious hardcoded relationships).
- **Analysis-only mode** — enforces that real data is not contaminated by synthetic generation.
- **Claims gate system** — independent derivation consistency, out-of-sample persistence, null model resistance, and provenance checks must all pass before a claim is registered.
- **Full provenance tracking** — every run is timestamped and logged under `UGP_discovery_lab_runs/`.

---

## Adding a new experiment

1. Create a class in `ugp_discovery_lab/experiments/your_experiment.py` that subclasses `Experiment`.
2. Decorate with `@register_experiment("name")`.
3. Implement `tasks()` and `run_task()`.
4. Create `configs/experiments/your_experiment.yaml`.
5. Run: `ugp run-experiment -c configs/experiments/your_experiment.yaml`.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `"Analysis-only mode requires non-empty inputs.runs"` | Config missing `inputs.runs` | Add real data paths to config |
| `"Unknown experiment: ..."` | Class not registered or import error | Check `experiments/__init__.py` |
| `"Data integrity issues detected"` | Biased generator detected | Remove suspicious fields from data config |
| `"No lawful evolution data found, generating synthetic data"` | Expected files not found | Use `--analysis-only` with correct paths, or let synthetic run normally |
