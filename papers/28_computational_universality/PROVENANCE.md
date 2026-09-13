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
| `t_orbit_survey.py` | `canonical_run/` | Orbit-satisfying rules survey |
| `t_perturbed_orbits.py` | `canonical_run/` | Perturbed orbit test (8/10 no solution) |
| `t_analytical_verification.py` | `canonical_run/` | Algebraic derivation: orbit → all 8 Rule 110 bits |
| `t_cup12_mdl_minimal.py` | `canonical_run/` | CUP-12 MDL analysis |
| `t_cup12_cross_sector.py` | `canonical_run/` | f_CROSS 76-bit description |
| `z2_sublayer_consistency.py` | `canonical_run/` | Z₂ MDL / c-value / Rule 110 vs 124 |
| `rule110_rule124_chiral_pair.py` | `canonical_run/` | Chiral pair v_R = \|v_L\| = 2/3 |
| `fmdl_predecessor_counts.py` | `canonical_run/` | GoE predecessor counts 16,807 states |
| `gte_predecessor_check.py` | `canonical_run/` | G₁ T⁻¹ = 0 |
| `NcColorArithmetic.lean` | `ugp-lean/GTE/` | N_c = 3 (Mersenne GCD + ridge factorial) |

**Graduated 2026-05-20 (sandbox → `canonical_run/`):**

| Script | JSON output |
|--------|-------------|
| `orbit_admissible_count.py` | — |
| `z7_conservation_landscape.py` | — |
| `gtp_chain_uniqueness.py` | — |
| `gtp3_sum_trajectory.py` | `gtp3_sum_trajectory_results.json` |
| `fmdl_decay_depth.py` | — |
| `transitivity_spectrum.py` | — |
| `photon_vacuum_casimir_analysis.py` | `photon_vacuum_casimir_results.json` |
| `ranks_46_50_casimir_items.py` | `ranks_46_50_casimir_results.json` |
| `z3_z7_color_extension.py` | `z3_z7_color_extension_results.json` |
| `z2_longitudinal_extension.py` | `z2_longitudinal_extension_results.json` |
| `z7_output_distribution.py` | `z7_output_distribution_results.json` |
| `fmdl3d_chirality.py` | `fmdl3d_chirality_results.json` |
| `gte_triple_neutral_discrimination.py` | — |
| `complex_z7_rule110.py` | `complex_z7_rule110_results.json` |
| `rule110_period3_glider.py` | — |
| `z5_transitivity_check.py` | — |

**Graduated 2026-05-20 (sandbox → `scripts/`):**

| Script |
|--------|
| `ca_vertex_table.py` |
| `z7_gauge_invariance_check.py` |

**Remaining Lean graduation (exp → canonical):** `OrbitPerturbationCatalog`, `Z7ChargeConjugation`, `GoEStabilityHierarchy`, `Z5TransitivityUniqueness`, `DimensionalSliceUniqueness`, `GTPNeutralDiscrimination`, `SMOrbitCausalIsolation`, `EWBosonStructure`, `GUTStructure`, `CasimirMasslessEther` — see REPRODUCE.md Step 1b.

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

---

## 2026-05-18 — Expert-Readability Improvements

Expert-readability improvements targeting presentation to a computational automata specialist audience:

- **Orbit neighborhood trace table** (§2.3, Table 2): added cell-by-cell derivation showing
  how each of the 10 orbit transitions activates a specific binary neighborhood with a
  uniquely determined output, making the algebraic derivation of Rule 110 from the SM orbit
  self-contained and checkable by inspection
- **Z₇ orbit state values table** (§6.2, Table 4): added complete gen₁/gen₂/gen₃ Z₇ values
  per SM family alongside SM winding numbers, with explicit note that orbit state values and
  SM winding numbers are distinct Z₇ quantities (orbit position vs.\ interaction charge)
- **f_MDL orbit neighborhood entries table** (§6.2, Table 5): added all 10 cell-by-cell
  Z₇ orbit transitions that constitute the fixed orbit entries of f_MDL, annotated with
  physical interpretations (quark flavor-change neighborhood, W⁺ emission neighborhood)
- **PSC implications scope remark** (§12.4): added remark clarifying which results in the
  paper are unconditionally proved by exhaustive arithmetic computation (CUP-4 orbit forces
  Rule 110; three-generation count; Z₇ coupling uniqueness) versus which are PSC-conditioned
  implications where the CA conclusion holds independently; prevents overstating the
  derivational force of the PSC chain
- **Statistical significance section rewrite** (§4): removed an incorrect three-factor
  multiplicative formula; primary significance claim is now CUP-4 algebraic uniqueness
  (Lean-certified exhaustive result); p_raw = 1.36% is presented as a bound on false-positive
  rate for random orbits; structural observations (rule selectivity, gen₃ all-ones, Z₅ ring)
  are documented as reinforcing but not independently multiplied
- **SM winding assignment context** (§1.2): added paragraph and equation distinguishing
  Z₇ orbit state values (gen₁ = [1,5,2,2,1]) from SM winding interaction charges
  ({0,2,3,4,6} ⊂ Z₇); prevents confusion between two distinct Z₇ structures present
  in the paper
