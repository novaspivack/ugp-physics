# 🚀 ΛΩ-RCP Quick Start

## One-Command Execution

```bash
cd "MFRR/ΛΩ-RCP-PHASE1"

make init && make all
```

## What This Does

1. Creates Python virtual environment
2. Installs dependencies (numpy, scipy, networkx, pandas, etc.)
3. Runs all 5 tests in parallel (8 cores):
   - **L1**: Fisher Heat–Kernel Scaling (Λ–Φ Duality)
   - **L2**: Meta-Reflexive Energy Conservation
   - **L3**: Observer Complexity Invariance
   - **RG**: SRRG–RG Duality
   - **PC**: Profit–Curvature Equivalence

## Expected Runtime

⏱️ **15–25 minutes** on 8 cores (M1/M2 Mac)

## Check Results

```bash
cd results
grep -h "status" *.json
```

✅ Look for **5 × "status": "PASS"**

## Full Documentation

- **Start here**: `docs/1_0_PROGRAM_STATUS.md`
- **How to run**: `docs/1_5_EXECUTION_GUIDE.md`
- **Theory**: `docs/1_2_THEOREMS_AND_LEMMAS.md`
- **All docs**: `docs/README.md`

## Program Status

✅ **COMPLETE & READY FOR EXECUTION**

- 11 Python modules
- 8 documentation files  
- 5 computational tests
- 69 parallel tasks
- Cross-platform multiprocessing

---

**Built on November 6, 2025**
