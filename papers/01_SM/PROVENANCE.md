# Provenance: Standard Model Paper

**Paper:** *A Deterministic Number-Theoretic Framework for the Standard Model Parameter Spectrum*  
**Status:** In preparation

---

## Primary Script

All end-to-end Standard Model results (empirical/theoretical dual-path UCL, gauge couplings, CKM/PMNS, Higgs, cosmological constant, neutrino seesaw) are produced by a single self-contained Python script:

| Script | Location |
|--------|----------|
| `UGP_GTE_SM_Verifier.py` | `UGP_GTE_SM_Verifier/` |

Run command:
```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
  --preset-fullstack --n 10 --full-derivation 1
```

**Expected runtime:** 3–8 minutes on a modern laptop.

---

## Canonical Frozen Run Artifacts

The frozen artifact bundle in `papers/01_SM/canonical_run/` was produced by a verified `--preset-fullstack --n 10 --full-derivation 1` UGP_GTE_SM_Verifier run.

### Key Verified Outputs

| Quantity | Canonical Value | Source |
|----------|----------------|--------|
| Primary σ GoF (empirical) | **4.364 × 10⁻⁵ %** | `dual_path_comparison.json` |
| Primary σ GoF (theoretical) | 0.293 % | `dual_path_comparison.json` |
| W-ρ statistic | 1.04900 (PASS) | Run log |
| Baryon RMS (theoretical) | ~0.01 % | Run log |
| Fine-structure constant α | +2.39 ppm vs CODATA | Run log |
| sin²θ_W | ~0.259343 | `ewk_couplings_from_gte.json` |
| Σmν (neutrino masses) | 60 meV | `seesaw_from_ugp.json` |
| δ_CP | ~38.97° | `seesaw_from_ugp.json` |
| Gauge anomaly cancellation | Exact rationals; all four sums vanish | `anomaly_proof.json` |

### Canonical Frozen Artifacts (Core Run)

| File | Contents |
|------|----------|
| `dual_path_comparison.json` | Empirical + theoretical mass predictions; primary σ GoF |
| `gte_cascade_derivation.json` | N-value cascade derivation |
| `anomaly_proof.json` | Gauge anomaly cancellation (exact rationals) |
| `ckm_report.json` | CKM matrix derived from τ(1008)/D₁ formula |
| `pmns_report.json` | PMNS matrix (QLC + TM2) |
| `pmns_ckm_style_suite.json` | Combined PMNS/CKM suite |
| `seesaw_from_ugp.json` | Neutrino masses, δ_CP, M_R scales |
| `ewk_couplings_from_gte.json` | Gauge couplings g₁, g₂; sin²θ_W |
| `dof_ledger.json` | Degrees of freedom ledger |
| `nulls_suite.json` | Permutation nulls (all < 4×10⁻⁵ %) |
| `grand_synthesis_audit.json` | Full synthesis audit |
| `uncertainty_summary.json` | Particle-level uncertainty propagation |
| `theoretical_coefficients.json` | Derived GTE coefficients |
| `quark_evolution_certificate.json` | Quark mass evolution certificate |
| `dual_universe_n10.json` | Dual universe analysis at n=10 |

### Supplementary Run Artifacts

Two additional frozen artifacts under `papers/01_SM/Verifier_runs/`:

| File | Contents |
|------|----------|
| `cosmological_lambda_L_model_trace.json` | Cosmological constant Λ decomposition |
| `te1e_frw_validation_run_20251110_230054_summary.json` | FRW consistency validation |

Lambda normalization proof lives in `ugp_discovery_lab/results/lambda_normalization_proof.json`.

---

## Companion Computational Artifacts

The paper's main computational artifacts live in `papers/01_SM/canonical_run/`.  The supporting structural analyses — covering ridge seed uniqueness, engine sensitivity, the α_s pre-commit trail, the lepton-sector anchor, the charged-fermion structural chain, the VV group-theory derivation, and the neutrino-sector structural mechanism — are provided as standalone scripts with individual JSON output and SHA-256 hashes.  Each script is independently reproducible.

