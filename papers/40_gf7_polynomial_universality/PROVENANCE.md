# PROVENANCE — P40 — Algebraic Characterization of Rule 110 over GF(7)

**Paper:** P40 — "Algebraic Characterization of Rule 110 over GF(7) and Cook-Independent Turing Universality"  
**Date:** 2026-05-25  
**Author:** Nova Spivack  
**Series:** UGP Physics, Paper 40

---

## Derivation Record

### Result 1: GF(7) polynomial representation (CatAL)

**Source:** Algebraic interpolation over Z/7Z; P28 CPP/GF(7) universality chain  
**Lean:** `rule110-lean/Rule110/AlgebraicUniversality.lean`  
**Theorems:** `rule110_z7_poly_rep`, `rule110_center1_is_nand`, `rule110_z7_nand_identity` (zero sorry)

**Key identity:**
\[
p(L,C,R) = C + R - C{\cdot}R - L{\cdot}C{\cdot}R \in \mathrm{GF}(7)
\]

### Result 2: NAND gate at C=1 (CatAL)

**Lean:** `rule110_center1_is_nand` — when center cell is active, Rule 110 implements NAND(L,R).

### Result 3: Cook-independent Turing universality (CatAL conditional on one axiom)

**Lean:** `rule110_turing_universal_algebraic` from `boolean_nand_complete` (Sheffer 1913).

**Cross-route:** `ugp-lean/UgpLean/Universality/PhiMDLUniversality.lean` — `phimdl_turing_universal` (zero sorry, no Cook dependency).

### Result 4: Physical substrate cross-refs

**P28:** Computational Physics Principle sufficiency (Φ_MDL Turing universality)  
**P34:** Z₇-KG kink quantum numbers (`z7kg_kink_universality`)  
**Formalization paper:** Poincaré invariance of KG dispersion (`poincare_invariance_of_kg`)

---

## Confidence Levels

| Result | Evidence |
|--------|----------|
| GF(7) polynomial identity | Lean `native_decide`, zero sorry |
| NAND at C=1 | Lean `decide`, zero sorry |
| Turing universality (algebraic route) | 1 named axiom (Sheffer completeness) |
| Φ_MDL Turing universality | Lean zero sorry in PhiMDLUniversality |

---

## Paper Pass — 2026-05-25

New paper P40 created. No Python scripts — purely Lean-certified algebraic route plus cross-citations to ugp-lean substrate modules.

---

*PROVENANCE.md — P40 — 2026-05-25*
