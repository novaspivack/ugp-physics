"""
Reversible Core experiments for UGP Discovery Lab.
"""

from typing import List, Dict, Any
from pathlib import Path
import numpy as np
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from ..engines.reversible_uwca import ReversibleUWCA, EntropyTracker
from .base import Experiment


@register_experiment("reversible_core")
class ReversibleCore(Experiment):
    """
    Test reversible UWCA implementation with entropy tracking and information conservation.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate reversible core test tasks."""
        tasks = []
        
        # Get test configurations
        run_config = self.cfg.get("run", {})
        le_config = self.cfg.get("le_config", {})
        
        # Generate tasks for different configurations
        windows = run_config.get("windows", [10])
        steps = run_config.get("steps", 100)
        seed = run_config.get("seed", [1, 73, 823])
        
        for window_n in windows:
            task = {
                "task_id": f"reversible_{le_config.get('b_policy', 'fib')}_{window_n}",
                "window_n": window_n,
                "steps": steps,
                "seed": seed,
                "le_config": le_config,
                "test_type": "reversible_core"
            }
            
            if self.validate_task(task):
                tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} reversible core tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single reversible core test."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting reversible core test: {task_id}")
                
                # Extract parameters
                window_n = task["window_n"]
                steps = task["steps"]
                seed = task["seed"]
                le_config = task["le_config"]
                
                logger.info(f"Running reversible evolution: n={window_n}, steps={steps}")
                
                # Create reversible UWCA
                uwca_width = 32  # Fixed width for CA simulation
                uwca = ReversibleUWCA(uwca_width, "rule110", wrap=True)
                
                # Initialize with seed-based pattern
                initial_state = self._seed_to_ca_state(seed, uwca_width)
                
                # Run forward evolution
                logger.info("Running forward evolution...")
                forward_history = uwca.simulate_forward(initial_state, steps)
                
                # Run backward evolution
                logger.info("Running backward evolution...")
                backward_history = uwca.simulate_backward(steps)
                
                # Analyze information conservation
                info_analysis = self._analyze_information_conservation(
                    forward_history, backward_history, logger
                )
                
                # Run entropy tracking
                entropy_analysis = self._run_entropy_tracking(forward_history, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "window_n": window_n,
                    "steps": steps,
                    "seed": seed,
                    "le_config": le_config,
                    "forward_history": forward_history,
                    "backward_history": backward_history,
                    "information_analysis": info_analysis,
                    "entropy_analysis": entropy_analysis,
                    "uwca_info": uwca.get_history_info()
                }
                
                logger.info(f"Reversible core test {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Reversible core test {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _seed_to_ca_state(self, seed: List[int], width: int) -> List[int]:
        """Convert UGP seed to CA state."""
        # Simple conversion: use seed values to create a pattern
        state = [0] * width
        
        for i, val in enumerate(seed[:width]):
            state[i] = val % 2
        
        # Add some structure based on the seed
        if len(seed) >= 3:
            # Use seed values to create interesting patterns
            a, b, c = seed[0], seed[1], seed[2]
            
            # Create pattern based on seed values
            for i in range(width):
                if i % 7 == 0:  # Fibonacci-like spacing
                    state[i] = (state[i] + 1) % 2
        
        return state
    
    def _analyze_information_conservation(self, forward_history: List[List[int]], 
                                        backward_history: List[List[int]], 
                                        logger) -> Dict[str, Any]:
        """Analyze information conservation in reversible evolution."""
        logger.debug("Analyzing information conservation...")
        
        # Check if backward evolution reconstructs forward evolution
        reconstruction_accuracy = self._calculate_reconstruction_accuracy(
            forward_history, backward_history
        )
        
        # Calculate information flow metrics
        forward_entropy = [self._calculate_entropy(state) for state in forward_history]
        backward_entropy = [self._calculate_entropy(state) for state in backward_history]
        
        # Check for information conservation laws
        conservation_analysis = {
            "reconstruction_accuracy": reconstruction_accuracy,
            "forward_entropy_evolution": forward_entropy,
            "backward_entropy_evolution": backward_entropy,
            "entropy_conservation": abs(np.mean(forward_entropy) - np.mean(backward_entropy)) < 0.1,
            "information_lost": reconstruction_accuracy < 1.0
        }
        
        return conservation_analysis
    
    def _calculate_reconstruction_accuracy(self, forward: List[List[int]], 
                                         backward: List[List[int]]) -> float:
        """Calculate how accurately backward evolution reconstructs forward evolution."""
        if not forward or not backward:
            return 0.0
        
        # Compare states in reverse order
        min_len = min(len(forward), len(backward))
        matches = 0
        total_comparisons = 0
        
        for i in range(min_len):
            forward_idx = len(forward) - 1 - i
            backward_idx = i
            
            if forward_idx >= 0 and backward_idx < len(backward):
                forward_state = forward[forward_idx]
                backward_state = backward[backward_idx]
                
                if len(forward_state) == len(backward_state):
                    matches += sum(1 for f, b in zip(forward_state, backward_state) if f == b)
                    total_comparisons += len(forward_state)
        
        return matches / total_comparisons if total_comparisons > 0 else 0.0
    
    def _calculate_entropy(self, state: List[int]) -> float:
        """Calculate Shannon entropy of a binary state."""
        if not state:
            return 0.0
        
        ones = sum(state)
        zeros = len(state) - ones
        
        if ones == 0 or zeros == 0:
            return 0.0
        
        p1 = ones / len(state)
        p0 = zeros / len(state)
        
        return -(p1 * np.log2(p1) + p0 * np.log2(p0))
    
    def _run_entropy_tracking(self, history: List[List[int]], logger) -> Dict[str, Any]:
        """Run entropy tracking analysis."""
        logger.debug("Running entropy tracking analysis...")
        
        tracker = EntropyTracker()
        entropy_evolution = []
        
        for state in history:
            entropy = tracker.update(state)
            entropy_evolution.append(entropy)
        
        # Analyze entropy trends
        entropy_trend = self._analyze_entropy_trend(entropy_evolution)
        tracker_summary = tracker.get_entropy_trend()
        
        return {
            "entropy_evolution": entropy_evolution,
            "entropy_trend": entropy_trend,
            "tracker_summary": tracker_summary,
            "final_entropy": entropy_evolution[-1] if entropy_evolution else 0.0,
            "entropy_stability": np.std(entropy_evolution) < 0.1 if len(entropy_evolution) > 1 else True
        }
    
    def _analyze_entropy_trend(self, entropy_sequence: List[float]) -> Dict[str, Any]:
        """Analyze entropy trend over time."""
        if len(entropy_sequence) < 2:
            return {"trend": "insufficient_data", "slope": 0.0}
        
        # Fit linear trend
        x = np.arange(len(entropy_sequence))
        y = np.array(entropy_sequence)
        
        try:
            slope, intercept = np.polyfit(x, y, 1)
            
            if abs(slope) < 1e-6:
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            return {
                "trend": trend,
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": self._calculate_r_squared(x, y, slope, intercept)
            }
        except:
            return {"trend": "analysis_failed", "slope": 0.0}
    
    def _calculate_r_squared(self, x: np.ndarray, y: np.ndarray, slope: float, intercept: float) -> float:
        """Calculate R-squared for linear fit."""
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return float(1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0)
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize reversible core test results."""
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
            # Aggregate analysis
            all_reconstruction_accuracies = [
                r["information_analysis"]["reconstruction_accuracy"] 
                for r in successful_results
            ]
            
            all_entropy_stabilities = [
                r["entropy_analysis"]["entropy_stability"] 
                for r in successful_results
            ]
            
            summary["metrics"] = {
                "average_reconstruction_accuracy": float(np.mean(all_reconstruction_accuracies)),
                "entropy_conservation_rate": sum(all_entropy_stabilities) / len(all_entropy_stabilities),
                "information_conservation_verified": np.mean(all_reconstruction_accuracies) > 0.95,
                "entropy_stability_verified": sum(all_entropy_stabilities) / len(all_entropy_stabilities) > 0.8
            }
            
            # Discoveries
            discoveries = []
            
            if summary["metrics"]["information_conservation_verified"]:
                discoveries.append("Information conservation verified in reversible UWCA")
            
            if summary["metrics"]["entropy_stability_verified"]:
                discoveries.append("Entropy stability confirmed across reversible evolutions")
            
            # Check for specific entropy trends
            for r in successful_results:
                entropy_trend = r["entropy_analysis"]["entropy_trend"]["trend"]
                if entropy_trend == "stable":
                    discoveries.append("Stable entropy evolution detected")
                    break
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
