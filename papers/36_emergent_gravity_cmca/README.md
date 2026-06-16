# P36 — Emergent Gravity from Rule 110 Cellular Automaton

**Paper:** P36 in the UGP Physics series  
**Status:** Draft (2026-05-20)  
**Author:** Nova Spivack

## Summary

This paper derives emergent (3+1)-dimensional Einsteinian gravity from the
Rule 110 cellular automaton within the Universal Generative Principle (UGP)
framework. Four interlocking results are assembled:

1. **D = 4 (CatAL):** Spacetime dimension is machine-certified via
   `gte_spacetime_dimension` (Lean 4, zero sorry): D_spatial = 3 forced by
   the SM generation orbit (`three_dim_fmdl_structure_forced`) plus
   D_temporal = 1 definitional gives D = 4 by arithmetic.

2. **Gorard chain (CatA):** Ollivier–Ricci curvature on the Rule 110 causal
   graph confirms the Einstein-equation three-region structure:
   - κ_EE = 0.000 exactly (vacuum flat, L = 280, 500, 1000)
   - κ_SD = +0.778 ± 0.03 (matter curves, stable < 0.5% variation)
   - κ_XD < 0 (gravitational potential flanking, all tape sizes)

3. **T_μν matter coupling (CatA):** T_00^(CA)(x) = |w(x) − 4/7| derived
   from Z₇ winding density. Discrete Einstein equation:
   κ_excess = 4.84 × T_00^(CA), p = 1.37×10⁻¹⁴⁸ (L=280, T=150, N=15).
   Six of six parameter choices confirm positive slope.

4. **MDL–Lovelock correspondence (CatAD):** Nine-row formal dictionary
   mapping MDL uniqueness of Rule 110 to Lovelock uniqueness of the
   Einstein–Hilbert action, with vacuum stability equivalence as the
   deepest structural parallel.

## Files

| File | Description |
|------|-------------|
| `emergent_gravity_paper.tex` | Main paper (LaTeX) |
| `nova_zenodo_doi_placeholder.tex` | Zenodo DOI placeholder |
| `README.md` | This file |
| `REPRODUCE.md` | Reproduction instructions |
| `PROVENANCE.md` | Provenance and derivation record |

## Building

```bash
cd papers/36_emergent_gravity
pdflatex emergent_gravity_paper.tex
bibtex emergent_gravity_paper
pdflatex emergent_gravity_paper.tex
pdflatex emergent_gravity_paper.tex
```

Requires: LaTeX distribution with standard packages (amsmath, booktabs,
tcolorbox, hyperref, cleveref).

## Key open problem

The continuum limit (CA lattice spacing → 0 recovering continuous SO(1,3))
is not proved. This is the standard lattice-to-continuum gap (analogous
to lattice QCD) and is stated as an open problem in §6.
