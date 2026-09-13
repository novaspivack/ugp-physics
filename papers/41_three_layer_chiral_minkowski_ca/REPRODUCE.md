# REPRODUCE — P41 — Three-Layer Chiral Minkowski CA

**Paper:** P41 — Three-Layer Chiral Minkowski CA (CMCA)  
**Status:** Scripts graduated 2026-05-25; canonical implementation self-contained 2026-05-31

---

## Code Navigation

### Which file to use

**Use the Python scripts for:** large-lattice numerical experiments, figure generation, full reproducibility in any Python 3.9+ environment, and the complete supplemental suite (Lorentz, coupling, spectral dimension, double-slit).

**Use the .wl for:** independent verification in Mathematica or Wolfram Engine; an alternative execution path with no Python dependency.

### Script roles

| Script | Role |
|--------|------|
| `cmca_full_reproducibility.py` | **Primary**: all 9 P41 headline claims (L=840, ~2.9 s) |
| `cmca_full_reproducibility_wolfram_version.wl` | **Secondary**: independent Wolfram cross-check of same 9 claims (~41 s); M=7 inner clock mini-tape |
| `two_layer_chiral_afca_prototype.py` | Core CMCA simulator (Rule 110 + Rule 124, shared τ_c clock); imported by primary |
| `cmca_algebraic_descent.py` | CMCA→Φ_MDL descent map |
| `cmca_spectral_dim_1d_v2.py` | 1+1D spectral dimension |
| `dslit_gte_interference.py` | Double-slit Born ensemble |
| `epic073_*` scripts | Supplemental rank-070 and rank-073 verifications |

### Related code in other papers

| File | Paper | Description |
|------|-------|-------------|
| `papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl` | P45 | Three-tape CMCA with single-bit inner clock gating (simpler than M=7 here); same 9-claim suite |
| `papers/45_three_tape_cmca/scripts/three_tape_cmca.py` | P45 | Python three-tape spatial extension (gravity, Bell, soliton) |
| `papers/49_gte_polynomial_wolfram/scripts/three_tape_wolframmodel_v2.wl` | P49 | Orbit-level DPP causal graph; no cell-level simulation or SR verification |

---

## Primary reproduction (all 9 headline claims)

**Primary reproduction:** `papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility.py` (Python, 2.9 s)

Single script verifying the full CMCA construction and every headline numerical claim:

```bash
cd /Users/nova/ugp-physics
python3 papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility.py
```

| Claim | Test | Expected |
|-------|------|----------|
| \|v_R\|=\|v_L\|=2/3 | Glider speed measurement | 0.6667 ±0.01 |
| Z₇ orbit preserved | gen₁→gen₂→gen₃→vac in 3 steps | PASS |
| V-A 32/125 mismatches | fMDL-110 vs fMDL-124 on SM vocabulary | 32/125 |
| τ_c≈γ (SR time dilation) | τ_c(glider)/τ_c(ether) | ≈1.563 (within 6.71% floor) |
| Observable Lorentz | ε₀(7) = π²/147 ≈ 6.71% | < 7% |
| sin²θ_W = 0.231207 | Orbit arithmetic | 384729/1664000 |
| Born rule P(k) = \|φ_k\|² | Position-space normalization | ∫P(x)dx = 1 |
| Double-slit corr = 0.998 | Huygens-Fresnel simulation | corr > 0.99 |
| MDL K_CA = 19 | Description-length bit count | 19 |

Results JSON: `papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_results.json`. Wall-clock cap: 900 s.

**Secondary reproduction:** `papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl` (Wolfram Language, 41 s, requires `wolframscript`)

```bash
wolframscript -file papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl
```

## Core CMCA implementation (canonical)

`cmca_full_reproducibility.py` imports `two_layer_chiral_afca_prototype.py`, which is the
canonical CMCA simulator (Rule 110 + Rule 124 outer layers, shared inner τ_c clock).
Both are co-located in `scripts/` — the paper's reproducibility suite is fully self-contained.

To run the simulator directly:
```bash
python3 papers/41_three_layer_chiral_minkowski_ca/scripts/two_layer_chiral_afca_prototype.py
```

**Lean-only supplements** (not exercised by the Python suite; compile separately in `ugp-lean`):

- `CMCAMDLMinimality.lean` — construction-class lower bound K_CA ≥ 19 (Python verifies equality only)
- `GTECategoryStructure.lean` — Phi_MDL terminal object in Level-1 GTE category
- `GUTStructure.lean` — EW threshold step k = N_gen = 3 uniqueness (`isEWThresholdStep`)
- `BeableWindingPartitionInstance.lean` — unconditional Born rule on kink Hilbert space
- `ChiralPairVA.lean`, `ChiralMirrorSpeedSymmetry.lean`, `OrbitDepthEtherPeriod.lean` — discrete structural certificates

---

## Chiral pair and two-layer structure

