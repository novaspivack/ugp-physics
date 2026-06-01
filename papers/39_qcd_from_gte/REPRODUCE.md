# REPRODUCE — P39 — QCD Structure from the GTE Substrate

**Paper:** P39 — QCD Structure from the Generative Triple Evolution Substrate:
Asymptotic Freedom, Confinement, and Hadron Spectroscopy from F₂₁ ⊂ SU(3)

**Date:** 2026-05-24

---

## Compiling the paper

```bash
cd papers/39_qcd_from_gte
pdflatex gte_qcd_structure_paper.tex
bibtex gte_qcd_structure_paper
pdflatex gte_qcd_structure_paper.tex
pdflatex gte_qcd_structure_paper.tex
```

Requires: TeX Live 2024+ with `tcolorbox`, `tikz`, `longtable`, `appendix`,
`cleveref`, `microtype`, `enumitem`, `booktabs`.

Bibliography: `../bib/Spivack_Papers_Bibliography.bib`

---

## Lean verification

Build all certified modules from the `ugp-lean` repository:

```bash
cd ugp-lean
lake build UgpLean.Universality.SylowIndexCouplingHierarchy
lake build UgpLean.QFT.GaugedMassGap
lake build UgpLean.Spacetime.ColorConfinement
lake build UgpLean.Spacetime.MassGap
lake build UgpLean.Spacetime.OrbitMassHierarchy
lake build UgpLean.Universality.WeakIsospin
```

### Headline theorems (all zero sorry)

| Theorem | Module | What it certifies |
|---|---|---|
| `f21_substrate_identification` | SylowIndexCouplingHierarchy | F₂₁ ≅ Σ(21) ⊂ SU(3); all Casimirs |
| `frobenius_casimir_fundamental` | SylowIndexCouplingHierarchy | C_F = 4/3 |
| `frobenius_casimir_adjoint` | SylowIndexCouplingHierarchy | C_A = 3 |
| `f21_substrate_beta_coefficient` | SylowIndexCouplingHierarchy | b₀ = 7 |
| `f21_substrate_asymptotic_freedom` | SylowIndexCouplingHierarchy | β(g) < 0; AF |
| `f21_substrate_two_loop_beta_b1` | SylowIndexCouplingHierarchy | b₁ = 26 |
| `f21_theta_term_vanishes` | SylowIndexCouplingHierarchy | θ_QCD = 0 |
| `gte_physical_baryon_octet_is_ms` | SylowIndexCouplingHierarchy | Physical baryon octet is 8_MS |
| `no_psc_admissible_single_quark` | Spacetime/ColorConfinement | Colour confinement |
| `gte_mass_gap` | Spacetime/MassGap | Beable mass gap |
| `qft_gauged_mass_gap_pos` | QFT/GaugedMassGap | Conditional QFT gap |
| `qft_gauged_mass_gap_unconditional` | QFT/GaugedMassGap | Unconditional QFT gap |
| `leptonic_sector_heaviest_gen3` | Spacetime/OrbitMassHierarchy.lean §7, commit `d7e1b87` | Leptonic sector gen₃ heaviest (SCC prerequisite) |
| `mphi_equals_tau_mass_scc` | Spacetime/OrbitMassHierarchy.lean §7, commit `d7e1b87` | m_φ = m_τ = 1776.86 MeV via Self-Consistency Condition |
| `mkink_from_scc` | Spacetime/OrbitMassHierarchy.lean §7, commit `d7e1b87` | M_kink = (8/49) m_τ = 290.10 MeV |
| `fpi_from_scc` | Spacetime/OrbitMassHierarchy.lean §7, commit `d7e1b87` | f_π = M_kink/π = 92.34 MeV (+0.30% vs PDG) |
| `weak_isospin_identification` | Universality/WeakIsospin.lean, commit `0fb07eb` | SU(2)_L doublet structure from Z₇ W_B arithmetic (CatAL) |

---

## Numerical scripts

Scripts in `papers/39_qcd_from_gte/scripts/` (graduated) and `research-sandbox/` (pending graduation).

### Scripts referenced by P39

