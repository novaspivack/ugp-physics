# Quick Start - TE_2.4 BH Unitarity

## Installation (One Command)

```bash
cd TE_2_4_BH_Unitarity
./setup_environment.sh
```

## Run Phase 1 Test

```bash
source venv/bin/activate
cd src
python te2_4_jt_toy_model.py
```

## Key Packages You Need

### Must Install:
```bash
pip install numpy scipy matplotlib qutip
```

### Optional (for later phases):
```bash
pip install jax jaxlib pandas seaborn
```

## What Each Package Does

| Package | Purpose | Phase |
|---------|---------|-------|
| **numpy** | Arrays, linear algebra | All |
| **scipy** | ODE integration (solve_ivp) | Phase 1 |
| **matplotlib** | Plotting | All |
| **qutip** | Quantum dynamics, GKSL, Stinespring | Phase 2-3 |
| jax | Auto-differentiation (Hessians) | TE_2.2, TE_2.3 |
| pandas | Data analysis | Optional |
| seaborn | Pretty plots | Optional |

## Check If You Have Everything

```bash
python3 << EOF
import numpy
import scipy
import matplotlib
import qutip
print("✓ All critical packages installed!")
EOF
```

## If Something Fails

### QuTiP not installing?
```bash
# Try conda instead
conda install -c conda-forge qutip
```

### Need JAX?
```bash
# CPU only (sufficient for our needs)
pip install jax jaxlib
```

### Python too old?
```bash
python3 --version
# Need ≥3.10
```

## That's It!

You're ready to run TE_2.4 Phase 1. See `README.md` for full details.

