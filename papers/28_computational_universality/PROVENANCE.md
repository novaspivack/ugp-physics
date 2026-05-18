# Provenance: Computational Universality and the Standard Model (P28)

**Paper:** *Computational Universality and the Standard Model: Rule 110, Z₅ Rings, and Mod-7 Structure in the Universal Generative Principle*  
**Author:** Nova Spivack, 2026  
**Status:** In preparation — final draft

---

## Lean 4 Proofs

| Theorem | File | Build time | Zero sorry |
|---------|------|-----------|-----------|
| CUP-4 uniqueness, CUP-8, CUP-9 | `UgpLean/Universality/CUP4TotalParity.lean` | <5s | ✓ |
| CUP-11c universal mod-7 CA | `UgpLean/Universality/CUP11ModSeven.lean` | 1.1s | ✓ |
| f_MDL structural theorems, GoE, Z₇ orbit | `UgpLean/Universality/CUP3DUniqueness.lean` | 1.5s | ✓ |
| PSC unification, GoE→N_gen chain | `UgpLean/Universality/CUP3DPSCUnification.lean` | <5s | ✓ |
| Physical incompleteness (6 named bridge axioms) | `UgpLean/Universality/CUP3DPhysicalIncompleteness.lean` | <10s | ✓ (cond.) |
| Two-layer Rule 110 confluence | `UgpLean/Universality/TwoLayerConfluence.lean` | <2s | ✓ |
| GTE tile compilation theorem | `UgpLean/Universality/GTECompilation.lean` | <5s | ✓ |
| GTE tile uniqueness (bisimulation) | `UgpLean/Universality/GTEUniqueness.lean` | <5s | ✓ |
| GTE encode/decode (round-trip via Batteries) | `UgpLean/Universality/GTEInfTapeEncoding.lean` | <5s | ✓ |
| GTE computability (Primrec, 1 named axiom) | `UgpLean/Universality/GTEComputability.lean` | <5s | ✓ (1 axiom) |
| Hypothesis B: tape-level unification | `UgpLean/Universality/HypothesisB.lean` | <5s | ✓ (1 axiom) |
| B+C chain, simultaneous coherence | `UgpLean/Universality/HypothesisBCChain.lean` | <5s | ✓ (1 axiom) |
| PSC → universality chain (Hypothesis C) | `UgpLean/Universality/PSCUniversality.lean` | <5s | ✓ (1 axiom) |

### External repository: rule110-lean

Cook 2004/2008 formalization (github.com/novaspivack/rule110-lean):

| Module | Content | Zero sorry |
|--------|---------|-----------|
| `CyclicTagSystem.lean` | CTS step, eval, bounds | ✓ |
| `InfTape.lean` | Infinite bool tape, Rule 110 step | ✓ |
| `Ether.lean` | Period-14 Cook ether, spatial shift | ✓ |
| `CookGliderCatalog.lean` | C2 glider phases, GliderConfig | ✓ |
| `CookGliderVerification.lean` | M-formula checks, C2 phases 0/4/5/6 native_decide | ✓ |
| `CTStoRule110.lean` | CTS → Rule 110 tape (2 named axioms: glider collision gap) | named axioms |

---

## Computational Artifacts

| Script | Location | What it produces |
|--------|----------|-----------------|
| `t_null_cup4.py` | `canonical_run/` | CUP-4 null test, p≈1.36% raw |
| `t_epic067_r2_corrected_survey.py` | `canonical_run/` | Orbit-satisfying rules survey |
| `t_epic067_r3_perturbed_orbits.py` | `canonical_run/` | Perturbed orbit test (8/10 no solution) |
| `t_epic067_r4_analytical.py` | `canonical_run/` | Algebraic derivation: orbit → all 8 Rule 110 bits |
| `t_cup12_mdl_minimal.py` | `canonical_run/` | CUP-12 MDL analysis |
| `t_cup12_cross_sector.py` | `canonical_run/` | f_CROSS 76-bit description |

---

## Key Results

| Result | Status | Source |
|--------|--------|--------|
| CUP-4: Rule 110 uniquely selected | A_Lean | CUP4TotalParity.lean |
| Orbit algebraically determines all 8 Rule 110 bits | A (computational + analytical) | orbit survey scripts |
| CUP-8: gen3 all odd parity | A_Lean | CUP4TotalParity.lean |
| CUP-9: Z₅ ring structure | A_Lean | CUP4TotalParity.lean |
| p≈0.003% structural significance | A_Lean | null test script |
| Orbit-universality structural (not coincidental) | A | perturbed orbit test |
| CUP-11c: universal mod-7 CA exists | A_Lean | CUP11ModSeven.lean |
| fmdl_never_outputs_4 (electron theorem) | A_Lean | CUP3DUniqueness.lean |
| GoE: gen₁ has zero Z₇ predecessors | A_Lean | CUP3DUniqueness.lean |
| Physical incompleteness (undecidable predicate) | A_Lean (cond.) | CUP3DPhysicalIncompleteness.lean |
| Two-layer Rule 110 confluence | A_Lean | TwoLayerConfluence.lean |
| Hypothesis B (tape-level unification) | A_Lean (1 axiom) | HypothesisB.lean |
| Hypothesis C (PSC → universality chain) | A_Lean (cond. RCC) | PSCUniversality.lean |
| CUP-12: 76-bit MDL description | A/D | t_cup12_mdl_minimal.py |

---

## Relation to Other Papers

- Cites P01 (SM derivation from GTE) — not re-derived
- Cites P04 (UWCA universality) — not re-derived
- Cites P22 (interaction vertices) — referenced in coupling uniqueness section
- P29 (dark sector braid atlas) — companion paper for dark sector details

---

*P28 PROVENANCE.md — 2026-05-17*
