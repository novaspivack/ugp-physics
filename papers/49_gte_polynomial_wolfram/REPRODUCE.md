# Reproduction Instructions — P49: MDL Selects the Wolfram Rule

This document describes how to reproduce every figure, computation, and
Lean-certification result in the paper.

---

## 1. Overview

The paper studies the GTE polynomial p(L,C,R) = C+R−CR−LCR (mod 7) as a
standalone k=7 Wolfram cellular automaton. The scripts in `scripts/` generate
all figures and verify key numerical claims. The Lean modules in `ugp-lean`
certify the central algebraic theorems.

---

## Code Navigation

### Which file to use

**Use the Python scripts for:** all figure generation, spacetime diagrams, invariant subset classification, polynomial analysis, and large-scale glider/orbit scans. No Wolfram Engine required for Python scripts.

**Use `wolfram_model_causal_graph.wl` for:** the §5 WolframModel causal graph figure and §7 orbit ring diagram (alternative to `gen_orbit_ring_visualization.py`).

**Use `three_tape_wolframmodel_v2.wl` for:** the three-tape DPP causal structure demonstration (§8 figures); DPP synchronization via GlobalSpacelike.

**Do not use `three_tape_wolfram_model.wl` for new work** — it is a historical first attempt with an integer node aliasing bug; superseded by v2.

### Script roles (P49)

| Script | Role |
|--------|------|
| `wolfram_model_causal_graph.wl` | Single-tape GEN orbit causal graph (§5) + orbit ring diagram (§7) |
| `three_tape_wolframmodel_v2.wl` | Three-tape orbit causal graph with DPP synchronization (§8) |
| `three_tape_wolfram_model.wl` | Historical v1 (superseded; integer node aliasing bug) |
| `invariant_subset_classifier.py` | Exhaustive invariant subset classification (Theorem 4.2) |
| `spacetime_diagram_generator.py` | Z₇ spacetime diagrams with perturbation (Fig 1) |
| `ppoly_fmdl_contrast.py` | f_MDL vs p_poly contrast figures (Fig 2) |
| `gen_orbit_ring_visualization.py` | Orbit ring diagram via matplotlib (Fig 3; no Wolfram needed) |
| `three_tape_dpp_visualization.py` | Three-tape DPP architecture figures (Fig 5) |
| `bulk_causal_graph.py` | Bulk causal graph with cross-tape edges (Fig 6) |
| `z7_sector_dynamics.py` | Z₇ sector color comparison and scattering (Fig 7) |
| `glider_search_taichi.py` | Large-scale glider search (requires Taichi 1.7.3) |
| `orbit_visitation_rate.py` | SM orbit visitation rate (requires Taichi 1.7.3) |

### Algebraic and dynamical analysis scripts (P49 §4, §6)

Each script is self-contained (numpy/sympy only), includes a wall-clock
timeout, and writes a results JSON of the same base name alongside itself.

