# UGP Discovery Lab - Experiment Index

This document provides an overview of all available experiments in the UGP Discovery Lab.

## Available Experiments

### ca_universality

**Description:** CA Universality test with multiple rules

**Configuration:** `configs/experiments/ca_universality_test.yaml`

**YAML Schema:**
```yaml
experiment:
  description: CA Universality test with multiple rules
  name: ca_universality
  tests:
  - name: rule110_32x64
    rule: rule110
    seed:
    - 0
    - 0
    - 0
    - 1
    - 1
    - 1
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    steps: 64
    width: 32
    wrap: true
  - name: rule54_32x64
    rule: rule54
    seed:
    - 0
    - 0
    - 0
    - 1
    - 1
    - 1
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    steps: 64
    width: 32
    wrap: true
  - name: rule30_32x64
    rule: rule30
    seed:
    - 0
    - 0
    - 0
    - 1
    - 1
    - 1
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    steps: 64
    width: 32
    wrap: true
  - name: rule110_64x128
    rule: rule110
    seed:
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 0
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    steps: 128
    width: 64
    wrap: true
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/ca_universality_test.yaml
```

---

### dihedral_consistency

**Description:** Fit Dihedral-Lock planes; test 2cos(pi/n) and PSLQ alternatives

**Configuration:** `configs/experiments/dihedral_consistency.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Fit Dihedral-Lock planes; test 2cos(pi/n) and PSLQ alternatives
  fit:
    algebraic_basis:
    - sqrt2
    - sqrt3
    - phi
    - sqrt(2+sqrt2)
    - sqrt(10+2sqrt5)/2
    - (sqrt6+sqrt2)/2
    min_points: 200
    min_r2: 0.997
    pslq_max_denominator: 64
  hypotheses:
  - form: alpha = 1/(2*cos(pi/n))
  - form: alpha = rational
  - form: alpha = algebraic_combination
  inputs:
    runs:
    - UGP_discovery_lab_runs/**/dihedral_lock_*_summary.json
  name: dihedral_consistency
  report:
    export_json: true
    export_md: true
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/dihedral_consistency.yaml
```

---

### dihedral_lock

**Description:** Search Dihedral-Lock planes for n ∈ {5,6,8,10,12}

**Configuration:** `configs/experiments/dihedral_lock_search.yaml`

**YAML Schema:**
```yaml
experiment:
  description: "Search Dihedral-Lock planes for n \u2208 {5,6,8,10,12}"
  diagnostics:
    kernel_plane_fit: true
  dihedral:
    n_list:
    - 5
    - 6
    - 8
    - 10
    - 12
    samples_per_class: 20
    windows:
    - 10
    - 11
  fit:
    max_denominator: 16
    min_r2: 0.995
  name: dihedral_lock
  run:
    steps: 64
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/dihedral_lock_search.yaml
```

---

### index_lock

**Description:** Detect fixed |q_t - q_{t-1}| locks at ridge/mirror events

**Configuration:** `configs/experiments/index_lock_detection.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Detect fixed |q_t - q_{t-1}| locks at ridge/mirror events
  detection:
    event_types:
    - ridge
    - mirror
    min_support: 20
    tolerance: 0
  inputs:
    runs:
    - UGP_discovery_lab_runs/exp_20250917_110313
  name: index_lock
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/index_lock_detection.yaml
```

---

### kernel_fit

**Description:** Generic kernel plane fitting across different UGP evolutions

**Configuration:** `configs/experiments/kernel_fit_generic.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Generic kernel plane fitting across different UGP evolutions
  fit:
    models:
    - form: kM = kG + alpha*kL
      max_denominator: 16
    - form: kM = a*kG + b*kL + c
      max_denominator: 16
    thresholds:
      min_points: 50
      min_r2: 0.995
  name: kernel_fit
  sources:
  - glob: '*.json'
    name: LE_gte_lucas
    run_dir: UGP_discovery_lab_runs/exp_20250917_110313
  - glob: '*.json'
    name: LE_repunit
    run_dir: UGP_discovery_lab_runs/exp_20250917_110313
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/kernel_fit_generic.yaml
```

