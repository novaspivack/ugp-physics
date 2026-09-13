# Provenance: P48 — The Complete GTE Framework

**Paper:** P48, UGP Physics series.

## Sources

This monograph draws on the complete UGP Physics corpus (P01–P51), the NEMS
programme (Papers 01, 02, 05, 11, 13, 51), and the canonical `ugp-lean`
Lean 4 library. Every chapter's primary claims trace to the papers listed in
the chapter map; no original derivations are introduced in this paper — P48
is a proof paper that assembles the complete logical chain from the corpus into
a single coherent document, with every step labeled by its certification level.

Key source papers by chapter:

- **Foundation (Problem / Orientation / Principle):** P01 (SM derivation), P34
  (PSC/transputation), P00 (survey guide); NEMS Papers 01, 05, 13, 51.
- **The Mathematical Substrate:** P08 (UGP arithmetic, UWCA construction,
  GTE-as-program compilation), P28 (orbit uniqueness and the meaning of the
  universality), P01 (canonical triple catalogue); executable witness
  `scripts/UGP_GTE_UWCA_rule.py` (shared with P08);
  `Universality/UWCASimulation.lean`, `Universality/UWCAembedsRule110.lean`,
  `Universality/GTECompilation.lean`, `Universality/TriangleLiftTheorem.lean`.
- **The Selection (T96-02 / MDL selection / interpolation lift):** P46 (GTE
  polynomial UFT), P28 (Cook's theorem), P49 (lift, sparsity floor, chirality
  census, parity-projection forcing); rule110-lean;
  `MDLDerivabilityCriterion.lean`, `Universality/TriangleLiftTheorem.lean`,
  `Universality/TriangleLiftStructural.lean`,
  `Universality/ParityProjectionForcing.lean`.
- **One Field (Φ_MDL):** P42 (Φ_MDL field theory), P43 (Φ_MDL completeness),
  P45 (three-tape CMCA), P46, P50 (thermal shadow, tape saturation,
  matter-sector lattice dictionary); `Physics/CMCAPhysicalPoint.lean`.
- **Particles:** P17 (braid atlas), P38 (emergent gravity / Φ_MDL),
  P39 (QCD from GTE), P45, P01 (InformationMassTransformer pipeline and the
  locked theoretical-path benchmark); `GUTStructure.lean`, `BaryonNumber.lean`.
- **Forces:** P35 (GTE unification), P31 (Weinberg angle), P32 (CKM),
  P39, P40, P46; `AlphaEMStructuralIdentity.lean`, `CasimirB0Relation.lean`.
- **Spacetime / Gravity:** P36 (emergent gravity CMCA), P38, P44
  (quantum gravity completeness), P45; `PMDLGravityTheorems.lean`,
  `GorardRicciFlatVacuum.lean`.
- **Quantum Mechanics:** P34, P37 (quantum mechanics from GTE), P43,
  P46; `BornRuleMDL.lean`, `born_rule_unconditional`.
- **Cosmology:** P47 (GTE cosmological predictions);
  `PSCEpochSelection.lean`, `CMBSpectralTilt.lean`.
- **Context / Conclusion:** P00, P34, P37; `no_final_self_theory`,
  `tpc_three_level_hierarchy`.
- **Master quadratic, cyclotomic/Eisenstein arithmetic, dynamical zeta:** P49
  (GTE polynomial mathematical structure); `Polynomial/GoldenQuadratic.lean`,
  `Polynomial/EisensteinIdentities.lean`, `Polynomial/BiquadraticCompositum.lean`,
  `Polynomial/DynamicalZeta.lean`, `Polynomial/AGL17ChiralZ2.lean`.
- **Defect cosmology and the CC bracket structure:** P47 (defect cosmology,
  two-sided bracket), P46 (carrier/record split of the generating functional);
  `Physics/ZSevenVacuumSelection.lean`, `CCOneJumpResidual.lean`,
  `NgenBracketOrientation.lean`.
- **Adjudication degree and Three-Level MDL Unification:** P51 (polynomial
  certificate of transputation); `Framework/MDLTower.lean`, nems-lean
  `Diagonal/Sigma1Completeness.lean` and `Diagonal/NoConvergenceModulus.lean`,
  transputation-lean `Theorems/DiagonalDegree.lean`.
- **Coupling-sector parameters and the kink-broadening verdict:** P42 (Φ_MDL
  coupling sector, non-perturbative kink form factor), P39 (Λ_GTE seven-kink
  threshold derivation).

## Machine certification

All central algebraic steps are certified in the canonical `ugp-lean` library
with zero `sorry`. See `REPRODUCE.md` for the module list. A clean `lake build`
of `ugp-lean` exits 0.

## External citations

All external references were verified against arXiv/DOI records before inclusion
in `papers/bib/Spivack_Papers_Bibliography.bib`.
