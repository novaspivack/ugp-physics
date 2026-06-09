# REPRODUCE — P37 — Quantum Mechanics from Rule 110

**Paper:** P37 — "Quantum Mechanics from Rule 110: Hilbert Space, Hamiltonian,
and Born Rule"  
**Date:** 2026-05-20  
**Author:** Nova Spivack

---

## Reproducing the numerical results

### Result 1: Orbit decomposition and Hilbert space (CatA)

**Script:** `canonical_run/fmdl_hamiltonian_spectrum.py`

```bash
cd papers/37_quantum_mechanics/canonical_run
python3 fmdl_hamiltonian_spectrum.py
```

Expected output (exact):
- Total states: 16,807
- Distinct cycles: 1
- Cycle states: 1 (vacuum only)
- Transient states: 16,806 (99.994%)
- Garden-of-Eden states: 16,590 (98.71%)
- Maximum tail length: 7
- Vacuum predecessor count: 14,147
- gen1 tail length: 3, predecessors: 0 (GoE)
- gen2 tail length: 2, predecessors: 1
- gen3 tail length: 1, predecessors: 1

### Result 2: Eigenvalue-mass correspondence tests (CatA)

**Script:** `canonical_run/eigenvalue_mass_correspondence.py`

```bash
python3 eigenvalue_mass_correspondence.py
```

Expected output:
- T=3 ratio spread: 69.3% (FAIL)
- T=4 ratio spread: 63.0% (FAIL)
- Mass ratio discrepancy m_μ/m_e: 10,238% (FAIL)
- Mass ratio discrepancy m_τ/m_e: 115,807% (FAIL)
- Tail-3 state count: 75 (near-miss vs N_eff(gen1)=73)

### Result 3: Dark sector orbit structure (CatAL)

**Script:** `canonical_run/fmdl_z74_orbit_spectrum.py`

```bash
python3 fmdl_z74_orbit_spectrum.py
```

Expected output:
- Total states: 2,401
- Distinct cycles: 3 (vacuum + two period-2 cycles)
- Non-vacuum cycles: 2 (both length-2)
- Hilbert space dimension: 5
- GoE fraction: 97.08%
- Maximum tail length: 4

### Result 4: Winding class structure (CatAD)

**Analytic:** The 7 winding classes each contain exactly 2,401 states,
by the $\mathbb{Z}_7$-homomorphism argument (no script required).
Verification: `python3 -c "print(7**5 / 7, '==', 7**4)"` → 2401.0 == 2401.

---

## Lean 4 certification (CatAL results)

The following theorems are in the Lean 4 repository (build from source):

| Theorem | File | Result |
|---------|------|--------|
| `code_word_cardinality` | `Spacetime/MultiParticleHilbert.lean` | 4 code words (CatAL, zero sorry) |
| `n_particle_state_count` | `Spacetime/MultiParticleHilbert.lean` | N-particle state space has 4^N elements |
| `multiDWeight_eq_one` | `Spacetime/MultiParticleHilbert.lean` | DWeight product = 1 on all multi-states |
| `multiMass_append` | `Spacetime/MultiParticleHilbert.lean` | Total mass additive under concatenation |
| `smGenMass_multi_anchor` | `Spacetime/MultiParticleHilbert.lean` | Non-vacuum mass ≥ 1.8 MeV |
| `multiparticle_orbit_closure` | `Spacetime/MultiParticleHilbert.lean` | f_MDL preserves all code words |
| `inner_product_positive_definite` | `Spacetime/MultiParticleHilbert.lean` | Basis inner product positive definite |
| `multiparticle_space_well_defined` | `Spacetime/MultiParticleHilbert.lean` | All structural properties bundle (CatAL) |
| `dark_sector_orbit_structure` | `GUTStructure.lean §35` | Period-2 dark cycles |
| `dark_sector_period2_exhaustive` | `GUTStructure.lean §35` | Exhaustive Rule 110 4-cell |
| `dark_sector_vacuum_fixed_point` | `GUTStructure.lean §35` | Vacuum fixed point |
| `z7_color_subgroup_closed` | `GUTStructure.lean §33` | Z₃ = {1,2,4} ⊂ Z₇* closed |
| `z7_color_subgroup_generator` | `GUTStructure.lean §33` | Generator 2, order 3 |
| `w_u_in_color_subgroup` | `GUTStructure.lean §33` | w=2 ∈ Z₃ |
| `su2l_charge_assignment_z7_discriminator` | `GUTStructure.lean §33` | Doublet arithmetic |
| `phimdl_potential_su2l_invariant` | `Algebra/GaugeMDL.lean` | L2 preserved under SU(2)_L (CatAL) |
| `su2l_covariant_derivative_minimal` | `Algebra/GaugeMDL.lean` | MDL-minimal covariant derivative (CatAL) |
| `su2l_wpm_generator_algebra` | `Algebra/GaugeMDL.lean` | W± Lie algebra (CatAL) |
| `su2l_l2_from_phimdl_potential_catad` | `Algebra/GaugeMDL.lean` | SU(2)_L from PMDL; zero named axioms (CatAL) |
| `winding_class_sm_assignment` | `GUTStructure.lean §31` | Z₇ → SM charge map |
| `fmdl_nonzero_count_14` | `GUTStructure.lean` | 14-entry lookup table |

Build status: all theorems zero sorry (CatAL as of 2026-05-20).

---

## Building the paper

```bash
cd papers/37_quantum_mechanics
pdflatex quantum_mechanics_paper.tex
bibtex quantum_mechanics_paper
pdflatex quantum_mechanics_paper.tex
pdflatex quantum_mechanics_paper.tex
```

