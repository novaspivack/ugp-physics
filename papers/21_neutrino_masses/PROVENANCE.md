# Provenance: Neutrino Mass Prediction Paper (P22)

**Paper:** *Predicting the Neutrino Mass-Squared Ratio from the Braid Atlas Topological Invariants and the QCD Colour Rank*
**Author:** Nova Spivack
**Status:** In preparation

---

## Paper Claims

| Claim | Content | Status |
|-------|---------|--------|
| Mass-squared ratio | Δm²₂₁/Δm²₃₁ = 0.02936 from b = {5,11,19} with exponent 29/9 | [E] empirical + Lean structural |
| Null test | 8/3654 integer triples hit within 1%; Braid Atlas triple is one | [E] empirical |
| Normal hierarchy | m₁ < m₂ < m₃ automatic from b₁ < b₂ < b₃ | [T] structural |
| Three decompositions of 29/9 | Topology, mirror offset δ=7, GUT reps (45-16=29) | [T] Lean-certified |
| dim(126) = 2·N_c²·δ | Cross-sector bridge | [T] Lean `dim_126_SO10_eq_two_Nc_sq_delta` |
| Dirac scale E_D = v_H/29 | Structural scale; 29 = same integer as exponent numerator | [C] structural identification |
| Σmν ∈ [40,100] meV | With M_R in natural GUT range [10^16, 5×10^16] GeV | [C] |
| FN texture (q₁,q₂)=(N_c,strand)=(3,2) | Two-flavon FN charges on ν_R reproduce b^(29/9); both charges structural in N_c | [B] structural identification, pre-committed |
| MDL-uniqueness of (N_c,strand) | Among the 4 FN solutions at N_c=3, only (3,2) is singleton-atomic | [T] Lean `fn_texture_3_2_is_unique_singleton_atomic` |

---

## Computational Artifacts

All scripts are in `papers/01_SM/canonical_run/`:

| Script | Description |
|--------|-------------|
| `comp_p01_EBF_17_neutrino_survey.py` | Six-approach survey; identifies Braid Atlas b-values {5,11,19} as optimal |
| `comp_p01_EBF_18_neutrino_126_bridge.py` | N_c-cube and 126-bridge hypotheses; discovers b^{29/9} |
| `comp_p01_EBF_19_neutrino_29_9_derivation.py` | Null test: 8/3654 triples hit within 1% |
| `comp_p01_EBF_20_neutrino_absolute_scale.py` | Absolute scale scan; M_GUT sensitivity |
| `comp_p01_EBF_21_neutrino_29_9_structural_decomp.py` | Three structural decompositions of 29/9 |
| `comp_p01_EBF_22_neutrino_full_mechanism.py` | Full mechanism: m_ν = E_D²·b^{29/9}/M_GUT; sum=56 meV |
| `comp_p01_EBF_24_SO10_CG_majorana.py` | SO(10) CG analysis; verifies dim(126)=2·N_c²·δ; third decomposition (45-16)/N_c² |
| `comp_p21_SP2_fn_texture_b29_9.py` | FN texture identification: (q₁,q₂)=(N_c,strand)=(3,2) reproduces b^(29/9); pre-commit SHA `53a7e175…`; verdict `TEXTURE_3_2_FROM_Nc` |

Each script emits a JSON artifact with SHA-256 hash. See `papers/01_SM/PROVENANCE.md` for full descriptions.

---

## Lean Provenance

| Module | Theorems / definitions | Role |
|--------|------------------------|------|
| `UgpLean.MassRelations.KoideAngle` (§8-9.1) | `nuSeesawExponent` (Lean `def`, value `29/9`), `nu_seesaw_exponent_three_decompositions` (theorem), `dim_126_SO10_eq_two_Nc_sq_delta` (theorem), `nu_seesaw_exponent_from_GUT_rep_diff` (theorem), `neutrino_seesaw_structural_closure` (theorem) | All main neutrino theorems plus the underlying value definition |
| `UgpLean.MassRelations.KoideAngle` (§§4-7) | `koide_angle_from_N_c_pure`, `N_c_determines_everything`, `strand_count_eq_su_nc_adj_div_4` | Koide phase from N_c; strand count |
| `UgpLean.MassRelations.SeesawIndex` | `seesaw_index_is_gauge_matter_defect`: 29 = dim(adj_SO(10)) − dim(spinor_SO(10)) = 45 − 16 | Seesaw index = SO(10) gauge/matter representation defect |
| `UgpLean.MassRelations.ScaleTransport` | `mass_ratio_Z_independent` | RG robustness of 0.02936 ratio prediction |
| `UgpLean.MassRelations.NeutrinoFroggattNielsen` | `fn_solutions_are_complete`, `fn_texture_3_2_is_unique_singleton_atomic`, `fn_structural_texture_existence_and_uniqueness` | FN-charge solution enumeration at N_c=3 + MDL singleton-atomic uniqueness theorem |
| `UgpLean.MassRelations.NeutrinoMassRatio` | `fn_texture_gives_seesaw_exponent`, `seesaw_ratio_independent_of_MR`, `neutrino_mass_ratio_coarse_bound` | EPIC_052 Phase 1 (2026-05-16): arithmetic/algebraic chain from FN texture to coarse bound 0.029 < R < 0.030; zero sorry |