| Script | Verifies | Paper anchor |
|--------|----------|--------------|
| `golden_quadratic_unification.py` | Diagonal factorization p(x,x,x)−x = −x(x²+x−1); duality triage | §4 Golden-Quadratic Duality |
| `golden_quadratic_all_q_classification.py` | All-q dichotomy + singleton taxonomy, 1229 primes < 10⁴, 0 mismatches | All-q Dichotomy Theorem |
| `golden_quadratic_invariant_subsets_scan.py` | Exhaustive invariant-subset lattices q ≤ 23 (q = 29 closure-partial) | Golden-Fiber Classification |
| `golden_quadratic_padic_hensel.py` | Roots of m mod q^k, k ≤ 10: inert/split/ramified verdicts | 7-adic floor robustness |
| `golden_quadratic_gf49_frobenius_pisano.py` | GF(49) golden roots, Frobenius swap, Pisano order 16 | §4 Golden-Quadratic Duality |
| `golden_quadratic_monodromy_charpoly_exact.py` | Exact integer monodromy charpolys + 20-rule null battery (no golden factor) | Monodromy null remark |
| `eisenstein_f21_residue_field_isomorphism.py` | F₂₁ ≅ (ℤ[ω]/(3+ω))⁺ ⋊ μ₃: 21 checks + inert/ramified controls | Residue-Field Model Theorem |
| `eisenstein_norm_gte_constants.py` | Pre-registered Φ₆/Eisenstein-norm scan of 20 GTE constants | Φ₆ ladder |
| `eisenstein_variety_point_count_prime_powers.py` | Φ₆(q) counts on 23 prime powers; strata; torus orbit decomposition | Motivic identity + torus action |
| `phi6_ladder_identities_and_nulls.py` | Identity web I1–I4 + rival-form/wrong-target null batteries | Φ₆ ladder remark |
| `artin_mazur_zeta_gte_poly.py` | Periodic-point counts and cycle spectra T_n, n = 3..7 | §6 Dynamical zeta |
| `gte_poly_glider_cycle_structure.py` | σ-equivariant glider decomposition of the n = 7 cycles | §6 Dynamical zeta |
| `gte_zeta_moebius_fixed_point_theorem.py` | Möbius orbits on P¹(GF(q)); de Bruijn certificate; general-q scan q < 200 | Vacuum Uniqueness Theorem |
| `gte_zeta_drift_scaling.py` | Drift-3/7 mechanism tests; ether tile occupancy; binarity profiles | Drift-3/7 homonym remark |
| `gte_zeta_period475_linear_structure.py` | σ = T¹⁹⁰, T⁹⁵ = σ³; minimal polynomial (x⁴⁷⁵−1)/(x−1); zero mean | Attractor Factorization |
| `gte_zeta_torus_entropy.py` | Spacetime-torus transfer operators; zero-torus-entropy result | §6 Dynamical zeta |
| `cycle_spectrum_null_battery.py` | Null battery: 30 random + 10 structured GF(7) rules (~9 s) | §6 Dynamical zeta |
| `nineteen_factor_crt_tower_structure.py` | CRT split Z₂₅×Z₁₉; induced 25-ring CA; twist orders; gauge periods | Attractor Factorization |
| `nineteen_factor_linearization_no_go.py` | charpoly(DF) = x³(x−2)² at all 475 points; eigenvalue orders {0,3} | Linearization Dichotomy |
| `nineteen_factor_generalization_battery.py` | Pre-registered cross-field value-law battery (0/4 value laws) | Honest scope of the value 19 |
| `nineteen_factor_null_d_census_extension.py` | Extended 24-rule clock census (d = 19 at generic rate) | Honest scope of the value 19 |
| `triangle_lift_theorem.py` | Orbit-parity provenance; dual-method 7⁸ lift census (orbit-only 7, orbit+VT 1 = p); flattening floor; field-generality sweep | Direct-Interpolation Lift |
| `triangle_residual_tests.py` | Identity-orbit multilinear inconsistency + degree caps; mod-3/5 projection nulls; 120-ordering census ({110, 124}); δ/q_min sweep; coefficient-grammar null (24 vs 48) | Lift hypotheses + Chirality Census |
| `triangle_projection_battery_regenerate.py` | Four-projection battery artifact (total/a/b/c-parity) with pinned monomial ordering; total parity → 1 solution = p | Scope-of-parity remark |
| `parity_projection_homomorphism_battery.py` | All 777 additive reductions: statuses 277/490/5/5; forced survivors + shadow closure; 12 neighbor nulls; 0/45 perturbation null | Scope-of-parity remark |
| `parity_projection_local_function_battery.py` | Exhaustive + sampled mod-m recoding classes; per-class parity controls; mod-5 impossibility | Scope-of-parity remark |
| `parity_projection_architecture_filters.py` | Displaced-vacuum / closure filters over all recorded exceptions; Rule-106 product-parity exclusion | Scope-of-parity remark |
| `parity_projection_unrestricted_vacuity.py` | Explicit lookup-forcing certificates for 76/128 vacuum-transparent elementary rules | Scope-of-parity remark |

Run any of them directly, e.g.:

```bash
cd papers/49_gte_polynomial_wolfram/scripts
python3 golden_quadratic_all_q_classification.py
# expected: "Mismatches: 0", "ALL MATCH (dichotomy + singleton corollary): True"
python3 cycle_spectrum_null_battery.py
# expected: per-feature null base rates; n5_matches_p_spectrum: 0
python3 triangle_lift_theorem.py
# expected: "(C) orbit-only multilinear survivors: 7", "orbit+VT survivors: 1",
#           unique survivor coefficients (0,0,1,1,0,0,-1,-1); runtime < 5 s
python3 parity_projection_homomorphism_battery.py
# expected: Tier-1 statuses 277/490/5/5; parity-factoring survivors forcing
#           g1 = p; 12/12 neighbor nulls fail; 0/45 perturbations force p
```

