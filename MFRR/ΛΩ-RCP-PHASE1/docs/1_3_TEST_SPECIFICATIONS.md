# 1.3 Test Specifications

## Cross-References

- See [1.1 Program Overview](1_1_PROGRAM_OVERVIEW.md) for acceptance criteria summary
- See [1.2 Theorems and Lemmas](1_2_THEOREMS_AND_LEMMAS.md) for theoretical foundations
- See [1.4 Implementation Details](1_4_IMPLEMENTATION_DETAILS.md) for code architecture

## Test L1: Fisher Heat–Kernel Scaling (Lemma 1)

### Objective

Validate the Λ–Φ duality by confirming that spectral dimension scales as:

\[
D_{\mathrm{eff}} = 4 + \Lambda \log_\phi(\Omega)
\]

### Computational Protocol

1. **Build SRRG graphs** for multiple seeds and sizes \(N \in \{2000, 4000, 8000\}\)
2. **Compute Fisher metric proxy** from graph degree distribution
3. **Estimate scalar curvature** \(R_F\) from Fisher metric
4. **Compute geometric complexity** \(\Omega = \sum |R_F| \sqrt{\det \mathcal{I}}\)
5. **Estimate spectral dimension** \(d_s\) via random-walk return probability over time grid \(t \in [10^{-2}, 10^1]\)
6. **Fit linear relation** \(d_s = \beta_0 + \beta_1 \log_\phi(\Omega)\)

### Acceptance Criteria

- **Intercept** \(\beta_0 \approx 4.0\) within ±0.05
- **Slope** \(\beta_1 \approx \Lambda \approx 0.2618\) within ±10%

### Output Files

- `results/l1_records.csv`: columns `[seed, N, Omega, ds]`
- `results/l1_summary.json`: `{intercept, slope, target_dim, lambda_expected, pass_intercept, pass_lambda, status}`

---

## Test L2: Meta–Reflexive Energy Conservation (Lemma 2)

### Objective

Validate the Reflexive Landauer Hierarchy by confirming energy scales as:

\[
E(n) \approx k_B T \log n + \alpha \sum_{i=1}^n \int \Psi_i^2
\]

### Computational Protocol

1. **Build PT stack** of depth \(n \in \{2, 3, 4, 6, 8\}\)
2. **Run transputation updates** for \(T = 750\) steps per layer
3. **Measure total energy** \(E(n)\) and coherence term \(\sum \int \Psi_i^2\)
4. **Regress out coherence**: \(y = E - \alpha \cdot \mathrm{coh}\)
5. **Fit linear relation**: \(y = \beta_0 + \beta_1 \log n\)

### Acceptance Criteria

- **Slope** \(\beta_1 \approx k_B T = 1.0\) within ±10% (after regressing coherence)

### Output Files

- `results/l2_records.csv`: columns `[seed, depth, E_total, coh_sum]`
- `results/l2_summary.json`: `{alpha_coh, slope_vs_log_depth, kbT_expected, pass, status}`

---

## Test L3: Observer Complexity Invariance (Lemma 3)

### Objective

Validate that PSC stability requires observer capacity \(m \ge K(\mathcal{M}_\Psi)\).

### Computational Protocol

1. **Generate manifold** with known complexity proxy \(K^* = 512\)
2. **Run PT with observer** of capacity \(m \in \{64, 96, ..., 768\}\)
3. **Measure PSC violation rate** over \(T = 2000\) steps
4. **Find threshold capacity** \(m^*\) where violation rate drops to < 0.01
5. **Compare** \(m^*\) to \(K^*\)

### Acceptance Criteria

- **Threshold capacity** \(m^*\) within ±20% of generator complexity \(K^* = 512\)

### Output Files

- `results/l3_records.csv`: columns `[seed, capacity, violation_rate]`
- `results/l3_summary.json`: `{c_star, k_star, relative_error, status}`

---

## Test RG: SRRG–RG Duality

### Objective

Validate that SRRG β-functions match Wilsonian RG β-functions in perturbative regime.

### Computational Protocol

1. **Initialize couplings** \(g_0 = (m^2, \lambda) = (1.0, 0.2)\)
2. **Run SRRG flow** for 40 steps with step size 0.1
3. **Run Wilsonian blocking** on \(64^2\) lattice
4. **Estimate β-functions** from trajectory differences
5. **Compute relative error** \(\| \beta_{\mathrm{SRRG}} - \beta_{\mathrm{RG}} \| / \| \beta_{\mathrm{RG}} \|\)

### Acceptance Criteria

- **Mean relative β-error** < 15% in perturbative regime

### Output Files

- `results/rg_records.csv`: columns `[seed, mean_rel_beta_err]`
- `results/rg_summary.json`: `{mean_rel_beta_err, tol, status}`

---

## Test PC: Profit–Curvature Equivalence

### Objective

Validate the exponential relation:

\[
\log(\mathrm{Gen}/\mathrm{Drain}) = \Lambda \int R_F + \mathrm{const}
\]

### Computational Protocol

1. **Sample parametric family** \(X \sim \mathcal{N}(\theta, 1)\) for \(\theta \in \{-1.0, -0.5, 0.0, 0.5, 1.0\}\)
2. **Compute Fisher metric** from empirical variance
3. **Estimate scalar curvature** \(R_F\)
4. **Compute Gen/Drain** from mean absolute value and standard deviation
5. **Fit linear relation**: \(\log(\mathrm{Gen}/\mathrm{Drain}) = a \int R_F + b\)

### Acceptance Criteria

- **Slope** \(a \approx \Lambda \approx 0.2618\) within ±10%

### Output Files

- `results/pc_records.csv`: columns `[seed, theta, R_scalar, profit]`
- `results/pc_summary.json`: `{slope, intercept, lambda_expected, status}`

---

## Configuration

All test parameters are defined in `cfg/config.yaml`. Default seeds: `[101, 202, 303]` for reproducibility.

