# ugp_discovery_lab/experiments/claim_guard.py
"""
Gate any physical constant/analogy claim on alpha unless evidence is complete.
Validates that all three evidence requirements are met before allowing claims.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment


def _load(path: str | Path) -> Dict[str, Any]:
    """Load JSON file safely."""
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


@register_experiment("claim_guard")
class ClaimGuard(Experiment):
    """Gate physical constant claims based on evidence completeness."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "claim_guard"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("claim_guard", (self.root / "results/logs" / "claim_guard.log"))
        cfg = self.cfg
        claim_path = cfg.get("claim_path", "claims/alpha_attractor.json")
        claim = _load(claim_path)
        
        # Evidence paths
        ev = claim.get("evidence", {})
        dc = _load(ev.get("derivation_consistency", "results/reports/derivation_consistency_summary.json"))
        pcv = _load(ev.get("persistence_cv_summary", "results/reports/persistence_cv_summary.json"))
        nulls = _load(ev.get("null_surrogates_summary", "results/reports/null_surrogates_summary.json"))
        
        thresholds = claim.get("thresholds", {
            "consistency_tol": 1e-4,
            "cv_max_delta": 1e-4,
            "null_p_max": 0.01
        })

        # Checks
        ok_dc = (bool(dc) and 
                dc.get("verdict", False) and 
                dc.get("mean_abs_diff", 1e9) <= thresholds["consistency_tol"])
        
        ok_pcv = (bool(pcv) and 
                 pcv.get("verdict", False) and 
                 max((fs.get("delta", 1e9) for fs in pcv.get("fold_stats", [])), default=1e9) <= thresholds["cv_max_delta"])
        
        ok_nulls = bool(nulls) and nulls.get("verdict", False)

        verdict = bool(ok_dc and ok_pcv and ok_nulls)
        status = "ok" if verdict else "blocked"
        
        return {
            "task_id": "claim_guard",
            "claim": claim.get("claim_id", "unknown"),
            "ok_derivations": ok_dc,
            "ok_persistence": ok_pcv,
            "ok_nulls": ok_nulls,
            "thresholds": thresholds,
            "verdict": verdict,
            "status": status
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        r = results[0] if results else {}
        write_json_report(self.root, "claim_guard_summary", r)
        
        md = [
            "# Claim Guard — Summary",
            f"- Claim: {r.get('claim', 'unknown')}",
            f"- Independent derivations: {'PASS' if r.get('ok_derivations') else 'FAIL'}",
            f"- Out-of-sample persistence: {'PASS' if r.get('ok_persistence') else 'FAIL'}",
            f"- Null models: {'PASS' if r.get('ok_nulls') else 'FAIL'}",
            f"- Overall verdict: {'ALLOW' if r.get('verdict') else 'BLOCK'}"
        ]
        
        write_md_report(self.root, "claim_guard_summary", "\n".join(md))
        return r
