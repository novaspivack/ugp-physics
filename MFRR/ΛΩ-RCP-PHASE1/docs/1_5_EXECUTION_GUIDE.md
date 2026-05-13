# 1.5 Execution Guide

## Cross-References

- See [1.1 Program Overview](1_1_PROGRAM_OVERVIEW.md) for program structure
- See [1.3 Test Specifications](1_3_TEST_SPECIFICATIONS.md) for acceptance criteria
- See [1.4 Implementation Details](1_4_IMPLEMENTATION_DETAILS.md) for technical architecture

## Quick Start

### 1. Initialize Environment

```bash
cd "ΛΩ-RCP"
make init
```

This will:
- Create a Python virtual environment in `env/.venv`
- Install all dependencies (numpy, scipy, networkx, pandas, matplotlib, numba, pyyaml)

### 2. Run All Tests

```bash
make all
```

This executes all five tests sequentially:
- L1: Fisher Heat–Kernel Scaling
- L2: Meta–Reflexive Energy Conservation
- L3: Observer Complexity Invariance
- RG: SRRG–RG Duality
- PC: Profit–Curvature Equivalence

### 3. Run Individual Tests

```bash
make l1    # Lemma 1 only
make l2    # Lemma 2 only
make l3    # Lemma 3 only
make rg    # SRRG–RG duality only
make pc    # Profit–Curvature only
```

## Performance

### Expected Runtime (8 cores, M1/M2 Mac)

| Test | Tasks | Est. Time | Peak Memory |
|------|-------|-----------|-------------|
| L1   | 9 graphs | ~3–5 min | ~2 GB |
| L2   | 15 depth runs | ~2–3 min | ~1 GB |
| L3   | 27 trials | ~8–12 min | ~3 GB |
| RG   | 3 seeds | ~1 min | ~500 MB |
| PC   | 15 samples | ~2 min | ~1 GB |
| **Total** | **69 parallel tasks** | **~15–25 min** | **~3 GB peak** |

### Multiprocessing Configuration

Edit `cfg/config.yaml` to adjust parallelism:

```yaml
n_cores: 8  # Change to 4, 6, 10, etc.
```

**Recommended settings:**
- **8 cores**: Balanced performance, leaves 2 cores for OS/other tasks
- **10 cores**: Maximum speed, may impact system responsiveness
- **4 cores**: Conservative, good for background execution

## Output Files

After execution, check `results/` directory:

```
results/
├── l1_records.csv         # Raw data: seed, N, Omega, ds
├── l1_summary.json        # PASS/FAIL status
├── l2_records.csv         # Raw data: seed, depth, E_total, coh_sum
├── l2_summary.json        # PASS/FAIL status
├── l3_records.csv         # Raw data: seed, capacity, violation_rate
├── l3_summary.json        # PASS/FAIL status
├── rg_records.csv         # Raw data: seed, mean_rel_beta_err
├── rg_summary.json        # PASS/FAIL status
├── pc_records.csv         # Raw data: seed, theta, R_scalar, profit
└── pc_summary.json        # PASS/FAIL status
```

## Interpreting Results

### PASS/FAIL Criteria

Each `*_summary.json` contains:

```json
{
  "status": "PASS" | "FAIL",
  "key_metric": <measured_value>,
  "expected": <target_value>,
  "tolerance": <threshold>,
  "pass": true | false
}
```

### Success Indicators

✅ **All tests PASS** → Lemmas validated, theorems conditionally proven

⚠️ **One test FAIL** → Review CSV records, check for numerical instabilities

❌ **Multiple FAIL** → May indicate implementation bug or incorrect assumptions

## Troubleshooting

### Issue: ImportError for yaml/networkx/etc.

**Solution:**
```bash
make deps  # Reinstall dependencies
```

### Issue: Multiprocessing hangs on Windows

**Solution:** Already handled via `spawn` start method in code. If persists, reduce `n_cores`:

```yaml
n_cores: 4
```

### Issue: Out of memory

**Solution:** Reduce problem sizes in `cfg/config.yaml`:

```yaml
lemma1:
  N_list: [1000, 2000, 4000]  # Reduced from [2000, 4000, 8000]
```

### Issue: Results directory not found

**Solution:**
```bash
mkdir -p results logs
make l1  # Or whichever test
```

## Clean Slate

To reset all results:

```bash
make clean
```

This removes all `results/*` and `logs/*` files while preserving the code and configuration.

## Next Steps

After successful execution:

1. Review all `*_summary.json` files for PASS/FAIL status
2. Examine `*_records.csv` files for detailed numerical results
3. Compare measured values against theoretical predictions
4. Document any deviations or unexpected findings
5. Proceed to manuscript integration of validated results

See [1.6 Results Integration](1_6_RESULTS_INTEGRATION.md) for guidance on incorporating findings into the main MFRR monograph.