### Null-test, sensitivity, and gauge-sector artifacts

| Artifact | Script | Description |
|----------|--------|-------------|
| `nulls_suite_1000.json` | `nulls_suite_1000.py` | 1000-permutation null suite (N-perm + b-perm); raw distribution invariant under regen (min permutation σ > 5.6×10⁻², well above canonical baseline σ = 2.95×10⁻⁵); min ratios to baseline 1912:1 (N) and 5922:1 (b). |
| `dual_path_comparison_figure.{png,json}` | `dual_path_comparison_figure.py` | Figure 1 — theoretical vs empirical UCL coefficients (max 1.83 %, RMS 0.96 %). |
| `nu_R_sensitivity.{json,tex}` | `nu_R_sensitivity.py` | Σmν anchor sweep over preregistered [55,120] meV window + Δm² 1σ sweep; m_ββ ∈ [2.65, 32.23] meV across the full window. |
| `alpha_s_prediction.json` | `derive_alpha_s_prediction.py` | Blind α_s(M_Z) from Lean-certified g₃²_bare: predicted 0.11822, PDG 0.1179 ± 0.0009, +0.36σ. |
| `engine_param_sensitivity.json` | `engine_param_sensitivity.py` | Engine-parameter sensitivity (±0.01–10 %); geometric-mean primary-σ degradation factor ≈ 2.3×10³ at ±10 % (≈ 2.3×10² at ±1 %; ratios reflect the regenerated baseline_primary_sigma = 2.95×10⁻⁵, with absolute perturbed σ values essentially unchanged across regens). |
| `s3_overlap_seesaw.json` | `s3_overlap_seesaw.py` | S₃-overlap ν_R pipeline test (3 natural overlap formulas); pipeline as specified is underdetermined without external anchor. |
| `landscape_probe.{json,bfopt.json}` | `landscape_probe.py`, `landscape_probe_bfopt.py` | 5-axis two-layer optimum topology probe. |
| `te22_rcc_certificate.json` | `te22_rcc_certificate.py` | TE2.2 RCC computational certificate. 34,560 universes scanned; SM is the global D-minimizer. |
| `loo_ucl_validation.json` | `loo_ucl_validation.py` | UCL cross-validation showing all 9 UCL features mutually necessary. |
| `alpha_w_prediction.json` | `derive_alpha_w_prediction.py` | α_w(M_Z) = 0.0343 (+1.6% vs PDG); sin²θ_W = 0.2289 (−1.0% vs PDG). |
| `ebase_first_principles_audit.json` | `ebase_first_principles_audit.py` | Audit of engine E_base; certifies hardcoded experimental inputs and motivates structural-anchor analysis. |

### Lepton-sector anchor (structural search + null tests)

