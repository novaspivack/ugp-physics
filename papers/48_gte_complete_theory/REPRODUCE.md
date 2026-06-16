# Reproducing P48 Results

This monograph assembles derivations from P01–P47. All numerical predictions
are reproducible by running the scripts in the cited source papers. The central
algebraic steps are machine-checked in the canonical `ugp-lean` library.

## Scripts shipped with this paper (`scripts/`)

| Script | What it demonstrates | Expected output |
|--------|----------------------|-----------------|
| `scripts/UGP_GTE_UWCA_rule.py` | The executable witness of the Mathematical Substrate chapter: (Part A) the compiled GTE macro-program beside the bare arithmetic map T, register-exact on the canonical orbit (1,73,823) → (9,42,1023) → (5,275,65535) with all ridge invariants (m₁ = 20, m₂ = 15, gap 13, F₁₃ = 233) and CRT round-trips asserted; (Parts B–E) Rule 110 genuinely running on the survivor-window UWCA (per-coordinate prime alphabets, clopen penalty, deterministic sweep with local-determinism assertion) and on the P1–P4 register rails, compared cell-exactly against an independent native Rule 110 | 48,441 cell-steps verified, zero mismatches; regenerates `scripts/uwca_rule110_sidebyside.png` (the chapter's side-by-side figure), `scripts/uwca_rule110_verification.json`, and `scripts/gte_uwca_trace.csv`. Runtime < 1 s; Python 3.9+, no external packages |

Run from the paper directory: `python3 scripts/UGP_GTE_UWCA_rule.py`.

## Worked mass example (Particles chapter, §From N-Values to Masses)

The step-by-step lepton computation uses the canonical P01 verification
pipeline: `papers/01_SM/canonical_run/UGP_GTE_SM_Verifier.py` (class
`InformationMassTransformer`). The locked UCL coefficient vector, the base
energies E_base(73,1) = 0.4585 MeV / E_base(42,2) = 110.95 MeV /
E_base(275,3) = 6534.09 MeV, and the per-lepton calibration factors printed in
the chapter are reproduced by the verifier's dual-path mode:
`python3 UGP_GTE_SM_Verifier.py --n 10 --mode phys --quiet --coeffs-source empirical --run-dual-path`
(see P01 `REPRODUCE.md` for the full mode table). The theoretical-path table
values (0.513 / 105.9 / 1771 MeV, RMS 0.293%) are the locked canonical
benchmark recorded in P01.

## Foundational critique verification (`scripts/alpha_functional_form_and_param_counting.py`)

Two independent adversarial-critique computations. Run from the paper directory:
`python3 scripts/alpha_functional_form_and_param_counting.py`

### (A) α functional-form null test

Pre-registered grammar: all unary+binary combinations of the GTE-fixed atoms {7, 3}
with optional integer offset k ∈ [−12, 12]. 3675 (form, k) combinations enumerated.

| Criterion | Result |
|-----------|--------|
| Total forms enumerated | 3675 |
| Zero-offset (k=0) hits on 137 | **1**: 137 = 2⁷ + 3² |
| Offset-required (k≠0) hits | 7 |
| Distinct values in [100,175] reachable with k=0 | 12 of 76 |

The grammar is sparse at k=0; 137 is the unique zero-offset outcome. The absence of
any integer offset in 2⁷+3² is the decisive structural fact — not the value 137 alone.

### (B) Out-of-sample two-part MDL code (parameter counting)

GTE polynomial specification: K = 19 bits. Charitably conceding the entire fermion
sector as "training data" (all 19 bits), the same specification independently reproduces:

| Observable | Prediction | Measurement | Evidence (bits) |
|------------|------------|-------------|-----------------|
| n_s (CMB tilt) | 0.96488 | 0.9649 ± 0.0042 | 3.57 |
| η_B (baryon asymmetry) | 6.109×10⁻¹⁰ | 6.10×10⁻¹⁰ ± 4×10⁻¹² | 9.04 |
| sin²θ_W = 3/13 | 0.23077 | 0.23121 ± 0.0006 | 9.70 |

Robust total (n_s + η_B + sin²θ_W, θ_QCD discarded as prior-sensitive): **22.32 bits**,
exceeding the 19-bit budget by 3.32 bits (~10:1 odds against chance matching).
The out-of-sample information exceeds the total specification cost — the agreement
cannot be post-hoc fitting.

## Key results by section

| Section | Result | Script | Module |
|---------|--------|--------|--------|
| §1.4 | Goodness-of-fit statistics | — | — |
| Mathematical Substrate ch. | UWCA implements Rule 110; GTE compiles to a UWCA program | `scripts/UGP_GTE_UWCA_rule.py` | `Universality/UWCASimulation.lean`, `Universality/UWCAembedsRule110.lean`, `Universality/GTECompilation.lean` |
| Selection ch. (lift) | Direct-Interpolation Lift; sparsity floor; chirality census; parity-projection forcing | `papers/49_gte_polynomial_wolfram/scripts/triangle_lift_theorem.py`, `triangle_residual_tests.py`, `parity_projection_*.py` | `Universality/TriangleLiftTheorem.lean`, `Universality/TriangleLiftStructural.lean`, `Universality/ParityProjectionForcing.lean` |
| One Field ch. (lattice dictionary) | Tape saturation / physical point (conditional) | `papers/50_spin7_lattice/scripts/` | `Physics/CMCAPhysicalPoint.lean`, `Polynomial/SpinSevenWallSpectroscopy.lean` |
| §3.4 | Z₅ GF(5) no-kink exhaustive check | — | `MDLDerivabilityCriterion.lean` |
| §5.6 | Pion mass m_π = 139.57 MeV | `papers/35_gte_unification/scripts/` | `PionMassFromGOR.lean` |
| §5.6 | ω mass m_ω = 783.55 MeV | — | `MesonMasses.lean` |
| §6.2 | Weinberg angle sin²θ_W = 0.231207 | `papers/31_weinberg_angle/scripts/` | `WeinbergAngleMDL.lean` |
| §6.8 | 1/α_em = 137 | — | `AlphaEMStructuralIdentity.lean` |
| §7.3 | G_N from m_τ²/M_Pl² | — | `PMDLGravityTheorems.lean` |
| §8.3 | Born rule | — | `BornRuleMDL.lean` |
| §9.2 | Ω_Λ Route 1 = 0.6899 | `papers/47_gte_cosmology/scripts/` | `PSCEpochSelection.lean` |
| §9.2 | Ω_Λ Route 2 = 3π/14 = 0.6732 | `papers/45_three_tape_cmca/scripts/cc_temporal_voxel_formula.py` | `TemporalVoxelCC.lean` |
| §9.3 | n_s = 0.96488 | — | `CMBSpectralTilt.lean` |
| §9.4 | δ_CP = 68.51° | `papers/18_koide_cyclotomic/scripts/gte_cp_phase_final.py` | `CKMCPPhase.lean` |
| §9.5 | η_B = 6.109×10⁻¹⁰ | `papers/47_gte_cosmology/scripts/eta_b_full_chain.py` | FKTT Lean chain |
| §9.6 | Σm_ν = 59.4 meV | `papers/21_neutrino_masses/scripts/neutrino_mass_prediction.py` | — |
| Ch. 4 | Master quadratic / three completions | `papers/49_gte_polynomial_wolfram/scripts/` | `Polynomial/GoldenQuadratic.lean`, `Polynomial/DynamicalZeta.lean` |
| Ch. 4 | Cyclotomic identity web / Eisenstein model | `papers/49_gte_polynomial_wolfram/scripts/` | `Polynomial/EisensteinIdentities.lean`, `Polynomial/BiquadraticCompositum.lean` |
| Ch. 10 | Z₇ defect cosmology (T_G, bias, k* = 0, relics) | `papers/47_gte_cosmology/scripts/z7_domain_wall_*.py` | `Physics/ZSevenVacuumSelection.lean` |
| Ch. 10 | CC two-sided bracket / N_gen orientation exclusion | `papers/47_gte_cosmology/scripts/cc_*.py`, `ngen_bracket_orientation_family.py` | `CCOneJumpResidual.lean`, `NgenBracketOrientation.lean` |
| Ch. 9/13 | Adjudication degree 0′ | `papers/51_polynomial_transputation/scripts/` | nems-lean `Diagonal/*`, transputation-lean `Theorems/DiagonalDegree.lean` |
| Ch. 7 | Λ_GTE = 7·M_kink envelope | `papers/39_qcd_from_gte/scripts/lambda_gte_band_*.py` | — |
| Ch. 7 | Kink broadening b = 1.189 / Δα_kink | `papers/42_phimdl_field/scripts/kink_form_factor_*.py` | `Physics/KinkFormFactor.lean` |

## Lean build

The central derivations are certified in `ugp-lean` (primary library). Build with `lake build`
from the `ugp-lean` repository root; a clean build exits 0 with zero `sorry`
on all cited theorems.

A small number of theorems are in companion repositories, labeled at each occurrence in the paper:

- `nems-lean` — PSC trichotomy (`nems_trichotomy`) and `PSC_and_choice_force_PT`
- `rule110-lean` — Rule 110 Turing universality (`rule110_turing_universal_algebraic`, `rule110_center1_is_nand`)
- `transputation-lean` — internal adjudication forcing theorem

Key modules:

- `UgpLean/Universality/AlgebraicUniversality.lean` — Rule 110 / T96-02
- `UgpLean/MDL/MDLDerivabilityCriterion.lean` — T96-02 master closure
- `UgpLean/ContinuumLimit/AlgebraicNecessityTheorem.lean` — Φ_MDL uniqueness
- `UgpLean/Particles/GUTStructure.lean` — SM gauge group from Z₇×Z₃
- `UgpLean/Particles/BaryonNumber.lean` — baryon number as topological charge
- `UgpLean/Forces/ColorConfinementMDL.lean` — confinement from MDL
- `UgpLean/Forces/AlphaEMStructuralIdentity.lean` — 1/α_em = 137 (CatAL)
- `UgpLean/Forces/CasimirB0Relation.lean` — b₀ = 7 (CatAL)
- `UgpLean/Forces/MesonMasses.lean` — m_ω (CatAL)
- `UgpLean/Particles/PionMassFromGOR.lean` — m_π (CatAL)
- `UgpLean/Gravity/PMDLGravityTheorems.lean` — kink mass, Newton's constant
- `UgpLean/Gravity/GorardRicciFlatVacuum.lean` — C_Gorard = 3/32
- `UgpLean/Spacetime/VacuumGHConvergence.lean` — `vacuum_cmca_gh_converges_to_flat_space` (CatAL, zero sorry): vacuum spatial GH → flat ℝ³
- `UgpLean/Spacetime/MatterGHPrecompactness.lean` — `finGrid_family_totally_bounded`, `single_kink_gh_converges_to_flat` (both CatAL, zero sorry)
- `UgpLean/QM/BornRuleMDL.lean` — Born rule (CatAL unconditional)
- `UgpLean/QM/TransputationStateSelector.lean` — transputation forcing chain
- `UgpLean/Gravity/PSCEpochSelection.lean` — Ω_Λ = 0.6899 (D_res route)
- `UgpLean/Gravity/TemporalVoxelCC.lean` — Ω_Λ = 3π/14
- `UgpLean/Gravity/CMBSpectralTilt.lean` — n_s = 0.96488 (14 theorems)
- `UgpLean/MassRelations/CKMCPPhase.lean` — δ_CP = 68.51°
