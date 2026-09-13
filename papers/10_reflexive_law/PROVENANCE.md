# Provenance — Reflexive Reality and Self-Defining Physical Law

**Paper:** *Reflexive Reality and Self-Defining Physical Law*  
**Version:** v2 (2026-04-17 — Wave 1 revision)  
**Status:** Revised — ready for review

---

## Description

A philosophical essay arguing that the laws of physics are reflexively self-defining: the universe's generative principle is not externally imposed but is the unique fixed point of a self-referential process. Positions the argument relative to Wheeler's participatory universe, Rovelli's relational QM, and the companion NEMS formal programme.

---

## Files

| File | Description |
|------|-------------|
| `reflexive_reality_self_defining_law.tex` | LaTeX source (with bibliography) |
| `reflexive_reality_self_defining_law.pdf` | Pre-built PDF |
| `Gemini_Generated_Image_v1udfvv1udfvv1ud.png` | Conceptual figure |

---

## Lean Formalization Sources

All theorems are proved in nems-lean (Zenodo 10.5281/zenodo.19429710, GitHub: https://github.com/novaspivack/nems-lean) with zero sorry.

| Theorem | Paper | Lean name | Zenodo DOI |
|---------|-------|-----------|------------|
| PSC classification (Class I/IIa/IIb) | NEMS 02 | `NemS.classification_theorem` | 10.5281/zenodo.19429715 |
| Foundational Finality (trichotomy) | NEMS 23 | `NemS.foundational_finality` | 10.5281/zenodo.19429761 |
| Reflexive Closure (self-exhaustion impossible) | NEMS 56 | `ReflexiveClosure` | 10.5281/zenodo.19429835 |
| Transputation (unitarity-preserving selection) | NEMS 76 | `Transputation.Theorems.ForcedAdjudication` | 10.5281/zenodo.19429882 |

---

## Wave 1 Revision Changes (2026-04-17)

| Change | Section | Notes |
|--------|---------|-------|
| Bibliography added (8 entries) | End of paper | Wheeler 1983, Rovelli 1996, Barbour 1999, NEMS Hub, NEMS 02/23/56/76 |
| §6 heading: "Theorem" → "Proposition (Informal)" | §6 | Formal version is NEMS 23+56 [T] |
| §6: NEMS 23/56 machine-checked citations added | §6 | Trichotomy replaces informal regress argument |
| Definition 2: clause (c) added (no free bits) | §2 | Cites NEMS 02 `NemS.classification_theorem` |
| §4 taxonomy: NEMS class column added | §4 | Class I / IIa / IIb informal mapping |
| §4 taxonomy: explanatory note added | §4 | Refers to NEMS 02 for formal class assignment |
| Series position note added | §1 | Points to NEMS 02/23/56/76 for proofs |
| §5 gradient flow: unitarity note added | §5 (Ex. 5) | Cites NEMS 76 Transputation |
| §7: "PR-0 field experiments" fixed | §7 | Now cites companion work via SpivackNEMSHub |
| Claim-type tags [T/B/I] applied throughout | All sections | 23 tagged claims |
| Lean appendix added (3 theorems) | Appendix | NemS.classification_theorem, foundational_finality, ReflexiveClosure |
| Abstract added | Title area | Summarises paper scope and NEMS formal backing |

---

## Computational Artifacts

None. This is a theoretical/philosophical essay.

COMP-P10-A (reflexive QHO worked example) is an optional computation noted in the paper text (§5.4) and tracked in the revision notes; it is not blocking publication.
