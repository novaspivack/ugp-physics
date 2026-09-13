# P35 — GTE Unification Capstone

**Paper:** GTE Unification: A Bidirectional Correspondence between Rule 110 Orbit Arithmetic and the Standard Model Electroweak Sector

**Author:** Nova Spivack  
**Year:** 2026  
**Series:** UGP Physics Programme, Paper P35

## Summary

This paper assembles the bidirectional correspondence between GTE arithmetic,
the Rule 110 cellular automaton, and the Standard Model electroweak sector
into a single formal statement. The main result is the machine-certified theorem
`ugp_r110_sm_joint_unification` (7 conjuncts, Lean 4, zero `sorry`, zero new axioms),
packaging all six arrows of the correspondence.

Three SM parameters are derived from the single integer N_gen = 3:
- sin²θ_W(EW) = 3/13 ≈ 0.23077 (−0.195% from PDG)
- sin²θ_W(GUT) = 3/8 = 0.375 (exact SU(5) prediction)
- λ(Wolfenstein) = 9/40 = 0.225 (0.000% from PDG)

## Files

- `gte_unification_paper.tex` — Main LaTeX source
- `gte_unification_paper.pdf` — Compiled paper (14 pages)
- `gte_unification_refs.bib` — Supplemental bibliography
- `nova_zenodo_doi_placeholder.tex` — DOI placeholder (populated at publication)
- `PROVENANCE.md` — Provenance and certification chain
- `REPRODUCE.md` — Reproduction instructions

## Lean Certification

The main theorems are in `ugp-lean/UgpLean/Universality/GUTStructure.lean`:
- §27: `ugp_r110_sm_joint_unification` (7 conjuncts, zero sorry)
- §23: `gte_master_formula_complete` (zero sorry)

The single non-discharged axiom across the entire series is in P30 (Cook theorem):
`len6_evolved_inf30_eq_list420_at_slot` (InfTape transport step).
