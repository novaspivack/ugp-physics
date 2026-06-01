# Provenance

## Primary data sources

| Artifact | Path | SHA-256 |
|----------|------|---------|
| TE2.2 scan results | `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/phase2_scan_results.json` | `f810c1d2b07b598ef301205fee53512310552ea78cf8fb7476b3e9058d5fde93` |
| TE2.2 scan entry point | `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/src/phase2_truncation/te2_2_run_scan.py` | — |
| Constraint modules | `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/src/phase1_constraints/` | — |

Date of canonical TE2.2 run: **2025-11-20**

## Formal sources (cited, not re-derived)

| Paper | Role in this paper | DOI / archive |
|-------|--------------------|---------------|
| Paper 03 (SpivackNMstar) | PSC Exclusions Theorem: GUT groups, vector-like fermions, CP-conserving theories excluded | DOI: 10.5281/zenodo.19429717 |
| Paper 05 (SpivackPSCOpt) | Two-Layer PSC Theorem: Layer I forces G_SM and N_gen ≥ 3; Layer II selects N_gen = 3 | DOI: 10.5281/zenodo.19429721 |
| Paper 20 (SpivackGaugeRigidity) | PSC Sieve definition; Lean 4 formalization of all sieve constraints | DOI: 10.5281/zenodo.19575045 |
| Paper 21 (SpivackExistentialRigidity) | Existential Rigidity Theorem: SM is the only ontologically legal foundation for a PSC universe (now unconditional: RCC proved as PSC.RCCInfiniteFamilies, zero sorry, ugp-lean) | DOI: 10.5281/zenodo.19429757 |

## Verified claims from the TE2.2 certificate

The following values are read directly from `phase2_scan_results.json` and reported verbatim in the paper.

| Claim | Value | Source field |
|-------|-------|--------------|
| Total universe descriptions evaluated | 20,160 | `total_universes` |
| Universes passing hard PSC filters | 12 (0.06%) | `psc_universes` |
| Standard Model dissonance D_SM | 1.066657903568035 | `D_sm` |
| Global minimum D_min | 1.066657903568035 | `D_min` |
| SM rank (by D[Ψ], ascending) | 1 | `sm_rank` |
| Global minimizer gauge group | SU(3)×SU(2)×U(1) | `global_minimizer.gauge_group` |
| Global minimizer d | 4 | `global_minimizer.d` |
| Global minimizer N_gen | 3 | `global_minimizer.n_generations` |
| Hessian minimum eigenvalue λ_min | 2.0 | Computed analytically in scan |
| Four co-minimizers at D_min | ρ ∈ {1.13, 1.5}, τ ∈ {flat, hyperbolic} | `top_10` entries |

## Caveats and limitations

The following are explicit caveats acknowledged in the paper and required for correct interpretation.

1. **Discretization**: The TE2.2 scan is a finite exhaustive enumeration over a discrete parameter grid. It constitutes a computational certificate over exactly the 20,160 enumerated descriptions, not a proof over the full continuum of theories.

2. **C_2/C_3/C_5/C_9/C_11 partial prior**: Five of fourteen constraint terms are SM-targeted to varying degrees. C_2 (SRRG Fixed Point) and C_3 (SRRG Viability) encode the SRRG fixed-point result. C_5 (RG Flow Stability) uses `is_sm_like()` directly — it does not compute RG flow for each gauge group, and does not check the SM's U(1) Landau pole. C_9 (RIET Equivalence) and C_11 (Coherence Field) are MFRR-internal concepts implemented via `is_sm_like()` proxies. All five are acknowledged in §4.1 of the paper with justifications; the remaining nine constraints are independently defined.

3. **Continuum extension not machine-checked**: The analytic extension argument (density, continuity, and compactness of the PSC-admissible region for continuous parameters) is documented in the TE2.2 scan materials but has not been machine-checked in Lean 4 or any other proof assistant.

4. **RCC now proved**: Full uniqueness of the Standard Model as the only PSC-compatible theory is established by the Residual Classification Certificate (RCC), proved as `PSC.RCCInfiniteFamilies` (zero sorry, ugp-lean). The certificate combines: (a) TE2.2 finite scan of 34,560 universe descriptions; (b) extended computational certificate for 11 additional gauge groups; and (c) Lean-certified classification of all four infinite classical Lie families (B_n, C_n, D_n even, D_n odd, A_n for n≥3). SM uniqueness is now unconditional within the PSC framework.

5. **Neutrino sector out of scope**: Neither the formal programme nor the TE2.2 scan addresses Dirac vs. Majorana neutrinos, the mass hierarchy, or the CP-violating phase in the PMNS matrix.

6. **Vector-like fermion scope gap**: The formal exclusion of vector-like fermions (Paper 03) is not directly verified by the TE2.2 scan, because the scan's parameter space does not include a chirality parameter.

7. **Gauge group coverage**: The scan includes seven gauge groups. There are infinitely many compact semisimple Lie groups; the scan's numerical evidence against non-SM gauge groups is limited to those seven.

