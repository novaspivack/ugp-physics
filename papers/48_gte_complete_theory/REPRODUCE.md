# Reproducing P48 Results

This monograph assembles derivations from P01–P47. All numerical predictions
are reproducible by running the scripts in the cited source papers. The central
algebraic steps are machine-checked in the canonical `ugp-lean` library.

## Key results by section

| Section | Result | Script | Module |
|---------|--------|--------|--------|
| §1.4 | Goodness-of-fit statistics | — | — |
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
- `UgpLean/QM/BornRuleMDL.lean` — Born rule (CatAL unconditional)
- `UgpLean/QM/TransputationStateSelector.lean` — transputation forcing chain
- `UgpLean/Gravity/PSCEpochSelection.lean` — Ω_Λ = 0.6899 (D_res route)
- `UgpLean/Gravity/TemporalVoxelCC.lean` — Ω_Λ = 3π/14
- `UgpLean/Gravity/CMBSpectralTilt.lean` — n_s = 0.96488 (14 theorems)
- `UgpLean/MassRelations/CKMCPPhase.lean` — δ_CP = 68.51°