Runtimes: all triangle/parity scripts complete in under a minute except
`parity_projection_local_function_battery.py` (~15 min exhaustive + sampled
census) and `parity_projection_architecture_filters.py` (~5 min); every
script carries a wall-clock timeout.
`parity_projection_architecture_filters.py` reads the homomorphism- and
local-function-battery result JSONs from its own directory, so run (or keep)
those two artifacts first.

### Related code in other papers

| File | Paper | Description |
|------|-------|-------------|
| `papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl` | P45 | Full three-layer CMCA cell-level simulator; single-bit inner clock; SR dilation and 9 verifications |
| `papers/45_three_tape_cmca/scripts/three_tape_cmca.py` | P45 | Python three-tape CMCA (gravity, Bell, soliton); cell-level dynamics |
| `papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl` | P41 | Single-tape CMCA with M=7 inner clock; complete P41 9-claim reproducibility suite |

---

## 2. Dependencies

### 2.1 Python 3.10+

```bash
pip install numpy matplotlib networkx scipy
```

All Python scripts are self-contained and write figures to `scripts/figures/`
relative to their own location.

### 2.2 Taichi 1.7.3 (for glider search and orbit visitation scripts only)

```bash
pip install "taichi==1.7.3"
```

Taichi provides parallelised CA kernels (CPU or GPU backend). Tested on
Taichi 1.7.3 with the CPU and Metal (macOS arm64) backends. The two scripts
that require Taichi are `glider_search_taichi.py` and `orbit_visitation_rate.py`.
All other scripts work without Taichi.

**Critical constraint:** Do NOT add `from __future__ import annotations` to any
file that imports Taichi. That import defers type-annotation evaluation, which
breaks Taichi's kernel argument type inspection at import time.

Expected runtimes with Taichi (CPU backend):
- `glider_search_taichi.py` small run (L=200, T=100): ~30 s
- `glider_search_taichi.py` large run (L=10 000, T=2 000): 5–10 min
- `orbit_visitation_rate.py` (L=10 000, T=2 000): ~5 min

Both scripts include a 300-second wall-clock timeout (`TIMEOUT_SECONDS`).

### 2.3 Wolfram Engine 14.3.0 (for `.wl` scripts only)

Free download: https://www.wolfram.com/engine/

Install the SetReplace paclet (required by both `.wl` scripts):

```bash
wolframscript -code 'PacletInstall["SetReplace"]'
```

Tested versions: Wolfram Engine 14.3.0, SetReplace v0.3.196. Load via
`Needs["SetReplace\`"]` (local paclet), NOT `ResourceFunction["WolframModel"]`.

### 2.4 Lean 4 (for certification verification only)

```bash
elan install leanprover/lean4:stable
```

See §5 for module paths and build commands.

---

## 3. Script Inventory

All scripts write output to `scripts/figures/` relative to their own location.
Run from the `scripts/` directory:

```bash
cd papers/49_gte_polynomial_wolfram/scripts
```

| Script | What it produces | Paper section | Requires Taichi? |
|--------|-----------------|---------------|-----------------|
| `invariant_subset_classifier.py` | Printed table: all 127 non-empty subsets of Z₇, invariant subset classification | §4 (Theorem 4.2) | No |
| `spacetime_diagram_generator.py` | `p49_gte_spacetime_perturbed_v2.png`, `p49_gte_ether_only_v2.png` | §6 | No |
| `ppoly_fmdl_contrast.py` | `p49_gen1_fmdl_vs_ppoly.png`, `p49_ether_fmdl_vs_ppoly.png`, `p49_fmdl_vs_ppoly_table.png` | §2, §8 | No |
| `gen_orbit_ring_visualization.py` | `p49_gte_orbit_rings_v2.png` | §7 | No |
| `wolfram_model_causal_graph.wl` | `p49_gte_causal_g10.png`, `p49_gte_final_state_g10.png`, `p49_gte_orbit_rings_v2.png` (alt) | §5, §7 | No (Wolfram) |
| `z7_sector_dynamics.py` | `p49_z7_color_comparison.png`, plus glider search and scattering spacetime diagrams | §6 | No |
| `three_tape_dpp_visualization.py` | `p49_three_tape_dpp_v3.png`, `p49_three_tape_orbit_3d.png`, `p49_dpp_clock_diagram.png`, `p49_three_tape_causal_layered.png`, `p49_paper_fig2_combined.png` | §8 | No |
| `bulk_causal_graph.py` | `p49_bulk_causal_3d.png`, `p49_causal_comparison.png`, `p49_bulk_causal_cross_tape.png`, `p49_bulk_causal_slices.png` | §8 | No |
| `glider_search_taichi.py` | `p49_z7_excitation_panel.png`, `p49_z7_cone_fill.png`, per-sector excitation PNGs, `p49_z7_cone_fill_large.png` | §6 supplemental | **Yes** |
| `orbit_visitation_rate.py` | `p49_orbit_visitation_rates.png` | §6 supplemental | **Yes** |
| `three_tape_wolfram_model.wl` | Causal graph PNGs for three-tape encoding | §8 supplemental | No (Wolfram) |