Reproduce: `lake build UgpLean.MassRelations.KoideAngle UgpLean.MassRelations.SeesawIndex UgpLean.MassRelations.ScaleTransport UgpLean.MassRelations.NeutrinoFroggattNielsen UgpLean.MassRelations.NeutrinoMassRatio` (Lean 4.29.0-rc6, Mathlib 4.29.0-rc6). Zero sorry. Standard Mathlib axiom signature.

---

## Upgrade History

| Date | Change |
|------|--------|
| 2026-05-09 | Initial paper submitted to Zenodo; Lean certification via KoideAngle, SeesawIndex, ScaleTransport, NeutrinoFroggattNielsen |
| 2026-05-16 | **EPIC_052 Phase 1**: `NeutrinoMassRatio.lean` graduated to canonical `ugp-lean` (from sandbox `ugp-lean`, branch `theoretical_path_closure_sandbox`, commit `d77f7b2`). Coarse bound 0.029 < R < 0.030 Lean-certified zero sorry. Full Lagrangian bridge (Yukawa coupling scaling from FN texture → b^{q₁} and b^{q₂}) remains open; tight bound |R − 0.02936| < 0.0001 (Phase 2) deferred pending Mathlib Real.rpow norm_num extension. |
| 2026-05-16 | **EPIC_052 Phase 2**: tight bound `\|R − 0.02936\| < 0.0001` and NuFIT 6.0 1% comparison (`neutrino_mass_ratio_tight_bound`, `neutrino_mass_ratio_within_1pct_of_nufit`) proved zero-sorry via unit-width integer bounds on b^{58/9}: 31950 < 5^{58/9} < 31951, 5142772 < 11^{58/9} < 5142773, 174123159 < 19^{58/9} < 174123160 (all norm_num). Graduated from sandbox `ugp-lean` to canonical `ugp-lean`. `StructuralTheorems.lean` updated: `push_neg` → `push Not` (deprecation fix). |

---

## Data Provenance

- Neutrino oscillation data: NuFIT-5.2 global fit (2022), <https://www.nu-fit.org/>
- Normal ordering values: Δm²₂₁ = 7.42 × 10⁻⁵ eV², Δm²₃₁ = 2.517 × 10⁻³ eV²
- Cosmological bound: Planck 2018 TT,TE,EE+lowE+lensing+BAO: Σmν < 0.12 eV (95% CL)

---

## Related Papers

| Paper | Role |
|-------|------|
| P01 (Spivack2026_SM_UGP) | Parent paper; neutrino section §neutrino_structural |
| P17 (SpivackBraidAtlas) | Source of right-handed neutrino Braid Atlas triples |
| P18 (Spivack2026_Koide) | Source of Koide phase θ=2/9 and N_c structural chain |
| P19 (Spivack2026_CyclotomicMass) | Source of VV coefficients and dim(126) cross-identity context |
| ugp-lean | Lean 4 library containing all formal proofs |

## Update history (083C, 2026-06-02)

- **2026-06-02 (commit bba2d17e):** Added PMNS mixing angle orbit-ratio formulas: sin²θ₁₂=4/13 (+0.27σ), sin²θ₂₃=19/42 (+0.22σ), sinθ₁₃=11/73 (+0.67σ); χ²=0.564. Jarlskog invariant J_GTE added. NeutrinoSector structural theorems: `fn_dirac_yukawa_rank_theorem`, `pmns_cp_phase_from_z7_winding` (δ_CP=205.71°), `real_yukawa_gives_zero_leptogenesis_cp`. Scripts graduated: `pmns_orbit_ratio_final.py`, `pmns_jarlskog_derivation.py`.
