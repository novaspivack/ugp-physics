# P31 — Arithmetic Derivation of the Electroweak Mixing Angle from Rule 110 Orbit Arithmetic

**Status:** Draft (abstract and §1 complete; §2–§7 stubbed)
**Series:** UGP Physics, Paper 31
**Source:** `weinberg_angle_paper.tex`

## Overview

This paper derives the electroweak mixing angle sin²θ_W = 3/13 ≈ 0.23077 from the
combinatorial arithmetic of the Rule 110 cellular automaton orbit that the Standard Model
generation sequence is forced to satisfy.

The derivation is a ten-step chain from N_gen = 3 (Garden of Eden orbit depth,
Lean-certified) through the palindrome decomposition of the 13 active f_MDL
neighborhoods.  The chain is machine-certified in Lean 4, zero sorry, zero new axioms,
conditional on one bridge import from the UGP dynamics paper (P22).

## Key results

| Prediction | Formula | Value | PDG (0.23122) | Error | Status |
|---|---|---|---|---|---|
| Bare (tree-level) | 3456/15101 | 0.22886 | −1.02% | −4.5σ | Lean-certified |
| EW scale | N_gen/c_H = 3/13 | 0.23077 | −0.195% | −0.8σ | Lean-certified (cond.) |
| GUT scale | N_gen/2^N_gen = 3/8 | 0.37500 | SU(5) exact | 0.000% | Lean-certified |

## Lean certification

All theorems in `ugp-lean`, module `GUTStructure.lean`, zero sorry.
Key commit: `596b190` (GUTStructure §12 WeinbergClosure).

**Remaining before submission:** Import `doublet_partner_is_left_chiral` from P22
(`Spivack2026_UGPDynamics`) into `GUTStructure.lean`.  This converts the conditional
CatAL results to unconditional.  Estimated: one session.

## Compilation

```bash
cd papers/31_weinberg_angle
pdflatex weinberg_angle_paper.tex
bibtex weinberg_angle_paper
pdflatex weinberg_angle_paper.tex
pdflatex weinberg_angle_paper.tex
```

Requires the master bibliography at `../bib/Spivack_Papers_Bibliography.bib`.

## Dependencies

- **P01** (`Spivack2026_SM_UGP`): GTE cascade, Z_5 ring, N_fam = 5, bare gauge couplings
- **P22** (`Spivack2026_UGPDynamics`): `doublet_partner_is_left_chiral` (one-bridge import)
- **P28** (`SpivackCompUniversality`): SM orbit forces Rule 110 (CUP-4); f_MDL; N_gen = 3
