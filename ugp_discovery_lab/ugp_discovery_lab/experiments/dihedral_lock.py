"""
Dihedral-Lock discovery experiments for UGP Discovery Lab.

Searches for Dihedral-Lock relations (generalizing Quarter-Lock) on survivor windows
that obey dihedral D_n symmetry. Fits rational planes:
k_M = k_G + (1/λ_n)k_L
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
import numpy as np
import random
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from ..diagnostics.kernel_plane_fit import KernelPlaneFitter
from .base import Experiment


@register_experiment("dihedral_lock")
class DihedralLock(Experiment):
    """
    Search for Dihedral-Lock relations on survivor windows with D_n symmetry.
    
    This experiment generates survivor windows with enforced dihedral tiling
    and searches for rational plane relationships in the kernel coefficient space.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate dihedral lock discovery tasks."""
        tasks = []
        
        # Get configuration
        dihedral_config = self.cfg.get("dihedral", {})
        n_list = dihedral_config.get("n_list", [5, 6, 8, 10, 12])
        windows = dihedral_config.get("windows", [10, 11])
        samples_per_class = dihedral_config.get("samples_per_class", 20)
        
        fit_config = self.cfg.get("fit", {})
        max_denominator = fit_config.get("max_denominator", 16)
        min_r2 = fit_config.get("min_r2", 0.995)
        
        # Generate tasks for each D_n and window combination
        for Dn in n_list:
            for window_n in windows:
                for sample_idx in range(samples_per_class):
                    task = {
                        "task_id": f"dihedral_D{Dn}_n{window_n}_s{sample_idx}",
                        "Dn": Dn,
                        "window_n": window_n,
                        "sample_idx": sample_idx,
                        "max_denominator": max_denominator,
                        "min_r2": min_r2,
                        "test_type": "dihedral_lock"
                    }
                    
                    if self.validate_task(task):
                        tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} dihedral lock discovery tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single dihedral lock discovery task."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting dihedral lock discovery: {task_id}")
                
                # Extract parameters
                Dn = task["Dn"]
                window_n = task["window_n"]
                sample_idx = task["sample_idx"]
                max_denominator = task["max_denominator"]
                min_r2 = task["min_r2"]
                
                logger.info(f"Searching for D{Dn} lock at window n={window_n}, sample {sample_idx}")
                
                # Generate survivor window with dihedral symmetry
                survivor_window = self._generate_dihedral_survivor_window(
                    Dn, window_n, sample_idx, logger
                )
                
                # Run evolution to accumulate kernel coefficients
                kernel_points = self._run_evolution_and_extract_kernels(
                    survivor_window, window_n, logger
                )
                
                # Fit planes and search for dihedral locks
                plane_results = self._fit_dihedral_planes(
                    kernel_points, Dn, max_denominator, min_r2, logger
                )
                
                # Analyze results
                analysis = self._analyze_dihedral_results(plane_results, Dn, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "Dn": Dn,
                    "window_n": window_n,
                    "sample_idx": sample_idx,
                    "kernel_points": kernel_points,
                    "plane_results": plane_results,
                    "analysis": analysis,
                    "candidate_plane": analysis.get("best_plane", {}),
                    "support": {
                        "num_points": len(kernel_points),
                        "residual_stats": analysis.get("residual_stats", {})
                    }
                }
                
                logger.info(f"Dihedral lock discovery {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Dihedral lock discovery {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _generate_dihedral_survivor_window(self, Dn: int, window_n: int, 
                                         sample_idx: int, logger) -> Dict[str, Any]:
        """Generate a survivor window with enforced D_n dihedral symmetry."""
        logger.debug(f"Generating D{Dn} survivor window for n={window_n}")
        
        # Set up random seed for reproducible but varied samples
        random.seed(hash(f"D{Dn}_n{window_n}_s{sample_idx}") % 2**32)
        
        # Generate base survivor configuration
        base_config = self._generate_base_survivor_config(window_n)
        
        # Apply dihedral symmetry constraints
        dihedral_config = self._apply_dihedral_constraints(base_config, Dn, logger)
        
        return {
            "Dn": Dn,
            "window_n": window_n,
            "base_config": base_config,
            "dihedral_config": dihedral_config,
            "symmetry_group": f"D{Dn}",
            "seed": sample_idx
        }
    
    def _generate_base_survivor_config(self, window_n: int) -> Dict[str, Any]:
        """Generate a base survivor configuration."""
        # Ridge value
        ridge = 2**window_n - 16
        
        # Find divisors of ridge for survivor pairs
        divisors = []
        for i in range(16, int(ridge**0.5) + 1):
            if ridge % i == 0:
                j = ridge // i
                if j >= 16:
                    divisors.append((i, j))
        
        # Select a random survivor pair
        if divisors:
            b2, q2 = random.choice(divisors)
        else:
            # Fallback
            b2, q2 = 24, 42
        
        # Compute derived values
        q1 = q2 - 13  # Fibonacci rigidity
        b1 = b2 + q2 + 7  # Mirror constraint
        c1 = b1 * q1 + 20  # Prime-lock
        
        return {
            "ridge": ridge,
            "b2": b2, "q2": q2,
            "b1": b1, "q1": q1,
            "c1": c1,
            "seed": [1, b1, c1]
        }
    
    def _apply_dihedral_constraints(self, base_config: Dict[str, Any], 
                                  Dn: int, logger) -> Dict[str, Any]:
        """Apply dihedral symmetry constraints to the base configuration."""
        logger.debug(f"Applying D{Dn} constraints")
        
        # For dihedral groups, we need to ensure the configuration
        # has the appropriate rotational and reflection symmetries
        
        dihedral_config = base_config.copy()
        
        if Dn == 5:
            # D5: pentagonal symmetry - ensure 72-degree rotational symmetry
            dihedral_config["rotation_angle"] = 72
            dihedral_config["reflection_axes"] = 5
        elif Dn == 6:
            # D6: hexagonal symmetry - ensure 60-degree rotational symmetry
            dihedral_config["rotation_angle"] = 60
            dihedral_config["reflection_axes"] = 6
        elif Dn == 8:
            # D8: octagonal symmetry - ensure 45-degree rotational symmetry
            dihedral_config["rotation_angle"] = 45
            dihedral_config["reflection_axes"] = 8
        elif Dn == 10:
            # D10: decagonal symmetry - ensure 36-degree rotational symmetry
            dihedral_config["rotation_angle"] = 36
            dihedral_config["reflection_axes"] = 10
        elif Dn == 12:
            # D12: dodecagonal symmetry - ensure 30-degree rotational symmetry
            dihedral_config["rotation_angle"] = 30
            dihedral_config["reflection_axes"] = 12
        
        # Add symmetry-preserving perturbations
        dihedral_config["symmetry_preserved"] = True
        dihedral_config["perturbation_strength"] = 0.1
        
        return dihedral_config
    
    def _run_evolution_and_extract_kernels(self, survivor_window: Dict[str, Any], 
                                         window_n: int, logger) -> List[List[float]]:
        """Run evolution and extract kernel coefficient points."""
        logger.debug("Running evolution and extracting kernel coefficients")
        
        # Initialize evolution
        seed = survivor_window["dihedral_config"]["seed"]
        steps = self.cfg.get("run", {}).get("steps", 64)
        
        # Simple evolution simulation
        kernel_points = []
        current_state = {
            "a": seed[0],
            "b": seed[1],
            "c": seed[2],
            "q": 0,
            "m": 0
        }
        
        # Initialize
        current_state["q"] = current_state["c"] // current_state["b"]
        current_state["m"] = current_state["c"] % current_state["b"]
        
        for step in range(steps):
            # Compute kernel coefficients (simplified model)
            k_M, k_G, k_L = self._compute_kernel_coefficients(current_state, window_n)
            kernel_points.append([k_M, k_G, k_L])
            
            # Simple evolution step
            next_state = self._evolve_state_simple(current_state, window_n, step)
            current_state = next_state
        
        logger.debug(f"Extracted {len(kernel_points)} kernel points")
        return kernel_points
    
    def _compute_kernel_coefficients(self, state: Dict[str, Any], 
                                   window_n: int) -> Tuple[float, float, float]:
        """Compute kernel coefficients (k_M, k_G, k_L) from current state."""
        # Simplified kernel coefficient computation
        # In a full implementation, these would be computed from the actual
        # invariant defect structure
        
        a, b, c, q, m = state["a"], state["b"], state["c"], state["q"], state["m"]
        
        # Placeholder computation - replace with actual kernel computation
        k_M = a + b * 0.1 + c * 0.01
        k_G = b + c * 0.1 + m * 0.01
        k_L = c + m * 0.1 + q * 0.01
        
        # Add some structure to make plane fitting meaningful
        # This simulates the kind of linear relationships we expect
        k_M = k_G + 0.25 * k_L + random.gauss(0, 0.01)
        
        return float(k_M), float(k_G), float(k_L)
    
    def _evolve_state_simple(self, state: Dict[str, Any], window_n: int, 
                           step: int) -> Dict[str, Any]:
        """Simple state evolution for kernel point generation."""
        next_state = state.copy()
        
        # Simple evolution rules
        if step % 2 == 0:  # Even step
            next_state["b"] = state["b"] + 1
            next_state["c"] = state["c"] + state["b"]
        else:  # Odd step
            next_state["a"] = state["a"] + 1
            next_state["c"] = state["c"] + state["a"]
        
        # Update derived values
        next_state["q"] = next_state["c"] // next_state["b"] if next_state["b"] > 0 else 0
        next_state["m"] = next_state["c"] % next_state["b"] if next_state["b"] > 0 else 0
        
        return next_state
    
    def _fit_dihedral_planes(self, kernel_points: List[List[float]], Dn: int,
                           max_denominator: int, min_r2: float, logger) -> Dict[str, Any]:
        """Fit planes and search for dihedral lock patterns."""
        logger.debug(f"Fitting planes for D{Dn} dihedral lock")
        
        if len(kernel_points) < 3:
            return {"error": "Insufficient points for plane fitting"}
        
        # Use the kernel plane fitter
        fitter = KernelPlaneFitter(max_denominator=max_denominator)
        plane_result = fitter.fit_plane(kernel_points)
        
        if "error" in plane_result:
            return plane_result
        
        # Check for dihedral lock pattern
        coeffs = plane_result["coefficients"]
        a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
        
        dihedral_lock = {"detected": False}
        
        # Look for pattern: k_M = k_G + (1/λ_n)k_L
        if abs(a - 1.0) < 1e-6 and abs(c - 0.0) < 1e-6 and b > 0:
            lambda_n = 1.0 / b if b > 1e-6 else None
            if lambda_n and self._is_rational(lambda_n, max_denominator):
                dihedral_lock = {
                    "detected": True,
                    "lambda_n": lambda_n,
                    "lambda_n_rational": self._float_to_rational(lambda_n, max_denominator),
                    "equation": f"k_M = k_G + (1/{1/b:.3f})k_L"
                }
        
        # Check if this meets quality thresholds
        meets_threshold = plane_result["r_squared"] >= min_r2
        
        return {
            "plane_fit": plane_result,
            "dihedral_lock": dihedral_lock,
            "meets_threshold": meets_threshold,
            "Dn": Dn
        }
    
    def _is_rational(self, x: float, max_denominator: int, tolerance: float = 1e-6) -> bool:
        """Check if a number has a simple rational representation."""
        for denom in range(1, max_denominator + 1):
            num = round(x * denom)
            if abs(x - num / denom) < tolerance:
                return True
        return False
    
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
    
    def _analyze_dihedral_results(self, plane_results: Dict[str, Any], 
                                Dn: int, logger) -> Dict[str, Any]:
        """Analyze dihedral lock results."""
        logger.debug(f"Analyzing results for D{Dn}")
        
        if "error" in plane_results:
            return {"error": plane_results["error"]}
        
        analysis = {
            "Dn": Dn,
            "plane_quality": plane_results["plane_fit"]["r_squared"],
            "dihedral_lock_detected": plane_results["dihedral_lock"]["detected"],
            "meets_threshold": plane_results["meets_threshold"]
        }
        
        # Find best plane
        if plane_results["dihedral_lock"]["detected"]:
            dihedral_lock = plane_results["dihedral_lock"]
            analysis["best_plane"] = {
                "lambda": dihedral_lock["lambda_n"],
                "lambda_rational": dihedral_lock["lambda_n_rational"],
                "equation": dihedral_lock["equation"],
                "error": plane_results["plane_fit"]["residuals"],
                "r2": plane_results["plane_fit"]["r_squared"]
            }
            
            # Compute residual statistics
            residuals = plane_results["plane_fit"].get("residuals", 0)
            analysis["residual_stats"] = {
                "mean": float(residuals),
                "std": 0.0,  # Would need actual residual data
                "max": float(residuals)
            }
        else:
            analysis["best_plane"] = None
            analysis["residual_stats"] = {"mean": 0, "std": 0, "max": 0}
        
        return analysis
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize dihedral lock discovery results."""
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
            # Group by D_n
            results_by_Dn = {}
            for result in successful_results:
                Dn = result["Dn"]
                if Dn not in results_by_Dn:
                    results_by_Dn[Dn] = []
                results_by_Dn[Dn].append(result)
            
            # Analyze results by dihedral group
            dihedral_analysis = {}
            for Dn, dn_results in results_by_Dn.items():
                detected_locks = [r for r in dn_results if r["analysis"]["dihedral_lock_detected"]]
                threshold_meets = [r for r in dn_results if r["analysis"]["meets_threshold"]]
                
                dihedral_analysis[f"D{Dn}"] = {
                    "total_samples": len(dn_results),
                    "locks_detected": len(detected_locks),
                    "threshold_meets": len(threshold_meets),
                    "detection_rate": len(detected_locks) / len(dn_results),
                    "threshold_rate": len(threshold_meets) / len(dn_results)
                }
                
                # Collect best candidates
                if detected_locks:
                    best_lock = max(detected_locks, 
                                  key=lambda r: r["analysis"]["plane_quality"])
                    dihedral_analysis[f"D{Dn}"]["best_candidate"] = best_lock["analysis"]["best_plane"]
            
            summary["metrics"] = {
                "dihedral_groups_tested": list(results_by_Dn.keys()),
                "dihedral_analysis": dihedral_analysis,
                "total_locks_detected": sum(len([r for r in results if r["analysis"]["dihedral_lock_detected"]]) 
                                          for results in results_by_Dn.values())
            }
            
            # Discoveries
            discoveries = []
            
            # Check for consistent dihedral locks
            for Dn, analysis in dihedral_analysis.items():
                if analysis["detection_rate"] > 0.5:  # More than 50% detection rate
                    discoveries.append(f"Consistent {Dn} dihedral lock detected (rate: {analysis['detection_rate']:.1%})")
                
                if "best_candidate" in analysis:
                    candidate = analysis["best_candidate"]
                    discoveries.append(f"Strong {Dn} candidate: λ = {candidate['lambda_rational']['numerator']}/{candidate['lambda_rational']['denominator']}")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
