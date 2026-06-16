# Reproducibility: Computational Universality and the Standard Model (P28)

All results in this paper are fully reproducible.

---

## Step 1: Build Lean proofs

```bash
cd /path/to/ugp-lean
lake build UgpLean.Universality.CUP4TotalParity
lake build UgpLean.Universality.CUP11ModSeven
lake build UgpLean.Universality.CUP3DUniqueness
lake build UgpLean.Universality.CUP3DPSCUnification
lake build UgpLean.Universality.CUP3DPhysicalIncompleteness
lake build UgpLean.Universality.TwoLayerConfluence
lake build UgpLean.Universality.GTECompilation
lake build UgpLean.Universality.GTEUniqueness
lake build UgpLean.Universality.GTEInfTapeEncoding
lake build UgpLean.Universality.GTEComputability
lake build UgpLean.Universality.HypothesisB
lake build UgpLean.Universality.HypothesisBCChain
lake build UgpLean.Universality.PSCUniversality
```

Expected: all build successfully, zero bare `sorry` across all modules. Total build time: <60s after Mathlib cache is populated.

Named physics bridge axioms (3 total — all documented, no bare sorry):
- `rcc_physics_ax` (PSC.RCCComplete): RCC, analytically backed by `rcc_analytical_complete`
- `rule110_simulates_computable` (GTEComputability): Cook's universality theorem (Cook 2004/2009)
- `simultaneous_dual_tape_ax` (HypothesisBCChain): dual-sector tape coherence

Key zero-sorry theorems:
- `fmdl_gen1_is_garden_of_eden` (CUP3DUniqueness): Z₇ gen₁ GoE, 7^5 states, native_decide
- `cup1_orbit_uniquely_selects_rule110` (CUP4TotalParity): orbit uniqueness, 256 rules
- `gte_compilation_theorem` (GTECompilation): GTE tile compilation, rfl
- `hypothesis_b_tape_level` (HypothesisB): dual-sector tape unification
- `hypothesis_c_psc_forces_universality` (PSCUniversality): PSC chain, cond. rcc_physics_ax

---

## Step 2: Build rule110-lean (external Cook formalization)

```bash
cd /path/to/rule110-lean
lake build
```

Expected: zero sorry across all modules (CyclicTagSystem, InfTape, Ether, GliderConfig,
CookGliderCatalog, CookGliderVerification). The `CTStoRule110` module contains two named
axioms (`cook_c2_tape_bit_ax`, `cook_cts_step_sim_ax`) documenting the remaining
Cook 2004/2008 glider collision correctness gap.

---

## Step 3: Run CUP-4 null test

```bash
cd papers/28_computational_universality/canonical_run
python3 t_null_cup4.py
```

Expected output: p_raw = 1.36% (136/10000), 10 winning orderings for Rule 110,
Z₅ ring structure confirmed. Runtime: <60s.

---

## Step 4: Run orbit survey

```bash
python3 t_orbit_survey.py
```

Expected: orbit-satisfying rules = [110, 111]. Rule 110 is vacuum-transparent. Runtime: ~3s.

---

## Step 5: Run perturbed orbit test

```bash
python3 t_perturbed_orbits.py
```

Expected: 8/10 perturbations yield no rule; 2/10 yield simple Class 1/3 rules;
zero Class 4 rules from any perturbed orbit. Runtime: <1s.

---

## Step 6: Run analytical orbit derivation

```bash
python3 t_analytical_verification.py
```

Expected: orbit path activates 7 of 8 binary neighborhoods; required outputs exactly match
Rule 110 minterms {1,2,3,5,6}; all 8 bits algebraically determined. Runtime: <1s.

---

## Step 7: Run CUP-12 analysis

```bash
python3 t_cup12_mdl_minimal.py
python3 t_cup12_cross_sector.py
```

Expected: f_MDL 18 fixed + 325 free; f_CROSS 27 fixed, 76-bit description. Runtime: <30s.

---

## Step 8: Run Z₂ sublayer consistency and c-value analysis

```bash
cd papers/28_computational_universality/canonical_run
python3 z2_sublayer_consistency.py
```

Expected: binary CA rule enumeration over all rules satisfying $f(0,0,0)=0$ and Class-4 universality; MDL one-count distribution computed; c-value formula $c_P = 7 + \mathrm{MDL}(\text{rule}_P)$ verified for EW bosons ($c_Z = 12 = 7 + 5$); Wolfram Class 4 resonance confirmed at MDL $= 5$; sublayer-consistency selection of Rule 110 over Rule 124 verified. Runtime: 99ms.

---

## Step 9: Run two-layer chiral CA (Lorentz symmetry verification)

```bash
python3 rule110_rule124_chiral_pair.py
```