- **Mathematica pseudocode** (§2.1): added five-line CUP-4 verification pseudocode
  allowing expert readers to reproduce the orbit check interactively
- **Rule 110 universality proof status** (abstract, §1, §5): clarified that Rule 110 is
  the only elementary CA rule with a *completed, published proof* of computational
  universality; Rules 124 and 126 are conjectured universal but remain formally unproved
- **Z₇=1 matter-antimatter comparison** (§9.3): corrected the matter-dominance discussion
  to use only SM winding values {0,2,3,4,6} for the asymmetry comparison; Z₇∈{1,5} are
  non-SM orbit-internal values and do not appear in the winding-based particle count
- **CUP-12 language** (§8 Remark 8.3): softened "not an open problem" language to
  distinguish the mathematical content of CUP-12 (MDL-minimality of f_MDL, Lean-certified)
  from the physical identification of f_MDL as the CA governing the SM generation sector
  (a working hypothesis based on the MDL principle)
- **76-bit description length** (§8.1): added sentence explaining the compact binary
  counting scheme: each of the 27 fixed neighborhoods requires 9 bits for the index
  (⌈log₂ 7³⌉) and 3 bits for the output value (⌈log₂ 7⌉), giving ≈76 bits
- **1920 orderings footnote** (§6.1): added footnote clarifying the combinatorial source
  of the 1920 figure in CUP-11b (candidate neighborhood-to-output assignment orderings
  in the Z₇ orbit analysis of the 5-cell periodic ring)
- **gen₁ perturbation note** (§5.2): added paragraph explaining why gen₁ perturbations
  are not tested in the same way as gen₂/gen₃ perturbations (gen₁ is the initial condition,
  not a CA output, so perturbing it defines a new orbit problem rather than a perturbation)
- **Bridge axiom count** (App. A Lean inventory): corrected to six named bridge axioms
  in CUP3DPhysicalIncompleteness.lean (previously stated as seven at one location)
- **Artifact manifest** (App. C): added `t_cup12_cross_sector.py` and
  `t_cup12_cross_sector_results.json`, which were referenced in §8.1 but absent from
  the manifest

**Commit:** `3978b419` (paper and companion doc edits) + subsequent documentation commit  
**Pre-existing macro fix:** Added missing `\newcommand{\Nc}{N_c}` definition to preamble

---

## 2026-05-18 — CUP-11b Z₇ Sum Conservation and Attractor Basin (§6)

§6 CUP-11b — Z₇ sum conservation: Lean-certified result (`cup11b_z7_sum_conservation`, `CUP3DUniqueness.lean` §6, commit `bc87df8`, CatAL, zero sorry). Result: gen₁ conserves Z₇ sum under f_MDL (sum 4→4); gen₂ and gen₃ do not (4→3, 3→0). The totalistic rule g = [6,5,6,3,3,6,3] is noted as a structurally related Wolfram Class 2 CA over Z₇.

**Commit:** `5072d003`

---

## 2026-05-19 — CatAL Upgrades and New Structural Results (Specs 01–06)

Six completed specs contributed the following content now in the paper:

**Spec 01 — Z₇ Sum Conservation Characterization (§6, CUP-11b)**
- CUP-11b theorem status: CatAL. Z₇ sum conserved at gen₁ (sum 4=4), broken at gen₂ and gen₃.
- Reviewer map table: CUP-11b row upgraded to CatAL.
- New remark: complete characterization of Z₇-sum-4-conserving states — exactly 10 of 7⁵=16,807 states (5 cyclic rotations of gen₁ and 5 of [0,2,5,2,2]). Lean: `cup11b_z7_sum4_conserving_count`, `cup11b_z7_sum4_conserving_characterization` (`CUP3DUniqueness.lean`, commit `bc87df8`).

**Spec 02 — Weight-5 Minterm Uniqueness (§5.3, orbit-universality theorem)**
- Orbit-universality structural connection theorem upgraded to CatAL. Among all 56 weight-5 binary CA rules, Rule 110 is the unique orbit satisfier with vacuum-transparency (`rule110_unique_weight5_orbit_satisfier`, `CUP4TotalParity.lean`).
- `orbit_weight_dichotomy` (CatAL): among orbit-satisfying rules, vacuum-transparency ↔ Hamming weight 5.
- New remark: non-minterm neighborhoods {0,4,7} have physical interpretations (vacuum, left-only, all-ones). Lean: `rule110_non_minterm_set`.

**Spec 03 — Orbit Perturbation Catalog (§5.2, Table 1)**
- Perturbed orbit table now cites Lean certification: `orbit_perturbation_destroys_universality` (`OrbitPerturbationCatalog.lean`, commit `78b1e41`, zero sorry).
- `rule110_orbit_complete_isolation` (CatAL): (smGen₂, smGen₃) is unique 2-step orbit output from smGen₁ over all 1024 pairs.
- Reviewer map: orbit-universality row upgraded CatA → CatAL.

