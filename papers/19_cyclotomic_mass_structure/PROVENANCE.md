# Provenance: Cyclotomic-12 Mass Structure Paper (P19)

**Paper:** *Cyclotomic-12 Structure in the Charged-Fermion Mass Spectrum: A₂ Weyl-Chamber Geometry, Froggatt–Nielsen UV Completion, SU(5)/SO(10) GUT Derivation of VV Coefficients, and Three Null-Discipline Tests*
**Author:** Nova Spivack
**Status:** In preparation

---

## Paper Claims and Their Status

The paper uses a three-level status taxonomy:

* **[T] Theorem-certified** — machine-checked in `ugp-lean` (zero `sorry`).
* **[E] Empirical structural regularity** — verified against PDG data with pre-registered null tests.
* **[C] Consistency claim** — established as non-trivial structural consistency; not a uniqueness statement.

### TT formula

| Claim | Content | Status |
|-------|---------|--------|
| TT formula holds (3 gens) | `log(m_{u_g}/m_{ℓ_g}) = (π/6)·2^g + π/8`, ≤0.37% | [E] |
| α=π/6 is A₂ Weyl angle | `angle_alpha1_omega1_eq_pi_div_six` | [T] |
| 2^g from binary cascade | `cascadeState_eq_TT` | [T] |
| β=π/8 from FN potential | `fn_vevs_are_potential_minima` | [T] |
| β=π/8 = α/C₂(SU(3)) | `beta_eq_alpha_div_c2_su3` | [T] |
| FN = heavy-fermion tower | `tower_eq_FN` (EFT duality) | [T] |
| β=2/5 excluded | 6.75σ current PDG data | [E] |
| β=1/φ² excluded | 3.62σ current PDG data | [E] |

### VV formula

| Claim | Content | Status |
|-------|---------|--------|
| VV formula holds (3 gens) | `log m_{d_g} = (13/9) log m_{u_g} − (7/6) log m_{ℓ_g} − 5/14`, ≤0.17% | [E] |
| Null density (formula) | ≤10⁻⁵ under random triple-permutation | [E] |
| α_d = 1 + rank(SU(5))/N_c² = 13/9 | Structural | [T] |
| β_d = −(1 + Y_QL) = −7/6 | Structural | [T] |
| γ_d = −dim(45_SU(5))/dim(126_SO(10)) = −5/14 | `VV_from_GUT_group_theory` | [T] |
| dim(126_SO(10)) = 2 N_c² δ | `dim_126_SO10_eq_two_Nc_sq_delta` | [T] |
| SC-JJJ basis saturation | 54% triple-null at 10⁻³ (GUT basis) | [E] |
| SC-KKK FN obstruction | No consistent FN integer-charge assignment | [E] |
| SC-LLL discrete-flavour | 40% triple-null at 10⁻³ | [E] |
| CDM: Δa_eff = α_d = 13/9 | `cabibbo_effective_charge` (effective Cabibbo FN charge = VV coefficient) | [T] |
| CDM: log\|V_us\|_CDM = −13π/27 | `log_cabibbo_eq_neg_13pi_27` (structural log prediction) | [T] |
| CDM: \|V_us\|_CDM = ε₁^(α_d) = exp(−13π/27) | `cabibbo_vev_formula`, `cdm_mechanism_summary` — uses `fn_vevs_are_potential_minima` + `VV_from_GUT_group_theory` | [T] |
| CDM-4 FN bridge: additive VV propagation | `fn_vv_correction_additive`: fnMixChargeDown(α_d) = fnMixChargeDown(1) + (α_d−1); formal proof that VV GUT coefficient shifts bare FN charge additively — KEY structural bridge | [T] |
| CDM-4 FN bridge: GUT correction = charge gap | `fn_charge_gap_is_gut_correction`: rightSectorMixCharge − leftDoubletMixCharge = gut_rank_correction; the two FN approaches differ by exactly the GUT rank correction rank(SU(5))/N_c² | [T] |
| CDM-4 FN bridge: log formula | `fn_diagonalization_vv_bridge`: fnMixChargeDown(α_d) × log(ε₁) = −13π/27 | [T] |
| CDM-4 FN bridge: VV gives more suppression | `fn_vv_more_suppressed`: ε₁^(α_d) < ε₁^1 (VV tightens FN hierarchy, consistent with CDM) | [T] |
| CDM-4 FN bridge: algebraic identity | `fn_cdm_physical_sorry`: log(cabibbo_structural_prediction) = fnMixChargeDown(α_d) × log(ε₁) — both sides equal log_cabibbo_structural = −13π/27 (proved via Real.log_exp + fn_diag_vv_log_eq_cabibbo) | [T] zero sorry (2026-05-11) |
| CDM-4 physical [C] (open) | Broader identification \|V_us\|_SM = ε₁^(α_d) via 2×2 FN SVD diagonalization: \|(U_uL† U_dL)_{12}\| = ε₁^(α_d)·(1+O(ε₁²)) — not yet formalized in Lean | [C] open structural hypothesis |

