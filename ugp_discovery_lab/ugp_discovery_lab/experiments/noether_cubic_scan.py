# ugp_discovery_lab/experiments/noether_cubic_scan.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import itertools
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment
from ..diagnostics.plotting import fig_noether_dJ_series


def _load_runs(run_globs: List[str]) -> List[Dict[str, Any]]:
    """Load experiment result files from glob patterns."""
    files = []
    for g in run_globs:
        files.extend(Path().glob(g))
    datasets = []
    for f in files:
        try:
            data = json.loads(Path(f).read_text())
            datasets.append(data)
        except Exception:
            continue
    return datasets


def _extract_series(dataset: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract M, G, L series from dataset."""
    # Expect dataset to contain "series": {"M": [...], "G":[...], "L":[...]} or similar
    # Fallback: try keys in common outputs
    s = dataset.get("series", {})
    if s and all(k in s for k in ("M","G","L")):
        M = np.asarray(s["M"], dtype=float)
        G = np.asarray(s["G"], dtype=float)
        L = np.asarray(s["L"], dtype=float)
        n = min(len(M), len(G), len(L))
        return M[:n], G[:n], L[:n]
    
    # Fallback: scan for plausible keys
    for k in dataset.keys():
        if isinstance(dataset[k], dict) and all(x in dataset[k] for x in ("M","G","L")):
            M = np.asarray(dataset[k]["M"], dtype=float)
            G = np.asarray(dataset[k]["G"], dtype=float)
            L = np.asarray(dataset[k]["L"], dtype=float)
            n = min(len(M), len(G), len(L))
            return M[:n], G[:n], L[:n]
    
    # If not found, return empty
    return np.array([]), np.array([]), np.array([])


@register_experiment("noether_cubic_scan")
class NoetherCubicScan(Experiment):
    """Search for cubic Noether currents in UGP data."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        cfg = self.cfg
        max_combos_per_task = int(cfg.get("search", {}).get("max_combos_per_task", 1000))
        
        # Calculate total combinations - limit to reduce system load
        coeff_grid = cfg.get("search", {}).get("coeff_grid", [-1, 0, 1])
        # Limit exponents to reduce total combinations
        exps = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if (i+j+k) > 0 and (i+j+k) <= 3]
        total_combos = len(coeff_grid) ** len(exps)
        
        # Create chunks
        n_chunks = max(1, (total_combos + max_combos_per_task - 1) // max_combos_per_task)
        return [{"task_id": f"cubic_chunk_{i}", "chunk_id": i, "n_chunks": n_chunks, "max_combos": max_combos_per_task} for i in range(n_chunks)]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger(f"noether_cubic_scan:{task['task_id']}", 
                          (self.root/"results/logs"/f"{task['task_id']}.log"))
        
        inputs = self.cfg.get("inputs", {}).get("runs", [])
        datasets = _load_runs(inputs)
        coeff_grid = self.cfg.get("search", {}).get("coeff_grid", [-1, 0, 1])
        tolerance_abs = float(self.cfg.get("search", {}).get("tolerance_abs", 1e-8))
        sample_fraction = float(self.cfg.get("search", {}).get("sample_fraction", 0.3))
        max_hits = int(self.cfg.get("search", {}).get("max_hits", 10))
        
        # Chunking parameters
        chunk_id = task.get("chunk_id", 0)
        n_chunks = task.get("n_chunks", 1)
        max_combos = task.get("max_combos", 1000)

        hits: List[Dict[str, Any]] = []
        series_plots: List[str] = []

        # Enumerate cubic coefficients a_ijk for i+j+k<=3
        # Represent J = sum_{i+j+k<=3} c_{ijk} * M^i G^j L^k, ignoring constant term
        exps = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) 
                if (i+j+k) > 0 and (i+j+k) <= 3]
        
        # Generate all combinations and chunk them
        all_combos = list(itertools.product(coeff_grid, repeat=len(exps)))
        start_idx = chunk_id * max_combos
        end_idx = min((chunk_id + 1) * max_combos, len(all_combos))
        combos = all_combos[start_idx:end_idx]

        logger.info(f"Chunk {chunk_id}/{n_chunks}: Processing {len(combos)} cubic candidates (indices {start_idx}-{end_idx-1}) with grid {coeff_grid} over {len(exps)} terms.")

        for data in datasets:
            M, G, L = _extract_series(data)
            if M.size == 0:
                continue
            
            n = len(M)
            idx = np.arange(n)
            if n > 0 and sample_fraction < 1.0:
                rng = np.random.default_rng(12345)
                mask = rng.choice(idx, size=max(4, int(sample_fraction * n)), replace=False)
                mask.sort()
            else:
                mask = idx
            
            # Prepare monomials
            monos = []
            for (i,j,k) in exps:
                monos.append((M**i)*(G**j)*(L**k))
            monos = np.stack([m for m in monos], axis=1)  # n x T

            for cvec in combos:
                c = np.asarray(cvec, dtype=float).reshape(-1, 1)  # T x 1
                J = (monos @ c).ravel()  # length n
                dJ = np.diff(J)  # ΔJ
                max_abs = float(np.max(np.abs(dJ[mask[:-1]]))) if len(mask) > 1 else float(np.max(np.abs(dJ)))
                mean_abs = float(np.mean(np.abs(dJ)))
                std_abs = float(np.std(dJ))
                
                if max_abs <= tolerance_abs:
                    hits.append({
                        "coeffs": {str(exps[t]): int(cvec[t]) for t in range(len(exps))},
                        "max_abs_dJ": max_abs,
                        "mean_abs_dJ": mean_abs,
                        "std_dJ": std_abs,
                        "n_evals": int(len(dJ)),
                    })
                    
                    # Save a ΔJ series plot for the first few
                    if len(series_plots) < 5:
                        outdir = self.root / "results" / "artifacts" / "noether_cubic_scan"
                        p_list = fig_noether_dJ_series(dJ, outdir, "Cubic Noether ΔJ")
                        series_plots.extend(p_list)

        hits.sort(key=lambda h: (h["max_abs_dJ"], h["mean_abs_dJ"]))
        
        return {
            "task_id": task["task_id"],
            "chunk_id": chunk_id,
            "n_chunks": n_chunks,
            "n_candidates_tested": len(combos),
            "n_hits": len(hits),
            "top_hits": hits[:max_hits],
            "fig_paths": series_plots,
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = {
            "experiment": "noether_cubic_scan",
            "n_tasks": len(results),
            "total_candidates": int(sum(r.get("n_candidates_tested", 0) for r in results)),
            "total_hits": int(sum(r.get("n_hits", 0) for r in results)),
            "examples": [r.get("top_hits", []) for r in results][:1],
            "figs": sum((r.get("fig_paths", []) for r in results), []),
        }
        
        write_json_report(self.root, "noether_cubic_scan_summary", summary)

        # Build MD
        md = ["# Noether Cubic Scan — Summary", "", 
              f"- Total candidates tested: {summary['total_candidates']}",
              f"- Total hits: {summary['total_hits']}", ""]
        
        if summary["figs"]:
            md.append("## Figures")
            for p in summary["figs"]:
                md.append(f"![ΔJ series]({p})")
        
        write_md_report(self.root, "noether_cubic_scan_summary", "\n".join(md))
        return summary
