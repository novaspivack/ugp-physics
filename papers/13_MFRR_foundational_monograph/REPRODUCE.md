# Reproduction Guide — MFRR Foundational Monograph (P13)

Reproduces results referenced in:
*"Mathematical Foundations of Reflexive Reality"*

---

## LaTeX compilation

```bash
cd papers/13_MFRR_foundational_monograph
pdflatex -interaction=nonstopmode Mathematical_Foundations_of_Reflexive_Reality.tex
bibtex Mathematical_Foundations_of_Reflexive_Reality
pdflatex -interaction=nonstopmode Mathematical_Foundations_of_Reflexive_Reality.tex
pdflatex -interaction=nonstopmode Mathematical_Foundations_of_Reflexive_Reality.tex
```

All figure assets and the local `references.bib` are co-located in this directory.
The central bibliography is referenced as `../bib/Spivack_Papers_Bibliography`.

## Explanatory summary documents

```bash
cd papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_FOR_PHYSICISTS
pdflatex MFRR_FOR_PHYSICISTS_SHORT_OVERVIEW.tex
```

## Computational results

The MFRR programme's computational results are reproduced via the companion
code repositories:

- **TE2.2 extended scan** (34,560 universes): see `papers/14_psc_concordance/REPRODUCE.md`
- **Lean formalization**: see `ugp-lean/docs/BUILD.md`
- **NEMS Lean library**: see <https://github.com/novaspivack/nems-lean>

## Lean formalization

Machine-checked theorems cited from ugp-lean:
```bash
cd /path/to/ugp-lean
lake build UgpLean
```