**Spec 04 — Z₇ Charge Conjugation (§6.2, §9.3)**
- New theorem: Z₇ charge conjugation structure (CatAL). C(v)=(7−v)%7 formalized; C(v)=v ↔ v=0; involution; sum-to-zero; three conjugate pairs (1,6), (2,5), (3,4). Lean: `z7_conj_self_conjugate_iff_zero`, `z7_conj_involution`, `z7_conj_sum_zero`, `z7_conj_pairs` (`Z7ChargeConjugation.lean`, commit `d1ea294`).
- `fmdl_conj_pair_asymmetry_unique` (CatAL): Z₇=3 (W⁺) is the unique value in the f_MDL output range whose conjugate is not in the range. `fmdl_w_plus_unique_neighborhood` (CatAL): (2,0,2) is the unique Z₇=3 neighborhood.
- §9.3 matter-dominance text sharpened to the arithmetic CatAL level. Z₇ CP violation remark upgraded to CatAL citing the new Lean theorems.
- Preimage counts stated: 0→329, 1→5, 2→3, 3→1, 4→0, 5→4, 6→1 (`fmdl_preimage_counts`, `native_decide`).

**Spec 05 — GoE Orbital Chain Isolation (§12.2)**
- New theorem: Orbital Chain Isolation (CatAL). Exact f_MDL predecessor counts: pred(gen₁)=0, pred(gen₂)=1, pred(gen₃)=1. The orbit is a completely isolated linear chain. Lean: `fmdl_orbit_linear_chain`, `fmdl_gen2_unique_predecessor`, `fmdl_gen3_unique_predecessor` (`GoEStabilityHierarchy.lean`, commit `b8a45a8`).
- Physical interpretation: generation decay is deterministic and non-confluent; τ-like states arise only from μ-like states.
- Dual-layer stability: GTE-level GoE (algebraic, `GoEHierarchy.lean`) and CA orbital chain isolation together encode stability at both the mass-cascade and winding-dynamics levels.
- Reviewer map: new GoE orbital chain row (CatAL).

**Spec 06 — Z₅ Transitivity Uniqueness (§3, §11 "Why Z₅?")**
- New remark (§3 after CUP-9): p=5 is the unique prime ≤ 23 for which Rule 110 acts with full Hamming-3 transitivity on all cyclic rotations of a weight-3 vector (2-step orbit to all-ones). Total null for primes {2,3,7,11,13,17,19,23}. Lean: `z5_transitivity_uniqueness` (`Z5TransitivityUniqueness.lean`, commit `12ba03c`, zero sorry).
- §11.7 "Why Z₅?" open problem replaced with partially-answered text citing the transitivity uniqueness theorem as a CA-internal reason for N_fam=5, independent of P01's algebraic derivation.
- Artifact manifest: `z5_transitivity_check.py` (Python prime sweep, <1s runtime).

**App. A (Lean inventory)**: six new modules added to per-file sorry summary and longtable:
`OrbitPerturbationCatalog.lean`, `Z7ChargeConjugation.lean`, `GoEStabilityHierarchy.lean`, `Z5TransitivityUniqueness.lean`; plus new theorem rows for `CUP4TotalParity.lean` §10–§11 and `CUP3DUniqueness.lean` Z₇ sum conservation theorems.

---

## 2026-05-19 — Specs 07, 09 and Ranks 11, 12 Updates (Second Post-Spec Pass)

**SPEC_070_07 (Dimensional Slice Uniqueness, D7U) — COMPLETE**
- New Remark (§2.3 after CUP-4 corollary): CUP-4 is not 1D-specific; `dimensional_slice_uniqueness` (CatAL, `DimensionalSliceUniqueness.lean`, commit `c0e9231`, zero sorry, 17 theorems). Removing vacuum-transparency gives 2 valid rules; condition is essential (`dim_slice_vacuum_essential`).
- New Corollary `cor:dsu` (§9.1 after 3+1D causal geometry theorem): dimension-independent Rule 110 selection. All 3 axes simultaneously forced in 3D (`three_dim_all_slices_rule110`). Complete f_MDL,3D structure forced by SM physics (`three_dim_fmdl_structure_forced`).
- App. A: new `DimensionalSliceUniqueness.lean` entry with all 17 theorems listed.

**SPEC_070_08 (Cook, K1R) — skipped (IN_PROGRESS)**

**SPEC_070_09 (GTE Uniqueness Lean, G8B) — COMPLETE**
- §12.4 (after GTE Uniqueness Theorem paragraph): Lean result is stronger than monograph's theorem — minimality not a necessary hypothesis. `gte_uniqueness_up_to_bisimulation` (CatAL) is unconditional; `sigma_gte_is_minimal` and `lawful_iff_bisim_sigma_gte` confirm minimality as consequence. Commits `7214db5`, `58a6b1d`.
- App. A: `GTEUniqueness.lean` entry updated with `sigma_gte_is_lawful`, `IsMinimalProgram`, `sigma_gte_is_minimal`, `lawful_iff_bisim_sigma_gte`, `gte_uniqueness_complete`.

