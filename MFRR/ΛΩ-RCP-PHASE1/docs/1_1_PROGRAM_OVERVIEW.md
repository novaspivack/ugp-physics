# 1.1 Program Overview: ΛΩ-RCP (Reflexive Closure Program)

## Cross-References

- See [1.2 Theorems and Lemmas](1_2_THEOREMS_AND_LEMMAS.md) for theoretical foundations
- See [1.3 Test Specifications](1_3_TEST_SPECIFICATIONS.md) for detailed test plans
- See [1.4 Implementation Details](1_4_IMPLEMENTATION_DETAILS.md) for code architecture

## Program Mission

The **ΛΩ-RCP (Reflexive Closure Program)** validates the mathematical foundations of Reflexive Reality by testing three foundational lemmas and five frontier theorems that extend the framework along its remaining unclosed axes:

1. **Dimensional closure** (Λ–Φ duality)
2. **Observer recursion** (complexity invariance)
3. **Energetic hierarchy** (meta-reflexive energy conservation)
4. **Quantum-field unification** (SRRG–RG duality)
5. **Information-geometric closure** (Profit–Curvature equivalence)

## Program Structure

```
ΛΩ-RCP/
├── src/rcp/          # Core implementation modules
├── cfg/              # Configuration files (config.yaml)
├── data/             # Input data (if needed)
├── results/          # Output files (CSV, JSON, plots)
├── logs/             # Execution logs
├── docs/             # Documentation (.md files)
└── env/              # Virtual environment
```

## Five Core Tests

### Lemma Tests (L1–L3)

- **L1**: Fisher Heat–Kernel Scaling → Spectral Dimension vs. Curvature
- **L2**: Recursive Bundle Action → Meta-Adjudication Stress and Landauer Hierarchy
- **L3**: Observer Complexity Lower Bound → PSC Stability vs. Observer Capacity

### Frontier Tests (RG, PC)

- **RG**: SRRG–RG Duality → β-function equivalence in Gaussian/ϕ⁴ sectors
- **PC**: Profit–Curvature Identity → log(Gen/Drain) vs. ∫R_F slope ≈ Λ

## Acceptance Criteria Summary

| Test | Primary Metric | Acceptance Threshold |
|------|----------------|---------------------|
| L1   | intercept ≈ d, slope ≈ Λ | ±0.05 intercept, ±10% slope |
| L2   | energy slope vs. log(depth) | ±10% of k_B T |
| L3   | threshold capacity c* | ±20% of generator complexity |
| RG   | mean relative β-error | < 15% in perturbative regime |
| PC   | slope a in log(Gen/Drain) | ±10% of Λ |

## Quick Start

```bash
cd ΛΩ-RCP
make init      # Create venv and install dependencies
make all       # Run all five tests
```

## Output Files

Each test produces:
- `results/{test}_records.csv` - Raw data records
- `results/{test}_summary.json` - PASS/FAIL status and key metrics

## Next Steps

1. Review [1.2 Theorems and Lemmas](1_2_THEOREMS_AND_LEMMAS.md) for formal statements
2. Review [1.3 Test Specifications](1_3_TEST_SPECIFICATIONS.md) for computational protocols
3. Execute tests: `make all`
4. Analyze results against acceptance criteria

