# Provenance: P48 — The Complete GTE Framework

**Paper:** P48, UGP Physics series.

## Sources

This monograph draws on the complete UGP Physics corpus (P01–P47), the NEMS
programme (Papers 01, 02, 05, 11, 13, 51), and the canonical `ugp-lean`
Lean 4 library. Every chapter's primary claims trace to the papers listed in
the chapter map; no original derivations are introduced in this paper — P48
is a proof paper that assembles the complete logical chain from P01–P47 into
a single coherent document, with every step labeled by its certification level.

Key source papers by chapter:

- **Chs. 1–2 (Foundation):** P01 (SM derivation), P34 (PSC/transputation), P00
  (survey guide); NEMS Papers 01, 05, 13, 51.
- **Ch. 3 (T96-02 / MDL selection):** P46 (GTE polynomial UFT), P28 (Cook's
  theorem); rule110-lean; `MDLDerivabilityCriterion.lean`.
- **Ch. 4 (Φ_MDL field):** P42 (Φ_MDL field theory), P43 (Φ_MDL completeness),
  P45 (three-tape CMCA), P46.
- **Ch. 5 (Particles):** P17 (braid atlas), P38 (emergent gravity / Φ_MDL),
  P39 (QCD from GTE), P45; `GUTStructure.lean`, `BaryonNumber.lean`.
- **Ch. 6 (Forces):** P35 (GTE unification), P31 (Weinberg angle), P32 (CKM),
  P39, P40, P46; `AlphaEMStructuralIdentity.lean`, `CasimirB0Relation.lean`.
- **Ch. 7 (Spacetime / Gravity):** P36 (emergent gravity CMCA), P38, P44
  (quantum gravity completeness), P45; `PMDLGravityTheorems.lean`,
  `GorardRicciFlatVacuum.lean`.
- **Ch. 8 (Quantum Mechanics):** P34, P37 (quantum mechanics from GTE), P43,
  P46; `BornRuleMDL.lean`, `born_rule_unconditional`.
- **Ch. 9 (Cosmology):** P47 (GTE cosmological predictions);
  `PSCEpochSelection.lean`, `CMBSpectralTilt.lean`.
- **Chs. 10–11 (Context / Conclusion):** P00, P34, P37; `no_final_self_theory`,
  `tpc_three_level_hierarchy`.

## Machine certification

All central algebraic steps are certified in the canonical `ugp-lean` library
with zero `sorry`. See `REPRODUCE.md` for the module list. A clean `lake build`
of `ugp-lean` exits 0.

## External citations

All external references were verified against arXiv/DOI records before inclusion
in `papers/bib/Spivack_Papers_Bibliography.bib`.