**SPEC_070_10 (Orbital Helicity, H0P) — skipped (FAILED, all CANCELLED)**

**Rank 11 (GTE Triple Discrimination of Neutral Particles) — COMPLETE**
- §11.4: replaced "ν/γ/Z discrimination" open problem with partial closure. All five Z₇=0 SM particles with GTE triples (νe, νμ, ντ, Z, H⁰) pairwise distinguishable by (a,b,c) triples: two-level discriminant (b-component separates EW b=3 from neutrino b=1 sector; a or c identifies within sector). Machine-certified: `gte_triple_neutral_discrimination`, `GTPNeutralDiscrimination.lean`, commit `683e47a`, 10 theorems, zero sorry. Photon (no GTE triple) still requires spin/isospin.
- App. A: new `GTPNeutralDiscrimination.lean` entry with 10 theorems.

**Rank 12 (3D f_MDL Chirality, CA-Level Parity Violation) — Part A READY**
- §9.4 (CP violation Remark): added chirality sentences. SM orbit is intrinsically chiral — gen₁ (3-step orbit) vs P(gen₁) (2-step, vacuum-like). gen₃ is parity-covariant ("chirally neutral"). CatA, `fmdl3d_chirality.py`.
- §11.5 (Chirality open problem): added partial closure before "What remains open". 14/343 P-violating triples (4.1%); SM orbit structurally left-handed. CatA.

**Additional consistency fixes**
- §12.2 conclusion: updated "three open sectors" language to reflect partial resolutions (photon, full chirality encoding, color remain open).
- Introduction "Not claimed" box: updated to reflect partial resolution of ν/γ/Z discrimination.

---

## 2026-05-19 — Third Post-Spec Pass: Ranks 20–40 and B-Series CatAL Upgrades

Applied all READY P28-bucketed entries from Ranks 20, 22–27, 30–31, 34–35, 37–40 and Tasks B26, B41, B43, B44, B46, B47 plus the new zero-point entropy entry. Entries re-bucketed to P33 (Ranks 33, 36, 41 main treatments) and to P32 (B41 Wolfenstein, B48 CKM) were NOT applied to P28.

**§5 (Orbit-Universality) — Rank 34**
- New Remark `rem:orbit_admissible`: SM orbit imposes 23 constraints on Z₇ CA function; orbit-admissible class has 7^320 ≈ 10^270 elements; MDL uniquely selects f_MDL (CatA, `orbit_admissible_count.py`).

**§6 (CUP-11 / f_MDL properties) — Ranks 27, B34.1, B44.1, 41.2**
- New Remark `rem:conservation_landscape`: full Z₇ sum conservation table (v=0 to 6); sum=4 is rarest non-zero class (10/16807); orbit sum trajectory 4→4→3→0. CatAL: `z7_conservation_count_table`, `z7_sum4_uniquely_sparse`, `z7_gen3_not_sum_conserving`.
- New Remark `rem:fmdl_count`: f_MDL nonzero count = c_H + 1 = 14 = N_gen + 2·N_fam + 1. CatAL: `GUTStructure.fmdl_count_eq_chiggs_plus_one` (commit `db30758`).
- New Remark `rem:bsum`: b_sum = 390 = 2×3×5×13 encodes all SM structural parameters; Weinberg ratio 3/13 from prime factorization. CatAL: `b_sum_is_product`, `weinberg_ratio_from_bsum` (commit `7aacd43`).
- New Remark `rem:uniform_fp`: photon (Z₇=0) is unique uniform fixed point of f_MDL; CA ether interpretation. CatAL: `fmdl_unique_uniform_fixed_point`, `photon_is_ca_ether` (`CUP3DUniqueness.lean` §7d).

**§7 (CUP-12 GoE section) — Ranks 35, 36.2, B26.1**
- New Remark `rem:all_rotations_goe`: all 5 gen₁ cyclic rotations are GoE states; Z₅ ring symmetry = GoE family structure. CatAL: `fmdl_gen1_all_rotations_are_goe` (5×16807 cases, native_decide).
- New Remark `rem:z5_equivariance`: f_MDL is exactly Z₅-equivariant (84035 cases). CatAL: `fmdl_z5_equivariant` (commit `07b55a4`).
- New Remark `rem:goe_part1`: GoE property is Part 1 of 6-property causal isolation; forward ref to companion paper. CatAL: `sm_orbit_complete_causal_isolation`.

**§9 (3D / Interactions) — Ranks 39, B43, 33.2 brief**
- New sparsity certificate note in CP violation remark: 14/343 neighborhoods, none produce Z₇=4. CatAL: `fmdl_nonzero_count_14`.
- New Remark `rem:sm_vertex`: SM charged-current vertex (u,γ,u)→W⁺ is unique; 34/36 = 94.44% photon transparency. CatAL: `sm_charged_current_vertex`, `sm_w_minus_absence`, `u_photon_u_to_W_vertex` (commits `ddb6a84`, `Z7ChargeConjugation.lean` §5).

