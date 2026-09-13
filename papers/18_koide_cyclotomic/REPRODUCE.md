# Reproduction Guide: Koide Cyclotomic-12 Closed Form (P18)

This document provides step-by-step reproduction instructions for every quantitative claim in the paper.

## Requirements

- **Python 3.9+** with `numpy` (required), `scipy`, `sympy` (optional — used by a subset of scripts)
- **Lean 4.29.0-rc6** with **Mathlib 4.29.0-rc6** for the machine-checked identities
- `git` for cloning the two public repositories

## 1. Numerical closed-form verification (61 ppm m_τ prediction)

Clone the `ugp-physics` repository and run the closed-form computation directly:

```bash
git clone https://github.com/novaspivack/ugp-physics
cd ugp-physics/papers/01_SM/canonical_run
python3 -c "
import math
m_e = 0.5109989500e-3   # PDG m_e in GeV
m_mu = 105.6583755e-3   # PDG m_mu in GeV
m_tau_pdg = 1776.86e-3  # PDG m_tau in GeV
# Koide cyclotomic-12 closed form:
sqrt_mt = 2*(math.sqrt(m_e) + math.sqrt(m_mu)) + math.sqrt(3)*math.sqrt(m_e + 4*math.sqrt(m_e*m_mu) + m_mu)
m_tau_pred = sqrt_mt**2
print(f'Predicted m_tau = {m_tau_pred*1000:.3f} MeV')
print(f'PDG m_tau       = {m_tau_pdg*1000:.3f} MeV')
print(f'Relative error  = {1e6*(m_tau_pred - m_tau_pdg)/m_tau_pdg:.1f} ppm')
"
```

Expected output: `Predicted m_tau ≈ 1776.969 MeV`, relative error ≈ 61 ppm.

## 2. Structural origin from N_c (observation 4)

