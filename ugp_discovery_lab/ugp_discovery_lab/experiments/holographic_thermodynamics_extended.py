"""
Extended Holographic Thermodynamics Experiment

Implements Phase 11.5: Extended Optimization to find even better parameter combinations.
Tests finer parameter grids around optimal values and advanced combination forms.
"""

import json
import math
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import pearsonr
from itertools import product

from .base import Experiment, timing_decorator
from ..core.registry import register_experiment


@dataclass
class ExtendedParameterCombination:
    """Represents an extended parameter combination for testing."""
    block_size: int
    scaling_constant: float
    combination_type: str
    power_exponent: Optional[float] = None  # For power law combinations
    cv_entropy: float = 0.0
    cv_total_info: float = 0.0
    improvement_ratio: float = 0.0
    correlation: float = 0.0
    compensation_efficiency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ExtendedOptimizationResult:
    """Results from extended parameter optimization."""
    best_parameters: ExtendedParameterCombination
    total_combinations_tested: int
    improvement_found: bool
    best_improvement_ratio: float
    optimal_scaling_range: Tuple[float, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@register_experiment("holographic_thermodynamics_extended")
class HolographicThermodynamicsExtended(Experiment):
    """
    Extended holographic thermodynamics experiment with finer parameter optimization.
    
    This experiment tests finer parameter grids around optimal values and advanced
    combination forms to find even better parameter combinations.
    """
    
    def __init__(self, config: Dict[str, Any], root: Path):
        super().__init__(config, root)
        self.boundary_width = config.get("analysis", {}).get("boundary_width", 2)
        self.trajectory_length = config.get("analysis", {}).get("trajectory_length", 2000)
        
        # Extended optimization parameters
        self.block_sizes = config.get("optimization", {}).get("block_sizes", [1, 2])
        # Finer grid around optimal C = 0.1
        self.scaling_constants = config.get("optimization", {}).get("scaling_constants", 
                                                                   np.linspace(0.01, 0.5, 20))
        self.combination_types = config.get("optimization", {}).get("combination_types", 
                                                                   ["exponential", "power_law", "logarithmic"])
        self.power_exponents = config.get("optimization", {}).get("power_exponents", [0.5, 1.0, 1.5, 2.0])
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for extended holographic thermodynamics analysis."""
        return [{
            "task_id": "holographic_thermodynamics_extended_optimization",
            "description": "Extended optimization for even better Generalized Second Law parameters",
            "trajectory_length": self.trajectory_length,
            "config": self.cfg
        }]
    
    def _generate_synthetic_trajectory(self, n_steps: int = 2000) -> np.ndarray:
        """Generate a longer synthetic PR-1 lattice trajectory for better statistics."""
        lattice_size = 20
        trajectory = []
        current_state = np.random.randint(0, 2, (lattice_size, lattice_size))
        
        for step in range(n_steps):
            # Apply UGP-like evolution rules
            if np.random.random() < 0.3:
                i, j = np.random.randint(0, lattice_size, 2)
                current_state[i, j] = 1 - current_state[i, j]
            
            # Holographic correlations (information transfer)
            if step % 50 == 0:
                boundary_mask = self._get_boundary_mask(lattice_size, self.boundary_width)
                interior_mask = ~boundary_mask
                
                boundary_state = current_state[boundary_mask]
                interior_state = current_state[interior_mask]
                
                if len(boundary_state) > 0 and len(interior_state) > 0:
                    correlation_strength = 0.1
                    for i in range(min(len(boundary_state), len(interior_state))):
                        if np.random.random() < correlation_strength:
                            boundary_idx = np.where(boundary_mask.flatten())[0][i]
                            interior_idx = np.where(interior_mask.flatten())[0][i]
                            current_state.flat[boundary_idx] = current_state.flat[interior_idx]
            
            trajectory.append(current_state.copy())
        
        return np.array(trajectory)
    
    def _get_boundary_mask(self, lattice_size: int, boundary_width: int) -> np.ndarray:
        """Create a mask for the boundary region of the lattice."""
        mask = np.zeros((lattice_size, lattice_size), dtype=bool)
        
        for i in range(lattice_size):
            for j in range(lattice_size):
                if (i < boundary_width or i >= lattice_size - boundary_width or 
                    j < boundary_width or j >= lattice_size - boundary_width):
                    mask[i, j] = True
        
        return mask
    
    def _compute_entropy_with_block_size(self, lattice_state: np.ndarray, block_size: int) -> float:
        """Compute entropy using specified block size."""
        h, w = lattice_state.shape
        entropy = 0.0
        block_count = 0
        
        for i in range(0, h-block_size+1, block_size):
            for j in range(0, w-block_size+1, block_size):
                block = lattice_state[i:i+block_size, j:j+block_size]
                if block.shape == (block_size, block_size):
                    # Convert to integer
                    block_int = int(''.join(map(str, block.flatten())), 2)
                    
                    # Compute entropy contribution
                    if block_int > 0:
                        p = 1.0 / (2 ** (block_size * block_size))
                        entropy -= p * math.log2(p)
                    block_count += 1
        
        return entropy / block_count if block_count > 0 else 0.0
    
    def _compute_holographic_information(self, lattice_state: np.ndarray) -> float:
        """Compute holographic information as mutual information between boundary and interior."""
        boundary_mask = self._get_boundary_mask(lattice_state.shape[0], self.boundary_width)
        interior_mask = ~boundary_mask
        
        boundary_state = lattice_state[boundary_mask].flatten()
        interior_state = lattice_state[interior_mask].flatten()
        
        if len(boundary_state) == 0 or len(interior_state) == 0:
            return 0.0
        
        # Compute mutual information
        boundary_discrete = (boundary_state * 255).astype(int)
        interior_discrete = (interior_state * 255).astype(int)
        
        # Create joint distribution
        joint_counts = {}
        for b_val, i_val in zip(boundary_discrete, interior_discrete):
            key = (b_val, i_val)
            joint_counts[key] = joint_counts.get(key, 0) + 1
        
        # Normalize to probabilities
        total = sum(joint_counts.values())
        joint_probs = {k: v/total for k, v in joint_counts.items()}
        
        # Compute marginal probabilities
        boundary_probs = {}
        interior_probs = {}
        
        for (b_val, i_val), prob in joint_probs.items():
            boundary_probs[b_val] = boundary_probs.get(b_val, 0) + prob
            interior_probs[i_val] = interior_probs.get(i_val, 0) + prob
        
        # Compute mutual information
        mi = 0.0
        for (b_val, i_val), joint_prob in joint_probs.items():
            if joint_prob > 0:
                boundary_prob = boundary_probs.get(b_val, 0)
                interior_prob = interior_probs.get(i_val, 0)
                if boundary_prob > 0 and interior_prob > 0:
                    mi += joint_prob * math.log2(joint_prob / (boundary_prob * interior_prob))
        
        return mi
    
    def _combine_information_extended(self, entropy: float, holographic_info: float, 
                                    scaling_constant: float, combination_type: str, 
                                    power_exponent: Optional[float] = None) -> float:
        """Combine entropy and holographic information using extended methods."""
        if combination_type == "exponential":
            return entropy * math.exp(scaling_constant * holographic_info)
        elif combination_type == "power_law":
            if power_exponent is None:
                power_exponent = 1.0
            return entropy * (1 + scaling_constant * holographic_info ** power_exponent)
        elif combination_type == "logarithmic":
            return entropy * (1 + scaling_constant * math.log(1 + abs(holographic_info)))
        elif combination_type == "hyperbolic":
            return entropy * (1 + scaling_constant * math.tanh(holographic_info))
        elif combination_type == "information_theoretic":
            # Account for mutual information between S and I_holo
            return entropy + holographic_info - abs(entropy - holographic_info) * scaling_constant
        else:
            raise ValueError(f"Unknown combination type: {combination_type}")
    
    def _test_extended_parameter_combination(self, trajectory: np.ndarray, block_size: int, 
                                           scaling_constant: float, combination_type: str,
                                           power_exponent: Optional[float] = None) -> ExtendedParameterCombination:
        """Test a specific extended parameter combination."""
        
        # Compute information budget over time
        entropy_values = []
        holographic_values = []
        total_info_values = []
        
        for lattice_state in trajectory:
            # Compute entropy with specified block size
            entropy = self._compute_entropy_with_block_size(lattice_state, block_size)
            entropy_values.append(entropy)
            
            # Compute holographic information
            holographic_info = self._compute_holographic_information(lattice_state)
            holographic_values.append(holographic_info)
            
            # Combine information using extended method
            total_info = self._combine_information_extended(entropy, holographic_info, 
                                                          scaling_constant, combination_type, power_exponent)
            total_info_values.append(total_info)
        
        # Calculate conservation metrics
        entropy_cv = float(np.std(entropy_values, ddof=1) / abs(np.mean(entropy_values)) 
                          if np.mean(entropy_values) != 0 else float('inf'))
        total_info_cv = float(np.std(total_info_values, ddof=1) / abs(np.mean(total_info_values)) 
                             if np.mean(total_info_values) != 0 else float('inf'))
        
        # Calculate improvement ratio (lower CV is better)
        improvement_ratio = entropy_cv / total_info_cv if total_info_cv > 0 else 0.0
        
        # Calculate correlation
        try:
            correlation = float(pearsonr(entropy_values, holographic_values)[0])  # type: ignore
        except:
            correlation = 0.0
        
        # Calculate compensation efficiency
        entropy_changes = np.diff(entropy_values)
        holographic_changes = np.diff(holographic_values)
        
        compensated_decreases = 0
        total_decreases = 0
        
        for i in range(len(entropy_changes)):
            if entropy_changes[i] < 0:  # Entropy decrease
                total_decreases += 1
                if holographic_changes[i] > 0:  # Holographic increase
                    compensated_decreases += 1
        
        compensation_efficiency = compensated_decreases / total_decreases if total_decreases > 0 else 0.0
        
        return ExtendedParameterCombination(
            block_size=block_size,
            scaling_constant=scaling_constant,
            combination_type=combination_type,
            power_exponent=power_exponent,
            cv_entropy=entropy_cv,
            cv_total_info=total_info_cv,
            improvement_ratio=improvement_ratio,
            correlation=correlation,
            compensation_efficiency=compensation_efficiency
        )
    
    @timing_decorator
    def run_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the extended holographic thermodynamics analysis."""
        
        self.logger.info("Generating extended trajectory for advanced optimization analysis...")
        
        # Generate longer trajectory for better statistics
        trajectory = self._generate_synthetic_trajectory(n_steps=self.trajectory_length)
        
        # Calculate total combinations
        total_combinations = 0
        for block_size in self.block_sizes:
            for scaling_constant in self.scaling_constants:
                for combination_type in self.combination_types:
                    if combination_type == "power_law":
                        total_combinations += len(self.power_exponents)
                    else:
                        total_combinations += 1
        
        self.logger.info(f"Testing {total_combinations} extended parameter combinations...")
        
        # Test all extended parameter combinations
        all_combinations = []
        best_improvement = 0.0
        best_combination = None
        
        for block_size, scaling_constant, combination_type in product(
            self.block_sizes, self.scaling_constants, self.combination_types
        ):
            if combination_type == "power_law":
                for power_exponent in self.power_exponents:
                    combination = self._test_extended_parameter_combination(
                        trajectory, block_size, scaling_constant, combination_type, power_exponent
                    )
                    all_combinations.append(combination.to_dict())
                    
                    if combination.improvement_ratio > best_improvement:
                        best_improvement = combination.improvement_ratio
                        best_combination = combination
            else:
                combination = self._test_extended_parameter_combination(
                    trajectory, block_size, scaling_constant, combination_type
                )
                all_combinations.append(combination.to_dict())
                
                if combination.improvement_ratio > best_improvement:
                    best_improvement = combination.improvement_ratio
                    best_combination = combination
        
        # Find optimal scaling range (combinations with > 90% of best improvement)
        threshold = best_improvement * 0.9
        optimal_scaling_values = [c["scaling_constant"] for c in all_combinations 
                                if c["improvement_ratio"] >= threshold]
        optimal_scaling_range = (min(optimal_scaling_values), max(optimal_scaling_values)) if optimal_scaling_values else (0.0, 0.0)
        
        # Create extended optimization result
        optimization_result = ExtendedOptimizationResult(
            best_parameters=best_combination or ExtendedParameterCombination(0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0),
            total_combinations_tested=len(all_combinations),
            improvement_found=best_improvement > 1.0,
            best_improvement_ratio=best_improvement,
            optimal_scaling_range=optimal_scaling_range
        )
        
        # Generate results
        results = {
            "experiment": "holographic_thermodynamics_extended",
            "success": True,
            "trajectory_length": len(trajectory),
            "optimization_result": optimization_result.to_dict(),
            "all_combinations": all_combinations,
            "generalized_second_law_supported": best_improvement > 1.2,  # Require 20% improvement
            "best_parameters": best_combination.to_dict() if best_combination else None
        }
        
        return results
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize the extended holographic thermodynamics results."""
        
        if not results:
            return {
                "summary_type": "holographic_thermodynamics_extended",
                "success": False,
                "error": "No results to summarize"
            }
        
        # Combine all results
        all_optimizations = []
        all_combinations = []
        
        for result in results:
            if result.get("success", False):
                all_optimizations.append(result.get("optimization_result", {}))
                all_combinations.extend(result.get("all_combinations", []))
        
        # Find overall best combination
        best_combination = None
        best_improvement = 0.0
        
        for combination in all_combinations:
            improvement = combination.get("improvement_ratio", 0.0)
            if improvement > best_improvement:
                best_improvement = improvement
                best_combination = combination
        
        # Calculate statistics
        total_combinations_tested = sum(opt.get("total_combinations_tested", 0) for opt in all_optimizations)
        improvements_found = sum(1 for opt in all_optimizations if opt.get("improvement_found", False))
        
        summary = {
            "summary_type": "holographic_thermodynamics_extended",
            "success": True,
            "total_tasks": len(results),
            "successful_tasks": len([r for r in results if r.get("success", False)]),
            "total_combinations_tested": total_combinations_tested,
            "improvements_found": improvements_found,
            "best_improvement_ratio": best_improvement,
            "generalized_second_law_supported": best_improvement > 1.2,
            "best_parameters": best_combination,
            "optimization_success": best_improvement > 1.0,
            "scientific_interpretation": (
                f"Extended optimization tested {total_combinations_tested} parameter combinations. "
                f"Found {improvements_found} combinations with improvement. "
                f"Best improvement ratio: {best_improvement:.3f}. "
                + ("Significant improvement achieved with extended optimization." if best_improvement > 1.2 
                   else "Extended optimization provides further insights for refinement.") +
                " This represents advanced investigation of the theoretical framework."
            )
        }
        
        return summary