| Artifact | Script | Description |
|----------|--------|-------------|
| `comp_p01_K_charged_lepton_integer_search.json` | `comp_p01_K_charged_lepton_integer_search.py` | Bounded integer-relation search over UGP 21-atom structural basis. Electron hit: m_e ≈ δ·b₁ = 511 keV to +2.05 ppm, description length 2. |
| `comp_p01_K_null_test.json` | `comp_p01_K_null_test.py` | 500-trial permutation null under description-length caps. Electron δ·b₁ hit STRUCTURALLY SIGNIFICANT at p=0.004 (cap 10) / p=0.008 (cap 20). |
| `comp_p01_L_koide_from_s3.json` | `comp_p01_L_koide_from_s3.py` | Koide Q=2/3 as S₃ equal-norm condition. Empirical angle 44.999735° (target 45°). |
| `comp_p01_M_kev_scale_derivation.json` | `comp_p01_M_kev_scale_derivation.py` | Tests whether δ·b₁ = 511 keV derives from UGP scale-free structure; finds UGP is scale-free by construction. |
| `comp_p01_N_koide_anchored_composite.json` | `comp_p01_N_koide_anchored_composite.py` | UGP δ·b₁ + Koide 2/3 + m_μ predicts m_τ at 61.5 ppm, inside PDG τ uncertainty. |
| `comp_p01_O_koide_ridge_amplitude.json` | `comp_p01_O_koide_ridge_amplitude.py` | Koide as asymptotic UGP ridge-amplitude limit; r²_n = R_n/2^(n−1) → 2. |
| `comp_p01_P_koide_integer_triple.json` | `comp_p01_P_koide_integer_triple.py` | UGP integer-triple search for Koide + lepton-ratio match; 1715-atom library. |
| `comp_p01_Q_gte_basin_koide.json` | `comp_p01_Q_gte_basin_koide.py` | GTE basin q_early Koide test; rejects naive basin-centre identification. |
| `comp_p01_R_koide_S3_quadric.json` | `comp_p01_R_koide_S3_quadric.py` | Koide as unique S₃-invariant null quadric; M = 3I − 2J has spectrum (−3, +3, +3). Null test: 0 of 10,000 random triples closer to the null cone (p < 10⁻⁴). |

### TT / VV mass-relation artifacts

| Artifact | Script | Description |
|----------|--------|-------------|
| `comp_p01_TT_up_lepton_cyclotomic_identity.json` | `comp_p01_TT_up_lepton_cyclotomic_identity.py` | TT identity log(m_u_g/m_lep_g) = (π/6)·2^g + β; best-fit β = π/8 (0.44% max-frac-err). Null density 6×10⁻⁶ in 10⁶ random trials. |
| `comp_p01_VV_down_linked_to_up_lepton.json` | `comp_p01_VV_down_linked_to_up_lepton.py` | VV identity log(m_d_g) = (13/9)·log(m_u_g) + (−7/6)·log(m_lep_g) + (−5/14). 0 of 10⁵ random trials. |
| `comp_p01_WW_LHC_run4_discriminator.json` | `comp_p01_WW_LHC_run4_discriminator.py` | Pre-committed LHC Run-4 discriminator for β in TT. |
| `comp_p01_XX_gut_structure_search.json` | `comp_p01_XX_gut_structure_search.py` | GUT/Lie-theoretic search for VV coefficients: −5/14 = −dim(45_SU5)/dim(126_SO10); −7/6 = −(1 + Y_Q); 13/9 = 1 + rank(SU5)/N_c². |
| `comp_p01_QQ_mW_from_inverse_solved_M2.json` | `comp_p01_QQ_mW_from_inverse_solved_M2.py` | m_W at −4.88σ from inverse-solved M_2 = 37.4 GeV via 1-loop SM running. |
| `comp_p01_RR_koide_s3_flow_phase1.json` | `comp_p01_RR_koide_s3_flow_phase1.py` | Classification of linear S_3-equivariant q-preserving operators; sharpens the open-problem statement in the Koide analysis. |

### E_base structural analysis and type-modulation

