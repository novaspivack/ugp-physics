# ugp_discovery_lab/experiments/persistence_cv.py
"""
Out-of-sample persistence test with K-fold cross-validation.
Tests if alpha estimates are stable across different data splits.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import numpy as np
import random

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment
from ..diagnostics.stats import bootstrap_ci


def _load_alphas(globs: List[str]) -> List[Dict[str, Any]]:
    """Load alpha data from glob patterns."""
    files = []
    for g in globs:
        files.extend(Path().glob(g))
    
    out = []
    for f in files:
        try:
            out.append(json.loads(Path(f).read_text()))
        except Exception:
            pass
    return out


def _extract_records(d: Dict[str, Any]) -> List[Tuple[str, int, str, float]]:
    """Extract alpha records. Returns list of (seed, window, policy, alpha)."""
    rec = []
    for item in d.get("results", []):
        meta = item.get("meta", {})
        seed = str(meta.get("seed", "?"))
        window = int(meta.get("window", -1))
        policy = str(meta.get("policy", "?"))
        s = item.get("trajectory", [])
        if s:
            alpha = float(s[-1].get("alpha", np.nan))
            if np.isfinite(alpha):
                rec.append((seed, window, policy, alpha))
    return rec


@register_experiment("persistence_cv")
class PersistenceCV(Experiment):
    """Test out-of-sample persistence of alpha with K-fold cross-validation."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "pcv"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("persistence_cv", (self.root / "results/logs" / "pcv.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        K = int(cfg.get("cv", {}).get("K", 5))
        cv_max_delta = float(cfg.get("cv", {}).get("cv_max_delta", 1e-4))
        rng = random.Random(12345)

        datasets = _load_alphas(inputs)
        recs = []
        for d in datasets:
            recs += _extract_records(d)
        
        if len(recs) < K:
            return {"task_id": "pcv", "status": "insufficient_data", "n": len(recs)}

        # Make folds by hashing (seed, window, policy)
        keys = list({(s, w, p) for (s, w, p, a) in recs})
        rng.shuffle(keys)
        folds = [keys[i::K] for i in range(K)]

        fold_stats = []
        for k in range(K):
            test_keys = set(folds[k])
            train = [a for (s, w, p, a) in recs if (s, w, p) not in test_keys]
            test = [a for (s, w, p, a) in recs if (s, w, p) in test_keys]
            
            if not train or not test:
                continue
            
            mu_train = np.mean(train)
            mu_test = np.mean(test)
            delta = abs(mu_train - mu_test)
            ci_train = bootstrap_ci(np.array(train), n_boot=1000, agg="mean")
            ci_test = bootstrap_ci(np.array(test), n_boot=1000, agg="mean")
            
            fold_stats.append({
                "fold": k,
                "mu_train": float(mu_train),
                "mu_test": float(mu_test),
                "delta": float(delta),
                "ci_train": ci_train,
                "ci_test": ci_test
            })
        
        # Success criterion
        ok = (fold_stats and max(fs["delta"] for fs in fold_stats) <= cv_max_delta)
        
        return {
            "task_id": "pcv",
            "fold_stats": fold_stats,
            "cv_max_delta": cv_max_delta,
            "verdict": ok,
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        r = results[0] if results else {}
        write_json_report(self.root, "persistence_cv_summary", r)
        
        lines = [
            "# Persistence CV — Summary",
            f"- cv_max_delta: {r.get('cv_max_delta')}",
            f"- Verdict: {'PASS' if r.get('verdict') else 'FAIL'}",
            ""
        ]
        
        for fs in r.get("fold_stats", []):
            lines.append(f"## Fold {fs['fold']}")
            lines.append(f"- mu_train={fs['mu_train']:.6g} (CI={fs['ci_train']})")
            lines.append(f"- mu_test ={fs['mu_test']:.6g} (CI={fs['ci_test']})")
            lines.append(f"- delta={fs['delta']:.6g}")
        
        write_md_report(self.root, "persistence_cv_summary", "\n".join(lines))
        return r