### Composite chain

| Claim | Content | Status |
|-------|---------|--------|
| All 9 masses from 2 inputs | TT + VV + Koide chain | [E]+[T] |
| End-to-end Lean capstone | `PhysicalMasses.TT_formula_holds_on_physical`, `LeptonMassPrediction.predictedLeptonMass` | [T] |

---

## Computational Artifacts

All computational artifacts reside in `papers/01_SM/canonical_run/` (shared with Paper 1 / P01).

### Core artifacts for P19

| File | Description |
|------|-------------|
| `comp_p01_TT_up_lepton_cyclotomic_identity.py` / `.json` | TT identity verification; null-density test (6×10⁻⁶ under 10⁶ trials). |
| `comp_p01_VV_down_linked_to_up_lepton.py` / `.json` | VV identity verification; null density ≤10⁻⁵. |
| `comp_p01_WW_LHC_run4_discriminator.py` / `.json` | Pre-committed LHC Run-4 discriminator for β in TT. |
| `comp_p01_XX_gut_structure_search.py` / `.json` | GUT/Lie-theoretic search for VV coefficients; exact matches for 13/9, −7/6, −5/14. |
| `comp_p01_EBF_14_vv_rg_flow.py` / `.json` | One-loop gauge RG running test of VV coefficient identification. |
| `comp_p01_EBF_15_vv_gj_su5_full.py` / `.json` | Full Georgi–Jarlskog SU(5) RG computation (72-point parameter scan). |
| `comp_p01_EBF_16_vv_gut_group_theory.py` / `.json` | Exact Weyl-dimension-formula verification for A_4 = SU(5) and D_5 = SO(10); structural derivation of all three VV coefficients. |
| `comp_p19_T01_wolfenstein_improved.py` / `.json` | **T-01 tension analysis (2026-05-11).** Improved Wolfenstein λ formula: ε₁^(α_d) = e^{−13π/27} ≈ 0.2203 (1.9% off PDG 0.2245). Full null test of 576 rational powers p/q ∈ [1,24]²; 13/9 ranks #6 numerically but is uniquely Lean-certified from VV relation. Reduces tension from 12.5% (sin(14.68°)) to 1.9%. |

Each script is independently reproducible with Python 3.9+, `numpy`, and (where used) `sympy`.  Each `.json` artifact carries a SHA-256 hash; re-running the script on the committed state reproduces the content modulo any explicit `timestamp_utc` field.

### Pre-registration methodology

The null-discipline tests (SC-JJJ GUT basis, SC-KKK FN basis, SC-LLL discrete-flavour basis) are pre-registered: basis definitions are committed with SHA-256 hashes before any scan is executed; null rates are computed only after commit.  This mirrors pre-registration in clinical trials.

---

## Lean Provenance

