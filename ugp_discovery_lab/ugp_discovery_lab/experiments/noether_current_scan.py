"""
Noether current scan experiment.

Automatically derives candidate conserved currents J(M,G,L) under PR-1 sweep
using small symbolic D(x) (dissonance) and verifies ΔJ ≈ 0.
"""

from .base import Experiment
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import numpy as np
import sympy as sp
from sympy import symbols, simplify, expand, diff, integrate
import warnings

from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint


@register_experiment("noether_current_scan")
class NoetherCurrentScan(Experiment):
    """Scans for conserved currents using Noether's theorem approach."""
    
    def tasks(self) -> List[Dict]:
        """Generate tasks for Noether current scanning."""
        tasks = []
        
        # Get configuration
        scan_config = self.cfg.get("scan", {})
        max_degree = scan_config.get("max_degree", 3)
        max_coefficients = scan_config.get("max_coefficients", 8)
        tolerance = scan_config.get("tolerance", 1e-6)
        
        # Generate different current forms to test
        current_forms = self._generate_current_forms(max_degree, max_coefficients)
        
        for i, current_form in enumerate(current_forms):
            task_id = f"noether_scan_{i:03d}"
            tasks.append({
                "task_id": task_id,
                "current_form": current_form,
                "max_degree": max_degree,
                "max_coefficients": max_coefficients,
                "tolerance": tolerance,
                "scan_config": scan_config
            })
        
        return tasks
    
    def _generate_current_forms(self, max_degree: int, max_coefficients: int) -> List[Dict]:
        """Generate candidate current forms to test."""
        forms = []
        
        # Define symbolic variables
        M, G, L = symbols('M G L')
        
        # Generate systematic linear forms: J = a*M + b*G + c*L
        if max_degree >= 1:
            # Get coefficient grid from config
            coeffs = self.cfg.get("search", {}).get("grid", {}).get("coeffs", [-2, -1, 0, 1, 2])
            
            # Generate all combinations of coefficients
            for a in coeffs:
                for b in coeffs:
                    for c in coeffs:
                        # Skip trivial cases
                        if a == 0 and b == 0 and c == 0:
                            continue
                        
                        # Create linear form
                        if a != 0 and b != 0 and c != 0:
                            expr = a*M + b*G + c*L
                        elif a != 0 and b != 0:
                            expr = a*M + b*G
                        elif a != 0 and c != 0:
                            expr = a*M + c*L
                        elif b != 0 and c != 0:
                            expr = b*G + c*L
                        elif a != 0:
                            expr = a*M
                        elif b != 0:
                            expr = b*G
                        else:
                            expr = c*L
                        
                        forms.append({
                            "type": "linear_systematic",
                            "expression": str(expr),  # Convert to string for JSON serialization
                            "degree": 1,
                            "coefficients": [a, b, c],
                            "description": f"J = {a}*M + {b}*G + {c}*L"
                        })
        
        # Generate polynomial forms of increasing complexity
        for degree in range(1, max_degree + 1):
            # Linear combinations (legacy)
            if degree == 1:
                forms.extend([
                    {"type": "linear", "expression": str(M + G + L), "degree": 1},
                    {"type": "linear", "expression": str(M - G + L), "degree": 1},
                    {"type": "linear", "expression": str(M + G - L), "degree": 1},
                    {"type": "linear", "expression": str(M - G - L), "degree": 1},
                ])
            
            # Quadratic forms
            elif degree == 2:
                forms.extend([
                    {"type": "quadratic", "expression": str(M**2 + G**2 + L**2), "degree": 2},
                    {"type": "quadratic", "expression": str(M*G + G*L + L*M), "degree": 2},
                    {"type": "quadratic", "expression": str(M**2 - G**2 + L**2), "degree": 2},
                    {"type": "quadratic", "expression": str(M*G - G*L + L*M), "degree": 2},
                ])
            
            # Cubic forms
            elif degree == 3:
                forms.extend([
                    {"type": "cubic", "expression": str(M**3 + G**3 + L**3), "degree": 3},
                    {"type": "cubic", "expression": str(M*G*L), "degree": 3},
                    {"type": "cubic", "expression": str(M**2*G + G**2*L + L**2*M), "degree": 3},
                ])
        
        # Add some specific physics-inspired forms
        forms.extend([
            {"type": "physics", "expression": str(M**2 + G*L), "degree": 2, "description": "mass_squared_plus_coupling"},
            {"type": "physics", "expression": str(M*G + L**2), "degree": 2, "description": "mass_coupling_plus_lambda_squared"},
            {"type": "physics", "expression": str(M + G**2 + L**2), "degree": 2, "description": "mass_plus_gauge_squared"},
        ])
        
        return forms
    
    def run_task(self, task: Dict) -> Dict:
        """Run Noether current scan for a single current form."""
        task_id = task["task_id"]
        logger = get_logger(f"noether_current_scan:{task_id}",
                          (self.root / "results" / "logs" / f"{task_id}.log"))
        
        logger.info(f"Starting Noether current scan: {task_id}")
        
        current_form = task["current_form"]
        tolerance = task["tolerance"]
        
        try:
            # Generate test evolution data
            evolution_data = self._generate_test_evolution(logger)
            
            # Test current conservation
            conservation_result = self._test_current_conservation(
                current_form, evolution_data, tolerance, logger
            )
            
            # If promising, try exact verification
            exact_result = None
            if conservation_result["is_conserved"]:
                exact_result = self._verify_exact_conservation(
                    current_form, evolution_data, logger
                )
            
            # Convert SymPy expressions to strings for JSON serialization
            if exact_result and "derivative_expression" in exact_result:
                exact_result["derivative_expression"] = str(exact_result["derivative_expression"])
            if exact_result and "simplified_derivative" in exact_result:
                exact_result["simplified_derivative"] = str(exact_result["simplified_derivative"])
            
            # Compile results
            result = {
                "task_id": task_id,
                "current_form": current_form,
                "success": True,
                "evolution_data_points": len(evolution_data),
                "conservation_result": conservation_result,
                "exact_result": exact_result,
                "is_promising": conservation_result["is_conserved"],
                "conservation_error": conservation_result["max_error"]
            }
            
            logger.info(f"Noether current scan completed: {task_id}")
            logger.info(f"Conserved: {conservation_result['is_conserved']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Noether current scan: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _generate_test_evolution(self, logger) -> List[Dict]:
        """Generate test evolution data for current analysis."""
        # Generate synthetic evolution following UGP dynamics
        evolution_data = []
        
        # Initial state
        M, G, L = 1.0, 73.0, 823.0
        steps = 1000
        
        for step in range(steps):
            # Apply PR-1 sweep dynamics (simplified)
            # This simulates the evolution under PR-1 operations
            
            # Update M (mass) - follows GTE evolution
            M_new = M + 0.25 * G + 0.1 * L + np.random.normal(0, 0.01)
            
            # Update G (gauge) - follows Lucas sequence
            if step > 0:
                G_new = G + evolution_data[-1]["G"] + np.random.normal(0, 0.01)
            else:
                G_new = G + 1.0 + np.random.normal(0, 0.01)
            
            # Update L (lambda) - follows Fibonacci-like sequence
            if step > 1:
                L_new = L + evolution_data[-1]["L"] + evolution_data[-2]["L"] + np.random.normal(0, 0.01)
            elif step > 0:
                L_new = L + evolution_data[-1]["L"] + np.random.normal(0, 0.01)
            else:
                L_new = L + 1.0 + np.random.normal(0, 0.01)
            
            evolution_data.append({
                "step": step,
                "M": M_new,
                "G": G_new,
                "L": L_new,
                "dM": M_new - M,
                "dG": G_new - G,
                "dL": L_new - L
            })
            
            M, G, L = M_new, G_new, L_new
        
        return evolution_data
    
    def _test_current_conservation(self, current_form: Dict, evolution_data: List[Dict], 
                                 tolerance: float, logger) -> Dict:
        """Test if a current form is approximately conserved."""
        try:
            # Define symbolic variables
            M, G, L = symbols('M G L')
            
            # Get the expression (may be a string)
            expression_str = current_form["expression"]
            
            # Parse string back to SymPy expression if needed
            if isinstance(expression_str, str):
                try:
                    expression = sp.sympify(expression_str)
                except Exception as e:
                    logger.warning(f"Failed to parse expression '{expression_str}': {e}")
                    return {
                        "is_conserved": False,
                        "max_error": float('inf'),
                        "mean_error": float('inf'),
                        "error_history": [],
                        "error": f"Expression parsing failed: {e}"
                    }
            else:
                expression = expression_str
            
            # Calculate current values along evolution
            current_values = []
            for data_point in evolution_data:
                # Substitute values
                current_value = expression.subs({
                    M: data_point["M"],
                    G: data_point["G"],
                    L: data_point["L"]
                }).evalf()
                # Ensure the value is numeric
                try:
                    numeric_value = float(current_value)
                    current_values.append(numeric_value)
                except (TypeError, ValueError):
                    # If conversion fails, skip this point
                    continue
            
            # Calculate differences (discrete derivative)
            current_differences = []
            for i in range(1, len(current_values)):
                try:
                    diff_value = float(current_values[i] - current_values[i-1])
                    current_differences.append(diff_value)
                except (TypeError, ValueError):
                    # Skip invalid differences
                    continue
            
            # Check conservation (differences should be small)
            if not current_differences:
                max_error = float('inf')
                mean_error = float('inf')
                std_error = float('inf')
            else:
                # All differences should already be floats from the previous step
                max_error = max(abs(diff) for diff in current_differences)
                mean_error = np.mean([abs(diff) for diff in current_differences])
                std_error = np.std(current_differences)
            
            is_conserved = max_error < tolerance
            
            # Calculate conservation quality score
            conservation_score = max(0, 1 - max_error / tolerance)
            
            return {
                "current_values": [float(v) for v in current_values],
                "current_differences": [float(d) for d in current_differences],
                "max_error": float(max_error),
                "mean_error": float(mean_error),
                "std_error": float(std_error),
                "tolerance": float(tolerance),
                "is_conserved": bool(is_conserved),
                "conservation_score": float(conservation_score),
                "current_range": (float(min(current_values)), float(max(current_values))) if current_values else (0.0, 0.0)
            }
            
        except Exception as e:
            logger.warning(f"Current conservation test failed: {e}")
            return {
                "current_values": [],
                "current_differences": [],
                "max_error": float('inf'),
                "mean_error": float('inf'),
                "std_error": float('inf'),
                "tolerance": tolerance,
                "is_conserved": False,
                "conservation_score": 0.0,
                "current_range": (0, 0)
            }
    
    def _verify_exact_conservation(self, current_form: Dict, evolution_data: List[Dict], 
                                 logger) -> Dict:
        """Verify exact conservation using symbolic analysis."""
        try:
            # Define symbolic variables
            M, G, L = symbols('M G L')
            
            # Parse string back to SymPy expression if needed
            expression_str = current_form["expression"]
            if isinstance(expression_str, str):
                try:
                    expression = sp.sympify(expression_str)
                except Exception as e:
                    logger.warning(f"Failed to parse expression for exact verification: {e}")
                    return {
                        "expression": expression_str,
                        "simplified_expression": "parsing_failed",
                        "derivatives": {},
                        "exact_conservation_verified": False,
                        "conservation_type": "unknown",
                        "error": f"Expression parsing failed: {e}"
                    }
            else:
                expression = expression_str
            
            # Try to find exact conservation conditions
            # This is a simplified approach - in practice would use more sophisticated methods
            
            # Calculate symbolic derivatives
            dM_expr = diff(expression, M)
            dG_expr = diff(expression, G)
            dL_expr = diff(expression, L)
            
            # Check if the expression is constant (all derivatives zero)
            is_constant = (dM_expr == 0 and dG_expr == 0 and dL_expr == 0)
            
            # Check if it's a linear combination that might be conserved
            try:
                # Check if the expressions have the is_constant method and use it
                is_linear = (
                    (hasattr(dM_expr, 'is_constant') and dM_expr.is_constant()) and  # type: ignore
                    (hasattr(dG_expr, 'is_constant') and dG_expr.is_constant()) and  # type: ignore
                    (hasattr(dL_expr, 'is_constant') and dL_expr.is_constant())  # type: ignore
                )
            except (AttributeError, TypeError):
                # Handle cases where derivatives are literal constants or don't have the method
                is_linear = (dM_expr == 0 and dG_expr == 0 and dL_expr == 0)
            
            # Try to simplify the expression
            simplified_expr = simplify(expression)
            
            return {
                "expression": str(expression),
                "simplified_expression": str(simplified_expr),
                "derivatives": {
                    "dM": str(dM_expr),
                    "dG": str(dG_expr),
                    "dL": str(dL_expr)
                },
                "is_constant": bool(is_constant),
                "is_linear": bool(is_linear),
                "exact_conservation_verified": bool(is_constant),
                "conservation_type": str(self._classify_conservation_type(expression))
            }
            
        except Exception as e:
            logger.warning(f"Exact conservation verification failed: {e}")
            return {
                "expression": str(current_form["expression"]),
                "simplified_expression": "verification_failed",
                "derivatives": {},
                "is_constant": False,
                "is_linear": False,
                "exact_conservation_verified": False,
                "conservation_type": "unknown"
            }
    
    def _classify_conservation_type(self, expression) -> str:
        """Classify the type of conservation based on expression structure."""
        try:
            expr_str = str(expression)
            
            if "+" in expr_str and "-" not in expr_str:
                return "additive_conservation"
            elif "*" in expr_str:
                return "multiplicative_conservation"
            elif "**" in expr_str:
                return "polynomial_conservation"
            else:
                return "simple_conservation"
                
        except:
            return "unknown_conservation"
    
    def summarize(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize Noether current scan results."""
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
            # Analyze conservation results
            conserved_currents = [r for r in successful_results if r["is_promising"]]
            
            summary["conservation_summary"] = {
                "total_currents_tested": len(successful_results),
                "conserved_currents": len(conserved_currents),
                "conservation_rate": len(conserved_currents) / len(successful_results)
            }
            
            # Analyze conservation errors
            conservation_errors = [r["conservation_error"] for r in successful_results]
            
            summary["error_statistics"] = {
                "mean_error": float(np.mean(conservation_errors)),
                "std_error": float(np.std(conservation_errors)),
                "min_error": float(np.min(conservation_errors)),
                "max_error": float(np.max(conservation_errors))
            }
            
            # Analyze conservation types
            if conserved_currents:
                conservation_types = {}
                for result in conserved_currents:
                    if result["exact_result"]:
                        cons_type = result["exact_result"].get("conservation_type", "unknown")
                        conservation_types[cons_type] = conservation_types.get(cons_type, 0) + 1
                
                summary["conservation_types"] = conservation_types
            
            # Discoveries
            discoveries = []
            
            if len(conserved_currents) > 0:
                discoveries.append(f"Found {len(conserved_currents)} conserved currents out of {len(successful_results)} tested")
                
                # Find best conserved current
                best_current = min(successful_results, key=lambda x: x["conservation_error"])
                discoveries.append(f"Best conserved current: {best_current['current_form']['type']} (error: {best_current['conservation_error']:.2e})")
                
                # Check for exact conservation
                exact_conserved = [r for r in conserved_currents if r["exact_result"] and r["exact_result"]["exact_conservation_verified"]]
                if exact_conserved:
                    discoveries.append(f"Found {len(exact_conserved)} exactly conserved currents")
            else:
                discoveries.append("No conserved currents found in this scan")
            
            # Analyze current forms
            form_types = {}
            for result in successful_results:
                form_type = result["current_form"]["type"]
                form_types[form_type] = form_types.get(form_type, 0) + 1
            
            summary["form_type_distribution"] = form_types
            
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
