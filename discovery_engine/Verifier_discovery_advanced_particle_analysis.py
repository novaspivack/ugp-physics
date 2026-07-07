# Pattern_test_curves_2.py  (enhanced)
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import namedtuple
import random
from math import erf, sqrt
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- Add for checkpointing/db ---
import hashlib
import time
import sqlite3

# ---------------- DEFAULT CONFIG ----------------
DEFAULT_CSV_PATH = "discovery_runs/new_UCL2_discovery_run_20250825-033418_9e2616a4/candidates.csv"
MASS_CUTOFF_DEFAULT = float('inf')  # No cutoff by default - analyze full CSV
REL_EPS = 0.02     # tolerance in log10 space ≈ 4.6% in mass
ABS_EPS = 0.005    # tolerance in log10 units
LAMBDA_P = 0.5     # param penalty
LAMBDA_F = 0.25    # family prior penalty
MAX_CURVES_DEFAULT = 10
RANSAC_TRIALS_DEFAULT = 3000
SM_WEIGHT = 3.0
STABLE_BONUS = 1.2  # apply to classification_color=='Green'
RANDOM_SEED = 42
# -------------------------------------------------

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

Curve = namedtuple("Curve", "family theta score n_inliers sm_hits bic")

# ------------------------- CHECKPOINT / IO UTILS -------------------------

def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def _save_json(path: Path, obj: dict):
    path.write_text(json.dumps(obj, indent=2))

def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

# ------------------------- OPTIONAL SQLITE SINK -------------------------

