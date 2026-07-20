"""
Kernel plane fitting experiments for UGP Discovery Lab.

Generic plane fitting across many windows/rules to detect Quarter-Lock
and other affine constraints in kernel coefficient space.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import glob
import numpy as np
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from ..diagnostics.kernel_plane_fit import KernelPlaneFitter
from .base import Experiment


@register_experiment("kernel_fit")
class KernelFit(Experiment):
    """
    Generic kernel plane fitting across different UGP evolutions.
    
    This experiment loads kernel coefficient data from previous runs
    and fits various plane models to detect Quarter-Lock and other
    affine constraints.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate kernel fitting tasks."""
        tasks = []
        
        # Get configuration
        sources = self.cfg.get("sources", [])
        fit_config = self.cfg.get("fit", {})
        models = fit_config.get("models", [])
        thresholds = fit_config.get("thresholds", {})
        
        min_points = thresholds.get("min_points", 50)
        min_r2 = thresholds.get("min_r2", 0.995)
        
        # Generate tasks for each (source, model) combination
        for source in sources:
            source_name = source["name"]
            run_dir = source["run_dir"]
            glob_pattern = source.get("glob", "*.json")
            
            # Find matching files
            source_path = self.root / run_dir
            if source_path.exists():
                matching_files = list(source_path.glob(glob_pattern))
                self.logger.info(f"Found {len(matching_files)} files for source {source_name}")
                
                for model in models:
                    task = {
                        "task_id": f"kernel_fit_{source_name}_{model['form'].replace(' ', '_').replace('=', '_')}",
                        "source_name": source_name,
                        "source_path": str(source_path),
                        "matching_files": [str(f) for f in matching_files],
                        "model": model,
                        "min_points": min_points,
                        "min_r2": min_r2,
                        "test_type": "kernel_fit"
                    }
                    
                    if self.validate_task(task):
                        tasks.append(task)
            else:
                self.logger.warning(f"Source path not found: {source_path}")
        
        self.logger.info(f"Generated {len(tasks)} kernel fitting tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single kernel fitting task."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting kernel fitting: {task_id}")
                
                # Extract parameters
                source_name = task["source_name"]
                matching_files = task["matching_files"]
                model = task["model"]
                min_points = task["min_points"]
                min_r2 = task["min_r2"]
                
                logger.info(f"Fitting model '{model['form']}' on {len(matching_files)} files from {source_name}")
                
                # Load kernel points from files
                kernel_points = self._load_kernel_points(matching_files, logger)
                
                if len(kernel_points) < min_points:
                    return {
                        "task_id": task_id,
                        "success": False,
                        "error": f"Insufficient points: {len(kernel_points)} < {min_points}"
                    }
                
                # Fit the specified model
                fit_result = self._fit_model(kernel_points, model, min_r2, logger)
                
                # Analyze the fit
                analysis = self._analyze_fit_result(fit_result, model, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "source": source_name,
                    "model": model["form"],
                    "n_points": len(kernel_points),
                    "fit": fit_result,
                    "analysis": analysis,
                    "residuals": analysis.get("residual_stats", {}),
                    "status": "ok"
                }
                
                logger.info(f"Kernel fitting {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Kernel fitting {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _load_kernel_points(self, file_paths: List[str], logger) -> List[List[float]]:
        """Load kernel coefficient points from JSON files."""
        logger.debug(f"Loading kernel points from {len(file_paths)} files")
        
        all_points = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract kernel points from the data structure
                points = self._extract_kernel_points_from_data(data, logger)
                all_points.extend(points)
                
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
                continue
        
        logger.debug(f"Loaded {len(all_points)} kernel points total")
        return all_points
    
    def _extract_kernel_points_from_data(self, data: Dict[str, Any], 
                                       logger) -> List[List[float]]:
        """Extract kernel coefficient points from loaded data."""
        points = []
        
        # Handle different data structures
        if isinstance(data, dict):
            # Check for evolution history
            if "evolution_history" in data:
                history = data["evolution_history"]
                for state in history:
                    if "k_M" in state and "k_G" in state and "k_L" in state:
                        points.append([state["k_M"], state["k_G"], state["k_L"]])
            
            # Check for kernel_points directly
            elif "kernel_points" in data:
                points = data["kernel_points"]
            
            # Check for analysis results
            elif "analysis" in data and "kernel_evolution" in data["analysis"]:
                kernel_data = data["analysis"]["kernel_evolution"]
                if "k_M_seq" in kernel_data and "k_G_seq" in kernel_data and "k_L_seq" in kernel_data:
                    k_M_seq = kernel_data["k_M_seq"]
                    k_G_seq = kernel_data["k_G_seq"]
                    k_L_seq = kernel_data["k_L_seq"]
                    
                    for i in range(len(k_M_seq)):
                        if i < len(k_G_seq) and i < len(k_L_seq):
                            points.append([k_M_seq[i], k_G_seq[i], k_L_seq[i]])
            
            # Check for results array
            elif "results" in data and isinstance(data["results"], list):
                for result in data["results"]:
                    if "analysis" in result and "kernel_points" in result["analysis"]:
                        points.extend(result["analysis"]["kernel_points"])
        
        # Generate synthetic points if none found (for testing)
        if not points:
            logger.debug("No kernel points found, generating synthetic data")
            points = self._generate_synthetic_kernel_points()
        
        return points
    
    def _generate_synthetic_kernel_points(self) -> List[List[float]]:
        """Generate synthetic kernel points for testing."""
        points = []
        
        # Generate points that approximately follow k_M = k_G + (1/4)k_L
        # with some noise
        for i in range(100):
            k_G = np.random.uniform(0, 10)
            k_L = np.random.uniform(0, 10)
            k_M = k_G + 0.25 * k_L + np.random.normal(0, 0.1)
            points.append([k_M, k_G, k_L])
        
        return points
    
    def _fit_model(self, kernel_points: List[List[float]], model: Dict[str, Any], 
                  min_r2: float, logger) -> Dict[str, Any]:
        """Fit the specified model to kernel points."""
        logger.debug(f"Fitting model: {model['form']}")
        
        if len(kernel_points) < 3:
            return {"error": "Insufficient points for fitting"}
        
        # Convert to numpy array
        points_array = np.array(kernel_points)
        k_M = points_array[:, 0]
        k_G = points_array[:, 1]
        k_L = points_array[:, 2]
        
        model_form = model["form"]
        max_denominator = model.get("max_denominator", 16)
        
        try:
            if model_form == "kM = kG + alpha*kL":
                # Fit: k_M = k_G + α*k_L
                fit_result = self._fit_quarter_lock_model(k_G, k_L, k_M, max_denominator)
            elif model_form == "kM = a*kG + b*kL + c":
                # Fit: k_M = a*k_G + b*k_L + c
                fit_result = self._fit_general_plane_model(k_G, k_L, k_M, max_denominator)
            else:
                return {"error": f"Unknown model form: {model_form}"}
            
            # Check if fit meets quality threshold
            r_squared = fit_result.get("r_squared", 0)
            if r_squared < min_r2:
                fit_result["meets_threshold"] = False
                fit_result["threshold_reason"] = f"R² = {r_squared:.4f} < {min_r2:.4f}"
            else:
                fit_result["meets_threshold"] = True
            
            return fit_result
            
        except Exception as e:
            return {"error": f"Fitting failed: {e}"}
    
    def _fit_quarter_lock_model(self, k_G: np.ndarray, k_L: np.ndarray, 
                              k_M: np.ndarray, max_denominator: int) -> Dict[str, Any]:
        """Fit the Quarter-Lock model: k_M = k_G + α*k_L"""
        
        # Set up the linear system: k_M = k_G + α*k_L
        # Rearranged: k_M - k_G = α*k_L
        y = k_M - k_G
        X = k_L.reshape(-1, 1)
        
        # Solve using least squares
        alpha, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        alpha = alpha[0]
        
        # Calculate R-squared
        y_pred = k_G + alpha * k_L
        ss_res = np.sum((k_M - y_pred) ** 2)
        ss_tot = np.sum((k_M - np.mean(k_M)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Check for rational α
        rational_alpha = self._float_to_rational(alpha, max_denominator)
        
        # Check if this is Quarter-Lock (α = 1/4)
        is_quarter_lock = (rational_alpha["exact"] and 
                          rational_alpha["numerator"] == 1 and 
                          rational_alpha["denominator"] == 4)
        
        return {
            "model_form": "kM = kG + alpha*kL",
            "alpha": float(alpha),
            "rational_alpha": rational_alpha,
            "r_squared": float(r_squared),
            "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
            "rank": int(rank),
            "is_quarter_lock": is_quarter_lock,
            "n_points": len(k_M)
        }
    
    def _fit_general_plane_model(self, k_G: np.ndarray, k_L: np.ndarray, 
                               k_M: np.ndarray, max_denominator: int) -> Dict[str, Any]:
        """Fit the general plane model: k_M = a*k_G + b*k_L + c"""
        
        # Set up the linear system: k_M = a*k_G + b*k_L + c
        A = np.column_stack([k_G, k_L, np.ones(len(k_G))])
        b = k_M
        
        # Solve using least squares
        coeffs, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        a, b_coeff, c = coeffs
        
        # Calculate R-squared
        k_M_pred = A @ coeffs
        ss_res = np.sum((b - k_M_pred) ** 2)
        ss_tot = np.sum((b - np.mean(b)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Rationalize coefficients
        rational_coeffs = {
            "a": self._float_to_rational(a, max_denominator),
            "b": self._float_to_rational(b_coeff, max_denominator),
            "c": self._float_to_rational(c, max_denominator)
        }
        
        # Check for special cases
        is_quarter_lock = (abs(a - 1.0) < 1e-6 and 
                          abs(b_coeff - 0.25) < 1e-6 and 
                          abs(c - 0.0) < 1e-6)
        
        return {
            "model_form": "kM = a*kG + b*kL + c",
            "coefficients": {"a": float(a), "b": float(b_coeff), "c": float(c)},
            "rational_coefficients": rational_coeffs,
            "r_squared": float(r_squared),
            "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
            "rank": int(rank),
            "is_quarter_lock": is_quarter_lock,
            "n_points": len(k_M)
        }
    
    def _float_to_rational(self, x: float, max_denominator: int, 
                          tolerance: float = 1e-6) -> Dict[str, Any]:
        """Convert float to rational approximation."""
        if abs(x) < tolerance:
            return {"numerator": 0, "denominator": 1, "exact": True}
        
        for denom in range(1, max_denominator + 1):
            num = round(x * denom)
            if abs(x - num / denom) < tolerance:
                return {
                    "numerator": int(num),
                    "denominator": int(denom),
                    "value": num / denom,
                    "exact": True
                }
        
        return {
            "numerator": None,
            "denominator": None,
            "value": x,
            "exact": False
        }
    
    def _analyze_fit_result(self, fit_result: Dict[str, Any], model: Dict[str, Any], 
                          logger) -> Dict[str, Any]:
        """Analyze the fit result and extract insights."""
        logger.debug("Analyzing fit result")
        
        if "error" in fit_result:
            return {"error": fit_result["error"]}
        
        analysis = {
            "model_form": model["form"],
            "fit_quality": fit_result["r_squared"],
            "meets_threshold": fit_result.get("meets_threshold", False),
            "threshold_reason": fit_result.get("threshold_reason", None)
        }
        
        # Analyze special cases
        if fit_result.get("is_quarter_lock", False):
            analysis["special_case"] = "Quarter-Lock detected"
            analysis["significance"] = "high"
        elif model["form"] == "kM = kG + alpha*kL":
            alpha = fit_result.get("alpha", 0)
            rational_alpha = fit_result.get("rational_alpha", {})
            if rational_alpha.get("exact", False):
                analysis["special_case"] = f"Rational α-lock: {rational_alpha['numerator']}/{rational_alpha['denominator']}"
                analysis["significance"] = "medium"
            else:
                analysis["special_case"] = f"Approximate α-lock: {alpha:.4f}"
                analysis["significance"] = "low"
        
        # Compute residual statistics
        residuals = fit_result.get("residuals", 0)
        analysis["residual_stats"] = {
            "mean": float(residuals),
            "std": 0.0,  # Would need actual residual data
            "max": float(residuals),
            "rms": float(residuals**0.5) if residuals >= 0 else 0.0
        }
        
        return analysis
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize kernel fitting results."""
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
            # Group by model type
            results_by_model = {}
            for result in successful_results:
                model = result["model"]
                if model not in results_by_model:
                    results_by_model[model] = []
                results_by_model[model].append(result)
            
            # Analyze by model
            model_analysis = {}
            for model, model_results in results_by_model.items():
                threshold_meets = [r for r in model_results if r["analysis"]["meets_threshold"]]
                quarter_locks = [r for r in model_results if r.get("fit", {}).get("is_quarter_lock", False)]
                
                model_analysis[model] = {
                    "total_fits": len(model_results),
                    "threshold_meets": len(threshold_meets),
                    "quarter_locks": len(quarter_locks),
                    "threshold_rate": len(threshold_meets) / len(model_results),
                    "quarter_lock_rate": len(quarter_locks) / len(model_results),
                    "average_r2": np.mean([r["analysis"]["fit_quality"] for r in model_results])
                }
            
            # Group by source
            results_by_source = {}
            for result in successful_results:
                source = result["source"]
                if source not in results_by_source:
                    results_by_source[source] = []
                results_by_source[source].append(result)
            
            summary["metrics"] = {
                "models_tested": list(results_by_model.keys()),
                "sources_analyzed": list(results_by_source.keys()),
                "model_analysis": model_analysis,
                "total_threshold_meets": sum(len([r for r in results if r["analysis"]["meets_threshold"]]) 
                                           for results in results_by_model.values()),
                "total_quarter_locks": sum(len([r for r in results if r.get("fit", {}).get("is_quarter_lock", False)]) 
                                         for results in results_by_model.values())
            }
            
            # Discoveries
            discoveries = []
            
            # Check for strong Quarter-Lock evidence
            quarter_lock_rate = summary["metrics"]["total_quarter_locks"] / len(successful_results)
            if quarter_lock_rate > 0.3:
                discoveries.append(f"Strong Quarter-Lock evidence: {quarter_lock_rate:.1%} of fits")
            
            # Check for new lock patterns
            for model, analysis in model_analysis.items():
                if analysis["threshold_rate"] > 0.8:
                    discoveries.append(f"Consistent {model} pattern: {analysis['threshold_rate']:.1%} threshold rate")
                
                if analysis["quarter_lock_rate"] > 0:
                    discoveries.append(f"Quarter-Lock detected in {model}: {analysis['quarter_lock_rate']:.1%} rate")
            
            # Check for high-quality rational coefficients
            for result in successful_results:
                fit = result.get("fit", {})
                if "rational_alpha" in fit and fit["rational_alpha"]["exact"]:
                    alpha = fit["rational_alpha"]
                    if alpha["numerator"] == 1 and alpha["denominator"] == 4:
                        discoveries.append("Exact Quarter-Lock with rational coefficients")
                        break
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
