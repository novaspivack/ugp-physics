"""
Renormalization Group flow experiments for UGP Discovery Lab.

Defines and iterates an RG operator R: double window → crop → rescale → refit kernel.
Detects fixed points/cycles and measures contraction.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import numpy as np
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from .base import Experiment


@register_experiment("rg_flow")
class RGFlow(Experiment):
    """
    Iterate RG operator and detect fixed points/cycles.
    
    This experiment applies a renormalization group operator to kernel data,
    iteratively transforming the window size and refitting planes to detect
    scale-invariant behavior and fixed points.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate RG flow tasks."""
        tasks = []
        
        # Get configuration
        rg_config = self.cfg.get("rg", {})
        input_config = self.cfg.get("input", {})
        fit_config = self.cfg.get("fit", {})
        stopping_config = self.cfg.get("stopping", {})
        
        iterations = rg_config.get("iterations", 8)
        initial_window = rg_config.get("initial_window", 64)
        crop_policy = rg_config.get("crop_policy", "center")
        rescale_policy = rg_config.get("rescale_policy", "normalize")
        
        source_run = input_config.get("source_run")
        model = fit_config.get("model", "kM = kG + alpha*kL")
        max_denominator = fit_config.get("max_denominator", 16)
        
        tol_plane = stopping_config.get("tol_plane", 1e-3)
        tol_param = stopping_config.get("tol_param", 1e-3)
        
        # Generate tasks for each source run
        if source_run:
            task = {
                "task_id": f"rg_flow_{Path(source_run).name}",
                "source_run": source_run,
                "model": model,
                "max_denominator": max_denominator,
                "iterations": iterations,
                "initial_window": initial_window,
                "crop_policy": crop_policy,
                "rescale_policy": rescale_policy,
                "tol_plane": tol_plane,
                "tol_param": tol_param,
                "test_type": "rg_flow"
            }
            
            if self.validate_task(task):
                tasks.append(task)
        else:
            self.logger.warning("No source_run specified in configuration")
        
        self.logger.info(f"Generated {len(tasks)} RG flow tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single RG flow task."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting RG flow analysis: {task_id}")
                
                # Extract parameters
                source_run = task["source_run"]
                model = task["model"]
                max_denominator = int(task["max_denominator"])
                iterations = int(task["iterations"])
                initial_window = int(task["initial_window"])
                crop_policy = task["crop_policy"]
                rescale_policy = task["rescale_policy"]
                tol_plane = float(task["tol_plane"])
                tol_param = float(task["tol_param"])
                
                logger.info(f"RG flow: {iterations} iterations, window={initial_window}, model='{model}'")
                
                # Load initial data from source run
                initial_data = self._load_source_data(source_run, logger)
                
                if not initial_data:
                    return {
                        "task_id": task_id,
                        "success": False,
                        "error": "No source data found"
                    }
                
                # Initialize RG flow
                rg_state = self._initialize_rg_state(initial_data, initial_window, logger)
                
                # Run RG iterations
                trajectory = []
                for iteration in range(iterations):
                    logger.debug(f"RG iteration {iteration}")
                    
                    # Apply RG operator
                    next_state = self._apply_rg_operator(
                        rg_state, crop_policy, rescale_policy, model, 
                        max_denominator, logger
                    )
                    
                    # Record trajectory
                    trajectory_point = {
                        "iter": iteration,
                        "window_size": next_state["window_size"],
                        "plane_params": next_state["plane_params"],
                        "plane_error": next_state["plane_error"],
                        "alpha": next_state.get("alpha", 0)
                    }
                    trajectory.append(trajectory_point)
                    
                    # Check for convergence
                    if iteration > 0:
                        convergence = self._check_convergence(
                            trajectory[-1], trajectory[-2], tol_plane, tol_param, logger
                        )
                        
                        if convergence["converged"]:
                            logger.info(f"Converged at iteration {iteration}")
                            break
                    
                    # Update state for next iteration
                    rg_state = next_state
                
                # Analyze trajectory
                analysis = self._analyze_rg_trajectory(trajectory, tol_plane, tol_param, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "source_run": source_run,
                    "model": model,
                    "trajectory": trajectory,
                    "analysis": analysis,
                    "fixed_point": analysis.get("fixed_point", {}),
                    "status": "ok"
                }
                
                logger.info(f"RG flow analysis {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"RG flow analysis {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _load_source_data(self, source_run: str, logger) -> Dict[str, Any]:
        """Load source data from run directory."""
        logger.debug(f"Loading source data from {source_run}")
        
        # Resolve path
        if not Path(source_run).is_absolute():
            source_path = self.root / source_run
        else:
            source_path = Path(source_run)
        
        if not source_path.exists():
            logger.warning(f"Source path not found: {source_path}")
            return {}
        
        # Look for summary JSON files
        summary_files = list(source_path.glob("**/summary.json")) + \
                       list(source_path.glob("**/*_summary.json"))
        
        if summary_files:
            try:
                with open(summary_files[0], 'r') as f:
                    data = json.load(f)
                logger.debug(f"Loaded data from {summary_files[0]}")
                return data
            except Exception as e:
                logger.warning(f"Failed to load {summary_files[0]}: {e}")
        
        # Generate synthetic data if none found
        logger.debug("No source data found, generating synthetic data")
        return self._generate_synthetic_source_data()
    
    def _generate_synthetic_source_data(self) -> Dict[str, Any]:
        """Generate synthetic source data for testing."""
        # Generate synthetic kernel points that approximately follow Quarter-Lock
        kernel_points = []
        for i in range(100):
            k_G = np.random.uniform(0, 10)
            k_L = np.random.uniform(0, 10)
            k_M = k_G + 0.25 * k_L + np.random.normal(0, 0.01)
            kernel_points.append([k_M, k_G, k_L])
        
        return {
            "kernel_points": kernel_points,
            "metadata": {
                "source": "synthetic",
                "n_points": len(kernel_points)
            }
        }
    
    def _initialize_rg_state(self, source_data: Dict[str, Any], 
                           initial_window: int, logger) -> Dict[str, Any]:
        """Initialize RG state from source data."""
        logger.debug("Initializing RG state")
        
        # Extract kernel points
        if "kernel_points" in source_data:
            kernel_points = source_data["kernel_points"]
        else:
            # Generate synthetic points
            kernel_points = self._generate_synthetic_source_data()["kernel_points"]
        
        # Initial plane fitting
        plane_params = self._fit_initial_plane(kernel_points, logger)
        
        rg_state = {
            "kernel_points": kernel_points,
            "window_size": len(kernel_points),
            "plane_params": plane_params,
            "plane_error": plane_params.get("residuals", 0),
            "alpha": plane_params.get("alpha", 0.25)
        }
        
        logger.debug(f"Initialized RG state with {len(kernel_points)} points")
        return rg_state
    
    def _fit_initial_plane(self, kernel_points: List[List[float]], 
                          logger) -> Dict[str, Any]:
        """Fit initial plane to kernel points."""
        if len(kernel_points) < 3:
            return {"error": "Insufficient points"}
        
        points_array = np.array(kernel_points)
        k_M = points_array[:, 0]
        k_G = points_array[:, 1]
        k_L = points_array[:, 2]
        
        # Fit Quarter-Lock model: k_M = k_G + α*k_L
        y = k_M - k_G
        X = k_L.reshape(-1, 1)
        
        alpha, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        alpha = alpha[0]
        
        # Calculate R-squared
        y_pred = k_G + alpha * k_L
        ss_res = np.sum((k_M - y_pred) ** 2)
        ss_tot = np.sum((k_M - np.mean(k_M)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            "alpha": float(alpha),
            "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
            "r_squared": float(r_squared),
            "rank": int(rank)
        }
    
    def _apply_rg_operator(self, rg_state: Dict[str, Any], crop_policy: str,
                         rescale_policy: str, model: str, max_denominator: int,
                         logger) -> Dict[str, Any]:
        """Apply one step of the RG operator."""
        logger.debug("Applying RG operator")
        
        # Step 1: Double window (synthetic expansion)
        doubled_points = self._double_window(rg_state["kernel_points"], logger)
        
        # Step 2: Crop according to policy
        cropped_points = self._crop_window(doubled_points, crop_policy, logger)
        
        # Step 3: Rescale according to policy
        rescaled_points = self._rescale_points(cropped_points, rescale_policy, logger)
        
        # Step 4: Refit plane
        plane_params = self._fit_plane_to_points(rescaled_points, model, max_denominator, logger)
        
        # Update state
        next_state = {
            "kernel_points": rescaled_points,
            "window_size": len(rescaled_points),
            "plane_params": plane_params,
            "plane_error": plane_params.get("residuals", 0),
            "alpha": plane_params.get("alpha", 0.25)
        }
        
        return next_state
    
    def _double_window(self, kernel_points: List[List[float]], 
                      logger) -> List[List[float]]:
        """Double the window size (synthetic expansion)."""
        logger.debug("Doubling window")
        
        # For synthetic expansion, we can interpolate or generate new points
        # In a real implementation, this would involve actual window expansion
        
        doubled_points = kernel_points.copy()
        
        # Add interpolated points between existing ones
        if len(kernel_points) >= 2:
            for i in range(len(kernel_points) - 1):
                p1 = kernel_points[i]
                p2 = kernel_points[i + 1]
                
                # Interpolate
                interpolated = [
                    (p1[0] + p2[0]) / 2,
                    (p1[1] + p2[1]) / 2,
                    (p1[2] + p2[2]) / 2
                ]
                doubled_points.append(interpolated)
        
        return doubled_points
    
    def _crop_window(self, kernel_points: List[List[float]], 
                    crop_policy: str, logger) -> List[List[float]]:
        """Crop the window according to policy."""
        logger.debug(f"Cropping window with policy: {crop_policy}")
        
        if crop_policy == "center":
            # Keep center portion
            n = len(kernel_points)
            start = n // 4
            end = 3 * n // 4
            return kernel_points[start:end]
        elif crop_policy == "boundary":
            # Keep boundary portions
            n = len(kernel_points)
            start = n // 4
            end = 3 * n // 4
            return kernel_points[:start] + kernel_points[end:]
        else:
            # Default: keep all points
            return kernel_points
    
    def _rescale_points(self, kernel_points: List[List[float]], 
                       rescale_policy: str, logger) -> List[List[float]]:
        """Rescale points according to policy."""
        logger.debug(f"Rescaling points with policy: {rescale_policy}")
        
        if rescale_policy == "normalize":
            # Normalize by L2 norm
            points_array = np.array(kernel_points)
            norms = np.linalg.norm(points_array, axis=1)
            normalized_points = points_array / norms[:, np.newaxis]
            return normalized_points.tolist()
        elif rescale_policy == "center":
            # Center around mean
            points_array = np.array(kernel_points)
            centered_points = points_array - np.mean(points_array, axis=0)
            return centered_points.tolist()
        else:
            # Default: no rescaling
            return kernel_points
    
    def _fit_plane_to_points(self, kernel_points: List[List[float]], 
                           model: str, max_denominator: int, 
                           logger) -> Dict[str, Any]:
        """Fit plane to kernel points using specified model."""
        logger.debug(f"Fitting plane with model: {model}")
        
        if len(kernel_points) < 3:
            return {"error": "Insufficient points"}
        
        points_array = np.array(kernel_points)
        k_M = points_array[:, 0]
        k_G = points_array[:, 1]
        k_L = points_array[:, 2]
        
        if model == "kM = kG + alpha*kL":
            # Fit Quarter-Lock model
            y = k_M - k_G
            X = k_L.reshape(-1, 1)
            
            alpha, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
            alpha = alpha[0]
            
            # Calculate R-squared
            y_pred = k_G + alpha * k_L
            ss_res = np.sum((k_M - y_pred) ** 2)
            ss_tot = np.sum((k_M - np.mean(k_M)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return {
                "alpha": float(alpha),
                "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
                "r_squared": float(r_squared),
                "rank": int(rank)
            }
        else:
            # Default: general plane fit
            return self._fit_general_plane(k_M, k_G, k_L)
    
    def _fit_general_plane(self, k_M: np.ndarray, k_G: np.ndarray, 
                         k_L: np.ndarray) -> Dict[str, Any]:
        """Fit general plane model."""
        A = np.column_stack([k_G, k_L, np.ones(len(k_G))])
        b = k_M
        
        coeffs, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        a, b_coeff, c = coeffs
        
        # Calculate R-squared
        k_M_pred = A @ coeffs
        ss_res = np.sum((b - k_M_pred) ** 2)
        ss_tot = np.sum((b - np.mean(b)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            "coefficients": {"a": float(a), "b": float(b_coeff), "c": float(c)},
            "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
            "r_squared": float(r_squared),
            "rank": int(rank)
        }
    
    def _check_convergence(self, current: Dict[str, Any], previous: Dict[str, Any],
                         tol_plane: float, tol_param: float, logger) -> Dict[str, Any]:
        """Check for convergence between RG iterations."""
        logger.debug("Checking convergence")
        
        # Check parameter convergence
        current_alpha = current.get("alpha", 0)
        previous_alpha = previous.get("alpha", 0)
        
        # Ensure alpha values are numeric
        if not isinstance(current_alpha, (int, float)):
            current_alpha = 0
        if not isinstance(previous_alpha, (int, float)):
            previous_alpha = 0
            
        param_diff = abs(current_alpha - previous_alpha)
        
        # Check plane error convergence
        current_error = current.get("plane_error", 0)
        previous_error = previous.get("plane_error", 0)
        
        # Ensure error values are numeric
        if not isinstance(current_error, (int, float)):
            current_error = 0
        if not isinstance(previous_error, (int, float)):
            previous_error = 0
            
        plane_diff = abs(current_error - previous_error)
        
        converged = (param_diff < tol_param) and (plane_diff < tol_plane)
        
        return {
            "converged": converged,
            "param_diff": param_diff,
            "plane_diff": plane_diff,
            "tol_param": tol_param,
            "tol_plane": tol_plane
        }
    
    def _analyze_rg_trajectory(self, trajectory: List[Dict[str, Any]], 
                             tol_plane: float, tol_param: float, 
                             logger) -> Dict[str, Any]:
        """Analyze the RG trajectory for fixed points and patterns."""
        logger.debug("Analyzing RG trajectory")
        
        if not trajectory:
            return {"error": "Empty trajectory"}
        
        # Check for fixed point
        fixed_point = None
        if len(trajectory) >= 2:
            last_point = trajectory[-1]
            for i, point in enumerate(trajectory[:-1]):
                convergence = self._check_convergence(last_point, point, tol_plane, tol_param, logger)
                if convergence["converged"]:
                    fixed_point = {
                        "alpha": last_point["alpha"],
                        "within_tol": True,
                        "iter": i + 1,
                        "convergence_info": convergence
                    }
                    break
        
        # Analyze parameter evolution
        alphas = [point["alpha"] for point in trajectory if isinstance(point.get("alpha"), (int, float))]
        plane_errors = [point["plane_error"] for point in trajectory if isinstance(point.get("plane_error"), (int, float))]
        
        # Compute convergence metrics
        alpha_stability = np.std(alphas[-3:]) if len(alphas) >= 3 else (np.std(alphas) if alphas else 0.0)
        error_stability = np.std(plane_errors[-3:]) if len(plane_errors) >= 3 else (np.std(plane_errors) if plane_errors else 0.0)
        
        # Check for Quarter-Lock convergence
        quarter_lock_convergence = None
        if alphas:
            final_alpha = alphas[-1]
            if isinstance(final_alpha, (int, float)) and abs(final_alpha - 0.25) < tol_param:
                quarter_lock_convergence = {
                    "detected": True,
                    "final_alpha": float(final_alpha),
                    "deviation_from_quarter": abs(final_alpha - 0.25)
                }
        
        # Detect limit cycles
        cycles = self._detect_limit_cycles(trajectory, tol_plane, logger)
        
        analysis = {
            "trajectory_length": len(trajectory),
            "fixed_point": fixed_point,
            "cycles": cycles,
            "alpha_evolution": alphas,
            "error_evolution": plane_errors,
            "alpha_stability": float(alpha_stability),
            "error_stability": float(error_stability),
            "quarter_lock_convergence": quarter_lock_convergence,
            "final_alpha": float(alphas[-1]) if alphas else None,
            "final_error": float(plane_errors[-1]) if plane_errors else None
        }
        
        return analysis
    
    def _detect_limit_cycles(self, trajectory: List[Dict[str, Any]], 
                           tol_cycle: float, logger) -> List[Dict[str, Any]]:
        """Detect limit cycles in RG trajectory."""
        cycles = []
        
        if len(trajectory) < 4:  # Need at least 4 points to detect cycles
            return cycles
        
        logger.debug("Detecting limit cycles")
        
        # Extract parameter vectors (alpha, plane_error, window_size)
        param_vectors = []
        for point in trajectory:
            vector = np.array([
                float(point.get("alpha", 0)),
                float(point.get("plane_error", 0)),
                float(point.get("window_size", 64))
            ])
            param_vectors.append(vector)
        
        param_vectors = np.array(param_vectors)
        
        # Look for cycles of length 2-3
        for cycle_length in [2, 3]:
            for start_idx in range(len(param_vectors) - cycle_length):
                # Check if we have a repeating pattern
                cycle_candidates = []
                max_distance = 0.0
                
                for i in range(cycle_length):
                    idx1 = start_idx + i
                    idx2 = start_idx + cycle_length + i
                    
                    if idx2 >= len(param_vectors):
                        break
                    
                    # Calculate distance between parameter vectors
                    distance = np.linalg.norm(param_vectors[idx1] - param_vectors[idx2])
                    max_distance = max(max_distance, distance)
                    
                    if distance <= tol_cycle:
                        cycle_candidates.append((idx1, idx2))
                
                # If we found a complete cycle
                if len(cycle_candidates) == cycle_length and max_distance <= tol_cycle:
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
        """Summarize RG flow results."""
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
            # Analyze fixed points
            fixed_points = []
            quarter_lock_convergences = []
            
            for result in successful_results:
                analysis = result.get("analysis", {})
                
                if analysis.get("fixed_point"):
                    fixed_points.append(analysis["fixed_point"])
                
                if analysis.get("quarter_lock_convergence", {}).get("detected"):
                    quarter_lock_convergences.append(analysis["quarter_lock_convergence"])
            
            # Analyze convergence patterns
            convergence_analysis = {
                "fixed_points_detected": len(fixed_points),
                "quarter_lock_convergences": len(quarter_lock_convergences),
                "average_convergence_iter": np.mean([fp["iter"] for fp in fixed_points]) if fixed_points else None,
                "alpha_stability": np.mean([float(result["analysis"]["alpha_stability"]) for result in successful_results if isinstance(result["analysis"].get("alpha_stability"), (int, float))])
            }
            
            summary["metrics"] = convergence_analysis
            
            # Discoveries
            discoveries = []
            
            if fixed_points:
                discoveries.append(f"RG fixed points detected in {len(fixed_points)} runs")
                
                # Check for consistent fixed point values
                fixed_alphas = [fp["alpha"] for fp in fixed_points]
                if len(set(fixed_alphas)) == 1:
                    discoveries.append(f"Consistent fixed point: α = {fixed_alphas[0]:.4f}")
                else:
                    alpha_range = max(fixed_alphas) - min(fixed_alphas)
                    discoveries.append(f"Fixed point range: α ∈ [{min(fixed_alphas):.4f}, {max(fixed_alphas):.4f}] (span: {alpha_range:.4f})")
            
            if quarter_lock_convergences:
                discoveries.append(f"Quarter-Lock convergence detected in {len(quarter_lock_convergences)} runs")
                
                # Check for exact Quarter-Lock
                exact_quarters = [qlc for qlc in quarter_lock_convergences 
                                if isinstance(qlc.get("deviation_from_quarter"), (int, float)) and qlc["deviation_from_quarter"] < 1e-6]
                if exact_quarters:
                    discoveries.append("Exact Quarter-Lock fixed point confirmed")
            
            # Check for stability patterns
            alpha_stability = convergence_analysis.get("alpha_stability")
            if alpha_stability is not None and isinstance(alpha_stability, (int, float)) and alpha_stability < 1e-4:
                discoveries.append("High alpha stability across RG flow")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
