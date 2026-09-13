"""
holographic_transducer_gte.py — COMP-P04-A
==========================================
Tests the holographic claim in Paper 4 using *genuine GTE trajectory data*
(not synthetic CA data). This replaces / supplements the original
holographic_transducer.py which used Rule-110 CA synthetic data.

Method (per SPEC-P04 COMP-4-A):
  1. Load even-step ("ridge proxy") events from the existing deep-trajectory
     run as bulk states: (a, b, c) at each even step.
  2. Use the c-component alone as the boundary state.
  3. For each trajectory, construct sliding-window feature vectors:
       X[t] = [c(t), c(t-1), …, c(t-W+1)]   (W = window_size)
       y[t] = [a(t), b(t)]                    (bulk to reconstruct)
  4. Train a linear reconstructor on 80 % of samples (per trajectory).
  5. Evaluate R² on the held-out 20 %.
  6. Aggregate across all trajectories; report mean ± std R².

Decision rule (per SPEC-P04):
  R² ≥ 0.90  → holographic claim survives
  R² < 0.50  → holographic claim is removed

Output: ugp_discovery_lab/UGP_discovery_lab_runs/exp_holographic_gte/results/experiment_results.json
"""

from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

try:
    from sklearn.linear_model import Ridge
    from sklearn.metrics import r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEEP_TRAJ_JSON = (
    REPO_ROOT
    / "ugp_discovery_lab"
    / "UGP_discovery_lab_runs"
    / "exp_20260413_deep_trajectories"
    / "results"
    / "reports"
    / "experiment_results.json"
)
OUT_DIR = (
    REPO_ROOT
    / "ugp_discovery_lab"
    / "UGP_discovery_lab_runs"
    / "exp_holographic_gte"
    / "results"
)

WINDOW_SIZE = 20       # number of past c-values used as boundary feature
TRAIN_FRAC  = 0.80     # fraction for training

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _is_ridge_proxy(e: dict) -> bool:
    """Use even-step events as ridge proxies (matching gte_gsl_fit.py convention)."""
    st = e.get("step_type", "")
    if "ridge" in st.lower():
        return True
    return e.get("step", 0) % 2 == 0


