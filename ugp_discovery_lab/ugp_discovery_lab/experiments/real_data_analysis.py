"""
Real Data Analysis Experiment

This experiment analyzes existing experiment results to validate
the integrity system with real UGP data in analysis-only mode.
"""

from typing import List, Dict, Any
import json
import numpy as np
from pathlib import Path
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..experiments.base import Experiment


@register_experiment("real_data_analysis")
class RealDataAnalysis(Experiment):
    """Analyze real UGP experiment results in analysis-only mode."""
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for real data analysis."""
        tasks = []
        
        # Get input files from configuration
        inputs = self.cfg.get("inputs", {})
        runs = inputs.get("runs", [])
        
        if not runs:
            raise ValueError("No input runs specified for real data analysis")
        
        # Create tasks for each input file
        for i, run_path in enumerate(runs):
            tasks.append({
                "task_id": f"real_data_analysis_{i}",
                "run_path": run_path,
                "analysis_type": "quarterlock_validation"
            })
        
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single real data file."""
        task_id = task["task_id"]
        run_path = task["run_path"]
        analysis_type = task["analysis_type"]
        
        logger = get_logger(f"real_data_analysis:{task_id}")
        logger.info(f"Analyzing real data: {run_path}")
        
        try:
            # Read the experiment results file
            results_path = Path(run_path)
            if not results_path.exists():
                raise FileNotFoundError(f"Results file not found: {run_path}")
            
            with open(results_path, 'r') as f:
                data = json.load(f)
            
            # Extract results from the experiment data
            results = data.get("data", {}).get("results", [])
            
            if not results:
                raise ValueError("No results found in experiment data")
            
            # Analyze the results based on experiment type
            analysis_results = self._analyze_results(results, analysis_type, logger)
            
            return {
                "task_id": task_id,
                "run_path": str(run_path),
                "analysis_type": analysis_type,
                "status": "success",
                "analysis_results": analysis_results,
                "data_origin": {
                    "type": "real",
                    "source": "experiment_results",
                    "file": str(run_path),
                    "experiment_name": data.get("data", {}).get("experiment_name", "unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"Real data analysis failed: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
    
    def _analyze_results(self, results: List[Dict], analysis_type: str, logger) -> Dict[str, Any]:
        """Analyze results based on the analysis type."""
        
        if analysis_type == "quarterlock_validation":
            return self._analyze_quarterlock_results(results, logger)
        else:
            return {"analysis_type": analysis_type, "message": "Unknown analysis type"}
    
    def _analyze_quarterlock_results(self, results: List[Dict], logger) -> Dict[str, Any]:
        """Analyze Quarter-Lock results from real data."""
        
        alpha_values = []
        confidence_intervals = []
        r_squared_values = []
        
        for result in results:
            if result.get("success", False):
                fit_result = result.get("fit_result", {})
                if fit_result:
                    alpha = fit_result.get("alpha")
                    ci = fit_result.get("confidence_interval", [])
                    r2 = fit_result.get("r_squared")
                    
                    if alpha is not None:
                        alpha_values.append(alpha)
                        confidence_intervals.append(ci)
                        if r2 is not None:
                            r_squared_values.append(r2)
        
        if not alpha_values:
            return {"error": "No valid alpha values found in results"}
        
        # Calculate statistics
        alpha_mean = np.mean(alpha_values)
        alpha_std = np.std(alpha_values)
        alpha_min = np.min(alpha_values)
        alpha_max = np.max(alpha_values)
        
        # Check against theoretical value
        theoretical_alpha = 0.25
        error_from_theoretical = abs(alpha_mean - theoretical_alpha)
        
        # Calculate confidence intervals
        ci_lower = [ci[0] for ci in confidence_intervals if len(ci) >= 2]
        ci_upper = [ci[1] for ci in confidence_intervals if len(ci) >= 2]
        
        analysis = {
            "n_results": len(results),
            "n_valid_alpha": len(alpha_values),
            "alpha_statistics": {
                "mean": float(alpha_mean),
                "std": float(alpha_std),
                "min": float(alpha_min),
                "max": float(alpha_max)
            },
            "theoretical_comparison": {
                "theoretical_alpha": theoretical_alpha,
                "error_from_theoretical": float(error_from_theoretical),
                "relative_error": float(error_from_theoretical / theoretical_alpha)
            },
            "confidence_intervals": {
                "mean_lower": float(np.mean(ci_lower)) if ci_lower else None,
                "mean_upper": float(np.mean(ci_upper)) if ci_upper else None
            },
            "r_squared": {
                "mean": float(np.mean(r_squared_values)) if r_squared_values else None,
                "min": float(np.min(r_squared_values)) if r_squared_values else None,
                "max": float(np.max(r_squared_values)) if r_squared_values else None
            }
        }
        
        logger.info(f"Quarter-Lock analysis: α = {alpha_mean:.6f} ± {alpha_std:.6f}")
        logger.info(f"Error from theoretical (0.25): {error_from_theoretical:.2e}")
        
        return analysis
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize real data analysis results."""
        
        successful_results = [r for r in results if r.get("status") == "success"]
        
        if not successful_results:
            return {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "status": "failed",
                "message": "No successful real data analysis tasks."
            }
        
        # Aggregate analysis results
        all_alpha_means = []
        all_errors = []
        all_r_squared = []
        
        for result in successful_results:
            analysis = result.get("analysis_results", {})
            if "alpha_statistics" in analysis:
                all_alpha_means.append(analysis["alpha_statistics"]["mean"])
            if "theoretical_comparison" in analysis:
                all_errors.append(analysis["theoretical_comparison"]["error_from_theoretical"])
            if "r_squared" in analysis and analysis["r_squared"]["mean"]:
                all_r_squared.append(analysis["r_squared"]["mean"])
        
        summary = {
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(results) - len(successful_results),
            "status": "success",
            "data_origin": {
                "type": "real",
                "source": "experiment_results",
                "n_files_analyzed": len(successful_results)
            },
            "quarterlock_analysis": {
                "overall_alpha_mean": float(np.mean(all_alpha_means)) if all_alpha_means else None,
                "overall_alpha_std": float(np.std(all_alpha_means)) if all_alpha_means else None,
                "overall_error_from_theoretical": float(np.mean(all_errors)) if all_errors else None,
                "overall_r_squared_mean": float(np.mean(all_r_squared)) if all_r_squared else None,
                "n_datasets": len(all_alpha_means)
            },
            "integrity_status": "real_data_analysis_completed"
        }
        
        return summary
