# P30 — Cook Theorem Formalization Paper — OUTLINE

**Working title:** Machine-Certified Formalization of Cook's Rule 110 Universality Theorem in Lean 4

**Status:** Draft aligned with partial Lean certification (2026-05-19). Revise to unconditional wording when `rule110_turing_universal_from_cook` closes.

**Lean source of truth:** `/Users/nova/rule110-lean` — `CookUniversalityChain.lean`, `CookUniversalityScaffold.lean`, `CTStoRule110.lean`

---

## Front matter

- Title, author (authblk), date 2026
- `\input{nova_zenodo_doi_placeholder}` + `\NovaZenodoAfterTitle`
- Claim-strength box ($\CatAL$ vs partial discharge vs open axiom)
- Abstract: what is proved, what is partial, what remains open; link to P28 conditional incompleteness

---

## §1 Introduction

- Cook (2004, 2009): Rule 110 universality via cyclic tag systems (CTS) and glider collisions
- Goal of this paper: machine-checked formalization in Lean 4 (`rule110-lean`), not a re-proof on paper
- Relation to UGP P28: `rule110_simulates_computable` bridge; upgrading conditional → unconditional when complete
- Contribution taxonomy: infrastructure ($\CatAL$), discharged bridge lemmas, partial C1/C3 families, open global targets
- Roadmap paragraph

---

## §2 Cook's construction (mathematical overview)

- Rule 110, ether (period 14), gliders (C1/C2/C3, ossifier A, leader Ē)
- Cyclic tag systems: `cts_step`, appendants, evaluation
- Cook's simulation pipeline: TM → CTS → Rule 110 tape (high level; cite Cook2009, NearyW06)
- Neary–Woods collision checklist (five kinds) — role in `cts_step` correctness
- No Lean syntax yet; figures optional (ether period table from README)

---

## §3 Infinite-tape semantics in Lean

- `InfTape`, `infTapeStep`, `infRule110Steps`
- Ether stability: `infRule110Steps_cookEther_shift`
- **Icc locality:** `infRule110Steps_agree_Icc` — proof idea → Appendix E.1
- Overlay locality: `overrideCells_eq_base_on_Icc`, far-field drift setup
- List↔InfTape bridge: `listToInfTape`, `listReadDiff_eq_tape_has_glider_at` (`CookC2InfTapeBridge`)

---

## §4 Bridge axioms C1–C3 and the certification chain

- Named axioms in `CTStoRule110.lean`:
  - C1: `cook_c2_tape_bit_ax` (OPEN global)
  - C2: `cook_cts_step_sim_ax` (DISCHARGED)
  - C3: `cook_cts_eval_sim_ax` (OPEN global); C3′ data-cone variants
- `CookCtsEvalSim`, `CookCtsEvalSimAt`, `CookCtsEvalSimAtDataCones`
- `CookUniversalityDischarged` structure — fields = partial bundle
- `cook_bridge_axioms_open` — what global closure requires
- Top target: `rule110_turing_universal_from_cook` (OPEN)

---

## §5 Discharged results ($\CatAL$)

### 5.1 Stage 1 — far-field ether drift

- `cook_cts_step_sim_ax` / `cook_cts_step_sim_far_field`
- Hypothesis: `cts_word_far_boundary w.length + M ≤ i`
- Proof architecture: overrides outside cone → `infRule110Steps_agree_Icc`

### 5.2 Stage 1b — partial C1 (L ≤ 7)

- List sim, InfTape `natToWord`, with_support, with_support_idx
- `cook_c2_tape_bit_decoder_exists_upto7`
- Ossifier bare equivalence (`CookC2SupportBareEquiv`) — analytical L ≤ 7 support readback
- Min-word isolated encoding (`cook_c2_tape_bit_min_word`)

### 5.3 Stage 2 — support encoding and collisions

- `cts_to_rule110_tape_with_support_idx`
- Five collision kinds — `cook_collision_all_five_kinds_certified` (negative witnesses: cone not fixed)

### 5.4 Stage 3 — operational partial chain

- Empty appendant: C3′ all $n$ (`cook_standard_empty_cts_data_cones`)
- L = 6 partial: `cook_min_len6_cts`, origin + phased decode
- Legacy C3 empty $n=1$ **refuted** (`CookLegacyC3EmptyN1Blocked`)
- `CookStage3OperationalDischarged`

### 5.5 Stage 4 — TM compilation scaffolds

- `TMCompilesStep`, `cook_stage4_tm_compiles_step_bundle` (identity, Bool, consume-head, countdown)
- `CookFinTM2Compiles` — **OPEN** for general FinTM2

---

## §6 Partial discharge inventory

- Table: `CookBridgeAxiomTag` vs `cook_bridge_axiom_partial_discharge`
- Parameter bounds (L ≤ 7, slot ≤ 6 decoder, slots ≤ 20 min-word)
- What partial discharge does **not** imply (global C1 shape)

---

## §7 Open problems and completion criteria

- Global `cook_c2_tape_bit_ax`
- `CookFinTM2Compiles` / Cook §2 TM→CTS encoding
- Global `cook_cts_eval_sim_ax`
- `rule110_turing_universal_from_cook`
- Engineering notes: init-cone `native_decide` vs analytical cone transport (no process language)

---

## §8 Conclusion

- Summary of machine-checked infrastructure
- Honest gap statement
- P28 upgrade path when complete

---

## Acknowledgments / AI disclosure (if venue requires)

- Lean 4 / Mathlib; Cook sources; optional AI-assisted drafting disclosure block

---

## Appendices (P01-style A–E)

### Appendix A — Theorem and lemma inventory

- Long table: name | statement sketch | module | status (discharged / partial / axiom)

### Appendix B — Lean module map

- Dependency diagram (text): Basic → InfTape → Ether → CTS → CTStoRule110 → CookC2* → CookStage* → CookUniversalityChain

### Appendix C — Artifact manifest

- `rule110-lean` repo, `cook_blocks.json`, `scripts/gen_cook_block_data.py`, `scripts/cook_m_values.py`
- No ugp-physics Python artifacts for P30

### Appendix D — Reproducibility

- Prerequisites: Lean 4.29, Mathlib v4.29.1, `lake build`
- Expected: green build, count bridge axioms via `#print axioms` on key theorems

### Appendix E — Proof sketches

- E.1 `infRule110Steps_agree_Icc` (Icc locality)
- E.2 Support/data cone disjointness (`cts_support_agrees_on_data_cone_gen`)
- E.3 Bare-equivalence ossifier readback (`c2SimReadAtWithOssifier_eq_bare`)

---

## Bibliography

- `\bibliography{../bib/Spivack_Papers_Bibliography,cook_theorem_refs}`
- Central: Cook2004, Cook2009, SpivackCompUniversality, Spivack2025_UGPDynamicsUniversality
- Local: NearyW06, rule110-lean (misc)