## COMP-P14-A: C14 Lambda Derivation Audit (2026-04-17)

**Question:** Was ln(φ)/ln(2π) derived from PSC axioms before being compared to Λ_obs, or was it found by targeting Λ_obs?

**Finding:** The formula is an algebraic expression that numerically equals 10⁻¹²² (Planck units). The TE_1.E programme (`MFRR/TE_1_VALIDATION_PROGRAM/TE_1.E_Lambda/`) derives Λ via a structural FRW+Ψ solver whose calibration pass explicitly computes "a global scale factor so that Λ_phys matches Λ_obs" (TE_1.E Final Validation Report, §2). The formula ln(φ)/ln(2π) is the Planck-unit algebraic expression corresponding to the calibrated value — it was identified because it matches the observation, not derived prior to it.

**Classification:** C14 is **algebraically targeted at Λ_obs**. The paper now discloses this in §3.2 and §4.1, classifying C14 as "PSC-conditional" rather than "PSC-derived in the strictest sense."

## COMP-P14-B: C5 Landau Pole Audit (2026-04-17)

**Question:** Does C5 (RG Flow Stability) correctly handle the SM's U(1) Landau pole?

**Finding:** `RGFlowStabilityConstraint.evaluate()` (file `te2_2_srrg_constraint.py`, lines 285–291) checks `universe.is_sm_like(tol=1e-3)` directly. If True, returns 0.0 (stable). If False, returns 1.0 (unstable). The implementation does not compute RG flow; it uses the SM as a shortcut justified by the SRRG TS9 97% attraction result. The SM's U(1) Landau pole is NOT evaluated — the SM receives a free pass by definition.

**Classification:** C5 implementation is **SM-tautological via is_sm_like()** and does not correctly model the SM's known U(1) UV behavior. The paper now discloses this explicitly in §4.1.

## Extended Scan (2026-04-17 Upgrade)

| Artifact | Path | SHA-256 |
|----------|------|---------|
| Extended scan results | `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/extended_scan_results.json` | `407078d74a2fe3a21d7f77d2b7252f6840e5136d7439b6286e05a0e21a9c3622` |

**Extended scan config:** 12 gauge groups (original 7 + Pati-Salam, E₆, G₂, SU(6), SU(4)); 34,560 total universes; 15 constraints (14 − C9 − C11 + C15 + C16 + C4'); 0.25s runtime

**Key new results:**
- All 5 new BSM groups fail PSC sieve: min_D = 2,192,010 vs D_SM = 1.009
- D_SM = 1.009 in extended scan (contribution: C4'=0.955, C16=0.036, C15=0.018)
- SM rank #1 out of 34,560; 12 PSC-passing universes (0.035%), all SM-like

## New Constraint Scripts (NW1-4, 2026-04-17)

| Script | Role | Notes |
|--------|------|-------|
| `src/phase1_constraints/te2_2_ugp_coupling_constraints.py` | C15, C16, C4' | UGP-derived predictions from ugp-lean rationals |
| `src/phase1_constraints/te2_2_rg_stability_principled.py` | Principled C5 | Physics-based RG stability per gauge group |
| `src/phase2_truncation/te2_2_run_scan_extended.py` | Extended scan runner | 12 groups, 15 constraints |

## Lean Certificates (2026-04-25)

Two new tree-level EW observable predictions ($C_{17}$, $C_{18}$) added to the concordance scan:

| Theorem | Module | Claim |
|---------|--------|-------|
| `sin2_theta_W_bare_eq` | `UgpLean.Phase4.GaugeCouplings` | sin²θ_W = 3456/15101 ≈ 0.2289 (tree-level); PDG 0.23121; 1.0% deviation |
| `cos2_theta_W_bare_eq` | `UgpLean.Phase4.GaugeCouplings` | cos²θ_W = complementary exact rational |
| `alpha_em_formula_exact` | `UgpLean.Phase4.GaugeCouplings` | 1/α_EM = 4π(1/g₁² + 1/g₂²) = 4π × 377525/37264 ≈ 127.31 (tree-level); PDG 127.952; 0.5% deviation |

All zero sorry. ugp-lean commits `026c955` and `19da6d2`.

---

## Lean Certificate (NW3, 2026-04-17)

| Theorem | File | Status |
|---------|------|--------|
| `ugp_coupling_predictions_are_independent` | `ugp-lean/UgpLean/TE22/ScanCertificate.lean` | ✅ 0 sorry |
| `ugp_g1g2_prediction_close_to_SM` | Same | ✅ 0 sorry |
| `SM_gauge_uniquely_selected` | Same | ✅ 0 sorry (decidable fragment: exactly one of 60 (GaugeGroup, Dimension) pairs is SM) |
| `isSMGauge_iff` | Same | ✅ 0 sorry (full logical characterization of the SM gauge label) |
| `SM_is_D_minimizer_extended` | Same | ✅ 0 sorry (alias to `isSMGauge_iff`) |
| Full SM D-minimizer over 20,160+ universes | Same | ⏳ OPEN — decidable fragment proved; full claim pending `Fintype` instance + `native_decide` |
