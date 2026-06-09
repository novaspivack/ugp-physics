# REPRODUCE — P36 Emergent Gravity from Rule 110

## Overview

This file describes how to reproduce the numerical results of P36.

---

## Prerequisites

- Python 3.9+ with numpy, scipy (for numerical computations)
- LaTeX distribution (for PDF compilation)
- Lean 4 with Mathlib4 (for Lean certificate verification)

---

## Reproducing Result 2: Gorard Chain (§3)

**Script:** `canonical_run/rule110_ricci_scaling.py`

```bash
cd papers/36_emergent_gravity_cmca/canonical_run
python3 rule110_ricci_scaling.py
```

**Expected output:**
- L=500, T=100: κ_EE = 0.0000000000, κ_SD ≈ +0.780, κ_XD ≈ −0.924
- L=1000, T=100: κ_EE = 0.0000000000, κ_SD ≈ +0.775, κ_XD ≈ −0.910
- Global κ = 0.00000000 at both tape sizes

**Key parameters:**
- Ether: `11111000100110` (period 14, W_vac = 8/14)
- ε = 0.1 (Wasserstein regularization)
- seed = 7
- N_perturb = L/18 (proportional to tape size)

---

## Reproducing Result 3: T_μν Matter Coupling (§4)

**Script:** `canonical_run/gravity_tmunu.py`

```bash
cd papers/36_emergent_gravity_cmca/canonical_run
python3 gravity_tmunu.py
```

**Expected output (primary test: L=280, T=150, N_PERTURB=15, seed=7):**
- κ_baseline = 0.000000
- slope = +4.8409
- intercept = −0.3212
- R² = 0.2014
- p-value = 1.37 × 10⁻¹⁴⁸

**Expected output (secondary test: L=560, T=100, N_PERTURB=30, seed=42):**
- slope = +4.1727
- R² = 0.1787
- p-value = 3.74 × 10⁻¹⁷³

---

## Lean Certificate: Matter Step κ_SD > 0 (§3)

**Theorem:** `gorard_matter_step_kappa_positive` (GUTStructure §74, `ugp-lean` → graduate to `ugp-lean`)

Machine-certifies κ_SD > 0 for SM generation states (arithmetic proxy, zero sorry).

```bash
cd ugp-lean
lake build UgpLean.Universality.GUTStructure
# Expected: zero errors, zero sorry; gorard_matter_step_kappa_positive in §74
```

| Lean theorem | Section | Content |
|---|---|---|
| `gorard_matter_step_kappa_positive` | GUTStructure §74 | κ_SD > 0 for non-vacuum Rule-110 neighborhoods (matter step, arithmetic proxy) |

**Commit:** `74e48b7` (ugp-lean)

---

## Reproducing Result 1: D = 4 Lean Certificate (§2)

**File:** `ugp-lean/UgpLean/Universality/GUTStructure.lean` §54 (graduate to `ugp-lean`)

```bash
cd ugp-lean
lake build
# Expected: 3295/3295 jobs, zero errors, zero sorry
```

**Theorems to verify (all in §54 SpacetimeDimension section):**
- `fmdl_spatial_dimension := 3`
- `ca_temporal_dimension := 1`
- `gte_spacetime_dimension`
- `fmdl_spatial_dim_eq_ngen`
- `gte_dimension_as_ngen_plus_one`
- `gte_dimension_summary`

---

## Compiling the PDF

```bash
cd papers/36_emergent_gravity_cmca
pdflatex emergent_gravity_paper.tex
bibtex emergent_gravity_paper
pdflatex emergent_gravity_paper.tex
pdflatex emergent_gravity_paper.tex
```

---

## Reproducing Result 5: Spectral Dimension of Rule 110 Causal Graph (§2 Remark)

**Script:** `scripts/spectral_dimension_causal_graph.py`

```bash
cd papers/36_emergent_gravity_cmca/scripts/
python3 spectral_dimension_causal_graph.py
```

**Expected output (primary: ether-IC, undirected graph):**
- d_s (large-scale avg, t=30--70): ≈ 2.0--2.5

**Key parameters:**
- L = 200 (tape length), T = 200 (timesteps)
- 300 random walks × 80 start nodes (bulk only)
- Seed: 42 (numpy and random)

**Interpretation:**
The 1D Rule 110 causal graph has spectral dimension d_s ≈ 2, consistent
with the topological dimension of a 1D×T grid.
The D = 4 argument in §2 is an arithmetic argument from the f_MDL orbit
structure (3 spatial + 1 temporal directions), not a spectral-geometric
property of the causal graph.

---