**§11 (Open Problems) — Ranks 25, 31.2, B41, ZERO-PT**
- §11 item 7 "Why Z₅?": extended with weight-3 exclusivity across all t≤4; p=7 has zero weight-3 transitivity; p=7 has one weight-4 transitive class. CatAL: `z5_w3_exclusive_among_primes`, `z5_w3_t1_full_transitivity`, `p7_w4_t1_full_transitivity`.
- New item: Z₇/Z₂ algebraic incompatibility (φ: Z₇→Z₂ not ring homomorphism; failure at Z₇=4). CatAL: `z7_binary_not_ring_homomorphism`.
- New item: CA masslessness criterion (f_MDL(0,k,0)=k iff k∈{0,1}); massive decay corollary. CatAL: `fmdl_massless_criterion`, `fmdl_massive_decay` (commit `ddb6a84`).
- New item: CA zero-point entropy = 0.000 bits/step for vacuum; random IC = 0.647 bits/cell/step. CatA: `photon_vacuum_casimir_analysis.py`.

**§12.2 (GoE and stability) — Ranks 22, 23, 26, 38, 40**
- New Theorem `thm:unique_vacuum`: vacuum is unique fixed point; no false vacua; all 16807 states converge ≤7 steps. CatAL: `fmdl_unique_fixed_point`, `fmdl_vacuum_is_unique_attractor` (native_decide).
- New Theorem `thm:gtp3`: SM orbit is unique GTP-3; exactly 5 GTP-3 chains; no GTP-4. N_gen=3 from CA graph topology. CatAL: `sm_orbit_unique_gtp3`, `fmdl_max_gtp_length_is_3`, `sm_orbit_gtp3_count`.
- New Corollary `cor:lepton_universality`: CA-level lepton universality (unique decay channels, equal cardinality, no mixing). CatAL: `fmdl_ca_lepton_universality`, `fmdl_no_generation_shortcut`.
- New Remark `rem:gtp3_trajectory`: GTP-3 sum fingerprint (4,4,3) is universal for all orbit-admissible f (not just f_MDL). CatAL: `gtp3_sum_trajectory_of_gen1_rotations`, `orbit_sum_trajectory_invariant`.

**§12.3 (Causal chain) — Tasks B47, B46**
- New Remark `rem:family_capacity`: N_gen + N_fam = 2^N_gen = 8 (generation-orbit filling identity); running shift = N_fam = Z₅ ring size. CatAL: `gte_family_capacity_identity`, `running_shift_is_z5_ring` (`GUTStructure.lean` §13).

**§12.7 (Relationship to existing results) — Ranks 20, 30**
- GTE Uniqueness section: upgraded bisimulation to isomorphism — any minimal lawful UWCA program is isomorphic (not just bisimilar) to Σ_GTE. CatAL: `gte_uniqueness_isomorphism` (`GTEUniqueness.lean` §5).
- New Remark `rem:decay_depth`: global decay depth profile; N_gen=3 = max non-binary depth; global horizon = 7 steps. CatAL: `fmdl_orbit_depth_profile`, `fmdl_universal_7step_convergence`, `fmdl_max_depth_is_7`.

**App. A (Lean inventory)**
- New sections: Z₅ Transitivity §8 extended (3 theorems); GoE Stability §6–§9 extended (10 theorems); CUP3D Uniqueness §7a–§10 extended (25 theorems); Dimensional Slice §4b (2 theorems); Z₇ Charge Conjugation §5–§6 extended (9 theorems); CA Masslessness and Ether (5 theorems); SM Orbit Causal Isolation (1 master theorem); GTE Uniqueness §5 extended (4 theorems); GUT Structure §9+§13+§16 (12 theorems).
- Per-file summary: 4 new modules added (`CasimirMasslessEther.lean`, `SMOrbitCausalIsolation.lean`, `GUTStructure.lean` §9/13/16, `GTEUniqueness.lean` §5).

**App. C (Artifact Manifest)**
- 8 new sandbox script entries: `orbit_admissible_count.py`, `z7_conservation_landscape.py`, `gtp_chain_uniqueness.py`, `gtp3_sum_trajectory.py`, `fmdl_decay_depth.py`, `transitivity_spectrum.py`, `photon_vacuum_casimir_analysis.py`, `ranks_46_50_casimir_items.py`. To be migrated to `canonical_run/` at graduation.

**Page count:** 43 → 53 pages after this pass.

---

## Pass 4 — Fourth Pass: Adversarial Read + Remaining Entries (2026-05-19)

**Files changed:** `computational_universality_ugp.tex`  
**Commits:** `3d61478e`  
**Zenodo impact:** No deposit until full paper series ready.

### Issues Found and Fixed (Adversarial Read)

**Issue 1: Depth-5/6 swap in global decay profile remark**  
- Error: Paper said "depth 5: 715; depth 6: 170" but lab notes (verified by `fmdl_decay_depth.py`) give "depth 5: 170; depth 6: 715". Fixed by swapping the two numbers in Remark `rem:decay_depth`.

