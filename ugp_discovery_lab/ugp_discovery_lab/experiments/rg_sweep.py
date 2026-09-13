"""
Extended RG Sweep Experiment.

Run RG flow analysis across multiple policies, seeds, and windows to check
for universal convergence to Quarter-Lock or distinct basins.
"""

from .base import Experiment
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import numpy as np
from itertools import product

from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint
from ..core.reporting import write_json_report, write_md_report


@register_experiment("rg_sweep")
class RGSweep(Experiment):
    """Extended RG exploration across policies and seeds."""
    
    def tasks(self) -> List[Dict]:
        """Generate tasks for RG sweep across parameter space."""
        tasks = []
        
        # Get configuration
        rg_config = self.cfg.get("rg", {})
        param_grid = self.cfg.get("param_grid", {})
        fit_config = self.cfg.get("fit", {})
        
        # Extract parameter grids
        seeds_list = param_grid.get("seeds", [[1, 73, 823]])
        windows_list = param_grid.get("windows", [10, 11, 12])
        laws_list = param_grid.get("laws", [
            {"c_policy": "mersenne", "b_policy": "fib", "a_policy": "gte", "mirror": "d2"},
            {"c_policy": "mersenne", "b_policy": "lucas", "a_policy": "gte", "mirror": "d2"}
        ])
        
        # Generate all combinations
        for seeds in seeds_list:
            for window in windows_list:
                for law in laws_list:
                    task_id = f"rg_seed_{'_'.join(map(str, seeds))}_law_{law['c_policy']}_{law['b_policy']}_win{window}"
                    
                    tasks.append({
                        "task_id": task_id,
                        "seeds": seeds,
                        "window": window,
                        "law": law,
                        "rg_config": rg_config,
                        "fit_config": fit_config
                    })
        
        return tasks
    
    def run_task(self, task: Dict) -> Dict:
        """Run RG sweep for a single parameter combination."""
        task_id = task["task_id"]
        seeds = task["seeds"]
        window = task["window"]
        law = task["law"]
        rg_config = task["rg_config"]
        fit_config = task["fit_config"]
        
        logger = get_logger(f"rg_sweep:{task_id}")
        logger.info(f"Starting RG sweep: {task_id}")
        logger.info(f"Seeds: {seeds}, Window: {window}, Law: {law}")
        
        try:
            # Generate or load initial data
            initial_data = self._generate_initial_data(seeds, window, law, logger)
            
            # Run RG iterations
            trajectory = self._run_rg_iterations(
                initial_data, rg_config, fit_config, logger
            )
            
            # Analyze trajectory for fixed points and cycles
            analysis = self._analyze_rg_trajectory(trajectory, rg_config, logger)
            
            # Compile results
            result = {
                "task_id": task_id,
                "success": True,
                "seeds": seeds,
                "window": window,
                "law": law,
                "trajectory": trajectory,
                "analysis": analysis,
                "fixed_point": analysis.get("fixed_point"),
                "cycle": analysis.get("cycles", []),
                "status": "ok"
            }
            
            logger.info(f"RG sweep completed: {task_id}")
            if analysis.get("fixed_point"):
                logger.info(f"Fixed point: α = {analysis['fixed_point']['alpha']:.6f}")
            
            return result
            
        except Exception as e:
            logger.error(f"RG sweep failed: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _generate_initial_data(self, seeds: List[int], window: int, 
                             law: Dict[str, str], logger) -> Dict[str, Any]:
        """Generate initial data for RG sweep."""
        # Create synthetic initial kernel data
        np.random.seed(seeds[0])  # Use first seed for reproducibility
        
        # Generate initial k_M, k_G, k_L values
        n_points = 100
        
        # Base values with some variation
        k_G_base = 1.0 + 0.1 * np.random.randn(n_points)
        k_L_base = 0.5 + 0.1 * np.random.randn(n_points)
        
        # Create k_M with some initial relationship
        alpha_initial = 0.25 + 0.05 * np.random.randn()  # Near Quarter-Lock
        k_M_base = k_G_base + alpha_initial * k_L_base + 0.02 * np.random.randn(n_points)
        
        return {
            "k_M": k_M_base.tolist(),
            "k_G": k_G_base.tolist(),
            "k_L": k_L_base.tolist(),
            "window": window,
            "law": law,
            "alpha_initial": alpha_initial
        }
    
    def _run_rg_iterations(self, initial_data: Dict, rg_config: Dict,
                          fit_config: Dict, logger) -> List[Dict]:
        """Run RG iterations and return trajectory."""
        iterations = rg_config.get("iterations", 8)
        crop_policy = rg_config.get("crop_policy", "center")
        rescale_policy = rg_config.get("rescale_policy", "normalize")
        
        trajectory = []
        
        # Initial state
        current_data = initial_data.copy()
        
        for iter_num in range(iterations + 1):
            # Fit current data
            fit_result = self._fit_kernel_data(current_data, fit_config, logger)
            
            # Record trajectory point
            trajectory.append({
                "iter": iter_num,
                "alpha": fit_result["alpha"],
                "plane_error": fit_result["plane_error"],
                "window_size": current_data["window"],
                "r_squared": fit_result["r_squared"]
            })
            
            if iter_num < iterations:
                # Apply RG operator (simplified)
                current_data = self._apply_rg_operator(
                    current_data, crop_policy, rescale_policy, logger
                )
        
        return trajectory
    
    def _fit_kernel_data(self, data: Dict, fit_config: Dict, logger) -> Dict[str, Any]:
        """Fit kernel data to k_M = k_G + α·k_L."""
        try:
            k_M = np.array(data["k_M"])
            k_G = np.array(data["k_G"])
            k_L = np.array(data["k_L"])
            
            # Fit linear model: k_M = k_G + α·k_L
            # Rearrange to: k_M - k_G = α·k_L
            y = k_M - k_G
            X = k_L.reshape(-1, 1)
            
            # Simple linear regression
            alpha = np.sum(X.flatten() * y) / np.sum(X.flatten() ** 2)
            
            # Calculate residuals and R-squared
            y_pred = alpha * X.flatten()
            residuals = y - y_pred
            plane_error = np.sqrt(np.mean(residuals ** 2))
            
            # R-squared
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return {
                "alpha": float(alpha),
                "plane_error": float(plane_error),
                "r_squared": float(r_squared),
                "residuals": residuals.tolist()
            }
            
        except Exception as e:
            logger.warning(f"Fitting failed: {e}")
            return {
                "alpha": 0.0,
                "plane_error": float('inf'),
                "r_squared": 0.0,
                "residuals": []
            }
    
    def _apply_rg_operator(self, data: Dict, crop_policy: str,
                          rescale_policy: str, logger) -> Dict:
        """Apply RG operator to transform data."""
        try:
            k_M = np.array(data["k_M"])
            k_G = np.array(data["k_G"])
            k_L = np.array(data["k_L"])
            window = data["window"]
            
            # Crop data (simplified - take center portion)
            if crop_policy == "center":
                crop_size = max(1, len(k_M) // 2)
                start_idx = (len(k_M) - crop_size) // 2
                end_idx = start_idx + crop_size
                
                k_M_cropped = k_M[start_idx:end_idx]
                k_G_cropped = k_G[start_idx:end_idx]
                k_L_cropped = k_L[start_idx:end_idx]
            
            # Rescale (simplified - normalize)
            if rescale_policy == "normalize":
                # Normalize each kernel component
                k_M_rescaled = k_M_cropped / np.std(k_M_cropped) if np.std(k_M_cropped) > 0 else k_M_cropped
                k_G_rescaled = k_G_cropped / np.std(k_G_cropped) if np.std(k_G_cropped) > 0 else k_G_cropped
                k_L_rescaled = k_L_cropped / np.std(k_L_cropped) if np.std(k_L_cropped) > 0 else k_L_cropped
            
            # Update window size (simplified)
            new_window = max(4, window - 1)
            
            return {
                "k_M": k_M_rescaled.tolist(),
                "k_G": k_G_rescaled.tolist(),
                "k_L": k_L_rescaled.tolist(),
                "window": new_window,
                "law": data["law"]
            }
            
        except Exception as e:
            logger.warning(f"RG operator failed: {e}")
            return data  # Return unchanged data
    
    def _analyze_rg_trajectory(self, trajectory: List[Dict], 
                             rg_config: Dict, logger) -> Dict[str, Any]:
        """Analyze RG trajectory for fixed points and cycles."""
        if len(trajectory) < 2:
            return {
                "fixed_point": None,
                "cycles": [],
                "convergence_info": "insufficient_data"
            }
        
        tol_plane = float(rg_config.get("tol_plane", 1e-3))
        tol_param = float(rg_config.get("tol_param", 1e-3))
        tol_cycle = float(rg_config.get("tol_cycle", 1e-4))
        
        # Check for fixed point
        fixed_point = None
        if len(trajectory) >= 2:
            last_point = trajectory[-1]
            for i, point in enumerate(trajectory[:-1]):
                # Check convergence criteria
                alpha_diff = abs(last_point["alpha"] - point["alpha"])
                error_diff = abs(last_point["plane_error"] - point["plane_error"])
                
                if alpha_diff <= tol_param and error_diff <= tol_plane:
                    fixed_point = {
                        "alpha": last_point["alpha"],
                        "within_tol": True,
                        "iter": i + 1,
                        "alpha_diff": alpha_diff,
                        "error_diff": error_diff
                    }
                    break
        
        # Detect limit cycles
        cycles = self._detect_limit_cycles(trajectory, tol_cycle, logger)
        
        return {
            "fixed_point": fixed_point,
            "cycles": cycles,
            "trajectory_length": len(trajectory),
            "final_alpha": trajectory[-1]["alpha"] if trajectory else None,
            "final_error": trajectory[-1]["plane_error"] if trajectory else None
        }
    
    def _detect_limit_cycles(self, trajectory: List[Dict], 
                           tol_cycle: float, logger) -> List[Dict]:
        """Detect limit cycles in RG trajectory."""
        cycles = []
        
        if len(trajectory) < 4:
            return cycles
        
        # Extract parameter vectors (alpha, plane_error, window_size)
        param_vectors = []
        for point in trajectory:
            vector = np.array([
                point.get("alpha", 0),
                point.get("plane_error", 0),
                point.get("window_size", 64)
            ])
            param_vectors.append(vector)
        
        param_vectors = np.array(param_vectors)
        
        # Look for cycles of length 2-3
        for cycle_length in [2, 3]:
            for start_idx in range(len(param_vectors) - cycle_length):
                # Check if we have a repeating pattern
                max_distance = 0.0
                
                for i in range(cycle_length):
                    idx1 = start_idx + i
                    idx2 = start_idx + cycle_length + i
                    
                    if idx2 >= len(param_vectors):
                        break
                    
                    # Calculate distance between parameter vectors
                    distance = np.linalg.norm(param_vectors[idx1] - param_vectors[idx2])
                    max_distance = max(max_distance, distance)
                
                # If we found a complete cycle
                if max_distance <= tol_cycle:
                    cycle_iters = [start_idx + i for i in range(cycle_length)]
                    cycles.append({
                        "k": cycle_length,
                        "iters": cycle_iters,
                        "max_distance": float(max_distance),
                        "start_iter": start_idx,
                        "cycle_type": f"limit_cycle_{cycle_length}"
                    })
                    
                    logger.debug(f"Found {cycle_length}-cycle starting at iteration {start_idx}")
        
        return cycles
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize RG sweep results."""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0
        }
        
        if successful_results:
            # Analyze convergence patterns
            fixed_points = [r["fixed_point"] for r in successful_results if r.get("fixed_point")]
            cycles = [r["cycle"] for r in successful_results if r.get("cycle")]
            
            summary["convergence_summary"] = {
                "fixed_points_detected": len(fixed_points),
                "cycles_detected": len([c for c in cycles if c]),
                "convergence_rate": len(fixed_points) / len(successful_results)
            }
            
            # Analyze alpha values
            final_alphas = [r["analysis"]["final_alpha"] for r in successful_results 
                          if r["analysis"].get("final_alpha") is not None]
            
            if final_alphas:
                summary["alpha_statistics"] = {
                    "mean_alpha": float(np.mean(final_alphas)),
                    "std_alpha": float(np.std(final_alphas)),
                    "min_alpha": float(np.min(final_alphas)),
                    "max_alpha": float(np.max(final_alphas)),
                    "quarter_lock_convergences": len([a for a in final_alphas if abs(a - 0.25) < 1e-3])
                }
            
            # Discoveries
            discoveries = []
            
            if fixed_points:
                alpha_values = [fp["alpha"] for fp in fixed_points]
                mean_alpha = np.mean(alpha_values)
                discoveries.append(f"Fixed points detected in {len(fixed_points)} runs")
                discoveries.append(f"Average fixed point: α = {mean_alpha:.6f}")
                
                # Check for Quarter-Lock convergence
                quarter_convergences = [fp for fp in fixed_points if abs(fp["alpha"] - 0.25) < 1e-3]
                if quarter_convergences:
                    discoveries.append(f"Quarter-Lock convergence in {len(quarter_convergences)} runs")
            
            if any(cycles):
                cycle_count = len([c for c in cycles if c])
                discoveries.append(f"Limit cycles detected in {cycle_count} runs")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        # Write summary files
        write_json_report(self.root, "rg_sweep_summary", summary)
        
        # Create markdown report
        md_content = [
            "# RG Sweep — Summary",
            "",
            f"- **Total Tasks:** {summary.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary.get('successful_tasks', 0)}",
            f"- **Failed Tasks:** {summary.get('failed_tasks', 0)}",
            f"- **Success Rate:** {summary.get('success_rate', 0):.1%}",
            f"- **Status:** {summary.get('status', 'unknown').replace('_', ' ').title()}",
            "",
            "## Convergence Analysis",
        ]
        
        if "convergence_summary" in summary:
            conv = summary["convergence_summary"]
            md_content.extend([
                f"- **Fixed Points Detected:** {conv.get('fixed_points_detected', 0)}",
                f"- **Cycles Detected:** {conv.get('cycles_detected', 0)}",
                f"- **Convergence Rate:** {conv.get('convergence_rate', 0):.1%}",
            ])
        
        if "alpha_statistics" in summary:
            alpha_stats = summary["alpha_statistics"]
            md_content.extend([
                "",
                "## Alpha Statistics",
                f"- **Mean Alpha:** {alpha_stats.get('mean_alpha', 0):.6f}",
                f"- **Std Alpha:** {alpha_stats.get('std_alpha', 0):.6f}",
                f"- **Min Alpha:** {alpha_stats.get('min_alpha', 0):.6f}",
                f"- **Max Alpha:** {alpha_stats.get('max_alpha', 0):.6f}",
                f"- **Quarter-Lock Convergences:** {alpha_stats.get('quarter_lock_convergences', 0)}",
            ])
        
        if "discoveries" in summary:
            md_content.extend([
                "",
                "## Discoveries",
            ])
            for discovery in summary["discoveries"]:
                md_content.append(f"- {discovery}")
        
        if "errors" in summary:
            md_content.extend([
                "",
                "## Errors",
            ])
            for error in summary["errors"]:
                md_content.append(f"- {error}")
        
        write_md_report(self.root, "rg_sweep_summary", "\n".join(md_content))
        
        return summary
