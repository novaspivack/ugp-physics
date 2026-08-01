# ugp_discovery_lab/experiments/alpha_changepoint_scan.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment
from ..diagnostics.plotting import fig_changepoints


def _load_runs(globs: List[str]) -> List[Dict[str, Any]]:
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


def _rolling_alpha(kG: np.ndarray, kL: np.ndarray, kM: np.ndarray, win: int = 64, stride: int = 8) -> np.ndarray:
    """Compute rolling alpha estimates."""
    out = []
    i = 0
    n = min(len(kG), len(kL), len(kM))
    while i + win <= n:
        X = np.column_stack([kG[i:i+win], kL[i:i+win], np.ones(win)])
        y = kM[i:i+win]
        a, alpha, c = np.linalg.lstsq(X, y, rcond=None)[0]
        out.append(alpha)
        i += stride
    return np.asarray(out, dtype=float)


def _detect_changepoints(series: np.ndarray, penalty: float = 10.0) -> List[int]:
    """
    Simple change-point detector via binary segmentation on mean shifts.
    For production, you may replace with 'ruptures' library (PELT).
    """
    cps = []
    def _bs(x, start, end):
        if end - start < 16:
            return
        seg = x[start:end]
        n = len(seg)
        best = None
        best_cost = 0.0
        for k in range(start+8, end-8):
            left = x[start:k]; right = x[k:end]
            cost = abs(left.mean() - right.mean()) / (left.std()+right.std()+1e-8)
            if cost > best_cost and cost > penalty:
                best_cost = cost; best = k
        if best is not None:
            cps.append(best)
            _bs(x, start, best)
            _bs(x, best, end)
    _bs(series, 0, len(series))
    cps.sort()
    return cps


@register_experiment("alpha_changepoint_scan")
class AlphaChangePointScan(Experiment):
    """Detect change-points in alpha evolution over time."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "acps"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("alpha_changepoint_scan", (self.root/"results/logs"/"acps.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        win = int(cfg.get("rolling", {}).get("win", 64))
        stride = int(cfg.get("rolling", {}).get("stride", 8))
        penalty = float(cfg.get("penalty", 10.0))

        datasets = _load_runs(inputs)
        figs = []
        all_cps = []

        for d in datasets:
            s = d.get("series", {})
            # Try both "kG,kL,kM" and "G,L,M" formats
            if all(k in s for k in ("kG","kL","kM")):
                kG = np.asarray(s["kG"], dtype=float)
                kL = np.asarray(s["kL"], dtype=float)
                kM = np.asarray(s["kM"], dtype=float)
            elif all(k in s for k in ("G","L","M")):
                kG = np.asarray(s["G"], dtype=float)
                kL = np.asarray(s["L"], dtype=float)
                kM = np.asarray(s["M"], dtype=float)
            else:
                continue
            n = min(len(kG), len(kL), len(kM))
            alphas = _rolling_alpha(kG[:n], kL[:n], kM[:n], win=win, stride=stride)
            if len(alphas) < 8:
                continue
            cps = _detect_changepoints(alphas, penalty=penalty)
            all_cps.append(cps)
            outdir = self.root/"results"/"artifacts"/"alpha_changepoint_scan"
            fig = fig_changepoints(alphas, cps, outdir, "Alpha change-points")
            figs.append(fig)

        return {"task_id": "acps", "changepoints": all_cps, "fig_paths": figs, "status": "ok"}

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        write_json_report(self.root, "alpha_changepoint_scan_summary", results[0] if results else {})
        md = ["# Alpha Change-point Scan — Summary", ""]
        if results:
            r = results[0]
            for i, cps in enumerate(r.get("changepoints", [])):
                md.append(f"- Run {i+1}: cps={cps}")
            for p in r.get("fig_paths", []):
                md.append(f"![changepoints]({p})")
        write_md_report(self.root, "alpha_changepoint_scan_summary", "\n".join(md))
        return results[0] if results else {}