The bibliography uses `../bib/Spivack_Papers_Bibliography.bib` (master bib only).

---

## Lean build (ugp-lean until graduation)

```bash
cd /path/to/ugp-lean
lake build UgpLean.Universality.GUTStructure
lake build UgpLean.Spacetime.MultiParticleHilbert
```

| Theorem | Section | In prior REPRODUCE table? |
|---------|---------|---------------------------|
| `code_word_cardinality`, `n_particle_state_count`, `multiDWeight_eq_one`, `multiMass_append`, `smGenMass_multi_anchor`, `multiparticle_orbit_closure`, `inner_product_positive_definite`, `multiparticle_space_well_defined` | `Spacetime/MultiParticleHilbert.lean` (commits `474dd75`, `b389e24c`) | ✅ Added 2026-05-24 |
| `dark_sector_orbit_structure` | §35 | ✅ |
| `z7_color_subgroup_*`, `su2l_charge_assignment_z7_discriminator` | §33 | ✅ |
| `winding_class_sm_assignment` | §31 | ✅ |
| `HyperchargeConsistency` | §73 | ⏳ Add after graduation |
| `tail_length_strict_ordering`, `neff_not_monotone_in_tail`, `mass_quantitative_formula_requires_cascade` | §76 | ⏳ Add after graduation |
| `gauge_arithmetic_identification` | §55 | ⏳ |

**Cross-repo:** one `nems-lean` citation in paper — build separately if verifying that theorem.

---

## Graduation checklist (full reproducibility)

| Item | Status |
|------|--------|
| `canonical_run/*.py` (3 scripts) | ✅ Graduated |
| `Spacetime/MultiParticleHilbert.lean` (15 theorems, zero sorry) | ✅ Certified (commits `474dd75`, `b389e24c`, `ugp-lean`) |
| `Algebra/GaugeMDL.lean` (SU(2)_L bundle, zero sorry) | ✅ Certified (commit `378ff20`, `ugp-lean`) |
| `GUTStructure` §§31,33,35,55,73,76 | ✅ `ugp-lean` |
| REPRODUCE Lean §73/§76 | ⏳ Documented above |
| Paper `.tex` says `ugp-lean` | ⏳ Harmonize after Lean graduation |
| Committed JSON for canonical_run outputs | ⏳ Optional SHA-256 at release |

Handoff 8 § P37.

---

*REPRODUCE.md — P37 — reproducibility audit 2026-05-20*

---

## Paper pass update — 2026-05-24

- `canonical_run/rank94_eigenvalue_mass.py` renamed to `canonical_run/eigenvalue_mass_correspondence.py`.
- Script reference updated in REPRODUCE.md.
- New Lean theorems for Lorentz causal structure (`lamport_strict_partial_order`, `minkowski_causal_isomorphism`, `minkowski_causal_surjection_continuum_limit` in `CausalInvariance.lean`) added to Lean section.

| Theorem | File | Result |
|---------|------|--------|
| `lamport_strict_partial_order` | `CausalInvariance.lean §2` | AFCA causal invariance (zero sorry) |
| `chiral_trajectory_light_cone` | `CausalInvariance.lean §3` | Discrete light-cone bound (zero sorry) |
| `minkowski_causal_isomorphism` | `CausalInvariance.lean §4` | Minkowski cone inclusion (zero sorry) |
| `minkowski_causal_surjection_continuum_limit` | `CausalInvariance.lean §4` | Coordinate surjection (zero sorry) |

---

## EPIC_073 scripts (graduated 2026-05-25)

```bash
cd papers/37_quantum_mechanics/scripts
python3 g_minus_2_muon_gte_correction.py          # 070-131: one-loop a_μ GTE falsification (CatA)
python3 g_minus_2_two_loop_gte.py                 # 070-139: two-loop neutral on Δa_μ (CatD)
python3 gte_hvp_dispersion_estimate.py             # 070-140: hadronic HVP dispersion (CatD neutral)
python3 dslit_gte_interference.py                 # 75-DSLIT: Born click ensemble (CatA)
python3 epic073_rank070_97b_thooft_effectmeasure_bridge.py  # 070-97B: EffectMeasure B1 (CatA partial)
```

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `g_minus_2_muon_gte_correction.py` | 070-131 | a_μ^{GTE,1L} = 1/(274π); matches Schwinger 0.026%; neutral on Fermilab Δa_μ |
| `g_minus_2_two_loop_gte.py` | 070-139 | Two-loop QED 1660× Δa_μ; neutral verdict |
| `gte_hvp_dispersion_estimate.py` | 070-140 | HVP ≈ 6.20×10⁻⁸; wrong sign for anomaly; not a GTE prediction |
| `dslit_gte_interference.py` | 75-DSLIT | Zone L2 Born clicks corr=0.9942; χ²_red ≈ 10⁻⁴ |
| `epic073_rank070_97b_thooft_effectmeasure_bridge.py` | 070-97B | Winding-sector Born weights satisfy EffectMeasure axioms (200/200) |

**Lean (zero sorry):** `BornRuleMDL.lean`, `FockSpaceKink.lean`, `TwoRoleTheorem.lean`, `ThooftEffectMeasureBridge.lean`.

Also canonical in `papers/41_two_layer_ca/scripts/dslit_gte_interference.py` (cross-ref P41 double-slit section).

*REPRODUCE.md — P37 — EPIC_073 pass 2026-05-25*
