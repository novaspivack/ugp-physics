#!/usr/bin/env python3
"""
train_extended_be_law.py — Extended Nuclear Binding Energy Law (SPEC_054_ENL)

Trains a 9-term extended binding energy law by adding three structurally-motivated
features to the existing 6-term GTE coordinate feature set:
  F7: Magic-number proximity (protons)  — exp(-dist_to_nearest_magic_Z / sigma)
  F8: Magic-number proximity (neutrons) — exp(-dist_to_nearest_magic_N / sigma)
  F9: Pairing delta                     — ±A^{-3/4} for even-even / odd-odd

Both models (parsimonious 6-term and extended 9-term) are evaluated side-by-side
with identical train/test splits for honest comparison.

Outputs:
  papers/03_nuclear/canonical_models/extended_binding_energy_law.txt
  papers/03_nuclear/canonical_models/extended_stability_law.txt

Usage:
  python papers/03_nuclear/train_extended_be_law.py

Requires: numpy, scipy, scikit-learn, pandas
"""

from __future__ import annotations
import json
import math
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error

# ─── Magic numbers ────────────────────────────────────────────────────────────
MAGIC_NUMBERS = [2, 8, 20, 28, 50, 82, 126]
SHELL_SIGMA = 5.0   # diffuseness for exp proximity (nucleon units)

# ─── Ridge regularization ─────────────────────────────────────────────────────
RIDGE_ALPHA = 0.01  # same as original; can tune but keep consistent

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO_ROOT / "papers/03_nuclear/training_data_with_stability.csv"
OUT_DIR   = REPO_ROOT / "papers/03_nuclear/canonical_models"
PROV_PATH = REPO_ROOT / "papers/03_nuclear/PROVENANCE.md"


def magic_proximity(x: float, sigma: float = SHELL_SIGMA) -> float:
    """Continuous magic-number proximity: exp(-min_distance / sigma). Range (0,1]."""
    min_dist = min(abs(x - m) for m in MAGIC_NUMBERS)
    return math.exp(-min_dist / sigma)


def pairing_delta(Z: int, N: int, A: int) -> float:
    """
    Pairing energy term scaled by A^{-3/4}.
    +A^{-3/4} for even-even, 0 for odd-A, -A^{-3/4} for odd-odd.
    """
    z_even = (Z % 2 == 0)
    n_even = (N % 2 == 0)
    if z_even and n_even:
        delta = +1.0
    elif (not z_even) and (not n_even):
        delta = -1.0
    else:
        delta = 0.0
    return delta * A ** (-0.75)


def compute_f1_f6(Z: float, N: float) -> list[float]:
    """Original 6 GTE coordinate features (matches nuclear_be_api.py)."""
    A = Z + N
    eps = 1e-9
    f1 = math.log(N * (N - 1) / A + 1 + eps)
    f2 = math.log(A ** (2 / 3) + 1)
    f3 = math.log(Z * (Z - 1) / A + 1 + eps)
    f4 = ((N - Z) / A) ** 2
    f5 = math.exp(-Z * (Z - 1) / (100 * A))
    f6 = math.exp(-N * (N - 1) / (100 * A))
    return [f1, f2, f3, f4, f5, f6]


def compute_f7_f9(Z: int, N: int) -> list[float]:
    """Three new extended features: magic proximity (Z, N) + pairing."""
    A = Z + N
    f7 = magic_proximity(Z)
    f8 = magic_proximity(N)
    f9 = pairing_delta(Z, N, A)
    return [f7, f8, f9]


def build_feature_matrix(df: pd.DataFrame, extended: bool) -> np.ndarray:
    rows = []
    for _, row in df.iterrows():
        Z, N = int(row["Z"]), int(row["N"])
        feats = compute_f1_f6(float(Z), float(N))
        if extended:
            feats += compute_f7_f9(Z, N)
        rows.append(feats)
    return np.array(rows)


