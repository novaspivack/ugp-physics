# Reproduction Guide — The Information Profit Principle

This document describes how to reproduce the computational results reported in the paper.

---

## Environment

- Python 3.9 or later
- numpy
- scipy
- matplotlib (for figure generation)

Install dependencies:

```
pip install numpy scipy matplotlib
```

No other packages are required for the core experiments. All scripts are self-contained.

---

## 1. Analytical Derivation Verification

The IPT value can be verified independently with the standalone script in the `information_profit/` code directory:

```
cd information_profit/
python verify_ipt_derivation.py
```

Expected output (to 10 decimal places):

```
=== Information Profit Threshold Derivation Verification ===
phi      = 1.6180339887
ln(phi)  = 0.4812118251
ln(2*pi) = 1.8378770664
Lambda   = 0.2618302572
Lambda/2 = 0.1309151286
IPT      = 1.1309151286
PASS: IPT = 1.1309151286 is within 1e-04 of 1.1309
Result saved to results/ipt_derivation_verification.json
```

Result is also saved to `information_profit/results/ipt_derivation_verification.json`.

---

## 2. TE1.H Simulation (2D Toy Field Simulator)

**Location:** `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/`

**Entry point:**

```
cd MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/
python run_te1h.py
```

This runs three scenarios (Unprofitable rho ≈ 0.80, Profitable rho ≈ 1.40, High Noise rho < 1.00)
for 400 steps each on a 64x64 field and writes coherence history CSVs to `results/csv/`.

To run the full pipeline including figures:

```
python te1b_pipeline_levin.py
```

**Pre-computed result files:**

```
results/csv/unprofitable:_gen_drain_≈_0.8_(<_1.13)_coherence_history.csv
results/csv/profitable:_gen_drain_≈_1.4_(>_1.13)_coherence_history.csv
results/csv/profitable_gen_+_high_noise:_gen_drain_<_1.0_coherence_history.csv
```

SHA-256 checksums for the pre-computed CSVs appear in `PROVENANCE.md`.

**Expected results (coherence slope, Delta-C per step):**

| Scenario             | rho    | Delta-C/step        |
|----------------------|--------|---------------------|
| Unprofitable         | ~0.80  | -1.94e-5  (decay)   |
| Profitable           | ~1.40  | +1.00e-4  (growth)  |
| High Noise           | <1.00  | -3.51e-5  (decay)   |

---

## 3. TE2.1 Evolutionary Genesis

**Location:** `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/`

**Entry point (genesis experiment):**

```
cd MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/
python MFRR_Evolutionary_Genesis.py
```

**Entry point (sweep experiment):**

```
python MFRR_Evolutionary_Sweep.py
```

The sweep runs a 4x6 grid (metabolic cost x decay rate), 3 random seeds per point,
40 generations, 600 frames per run (72 total sweep runs).

**Expected results:**

- Genesis: 124 runs total; 15 with final rho > 1.1309 (IPT); supercritical range [1.137, 1.567]; supercritical mean 1.234; overall mean 0.821
- Sweep: 72 runs; 14/72 (19.4%) exceed IPT; supercritical runs concentrated at lowest metabolic cost / decay rate combinations

Pre-computed result JSON files are in `results/` within the TE2.1 directory.
See `PROVENANCE.md` for file dates.

**Note:** Due to random initialization, exact counts may vary by a small number of runs
if re-run with different random seeds. The pre-computed results in `results/` correspond
to the values reported in the paper.

---

## 4. E4 Reflexive Landauer Energy Model Check

**Location:** `MFRR/E4_reflexive_landauer_check.py`

**Entry point:**

```
cd MFRR/
python E4_reflexive_landauer_check.py
```

Generates 50 randomized parameter configurations and checks that the modeled PT energy
cost exceeds the Reflexive Landauer bound in each case. Results are saved to
`MFRR/E4_reflexive_landauer_results.json`.

**Pre-computed result file:** `MFRR/E4_reflexive_landauer_results.json`

SHA-256: `13cf53baaa10f02b9e5cda2b88fafaeff717fafa7057d1da4fcb4f3c938f4071`

**Expected results:**

| Statistic               | Value  |
|-------------------------|--------|
| Total trials            | 50     |
| Pass rate               | 100%   |
| Min margin              | 0.0182 |
| Max margin              | 4.0798 |
| Mean margin             | 0.9481 |

The E4 result file is pre-computed and does not need to be re-run to verify the
reported statistics; the SHA-256 above can be used to confirm file integrity.

---

## 5. Lean Machine-Checked Verification (updated 2026-05-12)

Two Lean 4 libraries provide machine-checked verification.

### 5a. ugp-physics-lean — IPT, GXT, and SRRG modules

Repository: https://github.com/novaspivack/ugp-physics-lean

