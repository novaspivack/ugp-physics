# Topology Lab

Data-driven discovery of the mapping from **GTE triples (a, b, c)** to particle **quantum numbers** (charge, spin, family, generation), together with the Canonical Braid Atlas — the topological translation of those arithmetic relationships into braid-group predictions for the 12 fundamental fermions.

The work is organized as three sequential pillars (2a → 2a-R → 2b/2c):

---

## Directory structure

```
topology_lab/
├── pillar2a_rosetta_stone/      GTE → quantum number discovery (v1.0, 39 features, 67.7% accuracy)
├── pillar2a_refinement/         Enhanced discovery (360 features, XGBoost/LightGBM, >81%)
├── pillar2b_canonical_braid_atlas/  Topological translation of arithmetic patterns
└── pillar2c_foundational_fortification/  Formal proofs, dynamic braid analysis, MDL validation
```

Each subdirectory has its own `README.md` with detailed usage.

---

## Requirements

```bash
pip install numpy pandas scikit-learn sympy matplotlib seaborn scipy
pip install xgboost lightgbm   # pillar 2a-R and 2c
pip install gplearn             # optional — symbolic regression in 2a
pip install gmpy2               # optional — faster number theory in 2a
```

---

## Pillar 2a — GTE Rosetta Stone (`pillar2a_rosetta_stone/`)

Initial discovery of GTE-triple → quantum-number mappings using 39 number-theoretic features extracted from the 12 fundamental fermions.

**Key scripts:**

| Script | Role |
|---|---|
| `GTE_Feature_Extractor.py` | `GTEFeatureExtractor` — 39 number-theoretic features (Möbius μ, divisor σ/τ, modular residues, GCD ratios) |
| `Rosetta_Stone_Lab.py` | `RosettaStoneLab` — decision trees, Lasso, optional symbolic regression (gplearn); outputs `Rosetta_Stone_Report.md` |

```bash
cd topology_lab/pillar2a_rosetta_stone
python GTE_Feature_Extractor.py    # produces feature_matrix.csv
python Rosetta_Stone_Lab.py        # runs discovery protocol
```

**Result:** 67.7% accuracy on charge/spin/family/generation across 12 particles.

---

## Pillar 2a-R — Enhanced Rosetta Stone (`pillar2a_refinement/`)

Expanded feature space and advanced ML to push beyond the 67.7% ceiling.

**Enhancements:**
- 360 total features (9.2× expansion): 276 pairwise interaction terms, 30 non-linear transforms, 15 ratio features.
- XGBoost and LightGBM benchmarks; enhanced Lasso and symbolic regression with MDL scoring.

**Key scripts:**

| Script | Role |
|---|---|
| `GTE_Feature_Extractor_v2.py` | `GTEFeatureExtractorV2` — 360 features |
| `Rosetta_Stone_Lab_v2.py` | `RosettaStoneLabV2` — XGBoost/LightGBM + v2 features |
| `Advanced_Rosetta_Stone_Lab.py` | Deep ML pipelines (NN, RF, stacking) |
| `Focused_Rosetta_Stone_Lab.py` | Focused analysis targeting the hardest quantum numbers |

```bash
cd topology_lab/pillar2a_refinement
python GTE_Feature_Extractor_v2.py
python Rosetta_Stone_Lab_v2.py
```

---

## Pillar 2b — Canonical Braid Atlas (`pillar2b_canonical_braid_atlas/`)

Theoretical translation of the arithmetic patterns (from 2a-R) into topological predictions. Specifies the arithmetic-topological dictionary (Hypotheses S-1, F-1, G-1, Q-1) and the master table of target braid fingerprints for all 12 fermions.

This pillar is primarily a **theoretical framework document** (`Canonical_Braid_Atlas_v1.0.md`). The test file `test_atlas_math.py` verifies the underlying arithmetic.

```bash
cd topology_lab/pillar2b_canonical_braid_atlas
python test_atlas_math.py
```

See `pillar2b_canonical_braid_atlas/README.md` for the full theoretical framework.

---

## Pillar 2c — Foundational Fortification (`pillar2c_foundational_fortification/`)

Elevates the braid atlas from statistical correlations to **proven theorems**: formal derivations from fundamental symmetries, dynamic braid time-series analysis, and MDL compliance validation.

**Key achievements:**
- 81.1% accuracy (vs. 67.7% in v1.0) — identified as close to the theoretical maximum given the data.
- First integration of static number-theoretic features with dynamic braid time-series features.
- Uniqueness proof: no alternative mapping achieves better MDL score.
- Formal derivations of all mappings from symmetry first principles.

**Key scripts:**

| Script | Role |
|---|---|
| `DynamicBraidAnalyzer.py` | `DynamicBraidAnalyzer` — braid time-series, FFT/oscillation invariants |
| `Dynamic_Feature_Analysis.py` | `DynamicFeatureAnalyzer` — combines static + dynamic features, RF/LassoCV |
| `Advanced_Feature_Engineering.py` | `AdvancedFeatureEngineer` — stacked pipeline on dynamic analysis |

```bash
cd topology_lab/pillar2c_foundational_fortification
python DynamicBraidAnalyzer.py
python Dynamic_Feature_Analysis.py
```

See `pillar2c_foundational_fortification/README.md`, `Symmetry_Derivations.md`, and `MDL_Uniqueness_Proofs.md` for formal derivations.

---

## Progression summary

| Pillar | Features | Best accuracy | Method |
|---|---|---|---|
| 2a | 39 | 67.7% | Decision trees, Lasso, symbolic regression |
| 2a-R | 360 | >81% | XGBoost, LightGBM, enhanced symbolic |
| 2c | Static + dynamic | 81.1% | Static + braid time-series, formal proofs |

---

## Related

- `UGP_GTE_SM_Verifier/` — GTE verifier producing the canonical triples used as input here
- `uniqueness/` — computational proof that the canonical seed (n=10, b₁=73) is unique
- Braid Atlas (forthcoming, not included in this release)