**Issue 2: Internal label "Rank~56" in paper body**  
- `\S12.3` Remark `rem:family_capacity` referenced "Rank~56" (an internal tracking label). Replaced with "from GUT orbit arithmetic, see companion paper on Weinberg angle derivation."

**Issue 3: Apparent $7^{325}$ vs $7^{320}$ inconsistency**  
- CUP-11c says "$7^{325}$ free completions" (constraining only the 18 non-trivially non-zero neighborhoods). The orbit-admissible remark (entry 34.1) says "$7^{320}$ elements" (23 constraints including 5 gen₃→vacuum zero outputs). Added reconciling parenthetical to the orbit-admissible remark explaining that the difference is the 5 gen₃→vacuum constraints which are orbit-required to output 0 but already match the MDL default.

### New Entry Applied

**B45.1 (Task B-45, Rule 110 ether = neutrino sector background)**  
- New Remark `rem:ether_neutrino` in §9.3 (after the CP violation remark): The Rule 110 ether carries Z₇ winding = 1 (neutrino sector), not Z₇ = 0 (EM vacuum). Corrects the two-level structure labeling. CatAL: `ether_z7_sum_mod7`, `ether_not_em_vacuum`, etc. (commit `ddb6a84`).
- Added `ether_z7_sum_mod7` and `ether_not_em_vacuum` rows to App. A Lean inventory longtable.

### Entry Disposition

- **31.1** (formal Z₇/Z₂ ring incompatibility lemma): Covered by existing §11 item 8 remark (entry 31.2, applied in commit `0faefb8f`). Marking CANCELLED as superseded.
- **28.1, 28.2** (Z₅ equivariance in §9/§11 + App. A entry): Already covered by Remark `rem:z5_equivariance` in §7.1 (CUP-12 section, B26.1 applied in `0faefb8f`). Marking PLANNED → CANCELLED as superseded.

**Page count:** 53 pages (unchanged from pass 3).

---

## Pass 5 — Final update pass (2026-05-19)

**What changed:**
1. **B76.1 — Wolfram citation added to §1 Introduction.** Two sentences added after the first mention of Rule 110 in §1, crediting prior empirical identification of Rule 110 as the paradigmatic class-4 CA (`\cite{Wolfram2020Tech}`) and positioning this paper's algebraic derivation as a strictly stronger result.

2. **B44.3 — Rule 110 and Rule 124 joint MDL count added to §11 (Open Problems).** New item #11: Among vacuum-transparent binary CA rules, Rules 110 and 124 share the minimum MDL one-count of 5. Rule 110 is preferred by sublayer consistency (differs from Rule 124 at exactly neighborhoods (0,0,1) and (1,0,0)). Lean-certified: `rule124_minterms_card`, `rule110_and_124_joint_mdl_count`, `rule110_preferred_by_sublayer_consistency` (GUTStructure.lean §17, commit `7aacd43`).

3. **B52.1 — Goldstone cascade formula added to CUP-11 section (after `rem:bsum`).** New Remark `rem:goldstone_cascade`: the EW boson GTE cascade depths obey c_P = c_H − d_P where d_P ∈ {0,1,2} is the number of Goldstone d.o.f. absorbed. Lean-certified: `goldstone_cascade_higgs/z/w/formula` (EWBosonStructure.lean §5, commit `8e7c6aa`).

4. **B52.2 — EWBosonStructure §5 theorems added to Lean inventory.** New section in App. A longtable and new `\item` in the module list for `EWBosonStructure.lean` (4 theorems + 3 defs, zero sorry, commit `8e7c6aa`). GUTStructure.lean entry updated to include §17 (Rule 124 MDL count theorems).

**Compile:** 54 pages, 4-pass clean (zero new overfulls > 1pt; only pre-existing 1.01pt entries in TwoLayerConfluence/PSC longtable rows).

**Zenodo impact:** No deposit until full paper series ready (P28+P30–P33).

---

## Pass 6 — Absolutely final pass: bidirectional unification (2026-05-19)

**What changed:**

1. **§12 Conclusion — bidirectional unification paragraph added.** New `\paragraph` near the end of the Conclusion subsection (before the PSC chain paragraphs), summarizing that all results in this paper and companion papers P31/P32/P33 are subsumed by `ugp_r110_sm_joint_unification` (`GUTStructure.lean §27`, commit `0fb7921`, zero sorry). Lists the 7 certified conjuncts: arithmetic bridge $N_{\rm gen}+N_{\rm fam}=2^{N_{\rm gen}}$; EW Weinberg $\sin^2\theta_W=3/13$; GUT formula $\sin^2\theta_W(M_{\rm GUT})=3/8$; CKM $\lambda=9/40$; double Mersenne endpoint; photon as unique CA fixed point; gen₁ as Garden of Eden.

2. **App. A — GUTStructure §23 (GTE master formula) added to longtable.** 9 theorems: `gte_master_formula_complete` (capstone, 4 SM EW parameters from $N_{\rm gen}=3$), `gte_generating_triple`, `gte_master_formula_{gut_weinberg,ew_weinberg,wolfenstein,rb}`, `gte_cross_sector_bridge`, `gte_arithmetic_root`, `ngen_3_mersenne_uniqueness`. Commits `9f07d7e`/`b30bf27`, zero sorry. (Applies B70.5.)

