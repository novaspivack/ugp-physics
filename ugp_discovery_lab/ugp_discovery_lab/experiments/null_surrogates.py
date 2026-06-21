# ugp_discovery_lab/experiments/null_surrogates.py
"""
Strict null model tests for alpha effects.
Tests permutation, circular shift, and AAFT surrogates.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment
from ..diagnostics.stats import empirical_pvalue, bh_fdr


def _load_series(globs: List[str]) -> List[Dict[str, Any]]:
    """Load series data from glob patterns."""
    files = []
    out = []
    for g in globs:
        files.extend(Path().glob(g))
    
    for f in files:
        try:
            out.append(json.loads(Path(f).read_text()))
        except Exception:
            pass
    return out


def _extract_alpha_obs(d: Dict[str, Any]) -> float | None:
    """Extract observed alpha value from dataset."""
    for item in d.get("results", []):
        traj = item.get("trajectory", [])
        if traj:
            return float(traj[-1].get("alpha", np.nan))
    return None


def _circular_shift(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Circular shift preserving phase structure."""
    if len(x) < 2:
        return x.copy()
    k = int(rng.integers(0, len(x)))
    return np.roll(x, k)


def _aaft_surrogate(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Amplitude-Adjusted Fourier Transform surrogate.
    Simple AAFT: rank-match white noise to x, Fourier-phase randomize, rank-match back.
    """
    y = rng.standard_normal(len(x))
    xranks = x.argsort().argsort()
    y_sorted = np.sort(y)
    y1 = y_sorted[xranks]  # match amplitude
    Y = np.fft.rfft(y1)
    phases = rng.uniform(0, 2*np.pi, size=len(Y))
    Y2 = np.abs(Y) * np.exp(1j * phases)
    y2 = np.fft.irfft(Y2, n=len(x))
    
    # Rank-match back to x's amplitude
    y2_sorted = np.sort(y2)
    ranks = y2.argsort().argsort()
    x_sorted = np.sort(x)
    return x_sorted[ranks]


@register_experiment("null_surrogates")
class NullSurrogates(Experiment):
    """Test alpha effects against strict null models."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "nulls"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("null_surrogates", (self.root / "results/logs" / "nulls.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        n_perm = int(cfg.get("tests", {}).get("n_perm", 500))
        p_thresh = float(cfg.get("tests", {}).get("p_thresh", 0.01))
        rng = np.random.default_rng(20250917)
        
        datasets = _load_series(inputs)
        effects = []
        pvals = []
        
        for d in datasets:
            alpha_obs = _extract_alpha_obs(d)
            if alpha_obs is None or not np.isfinite(alpha_obs):
                continue
            
            # Build nulls
            null_perm = []
            null_shift = []
            null_aaft = []
            
            x = np.array([t.get("alpha", np.nan) for t in d.get("results", [{}])[0].get("trajectory", [])], dtype=float)
            x = x[np.isfinite(x)]
            if len(x) < 8:
                continue
            
            for _ in range(n_perm):
                # Permutation null: shuffle
                xp = rng.permutation(x)
                null_perm.append(float(xp[-1]))
                
                # Circular shift null
                xs = _circular_shift(x, rng)
                null_shift.append(float(xs[-1]))
                
                # AAFT null
                xa = _aaft_surrogate(x, rng)
                null_aaft.append(float(xa[-1]))
            
            # P-values
            p_perm = empirical_pvalue(alpha_obs, np.array(null_perm))
            p_shift = empirical_pvalue(alpha_obs, np.array(null_shift))
            p_aaft = empirical_pvalue(alpha_obs, np.array(null_aaft))
            
            effects.append({
                "alpha_obs": float(alpha_obs),
                "p_perm": p_perm,
                "p_shift": p_shift,
                "p_aaft": p_aaft
            })
            pvals += [p_perm, p_shift, p_aaft]

        # FDR correction across all tests
        rej, p_adj = bh_fdr(np.array(pvals), alpha=p_thresh) if pvals else ([], [])
        verdict = bool(pvals) and all(rej)
        
        return {
            "task_id": "nulls",
            "effects": effects,
            "pvals_raw": pvals,
            "p_thresh": p_thresh,
            "verdict": verdict,
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        r = results[0] if results else {}
        write_json_report(self.root, "null_surrogates_summary", r)
        
        md = [
            "# Null Surrogates — Summary",
            f"- p_thresh: {r.get('p_thresh')}",
            f"- Verdict: {'PASS' if r.get('verdict') else 'FAIL'}"
        ]
        
        for e in r.get("effects", []):
            md.append(f"- alpha_obs={e['alpha_obs']:.6g}, p_perm={e['p_perm']:.3g}, p_shift={e['p_shift']:.3g}, p_aaft={e['p_aaft']:.3g}")
        
        write_md_report(self.root, "null_surrogates_summary", "\n".join(md))
        return r
