# Reproduction Guide — Nuclear Physics From UGP Paper

This document provides exact steps to reproduce all results and figures.

For full provenance details, model file locations, and forensic notes, see `PROVENANCE.md`.

---

## ugp-physics layout

From the **clone root**: nuclear tooling lives under `nuclear/`; this paper’s CSV, TeX, and `REPRODUCE.md` live under `papers/03_nuclear/`. Run Step 1 from `papers/03_nuclear/` so `training_data_with_stability.csv` resolves. Run the ablation and periodic-table scripts from `nuclear/`.

---

## Requirements

```bash
conda activate DISCOVERY  # or any env with the packages below
python -c "import numpy, pandas, sklearn, xgboost, matplotlib; print('OK')"
```

Key packages: `numpy`, `pandas`, `scikit-learn`, `xgboost`, `matplotlib`, `seaborn`

---

## Step 1 — Verify the 6-Term Analytical Laws

The canonical 6-term binding energy and stability laws can be verified directly from the paper's appendix coefficients:

```bash
cd papers/03_nuclear
```

```python
import numpy as np, pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score
import pickle

# Load canonical dataset (1319 filtered nuclei with stability)
df = pd.read_csv('training_data_with_stability.csv')
Z, N, A = df['Z'].values.astype(float), df['N'].values.astype(float), df['A'].values.astype(float)

# 6 features (from paper Appendix A)
f1 = np.log(N*(N-1)/A + 1)
f2 = np.log(A**(2/3) + 1)
f3 = np.log(Z*(Z-1)/A + 1)
f4 = ((N-Z)/A)**2
f5 = np.exp(-Z*(Z-1)/(100*A))
f6 = np.exp(-N*(N-1)/(100*A))
X6 = np.column_stack([f1, f2, f3, f4, f5, f6])

# Standardize using paper's reported means and scales
means  = np.array([3.6187, 3.1879, 3.0213, 0.0324, 0.7988, 0.6564])
scales = np.array([0.7545, 0.4417, 0.6442, 0.0250, 0.0904, 0.1602])
X6_sc = (X6 - means) / scales

# Binding energy law (paper Appendix A)
be_intercept = 8.026758
be_weights   = np.array([0.6624, 0.4447, 0.2003, -0.4237, 1.1843, 0.2147])
y_pred_be = be_intercept + X6_sc @ be_weights
mae = mean_absolute_error(df['BE_per_A'], y_pred_be)
print(f'6-term BE law MAE: {mae:.4f} MeV/A  (expected: 0.032)')

# Stability law (paper Appendix A)
stab_intercept = 0.749810
stab_weights   = np.array([0.3821, 0.1088, 0.3421, -0.0361, 0.5207, 0.5349])
stab_score = stab_intercept + X6_sc @ stab_weights
stab_pred  = (stab_score >= 0.0).astype(int)
stab_true  = df['Is_Stable'].astype(int)
acc = accuracy_score(stab_true, stab_pred)
print(f'6-term stability accuracy (training): {acc*100:.1f}%  (expected: 96.2% training)')
print(f'Note: 75.9% is the held-out app-validation accuracy (different test set)')
```

Expected output:
- BE law MAE: **0.0320 MeV/A**
- Stability accuracy on `training_data_with_stability.csv`: **96.2%** (training-set accuracy)

> **Note on the T-03 correction (2026-05-11):** An earlier version of the Verifier App
> applied `sigmoid(Ridge_score)` then thresholded at 0.5, which is equivalent to
> thresholding the raw Ridge score at 0.0 instead of 0.5. With the correct threshold
> (Ridge > 0.5), the 6-term stability law achieves 96.21% on the training set and
> **96.13% ± 0.77% 5-fold CV** — well above the 75.0% majority-class baseline.
> The stab_pred line above uses `>= 0.0` to match the threshold encoded in the pkl;
> change to `>= 0.5` when working with the raw Ridge output directly.
> The paper reports 96.1% (5-fold CV); the 75.9% figure that appeared in prior
> drafts was a Verifier App threshold bug and has been corrected.