---

### lawful_evolution

**Description:** GTE-DIHEDRAL-D6: test D6 symmetry group for dihedral locks

**Configuration:** `configs/experiments/gte_dihedral_d6.yaml`

**YAML Schema:**
```yaml
experiment:
  description: 'GTE-DIHEDRAL-D6: test D6 symmetry group for dihedral locks'
  diagnostics:
    dihedral_lock_search: true
    kernel_plane_fit: true
  le_config:
    a_policy: gte
    b_policy: fib
    c_policy: mersenne
    mirror: d6
    triggers:
      mirror: true
      ridge: true
  name: lawful_evolution
  run:
    seed:
    - 1
    - 73
    - 823
    steps: 200
    windows:
    - 10
    - 11
    - 12
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/gte_dihedral_d6.yaml
```

---

### lock_stability

**Description:** Stress test lock laws across seeds/scales/policy variants.

**Configuration:** `configs/experiments/lock_stability.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Stress test lock laws across seeds/scales/policy variants.
  fit:
    dihedral:
      min_r2: 0.996
      pslq_max_denominator: 64
    index:
      min_support: 25
      tolerance: 0
    quarterlock:
      tol: 1e-6
  name: lock_stability
  params:
    laws:
    - a_policy: gte
      b_policy: fib
      c_policy: mersenne
      mirror: d2
    - a_policy: gte
      b_policy: lucas
      c_policy: mersenne
      mirror: d2
    - a_policy: gte
      b_policy: fib
      c_policy: repunit
      mirror: d2
      repunit_base: 3
    seeds:
    - - 1
      - 73
      - 823
    - - 1
      - 73
      - 2137
    - - 2
      - 89
      - 1597
    - - 3
      - 97
      - 2203
    windows:
    - 10
    - 11
    - 12
    - 13
  report:
    export_md: true
    heatmaps: true
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/lock_stability.yaml
```

---

### noether_current_scan

**Description:** Search for conserved linear forms J(M,G,L) under PR-1

**Configuration:** `configs/experiments/noether_scan.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Search for conserved linear forms J(M,G,L) under PR-1
  name: noether_current_scan
  report:
    export_json: true
    export_md: true
  runs:
  - UGP_discovery_lab_runs/**/LE_*_summary.json
  search:
    basis:
    - M
    - G
    - L
    degree: 1
    grid:
      coeffs:
      - -3
      - -2
      - -1
      - 0
      - 1
      - 2
      - 3
    max_hits: 5
    tolerance: 1e-8
  validation:
    max_steps: 500
    min_steps: 100
    require_real_data: false
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/noether_scan.yaml
```

---

### quarterlock_anchor

**Description:** Refit Quarter-Lock on independent data to anchor the coefficient exactly.

**Configuration:** `configs/experiments/quarterlock_anchor.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Refit Quarter-Lock on independent data to anchor the coefficient exactly.
  fit:
    min_points: 500
    model: kM = kG + alpha*kL
    target_value: 1/4
    tol_abs: 1e-6
  inputs:
    runs:
    - UGP_discovery_lab_runs/**/LE_gte_*_summary.json
  name: quarterlock_anchor
  report:
    export_json: true
    export_md: true
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/quarterlock_anchor.yaml
```

---

### reversible_core

**Description:** GTE-REVERSIBLE-CORE: reversible UWCA with entropy tracking

**Configuration:** `configs/experiments/gte_reversible_core.yaml`

**YAML Schema:**
```yaml
experiment:
  description: 'GTE-REVERSIBLE-CORE: reversible UWCA with entropy tracking'
  diagnostics:
    entropy_analysis: true
    information_conservation: true
  le_config:
    a_policy: gte
    b_policy: fib
    c_policy: mersenne
    entropy_tracking: true
    mirror: d2
    reversible: true
  name: reversible_core
  run:
    seed:
    - 1
    - 73
    - 823
    steps: 200
    windows:
    - 10
    - 11
    - 12
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/gte_reversible_core.yaml
```

---

### rg_cycle_detector

**Description:** Detect limit cycles in RG flow dynamics

