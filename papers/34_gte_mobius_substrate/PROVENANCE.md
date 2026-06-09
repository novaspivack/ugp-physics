# PROVENANCE — P34 GTE-Möbius Substrate

**Paper:** `papers/34_gte_mobius_substrate/gte_mobius_substrate_paper.tex`  
**Status:** Draft (~28 pages, 2026-05-20)

---

## Origin

Formal substrate + NEMS framework instance from epic_071 (`SPEC_236_GTF`, Rank 236-GTF). Sits between P33 (deeper consequences) and P35 (unification capstone).

---

## Lean sources (current)

| Module | Repo | Commit / note |
|--------|------|---------------|
| `GTEFrameworkInstance.lean` | `ugp-lean` | `41a1461`; zero sorry; 1 bridge axiom |
| `GUTStructure.lean` §62 TPC | `ugp-lean` | 13-theorem block |
| `GUTStructure.lean` §67 C3 | `ugp-lean` | TPC completeness |
| `LawvereZone.lean` | `ugp-lean` | C4 correspondence (R249.1) |
| `GTEComputability.lean` | `ugp-lean` | Rule 110 / GTE compilation |
| `GTEFinalCoalgebra.lean` | `ugp-lean` | `5f5df60`; zero sorry, zero axiom; C1 Theorem (CatAL) |
| `GTEOptimalityInstance.lean` | `ugp-lean` | `5f5df60`; zero sorry; GTE orbit-admissible instance |

**Graduation target:** canonical `ugp-lean`; update appendix table from `ugp-lean` labels.

---

## Computational artifacts

**Graduated 2026-05-24** to `papers/34_gte_mobius_substrate/scripts/`:

| Script | Rank | Status |
|--------|------|--------|
| `mdl_uniqueness_score.py` | 96-MDLUNIQ | CatAL (all layers) |
| `mdl_l1_potential_closure.py` | 96 L1 | PROVISIONAL-UNCONDITIONAL |
| `z7_fca_phase_check.py` | 45-Z7FCA | COMPLETE |

Cross-reference: `fmdl_wolfram_category.py` in P28 (Rank 46-CAT).

---

## Change log

| Date | Change |
|------|--------|
| 2026-05-19 | Directory + PLANNED stubs |
| 2026-05-20 | Full paper draft; R236.1 C3 prose APPLIED; REPRODUCE/PROVENANCE populated (audit) |
| 2026-05-20 | C1 promoted from Conjectured (CatD) → **Proved (CatAL)**; `GTEFinalCoalgebra.lean` commit `5f5df60`, zero sorry, zero axiom; all 7 proof stages complete; updated conjecture→theorem, scope table, summary table, appendix tables, abstract, Lean cert table |

---

*PROVENANCE.md — P34 — 2026-05-20*

---

## Paper Pass — 2026-05-24

**What changed:**

1. **Claim-strength macros** — Changed `\catAL`, `\catA`, `\catAD`, `\catD` macro definitions to render as abbreviated scientific notation (A_L4, A, A/D, D) rather than literal "CatAL" etc.
2. **Claim-strength taxonomy box** — Added tcolorbox defining the abbreviations in plain scientific terms.
3. **§Scope** — Updated "CatAD" literal in prose → `\catAD`.
4. **§C3 TPC Completeness** — Fixed "CatA-certified" → "analytically established", "CatAL" → "machine-certified".
5. **§C4 Lawvere-Physical** — Fixed "CatAD pending C3" → "analytically derived, pending C3".
6. **§Open Problems (fine-angle)** — Fixed two "CatAL" literals → "machine-certified in Lean 4".
7. **§Φ_MDL Realization** — Added motivating paragraph explaining why the continuous field realization is needed (bridge from abstract algebra to physical field).
8. **§Algebraic Lifting Theorem** — Added motivating paragraph explaining the beable-vs-physical scale gap that the theorems close.

*PROVENANCE.md — P34 — 2026-05-24*

---

## Paper Pass — 2026-05-25 (EPIC_073 graduation)

**Ranks:** 070-107, 281-3DH, 281-3DH-B, 280-NTH, 285-FCA, 286-FCA

| Result | Rank | Script / Lean | Status |
|--------|------|---------------|--------|
| PSC/PI → [D] Lorentz equivariance | 070-107 | `PSCPILorentzMain.lean` | CatAL (1 structural axiom `d2_universal`) |
| 3D GTE Hamiltonian spec | 281-3DH | `epic073_rank281_3dh_3d_hamiltonian_spec.py` | CatAD partial |
| SO(3) continuum emergence | 281-3DH-B | `epic073_rank281_3dh_b_so3_emergence.py` | CatAD |
| Noether angular momentum | 280-NTH | `NoetherAngularMomentum.lean` | CatAL partial |
| FCA Φ_MDL refinement route | 285-FCA, 286-FCA | cross-ref P28 | READY |

**Graduated:** two scripts → `papers/34_gte_mobius_substrate/scripts/` (2026-05-25).