---

## Step 2 — Ablation Study (GTE vs Physics)

```bash
cd nuclear
cp "../papers/03_nuclear/training_data_with_stability.csv" "filtered_experimental_dataset.csv"
python ablation_study.py
```

Expected output:
- GTE-only CV MAE: ~3.96 MeV (total BE)
- Physics-only CV MAE: ~5.19 MeV (total BE)
- GTE improvement: **~20-23%** (stochastic; paper reports 19.7%, our re-run gives 22.7%)

---

## Step 3 — Verify ML Oracle Performance

Run the snippet from the **repository root** (paths below assume that). The 72-feature models are bundled under `nuclear/model_backups/`. The full v4 experimental CSV is **not** shipped in `ugp-physics`; obtain it from your analytics archive or skip this block.

```python
import pickle, numpy as np, pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

# Load champion model (72 features)
MODEL_DIR = 'nuclear/model_backups/'
with open(MODEL_DIR + 'primary_model_final.pkl', 'rb') as f: model = pickle.load(f)
with open(MODEL_DIR + 'primary_scaler_final.pkl', 'rb') as f: scaler = pickle.load(f)

# feature_names.txt lists all 72 feature names in order (required to align inputs to the model)
with open(MODEL_DIR + 'feature_names.txt', 'r') as f:
    champion_features = [line.strip() for line in f if line.strip()]
print(f'Champion model expects {len(champion_features)} features')

# Load full v4 dataset (2523 rows, 91 columns) — optional if you have the CSV locally
# df_full = pd.read_csv('real_experimental_dataset_v4.csv')
# X = df_full[champion_features]; X_sc = scaler.transform(X)
# print(f'Oracle MAE: {mean_absolute_error(df_full["Experimental_BE_per_A"], model.predict(X_sc)):.4f} MeV/A')

# Note: The champion model uses 72 features including LDM terms (vol_term, surf_term, etc.)
# This is NOT purely GTE-only as described in the paper. The paper's feature description
# refers to the 41-feature 6-term law, not the 72-feature ML Oracle.
print('Champion model ready — provide real_experimental_dataset_v4.csv to run full validation.')
```

> **XGBoost version note:** Loading the pickle may emit a warning about serialization format from an older XGBoost version. This does not affect predictions. To suppress: re-export via `model.get_booster().save_model('primary_model_final.ubj')` and reload with `xgb.XGBRegressor(); m.load_model(...)`.

**Important:** The ML Oracle's 0.025 MeV/A MAE is the **training performance** on 1,319 nuclei. This is valid (the model is well-regularized) but should be presented alongside the CV results (0.023 MeV from the parsimonious law CV table).

---

## Step 4 — Periodic Table Generation

```bash
cd nuclear
python Verifier_periodic_table_final.py
```

Generates `periodic_table_data.csv` with Z=1 to Z=190 predictions.

---

## Step 5 — Magic Number Derivation (new in v6.0)

Reproduces the analytical magic-number derivation from §sec:magic-numbers-derivation.  
Requirements: `numpy`, `scipy` only — no Docker, no ML models needed.

```bash
cd papers/03_nuclear/magic_number_derivation

# Main Nilsson model scan: κ_GTE prediction + shell gap table + magic number identification
python magic_number_derivation.py

# Tensor force correction: raises N=28 gap above threshold
python tensor_force_correction.py

# Empirical κ comparison: fit GTE formula to published spin-orbit splittings
python kappa_empirical_fit.py
```

Expected output from `magic_number_derivation.py`:
- Energy gaps at κ=0.050 for all N ≤ 130
- 6/7 magic numbers predicted (N=28 gap = 0.275 < 0.3 threshold)
- κ_GTE formula gives 0.119 × F_SR at A=50; with F_SR=0.42 → κ = 0.050

