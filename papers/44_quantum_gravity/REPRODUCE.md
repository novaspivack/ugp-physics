# P44 — REPRODUCE

## Compilation

```bash
cd papers/44_quantum_gravity
pdflatex quantum_gravity_completeness.tex
bibtex quantum_gravity_completeness
pdflatex quantum_gravity_completeness.tex
pdflatex quantum_gravity_completeness.tex
```

Expected output: `quantum_gravity_completeness.pdf`, approximately 25–30 pages, no errors.

## Lean verification

All theorems in Appendix A are in the `ugp-lean` canonical Lean 4 repository
(<https://github.com/novaspivack/ugp-lean>).

```bash
cd /path/to/ugp-lean
lake build
# Expected: zero sorry in the modules listed in Appendix A
```

Key modules (all zero sorry):

### Curved-background theory and EFE
- `UgpLean/Gravity/CurvedBackgroundLagrangian.lean`
- `UgpLean/Gravity/HawkingRadiation.lean`
- `UgpLean/Gravity/UVFiniteness.lean`

### Holographic encoding theorem (GHET)
- `UgpLean/Gravity/GHETEquivalence.lean`
- `UgpLean/Substrate/RSCodeOrbit.lean`

### Cosmology and dark energy
- `UgpLean/Cosmology/MDLInitialState.lean`
- `UgpLean/Gravity/ClassicalLambda.lean`
- `UgpLean/Gravity/NRTVacuumEnergy.lean`
- `UgpLean/Gravity/OmegaLambda.lean`
- `UgpLean/Gravity/PSCEpochSelection.lean`  ← PSP arithmetic (commit 09145e8, zero sorry incl. interval bound)

### Galois structure
- `UgpLean/Algebra/CyclotomicGalois.lean`
- `UgpLean/Substrate/FermionicStatistics.lean`
- `UgpLean/Substrate/BaryonNumber.lean`
- `UgpLean/Substrate/SU3GluonCount.lean`

### Geometric structure
- `UgpLean/Spacetime/GF7VacuumFixedPoint.lean`
- `UgpLean/Spacetime/DiscreteBianchi.lean`
- `UgpLean/Spacetime/GorardRicciFlatVacuum.lean`
- `UgpLean/Spacetime/GorardMasterBundle.lean`
- `UgpLean/Cosmology/WeylAlgebraicMiracle.lean`
- `UgpLean/Spacetime/ClassicalDiscreteRG.lean`

### Open (pending Mathlib library)
- `UgpLean/Gravity/WaldEntropy.lean` — 3 sorries (Mathlib manifold integrals)
- `UgpLean/Cosmology/CMBSpectralTilt.lean` — axiom stub (OQ-QG-1-Z₂-EFT)
- `UgpLean/ContinuumLimit/WassersteinDistance.lean` — 2 named sorrys: `W1_eq_zero_iff`, `W1_triangle` (Mathlib OT library; `W1_ge_of_lipschitz` now zero sorry)

### Gorard–Vacuum W₁ bridge (EPIC 083, partially CatAL)
- `UgpLean/ContinuumLimit/GorardVacuumW1Bridge.lean` — `gorard_vacuum_oric_zero_scoped` (∀ n, CatAL zero sorry), `vacuum_w1_eq_one` (CatAL zero sorry), `W1_ge_of_lipschitz` (CatAL zero sorry)

### Vacuum spatial GH convergence (OQ-QG-1a, CatAL)
- `UgpLean/Spacetime/VacuumGHConvergence.lean` — `vacuum_cmca_gh_converges_to_flat_space` (CatAL, zero sorry): vacuum CMCA spatial graph → flat ℝ³ in GH, bound ≤ 1/L
- `UgpLean/Spacetime/MatterGHPrecompactness.lean` — `finGrid_family_totally_bounded` (CatAL, zero sorry): GH family pre-compact; `single_kink_gh_converges_to_flat` (CatAL, zero sorry): isolated kink does not curve GH limit

## Key scripts

All computation scripts are in `papers/44_quantum_gravity/scripts/`.

| Script | Result | Key value |
|---|---|---|
| `hawking_radiation_phimdl.py` | T_H, M_crit | M_crit = 3.34×10³⁹ MeV |
| `greybody_factor_phimdl.py` | Greybody suppression table | Exponential for M_BH ≫ M_crit |
| `uv_finiteness_curved_background.py` | UV divergence classification | C_i ≈ 41.76 |
| `rt_wald_extension_proof.py` | RT formula proof; log7 cancellation | T₂→T₃ verified |
| `flrw_gte_bounce.py` | Bounce dynamics; reheating | T_reh = 6.49×10⁸ GeV |
| `mdl_initial_state_scoring.py` | MDL K-scores | K_tot = log₂(3) = 1.585 bits |
| `cyclotomic_z7_analysis.py` | Galois structure | Gal(Q(ζ₇)/Q) ≅ Z₂ × Z₃ |
| `norfleet_tools_test.py` | κ_SD = 10/13; ρ(B) = 2.29; D_CF = 4.018 | Norfleet tools |
| `bianchi_extended_test.py` | Extended Bianchi k=3..10 | max|∑κ| < 10⁻¹⁴ |
| `bakry_emery_saturation_check.py` | W = 8.80×10⁻⁵ at κ_SD saturation | Bakry-Émery floor |
| `strong_field_uv_bound.py` | V_max bound, kink minimum length, EFT breakdown scale | V_max = 3.435×10⁻³ GeV⁴; a_kink = 6.80×10⁻¹⁶ m; EFT breaks at M=1.81 (CatAD) |
| `hawking_kink_emission.py` | Two critical masses for kink Hawking emission; Bose enhancement | M_kink_crit = (49/8)M_crit = 2.044×10⁴⁰ MeV; Planck factor 5.64 at M_crit (CatAD) |
| `hypergraph_cmca_curvature_comparison.py` | Deviation-based Ollivier–Ricci κ for Rule 110/124/30/90; vacuum flatness + C_Gorard specificity | κ_EE=0 universal; κ_SD≈10/13 universal; C_Gorard=3/32 CMCA-specific (CatA) |

### Running the Hawking radiation script

```bash
cd papers/44_quantum_gravity
python3 scripts/hawking_radiation_phimdl.py
```
Expected: M_crit = 3.34×10³⁹ MeV; T_H formula verified at several M_BH values.

### Running the bounce dynamics script

```bash
python3 scripts/flrw_gte_bounce.py
```
Expected: f_C(1) = 0 (bounce at ρ_Pl); ḢB = 3/π² ≈ 0.304; T_reh = 6.49×10⁸ GeV.

### Running the MDL initial state scoring

```bash
python3 scripts/mdl_initial_state_scoring.py
```
Expected: unique minimum at k=0, Φ₀=0, Φ̇₀=M_Pl with K_tot = log₂(3) = 1.585 bits.

### Running the Ω_Λ structural prediction check

The numerical value Ω_Λ = (ln2/3π) × log₂(2000/3) ≈ 0.6899 can be verified:
```python
import numpy as np
L_model = np.log2(2000/3)
omega = np.log(2) / (3 * np.pi) * L_model
print(f"Omega_Lambda = {omega:.4f}")  # Expected: 0.6899
```

## Cosmological constant prediction verification

Formula: Ω_Λ = (ln2/3π) × log₂(2000/3) = 0.6899
Planck 2018: Ω_Λ^obs = 0.6889 ± 0.0056 (+0.18σ)
No free parameters; no dimensional input.

## Lean PSP interval bound

Lean theorem `omega_lambda_gte_approx` (commit 09145e8) certifies:
|Ω_Λ^GTE − 0.690| < 0.001 via interval arithmetic (zero sorry).