def _build_xy(evo: List[dict], window: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build feature matrix X (boundary window) and target matrix y (bulk a,b).
    Selects even-step entries; uses log(|v|+1) encoding to handle scale.
    """
    ridge_events = [e for e in evo if _is_ridge_proxy(e)]
    if len(ridge_events) < window + 2:
        return np.empty((0, window)), np.empty((0, 2))

    # Log-encode to handle large integers
    def lenc(v):
        return math.log(abs(int(v)) + 1)

    c_seq  = np.array([lenc(e["c"]) for e in ridge_events])
    ab_seq = np.array([[lenc(e["a"]), lenc(e["b"])] for e in ridge_events])

    X, y = [], []
    for t in range(window, len(c_seq)):
        X.append(c_seq[t - window : t])   # boundary window
        y.append(ab_seq[t])               # bulk target (a, b)

    return np.array(X), np.array(y)


def _run_one_trajectory(evo: List[dict], basin: str, seed: list,
                        window: int) -> Dict[str, Any]:
    X, y = _build_xy(evo, window)
    if len(X) < 10:
        return {"skip": True, "reason": "too few samples", "basin": basin}

    n_train = max(5, int(len(X) * TRAIN_FRAC))
    X_tr, X_te = X[:n_train], X[n_train:]
    y_tr, y_te = y[:n_train], y[n_train:]

    if len(X_te) < 3:
        return {"skip": True, "reason": "too few test samples", "basin": basin}

    if HAS_SKLEARN:
        reg = Ridge(alpha=1e-3, fit_intercept=True)
        reg.fit(X_tr, y_tr)
        y_pred = reg.predict(X_te)
        r2 = float(r2_score(y_te, y_pred))
        # Component-level R²
        r2_a = float(r2_score(y_te[:, 0], y_pred[:, 0]))
        r2_b = float(r2_score(y_te[:, 1], y_pred[:, 1]))
    else:
        # Fallback: manual least-squares
        X_tr_aug = np.hstack([X_tr, np.ones((len(X_tr), 1))])
        X_te_aug = np.hstack([X_te, np.ones((len(X_te), 1))])
        W, _, _, _ = np.linalg.lstsq(X_tr_aug, y_tr, rcond=None)
        y_pred = X_te_aug @ W
        ss_res = ((y_te - y_pred) ** 2).sum()
        ss_tot = ((y_te - y_te.mean(axis=0)) ** 2).sum()
        r2 = float(1 - ss_res / (ss_tot + 1e-12))
        r2_a = r2_b = float("nan")

    return {
        "skip": False,
        "basin": basin,
        "seed": seed,
        "n_samples": len(X),
        "n_train": n_train,
        "n_test": len(X_te),
        "r2_combined": r2,
        "r2_a": r2_a,
        "r2_b": r2_b,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"COMP-P04-A: Holographic transducer test on GTE data")
    print(f"Loading: {DEEP_TRAJ_JSON}")

    if not DEEP_TRAJ_JSON.exists():
        raise FileNotFoundError(
            f"Deep trajectory data not found at:\n  {DEEP_TRAJ_JSON}\n"
            "Run the gte_deep_trajectories experiment first."
        )

    raw = json.loads(DEEP_TRAJ_JSON.read_text())
    results_list = raw.get("data", raw).get("results", [])
    print(f"  {len(results_list)} trajectory entries found.")

    per_traj = []
    for entry in results_list:
        if not entry.get("success", True):
            continue
        evo   = entry.get("evolution_history", [])
        basin = entry.get("basin", "?")
        seed  = entry.get("seed", [])
        res   = _run_one_trajectory(evo, basin, seed, WINDOW_SIZE)
        per_traj.append(res)
        if not res.get("skip"):
            print(f"  seed={seed}  basin={basin}  R²={res['r2_combined']:.4f}  "
                  f"(a: {res['r2_a']:.4f}, b: {res['r2_b']:.4f})")
        else:
            print(f"  seed={seed}  basin={basin}  SKIPPED: {res['reason']}")

    valid = [r for r in per_traj if not r.get("skip")]
    if not valid:
        print("ERROR: no valid trajectories produced results.")
        return

    r2_values = [r["r2_combined"] for r in valid]
    mean_r2 = float(np.mean(r2_values))
    std_r2  = float(np.std(r2_values))
    min_r2  = float(np.min(r2_values))
    max_r2  = float(np.max(r2_values))

    # Basin-level breakdown
    basin_r2: Dict[str, List[float]] = {}
    for r in valid:
        b = r["basin"]
        basin_r2.setdefault(b, []).append(r["r2_combined"])
    basin_summary = {b: {"mean": float(np.mean(vs)), "std": float(np.std(vs)), "n": len(vs)}
                     for b, vs in basin_r2.items()}

    # Decision
    if mean_r2 >= 0.90:
        claim = "SURVIVES"
        verdict = (
            f"Holographic reconstruction of GTE bulk from GTE boundary achieves "
            f"R² = {mean_r2:.4f} ± {std_r2:.4f}. Per NEMS Paper 48's H2-holography "
            f"taxonomy, this constitutes boundary-determines-world-type holography "
            f"within the GTE framework."
        )
    elif mean_r2 >= 0.50:
        claim = "BORDERLINE"
        verdict = (
            f"GTE bulk reconstruction from boundary achieves R² = {mean_r2:.4f} ± "
            f"{std_r2:.4f}. This is above the removal threshold (0.50) but below "
            f"the strong holographic threshold (0.90). Report as 'Preliminary "
            f"Holographic Consistency Test' with non-linear reconstructor as future work."
        )
    else:
        claim = "REMOVED"
        verdict = (
            f"GTE bulk reconstruction from boundary achieves R² = {mean_r2:.4f} ± "
            f"{std_r2:.4f}, insufficient for a holographic claim. The holographic "
            f"section should be relabeled 'Attempted Holographic Test' and results "
            f"reported for completeness."
        )

    output = {
        "experiment": "COMP-P04-A: holographic_transducer_gte",
        "date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_size": WINDOW_SIZE,
        "train_fraction": TRAIN_FRAC,
        "n_trajectories_tested": len(valid),
        "r2_mean": mean_r2,
        "r2_std": std_r2,
        "r2_min": min_r2,
        "r2_max": max_r2,
        "basin_summary": basin_summary,
        "holographic_claim": claim,
        "verdict": verdict,
        "per_trajectory": valid,
        "source_data": str(DEEP_TRAJ_JSON),
    }

    # SHA-256
    payload = json.dumps(output, sort_keys=True).encode()
    output["sha256"] = hashlib.sha256(payload).hexdigest()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "experiment_results.json"
    out_path.write_text(json.dumps(output, indent=2))

    print(f"\n{'='*60}")
    print(f"RESULT: {claim}")
    print(f"Mean R²: {mean_r2:.4f} ± {std_r2:.4f}  (range [{min_r2:.4f}, {max_r2:.4f}])")
    print(f"Basin breakdown: {basin_summary}")
    print(f"Verdict: {verdict}")
    print(f"\nOutput written to: {out_path}")
    print(f"SHA-256: {output['sha256']}")


if __name__ == "__main__":
    main()