Expected: two-layer CA {Rule 110 (right-mover) + Rule 124 (left-mover)}, periodic tape
L=840, T=300 steps. Results: v_R = +2/3, v_L = -2/3 exactly (deviation < 1e-6);
100% period-3 purity for both glider families; 100 full C₂ glider cycles.
Confirms Lorentz-symmetric causal structure. Runtime: <5s.

---

## Step 10: Run f_MDL predecessor counts (GoE stability hierarchy)

```bash
python3 fmdl_predecessor_counts.py
```

Expected: exhaustive search over all 7⁵ = 16,807 Z₇ states; predecessor counts:
pred(gen₁) = 0 (Garden of Eden), pred(gen₂) = 1 (unique predecessor = gen₁),
pred(gen₃) = 1 (unique predecessor = gen₂); orbital chain isolation confirmed;
result matches Lean certification in `GoEStabilityHierarchy.lean`. Runtime: <5s.

---

## Step 11: Run GTE T⁻¹ predecessor check (mass-cascade GoE)

```bash
python3 gte_predecessor_check.py
```

Expected: no GTE triple maps to G₁ = (1, 73, 823) under the GTE cascade map T;
T⁻¹ predecessor count = 0; G₁ is arithmetically primordial at the mass-cascade level.
Result matches Lean certification in `GoEHierarchy.lean`. Runtime: <1s.

---

## Step 1b: Build ugp-lean modules (until canonical Lean graduation)

CatAL results cited in Appendix A that are currently only in `ugp-lean`:

```bash
cd /path/to/ugp-lean
lake build UgpLean.Universality.OrbitPerturbationCatalog
lake build UgpLean.Universality.Z7ChargeConjugation
lake build UgpLean.Universality.GoEStabilityHierarchy
lake build UgpLean.Universality.Z5TransitivityUniqueness
lake build UgpLean.Universality.DimensionalSliceUniqueness
lake build UgpLean.Universality.GTPNeutralDiscrimination
lake build UgpLean.Universality.SMOrbitCausalIsolation
lake build UgpLean.Universality.EWBosonStructure
lake build UgpLean.Universality.GUTStructure
lake build UgpLean.Universality.CasimirMasslessEther
```

Expected: zero sorry on each module after Mathlib cache.

`NcColorArithmetic.lean` is already in canonical `ugp-lean`.

Step 8 writes `canonical_run/z2_sublayer_consistency_results.json` (same directory as script).

---

## Steps 12–27: Additional canonical_run scripts

All the following are in `canonical_run/` (graduated 2026-05-20):

```bash
cd papers/28_computational_universality/canonical_run
python3 orbit_admissible_count.py          # SM orbit neighborhood constraints
python3 z7_conservation_landscape.py       # Z₇ sum conservation sweep (239ms)
python3 gtp_chain_uniqueness.py            # GTP-n exhaustive search (132ms)
python3 gtp3_sum_trajectory.py             # GTP-3 chain + Z₇-sum trajectory
python3 fmdl_decay_depth.py               # Decay depth distribution (all 16807 states)
python3 transitivity_spectrum.py           # (p,w,t) transitivity spectrum (~0.2s)
python3 photon_vacuum_casimir_analysis.py  # CA zero-point entropy; Casimir
python3 ranks_46_50_casimir_items.py       # Masslessness criterion; virtual-photon
python3 z3_z7_color_extension.py          # Z₃×Z₇ orbit (9261 nbhds, 88ms)
python3 z2_longitudinal_extension.py      # Binary CA Z₂ / γ–Z (98ms)
python3 z7_output_distribution.py         # f_MDL output distribution; preimage counts
python3 fmdl3d_chirality.py               # P-violation 14/343; 3D parity (0.08s)
python3 gte_triple_neutral_discrimination.py  # GTE triple pairwise distinctness
python3 complex_z7_rule110.py             # Complex Z₇ embedding; bifurcation
python3 rule110_period3_glider.py          # Period-3 C₂ glider; v_R = 2/3
python3 z5_transitivity_check.py          # Z₅ transitivity uniqueness sweep (<1s)
```

```bash
cd papers/28_computational_universality/scripts
python3 ca_vertex_table.py         # 343-entry f_MDL catalog + P22 coverage
python3 z7_gauge_invariance_check.py  # Z₇ / Z₅ equivariance tests (231ms)
```

Frozen JSON outputs for scripts that write them are co-located in `canonical_run/`.

---

## Remaining graduation item (Lean only)

The modules listed in Step 1b must be graduated from `ugp-lean` → `ugp-lean`
before Zenodo deposit. Python graduation is complete as of 2026-05-20.

---

## Step 1b: Build ugp-lean Spacetime / QFT modules (physical substrate)