def _init_db(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS runs(
            run_id TEXT PRIMARY KEY,
            created_at TEXT,
            csv_path TEXT,
            csv_hash TEXT,
            args_json TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS curves(
            run_id TEXT,
            rank INTEGER,
            family TEXT,
            theta TEXT,
            expression TEXT,
            score REAL,
            inliers INTEGER,
            sm_hits INTEGER,
            bic REAL,
            PRIMARY KEY(run_id, rank)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS curve_inliers(
            run_id TEXT,
            rank INTEGER,
            particle_id TEXT,
            PRIMARY KEY(run_id, rank, particle_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lm_curves(
            run_id TEXT,
            rank INTEGER,
            family TEXT,
            theta TEXT,
            expression TEXT,
            score REAL,
            inliers INTEGER,
            sm_hits INTEGER,
            PRIMARY KEY(run_id, rank)
        )
    """)
    conn.commit()
    return conn

def _db_write_curves(conn, run_id: str, curves_json: list):
    cur = conn.cursor()
    for c in curves_json:
        cur.execute(
            "INSERT OR REPLACE INTO curves(run_id, rank, family, theta, expression, score, inliers, sm_hits, bic) VALUES(?,?,?,?,?,?,?,?,?)",
            (run_id, c['rank'], c['family'], json.dumps(c['theta']), c['expression'], c['score'], c['inliers'], c['sm_hits'], c.get('bic'))
        )
        for pid in c.get('inlier_ids', []):
            cur.execute("INSERT OR REPLACE INTO curve_inliers(run_id, rank, particle_id) VALUES(?,?,?)",
                        (run_id, c['rank'], pid))
    conn.commit()

def _db_write_lm_curves(conn, run_id: str, lm_json: list):
    cur = conn.cursor()
    for c in lm_json:
        cur.execute(
            "INSERT OR REPLACE INTO lm_curves(run_id, rank, family, theta, expression, score, inliers, sm_hits) VALUES(?,?,?,?,?,?,?,?)",
            (run_id, c['rank'], c['family'], json.dumps(c['theta']), c['expression'], c['score'], c['inliers'], c['sm_hits'])
        )
    conn.commit()

# ------------------------- DATA LOADING -------------------------

def load_df(csv_path: str, mass_cutoff: float) -> pd.DataFrame:
    df: pd.DataFrame = pd.read_csv(csv_path)
    mass = df.get("mass_mev_calibrated", pd.Series(np.nan, index=df.index))
    mass = mass.fillna(df.get("mass_mev_raw", np.nan))
    df["mass_eff"] = mass

    # Special handling for mass cutoff: Keep Top quark (particle_top) even if above cutoff
    # but exclude other unreliable high-mass particles
    before_filter = len(df)
    
    # Create mask for particles to keep
    keep_mask = (
        np.isfinite(df["mass_eff"]) & 
        (df["mass_eff"] > 1e-6) & 
        (
            (df["mass_eff"] < mass_cutoff) |  # Below cutoff: keep all
            (df["id"] == "particle_top")      # Above cutoff: keep only Top quark
        )
    )
    
    df = df[keep_mask].copy()  # type: ignore
    
    after_filter = len(df)
    removed_count = before_filter - after_filter
    
    # Log what was removed
    if removed_count > 0:
        # Check if we kept the Top quark
        top_mask = df['id'] == 'particle_top'
        if top_mask.any():
            top_mass = df.loc[top_mask, 'mass_eff'].iloc[0]
            print(f"✅ Kept Top quark (mass: {top_mass/1000:.2f} GeV)")
        
        print(f"⚠️  Mass filtering: {removed_count} particles removed above {mass_cutoff/1000:.1f} GeV cutoff")
        print(f"   (Excluded unreliable high-mass UGP particles, kept verified SM particles)")
    else:
        print(f"✅ Mass filtering: No particles removed")

    # Branch inference via residue classes of the even ladder
    # Handle large integers by using Python's built-in modulo operation
    mod = df["b"].apply(lambda x: int(x) % 233 if pd.notna(x) else np.nan)
    df["branch_inferred"] = np.where(mod==42, "our", np.where(mod==24, "mirror", "off_ladder"))

    # ladder index k (only meaningful on ladder)
    k = np.full(len(df), np.nan, dtype="float64")
    cond_our = (df["branch_inferred"]=="our")
    cond_mir = (df["branch_inferred"]=="mirror")
    # Use apply for large integer operations
    b_our = df.loc[cond_our, "b"].apply(lambda x: int(x) if pd.notna(x) else np.nan)
    b_mir = df.loc[cond_mir, "b"].apply(lambda x: int(x) if pd.notna(x) else np.nan)
    k[cond_our] = (b_our - 42) / 233.0
    k[cond_mir] = (b_mir - 24) / 233.0
    df["k"] = k
    df["k_is_int"] = np.isclose(df["k"], np.round(df["k"]), atol=1e-9)

    # Insist on integer ladder index when mining curves
    df = df[df["k_is_int"]].copy()  # type: ignore

    # c-state annotation
    df["c_state"] = np.where(df["c"]==65535, "ridge_65535",
                        np.where(df["c"]==15, "latched_15", "transitional"))

    # y = log10 mass
    df["log_mass"] = np.log10(df["mass_eff"].astype("float64"))
    
    # Keep both sources if present
    tau_raw = df.get("lifetime_s_raw")
    tau_cal = df.get("lifetime_s")

    # Canonicalize to float columns
    df["lifetime_raw"] = tau_raw.astype("float64") if tau_raw is not None else np.nan
    df["lifetime_cal"] = tau_cal.astype("float64") if tau_cal is not None else np.nan

    # Build both logs
    def _safe_log10(s):
        out = pd.Series(np.nan, index=df.index)
        m = np.isfinite(s) & (s > 0)
        out[m] = np.log10(s[m])
        return out

    df["log_tau_raw"] = _safe_log10(df["lifetime_raw"])
    df["log_tau_cal"] = _safe_log10(df["lifetime_cal"])

    # Weights: base=1, SM boost, stability bonus
    is_sm = df["id"].astype(str).str.startswith("particle_")
    df["w"] = 1.0
    df.loc[is_sm, "w"] *= SM_WEIGHT
    df.loc[df["classification_color"]=="Green", "w"] *= STABLE_BONUS

    return df

# === NEW: sector tagging ===
def add_sector(df: pd.DataFrame) -> pd.DataFrame:
    cm  = df.get("canonical_match", pd.Series("", index=df.index)).fillna("").astype(str)
    pid = df.get("id", pd.Series("", index=df.index)).fillna("").astype(str).str.lower()

    is_neu  = cm.str.contains("neutrino") | pid.str.contains("neutrino")
    is_bos  = pid.str.contains("w_boson|z_boson|higgs_boson")
    is_comp = cm.isin(["proton","neutron","lambda","sigma_plus","sigma_zero","sigma_minus","xi_zero","xi_minus","omega_minus"]) | pid.str.contains("proton|neutron|lambda|sigma|xi|omega|photon|gluon")
    # fermion = default (charged leptons + quarks)
    sector = np.select([is_neu, is_bos, is_comp], ["neutrino","boson","composite"], default="fermion")
    df["sector"] = sector
    return df

# ------------------------- MODEL EVAL ---------------------------

def model_eval(family: str, theta: tuple, x: np.ndarray) -> np.ndarray:
    """Evaluate model y(x) for the requested family."""
    if family == "const":  # y = A
        (A,) = theta
        return np.full_like(x, A, dtype="float64")
    if family == "line":   # y = A + Bx
        A,B = theta
        return A + B*x
    if family == "quad":   # y = A + Bx + Cx^2
        A,B,C = theta
        return A + B*x + C*(x**2)
    if family == "hinge_centered":  # y = A + B*(x-k0) + D*max(0,x-k0)
        A,B,D,k0 = theta
        z = x - k0
        return A + B*z + D*np.maximum(0.0, z)
    if family == "hinge2_centered": # y = A + B*(x-k0) + D0*max(0,x-k0) + D1*max(0,x-k1)
        A,B,D0,k0,D1,k1 = theta
        z0 = x - k0
        return A + B*z0 + D0*np.maximum(0.0, z0) + D1*np.maximum(0.0, x - k1)
    raise ValueError(f"unknown family: {family}")

# ------------------------- FITTERS ------------------------------

def fit_from_points_bootstrap(family: str, pts: list) -> tuple | None:
    """Fast bootstrap-specific fitting - uses simple quantile-based breakpoints."""
    x = np.array([p[0] for p in pts], dtype="float64")
    y = np.array([p[1] for p in pts], dtype="float64")
    if family == "const":
        return (float(np.median(y)),)
    if family == "line":
        if len(pts) < 2 or np.allclose(x[0], x[1]):
            return None
        B = (y[1]-y[0])/(x[1]-x[0])
        A = y[0] - B*x[0]
        return (float(A), float(B))
    if family == "quad":
        if len(pts) < 3:
            return None
        M = np.vstack([np.ones_like(x), x, x**2]).T
        try:
            theta, *_ = np.linalg.lstsq(M, y, rcond=None)
            return (float(theta[0]), float(theta[1]), float(theta[2]))
        except np.linalg.LinAlgError:
            return None
    if family == "hinge_centered":
        if len(pts) < 3:
            return None
        # Fast bootstrap: use only 20 quantiles for speed
        quantiles = np.quantile(x, np.linspace(0.05, 0.95, 20))
        k0_candidates = np.unique(quantiles)
        best = None
        best_sse = np.inf
        for k0 in k0_candidates:
            z = x - k0
            Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
            try:
                (A,B,D), *_ = np.linalg.lstsq(Phi, y, rcond=None)
                yhat = A + B*z + D*np.maximum(0.0, z)
                sse = float(np.sum((y - yhat)**2))
                if sse < best_sse:
                    best_sse = sse
                    best = (float(A), float(B), float(D), float(k0))
            except:
                continue
        return best
    if family == "hinge2_centered":
        if len(pts) < 4:
            return None
        # Fast bootstrap: use only 10x10 grid for speed
        k0_quants = np.quantile(x, np.linspace(0.1, 0.9, 10))
        k1_quants = np.quantile(x, np.linspace(0.1, 0.9, 10))
        best = None
        best_sse = np.inf
        for k0 in k0_quants:
            for k1 in k1_quants:
                if k1 <= k0:
                    continue
                z0 = x - k0
                Phi = np.vstack([
                    np.ones_like(z0), z0,
                    np.maximum(0.0, z0),
                    np.maximum(0.0, x - k1)
                ]).T
                try:
                    (A,B,D0,D1), *_ = np.linalg.lstsq(Phi, y, rcond=None)
                    yhat = A + B*z0 + D0*np.maximum(0.0, z0) + D1*np.maximum(0.0, x - k1)
                    sse = float(np.sum((y - yhat)**2))
                    if sse < best_sse:
                        best_sse = sse
                        best = (float(A), float(B), float(D0), float(k0), float(D1), float(k1))
                except:
                    continue
        return best
    return None

def fit_from_points(family: str, pts: list) -> tuple | None:
    """Minimal closed-form fits from tiny samples."""
    x = np.array([p[0] for p in pts], dtype="float64")
    y = np.array([p[1] for p in pts], dtype="float64")
    if family == "const":
        return (float(np.median(y)),)
    if family == "line":
        if len(pts) < 2 or np.allclose(x[0], x[1]):
            return None
        B = (y[1]-y[0])/(x[1]-x[0])
        A = y[0] - B*x[0]
        return (float(A), float(B))
    if family == "quad":
        if len(pts) < 3:
            return None
        M = np.vstack([np.ones_like(x), x, x**2]).T
        try:
            theta, *_ = np.linalg.lstsq(M, y, rcond=None)
            return (float(theta[0]), float(theta[1]), float(theta[2]))
        except np.linalg.LinAlgError:
            return None
    if family == "hinge_centered":
        if len(pts) < 3:
            return None
        # Ultra-high-density breakpoint selection: use extremely dense quantiles + sample points
        # This provides maximum coverage while still being much faster than exhaustive
        # Generate 400 quantiles (every 0.25th percentile) + 100 sample points = 500 total
        quantile_percentiles = np.linspace(0.25, 99.75, 400)  # 0.25, 0.5, 0.75, ..., 99.75
        quantiles = np.quantile(x, quantile_percentiles / 100.0)
        sample_points = np.random.choice(x, size=min(100, len(x)), replace=False)
        k0_candidates = np.unique(np.r_[quantiles, sample_points])
        print(f"🔍 Testing {len(k0_candidates)} hinge breakpoints on {len(x)} points...")
        best = None
        best_sse = np.inf
        for i, k0 in enumerate(k0_candidates):
            if i % max(1, len(k0_candidates)//5) == 0:  # Print progress every 20%
                print(f"🔄 Testing breakpoint {i+1}/{len(k0_candidates)}: k0={k0:.2f}")
            z = x - k0
            Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
            try:
                theta, *_ = np.linalg.lstsq(Phi, y, rcond=None)  # (A,B,D)
            except np.linalg.LinAlgError:
                continue
            yhat = Phi @ theta
            sse = float(np.sum((y - yhat)**2))
            if sse < best_sse:
                best_sse = sse
                best = (float(theta[0]), float(theta[1]), float(theta[2]), float(k0))
        print(f"✅ Hinge fitting completed, best SSE: {best_sse:.2f}")
        return best  # (A,B,D,k0)
    if family == "hinge2_centered":
        if len(pts) < 4:
            return None
        kc = np.unique(np.r_[x, np.quantile(x, [0.15, 0.35, 0.5, 0.65, 0.85])])
        best_theta = None
        best_sse = np.inf
        for k0 in kc:
            for k1 in kc:
                if k1 <= k0:
                    continue
                z0 = x - k0
                Phi = np.vstack([
                    np.ones_like(x),              # A
                    z0,                           # B*(x-k0)
                    np.maximum(0.0, z0),          # D0*max(0,x-k0)
                    np.maximum(0.0, x - k1)       # D1*max(0,x-k1)
                ]).T
                try:
                    th, *_ = np.linalg.lstsq(Phi, y, rcond=None)  # (A,B,D0,D1)
                except np.linalg.LinAlgError:
                    continue
                yhat = Phi @ th
                sse = float(np.sum((y - yhat)**2))
                if sse < best_sse:
                    best_sse = sse
                    best_theta = (float(th[0]), float(th[1]), float(th[2]), float(k0), float(th[3]), float(k1))
        return best_theta
    return None

# ------------------------- RANSAC / SCORING ---------------------

def inliers_mask(y: np.ndarray, yhat: np.ndarray, rel_eps=REL_EPS, abs_eps=ABS_EPS) -> np.ndarray:
    tol = np.maximum(abs_eps, rel_eps*np.abs(y))
    return np.abs(y - yhat) <= tol

def longest_run_length(ks_int: np.ndarray) -> int:
    """Longest consecutive run in integer ks."""
    if len(ks_int) == 0:
        return 0
    ks = np.sort(np.unique(ks_int))
    runs = 1
    best = 1
    for i in range(1, len(ks)):
        runs = runs + 1 if ks[i] == ks[i-1] + 1 else 1
        best = max(best, runs)
    return best

def ransac_family(df: pd.DataFrame, family: str, trials: int=1000):
    sub: pd.DataFrame = df[np.isfinite(df["k"])].copy()  # type: ignore
    x = sub["k"].to_numpy(dtype="float64")
    y = sub["log_mass"].to_numpy(dtype="float64")
    w = sub["w"].to_numpy(dtype="float64")
    is_sm = sub["id"].astype(str).str.startswith("particle_").to_numpy()

    need = {"const":1, "line":2, "quad":3, "hinge_centered":3, "hinge2_centered":4}[family]

    # Check if we have enough data points
    if len(sub) < need:
        return None, sub

    best = None
    for _ in range(trials):
        idx = np.random.choice(len(sub), size=need, replace=False)
        pts = list(zip(x[idx], y[idx]))
        theta = fit_from_points(family, pts)
        if theta is None:
            continue
        yhat = model_eval(family, theta, x)
        mask = inliers_mask(y, yhat)
        if mask.sum() < need:
            continue

        Xin = x[mask]; Yin = y[mask]
        # Refine by LS on inliers
        if family in ("const","line","quad","hinge_centered","hinge2_centered"):
            if family == "const":
                A = (float(np.median(Yin)),)
            elif family == "line":
                M = np.vstack([np.ones_like(Xin), Xin]).T
                A, *_ = np.linalg.lstsq(M, Yin, rcond=None)
                A = tuple(map(float, A))
            elif family == "quad":
                M = np.vstack([np.ones_like(Xin), Xin, Xin**2]).T
                A, *_ = np.linalg.lstsq(M, Yin, rcond=None)
                A = tuple(map(float, A))
            elif family == "hinge_centered":
                k0 = float(theta[-1])
                z = Xin - k0
                Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
                (A1,B1,D1), *_ = np.linalg.lstsq(Phi, Yin, rcond=None)
                A = (float(A1), float(B1), float(D1), float(k0))
            elif family == "hinge2_centered":
                A0,B0,D00,k00,D10,k10 = theta
                z0 = Xin - k00
                Phi = np.vstack([
                    np.ones_like(z0), z0,
                    np.maximum(0.0, z0),
                    np.maximum(0.0, Xin - k10)
                ]).T
                (A1,B1,D01,D11), *_ = np.linalg.lstsq(Phi, Yin, rcond=None)
                A = (float(A1), float(B1), float(D01), float(k00), float(D11), float(k10))
        else:
            A = theta

        yhat = model_eval(family, A, x)
        mask = inliers_mask(y, yhat)
        nin = int(mask.sum())
        sm_hits = int(is_sm[mask].sum())
        p = len(A)
        fam_pen = {"const":0, "line":1, "quad":2, "hinge_centered":2, "hinge2_centered":3}[family]

        # Contiguity and slope regularization
        ks_in = np.round(x[mask]).astype(int)
        runlen = longest_run_length(ks_in)
        contiguity_bonus = np.log1p(runlen)

        if family == "hinge_centered":
            if len(A) == 4:
                _, B_val, D_val, _ = A
                slope_pen = 1e2 * (B_val**2 + D_val**2)
            else:
                slope_pen = 0.0
        elif family == "hinge2_centered":
            if len(A) == 6:
                _, B_val, D0, _, D1, _ = A
                slope_pen = 1.5e2 * (B_val**2 + D0**2 + D1**2)
            else:
                slope_pen = 0.0
        else:
            slope_pen = 0.0

        score = float((w[mask].sum())
                      - LAMBDA_P*p
                      - LAMBDA_F*fam_pen
                      - slope_pen
                      + contiguity_bonus)

        if nin >= p+1:
            resid = y[mask] - yhat[mask]
            sse = float(np.sum(resid**2))
            bic = nin*np.log(sse/nin) + p*np.log(nin) if sse>0 else -np.inf
        else:
            bic = np.inf

        cur = Curve(family, A, score, nin, sm_hits, bic)
        if (best is None) or (cur.score > best.score):
            best = cur

    return best, sub

# ----------- MULTIPROCESSING RANSAC -----------
def _ransac_trial(args):
    """Single RANSAC trial for multiprocessing - self-contained with all dependencies."""
    x, y, w, is_sm, family, need, constants = args
    LAMBDA_P, LAMBDA_F, REL_EPS, ABS_EPS = constants
    
    # Local copies of functions to avoid global dependencies
    def _model_eval(family: str, theta: tuple, x: np.ndarray) -> np.ndarray:
        """Evaluate model y(x) for the requested family."""
        if family == "const":  # y = A
            return np.full_like(x, theta[0])
        elif family == "line":  # y = A + B*x
            A, B = theta
            return A + B*x
        elif family == "quad":  # y = A + B*x + C*x^2
            A, B, C = theta
            return A + B*x + C*x**2
        elif family == "hinge_centered":  # y = A + B*(x-k0) + D*max(0,x-k0)
            A, B, D, k0 = theta
            z = x - k0
            return A + B*z + D*np.maximum(0.0, z)
        elif family == "hinge2_centered":  # y = A + B*(x-k0) + D0*max(0,x-k0) + D1*max(0,x-k1)
            A, B, D0, k0, D1, k1 = theta
            z0 = x - k0
            return A + B*z0 + D0*np.maximum(0.0, z0) + D1*np.maximum(0.0, x - k1)
        else:
            return np.full_like(x, np.nan)
    
    def _fit_from_points(family: str, pts: list) -> tuple | None:
        """Minimal closed-form fits from tiny samples."""
        x = np.array([p[0] for p in pts], dtype="float64")
        y = np.array([p[1] for p in pts], dtype="float64")
        if family == "const":
            return (float(np.median(y)),)
        elif family == "line":
            M = np.vstack([np.ones_like(x), x]).T
            A, *_ = np.linalg.lstsq(M, y, rcond=None)
            return tuple(map(float, A))
        elif family == "quad":
            M = np.vstack([np.ones_like(x), x, x**2]).T
            A, *_ = np.linalg.lstsq(M, y, rcond=None)
            return tuple(map(float, A))
        elif family == "hinge_centered":
            # Simple 3-point hinge: use first, middle, last points
            if len(pts) < 3:
                return None
            x0, y0 = pts[0]
            x1, y1 = pts[len(pts)//2]
            x2, y2 = pts[-1]
            # Estimate k0 as middle x, solve for A,B,D
            k0 = float(x1)
            z0, z1, z2 = x0-k0, x1-k0, x2-k0
            Phi = np.array([[1, z0, max(0, z0)], [1, z1, max(0, z1)], [1, z2, max(0, z2)]])
            try:
                A, B, D = np.linalg.solve(Phi, [y0, y1, y2])
                return (float(A), float(B), float(D), float(k0))
            except:
                return None
        elif family == "hinge2_centered":
            # Simple 4-point double hinge
            if len(pts) < 4:
                return None
            x0, y0 = pts[0]
            x1, y1 = pts[len(pts)//3]
            x2, y2 = pts[2*len(pts)//3]
            x3, y3 = pts[-1]
            k0, k1 = float(x1), float(x2)
            z0, z1, z2, z3 = x0-k0, x1-k0, x2-k0, x3-k0
            Phi = np.array([
                [1, z0, max(0, z0), max(0, x0-k1)],
                [1, z1, max(0, z1), max(0, x1-k1)],
                [1, z2, max(0, z2), max(0, x2-k1)],
                [1, z3, max(0, z3), max(0, x3-k1)]
            ])
            try:
                A, B, D0, D1 = np.linalg.solve(Phi, [y0, y1, y2, y3])
                return (float(A), float(B), float(D0), float(k0), float(D1), float(k1))
            except:
                return None
        return None
    
    def _inliers_mask(y: np.ndarray, yhat: np.ndarray, rel_eps=REL_EPS, abs_eps=ABS_EPS) -> np.ndarray:
        """Check which points are inliers."""
        tol = np.maximum(abs_eps, rel_eps*np.abs(y))
        return np.abs(y - yhat) <= tol
    
    def _longest_run_length(ks_int: np.ndarray) -> int:
        """Longest consecutive run in integer ks."""
        if len(ks_int) == 0:
            return 0
        ks_sorted = np.sort(ks_int)
        runs = np.split(ks_sorted, np.where(np.diff(ks_sorted) != 1)[0] + 1)
        return max(len(run) for run in runs) if runs else 0
    
    # Main RANSAC trial logic
    idx = np.random.choice(len(x), size=need, replace=False)
    pts = list(zip(x[idx], y[idx]))
    theta = _fit_from_points(family, pts)
    if theta is None:
        return None
    
    yhat = _model_eval(family, theta, x)
    mask = _inliers_mask(y, yhat)
    if mask.sum() < need:
        return None

    Xin = x[mask]; Yin = y[mask]
    
    # Refine by LS on inliers (same logic as ransac_family)
    if family in ("const","line","quad","hinge_centered","hinge2_centered"):
        if family == "const":
            A = (float(np.median(Yin)),)
        elif family == "line":
            M = np.vstack([np.ones_like(Xin), Xin]).T
            A, *_ = np.linalg.lstsq(M, Yin, rcond=None)
            A = tuple(map(float, A))
        elif family == "quad":
            M = np.vstack([np.ones_like(Xin), Xin, Xin**2]).T
            A, *_ = np.linalg.lstsq(M, Yin, rcond=None)
            A = tuple(map(float, A))
        elif family == "hinge_centered":
            k0 = float(theta[-1])
            z = Xin - k0
            Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
            (A1,B1,D1), *_ = np.linalg.lstsq(Phi, Yin, rcond=None)
            A = (float(A1), float(B1), float(D1), float(k0))
        elif family == "hinge2_centered":
            A0,B0,D00,k00,D10,k10 = theta
            z0 = Xin - k00
            Phi = np.vstack([
                np.ones_like(z0), z0,
                np.maximum(0.0, z0),
                np.maximum(0.0, Xin - k10)
            ]).T
            (A1,B1,D01,D11), *_ = np.linalg.lstsq(Phi, Yin, rcond=None)
            A = (float(A1), float(B1), float(D01), float(k00), float(D11), float(k10))
    else:
        A = theta

    yhat = _model_eval(family, A, x)
    mask = _inliers_mask(y, yhat)
    nin = int(mask.sum())
    sm_hits = int(is_sm[mask].sum())
    p = len(A)
    fam_pen = {"const":0, "line":1, "quad":2, "hinge_centered":2, "hinge2_centered":3}[family]

    # Contiguity and slope regularization
    ks_in = np.round(x[mask]).astype(int)
    runlen = _longest_run_length(ks_in)
    contiguity_bonus = np.log1p(runlen)

    if family == "hinge_centered":
        if len(A) == 4:
            _, B_val, D_val, _ = A
            slope_pen = 1e2 * (B_val**2 + D_val**2)
        else:
            slope_pen = 0.0
    elif family == "hinge2_centered":
        if len(A) == 6:
            _, B_val, D0, _, D1, _ = A
            slope_pen = 1.5e2 * (B_val**2 + D0**2 + D1**2)
        else:
            slope_pen = 0.0
    else:
        slope_pen = 0.0

    score = float((w[mask].sum())
                  - LAMBDA_P*p
                  - LAMBDA_F*fam_pen
                  - slope_pen
                  + contiguity_bonus)

    if nin >= p+1:
        resid = y[mask] - yhat[mask]
        sse = float(np.sum(resid**2))
        bic = nin*np.log(sse/nin) + p*np.log(nin) if sse>0 else -np.inf
    else:
        bic = np.inf

    return Curve(family, A, score, nin, sm_hits, bic)

def ransac_family_mp(df: pd.DataFrame, family: str, trials: int=1000, max_workers: int=4):
    """Multiprocessing version of ransac_family."""
    sub: pd.DataFrame = df[np.isfinite(df["k"])].copy()  # type: ignore
    x = sub["k"].to_numpy(dtype="float64")
    y = sub["log_mass"].to_numpy(dtype="float64")
    w = sub["w"].to_numpy(dtype="float64")
    is_sm = sub["id"].astype(str).str.startswith("particle_").to_numpy()

    need = {"const":1, "line":2, "quad":3, "hinge_centered":3, "hinge2_centered":4}[family]

    # Check if we have enough data points
    if len(sub) < need:
        return None, sub

    # Prepare arguments for multiprocessing (include constants)
    constants = (LAMBDA_P, LAMBDA_F, REL_EPS, ABS_EPS)
    trial_args = [(x, y, w, is_sm, family, need, constants) for _ in range(trials)]
    
    best = None
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_ransac_trial, trial_args))
            
        # Find the best result
        for result in results:
            if result is not None and (best is None or result.score > best.score):
                best = result
                
    except Exception as e:
        print(f"Multiprocessing failed: {e}, falling back to single-threaded")
        return ransac_family(df, family, trials)

    return best, sub

# ----------- GENERIC RANSAC FOR ARBITRARY X,Y (e.g., lifetime-mass) -----------
def ransac_family_XY(x, y, w, is_sm, family: str, trials: int=1000):
    need = {"const":1, "line":2, "quad":3, "hinge_centered":3, "hinge2_centered":4}[family]
    N = len(x)
    
    # Check if we have enough data points
    if N < need:
        return None
        
    best = None
    for _ in range(trials):
        idx = np.random.choice(N, size=need, replace=False)
        pts = list(zip(x[idx], y[idx]))
        theta = fit_from_points(family, pts)
        if theta is None:
            continue
        yhat = model_eval(family, theta, x)
        mask = inliers_mask(y, yhat)
        if mask.sum() < need:
            continue
        Xin = x[mask]; Yin = y[mask]
        # refine
        if family in ("const","line","quad","hinge_centered","hinge2_centered"):
            if family == "const":
                A = (float(np.median(Yin)),)
            elif family == "line":
                M = np.vstack([np.ones_like(Xin), Xin]).T
                A, *_ = np.linalg.lstsq(M, Yin, rcond=None)
                A = tuple(map(float, A))
            elif family == "quad":
                M = np.vstack([np.ones_like(Xin), Xin, Xin**2]).T
                A, *_ = np.linalg.lstsq(M, Yin, rcond=None)
                A = tuple(map(float, A))
            elif family == "hinge_centered":
                k0 = float(theta[-1])
                z = Xin - k0
                Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
                (A1,B1,D1), *_ = np.linalg.lstsq(Phi, Yin, rcond=None)
                A = (float(A1), float(B1), float(D1), float(k0))
            elif family == "hinge2_centered":
                A0,B0,D00,k00,D10,k10 = theta
                z0 = Xin - k00
                Phi = np.vstack([
                    np.ones_like(z0), z0,
                    np.maximum(0.0, z0),
                    np.maximum(0.0, Xin - k10)
                ]).T
                (A1,B1,D01,D11), *_ = np.linalg.lstsq(Phi, Yin, rcond=None)
                A = (float(A1), float(B1), float(D01), float(k00), float(D11), float(k10))
        else:
            A = theta
        yhat = model_eval(family, A, x)
        mask = inliers_mask(y, yhat)
        nin = int(mask.sum())
        p = len(A)
        fam_pen = {"const":0, "line":1, "quad":2, "hinge_centered":2, "hinge2_centered":3}[family]
        # contiguity here uses sorted unique X mapped to ints (for stability)
        ks_in = np.round(Xin := x[mask]).astype(int)
        runlen = longest_run_length(ks_in)
        contiguity_bonus = np.log1p(runlen)
        if family == "hinge_centered":
            if len(A) == 4:
                _,B_val,D_val,_ = A
                slope_pen = 1e2 * (B_val**2 + D_val**2)
            else:
                slope_pen = 0.0
        elif family == "hinge2_centered":
            if len(A) == 6:
                _,B_val,D0,_,D1,_ = A
                slope_pen = 1.5e2 * (B_val**2 + D0**2 + D1**2)
            else:
                slope_pen = 0.0
        else:
            slope_pen = 0.0
        score = float((w[mask].sum()) - LAMBDA_P*p - LAMBDA_F*fam_pen - slope_pen + contiguity_bonus)
        # BIC
        if nin >= p+1:
            resid = y[mask] - yhat[mask]
            sse = float(np.sum(resid**2))
            bic = nin*np.log(sse/nin) + p*np.log(nin) if sse>0 else -np.inf
        else:
            bic = np.inf
        cur = Curve(family, A, score, nin, int(is_sm[mask].sum()), bic)
        if (best is None) or (cur.score > best.score):
            best = cur
    return best

def mine_curves(df: pd.DataFrame, families=("line","hinge_centered","quad","const"), max_curves: int=10, trials: int=3000, max_workers: int=4):
    df = df.copy()
    df["covered_weight"] = 0.0
    curves = []
    for j in range(max_curves):
        df["w_eff"] = df["w"] * (1.0 - np.clip(df["covered_weight"], 0.0, 0.9))
        best_overall = None
        best_sub = None
        for fam in families:
            candidate, sub = ransac_family_mp(df.assign(w=df["w_eff"]), fam, trials=trials, max_workers=max_workers)
            if candidate is None:
                continue
            if (best_overall is None) or (candidate.score > best_overall.score):
                best_overall, best_sub = candidate, sub
        if best_overall is None:
            break

        # mark coverage
        x = best_sub["k"].to_numpy(dtype="float64")
        y = best_sub["log_mass"].to_numpy(dtype="float64")
        yhat = model_eval(best_overall.family, best_overall.theta, x)
        mask = inliers_mask(y, yhat)
        covered_ids = best_sub.loc[mask, "id"]
        df.loc[df["id"].isin(covered_ids), "covered_weight"] += 0.75

        curves.append((best_overall, covered_ids.tolist()))
        print(f"[{j+1}] {best_overall.family:>15}  score={best_overall.score:.2f}  inliers={best_overall.n_inliers}  SM={best_overall.sm_hits}  BIC={best_overall.bic:.1f}  theta={best_overall.theta}")
    return curves

def run_mass_k_mining_per_sector(df: pd.DataFrame, families, max_curves, trials, out_dir: Path,
                                 sectors: list[str], sample_size: int | None = None, args=None) -> list[tuple]:
    all_curves = []
    for sec in sectors:
        sub = df[(df["sector"] == sec) & np.isfinite(df["k"]) & np.isfinite(df["log_mass"])].copy()
        if sub.empty:
            print(f"[mass-k] skip sector={sec}: empty after filters"); continue
        
        # Apply sampling if specified and data is large enough
        if sample_size and len(sub) > sample_size:
            sub = sub.sample(n=sample_size, random_state=42).copy()
            print(f"[mass-k] sector={sec}: rows={len(sub)} (sampled from larger dataset)")
        else:
            print(f"[mass-k] sector={sec}: rows={len(sub)}")

        max_workers = getattr(args, 'max_workers', 4) if args else 4
        curves = mine_curves(sub, families=families, max_curves=max_curves, trials=trials, max_workers=max_workers)  # type: ignore
        # Tag sector into curves and stash for later report writing
        tagged = []
        for c, inliers in curves:
            tagged.append((sec, c, inliers))
        all_curves.extend(tagged)
    return all_curves

# ----------- LIFETIME-MASS CURVE MINING -----------
def mine_curves_lifetime_mass(df: pd.DataFrame, families=("line","hinge_centered","quad","const"), max_curves: int=10, trials: int=3000):
    dg = df.copy()
    dg = dg[np.isfinite(dg["log_mass"]) & np.isfinite(dg["log_tau"])].copy()
    x = dg["log_mass" ].to_numpy(float)  # type: ignore
    y = dg["log_tau"  ].to_numpy(float)  # type: ignore
    w = dg["w"        ].to_numpy(float)  # type: ignore
    is_sm = dg["id"].astype(str).str.startswith("particle_").to_numpy()  # type: ignore
    ids = dg["id"].astype(str).to_numpy()  # type: ignore
    covered = np.zeros(len(dg), dtype=float)
    curves = []
    for j in range(max_curves):
        w_eff = w * (1.0 - np.clip(covered, 0.0, 0.9))
        best = None
        best_mask = None
        for fam in families:
            cand = ransac_family_XY(x, y, w_eff, is_sm, fam, trials=trials)
            if cand is None:
                continue
            yhat = model_eval(cand.family, cand.theta, x)
            mask = inliers_mask(y, yhat)
            if (best is None) or (cand.score > best.score):
                best = cand
                best_mask = mask
        if best is None:
            break
        curves.append((best, ids[best_mask].tolist(), x[best_mask].copy()))
        covered[best_mask] += 0.75
        print(f"[LM {j+1}] {best.family:>15} score={best.score:.2f} inliers={best.n_inliers} SM={best.sm_hits} BIC={best.bic:.1f} theta={best.theta}")
    return curves

# ------------------------- PRETTY EXPRESSIONS -------------------

def pretty_expr_centered(curve: Curve) -> str:
    fam, th = curve.family, curve.theta
    if fam=="const":
        (A,) = th
        return f"log10(m) = {A:.5f}"
    if fam=="line":
        A,B = th
        return f"log10(m) = {A:.5f} + {B:.6f}·k"
    if fam=="hinge_centered":
        A,B,D,k0 = th
        return f"log10(m) = {A:.5f} + {B:.6f}·(k−{k0:.0f}) + {D:.6f}·max(0, k−{k0:.0f})"
    if fam=="hinge2_centered":
        A,B,D0,k0,D1,k1 = th
        return (f"log10(m) = {A:.5f} + {B:.6f}·(k−{k0:.0f}) + "
                f"{D0:.6f}·max(0, k−{k0:.0f}) + {D1:.6f}·max(0, k−{k1:.0f})")
    if fam=="quad":
        A,B,C = th
        return f"log10(m) = {A:.5f} + {B:.6f}·k + {C:.6f}·k^2"
    return f"{fam} {th}"

def pretty_expr_lm(curve: Curve) -> str:
    fam, th = curve.family, curve.theta
    if fam == "const":
        (A,) = th
        return f"log10(τ) = {A:.5f}"
    if fam == "line":
        A, B = th
        return f"log10(τ) = {A:.5f} + {B:.6f}·log10(m)"
    if fam == "quad":
        A, B, C = th
        return f"log10(τ) = {A:.5f} + {B:.6f}·log10(m) + {C:.6f}·(log10(m))^2"
    if fam == "hinge_centered":
        A, B, D, x0 = th
        return f"log10(τ) = {A:.5f} + {B:.6f}·(log10(m)−{x0:.2f}) + {D:.6f}·max(0, log10(m)−{x0:.2f})"
    return f"{fam} {th}"

# ------------------------- PHYSICS INTERPRETATION LAYER -------------------------

def interpret_curve_physics(curve: Curve, df: pd.DataFrame, inlier_ids: list) -> dict:
    """Automatically label each discovered curve with physics insights."""
    inliers = df[df["id"].isin(inlier_ids)].copy()

    # 1. STRUCTURAL CLASSIFICATION
    if curve.family == "hinge_centered":
        A, B, D, k0 = curve.theta
        k0_mass = 10**A
        if k0_mass < 100:
            structural_type = "low_energy_phase_transition"
        elif k0_mass < 1000:
            structural_type = "electroweak_scale"
        elif k0_mass < 100000:
            structural_type = "beyond_sm_scale"
        else:
            structural_type = "ultra_high_energy"

        if abs(B) < 1e-4 and abs(D) < 1e-4:
            slope_character = "ultra_stable_plateau"
        elif abs(B) < 1e-3 and abs(D) < 1e-3:
            slope_character = "stable_band"
        else:
            slope_character = "evolving_band"

    elif curve.family == "hinge2_centered":
        A,B,D0,k0,D1,k1 = curve.theta
        k0_mass = 10**A
        structural_type = "multi_phase_transition"
        slope_character = "piecewise_evolving"

    elif curve.family == "line":
        A, B = curve.theta
        if abs(B) < 1e-4:
            structural_type = "mass_independent_constant"; slope_character = "ultra_stable"
        elif abs(B) < 1e-3:
            structural_type = "slow_mass_evolution"; slope_character = "quasi_stable"
        else:
            structural_type = "mass_dependent_evolution"; slope_character = "evolving"
    elif curve.family == "quad":
        structural_type = "curved_evolution"; slope_character = "accelerating"
    else:
        structural_type = "constant_regime"; slope_character = "stable"

    # 2. OSCILLATORY ANALYSIS (quick FFT)
    x = inliers["k"].to_numpy(dtype="float64")  # type: ignore
    y = inliers["log_mass"].to_numpy(dtype="float64")  # type: ignore
    yhat = model_eval(curve.family, curve.theta, x)
    residuals = y - yhat
    oscillatory = False; period_estimate = np.nan
    if len(residuals) >= 16:
        R = np.fft.rfft(residuals - residuals.mean())
        P = np.abs(R)**2; P[0] = 0.0
        if len(P) > 1:
            peak_idx = np.argmax(P[1:]) + 1
            if peak_idx > 0:
                oscillatory = (P[peak_idx] > 2.0*np.mean(P[1:]))
                period_estimate = len(residuals)/peak_idx if oscillatory else np.nan

    # 3. Enrichment
    sm_inliers = inliers[inliers["id"].str.startswith("particle_")]  # type: ignore
    sm_enrichment = len(sm_inliers) / len(inliers) if len(inliers) > 0 else 0.0
    stable_inliers = inliers[inliers["classification_color"] == "Green"]
    stability_enrichment = len(stable_inliers) / len(inliers) if len(inliers) > 0 else 0.0

    # 4. Significance score (heuristic)
    significance_score = 0.0
    significance_score += {"hinge2_centered":3.5, "hinge_centered":3.0, "line":2.0, "quad":1.5}.get(curve.family,1.0)
    if sm_enrichment > 0.1: significance_score += 2.0
    if sm_enrichment > 0.5: significance_score += 3.0
    if stability_enrichment > 0.3: significance_score += 1.5
    if oscillatory: significance_score += 2.0
    if curve.n_inliers > 100: significance_score += 1.0
    if curve.n_inliers > 500: significance_score += 2.0

    # 5. Alignment of hinge(s) to multiples of 233 (even‑ladder harmonic)
    def _align233(val: float) -> float:
        r = np.mod(val, 233.0)
        return float(min(r, 233.0 - r))
    align_info = {}
    if curve.family == "hinge_centered":
        _,_,_,k0 = curve.theta
        align_info["k0_mod233_dist"] = _align233(float(k0))
    elif curve.family == "hinge2_centered":
        _,_,_,k0,_,k1 = curve.theta
        align_info["k0_mod233_dist"] = _align233(float(k0))
        align_info["k1_mod233_dist"] = _align233(float(k1))

    return {
        "structural_type": structural_type,
        "slope_character": slope_character,
        "oscillatory": oscillatory,
        "period_estimate": period_estimate,
        "sm_enrichment": sm_enrichment,
        "stability_enrichment": stability_enrichment,
        "significance_score": significance_score,
        "align233": align_info
    }

# ------------------------- OSCILLATION (STRICT) -----------------

def fit_best_trend(x: np.ndarray, y: np.ndarray):
    candidates = []
    # const
    A0 = np.median(y)
    yhat = np.full_like(y, A0)
    p = 1
    sse = np.sum((y-yhat)**2)
    bic = len(y)*np.log(sse/len(y)) + p*np.log(len(y))
    candidates.append(("const", (float(A0),), yhat, bic))
    # line
    try:
        M = np.vstack([np.ones_like(x), x]).T
        (A,B), *_ = np.linalg.lstsq(M, y, rcond=None)
        yhat = A + B*x
        p = 2
        sse = np.sum((y-yhat)**2)
        bic = len(y)*np.log(sse/len(y)) + p*np.log(len(y))
        candidates.append(("line", (float(A),float(B)), yhat, bic))
    except Exception:
        pass
    # quad
    try:
        M = np.vstack([np.ones_like(x), x, x**2]).T
        (A,B,C), *_ = np.linalg.lstsq(M, y, rcond=None)
        yhat = A + B*x + C*x**2
        p = 3
        sse = np.sum((y-yhat)**2)
        bic = len(y)*np.log(sse/len(y)) + p*np.log(len(y))
        candidates.append(("quad", (float(A),float(B),float(C)), yhat, bic))
    except Exception:
        pass
    # hinge_centered (quick single-pass estimate via points + LS)
    theta = fit_from_points("hinge_centered", list(zip(x, y)))
    if theta is not None:
        A,B,D,k0 = theta
        z = x - k0
        yhat = A + B*z + D*np.maximum(0.0, z)
        p = 4
        sse = np.sum((y-yhat)**2)
        bic = len(y)*np.log(sse/len(y)) + p*np.log(len(y))
        candidates.append(("hinge_centered", (float(A),float(B),float(D),float(k0)), yhat, bic))
    if not candidates:
        return ("const", (float(np.median(y)),), np.full_like(y, np.median(y)), np.inf)
    return min(candidates, key=lambda t: t[3])

def ar1_whiten(r: np.ndarray) -> np.ndarray:
    r = np.asarray(r, float)
    if len(r) < 3:
        return r.copy()
    r0 = np.dot(r, r) / len(r)
    r1 = np.dot(r[1:], r[:-1]) / (len(r)-1)
    phi = np.clip(r1 / r0, -0.99, 0.99)
    eps = r[1:] - phi*r[:-1]
    return eps

def block_permutation(series: np.ndarray, block: int=32, nperm: int=400) -> np.ndarray:
    print(f"🔄 Running {nperm} block permutations on series of length {len(series)}...")
    rng = np.random.default_rng(0)
    N = len(series)
    blocks = []
    for i in range(0, N, block):
        blocks.append(series[i:min(N, i+block)])
    print(f"📦 Created {len(blocks)} blocks")
    peaks = []
    for i in range(nperm):
        if i % max(1, nperm//10) == 0:  # Print progress every 10%
            print(f"🔄 Permutation {i+1}/{nperm}")
        order = rng.permutation(len(blocks))
        cat = np.concatenate([blocks[j] for j in order])
        R = np.fft.rfft(cat - cat.mean())
        P = np.abs(R)**2
        P[0] = 0.0
        peaks.append(P.max())
    print(f"✅ Completed {nperm} permutations")
    return np.array(peaks)

def oscillation_test_strict(df: pd.DataFrame, top_segments: int=3, out_dir: Path | None=None, nperm: int=400):
    print(f"🔍 Starting oscillation test with {nperm} permutations...")
    seg_counts = (
        df.groupby(["branch_inferred","c_state"]).size().sort_values(ascending=False)  # type: ignore
    )
    segments = list(seg_counts.index[:top_segments])  # type: ignore
    print(f"📊 Found {len(segments)} segments to test")

    osc_results = []
    for i, (br, cs) in enumerate(segments):  # type: ignore
        print(f"🔄 Testing segment {i+1}/{len(segments)}: {br}/{cs}")
        sub = df[(df["branch_inferred"]==br) & (df["c_state"]==cs) & (df["k_is_int"])].copy()
        if len(sub) < 32:
            continue
        x = sub["k"].to_numpy(dtype="float64")  # type: ignore
        y = sub["log_mass"].to_numpy(dtype="float64")  # type: ignore

        family, theta, yhat, _ = fit_best_trend(x, y)
        r = y - yhat
        eps = ar1_whiten(r)
        R = np.fft.rfft(eps - eps.mean())
        P = np.abs(R)**2
        P[0] = 0.0
        freqs = np.fft.rfftfreq(len(eps), d=1.0)
        i = np.argmax(P)
        f_peak = freqs[i]
        P_peak = P[i]
        Period = 1.0/f_peak if f_peak>0 else np.inf

        null_peaks = block_permutation(eps, block=32, nperm=nperm)
        z = (P_peak - null_peaks.mean()) / (null_peaks.std() + 1e-12)

        osc_results.append({
            "branch": br,
            "c_state": cs,
            "trend_family": family,
            "trend_theta": tuple(map(float, theta)) if isinstance(theta, (tuple,list,np.ndarray)) else theta,
            "period_steps": float(Period),
            "z_score": float(z),
            "n_points": int(len(sub)),
        })

        if out_dir is not None:
            res_csv = out_dir / f"residuals_{br}_{cs}.csv"
            _write_csv(res_csv, [{"k": float(xx), "residual": float(rr)} for xx,rr in zip(x, r)], ["k","residual"])
            plt.figure(figsize=(10, 6))
            plt.plot(x, r, marker='.', linestyle='none', ms=3)
            plt.title(f"Residuals (branch={br}, c={cs})   P≈{Period:.2f} steps, z≈{z:.2f}")
            plt.xlabel("k"); plt.ylabel("log10(m) residual")
            plt.grid(True)
            plt.savefig(out_dir / f"residuals_{br}_{cs}.png", dpi=180, bbox_inches='tight')
            plt.close()

    return osc_results

# -------- Lifetime–Mass OSCILLATION (STRICT) --------

def oscillation_test_strict_lm(df: pd.DataFrame, top_segments: int = 3, out_dir: Path | None = None, nperm: int=400):
    base = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
    if base.empty:
        return []
    seg_counts = (
        base.groupby(["branch_inferred", "c_state"]).size().sort_values(ascending=False)  # type: ignore
    )
    segments = list(seg_counts.index[:top_segments])  # type: ignore

    results = []
    for br, cs in segments:  # type: ignore
        sub = base[(base["branch_inferred"] == br) & (base["c_state"] == cs)].copy()
        if len(sub) < 32:
            continue
        sub = sub.sort_values("log_mass")  # type: ignore
        x = sub["log_mass"].to_numpy(dtype="float64")
        y = sub["log_tau"].to_numpy(dtype="float64")

        family, theta, yhat, _ = fit_best_trend(x, y)
        r = y - yhat
        eps = ar1_whiten(r)

        R = np.fft.rfft(eps - eps.mean())
        P = np.abs(R) ** 2
        P[0] = 0.0
        freqs = np.fft.rfftfreq(len(eps), d=1.0)  # treat sorted-by-x as unit spacing
        i = np.argmax(P)
        f_peak = freqs[i]
        P_peak = P[i]
        Period = 1.0 / f_peak if f_peak > 0 else np.inf

        null_peaks = block_permutation(eps, block=32, nperm=nperm)
        z = (P_peak - null_peaks.mean()) / (null_peaks.std() + 1e-12)

        results.append({
            "branch": br,
            "c_state": cs,
            "trend_family": family,
            "trend_theta": tuple(map(float, theta)) if isinstance(theta, (tuple, list, np.ndarray)) else theta,
            "period_index_units": float(Period),
            "z_score": float(z),
            "n_points": int(len(sub)),
        })

        if out_dir is not None:
            res_csv = out_dir / f"lm_residuals_{br}_{cs}.csv"
            _write_csv(res_csv, [{"log_mass": float(xx), "residual": float(rr)} for xx,rr in zip(x, r)], ["log_mass","residual"])
            plt.figure(figsize=(10, 6))
            plt.plot(x, r, marker='.', linestyle='none', ms=3)
            plt.title(f"Residuals LM (branch={br}, c={cs})   P≈{Period:.2f} idx, z≈{z:.2f}")
            plt.xlabel("log10(mass [MeV])")
            plt.ylabel("log10(τ) residual")
            plt.grid(True)
            plt.savefig(out_dir / f"lm_residuals_{br}_{cs}.png", dpi=180, bbox_inches='tight')
            plt.close()

    return results

# -------- Lifetime–Mass GLOBAL LAW (power / broken-power) --------

def fit_lifetime_mass_global(df: pd.DataFrame):
    dg = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
    if len(dg) < 3:
        return {}
    x = dg["log_mass"].to_numpy(float)  # type: ignore
    y = dg["log_tau"].to_numpy(float)  # type: ignore

    # linear (power-law) fit
    M1 = np.vstack([np.ones_like(x), x]).T
    (A1, B1), *_ = np.linalg.lstsq(M1, y, rcond=None)
    yhat1 = A1 + B1 * x
    sse1 = float(np.sum((y - yhat1) ** 2))
    p1 = 2
    bic1 = len(x) * np.log(sse1 / len(x)) + p1 * np.log(len(x)) if sse1 > 0 else -np.inf
    sst = float(np.sum((y - y.mean()) ** 2))
    r2_1 = 1.0 - (sse1 / sst if sst > 0 else 0.0)

    # hinge (broken power-law) fit
    print(f"🔍 Fitting hinge model on {len(x)} points...")
    theta0 = fit_from_points("hinge_centered", list(zip(x, y)))
    print(f"✅ Hinge fit completed")
    if theta0 is not None:
        A2, B2, D2, x0 = theta0
        z = x - x0
        Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
        (A2f, B2f, D2f), *_ = np.linalg.lstsq(Phi, y, rcond=None)
        theta2 = (float(A2f), float(B2f), float(D2f), float(x0))
        yhat2 = theta2[0] + theta2[1] * (x - x0) + theta2[2] * np.maximum(0.0, x - x0)
        sse2 = float(np.sum((y - yhat2) ** 2))
        p2 = 4
        bic2 = len(x) * np.log(sse2 / len(x)) + p2 * np.log(len(x)) if sse2 > 0 else -np.inf
        r2_2 = 1.0 - (sse2 / sst if sst > 0 else 0.0)
    else:
        theta2 = None
        bic2 = np.inf
        r2_2 = -np.inf

    best = {
        "power_law": {
            "family": "line",
            "theta": (float(A1), float(B1)),
            "bic": float(bic1),
            "r2": float(r2_1),
            "expression": f"log10(τ) = {A1:.5f} + {B1:.6f}·log10(m)",
        },
    }
    if theta2 is not None:
        best["broken_power_law"] = {
            "family": "hinge_centered",
            "theta": tuple(map(float, theta2)),
            "bic": float(bic2),
            "r2": float(r2_2),
            "expression": pretty_expr_lm(Curve("hinge_centered", theta2, 0.0, 0, 0, 0.0)),
        }

    winner_key = min(best.keys(), key=lambda k: best[k]["bic"])
    best["winner"] = winner_key  # type: ignore
    return best

def compare_lifetime_meta_models(df: pd.DataFrame) -> dict:
    """Compare pooled vs stratified lifetime–mass models using BIC and simple CV."""
    base = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
    if base.empty or "sector" not in base.columns:
        return {}

    # Design: pool
    X_pool = np.vstack([np.ones(len(base)), base["log_mass"].values]).T  # type: ignore
    y = base["log_tau"].values  # type: ignore
    th_pool, *_ = np.linalg.lstsq(X_pool, y, rcond=None)  # type: ignore
    yhat_pool = X_pool @ th_pool
    bic_pool = _bic(y, yhat_pool, X_pool.shape[1])

    # Design: sector intercepts (fixed effects)
    secs = pd.Categorical(base["sector"])
    S = pd.get_dummies(secs, drop_first=True).values  # K-1 contrasts
    X_si = np.hstack([np.ones((len(base),1)), base[["log_mass"]].values, S])  # type: ignore
    th_si, *_ = np.linalg.lstsq(X_si, y, rcond=None)  # type: ignore
    yhat_si = X_si @ th_si
    bic_si = _bic(y, yhat_si, X_si.shape[1])

    # Design: sector intercepts + sector*log_mass interactions
    X_six = np.hstack([np.ones((len(base),1)), base[["log_mass"]].values, S, S*base[["log_mass"]].values])  # type: ignore
    th_six, *_ = np.linalg.lstsq(X_six, y, rcond=None)  # type: ignore
    yhat_six = X_six @ th_six
    bic_six = _bic(y, yhat_six, X_six.shape[1])

    # Simple k-fold CV (k=5) on pooled vs interactions
    k = 5
    idx = np.arange(len(base))
    rng = np.random.default_rng(1)
    rng.shuffle(idx)
    folds = np.array_split(idx, k)
    def _cv_rmse(X):
        rmses = []
        for f in folds:
            tr = np.setdiff1d(idx, f, assume_unique=False)
            th, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)  # type: ignore
            yhat = X[f] @ th
            rmses.append(np.sqrt(np.mean((y[f]-yhat)**2)))
        return float(np.mean(rmses))
    cv_pool = _cv_rmse(X_pool)
    cv_six  = _cv_rmse(X_six)

    return {
        "bic_pool": bic_pool, "bic_sector_intercept": bic_si, "bic_sector_interact": bic_six,
        "cv_rmse_pool": cv_pool, "cv_rmse_sector_interact": cv_six,
        "winner": min([("pool",bic_pool), ("sector_interact",bic_six)], key=lambda t: t[1])[0]
    }

def compare_massk_linear_meta(df: pd.DataFrame) -> dict:
    """Coarse diagnostic: pooled linear mass–k vs sector-interact linear mass–k."""
    base = df[np.isfinite(df["k"]) & np.isfinite(df["log_mass"])]
    if base.empty or "sector" not in base.columns:
        return {}
    X_pool = np.vstack([np.ones(len(base)), base["k"].values]).T  # type: ignore
    y = base["log_mass"].values  # type: ignore
    th_pool, *_ = np.linalg.lstsq(X_pool, y, rcond=None)  # type: ignore
    yhat_pool = X_pool @ th_pool
    bic_pool = _bic(y, yhat_pool, X_pool.shape[1])

    secs = pd.Categorical(base["sector"])
    S = pd.get_dummies(secs, drop_first=True).values
    X_six = np.hstack([np.ones((len(base),1)), base[["k"]].values, S, S*base[["k"]].values])  # type: ignore
    th_six, *_ = np.linalg.lstsq(X_six, y, rcond=None)  # type: ignore
    yhat_six = X_six @ th_six
    bic_six = _bic(y, yhat_six, X_six.shape[1])

    return {"bic_pool_linear": float(bic_pool), "bic_sector_interact_linear": float(bic_six),
            "winner": "pool" if bic_pool < bic_six else "sector_interact"}

# -------- Group-wise POWER-LAW slopes (diagnostic) --------

def group_power_law_summary(df: pd.DataFrame, min_n: int = 24):
    out = []
    base = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
    if base.empty:
        return out
    for (br, cs), sub in base.groupby(["branch_inferred", "c_state"]):  # type: ignore
        if len(sub) < min_n:
            continue
        x = sub["log_mass"].to_numpy(float)  # type: ignore
        y = sub["log_tau"].to_numpy(float)  # type: ignore
        M = np.vstack([np.ones_like(x), x]).T
        (A, B), *_ = np.linalg.lstsq(M, y, rcond=None)
        yhat = A + B * x
        sse = float(np.sum((y - yhat) ** 2))
        sst = float(np.sum((y - y.mean()) ** 2))
        r2 = 1.0 - (sse / sst if sst > 0 else 0.0)
        out.append({
            "branch": br,
            "c_state": cs,
            "beta": float(B),
            "intercept": float(A),
            "r2": float(r2),
            "n": int(len(sub)),
        })
    out.sort(key=lambda d: -abs(d["beta"]))
    return out

# -------- Optional: per-curve CV, per-curve oscillation, bootstrap CIs --------

def _refit_fixed_breaks(family: str, theta: tuple, x: np.ndarray, y: np.ndarray) -> tuple:
    """Refit coefficients holding breakpoints fixed (for CV)."""
    if family == "const":
        return (float(np.median(y)),)
    if family == "line":
        M = np.vstack([np.ones_like(x), x]).T
        th, *_ = np.linalg.lstsq(M, y, rcond=None)
        return (float(th[0]), float(th[1]))
    if family == "quad":
        M = np.vstack([np.ones_like(x), x, x**2]).T
        th, *_ = np.linalg.lstsq(M, y, rcond=None)
        return (float(th[0]), float(th[1]), float(th[2]))
    if family == "hinge_centered":
        A,B,D,k0 = theta
        z = x - float(k0)
        Phi = np.vstack([np.ones_like(z), z, np.maximum(0.0, z)]).T
        th, *_ = np.linalg.lstsq(Phi, y, rcond=None)
        return (float(th[0]), float(th[1]), float(th[2]), float(k0))
    if family == "hinge2_centered":
        A,B,D0,k0,D1,k1 = theta
        z0 = x - float(k0)
        Phi = np.vstack([
            np.ones_like(z0), z0,
            np.maximum(0.0, z0),
            np.maximum(0.0, x - float(k1))
        ]).T
        th, *_ = np.linalg.lstsq(Phi, y, rcond=None)
        return (float(th[0]), float(th[1]), float(th[2]), float(k0), float(th[3]), float(k1))
    return theta

def cv_score_curve(df: pd.DataFrame, curve: Curve, inlier_ids: list, frac: float=0.2, nsplits: int=3) -> float:
    """Return average RMSE over nsplits random holdouts (fixed breakpoints)."""
    sub = df[df["id"].isin(inlier_ids)].copy()
    x = sub["k"].to_numpy(float) if "k" in sub else None  # type: ignore
    y = sub["log_mass"].to_numpy(float)  # type: ignore
    if x is None or len(x) < 8:
        return float("nan")
    rng = np.random.default_rng(0)
    rmses = []
    for _ in range(nsplits):
        m = len(sub)
        test_mask = np.zeros(m, dtype=bool)
        test_idx = rng.choice(m, size=max(1, int(frac*m)), replace=False)
        test_mask[test_idx] = True
        xtr, ytr = x[~test_mask], y[~test_mask]
        xte, yte = x[test_mask], y[test_mask]
        th = _refit_fixed_breaks(curve.family, curve.theta, xtr, ytr)
        yhat = model_eval(curve.family, th, xte)
        rmse = float(np.sqrt(np.mean((yte - yhat)**2))) if len(yte)>0 else float("nan")
        rmses.append(rmse)
    return float(np.nanmean(rmses)) if len(rmses)>0 else float("nan")

def sector_cv_sigma_massk(df: pd.DataFrame, curves_json_path: Path) -> dict:
    """
    Compute per-sector sigma (std of CV RMSE in log space) from curves.json entries that have cv_rmse.
    Returns { sector: { 'sigma_logm': float, 'n_curves': int } } and writes to analytics_windows.json.
    """
    if not curves_json_path.exists():
        return {}
    cj = json.loads(curves_json_path.read_text())
    buckets: Dict[str, List[float]] = {}
    for c in cj:
        sec = c.get("sector") or "unknown"
        rmse = c.get("cv_rmse", None)
        fam  = c.get("family","")
        # Only use fermion sector by default; others optional
        if rmse is not None and isinstance(rmse, (int,float)) and np.isfinite(rmse):
            buckets.setdefault(sec, []).append(float(rmse))
    out = {}
    for sec, arr in buckets.items():
        if len(arr) == 0: 
            continue
        # robust: median absolute deviation approx -> fallback to std
        sigma = float(np.median(arr)) if len(arr) < 5 else float(np.std(arr, ddof=1))
        out[sec] = {"sigma_logm": sigma, "n_curves": len(arr)}
    return out

def sector_cv_sigma_lm(lm_curves_json_path: Path, df: pd.DataFrame) -> dict:
    """
    Compute per-sector sigma for log_tau vs log_mass from lm_curves.json by refitting each LM curve's family
    on its inliers and doing a quick 3-fold CV over those inliers.
    """
    if not lm_curves_json_path.exists():
        return {}
    lm = json.loads(lm_curves_json_path.read_text())
    out = {}
    for c in lm:
        sec = c.get("sector") or "unknown"
        ids = c.get("inlier_ids", [])
        fam = c.get("family")
        th  = tuple(c.get("theta", []))
        sub = df[df["id"].isin(ids) & np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])]  # type: ignore
        if len(sub) < 8:
            continue
        x = sub["log_mass"].to_numpy(float)  # type: ignore
        y = sub["log_tau"].to_numpy(float)   # type: ignore
        # quick 3-fold CV using fixed family; breakpoints fixed if hinge
        idx = np.arange(len(sub))
        rng = np.random.default_rng(2)
        rng.shuffle(idx)
        folds = np.array_split(idx, 3)
        rmses = []
        for f in folds:
            tr = np.setdiff1d(idx, f, assume_unique=False)
            th_refit = _refit_fixed_breaks(fam, th, x[tr], y[tr])
            yhat = model_eval(fam, th_refit, x[f])
            rmses.append(np.sqrt(np.mean((y[f]-yhat)**2)))
        rmse = float(np.mean(rmses))
        bucket = out.setdefault(sec, {"vals": []})
        bucket["vals"].append(rmse)
    # reduce
    for sec, rec in list(out.items()):
        vals = rec["vals"]
        if not vals: 
            out.pop(sec); 
            continue
        sigma = float(np.median(vals)) if len(vals) < 5 else float(np.std(vals, ddof=1))
        out[sec] = {"sigma_logtau": sigma, "n_curves": len(vals)}
    return out

def per_curve_oscillation(df: pd.DataFrame, curve: Curve, inlier_ids: list, nperm: int=400, out_dir: Optional[Path]=None, tag: str="") -> Dict[str, float]:
    """Strict oscillation on residuals for a single curve (k–log m)."""
    sub = df[df["id"].isin(inlier_ids)].copy()
    if len(sub) < 32:
        return {}
    sub = sub.sort_values("k")  # type: ignore
    x = sub["k"].to_numpy(float)  # type: ignore
    y = sub["log_mass"].to_numpy(float)  # type: ignore
    yhat = model_eval(curve.family, curve.theta, x)
    r = y - yhat
    eps = ar1_whiten(r)

    R = np.fft.rfft(eps - eps.mean())
    P = np.abs(R)**2; P[0] = 0.0
    freqs = np.fft.rfftfreq(len(eps), d=1.0)
    i = np.argmax(P); f_peak = freqs[i]
    Period = 1.0/f_peak if f_peak>0 else np.inf
    null_peaks = block_permutation(eps, block=32, nperm=nperm)
    z = (P[i] - null_peaks.mean()) / (null_peaks.std() + 1e-12)

    if out_dir is not None:
        plt.figure(figsize=(10,6))
        plt.plot(x, r, '.', ms=3)
        plt.title(f"Residuals (curve={tag})  P≈{Period:.2f} steps, z≈{z:.2f}")
        plt.xlabel("k"); plt.ylabel("log10(m) residual"); plt.grid(True)
        plt.savefig(out_dir / f"residuals_curve_{tag}.png", dpi=180, bbox_inches='tight'); plt.close()
    return {"period_steps": float(Period), "z_score": float(z), "n_points": int(len(sub))}

def bootstrap_curve_ci(df: pd.DataFrame, curve: Curve, inlier_ids: list, n_boot: int=0, out_dir: Optional[Path]=None, tag: str=""):
    """Bootstrap hinge(s) for uncertainty (re-fit hinges each bootstrap via LS on quantiles)."""
    if n_boot <= 0:
        return {}
    if curve.family not in ("hinge_centered", "hinge2_centered"):
        return {}

    sub = df[df["id"].isin(inlier_ids)].copy()
    x = sub["k"].to_numpy(float)  # type: ignore
    y = sub["log_mass"].to_numpy(float)  # type: ignore
    rng = np.random.default_rng(123)
    k0s, k1s = [], []

    for _ in range(n_boot):
        idx = rng.integers(0, len(x), size=len(x))
        xs, ys = x[idx], y[idx]
        th = fit_from_points_bootstrap(curve.family, list(zip(xs, ys)))
        if th is None:
            continue
        if curve.family == "hinge_centered":
            _,_,_,k0 = th
            k0s.append(float(k0))
        else:
            _,_,_,k0,_,k1 = th
            k0s.append(float(k0)); k1s.append(float(k1))

    out = {}
    if k0s:
        out["k0_mean"] = float(np.mean(k0s)); out["k0_std"] = float(np.std(k0s))
        out["k0_ci5"] = float(np.percentile(k0s, 5)); out["k0_ci95"] = float(np.percentile(k0s, 95))
    if k1s:
        out["k1_mean"] = float(np.mean(k1s)); out["k1_std"] = float(np.std(k1s))
        out["k1_ci5"] = float(np.percentile(k1s, 5)); out["k1_ci95"] = float(np.percentile(k1s, 95))

    if out_dir is not None and k0s:
        plt.figure(figsize=(8,4))
        plt.hist(k0s, bins=40, alpha=0.7)
        plt.title(f"Bootstrap k0 (curve={tag})")
        plt.xlabel("k0"); plt.ylabel("count")
        plt.grid(True); plt.savefig(out_dir / f"bootstrap_k0_{tag}.png", dpi=160, bbox_inches='tight'); plt.close()
        if k1s:
            plt.figure(figsize=(8,4))
            plt.hist(k1s, bins=40, alpha=0.7)
            plt.title(f"Bootstrap k1 (curve={tag})")
            plt.xlabel("k1"); plt.ylabel("count")
            plt.grid(True); plt.savefig(out_dir / f"bootstrap_k1_{tag}.png", dpi=160, bbox_inches='tight'); plt.close()
    return out

# ------------------------- PLOTTING ------------------------------

def plot_with_inlier_support(df_on_ladder: pd.DataFrame, curves, out_png: Path):
    x = df_on_ladder["k"].to_numpy(float)
    y = df_on_ladder["log_mass"].to_numpy(float)

    # Save scatter data
    pts_csv = out_png.with_suffix("")
    pts_points = out_png.parent / "points_k_logm.csv"
    _write_csv(pts_points, [{"k": float(k), "log_mass": float(v)} for k, v in zip(x, y)], ["k","log_mass"]) 
    _append_md(out_png.parent / "top_curves_overlay.md", [
        "# Top curves overlay (mass vs k)",
        f"- PNG: {out_png.name}",
        f"- Points CSV: {pts_points.name}",
        "- Curves CSV: curves_k_logm.csv"
    ])

    # Save curve lines data
    curve_lines = []
    for idx, (c, inlier_ids) in enumerate(curves[:3], start=1):
        sub = df_on_ladder[df_on_ladder["id"].isin(inlier_ids)]
        if sub.empty:
            continue
        xmin = float(sub["k"].min())
        xmax = float(sub["k"].max())
        xs = np.linspace(xmin, xmax, 400)
        ys = model_eval(c.family, c.theta, xs)
        for xi, yi in zip(xs, ys):
            curve_lines.append({"rank": idx, "family": c.family, "expr": pretty_expr_centered(c), "k": float(xi), "log_mass_fit": float(yi)})
    curves_csv = out_png.parent / "curves_k_logm.csv"
    _write_csv(curves_csv, curve_lines, ["rank","family","expr","k","log_mass_fit"])

    # Plot
    plt.figure(figsize=(12, 8))
    plt.scatter(x, y, s=6)
    for c, inlier_ids in curves[:3]:
        sub = df_on_ladder[df_on_ladder["id"].isin(inlier_ids)]
        if sub.empty:
            continue
        xmin = float(sub["k"].min()); xmax = float(sub["k"].max())
        xs = np.linspace(xmin, xmax, 400)
        ys = model_eval(c.family, c.theta, xs)
        label = f"{c.family}: {pretty_expr_centered(c)}"
        plt.plot(xs, ys, linewidth=2, label=label)
    plt.title("log10(mass) vs k with top curves (restricted to inlier span)")
    plt.xlabel("k (even-ladder index)"); plt.ylabel("log10(mass [MeV])")
    plt.grid(True); plt.legend()
    plt.savefig(out_png, dpi=180, bbox_inches='tight'); plt.close()

def plot_lifetime_mass(df: pd.DataFrame, curves, out_png: Path):
    dg = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
    X = dg["log_mass"].to_numpy(float)  # type: ignore
    Y = dg["log_tau"].to_numpy(float)  # type: ignore

    pts_csv = out_png.parent / "points_logm_logtau.csv"
    _write_csv(pts_csv, [{"log_mass": float(x), "log_tau": float(y)} for x,y in zip(X,Y)], ["log_mass","log_tau"]) 
    _append_md(out_png.parent / "lm_top_curves_overlay.md", [
        "# Lifetime–mass overlay", f"- PNG: {out_png.name}", f"- Points CSV: {pts_csv.name}", "- Curves CSV: lm_curves_logm_logtau.csv"
    ])

    curve_lines = []
    for idx,(c, ids, xin) in enumerate(curves[:3], start=1):
        xmin = float(xin.min()); xmax = float(xin.max())
        xs = np.linspace(xmin, xmax, 400)
        ys = model_eval(c.family, c.theta, xs)
        for xi, yi in zip(xs, ys):
            curve_lines.append({"rank": idx, "family": c.family, "expr": pretty_expr_lm(c), "log_mass": float(xi), "log_tau_fit": float(yi)})
    _write_csv(out_png.parent / "lm_curves_logm_logtau.csv", curve_lines, ["rank","family","expr","log_mass","log_tau_fit"])

    plt.figure(figsize=(12, 8))
    plt.scatter(X, Y, s=6)
    for c, ids, xin in curves[:3]:
        xmin = float(xin.min()); xmax = float(xin.max())
        xs = np.linspace(xmin, xmax, 400)
        ys = model_eval(c.family, c.theta, xs)
        plt.plot(xs, ys, linewidth=2, label=f"{c.family}: {pretty_expr_lm(c)}")
    plt.title("log10(lifetime) vs log10(mass) with top curves (inlier span)")
    plt.xlabel("log10(mass [MeV])"); plt.ylabel("log10(lifetime [s])")
    plt.grid(True); plt.legend()
    plt.savefig(out_png, dpi=180, bbox_inches='tight'); plt.close()

# ------------------------- REPORT WRITING ------------------------

def write_report(out_dir: Path, df: pd.DataFrame, curves, osc_results,
                 bootstrap_n: int = 0, cv_frac: float = 0.2, nperm: int = 400,
                 save_curve_residuals: bool = False, mass_cutoff: float = float('inf')):
    curves_json = []
    for j, (c, ids) in enumerate(curves, 1):
        physics = interpret_curve_physics(c, df, ids)

        # Optional extras
        per_osc = per_curve_oscillation(df, c, ids, nperm=nperm,
                                        out_dir=(out_dir if save_curve_residuals else None),
                                        tag=f"{j}")
        cv_rmse = cv_score_curve(df, c, ids, frac=cv_frac, nsplits=3)
        boot = bootstrap_curve_ci(df, c, ids, n_boot=bootstrap_n,
                                  out_dir=(out_dir if save_curve_residuals else None),
                                  tag=f"{j}")

        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy scalar types
                return obj.item()
            elif isinstance(obj, (np.bool_, np.integer, np.floating)):
                return obj.item()
            else:
                return obj

        # Determine sector for this curve from inliers (majority vote)
        inlier_df = df[df["id"].isin(ids)]  # type: ignore
        sector_val = None
        if "sector" in inlier_df.columns and not inlier_df.empty:  # type: ignore
            sector_val = inlier_df["sector"].mode().iat[0]  # type: ignore

        curves_json.append({
            "rank": j,
            "family": c.family,
            "theta": tuple(map(float, c.theta)),
            "expression": pretty_expr_centered(c),
            "score": float(c.score),
            "inliers": int(c.n_inliers),
            "sm_hits": int(c.sm_hits),
            "bic": float(c.bic),
            "inlier_ids": ids,
            "sector": sector_val,                      # <--- NEW
            "physics_interpretation": convert_numpy_types(physics),
            "per_curve_osc": convert_numpy_types(per_osc),
            "cv_rmse": cv_rmse,
            "bootstrap_hinges": convert_numpy_types(boot)
        })
    (out_dir / "curves.json").write_text(json.dumps(curves_json, indent=2))

    md_lines = []
    md_lines.append(f"# Curve Mining Summary (mass < {mass_cutoff/1000:.1f} GeV)\n")
    md_lines.append("## Counts by branch and c-state\n")
    counts = df.groupby(["branch_inferred","c_state"]).size().rename("count")  # type: ignore
    md_lines.append(counts.to_markdown())
    md_lines.append("\n\n## Top Curves with Physics Interpretation\n")
    for j, c_d in enumerate(curves_json, 1):
        md_lines.append(f"### [{j}] {c_d['expression']}")
        md_lines.append(f"- family: `{c_d['family']}`  ")
        md_lines.append(f"- theta: `{c_d['theta']}`  ")
        md_lines.append(f"- score: **{c_d['score']:.2f}**, inliers: **{c_d['inliers']}**, SM hits: **{c_d['sm_hits']}**, BIC: {c_d['bic']:.1f}")
        phys = c_d['physics_interpretation']
        md_lines.append(f"- **Physics Classification**: {phys['structural_type']} ({phys['slope_character']})")
        md_lines.append(f"- **Significance Score**: {phys['significance_score']:.1f}/10")
        md_lines.append(f"- **SM Enrichment**: {phys['sm_enrichment']:.1%}")
        md_lines.append(f"- **Stability Enrichment**: {phys['stability_enrichment']:.1%}")
        if "align233" in phys and phys["align233"]:
            md_lines.append(f"- **Hinge alignment to 233**: {phys['align233']}")
        if phys['oscillatory']:
            md_lines.append(f"- **Oscillatory (fast FFT check)**: period ≈ {phys['period_estimate']:.1f} steps")
        if c_d["per_curve_osc"]:
            md_lines.append(f"- **Per-curve oscillation (strict)**: P≈{c_d['per_curve_osc'].get('period_steps', float('nan')):.2f}, z≈{c_d['per_curve_osc'].get('z_score', float('nan')):.2f}, n={c_d['per_curve_osc'].get('n_points', 0)}")
        if c_d["cv_rmse"] == c_d["cv_rmse"]:  # not NaN
            md_lines.append(f"- **Per-curve CV RMSE**: {c_d['cv_rmse']:.4f} (log10 units)")
        if c_d["bootstrap_hinges"]:
            md_lines.append(f"- **Bootstrap hinges**: {c_d['bootstrap_hinges']}")
        md_lines.append("")

    md_lines.append("\n\n## Oscillation (strict detrend + AR(1) whiten + block permutation)\n")
    if osc_results:
        for r in osc_results:
            md_lines.append(f"- segment (branch={r['branch']}, c_state={r['c_state']}): P≈{r['period_steps']:.2f} steps, z≈{r['z_score']:.2f}, n={r['n_points']}")
    else:
        md_lines.append("- (no segments large enough for testing)")

    # Per-sector summary (mass–k)
    try:
        sec_tbl = {}
        for c in curves_json:
            sec = c.get("sector","unknown")
            ent = sec_tbl.setdefault(sec, {"n_curves":0, "bic_vals":[], "cv_vals":[]})
            ent["n_curves"] += 1
            if isinstance(c.get("bic"), (int,float)) and np.isfinite(c["bic"]):
                ent["bic_vals"].append(float(c["bic"]))
            if isinstance(c.get("cv_rmse"), (int,float)) and np.isfinite(c["cv_rmse"]):
                ent["cv_vals"].append(float(c["cv_rmse"]))
        md_lines.append("\n\n## Mass–k Sector Summary\n")
        if sec_tbl:
            md_lines.append("| sector | n_curves | median BIC | median CV RMSE (log m) |")
            md_lines.append("|---|---:|---:|---:|")
            for sec, ent in sec_tbl.items():
                med_bic = np.median(ent["bic_vals"]) if ent["bic_vals"] else float("nan")
                med_cv  = np.median(ent["cv_vals"])  if ent["cv_vals"]  else float("nan")
                md_lines.append(f"| {sec} | {ent['n_curves']} | {med_bic:.1f} | {med_cv:.4f} |")
        else:
            md_lines.append("- (no curves)")
    except Exception:
        pass

    (out_dir / "report.md").write_text("\n".join(md_lines))

# -------- Multivariate SURFACES (low-rank) --------

def _bic(y, yhat, p):
    n = len(y)
    sse = float(np.sum((y - yhat) ** 2))
    return n*np.log(sse/n) + p*np.log(n) if (n>p and sse>0) else -np.inf

def _fit_plane(X: np.ndarray, y: np.ndarray):
    # LS with intercept column included in X
    th, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ th
    # p = params
    p = X.shape[1]
    bic = _bic(y, yhat, p)
    sst = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - (float(np.sum((y - yhat) ** 2)) / sst if sst>0 else 0.0)
    return th.astype(float), yhat, bic, r2

def _quantile_grid(x: np.ndarray, qs=(0.2,0.35,0.5,0.65,0.8)):
    xs = [np.quantile(x, q) for q in qs]
    return sorted(set([float(v) for v in xs]))

def fit_mass_surface(df: pd.DataFrame) -> dict:
    """Fit log_mass ~ A + B*k + C*I_c15 + D*I_our (+ hinge on k)."""
    g = df.copy()
    xk = g["k"].to_numpy(float)
    y = g["log_mass"].to_numpy(float)
    I_c15 = (g["c_state"]=="latched_15").to_numpy(float)
    I_our = (g["branch_inferred"]=="our").to_numpy(float)
    # baseline plane
    X0 = np.vstack([np.ones_like(xk), xk, I_c15, I_our]).T
    th0, yhat0, bic0, r20 = _fit_plane(X0, y)
    best = {"family":"plane", "theta":th0.tolist(), "bic":bic0, "r2":r20,
            "expression":"log10(m)=A + B·k + C·I_c15 + D·I_our"}
    # plane + hinge on k
    best_h = None
    for k0 in _quantile_grid(xk):
        H = np.maximum(0.0, xk - k0)
        Xh = np.vstack([np.ones_like(xk), xk, I_c15, I_our, H]).T
        th, yhat, bich, r2h = _fit_plane(Xh, y)
        if (best_h is None) or (bich < best_h[0]):
            best_h = (bich, r2h, float(k0), th)
    if best_h is not None and best_h[0] < bic0:
        bich, r2h, k0, th = best_h
        best = {"family":"plane_hinge_k", "theta":th.tolist(), "k0":k0,
                "bic":bich, "r2":r2h,
                "expression":f"log10(m)=A + B·k + C·I_c15 + D·I_our + E·max(0,k−{k0:.0f})"}
    return best

def fit_lifetime_surface(df: pd.DataFrame) -> dict:
    """Fit log_tau ~ A + B·log_m + C·I_c15 + D·I_our (+ hinge on log_m)."""
    g = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
    if g.empty:
        return {}
    xm = g["log_mass"].to_numpy(float)  # type: ignore
    y = g["log_tau"].to_numpy(float)  # type: ignore
    I_c15 = (g["c_state"]=="latched_15").to_numpy(float)  # type: ignore
    I_our = (g["branch_inferred"]=="our").to_numpy(float)  # type: ignore
    X0 = np.vstack([np.ones_like(xm), xm, I_c15, I_our]).T
    th0, yhat0, bic0, r20 = _fit_plane(X0, y)
    best = {"family":"plane", "theta":th0.tolist(), "bic":bic0, "r2":r20,
            "expression":"log10(τ)=A + B·log10(m) + C·I_c15 + D·I_our"}
    best_h = None
    for x0 in _quantile_grid(xm):
        H = np.maximum(0.0, xm - x0)
        Xh = np.vstack([np.ones_like(xm), xm, I_c15, I_our, H]).T
        th, yhat, bich, r2h = _fit_plane(Xh, y)
        if (best_h is None) or (bich < best_h[0]):
            best_h = (bich, r2h, float(x0), th)
    if best_h is not None and best_h[0] < bic0:
        bich, r2h, x0, th = best_h
        best = {"family":"plane_hinge_logm", "theta":th.tolist(), "x0":x0,
                "bic":bich, "r2":r2h,
                "expression":f"log10(τ)=A + B·log10(m) + C·I_c15 + D·I_our + E·max(0,log10(m)−{x0:.2f})"}
    return best

def write_surfaces(out_dir: Path, mass_surf: dict, lm_surf: dict):
    payload = {"mass_surface": mass_surf, "lifetime_surface": lm_surf}
    (out_dir/"surfaces.json").write_text(json.dumps(payload, indent=2))
    # append a short section to report.md
    lines = ["\n\n## Multivariate Surfaces (low-rank)\n"]
    if mass_surf:
        lines.append("### Mass surface (k, I_c15, I_our)\n")
        lines.append(f"- {mass_surf['expression']}  ")
        lines.append(f"  BIC: {mass_surf['bic']:.1f}, R²: {mass_surf['r2']:.4f}\n")
    if lm_surf:
        lines.append("### Lifetime surface (log10 m, I_c15, I_our)\n")
        lines.append(f"- {lm_surf['expression']}  ")
        lines.append(f"  BIC: {lm_surf['bic']:.1f}, R²: {lm_surf['r2']:.4f}\n")
    with open(out_dir/"report.md", "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

# -------- Consensus / Harmonics / Heatmaps / FDR / Law Family / Export --------

def _norm_sf_from_z(z: float) -> float:
    # two-sided p from z using error function: p = 2 * (1 - Phi(|z|))
    zp = abs(z)
    Phi = 0.5 * (1.0 + erf(zp / sqrt(2.0)))
    return max(0.0, 2.0 * (1.0 - Phi))

def compute_consensus(out_dir: Path) -> pd.DataFrame:
    """Aggregate inlier membership across mass–k curves, lifetime–mass curves, and surfaces.
    Returns a DataFrame with columns: particle_id, score, sources_json.
    """
    sources = {}
    def add(ids, tag):
        for pid in ids:
            rec = sources.setdefault(pid, {"score":0, "sources":[]})
            rec["score"] += 1
            rec["sources"].append(tag)
    # mass–k curves.json
    cj_path = out_dir / "curves.json"
    if cj_path.exists():
        cj = json.loads(cj_path.read_text())
        for c in cj:
            add(c.get("inlier_ids", []), f"mass_curve_{c.get('rank')}")
    # lifetime–mass lm_curves.json
    lm_path = out_dir / "lm_curves.json"
    if lm_path.exists():
        lm = json.loads(lm_path.read_text())
        for c in lm:
            for pid in c.get("inlier_ids", []):
                add([pid], f"lm_curve_{c.get('rank')}")
    # surfaces: no per-id inliers; skip
    rows = []
    for pid, rec in sources.items():
        rows.append({"particle_id": pid, "consensus_score": rec["score"], "sources": json.dumps(rec["sources"])})
    dfc = pd.DataFrame(rows).sort_values(["consensus_score","particle_id"], ascending=[False,True])
    if not dfc.empty:
        dfc.to_csv(out_dir / "consensus_scores.csv", index=False)
        # anchors markdown
        topN = dfc.head(50)
        lines = ["\n\n## Consensus Anchors (top 50)\n", "| particle_id | score | sources |", "|---|---:|---|"]
        for _,r in topN.iterrows():
            lines.append(f"| {r['particle_id']} | {int(r['consensus_score'])} | {r['sources']} |")
        with open(out_dir/"anchors_topN.md","w",encoding="utf-8") as f:
            f.write("\n".join(lines))
    return dfc

def analyze_harmonics(out_dir: Path, base: float=233.0, harmonics=(0.5,1,2,3)) -> dict:
    """Analyze hinge alignment to base*harmonic multiples; write histogram."""
    cj_path = out_dir / "curves.json"
    if not cj_path.exists():
        return {}
    cj = json.loads(cj_path.read_text())
    klist = []
    for c in cj:
        fam = c.get("family")
        theta = c.get("theta", [])
        if fam == "hinge_centered" and len(theta) == 4:
            k0 = float(theta[3]); klist.append(k0)
        elif fam == "hinge2_centered" and len(theta) == 6:
            k0 = float(theta[3]); k1 = float(theta[5]); klist.extend([k0,k1])
    if not klist:
        return {}
    def dist_to_harmonic(k0):
        best = (None, 1e12)
        for h in harmonics:
            step = base * h
            # distance to nearest multiple of step
            r = np.mod(k0, step)
            d = float(min(r, step - r))
            if d < best[1]:
                best = (step, d)
        return best
    dists = [dist_to_harmonic(k0)[1] for k0 in klist]
    _write_csv(out_dir/"hinge_alignment_distances.csv", [{"distance": float(d)} for d in dists], ["distance"])
    # histogram
    plt.figure(figsize=(8,4))
    plt.hist(dists, bins=40, alpha=0.8)
    plt.title("Hinge distance to nearest 233 harmonic")
    plt.xlabel("distance (k units)"); plt.ylabel("count")
    plt.grid(True)
    plt.savefig(out_dir/"hinge_alignment_hist.png", dpi=160, bbox_inches='tight'); plt.close()
    stats = {"n_hinges": len(klist), "median_dist": float(np.median(dists)), "mean_dist": float(np.mean(dists))}
    (out_dir/"hinge_alignment_stats.json").write_text(json.dumps(stats, indent=2))
    return stats

def plot_heatmaps(out_dir: Path, df: pd.DataFrame):
    """2D residual heatmaps for mass–k and lifetime–mass."""
    # mass plane
    try:
        x = df["k"].to_numpy(float)
        y = df["log_mass"].to_numpy(float)
        fam, theta, yhat, _ = fit_best_trend(x, y)
        r = y - yhat
        plt.figure(figsize=(8,6))
        H, xe, ye = np.histogram2d(x, r, bins=100)
        _write_csv(out_dir/"residual_heatmap_mass.csv", [{"k_bin": float(xe[i]), "res_bin": float(ye[j]), "count": int(H[i,j])} for i in range(H.shape[0]) for j in range(H.shape[1])], ["k_bin","res_bin","count"])
        plt.hist2d(x, r, bins=100, cmap="viridis")
        plt.colorbar(label="count")
        plt.title("Residual heatmap: mass vs k")
        plt.xlabel("k"); plt.ylabel("log10(m) residual")
        plt.savefig(out_dir/"residual_heatmap_mass.png", dpi=160, bbox_inches='tight'); plt.close()
    except Exception:
        pass
    # lifetime plane
    try:
        g = df[np.isfinite(df["log_mass"]) & np.isfinite(df["log_tau"])].copy()
        if not g.empty:
            xm = g["log_mass"].to_numpy(float)  # type: ignore
            y = g["log_tau"].to_numpy(float)  # type: ignore
            fam, theta, yhat, _ = fit_best_trend(xm, y)
            r = y - yhat
            plt.figure(figsize=(8,6))
            H, xe, ye = np.histogram2d(xm, r, bins=100)
            _write_csv(out_dir/"residual_heatmap_lm.csv", [{"logm_bin": float(xe[i]), "res_bin": float(ye[j]), "count": int(H[i,j])} for i in range(H.shape[0]) for j in range(H.shape[1])], ["logm_bin","res_bin","count"])
            plt.hist2d(xm, r, bins=100, cmap="magma")
            plt.colorbar(label="count")
            plt.title("Residual heatmap: lifetime vs log mass")
            plt.xlabel("log10(m)"); plt.ylabel("log10(τ) residual")
            plt.savefig(out_dir/"residual_heatmap_lm.png", dpi=160, bbox_inches='tight'); plt.close()
    except Exception:
        pass

def fdr_oscillation(osc_results: List[dict]) -> List[dict]:
    """Attach two-sided p-values and BH q-values to oscillation results."""
    if not osc_results:
        return []
    # compute p from z
    pvals = [ _norm_sf_from_z(r.get("z_score", 0.0)) for r in osc_results ]
    m = len(pvals)
    order = np.argsort(pvals)
    qvals = [0.0]*m
    prev = 1.0
    for rank, idx in enumerate(order, start=1):
        q = pvals[idx] * m / rank
        prev = min(prev, q)
        qvals[idx] = prev
    out = []
    for r, p, q in zip(osc_results, pvals, qvals):
        r2 = dict(r)
        r2["p_value"] = float(p)
        r2["q_value"] = float(q)
        out.append(r2)
    return out

def fit_law_family(out_dir: Path) -> dict:
    """Meta-fit a shared slope across hinge curves as a simple law family (diagnostic)."""
    cj_path = out_dir/"curves.json"
    if not cj_path.exists():
        return {}
    cj = json.loads(cj_path.read_text())
    Bs, Ds = [], []
    for c in cj:
        if c.get("family") == "hinge_centered":
            A,B,D,k0 = c.get("theta", [None]*4)
            if B is not None and D is not None:
                Bs.append(float(B)); Ds.append(float(D))
    if not Bs:
        return {}
    law = {
        "B_shared_median": float(np.median(Bs)),
        "D_shared_median": float(np.median(Ds)),
        "B_IQR": [float(np.percentile(Bs,25)), float(np.percentile(Bs,75))],
        "D_IQR": [float(np.percentile(Ds,25)), float(np.percentile(Ds,75))],
    }
    (out_dir/"law_family.json").write_text(json.dumps(law, indent=2))
    return law

def export_parquet_or_csv(out_dir: Path, df: pd.DataFrame):
    try:
        # Create parquet directory and export
        pq_dir = out_dir/"parquet"; pq_dir.mkdir(exist_ok=True)
        
        # Fix mixed data types before parquet export
        df_clean = df.copy()
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                # Try to convert to numeric, fallback to string
                try:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                except:
                    df_clean[col] = df_clean[col].astype(str)
        
        df_clean.to_parquet(pq_dir/"catalog.parquet", index=False)
        print(f"✅ Parquet export: {len(df)} rows to {pq_dir/'catalog.parquet'}")
        
        # Also export CSV for compatibility
        df_clean.to_csv(pq_dir/"catalog_export.csv", index=False)
        print(f"✅ CSV export: {len(df)} rows to {pq_dir/'catalog_export.csv'}")
        
    except Exception as e:
        print(f"⚠️  Parquet export failed: {e}")
        # Fallback to CSV in main directory
        df.to_csv(out_dir/"catalog_export.csv", index=False)
        print(f"✅ CSV fallback export: {len(df)} rows to {out_dir/'catalog_export.csv'}")

def write_interpretation(out_dir: Path, df: pd.DataFrame):
    lines = ["\n\n## Interpretation (conditional)\n"]
    # Subsets
    total = len(df)
    greens = df[df["classification_color"]=="Green"]
    blues = df[df["classification_color"]=="Blue"]
    g_n, b_n = len(greens), len(blues)
    lines.append(f"- Catalog size: {total}; Green: {g_n} ({g_n/max(1,total):.1%}); Blue: {b_n} ({b_n/max(1,total):.1%})")

    # Load optional artifacts
    law_family = _load_json(out_dir/"law_family.json") if (out_dir/"law_family.json").exists() else {}
    hinge_stats = _load_json(out_dir/"hinge_alignment_stats.json") if (out_dir/"hinge_alignment_stats.json").exists() else {}
    osc_mass = _load_json(out_dir/"oscillation_fdr_mass.json") if (out_dir/"oscillation_fdr_mass.json").exists() else []
    osc_lm = _load_json(out_dir/"oscillation_fdr_lm.json") if (out_dir/"oscillation_fdr_lm.json").exists() else []
    surf = _load_json(out_dir/"surfaces.json") if (out_dir/"surfaces.json").exists() else {}

    # Conditional narratives
    if law_family:
        lines.append(f"- Shared hinge slopes (median): B≈{law_family.get('B_shared_median','?'):.3e}, D≈{law_family.get('D_shared_median','?'):.3e}; IQR ranges suggest {'tight' if (law_family.get('B_IQR') and (law_family['B_IQR'][1]-law_family['B_IQR'][0])<1e-3) else 'broad'} slope concentration.")
    if hinge_stats:
        lines.append(f"- Hinges align near even-step harmonics: median distance to harmonic ≈ {hinge_stats.get('median_dist','?'):.1f} k-units.")

    def _q_hits(osc):
        return [r for r in osc if r.get('q_value',1.0) < 0.05]
    q_mass = _q_hits(osc_mass); q_lm = _q_hits(osc_lm)
    if q_mass:
        lines.append(f"- Significant oscillations in mass–k (FDR q<0.05): {len(q_mass)} segments; strongest period ~ {q_mass[0].get('period_steps','?'):.0f} steps.")
    if q_lm:
        lines.append(f"- Significant oscillations in lifetime–mass (FDR q<0.05): {len(q_lm)} segments; strongest period index ~ {q_lm[0].get('period_index_units','?'):.0f}.")

    # Surfaces
    ms = surf.get('mass_surface'); ls = surf.get('lifetime_surface')
    if ms and ms.get('r2',0)>0:
        lines.append(f"- Mass surface (k, c-state, branch) explains R²≈{ms['r2']:.3f} with {'hinge at k≈'+str(int(ms.get('k0'))) if 'k0' in ms else 'no hinge'}.")
    if ls and ls.get('r2',0)>0:
        lines.append(f"- Lifetime surface (log m, c-state, branch) explains R²≈{ls['r2']:.3f} with {'hinge at log m≈'+str(ls.get('x0')) if 'x0' in ls else 'no hinge'}.")

    # Stability-focused insight (what's new beyond "GTE echoes")
    # Compare distributions of k and log m for Green/Blue vs all
    if g_n>10:
        g_k_mu = float(greens['k'].mean()); all_k_mu = float(df['k'].mean())
        lines.append(f"- Greens concentrate near k≈{g_k_mu:.0f} vs catalog mean k≈{all_k_mu:.0f}, suggesting selective sub-trajectories within the ladder.")
    if b_n>10 and df['log_mass'].notna().any():  # type: ignore
        b_m_mu = float(blues['log_mass'].mean()); all_m_mu = float(df['log_mass'].mean())
        lines.append(f"- Blues show mean log mass≈{b_m_mu:.2f} vs catalog mean≈{all_m_mu:.2f}, indicating viable but unstable states occupy a distinct mass band.")

    # Avoid hard claims; emphasize testable hypotheses
    lines.append("\n**Takeaway.** The laws we recover (hinges at even-step harmonics, broken lifetime power, oscillations with FDR control) are consistent with a deterministic ladder. More importantly, the **stable/viable subsets** occupy specific sub-trajectories and bands, which can be formulated as falsifiable hypotheses about where stability emerges (in k and log m). These are lateral insights beyond generation rules: they prioritize which GTE sub-trajectories are **significant**, and offer concrete targets for physics proofs or empirical checks.")

    _append_md(out_dir/"report.md", lines)

# -------- Artifact companions (CSV/MD) --------

def _write_csv(path: Path, rows: List[Dict[str, Any]], field_order: Optional[List[str]] = None):
    if not rows:
        path.write_text("")
        return
    import csv
    keys = field_order or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})

def _append_md(out: Path, lines: List[str]):
    with open(out, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# ------------------------- CLI / MAIN ----------------------------

def main():
    ap = argparse.ArgumentParser(description="Mine simple curves on (k, log10(mass)) below a mass cutoff.")
    
    # === PREFERRED V4 ANALYTICS COMMAND ===
    # For comprehensive V4 analytics across all sectors with meta-law analysis:
    #
    # python Verifier_discovery_advanced_particle_analysis.py \
    #   --csv path/to/v4/candidates.csv \
    #   --out run_v4_all_sectors
    #
    # DEFAULT: --preset v4_all_sectors_fast (5-10 minutes)
    # This preset enables:
    # • Mass–k mining per sector (fermion, neutrino, boson, composite)
    # • Lifetime–mass analysis with auto mode selection
    # • Meta-law testing (pooled vs sector-interaction models)
    # • Surfaces, consensus, harmonics, oscillations, exports
    # • Full QA artifacts and uncertainty summaries
    #
    # Alternative presets:
    # • --preset v4_all_sectors_thorough  (2-4 hours, maximum precision)
    # • --preset v4_fermions_only         (fermion-only with domain guard)
    # ===
    ap.add_argument("--csv", default=DEFAULT_CSV_PATH, help="Path to candidates.csv")
    ap.add_argument("--mass_cutoff", type=float, default=MASS_CUTOFF_DEFAULT, help="Max mass (MeV)")
    ap.add_argument("--use_calibration_threshold", action="store_true", help="Shortcut: set mass cutoff to 173 GeV (1.73e5 MeV)")
    ap.add_argument("--max_curves", type=int, default=MAX_CURVES_DEFAULT, help="Number of curves to mine")
    ap.add_argument("--trials", type=int, default=RANSAC_TRIALS_DEFAULT, help="RANSAC trials per family")
    ap.add_argument("--sample_size", type=int, default=None, help="Sample size for curve mining (default: use all data)")
    ap.add_argument("--max_workers", type=int, default=4, help="Number of multiprocessing workers for RANSAC (default: 4)")
    ap.add_argument("--out", default="", help="Output directory (default: Verifier_analytics_runs/analytics_run_all_sectors_TIMESTAMP)")
    ap.add_argument("--do_lifetime", action="store_true", help="Also mine curves on (log10 mass, log10 lifetime)")

    # NEW options
    ap.add_argument("--with_hinge2", action="store_true", help="Enable the two-hinge family (hinge2_centered)")
    ap.add_argument("--bootstrap_n", type=int, default=0, help="Per-curve bootstrap refits for hinge CI (0=off)")
    ap.add_argument("--cv_frac", type=float, default=0.2, help="Hold-out fraction for per-curve CV")
    ap.add_argument("--nperm", type=int, default=400, help="Permutations for oscillation z-scores")
    ap.add_argument("--save_curve_residuals", action="store_true", help="Save residual plots / bootstrap hists for top curves")
    ap.add_argument("--reuse", action="store_true", help="Reuse existing artifacts if inputs match (manifest.json)")
    ap.add_argument("--db", default="", help="Optional path to a SQLite file to store curves/inliers (''=off)")
    ap.add_argument("--skip_mass", action="store_true", help="Skip mass–k curve mining (reuse or none)")
    ap.add_argument("--skip_segment_osc", action="store_true", help="Skip segment-level oscillation tests")
    ap.add_argument("--skip_global_fits", action="store_true", help="Skip global fitting (hinge, etc.)")
    ap.add_argument("--skip_report", action="store_true", help="Skip writing/append report")
    ap.add_argument("--skip_lifetime", action="store_true", help="Skip lifetime–mass analysis")
    ap.add_argument("--do_surface", action="store_true", help="Fit multivariate surfaces (mass: (k, 1[c=15], 1[branch]); lifetime: (log m, 1[c=15], 1[branch])")
    ap.add_argument("--skip_surface", action="store_true", help="Skip surface fitting")
    ap.add_argument("--do_consensus", action="store_true", help="Compute consensus inlier scores and anchors")
    ap.add_argument("--check_harmonics", action="store_true", help="Analyze hinge alignment to 233 harmonics")
    ap.add_argument("--fit_law_family", action="store_true", help="Meta-fit shared slope family across curves")
    ap.add_argument("--plot_heatmaps", action="store_true", help="Plot residual heatmaps for mass and lifetime")
    ap.add_argument("--export_parquet", action="store_true", help="Export catalog as parquet (fallback CSV)")
    ap.add_argument("--skip_export", action="store_true", help="Skip exporting to parquet")
    ap.add_argument("--skip_inlier_analysis", action="store_true", help="Skip inlier analysis")
    ap.add_argument("--skip_physics_analysis", action="store_true", help="Skip physics analysis")
    ap.add_argument("--skip_oscillation_analysis", action="store_true", help="Skip oscillation analysis")
    ap.add_argument("--class_scope",
        choices=["fermions_only","no_neutrinos","all"],
        default="fermions_only",
        help="Which classes are allowed to PARTICIPATE in mining/fitting.")
    ap.add_argument("--domain_guard", action="store_true",
        help="Restrict mass–k fitting to interpolation regime (<= top mass) and integer k.")
    ap.add_argument("--allow_nonfermion_k_laws", action="store_true",
        help="Enable mass–k mining for neutrino/boson/composite sectors (off by default).")
    ap.add_argument(
        "--lifetime_source_mode",
        choices=["auto", "raw", "calibrated", "dual"],
        default="auto",
        help="Which lifetime to use for LM analytics: raw Tier-1, calibrated, both (dual), or auto preference."
    )
    ap.add_argument(
        "--preset",
        choices=["v4_all_sectors_fast", "v4_all_sectors_balanced", "v4_all_sectors_no_bootstrap", "v4_all_sectors_thorough", "v4_fermions_only", "v4_micro_test"],
        default="v4_all_sectors_fast",
        help="Apply a preset configuration of analytics flags. Default: v4_all_sectors_fast (5-10 min). Use v4_all_sectors_balanced for optimal speed/accuracy (15-30 min). Use v4_all_sectors_thorough for maximum precision (2-4 hours)."
    )



    args = ap.parse_args()

    def _apply_preset(args):
        if not getattr(args, "preset", None):
            return

        if args.preset == "v4_all_sectors_fast":
            # Fast: same scope & features, much lighter sampling (DEFAULT)
            args.class_scope = "all"
            args.allow_nonfermion_k_laws = True
            args.use_calibration_threshold = True  # Set 173 GeV cutoff
            args.do_lifetime = True
            if hasattr(args, "lifetime_source_mode"):
                args.lifetime_source_mode = "auto"  # pick best available once
            args.do_surface = True
            args.do_consensus = True
            args.check_harmonics = True
            args.fit_law_family = True
            args.plot_heatmaps = True
            args.export_parquet = True
            args.with_hinge2 = True
            args.bootstrap_n = 20
            args.cv_frac = 0.10
            args.nperm = 50
            args.max_curves = 3  # Limit to top 3 curves per sector
            args.trials = 10     # Much fewer RANSAC trials
            args.sample_size = 50000  # Sample only 50k particles for curve mining

        elif args.preset == "v4_all_sectors_balanced":
            # Balanced: optimal speed/accuracy tradeoff (15-30 minutes)
            args.class_scope = "all"
            args.allow_nonfermion_k_laws = True
            args.use_calibration_threshold = True  # Set 173 GeV cutoff
            args.do_lifetime = True
            if hasattr(args, "lifetime_source_mode"):
                args.lifetime_source_mode = "auto"  # pick best available once
            args.do_surface = True
            args.do_consensus = True
            args.check_harmonics = True
            args.fit_law_family = True
            args.plot_heatmaps = True
            args.export_parquet = True
            args.with_hinge2 = True
            args.bootstrap_n = 10  # Reduced from 50 to 10 for speed
            args.cv_frac = 0.15
            args.nperm = 200
            args.max_curves = 10  # 10 curves per sector (40 total)
            args.trials = 100     # Good balance of trials
            args.sample_size = 100000  # 100k sample for comprehensive coverage

        elif args.preset == "v4_all_sectors_no_bootstrap":
            # No bootstrap: maximum speed (5-10 minutes)
            args.class_scope = "all"
            args.allow_nonfermion_k_laws = True
            args.use_calibration_threshold = True  # Set 173 GeV cutoff
            args.do_lifetime = True
            if hasattr(args, "lifetime_source_mode"):
                args.lifetime_source_mode = "auto"  # pick best available once
            args.do_surface = True
            args.do_consensus = True
            args.check_harmonics = True
            args.fit_law_family = True
            args.plot_heatmaps = True
            args.export_parquet = True
            args.with_hinge2 = True
            args.bootstrap_n = 0  # No bootstrap for maximum speed
            args.cv_frac = 0.15
            args.nperm = 200
            args.max_curves = 10  # 10 curves per sector (40 total)
            args.trials = 100     # Good balance of trials
            args.sample_size = 100000  # 100k sample for comprehensive coverage

        elif args.preset == "v4_all_sectors_thorough":
            # Thorough: maximum precision (2-4 hours)
            args.class_scope = "all"
            args.allow_nonfermion_k_laws = True
            args.use_calibration_threshold = True  # Set 173 GeV cutoff
            args.do_lifetime = True
            if hasattr(args, "lifetime_source_mode"):
                args.lifetime_source_mode = "dual"  # run raw + calibrated LM
            args.do_surface = True
            args.do_consensus = True
            args.check_harmonics = True
            args.fit_law_family = True
            args.plot_heatmaps = True
            args.export_parquet = True
            args.with_hinge2 = True
            args.bootstrap_n = 300
            args.cv_frac = 0.20
            args.nperm = 600
            # For full all-sector exploration we typically do NOT force domain_guard;
            # keep user's explicit flag if they pass it, otherwise leave as-is.

        elif args.preset == "v4_fermions_only":
            # A clean fermion-only law run (sectorized discovery but k-laws on fermions)
            args.class_scope = "fermions_only"
            args.allow_nonfermion_k_laws = False
            args.domain_guard = True         # integer ladder + interpolation regime
            args.use_calibration_threshold = True  # ≤ top mass
            args.do_lifetime = True
            if hasattr(args, "lifetime_source_mode"):
                args.lifetime_source_mode = "dual"
            args.do_surface = True
            args.do_consensus = True
            args.check_harmonics = True
            args.fit_law_family = True
            args.plot_heatmaps = True
            args.export_parquet = True
            args.with_hinge2 = True
            args.bootstrap_n = 200
            args.cv_frac = 0.20
            args.nperm = 400

        elif args.preset == "v4_micro_test":
            # Ultra-minimal test to verify all steps complete without hanging
            args.class_scope = "fermions_only"
            args.allow_nonfermion_k_laws = False
            args.domain_guard = True
            args.use_calibration_threshold = True
            args.do_lifetime = True
            if hasattr(args, "lifetime_source_mode"):
                args.lifetime_source_mode = "auto"  # Single mode for speed
            args.do_surface = False  # Skip heavy operations
            args.do_consensus = False
            args.check_harmonics = False
            args.fit_law_family = False
            args.plot_heatmaps = False
            args.export_parquet = False
            args.with_hinge2 = False
            args.bootstrap_n = 0  # No bootstrap
            args.cv_frac = 0.10
            args.nperm = 10  # Minimal permutations
            args.max_curves = 1  # Only 1 curve per family
            args.trials = 5  # Only 5 trials per family
            args.sample_size = 1000  # Tiny sample
            args.max_workers = 2  # Minimal workers
            args.skip_segment_osc = True  # Skip oscillation tests entirely
            # Note: Global fitting is now optimized and should complete quickly

    print(f"⚙️  Preset applied: {args.preset}")

    # Apply preset before any data loading/processing uses args
    _apply_preset(args)

    # Auto-generate run folder name if not specified
    if not args.out:
        # Create organized directory structure
        master_dir = Path("Verifier_analytics_runs")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        run_folder = f"analytics_run_all_sectors_{timestamp}"
        out_dir = master_dir / run_folder
    else:
        out_dir = Path(args.out)
    
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {out_dir.absolute()}")

    # Handle calibration shortcut BEFORE loading data
    mass_cutoff = args.mass_cutoff
    if args.use_calibration_threshold:
        mass_cutoff = 1.73e5  # 173 GeV in MeV
        print(f"🎯 Using calibration threshold: {mass_cutoff/1000:.1f} GeV ({mass_cutoff:.0f} MeV)")
    
    # Loud log at startup to show effective cutoff
    if mass_cutoff == float('inf'):
        print(f"📊 Mass cutoff: NO LIMIT (analyzing full CSV)")
    else:
        print(f"📊 Mass cutoff: {mass_cutoff/1000:.1f} GeV ({mass_cutoff:.0f} MeV)")
    
    # Load data with the effective cutoff
    df = load_df(args.csv, mass_cutoff)
    
    # Add sector tagging
    df = add_sector(df)
    
    # Apply cohort selection and domain guard
    def _class_mask(df: pd.DataFrame, scope: str) -> pd.Series:
        if scope == "fermions_only":
            return df["sector"] == "fermion"
        if scope == "no_neutrinos":
            return df["sector"] != "neutrino"
        return pd.Series(True, index=df.index)  # all

    df_all = df.copy()
    fit_mask = _class_mask(df, args.class_scope)
    df = df[fit_mask].copy()

    if args.domain_guard:
        # Guard: integer ladder & interpolation regime for k-laws
        if "k_is_int" in df.columns:
            df = df[df["k_is_int"] == True].copy()

    print(f"🔎 Class scope: {args.class_scope} | analytical rows: {len(df)} / {len(df_all)} total")

    # Select lifetime column for LM analytics based on --lifetime_source_mode
    def _select_lifetime_columns(df: pd.DataFrame, mode: str) -> str:
        has_raw = "log_tau_raw" in df.columns and bool(df["log_tau_raw"].notna().any())  # type: ignore
        has_cal = "log_tau_cal" in df.columns and bool(df["log_tau_cal"].notna().any())  # type: ignore
        if mode == "raw":
            return "log_tau_raw" if has_raw else ""
        if mode == "calibrated":
            return "log_tau_cal" if has_cal else ""
        if mode == "auto":
            # Prefer raw if available; else calibrated
            return "log_tau_raw" if has_raw else ("log_tau_cal" if has_cal else "")
        if mode == "dual":
            # handled later; return a sentinel indicating both are available/desired
            return "dual" if (has_raw or has_cal) else ""
        return ""

    active_log_tau = _select_lifetime_columns(df, args.lifetime_source_mode)  # type: ignore
    if args.do_lifetime and args.lifetime_source_mode != "dual":
        if not active_log_tau:
            print(f"⚠️  No usable lifetime for mode={args.lifetime_source_mode}; skipping lifetime–mass analysis.")
            args.skip_lifetime = True
        else:
            # unify to expected column name for downstream functions
            df = df.copy()
            df["log_tau"] = df[active_log_tau]

    # Checkpoint manifest logic
    manifest_path = out_dir / "manifest.json"
    csv_path = Path(args.csv)
    csv_hash = _file_sha256(csv_path) if csv_path.exists() else ""
    manifest = _load_json(manifest_path)
    run_id = manifest.get("run_id") or f"run_{int(time.time())}"
    manifest.setdefault("run_id", run_id)
    manifest.update({
        "csv_path": str(csv_path),
        "csv_hash": csv_hash,
        "mass_cutoff": mass_cutoff,  # Use effective cutoff, not raw argument
        "args": {
            "max_curves": args.max_curves,
            "trials": args.trials,
            "with_hinge2": args.with_hinge2,
            "bootstrap_n": args.bootstrap_n,
            "cv_frac": args.cv_frac,
            "nperm": args.nperm,
            "do_lifetime": args.do_lifetime
        }
    })

    conn = None
    if args.db:
        conn = _init_db(Path(args.db))
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO runs(run_id, created_at, csv_path, csv_hash, args_json) VALUES(?,?,?,?,?)",
                    (run_id, time.strftime('%Y-%m-%d %H:%M:%S'), str(csv_path), csv_hash, json.dumps(manifest.get('args', {}))))
        conn.commit()

    print("Counts by branch and c-state (below cutoff):")
    print(df.groupby(["branch_inferred","c_state"]).size().rename("count"))  # type: ignore

    families = ("line","hinge_centered","quad","const")
    if args.with_hinge2:
        families = ("line","hinge_centered","hinge2_centered","quad","const")

    curves = None
    curves_json_loaded = None
    curves_json_path = out_dir / "curves.json"

    if args.reuse and curves_json_path.exists():
        # try reuse if csv hash matches
        prev = _load_json(manifest_path)
        if prev.get("csv_hash") == csv_hash:
            print("[reuse] Loading curves.json")
            curves_json_loaded = _load_json(curves_json_path)
        else:
            print("[reuse] CSV changed; recomputing curves")

    if not args.skip_mass and curves_json_loaded is None:
        # choose sectors to mine (default = fermion only for v3-comparable behavior)
        if args.class_scope == "fermions_only":
            sectors_to_mine = ["fermion"]
        else:
            all_secs = sorted(df["sector"].dropna().unique())  # type: ignore
            if args.allow_nonfermion_k_laws:
                sectors_to_mine = all_secs
            else:
                sectors_to_mine = [s for s in all_secs if s == "fermion"]
                if any(s != "fermion" for s in all_secs):
                    print("ℹ️  Non-fermion sectors present; mass–k mining restricted to fermion unless --allow_nonfermion_k_laws is set.")
        sample_size = getattr(args, 'sample_size', None)
        all_curves = run_mass_k_mining_per_sector(df, families=families,  # type: ignore
                                                  max_curves=args.max_curves, trials=args.trials,
                                                  out_dir=out_dir, sectors=sectors_to_mine,
                                                  sample_size=sample_size, args=args)
        # Flatten for existing plotting/report code which expects (Curve, inliers)
        # but we'll keep sector info around for JSON writing & reporting
        curves = [(c, inliers) for (_, c, inliers) in all_curves]

        sub = df[np.isfinite(df["k"])].copy()  # type: ignore
        print("🎨 Creating mass-k plot...")
        plot_with_inlier_support(sub, curves, out_dir / "top_curves_overlay.png")  # type: ignore
        print("✅ Mass-k plot completed")  # type: ignore

        # segment-level oscillation unless skipped
        print("🔄 Running oscillation tests...")
        osc_results = [] if args.skip_segment_osc else oscillation_test_strict(df, top_segments=3, out_dir=out_dir, nperm=args.nperm)  # type: ignore
        if not args.skip_segment_osc and osc_results:
            osc_fdr = fdr_oscillation(osc_results)
            (out_dir/"oscillation_fdr_mass.json").write_text(json.dumps(osc_fdr, indent=2))
        print("✅ Oscillation tests completed")
        if not args.skip_report:
            print("📝 Writing mass-k report...")
            write_report(out_dir, df, curves, osc_results,  # type: ignore
                         bootstrap_n=args.bootstrap_n, cv_frac=args.cv_frac, nperm=args.nperm,
                         save_curve_residuals=args.save_curve_residuals, mass_cutoff=mass_cutoff)
            print("✅ Mass-k report completed")
        # Analytics windows (mass–k): per-sector sigma summary
        try:
            sigma_mk = sector_cv_sigma_massk(df=df, curves_json_path=out_dir/"curves.json")  # type: ignore
            if sigma_mk:
                windows_payload = _load_json(out_dir/"analytics_windows.json")
                windows_payload["mass_k"] = sigma_mk
                _save_json(out_dir/"analytics_windows.json", windows_payload)
        except Exception as _e:
            pass

        # Mass–k meta-law diagnostic (linear only)
        try:
            mk_meta = compare_massk_linear_meta(df)  # type: ignore
            if mk_meta:
                with open(out_dir / "report.md", "a", encoding="utf-8") as f:
                    f.write("\n\n## Mass–k Meta-Law (linear diagnostic)\n")
                    f.write(f"- BIC (pooled linear): {mk_meta['bic_pool_linear']:.1f}\n")
                    f.write(f"- BIC (sector-interact linear): {mk_meta['bic_sector_interact_linear']:.1f}\n")
                    f.write(f"- Verdict: **{mk_meta['winner']}** (diagnostic only)\n")
        except Exception:
            pass

        # Domain guard flags in artifacts
        try:
            guard_payload = {"domain_guard": bool(args.domain_guard), "mass_cutoff_mev": float(mass_cutoff)}
            sidecar = _load_json(out_dir/"analytics_domain.json")
            sidecar.update(guard_payload)
            _save_json(out_dir/"analytics_domain.json", sidecar)
        except Exception:
            pass

        # update manifest & db
        _save_json(manifest_path, manifest)
        if conn:
            # We will write sector into curves.json in Phase 3; here we keep DB as-is.
            cj = json.loads((out_dir/"curves.json").read_text()) if (out_dir/"curves.json").exists() else []
            _db_write_curves(conn, run_id, cj)
    elif curves_json_loaded is not None:
        print("[reuse] Skipping mass–k mining; using existing curves.json")
    else:
        print("[skip] mass–k mining skipped")

    if args.do_lifetime and not args.skip_lifetime:
        print("⏱️  Starting lifetime-mass analysis...")
        modes_to_run = [args.lifetime_source_mode]
        if args.lifetime_source_mode == "dual":
            modes_to_run = ["raw", "calibrated"]

        lm_summaries = {}  # store comparison metrics per mode

        for lm_mode in modes_to_run:
            # prepare a working df copy with selected log_tau
            log_tau_col = _select_lifetime_columns(df, lm_mode)  # type: ignore
            if not log_tau_col:
                print(f"ℹ️  LM mode={lm_mode}: no data; skipping.")
                continue
            df_lm = df.copy()
            df_lm["log_tau"] = df_lm[log_tau_col]

            # === existing LM body but replace 'df' by 'df_lm' inside this loop ===
            print(f"\n=== Lifetime vs Mass curve mining (mode={lm_mode}) ===")
            print(f"🔍 Mining lifetime curves with {args.trials} trials, {args.max_curves} max curves...")
            lm_curves = mine_curves_lifetime_mass(df_lm, families=("line","hinge_centered","quad","const"),  # type: ignore
                                                  max_curves=args.max_curves, trials=args.trials)
            print(f"✅ Found {len(lm_curves)} lifetime curves")
            plot_lifetime_mass(df_lm, lm_curves, out_dir / f"lm_top_curves_overlay_{lm_mode}.png")  # type: ignore

            # write lm_curves_{mode}.json
            lm_json = []
            for j,(c, ids, xin) in enumerate(lm_curves, 1):
                inlier_df = df_lm[df_lm["id"].isin(ids)]  # type: ignore
                sector_val = inlier_df["sector"].mode().iat[0] if ("sector" in inlier_df.columns and not inlier_df.empty) else None  # type: ignore
                lm_json.append({
                    "rank": j, "family": c.family, "theta": tuple(map(float, c.theta)),
                    "expression": pretty_expr_lm(c), "score": float(c.score),
                    "inliers": int(c.n_inliers), "sm_hits": int(c.sm_hits),
                    "inlier_ids": ids, "sector": sector_val, "lifetime_mode": lm_mode
                })
            (out_dir / f"lm_curves_{lm_mode}.json").write_text(json.dumps(lm_json, indent=2))

            # Strict oscillation
            lm_osc_results = [] if args.skip_segment_osc else oscillation_test_strict_lm(df_lm, top_segments=3, out_dir=out_dir, nperm=args.nperm)  # type: ignore
            if lm_osc_results:
                lm_fdr = fdr_oscillation(lm_osc_results)
                (out_dir/f"oscillation_fdr_lm_{lm_mode}.json").write_text(json.dumps(lm_fdr, indent=2))

            # Global fits / group summary / meta-law
            print("🔍 Running global lifetime-mass fits...")
            lm_global = fit_lifetime_mass_global(df_lm)  # type: ignore
            print("✅ Global fits completed")
            group_pw = group_power_law_summary(df_lm)  # type: ignore
            meta = compare_lifetime_meta_models(df_lm)  # type: ignore

            lm_summaries[lm_mode] = {
                "n_curves": len(lm_json),
                "global": lm_global, "meta": meta
            }

            # Append a mode-tagged section to report
            if not args.skip_report:
                lines = []
                lines.append(f"\n\n## Lifetime–Mass (mode={lm_mode})\n")
                if lm_json:
                    lines.append("### Top curves\n")
                    for c in lm_json:
                        lines.append(f"- [{c['rank']}] {c['expression']}  ")
                        lines.append(f"  family: `{c['family']}`, inliers: **{c['inliers']}**, SM hits: **{c['sm_hits']}**, score: {c['score']:.2f}\n")
                else:
                    lines.append("- (no admissible lifetime–mass curves found)\n")
                if lm_global:
                    win = lm_global.get("winner")
                    for k, v in lm_global.items():
                        if k == "winner": continue
                        tag = "(winner)" if k == win else ""
                        lines.append(f"- **{k}** {tag}: {v['expression']}  BIC: {v['bic']:.1f}, R²: {v['r2']:.4f}")
                if meta:
                    lines.append("\n- Meta-Law:")
                    lines.append(f"  BIC (pooled): {meta['bic_pool']:.1f}, BIC (sector-interactions): {meta['bic_sector_interact']:.1f}")
                    lines.append(f"  CV RMSE (pooled): {meta['cv_rmse_pool']:.4f}, CV RMSE (sector-interactions): {meta['cv_rmse_sector_interact']:.4f}")
                    lines.append(f"  Verdict: **{meta['winner']}**")
                with open(out_dir / "report.md", "a", encoding="utf-8") as f:
                    f.write("\n".join(lines))

        # (Optional) summarize RAW vs CALIBRATED differences
        if args.lifetime_source_mode == "dual" and not args.skip_report:
            raw_meta = (lm_summaries.get("raw") or {}).get("meta", {})
            cal_meta = (lm_summaries.get("calibrated") or {}).get("meta", {})
            with open(out_dir / "report.md", "a", encoding="utf-8") as f:
                f.write("\n\n## Lifetime–Mass RAW vs CALIBRATED (comparison)\n")
                if raw_meta and cal_meta:
                    f.write(f"- ΔBIC pooled: {cal_meta.get('bic_pool',np.nan) - raw_meta.get('bic_pool',np.nan):.1f}\n")
                    f.write(f"- ΔBIC sector-interact: {cal_meta.get('bic_sector_interact',np.nan) - raw_meta.get('bic_sector_interact',np.nan):.1f}\n")
                    f.write(f"- ΔCV RMSE pooled: {cal_meta.get('cv_rmse_pool',np.nan) - raw_meta.get('cv_rmse_pool',np.nan):.4f}\n")
                    f.write(f"- ΔCV RMSE sector-interact: {cal_meta.get('cv_rmse_sector_interact',np.nan) - raw_meta.get('cv_rmse_sector_interact',np.nan):.4f}\n")
                else:
                    f.write("- One of the modes had no usable data; no comparison.\n")
    else:
        if args.do_lifetime:
            print("[skip] lifetime–mass analysis skipped")

    # ----- SURFACE FITTING (optional) -----
    if args.do_surface and not args.skip_surface:
        print("\n=== Multivariate surface fitting ===")
        mass_surf = fit_mass_surface(df)  # type: ignore
        lm_surf = fit_lifetime_surface(df) if args.do_lifetime else {}  # type: ignore
        write_surfaces(out_dir, mass_surf, lm_surf)
    else:
        if args.do_surface:
            print("[skip] surface fitting skipped")

    # ----- OPTIONAL ANALYTICS -----
    if args.do_consensus:
        compute_consensus(out_dir)
    if args.check_harmonics:
        analyze_harmonics(out_dir)
    if args.fit_law_family:
        fit_law_family(out_dir)
    if args.plot_heatmaps:
        plot_heatmaps(out_dir, df)  # type: ignore
    if args.export_parquet:
        export_parquet_or_csv(out_dir, df)  # type: ignore

    # Save manifest at end
    _save_json(manifest_path, manifest)
    if conn:
        conn.close()
    
    # Write interpretation if not skipping report
    if not args.skip_report:
        write_interpretation(out_dir, df)  # type: ignore

    # === Analytics QA gates (soft warnings) ===
    try:
        # Mass–k curves.json CV & BIC sanity (if present)
        cj_path = out_dir/"curves.json"
        if cj_path.exists():
            cj = json.loads(cj_path.read_text())
            # warn if any hinge curve with |theta| extreme or too few inliers
            for c in cj:
                fam = c.get("family","")
                if fam.startswith("hinge") and c.get("inliers",0) < 12:
                    print(f"⚠️  QA: hinge curve rank={c.get('rank')} has few inliers ({c.get('inliers')}); treat cautiously.")
                if fam == "hinge_centered":
                    th = c.get("theta", [])
                    if len(th)==4 and abs(th[1])>1.0:  # B too steep in log-space per k
                        print(f"⚠️  QA: hinge slope B unusually large (|B|>1) in rank={c.get('rank')}.")
        # Lifetime meta-law decision sanity
        meta_path = out_dir/"report.md"
        # (no-op: we already appended numeric evidence)
    except Exception as _e:
        pass

    # Final summary
    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"📁 All outputs saved to: {out_dir.absolute()}")
    print(f"📊 Key files generated:")
    
    # List key output files
    key_files = [
        "curves.json", "report.md", "top_curves_overlay.png",
        "manifest.json"
    ]
    
    # Add lifetime files if they exist (check for mode-specific names)
    if args.do_lifetime:
        lm_files = list(out_dir.glob("lm_curves_*.json"))
        lm_plots = list(out_dir.glob("lm_top_curves_overlay_*.png"))
        if lm_files:
            key_files.extend([f.name for f in lm_files])
        if lm_plots:
            key_files.extend([f.name for f in lm_plots])
    
    if args.do_lifetime:
        # Check for oscillation files (they may not be generated if skipped)
        osc_mass = out_dir / "oscillation_fdr_mass.json"
        osc_lm_files = list(out_dir.glob("oscillation_fdr_lm_*.json"))
        if osc_mass.exists():
            key_files.append("oscillation_fdr_mass.json")
        if osc_lm_files:
            key_files.extend([f.name for f in osc_lm_files])
    if args.do_surface:
        key_files.append("surfaces.json")
    if args.do_consensus:
        key_files.extend(["consensus_scores.csv", "anchors_topN.md"])
    if args.check_harmonics:
        key_files.extend(["hinge_alignment_hist.png", "hinge_alignment_stats.json"])
    if args.fit_law_family:
        key_files.append("law_family.json")
    if args.plot_heatmaps:
        key_files.extend(["residual_heatmap_mass.png", "residual_heatmap_lm.png"])
    if args.export_parquet:
        key_files.append("parquet/catalog.parquet")
        key_files.append("parquet/catalog_export.csv")
    
    for file in key_files:
        file_path = out_dir / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} (not generated)")
    
    print(f"\n💡 To reuse results, run with: --out {out_dir.name} --reuse")

if __name__ == "__main__":
    main()
