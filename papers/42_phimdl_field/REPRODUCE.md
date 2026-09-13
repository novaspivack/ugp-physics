# REPRODUCE — P42: The Φ_MDL Field

**Paper:** The Φ_MDL Field: Quantum Structure, Born Rule, and Continuum Completion
of the Chiral Minkowski CA  
**Author:** Nova Spivack  
**Series:** UGP Physics P42

---

## Dependencies

- Python 3.10+: `numpy`, `scipy`
- LaTeX: `pdflatex`, `bibtex`
- Lean 4 (optional): `ugp-lean` repository, `lake build`

---

## Scripts

All computation scripts are in `scripts/`. Each produces a JSON results file.

### `scripts/phimdl_3d_domain_wall.py`

Computes domain wall tension, 3+1D Z₇ superselection, Born rule sector weights,
and SR time dilation for moving domain walls.

```bash
cd papers/42_phimdl_field
python3 scripts/phimdl_3d_domain_wall.py
# → scripts/phimdl_3d_domain_wall_results.json
```

**Key outputs:** σ = 7450.31 MeV/fm², SR time dilation max error < 2×10⁻¹⁶,
Z₇ topological charge = sector label (all 7 sectors).

---

### `scripts/phimdl_vortex_3d.py`

Computes the domain-wall junction tension in 3+1D using the product ansatz
φ(x,y) = kink(x) + kink(y) on a 256×256 grid.

```bash
cd papers/42_phimdl_field
python3 scripts/phimdl_vortex_3d.py
# → scripts/phimdl_vortex_3d_results.json
```

**Key outputs:** λ_dim = −16/49 (analytically exact, confirmed numerically to
convergence error < 10⁻¹⁰); λ = −1654.77 MeV/fm (attractive);
|λ/σ| = 2.000 (wall thickness ratio).

---

### `scripts/cmca_algebraic_descent.py`

Verifies the explicit descent map from the R110 Cook A-glider to the Φ_MDL BPS kink
at lattice resolution M = 7.

```bash
cd papers/42_phimdl_field
python3 scripts/cmca_algebraic_descent.py
# → scripts/cmca_algebraic_descent_results.json
```

**Key outputs:** RMSD = 5.34% ≤ ε₀(7) = 6.71% (Nyquist bound); Pearson r = 0.994;
winding number Q = 1/7 (exact).

---

## Lean 4 Certification

```bash
cd ugp-lean
lake build UgpLean.Universality.PhiMDLThermalState
lake build UgpLean.Universality.DualFrameBornRule
lake build UgpLean.Substrate.TransputationStateSelector
lake build UgpLean.Framework.CMCAContinuumLimit
lake build UgpLean.Universality.LorentzInvariance
lake build UgpLean.Universality.BeableWindingPartitionInstance
lake build UgpLean.Spacetime.LiftingTheorem
lake build UgpLean.Universality.AlgebraicDescentTheorem
lake build UgpLean.Substrate.WindingCoinDecoupling
lake build UgpLean.Physics.ZSevenVacuumSelection
lake build UgpLean.Physics.KinkVacuumPolarization
lake build UgpLean.Physics.KinkFormFactor
lake build UgpLean.Universality.SylowIndexCouplingHierarchy
```

Expected result: all modules build with zero sorry (see Appendix A of paper).
The `ZSevenVacuumSelection` module certifies the coupling-sector scope results
(V_coupling breaks the Z₇ vacuum-label degeneracy; minimum at k* = 0); the
`KinkVacuumPolarization` and `KinkFormFactor` modules certify the algebraic
cores of the coupling-normalization and form-factor results.

---

## Build Paper

```bash
cd papers/42_phimdl_field
pdflatex phimdl_field_paper.tex
bibtex phimdl_field_paper
pdflatex phimdl_field_paper.tex
pdflatex phimdl_field_paper.tex
```

---

## Previously graduated scripts (not in this directory)

The following scripts are in other paper directories but produce data cited here:

- `papers/41_three_layer_chiral_minkowski_ca/scripts/phiborn1_kg_amplitude_probability.py` — Position Born density normalization
- `phiborn2_kink_overlap_born.py` — Dual-frame Born rule for overlapping kinks
- `phiborn3_measurement_collapse.py` — [D]-collapse Monte Carlo (500k trials)

## One-loop effective potential and exact S-matrix

| Script | Produces |
|---|---|
| `papers/42_phimdl_field/scripts/phimdl_cw_effective_potential.py` | V_eff^(1) = −2.367×10⁻² GeV⁴ at all 7 Z₇ vacua (pure-φ sector degeneracy preserved) |
| `papers/42_phimdl_field/scripts/phimdl_kink_fluctuation_spectrum.py` | PT spectrum s=1; zero mode + continuum at m_φ |
| `papers/42_phimdl_field/scripts/phimdl_casimir_tba.py` | TBA kernel φ(θ)=2/cosh(θ); ZZ S-matrix (CatAD) |

**Superseded** (retained for the record; do not use for the quantum kink mass —
both computations are incorrect, see §Quantum kink mass of the paper):

| Script | Status |
|---|---|
| `papers/42_phimdl_field/scripts/phimdl_casimir_3d1d_correction.py` | SUPERSEDED — produced the spurious ΔM = +31.22 MeV / M^Q = 321.32 MeV |
| `papers/42_phimdl_field/scripts/phimdl_casimir_dimreg.py` | SUPERSEDED — inverted Levinson convention; inconsistent μ-flow |
| `papers/42_phimdl_field/scripts/casimir_clogfin_precision.py` | SUPERSEDED — precision study of a coefficient belonging to the superseded bookkeeping |

## Quantum kink mass (M^Q = 281 ± 21 MeV)