3. **App. A — GUTStructure §27 (bidirectional unification) added to longtable.** 6 theorems: `ugp_arith_forces_rule110`, `sm_selects_gte_triple`, `gte_predicts_ew_mixing`, `gte_predicts_ckm_lambda`, `rule110_encodes_sm_particles`, `ugp_r110_sm_joint_unification` (capstone, 7-conjunct). Commit `0fb7921`, zero sorry.

**Compile:** 55 pages, 4-pass clean (only pre-existing 1.01pt hbox overfulls; vbox overfulls are pagination-only).

**Zenodo impact:** No deposit until full paper series ready (P28+P30–P33).

---

## Pass 7 — Single-cycle / 't Hooft information-loss (2026-05-19)

**What changed:**

1. **§12 Discussion — 't Hooft information-loss paragraph extended.** Added 3 sentences after the existing 't Hooft CAI citation: orbit decomposition of f_MDL on Z₇⁵ has exactly one periodic orbit (vacuum fixed point), placing the dynamics in Chapter 7 (information-loss category) of 't Hooft's framework; tail-length hierarchy gen₃=1, gen₂=2, gen₁=3 (GoE) matches physical stability ordering. CatA, numerical verification over all 16,807 states.

**Compile:** 55 pages, clean (only pre-existing 1.01pt hbox overfulls, unchanged).

**Zenodo impact:** No deposit until full paper series ready (P28+P30–P33).

*P28 PROVENANCE.md — 2026-05-19*

---

## Pass 8 — Chiral pair Lorentz-symmetric light cone (2026-05-19)

**What changed:**

1. **§12 Discussion (Wolfram connection paragraph) — chiral pair remark added.** After the preferred-frame confirmation sentence (v_R=2/3, v_L≈1/3, ratio≈2), added three new sentences: Rule 124 (spatial mirror of Rule 110) carries an exactly mirrored period-3 glider at v_L = −2/3 (CatA); the two-layer chiral CA {Rule 110 + Rule 124} achieves v_R = |v_L| = 2/3 with 100% period-3 purity (T=300 steps); this provides a concrete CA-level Lorentz-symmetric light cone at the cost of doubling the CA layers.

**Compile:** 58 pages, clean (zero hbox overfulls; pre-existing vbox pagination overfulls unchanged).

**Zenodo impact:** No deposit until full paper series ready (P28+P30–P33).

*P28 PROVENANCE.md — 2026-05-19*

---

## 2026-05-24 — Track B paper pass: F₂₁/QCD/hadron/lifting sections

New section added: `sections/physical_substrate_extensions.tex` (included in main tex at §12.6 boundary):
- **F₂₁ = Z₇ ⋊ Z₃ substrate identification** with SU(3) branching proof
- **Algebraic Lifting Theorem** — beable → physical (LiftingTheorem.lean, zero sorry)
- **3D spatial composite lifting** — mesons as spatially separated quark–antiquark pairs (SpatiallyExtendedLifting.lean, zero sorry)
- **Algebraic Descent Theorem** — F₂₁-algebraic properties M-independent (AlgebraicDescentTheorem.lean, zero sorry)
- **Colour confinement**: `no_psc_admissible_single_quark`, `qft_gauged_mass_gap_unconditional` (ColorConfinement.lean, GaugedMassGap.lean)
- **Asymptotic freedom**: b₀=7, b₁=26 (SylowIndexCouplingHierarchy.lean, zero sorry)
- **Hadron spectroscopy**: θ_P = −13.08° ± 3.74° (PDG range: [−14.3°, −10.7°]), χ_top^(1/4) = 166.5 MeV (PROVISIONAL)
- **EFT domain of validity**: Λ_GTE ≈ 2 GeV

Full vocabulary pass: removed all internal confidence-category labels from prose throughout main paper and new section; replaced with English equivalents.

## Step 28: Vertex catalog, GF(7), and decay-rate scripts

```bash
cd papers/28_computational_universality/scripts
python3 gauged_vertex_catalog.py
python3 gf7_orbit_code_check.py
python3 fmdl_wolfram_category.py
```

Decay rates (companion Paper 33): `papers/33_deeper_consequences/scripts/decay_rates_from_gte.py`

**Graduated 2026-05-24** (sandbox → `scripts/`):

