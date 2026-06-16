# REPRODUCE.md — P33: Deeper Consequences of Arithmetic Universality

## Overview

This document provides step-by-step instructions for reproducing all computational
and Lean results in the paper "Deeper Consequences of Arithmetic Universality in
the Standard Model."

---

## Lean Certification (CatAL results)

All CatAL results are machine-certified in the `ugp-lean` repository
(to be graduated to `ugp-lean` before publication).

### Build all relevant Lean modules

```bash
cd /path/to/ugp-lean
lake build UgpLean.Universality.EWBosonStructure
lake build UgpLean.Universality.Z7ChargeConjugation
lake build UgpLean.Universality.SMOrbitCausalIsolation
lake build UgpLean.Universality.GoEStabilityHierarchy
lake build UgpLean.Universality.CasimirMasslessEther
lake build UgpLean.Universality.GUTStructure
```

Expected: all build successfully, zero `sorry`, after Mathlib4 cache is populated.

### Key theorems by section

| Section | Theorem | Module |
|---------|---------|--------|
| §2 | `ew_c_staircase`, `ew_c_arithmetic_progression` | `EWBosonStructure.lean` |
| §2 | `fmdl_nonzero_count_14`, `fmdl_count_eq_chiggs_plus_one` | `GUTStructure.lean §7` |
| §2 | `u_photon_u_to_W_vertex` | `GUTStructure.lean` / commit `ddb6a84` |
| §3 | `fmdl_matter_cp_violation`, `fmdl_conj_pair_asymmetry_unique` | `Z7ChargeConjugation.lean` |
| §3 | `fmdl_mdl_uniqueness`, `fmdl_mdl_minimal_implies_z4_exclusion` | `GUTStructure.lean` |
| §4 | `sm_orbit_complete_causal_isolation` (6-part) | `SMOrbitCausalIsolation.lean` |
| §4 | `sm_orbit_unique_gtp3`, `fmdl_max_gtp_length_is_3` | `GoEStabilityHierarchy.lean` |
| §4 | `orbit_sum_trajectory_invariant` | `SMOrbitCausalIsolation.lean` |
| §4 | `vacuum_selects_rule110_over_rule111` | `GUTStructure.lean §3` / commit `c602e80` |
| §5 | `fmdl_unique_uniform_fixed_point`, `photon_is_ca_ether` | `CasimirMasslessEther.lean` |
| §5 | `fmdl_massless_criterion`, `ether_z7_sum_mod7` | `CasimirMasslessEther.lean` / commit `ddb6a84` |
| §7 | `ca_w_plus_is_emission_not_absorption`, `p22_absorption_vertices_are_transparent` | `Z7ChargeConjugation.lean §5` |
| §7 | `sm_charged_current_vertex`, `sm_w_minus_absence`, `sm_cp_vertex_asymmetry` | `Z7ChargeConjugation.lean §5` |

---

## Python Computations (CatA results)

All scripts graduated to `papers/33_deeper_consequences/scripts/` (2026-05-20):

```bash
cd papers/33_deeper_consequences/scripts

python3 casimir_anti_enhancement.py    # §6 Casimir: r_D/r_P ≈ 1.063 (anti-enhancement)
python3 ca_vertex_table.py              # §7 complete 14-neighborhood f_MDL catalog
python3 photon_vacuum_casimir_analysis.py  # §5 photon fixed point; massless sectors
python3 mdl_cp_uniqueness.py            # §3 MDL = CP asymmetry (10k-sample MC)
python3 fmdl3d_chirality.py             # §3 chirality: 14/343 P-violating triples
python3 z7_vertex_catalog.py    # §7.5 full SM Z₇ vertex catalog
python3 w_boson_self_energy.py    # §7 W self-energy Π_W(q²)
python3 leptoquark_su5_windings.py           # §7.5 SU(5) leptoquark Z₇ windings
python3 leptoquark_vertex_catalog.py  # §7.5 20 physical leptoquark processes
python3 pmns_cp_phase.py             # PMNS CP-phase NLO correction
python3 pmns_z5_correction.py        # PMNS Z₅ NLO θ₁₂ correction
python3 cp_observables.py   # §3 CP: sin(2β)=0.6939 (-0.30σ); ε_K=2.165e-3
python3 epsilon_k_tension.py  # §3 ε_K root-cause: Rb shortfall; ≤1σ with B̂_K
python3 decay_rates_from_gte.py  # §Tree-level lepton decay rates: Γ_μ +12.2%, Γ_τ +12.5%
```

