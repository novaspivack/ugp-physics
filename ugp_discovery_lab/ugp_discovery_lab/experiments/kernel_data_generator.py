"""
Kernel Data Generator for Independent Alpha Estimators.

Generates synthetic kernel series (kG, kL, kM) that follow the RG attractor pattern
for testing independent alpha estimation methods.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
import numpy as np
from scipy.optimize import minimize_scalar

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment


@register_experiment("kernel_data_generator")
class KernelDataGenerator(Experiment):
    """
    Generate synthetic kernel series data for testing independent alpha estimators.
    
    Creates kG, kL, kM series that follow the RG attractor pattern:
    kM ≈ kG + alpha*kL + noise
    where alpha converges to the RG attractor value -0.08503468530335825
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate kernel data generation tasks."""
        cfg = self.cfg
        n_series = int(cfg.get("generation", {}).get("n_series", 10))
        series_length = int(cfg.get("generation", {}).get("series_length", 200))
        
        tasks = []
        for i in range(n_series):
            task = {
                "task_id": f"kernel_series_{i}",
                "series_id": i,
                "series_length": series_length,
                "seed": 12345 + i,
                "target_alpha": -0.08503468530335825  # Our primary RG attractor
            }
            tasks.append(task)
        
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single kernel series dataset."""
        logger = get_logger("kernel_data_generator", 
                           (self.root / "results/logs" / "kernel_generator.log"))
        
        series_id = task["series_id"]
        series_length = task["series_length"]
        seed = task["seed"]
        target_alpha = task["target_alpha"]
        
        logger.info(f"Generating kernel series {series_id} with length {series_length}")
        
        # Set random seed for reproducibility
        np.random.seed(seed)
        
        # Generate base series with some structure
        t = np.linspace(0, 10, series_length)
        
        # kG: Growing trend with some oscillation
        kG = 0.1 * t + 0.05 * np.sin(2 * np.pi * t) + 0.01 * np.random.randn(series_length)
        
        # kL: Different pattern - exponential-like with noise
        kL = 0.02 * np.exp(0.3 * t) + 0.005 * np.cos(3 * np.pi * t) + 0.005 * np.random.randn(series_length)
        
        # kM: Follow the RG attractor relationship with convergence
        # Start with some initial alpha and converge to target
        alpha_evolution = target_alpha + (0.1 - target_alpha) * np.exp(-0.1 * t)
        
        # Generate kM following the relationship kM ≈ kG + alpha*kL + noise
        # But with alpha evolving over time
        kM = np.zeros(series_length)
        for i in range(series_length):
            kM[i] = kG[i] + alpha_evolution[i] * kL[i] + 0.001 * np.random.randn()
        
        # Store the series data
        series_data = {
            "kG": kG.tolist(),
            "kL": kL.tolist(), 
            "kM": kM.tolist(),
            "alpha_evolution": alpha_evolution.tolist(),
            "target_alpha": target_alpha,
            "series_length": series_length,
            "seed": seed
        }
        
        # Calculate some basic statistics
        final_alpha = alpha_evolution[-1]
        alpha_error = abs(final_alpha - target_alpha)
        
        result = {
            "task_id": task["task_id"],
            "success": True,
            "series_id": series_id,
            "series_data": series_data,
            "statistics": {
                "final_alpha": float(final_alpha),
                "target_alpha": float(target_alpha),
                "alpha_error": float(alpha_error),
                "convergence_achieved": alpha_error < 0.001
            },
            "status": "completed"
        }
        
        logger.info(f"Generated series {series_id}: final_alpha={final_alpha:.8f}, error={alpha_error:.8f}")
        
        return result
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize kernel data generation results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary = {
                "status": "failed",
                "message": "No successful kernel series generated",
                "total_attempted": len(results)
            }
        else:
            # Calculate aggregate statistics
            final_alphas = [r["statistics"]["final_alpha"] for r in successful_results]
            alpha_errors = [r["statistics"]["alpha_error"] for r in successful_results]
            convergence_rate = sum(r["statistics"]["convergence_achieved"] for r in successful_results) / len(successful_results)
            
            summary = {
                "status": "completed",
                "total_series": len(successful_results),
                "target_alpha": successful_results[0]["statistics"]["target_alpha"],
                "statistics": {
                    "mean_final_alpha": float(np.mean(final_alphas)),
                    "std_final_alpha": float(np.std(final_alphas)),
                    "mean_alpha_error": float(np.mean(alpha_errors)),
                    "max_alpha_error": float(np.max(alpha_errors)),
                    "convergence_rate": float(convergence_rate)
                }
            }
        
        # Write reports
        write_json_report(self.root, "kernel_data_generation_summary", summary)
        
        md_content = [
            "# Kernel Data Generation Summary",
            f"- Status: {summary['status']}",
            f"- Total series generated: {summary.get('total_series', 0)}",
        ]
        
        if "statistics" in summary:
            stats = summary["statistics"]
            md_content.extend([
                f"- Target alpha: {summary['target_alpha']:.8f}",
                f"- Mean final alpha: {stats['mean_final_alpha']:.8f}",
                f"- Alpha error (mean): {stats['mean_alpha_error']:.8f}",
                f"- Convergence rate: {stats['convergence_rate']:.1%}"
            ])
        
        write_md_report(self.root, "kernel_data_generation_summary", "\n".join(md_content))
        
        return summary