| Artifact | Script | Description |
|----------|--------|-------------|
| `comp_p01_EBF_01_casimir_type_modulation.json` | `comp_p01_EBF_01_casimir_type_modulation.py` | Casimir-invariant type modulation; H-3e formula (C₂(SU3)/(3/2) for up; C₂(SU3)·(1 − 2sin²θ_W/3) for down) at 4.6% max deviation. |
| `comp_p01_EBF_02_orbit_volume_holographic.json` | `comp_p01_EBF_02_orbit_volume_holographic.py` | 40 orbit invariants tested; tau and charm have distinct c-signs in Braid Atlas canonical triples. |
| `comp_p01_EBF_03_det_ratio_null_and_corrections.json` | `comp_p01_EBF_03_det_ratio_null_and_corrections.py` | α_s/π correction closes up-type Casimir gap to 0.64%. |
| `comp_p01_EBF_04_fibonacci_generation_hierarchy.json` | `comp_p01_EBF_04_fibonacci_generation_hierarchy.py` | Pentagon–Hexagon identity k_gen + k_gen2 = φ(cos(π/10) − cos(π/3)). |
| `comp_p01_EBF_05_mfrr_reflexive_landauer_bridge.json` | `comp_p01_EBF_05_mfrr_reflexive_landauer_bridge.py` | MFRR Landauer bridge for charged-fermion masses: anti-correlation theorem rules this out. |
| `comp_p01_EBF_06_type_mod_u1_correction.json` | `comp_p01_EBF_06_type_mod_u1_correction.py` | Type modulation at 4 ppm (up) / 0.84% (down) via Casimir + QCD + U(1) hypercharge correction. |
| `comp_p01_EBF_07_upquark_hierarchy.json` | `comp_p01_EBF_07_upquark_hierarchy.py` | Up-quark mass hierarchy analysis via TT cascade + Braid Atlas structure. |
| `comp_p01_EBF_08_muon_electron_ratio.json` | `comp_p01_EBF_08_muon_electron_ratio.py` | m_μ/m_e structural formula analysis. |
| `comp_p01_EBF_09_deep_muon_structure.json` | `comp_p01_EBF_09_deep_muon_structure.py` | Deep m_μ/m_e structure; identifies Koide angle θ = 2/9 from UGP integer a_μ = 9. |
| `comp_p01_EBF_10_koide_universality.json` | `comp_p01_EBF_10_koide_universality.py` | Koide universality test: Q=2/3 is charged-lepton-specific; other sectors require distinct mechanisms. |

### N_c structural chain (Koide angle derivation)

| Artifact | Script | Description |
|----------|--------|-------------|
| `comp_p01_EBF_11_koide_angle_structural_search.json` | `comp_p01_EBF_11_koide_angle_structural_search.py` | Discovery of a_μ = N_c² = 9 and the universal a-value pattern {1, 5, 9}. |
| `comp_p01_EBF_12_top_quark_and_s3_angle.json` | `comp_p01_EBF_12_top_quark_and_s3_angle.py` | Top-quark a-value a_top = N_c⁴ − a_τ = 76; structural derivation of δ = 7, b₁ = 73 from N_c. |
| `comp_p01_EBF_13_s3_koide_angle_proof.json` | `comp_p01_EBF_13_s3_koide_angle_proof.py` | strand_count = (N_c²−1)/4 = 2; θ = strand_count/N_c² = 2/9 from N_c = 3. |

### VV GUT group theory derivation

| Artifact | Script | Description |
|----------|--------|-------------|
| `comp_p01_EBF_14_vv_rg_flow.json` | `comp_p01_EBF_14_vv_rg_flow.py` | One-loop gauge RG running test of VV coefficient identification; confirms the N_c identification is algebraic rather than RG-dynamical. |
| `comp_p01_EBF_15_vv_gj_su5_full.json` | `comp_p01_EBF_15_vv_gj_su5_full.py` | Full Georgi-Jarlskog SU(5) RG computation (72-point parameter scan). |
| `comp_p01_EBF_16_vv_gut_group_theory.json` | `comp_p01_EBF_16_vv_gut_group_theory.py` | Exact GUT group-theory derivation of VV coefficients: α = 1 + rank(SU(5))/N_c², β = −(1 + Y_Q), γ = −dim(45_SU5)/dim(126_SO10) = −5/14. Weyl dimension formula verified for A_4 = SU(5) and D_5 = SO(10). |

### Neutrino sector structural prediction

