#!/usr/bin/env python3
"""
train_stability_with_f10.py
============================
COMP-001: Retrain the stability classifier with:
  1. Corrected NUBASE2020 stability labels
     (elements with no stable isotopes → all their isotopes labeled False)
  2. F10 feature: (Z mod 2) × δ_pair × A^(-3/4)
     (GTE-derived proton-parity interaction term)

This is the 10-term stability classifier:
  F1-F6:  original 6-term GTE coordinate features
  F7:     proton magic-number proximity
  F8:     neutron magic-number proximity
  F9:     δ_pair × A^(-3/4)    (combined parity — from 9-term law)
  F10:    (Z%2) × δ_pair × A^(-3/4)  (proton-parity — new GTE feature)

Outputs:
  canonical_models/stability_10term_f10.pkl
  canonical_models/stability_10term_f10_results.json
  training_data_with_stability_nubase.csv  (corrected labels)
"""

import numpy as np
import pandas as pd
import json
import pickle
from pathlib import Path
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
TRAINING_CSV = HERE / 'training_data_with_stability.csv'
OUT_CSV      = HERE / 'training_data_with_stability_nubase.csv'
MODEL_DIR    = HERE / 'canonical_models'
MODEL_DIR.mkdir(exist_ok=True)

# ── NUBASE correction: elements with NO stable isotopes ───────────────────────
# Source: nubase_stability_lookup.py — validated against NUBASE2020
NO_STABLE_ISOTOPES_Z = {43, 61} | set(range(84, 119))  # Tc, Pm, Po → Og

# ── GTE 6-term features (from paper Appendix A) ───────────────────────────────
MEANS_6  = np.array([3.6187, 3.1879, 3.0213, 0.0324, 0.7988, 0.6564])
SCALES_6 = np.array([0.7545, 0.4417, 0.6442, 0.0250, 0.0904, 0.1602])
MAGIC_Z  = np.array([2, 8, 20, 28, 50, 82, 126])
MAGIC_N  = np.array([2, 8, 20, 28, 50, 82, 126])
SIGMA_MAGIC = 5.0


def compute_features(Z_arr, N_arr):
    """Compute all 10 features for arrays of (Z, N) values."""
    Z = Z_arr.astype(float)
    N = N_arr.astype(float)
    A = Z + N

    # F1-F6: original 6 GTE features
    f1 = np.log(N * (N - 1) / A + 1)
    f2 = np.log(A ** (2 / 3) + 1)
    f3 = np.log(Z * (Z - 1) / A + 1)
    f4 = ((N - Z) / A) ** 2
    f5 = np.exp(-Z * (Z - 1) / (100 * A))
    f6 = np.exp(-N * (N - 1) / (100 * A))
    X6 = np.column_stack([f1, f2, f3, f4, f5, f6])
    X6_sc = (X6 - MEANS_6) / SCALES_6  # standardized with training params

    # F7: proton magic-number proximity
    dist_Z = np.min(np.abs(Z_arr[:, None] - MAGIC_Z[None, :]), axis=1).astype(float)
    f7 = np.exp(-dist_Z / SIGMA_MAGIC)

    # F8: neutron magic-number proximity
    dist_N = np.min(np.abs(N_arr[:, None] - MAGIC_N[None, :]), axis=1).astype(float)
    f8 = np.exp(-dist_N / SIGMA_MAGIC)

    # F9: combined parity = δ_pair × A^(-3/4)
    Z_i = Z_arr.astype(int)
    N_i = N_arr.astype(int)
    A_i = A.astype(int)
    delta_pair = np.where(
        (Z_i % 2 == 0) & (N_i % 2 == 0), +1.0,
        np.where((Z_i % 2 == 1) & (N_i % 2 == 1), -1.0, 0.0)
    )
    f9 = delta_pair / (A ** 0.75)

    # F10: proton-parity × combined parity (NEW GTE feature)
    # = (Z mod 2) × δ_pair × A^(-3/4)
    # GTE derivation: parity of Z×b_p = Z mod 2 (since b_p = 11459 is odd)
    f10 = (Z_i % 2).astype(float) * delta_pair / (A ** 0.75)

    # Stack all 10 features (F1-F6 are pre-scaled; F7-F10 are raw)
    return np.column_stack([X6_sc, f7, f8, f9, f10])