All Lean theorems are in the public `ugp-lean` repository (<https://github.com/novaspivack/ugp-lean>).

| Module | Role |
|--------|------|
| `UgpLean.MassRelations.SU3FlavorCartan` | A_2 Weyl-chamber angle π/6 |
| `UgpLean.MassRelations.BinaryCascade` | Binary cascade → TT closed form |
| `UgpLean.MassRelations.FroggattNielsen` | FN UV completion; β=π/8 |
| `UgpLean.MassRelations.CartanFlavonPotential` | Z_6 × Z_16 potential minima |
| `UgpLean.MassRelations.Z2OrbifoldDepth` | Doubled FN charges from Z_2-tree depth |
| `UgpLean.MassRelations.HeavyFermionTower` | EFT duality: FN = heavy-fermion tower |
| `UgpLean.MassRelations.UpLeptonCyclotomic` | TT scaffolding; β = α/C₂(SU(3)) = π/8 |
| `UgpLean.MassRelations.DownRational` | VV rational form; N_c formulas; GUT group-theory derivation |
| `UgpLean.MassRelations.ClebschGordan` | Clebsch–Gordan structural anchors |
| `UgpLean.MassRelations.KoideClosedForm` | Koide m_τ prediction (see P18) |
| `UgpLean.MassRelations.KoideAngle` | θ = (N_c²−1)/(4N_c²) = 2/9 from N_c = 3; N_c chain |
| `UgpLean.MassRelations.ClaimCBridge` | Formal TT cascade: (π/6)·2^g + π/8 |
| `UgpLean.MassRelations.PhysicalMasses` | End-to-end capstone (TT + VV + Koide) |
| `UgpLean.MassRelations.LeptonMassPrediction` | Lepton mass pipeline from (m_e, θ) |
| `UgpLean.MassRelations.CKMMixing` | CDM mechanism + FN diagonalization bridge (2026-05-11, updated zero-sorry 2026-05-11): Δa_eff = α_d = 13/9; \|V_us\|_CDM = ε₁^(α_d) = exp(−13π/27) ≈ 0.2203; additive VV propagation `fn_vv_correction_additive`; GUT charge gap `fn_charge_gap_is_gut_correction`; log formula `fn_diagonalization_vv_bridge`; algebraic identity `fn_cdm_physical_sorry`. **Entire module zero sorry (11 theorems, §1–§7).** Physical [C] claim (|V_us|_SM = ε₁^(α_d) via 2×2 SVD) remains open but is NOT stated as a Lean theorem. |
| `UgpLean.ElegantKernel.Unconditional.KGenFullClosure` | k_gen = φ·cos(π/10); pentagon–hexagon bridge |

Reproduce all theorems by cloning the repository and running `lake build` (Lean 4.29.0-rc6, Mathlib 4.29.0-rc6).  Zero `sorry`; standard Mathlib axiom signature `[propext, Classical.choice, Quot.sound]`.

---

## PDG Data Provenance

All experimental masses are from the 2022 PDG *Review of Particle Physics*.
- URL: <https://pdg.lbl.gov/2022/>
- Citation: R. L. Workman et al. (Particle Data Group), Prog. Theor. Exp. Phys. 2022, 083C01.

---

## Known Tensions and Resolutions

| Tension | Original claim | Improved result (2026-05-11) | Status |
|---------|---------------|------------------------------|--------|
| Wolfenstein λ (CKM) | sin(14.68°) ≈ 0.253 vs PDG 0.2245 (~12.5% off) | ε₁^(α_d) = e^{−13π/27} ≈ 0.2203 (~1.9% off). Lean-certified: entire `CKMMixing` module zero sorry (11 theorems, §1–§7, 2026-05-11). Algebraic CDM formula [T], FN diagonalization bridge [T], algebraic identity `fn_cdm_physical_sorry` [T]. Physical [C] claim (|V_us|_SM = ε₁^(α_d) via 2×2 SVD) is an open structural hypothesis, NOT stated as a Lean theorem. | Resolved: tension reduced 6.7×. Full Lean module zero sorry [T]. Physical identification [C] remains open honest hypothesis. |

---

## What This Paper Does NOT Claim

1. The VV formula is presented as a structural identity with each coefficient independently identified in SU(5)/SO(10) representation theory; this identification is consistency-class, not a uniqueness statement.  Three independent null-discipline tests quantify the saturation of alternative structural bases; these tests establish that no single structural basis *by itself* uniquely determines the coefficient triple.

2. The TT formula is **not** claimed to predict absolute up-type masses from first principles; it predicts the up-to-lepton log-mass ratio.  The lepton masses are inputs from the Koide closed form (see the companion paper P18).

3. The Froggatt–Nielsen UV completion is a **realisation**, not a unique derivation.  VEV coset selection (96 equivalent minima on the Cartan torus) requires additional input.

4. The full CKM and PMNS matrix predictions are addressed in the parent paper P01 and are not claimed at full precision in this paper.

---

## Related Papers

| Paper | Role |
|-------|------|
| `Spivack2026_SM_UGP` (P01) | Parent paper; UGP framework and full SM derivation |
| `Spivack2026_Koide` (P18) | Companion; Koide closed form and cyclotomic-12 |
| `ugp-lean` | Lean 4 library containing all formal proofs |