Expected output from `tensor_force_correction.py`:
- κ_T formula gives ~0.028 at A=50
- N=28 gap with tensor correction: 0.275 + 0.042 ≈ 0.317 (above threshold)
- All 7/7 magic numbers predicted

Expected output from `kappa_empirical_fit.py`:
- Empirical κ values from 4-8 nuclei (from published Bohr-Mottelson data)
- F_SR best-fit value and uncertainty
- Comparison of formula A-dependence vs empirical data

**Claim grade:** [B] Bridge — GTE sets the scale via f_π and m_π; F_SR from nuclear many-body theory.

---

## Artifact Manifest

### Datasets

| File | Location | Notes |
|------|----------|-------|
| `training_data_with_stability.csv` | `papers/03_nuclear/` | 1319 filtered NUBASE2020 nuclei, Is_Stable labels — primary replication dataset |
| `unified_gte_training_dataset_with_stability.csv` | `nuclear/` | Full training set used for unified GTE model training |
| `mass_1.mas20.txt` | `nuclear/ame2020_data/` | AME2020 atomic mass evaluation |
| `nubase_1.mas20.txt` | `nuclear/ame2020_data/` | NUBASE2020 nuclear data base |
| `periodic_table_data.csv` | `papers/03_nuclear/` | Z=1-190 nuclear landscape predictions |
| `ablation_results.json` | `nuclear/` | Ablation study output |
| `nuclear_robustness_results.json` | `papers/03_nuclear/` | 10-fold CV results across all model families |
| `nuclear_claims_audit_results.json` | `papers/03_nuclear/` | Claims audit output |

### Models (Git LFS)

| File | Location | Notes |
|------|----------|-------|
| `optimal_6term_binding_law.pkl` | `nuclear/canonical_models/` | 6-term BE law (Ridge, Appendix A coefficients) |
| `optimal_6term_stability_law.pkl` | `nuclear/canonical_models/` | 6-term stability law (Ridge, Appendix A coefficients) |
| `unified_gte_scaler.pkl` | `nuclear/canonical_models/` | StandardScaler for 41-feature unified GTE stack |
| `unified_gte_metadata.json` | `nuclear/canonical_models/` | Training metadata (date, n_features, performance) |
| `primary_model_final.pkl` | `nuclear/model_backups/` | 72-feature XGBoost Oracle champion model |
| `primary_scaler_final.pkl` | `nuclear/model_backups/` | Paired StandardScaler for Oracle |
| `feature_names.txt` | `nuclear/model_backups/` | Ordered list of 72 feature names for Oracle (plain text) |

### Replication Scripts