## Reproducing Result 6: Spectral Dimension of 3D f_MDL Causal Graph (§6 Proposition)

**Script:** `scripts/spectral_dimension_3d_fmdl.py`

```bash
cd papers/36_emergent_gravity_cmca/scripts/
python3 spectral_dimension_3d_fmdl.py
```

**Expected output:**
- 3D f_MDL causal graph: d_s = 4.153 ± 0.05 (large-scale avg, t=30–70)
- 1D chiral pair (R110+R124): d_s ≈ 2.2 (layers causally decoupled, unchanged from single layer)

**Key parameters:**
- L = 8 (spatial lattice, 3D), T = 20 (timesteps)
- 150 random walks × 15 start nodes
- Seed: 42 (numpy and random)

**Interpretation:**
Finite-L measurement d_s ≈ 4.15 is consistent with machine-certified d_s = 4
in the thermodynamic limit (`causal_graph_spectral_dim_thermodynamic_limit`,
`UgpLean/Spacetime/Spectral/ThermodynamicLimit.lean`, commit `c285401`).
The overshoot is expected O(1/L) finite-size correction.

**Lean verification:**
```bash
cd ugp-lean
lake build UgpLean.Spacetime.Spectral.ThermodynamicLimit
lake build UgpLean.Spacetime.CausalGraph
lake build UgpLean.Spacetime.ChiralPairDecoupling
```

---

## Lean Certification: Spacetime Modules

| Module | Commit | Key theorems |
|--------|--------|--------------|
| `Spacetime/CausalGraph.lean` | `9d92c46` | `causal_graph_rule_independent` |
| `Spacetime/Spectral/ThermodynamicLimit.lean` | `c285401` | `causal_graph_spectral_dim_thermodynamic_limit` |
| `Spacetime/Spectral/DegreeNormalized.lean` | `c285401` | degree-normalized walk definitions |
| `Spacetime/Spectral/SpectralDimensionFromAsymptotic.lean` | `c285401` | real-analysis bridge (0 sorry) |
| `Spacetime/Spectral/HeatKernelLaplace.lean` | `c285401` | diffusive asymptotic (1 documented helper sorry) |
| `Spacetime/ChiralPairDecoupling.lean` | — | chiral pair causal isolation |
| `Spacetime/CausalInvariance.lean` | — | `minkowski_causal_isomorphism`, surjection theorems |
| `Spacetime/ChiralGliderDynamics.lean` | — | dynamics→admissibility bridge |
| `Spacetime/LiftingTheorem.lean` | `89cbef3` | `algebraic_lifting_theorem` |
| `Spacetime/GeodesicTheorem.lean` | `544df1b` | `gte_equivalence_principle`; `d2_orbit_closed_under_step`; `d2_geodesic_step`; `d2_orbit_closed_iter`; `causal_sequence_exists`; `geodesic_preferred_direction` |
| `Spacetime/CentroidMeasure.lean` | `544df1b` | `beableCentroid`; `centroid_well_defined`; `beableCentroid_point` |
| `Spacetime/ColorConfinement.lean` | `011f65d` | `no_psc_admissible_single_quark` |
| `Spacetime/MassGap.lean` | `907ed77` / `f96977a` | `gte_mass_gap`; `gte_mass_formula_physical` (Δ ≥ 1.8 MeV) |
| `QFT/GaugedMassGap.lean` | — | `qft_gauged_mass_gap_unconditional`, `confined_massive_color_singlet` |
| `Spacetime/DWeightSRFormula.lean` | `74f2294`, `28dce40f` | `dmdl_qec_sr_bundle`; `dmdl_dweight_sr_formula`; `dmdl_proper_time_ratio`; `dmdl_dweight_positive` — [D]-weighted SR (zero sorry) |
| `Spacetime/SpatiallyExtendedLifting.lean` | `9078a1b` | `causal_path_exists` (theorem, forward-causal pairs); `meson_bound_state_exists`; `baryon_bound_state_exists` |

---

## Reproducing Result 9: Mass Gap Lattice Confirmation (§Color Confinement)

**Script:** `scripts/mass_gap_smeared_gevp.py`

```bash
cd papers/36_emergent_gravity_cmca/scripts
python3 mass_gap_smeared_gevp.py
```

**Expected output:**
- Gap $= 15.68 \pm 2.85$ sim units at $\beta = 0.45$, GEVP with APE smearing
- ROBUST 5/5 criteria: commit `5450ecf0`
- $\beta$-scaling across $\beta \in \{0.35, 0.40, 0.45, 0.50\}$: commit `039483ee`

