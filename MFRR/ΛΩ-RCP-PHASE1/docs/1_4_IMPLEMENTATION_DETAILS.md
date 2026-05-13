# 1.4 Implementation Details

## Cross-References

- See [1.1 Program Overview](1_1_PROGRAM_OVERVIEW.md) for program structure
- See [1.3 Test Specifications](1_3_TEST_SPECIFICATIONS.md) for computational protocols

## Module Architecture

### Core Utilities (`src/rcp/util.py`)

- `set_seed(s)`: Deterministic seeding for reproducibility
- `phi()`: Golden ratio \(\phi = \frac{1+\sqrt{5}}{2}\)
- `Lambda()`: Norfleet constant \(\Lambda = \frac{\ln \phi}{\ln(2\pi)}\)
- `save_json(obj, path)`: JSON serialization helper
- `ensure_dirs()`: Creates results/ and logs/ directories

### Graph and Geometry (`src/rcp/fisher_graphs.py`)

- `build_srrg_graph(seed, N, params)`: Constructs SRRG-like random graph
  - Uses distance-dependent edge probabilities: \(p_1 = 4/N\) (near), \(p_2 = 8/N\) (far)
- `fisher_metric_proxy(G)`: Estimates Fisher metric from node degrees
- `scalar_curvature_proxy(I)`: Computes curvature scalar from Fisher metric
- `omega_complexity(R, I)`: Computes geometric complexity \(\Omega = \sum |R_F| \sqrt{\det \mathcal{I}}\)

### Spectral Analysis (`src/rcp/spectral_dim.py`)

- `random_walk_return_probability(G, t, rng)`: Estimates return probability at time \(t\)
- `spectral_dimension(G, t_grid, seed)`: Estimates \(d_s\) via logarithmic scaling of return probability

### Test Modules

#### `run_l1.py`: Lemma 1 (Fisher Heat–Kernel Scaling)

1. Build graphs for multiple seeds and sizes
2. Compute \(\Omega\) and \(d_s\) for each
3. Fit linear model: \(d_s = \beta_0 + \beta_1 \log_\phi(\Omega)\)
4. Validate intercept ≈ 4.0 and slope ≈ Λ

#### `run_l2.py`: Lemma 2 (Meta–Reflexive Energy Conservation)

1. Simulate PT stack of varying depth \(n\)
2. Measure total energy \(E(n)\) and coherence term
3. Regress out coherence: \(y = E - \alpha \cdot \mathrm{coh}\)
4. Fit: \(y = \beta_0 + \beta_1 \log n\)
5. Validate slope ≈ \(k_B T\)

#### `run_l3.py`: Lemma 3 (Observer Complexity)

1. Generate manifold with known complexity \(K^*\)
2. Run PT with observer of varying capacity \(m\)
3. Measure PSC violation rate
4. Find threshold \(m^*\) where violations drop to < 0.01
5. Validate \(m^* \approx K^*\)

#### `run_rg.py`: SRRG–RG Duality

1. Run SRRG flow and Wilsonian blocking from same initial conditions
2. Estimate β-functions from trajectory differences
3. Compute relative error: \(\| \beta_{\mathrm{SRRG}} - \beta_{\mathrm{RG}} \| / \| \beta_{\mathrm{RG}} \|\)
4. Validate mean error < 15%

#### `run_pc.py`: Profit–Curvature Equivalence

1. Sample parametric family for varying \(\theta\)
2. Compute Fisher curvature and Gen/Drain
3. Fit: \(\log(\mathrm{Gen}/\mathrm{Drain}) = a \int R_F + b\)
4. Validate slope \(a \approx \Lambda\)

## Multiprocessing

All computationally intensive tests utilize cross-platform multiprocessing:

- **Default cores**: 8 of 10 available cores (configurable via `n_cores` in `cfg/config.yaml`)
- **Platform compatibility**: Uses `spawn` method for Windows/macOS/Linux compatibility
- **Parallelized tasks**:
  - **L1**: Graph generation and spectral dimension estimation across seeds and sizes
  - **L2**: PT stack simulation across depths and seeds
  - **L3**: Observer trials across capacities and seeds (most intensive)
  - **RG**: SRRG/Wilson flow comparison across seeds
  - **PC**: Profit-curvature sampling across parameter grid

### Multiprocessing Architecture

Each test implements a `process_*_task(args)` function that executes a single independent computational unit:

```python
with Pool(processes=n_cores) as pool:
    results = pool.map(process_task, tasks)
```

This design ensures:
- Maximum parallelization efficiency
- Clean process isolation
- Deterministic reproducibility (each task has unique seed)
- Cross-platform compatibility

## Configuration

All parameters are defined in `cfg/config.yaml`:

- **n_cores**: `8` (number of parallel processes, max 10)
- **Seeds**: `[101, 202, 303]` for deterministic reproducibility
- **Test-specific parameters**: See `cfg/config.yaml` for detailed thresholds and tolerances

## Execution

### Single Test

```bash
make l1    # Run Lemma 1 test
make l2    # Run Lemma 2 test
make l3    # Run Lemma 3 test
make rg    # Run SRRG–RG duality test
make pc    # Run Profit–Curvature test
```

### All Tests

```bash
make all   # Run all five tests sequentially
```

### Clean Results

```bash
make clean # Remove all results/ and logs/ files
```

## Output Format

Each test produces:

1. **CSV records**: `results/{test}_records.csv` - Raw data points
2. **JSON summary**: `results/{test}_summary.json` - PASS/FAIL status and key metrics

### JSON Summary Schema

```json
{
  "status": "PASS" | "FAIL",
  "key_metric": <value>,
  "expected": <value>,
  "tolerance": <value>,
  "pass": <boolean>
}
```

## Dependencies

- `numpy`: Numerical computations
- `scipy`: Scientific computing (if needed)
- `networkx`: Graph construction and analysis
- `pandas`: Data manipulation
- `matplotlib`: Plotting (optional)
- `numba`: JIT compilation (optional, for performance)
- `pyyaml`: Configuration file parsing

All dependencies installed via `make deps` after `make init`.