```bash
# Clone and build
git clone https://github.com/novaspivack/ugp-physics-lean
cd ugp-physics-lean
lake build
# Expected: build succeeds; 2 sorry warnings (both in abstract Lie-group
#   minimality theorems pending LieGroup.exp in Mathlib — see below)
```

Key theorems verified zero-sorry:

| Theorem | Lean name | Module |
|---------|-----------|--------|
| H9: IPT fixed point of Landauer map | `ipt_self_consistent` | `UgpPhysicsLean.GXT.H9SelfConsistency` |
| A1: 1/φ is unique positive FP of x=1/(1+x) | `golden_ratio_fixed_point_unique` | `UgpPhysicsLean.GXT.GoldenRatioFixedPoint` |
| A2: entropy formula H(U(1))=ln(2π) | `entropy_formula_U1`, `A2_adjudication_entropy` | `UgpPhysicsLean.IPT.InformationProfitThreshold` |
| A2: Circle ≅ ℝ/(2πℤ) as topological groups | `circle_iso_addCircle_2pi` | `UgpPhysicsLean.GXT.U1DirectProof` |
| A2: Circle.exp is surjective | `circle_exp_surjective_MAIN` | `UgpPhysicsLean.GXT.LieExpSurjective` |
| A3: 1/2 PSC split | `A3_forward_backward_split` | `UgpPhysicsLean.IPT.InformationProfitThreshold` |
| IPT theorem | `IPT_theorem` | `UgpPhysicsLean.IPT.InformationProfitThreshold` |

Remaining sorries (2, both in abstract Lie group minimality):
- `u1_minimality_reduced` (U1DirectProof.lean): kernel characterization needs Lie structure
- `lie_exp_properties_of_compact_connected_dim1_SORRY` (LieExpSurjective.lean): needs `LieGroup.exp` in Mathlib

Both sorries are in the abstract-G theorem only. For the UGP/IPT application
(G = Circle = U(1)), all results are zero-sorry.

### 5b. ugp-lean — GTE.LinearResponse (A1 canonical home)

Repository: https://github.com/novaspivack/ugp-lean

```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean
lake build UgpLean.IPT.InformationProfitThreshold
# Expected: 0 errors, 0 sorry warnings
# Key theorems: abs_psi_eq_inv_phi (A1), A2_adjudication_entropy,
#               A3_forward_backward_split, IPT_theorem
```

This verifies: ρ_crit = 1 + ln(φ)/(2ln(2π)) ≈ 1.1309 is machine-proved [T].

---

## 6. PDF Build Instructions

The paper source is `Information_Profit_Principle.tex`.

Requirements: LaTeX distribution with pdflatex (e.g., TeX Live 2023+) and BibTeX.

```
cd papers/15_information_profit/
pdflatex Information_Profit_Principle.tex
bibtex Information_Profit_Principle
pdflatex Information_Profit_Principle.tex
pdflatex Information_Profit_Principle.tex
```

The bibliography file is at `papers/bib/Spivack_Papers_Bibliography.bib`.

---

## Note on Paper-Directory Copies

For convenience during peer review, copies of the four MFRR-sourced scripts referenced in the
paper text have been graduated into the paper directory:

| Script | Source location | Paper-dir copy |
|--------|----------------|----------------|
| `information_profit_simulation.py` | `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/` | `papers/15_information_profit/` |
| `MFRR_Evolutionary_Genesis.py` | `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/` | `papers/15_information_profit/` |
| `MFRR_Evolutionary_Sweep.py` | `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/` | `papers/15_information_profit/` |
| `E4_reflexive_landauer_check.py` | `MFRR/` | `papers/15_information_profit/` |

The **canonical** versions are the originals in the MFRR directory. Run instructions
above (sections 2–4) still reference those locations.

---

## SHA-256 of Key Result Files

| File | SHA-256 |
|------|---------|
| `MFRR/E4_reflexive_landauer_results.json` | `13cf53baaa10f02b9e5cda2b88fafaeff717fafa7057d1da4fcb4f3c938f4071` |
| `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/results/csv/profitable:_gen_drain_≈_1.4_(>_1.13)_coherence_history.csv` | `b63b40598999dc2283215d18a0e96d482092f5468462e416672777979abb7ad4` |
| `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/results/csv/unprofitable:_gen_drain_≈_0.8_(<_1.13)_coherence_history.csv` | `ae2d9e96f52a8ce1c398a1c5e1065fe0e184705635873a715f3aa29e1a48fab2` |
| `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/results/csv/profitable_gen_+_high_noise:_gen_drain_<_1.0_coherence_history.csv` | `1cc3cb6dccdf5c43e8479236b19ed1f4fc99f87f7dbb004bcfb56b97ae5794cd` |
