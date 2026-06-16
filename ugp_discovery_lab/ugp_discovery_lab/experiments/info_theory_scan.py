# ugp_discovery_lab/experiments/info_theory_scan.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment


def _load_series(globs: List[str]) -> List[Dict[str, Any]]:
    """Load experiment result files from glob patterns."""
    files = []
    for g in globs:
        files.extend(Path().glob(g))
    out = []
    for f in files:
        try:
            out.append(json.loads(Path(f).read_text()))
        except Exception:
            continue
    return out


def _extract_MGL(d: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract M, G, L series from dataset."""
    s = d.get("series", {})
    M = np.asarray(s.get("M", []), dtype=float)
    G = np.asarray(s.get("G", []), dtype=float)
    L = np.asarray(s.get("L", []), dtype=float)
    n = min(len(M), len(G), len(L))
    return M[:n], G[:n], L[:n]


def _hist_mi(x: np.ndarray, y: np.ndarray, bins: int = 16) -> float:
    """Mutual information via histogram estimator with bias correction (Miller–Madow)."""
    H, xedges, yedges = np.histogram2d(x, y, bins=bins)
    px = H.sum(axis=1)
    py = H.sum(axis=0)
    pxy = H
    n = H.sum()
    # avoid zeros
    px = px / (n + 1e-18)
    py = py / (n + 1e-18)
    pxy = pxy / (n + 1e-18)

    # entropies
    def H1(p):
        p = p[p > 0]
        return -np.sum(p * np.log(p + 1e-18))
    def H2(p):
        p = p[p > 0]
        return -np.sum(p * np.log(p + 1e-18))

    Hx = H1(px)
    Hy = H1(py)
    Hxy = H2(pxy.flatten())
    mi = Hx + Hy - Hxy

    # Miller–Madow correction (approx)
    kx = (px > 0).sum()
    ky = (py > 0).sum()
    kxy = (pxy > 0).sum()
    mm = ((kx - 1) * (ky - 1)) / (2.0 * n + 1e-18)
    return float(max(mi - mm, 0.0))


def _transfer_entropy(x: np.ndarray, y: np.ndarray, lag: int = 1, bins: int = 16) -> float:
    """
    Estimate transfer entropy T_{X->Y} using conditional MI with simple discretization:
    T = I(Y_t ; X_{t-τ} | Y_{t-τ})
    """
    if len(x) <= lag or len(y) <= lag:
        return 0.0
    Yt = y[lag:]
    Ylag = y[:-lag]
    Xlag = x[:-lag]
    # compute MI(Yt; Xlag | Ylag) = H(Yt|Ylag) - H(Yt|Xlag,Ylag)
    # Approximate via histogram binning + entropy
    def cond_entropy(a, cond, bins=16):
        # H(a|cond)
        # Joint over (a,cond)
        H_joint, *_ = np.histogram2d(a, cond, bins=bins)
        H_cond = H_joint.sum(axis=0, keepdims=True)
        p_joint = H_joint / (H_joint.sum() + 1e-18)
        p_cond = H_cond / (H_cond.sum() + 1e-18)
        # For nonzero p_joint entries, contribution = -p_joint * log( p_joint / p_cond )
        nz = p_joint > 0
        ratio = np.zeros_like(p_joint) + 1e-18
        ratio[nz] = p_joint[nz] / (p_cond[:, :].T[nz] + 1e-18)
        return float(-np.sum(p_joint[nz] * np.log(ratio[nz] + 1e-18)))

    H_Yt_given_Ylag = cond_entropy(Yt, Ylag, bins=bins)

    # Joint conditioning on (Xlag, Ylag): embed as a single variable via hashing bins
    # First bin Xlag,Ylag:
    # To avoid complex 3D hist, we discretize to ranks and then estimate entropies on pairs
    # (Simple but serviceable for scanning.)
    def rank_bins(v, bins=16):
        r = np.argsort(np.argsort(v))
        # map ranks to bins
        return (r * bins) // (len(v) + 1)

    Xb = rank_bins(Xlag, bins)
    Yb = rank_bins(Ylag, bins)
    # combine into one code
    comb = Xb.astype(int) * (bins) + Yb.astype(int)
    H_Yt_given_XY = cond_entropy(Yt, comb, bins=bins)
    te = H_Yt_given_Ylag - H_Yt_given_XY
    return float(max(te, 0.0))


@register_experiment("info_theory_scan")
class InfoTheoryScan(Experiment):
    """Information-theoretic analysis of UGP dynamics."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "its"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("info_theory_scan", (self.root/"results/logs"/"its.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        bins = int(cfg.get("settings", {}).get("bins", 16))
        max_lag = int(cfg.get("settings", {}).get("max_lag", 3))

        datasets = _load_series(inputs)
        results = []

        for d in datasets:
            M, G, L = _extract_MGL(d)
            if min(len(M), len(G), len(L)) < 32:
                continue
            # Mutual information
            mi_MG = _hist_mi(M, G, bins)
            mi_ML = _hist_mi(M, L, bins)
            mi_GL = _hist_mi(G, L, bins)
            # Transfer entropy for lags 1..max_lag
            te = []
            for lag in range(1, max_lag+1):
                te.append({
                    "lag": lag,
                    "T_M_to_G": _transfer_entropy(M, G, lag, bins),
                    "T_G_to_M": _transfer_entropy(G, M, lag, bins),
                    "T_M_to_L": _transfer_entropy(M, L, lag, bins),
                    "T_L_to_M": _transfer_entropy(L, M, lag, bins),
                    "T_G_to_L": _transfer_entropy(G, L, lag, bins),
                    "T_L_to_G": _transfer_entropy(L, G, lag, bins),
                })
            results.append({
                "mi": {"I(M;G)": mi_MG, "I(M;L)": mi_ML, "I(G;L)": mi_GL},
                "te": te
            })

        return {"task_id": "its", "results": results, "status": "ok"}

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        write_json_report(self.root, "info_theory_scan_summary", results[0] if results else {})
        md = ["# Info-Theory Scan — Summary", ""]
        if results:
            r = results[0]
            for i, block in enumerate(r.get("results", [])):
                md.append(f"## Run {i+1}")
                mi = block.get("mi", {})
                md.append(f"- I(M;G) = {mi.get('I(M;G)',0):.4g}, I(M;L) = {mi.get('I(M;L)',0):.4g}, I(G;L) = {mi.get('I(G;L)',0):.4g}")
                md.append("- Transfer entropy:")
                for te in block.get("te", []):
                    md.append(f"  - lag={te['lag']}: T(M→G)={te['T_M_to_G']:.4g}, T(G→M)={te['T_G_to_M']:.4g}, "
                              f"T(M→L)={te['T_M_to_L']:.4g}, T(L→M)={te['T_L_to_M']:.4g}, T(G→L)={te['T_G_to_L']:.4g}, T(L→G)={te['T_L_to_G']:.4g}")
        write_md_report(self.root, "info_theory_scan_summary", "\n".join(md))
        return results[0] if results else {}
