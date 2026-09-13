# ugp_discovery_lab/experiments/rg_long_cycles.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import json
import numpy as np

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment
from ..diagnostics.plotting import fig_rg_trajectories


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


def _detect_cycles(alpha_series: List[float], max_cycle_length: int = 10, 
                   tolerance: float = 1e-6) -> List[Dict[str, Any]]:
    """
    Detect cycles in alpha series using pairwise distance comparison.
    
    Args:
        alpha_series: List of alpha values
        max_cycle_length: Maximum cycle length to detect
        tolerance: Distance tolerance for cycle detection
    
    Returns:
        List of detected cycles with metadata
    """
    n = len(alpha_series)
    if n < 4:
        return []
    
    cycles = []
    alpha_array = np.array(alpha_series)
    
    # Check for cycles of length 2 to max_cycle_length
    for cycle_len in range(2, min(max_cycle_length + 1, n // 2)):
        # Compare each position with position + cycle_len
        distances = []
        for i in range(n - cycle_len):
            dist = abs(alpha_array[i] - alpha_array[i + cycle_len])
            distances.append(dist)
        
        # Find positions where cycle is maintained
        cycle_positions = []
        for i, dist in enumerate(distances):
            if dist <= tolerance:
                cycle_positions.append(i)
        
        # Check for sustained cycles (at least 3 consecutive positions)
        if len(cycle_positions) >= 3:
            # Find longest consecutive sequence
            consecutive_cycles = []
            current_cycle = [cycle_positions[0]]
            
            for i in range(1, len(cycle_positions)):
                if cycle_positions[i] == cycle_positions[i-1] + 1:
                    current_cycle.append(cycle_positions[i])
                else:
                    if len(current_cycle) >= 3:
                        consecutive_cycles.append(current_cycle)
                    current_cycle = [cycle_positions[i]]
            
            if len(current_cycle) >= 3:
                consecutive_cycles.append(current_cycle)
            
            # Record the best cycle for this length
            if consecutive_cycles:
                best_cycle = max(consecutive_cycles, key=len)
                cycles.append({
                    "cycle_length": cycle_len,
                    "start_iteration": best_cycle[0],
                    "end_iteration": best_cycle[-1],
                    "cycle_iterations": len(best_cycle),
                    "max_distance": max(distances[best_cycle[0]:best_cycle[-1]+1]),
                    "mean_distance": np.mean([distances[i] for i in best_cycle]),
                    "alpha_values": [alpha_series[i] for i in best_cycle]
                })
    
    return cycles


@register_experiment("rg_long_cycles")
class RGLongCycles(Experiment):
    """Detect long cycles in RG flow trajectories."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        cfg = self.cfg
        max_cycle_length = int(cfg.get("detection", {}).get("max_cycle_length", 20))
        tolerance = float(cfg.get("detection", {}).get("tolerance", 1e-6))
        
        return [{
            "task_id": "rg_long_cycles",
            "max_cycle_length": max_cycle_length,
            "tolerance": tolerance
        }]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger(f"rg_long_cycles:{task['task_id']}", 
                          (self.root/"results/logs"/f"{task['task_id']}.log"))
        
        inputs = self.cfg.get("inputs", {}).get("runs", [])
        datasets = _load_runs(inputs)
        
        max_cycle_length = task["max_cycle_length"]
        tolerance = task["tolerance"]
        
        all_cycles = []
        trajectory_data = []
        fig_paths = []
        
        logger.info(f"Analyzing {len(datasets)} datasets for cycles up to length {max_cycle_length}")
        
        for i, dataset in enumerate(datasets):
            # Check if this is a summary file with results array
            if "data" in dataset and "results" in dataset["data"]:
                # Process each result in the results array
                results = dataset["data"]["results"]
                for j, result in enumerate(results):
                    alpha_series = None
                    
                    # Try different possible locations for alpha data
                    if "trajectory" in result and result["trajectory"]:
                        alpha_series = [point.get("alpha", 0) for point in result["trajectory"]]
                    elif "analysis" in result and "rg_trajectory" in result["analysis"]:
                        trajectory = result["analysis"]["rg_trajectory"]
                        alpha_series = [point.get("alpha", 0) for point in trajectory]
                    elif "rg_results" in result:
                        alpha_series = [res.get("alpha", 0) for res in result["rg_results"]]
                    elif "alpha_series" in result:
                        alpha_series = result["alpha_series"]
                    elif "series" in result and "alpha" in result["series"]:
                        alpha_series = result["series"]["alpha"]
                    
                    if alpha_series is None or len(alpha_series) < 10:
                        logger.warning(f"Dataset {i}, Result {j}: No valid alpha series found")
                        continue
                    
                    # Process this alpha series
                    cycles = _detect_cycles(alpha_series, max_cycle_length, tolerance)
                    if cycles:
                        all_cycles.extend(cycles)
                        trajectory_data.append({
                            "dataset_id": i,
                            "result_id": j,
                            "alpha_series": alpha_series,
                            "cycles": cycles
                        })
            else:
                # Handle single result format (legacy)
                alpha_series = None
                
                # Try different possible locations for alpha data
                if "trajectory" in dataset and dataset["trajectory"]:
                    alpha_series = [point.get("alpha", 0) for point in dataset["trajectory"]]
                elif "analysis" in dataset and "rg_trajectory" in dataset["analysis"]:
                    trajectory = dataset["analysis"]["rg_trajectory"]
                    alpha_series = [point.get("alpha", 0) for point in trajectory]
                elif "rg_results" in dataset:
                    alpha_series = [result.get("alpha", 0) for result in dataset["rg_results"]]
                elif "alpha_series" in dataset:
                    alpha_series = dataset["alpha_series"]
                elif "series" in dataset and "alpha" in dataset["series"]:
                    alpha_series = dataset["series"]["alpha"]
                
                if alpha_series is None or len(alpha_series) < 10:
                    logger.warning(f"Dataset {i}: No valid alpha series found")
                    continue
                
                # Process this alpha series
                cycles = _detect_cycles(alpha_series, max_cycle_length, tolerance)
                if cycles:
                    all_cycles.extend(cycles)
                    trajectory_data.append({
                        "dataset_id": i,
                        "result_id": 0,
                        "alpha_series": alpha_series,
                        "cycles": cycles
                    })
        
        # Create trajectory plots if we have data
        if trajectory_data:
            outdir = self.root / "results" / "artifacts" / "rg_long_cycles"
            fig_paths = fig_rg_trajectories(trajectory_data, outdir, "RG Long Cycle Detection")
        
        # Sort cycles by cycle length and stability
        all_cycles.sort(key=lambda c: (c["cycle_length"], -c["cycle_iterations"]))
        
        return {
            "task_id": task["task_id"],
            "n_datasets_analyzed": len(datasets),
            "n_cycles_found": len(all_cycles),
            "cycles": all_cycles,
            "trajectory_data": trajectory_data,
            "fig_paths": fig_paths,
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {"experiment": "rg_long_cycles", "status": "no_results"}
        
        result = results[0]  # Single task
        summary = {
            "experiment": "rg_long_cycles",
            "n_datasets_analyzed": result.get("n_datasets_analyzed", 0),
            "n_cycles_found": result.get("n_cycles_found", 0),
            "cycles": result.get("cycles", []),
            "fig_paths": result.get("fig_paths", [])
        }
        
        write_json_report(self.root, "rg_long_cycles_summary", summary)
        
        # Build MD report
        md_lines = [
            "# RG Long Cycle Detection — Summary",
            "",
            f"- Datasets analyzed: {summary['n_datasets_analyzed']}",
            f"- Cycles found: {summary['n_cycles_found']}",
            ""
        ]
        
        if summary["cycles"]:
            md_lines.append("## Detected Cycles")
            md_lines.append("")
            
            for cycle in summary["cycles"][:10]:  # Show top 10
                md_lines.extend([
                    f"### Cycle Length {cycle['cycle_length']}",
                    f"- Dataset: {cycle['dataset_id']}",
                    f"- Iterations: {cycle['start_iteration']}-{cycle['end_iteration']}",
                    f"- Duration: {cycle['cycle_iterations']} steps",
                    f"- Max distance: {cycle['max_distance']:.2e}",
                    f"- Mean distance: {cycle['mean_distance']:.2e}",
                    ""
                ])
        
        if summary["fig_paths"]:
            md_lines.append("## Figures")
            md_lines.append("")
            for path in summary["fig_paths"]:
                md_lines.append(f"![RG Trajectories]({path})")
        
        write_md_report(self.root, "rg_long_cycles_summary", "\n".join(md_lines))
        return summary
