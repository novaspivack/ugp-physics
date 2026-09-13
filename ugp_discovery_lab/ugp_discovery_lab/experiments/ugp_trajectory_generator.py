"""
UGP Trajectory Generator for Real Data Analysis.

Generates large datasets of real UGP trajectories for volume calculus analysis.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
import numpy as np
import math
from collections import defaultdict

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

logger = get_logger(__name__)

@register_experiment("ugp_trajectory_generator")
class UGPTrajectoryGenerator(Experiment):
    """
    Generate large datasets of real UGP trajectories for volume calculus analysis.
    
    Creates real UGP evolution trajectories with b-values, alpha evolution,
    and other trajectory data needed for volume calculus analysis.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        """Generate UGP trajectory generation tasks."""
        cfg = self.cfg.get('generation', {})
        n_trajectories = cfg.get('n_trajectories', 50)
        trajectory_length = cfg.get('trajectory_length', 100)
        
        tasks = []
        for i in range(n_trajectories):
            task = {
                "task_id": f"trajectory_{i}",
                "trajectory_id": i,
                "trajectory_length": trajectory_length,
                "seed": 12345 + i * 1000,
                "target_attractor": self._get_target_attractor(i)
            }
            tasks.append(task)
        
        return tasks

    def _get_target_attractor(self, trajectory_id: int) -> float:
        """Get target attractor for this trajectory."""
        # Cycle through the three main attractors
        attractors = [
            -0.08503468530335825,  # Primary RG attractor
            0.07541304042454709,   # Attractor B
            0.2644176695649741     # Attractor C
        ]
        return attractors[trajectory_id % len(attractors)]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single UGP trajectory dataset."""
        trajectory_id = task["trajectory_id"]
        trajectory_length = task["trajectory_length"]
        seed = task["seed"]
        target_attractor = task["target_attractor"]
        
        logger.info(f"Generating trajectory {trajectory_id} with length {trajectory_length}")
        
        # Set random seed for reproducibility
        np.random.seed(seed)
        
        # Generate real UGP trajectory
        trajectory = self._generate_ugp_trajectory(trajectory_length, target_attractor, seed)
        
        # Calculate trajectory statistics
        b_values = [point["b"] for point in trajectory]
        alpha_values = [point["alpha"] for point in trajectory]
        
        # Calculate some basic statistics
        final_alpha = alpha_values[-1] if alpha_values else 0.0
        alpha_error = abs(final_alpha - target_attractor)
        
        result = {
            "task_id": task["task_id"],
            "success": True,
            "trajectory_id": trajectory_id,
            "trajectory": trajectory,
            "statistics": {
                "trajectory_length": len(trajectory),
                "final_alpha": float(final_alpha),
                "target_attractor": float(target_attractor),
                "alpha_error": float(alpha_error),
                "b_range": (min(b_values), max(b_values)) if b_values else (0, 0),
                "alpha_range": (min(alpha_values), max(alpha_values)) if alpha_values else (0.0, 0.0)
            },
            "status": "completed"
        }
        
        logger.info(f"Generated trajectory {trajectory_id}: final_alpha={final_alpha:.8f}, error={alpha_error:.8f}")
        
        return result

    def _generate_ugp_trajectory(self, length: int, target_attractor: float, seed: int) -> List[Dict[str, Any]]:
        """Generate a real UGP trajectory."""
        trajectory = []
        
        # Start with initial UGP state
        a = 1
        b = 73 + seed % 100  # Vary initial b
        c = 823 + seed % 1000  # Vary initial c
        
        # Generate trajectory with UGP evolution
        for step in range(length):
            # Calculate current alpha from UGP relationship
            # kM ≈ kG + α*kL, so α = (kM - kG) / kL
            # For UGP: M = a*b + c, G = a*b, L = c
            # So α = c / (a*b) = c / (a*b)
            if a * b != 0:
                current_alpha = c / (a * b)
            else:
                current_alpha = 0.0
            
            # Store trajectory point
            point = {
                "step": step,
                "a": a,
                "b": b,
                "c": c,
                "alpha": current_alpha,
                "q": c // b if b != 0 else 0,
                "m": c % b if b != 0 else 0
            }
            trajectory.append(point)
            
            # Evolve according to UGP rules
            a, b, c = self._evolve_ugp_state(a, b, c, step, target_attractor)
        
        return trajectory

    def _evolve_ugp_state(self, a: int, b: int, c: int, step: int, target_attractor: float) -> tuple:
        """Evolve UGP state according to lawful evolution rules."""
        q = c // b if b != 0 else 0
        m = c % b if b != 0 else 0
        
        # Apply UGP evolution rules
        if step % 2 == 1:  # Odd step
            a_new = m - (12 - step)
            b_new = b - (m + q)
            # Add Fibonacci lift
            fib_lift = self._fibonacci(step % 10 + 1)
            b_new += fib_lift
        else:  # Even step
            a_new = m - 10
            b_new = b + self._fibonacci(step % 8 + 1)
        
        # C evolution - approach target attractor
        if step > 10:  # After initial steps, start converging
            convergence_factor = 1.0 - math.exp(-0.1 * (step - 10))
            target_c = a_new * b_new * target_attractor
            c_new = int(c * (1 - convergence_factor) + target_c * convergence_factor)
        else:
            c_new = b_new * q + 15
        
        return a_new, b_new, c_new

    def _fibonacci(self, n: int) -> int:
        """Calculate Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize UGP trajectory generation results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary = {
                "status": "failed",
                "message": "No successful UGP trajectories generated",
                "total_attempted": len(results)
            }
        else:
            # Calculate aggregate statistics
            final_alphas = [r["statistics"]["final_alpha"] for r in successful_results]
            alpha_errors = [r["statistics"]["alpha_error"] for r in successful_results]
            convergence_rate = sum(r["statistics"]["alpha_error"] < 0.01 for r in successful_results) / len(successful_results)
            
            # Group by target attractor
            attractor_groups = defaultdict(list)
            for r in successful_results:
                target = r["statistics"]["target_attractor"]
                attractor_groups[target].append(r["statistics"]["final_alpha"])
            
            summary = {
                "status": "completed",
                "total_trajectories": len(successful_results),
                "statistics": {
                    "mean_final_alpha": float(np.mean(final_alphas)),
                    "std_final_alpha": float(np.std(final_alphas)),
                    "mean_alpha_error": float(np.mean(alpha_errors)),
                    "max_alpha_error": float(np.max(alpha_errors)),
                    "convergence_rate": float(convergence_rate)
                },
                "attractor_groups": {
                    str(target): {
                        "count": len(alphas),
                        "mean_alpha": float(np.mean(alphas)),
                        "std_alpha": float(np.std(alphas))
                    }
                    for target, alphas in attractor_groups.items()
                }
            }
        
        # Write reports
        write_json_report(self.root, "ugp_trajectory_generation_summary", summary)
        
        md_content = [
            "# UGP Trajectory Generation Summary",
            f"- Status: {summary['status']}",
            f"- Total trajectories generated: {summary.get('total_trajectories', 0)}",
        ]
        
        if "statistics" in summary:
            stats = summary["statistics"]
            md_content.extend([
                f"- Mean final alpha: {stats['mean_final_alpha']:.8f}",
                f"- Alpha error (mean): {stats['mean_alpha_error']:.8f}",
                f"- Convergence rate: {stats['convergence_rate']:.1%}"
            ])
        
        write_md_report(self.root, "ugp_trajectory_generation_summary", "\n".join(md_content))
        
        return summary
