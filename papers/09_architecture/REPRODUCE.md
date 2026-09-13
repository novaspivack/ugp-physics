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

## Lean verification: Two-Layer PSC enumeration

The Layer~I PSC filter over $34{,}560$ universe descriptions is machine-certified in
`ugp-lean/UgpLean/TE22/ScanCertificate.lean`:

```bash
git clone https://github.com/novaspivack/ugp-lean.git
cd ugp-lean
lake build UgpLean.TE22.ScanCertificate
```

| Theorem | Statement |
|---------|-----------|
| `universe_params_card` | `Fintype.card UniverseParams = 34560` |
| `psc_12_survivors_card` | Exactly 12 Layer~I PSC survivors |
| `psc_enumeration_forces_ngen_3` | Every PSC-admissible universe has $N_{\mathrm{gen}} = 3$ |
| `psc_admissible_forces_sm_gauge` | Every PSC-admissible universe is SM gauge content in 4D |

All four theorems: zero `sorry`, discharged by `native_decide`.
