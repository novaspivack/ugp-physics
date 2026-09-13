# Provenance — P52: The PSL(2,7) Algebraic Structure of the GTE Framework

## Paper

**Title:** The PSL(2,7) Algebraic Structure of the Generative Triple Evolution Framework  
**Author:** Nova Spivack  
**Series:** UGP Physics Series, Paper 52  
**Status:** DRAFT  
**DOI:** (pending Zenodo deposit)

## Prior papers this builds on

| Paper | Key contribution cited |
|-------|----------------------|
| P34 (SpivackGTEMobius) | GTE-Möbius architecture (A, e, [D]); F₂₁ gauge skeleton group; Fibonacci–Möbius dynamics |
| P48 (SpivackGTECompleteFramework) | GTE complete framework; Transputation D1–D5; Level-0 polynomial p |
| P43 (SpivackCompleteness) | Algebraic Lifting Theorem; Level-0 → Level-2 bridge |
| P27 (SpivackSRRG) | SRRG fixed point; Z₇ generation orbit |

## Core results and certification levels

### CatAL — machine-certified in Lean 4, zero sorry

| Theorem | Statement | Module |
|---------|-----------|--------|
| `f21_is_borel_psl27` | F₂₁ = stabilizer of ∞ ∈ P¹(𝔽₇) in PSL(2,7), order 21 | `Polynomial/PSL27Unification.lean` |
| `pgl27_generated_by_singer_and_borel` | ⟨Fibonacci–Möbius, F₂₁⟩ = PGL(2,7), order 336 | `Polynomial/PSL27Unification.lean` |
| `psl27_is_aut_fano` | \|PSL(2,7)\| = 168, unique simple group of this order | `Polynomial/PSL27Unification.lean` |
| `f21_regular_on_fano_flags` | F₂₁ acts simply transitively on all 21 Fano incidence flags | `Algebra/FanoRegularAction.lean` |
| `eisenstein_a4_from_inert_2` | A₄ = V₄ ⋊ ℤ₃ from ℤ[ω]/(2); 2 inert in Eisenstein integers | `Algebra/EisensteinFunctor.lean` |
| `gte_manifest_flavor_is_s3_in_a4` | Manifest S₃ = ⟨μ₃, (2 3)⟩ embeds in A₄ = V₄ ⋊ μ₃ | `Algebra/FlavorGroupStructure.lean` |
| `klein_quartic_genus_eq_n_gen` | genus(Klein quartic) = N_gen = 3; Hurwitz saturated | `Cosmology/CCBracketHurwitz.lean` |

### CatA — computationally confirmed

- G₈₄ = F₂₁ ×_{ℤ₃} A₄ does not embed in GL(2,7) or PGL(2,7): verified by exhaustive group-order argument
- Klein quartic orbifold formula χ = 168 × (−1/42) = −4: verified by exact rational arithmetic

### CatAD — analytically derived

- A₄ from ℤ[ω]/(2) is the GTE leading-order neutrino flavor symmetry completing manifest S₃ to TBM-generating A₄ (tri-bimaximal mixing angles follow from A₄ representation theory)
- Klein quartic genus = N_gen derivation from Gauss-Bonnet area formula and Hurwitz covering argument

### CatD — theoretical arguments, further development needed

- Physical realization of the Klein quartic in GTE CMCA dynamics
- TBM correction structure from A₄ → S₃ symmetry breaking
- G₈₄ as a physical symmetry of the CMCA tape

## Lean certification status

All CatAL theorems reside in the `ugp-lean-exp` development repository.
The relevant modules have been built and verified with `lake build UgpLean` with zero sorry.
Graduation to canonical `ugp-lean` is pending.

Lean modules containing P52 theorems:
- `UgpLean/Polynomial/PSL27Unification.lean`
- `UgpLean/Algebra/FanoRegularAction.lean`
- `UgpLean/Algebra/EisensteinFunctor.lean`
- `UgpLean/Algebra/FlavorGroupStructure.lean`
- `UgpLean/Cosmology/CCBracketHurwitz.lean`

Supporting modules (imported):
- `UgpLean/Polynomial/PSL27Unification.lean` also imports `DynamicalZeta.lean` for `moebiusP1` and `P1GF7`

## External citations used

All citations reference published or verified works in `../bib/Spivack_Papers_Bibliography.bib`.
No external physics papers are cited in the current draft that require verification.