**Lean verification:**
```bash
cd ugp-lean
lake build UgpLean.QFT.GaugedMassGap
lake build UgpLean.Spacetime.MassGap
lake build UgpLean.Spacetime.ColorConfinement
```

---

## Reproducing Result: Dynamical Causal Graph (64-DCG, negative)

Three scripts test τ_c-weighted AFCA outer Rule~110 prescriptions. All rounds returned NEGATIVE (closed CatD).

| Script | Round | Key result |
|--------|-------|------------|
| `scripts/rank64_dcg_dynamical_causal_graph.py` | R1 (M=7, fresh-reinit) | Binary τ_c; no valid ε window |
| `scripts/rank64_dcg_round2_m49.py` | R2 (M=49, fresh-reinit) | Inverted τ_c gradient (ratio 0.903) |
| `scripts/rank64_dcg_round3_noreinit.py` | R3 (M=7, no-reinit+injection) | τ_c ratio 1.041 (dead-zone) |

```bash
cd papers/36_emergent_gravity_cmca/scripts
python3 rank64_dcg_dynamical_causal_graph.py
python3 rank64_dcg_round2_m49.py
python3 rank64_dcg_round3_noreinit.py
```

Artifacts: `papers/36_emergent_gravity_cmca/data/rank64_dcg_*_results.json`

---

## Reproducing Result 7: Particle Size Bounds (PSB)

**Script:** `scripts/particle_size_bounds.py`

```bash
cd papers/36_emergent_gravity_cmca/scripts/
python3 particle_size_bounds.py
```

**Expected output (key values):**
- Z₇^5 information-theoretic minimum: 15 cells (5 × log₂(7) = 14.04 bits → ⌈14.04⌉)
- Electron Compton radius: 2.389 × 10²² Planck cells
- Top quark effective size: 7.044 × 10¹⁶ Planck cells (Compton-limited)
- W boson: 1.520 × 10¹⁷ cells; Z boson: 1.339 × 10¹⁷ cells; Higgs: 9.769 × 10¹⁶ cells
- All stable SM particles: Compton-limited (no causal upper bound)
- All unstable SM particles: Compton-limited (c×τ/l_P exceeds λ_C for all)

**Key parameters:**
- Planck length: l_P = 1.6162 × 10⁻³⁵ m
- Particles: 13 SM particles (fermion generations + proton + W, Z, Higgs)
- Practical thermal floor: 100 cells

---

## Reproducing Result 8: First Two-Particle Dynamics (MPD, EPIC_072)

**Script:** `scripts/two_particle_dynamics.py`

```bash
cd papers/36_emergent_gravity_cmca/scripts/
python3 two_particle_dynamics.py
```

**Expected output (key values):**
- t=0: two gen₁ at positions 5 and 14, Z₇_total=1
- t=5: patterns spread to 14 non-vacuum rings, all "other", Z₇_total=0
- t=10: all 20 rings non-vacuum, all "other", Z₇_total=0
- t=20: gen₂ pattern [2,5,2,0,2] appears transiently at position 1
- Z₇ winding not conserved under boundary coupling (fluctuates 0,1,4,5)
- No geometric collision within T=30 steps (particles decohere before meeting)

**Key parameters:**
- N=20 ring positions, T=30 timesteps
- Initial gen₁ = [1,5,2,2,1] at positions 5 and 14
- f_MDL rule: fmdl(l,c,r) = (l + 2c + r) mod 7
- Coupling: boundary cell exchange between adjacent rings

**Interpretation:**
This is the first multi-particle dynamics simulation in GTE. The boundary coupling
model is too aggressive (violates Z₇ conservation, immediately destroys ring identity).
The transient gen₂ appearance at t=20 is the first generation-changing event observed
in GTE multi-particle dynamics. A Z₇-conserving coupling model is needed for Round 2.

---

## Notes

- The MDL–Lovelock correspondence (§5) is a theoretical result with no
  numerical script; it is fully described in the paper.
- The continuum limit (open problem, §6) has no reproducing script by
  definition (the limit is not yet proved).
- Results 7 and 8 are from EPIC_072 exploratory work and establish computational
  methodology for particle size bounds and multi-particle dynamics.

---

---

## Reproducing SR / AFCA results (graduated 2026-05-24)

```bash
cd papers/36_emergent_gravity_cmca/scripts
python3 sr_time_dilation_round19.py      # 3-SRT definitive SR (Round 19)
python3 true_afca_causal_invariance.py # 31-ACS true AFCA τ_c ratio
python3 width_scaling_sr.py              # 47-WDS M-independent SR floor
python3 geodesic_effort_computation.py   # 48–50 geodesic / effort / equivalence
python3 nested_lattice_depth_scaling.py # 51-NLD N=2 optimal nesting
python3 sr_convergence_volume.py        # 52-SCV systematic SR floor
python3 klein_gordon_sr_exact.py        # 67-KGS exact SR (<0.1% mean error)
python3 z7_kg_sr_preservation.py        # 68-KGGTE Z₇-KG preserves SR
```

