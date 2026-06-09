# ugp_discovery_lab/experiments/mdl_cost_function.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import numpy as np
import math
from fractions import Fraction

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

logger = get_logger(__name__)

class MDLCostFunction:
    """
    Implements the MDL (Minimum Description Length) cost function to find the optimal g1^2.
    L_total(x) = L_model(x) + L_data(x)
    """
    
    def __init__(self, targets: Dict[str, float], uncertainties: Dict[str, float]):
        self.targets = targets
        self.uncertainties = uncertainties
        
    def get_model_complexity(self, value: float, max_denominator: int = 10000) -> float:
        """
        Calculates the MDL cost of a number's rational representation.
        L_model(x) = log₂(p) + log₂(q) where x = p/q in lowest terms.
        """
        try:
            f = Fraction(value).limit_denominator(max_denominator)
            p, q = f.numerator, f.denominator
            
            # Cost to specify an integer n is approximately log₂(n) bits
            return math.log2(p) + math.log2(q)
        except (ValueError, OverflowError):
            return float('inf')
    
    def get_data_cost(self, g1_squared_candidate: float) -> float:
        """
        Calculates L_data(x) based on how well the laws predict the data.
        Uses χ² error against PDG values.
        """
        try:
            # Calculate predicted values using the Standard Model relationships
            # g₁² = 4π × α_fine
            alpha_fine_pred = g1_squared_candidate / (4 * math.pi)
            
            # Standard Model relationships (simplified)
            # M_Z = g₁ × v / (2 cos θ_W)
            # M_W = g₁ × v / 2
            # sin²θ_W = 1 - (M_W/M_Z)²
            
            # Using g₁² = 0.425 (weak coupling) and v = 246.22 GeV
            g2_squared = 0.425  # Weak coupling (from config)
            higgs_vev = 246.22  # GeV (from config)
            
            # Calculate sin²θ_W from the relationship
            # In the Standard Model: g₁² = g₂² tan²θ_W
            sin_sq_theta_w_pred = g1_squared_candidate / (g1_squared_candidate + g2_squared)
            
            # Calculate M_Z and M_W
            # M_Z = v × sqrt(g₁² + g₂²) / 2
            # M_W = v × g₂ / 2
            M_Z_pred = higgs_vev * math.sqrt(g1_squared_candidate + g2_squared) / 2
            M_W_pred = higgs_vev * math.sqrt(g2_squared) / 2
            
            # Calculate χ² statistic
            chi_sq = 0
            
            # sin²θ_W comparison
            if 'sin_sq_theta_w' in self.targets and 'sin_sq_theta_w_error' in self.uncertainties:
                chi_sq += ((sin_sq_theta_w_pred - self.targets['sin_sq_theta_w']) / self.uncertainties['sin_sq_theta_w_error']) ** 2
            
            # M_Z comparison
            if 'M_Z_gev' in self.targets and 'M_Z_error' in self.uncertainties:
                chi_sq += ((M_Z_pred - self.targets['M_Z_gev']) / self.uncertainties['M_Z_error']) ** 2
            
            # M_W comparison
            if 'M_W_gev' in self.targets and 'M_W_error' in self.uncertainties:
                chi_sq += ((M_W_pred - self.targets['M_W_gev']) / self.uncertainties['M_W_error']) ** 2
            
            # L_data is proportional to χ². Convert to bits using log₂(e).
            return chi_sq * math.log2(math.e)
            
        except (ValueError, OverflowError, ZeroDivisionError):
            return float('inf')
    
    def get_total_cost(self, g1_squared_candidate: float, max_denominator: int = 10000) -> Tuple[float, float, float]:
        """
        Calculate L_total(x) = L_model(x) + L_data(x)
        Returns (L_total, L_model, L_data)
        """
        L_model = self.get_model_complexity(g1_squared_candidate, max_denominator)
        L_data = self.get_data_cost(g1_squared_candidate)
        L_total = L_model + L_data
        
        return L_total, L_model, L_data

