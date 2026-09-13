#!/usr/bin/env python3
"""
ablation_equal_size_random.py — COMP-P03-A
==========================================
Decision-gate ablation for Paper 3 (GTE Features for Nuclear Binding Energy).

Three XGBoost models, each using exactly 50 features, on the same data:
  1. GTE Composition Features  — from nucleon-seed GTE arithmetic
  2. Random Polynomial 50      — 50 random degree-≤3 polynomials in (A, Z); seed=42
  3. Enriched BW 50            — standard Bethe-Weizsäcker + shell + pairing + magic-number terms

Reports for each:
  - in_sample_mae   (training-set predictions)
  - cv_10fold_mae   (10-fold CV; approximates LOOCV for practical runtime)
  - nubase_mae      (held-out AME2020 nuclei not in training set)

Decision:
  Path A: GTE cv_10fold_mae < RandomPoly cv_10fold_mae  AND
          GTE cv_10fold_mae < EnrichedBW cv_10fold_mae
  Path B: otherwise

Output: nuclear/ablation_results.json
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold, cross_validate
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
TRAINING_CSV = ROOT / "papers/03_nuclear/training_data_with_stability.csv"
AME2020_MASS = ROOT / "nuclear/ame2020_data/mass_1.mas20.txt"
OUT_PATH = ROOT / "nuclear/ablation_results.json"

# ── GTE seed constants ────────────────────────────────────────────────────────
PROTON  = dict(a=5, b=11459, c=15, g=3)
NEUTRON = dict(a=5, b=11441, c=15, g=3)

# ─────────────────────────────────────────────────────────────────────────────
# Feature builders
# ─────────────────────────────────────────────────────────────────────────────

def _gte_triple(Z: np.ndarray, N: np.ndarray):
    """Compute composite GTE triple for Z protons + N neutrons."""
    log_a = Z * np.log(PROTON["a"]) + N * np.log(NEUTRON["a"])
    a_eff = np.exp(np.minimum(log_a, 700))
    b_eff = Z * PROTON["b"] + N * NEUTRON["b"]   # = 11441·A + 18·Z
    c_eff = (Z * PROTON["c"] + N * NEUTRON["c"]).astype(float)  # = 15·A
    g_eff = (Z * PROTON["g"] + N * NEUTRON["g"]).astype(float)  # = 3·A
    return a_eff, b_eff, c_eff, g_eff


def build_gte_features(Z: np.ndarray, N: np.ndarray) -> np.ndarray:
    """50 GTE composition features from nucleon-seed arithmetic."""
    A = Z + N
    a, b, c, g = _gte_triple(Z, N)

    eps = 1e-10
    k_gen = 0.0072973525693  # fine-structure constant (UGP Elegant Kernel)

    # Basic (4)
    F = [a, b, c, g]
    # Log (4)
    F += [np.log(a+eps), np.log(b+eps), np.log(c+eps), np.log(g+eps)]
    # Sqrt (4)
    F += [np.sqrt(a), np.sqrt(b), np.sqrt(c), np.sqrt(g)]
    # Squares and cubes (8)
    for x in (a, b, c, g):
        xc = np.minimum(x, 1e7)   # cap before squaring
        F += [xc**2, xc**3]
    # Pairwise cross-products (6)
    ac = np.minimum(a, 1e7); bc = np.minimum(b, 1e7)
    cc = np.minimum(c, 1e7); gc = np.minimum(g, 1e7)
    F += [ac*bc, ac*cc, ac*gc, bc*cc, bc*gc, cc*gc]
    # Sequential ratios (4)
    F += [b/(a+eps), c/(b+eps), g/(c+eps), a/(g+eps)]
    # Geometric and harmonic means of (a,b,c) (2)
    abc_geo = (a*b*c+eps) ** (1.0/3)
    abc_har = 3.0 / (1/(a+eps) + 1/(b+eps) + 1/(c+eps))
    F += [abc_geo, abc_har]
    # Fractional parts / mu (4)
    mu_a = a - np.floor(a); mu_b = b - np.floor(b)
    mu_c = c - np.floor(c); mu_g = g - np.floor(g)
    F += [mu_a, mu_b, mu_c, mu_g]
    # Mu combinations (3)
    F += [mu_a+mu_b+mu_c+mu_g, mu_a*mu_b*mu_c*mu_g, np.abs(mu_a)+np.abs(mu_b)+np.abs(mu_c)+np.abs(mu_g)]
    # Shell-strength ratio (1)
    F += [np.log(b/(c+eps))]
    # Relative indices (3)
    F += [b/(a+eps), c/(b+eps), g/(c+eps)]
    # k_gen × surface interactions (7)
    ks = k_gen * (A ** (2.0/3))
    F += [ks, ks**2, np.exp(np.minimum(ks, 50)), a*ks, b*ks, c*ks, g*ks]

    X = np.column_stack(F)
    X = np.nan_to_num(X, nan=0.0, posinf=1e30, neginf=-1e30)
    # Clip to float32 max to avoid overflow in StandardScaler
    X = np.clip(X, -1e30, 1e30)
    assert X.shape[1] == 50, f"GTE feature count mismatch: {X.shape[1]}"
    return X


def build_random_poly_features(Z: np.ndarray, N: np.ndarray, seed: int = 42) -> np.ndarray:
    """50 random degree-≤3 polynomial features in (A, Z).

    Each feature is a random linear combination of the 10-term degree-3
    polynomial basis {1, A, Z, A², AZ, Z², A³, A²Z, AZ², Z³}.
    Coefficients are drawn i.i.d. N(0,1) with a fixed seed.
    """
    A = (Z + N).astype(float)
    Zf = Z.astype(float)
    n_samples = len(Z)

    # Degree-3 polynomial basis over (A, Z) — 10 terms
    basis = np.column_stack([
        np.ones(n_samples),      # 1
        A,                        # A
        Zf,                       # Z
        A**2, A*Zf, Zf**2,       # degree-2
        A**3, A**2*Zf, A*Zf**2, Zf**3,  # degree-3
    ])  # shape (n, 10)

    rng = np.random.default_rng(seed)
    W = rng.standard_normal((10, 50))   # 50 random projections
    X = basis @ W                        # shape (n, 50)
    X = np.nan_to_num(X, nan=0.0, posinf=1e15, neginf=-1e15)
    return X


def build_enriched_bw_features(Z: np.ndarray, N: np.ndarray) -> np.ndarray:
    """50 enriched Bethe-Weizsäcker features."""
    Z = Z.astype(float); N = N.astype(float)
    A = Z + N
    eps = 1e-10

    # Standard SEMF terms (5)
    vol   = A
    surf  = A**(2.0/3)
    coul  = Z*(Z-1) / (A**(1.0/3) + eps)
    asym  = (N-Z)**2 / (A + eps)
    z_even = (Z % 2 == 0).astype(float)
    n_even = (N % 2 == 0).astype(float)
    pair_sign = np.where((Z % 2 == 0) & (N % 2 == 0), 1.0,
                 np.where((Z % 2 == 1) & (N % 2 == 1), -1.0, 0.0))
    pairing = pair_sign / np.sqrt(A + eps)

    F = [vol, surf, coul, asym, pairing]

    # Higher-order BW variants (6)
    F += [
        Z*(Z-1)/A,            # Coulomb / A
        Z**2 / A,             # fissility
        (N-Z)/A,              # asymmetry ratio
        (N-Z)**4 / (A**3 + eps),  # higher-order asymmetry
        A**(1.0/3),
        A**(4.0/3),
    ]

    # Pairing / structure (4)
    F += [z_even, n_even, z_even*n_even, ((N-Z) % 2 == 0).astype(float)]

    # Magic-number Z distances (9)
    magic_Z = np.array([2, 8, 20, 28, 50, 82])
    for m in magic_Z:
        F.append(np.abs(Z - m))
    F.append(np.min(np.abs(Z[:, None] - magic_Z[None, :]), axis=1))  # nearest magic Z
    F.append((np.abs(Z - 114)).clip(0))   # super-heavy shell

    # Magic-number N distances (9)
    magic_N = np.array([2, 8, 20, 28, 50, 82, 126])
    for m in magic_N:
        F.append(np.abs(N - m))
    F.append(np.min(np.abs(N[:, None] - magic_N[None, :]), axis=1))  # nearest magic N
    F.append((np.abs(N - 184)).clip(0))   # predicted shell

    # Shell-closure indicators (8)
    for m in [2, 8, 20, 28]:
        F.append((Z == m).astype(float))
        F.append((N == m).astype(float))

    # Ratios and cross terms (9)
    F += [
        N / (A + eps),
        Z / (A + eps),
        surf / (A + eps),
        coul / (A + eps),
        np.log(A + eps),
        np.log(Z + eps),
        np.log(N + eps),
        A**(1.0/6),
        Z*N / (A + eps),
    ]

    X = np.column_stack(F)
    X = np.nan_to_num(X, nan=0.0, posinf=1e15, neginf=-1e15)
    if X.shape[1] != 50:
        # Trim or pad to exactly 50
        if X.shape[1] > 50:
            X = X[:, :50]
        else:
            pad = np.zeros((X.shape[0], 50 - X.shape[1]))
            X = np.hstack([X, pad])
    return X


# ─────────────────────────────────────────────────────────────────────────────
# AME2020 parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_ame2020(path: Path) -> pd.DataFrame:
    """Parse AME2020 mass table; return DataFrame with Z, N, A, BE (MeV)."""
    rows = []
    with open(path) as f:
        for line in f:
            if len(line) < 68:
                continue
            try:
                z_str = line[9:14].strip()
                a_str = line[14:19].strip()
                be_str = line[54:67].strip()
                if not z_str or not a_str or not be_str:
                    continue
                # Skip estimated values (contain '#')
                if '#' in z_str or '#' in a_str or '#' in be_str:
                    continue
                Z = int(z_str)
                A = int(a_str)
                if A < 2 or Z < 1:
                    continue
                be_per_A_keV = float(be_str)
                N = A - Z
                if N < 0:
                    continue
                be_mev = be_per_A_keV * A / 1000.0
                rows.append(dict(Z=Z, N=N, A=A, BE=be_mev))
            except (ValueError, IndexError):
                continue
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Model training helpers
# ─────────────────────────────────────────────────────────────────────────────

XGB_PARAMS = dict(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    verbosity=0,
)


def _make_pipeline() -> Pipeline:
    """StandardScaler → XGBoost pipeline (handles large-value GTE features)."""
    return Pipeline([
        ("scaler", StandardScaler()),
        ("xgb", xgb.XGBRegressor(**XGB_PARAMS)),
    ])


def run_cv(X: np.ndarray, y: np.ndarray, cv: int = 10) -> float:
    """Return mean absolute error from k-fold CV (scaled pipeline)."""
    kf = KFold(n_splits=cv, shuffle=True, random_state=42)
    scores = -cross_val_score(
        _make_pipeline(), X, y,
        cv=kf, scoring="neg_mean_absolute_error", n_jobs=1
    )
    return float(np.mean(scores))


def train_and_eval(X_train: np.ndarray, y_train: np.ndarray,
                   X_nubase: np.ndarray, y_nubase: np.ndarray,
                   name: str) -> dict:
    """Train XGBoost pipeline on full training set; report in-sample and NUBASE MAE."""
    print(f"  Training {name} …", flush=True)
    pipe = _make_pipeline()
    pipe.fit(X_train, y_train)
    y_pred_train = pipe.predict(X_train)
    insample_mae = float(mean_absolute_error(y_train, y_pred_train))
    y_pred_nubase = pipe.predict(X_nubase)
    nubase_mae = float(mean_absolute_error(y_nubase, y_pred_nubase))
    return dict(in_sample_mae=round(insample_mae, 4), nubase_mae=round(nubase_mae, 4))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("COMP-P03-A  ablation_equal_size_random.py")
    print("=" * 62)

    # ── Load training data ───────────────────────────────────────────────
    print("\n[1] Loading training data …")
    train_df = pd.read_csv(TRAINING_CSV)
    Z_tr = train_df["Z"].values
    N_tr = train_df["N"].values
    y_tr = train_df["BE"].values
    print(f"    Training set: {len(train_df)} nuclei")

    # ── Build training feature matrices ─────────────────────────────────
    print("\n[2] Building feature matrices (50 features each) …")
    X_gte  = build_gte_features(Z_tr, N_tr)
    X_rand = build_random_poly_features(Z_tr, N_tr, seed=42)
    X_bw   = build_enriched_bw_features(Z_tr, N_tr)
    print(f"    GTE  shape: {X_gte.shape}")
    print(f"    Rand shape: {X_rand.shape}")
    print(f"    BW   shape: {X_bw.shape}")

    # ── 10-fold CV ───────────────────────────────────────────────────────
    print("\n[3] Running 10-fold CV (approximates LOOCV) …")
    cv_gte  = run_cv(X_gte,  y_tr)
    print(f"    GTE  10-fold CV MAE = {cv_gte:.4f} MeV")
    cv_rand = run_cv(X_rand, y_tr)
    print(f"    Rand 10-fold CV MAE = {cv_rand:.4f} MeV")
    cv_bw   = run_cv(X_bw,   y_tr)
    print(f"    BW   10-fold CV MAE = {cv_bw:.4f} MeV")

    # ── Load AME2020 for out-of-sample NUBASE evaluation ─────────────────
    print("\n[4] Parsing AME2020 for NUBASE evaluation …")
    ame_df = parse_ame2020(AME2020_MASS)
    print(f"    AME2020 rows (experimental, A≥2): {len(ame_df)}")

    # Keep only nuclei NOT in training set  (different (Z,N) pairs)
    train_keys = set(zip(Z_tr.tolist(), N_tr.tolist()))
    mask_new = ~ame_df.apply(lambda r: (int(r["Z"]), int(r["N"])) in train_keys, axis=1)
    nubase_holdout = ame_df[mask_new].reset_index(drop=True)
    print(f"    Hold-out NUBASE nuclei: {len(nubase_holdout)}")

    Z_nb = nubase_holdout["Z"].values
    N_nb = nubase_holdout["N"].values
    y_nb = nubase_holdout["BE"].values

    X_gte_nb  = build_gte_features(Z_nb, N_nb)
    X_rand_nb = build_random_poly_features(Z_nb, N_nb, seed=42)
    X_bw_nb   = build_enriched_bw_features(Z_nb, N_nb)

    # ── Train on full training set & evaluate NUBASE ─────────────────────
    print("\n[5] Training on full training set and evaluating NUBASE …")
    res_gte  = train_and_eval(X_gte,  y_tr, X_gte_nb,  y_nb, "GTE Composition")
    res_rand = train_and_eval(X_rand, y_tr, X_rand_nb, y_nb, "Random Poly 50")
    res_bw   = train_and_eval(X_bw,   y_tr, X_bw_nb,   y_nb, "Enriched BW 50")

    res_gte["cv_10fold_mae"]  = round(cv_gte,  4)
    res_rand["cv_10fold_mae"] = round(cv_rand, 4)
    res_bw["cv_10fold_mae"]   = round(cv_bw,   4)

    # ── Decision ─────────────────────────────────────────────────────────
    path_a = (cv_gte < cv_rand) and (cv_gte < cv_bw)
    path = "A" if path_a else "B"
    margin_vs_rand = round(cv_rand - cv_gte, 4)
    margin_vs_bw   = round(cv_bw   - cv_gte, 4)

    print("\n" + "=" * 62)
    print(f"  GTE   CV MAE = {cv_gte:.4f} MeV")
    print(f"  Rand  CV MAE = {cv_rand:.4f} MeV   (GTE margin: {margin_vs_rand:+.4f})")
    print(f"  BW    CV MAE = {cv_bw:.4f} MeV   (GTE margin: {margin_vs_bw:+.4f})")
    print(f"\n  DECISION → PATH {path}")
    if path == "A":
        print("  GTE features WIN vs both baselines — full UGP nuclear paper.")
    else:
        print("  GTE features do NOT beat both baselines — reposition as ML methods paper.")
    print("=" * 62)

    # ── Artifact ─────────────────────────────────────────────────────────
    output = {
        "script": "nuclear/ablation_equal_size_random.py",
        "spec_id": "COMP-P03-A",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_training": int(len(train_df)),
        "n_nubase_holdout": int(len(nubase_holdout)),
        "cv_folds": 10,
        "gte_composition": {
            "in_sample_mae": res_gte["in_sample_mae"],
            "cv_10fold_mae": res_gte["cv_10fold_mae"],
            "nubase_mae": res_gte["nubase_mae"],
        },
        "random_poly_50": {
            "in_sample_mae": res_rand["in_sample_mae"],
            "cv_10fold_mae": res_rand["cv_10fold_mae"],
            "nubase_mae": res_rand["nubase_mae"],
        },
        "enriched_bw_50": {
            "in_sample_mae": res_bw["in_sample_mae"],
            "cv_10fold_mae": res_bw["cv_10fold_mae"],
            "nubase_mae": res_bw["nubase_mae"],
        },
        "decision": {
            "path": path,
            "gte_beats_random_poly": bool(cv_gte < cv_rand),
            "gte_beats_enriched_bw": bool(cv_gte < cv_bw),
            "margin_vs_random_poly_mev": margin_vs_rand,
            "margin_vs_enriched_bw_mev": margin_vs_bw,
        },
    }

    OUT_PATH.write_text(json.dumps(output, indent=2))
    sha256 = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()[:8]
    print(f"\nArtifact: {OUT_PATH}")
    print(f"SHA-256 prefix: {sha256}")
    print("Done.")


if __name__ == "__main__":
    main()