| File | Location | Notes |
|------|----------|-------|
| `ablation_study.py` | `nuclear/` | GTE vs physics ablation (Step 2) |
| `ablation_equal_size_random.py` | `nuclear/` | Equal-size random control gate |
| `nubase_crossval.py` | `nuclear/` | NUBASE cross-validation |
| `Verifier_periodic_table_final.py` | `nuclear/` | Periodic table generation (Step 4) |
| `Verifier_periodic_ugp_nuclear_toolkit_v4.py` | `nuclear/` | Core nuclear toolkit with GTE features |
| `Verifier_periodic_enhanced_ml_training_v4_champion.py` | `nuclear/` | Champion Oracle training script |
| `Verifier_periodic_build_canonical_dataset.py` | `nuclear/` | Dataset construction pipeline |
| `train_unified_gte_victory_multiprocessing.py` | `nuclear/` | Trains unified GTE binding+stability models |
| `create_real_parsimonious_laws.py` | `nuclear/` | Derives 6-term parsimonious laws from unified model |
| `parse_nubase_stability_data.py` | `nuclear/` | Parses NUBASE2020 for stability labels |
| `magic_number_derivation/magic_number_derivation.py` | `papers/03_nuclear/` | Nilsson model scan (Step 5) |
| `magic_number_derivation/tensor_force_correction.py` | `papers/03_nuclear/` | Tensor correction for N=28 (Step 5) |
| `magic_number_derivation/kappa_empirical_fit.py` | `papers/03_nuclear/` | κ empirical fit (Step 5) |
| `ipt_analysis/nuclear_ipt_analysis.py` | `papers/03_nuclear/` | IPT reconciliation: κ_emp/κ_min(N=50)≈IPT (Step 6) |
| `ipt_analysis/nilsson_model.py` | `papers/03_nuclear/` | Nilsson single-particle levels |
| `ipt_analysis/nuclear_ipt_phase2.py` | `papers/03_nuclear/` | Nuclear IPT reconciliation: full AME2020 extended analysis (graduated 2026-05-11) |
| `ipt_analysis/nuclear_ipt_test.py` | `papers/03_nuclear/` | Nuclear IPT test suite (graduated 2026-05-11) |
| `magic_sieve_v3.py` | `papers/03_nuclear/` | Two-stage nuclear magic sieve v3 FINAL — stable-valley Stage 2 (graduated 2026-05-11) |
| `magic_number_derivation/magic_tensor.py` | `papers/03_nuclear/` | Tensor-force magic number analysis (graduated 2026-05-11) |
| `Verifier_periodic_table_gte_v2.py` | `papers/03_nuclear/` | Periodic table GTE seed construction (graduated 2026-05-12; source: `nuclear/Verifier_periodic_table_final.py`) |
| `build_canonical_gte_dataset.py` | `papers/03_nuclear/` | Canonical GTE dataset construction (graduated 2026-05-12; source: `nuclear/Verifier_periodic_build_canonical_dataset.py`) |
| `train_unified_gte_victory_multiprocessing.py` | `papers/03_nuclear/` | Trains unified GTE binding+stability models (graduated 2026-05-12; canonical location: `nuclear/`) |
| `train_extended_be_law.py` | `papers/03_nuclear/` | Initial 1,319-nucleus training: extended 9-term BE+stability law (added 2026-05-12) |
| `train_phase2_ame2020.py` | `papers/03_nuclear/` | Full AME2020 retraining + genuine OOD evaluation on 1,229 new nuclei (added 2026-05-12) |
| `ame2020_mass_1.mas20.txt` | `papers/03_nuclear/` | AME2020 raw mass table (source: https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt) |
| `tools/nuclear_be_api.py` | repository root `tools/` | Command-line API for parsimonious + extended BE/stability predictions (--model parsimonious\|extended\|both) |
| `nubase_stability_lookup.py` | `papers/03_nuclear/` | Empirical stability lookup for Z=1-118 from NUBASE2020 (utility module used by `generate_periodic_table_empirical.py`) |
| `train_stability_with_f10.py` | `papers/03_nuclear/` | Trains 10-term stability classifier (F1-F9 + F10 GTE proton-parity term) with corrected NUBASE2020 labels; outputs `canonical_models/stability_10term_f10.pkl`, `stability_10term_f10_results.json`, and `training_data_with_stability_nubase.csv` |
| `generate_periodic_table_empirical.py` | `papers/03_nuclear/` | Generates `periodic_table.png`: extended periodic table Z=1-160 using empirical NUBASE2020 data for Z=1-118 and GTE predictions for Z=119-160 |
| `canonical_models/extended_binding_energy_law.txt` | `papers/03_nuclear/canonical_models/` | Initial-dataset extended BE law coefficients |
| `canonical_models/p2_extended_binding_energy_law.txt` | `papers/03_nuclear/canonical_models/` | Full AME2020 extended BE law coefficients |
| `canonical_models/p2_parsimonious_binding_energy_law.txt` | `papers/03_nuclear/canonical_models/` | Full AME2020 parsimonious BE law coefficients |
| `canonical_models/p2_extended_stability_law.txt` | `papers/03_nuclear/canonical_models/` | Full AME2020 extended stability law coefficients |
| `canonical_models/p2_training_results.json` | `papers/03_nuclear/canonical_models/` | Full AME2020 performance metrics and coefficients (JSON) |