Channel-resolved dimensional regularization of the 3+1D domain-wall tension
(interface formalism), benchmark-validated and cross-checked by an
independent finite-box mode-sum:

| Script | Produces |
|---|---|
| `scripts/kink_pole_mass_dhn_benchmarks.py` | Validation: exact sine-Gordon (−m/π) and φ⁴ ((1/(4√3)−3/(2π))m) one-loop kink masses reproduced to 3×10⁻¹⁴ |
| `scripts/kink_pole_mass_interface_dimreg.py` | Main result: ΔM = −7.2 MeV (on-shell) / −10.0 MeV (MS̄@m_φ); M^Q = 281 ± 21 MeV |
| `scripts/kink_pole_mass_box_modesum_check.py` | Independent finite-box mode-sum cross-check (3×10⁻⁵ agreement) |
| `scripts/kink_pole_mass_branch_verdict.py` | Λ_GTE readings and coupling-σ table after the M^Q correction |

## Coupling-sector scope (Z₇ degeneracy and V_coupling)

| Script | Produces |
|---|---|
| `scripts/z7_vacuum_selection_coupling_form_discriminator.py` | Coupling-form discriminator (dual-grammar MDL costs, BPS window, Z₇-shift scans) |
| `scripts/z7_vacuum_selection_downstream_integrity.py` | Downstream-integrity audit of the coupling-sector scope note |
| `scripts/z7_vacuum_selection_field_range_consistency.py` | Field-range consistency for the vacuum-manifold statement (ℝ-valued Φ, ℤ-many minima in 7 Z₇-classes) |
| `scripts/color_coupling_e_normalization.py` | e²(Λ_GTE) = 7/2 normalization and PDG running comparison; bracket [3.50, 3.76] |
| `scripts/color_coupling_g_scc_analog.py` | g = m_τ zero-new-scale completion for the χ-sector mass parameter |

## Coupling normalization at the EFT boundary

Scheme conversion, threshold constants, kink vacuum polarization, and the
non-perturbative kink charge form factor measurement (b = 1.189 ± 0.049):

| Script | Produces |
|---|---|
| `scripts/villain_msbar_required_coefficient.py` | Required Villain→MS̄ conversion coefficient; derived heat-kernel value 60.8 (scheme-conversion route closed) |
| `scripts/villain_msbar_heatkernel_lambda_ratio.py` | Λ_HK/Λ_W and Λ_MS̄/Λ_HK ratios (CatAD) |
| `scripts/villain_msbar_scheme_landscape.py` | Full scheme-landscape survey |
| `scripts/burnside_threshold_coset_matching.py` | Coset-sector threshold constant c_coset ∈ [−2.51, −1.00] (wrong sign) |
| `scripts/burnside_threshold_verdict_sigma.py` | σ-accounting with the threshold piece |
| `scripts/kink_vacuum_polarization_matching_constant.py` | c_kink scheme family; Cartan weights {0,±1/2}, t_kink = 3, b̂ = −4 |
| `scripts/kink_vacuum_polarization_lattice_tape.py` | Lattice-tape control: c_kink(lattice) = −1.00 (discreteness alone fails) |
| `scripts/kink_vacuum_polarization_verdict_sigma.py` | σ-verdict table for the VP matching constant |
| `scripts/dissolution_constant_exact_pt_spectral.py` | Exact-PT spectral route: structural obstruction (CatAD) |
| `scripts/dissolution_constant_spectral_class.py` | Spectral-class reformulation of the dissolution constant |
| `scripts/dissolution_constant_sumrule_dispersive.py` | Dispersive sum-rule bracket |
| `scripts/norfleet_residual_hypothesis.py` | Pre-registered residual-hypothesis battery (all forms fail — honest null) |
| `scripts/kink_form_factor_canonical_sanity.py` | Free-field exact estimator gate |
| `scripts/kink_form_factor_classical_lattice.py` | Classical (ℏ→0) lattice control with the identical estimator |
| `scripts/kink_form_factor_mc_2d_tuning_scan.py` | 2D tuning scan for the bare cosine coefficient |
| `scripts/kink_form_factor_lattice_mc_2d.py` | 1+1D dissolution positive control |
| `scripts/kink_form_factor_tape_charge_profile.py` | Tape charge-profile extraction |
| `scripts/kink_form_factor_precision_runner.py` | Main 3+1D substrate-regulated lattice MC runner (free-field / single-well vacuum / one-kink modes) |
| `scripts/kink_form_factor_precision_extraction.py` | Canonical extraction: w-ladder + capillary infinite-volume completion → b = 1.189 ± 0.015 (stat) ± 0.047 (syst) |
| `scripts/kink_form_factor_precision_diagnostics.py` | μ-estimator audit and MC-time-resolved diagnostics |
| `scripts/kink_form_factor_precision_dispersive_bracket.py` | Dispersive bracket: hard bounds b ≤ 2.51 / 3.06 |
| `scripts/kink_form_factor_precision_coupling_verdict.py` | Coupling verdict: c_kink = +2.45/+2.21 ± 0.33; offset reduced to +1.5σ (tree) / +1.3σ (quantum mass) |

The Monte Carlo campaign data for the runner are the
`scripts/kink_form_factor_precision_run_v3_*.json` files with matching
`scripts/prec_log_v3_*.txt` logs; the extraction script reads these directly.

## Kink-sector hadronic vacuum polarization

| Script | Produces |
|---|---|
| `scripts/kink_form_factor_delta_alpha_had.py` | Δα_kink = 3.47×10⁻⁴ (single-pole) / 3.70×10⁻⁴ (extended spectral model); 1.26–1.34% of Δα_had |

Run all scripts with `python3 <script path>`; each writes its JSON results file
next to the script.