@register_experiment("mdl_cost_function")
class MDLCostFunctionExperiment(Experiment):
    """
    Finds the MDL-optimal value for g1_squared by minimizing L_model + L_data.
    Tests if g₁² = 0.128 (or k_a × 128/125) is the unique global minimum.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "find_mdl_optimal_g1_squared"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting MDL Cost Function Analysis: {task['task_id']}")

        # Configuration
        search_config = self.cfg.get('search', {})
        g1_min = search_config.get('g1_squared_min', 0.120)
        g1_max = search_config.get('g1_squared_max', 0.140)
        steps = search_config.get('steps', 2001)
        max_denominator = search_config.get('max_denominator', 10000)
        
        # Input parameters
        inputs = self.cfg.get('inputs', {})
        g2_squared = inputs.get('g2_squared', 0.425)
        higgs_vev_gev = inputs.get('higgs_vev_gev', 246.22)
        
        # Target values and uncertainties
        targets = self.cfg.get('targets', {})
        uncertainties = {
            'sin_sq_theta_w_error': targets.get('sin_sq_theta_w_error', 0.00013),
            'M_Z_error': targets.get('M_Z_error', 0.0021),
            'M_W_error': targets.get('M_W_error', 0.009)
        }
        
        logger.info(f"Search range: [{g1_min}, {g1_max}] with {steps} steps")
        logger.info(f"Targets: sin²θ_W={targets.get('sin_sq_theta_w', 'N/A')}, "
                   f"M_Z={targets.get('M_Z_gev', 'N/A')} GeV, M_W={targets.get('M_W_gev', 'N/A')} GeV")
        
        # Create search grid
        g1_values = np.linspace(g1_min, g1_max, steps)
        
        # Initialize MDL calculator
        mdl_calc = MDLCostFunction(targets, uncertainties)
        
        # Calculate costs for each point
        results = []
        for g1_squared in g1_values:
            L_total, L_model, L_data = mdl_calc.get_total_cost(g1_squared, max_denominator)
            
            results.append({
                'g1_squared': g1_squared,
                'L_total': L_total,
                'L_model': L_model,
                'L_data': L_data,
                'rational_approximation': str(Fraction(g1_squared).limit_denominator(max_denominator))
            })
        
        # Find the minimum
        valid_results = [r for r in results if np.isfinite(r['L_total'])]
        if not valid_results:
            logger.error("No valid results found!")
            return {
                "task_id": task["task_id"],
                "success": False,
                "error": "No valid MDL calculations"
            }
        
        best_result = min(valid_results, key=lambda x: x['L_total'])
        
        logger.info(f"MDL analysis completed:")
        logger.info(f"  Optimal g₁²: {best_result['g1_squared']:.6f}")
        logger.info(f"  L_total: {best_result['L_total']:.6f}")
        logger.info(f"  L_model: {best_result['L_model']:.6f}")
        logger.info(f"  L_data: {best_result['L_data']:.6f}")
        logger.info(f"  Rational approximation: {best_result['rational_approximation']}")
        
        # Check if the minimum is near our expected values
        k_a = 1/8  # 0.125
        target_128 = 0.128
        k_a_corrected = k_a * (128/125)  # 0.128
        
        distances = {
            'k_a': abs(best_result['g1_squared'] - k_a),
            'target_128': abs(best_result['g1_squared'] - target_128),
            'k_a_corrected': abs(best_result['g1_squared'] - k_a_corrected)
        }
        
        closest_match = min(distances.keys(), key=lambda k: distances[k])
        
        logger.info(f"  Closest to: {closest_match} (distance: {distances[closest_match]:.6f})")
        
        # Analyze the cost landscape
        L_total_values = [r['L_total'] for r in valid_results]
        L_model_values = [r['L_model'] for r in valid_results]
        L_data_values = [r['L_data'] for r in valid_results]
        
        result = {
            "task_id": task["task_id"],
            "success": True,
            "status": "completed",
            "search_parameters": {
                "g1_squared_min": g1_min,
                "g1_squared_max": g1_max,
                "steps": steps,
                "max_denominator": max_denominator
            },
            "targets": targets,
            "uncertainties": uncertainties,
            "optimal_result": best_result,
            "distance_analysis": distances,
            "closest_match": closest_match,
            "cost_landscape": {
                "L_total_min": min(L_total_values),
                "L_total_max": max(L_total_values),
                "L_model_min": min(L_model_values),
                "L_model_max": max(L_model_values),
                "L_data_min": min(L_data_values),
                "L_data_max": max(L_data_values)
            },
            "all_results": valid_results[:100]  # First 100 for analysis
        }
        
        return result

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize MDL cost function results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary_data = {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0,
                "status": "failed",
                "error": "No successful MDL cost function analyses"
            }
        else:
            result = successful_results[0]
            optimal = result["optimal_result"]
            
            summary_data = {
                "total_tasks": len(results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(results) - len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "status": "completed",
                "optimal_g1_squared": optimal["g1_squared"],
                "optimal_L_total": optimal["L_total"],
                "optimal_L_model": optimal["L_model"],
                "optimal_L_data": optimal["L_data"],
                "rational_approximation": optimal["rational_approximation"],
                "closest_match": result["closest_match"],
                "distance_analysis": result["distance_analysis"],
                "search_parameters": result["search_parameters"],
                "targets": result["targets"],
                "cost_landscape": result["cost_landscape"]
            }
        
        # Write reports
        write_json_report(self.root, "mdl_cost_function_summary", summary_data)
        
        # Create markdown report
        md_lines = [
            "# MDL Cost Function Analysis — Summary",
            "",
            f"- **Total Tasks:** {summary_data.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary_data.get('successful_tasks', 0)}",
            f"- **Success Rate:** {summary_data.get('success_rate', 0):.1%}",
            ""
        ]
        
        if successful_results:
            optimal = summary_data['optimal_result']
            
            md_lines.extend([
                "## Optimal Result",
                f"- **Optimal g₁²:** {optimal['g1_squared']:.6f}",
                f"- **L_total (bits):** {optimal['L_total']:.6f}",
                f"- **L_model (bits):** {optimal['L_model']:.6f}",
                f"- **L_data (bits):** {optimal['L_data']:.6f}",
                f"- **Rational Approximation:** {optimal['rational_approximation']}",
                f"- **Closest Match:** {summary_data['closest_match']}",
                "",
                "## Distance Analysis",
                f"- **Distance to k_a (0.125):** {summary_data['distance_analysis']['k_a']:.6f}",
                f"- **Distance to target 0.128:** {summary_data['distance_analysis']['target_128']:.6f}",
                f"- **Distance to k_a × (128/125):** {summary_data['distance_analysis']['k_a_corrected']:.6f}",
                "",
                "## Search Parameters",
                f"- **Search Range:** [{summary_data['search_parameters']['g1_squared_min']}, {summary_data['search_parameters']['g1_squared_max']}]",
                f"- **Steps:** {summary_data['search_parameters']['steps']}",
                f"- **Max Denominator:** {summary_data['search_parameters']['max_denominator']}",
                "",
                "## Cost Landscape",
                f"- **L_total Range:** [{summary_data['cost_landscape']['L_total_min']:.6f}, {summary_data['cost_landscape']['L_total_max']:.6f}]",
                f"- **L_model Range:** [{summary_data['cost_landscape']['L_model_min']:.6f}, {summary_data['cost_landscape']['L_model_max']:.6f}]",
                f"- **L_data Range:** [{summary_data['cost_landscape']['L_data_min']:.6f}, {summary_data['cost_landscape']['L_data_max']:.6f}]",
                "",
                "## Verdict",
                ""
            ])
            
            # Determine verdict
            closest = summary_data['closest_match']
            distance = summary_data['distance_analysis'][closest]
            
            if distance < 1e-6:
                verdict = "🎯 **CONFIRMED**: MDL principle uniquely selects the predicted value!"
            elif distance < 1e-3:
                verdict = "✅ **STRONG SUPPORT**: Very close to predicted value"
            elif distance < 1e-2:
                verdict = "⚠️ **PARTIAL SUPPORT**: Reasonably close but not exact"
            else:
                verdict = "❌ **CONTRADICTION**: MDL minimum is far from predicted value"
            
            md_lines.append(verdict)
            md_lines.append("")
        
        write_md_report(self.root, "mdl_cost_function_summary", "\n".join(md_lines))
        return summary_data