The structural identification of the Koide phase as θ = (N_c² − 1)/(4 N_c²) = 2/9 is verified by:

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_EBF_09_deep_muon_structure.py      # identifies θ = 2/a_μ = 2/9
python3 comp_p01_EBF_11_koide_angle_structural_search.py  # discovers a-value pattern {1,5,9}
python3 comp_p01_EBF_12_top_quark_and_s3_angle.py         # derives δ=7, b_1=73, a_top=76 from N_c
python3 comp_p01_EBF_13_s3_koide_angle_proof.py           # verifies strand_count = (N_c²−1)/4 = 2; θ = 2/9 from N_c = 3
```

Each script emits a JSON artifact in the same directory with a SHA-256 hash.

## 3. Auxiliary null-test artifacts

```bash
python3 comp_p01_L_koide_from_s3.py           # Koide as S_3 equal-norm condition
python3 comp_p01_O_koide_ridge_amplitude.py   # Koide as asymptotic UGP ridge-amplitude limit
python3 comp_p01_R_koide_S3_quadric.py        # Koide as unique S_3-invariant null quadric (null test: 10 000 random triples)
```

## 3b. Generation-Yukawa cone decomposition (amplitude √2 pinning)

The decomposition of the Koide cone parametrisation √m_g = a(1 + √2·cos(θ + 2πg/3))
into its democratic (trivial S₃-irrep) and orbit (standard S₃-irrep) components, and
the verification that the cone amplitude √2 is forced by the equal-irrep-norm /
Q = 2/3 condition, are reproduced by:

```bash
cd papers/18_koide_cyclotomic/scripts
python3 koide_yukawa_mechanism.py
```

Expected: lepton-mass sanity check max error 0.0054%; Koide Q on the cone amplitudes
= 0.666667; m_μ/m_e = 206.770 (0.001% vs PDG); trivial-irrep norm = standard-irrep
norm = √3 (equal-norm); cone amplitude b = √2 = √(dim standard rep); amplitudes
b = 1.0 and b = 1.5 give Q = 0.500 and 0.708 respectively (only √2 gives 2/3). The
script emits `koide_yukawa_mechanism_results.json`.

## 3c. Equal-irrep-norm mechanism and CV(√m)=1 reformulation

The origin of the cone amplitude √2 (the equal trivial/standard S₃-irrep-norm
condition) is analysed by:

```bash
cd papers/18_koide_cyclotomic/scripts
python3 koide_equalnorm_mechanism.py
```

Expected: the raw orbit a-values {1,9,5} have Z₃-Fourier magnitudes |A_k|² = [225,48,48]
and do NOT satisfy the equal-mode condition (225 ≠ 96) — the equal-irrep-norm is not
inherited from the discrete orbit labels; the cone (b = √2) has coefficient of variation
CV(√m) = 1 exactly for every phase θ, with the Koide quotient satisfying Q = (1+CV²)/3
(so Q = 2/3 ⟺ CV = 1, i.e. the √-mass standard deviation equals its mean); an
exponential (maximum-entropy at fixed mean) spectrum has CV = 1; and the equal-norm
output of a symmetric Z₃ kernel is a codimension-1 locus 2r²+8r−1 = 0. The script emits
`koide_equalnorm_mechanism_results.json`.

The origin of CV(√m) = 1 is examined further by:

```bash
cd papers/18_koide_cyclotomic/scripts
python3 koide_cv_origin.py
```

Expected: the hypothesis m_g ∝ a_g (orbit labels {1,9,5}) gives Koide Q = 0.386 and
CV = 0.396 — failing both the Koide and CV = 1 conditions (the orbit labels are not the
√-mass amplitudes); no a_g-based mass-generation model (exponential, linear, power-law)
reproduces both CV = 1 and the real mass ratios without fitting; and the Koide quotient
equals the inverse participation ratio Σp² (Simpson / Rényi-2 index) of the normalized
√-mass vector, so the Koide relation is exactly the statement that the participation
ratio is N_gen/2 = 3/2. The script emits `koide_cv_origin_results.json`.

## 3d. Origin of the generation (flavour) permutation symmetry

The block decomposition (trivial 1 ⊕ standard 2) that the equal-irrep-norm
argument uses is supplied by the cyclic Z₃ generation symmetry — the Z₃ factor
of the Φ_MDL automorphism group F₂₁ = Z₇ ⋊ Z₃ (all three charged leptons share
the same Z₇ winding w = 4) — not by an imposed S₃, and not by the (distinct)
spatial three-tape S₃:

```bash
cd papers/18_koide_cyclotomic/scripts
python3 koide_s3_derivation.py
```

Expected (`koide_s3_derivation_results.json`):
- Part A: three identical tapes give an exact S₃ (and Z₃) commutator (max ≈ 4.4×10⁻¹⁶);
  this is the spatial x/y/z tape symmetry, explicitly NOT the flavour symmetry.
- Part B: cyclic Z₃ on ℝ³ has real-irrep dimensions {1, 2} — identical to the
  S₃ decomposition ℝ³ = 1 ⊕ 2 — and equipartition of the two irrep types forces
  b² = 2, b = √2, Koide Q = 2/3 (θ-independent).
- Part C: the mechanism is N-universal — equipartition gives b² = 2 for every
  N_gen ≥ 3, with Q = 2/N_gen, equal to 2/3 precisely because N_gen = 3.
- Part D (null tests): (1) at N_gen = 2 the standard irrep is 1-dimensional
  (1 ⊕ 1), so the amplitude becomes θ-dependent (no universal b = √2) and the
  spectrum degenerates; (2) a distinguishing label on one generation/tape breaks
  the permutation symmetry, while the same label applied democratically preserves
  it; (3) only N_gen = 3 yields Q = 2/3.

The script uses a fixed NumPy seed; its JSON artifact is bit-exact reproducible.

## 4. Machine-checked Lean proofs

Clone the `ugp-lean` repository and verify every theorem in the paper:

```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean
lake exe cache get           # downloads pre-compiled Mathlib
lake build UgpLean.MassRelations.KoideClosedForm
lake build UgpLean.MassRelations.KoideAngle
lake build UgpLean.MassRelations.KoideNewtonFlow
lake build UgpLean.MassRelations.LeptonMassPrediction
lake build UgpLean.MassRelations.KoideYukawaAmplitude
lake build UgpLean.MassRelations.KoideEqualNormReformulation
lake build UgpLean.MassRelations.KoideIrrepEqualNorm
lake build UgpLean.MassRelations.KoideGenerationCyclicSymmetry
```

Module `KoideGenerationCyclicSymmetry` adds `cone_cyclic_shift_0/1/2` (the cyclic
generation generator acts on the cone as the phase shift θ ↦ θ + 2π/3),
`cone_trivial_block_cyclic_invariant`, `cone_total_norm_cyclic_invariant`, and
`koide_amplitude_from_cyclic_generation_symmetry` (under the cyclic Z₃ generation
symmetry, MDL equipartition forces b = √2, b² = d_standard(S₃) = 2, Q = 2/3 for
every θ). This certifies that the flavour symmetry behind the Koide cone is the
cyclic Z₃ generation factor of F₂₁ = Z₇ ⋊ Z₃, which over ℝ supplies the same
1 ⊕ 2 block structure as S₃ without requiring the S₃ transpositions.

Module `KoideYukawaAmplitude` adds `koide_Q_iff_amplitude` (Q = 2/3 ⟺ b² = 2, for
every phase θ), `equal_norm_iff_amplitude`, `cone_amplitude_eq_sqrt2` (b ≥ 0 and
Q = 2/3 ⟹ b = √2), and `koide_cone_pinned`, certifying that the cone amplitude √2 is
the equal trivial/standard S₃-irrep-norm condition.

Module `KoideEqualNormReformulation` adds `koide_cv_one_iff_amplitude` (Var = mean² ⟺
b² = 2, i.e. equal-irrep-norm ⟺ coefficient of variation CV(√m) = 1),
`koide_Q_eq_one_third_one_plus_cv_sq` (Q = (1+CV²)/3 for every (b,θ)), and the certified
negative `lepton_a_values_not_equal_modes` (the raw orbit a-values {1,9,5} fail the
equal-Fourier-mode condition: 2·(1+9+5)² ≠ 3·(1²+9²+5²), i.e. 450 ≠ 321).

Each module builds with zero `sorry`.  Axiom signature: `#print axioms <theorem_name>` returns the standard Mathlib signature `[propext, Classical.choice, Quot.sound]` with no UGP-specific axioms.

## 5. Expected runtime

- Numerical closed-form: < 1 second
- Each standalone Python script: < 60 seconds
- Full Lean build (clean): 30–60 minutes (depends on machine and Mathlib cache)

## Deterministic reproducibility

All numerical results are deterministic.  No RNG or stochastic search is involved in the closed-form claims.  The null-test scripts use explicitly seeded NumPy generators so their JSON artifacts are bit-exact reproducible across platforms.
