# PROVENANCE — P55: The Octonionic Shadow of GF(7)

**Paper:** "The Octonionic Shadow of GF(7): Color, Chirality, and Three Generations from a Quadratic-Residue Difference Set"  
**Author:** Nova Spivack  
**Series:** UGP Physics Programme, Paper P55  
**Date:** July 2026  
**Status:** Preprint (Zenodo DOI pending deposition)

---

## Source of Claims

All claims in this paper originate from one of three provenance types:

### Type 1: Verification scripts (CatA)

Located in `papers/55_octonionic_shadow/scripts/`. Each script runs assertion-checked
computations; a clean exit (exit code 0) constitutes the verification.

| Script | Theorems supported |
|--------|-------------------|
| `octonion_from_qr7.py` | Thm A, Thm B |
| `psl27_group_layer.py` | Thm C |
| `hurwitz_coset_enumeration.py` | Thm C (+ certificate export) |
| `f21_octonion_interface_verify.py` | Thm D, D', E (UGP interface) |
| `g2_stabilizer_derivation.py` | Thm E |
| `g2_stabilizer_certificate_export.py` | Thm E (certificate) |
| `quaternion_electroweak_shadow.py` | Thms F1–F4 |
| `electroweak_housing_closure.py` | Thm F5, H1, H2, H3 |
| `hypercharge_group_derivation.py` | Prop O1' |
| `generations_triality_nogo.py` | Thm G0 |
| `positive_triality_theorems.py` | Thms G1–G6 |
| `triality_identification_discriminator.py` | Thm G6 (Eisenstein norm) |
| `triality_pairing_alternative_test.py` | Thm H2 (cyclic invariance) |
| `kink_sigma_parity_action.py` | Remark (Z₂ parity) |
| `kink_dirac_index_nogo.py` | Sector action + Callias no-go |
| `higher_seeds_cyclotomic_norms.py` | Thm H3 extension |
| `cyclotomic_norm_null_test.py` | ζ₅ null test (Remark in §7) |
| `furey_cl6_comparison.py` | Thm D (Furey generator comparison) |
| `triple_exchange_s3_equivariance.py` | Remark (S₃ non-equivariance of exchange phases) |
| `base_rate_analysis_qr7_chain.py` | §8 base-rate classification of chain joints |
| `rh_neutrino_pinning.py` | §7 seesaw mass formula, NO prediction, Eisenstein pinning |

### Type 2: Lean 4 machine certificates (CatAL)

All Lean modules reside in the `ugp-lean` library, zero sorry.

| Module | Theorems | Sorry |
|--------|----------|-------|
| `Algebra/OctonionShadowInterface.lean` | 20 | 0 |
| `Algebra/HurwitzCosetCertificate.lean` | 7 | 0 |
| `Algebra/G2StabilizerCertificate.lean` | 39 | 0 |
| `Algebra/TrialityInterface.lean` | 20 | 0 |
| `Algebra/OctonionColorFlavorDisambiguation.lean` | 10 | 0 |
| `Algebra/KinkSigmaParityAction.lean` | 11 | 0 |
| `Algebra/KinkSectorTrialityAction.lean` | 12 | 0 |
| `Spacetime/PhiMDLZeroModeIndex.lean` | 9 | 0 |
| `Algebra/BraidAtlasPhaseEquivariance.lean` | 20 | 0 |
| `MassRelations/SeesawNumericalCerts.lean` | 10 | 0 |
| `MassRelations/SeesawTrialityPinning.lean` | 16 | 0 |

**Total:** 174 theorems across 11 modules, zero sorry.

### Type 3: Published references

External claims (Koide formula, Günaydin–Gürsey identification, Furey–Hughes
three-generation result) are cited to the published literature with verified
arXiv/DOI references. See `papers/bib/Spivack_Papers_Bibliography.bib`.

---

## Data Artifacts

Located in `papers/55_octonionic_shadow/data/`:

| Artifact | Produced by | Content |
|----------|-------------|---------|
| `hurwitz_coset_certificate.json` | `hurwitz_coset_enumeration.py` | 168-coset Todd–Coxeter table |
| `triality_identification_discriminator_results.json` | `triality_identification_discriminator.py` | Eisenstein norm discriminator output |
| `triality_pairing_alternative_test_results.json` | `triality_pairing_alternative_test.py` | Cyclic invariance test |
| `kink_sigma_parity_action_results.json` | `kink_sigma_parity_action.py` | σ-action on kink quantum numbers |
| `kink_dirac_index_nogo_results.json` | `kink_dirac_index_nogo.py` | Callias no-go + sector S₃ action |
| `hypercharge_group_derivation_results.json` | `hypercharge_group_derivation.py` | Y=N/3, anomaly traces |
| `higher_seeds_cyclotomic_norms_results.json` | `higher_seeds_cyclotomic_norms.py` | b_gen2, b_gen3 Eisenstein norm check |
| `cyclotomic_norm_null_test_results.json` | `cyclotomic_norm_null_test.py` | ζ₅ density null test |
| `base_rate_analysis_results.json` | `base_rate_analysis_qr7_chain.py` | Joint classification + base-rate statistics for chain |
| `triple_exchange_s3_equivariance_results.json` | `triple_exchange_s3_equivariance.py` | S₃ non-equivariance of exchange phases; equivariant subgroup |

**Note:** `rh_neutrino_pinning_results.json` (produced by `rh_neutrino_pinning.py`) saves
alongside the script in `scripts/` rather than `data/`.

---

## Figures

Located in `papers/55_octonionic_shadow/figures/`:

| Figure | File | Produced by |
|--------|------|-------------|
| F1 | `fano_plane_qr7.pdf` | `figures/make_fano_plane.py` |
| F2 | TikZ inline in paper | `octonionic_shadow_paper.tex` §5 |
| F3 | `weight_ladder.pdf` | `figures/make_weight_ladder.py` |
| F5 | `triality_diagram.pdf` | `figures/make_triality_diagram.py` |
| F6 | `koide_circle.pdf` | `figures/make_koide_circle.py` |

---

## Prediction Registry

The normal-ordering prediction in §7 of this paper is pre-registered in the
UGP corpus falsifiable-predictions registry:

| Field | Value |
|-------|-------|
| File | `papers/common/predictions/ugp_falsifiable_predictions_v1.md` |
| SHA-256 | `d9ae2ebf2185862c7d56a5b662af35892bf3cb5f2ef262b147b2241ab2c53f25` |
| Registry date | 2026-07-04 |
| Entry | #1 (Neutrino mass ordering — Normal Ordering, CatAL) |
| Verify | `python3 papers/common/predictions/verify_predictions_hash.py` |

The registry is deposited on Zenodo with SHA-256 companion and OpenTimestamps
notarization. Concept DOI: https://doi.org/10.5281/zenodo.21200551

---

## Relationship to Prior Work

- **P48** (`SpivackGTECompleteFramework`): The GTE complete framework paper. P55 provides a second,
  independent octonionic derivation of N_c=3, the charge spectrum, and N_gen=3; it does not
  supersede P48's arithmetic derivations.
- **P18** (`Spivack2026_Koide`): Koide closed form. P55 reinterprets θ=2/9 as a triality orbit coordinate.
- **Furey–Hughes 2025** (`FureyHughes2025`): Essential prior art for three-generation derivation from
  Spin(8) triality; predates Theorem G by ~10 months.

---

## Figure Provenance

All figures were generated by the scripts in `figures/`, using numerical values
from the verification scripts and data artifacts in this directory.