---

## 4. Reproducing Each Figure

### Theorem 4.2 verification — exhaustive invariant subset classification

Verifies computationally that exactly three non-empty subsets of Z₇ are closed
under p: the vacuum singleton {0}, the binary sublayer {0,1} (= Rule 110), and
the full space Z₇.

```bash
python3 invariant_subset_classifier.py
```

Expected output: `PASS: Exactly 3 invariant subsets confirmed: {0}, {0,1}, Z₇`.
Runtime: < 1 ms. No figure produced — pure printed verification.

---

### Figure 1 — Z₇ spacetime diagrams (§6)

56-cell ether tape with a single Z₇=3 injection at center (Fig 1a) and the
unperturbed ether baseline (Fig 1b).

```bash
python3 spacetime_diagram_generator.py
```

Produces:
- `figures/p49_gte_spacetime_perturbed_v2.png` — causal cone diagram
- `figures/p49_gte_ether_only_v2.png` — unperturbed ether baseline

Runtime: ~2 s.

---

### Figure 2 — f_MDL vs p_poly contrast (§2)

Three panels: GEN₁ ring evolution under the two rules, ether + injection
response comparison, and lookup table sparsity (343-cell grid).

```bash
python3 ppoly_fmdl_contrast.py
```

Produces:
- `figures/p49_gen1_fmdl_vs_ppoly.png`
- `figures/p49_ether_fmdl_vs_ppoly.png`
- `figures/p49_fmdl_vs_ppoly_table.png`

Runtime: ~5 s.

---

### Figure 3 — GEN orbit ring diagram (§7)

Four-state orbit ring: GEN₁=[1,5,2,2,1] → GEN₂=[2,5,2,0,2] → GEN₃=[5,6,5,3,5]
→ VAC=[0,0,0,0,0] under f_MDL on a 5-cell periodic ring.

**Python version (no Wolfram Engine required):**
```bash
python3 gen_orbit_ring_visualization.py
```
Produces `figures/p49_gte_orbit_rings_v2.png`. Runtime: ~2 s.

**Wolfram version (requires Wolfram Engine + SetReplace):**
```bash
wolframscript -file wolfram_model_causal_graph.wl
```
Also produces `figures/p49_gte_orbit_rings_v2.png` (overwritten if Python
version was run first).

---

### Figure 4 — WolframModel causal graph (§5.3)

Causal graph of the ruleGTE WolframModel at 10 generations (1023 events, binary tree).
There are two independent ways to produce this figure:

**Method A — Canonical WolframScript (requires Wolfram Engine + SetReplace):**
```bash
wolframscript -file gte_rulegte_causal_graph.wl
```
Produces:
- `figures/p49_gte_causal_g10.png` — tree-layout causal graph
- `figures/p49_gte_causal_g10_wolfram_radial.png` — radial embedding
- `figures/p49_gte_rulegte_final_state.png` — final hypergraph state (2048 hyperedges)

**Method B — Python fallback (no Wolfram Engine required):**
```bash
python3 gte_wolframmodel_causal_graph.py
```
Produces:
- `figures/p49_gte_causal_g10_python.png` — Python-generated causal graph
- `figures/p49_gte_causal_g10.png` — canonical figure (same data)

**Topology analysis (§5.3 GEN₂/GEN₃ degeneracy):**
```bash
python3 gte_causal_graph_corrected.py
```
Produces:
- `figures/p49_gte_causal_topology_analysis.png` — GEN₂/GEN₃ topology diagram
- `figures/p49_gte_causal_graph_comparison.png` — deterministic vs. multiway comparison
- `figures/p49_gte_causal_g10_deterministic.png` — deterministic (linear) causal chain

**Legacy script (do not use for new figures):**
`wolfram_model_causal_graph.wl` — uses single-brace orbit rules (produces 0 events
with WolframModel v0.3 syntax; shown as deterministic linear chain only).

---

### Figure 5 — Three-tape DPP visualization suite (§8)

