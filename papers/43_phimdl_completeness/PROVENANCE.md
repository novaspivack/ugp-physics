# P43 — PROVENANCE

**Paper:** The Complete Φ_MDL Framework: Quantum Mechanics, Emergent Gravity,
and Non-perturbative Quantum Gravity
**Status:** Updated 2026-05-26 (comprehensive EPIC_076 QGR expansion)
**Created:** 2026-05-26
**Primary author:** Nova Spivack

## Summary of EPIC_076 additions (2026-05-26)

Building on EPIC_075 semiclassical gravity (G derived at CatAD), EPIC_076 added:

- **M2 (CatAD):** Graviton Fock space H_phys = H_Φ_MDL ⊗ H_grav; GTE coupling
  constants α_g = 5.65×10⁻⁴⁰, κ = 5.81×10⁻²² MeV⁻¹; kink gravitational
  lifetime τ_grav ≈ 4×10¹⁵ s >> t_Hubble.
- **M3 (CatAD, two routes):** S_BH = A/(4G) via (a) domain wall tension and
  (b) Wald entropy theorem on MDL-forced EH action; factor chain derivation;
  1/4 explained by EH normalization, not microstate counting.
- **M4 (CatAL, zero axioms):** Geodesic theorem for timelike worldlines:
  `psc_orbit_is_curvature_geodesic` and `tau_c_prefers_geodesic` (zero sorry,
  zero custom axioms) — timelike sector complete.
- **M5 (CatAD):** Planck-scale EFT: M_Pl^GTE = 1.2204×10¹⁹ GeV (0.040%);
  running α_g table across all scales; graviton-QCD crossover at 0.343 M_Pl.
- **NPG-Planck (CatAD/CatA):** Three convergences at M_Pl (ε₀=1, α_g=1,
  λ=l_Pl); σ(gg→gg) = l_Pl²; non-perturbative S-matrix finite and unitary.
- **Path integral (CatA):** Z_GTE = ∫DΦ exp(iS_Φ+iS_EH[g[Φ]]); UV-finite;
  conformal-factor-free (Z₇-compact field space).
- **QBH (CatAD/CatA):** M_BH_min = M_Pl/√2 = 8.630×10²¹ MeV; S(M_Pl) = 4π;
  S(M_BH_min) = 2π; T_H^max = √2 M_Pl/(8π) = 6.867×10²⁰ MeV; CMCA
  singularity resolution; P⊤ information recovery.

## Principal theorems certified in ugp-lean

All theorems are in the `ugp-lean` canonical Lean 4 repository.

### No-CA-replica / Continuum limit (CMCAContinuumLimit.lean)
- `no_finite_ca_exact_lorentz_replica` — ε₀(M) = π²/(3M²) > 0 (zero sorry)
- `phimdl_is_unique_exact_lorentz_model` — Φ_MDL is unique zero-error limit (zero sorry)

### No Class-4 outer-totalistic Z₇ CA (NoClass4OuterTotalisticZ7.lean)
- `outer_totalistic_is_reflection_invariant` — zero sorry
- `no_class4_outer_totalistic_z7_3d` — zero sorry (1 physics axiom)
- `outer_totalistic_z7_vn6_rule_space_card` — zero sorry

### QCA winding coin impossibility (WindingCoinDecoupling.lean)
- `commutes_with_winding_iff_diagonal` — zero sorry
- `diagonal_coin_decouples_sectors` — zero sorry
- `phimdl_domain_wall_junction_tension_exact` — λ_dim = −16/49 (zero sorry)

### Born rule and thermal state
- `born_rule_unconditional` — zero sorry, zero custom axioms
- `phimdl_thermal_state_master` — 277 lines, zero sorry, zero custom axioms

### QEC stabilizer
- `dweight_qec_stabilizer_bundle` — zero sorry
- `dweight_qec_stabilizer_bundle_substrate` — zero sorry

### Stress-energy tensor and gravity (StressEnergyTensor.lean)
- `phimdl_tmunu_symmetric` — zero sorry
- `phimdl_tmunu_vacuum_zero` — zero sorry
- `phimdl_gravity_sector_prerequisites` — zero sorry

### Geodesics (GeodesicTheorem.lean)
- `causal_sequence_exists` — zero sorry
- `geodesic_preferred_direction` — zero sorry
- `tau_c_prefers_geodesic` — zero sorry (EPIC_076 Pass 9)
- `psc_orbit_is_curvature_geodesic` — zero sorry, zero custom axioms (EPIC_076 Pass 8)
  Status: timelike worldline geodesic theorem COMPLETE at CatAL, zero axioms

### β-function and hierarchy (BetaCoefficientIdentity.lean, FrobeniusPrimeIdentity.lean)
- `b0_eq_z7_order` — (11·3 − 2·6)/3 = 7 = |Z₇| (zero sorry)
- `gte_beta_coefficient_bundle` — zero sorry
- `gte_planck_cascade_group_identity` — zero sorry
- `frobenius_prime_condition` — |Z₇| = |Z₃|²−|Z₃|+1 iff orbit identity (zero sorry)

### Algebraic necessity (AlgebraicNecessityTheorem.lean)
- `algebraic_necessity_master_bundle` — zero sorry
- `f21_unique_nonabelian_order_21_numeric` — zero sorry
- `b0_uniquely_forces_n7` — zero sorry

## Key numerical results

- M_kink = 290.10 MeV (relative error 1.4×10⁻⁶)
- λ(step_fmdl3d) = 0.8575 ≈ 6/7 (823,543 inputs)
- No Class-4 hits: 510 trials, λ_c ≈ 0.54 ± 0.04
- M_Pl/m_τ = 21^10 × 7^7 / 2 at 0.040% (all components GTE-derived, CatAD)
- G_N = m_τ²/M_Pl² = 6.714×10⁻⁴⁵ MeV⁻² (CatAD)
- α_g = (M_kink/M_Pl)² = 5.65×10⁻⁴⁰ (CatAD)
- h₀₀(1 fm) = 1.54×10⁻³⁹ (linearized gravity regime confirmed)
- τ_grav ≈ 4×10¹⁵ s >> t_Hubble (kinks gravitationally stable)
- S_BH(M☉) = 1.050×10⁷⁷; r_S(M☉) = 2956.5 m (0.12% from PDG)
- S_BH(M_Pl) = 4π (exact); S_BH(M_BH_min) = 2π (exact)
- T_H^max = √2 M_Pl/(8π) = 6.867×10²⁰ MeV (exact)
- Wald factor chain: −2π × (−4)/(2×16π) = 0.250000 = 1/4 (exact)
- M_BH_min = M_Pl/√2 = 8.630×10²¹ MeV (CatAD)
- Λ = (ln2/π) · L_model · H₀²/c² at 0.31σ (P01, independent)

## Companion papers

- P41 (SpivackCMCA): Three-Layer Chiral Minkowski CA
- P42 (SpivackPhiMDLField): Φ_MDL field, Born rule, continuum completion
- P38 (SpivackPhiMDLGravity): Emergent gravity from Φ_MDL
- P34 (SpivackGTEMobius): GTE-Möbius substrate, transputation
- P36 (SpivackEmergentGravity): Rule 110 emergent gravity
- P37 (SpivackQMFromR110): QM from Rule 110
- P01 (Spivack2026_SM_UGP): SM from UGP (cosmological constant formula)
- P16 (SpivackBHUnitarity): BH reflexive unitarity and P⊤ information recovery