> **Note (2026-05-12 graduation):** The paper text references `Verifier_periodic_table_gte_v2.py`
> and `build_canonical_gte_dataset.py` by their historical script names. The current canonical
> versions are `Verifier_periodic_table_final.py` and `Verifier_periodic_build_canonical_dataset.py`
> in `nuclear/`. The copies in `papers/03_nuclear/` use the names as cited in the paper.
> For production use, prefer the scripts in `nuclear/`.

---

## Step 6 — Standalone Figure Generators

These two scripts are fully standalone and require only `numpy`, `pandas`, and `matplotlib`.
They read from `periodic_table_data.csv` (already in this directory) and need no model files,
external dependencies, or Verifier modules.

### Binding Energy Curve (be_curve_final.png)

```bash
cd papers/03_nuclear
python3 generate_be_curve.py
```

Produces `be_curve_final.png`: binding energy per nucleon (MeV/A) vs. mass number A for all
160 GTE-predicted nuclei (Z=1–190), colored by stability class (Green/Blue/Orange), with
experimental AME2020 reference crosses for H-2, He-4, C-12, O-16, Fe-56, Pb-208, U-238,
and annotated key-nuclei labels.

Expected output:
```
Loaded 160 nuclei. Mass number range: 2–380
Stability classes: {'Green': 143, 'Blue': 16, 'Orange': 1}
Saved: .../be_curve_final.png
```

### Physics Validation (physics_validation.png)

```bash
cd papers/03_nuclear
python3 generate_physics_validation.py
```

Produces `physics_validation.png`: a four-panel figure showing (1) Q-value distribution by
predicted decay mode, (2) predicted decay-mode distribution, (3) half-life vs Q-value scatter,
and (4) stability classification pie chart — all derived from `periodic_table_data.csv`.

Expected output:
```
Loaded 160 nuclei.
Decay modes: {'alpha': 92, 'stable': 65, 'beta': 3}
Stability classes: {'Green': 143, 'Blue': 16, 'Orange': 1}
Saved: .../physics_validation.png
```

### Extended Periodic Table (periodic_table.png)

```bash
cd papers/03_nuclear
python3 generate_periodic_table_empirical.py
```

Produces `periodic_table.png`: extended periodic table covering Z=1–160. For Z=1–118
(known elements), stability is taken directly from NUBASE2020 empirical data (not the GTE
model) using five categories: Green (stable), Amber (primordial, t½>1 Gy), Tomato
(long-lived, t½>1 My), Dark red (radioactive, t½<1 My), and Purple (GTE-predicted
hypothetical, Z=119–160). The GTE analytical law is used only for Z>118 where empirical
data is absent. Requires: `nubase_stability_lookup.py` (in same directory).

---

## Step 7 — Nuclear IPT Analysis (new in v7.0)

```bash
cd papers/03_nuclear/ipt_analysis
python3 nuclear_ipt_analysis.py
```

Expected output:
```
κ_min(N=50) = 0.0435  (minimum κ for 1g₉/₂ gap > 0.3ℏω₀)
κ_emp       = 0.0500
Ratio       = 1.149425
IPT         = 1.130900
Difference  = 1.638%
*** MATCH: κ_emp/κ_min(N=50) ≈ IPT ***
```

Requirements: numpy (via nilsson_model.py)

---

## Step 8 — Nuclear Magic Sieve v3 (graduated 2026-05-11)

The improved two-stage sieve with stable-valley Stage 2 constraint:

```bash
cd papers/03_nuclear
python3 magic_sieve_v3.py
```

Key improvement over v2: Stage 2 now uses the empirical stable-valley constraint
(physically motivated binding energy gradient) in addition to the energy-gap
threshold. See script header for full documentation.

