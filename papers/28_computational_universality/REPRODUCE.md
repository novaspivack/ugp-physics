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
python3 t_epic067_r2_corrected_survey.py
```

Expected: orbit-satisfying rules = [110, 111]. Rule 110 is vacuum-transparent. Runtime: ~3s.

---

## Step 5: Run perturbed orbit test

```bash
python3 t_epic067_r3_perturbed_orbits.py
```

Expected: 8/10 perturbations yield no rule; 2/10 yield simple Class 1/3 rules;
zero Class 4 rules from any perturbed orbit. Runtime: <1s.

---

## Step 6: Run analytical orbit derivation

```bash
python3 t_epic067_r4_analytical.py
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

*P28 REPRODUCE.md — 2026-05-17*
