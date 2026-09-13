# REPRODUCE — P54: The Fire in the Equations

## Requirements

- TeX Live 2023 or later (or any distribution with `pdflatex`)
- Packages: `amsmath`, `amssymb`, `amsthm`, `tcolorbox`, `tikz` (with `positioning`,
  `arrows.meta`, `shapes.geometric`, `backgrounds`, `calc`, `decorations.pathreplacing`),
  `enumitem`, `longtable`, `booktabs`, `microtype`, `hyperref`, `natbib`, `setspace`

## Compilation

```bash
cd papers/54_consciousness_primordial_ground
pdflatex consciousness_primordial_ground.tex
pdflatex consciousness_primordial_ground.tex   # second pass for cross-references
```

Two passes are required to resolve TOC and internal cross-references.

## Expected output

- `consciousness_primordial_ground.pdf` — 31 pages

## No scripts or data files

This paper contains no computational scripts and no data files.
All formal claims cited are machine-checked in the Lean libraries referenced in PROVENANCE.md.
