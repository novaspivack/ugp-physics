# Reproducing P47 Results

This paper assembles cosmological predictions of the GTE/Φ_MDL framework. The
numerical results are reproduced by the scripts below; the central algebraic steps
are machine-checked in the canonical `ugp-lean` library.

## Scripts

| Script | Produces |
|---|---|
| `papers/45_three_tape_cmca/scripts/cc_temporal_voxel_formula.py` | CC coefficient 9/112 and Ω_Λ = 3π/14 = 0.6732 |
| `papers/45_three_tape_cmca/scripts/sr_ratio_measurement.py` | Proper-time rate τ measurement |
| `papers/18_koide_cyclotomic/scripts/gte_cp_phase_final.py` | δ_CP = π/2 − 3/8 = 68.51° |
| `papers/18_koide_cyclotomic/scripts/jarlskog_from_koide.py` | Jarlskog invariant J = 3.02×10⁻⁵ |
| `papers/18_koide_cyclotomic/scripts/ckm_a_parameter_gte.py` | Wolfenstein A = sin(π/3) |
| `papers/21_neutrino_masses/scripts/neutrino_mass_prediction.py` | m_ν₁ = 0.679 meV, Σm_ν = 59.4 meV |
| `papers/21_neutrino_masses/scripts/gte_leptogenesis.py` | Leptogenesis efficiency K₁ = 15.93 |

Run any script with `python3 <path>`; results are written to the adjacent
`*_results.json` file.

## EPIC_083 additions (2026-05-31): CC ratio formula and N_gen=3 uniqueness

The ratio between the two structural Ω_Λ routes is now derived in closed GTE-atom form
(CatAD; G02 session, all results reproducible from formulas in §cc-range):

```python
import math

# GTE atoms
D, N_fam, N_gen, Z7 = 4, 5, 3, 7

# Route 1 (PSC epoch, §cc-dres)
Omega_PSC  = (math.log(2) / (N_gen * math.pi)) * math.log2(D**2 * N_fam**3 / N_gen)
# Route 2 (holographic mode count, §cc-voxel)
Omega_holo = (N_gen / Z7) * (math.pi / 2)

ratio = Omega_PSC / Omega_holo
# Closed form: 14 * ln(2000/3) / (9 * pi^2)
ratio_formula = 2 * Z7 * math.log(D**2 * N_fam**3 / N_gen) / (N_gen**2 * math.pi**2)

print(f"Omega_PSC  = {Omega_PSC:.6f}")    # 0.689914
print(f"Omega_holo = {Omega_holo:.6f}")   # 0.673198
print(f"Ratio      = {ratio:.6f}")        # 1.024831
print(f"Formula    = {ratio_formula:.6f}") # 1.024831 (should match)
print(f"2000/3     = D^2 * N_fam^3 / N_gen = {D**2 * N_fam**3} / {N_gen}")  # 2000/3
```

**N_gen=3 uniqueness:** For all integers N ≠ 3, at least one route deviates from
Planck 2018 (Ω_Λ = 0.6889 ± 0.0056) by more than 5σ. At N=3 the PSC route gives
+0.18σ and the holographic route gives −2.80σ. The continuous minimum of the route
spread function lies at N=3.034; the nearest integer is N=3 (PSC-selected independently
by the Two-Layer PSC Theorem).

```python
# Verify N_gen=3 uniqueness
Planck, sigma = 0.6889, 0.0056
for N in range(1, 8):
    op = (math.log(2) / (N * math.pi)) * math.log2(D**2 * N_fam**3 / N)
    oh = (N / Z7) * (math.pi / 2)
    both_ok = abs(op - Planck) < 5*sigma and abs(oh - Planck) < 5*sigma
    print(f"N={N}: PSC={op:.4f} ({(op-Planck)/sigma:+.1f}s) "
          f"holo={oh:.4f} ({(oh-Planck)/sigma:+.1f}s) both<5s: {both_ok}")
# Only N=3 prints True
```

## 083D additions (2026-06-04): Φ_MDL kink-top coupling and η_B

New script graduated from research-sandbox:

| Script | Produces |
|---|---|
| `papers/47_gte_cosmology/scripts/eta_b_full_chain.py` | Full η_B derivation chain; FKTT mechanism: η_B = 6.109×10⁻¹⁰ (+0.15σ from PDG, CatAL) |

Run with `python3 papers/47_gte_cosmology/scripts/eta_b_full_chain.py` from the repo root.
Results written to `papers/47_gte_cosmology/scripts/eta_b_full_chain_results.json`.

Mechanism: The right-handed neutrino N₁ is a Φ_MDL kink excitation (P42/P43). Its Dirac
Yukawa RGE at M_GUT uses g_kink-top = exp(−π/N_c) = ε_FN (Q=1 BPS instanton, CatAL)
rather than y_t_phys = 0.461. Physical top mass m_t = 172.61 GeV (CatAD) is unaffected.

---

## Lean build

The central derivations are certified in `ugp-lean`. Relevant modules:

