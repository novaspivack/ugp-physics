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
```

Each module builds with zero `sorry`.  Axiom signature: `#print axioms <theorem_name>` returns the standard Mathlib signature `[propext, Classical.choice, Quot.sound]` with no UGP-specific axioms.

## 5. Expected runtime

- Numerical closed-form: < 1 second
- Each standalone Python script: < 60 seconds
- Full Lean build (clean): 30–60 minutes (depends on machine and Mathlib cache)

## Deterministic reproducibility

All numerical results are deterministic.  No RNG or stochastic search is involved in the closed-form claims.  The null-test scripts use explicitly seeded NumPy generators so their JSON artifacts are bit-exact reproducible across platforms.
