# Reproduction Instructions

**Paper:** Black Hole Unitarity via Reflexive Unitarity and Stinespring Dilation

---

## Requirements

- Python 3.9+
- numpy >= 1.24.0
- scipy >= 1.10.0
- qutip >= 4.7.0
- matplotlib >= 3.7.0

Install all dependencies:

```bash
pip install numpy>=1.24.0 scipy>=1.10.0 qutip>=4.7.0 matplotlib>=3.7.0
```

Or using the code companion's requirements file:

```bash
pip install -r bh_unitarity/requirements.txt
```

---

## Source Code

The GKSL and Stinespring computations are implemented in:

```
MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src/
  te2_4_hilbert_space.py      — Hilbert space construction
  te2_4_gksl_constructor.py   — GKSL master equation
  te2_4_stinespring.py        — Stinespring dilation
  te2_4_jt_toy_model.py       — JT-like toy model driver
```

---

## Running the Computations

### Option 1: Thin wrapper (recommended)

From the repository root:

```bash
cd bh_unitarity
python run_stinespring_analysis.py
```

This reproduces the Stinespring analysis, reports F, Choi trace preservation
error, and dim(H_E), and saves results to `bh_unitarity/results/stinespring_results.json`.

### Option 2: Run the full TE2.4 suite directly

```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src
python te2_4_jt_toy_model.py
```

This regenerates `results/phase2_3_final/final_results.json`.

### Option 3: Run individual modules

```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src
python te2_4_stinespring.py   # Stinespring dilation tests
```

---

## Expected Outputs

| Quantity | Expected Value |
|---|---|
| `fidelity_with_thermal` | 0.9999192951 |
| Stinespring fidelity F (min) | ≥ 1 − 10⁻⁸ |
| `dim(H_E)` | 7 |
| Choi trace preservation error | ≤ 10⁻¹⁰ |
| Detailed balance error | 0.00% |
| CPTP validation | PASS |

---

## Primary Data File

```
MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/phase2_3_final/final_results.json
```

SHA-256: `bf2b079c9f3d2850434430356e9f4b1d49b448e6154c1cf808d348a730159b36`

Verify:

```bash
shasum -a 256 MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/phase2_3_final/final_results.json
```

---

## Building the PDF

From the `papers/16_bh_unitarity/` directory:

```bash
pdflatex BH_Reflexive_Unitarity.tex
bibtex BH_Reflexive_Unitarity
pdflatex BH_Reflexive_Unitarity.tex
pdflatex BH_Reflexive_Unitarity.tex
```

Requires a standard LaTeX distribution (TeX Live or MiKTeX) with the
following packages: `amsmath`, `amssymb`, `amsthm`, `geometry`, `microtype`,
`authblk`, `booktabs`, `graphicx`, `xcolor`, `url`, `hyperref`, `cite`,
`lmodern`.