- `UgpLean/Gravity/PSCEpochSelection.lean` — Ω_Λ = 0.6899 (D_res route)
- `UgpLean/Gravity/TemporalVoxelCC.lean` — Ω_Λ = 3π/14, holographic mode count, NRT
- `UgpLean/Gravity/EtherProperTimeRate.lean` — τ = 3/7 from Rule-110 ether
- `UgpLean/Gravity/CMBSpectralTilt.lean` — n_s = 1 − ln2/(2π²) (14 theorems)
- `UgpLean/ContinuumLimit/GorardRationalFormula.lean` — κ_SD = 10/13, Gorard chain
- `UgpLean/Gravity/GorardRicciFlatVacuum.lean` — C_Gorard = 3/32, superselection
- `UgpLean/Gravity/PMDLGravityTheorems.lean` — kink mass, Hawking emission, V_max
- `UgpLean/Gravity/NRTVacuumEnergy.lean` — Z₇ vacuum energy mass independence
- `UgpLean/MassRelations/CKMCPPhase.lean` — δ_CP, Jarlskog, A parameter

New in this version (2026-06-01):
- `UgpLean/Gravity/Z7AnomalyFree.lean` — Z₇ global scalar symmetry anomaly-free (4 theorems, zero sorry): `z7_global_scalar_anomaly_free`, `z7_shift_measure_preserving`, `z7_jacobian_eq_one`, `z7_vacuum_sectors_equiprobable`
- `UgpLean/ContinuumLimit/GorardVacuumW1Bridge.lean` — W₁=1 for vacuum measures, κ=0 ∀ adjacent edges (zero sorry): `gorard_vacuum_oric_zero_scoped`, `vacuum_w1_eq_one`, `W1_ge_of_lipschitz`
- `UgpLean/ContinuumLimit/WassersteinDistance.lean` — W₁ Wasserstein distance (fully proved, zero sorry): `W1_nonneg`, `W1_triangle`, `W1_eq_zero_iff`, `W1_attained`, `couplingCostSet_isCompact`

Build with `lake build` from the `ugp-lean` repository root; a clean build exits 0
with zero `sorry` on the cited theorems.

## Additional Lean certificates

| Theorem | Module | Commit | Statement |
|---|---|---|---|
| `incompleteness_implies_nonzero_omega_lambda` | `UgpLean/Gravity/PSCEpochSelection.lean` | `63c015b` | PSC incompleteness → D_res>0 → Ω_Λ>0 |
| `psc_enumeration_forces_ngen_3` | `UgpLean/TE22/ScanCertificate.lean` | `63c015b` | All 34,560 PSC survivors have N_gen=3 |

## 083C additions (2026-06-02): H₀, η_B, and PMNS cross-references

New scripts graduated from research-sandbox:

| Script | Produces |
|---|---|
| `papers/47_gte_cosmology/scripts/h0_full_first_principles.py` | H₀ = 67.95 km/s/Mpc (CatA; T_CMB sole external input) |
| `papers/47_gte_cosmology/scripts/h0_noncircular_from_tcmb.py` | Non-circular H₀ route; validates no circularity in Ω_Λ inputs |
| `papers/47_gte_cosmology/scripts/h0_combined_mechanisms.py` | η_B = 6.35×10⁻¹⁰ from kink-overlap × D_top |

| `papers/47_gte_cosmology/scripts/eta_b_exact_sech_overlap.py` | Exact sech overlap I(r) for r=5,11; verifies f₁×f₂ vs asymptotic 1/3025 approximation |

New Lean certificates:
- `UgpLean/Gravity/YukawaOverlapExponent.lean` — `leptogenesis_kink_overlap_catad` (CatAD, zero sorry): η_B from sech-overlap exponent α=N_c−1=2

PMNS angles: see `papers/21_neutrino_masses/scripts/pmns_orbit_ratio_final.py`.

## 083D additions (2026-06-04): M_R1 Pati-Salam structural derivation

New script graduated from research-sandbox:

| Script | Produces |
|---|---|
| `papers/47_gte_cosmology/scripts/pati_salam_scale_derivation.py` | M_{R,1} = 1.1105×10¹³ GeV from three-tape BPS instanton suppression (CatA; eq. MR1_gte) |

Run with `python3 papers/47_gte_cosmology/scripts/pati_salam_scale_derivation.py` from the repo root.
Results written to `papers/47_gte_cosmology/scripts/pati_salam_scale_derivation_results.json`.

Structural formula: M_{R,1} = M_R × exp(−π) / (19/5)^{29/9} = 1.1105×10¹³ GeV (0.04% from calibrated).
Components: M_R = 1.90×10¹⁶ GeV (CatA, P21); exp(−π) = ε_FN^{N_c} (CatA, P45 CMCA three-tape BPS);
(19/5)^{29/9} = 73.82 (CatAL, `fn_texture_gives_seesaw_exponent`).

---

## Defect-cosmology sector (§Defect Cosmology)

Scripts co-located with this paper in `papers/47_gte_cosmology/scripts/`; each
writes its `*_results.json` next to itself. Run with `python3 <path>` from the
repo root.

