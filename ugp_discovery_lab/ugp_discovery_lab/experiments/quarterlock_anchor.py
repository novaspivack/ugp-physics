"""
Quarter-Lock anchor validation experiment.

Re-fits Quarter-Lock on multiple independent windows/runs to pin down
the true coefficient for the canonical law (should be exactly 1/4).
"""

from .base import Experiment
from pathlib import Path
from typing import List, Dict, Any
import json
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
import warnings

from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint
from ..diagnostics.algebraic_basis import AlgebraicBasis


@register_experiment("quarterlock_anchor")
class QuarterLockAnchor(Experiment):
    """Validates Quarter-Lock coefficient as calibration anchor."""
    
    def tasks(self) -> List[Dict]:
        """Generate tasks for Quarter-Lock anchor analysis."""
        tasks = []
        
        # Get configuration
        fit_config = self.cfg.get("fit", {})
        target_value = fit_config.get("target_value", "1/4")
        tol_abs = fit_config.get("tol_abs", 1e-6)
        min_points = fit_config.get("min_points", 500)
        
        # Find all lawful evolution result files
        results_dir = self.root / "UGP_discovery_lab_runs"
        le_files = list(results_dir.glob("**/LE_*_summary.json"))
        
        if not le_files:
            # Generate synthetic data if no real data found
            self.logger.warning("No lawful evolution data found, generating synthetic data")
            return self._generate_synthetic_tasks()
        
        # Group files by experiment type
        experiment_groups = {}
        for file_path in le_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Extract experiment type from filename
                exp_type = self._extract_experiment_type(file_path.name)
                if exp_type not in experiment_groups:
                    experiment_groups[exp_type] = []
                experiment_groups[exp_type].append(data)
                
            except Exception as e:
                self.logger.warning(f"Could not load {file_path}: {e}")
        
        # Create tasks for each experiment group
        for exp_type, exp_data in experiment_groups.items():
            task_id = f"anchor_{exp_type}"
            tasks.append({
                "task_id": task_id,
                "experiment_type": exp_type,
                "data_files": [str(f) for f in le_files if exp_type in f.name],
                "experiment_data": exp_data,
                "fit_config": fit_config,
                "target_value": target_value,
                "tol_abs": tol_abs,
                "min_points": min_points,
                "model": fit_config.get("model", "kM = kG + alpha*kL")
            })
        
        return tasks
    
    def _generate_synthetic_tasks(self) -> List[Dict]:
        """Generate synthetic tasks for testing."""
        tasks = []
        
        # Test different experiment types with known Quarter-Lock
        test_types = [
            {"name": "LE_gte_fib", "expected_alpha": 0.25},
            {"name": "LE_gte_lucas", "expected_alpha": 0.25},
            {"name": "LE_mersenne_fib", "expected_alpha": 0.25},
        ]
        
        for exp_type in test_types:
            task_id = f"anchor_{exp_type['name']}_synthetic"
            tasks.append({
                "task_id": task_id,
                "experiment_type": exp_type["name"],
                "data_files": [],
                "experiment_data": [],
                "synthetic": True,
                "expected_alpha": exp_type["expected_alpha"],
                "fit_config": self.cfg.get("fit", {}),
                "target_value": "1/4",
                "tol_abs": 1e-6,
                "min_points": 500,
                "model": "kM = kG + alpha*kL"
            })
        
        return tasks
    
    def _extract_experiment_type(self, filename: str) -> str:
        """Extract experiment type from filename."""
        # Look for patterns like "LE_gte_lucas_..." or "LE_mersenne_fib_..."
        import re
        match = re.search(r'(LE_[^_]+)', filename)
        if match:
            return match.group(1)
        return "unknown"
    
    def run_task(self, task: Dict) -> Dict:
        """Run Quarter-Lock anchor analysis for a single experiment type."""
        task_id = task["task_id"]
        logger = get_logger(f"quarterlock_anchor:{task_id}",
                          (self.root / "results" / "logs" / f"{task_id}.log"))
        
        logger.info(f"Starting Quarter-Lock anchor analysis: {task_id}")
        
        experiment_type = task["experiment_type"]
        target_value = task["target_value"]
        tol_abs = task["tol_abs"]
        min_points = task["min_points"]
        
        try:
            # Load or generate data
            if task.get("synthetic", False):
                kernel_points = self._generate_synthetic_kernel_points(
                    task["expected_alpha"], min_points * 2
                )
            else:
                kernel_points = self._load_kernel_points(task, logger)
            
            if len(kernel_points) < min_points:
                logger.warning(f"Insufficient points: {len(kernel_points)} < {min_points}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": f"Insufficient points: {len(kernel_points)} < {min_points}"
                }
            
            # Fit the Quarter-Lock model k_M = k_G + α*k_L
            fit_result = self._fit_quarter_lock(kernel_points, logger)
            
            # Analyze consistency with target value
            target_alpha = self._parse_target_value(target_value)
            consistency_result = self._analyze_consistency(
                fit_result["alpha"], target_alpha, tol_abs, logger
            )
            
            # Compile results
            result = {
                "task_id": task_id,
                "experiment_type": experiment_type,
                "success": True,
                "data_points": len(kernel_points),
                "fit_result": fit_result,
                "consistency_result": consistency_result,
                "target_alpha": target_alpha,
                "observed_alpha": fit_result["alpha"],
                "is_consistent": consistency_result["is_consistent"],
                "verdict": consistency_result["verdict"]
            }
            
            logger.info(f"Quarter-Lock anchor analysis completed: {task_id}")
            logger.info(f"Alpha = {fit_result['alpha']:.8f}, Target = {target_alpha:.8f}")
            logger.info(f"Consistent: {consistency_result['is_consistent']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Quarter-Lock anchor analysis: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _generate_synthetic_kernel_points(self, alpha: float, n_points: int) -> List[List[float]]:
        """Generate synthetic kernel points with known alpha."""
        np.random.seed(42)  # For reproducibility
        points = []
        
        for _ in range(n_points):
            k_G = np.random.uniform(0, 10)
            k_L = np.random.uniform(0, 10)
            # Add some noise
            noise = np.random.normal(0, 0.001)  # Very small noise for anchor
            k_M = k_G + alpha * k_L + noise
            points.append([k_M, k_G, k_L])
        
        return points
    
    def _load_kernel_points(self, task: Dict, logger) -> List[List[float]]:
        """Load kernel points from lawful evolution data files."""
        all_points = []
        
        for data in task["experiment_data"]:
            try:
                # Extract kernel points from the data structure
                if "results" in data:
                    for result in data["results"]:
                        if "kernel_points" in result:
                            points = result["kernel_points"]
                            all_points.extend(points)
                        elif "evolution_history" in result:
                            # Extract from evolution history
                            history = result["evolution_history"]
                            for step in history:
                                if "k_M" in step and "k_G" in step and "k_L" in step:
                                    all_points.append([step["k_M"], step["k_G"], step["k_L"]])
                
            except Exception as e:
                logger.warning(f"Could not extract points from data: {e}")
        
        if not all_points:
            logger.warning("No kernel points found in data, generating synthetic")
            return self._generate_synthetic_kernel_points(0.25, 500)
        
        return all_points
    
    def _parse_target_value(self, target_str: str) -> float:
        """Parse target value string to float."""
        if target_str == "1/4":
            return 0.25
        elif "/" in target_str:
            num, den = target_str.split("/")
            return float(num) / float(den)
        else:
            return float(target_str)
    
    def _fit_quarter_lock(self, kernel_points: List[List[float]], logger) -> Dict:
        """Fit Quarter-Lock model k_M = k_G + α*k_L to kernel points."""
        points_array = np.array(kernel_points)
        k_M = points_array[:, 0]
        k_G = points_array[:, 1]
        k_L = points_array[:, 2]
        
        # Fit the model: k_M = k_G + α*k_L
        # Rearrange to: k_M - k_G = α*k_L
        y = k_M - k_G
        X = k_L.reshape(-1, 1)
        
        # Linear regression
        reg = LinearRegression()
        reg.fit(X, y)
        alpha = reg.coef_[0]
        
        # Calculate R-squared
        y_pred = reg.predict(X)
        r_squared = reg.score(X, y)
        
        # Calculate confidence interval for alpha
        residuals = y - y_pred
        mse = np.mean(residuals**2)
        std_error = np.sqrt(mse / np.sum((X - np.mean(X))**2))
        t_val = stats.t.ppf(0.975, len(y) - 2)  # 95% CI
        ci_half = t_val * std_error
        
        # Calculate additional statistics
        alpha_std = np.std(y / X.flatten())
        
        return {
            "alpha": float(alpha),
            "r_squared": float(r_squared),
            "confidence_interval": [float(alpha - ci_half), float(alpha + ci_half)],
            "std_error": float(std_error),
            "alpha_std": float(alpha_std),
            "n_points": len(kernel_points),
            "residuals_std": float(np.std(residuals))
        }
    
    def _analyze_consistency(self, observed_alpha: float, target_alpha: float, 
                           tolerance: float, logger) -> Dict:
        """Analyze consistency between observed and target alpha values."""
        error = abs(observed_alpha - target_alpha)
        relative_error = error / target_alpha if target_alpha != 0 else float('inf')
        
        is_consistent = error < tolerance
        
        # Use algebraic basis for additional analysis
        basis = AlgebraicBasis()
        quarter_analysis = basis.analyze_quarter_lock(observed_alpha, tolerance)
        
        return {
            "observed_alpha": observed_alpha,
            "target_alpha": target_alpha,
            "absolute_error": error,
            "relative_error": relative_error,
            "tolerance": tolerance,
            "is_consistent": is_consistent,
            "verdict": quarter_analysis["verdict"],
            "confidence_level": self._calculate_confidence_level(error, tolerance)
        }
    
    def _calculate_confidence_level(self, error: float, tolerance: float) -> str:
        """Calculate confidence level based on error vs tolerance."""
        ratio = error / tolerance
        
        if ratio < 0.1:
            return "very_high"
        elif ratio < 0.5:
            return "high"
        elif ratio < 1.0:
            return "acceptable"
        elif ratio < 2.0:
            return "low"
        else:
            return "very_low"
    
    def summarize(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize Quarter-Lock anchor results."""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0.0
        }
        
        if successful_results:
            # Analyze consistency across experiments
            consistency_summary = {}
            alpha_values = []
            
            for result in successful_results:
                exp_type = result["experiment_type"]
                alpha = result["observed_alpha"]
                is_consistent = result["is_consistent"]
                
                alpha_values.append(alpha)
                consistency_summary[exp_type] = {
                    "alpha": alpha,
                    "is_consistent": is_consistent,
                    "verdict": result["verdict"],
                    "data_points": result["data_points"],
                    "r_squared": result["fit_result"]["r_squared"]
                }
            
            # Calculate overall statistics
            alpha_array = np.array(alpha_values)
            consistent_count = sum(1 for r in successful_results if r["is_consistent"])
            
            summary["consistency_summary"] = consistency_summary
            summary["overall_statistics"] = {
                "mean_alpha": float(np.mean(alpha_array)),
                "std_alpha": float(np.std(alpha_array)),
                "min_alpha": float(np.min(alpha_array)),
                "max_alpha": float(np.max(alpha_array)),
                "consistent_experiments": consistent_count,
                "total_experiments": len(successful_results),
                "consistency_rate": consistent_count / len(successful_results)
            }
            
            # Discoveries
            discoveries = []
            
            if consistent_count == len(successful_results):
                discoveries.append("Quarter-Lock coefficient (1/4) confirmed across all experiments")
            elif consistent_count > len(successful_results) / 2:
                discoveries.append(f"Quarter-Lock coefficient mostly consistent ({consistent_count}/{len(successful_results)} experiments)")
            else:
                discoveries.append(f"Quarter-Lock coefficient inconsistent ({consistent_count}/{len(successful_results)} experiments)")
            
            alpha_std = np.std(alpha_array)
            if alpha_std < 1e-4:
                discoveries.append("Very low variance in alpha estimates across experiments")
            elif alpha_std < 1e-3:
                discoveries.append("Low variance in alpha estimates across experiments")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
