# Computational Provenance — MFRR Foundational Monograph (P13)

## Paper

"Mathematical Foundations of Reflexive Reality" (MFRR Monograph)

## Source

Main TeX: `papers/13_MFRR_foundational_monograph/Mathematical_Foundations_of_Reflexive_Reality.tex`
Summary documents: `papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/`

## Computational claims and their provenance

| Claim | Type | Source | Verification |
|---|---|---|---|
| SM ranks #1 of 34,560 universes | [C] Computational | TE2.2 extended scan (P14) | SHA-256 certified |
| Lean formalization (zero sorry; the formalization paper is the single source of truth for module/theorem counts) | [T] Theorem | ugp-lean | `lake build UgpLean` |
| NEMS programme results | [T] Theorem | nems-lean | Zenodo DOI: 10.5281/zenodo.19429761 |
| Reflexive Closure Theorem | [T] Theorem | nems-lean | Zenodo DOI: 10.5281/zenodo.19429835 |

## Dependencies

- ugp-lean (zero sorry; module/theorem count tracked in the formalization paper)
- nems-lean (companion formalization)
- TE2.2 scan data (P14)

## Version

v1.0 (2026-05-09)