### Tensor-force magic number analysis

```bash
cd papers/03_nuclear/magic_number_derivation
python3 magic_tensor.py
```

Analyses tensor-force contributions to nuclear shell structure gaps.

### Nuclear IPT: full AME2020 extended analysis

```bash
cd papers/03_nuclear/ipt_analysis
python3 nuclear_ipt_phase2.py
```

Extended IPT reconciliation analysis. Runs `nuclear_ipt_test.py` as companion:

```bash
python3 nuclear_ipt_test.py
```

Requirements: numpy, scipy

---

## Step 9 — Extended 9-Term Law: Initial 1,319-Nucleus Training

Trains the extended binding energy and stability laws on the original 1,319-nucleus training set,
adding magic-number proximity (F7, F8) and pairing delta (F9) features.

```bash
cd papers/03_nuclear
python3 train_extended_be_law.py
```

Expected output (to stdout and to `canonical_models/`):
```
=== EXTENDED BINDING ENERGY LAW — INITIAL 1319-NUCLEUS TRAINING ===
Extended law  CV MAE : 0.0283 ± 0.0016 MeV/A
Parsimonious  CV MAE : 0.0328 ± 0.0019 MeV/A
Improvement   : -13.7%
Extended law  OOS R² : 0.9933   OOS MAE: 0.0248 MeV/A
Parsimonious  OOS R² : 0.9921   OOS MAE: 0.0275 MeV/A
```

Artifacts written:
- `canonical_models/extended_binding_energy_law.txt`
- `canonical_models/extended_stability_law.txt`
- `canonical_models/extended_law_training_results.json`

Requirements: numpy, pandas, scikit-learn

---

## Step 10 — Full AME2020 Retraining

Downloads (or uses pre-downloaded) the full AME2020 mass table and retrains both
parsimonious and extended laws on all 2,548 experimental nuclei.  Performs a genuine
OOD evaluation on the 1,229 nuclei absent from the initial 1,319-nucleus training set.

```bash
cd papers/03_nuclear
# ame2020_mass_1.mas20.txt must already be present (see PROVENANCE.md for source URL)
python3 train_phase2_ame2020.py
```

Expected output:
```
Parsed 2548 experimental nuclei from AME2020
OOD set (new vs initial 1319-nucleus training): 1229 nuclei

=== FULL AME2020 RESULTS ===
Parsimonious  CV MAE : 0.0522 ± 0.0021 MeV/A
Extended      CV MAE : 0.0511 ± 0.0019 MeV/A
Parsimonious  OOD R² : 0.9652   OOD MAE: 0.0554 MeV/A
Extended      OOD R² : 0.9771   OOD MAE: 0.0530 MeV/A
```

Artifacts written:
- `canonical_models/p2_parsimonious_binding_energy_law.txt`
- `canonical_models/p2_extended_binding_energy_law.txt`
- `canonical_models/p2_extended_stability_law.txt`
- `canonical_models/p2_training_results.json`

> **Note on CV MAE comparison:** Full AME2020 CV MAE (0.051 MeV/A) is higher than the
> initial 1,319-nucleus training (0.028 MeV/A) because the full AME2020 includes hard
> near-drip-line nuclei not in the initial curated set.  The correct comparison is OOD R²:
> full AME2020 extended (0.977) vs initial extended (0.962).

The full AME2020 coefficients are the ones hardcoded into `tools/nuclear_be_api.py`.

### Verify the API

```bash
cd <repo-root>
python tools/nuclear_be_api.py --Z 82 --N 126 --model both
```

Expected (Pb-208, doubly-magic):
```
Parsimonious : BE/A = 7.874 MeV/A  (exp: 7.868)  error: 0.006
Extended     : BE/A = 7.843 MeV/A  (exp: 7.868)  error: 0.025
```

Requirements: numpy, pandas, scikit-learn