Five panels covering the three-tape DPP architecture: 3D orbit ring, clock
coupling diagram, causal layered graph, and combined headline figure.

```bash
python3 three_tape_dpp_visualization.py
```

Produces:
- `figures/p49_three_tape_dpp_v3.png`
- `figures/p49_three_tape_orbit_3d.png`
- `figures/p49_dpp_clock_diagram.png`
- `figures/p49_three_tape_causal_layered.png`
- `figures/p49_paper_fig2_combined.png`

Runtime: ~10 s.

---

### Figures 6a, 6b — Bulk causal graph (§8)

Combined three-tape DPP bulk causal graph with 135 within-tape and 90
cross-tape (gravitational) edges; side-by-side comparison of the coupled
bulk versus three independent causal trees.

```bash
python3 bulk_causal_graph.py
```

Produces:
- `figures/p49_bulk_causal_3d.png` — full 3D causal graph
- `figures/p49_causal_comparison.png` — coupled vs. independent comparison
- `figures/p49_bulk_causal_cross_tape.png` — cross-tape edges only
- `figures/p49_bulk_causal_slices.png` — time-slice causal structure

Runtime: ~20 s.

---

### Figures — Botanical L-system comparison (§5.4)

L-system renderings comparing the GTE causal graph structure to Apiaceae compound
umbel models. Requires only Python (no Wolfram Engine).

```bash
python3 botanical_causal_graph_analysis.py
```

Produces:
- `figures/botanical_lsystem_comparison.png` — GTE L-system vs four Apiaceae models side-by-side
- `figures/botanical_best_match.png` — side-by-side GTE vs Daucus carota best match
- `figures/botanical_metrics_comparison.png` — metric comparison table visualization

Runtime: ~5 s.

---

### Figure 7 — Z₇ sector color comparison (§6)

Five-sector side-by-side spacetime comparison (injection values Z₇=2 through 6)
into the ether background. Also runs the glider search (Experiment A) and
two-particle Z₇ winding scattering experiments (Experiment B).

```bash
python3 z7_sector_dynamics.py
```

Produces:
- `figures/p49_z7_color_comparison.png`
- Scattering spacetime diagrams (`p49_z7_scattering_*.png`)
- Glider search spacetime diagrams (`p49_z7_glider_search_v*.png`)

Runtime: ~60 s (glider search at L=200, T=500).

---

### Supplemental — Ether-excluded glider search (§6, requires Taichi)

Large-scale parallel glider search using excitation fields to eliminate ether
autocorrelation. Tests sector-dependence by pairwise Hamming fractions.

```bash
pip install "taichi==1.7.3"
python3 glider_search_taichi.py
```

Produces:
- `figures/p49_z7_excitation_panel.png` — side-by-side excitation spacetimes
- `figures/p49_z7_cone_fill.png` — cone fill fraction (small run)
- `figures/p49_z7_cone_fill_large.png` — cone fill fraction (large run, L=10 000)
- `figures/p49_z7_excitation_w*.png` — per-window excitation diagrams

Runtime: 30 s – 10 min depending on run size and backend.

---

### Supplemental — SM orbit visitation rate (§6, requires Taichi)

Measures what fraction of triples encountered during chaotic Z₇ evolution
match the 10 SM orbit neighborhoods of f_MDL.

```bash
python3 orbit_visitation_rate.py
```

Produces `figures/p49_orbit_visitation_rates.png`. Runtime: ~5 min (CPU).

---

### Supplemental — Three-tape WolframModel encoding (requires Wolfram Engine)

Encodes the three-tape GEN orbit product as a SetReplace hyperedge rewriting
system and generates the WolframModel causal graph.

```bash
wolframscript -file three_tape_wolfram_model.wl
```

---

## 5. Lean Verification

The central algebraic claims are machine-certified in `ugp-lean` (zero sorry).

Clone the repo and build individual modules:

```bash
git clone https://github.com/novaspivack/ugp-lean.git
cd ugp-lean
lake build UgpLean.Universality.Z7InvariantSubsets
lake build UgpLean.Universality.CUP3DUniqueness
lake build UgpLean.Universality.MDLDerivabilityCriterion
lake build UgpLean.Universality.PhiMDLUniversality
lake build UgpLean.Gravity.RelationalTime
lake build UgpLean.Polynomial.PolyExplorations
lake build UgpLean.Polynomial.GTECausalTree
lake build UgpLean.Polynomial.GoldenQuadratic
lake build UgpLean.Polynomial.EisensteinIdentities
lake build UgpLean.Polynomial.BiquadraticCompositum
lake build UgpLean.Polynomial.AGL17ChiralZ2
lake build UgpLean.Polynomial.DynamicalZeta
lake build UgpLean.Algebra.SRRGCABridge
lake build UgpLean.Universality.TriangleLiftTheorem
lake build UgpLean.Universality.TriangleLiftStructural
lake build UgpLean.Universality.ParityProjectionForcing
lake build UgpLean.Polynomial.SpinSevenWallSpectroscopy
lake build UgpLean.Polynomial.SpinSevenGroundSpace
```

