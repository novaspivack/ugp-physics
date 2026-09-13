# PROVENANCE — P41 — Three-Layer Chiral Minkowski CA

**Paper:** P41 — Three-Layer Chiral Minkowski CA (CMCA)  
**Date:** 2026-05-25  
**Author:** Nova Spivack

---

## Derivation Record

| Result | Script / Lean | Status |
|--------|---------------|--------|
| Rule 124 chiral mirror pair | `epic073_rank070_106_rule124_chiral_verification.py`; `ChiralMirrorSpeedSymmetry.lean` | CatA |
| Orbit depth = ether period = 7 | `epic073_rank070_110_orbit_depth_ether_period.py`; `OrbitDepthEtherPeriod.lean` | CatAL |
| Ether-phase C2 nucleation | `epic073_rank070_113_ether_phase_c2_nucleation.py` | CatA |
| Multi-cell injection loophole | `epic073_rank070_135_multicell_injection.py` | CatA |
| Multi-cell bypass grammar | `epic073_rank070_136_multicell_bypass_grammar.py` | CatA |
| Cross-layer failure mechanism | `cross_layer_failure_analysis.py` | CatA |
| Dynamical coupling bridge | `epic073_rank070_122_dynamical_coupling_bridge.py`; `DynamicalCouplingBridge.lean` | CatAD / CatAL partial |
| Excitation-level coupling | `excitation_level_coupling_formalism.py`; `ExcitationCoupling.lean` | CatAD |
| Generation orbit survival | `epic073_rank070_141_generation_orbit_two_layer.py` | CatA |
| KG dispersion Lorentz invariance | `epic073_lor1_kg_dispersion_lorentz.py`; `LorentzInvariance.lean` | CatAD / CatAL |
| CA–continuum Lorentz bridge | `continuum_limit_lorentz_bridge.py` | CatAD |
| Planck-scale Lorentz violation | `planck_scale_lorentz_prediction.py` | CatAD |
| Double-slit interference | `dslit_gte_interference.py` | CatA |
| Sync vs async three-layer SR dilation | `sync_vs_async_three_layer.py` | CatA |
| PSC/PI → [D] Lorentz equivariance | `PSCPILorentzMain.lean` | CatAL |
| OR curvature static κ | cross-ref P38 `dcg_or_static_kappa_round4.py` | CatA |

**Graduated:** 15 scripts → `papers/41_three_layer_chiral_minkowski_ca/scripts/` (2026-05-25 / 2026-05-31).

---

## Supplementary Results (2026-05-26)

| Result | Script / Lean | Status |
|--------|---------------|--------|
| Explicit CMCA→Φ_MDL descent map | `cmca_algebraic_descent.py`; RMSD=5.34%<ε₀(7)=6.71%; r=0.994; Q=1/7 | CatA |
| No finite-CA exact Lorentz replica | `CMCAContinuumLimit.lean`: `no_finite_ca_exact_lorentz_replica` | CatAL (zero sorry) |
| Unique exact Lorentz limit | `CMCAContinuumLimit.lean`: `phimdl_is_unique_exact_lorentz_model` | CatAL (zero sorry) |
| 2+1D discrete pair excluded | 4 rule variants, ~330 IC, T=1000; zero persistent gliders | CatA |
| Holographic structure | Continuum Φ_MDL domain walls (σ=290.10 MeV/fm²) | CatAD |
| 3+1D λ=0.8575≈6/7 saturation | All 7^7=823543 configs checked; uniform output distribution | CatA |
| No Class-4 outer-totalistic (510 trials) | `cmca_3d_lambda_search.py`, `cmca_3d_lambda_refined.py`; zero hits | CatA |
| Outer-totalistic not chiral (Lean) | `NoClass4OuterTotalisticZ7.lean`: `outer_totalistic_is_reflection_invariant` | CatAL (zero sorry) |
| No Class-4 outer-totalistic (Lean) | `NoClass4OuterTotalisticZ7.lean`: `no_class4_outer_totalistic_z7_3d` | CatAL (1 axiom) |
| Dimensional dissipation staircase | 1+1D persistent → 2+1D transient → 3+1D bifurcation | CatA |

**Newly graduated scripts (2026-05-26):**
- `cmca_algebraic_descent.py` → `papers/41_three_layer_chiral_minkowski_ca/scripts/`
- `cmca_full_reproducibility.py` → `papers/41_three_layer_chiral_minkowski_ca/scripts/`
- `cmca_spectral_dim_1d_v2.py` → `papers/41_three_layer_chiral_minkowski_ca/scripts/`
- `cmca_full_reproducibility_wolfram_version.wl` → `papers/41_three_layer_chiral_minkowski_ca/scripts/`

**Paper status:** Updated 2026-05-26 with dimensional staircase, no-Class-4 Lean certification, explicit descent map, and no-CA-replica theorem.

---

*PROVENANCE.md — P41 — updated 2026-05-26*
