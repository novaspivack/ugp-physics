#!/usr/bin/env python3
"""
nubase_crossval.py — COMP-P03-B
================================
Proper 10-fold cross-validation on the full GTE feature model using
the training dataset (1,319 nuclei from AME2020/NUBASE2020).

Reports mean ± std MAE for each feature set (GTE Composition, Random Poly,
Enriched BW) at 10-fold CV — the headline out-of-sample accuracy figures.

Output: nuclear/nubase_crossval_results.json
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
TRAINING_CSV = ROOT / "papers/03_nuclear/training_data_with_stability.csv"
OUT_PATH = ROOT / "nuclear/nubase_crossval_results.json"

# ── Reuse feature builders from ablation script ───────────────────────────────
PROTON  = dict(a=5, b=11459, c=15, g=3)
NEUTRON = dict(a=5, b=11441, c=15, g=3)


def _gte_triple(Z, N):
    log_a = Z * np.log(PROTON["a"]) + N * np.log(NEUTRON["a"])
    a_eff = np.exp(np.minimum(log_a, 700))
    b_eff = Z * PROTON["b"] + N * NEUTRON["b"]
    c_eff = (Z * PROTON["c"] + N * NEUTRON["c"]).astype(float)
    g_eff = (Z * PROTON["g"] + N * NEUTRON["g"]).astype(float)
    return a_eff, b_eff, c_eff, g_eff


def build_gte_features(Z, N):
    A = Z + N
    a, b, c, g = _gte_triple(Z, N)
    eps = 1e-10
    k_gen = 0.0072973525693
    F = [a, b, c, g]
    F += [np.log(a+eps), np.log(b+eps), np.log(c+eps), np.log(g+eps)]
    F += [np.sqrt(a), np.sqrt(b), np.sqrt(c), np.sqrt(g)]
    for x in (a, b, c, g):
        xc = np.minimum(x, 1e7)
        F += [xc**2, xc**3]
    ac = np.minimum(a, 1e7); bc = np.minimum(b, 1e7)
    cc = np.minimum(c, 1e7); gc = np.minimum(g, 1e7)
    F += [ac*bc, ac*cc, ac*gc, bc*cc, bc*gc, cc*gc]
    F += [b/(a+eps), c/(b+eps), g/(c+eps), a/(g+eps)]
    abc_geo = (a*b*c+eps)**(1.0/3)
    abc_har = 3.0 / (1/(a+eps) + 1/(b+eps) + 1/(c+eps))
    F += [abc_geo, abc_har]
    mu_a = a - np.floor(a); mu_b = b - np.floor(b)
    mu_c = c - np.floor(c); mu_g = g - np.floor(g)
    F += [mu_a, mu_b, mu_c, mu_g]
    F += [mu_a+mu_b+mu_c+mu_g, mu_a*mu_b*mu_c*mu_g, np.abs(mu_a)+np.abs(mu_b)+np.abs(mu_c)+np.abs(mu_g)]
    F += [np.log(b/(c+eps))]
    F += [b/(a+eps), c/(b+eps), g/(c+eps)]
    ks = k_gen * (A**(2.0/3))
    F += [ks, ks**2, np.exp(np.minimum(ks, 50)), a*ks, b*ks, c*ks, g*ks]
    X = np.column_stack(F)
    return np.nan_to_num(np.clip(X, -1e30, 1e30), nan=0.0)


def build_random_poly_features(Z, N, seed=42):
    A = (Z + N).astype(float); Zf = Z.astype(float)
    n = len(Z)
    basis = np.column_stack([
        np.ones(n), A, Zf, A**2, A*Zf, Zf**2, A**3, A**2*Zf, A*Zf**2, Zf**3
    ])
    rng = np.random.default_rng(seed)
    W = rng.standard_normal((10, 50))
    return np.nan_to_num(basis @ W, nan=0.0)


def build_enriched_bw_features(Z, N):
    Z = Z.astype(float); N = N.astype(float); A = Z + N; eps = 1e-10
    vol = A; surf = A**(2.0/3); coul = Z*(Z-1)/(A**(1.0/3)+eps)
    asym = (N-Z)**2/(A+eps)
    pair_sign = np.where((Z%2==0)&(N%2==0), 1.0, np.where((Z%2==1)&(N%2==1), -1.0, 0.0))
    pairing = pair_sign/np.sqrt(A+eps)
    z_even = (Z%2==0).astype(float); n_even = (N%2==0).astype(float)
    F = [vol, surf, coul, asym, pairing,
         Z*(Z-1)/A, Z**2/A, (N-Z)/A, (N-Z)**4/(A**3+eps), A**(1.0/3), A**(4.0/3),
         z_even, n_even, z_even*n_even, ((N-Z)%2==0).astype(float)]
    magic_Z = np.array([2,8,20,28,50,82])
    for m in magic_Z: F.append(np.abs(Z-m))
    F.append(np.min(np.abs(Z[:,None]-magic_Z[None,:]),axis=1))
    F.append((np.abs(Z-114)).clip(0))
    magic_N = np.array([2,8,20,28,50,82,126])
    for m in magic_N: F.append(np.abs(N-m))
    F.append(np.min(np.abs(N[:,None]-magic_N[None,:]),axis=1))
    F.append((np.abs(N-184)).clip(0))
    for m in [2,8,20,28]:
        F.append((Z==m).astype(float)); F.append((N==m).astype(float))
    F += [N/(A+eps), Z/(A+eps), surf/(A+eps), coul/(A+eps),
          np.log(A+eps), np.log(Z+eps), np.log(N+eps), A**(1.0/6), Z*N/(A+eps)]
    X = np.column_stack(F)
    X = np.nan_to_num(X, nan=0.0, posinf=1e15, neginf=-1e15)
    if X.shape[1] > 50: X = X[:, :50]
    elif X.shape[1] < 50: X = np.hstack([X, np.zeros((X.shape[0], 50-X.shape[1]))])
    return X


XGB_PARAMS = dict(n_estimators=500, max_depth=6, learning_rate=0.05,
                  subsample=0.8, colsample_bytree=0.8, random_state=42,
                  n_jobs=-1, verbosity=0)


def cv_fold_mae(X, y, n_splits=10):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    maes = []
    for fold, (tr, te) in enumerate(kf.split(X)):
        pipe = Pipeline([("sc", StandardScaler()), ("xgb", xgb.XGBRegressor(**XGB_PARAMS))])
        pipe.fit(X[tr], y[tr])
        maes.append(mean_absolute_error(y[te], pipe.predict(X[te])))
        print(f"    fold {fold+1}/{n_splits}: MAE={maes[-1]:.4f}", flush=True)
    return float(np.mean(maes)), float(np.std(maes))


def main():
    print("=" * 62)
    print("COMP-P03-B  nubase_crossval.py")
    print("=" * 62)

    df = pd.read_csv(TRAINING_CSV)
    Z = df["Z"].values; N = df["N"].values; y = df["BE"].values
    print(f"\n[1] Dataset: {len(df)} nuclei")

    results = {}
    for name, X in [
        ("gte_composition", build_gte_features(Z, N)),
        ("random_poly_50",  build_random_poly_features(Z, N)),
        ("enriched_bw_50",  build_enriched_bw_features(Z, N)),
    ]:
        print(f"\n[{name}] 10-fold CV …")
        mu, sd = cv_fold_mae(X, y)
        results[name] = dict(cv_10fold_mean_mae=round(mu, 4), cv_10fold_std_mae=round(sd, 4))
        print(f"  → {mu:.4f} ± {sd:.4f} MeV")

    print("\n" + "=" * 62)
    for k, v in results.items():
        print(f"  {k:25s}  {v['cv_10fold_mean_mae']:.4f} ± {v['cv_10fold_std_mae']:.4f} MeV")
    print("=" * 62)

    output = dict(
        script="nuclear/nubase_crossval.py",
        spec_id="COMP-P03-B",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        n_samples=int(len(df)),
        cv_folds=10,
        **results
    )
    OUT_PATH.write_text(json.dumps(output, indent=2))
    sha = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()[:8]
    print(f"\nArtifact: {OUT_PATH}  SHA-256: {sha}")


if __name__ == "__main__":
    main()
