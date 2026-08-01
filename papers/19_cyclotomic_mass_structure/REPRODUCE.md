# Reproducing All Results in "Cyclotomic-12 Structure in the Charged-Fermion Mass Spectrum"

**Paper:** Nova Spivack, *Cyclotomic-12 Structure in the Charged-Fermion Mass Spectrum:
A₂ Weyl-Chamber Geometry, Froggatt-Nielsen UV Completion, and Three Null-Discipline Tests
on the Down-Sector Coefficients*, 2026.

---

## Prerequisites

- Python 3.9 or later
- `numpy`, `scipy` (any recent version)
- Lean 4.29.0-rc6 + Mathlib (for formal proofs)

```bash
pip install numpy scipy
```

No GPU, no external optimization, no random seeds.

---

## Canonical computation artifacts

All computation artifacts for this paper live in:

```
papers/01_SM/canonical_run/
```

They are shared with Paper 1 (the UGP SM paper~\cite{Spivack2026_SM_UGP}) since they
were computed in the same verification campaign.

---

## TT relation (SC-TT)

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_TT_up_lepton_cyclotomic_identity.py
```

**Expected key outputs (in `comp_p01_TT_up_lepton_cyclotomic_identity.json`):**

| Field | Expected value |
|-------|---------------|
| `alpha_LS` | 0.5225 |
| `alpha_match_pi_6_within_0p5pct` | `true` |
| `null_density_random_fits_at_0p5pct` | `6e-6` |
| `verdict` | `STRUCTURAL_CANDIDATE_BREAKTHROUGH_up_lepton_alpha_pi_6` |

SHA-256 of output JSON (first 16 hex): `d8227f9d651b3d95`

---

## VV relation (SC-VV)

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_VV_down_linked_to_up_lepton.py
```

**Expected key outputs (in `comp_p01_VV_down_linked_to_up_lepton.json`):**

| Field | Expected value |
|-------|---------------|
| `n_structural_candidates` | 1 |
| `structural_candidates[0].max_pct_off_of_any_coef` | < 0.3% |
| `structural_candidates[0].exact_solution` | `[1.4467, -1.1695, -0.3582]` |
| `structural_candidates[0].null_density` | 0.0 |

SHA-256 of output JSON (first 16 hex): `10f1bb1e099d444d`

---

## β discrimination (SC-EEE)

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_EEE_beta_discrimination.py
```

**Expected key outputs:**

| Candidate β | Expected max σ | Status |
|-------------|---------------|--------|
| `π/8` (structural) | 2.55 | consistent |
| `1/φ²` (golden-ratio) | 3.62 | excluded |
| `2/5` (rational) | 6.75 | excluded |

SHA-256 of output JSON (first 16 hex): `120fd2aa2d2270f1`

---

## SC-JJJ: GUT-representation basis saturation

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_JJJ_vv_gut_saturation_null.py
```

**Expected key outputs:**

| Field | Expected value |
|-------|---------------|
| Hits for α_VV=13/9 at tol 1e-5 | 74 |
| Hits for β_VV=-7/6 at tol 1e-5 | 742 |
| Hits for γ_VV=-5/14 at tol 1e-5 | 94 |
| Triple-null at tol 1e-3 | 54.3% |

Basis pre-commit SHA-256: `644a7f90bc9682db672a8d8920df80a2c481e232c10f44c316a1321b626e8899`

SHA-256 of output JSON (first 16 hex): `f82288b4e6816cfe`

---

## SC-KKK: FN integer-charge obstruction

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_KKK_vv_rg_derivation.py
```

**Expected verdict:**
```
OUTCOME B (MAP): no FN-doubled assignment reproduces VV via SM RG (best candidate at 343.2%).
[C] classification of VV coefficient-value interpretations is further supported.
```

SHA-256 of output JSON (first 16 hex): `e9956111050db7b6`

---

## SC-LLL: Discrete-flavor basis saturation

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_LLL_vv_discrete_flavor_null.py
```

**Expected key outputs:**

| Field | Expected value |
|-------|---------------|
| Expressions count | 610,421 |
| Triple-null at tol 1e-3 | 39.8% |
| Basis pre-commit SHA-256 | `dc210d12...` |

SHA-256 of output JSON (first 16 hex): `db997f06ff06160f`

---

## CKM Phase-1 (SC-BBB)

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_BBB_ckm_from_tt_vv.py
```

SHA-256 of output JSON (first 16 hex): `ef33c48fa938e3fa`

---

## Cabibbo derivation from α_d (CDM)

The Wolfenstein parameter λ ≈ ε₁^(α_d) = exp(−13π/27) ≈ 0.2203 (1.9% from PDG 0.2245)
is derived in §Open Problem 3 from the VV coefficient α_d = 13/9 as an effective
Froggatt–Nielsen charge. The computation artifact is shared with P01:

```bash
cd papers/01_SM/canonical_run
python3 comp_p19_CDM_cabibbo_mechanism.py
```

The Lean-certified theorems (`cabibbo_effective_charge`, `cdm_mechanism_summary`, etc.)
are in `UgpLean.MassRelations.CKMMixing` (11 theorems, zero sorry).

---

## Lean 4 formal proofs

The machine-checked proofs are in the companion Lean 4 repository:

```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean
lake build
```

**Expected result:** build completes with 8198 jobs, 0 errors, 0 warnings,
no `sorry` in any module under `UgpLean.MassRelations`.

**Key modules to verify:**

```
UgpLean.MassRelations.SU3FlavorCartan
UgpLean.MassRelations.BinaryCascade
UgpLean.MassRelations.FroggattNielsen
UgpLean.MassRelations.CartanFlavonPotential
UgpLean.MassRelations.Z2OrbifoldDepth
UgpLean.MassRelations.HeavyFermionTower
UgpLean.MassRelations.PhysicalMasses
```

---

## Artifact SHA-256 summary

| Artifact | File | SHA-256 (first 16 hex) |
|----------|------|------------------------|
| SC-TT | `comp_p01_TT_up_lepton_cyclotomic_identity.json` | `d8227f9d651b3d95` |
| SC-VV | `comp_p01_VV_down_linked_to_up_lepton.json` | `10f1bb1e099d444d` |
| SC-EEE | `comp_p01_EEE_beta_discrimination.json` | `120fd2aa2d2270f1` |
| SC-JJJ | `comp_p01_JJJ_vv_gut_saturation_null.json` | `f82288b4e6816cfe` |
| SC-KKK | `comp_p01_KKK_vv_rg_derivation.json` | `e9956111050db7b6` |
| SC-LLL | `comp_p01_LLL_vv_discrete_flavor_null.json` | `db997f06ff06160f` |
| SC-BBB | `comp_p01_BBB_ckm_from_tt_vv.json` | `ef33c48fa938e3fa` |

---

## What NOT to include (for reproducibility bundles)

- Raw `.db` database files
- `Backups/` folder
- Private paths or internal development notes
- Any file referencing absolute local paths

---

## Citation

If you use these results, please cite:

> N. Spivack, "Cyclotomic-12 Structure in the Charged-Fermion Mass Spectrum:
> A₂ Weyl-Chamber Geometry, Froggatt-Nielsen UV Completion, and Three
> Null-Discipline Tests on the Down-Sector Coefficients," 2026.
> Code: https://github.com/novaspivack/ugp-physics (DOI upon publication).
> Lean proofs: https://github.com/novaspivack/ugp-lean (DOI: 10.5281/zenodo.19554700).