| Script | Source rank | Board status |
|--------|-------------|--------------|
| `gauged_vertex_catalog.py` | 93-VXCATALOG | COMPLETE |
| `gf7_orbit_code_check.py` | 39-CYC | COMPLETE |
| `fmdl_wolfram_category.py` | 46-CAT | COMPLETE |
| `f21_substrate_identification.py` | 112-FROBENIUS | CatA+CatAL |
| `asymptotic_freedom_f21.py` | 117-AFRGCHECK | CatA |
| `beta_function_two_loop_f21.py` | 119-TWOLOOP | CatA |
| `f21_su3_deconstruction_flow.py` | 115-DECONSTRUCT | PROVISIONAL CatA |
| `hadron_multiplets_gte.py` | 106-HADMULT | CatA |
| `jp_spin_mdl_derivation.py` | 125-JPSPIN | CatAL |
| `vector_meson_nonet_hyperfine.py` | 126-VECMESON | PROVISIONAL CatA |
| `quark_masses_gte.py` | 128-QUARKMASS | CatA |
| `pion_decay_constant_dhn.py` | 131-FPIGTE | CatA |
| `eta_mixing_angle_zero_pdg.py` | 129-THETAP | CatA |
| `chiral_condensate_nlo.py` | 134-NLO-B0 | CatA |

*P28 PROVENANCE.md — script graduation audit 2026-05-24*

---

## 2026-05-24 — Rank 18 meson scan: NOT graduated (superseded)

Rank 18-MES numerical scan scripts (`rank18_mes_meson_existence.py`, `rank18_mes_extended_scan.py`, `rank18_mes_rigorous_scan.py`, `rank18_mes_run18d.py`) and `rank18e_collision.py` (2-particle 1D collision test) are **not graduated** to `scripts/`.

The key P28 bound-state results are:
- `meson_bound_state_exists` and `baryon_bound_state_exists` — Lean-certified via `SpatiallyExtendedLifting.lean` (Rank 55-3DLT + Rank 140-3DLT-BARYON, CatAL, zero sorry)
- Color confinement — `no_psc_admissible_single_quark` (16,807 states, Lean)

The rank18 numerical scan (135 PSC-admissible color-neutral k=3 composites; meson null) was superseded by the Lean proofs in Ranks 55-3DLT and 140-3DLT-BARYON. The paper cites only the Lean-certified results. The sandbox scripts remain in `research-sandbox/` for archival reference.

---

## Paper Pass — 2026-05-25 (EPIC_073 FSS + CUP-5 graduation)

**Ranks:** 5-FSS, 5-FSS-COOK-PHASED, 5-FSS-COOK-CENTRAL, 5-FSS-COOK, 252-CUP5E, 281-3DH-B (cross-ref P34)

| Script | Rank | Status |
|--------|------|--------|
| `epic073_rank5_fss_r110_self_simulation.py` | 5-FSS | CatA negative partial |
| `epic073_rank5_fss_cook_phased.py` | 5-FSS-COOK-PHASED | CatA partial |
| `epic073_rank5_fss_cook_central.py` | 5-FSS-COOK-CENTRAL | CatA negative |
| `epic073_rank5_fss_cook_block_assembler.py` | 5-FSS-COOK | scaffold |

**Graduated:** four FSS scripts → `papers/28_computational_universality/scripts/` (2026-05-25).

**CUP-5 chain:** five computational rounds negative (252-CUP5 through 252-CUP5E); open problem unchanged in paper.

---

## 2026-06-10 — Λ_GTE matching scale: derived value replaces calibration

`sections/physical_substrate_extensions.tex` (eq. lambda_gte and dependent prose):
the PROVISIONAL calibration Λ_GTE = N₇·m_kink ≈ 2.01 +0.24/−0.44 GeV replaced by
the derived seven-kink full-winding threshold Λ_GTE = 7·m_kink ≈ 2.0 GeV
(tree (8/7)m_τ = 2030.70 ± 0.14 MeV, CatAD; pole 7M^Q = 1.970 ± 0.146 GeV, CatA;
envelope 1.96 ± 0.15 GeV, band < 10%). The "kink–antikink creation threshold"
description corrected to the seven-kink mechanism (kink–antikink pairs are
winding-neutral meson-sector fluctuations at 2M ≈ 0.58 GeV, inside the EFT).
P28 reports the value; the derivation, multiplier mechanism, and machine-certified
arithmetic core live in P39 (cited). Claim-strength taxonomy box extended with the
CatA tier.

---

## 2026-06-11 — Direct-Interpolation Lift forward note (CUP-4 as certified binary anchor)

New remark `rem:triangle_lift` in §Orbit–Universality Structural Connection: CUP-4 is
the certified binary anchor of the lift chain — the orbit's total-parity constraints on
the Z₅ family ring plus vacuum transparency (MDL-equivalent among orbit satisfiers)
force exactly one multilinear GF(7) rule in the full 7⁸ class, the GTE polynomial
p(L,C,R) = C+R−CR−LCR, with Rule 110 as its binary restriction (Lean, zero sorry:
`ugp_orbit_interpolation_lift`, `gte_orbit_parity_provenance`,
`interpolation_lift_binary_corollary`, `rule110_lift_sparsity_floor`,
`gf7_rule110_sparsity_floor`, `orbit_chirality_census`; ugp-lean). The ordering census
(survivor union over all 120 family orderings = the chiral pair {Rule 110, Rule 124},
reflection bijection) grounds the sublayer-consistency selection of Rule 110 over
Rule 124; cross-refs added at the §Open Problems sublayer-consistency item and the
Wolfram-comparison discussion. No existing P28 claim changes; full development in
P49/P48 (cited).