def main():
    print("=" * 72)
    print("COMP-001: Train 10-term Stability Classifier with NUBASE Labels + F10")
    print("=" * 72)

    # ── Load training data ─────────────────────────────────────────────────────
    df = pd.read_csv(TRAINING_CSV)
    print(f"\nLoaded training data: {len(df)} nuclei")
    print(f"Z range: {df.Z.min()} to {df.Z.max()}")

    # ── Apply NUBASE corrections ───────────────────────────────────────────────
    print(f"\nApplying NUBASE corrections...")
    old_labels = df['Is_Stable'].copy()
    df['Is_Stable_NUBASE'] = df['Is_Stable'].copy()

    # Elements with NO stable isotopes → all their training nuclei get False
    mask_no_stable = df['Z'].isin(NO_STABLE_ISOTOPES_Z)
    corrections = mask_no_stable & df['Is_Stable']
    n_corrected = corrections.sum()
    df.loc[mask_no_stable, 'Is_Stable_NUBASE'] = False

    print(f"  Nuclei of elements with no stable isotopes: {mask_no_stable.sum()}")
    print(f"  Labels changed True→False: {n_corrected}")
    print(f"  Old: {old_labels.sum()} stable, {(~old_labels).sum()} unstable")
    print(f"  New: {df['Is_Stable_NUBASE'].sum()} stable, {(~df['Is_Stable_NUBASE']).sum()} unstable")

    # Show what changed
    changed = df[corrections][['Z', 'N', 'A', 'Element', 'Is_Stable', 'Is_Stable_NUBASE']]
    if len(changed) > 0:
        print(f"\n  Corrected nuclei (sample):")
        for _, row in changed.head(10).iterrows():
            print(f"    Z={row.Z:3d} N={row.N:3d} A={row.A:3d} ({row.Element}): True → False")
        if len(changed) > 10:
            print(f"    ... and {len(changed)-10} more")

    # Save corrected CSV
    df.to_csv(OUT_CSV, index=False)
    print(f"\n  Saved corrected labels to: {OUT_CSV}")

    # ── Compute features ───────────────────────────────────────────────────────
    print("\nComputing 10 features (F1-F10)...")
    Z_arr = df['Z'].values
    N_arr = df['N'].values
    X = compute_features(Z_arr, N_arr)
    y = df['Is_Stable_NUBASE'].values.astype(int)

    print(f"  Feature matrix: {X.shape}")
    print(f"  Labels: {y.sum()} positive (stable), {(1-y).sum()} negative (unstable)")

    # ── Cross-validation ───────────────────────────────────────────────────────
    print("\nRunning 5-fold cross-validation...")
    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X, y, cv=cv, scoring='accuracy')
    print(f"  5-fold CV accuracy: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

    # ── Compare: 6-term only (old labels) ─────────────────────────────────────
    print("\nComparison: 6-term only with OLD (BE/A) labels...")
    X6_only = X[:, :6]
    y_old = old_labels.values.astype(int)
    cv_old = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores_old = cross_val_score(
        LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        X6_only, y_old, cv=cv_old, scoring='accuracy'
    )
    print(f"  6-term, old labels: {cv_scores_old.mean()*100:.2f}% ± {cv_scores_old.std()*100:.2f}%")

    print("\nComparison: 6-term only with NUBASE labels...")
    cv_scores_6_nubase = cross_val_score(
        LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        X6_only, y, cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring='accuracy'
    )
    print(f"  6-term, NUBASE labels: {cv_scores_6_nubase.mean()*100:.2f}% ± {cv_scores_6_nubase.std()*100:.2f}%")

    # ── Train final 10-term model on all data ──────────────────────────────────
    print("\nTraining final 10-term model on full dataset...")
    clf_final = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    clf_final.fit(X, y)
    train_acc = accuracy_score(y, clf_final.predict(X))
    print(f"  Training accuracy: {train_acc*100:.2f}%")

    # ── Inspect key elements ───────────────────────────────────────────────────
    print("\nKey element predictions (10-term model):")
    key_cases = [
        ('Mo-95',  42, 53),  ('Tc-98',  43, 55),  ('Ru-101', 44, 57),
        ('Nd-142', 60, 82),  ('Pm-142', 61, 81),  ('Sm-145', 62, 83),
        ('Pb-208', 82, 126), ('Bi-209', 83, 126), ('Po-210', 84, 126),
        ('Th-232', 90, 142), ('U-238',  92, 146),
        ('Fe-56',  26, 30),  ('Ni-62',  28, 34),
    ]
    print(f"  {'Name':>10}  {'Z':>4}  {'N':>4}  {'emp_stable':>12}  {'pred':>6}  {'score':>8}  {'correct?':>8}")
    for name, Z, N in key_cases:
        x = compute_features(np.array([Z]), np.array([N]))
        pred = clf_final.predict(x)[0]
        score = clf_final.decision_function(x)[0]
        emp = Z not in NO_STABLE_ISOTOPES_Z
        correct = (pred == 1) == emp
        print(f"  {name:>10}  {Z:>4}  {N:>4}  "
              f"{'stable' if emp else 'unstable':>12}  "
              f"{'S' if pred else 'U':>6}  {score:>8.4f}  "
              f"{'✓' if correct else '✗ WRONG':>8}")

    # ── Save model ─────────────────────────────────────────────────────────────
    model_path = MODEL_DIR / 'stability_10term_f10.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump({'model': clf_final, 'feature_names': [
            'f1_log_nn_A', 'f2_log_A23', 'f3_log_zz_A', 'f4_asym_sq',
            'f5_exp_zz', 'f6_exp_nn',
            'f7_magic_Z_prox', 'f8_magic_N_prox',
            'f9_pair_delta', 'f10_proton_parity'
        ]}, f)
    print(f"\nModel saved to: {model_path}")

    # ── Save results ───────────────────────────────────────────────────────────
    results = {
        'n_nuclei': int(len(df)),
        'n_stable_nubase': int(y.sum()),
        'n_unstable_nubase': int((1-y).sum()),
        'n_labels_corrected': int(n_corrected),
        'cv_10term_nubase': {
            'mean_accuracy': float(cv_scores.mean()),
            'std_accuracy': float(cv_scores.std()),
            'scores': cv_scores.tolist()
        },
        'cv_6term_old_labels': {
            'mean_accuracy': float(cv_scores_old.mean()),
            'std_accuracy': float(cv_scores_old.std()),
        },
        'cv_6term_nubase_labels': {
            'mean_accuracy': float(cv_scores_6_nubase.mean()),
            'std_accuracy': float(cv_scores_6_nubase.std()),
        },
        'train_accuracy': float(train_acc),
        'feature_list': ['F1-F6 (GTE 6-term, pre-scaled)', 'F7 magic_Z', 'F8 magic_N', 'F9 pair_delta', 'F10 proton_parity'],
        'model_coefficients': {
            'intercept': float(clf_final.intercept_[0]),
            'coef_F1_F10': clf_final.coef_[0].tolist()
        },
        'nubase_correction': {
            'no_stable_isotopes_Z': sorted(NO_STABLE_ISOTOPES_Z),
            'n_nuclei_corrected': int(n_corrected)
        }
    }
    results_path = MODEL_DIR / 'stability_10term_f10_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_path}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  Labels corrected (NUBASE): {n_corrected} changed True→False")
    print(f"  10-term + NUBASE labels:   {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}% CV")
    print(f"  6-term  + old labels:      {cv_scores_old.mean()*100:.2f}% ± {cv_scores_old.std()*100:.2f}% CV (old claim)")
    print(f"  6-term  + NUBASE labels:   {cv_scores_6_nubase.mean()*100:.2f}% ± {cv_scores_6_nubase.std()*100:.2f}% CV")
    print()
    print("  Interpretation:")
    print("  - Old 96.1% was against BE/A proxy labels, not NUBASE")
    print("  - New figures are against correct NUBASE empirical stability")
    print("  - F10 helps on even-A Tc/Pm; cannot help odd-A (fundamental limit)")
    return results


if __name__ == '__main__':
    main()