| Script | Produces |
|---|---|
| `z7_domain_wall_tension_consistency.py` | σ = 0.29010 GeV³ (BPS cross-check), T_G ≈ 0.70 GeV, Friedmann domination solve z_dom = 832, anisotropy-bound factors, frozen-network variant |
| `z7_domain_wall_kibble_foam.py` | 3D Kibble foam statistics, winding inventory (91% adjacent-vacuum), percolation, biased-vs-unbiased relaxation |
| `z7_domain_wall_winding_vs_vacuum_category.py` | Winding-alphabet vs vacuum-label category check; Z₃-orbit transversal |
| `z7_domain_wall_gauge_orbit_species_check.py` | Gauged-discrete escape ruled out (species collapse under ⟨×2⟩ orbits) |
| `z7_domain_wall_bias_annihilation.py` | Z_k normalizations, one-loop ΔF brackets (3 estimators × 5 masses), R_c, T_ann, clearances, GW ceiling, ΔN_eff |
| `z7_vacuum_selection_one_loop_direction.py` | One-loop vacuum-label splitting direction (fixed-μ scheme-sensitivity record) |
| `z7_vacuum_selection_physical_scheme_direction.py` | Decoupling-scheme direction with analytic anchors |
| `vacuum_selection_rg_improved_direction.py` | RG-improved Λ_GTE-anchored V_eff: 32-config factorial core, probe battery, critical-boundary finder, k* = 0 (ROBUST) |
| `vacuum_selection_rg_defect_numbers.py` | Final defect numbers: \|ΔV\| = 3.8×10⁻² GeV⁴, R_c = 7.7 GeV⁻¹, lifetime 5×10⁻²⁴ s, T_ann ≈ 0.70 GeV, ×700 BBN clearance, Ω_GW h² ≲ 3×10⁻⁴⁷, ΔN_eff ≈ 0 (reads `vacuum_selection_rg_improved_direction_results.json`; run that first) |

## CC bracket theorem and computability sector (§cc-dres, §cc-range)

| Script | Produces |
|---|---|
| `cc_floor_orientation_arithmetic.py` | GTE-atom inequality 14ln(2000/3) > 9π² at 50-digit precision; closed-form margin 0.016716; equivalence web; finite rational witness; measurement-absence audit |
| `cc_bracket_dres_consistency.py` | Planck strict interiority (both conventions); unresolved capacity fraction 2.42%; N-scan + orientation flip; precision horizon σ* = 3.381×10⁻⁴ |
| `cc_two_route_ngen_scan_canonical.py` | Canonical two-route N-scan: N = 3 anchors exact to 10⁻¹⁵; N = 1..11 table; continuous spread minimum N* = 3.034 |
| `ngen_bracket_orientation_family.py` | 16-variant ansatz family: admissible = {1,2,3} in every variant; closed-form boundary N* = 3.037018; separation certificate for all N ≥ 4; adversarial-alphabet thresholds |
| `cc_floor_ledger_decomposition_model.py` | Carrier–record decomposition certificates: floor ≤ Ω(R) ≤ census over all 65,536 realized subsets; load-bearing premise nulls; realized fraction 0.9393 at Planck (a-posteriori) |
| `pmdl_carrier_zero_point_evaluation.py` | Exact carrier coefficient chain N²/(D²·\|Z₇\|) = 9/112, Ω = 3π/14 at 10⁻⁵¹; suppression exponent −2 exact; pricing-gap and mode-count nulls |
| `d_res_left_ce_degree_certificate.py` | Left-c.e. monotone approximation; decode-from-value 48/48 (explicit RT ≤_T D_res reduction, exact arithmetic); convergence stage = max halting time; closed-form exclusion shadow |

Lean certificates for this sector (canonical `ugp-lean` modules): `CCOneJumpResidual`
(`omega_lambda_bracket_strict`, `bracket_strict_interiority`,
`no_computable_gte_rt_convergence_modulus`, `sigma_star_falsifiability_horizon`),
`NgenBracketOrientation` (`cc_floor_orientation_atom_inequality`,
`ngen_bracket_orientation_flip`, `ngen_pincer_from_layer1_and_orientation`),
`ZSevenVacuumSelection` (`vcoupling_breaks_z7_shift`,
`z7_vacua_chi_kinetic_inequivalent`, `wall_bias_minimum_unique`,
`compact_completion_minimum_at_k0`, `scalar_cw_step_inward`).

---

## 083D additions (2026-06-03): DESI w_a = 0 falsification analysis

New script graduated from research-sandbox:

| Script | Produces |
|---|---|
| `papers/47_gte_cosmology/scripts/desi_w_analysis.py` | Five-mechanism analysis confirming w = -1 is PSC-locked; all δw < 10⁻⁴⁰; DESI Y1 tension 0.33σ (w₀), 1.33σ (w_a); falsification thresholds |w₀+1| > 0.040 at 5σ and |w_a| > 0.45 at 5σ (Euclid projected) |

Run with `python3 papers/47_gte_cosmology/scripts/desi_w_analysis.py` from the repo root.
Results written to `desi_w_analysis_results.json` in the working directory.
