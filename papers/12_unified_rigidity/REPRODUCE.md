# Reproducing the Unified Rigidity Theorem materials

## Lean

Build the bridge library (PSC + UGP + dynamics interfaces):

```bash
git clone https://github.com/novaspivack/unified-rigidity-lean.git
cd unified-rigidity-lean
lake update
lake build
```

## Computational concordance

From the `ugp-physics` repository root:

```text
computational_concordance/REPRODUCE.md
```

## LaTeX

From `papers/12_unified_rigidity/`:

```bash
pdflatex Unified_Rigidity_Theorem.tex
bibtex Unified_Rigidity_Theorem
pdflatex Unified_Rigidity_Theorem.tex
pdflatex Unified_Rigidity_Theorem.tex
```

Bibliography: `../bib/Spivack_Papers_Bibliography.bib` (adds entries `unified-rigidity-lean` and `ugp-physics-repo` for this paper).

Requires `xcolor` (for hyperref link colors). Build exits 0 when citations resolve.