```bash
cd /path/to/ugp-lean
lake build UgpLean.Spacetime.LiftingTheorem
lake build UgpLean.Spacetime.SpatiallyExtendedLifting
lake build UgpLean.Spacetime.ColorConfinement
lake build UgpLean.Spacetime.MassGap
lake build UgpLean.Spacetime.AnomalyRenormalizability
lake build UgpLean.Spacetime.PhysicalExclusion
lake build UgpLean.Spacetime.ThreeGenerationCapstone
lake build UgpLean.QFT.GaugedMassGap
lake build UgpLean.Universality.AlgebraicDescentTheorem
lake build UgpLean.Universality.SylowIndexCouplingHierarchy
```

Expected: zero sorry on each module. Key theorems:
- `algebraic_lifting_theorem`, `no_fourth_generation_physical` (LiftingTheorem)
- `meson_bound_state_exists`, `baryon_bound_state_exists` (SpatiallyExtendedLifting)
- `no_psc_admissible_single_quark` (ColorConfinement)
- `qft_gauged_mass_gap_unconditional` (GaugedMassGap)
- `f21_substrate_beta_coefficient`, `f21_two_loop_beta_coefficient` (SylowIndexCouplingHierarchy)
- `gte_uniquely_predicts_three_generations` (ThreeGenerationCapstone, commit `fb7a611`)

---

## Step 28: Vertex catalog, GF(7), and decay-rate scripts

```bash
cd papers/28_computational_universality/scripts
python3 gauged_vertex_catalog.py    # 7/7 GTE vertices under Z₃ gauge; 0 spurious
python3 gf7_orbit_code_check.py     # orbit is not a GF(7) group code; {1,2,4} roots of unity
python3 fmdl_wolfram_category.py    # f_MDL Z₇ Wolfram Category IV (3/4 diagnostics)
```

Decay rates (Rank 43-DQR, also Paper 33):

```bash
cd papers/33_deeper_consequences/scripts
python3 decay_rates_from_gte.py
```

Expected: 7/7 GTE vertices under Z₃ gauge; tree-level Γ_μ +12.2%, Γ_τ +12.5% vs PDG.

Pass criteria: vertex recovery 7/7 with zero spurious; decay ordering preserved; rate errors within stated ±15% band.

---

## Step 29: F₂₁ / hadron chain scripts (graduated 2026-05-24)

```bash
cd papers/28_computational_universality/scripts
python3 f21_substrate_identification.py   # F₂₁ ≅ Σ(21) ⊂ SU(3); Casimirs
python3 asymptotic_freedom_f21.py         # b₀ = 7 one-loop
python3 beta_function_two_loop_f21.py     # b₁ = 26 two-loop
python3 f21_su3_deconstruction_flow.py    # deconstruction flow (PROVISIONAL)
python3 hadron_multiplets_gte.py          # meson/baryon multiplets
python3 jp_spin_mdl_derivation.py         # JP = 1/2 from MDL
python3 vector_meson_nonet_hyperfine.py   # vector nonet masses (~3.2% RMS)
python3 quark_masses_gte.py               # six quark masses within 7% PDG
python3 pion_decay_constant_dhn.py        # f_π = 91.35 MeV (−0.81% vs PDG)
python3 eta_mixing_angle_zero_pdg.py      # θ_P = −13.08° ± 3.74° (PDG range)
python3 chiral_condensate_nlo.py          # B₀_NLO = 2727 MeV (+2.24% vs PDG)
```

Results JSON co-located in `scripts/` (same directory as each script).

Dependencies: Python 3.9+, numpy, scipy (where used). Expected runtime: <5 min per script (wall-clock timeouts enforced).

---

Dependencies: Python 3.9+, numpy, scipy (where used). Expected runtime: <5 min per script (wall-clock timeouts enforced).

---

## Step 30: R110 self-simulation / Cook scaffold scripts (graduated 2026-05-25)

```bash
cd papers/28_computational_universality/scripts
python3 epic073_rank5_fss_r110_self_simulation.py      # 5-FSS: naive macro embedding negative partial
python3 epic073_rank5_fss_cook_phased.py               # 5-FSS-COOK-PHASED: phased CTS scaffold CatA partial
python3 epic073_rank5_fss_cook_central.py              # 5-FSS-COOK-CENTRAL: central region negative
python3 epic073_rank5_fss_cook_block_assembler.py      # 5-FSS-COOK: block assembly scaffold
```

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `epic073_rank5_fss_r110_self_simulation.py` | 5-FSS | Ether period-7 building block; naive single-tape fails |
| `epic073_rank5_fss_cook_phased.py` | 5-FSS-COOK-PHASED | Phased post-decode origin-cell readback confirmed |
| `epic073_rank5_fss_cook_central.py` | 5-FSS-COOK-CENTRAL | Central region C–G integrated; data-cone readback negative |
| `epic073_rank5_fss_cook_block_assembler.py` | 5-FSS-COOK | Block assembly scaffold |

**Paper cross-ref:** P28 §self-simulating embeddings remark; CUP-5 chain closed CatD (252-CUP5E).

---

*P28 REPRODUCE.md — 2026-05-24 (script graduation audit); EPIC_073 pass 2026-05-25*
