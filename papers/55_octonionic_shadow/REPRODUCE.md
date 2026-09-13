# REPRODUCE — P55: The Octonionic Shadow of GF(7)

Complete step-by-step reproduction instructions for all results in
"The Octonionic Shadow of GF(7): Color, Chirality, and Three Generations
from a Quadratic-Residue Difference Set."

---

## Prerequisites

- Python ≥ 3.10 with: `numpy`, `scipy`, `matplotlib`
- Lean 4 with Mathlib (for Lean module verification)
- `pdflatex` + BibTeX (for paper compilation)

Install Python dependencies:
```bash
pip install numpy scipy matplotlib
```

---

## Step 1: Run all verification scripts

All scripts are in `papers/55_octonionic_shadow/scripts/`. Run from the
paper directory or specify the full path. Each script exits 0 on success.

```bash
cd papers/55_octonionic_shadow

# Theorem A, B, B': QR(7) design and octonion construction
python scripts/octonion_from_qr7.py

# Theorem C: Group layer, PSL(2,7) ≅ GL(3,2)
python scripts/psl27_group_layer.py
python scripts/hurwitz_coset_enumeration.py
# Produces: data/hurwitz_coset_certificate.json

# Theorem D, D', E: Color sector, UGP interface, G₂/SU(3) derivation
python scripts/f21_octonion_interface_verify.py
python scripts/g2_stabilizer_derivation.py
python scripts/g2_stabilizer_certificate_export.py
python scripts/furey_cl6_comparison.py

# Theorems F1–F5: Electroweak shadow
python scripts/quaternion_electroweak_shadow.py
python scripts/electroweak_housing_closure.py

# Proposition O1': Hypercharge generator Y=N/3
python scripts/hypercharge_group_derivation.py
# Produces: data/hypercharge_group_derivation_results.json

# Theorem G0: Generation no-gos
python scripts/generations_triality_nogo.py

# Theorems G1–G6: Triality interface
python scripts/positive_triality_theorems.py

# Theorem G6 Eisenstein norm selection
python scripts/triality_identification_discriminator.py
# Produces: data/triality_identification_discriminator_results.json

# Theorem H2: Koide cyclic invariance
python scripts/triality_pairing_alternative_test.py
# Produces: data/triality_pairing_alternative_test_results.json

# Remark: σ-action (Z₂ parity on kink quantum numbers)
python scripts/kink_sigma_parity_action.py
# Produces: data/kink_sigma_parity_action_results.json

# Sector triality action + Callias no-go theorem
python scripts/kink_dirac_index_nogo.py
# Produces: data/kink_dirac_index_nogo_results.json

# Theorem H3 extension: Higher seed norms
python scripts/higher_seeds_cyclotomic_norms.py
# Produces: data/higher_seeds_cyclotomic_norms_results.json

# ζ₅ null test (Remark in §7)
python scripts/cyclotomic_norm_null_test.py
# Produces: data/cyclotomic_norm_null_test_results.json

# §7: Seesaw mass formula, RH neutrino Eisenstein pinning, NO prediction
python scripts/rh_neutrino_pinning.py
# Produces: scripts/rh_neutrino_pinning_results.json

# §8: Braid-atlas exchange statistics (S₃ non-equivariance)
python scripts/triple_exchange_s3_equivariance.py
# Produces: data/triple_exchange_s3_equivariance_results.json

# §8 base-rate analysis: joint classification of chain steps
python scripts/base_rate_analysis_qr7_chain.py
# Produces: data/base_rate_analysis_results.json
```

All scripts must exit 0 with no assertion errors.

---

## Step 2: Produce figures

```bash
cd papers/55_octonionic_shadow

# Figure F1: Fano plane
python figures/make_fano_plane.py
# Produces: figures/fano_plane_qr7.pdf

# Figure F3: Weight ladder
python figures/make_weight_ladder.py
# Produces: figures/weight_ladder.pdf

# Figure F5: Triality diagram
python figures/make_triality_diagram.py
# Produces: figures/triality_diagram.pdf

# Figure F6: Koide circle
python figures/make_koide_circle.py
# Produces: figures/koide_circle.pdf
```

Figure F2 is a TikZ diagram compiled inline with the paper.

---

## Step 3: Verify Lean modules

The Lean modules are in the `ugp-lean` library. Build from the repository root:

```bash
cd /path/to/ugp-lean
lake build UgpLean.Algebra.OctonionShadowInterface
lake build UgpLean.Algebra.HurwitzCosetCertificate
lake build UgpLean.Algebra.G2StabilizerCertificate
lake build UgpLean.Algebra.TrialityInterface
lake build UgpLean.Algebra.OctonionColorFlavorDisambiguation
lake build UgpLean.Algebra.KinkSigmaParityAction
lake build UgpLean.Algebra.KinkSectorTrialityAction
lake build UgpLean.Spacetime.PhiMDLZeroModeIndex
lake build UgpLean.Algebra.BraidAtlasPhaseEquivariance
lake build UgpLean.MassRelations.SeesawNumericalCerts
lake build UgpLean.MassRelations.SeesawTrialityPinning
```

