# P30 — Cook's Rule 110 Universality (Lean Certification)

**Working title:** Machine-Certified Formalization of Cook's Rule 110 Universality Theorem in Lean 4

**Status:** Draft paper tracks **partial** Lean certification (global bridge axioms still open).

## Files

| File | Description |
|------|-------------|
| [`cook_theorem_paper.tex`](cook_theorem_paper.tex) | Main manuscript |
| [`OUTLINE.md`](OUTLINE.md) | Section-by-section outline and appendix plan |
| [`cook_theorem_refs.bib`](cook_theorem_refs.bib) | Bibliography entries not in central bib |
| [`nova_zenodo_doi_placeholder.tex`](nova_zenodo_doi_placeholder.tex) | Zenodo DOI anchor |
| [`PROVENANCE.md`](PROVENANCE.md) | Origin and change log |
| [`REPRODUCE.md`](REPRODUCE.md) | Lean reproduction instructions |

## Lean source

Formal proofs live in the separate repository **`rule110-lean`** (not vendored in ugp-physics):

```
/Users/nova/rule110-lean
```

Key modules: `CookUniversalityChain.lean`, `CookUniversalityScaffold.lean`, `CTStoRule110.lean`, `CookC2InfTapeBridge.lean`, `CookC2SupportBareEquiv.lean`, `CookTM2Bridge.lean`.

## Build PDF (local)

From this directory:

```bash
pdflatex cook_theorem_paper.tex
bibtex cook_theorem_paper
pdflatex cook_theorem_paper.tex
pdflatex cook_theorem_paper.tex
```

Requires a LaTeX install with `authblk`, `tcolorbox`, `cleveref`, etc.

## Relation to P28

[P28](../28_computational_universality/) uses Rule 110 universality conditionally via bridge axioms. `cook_operational_stage3_tm_microstep_readback` (the renamed and rescoped former `rule110_turing_universal_from_cook`) is a conditional operational microstep-readback certificate, not itself a Turing-universality theorem. When its five residual Cook bridge axioms close, the readback certificate becomes unconditional; P28's incompleteness chain depends on `rule110_simulates_computable` in `ugp-lean` (a separate axiom composing this readback with a classical TM/Partrec compilation step), which upgrades accordingly once the readback side is unconditional and the TM→CTS compiler for arbitrary machines is formalized.

## When certification completes

Revise abstract/conclusion to unconditional wording, pin `rule110-lean` commit in `PROVENANCE.md` / `REPRODUCE.md`, inject Zenodo DOI, and publish per UGP release workflow.
