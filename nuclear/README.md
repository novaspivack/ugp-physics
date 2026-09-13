# Nuclear — UGP Nuclear Physics Tooling

GTE-based nuclear binding energy prediction, stability classification, and periodic-table generation. Code supporting **Paper 3: Nuclear Binding and the Periodic Table from UGP**.

**Central result:** A GTE-only XGBoost model (CV MAE ≈ 3.96 MeV total BE) outperforms a simplified Bethe-Weizsäcker physics-only baseline (CV MAE ≈ 5.19 MeV) by ~20% in cross-validated binding energy prediction. The paper cites 19.7% (original experimental run); re-running the same script gives 22.7% due to stochastic train/test splitting — both are consistent with a ~20% GTE advantage against the simplified 10-feature BW baseline. When the physics baseline is enriched with additional features (magic numbers, extended LDM, shell corrections) the gap narrows; the strongest claim is that GTE-only features are **competitive with standard simplified nuclear physics features and carry independent predictive content**.

The primary scientific contribution is two parsimonious **6-term analytical laws** distilled from the ML oracle: 0.032 MeV/A MAE for binding energy and 75.9% stability accuracy (majority-class baseline: 75.0%), using only GTE-derived coordinates.

---

## Files

| File | Purpose |
|---|---|
| `Verifier_periodic_ugp_nuclear_toolkit_v4.py` | `UGPNuclearToolkitV4`, `GTETriple` — GTE kernel constants, proton/neutron GTE triples, feature extraction, optional ML model loading |
| `ablation_study.py` | `GTEAblationStudy` — 3-way ablation: GTE-only vs. physics-only vs. hybrid, cross-validated on `filtered_experimental_dataset.csv` |
| `Verifier_periodic_enhanced_ml_training_v4_champion.py` | `EnhancedMLTrainerV4Champion` — 72-feature ensemble pipeline (XGBoost + physics features) on the full v4 experimental dataset |
| `Verifier_periodic_table_final.py` | `FinalPeriodicTableGenerator` — predicts binding energy and stability for Z=1 to Z=190 |
| `Verifier_periodic_build_canonical_dataset.py` | `CanonicalDatasetBuilder` — builds the balanced 1,319-nucleus dataset with stability labels |
| `parse_nubase_stability_data.py` | `NubaseStabilityParser` — parses NUBASE2003 text format to extract stability flags and half-lives |
| `create_conditional_universal_law.py` | Derives a conditional analytic binding law using sympy + sklearn |
| `create_residual_dataset.py` | `ResidualDatasetCreator` — builds residual dataset for calibrator ensemble training |

---

## Requirements

```bash
pip install numpy pandas scikit-learn xgboost matplotlib seaborn scipy sympy
```

All packages are listed in `requirements.txt` at the repository root.

---

## Paper 3 replication

See `papers/03_nuclear/REPRODUCE.md` for the full step-by-step replication guide. Quick summary:

### Step 1 — Verify the 6-term analytical laws

Run from `papers/03_nuclear/` (requires `training_data_with_stability.csv` in that directory):

```bash
cd papers/03_nuclear
python3 - <<'EOF'
import numpy as np, pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score

df = pd.read_csv('training_data_with_stability.csv')
Z, N, A = df['Z'].values.astype(float), df['N'].values.astype(float), df['A'].values.astype(float)

f1 = np.log(N*(N-1)/A + 1)
f2 = np.log(A**(2/3) + 1)
f3 = np.log(Z*(Z-1)/A + 1)
f4 = ((N-Z)/A)**2
f5 = np.exp(-Z*(Z-1)/(100*A))
f6 = np.exp(-N*(N-1)/(100*A))
X6 = np.column_stack([f1, f2, f3, f4, f5, f6])

means  = np.array([3.6187, 3.1879, 3.0213, 0.0324, 0.7988, 0.6564])
scales = np.array([0.7545, 0.4417, 0.6442, 0.0250, 0.0904, 0.1602])
X6_sc  = (X6 - means) / scales

be_weights   = np.array([0.6624, 0.4447, 0.2003, -0.4237, 1.1843, 0.2147])
stab_weights = np.array([0.3821, 0.1088, 0.3421, -0.0361, 0.5207, 0.5349])

print(f'BE law MAE: {mean_absolute_error(df["BE_per_A"], 8.026758 + X6_sc @ be_weights):.4f} MeV/A  (expected: 0.032)')
print(f'Stability accuracy: {accuracy_score(df["Is_Stable"].astype(int), ((0.749810 + X6_sc @ stab_weights) >= 0).astype(int))*100:.1f}%  (expected: 96.2%)')
EOF
```

### Step 2 — Ablation study (GTE vs. physics features)

```bash
cd nuclear
cp ../papers/03_nuclear/training_data_with_stability.csv filtered_experimental_dataset.csv
python ablation_study.py
```

Expected: GTE-only CV MAE ~3.96 MeV; physics-only ~5.19 MeV; GTE improvement ~20–23%.

### Step 3 — Periodic table generation (Z=1–190)

```bash
cd nuclear
python Verifier_periodic_table_final.py
```

Writes `periodic_table_data.csv`.

---

## GTE proton/neutron triples

The toolkit encodes the fundamental UGP-derived triples for the nucleons:

| Particle | a_eff | b_eff | c_eff | g_eff |
|---|---|---|---|---|
| Proton | 5 | 11459 | 15 | 3 |
| Neutron | 5 | 11441 | 15 | 3 |

These are used to construct the GTE features (log-transformed products and ratios) fed to all models.

---

## Model artifacts

Pre-trained models are stored under `model_backups/` (tracked with Git LFS):

| File | Description |
|---|---|
| `primary_model_final.pkl` | 72-feature champion XGBoost model |
| `primary_scaler_final.pkl` | StandardScaler for the 72-feature set |
| `physics_primary_scaler.pkl` | Scaler for physics-only feature set |
| `ultimate_gte_victory_model_scaler.pkl` | GTE-only model scaler |

The 6-term canonical analytical laws (no ML) are verified directly from the coefficient vectors in `papers/03_nuclear/REPRODUCE.md` — no model file needed for those.

---

## Dataset

The canonical dataset is `papers/03_nuclear/training_data_with_stability.csv` — 1,319 nuclei with experimental binding energies per nucleon (`BE_per_A`) and stability labels (`Is_Stable`). NUBASE2003 is the source; `parse_nubase_stability_data.py` documents the parsing procedure.