Or build the entire library:
```bash
lake build UgpLean
```

Verify zero sorry in all P55 modules:
```bash
grep -c "sorry" UgpLean/Algebra/OctonionShadowInterface.lean
grep -c "sorry" UgpLean/Algebra/HurwitzCosetCertificate.lean
grep -c "sorry" UgpLean/Algebra/G2StabilizerCertificate.lean
grep -c "sorry" UgpLean/Algebra/TrialityInterface.lean
grep -c "sorry" UgpLean/Algebra/OctonionColorFlavorDisambiguation.lean
grep -c "sorry" UgpLean/Algebra/KinkSigmaParityAction.lean
grep -c "sorry" UgpLean/Algebra/KinkSectorTrialityAction.lean
grep -c "sorry" UgpLean/Spacetime/PhiMDLZeroModeIndex.lean
grep -c "sorry" UgpLean/Algebra/BraidAtlasPhaseEquivariance.lean
grep -c "sorry" UgpLean/MassRelations/SeesawNumericalCerts.lean
grep -c "sorry" UgpLean/MassRelations/SeesawTrialityPinning.lean
# All should output 0
```

---

## Step 4: Verify the predictions registry hash

The normal-ordering prediction is pre-registered in `papers/common/predictions/`.
Verify the SHA-256 hash matches the committed registry file:

```bash
cd /path/to/ugp-physics
python3 papers/common/predictions/verify_predictions_hash.py
```

Expected output: exit 0 with a message confirming the hash matches
`d9ae2ebf2185862c7d56a5b662af35892bf3cb5f2ef262b147b2241ab2c53f25`.

---

## Step 5: Compile the paper

```bash
cd papers/55_octonionic_shadow
pdflatex octonionic_shadow_paper.tex
bibtex octonionic_shadow_paper
pdflatex octonionic_shadow_paper.tex
pdflatex octonionic_shadow_paper.tex
```

The final output is `octonionic_shadow_paper.pdf`.

---

## Numerical values to check

After running the scripts, confirm these key outputs appear in the results:

| Claim | Expected value | Script |
|-------|---------------|--------|
| Koide angle | 0.222229631 rad = 2/9 + 7.41×10⁻⁶ | `electroweak_housing_closure.py` |
| Koide Q | 0.6666605 (≈ 2/3 − 6×10⁻⁶) | `electroweak_housing_closure.py` |
| Frame group order | 1344 = 2³ × 168 | `octonion_from_qr7.py` |
| Valid Cayley tables | 480 of 3840 | `octonion_from_qr7.py` |
| PSL(2,7) order | 168 | `hurwitz_coset_enumeration.py` |
| G₂ dimension | 14 | `g2_stabilizer_derivation.py` |
| SU(3) stabilizer dim | 8 | `g2_stabilizer_derivation.py` |
| b_gen1 Eisenstein | 73 = N(9+ω) ✓ | `triality_identification_discriminator.py` |
| b_gen2 Eisenstein | 42: NOT a norm ✗ | `higher_seeds_cyclotomic_norms.py` |
| b_gen3 Eisenstein | 275: NOT a norm ✗ | `higher_seeds_cyclotomic_norms.py` |
| Callias gap | 0.17–0.20 | `kink_dirac_index_nogo.py` |
| S₃ distinct permutations | 6 | `kink_dirac_index_nogo.py` |
| ζ₅ norm density | 8% in [200,350] | `cyclotomic_norm_null_test.py` |
| Y=N/3 anomaly tr Y | 4 | `hypercharge_group_derivation.py` |
| Y=N/3 anomaly tr Y³ | 2 | `hypercharge_group_derivation.py` |
| NO confirmed (m_ν₁ < m_ν₂ < m_ν₃) | 0.679 / 8.612 / 50.110 meV | `rh_neutrino_pinning.py` |
| GTE Δm²₂₁/Δm²₃₁ ratio | 0.0294 (PDG: 0.0295) | `rh_neutrino_pinning.py` |
| Triple exchange equivariant subgroup | Z₂ = {e, σρ²} only | `triple_exchange_s3_equivariance.py` |
| gen3 exchange phase (Q_φ=3) | +1 (bosonic) | `triple_exchange_s3_equivariance.py` |
| gen1/gen2 exchange phases (Q_φ=4) | −1 (fermionic) | `triple_exchange_s3_equivariance.py` |
| Chain theorem-joints / selection-joints | 11 theorem-joints, 2 selection-joints | `base_rate_analysis_qr7_chain.py` |
| Koide angle p-value (uniform null) | ≈ 1.41×10⁻⁵ | `base_rate_analysis_qr7_chain.py` |