def cross_validate(X: np.ndarray, y: np.ndarray, alpha: float,
                   n_splits: int = 5) -> dict:
    """5-fold CV; returns mean and std of MAE and R²."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    maes, r2s = [], []
    for train_idx, val_idx in kf.split(X):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        sc = StandardScaler().fit(X_tr)
        model = Ridge(alpha=alpha).fit(sc.transform(X_tr), y_tr)
        y_pred = model.predict(sc.transform(X_val))
        maes.append(mean_absolute_error(y_val, y_pred))
        r2s.append(r2_score(y_val, y_pred))
    return {
        "cv_mae_mean": float(np.mean(maes)),
        "cv_mae_std":  float(np.std(maes)),
        "cv_r2_mean":  float(np.mean(r2s)),
        "cv_r2_std":   float(np.std(r2s)),
    }


def train_and_evaluate(X: np.ndarray, y: np.ndarray, alpha: float,
                       label: str, feature_names: list[str]) -> dict:
    """
    Evaluate with 5-fold CV + 80/20 hold-out, then train final deployment model
    on ALL data. CV and hold-out figures are for reporting; the full-data model
    coefficients are what get deployed in the API.
    """
    # 80/20 hold-out for supplementary OOS evaluation
    a_bins = pd.cut(np.arange(len(y)), bins=5, labels=False)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=a_bins
    )
    sc_tr = StandardScaler().fit(X_tr)
    m_tr  = Ridge(alpha=alpha).fit(sc_tr.transform(X_tr), y_tr)
    y_pred_te = m_tr.predict(sc_tr.transform(X_te))
    oos_mae = float(mean_absolute_error(y_te, y_pred_te))
    oos_r2  = float(r2_score(y_te, y_pred_te))
    train_mae = float(mean_absolute_error(y_tr, m_tr.predict(sc_tr.transform(X_tr))))

    # 5-fold CV on full dataset
    cv_stats = cross_validate(X, y, alpha)

    # Final deployment model: trained on ALL data
    sc_full   = StandardScaler().fit(X)
    model_full = Ridge(alpha=alpha).fit(sc_full.transform(X), y)
    full_train_mae = float(mean_absolute_error(y, model_full.predict(sc_full.transform(X))))

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Features:              {len(feature_names)}")
    print(f"  80/20 hold-out OOS MAE:{oos_mae:.4f} MeV/A  (in-distribution split)")
    print(f"  80/20 hold-out OOS R²: {oos_r2:.4f}           (in-distribution split)")
    print(f"  5-fold CV MAE:         {cv_stats['cv_mae_mean']:.4f} ± {cv_stats['cv_mae_std']:.4f} MeV/A")
    print(f"  5-fold CV R²:          {cv_stats['cv_r2_mean']:.4f} ± {cv_stats['cv_r2_std']:.4f}")
    print(f"  Full-data train MAE:   {full_train_mae:.4f} MeV/A  (deployment model)")
    print()
    print("  DEPLOYMENT Coefficients (full-data model, standardised):")
    print(f"    Intercept: {model_full.intercept_:.6f}")
    for name, coef in zip(feature_names, model_full.coef_):
        print(f"    {name:<30s} {coef:+.6f}")

    return {
        "label": label,
        "n_features": len(feature_names),
        "feature_names": feature_names,
        # Deployment model (trained on ALL data — use these in the API)
        "intercept": float(model_full.intercept_),
        "coef": [float(c) for c in model_full.coef_],
        "means": [float(m) for m in sc_full.mean_],
        "scales": [float(s) for s in sc_full.scale_],
        "full_train_mae": full_train_mae,
        # Evaluation metrics
        "oos_mae": oos_mae,
        "oos_r2":  oos_r2,
        **cv_stats,
    }


def write_law_file(result: dict, path: Path, target_label: str) -> None:
    """Write human-readable law file matching the style of complete_binding_energy_law.txt."""
    with open(path, "w") as fh:
        fh.write(f"EXTENDED {target_label.upper()} ANALYTICAL LAW (SPEC_054_ENL)\n")
        fh.write("=" * 60 + "\n\n")
        fh.write(f"Intercept: {result['intercept']:.6f}\n\n")
        fh.write("Term weights (applied to standardised features):\n")
        for name, coef in zip(result["feature_names"], result["coef"]):
            fh.write(f"  {coef:+.6f}  *  {name}\n")
        fh.write("\n")
        fh.write("Feature standardisation (mean, scale):\n")
        for name, mu, sc in zip(result["feature_names"], result["means"], result["scales"]):
            fh.write(f"  {name:<30s} mean={mu:.6f}  scale={sc:.6f}\n")
        fh.write("\n")
        fh.write(f"Training set:     {1319} nuclei (NUBASE2020 + AMDC + NDS + ENSDF, filtered)\n")
        fh.write(f"5-fold CV MAE:    {result['cv_mae_mean']:.4f} ± {result['cv_mae_std']:.4f} MeV/A\n")
        fh.write(f"5-fold CV R²:     {result['cv_r2_mean']:.4f} ± {result['cv_r2_std']:.4f}\n")
        fh.write(f"OOS MAE (20% holdout): {result['oos_mae']:.4f} MeV/A\n")
        fh.write(f"OOS R² (20% holdout):  {result['oos_r2']:.4f}\n")
        fh.write("\n")
        fh.write("Feature definitions:\n")
        fh.write("  F1 = log(N(N-1)/A + 1)  [GTE N-coordination]\n")
        fh.write("  F2 = log(A^(2/3) + 1)   [GTE surface/volume]\n")
        fh.write("  F3 = log(Z(Z-1)/A + 1)  [GTE Coulomb-analogue]\n")
        fh.write("  F4 = ((N-Z)/A)^2         [Isospin asymmetry]\n")
        fh.write("  F5 = exp(-Z(Z-1)/(100A)) [GTE proton interaction decay]\n")
        fh.write("  F6 = exp(-N(N-1)/(100A)) [GTE neutron interaction decay]\n")
        fh.write("  F7 = exp(-min|Z-m|/5.0)  [Proton magic-number proximity, sigma=5.0]\n")
        fh.write("       m in {2,8,20,28,50,82,126}\n")
        fh.write("  F8 = exp(-min|N-m|/5.0)  [Neutron magic-number proximity, sigma=5.0]\n")
        fh.write("  F9 = delta_pair * A^{-3/4} [Pairing: +1 even-even, 0 odd-A, -1 odd-odd]\n")
        fh.write("\nGenerated by: papers/03_nuclear/train_extended_be_law.py\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    print(f"Loading training data from {DATA_PATH} ...")
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found at {DATA_PATH}. "
            "Run from the ugp-physics repo root."
        )

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} nuclei.")

    y_be = df["BE_per_A"].values

    # Stability target: Is_Stable (bool → int)
    y_stab = df["Is_Stable"].astype(int).values

    # ─── Feature names ──────────────────────────────────────────────────────
    F6_NAMES = ["F1_log_N_coord", "F2_log_surface", "F3_log_Z_coulomb",
                "F4_asymmetry_sq", "F5_exp_Z_decay", "F6_exp_N_decay"]
    F9_NAMES = F6_NAMES + ["F7_shell_Z_prox", "F8_shell_N_prox", "F9_pairing_delta"]

    # ─── Build feature matrices ─────────────────────────────────────────────
    print("Building feature matrices ...")
    X6 = build_feature_matrix(df, extended=False)
    X9 = build_feature_matrix(df, extended=True)

    # ─── Train binding energy laws ──────────────────────────────────────────
    res6_be = train_and_evaluate(X6, y_be, RIDGE_ALPHA,
                                  "PARSIMONIOUS (6-term) — Binding Energy", F6_NAMES)
    res9_be = train_and_evaluate(X9, y_be, RIDGE_ALPHA,
                                  "EXTENDED (9-term) — Binding Energy", F9_NAMES)

    # ─── Train stability classifiers ────────────────────────────────────────
    res6_st = train_and_evaluate(X6, y_stab.astype(float), RIDGE_ALPHA,
                                  "PARSIMONIOUS (6-term) — Stability", F6_NAMES)
    res9_st = train_and_evaluate(X9, y_stab.astype(float), RIDGE_ALPHA,
                                  "EXTENDED (9-term) — Stability", F9_NAMES)

    # ─── Improvement summary ────────────────────────────────────────────────
    mae_improvement = (res6_be["cv_mae_mean"] - res9_be["cv_mae_mean"]) / res6_be["cv_mae_mean"] * 100
    r2_improvement  = res9_be["oos_r2"] - res6_be["oos_r2"]
    print(f"\n{'='*60}")
    print("  IMPROVEMENT SUMMARY")
    print(f"{'='*60}")
    print(f"  CV MAE (BE/A):  {res6_be['cv_mae_mean']:.4f} → {res9_be['cv_mae_mean']:.4f}  "
          f"({mae_improvement:+.1f}%)")
    print(f"  OOS R² (BE/A):  {res6_be['oos_r2']:.4f} → {res9_be['oos_r2']:.4f}  "
          f"(Δ = {r2_improvement:+.4f})")
    print(f"  OOS MAE (BE/A): {res6_be['oos_mae']:.4f} → {res9_be['oos_mae']:.4f}")

    # ─── Write output artifacts ─────────────────────────────────────────────
    OUT_DIR.mkdir(exist_ok=True)
    be_path   = OUT_DIR / "extended_binding_energy_law.txt"
    stab_path = OUT_DIR / "extended_stability_law.txt"

    write_law_file(res9_be, be_path, "BINDING ENERGY")
    write_law_file(res9_st, stab_path, "STABILITY")

    be_sha   = sha256_file(be_path)
    stab_sha = sha256_file(stab_path)

    print(f"\nWrote: {be_path}")
    print(f"  SHA-256: {be_sha}")
    print(f"Wrote: {stab_path}")
    print(f"  SHA-256: {stab_sha}")

    # ─── Write JSON artifacts for API use ───────────────────────────────────
    artifacts = {
        "parsimonious_be": res6_be,
        "extended_be":     res9_be,
        "parsimonious_stability": res6_st,
        "extended_stability":     res9_st,
    }
    artifact_path = OUT_DIR / "extended_law_training_results.json"
    with open(artifact_path, "w") as fh:
        json.dump(artifacts, fh, indent=2)
    print(f"Wrote: {artifact_path}")

    # ─── Append to PROVENANCE.md ─────────────────────────────────────────────
    if PROV_PATH.exists():
        with open(PROV_PATH, "a") as fh:
            fh.write(f"\n\n## SPEC_054_ENL — Extended BE Law (added 2026-05-12)\n\n")
            fh.write(f"| Artifact | SHA-256 |\n|---|---|\n")
            fh.write(f"| extended_binding_energy_law.txt | `{be_sha}` |\n")
            fh.write(f"| extended_stability_law.txt      | `{stab_sha}` |\n")
            fh.write(f"\n### Performance comparison\n\n")
            fh.write(f"| Model | CV MAE (MeV/A) | OOS R² |\n|---|---|---|\n")
            fh.write(f"| Parsimonious (6-term) | {res6_be['cv_mae_mean']:.4f} ± {res6_be['cv_mae_std']:.4f} | {res6_be['oos_r2']:.4f} |\n")
            fh.write(f"| Extended (9-term) | {res9_be['cv_mae_mean']:.4f} ± {res9_be['cv_mae_std']:.4f} | {res9_be['oos_r2']:.4f} |\n")
        print(f"Appended provenance to {PROV_PATH}")

    print("\nDone.")


if __name__ == "__main__":
    main()
