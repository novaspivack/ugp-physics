# Reproduction Instructions

**Code companion for:**
Black Hole Unitarity via Reflexive Unitarity and Stinespring Dilation:
A GKSL Model in a JT-like PSC Universe

---

## Requirements

- Python 3.9+
- numpy >= 1.24.0
- scipy >= 1.10.0
- qutip >= 4.7.0
- matplotlib >= 3.7.0

Install all dependencies:

```bash
pip install -r bh_unitarity/requirements.txt
```

---

## Step 1 — Verify the primary data file

```bash
shasum -a 256 MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/phase2_3_final/final_results.json
```

Expected:

```
bf2b079c9f3d2850434430356e9f4b1d49b448e6154c1cf808d348a730159b36
```

---

## Step 2 — Run the Stinespring analysis wrapper

From the repository root:

```bash
python bh_unitarity/run_stinespring_analysis.py
```

This script:
1. Imports `HorizonHilbertSpace`, `GKSLMasterEquation`, and `StinespringDilation`
   from `MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src/`
2. Constructs the GKSL master equation for n=3 modes, T_H=0.003979, coupling=0.01
3. Builds the Stinespring dilation (dim(H_E) = 7)
4. Verifies fidelity on vacuum, thermal, and Fock test states
5. Reports dim(H_E), Stinespring fidelity, and Choi trace preservation error
6. Saves results to `bh_unitarity/results/stinespring_results.json`

### Expected output

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

---

## Step 3 — (Optional) Regenerate final_results.json from scratch

```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src
python te2_4_jt_toy_model.py
```

This re-runs the full GKSL evolution, Page-like entropy curve, and Stinespring
dilation and writes a new `results/phase2_3_final/final_results.json`.
The SHA-256 of the regenerated file should match the value above.

---

## Step 4 — (Optional) Run individual source modules

```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src

# Hilbert space construction only
python te2_4_hilbert_space.py

# GKSL master equation (includes CPTP and detailed balance checks)
python te2_4_gksl_constructor.py

# Stinespring dilation
python te2_4_stinespring.py
```

---

## Expected Values

| Quantity | Expected value |
|---|---|
| `fidelity_with_thermal` | 0.9999192951 |
| Stinespring fidelity F (min) | ≥ 1 − 10⁻⁸ |
| `dim(H_E)` | 7 |
| Choi trace preservation error | ≤ 10⁻¹⁰ |
| Detailed balance error | 0.00% |
| CPTP validation | PASS |
| Steady-state entropy | 0.4945 |
| Entropy ratio vs. thermal | 97.2% |
