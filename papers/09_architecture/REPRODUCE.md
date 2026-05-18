# REPRODUCE — The Architecture of a Computable Universe

## Overview

This is an interpretive synthesis paper. It presents no novel computations,
simulations, or data analyses; all quantitative results cited herein are
produced by the foundational companion papers listed in the theorem table
(Appendix B of the paper). There are no computational artifacts to reproduce
beyond compiling the LaTeX source.

## Build the PDF

```bash
cd papers/09_architecture
pdflatex "The Architecture of a Computable Universe.tex"
bibtex "The Architecture of a Computable Universe"
pdflatex "The Architecture of a Computable Universe.tex"
pdflatex "The Architecture of a Computable Universe.tex"
```

Or with `latexmk`:

```bash
cd papers/09_architecture
latexmk -pdf -interaction=nonstopmode "The Architecture of a Computable Universe.tex"
```

Bibliography: `../bib/Spivack_Papers_Bibliography.bib` (shared across the paper series).

## Companion reproduction

The numerical claims cited in this paper are reproduced via the companion
papers' own `REPRODUCE.md` files:

| Cited result | Companion paper | Reproduction target |
|---|---|---|
| ML-I: Uniqueness sieve (n=10) | Paper 03 (Uniqueness) | `ugp_uniqueness_sieve.py` |
| ML-III: Turing universality | ugp-lean | `lake build` (module `Universality.TuringUniversal`) |
| ML-III: UWCA reversibility | ugp-lean | `lake build` (module `UWCAHistoryReversible`) |
| ML-IV: Gauge couplings | Paper 05 (Math Foundations) | `gauge_couplings_unified.py` |
| ML-IV: SU(2)/SU(3) rigidity | Paper 05 (Math Foundations) | `su2_rigidity_proof.py`, `su3_rigidity_proof.py` |
| ML-V: Necessary Observers | nems-lean | `lake build` (NEMS 09–22 chain) |