Pass criteria: Round 19 SR error <15% at canonical glider velocity; true AFCA 6.4% floor;
Klein–Gordon substrate mean SR error <0.1%.

Results JSON co-located in `scripts/`.

---

## Graduation status

### Python ✅ (2026-05-24)

| Script | Location |
|--------|----------|
| `rule110_ricci_scaling.py` | `canonical_run/` ✅ |
| `gravity_tmunu.py` | `canonical_run/` ✅ |
| `spectral_dimension_causal_graph.py` | `scripts/` ✅ |
| `spectral_dimension_3d_fmdl.py` | `scripts/` ✅ |
| `particle_size_bounds.py` | `scripts/` ✅ |
| `two_particle_dynamics.py` | `scripts/` ✅ |
| `mass_gap_smeared_gevp.py` | `scripts/` ✅ |
| `sr_time_dilation_round19.py` | `scripts/` ✅ |
| `true_afca_causal_invariance.py` | `scripts/` ✅ |
| `width_scaling_sr.py` | `scripts/` ✅ |
| `geodesic_effort_computation.py` | `scripts/` ✅ |
| `nested_lattice_depth_scaling.py` | `scripts/` ✅ |
| `sr_convergence_volume.py` | `scripts/` ✅ |
| `klein_gordon_sr_exact.py` | `scripts/` ✅ |
| `z7_kg_sr_preservation.py` | `scripts/` ✅ |

### JSON artifacts ✅

| File | Location |
|------|----------|
| `gravity_tmunu_results.json` | `data/` ✅ |

### Lean ⏳ (`ugp-lean`)

| Theorem | Section / module |
|---------|------------------|
| `gorard_matter_step_kappa_positive` | GUTStructure §74; commit `74e48b7` |
| `vacuum_ollivier_ricci_flatness`, `gorard_einstein_equation_discrete` | GUTStructure §32 |
| `gte_spacetime_dimension`, `fmdl_spatial_dimension` | GUTStructure §54 |
| `causal_graph_spectral_dim_thermodynamic_limit` | Spectral/ThermodynamicLimit.lean |
| `causal_graph_rule_independent` | CausalGraph.lean |
| `minkowski_causal_isomorphism` | CausalInvariance.lean |
| `gte_mass_gap`, `no_psc_admissible_single_quark` | MassGap / ColorConfinement |
| `qft_gauged_mass_gap_unconditional` | QFT/GaugedMassGap.lean |
| `gte_equivalence_principle` | GeodesicTheorem.lean |

Refresh commit pins after canonical graduation.

---

Refresh commit pins after canonical graduation.

---

## EPIC_073 Lorentz / Poisson scripts (graduated 2026-05-25)

```bash
cd papers/36_emergent_gravity_cmca/scripts
python3 epic073_rank070_109_poisson_causal_set.py     # 070-109: Poisson skip negative (CatA)
python3 planck_scale_lorentz_prediction.py            # 070-108: δ_LV(E) unified power law
python3 tmunu_lorentz_covariance_check.py             # 073-LOR2: T_μν Lorentz covariance
python3 continuum_limit_lorentz_bridge.py             # 073-LOR4: ε₀(M) → 0 as M → ∞
python3 epic073_lor1_kg_dispersion_lorentz.py        # 073-LOR1: KG dispersion exact LI
```

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `epic073_rank070_109_poisson_causal_set.py` | 070-109 | Boost CV increases with ρ<1; C₂ destroyed; negative |
| `planck_scale_lorentz_prediction.py` | 070-108 | δ_LV ~ (E/E_P)²; GRB crossover ~1.5×10¹⁷ eV |
| `tmunu_lorentz_covariance_check.py` | 073-LOR2 | T^{μν} Lorentz-covariant; kink T_{00} → 290.10 MeV |
| `continuum_limit_lorentz_bridge.py` | 073-LOR4 | ε₀(M)=π²/(3M²); n_fit≈2 |
| `epic073_lor1_kg_dispersion_lorentz.py` | 073-LOR1 | ω²=k²+m² exact Lorentz invariance |

Also canonical in `papers/41_two_layer_ca/scripts/` for two-track Lorentz cross-ref.

*REPRODUCE.md — P36 — EPIC_073 pass 2026-05-25*
