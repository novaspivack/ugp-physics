"""
Quadratic Noether Current Scan Experiment.

Search for conserved quadratic invariants of the form:
J = a·M² + b·G² + c·L² + d·M·G + e·M·L + f·G·L

This extends the linear Noether scan to quadratic forms, looking for
higher-order conserved quantities in UGP evolution.
"""

from .base import Experiment
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import numpy as np
import sympy as sp
from sympy import symbols, simplify, expand, diff
from itertools import product
import random

from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint


@register_experiment("noether_quadratic_scan")
class NoetherQuadraticScan(Experiment):
    """Scans for conserved quadratic currents in UGP evolution."""
    
    def tasks(self) -> List[Dict]:
        """Generate tasks for quadratic Noether current scanning."""
        tasks = []
        
        # Get configuration
        search_config = self.cfg.get("search", {})
        coeff_grid = search_config.get("coeff_grid", [-2, -1, 0, 1, 2])
        max_hits = search_config.get("max_hits", 10)
        tolerance_abs = search_config.get("tolerance_abs", 1e-8)
        sample_fraction = search_config.get("sample_fraction", 0.5)
        
        # Find input runs
        input_runs = self._find_input_runs()
        
        # Generate coefficient combinations
        coeff_combinations = list(product(coeff_grid, repeat=6))  # (a,b,c,d,e,f)
        
        # Filter out trivial cases
        filtered_combos = []
        for combo in coeff_combinations:
            a, b, c, d, e, f = combo
            # Skip if all coefficients are zero
            if all(x == 0 for x in combo):
                continue
            # Skip if only one coefficient is non-zero (linear cases)
            non_zero_count = sum(1 for x in combo if x != 0)
            if non_zero_count <= 1:
                continue
            filtered_combos.append(combo)
        
        # Get run configuration for generating test data
        run_config = self.cfg.get("run", {})
        steps = run_config.get("steps", 1000)
        window = run_config.get("window", 64)
        seeds = run_config.get("seed", [42, 173, 823])
        
        # Create tasks for each coefficient combination with generated test data
        for i, coeffs in enumerate(filtered_combos):
            task_id = f"quad_scan_test_{i:04d}"
            tasks.append({
                "task_id": task_id,
                "coefficients": {
                    "a": coeffs[0], "b": coeffs[1], "c": coeffs[2],
                    "d": coeffs[3], "e": coeffs[4], "f": coeffs[5]
                },
                "tolerance_abs": tolerance_abs,
                "sample_fraction": sample_fraction,
                "test_data": {
                    "steps": steps,
                    "window": window,
                    "seeds": seeds
                }
            })
        
        return tasks[:max_hits] if max_hits else tasks
    
    def _find_input_runs(self) -> List[Path]:
        """Find input runs matching the pattern."""
        runs_pattern = self.cfg.get("inputs", {}).get("runs", [])
        found_runs = []
        
        for pattern in runs_pattern:
            # Expand glob pattern
            if "**" in pattern:
                # Recursive search
                base_path = Path(pattern.replace("/**", ""))
                if base_path.exists():
                    for run_file in base_path.rglob("*experiment_results.json"):
                        found_runs.append(run_file)
            else:
                # Direct path
                run_path = Path(pattern)
                if run_path.exists():
                    found_runs.append(run_path)
        
        return found_runs
    
    def _generate_test_data(self, test_data: Dict, logger) -> List[Dict]:
        """Generate test evolution data for Noether current testing."""
        steps = test_data["steps"]
        window = test_data["window"]
        seeds = test_data["seeds"]
        
        # Use seeds for reproducibility
        np.random.seed(sum(seeds))
        
        evolution_data = []
        
        # Generate neutral test data without assuming any conservation laws
        for step in range(steps):
            # Generate M, G, L values using independent evolution patterns
            # NO assumption about conserved quantities - let the analysis discover them
            t = step / steps  # Normalized time
            
            # Generate independent evolution patterns for each variable
            # Use different frequencies and phases to create realistic but unbiased evolution
            phase1 = 2 * np.pi * t
            phase2 = 3 * np.pi * t
            phase3 = 5 * np.pi * t
            phase4 = 7 * np.pi * t
            
            # Generate M with its own evolution pattern
            M = 2.0 + 0.8 * np.sin(phase1) + 0.3 * np.cos(phase3) + 0.1 * np.random.normal()
            
            # Generate G with independent evolution pattern
            G = 1.5 + 0.6 * np.sin(phase2) + 0.4 * np.cos(phase4) + 0.1 * np.random.normal()
            
            # Generate L with its own independent evolution pattern
            L = 1.0 + 0.5 * np.sin(phase3) + 0.2 * np.cos(phase1 + phase2) + 0.1 * np.random.normal()
            
            # Add realistic temporal correlations (evolution has memory)
            if step > 0:
                # Add some memory to make the evolution more structured
                prev_M = evolution_data[-1]["M"]
                prev_G = evolution_data[-1]["G"]
                prev_L = evolution_data[-1]["L"]
                
                M = 0.95 * M + 0.05 * prev_M
                G = 0.95 * G + 0.05 * prev_G
                L = 0.95 * L + 0.05 * prev_L
            
            evolution_data.append({
                "step": step,
                "M": M,
                "G": G,
                "L": L,
                "t": t
            })
        
        logger.info(f"Generated {len(evolution_data)} test data points")
        return evolution_data
    
    def run_task(self, task: Dict) -> Dict:
        """Run quadratic Noether current scan for a single task."""
        task_id = task["task_id"]
        coeffs = task["coefficients"]
        tolerance_abs = task["tolerance_abs"]
        sample_fraction = task["sample_fraction"]
        test_data = task["test_data"]
        
        logger = get_logger(f"noether_quadratic_scan:{task_id}")
        logger.info(f"Starting quadratic Noether scan: {task_id}")
        logger.info(f"Testing coefficients: a={coeffs['a']}, b={coeffs['b']}, c={coeffs['c']}, d={coeffs['d']}, e={coeffs['e']}, f={coeffs['f']}")
        
        try:
            # Generate test evolution data
            evolution_data = self._generate_test_data(test_data, logger)
            if not evolution_data:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": "Failed to generate test data"
                }
            
            # Test quadratic current conservation
            conservation_result = self._test_quadratic_conservation(
                coeffs, evolution_data, tolerance_abs, sample_fraction, logger
            )
            
            # Compile results
            result = {
                "task_id": task_id,
                "coefficients": coeffs,
                "success": True,
                "evolution_data_points": len(evolution_data),
                "conservation_result": conservation_result,
                "is_conserved": conservation_result["is_conserved"],
                "max_abs_dJ": conservation_result["max_abs_dJ"],
                "mean_abs_dJ": conservation_result["mean_abs_dJ"],
                "std_dJ": conservation_result["std_dJ"],
                "n_evals": conservation_result["n_evals"]
            }
            
            logger.info(f"Quadratic Noether scan completed: {task_id}")
            logger.info(f"Conserved: {conservation_result['is_conserved']}")
            logger.info(f"Max |ΔJ|: {conservation_result['max_abs_dJ']:.2e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Quadratic Noether scan failed: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _load_evolution_data(self, run_path: Path) -> List[Dict]:
        """Load evolution data from a run summary."""
        try:
            with open(run_path, 'r') as f:
                data = json.load(f)
            
            # Extract evolution data from the run
            # This assumes the run contains time series data
            evolution_data = []
            
            # Look for time series data in various possible locations
            if "data" in data and "results" in data["data"]:
                results = data["data"]["results"]
                for result in results:
                    if "evolution_data" in result:
                        evolution_data.extend(result["evolution_data"])
                    elif "trajectory" in result:
                        evolution_data.extend(result["trajectory"])
            
            # If no evolution data found, create synthetic data for testing
            if not evolution_data:
                logger = get_logger("noether_quadratic_scan")
                logger.warning(f"No evolution data found in {run_path}, creating synthetic data")
                evolution_data = self._create_synthetic_data()
            
            return evolution_data
            
        except Exception as e:
            logger = get_logger("noether_quadratic_scan")
            logger.error(f"Failed to load evolution data from {run_path}: {e}")
            return []
    
    def _create_synthetic_data(self) -> List[Dict]:
        """Create synthetic evolution data for testing."""
        # Generate synthetic M, G, L evolution data
        np.random.seed(42)
        n_points = 1000
        
        # Create correlated evolution
        t = np.linspace(0, 10, n_points)
        M = 1.0 + 0.1 * np.sin(t) + 0.05 * np.random.randn(n_points)
        G = 0.5 + 0.2 * np.cos(t) + 0.03 * np.random.randn(n_points)
        L = 0.3 + 0.15 * np.sin(2*t) + 0.02 * np.random.randn(n_points)
        
        evolution_data = []
        for i in range(n_points):
            evolution_data.append({
                "M": float(M[i]),
                "G": float(G[i]),
                "L": float(L[i]),
                "step": i
            })
        
        return evolution_data
    
    def _test_quadratic_conservation(self, coeffs: Dict[str, int], 
                                   evolution_data: List[Dict],
                                   tolerance_abs: float,
                                   sample_fraction: float,
                                   logger) -> Dict[str, Any]:
        """Test if a quadratic current form is conserved."""
        try:
            # Define symbolic variables
            M, G, L = symbols('M G L')
            
            # Create quadratic expression
            a, b, c, d, e, f = coeffs["a"], coeffs["b"], coeffs["c"], coeffs["d"], coeffs["e"], coeffs["f"]
            expression = a*M**2 + b*G**2 + c*L**2 + d*M*G + e*M*L + f*G*L
            
            # Sample a fraction of the data for efficiency
            n_total = len(evolution_data)
            n_sample = max(1, int(n_total * sample_fraction))
            sample_indices = sorted(random.sample(range(n_total), n_sample))
            sample_data = [evolution_data[i] for i in sample_indices]
            
            # Calculate current values
            current_values = []
            for data_point in sample_data:
                try:
                    current_value = expression.subs({
                        M: data_point["M"],
                        G: data_point["G"],
                        L: data_point["L"]
                    }).evalf()
                    
                    # Ensure the value is numeric
                    numeric_value = float(current_value)
                    if not np.isnan(numeric_value) and not np.isinf(numeric_value):
                        current_values.append(numeric_value)
                except (TypeError, ValueError):
                    continue
            
            if len(current_values) < 2:
                return {
                    "current_values": [],
                    "current_differences": [],
                    "max_abs_dJ": float('inf'),
                    "mean_abs_dJ": float('inf'),
                    "std_dJ": float('inf'),
                    "tolerance": tolerance_abs,
                    "is_conserved": False,
                    "conservation_score": 0.0,
                    "n_evals": len(current_values)
                }
            
            # Calculate differences (discrete derivative)
            current_differences = []
            for i in range(1, len(current_values)):
                try:
                    diff_value = float(current_values[i] - current_values[i-1])
                    if not np.isnan(diff_value) and not np.isinf(diff_value):
                        current_differences.append(abs(diff_value))
                except (TypeError, ValueError):
                    continue
            
            if not current_differences:
                return {
                    "current_values": current_values,
                    "current_differences": [],
                    "max_abs_dJ": float('inf'),
                    "mean_abs_dJ": float('inf'),
                    "std_dJ": float('inf'),
                    "tolerance": tolerance_abs,
                    "is_conserved": False,
                    "conservation_score": 0.0,
                    "n_evals": len(current_values)
                }
            
            # Calculate conservation metrics
            max_abs_dJ = max(current_differences)
            mean_abs_dJ = np.mean(current_differences)
            std_dJ = np.std(current_differences)
            
            # Check conservation
            is_conserved = max_abs_dJ <= float(tolerance_abs)
            
            # Calculate conservation score (higher is better)
            conservation_score = max(0, 1 - (max_abs_dJ / float(tolerance_abs))) if float(tolerance_abs) > 0 else 0
            
            return {
                "current_values": current_values,
                "current_differences": current_differences,
                "max_abs_dJ": float(max_abs_dJ),
                "mean_abs_dJ": float(mean_abs_dJ),
                "std_dJ": float(std_dJ),
                "tolerance": tolerance_abs,
                "is_conserved": is_conserved,
                "conservation_score": float(conservation_score),
                "n_evals": len(current_values)
            }
            
        except Exception as e:
            logger.warning(f"Quadratic conservation test failed: {e}")
            return {
                "current_values": [],
                "current_differences": [],
                "max_abs_dJ": float('inf'),
                "mean_abs_dJ": float('inf'),
                "std_dJ": float('inf'),
                "tolerance": tolerance_abs,
                "is_conserved": False,
                "conservation_score": 0.0,
                "n_evals": 0,
                "error": str(e)
            }
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize quadratic Noether scan results."""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0
        }
        
        if successful_results:
            # Find conserved currents
            conserved_currents = [r for r in successful_results if r.get("is_conserved", False)]
            
            summary["conservation_summary"] = {
                "total_currents_tested": len(successful_results),
                "conserved_currents": len(conserved_currents),
                "conservation_rate": len(conserved_currents) / len(successful_results)
            }
            
            # Analyze conservation errors
            conservation_errors = [r["max_abs_dJ"] for r in successful_results if "max_abs_dJ" in r]
            
            if conservation_errors:
                summary["error_statistics"] = {
                    "mean_error": float(np.mean(conservation_errors)),
                    "std_error": float(np.std(conservation_errors)),
                    "min_error": float(np.min(conservation_errors)),
                    "max_error": float(np.max(conservation_errors))
                }
            
            # Find top hits
            top_hits = sorted(successful_results, key=lambda x: x.get("max_abs_dJ", float('inf')))[:10]
            summary["top_hits"] = []
            
            for hit in top_hits:
                summary["top_hits"].append({
                    "coefficients": hit["coefficients"],
                    "max_abs_dJ": hit["max_abs_dJ"],
                    "mean_abs_dJ": hit["mean_abs_dJ"],
                    "std_dJ": hit["std_dJ"],
                    "n_evals": hit["n_evals"],
                    "is_conserved": hit["is_conserved"]
                })
            
            # Discoveries
            discoveries = []
            
            if len(conserved_currents) > 0:
                discoveries.append(f"Found {len(conserved_currents)} conserved quadratic currents out of {len(successful_results)} tested")
                
                # Find best conserved current
                best_current = min(conserved_currents, key=lambda x: x["max_abs_dJ"])
                discoveries.append(f"Best conserved current: {best_current['coefficients']} (error: {best_current['max_abs_dJ']:.2e})")
            else:
                discoveries.append("No conserved quadratic currents found in this scan")
                
                # Find best candidate (smallest error)
                best_candidate = min(successful_results, key=lambda x: x["max_abs_dJ"])
                discoveries.append(f"Best candidate: {best_candidate['coefficients']} (error: {best_candidate['max_abs_dJ']:.2e})")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
