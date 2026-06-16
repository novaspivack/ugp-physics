# P45 — Three-Tape Chiral Minkowski Cellular Automaton: Scripts

**Paper:** "The Three-Tape Chiral Minkowski Cellular Automaton" (P45, Nova Spivack, 2026)  
**DOI:** [10.5281/zenodo.20465805](https://doi.org/10.5281/zenodo.20465805)

## Overview

These scripts implement the three-tape CMCA: three parallel 1+1D tapes (x, y, z), each carrying the three-layer chiral structure from P41, coupled by a shared global outer clock τ_c^out. By the Dimensional Protocol Principle (DPP), this shared clock promotes three independent 1+1D CMCAs to 3+1D Minkowski structure. The verification suite cross-checks nine headline physical claims — SR dilation, chirality, SM vertex conservation, gravity, Gorard vacuum flatness, Bell nonlocality, baryon number, kink mass, and soliton localization — plus supporting scripts for cosmology, leptogenesis, and Level 1→Level 2 continuum bridges.

## Quick Start

```bash
cd papers/45_three_tape_cmca/scripts

# Run all nine canonical verifications
python3 run_all_verifications.py

# Wolfram independent cross-check (all 9 verifications + polynomial + kink search)
wolframscript -file ThreeTapeCMCA.wl
```

Requirements: Python 3.10+, `numpy`, `scipy`. Wolfram Engine or Mathematica ≥ 12.0 for `.wl` scripts.

Options:

```bash
python3 run_all_verifications.py --out my_report.json
python3 run_all_verifications.py --quiet
```

Exit code `0` if all nine verifications pass; `1` otherwise. Report written atomically to `verification_report.json`.

## Key Concepts

**Three-tape DPP architecture.** Three spatial tapes, each with:
- `outer_plus`: Rule 110 (right-moving, v = +2/3)
- `outer_minus`: Rule 124 (left-moving, v = −2/3)
- `inner_clock`: Rule 110 (temporal gating τ_c)

A shared global outer clock τ_c^out synchronizes all three tapes, producing R^{3,1} Minkowski dynamics. Without the shared clock, three tapes are three independent 1+1D systems.

**f_MDL vs. p(L,C,R).** Same split as P41: the GTE polynomial `p(L,C,R) = C + R − CR − LCR` (mod 7) is the algebraic certificate (`p mod 2 = Rule 110` on binary inputs); `f_MDL` is the MDL-minimal physical update rule with 10 SM orbit entries.

**PSC kink orbit search.** Exhaustive Z₇⁵ search under f_MDL finds **45** configurations with non-zero winding that reach VACUUM in 3 steps. Z₅⁵ exhaustive search finds **0**. This is MDL substrate selection: PSC-consistent kink dynamics exist only in Z₇, not Z₅. Lean: `fmdl_gen1_to_gen2`, `z5_fmdl_no_psc_kink_orbits`.

**Ether convention.** P45 tiles from `[1,0,0,1,1,0,1,1,1,1,1,0,0,0]` — a cyclic rotation of P41's ETHER14. Translation-invariant; all observables are phase-independent.

## Nine Canonical Verifications

| # | Function | What it proves | Lean reference |
|---|----------|----------------|----------------|
| 1 | `verify_sr_time_dilation()` | Inner-clock gate rate = 3/7 on odd-parity ether cell | `EtherProperTimeRate` |
| 2 | `verify_va_chirality()` | Rule 110 and Rule 124 have opposite drift directions | — (structural) |
| 3 | `verify_sm_vertices()` | Z₇ winding conserved at all 33 SM vertex interactions | Z₇ winding conservation |
| 4 | `verify_gravity()` | Gravitational attraction via probe deflection; power-law scaling | — |
| 5 | `verify_gorard_vacuum()` | Ether is period-7 temporal orbit; κ = 0 on vacuum | `three_tape_gorard_vacuum_ricci_flat` |
| 6 | `verify_bell_inequality()` | CHSH S > 2 from two-tape GTE gravitational coupling | — |
| 7 | `verify_baryon_conservation()` | Baryon number B conserved at closed Z₇ vertices | `BaryonNumber.lean` |
| 8 | `verify_kink_mass()` | M_kink = (8/49) m_τ ≈ 290.10 MeV | — |
| 9 | `verify_soliton()` | Localized soliton via co-evolving reference (spread < 30 cells) | — |

Run individual verifications:

```python
from verification_suite import verify_sr_time_dilation, verify_bell_inequality
print(verify_sr_time_dilation())
print(verify_bell_inequality(G_eff=0.5))
```

## Script Categories

### Core CMCA

| File | Description |
|------|-------------|
| `three_tape_cmca.py` | Canonical `ThreeTapeCMCA` class: three tapes, shared τ_c^out, gravity, Bell density matrix, kink orbit search |
| `initial_conditions.py` | IC helpers: vacuum, glider (R110/R124), gravity source, proton triple, soliton |
| `verification_suite.py` | Nine canonical `verify_*` functions |
| `run_all_verifications.py` | CLI runner; writes `verification_report.json` |
| `ThreeTapeCMCA.wl` | Wolfram cross-check: all 9 verifications + polynomial + Z₇/Z₅ kink search |

Use in code:

```python
from three_tape_cmca import ThreeTapeCMCA
from initial_conditions import ic_glider_x

cmca = ThreeTapeCMCA(L=400, native_geodesic=True)
ic_glider_x(cmca)
cmca.run(T=500)
print(cmca.inner_tau_c_rate("x"))
```

Tape length `L` is arbitrary; the period-14 ether tile is repeated and truncated to `L`.

### Gravity

| File | Description |
|------|-------------|
| `gorard_coefficient_rule110.py` | Gorard coarse-graining coefficient C_Gorard from measured κ_3D |
| `gorard_planck_normalization.py` | Planck-scale normalization: gravity–EM gap ≈ 10^77.5 |
| `clock_gradient_geodesic.py` | CA-native geodesic: gravitational force from nearest-neighbor clock gradient |
| `selfconsistent_gravity.py` | Self-consistent gravity: source evolves under Rule 110 with probe |
| `gradient_kick_gravity.py` | Analytical 1/r potential with gradient kick; confirms F ~ b^{−2.30} |
| `coulomb_regime_gravity.py` | Definitive Coulomb-regime force law: b^{−2.00} confirmation |
| `gravity_force_law_continuum_limit.py` | Continuum limit: F → G_eff·M/(4πb²) as b/σ → ∞ |

### Bell / Quantum Mechanics

| File | Description |
|------|-------------|
| `born_rule_bell_violation.py` | Standalone CHSH reproduction: S = 2.4459 at G_eff = 0.5 |
| `bell_analytic_bound.py` | Analytic CHSH bound from diagonal H_grav; Z₇³ vs 3×3 qutrit comparison |
| `bell_layer_reconciliation.py` | L1 CHSH (S > 2) vs L2 P43 EPR semantics — two distinct physical layers |
| `z7_qudit_bell_cglmp.py` | Z₇ qudit Bell inequality (CGLMP d=7) on reduced density matrix |
| `born_rule_bridge_pw_to_field.py` | Page-Wootters Born rule → field-amplitude Born density bridge |
| `pw_born_rule_verification.py` | τ_c clock satisfies Page-Wootters prerequisites for Born rule |

### Special Relativity

| File | Description |
|------|-------------|
| `sr_ratio_measurement.py` | Reconciles claimed τ ratio 0.382 vs measured ≈ 0.43; documents cell-parity dependence |

The exact analytic ratio is **3/7 ≈ 0.4286** on odd-parity ether cells (verification 1). Global average over all cells is 4/7.

### Cosmology / Leptogenesis

| File | Description |
|------|-------------|
| `bps_instanton_action_derivation.py` | BPS instanton action S_1 = π/N_c from three-tape structure |
| `cc_temporal_voxel_formula.py` | Cosmological constant from temporal voxel formula: ρ_CC = (9/(7×D²)) M_Pl² H₀² |
| `srrg_mdl_bridge_derivation.py` | SRRG–MDL bridge: L_EW connection to K_CMCA minimization |
| `srrg_mdl_lean_bridge.py` | Numerical verification: β_SRRG(g) = 0 ↔ K_CMCA(g) = 0 at g* = 1/φ |

### Level 1 / Level 2 Bridge

| File | Description |
|------|-------------|
| `level1_level2_gravity_bridge.py` | L1 PMDL Poisson ≡ L2 EFE weak-field: G_eff·M_PMDL = 4π·G_N·M_kink |
| `polynomial_continuum_bridge.py` | Discrete p(L,C,R) vs continuous V_Z7(Φ) roles; gravity source identity |
| `l1_soliton_cross_tape.py` | Cross-tape Z₇ feedback search for self-sustaining winding configurations |
| `three_tape_sm_particles.py` | 3D SM particle spectrum from uniform triples (w,w,w); vertex conservation |
| `positional_nonlocality_analysis.py` | Gravitational source density ρ(p) = p(w_x,w_y,w_z)/6 positional structure |

## Wolfram Verification (`ThreeTapeCMCA.wl`)

```bash
# Wolfram Engine (macOS)
/Applications/Wolfram\ Engine.app/Contents/MacOS/WolframKernel -script ThreeTapeCMCA.wl

# Mathematica
/Applications/Mathematica.app/Contents/MacOS/WolframKernel -script ThreeTapeCMCA.wl
```

Implements all nine Python verifications plus polynomial cross-check and Z₇/Z₅ kink orbit search. Pure Wolfram Language — no Python dependency.

## Lean Certificates Referenced

| Lean theorem | File | What it proves |
|---|---|---|
| `dimensional_protocol_principle_master` | ugp-lean | Shared τ_c^out necessary and sufficient for 3+1D Minkowski |
| `cmca_tensor_product_gives_31d_minkowski` | ugp-lean | Tensor product of three CMCAs gives R^{3,1} |
| `rule110_z7_poly_rep` | `AlgebraicUniversality.lean` | p(L,C,R) mod 2 = Rule 110 on {0,1}³ |
| `EtherProperTimeRate` | ugp-lean | Analytic τ_inner/τ_outer = 3/7 |
| `three_tape_gorard_vacuum_ricci_flat` | `GorardRicciFlatVacuum.lean` | κ = 0 on ether vacuum |
| `fmdl_gen1_to_gen2` | `MDLDerivabilityCriterion.lean` | GEN1→GEN2 under f_MDL |
| `z5_fmdl_no_psc_kink_orbits` | `MDLDerivabilityCriterion.lean` | No PSC kink orbits in Z₅ |
| `BaryonNumber.lean` | ugp-lean | Baryon number conserved at closed Z₇ vertices |

## Default Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| Tape length `L` | 400 | Arbitrary; ether tile repeated |
| `native_geodesic` | `True` | Clock-layer gradient for gravity |
| `alpha` | 0.1 | Clock-rate modulation strength |
| `base_rate` | 0.6 | Base inner-clock firing rate |
| Gravity source σ | 5 | Gaussian source width |
| Probe `T_probe` | 300 | Probe evolution steps |
| Impact parameters | {30,40,50,70,100} | Gravity verification |

## Notes

**Two-level architecture.** The CMCA (Level 1) certifies algebraic structure. Φ_MDL (Level 2) is the physical continuum substrate. Scripts labeled "bridge" connect the two levels; do not conflate CMCA states with continuum field values.

**Output artifacts.** Each script writes a companion `*_results.json`. The verification runner writes `verification_report.json`.

**Timeouts.** Scripts include wall-clock caps (60–350 s) per repository safety policy.