| Artifact | Script | Description |
|----------|--------|-------------|
| `comp_p01_EBF_17_neutrino_survey.json` | `comp_p01_EBF_17_neutrino_survey.py` | Six-approach survey of structural neutrino mass prediction; Braid Atlas b-values {5,11,19} identified as optimal basis. |
| `comp_p01_EBF_18_neutrino_126_bridge.json` | `comp_p01_EBF_18_neutrino_126_bridge.py` | Tests N_c-cube (b³), 126-bridge, a-value hypotheses; discovers m_ν ∝ b^{29/9} structure. |
| `comp_p01_EBF_19_neutrino_29_9_derivation.json` | `comp_p01_EBF_19_neutrino_29_9_derivation.py` | Null test: 8/3654 integer triples in [2,30] hit within 1% of target; the Braid Atlas triple is one of them. |
| `comp_p01_EBF_20_neutrino_absolute_scale.json` | `comp_p01_EBF_20_neutrino_absolute_scale.py` | Absolute mass scale verification: full M_GUT sensitivity scan and falsifiability catalogue. |
| `comp_p01_EBF_21_neutrino_29_9_structural_decomp.json` | `comp_p01_EBF_21_neutrino_29_9_structural_decomp.py` | Structural decomposition landscape of 29/9 in N_c and mirror-offset constants. |
| `comp_p01_EBF_22_neutrino_full_mechanism.json` | `comp_p01_EBF_22_neutrino_full_mechanism.py` | Full mechanism verification: m_ν = E_D² · b^{29/9}/M_GUT with E_D = v_H/29. SHA-256 pre-commit of predictions. |
| `comp_p01_EBF_23_MGUT_from_UGP_gauge.json` | `comp_p01_EBF_23_MGUT_from_UGP_gauge.py` | Attempt to derive M_GUT from UGP Lean-certified bare gauge couplings via one-loop SM RGE. Finds SM does not cleanly unify (standard result); g₂² = g₃² crossing at 4.78×10^16 GeV. |
| `comp_p01_EBF_24_SO10_CG_majorana.json` | `comp_p01_EBF_24_SO10_CG_majorana.py` | SO(10) Clebsch-Gordan analysis for Majorana sector; identifies cross-identity dim(126) = 2·N_c²·δ and third decomposition 29/9 = (dim(45_SU5) − dim(16_SO10))/N_c². |

---

## Code Inventory

| File | Location | Role |
|------|----------|------|
| `UGP_GTE_SM_Verifier.py` | `UGP_GTE_SM_Verifier/` | All primary end-to-end SM results |
| `ucl_certificates.py` | `UGP_GTE_SM_Verifier/` | Quarter-lock residual computation |
| `higgs_canonical.py` | `UGP_GTE_SM_Verifier/` | Higgs canonical form |
| `neutrino_canonical.py` | `UGP_GTE_SM_Verifier/` | Neutrino canonical form |
| `Verifier_discovery_engine_v4.py` | `discovery_engine/` | Engine co-dependency |
| `comp_p01_*.py` | `papers/01_SM/canonical_run/` | Standalone structural-analysis scripts (listed above) |
| `comp_p01_EBF_*.py` | `papers/01_SM/canonical_run/` | E_base/Koide/VV/neutrino structural-analysis scripts (listed above) |

---

## Reference Lock Verification

To verify against the frozen reference lock:
```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py --verify-reference --n 10
```

Each standalone `comp_p01_*.py` script emits its own JSON artifact and SHA-256 hash; re-running any script on the committed state produces the same JSON modulo the `timestamp_utc` field (which changes on each run).

---

## Companion Formalization

| Resource | URL |
|----------|-----|
| `ugp-lean` library (Lean 4, Mathlib) | https://github.com/novaspivack/ugp-lean |

Machine-checked Lean 4 proofs for every Category A structural theorem cited in this paper.  See the companion formalization paper for the full theorem inventory.

Reproducibility of every `comp_p01_*.py` script is independent of the Lean library: scripts are self-contained Python and require only `numpy` and (optionally) `scipy`, `sympy`.

---

## Environment

