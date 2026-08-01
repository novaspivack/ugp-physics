# Installation Guide - TE_2.4 BH Unitarity

## Quick Start (Automated)

```bash
cd TE_2_4_BH_Unitarity
./setup_environment.sh
```

This will:
1. Check Python version (≥3.10 required)
2. Create virtual environment
3. Install all dependencies
4. Verify installations
5. Set up directory structure

---

## Manual Installation

### 1. Check Python Version

```bash
python3 --version
# Should be ≥3.10
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python3 -c "import numpy, scipy, matplotlib, qutip; print('✓ All core packages installed')"
```

---

## Key Dependencies

### Critical (Required)
- **NumPy** ≥1.24: Array operations
- **SciPy** ≥1.10: Integration (solve_ivp for ODEs)
- **Matplotlib** ≥3.7: Plotting
- **QuTiP** ≥4.7: Quantum dynamics (GKSL, Stinespring)

### Optional (Recommended)
- **JAX** ≥0.4: Automatic differentiation (for TE_2.2, TE_2.3)
- **Seaborn** ≥0.12: Enhanced plotting
- **Pandas** ≥2.0: Data analysis

---

## Special Notes

### QuTiP Installation

QuTiP is the most critical package for Phases 2 & 3. If you have issues:

```bash
# Try installing from conda-forge (if using conda)
conda install -c conda-forge qutip

# Or build from source
pip install git+https://github.com/qutip/qutip.git
```

### JAX Installation (Optional)

JAX requires specific CPU/GPU support:

```bash
# CPU-only (default)
pip install jax jaxlib

# For Apple Silicon Macs
pip install jax-metal

# For CUDA GPUs
pip install jax[cuda]
```

**Note:** JAX is optional for TE_2.4 but required for TE_2.2 and TE_2.3 (Hessian computations).

---

## Troubleshooting

### Issue: `ImportError: No module named 'qutip'`

**Solution:**
```bash
pip install qutip --upgrade
```

### Issue: `solve_ivp` fails with "required positional argument"

**Solution:** Update SciPy:
```bash
pip install scipy --upgrade
```

### Issue: QuTiP compilation errors on Mac

**Solution:** Install Xcode command-line tools:
```bash
xcode-select --install
pip install qutip --no-cache-dir
```

### Issue: JAX not found (but it's optional)

**Solution:** Either install JAX or ignore (only needed for TE_2.2/TE_2.3):
```bash
pip install jax jaxlib
```

---

## Verification Test

Run this to verify everything is working:

```bash
cd src
python te2_4_jt_toy_model.py
```

**Expected:** Should complete in ~1-2 minutes and produce:
```
============================================================
TE_2.4 Phase 1: 1+1D JT Gravity + Coherence Field
============================================================
...
✓ Phase 1 test complete!
============================================================
```

---

## Environment Variables

Add to your `~/.bashrc` or `~/.zshrc` for persistent setup:

```bash
# TE_2.4 Environment
export TE24_ROOT="/path/to/TE_2_4_BH_Unitarity"
export PYTHONPATH="${PYTHONPATH}:/path/to/TE_1_VALIDATION_PROGRAM"

# Activate function
te24() {
    cd "$TE24_ROOT"
    source venv/bin/activate
}
```

Then just run `te24` to activate the environment.

---

## Minimum System Requirements

- **CPU:** 4 cores (8-10 cores recommended)
- **RAM:** 8 GB (16 GB recommended)
- **Disk:** 2 GB free space
- **OS:** macOS, Linux, or Windows with WSL
- **Python:** 3.10 or higher

---

## Next Steps

After installation:

1. **Read README.md** for project overview
2. **Run Phase 1 test** (`python src/te2_4_jt_toy_model.py`)
3. **Check results** in `results/jt_toy_model/`
4. **Review** `TE_2_4_FINAL_REPORT.md` and `DELIVERABLES_SUMMARY.md` in this folder (private `../notes/` drafts are gitignored)

---

## Getting Help

If you encounter issues:

1. Check this troubleshooting section
2. Verify Python version: `python3 --version`
3. Check package versions: `pip list | grep -E "numpy|scipy|qutip"`
4. Review error messages carefully
5. Consult TE_2_X_6_IMPLEMENTATION_STRATEGY.md for context

---

**Last Updated:** November 20, 2025