```bash
cd papers/41_three_layer_chiral_minkowski_ca/scripts
python3 epic073_rank070_106_rule124_chiral_verification.py   # 070-106: Rule 124 mirror CA
python3 epic073_rank070_110_orbit_depth_ether_period.py      # 070-110: max depth = ether period = 7
python3 epic073_rank070_113_ether_phase_c2_nucleation.py     # 070-113: ether-phase C2 nucleation
python3 epic073_rank070_135_multicell_injection.py           # 070-135: multi-cell injection loophole
python3 epic073_rank070_136_multicell_bypass_grammar.py      # 070-136: min weight 2; cross-layer negative
python3 cross_layer_failure_analysis.py                      # 070-138: cross-layer failure mechanism
python3 epic073_rank070_141_generation_orbit_two_layer.py    # 070-141: generation orbit survival OQ-A3
```

## Coupling and excitation formalism

```bash
python3 epic073_rank070_122_dynamical_coupling_bridge.py      # 070-122: event-triggered coupling taxonomy
python3 excitation_level_coupling_formalism.py               # 070-124: C_exc formalism OQ-A1
```

## Two-track Lorentz

```bash
python3 epic073_lor1_kg_dispersion_lorentz.py                # 073-LOR1: KG dispersion exact LI
python3 continuum_limit_lorentz_bridge.py                   # 073-LOR4: ε₀(M) → 0
python3 planck_scale_lorentz_prediction.py                   # 070-108: Planck-scale δ_LV
```

## Quantum foundations

```bash
python3 dslit_gte_interference.py                          # 75-DSLIT: double-slit Born ensemble
```

## Continuum limit and dimensional staircase (EPIC_074)

```bash
cd papers/41_three_layer_chiral_minkowski_ca/scripts
python3 cmca_algebraic_descent.py        # 074-DESCENT: explicit CMCA→Φ_MDL descent map
python3 cmca_spectral_dim_1d_v2.py       # 074-SPECTRAL: 1+1D spectral dimension
python3 cmca_full_reproducibility.py     # Full reproducibility suite (all 9 headline claims)
```

| Script | Result |
|--------|--------|
| `cmca_algebraic_descent.py` | RMSD=5.34% < ε₀(7)=6.71%; Pearson r=0.994; Q=1/7 |
| `cmca_spectral_dim_1d_v2.py` | d\_s → 2 in 1+1D (as expected for 1D random walk) |
| `cmca_full_reproducibility.py` | All 9 claims PASS including Born rule and MDL K=19 |

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `epic073_rank070_106_rule124_chiral_verification.py` | 070-106 | v_R=+2/3, v_L=−2/3 decoupled chiral pair |
| `epic073_rank070_136_multicell_bypass_grammar.py` | 070-136 | Min injection weight 2; cross-layer 0/20 persistent C2 |
| `cross_layer_failure_analysis.py` | 070-138 | spread_causal_cone 5/5; phase mismatch 4.7% resonance |
| `excitation_level_coupling_formalism.py` | 070-124 | Resonant cycles p3=1.0 at t mod 21 |
| `epic073_rank070_141_generation_orbit_two_layer.py` | 070-141 | Forward gen orbit preserved in decoupled two-layer |
| `dslit_gte_interference.py` | 75-DSLIT | Zone L2 corr=0.9942; χ²_red ≈ 10⁻⁴ |
| `continuum_limit_lorentz_bridge.py` | 073-LOR4 | ε₀(M)=π²/(3M²); n_fit≈2 |
| `sync_vs_async_three_layer.py` | 074-UNIDM1 | ASYNC: τ_dilation confirms γ; SYNC: no dilation (CatA) |

**Lean (zero sorry):** `ExcitationCoupling.lean`, `DynamicalCouplingBridge.lean`, `CouplingNoGo.lean`, `ChiralMirrorSpeedSymmetry.lean`, `ChiralPairDecoupling.lean`, `OrbitDepthEtherPeriod.lean`, `Substrate/PSCPILorentzMain.lean`, `Substrate/LorentzInvariance.lean`.

Results JSON co-located in `scripts/`. Dependencies: Python 3.9+, numpy.

All scripts are self-contained within `scripts/`: no research-sandbox imports required.

---

## Mass-sector cross-reference (P01)

P41 certifies the discrete CMCA substrate; charged-fermion masses and UCL audits live in **P01** (`papers/01_SM/`).

| Audit | Where |
|-------|--------|
| Dual-path / bare Elegant Kernel limit | P01 Appendix (verifier modes); `comp_p01_ucl_coeff_audit.py` |
| Structural CMCA IMT mixer | `UGP_GTE_SM_Verifier.py --imt-mixer-mode cmca` (≈ v12 for masses today) |

See P01 `REPRODUCE.md` and `UGP_GTE_SM_Verifier/README.md`.

---

*REPRODUCE.md — P41 — EPIC_073 graduation 2026-05-25; canonical implementation self-contained 2026-05-31*
