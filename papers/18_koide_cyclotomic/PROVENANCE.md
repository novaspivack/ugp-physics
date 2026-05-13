# Provenance: Koide Cyclotomic-12 Closed Form Paper (P18)

**Paper:** *A Cyclotomic-12 Closed Form for Koide's Relation and Its Structural Origin from N_c = 3*
**Author:** Nova Spivack
**Status:** In preparation

---

## Paper Claims

The paper is a standalone charged-lepton result.  The first three observations are elementary facts about the charged-lepton mass eigenvalues and do not depend on any physics framework; the fourth observation identifies a structural origin within the UGP framework.

### Elementary observations (framework-independent)

| Claim | Content | Status |
|-------|---------|--------|
| Koide = 45° cone | `Q(m_e, m_μ, m_τ) = 2/3` iff `angle(√m, ê) = π/4` | elementary; machine-verified |
| Closed-form m_τ | `√m_τ = 2(√m_e + √m_μ) + √3 · √(m_e + 4√(m_e m_μ) + m_μ)` | machine-verified; 61 ppm against PDG |
| Cyclotomic-12 identity | surd coefficients satisfy `(2+√3) = 4 cos²(π/12)` and `(1+√3)² = 8 cos²(π/12)` | machine-verified |
| Empirical angle | `angle(v, ê) = 44.99974°` (0.95 arcseconds from π/4) | PDG input |

### Structural origin (within UGP framework)

| Claim | Content | Status |
|-------|---------|--------|
| θ = (N_c²−1)/(4N_c²) | Strand-count identity; θ = 2/9 from N_c = 3 | Lean `koide_angle_from_N_c_pure` |
| Full N_c chain | `δ = 7`, `b_1 = 73`, `a_top = 76` all from N_c = 3 | Lean `N_c_determines_everything` |
| Neutrino bridge | `N_c + θ = 29/9` controls neutrino mass-squared ratio to 0.4% | Lean `nuSeesawExponent`, `nu_seesaw_exponent_three_decompositions` |
| Cross-identity | `dim(126_SO(10)) = 2 N_c² δ = 126` | Lean `dim_126_SO10_eq_two_Nc_sq_delta` |

### Auxiliary dynamical result

| Claim | Content | Status |
|-------|---------|--------|
| S_3-Newton flow | S_3-equivariant Newton-step operator has the Koide null cone as attractor set | Lean `KoideNewtonFlow.*` |

---

## Lean Provenance

All Lean theorems are in the public `ugp-lean` repository (<https://github.com/novaspivack/ugp-lean>).

| Module | Role |
|--------|------|
| `UgpLean.MassRelations.KoideClosedForm` | Closed-form m_τ prediction; cyclotomic-12 surd identities |
| `UgpLean.MassRelations.KoideAngle` | θ = (N_c²−1)/(4 N_c²) = 2/9 derivation; full N_c structural chain |
| `UgpLean.MassRelations.KoideNewtonFlow` | S_3-equivariant Newton-step dynamical realisation |
| `UgpLean.MassRelations.LeptonMassPrediction` | End-to-end lepton mass pipeline |

Reproduce all theorems by cloning the repository and running `lake build` (Lean 4.29.0-rc6, Mathlib 4.29.0-rc6).  Zero `sorry`; standard Mathlib axiom signature `[propext, Classical.choice, Quot.sound]`.

---

## Computational Artifacts

The structural origin of the Koide phase (observation 4) is verified by standalone Python scripts in `papers/01_SM/canonical_run/` (shared with Paper 1).

| File | Description |
|------|-------------|
| `comp_p01_EBF_09_deep_muon_structure.py` | Identifies θ = 2/9 from UGP integer a_μ = 9 |
| `comp_p01_EBF_10_koide_universality.py` | Universality test: Q = 2/3 is charged-lepton-specific |
| `comp_p01_EBF_11_koide_angle_structural_search.py` | Discovery of universal a-value pattern {1, 5, 9} |
| `comp_p01_EBF_12_top_quark_and_s3_angle.py` | Top-quark a-value from N_c; structural derivation of δ = 7, b_1 = 73 |
| `comp_p01_EBF_13_s3_koide_angle_proof.py` | strand_count = (N_c²−1)/4 = 2; θ = strand_count/N_c² = 2/9 from N_c = 3 |
| `comp_p01_L_koide_from_s3.py` | Koide as S_3 equal-norm condition |
| `comp_p01_O_koide_ridge_amplitude.py` | Koide as asymptotic UGP ridge-amplitude limit |
| `comp_p01_R_koide_S3_quadric.py` | Koide as unique S_3-invariant null quadric; null test: 0 of 10 000 random triples closer to the null cone |

Each script is independently reproducible with Python 3.9+, `numpy`, and (where used) `scipy`/`sympy`.  Each `.json` artifact carries a SHA-256 hash.

---

## PDG Data Provenance

All experimental charged-lepton masses are from the 2022 PDG *Review of Particle Physics*.
- URL: <https://pdg.lbl.gov/2022/>
- Citation: R. L. Workman et al. (Particle Data Group), Prog. Theor. Exp. Phys. 2022, 083C01.

Reference values:
- m_e = 0.51099895000(15) MeV
- m_μ = 105.6583755(23) MeV
- m_τ = 1776.86(12) MeV

---

## Related Papers

| Paper | Role |
|-------|------|
| `Spivack2026_SM_UGP` (P01) | Parent paper; UGP framework; N_c structural chain is presented there alongside P18 |
| `Spivack2026_CyclotomicMass` (P19) | Sister paper; TT/VV structural mass relations |
| `ugp-lean` | Lean 4 library containing all formal proofs |