| Script | What it computes | Status |
|---|---|---|
| `rank97b_dbreakqcd_calibration_v2.py` | Physical scale calibration Routes A'/B'/C' | research-sandbox |
| `fradkin_shenker_confinement.py` | Fradkin–Shenker phase diagram | **scripts/** (graduated from `rank107_higgten_fradkin_shenker.py`) |
| `aprime_lagrangian_extension.py` | A′_μ coupling prediction | **scripts/** (graduated from `rank118_aprime_lagrangian.py`) |
| `rank121_berry21_su3_holonomy.py` | Non-abelian Berry holonomy 5/5 tests | research-sandbox |
| `rank129_thetap_chain.py` | θ_P mixing angle from GOR chain | **scripts/** (graduated 2026-05-31) |
| `rank130_chitop2.py` | Topological susceptibility χ_top^(1/4) | research-sandbox |
| `rank131_fpigte.py` | f_π = m_kink/π | research-sandbox |
| `rank134_nlo_b0.py` | NLO B₀ correction | research-sandbox |
| `rank106_hadmult.py` | Hadron multiplet structure | research-sandbox |
| `rank125_jpspin.py` | JP = 1/2+ derivation | research-sandbox |
| `mphi_scc_derivation.py` | m_φ first-principles via SCC (m_φ = m_τ) | **scripts/** (graduated 2026-05-24) |

### Key artifacts

| Artifact | Source | Central result |
|---|---|---|
| `rank97b_dbreakqcd_v2_results.json` | Route C' calibration | sim_to_fm = 0.112 fm/sim |
| `rank121_berry21_su3_holonomy_results.json` | Berry holonomy | 5/5 tests PASS |
| `rank107_higgten_fradkin_shenker_results.json` | Fradkin–Shenker | Option A selected |
| `rank118_aprime_lagrangian_results.json` | A′_μ coupling | e′ = e |
| `data/mphi_scc_derivation_results.json` | SCC derivation of m_φ | m_φ = m_τ = 1776.86 MeV; M_kink_pred = 290.10 MeV; f_π_pred = 92.34 MeV (+0.30%); 4/4 nulls PASS |

See `scripts/README.md` for graduation status of each script.

### α_s(M_Z) from σ_GTE — strong coupling derivation (G10 g_s CatAD)

Script: `scripts/g10_gs_derivation.py`
Artifact: `scripts/g10_gs_derivation_results.json`

```bash
python3 scripts/g10_gs_derivation.py
# -> scripts/g10_gs_derivation_results.json
```

Derivation chain:
1. σ_GTE = (9/4)·m_kink² = 0.18920 GeV²  [G13 CatAD]
2. K = √σ/Λ_MS^{nf=3} = 2.00 ± 0.08  [FLAG lattice QCD]
3. Λ_pred = √σ_GTE/K = 217.5 MeV
4. 2-loop RGE n_f=3→4→5 to M_Z = 91.187 GeV

**Result:** α_s(M_Z) = 0.12001 (err = +1.8% vs PDG 0.1179), g_s(M_Z) = 1.2281.
Sensitivity: over K ∈ [1.92, 2.08], α_s ∈ [0.1193, 0.1208] — all within 2.4% of PDG.
**CatLevel: CLOSED CatAD** (err < 5%).

---

### m_φ first-principles derivation (Self-Consistency Condition)

The Φ_MDL Lagrangian parameter m_φ is identified with the tau lepton mass
through the Self-Consistency Condition: the bare field scale must equal the
heaviest stable cascade composite in the pure-Z₇ (color-singlet, leptonic)
sector. Mechanism:

1. F₂₁ = Z₇ ⋊ Z₃ semidirect structure ⇒ leptonic sector inherits only the
   Z₇ kernel (no color modulation).
2. Three-generation cascade closure (no fourth family) ⇒ cascade terminates
   at the gen-3 endpoint.
3. MDL minimality on the Lagrangian parameter ⇒ bare scale = heaviest stable
   composite.

Therefore: m_φ = m_τ = 1776.86 MeV.

Predictions (replacing the previously calibrated inputs):
- M_kink = (8/49) m_τ = **290.10 MeV** (previously 286.98 MeV, ±40%)
- f_π   = M_kink/π   = **92.34 MeV** (PDG 92.07, error +0.30%; previously −0.81%)

Reproduce:
```bash
cd papers/39_qcd_from_gte
python3 scripts/mphi_scc_derivation.py
# -> data/mphi_scc_derivation_results.json
```

All four mandatory null tests (arithmetic-density, wrong-target, neighbour-atom,
physical-interpretation) PASS. The chain has no free parameters: only
v_Higgs (master EW scale, already in IMT) + Lean-certified canonical lepton
triple + F₂₁ structure + analytic BPS sine-Gordon formula.

---

## Physical-scale calibration

Central conversion: `sim_to_fm = 0.112` fm/sim (Route C' self-consistency).
Matching scale: Λ_GTE ≈ 2.01 GeV.
Systematic: f_quant ≈ 0.63 (classical–quantum correction, documented open issue).

---

### Weak Isospin Identification (94c-ISOSPIN)

Lean module: `UgpLean/Universality/WeakIsospin.lean`
Commit: `0fb07eb` (ugp-lean)
Theorem: `weak_isospin_identification` (CatAL, zero sorry, proved by `decide`)

No computational scripts — pure arithmetic certification.

Supporting theorems (all zero sorry):
- `wb_conservation_charged_current` — W_B conserved at all 4 SM CC vertices mod 7
- `weak_isospin_doublet_delta_four` — ΔW_B = 4 between doublet partners (ν/e⁻ and u/d)
- `species_formula_forces_delta_four` — species formula W_B = 4k mod 7 forces doublet structure
- `wb_wplus_uniquely_determined` — W_B(W⁺) = 3 is the unique Z₇ solution to CC constraints
- `wb_wminus_uniquely_determined` — W_B(W⁻) = 4 is the unique Z₇ solution

---

### F₂₁ → SU(3) Yang-Mills continuum limit (SU3-CONTINUUM)

Script: `scripts/f21_su3_continuum_limit.py`
Artifact: `scripts/f21_su3_continuum_limit_results.json`
Lean module: `UgpLean/Algebra/F21SU3Embedding.lean`

```bash
python3 scripts/f21_su3_continuum_limit.py
```

Establishes the embedding F₂₁ ↪ SU(3) (faithful 3-irrep, det=1, unitary), the
freezing obstacle for pure F₂₁ gauge theory (finite subgroup, not dense), the
Burnside coset-filling mechanism (irreducible ⇒ span_ℂ ρ(F₂₁) = full M₃(ℂ), so
the Φ_MDL scalar fills SU(3)/F₂₁ → IR is full SU(3) Yang-Mills), the gluon
branching 8 = 1' + 1'' + 3 + 3̄, and the f_quant string-tension factor with
mandatory null tests (precision-limited: best simple form 2^{-2/3} = 0.630).

Embedding/branching Lean theorems are CatAL zero sorry; the Burnside
coset-filling is a named CatAD axiom (`f21_burnside_full_enveloping_algebra`,
Mathlib density-theorem gap).

---

### G15: Y-junction G_inter derivation (2026-05-29)

Script: `scripts/g15_yjunction_derivation.py`  
Artifact: `scripts/g15_yjunction_results.json`

```bash
python3 scripts/g15_yjunction_derivation.py
```

Systematic scan over Y-junction baryon string formulas for G_inter, the inter-tape
confinement coupling in M_p = 3·M_kink + G_inter·|p(2,2,6)|/6.

Key result: G_inter = (w_u/F_{n+1}) × σ_GTE/m_kink = (2/89)×(9/4)×m_kink = 14.66 MeV
gives M_p = 938.37 MeV (+0.010% vs PDG), CatAD arithmetic precision.

Formula ingredients:
- w_u = 2: up-quark winding number (CatAD)  
- F_{n+1} = F₁₁ = 89 = b_seed + 2⁴: Fibonacci at GTE ridge level + 1 (CatAD structure)
- σ_GTE = (9/4)m_kink² (G13 CatAD)  
- m_kink = 4v_H/(7⁴√2) (G7+BPS CatAD)

F₁₁ = 89 is unique: F₁₀=55 gives +4.52% error, F₁₂=144 gives −2.78% error.

Physical mechanism (conjectural): Fibonacci suppression at Y-junction vertex from
GTE Fibonacci-lift structure at ridge n=10. Full path-integral derivation open.

---

*REPRODUCE.md — P39 — 2026-05-29*
