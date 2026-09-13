# P32 — The CKM Wolfenstein Parameters from Generative Triple Evolution Orbit Arithmetic

**Status:** Complete draft
**Series:** UGP Physics, Paper 32
**Source:** `ckm_matrix_paper.tex`

## Overview

This paper derives all four Wolfenstein parameters of the CKM quark mixing matrix
from the arithmetic of the Rule 110 cellular automaton orbit that the Standard Model
generation sequence is forced to satisfy, with zero free parameters.

The derivation identifies six GTE quark orbit indices with structural formulas in the
GTE constants N_gen = 3, N_fam = 5, c_H = 13, and derives the complete Wolfenstein
parametrization from them. All six arithmetic identities are machine-certified in Lean 4
with zero sorry (`six_quark_neff_complete`, §34).

## Key Results

| Parameter | GTE formula | GTE value | PDG | σ-pull | Status |
|---|---|---|---|---|---|
| λ | N_gen²/(2^N_gen × N_fam) | 9/40 = 0.22500 | 0.22500 ± 0.00067 | **0.000σ** | Lean-certified |
| A | √(N_eff(s)/N_eff(c)) | √(186/275) = 0.8224 | 0.814 ± 0.013 | +0.65σ | CatA |
| ρ̄ | from R_b, tan(γ) | 0.1545 | 0.159 ± 0.011 | −0.41σ | CatA |
| η̄ | from R_b, tan(γ) | 0.3417 | 0.348 ± 0.010 | −0.63σ | CatA |

All nine CKM matrix elements within 1σ of PDG at O(λ⁴). Zero free parameters.

## Deep Cross-Sector Identity

The CKM unitarity triangle radius equals the GUT-scale Weinberg mixing angle:

> **R_b = N_gen / 2^N_gen = 3/8 = sin²θ_W(GUT)**

Machine-certified in Lean 4 (`ckm_unitarity_triangle_radius_eq_gut_weinberg`,
alias of `gut_weinberg_angle_pow2` via `ngen_plus_nfam_eq_pow2`; zero sorry).

## Mersenne CP Violation

The bottom quark orbit index b_b = 2^13 − 1 = 8191 is a Mersenne prime (because c_H = 13
is the N_fam-th Mersenne prime exponent). Its primality forces tan(γ) to be irrational
(`bb_bs_product_not_square`, Lean-certified), making CP violation an arithmetic consequence
of the GTE orbit structure.

**CP angle:** γ = arctan(√(8191/186)/3) = 65.67° vs PDG 65.8° ± 5.4° (−0.023σ)

**Future test:** Belle II / LHCb targeting ±1° precision by ~2028 will test this
prediction at >4σ.

## Quark N_eff Structural Formulas

| Quark | N_eff | GTE formula | Status |
|---|---|---|---|
| u | 9 | N_gen² | Lean-certified (CatAL) |
| d | 5 | N_fam | Lean-certified (CatAL) |
| c | 275 | N_fam²(2N_fam+1) | Lean-certified (CatAL) |
| s | 186 | 2N_gen(2c_H+N_fam) | Lean-certified (CatAL) |
| b | 8191 | 2^c_H − 1 (Mersenne prime M₁₃) | Lean-certified (CatAL) |
| t | 337920 | 2^(c_H−2)·N_gen·N_fam·(2N_fam+1) | Lean-certified (CatAL) |

Individual certs: `GUTStructure.lean §15, §20`, commit `c4b0ae5`, zero sorry.
Joint capstone: `six_quark_neff_complete`, `GUTStructure.lean §34`, commit `c31b26c`, zero sorry.

## Lean Certification

Key module: `ugp-lean/UgpLean/Universality/GUTStructure.lean`

**§14:** λ = 9/40 arithmetic (`wolfenstein_lambda_formula`, `ckm_dof_count`; zero sorry)

**§15:** Quark N_eff structural formulas (u,d,c,s,b), A² rationality, cross-sector identity
(9 theorems + 5 definitions, commit `c4b0ae5`; zero sorry)

**§20:** Top quark formula (`neff_t_formula`, CatAL, zero sorry)

**§34:** Capstone — `six_quark_neff_complete` (6-conjunct, all six quarks),
`quark_g1_canonical_assignment` (Z₇ fingerprints), `quark_neff_all_distinct`
(commit `c31b26c`; zero sorry)

## Compilation

```bash
cd papers/32_ckm_matrix
pdflatex ckm_matrix_paper.tex
bibtex ckm_matrix_paper
pdflatex ckm_matrix_paper.tex
pdflatex ckm_matrix_paper.tex
```

Requires the master bibliography at `../bib/Spivack_Papers_Bibliography.bib`.

## Dependencies

- **P01** (`Spivack2026_SM_UGP`): GTE cascade, Z₅ ring, N_fam = 5, quark triples
- **P28** (`SpivackCompUniversality`): SM orbit forces Rule 110 (CUP-4); N_gen = 3; f_MDL
- **P31** (`SpivackWeinberg`): sin²θ_W(GUT) = 3/8 (cross-sector identity bridge)
