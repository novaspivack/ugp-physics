# PROVENANCE — P35 GTE Unification Capstone

**Paper:** GTE Unification: A Bidirectional Correspondence between Rule 110 Orbit
Arithmetic and the Standard Model Electroweak Sector

**Series position:** Paper 35 in the UGP Physics Programme (P01–P37)

**Date created:** 2026-05-20

## What this paper asserts

This is the capstone unification paper of the UGP Physics series.
It does not contain new derivations; it assembles results from prior papers
(P28, P29, P30, P31, P32, P33, P34, P36) into a single formal framework.

## Primary Lean certification

All arithmetic claims trace to theorems in:

**Repository:** `ugp-lean` (branch: main)  
**Module:** `UgpLean.Universality.GUTStructure`

Key theorems:
| Theorem | Section | Status |
|---|---|---|
| `ugp_r110_sm_joint_unification` | §27 | CatAL, zero sorry, zero new axioms |
| `gte_master_formula_complete` | §23 | CatAL, zero sorry |
| `gte_arithmetic_root` | §23 | CatAL |
| `weinberg_angle_closure` | §12 | CatAL |
| `wolfenstein_lambda_formula` | §14 | CatAL |
| `ngen_3_mersenne_uniqueness` | §23 | CatAL |

Additional modules:
- `CUP3DUniqueness.lean`: `fmdl_gen1_is_garden_of_eden`, `fmdl_unique_uniform_fixed_point`
- `DimensionalSliceUniqueness.lean`: `three_dim_fmdl_structure_forced`
- P30 (`rule110-lean`): `len6_evolved_origin_cert` (conditional on 1 axiom)

## Section source map (updated 2026-05-24)

| Section | Source paper |
|---|---|
| §2 GTE arithmetic | P28, P31, P32 |
| §3 GTE-Möbius substrate | P34 |
| §4 Bidirectional framework | P28, P31, P32, P33 |
| §5 Φ_MDL continuum substrate | P28, P34, P36 |
| §6 QCD from F₂₁ | P28 (new §§ from 2026-05-24 pass) |
| §7 Hadronic observables | P28 (new §§ from 2026-05-24 pass) |
| §8 Algebraic completeness | P28 (lifting/descent theorems) |
| §9 MDL-Lovelock gravity | P36 |
| §10 Deeper consequences | P33, P29 |
| §11 TPC boundary | P34 |

---

## 2026-05-24 — Track B paper pass: QCD/hadron/lifting sections added

New sections §§6–8 assembled from P28 physical substrate extensions:
- §6: QCD predictions from F₂₁ (asymptotic freedom, strong CP, colour factors, confinement, scale calibration, Lagrangian uniqueness, UV completion)
- §7: Hadronic observables (pion decay constant, η–η' mixing θ_P = −13.08° ± 3.74°, topological susceptibility χ_top^(1/4) = 166.5 MeV)
- §8: Algebraic completeness (Lifting Theorem, Descent Theorem, three-generation capstone, mass hierarchy, MDL uniqueness)

Added narrative transition sentences at §§6, 7, 8 section openings.
Full vocabulary pass: removed all internal confidence labels from prose; replaced with English equivalents.

**Last major revision:** 2026-05-24

## DOI

DOI pending Zenodo publication. See `nova_zenodo_doi_placeholder.tex`.

---

## Graduation checklist (2026-05-20 audit)

| Item | Status |
|------|--------|
| `GUTStructure` §27 + appendix inventory | ⏳ Graduate `ugp-lean` → `ugp-lean` |
| `CUP3DUniqueness`, `DimensionalSliceUniqueness` | ⏳ With shared bundle |
| Python scripts | ✅ 7 scripts in `scripts/` (2026-05-24) |
| Cross-paper hadron chain | ✅ P28 `scripts/` |
| Cross-paper Lean path in `.tex` | ⏳ Unify to `ugp-lean` post-graduation |

### Scripts graduated 2026-05-24 (original pass)

| Script | Rank |
|--------|------|
| `epsilon_scale_loglog.py` | 95-EPSSCALE |
| `epsilon_relative_expansion.py` | 95a-EPSREL |
| `two_sector_lattice.py` | 98-TWOSECTOR |
| `coupling_hierarchy_t98_5.py` | T98-5 |
| `substrate_wellposed_eft.py` | 103-WELLPOSED |
| `vcoup_uniqueness_enum.py` | 136-VCOUP |
| `epsilon_coupling_derivation.py` | 137-EPSDER |

### Scripts graduated 2026-05-24 (deferred pass — string tension and QCD chain)

| Script | Rank | P35 citation |
|--------|------|--------------|
| `rank132_sigmacal.py` | 132-SIGMACAL | √σ_4D = 440.6 MeV (§8 confinement, tab:predictions) |
| `rank113_kinkloop3v.py` | 113-KINKLOOP3V | Triangle form factor; vacuum polarization Π(Q²)∝log (§9 running coupling) |
| `rank114_eftmatch.py` | 114-EFTMATCH | Λ_GTE = 2.01 GeV UV matching scale (§9 deconstruction flow) |
| `rank146_threeloop_beta.py` | 146-THREELOOP | b₂=180.9, αs 3-loop=0.1193; P35 running coupling table update pending |

**Cross-references:**
- F₂₁ full lattice (rank120: β_c≈1.2, Higgs phase characterization) canonical in `papers/39_qcd_from_gte/scripts/`; P35 does not independently cite rank120 results — see P39.
- Hadronic/QCD chain (pion, θ_P, quark masses) canonical in `papers/28_computational_universality/scripts/`.

`REPRODUCE.md`; Handoff 9 § P35.

---

## Paper Pass — 2026-05-25 (EPIC_073 EW scale graduation)

**Ranks:** 168-EWD, 169-P2B, 158-EWS, 158-EWS-DR

| Script | Rank | Key result | Status |
|--------|------|------------|--------|
| `ew_threshold_definitional.py` | 168-EWD | EW threshold = k=N_gen orbit absorption | CatAL structural |
| `p22_vacuum_scale_bridge.py` | 169-P2B | E_0 = v_PSC sqrt(π/8); M_Z pred 91.914 GeV | CatAD |
| `ew_scale_consolidation.py` | 158-EWS | M_W=80.614 GeV, M_Z=91.914 GeV; consistency PASS | CatAD |
| `epic073_rank158_ews_dr_delta_r_ca_loop_closure.py` | 158-EWS-DR | Δr Sirlin path; photon VP loop negative | CatAD |

**Lean:** `EWScalePrediction.lean` — `e0_schwinger_sm_identity`, `mw_formula_from_vH`, `mz_formula_from_vH` (zero sorry).

**Lab notes:** `LAB_NOTE_169-P2B_vacuum_scale_bridge.md`, `LAB_NOTE_158-EWS_ew_scale_consolidation.md` (internal).

**Graduated:** sandbox → `papers/35_gte_unification/scripts/` (2026-05-25).
