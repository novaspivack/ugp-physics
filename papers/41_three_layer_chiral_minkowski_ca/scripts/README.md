# P41 — Three-Layer Chiral Minkowski Cellular Automaton: Scripts

**Paper:** "The Three-Layer Chiral Minkowski Cellular Automaton" (P41, Nova Spivack, 2026)  
**DOI:** [10.5281/zenodo.20417572](https://doi.org/10.5281/zenodo.20417572)

## Overview

These scripts implement and verify the 1+1D Chiral Minkowski Cellular Automaton (CMCA): three coupled binary layers (outer_plus Rule 110, outer_minus Rule 124, inner clock Rule 110) with async-firing gating (AFCA). Together they reproduce the paper's headline claims: chiral V–A structure, glider kinematics, SR proper-time dilation, the GTE polynomial universality certificate, PSC kink-orbit substrate selection, and bridges to continuum Φ_MDL physics.

## Quick Start

```bash
cd papers/41_three_layer_chiral_minkowski_ca/scripts

# Canonical three-layer CMCA simulator + built-in verification suite
python3 two_layer_chiral_afca_prototype.py

# Full reproducibility suite (all nine headline claims + Born + double-slit)
python3 cmca_full_reproducibility.py

# Independent Wolfram cross-check (11/11 claims)
wolframscript -file cmca_full_reproducibility_wolfram_version.wl
```

Requirements: Python 3.10+, `numpy`. Wolfram Engine or Mathematica ≥ 12.0 for `.wl` scripts.

## Key Concepts

**Three-layer architecture (AFCA).** Each spatial direction carries:
- `outer_plus` (L_{x+}): Rule 110 — right-moving excitations, |v| = 2/3
- `outer_minus` (L_{x−}): Rule 124 — left-moving excitations, |v| = −2/3 (spatial mirror of Rule 110)
- `inner_clock` (L_t): Rule 110 — temporal gating clock τ_c

Outer layers update only when the inner clock completes at that cell. This async gating produces SR proper-time dilation τ_inner/τ_outer = 3/7 on the period-7 ether orbit.

**f_MDL vs. the GTE polynomial p(L,C,R).** Two distinct objects:
- `p(L,C,R) = C + R − CR − LCR` (mod 7) — algebraic certificate; on binary {0,1}³ inputs, `p mod 2 = Rule 110` exactly
- `f_MDL` — MDL-minimal lookup table: 8 binary entries (Rule 110) + 10 SM orbit neighborhoods + 0 elsewhere

They agree on binary inputs and disagree on general Z₇ triples by design. Universality uses the polynomial restriction; particle physics uses f_MDL's orbit structure.

**Ether background and translation invariance.** Rule 110 has a unique period-14 quiescent background (the "ether"). P41 uses `ETHER14 = [1,1,1,1,1,0,0,0,1,0,0,1,1,0]`; P45 uses a cyclic rotation of the same orbit. Rule 110 is translation-invariant on a periodic lattice — all physical observables (τ_c ratios, glider speeds, SR dilation) are invariant under phase choice.

## Script Reference

### Core CMCA Simulator

| File | Description | Key result |
|------|-------------|------------|
| `two_layer_chiral_afca_prototype.py` | Canonical three-layer AFCA implementation | Chirality, SR τ = 3/7, generation orbit, PSC kink search |
| `sync_vs_async_three_layer.py` | Compares sync vs. async gating | Demonstrates AFCA gating necessity for SR dilation |
| `cmca_full_reproducibility.py` | Full reproducibility suite (orchestrator) | All P41 headline claims in one run |
| `cmca_full_reproducibility_wolfram_version.wl` | Wolfram independent cross-check | 11/11 independent verifications |

### Key Verification Functions (`two_layer_chiral_afca_prototype.py`)

| Function | What it tests | Lean certificate |
|----------|---------------|------------------|
| `verify_va_structure()` | 32/125 SM-vocabulary triples mismatch R110 vs R124 | `ChiralPairVA.va_mismatch_count` |
| `verify_z7_generation_orbit()` | GEN1→GEN2→GEN3→VACUUM under f_MDL | `fmdl_gen1_to_gen2`, `fmdl_gen1_is_garden_of_eden` |
| `verify_polynomial_equals_rule110_on_binary()` | p(L,C,R) mod 2 = Rule 110 on {0,1}³ | `rule110_z7_poly_rep` |
| `verify_z7_kink_orbit_existence_and_z5_absence()` | PSC kink orbits: Z₇ = 45, Z₅ = 0 | `fmdl_gen1_to_gen2`, `z5_fmdl_no_psc_kink_orbits` |
| `verify_decoupled_coevolution_afca()` | Z₇ orbit reaches vacuum under AFCA co-evolution | — |
| `measure_tau_c_sr()` | SR proper-time dilation via inner-clock τ_c ratio | `EtherProperTimeRate` |
| `measure_sync_glider_speed()` | Glider speeds |v| = 2/3 on both layers | — |
| `run_verification()` | Full checklist for clock option A or C | — |

Run individual checks from Python:

```python
import two_layer_chiral_afca_prototype as cmca
print(cmca.verify_va_structure())
print(cmca.verify_polynomial_equals_rule110_on_binary())
print(cmca.run_verification("A"))
```

### Chiral Verification Scripts

| File | Description |
|------|-------------|
| `epic073_rank070_106_rule124_chiral_verification.py` | Rule 124 = spatial mirror of Rule 110; ETHER_124 stability; two-layer chiral pair v_R = +2/3, v_L = −2/3 |
| `epic073_rank070_110_orbit_depth_ether_period.py` | f_MDL max orbit depth = ether temporal period = 7 |
| `epic073_rank070_141_generation_orbit_two_layer.py` | GEN1→GEN2→GEN3→VACUUM survives in decoupled two-layer CA |
| `epic073_rank070_113_ether_phase_c2_nucleation.py` | Ether phase C2 nucleation dynamics |
| `epic073_rank070_122_dynamical_coupling_bridge.py` | Constructive coupling families bypassing CouplingNoGo obstruction |
| `epic073_rank070_135_multicell_injection.py` | Multi-cell injection grammar on single layer |
| `epic073_rank070_136_multicell_bypass_grammar.py` | Multi-cell bypass grammar classification |
| `cross_layer_failure_analysis.py` | Why cross-layer deviation transfer fails (gcd(3,14) obstruction) |
| `excitation_level_coupling_formalism.py` | Excitation-level (glider) coupling operator formalism |

### Physics Bridge Scripts

| File | Description |
|------|-------------|
| `continuum_limit_lorentz_bridge.py` | CA-continuum Lorentz bridge: ε₀(7) = π²/147 → 0 in continuum limit |
| `epic073_lor1_kg_dispersion_lorentz.py` | Φ_MDL KG dispersion → exact Lorentz invariance (continuum track) |
| `planck_scale_lorentz_prediction.py` | Planck-scale Lorentz violation coefficient reconciliation |
| `dslit_gte_interference.py` | Double-slit Huygens-Fresnel interference from GTE/Φ_MDL |
| `phiborn1_kg_amplitude_probability.py` | Born rule from Z7-KG field amplitude: P(x) = \|dφ/dx\|² |
| `cmca_algebraic_descent.py` | Algebraic descent map from R110 Cook A-glider to Φ_MDL BPS kink |
| `cmca_spectral_dim_1d_v2.py` | Spectral dimension of 1D CMCA causal graph (undirected walk) |

### Wolfram Claims (`cmca_full_reproducibility_wolfram_version.wl`)

| Claim | What it proves |
|-------|----------------|
| `three_layer_cmca_runs` | Three-layer AFCA runs and passes full checklist |
| `glider_speed_2_3` | Glider speeds \|v\| = 2/3 on both chiral layers |
| `z7_generation_orbit` | GEN1→GEN2→GEN3→VACUUM in 3 f_MDL steps |
| `va_32_125` | 32/125 V–A chiral mismatches |
| `tau_c_sr_dilation` | SR proper-time dilation via τ_c ratio |
| `observable_lorentz_epsilon0` | Lattice Lorentz floor ε₀(7) = π²/147 < 7% |
| `sin2_theta_w_orbit` | sin²θ_W = 384729/1664000 from orbit structure |
| `born_rule_normalization` | Born density normalization from KG amplitude |
| `double_slit_correlation` | Huygens-Fresnel fringe correlation > 0.99 |
| `mdl_k_ca_19` | MDL description length K_CA = 19 bits |
| `polynomial_equals_rule110` | p(L,C,R) mod 2 = Rule 110 on {0,1}³ |

## Lean Certificates Referenced

| Lean theorem | File | What it proves |
|---|---|---|
| `rule110_z7_poly_rep` | `AlgebraicUniversality.lean` (rule110-lean) | p(L,C,R) mod 2 = Rule 110 on {0,1}³ |
| `rule124_eq_rule110_reflected` | `ChiralDoublet.lean` | Rule 124 = spatial mirror of Rule 110 |
| `fmdl_gen1_to_gen2` | `MDLDerivabilityCriterion.lean` | GEN1→GEN2 under f_MDL |
| `fmdl_gen1_is_garden_of_eden` | `MDLDerivabilityCriterion.lean` | GEN1 is a Garden of Eden (no f_MDL predecessor) |
| `z5_fmdl_no_psc_kink_orbits` | `MDLDerivabilityCriterion.lean` | No PSC kink orbits in Z₅ (3125-state exhaustive) |
| `ChiralPairVA.va_mismatch_count` | `ChiralPairVA.lean` | 32/125 V–A mismatches on SM vocabulary |
| `EtherProperTimeRate` | ugp-lean | Analytic τ_inner/τ_outer = 3/7 |
| `three_tape_gorard_vacuum_ricci_flat` | `GorardRicciFlatVacuum.lean` | κ = 0 on ether vacuum (shared with P45) |

## Notes

**Ether phase convention.** P41 tiles from `[1,1,1,1,1,0,0,0,1,0,0,1,1,0]`; P45 uses a cyclic rotation. Same orbit — observables are phase-invariant.

**Clock options.** Option A (shared inner clock gates both layers) is the MDL-minimal candidate. Option C gates R110 and R124 on the same completion event. Both are tested by `run_verification()`.

**PSC kink orbit search.** Exhaustive Z₇⁵ search finds 45 configurations with non-zero winding that reach VACUUM in 3 steps under f_MDL. Z₅⁵ exhaustive search finds 0 — MDL substrate selection favors Z₇.

**Output artifacts.** Each script writes a companion `*_results.json` in this directory. The canonical prototype writes `two_layer_chiral_afca_prototype_results.json`.

**Timeouts.** Long-running scripts include wall-clock caps (120–900 s) per repository safety policy.