A clean build exits 0 with zero `sorry` on all cited theorems.

Key theorems:
- `rule110_z7_poly_rep` (PhiMDLUniversality): p mod 7 restricted to {0,1}³ = Rule 110
- `p_poly_invariant_subsets_classification` (Z7InvariantSubsets): exactly 3 invariant subsets
- `nfam_qnr_explains_binary_floor` (Z7InvariantSubsets): QNR Binary Floor theorem
- `fmdl_z7_three_generation_orbit` (CUP3DUniqueness): GEN₁→GEN₂→GEN₃→VAC orbit
- `mdl_ca_rule_coding_closed` (MDLDerivabilityCriterion): T96-02 MDL + PSC uniqueness of p
- `dimensional_protocol_principle_master` (RelationalTime): DPP theorem (shared clock → 3+1D)
- `gte_diagonal_quadratic_factorization` (GoldenQuadratic): p(x,x,x) − x = −x(x²+x−1) over every commutative ring
- `master_quadratic_no_root_mod_seven_pow` (GoldenQuadratic): 7-adic floor robustness at every depth
- `master_quadratic_split_iff_qr5`, `second_floor_iff_ramified`, `gf49_golden_roots_frobenius_swap` (GoldenQuadratic): splitting law, ramification mechanism, Frobenius swap
- `f21_eisenstein_residue_model` (EisensteinIdentities): F₂₁ ≅ (ℤ[ω]/(3+ω))⁺ ⋊ μ₃
- `poly_p_torus_equivariance`, `poly_p_variety_orbit_decomposition_gf7` (EisensteinIdentities): torus action and ether-point orbit decomposition
- `phi6_identity_bundle`, `c_H_eq_phi3_ngen`, `cH_phi3_unique_at_ngen` (EisensteinIdentities): Φ₆ ladder identity web
- `biquadratic_compositum_alphabet_class`, `phi6_stability_class_lemma` (BiquadraticCompositum): alphabet-prime Artin class q ≡ 7, 13 (mod 15)
- `agl17_chiral_z2_mechanism` (AGL17ChiralZ2): AGL(1,7) full symmetry group; reflection swaps Rule 110 ↔ Rule 124
- `vacuum_unique_temporal_fixed_point_ring` (DynamicalZeta): Fix(T_n) = {vacuum} for every ring size n
- `t95_eq_sigma3_on_period475_cycle`, `period475_drift_cancelled_return_order_nineteen`, `period475_factorization` (DynamicalZeta): period-475 attractor factorization certificates
- `gte_orbit_parity_provenance`, `ugp_orbit_interpolation_lift`, `interpolation_lift_binary_corollary`, `rule110_lift_sparsity_floor`, `orbit_chirality_census` (TriangleLiftTheorem): Direct-Interpolation Lift census route, binary corollary, multilinear sparsity floor, chirality census
- `multilinear_binary_determination`, `orbit_vt_forces_interpolant`, `orbit_interpolation_lift_structural`, `gf7_rule110_sparsity_floor` (TriangleLiftStructural): structural Möbius-inversion lift route and canonical-class sparsity floor
- `parity_projection_additive_forcing`, `parity_projection_mod2_recoding_forcing` (ParityProjectionForcing): reduction-battery census counts (additive 777 forms; mod-2 recodings 16,807)
- `spin7_directed_wall_energies` (SpinSevenWallSpectroscopy): directed wall/bump tables, composite hub identity, half-integer gap exponent 3/2

---

## 6. Paper Compilation

```bash
cd papers/49_gte_polynomial_wolfram/
pdflatex gte_polynomial_wolfram.tex
bibtex gte_polynomial_wolfram
pdflatex gte_polynomial_wolfram.tex
pdflatex gte_polynomial_wolfram.tex
```

Figures are loaded from `scripts/figures/`. Ensure the Python scripts (§4)
have been run first to generate all required PNGs.
