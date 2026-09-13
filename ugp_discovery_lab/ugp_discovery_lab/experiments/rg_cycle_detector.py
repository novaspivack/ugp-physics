"""
RG cycle detector experiment.

Extends RG flow analysis to detect 2- and 3-cycles in renormalization group dynamics.
"""

from .base import Experiment
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist, squareform
import warnings

from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint


@register_experiment("rg_cycle_detector")
class RGCycleDetector(Experiment):
    """Detects limit cycles in RG flow dynamics."""
    
    def tasks(self) -> List[Dict]:
        """Generate tasks for RG cycle detection."""
        tasks = []
        
        # Get configuration
        detection_config = self.cfg.get("detection", {})
        max_cycles = detection_config.get("max_cycles", 3)
        cycle_tolerance = detection_config.get("cycle_tolerance", 1e-4)
        min_cycle_length = detection_config.get("min_cycle_length", 2)
        
        # Find RG flow result files
        results_dir = self.root / "UGP_discovery_lab_runs"
        rg_files = list(results_dir.glob("**/rg_flow_*_summary.json"))
        
        if not rg_files:
            # Generate synthetic RG flow data if no real data found
            self.logger.warning("No RG flow data found, generating synthetic data")
            return self._generate_synthetic_tasks()
        
        # Create tasks for each RG flow file
        for i, file_path in enumerate(rg_files):
            task_id = f"rg_cycle_{i:03d}"
            tasks.append({
                "task_id": task_id,
                "rg_file": str(file_path),
                "max_cycles": max_cycles,
                "cycle_tolerance": cycle_tolerance,
                "min_cycle_length": min_cycle_length,
                "detection_config": detection_config
            })
        
        return tasks
    
    def _generate_synthetic_tasks(self) -> List[Dict]:
        """Generate synthetic tasks for testing."""
        tasks = []
        
        # Test different types of RG flows
        test_scenarios = [
            {"name": "fixed_point", "type": "fixed_point"},
            {"name": "limit_cycle_2", "type": "limit_cycle", "cycle_length": 2},
            {"name": "limit_cycle_3", "type": "limit_cycle", "cycle_length": 3},
            {"name": "divergent", "type": "divergent"},
        ]
        
        for scenario in test_scenarios:
            task_id = f"rg_cycle_{scenario['name']}_synthetic"
            tasks.append({
                "task_id": task_id,
                "scenario": scenario,
                "synthetic": True,
                "max_cycles": 3,
                "cycle_tolerance": 1e-4,
                "min_cycle_length": 2,
                "detection_config": {}
            })
        
        return tasks
    
    def run_task(self, task: Dict) -> Dict:
        """Run RG cycle detection for a single RG flow."""
        task_id = task["task_id"]
        logger = get_logger(f"rg_cycle_detector:{task_id}",
                          (self.root / "results" / "logs" / f"{task_id}.log"))
        
        logger.info(f"Starting RG cycle detection: {task_id}")
        
        max_cycles = task["max_cycles"]
        cycle_tolerance = task["cycle_tolerance"]
        min_cycle_length = task["min_cycle_length"]
        
        try:
            # Load or generate RG flow data
            if task.get("synthetic", False):
                rg_trajectory = self._generate_synthetic_rg_flow(task["scenario"], logger)
            else:
                rg_trajectory = self._load_rg_trajectory(task["rg_file"], logger)
            
            if not rg_trajectory:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": "No RG trajectory data available"
                }
            
            # Detect cycles in the RG trajectory
            cycle_results = self._detect_cycles(
                rg_trajectory, max_cycles, cycle_tolerance, 
                min_cycle_length, logger
            )
            
            # Analyze trajectory properties
            trajectory_analysis = self._analyze_trajectory(rg_trajectory, logger)
            
            # Compile results
            result = {
                "task_id": task_id,
                "success": True,
                "trajectory_length": len(rg_trajectory),
                "cycle_results": cycle_results,
                "trajectory_analysis": trajectory_analysis,
                "has_cycles": len(cycle_results["cycles"]) > 0,
                "cycle_count": len(cycle_results["cycles"]),
                "convergence_type": cycle_results["convergence_type"]
            }
            
            logger.info(f"RG cycle detection completed: {task_id}")
            logger.info(f"Found {len(cycle_results['cycles'])} cycles")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RG cycle detection: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _generate_synthetic_rg_flow(self, scenario: Dict, logger) -> List[Dict]:
        """Generate synthetic RG flow data for testing."""
        trajectory = []
        steps = 100
        
        if scenario["type"] == "fixed_point":
            # Converge to a fixed point
            alpha = 0.25
            for step in range(steps):
                alpha += (0.25 - alpha) * 0.1  # Converge to 0.25
                trajectory.append({
                    "step": step,
                    "alpha": alpha,
                    "window_size": 64,
                    "plane_error": 0.01 * np.exp(-step/50)
                })
        
        elif scenario["type"] == "limit_cycle":
            # Create a limit cycle
            cycle_length = scenario["cycle_length"]
            base_alpha = 0.25
            amplitude = 0.05
            
            for step in range(steps):
                # Create periodic behavior
                phase = 2 * np.pi * step / cycle_length
                alpha = base_alpha + amplitude * np.sin(phase)
                
                trajectory.append({
                    "step": step,
                    "alpha": alpha,
                    "window_size": 64 + 2 * np.sin(phase),
                    "plane_error": 0.01 + 0.005 * abs(np.sin(phase))
                })
        
        elif scenario["type"] == "divergent":
            # Divergent behavior
            alpha = 0.25
            for step in range(steps):
                alpha += 0.01 * step  # Diverging
                trajectory.append({
                    "step": step,
                    "alpha": alpha,
                    "window_size": 64 + step,
                    "plane_error": 0.01 + 0.001 * step
                })
        
        return trajectory
    
    def _load_rg_trajectory(self, file_path: str, logger) -> List[Dict]:
        """Load RG trajectory from result file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract trajectory from the data structure
            trajectory = []
            
            if "results" in data:
                for result in data["results"]:
                    if "rg_trajectory" in result:
                        trajectory.extend(result["rg_trajectory"])
                    elif "analysis" in result and "alpha_evolution" in result["analysis"]:
                        # Reconstruct trajectory from analysis data
                        alpha_evolution = result["analysis"]["alpha_evolution"]
                        error_evolution = result["analysis"].get("error_evolution", [])
                        
                        for i, alpha in enumerate(alpha_evolution):
                            trajectory.append({
                                "step": i,
                                "alpha": alpha,
                                "window_size": 64 * (2 ** i),  # Approximate window size
                                "plane_error": error_evolution[i] if i < len(error_evolution) else 0.01
                            })
            
            return trajectory
            
        except Exception as e:
            logger.warning(f"Could not load RG trajectory from {file_path}: {e}")
            return []
    
    def _detect_cycles(self, trajectory: List[Dict], max_cycles: int, 
                      tolerance: float, min_cycle_length: int, logger) -> Dict:
        """Detect cycles in RG trajectory."""
        try:
            # Extract state vectors
            states = []
            for point in trajectory:
                state = np.array([point["alpha"], point["window_size"], point["plane_error"]])
                states.append(state)
            
            states_array = np.array(states)
            
            # Find similar states using clustering
            distances = pdist(states_array)
            distance_matrix = squareform(distances)
            
            # Use DBSCAN to find clusters of similar states
            clustering = DBSCAN(eps=tolerance, min_samples=min_cycle_length)
            cluster_labels = clustering.fit_predict(states_array)
            
            # Extract cycles from clusters
            cycles = []
            unique_labels = set(cluster_labels)
            unique_labels.discard(-1)  # Remove noise label
            
            for label in unique_labels:
                cluster_indices = [i for i, l in enumerate(cluster_labels) if l == label]
                
                if len(cluster_indices) >= min_cycle_length:
                    # Sort indices to get cycle order
                    cluster_indices.sort()
                    
                    # Check if indices form a cycle (consecutive or near-consecutive)
                    if self._is_valid_cycle(cluster_indices, len(trajectory)):
                        cycle_states = [trajectory[i] for i in cluster_indices]
                        cycles.append({
                            "cycle_length": len(cluster_indices),
                            "indices": cluster_indices,
                            "states": cycle_states,
                            "mean_state": np.mean(states_array[cluster_indices], axis=0).tolist(),
                            "state_variance": np.var(states_array[cluster_indices], axis=0).tolist()
                        })
            
            # Determine convergence type
            convergence_type = self._classify_convergence_type(trajectory, cycles, tolerance)
            
            return {
                "cycles": cycles,
                "cycle_count": len(cycles),
                "convergence_type": convergence_type,
                "trajectory_length": len(trajectory),
                "tolerance": tolerance,
                "min_cycle_length": min_cycle_length
            }
            
        except Exception as e:
            logger.warning(f"Cycle detection failed: {e}")
            return {
                "cycles": [],
                "cycle_count": 0,
                "convergence_type": "unknown",
                "trajectory_length": len(trajectory),
                "tolerance": tolerance,
                "min_cycle_length": min_cycle_length
            }
    
    def _is_valid_cycle(self, indices: List[int], trajectory_length: int) -> bool:
        """Check if indices form a valid cycle."""
        if len(indices) < 2:
            return False
        
        # Check if indices are reasonably spaced (not too close, not too far)
        for i in range(1, len(indices)):
            gap = indices[i] - indices[i-1]
            if gap < 2 or gap > trajectory_length // 4:  # Reasonable gap
                return False
        
        return True
    
    def _classify_convergence_type(self, trajectory: List[Dict], cycles: List[Dict], 
                                 tolerance: float) -> str:
        """Classify the type of convergence in the RG flow."""
        if len(cycles) == 0:
            # Check for fixed point convergence
            if len(trajectory) > 10:
                last_states = trajectory[-10:]
                alphas = [s["alpha"] for s in last_states]
                alpha_std = np.std(alphas)
                
                if alpha_std < tolerance:
                    return "fixed_point"
                else:
                    return "divergent"
            else:
                return "insufficient_data"
        
        elif len(cycles) == 1:
            cycle = cycles[0]
            if cycle["cycle_length"] == 2:
                return "limit_cycle_2"
            elif cycle["cycle_length"] == 3:
                return "limit_cycle_3"
            else:
                return f"limit_cycle_{cycle['cycle_length']}"
        
        else:
            return "complex_dynamics"
    
    def _analyze_trajectory(self, trajectory: List[Dict], logger) -> Dict:
        """Analyze trajectory properties."""
        try:
            alphas = [s["alpha"] for s in trajectory]
            window_sizes = [s["window_size"] for s in trajectory]
            plane_errors = [s["plane_error"] for s in trajectory]
            
            # Calculate statistics
            alpha_stats = {
                "mean": float(np.mean(alphas)),
                "std": float(np.std(alphas)),
                "min": float(np.min(alphas)),
                "max": float(np.max(alphas)),
                "range": float(np.max(alphas) - np.min(alphas))
            }
            
            window_stats = {
                "mean": float(np.mean(window_sizes)),
                "std": float(np.std(window_sizes)),
                "min": float(np.min(window_sizes)),
                "max": float(np.max(window_sizes))
            }
            
            error_stats = {
                "mean": float(np.mean(plane_errors)),
                "std": float(np.std(plane_errors)),
                "min": float(np.min(plane_errors)),
                "max": float(np.max(plane_errors))
            }
            
            # Calculate trends
            alpha_trend = self._calculate_trend(alphas)
            error_trend = self._calculate_trend(plane_errors)
            
            return {
                "alpha_statistics": alpha_stats,
                "window_statistics": window_stats,
                "error_statistics": error_stats,
                "alpha_trend": alpha_trend,
                "error_trend": error_trend,
                "trajectory_length": len(trajectory)
            }
            
        except Exception as e:
            logger.warning(f"Trajectory analysis failed: {e}")
            return {
                "alpha_statistics": {},
                "window_statistics": {},
                "error_statistics": {},
                "alpha_trend": "unknown",
                "error_trend": "unknown",
                "trajectory_length": len(trajectory)
            }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend in a time series."""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend calculation
        x = np.arange(len(values))
        y = np.array(values)
        
        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        if abs(slope) < 1e-6:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def summarize(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize RG cycle detection results."""
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
            # Analyze cycle detection results
            cycle_results = [r for r in successful_results if r["has_cycles"]]
            
            summary["cycle_summary"] = {
                "total_trajectories": len(successful_results),
                "trajectories_with_cycles": len(cycle_results),
                "cycle_detection_rate": len(cycle_results) / len(successful_results)
            }
            
            # Analyze convergence types
            convergence_types = {}
            cycle_lengths = []
            
            for result in successful_results:
                conv_type = result["convergence_type"]
                convergence_types[conv_type] = convergence_types.get(conv_type, 0) + 1
                
                for cycle in result["cycle_results"]["cycles"]:
                    cycle_lengths.append(cycle["cycle_length"])
            
            summary["convergence_type_distribution"] = convergence_types
            summary["cycle_length_distribution"] = {
                length: cycle_lengths.count(length) for length in set(cycle_lengths)
            }
            
            # Analyze trajectory properties
            trajectory_lengths = [r["trajectory_length"] for r in successful_results]
            
            summary["trajectory_statistics"] = {
                "mean_length": float(np.mean(trajectory_lengths)),
                "std_length": float(np.std(trajectory_lengths)),
                "min_length": int(np.min(trajectory_lengths)),
                "max_length": int(np.max(trajectory_lengths))
            }
            
            # Discoveries
            discoveries = []
            
            if len(cycle_results) > 0:
                discoveries.append(f"Found cycles in {len(cycle_results)} out of {len(successful_results)} RG flows")
                
                # Find most common cycle type
                most_common_type = max(convergence_types.items(), key=lambda x: x[1])
                discoveries.append(f"Most common convergence type: {most_common_type[0]} ({most_common_type[1]} trajectories)")
                
                # Analyze cycle lengths
                if cycle_lengths:
                    avg_cycle_length = np.mean(cycle_lengths)
                    discoveries.append(f"Average cycle length: {avg_cycle_length:.1f}")
            else:
                discoveries.append("No cycles detected in any RG flows")
            
            # Check for fixed points
            fixed_points = sum(1 for r in successful_results if r["convergence_type"] == "fixed_point")
            if fixed_points > 0:
                discoveries.append(f"Found fixed points in {fixed_points} trajectories")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