- Python 3.9+ with `numpy` (any recent version)
- Optional: `scipy`, `sympy`, `matplotlib` (used by a subset of the standalone scripts)
- No GPU, external optimiser, or Monte Carlo search required
- All RNG-based null tests use explicitly seeded NumPy generators; results are bit-exact reproducible across platforms

---

## Cross-sector Structural-Gap Artifacts

Supplementary structural-gap investigations supporting the open-problem registry (§10 of the main paper).

| Artifact | Description | Gate verdict |
|----------|-------------|--------------|
| `comp_p21_SP_C_vv_bvalue_power_law.json` | VV relation in GTE b-value space; gamma spread 6.27; residuals 15–170%. | Productive negative — VV is mass-level, not a b-value power law. |
| `comp_p21_SP_D_urc_sm_corrections.json` | URC vs SM 1-loop radiative corrections; K_URC ≈ 2.5e-4 vs α_s/(2π) ≈ 1.9e-2. | Productive negative — K_URC is 80× smaller than 1-loop QCD; confinement-scale 1:10:100 series. |
| `comp_p21_SP_E_ckm_wolfenstein.json` | CKM via Gatto-Sartori-Tonin from UGP masses. | Partial — \|Vus\| 1.1%; \|Vcb\| 269% (needs HQET). |
| `comp_p21_SP_G_te1p_composability.json` | TE₁.P factor vs QED running M_Z → Thomson; agreement 1.25%. | Structural explanation confirmed — TE₁.P = IR QED running; δ_UGP = UV instantiation. |

These artifacts inform the OP(iii), OP(v), OP(v'), and OP(v'') disclosures in §10.

---

## Change Log

### 2026-05-11 — m_W OP(viii) resolution + paper fixes

**Computation:** `comp_p01_AAA_mw_residual_decomposition.py/.json`

**Changes to `standard_model_from_ugp.tex`:**
- §subsec:higgs VEV paragraph: removed erroneous Sirlin formula (M_W = 80.38 claim was a paper bug — actual source was EWK echo g2_EWK=0.5948 × v_EWK=270.3 GeV using G_F_UGP ≠ G_F_PDG). Replaced with authoritative ZZ two-loop result (80.364 GeV) and honest EWK echo structural check disclosing G_F_UGP 17% below PDG.
- §subsec:status sin²θ_W convention note: updated to clarify EWK echo uses UGP-internal G_F, not PDG G_F.
- OP(viii): updated to state −0.42σ (PDG 2024 world avg 80.3692 ± 0.0133); added residual decomposition (13 MeV gap = SM/PDG tension); added EWK echo G_F discrepancy as new open structural subproblem.
- All 7 inline −1.28σ citations updated to −0.42σ (PDG 2024) / −1.28σ (older PDG 80.379) with context.

**Changes to `supplementary_information.tex`:**
- SC-OP-VIII table row: "partial closure" → "full closure at −0.42σ (PDG 2024)"; added COMP-P01-AAA artifact reference.
- m_W two-loop table row: "Partial closure within PDG 2σ" → "Closed within PDG 1σ".

**New artifact:** `comp_p01_AAA_mw_residual_decomposition.json` — quantitative decomposition of 13 MeV gap; PDG value sensitivity; ρ-formula verification/refutation; 3-loop upper bound.

**Downstream papers updated same session:**
- `papers/06_math_foundations/algebraic_geometric_foundations_ugp.tex` (line 649): "Blind falsification" → "Blind falsification and recovery"; added −0.42σ recovery result.
- `papers/22_ugp_dynamics/ugp_dynamics_paper.tex` (4 sites): all −1.28σ → −0.42σ; PDG table updated to 80.3692 ± 0.0133.
- `ugp-lean/UgpLean/Phase4/GaugeCouplings.lean` (line 66): docstring updated.
- `papers/00_survey_guide/ugp_survey_readers_guide.tex`: α_s σ 0.36 → 0.24 (PDG 2024); m_W OP(viii) closed; P21 row updated to NuFIT 6.0 0.16σ.
