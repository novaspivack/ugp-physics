# bh_unitarity — Code Companion

Companion code for:

**Black Hole Unitarity via Reflexive Unitarity and Stinespring Dilation:
A GKSL Model in a JT-like PSC Universe**
Nova Spivack, 2026

---

## What This Code Does

This directory provides a self-contained entry point for reproducing the
GKSL master equation and Stinespring dilation analysis reported in the paper.

The computation models Hawking evaporation as a GKSL (Gorini–Kossakowski–
Lindblad–Sudarshan) master equation acting on a finite-dimensional Fock
space for a 1+1D JT-like black hole. It then constructs an explicit
Stinespring dilation — a unitary on the enlarged system-plus-environment
Hilbert space — and verifies that the open-system dynamics are unitarily
equivalent to reversible evolution on H ⊗ H_E.

### Key results reproduced

| Quantity | Value |
|---|---|
| Steady-state fidelity with thermal state | 0.9999192951 |
| Stinespring fidelity (min over test states) | ≥ 1 − 10⁻⁸ |
| Environment dimension dim(H_E) | 7 |
| Choi trace preservation error | ≤ 10⁻¹⁰ |

### Model parameters

| Parameter | Value |
|---|---|
| n_modes | 3 |
| n_levels_per_mode | 2 |
| T_H | 0.003979 |
| coupling (γ₀) | 0.01 |
| dim(H) | 8 |
| dim(H_E) | 7 |

---

## Source Code

The underlying implementation lives in:

```
MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src/
  te2_4_hilbert_space.py       — Hilbert space construction and density matrix ops
  te2_4_gksl_constructor.py    — GKSL master equation, Lindblad operators, CPTP check
  te2_4_stinespring.py         — Stinespring dilation, Kraus operators, fidelity check
  te2_4_jt_toy_model.py        — Top-level driver; produces final_results.json
```

The wrapper script in this directory (`run_stinespring_analysis.py`) imports
from that source tree and runs the Stinespring analysis, saving results to
`bh_unitarity/results/stinespring_results.json`.

---

## Installation

Python 3.9 or later is required.

```bash
pip install -r bh_unitarity/requirements.txt
```

Or install the core dependencies directly:

```bash
pip install numpy>=1.24.0 scipy>=1.10.0 qutip>=4.7.0 matplotlib>=3.7.0
```

---

## Running

From the repository root:

```bash
python bh_unitarity/run_stinespring_analysis.py
```

Or from within this directory:

```bash
cd bh_unitarity
python run_stinespring_analysis.py
```

Expected terminal output:

```
Stinespring dilation initialized:
  System dimension: 8
  Environment dimension: 7
  Total dimension: 56

Results:
  Stinespring fidelity (min):  F = 1.000000e+00  (>= 1 - 1e-8: PASS)
  Choi trace preservation:     error = <1e-10     PASS
  dim(H_E):                    7

Results saved to bh_unitarity/results/stinespring_results.json
```

See `REPRODUCE.md` for full step-by-step instructions, including SHA-256
verification of the primary data file.

---

## Primary Data

```
MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/phase2_3_final/final_results.json
SHA-256: bf2b079c9f3d2850434430356e9f4b1d49b448e6154c1cf808d348a730159b36
```