### Casimir (§6)

Expected: λ₁ = 6.764 (Dirichlet BC); mode ratio r_D/r_P ≈ 1.063; L = 3–20.

Frozen output: `data/casimir_anti_enhancement_results.json`

### Photon vacuum (§5)

Expected: unique fixed point Z₇ = 0; massless sector k ∈ {0, 1}; ether Z₇ sum = 1.

Frozen output: `data/photon_vacuum_casimir_results.json`

### W self-energy (§7)

Expected: Γ = σ_z uniquely forced; Π_W(q²) non-trivial; M_W/M_Z = cos θ_W ratio.

Frozen output: `data/w_boson_self_energy_results.json`

### Chirality (§3.5)

Expected: 14/343 = 4.1% P-violating triples. Frozen output: `data/fmdl3d_chirality_results.json`

### Z₇ Leptoquark Vertex Catalog (§7.5)

Expected: 95 doubly-conserving; 20 physical; X-channel 4, X̄ 3, Y 7, Ȳ 6.
All four proton decay modes Z₇-conserving.

---

## Known Results (Reference Values)

| Result | Value | Status |
|--------|-------|--------|
| EW c-staircase | c ∈ {11, 12, 13} for W⁺, Z, H⁰ | CatAL |
| f_MDL active neighborhoods | 14 = c_H + 1 = 13 + 1 | CatAL |
| Palindrome decomposition | 3 (palindromic) + 10 (non-palindromic) + 1 (W⁺ vertex) | CatAL |
| GTP-3 count | Exactly 5 (cyclic rotations of gen₁) | CatAL |
| Maximum GTP length | 3 (no GTP-4 exists) | CatAL |
| Causal isolation | 6-part master theorem, all parts native_decide | CatAL |
| Photon fixed point | Unique: f_MDL(k,k,k) = k iff k = 0 | CatAL |
| Ether Z₇ winding | 1 (neutrino sector) | CatAL |
| Casimir enhancement | +6.3% (r_D/r_P ≈ 1.063) | CatA |
| Chirality | 14/343 P-violating triples | CatA |

---

## Graduation Status

### Python ✅ (2026-05-20 — all 11 scripts in `scripts/`)
### JSON artifacts ✅ (`data/` — 4 frozen outputs)

### Lean ⏳ (`ugp-lean` → `ugp-lean`)

`EWBosonStructure`, `Z7ChargeConjugation`, `SMOrbitCausalIsolation`, `GoEStabilityHierarchy`, `CasimirMasslessEther`, `GUTStructure` §§3,7,17,27,29,36,63,70,79,80,81, `DimensionalSliceUniqueness`, `ChiralPairVA`.

After Lean graduation: fill pending `---` commit entries in Lean table; update repo label from `ugp-lean` to `ugp-lean`.

### Planned
`qlc_correction.py` — QLC note §7.5; pending QLC derivation for higher-generation mixing.

---

## Paper pass update — 2026-05-24

All rank-prefixed scripts renamed to role-based names. Paper additions: CP observables Table (tab:cp_observables); decay rate derivation sketch (§Tree-Level Lepton Decay Rates).

| Old name | New name |
|----------|----------|
| `rank283_cpo_cp_observables.py` | `cp_observables.py` |
| `rank284_ekt_epsilon_k_tension.py` | `epsilon_k_tension.py` |
| `rank43_dqr_decay_rates_from_gte.py` | `decay_rates_from_gte.py` | 2026-05-24 |
| `rank140_z7_vertex_catalog.py` | `z7_vertex_catalog.py` |
| `rank157_dyson_self_energy.py` | `w_boson_self_energy.py` |
| `rank196_leptoquark.py` | `leptoquark_su5_windings.py` |
| `rank199_leptoquark_vertices.py` | `leptoquark_vertex_catalog.py` |
| `rank202_cp_phase.py` | `pmns_cp_phase.py` |
| `rank208_z5_correction.py` | `pmns_z5_correction.py` |
| `ranks_46_50_casimir_items.py` | `casimir_anti_enhancement.py` |