**Configuration:** `configs/experiments/rg_cycle_detector.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Detect limit cycles in RG flow dynamics
  detection:
    clustering_eps: 1e-4
    cycle_tolerance: 1e-4
    max_cycles: 3
    min_cycle_length: 2
    min_samples: 2
  inputs:
    runs:
    - UGP_discovery_lab_runs/**/rg_flow_*_summary.json
  name: rg_cycle_detector
  report:
    export_json: true
    export_md: true
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/rg_cycle_detector.yaml
```

---

### rg_flow

**Description:** Iterate RG operator and detect fixed points/cycles

**Configuration:** `configs/experiments/rg_flow_analysis.yaml`

**YAML Schema:**
```yaml
experiment:
  description: Iterate RG operator and detect fixed points/cycles
  fit:
    max_denominator: 16
    model: kM = kG + alpha*kL
  input:
    source_run: UGP_discovery_lab_runs/exp_20250917_110313
  name: rg_flow
  rg:
    crop_policy: center
    initial_window: 64
    iterations: 8
    rescale_policy: normalize
  stopping:
    tol_cycle: 1e-4
    tol_param: 1e-3
    tol_plane: 1e-3
```

**Usage:**
```bash
ugp run-experiment -c configs/experiments/rg_flow_analysis.yaml
```

---

## General Usage

### Running Experiments

```bash
# Run a single experiment
ugp run-experiment -c configs/experiments/experiment_name.yaml

# Run with plots (requires matplotlib)
ugp run-experiment -c configs/experiments/experiment_name.yaml --plots

# Run with multiple workers
ugp run-experiment -c configs/experiments/experiment_name.yaml --workers 4
```

### Running Test Suites

```bash
# Run smoke tests (fast)
ugp run-suite -c configs/suites/smoke.yaml

# Run CI golden path
ugp run-suite -c configs/suites/ci_golden.yaml

# Run full validation suite
ugp run-suite -c configs/suites/validation_suite.yaml
```

### Other Commands

```bash
# List available experiments
ugp list-experiments

# List available suites
ugp list-suites

# Clean up old artifacts
ugp clean --all

# Generate this documentation
ugp docs --output docs/
```

## Configuration Schema

All experiment configurations follow this general structure:

```yaml
experiment:
  name: "experiment_name"
  description: "Brief description of the experiment"
  
  # Experiment-specific parameters
  param1: value1
  param2: value2
  
  run:
    # Runtime parameters
    steps: 1000
    workers: 2
    
  fit:
    # Fitting parameters
    model: "model_specification"
    tolerance: 1e-6
    
  report:
    # Reporting options
    export_md: true
    export_json: true
```

## Experiment Types

### Core Experiments
- **ca_universality**: Test computational universality of cellular automata
- **lawful_evolution**: Explore UGP-lawful evolution patterns
- **reversible_core**: Test reversible computation extensions

### Discovery Experiments
- **dihedral_lock**: Search for dihedral symmetry constraints
- **kernel_fit**: Fit algebraic relationships in kernel space
- **index_lock**: Detect fixed index patterns
- **rg_flow**: Analyze renormalization group dynamics

### Validation Experiments
- **quarterlock_anchor**: Validate Quarter-Lock coefficient
- **dihedral_consistency**: Test dihedral constant hypotheses
- **lock_stability**: Stress test across parameter space

### Advanced Experiments
- **noether_current_scan**: Search for conserved currents
- **rg_cycle_detector**: Detect limit cycles in RG flow
- **holographic_transducer**: Test holographic reconstruction

## Scientific Methodology

All experiments follow rigorous scientific methodology:

1. **Empirical Validation**: Constants derived from data, not assumptions
2. **Error Analysis**: Confidence intervals and tolerance specifications
3. **Reproducibility**: Hash-based run equivalence detection
4. **Provenance Tracking**: Complete metadata and system information

## Contributing

To add a new experiment:

1. Create the experiment class in `ugp_discovery_lab/experiments/`
2. Add configuration file in `configs/experiments/`
3. Register the experiment using `@register_experiment`
4. Update this documentation with `ugp docs`

---
*Generated by UGP Discovery Lab Documentation System*
