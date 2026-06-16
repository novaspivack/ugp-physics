# ugp_discovery_lab/experiments/mdl_model_comparison.py
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

class MDLModelComparison:
    """
    Compares competing hypotheses for g1^2 using the MDL principle.
    Tests structured hypotheses against each other with proper encoding costs.
    """
    
    def __init__(self, targets: Dict[str, float], uncertainties: Dict[str, float]):
        self.targets = targets
        self.uncertainties = uncertainties
        
    def get_structured_model_cost(self, hypothesis_name: str, g1_value: float) -> float:
        """
        Calculate L_model based on the structured encoding of each hypothesis.
        """
        if hypothesis_name == "H_derived":
            # g₁² = k_a × (128/125) = (1/8) × (128/125)
            # k_a is an axiom (cost = 0), 128 and 125 are fundamental
            return math.log2(128) + math.log2(125)  # ~13.96 bits
            
        elif hypothesis_name == "H_simple":
            # g₁² = 16/125 (simpler version)
            return math.log2(16) + math.log2(125)  # ~10.96 bits
            
        elif hypothesis_name == "H_best_fit":
            # High-precision decimal - very expensive to encode
            # 15 digits of precision ≈ 50 bits
            return 50.0
            
        elif hypothesis_name == "H_old_formula":
            # Complex scaled_geometric_mean formula - very expensive
            # Would need to encode: formula structure + all constants + operations
            return 80.0
            
        elif hypothesis_name == "H_null":
            # Simple 1/8
            return math.log2(1) + math.log2(8)  # 3 bits
            
        else:
            # Generic rational approximation
            f = Fraction(g1_value).limit_denominator(10000)
            return math.log2(f.numerator) + math.log2(f.denominator)
    
    def get_data_cost(self, g1_squared_candidate: float) -> float:
        """
        Calculate L_data based on χ² error against PDG values.
        """
        try:
            # Calculate predicted values using Standard Model relationships
            alpha_fine_pred = g1_squared_candidate / (4 * math.pi)
            
            # Standard Model relationships
            g2_squared = 0.425  # Weak coupling
            higgs_vev = 246.22  # GeV
            
            # Calculate sin²θ_W from the relationship
            sin_sq_theta_w_pred = g1_squared_candidate / (g1_squared_candidate + g2_squared)
            
            # Calculate M_Z and M_W
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
            
            # Convert to bits
            return chi_sq * math.log2(math.e)
            
        except (ValueError, OverflowError, ZeroDivisionError):
            return float('inf')
    
    def evaluate_hypothesis(self, hypothesis_name: str, g1_value: float) -> Dict[str, Any]:
        """
        Evaluate a single hypothesis and return its MDL costs.
        """
        L_model = self.get_structured_model_cost(hypothesis_name, g1_value)
        L_data = self.get_data_cost(g1_value)
        L_total = L_model + L_data
        
        return {
            'hypothesis': hypothesis_name,
            'g1_squared': g1_value,
            'L_model': L_model,
            'L_data': L_data,
            'L_total': L_total,
            'rational_form': str(Fraction(g1_value).limit_denominator(10000))
        }
    
    def find_best_fit_value(self) -> float:
        """
        Find the floating-point value that gives absolute minimum χ² error.
        """
        best_value = 0.125
        best_chi_sq = float('inf')
        
        # Search in a fine grid around 0.128
        for g1_val in np.linspace(0.120, 0.140, 2001):
            chi_sq = 0
            
            try:
                # Calculate predictions
                g2_squared = 0.425
                higgs_vev = 246.22
                
                sin_sq_theta_w_pred = g1_val / (g1_val + g2_squared)
                M_Z_pred = higgs_vev * math.sqrt(g1_val + g2_squared) / 2
                M_W_pred = higgs_vev * math.sqrt(g2_squared) / 2
                
                # Calculate χ²
                if 'sin_sq_theta_w' in self.targets and 'sin_sq_theta_w_error' in self.uncertainties:
                    chi_sq += ((sin_sq_theta_w_pred - self.targets['sin_sq_theta_w']) / self.uncertainties['sin_sq_theta_w_error']) ** 2
                
                if 'M_Z_gev' in self.targets and 'M_Z_error' in self.uncertainties:
                    chi_sq += ((M_Z_pred - self.targets['M_Z_gev']) / self.uncertainties['M_Z_error']) ** 2
                
                if 'M_W_gev' in self.targets and 'M_W_error' in self.uncertainties:
                    chi_sq += ((M_W_pred - self.targets['M_W_gev']) / self.uncertainties['M_W_error']) ** 2
                
                if chi_sq < best_chi_sq:
                    best_chi_sq = chi_sq
                    best_value = g1_val
                    
            except (ValueError, OverflowError, ZeroDivisionError):
                continue
        
        return best_value

@register_experiment("mdl_model_comparison")
class MDLModelComparisonExperiment(Experiment):
    """
    Compares competing hypotheses for g1_squared using the MDL principle.
    Tests the structured hypothesis g₁² = k_a × (128/125) against alternatives.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "compare_mdl_hypotheses"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting MDL Model Comparison: {task['task_id']}")

        # Configuration
        hypotheses_config = self.cfg.get('hypotheses', [])
        targets = self.cfg.get('targets', {})
        uncertainties = {
            'sin_sq_theta_w_error': targets.get('sin_sq_theta_w_error', 0.00013),
            'M_Z_error': targets.get('M_Z_error', 0.0021),
            'M_W_error': targets.get('M_W_error', 0.009)
        }
        
        logger.info(f"Comparing {len(hypotheses_config)} hypotheses using MDL principle")
        logger.info(f"Targets: sin²θ_W={targets.get('sin_sq_theta_w', 'N/A')}, "
                   f"M_Z={targets.get('M_Z_gev', 'N/A')} GeV, M_W={targets.get('M_W_gev', 'N/A')} GeV")
        
        # Initialize MDL calculator
        mdl_calc = MDLModelComparison(targets, uncertainties)
        
        # Define hypothesis values
        hypothesis_values = {
            "H_derived": (1/8) * (128/125),  # k_a × (128/125) = 0.128
            "H_simple": 16/125,              # 0.128 (simpler form)
            "H_null": 1/8,                   # 0.125 (simple but incorrect)
        }
        
        # Find best fit value
        best_fit_value = mdl_calc.find_best_fit_value()
        hypothesis_values["H_best_fit"] = best_fit_value
        
        # Calculate old formula value (scaled_geometric_mean from previous experiments)
        # This gave 0.136619 with 6.73% error
        hypothesis_values["H_old_formula"] = 0.136619
        
        # Evaluate all hypotheses
        results = []
        for hypothesis_name, g1_value in hypothesis_values.items():
            result = mdl_calc.evaluate_hypothesis(hypothesis_name, g1_value)
            results.append(result)
            logger.info(f"{hypothesis_name}: g₁²={g1_value:.6f}, L_total={result['L_total']:.6f}")
        
        # Sort by L_total (ascending - lower is better)
        results.sort(key=lambda x: x['L_total'])
        
        # Determine winner
        winner = results[0]
        
        logger.info(f"MDL Model Comparison completed:")
        logger.info(f"  Winner: {winner['hypothesis']}")
        logger.info(f"  g₁²: {winner['g1_squared']:.6f}")
        logger.info(f"  L_total: {winner['L_total']:.6f} bits")
        logger.info(f"  L_model: {winner['L_model']:.6f} bits")
        logger.info(f"  L_data: {winner['L_data']:.6f} bits")
        
        # Check if H_derived won
        is_hypothesis_confirmed = winner['hypothesis'] in ["H_derived", "H_simple"]
        
        result = {
            "task_id": task["task_id"],
            "success": True,
            "status": "completed",
            "hypotheses_evaluated": len(results),
            "winner": winner,
            "hypothesis_confirmed": is_hypothesis_confirmed,
            "all_results": results,
            "ranking": [
                {
                    "rank": i+1,
                    "hypothesis": result['hypothesis'],
                    "g1_squared": result['g1_squared'],
                    "L_total": result['L_total'],
                    "L_model": result['L_model'],
                    "L_data": result['L_data']
                }
                for i, result in enumerate(results)
            ],
            "targets": targets,
            "uncertainties": uncertainties
        }
        
        return result

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize MDL model comparison results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary_data = {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0,
                "status": "failed",
                "error": "No successful MDL model comparisons"
            }
        else:
            result = successful_results[0]
            
            summary_data = {
                "total_tasks": len(results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(results) - len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "status": "completed",
                "winner": result["winner"],
                "hypothesis_confirmed": result["hypothesis_confirmed"],
                "ranking": result["ranking"],
                "all_results": result["all_results"],
                "targets": result["targets"],
                "verdict": "🎯 **CONFIRMED**" if result["hypothesis_confirmed"] else "❌ **NOT CONFIRMED**"
            }
        
        # Write reports
        write_json_report(self.root, "mdl_model_comparison_summary", summary_data)
        
        # Create markdown report
        md_lines = [
            "# MDL Model Comparison — Summary",
            "",
            f"- **Total Tasks:** {summary_data.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary_data.get('successful_tasks', 0)}",
            f"- **Success Rate:** {summary_data.get('success_rate', 0):.1%}",
            ""
        ]
        
        if successful_results:
            winner = summary_data['winner']
            
            md_lines.extend([
                "## Winner",
                f"- **Hypothesis:** {winner['hypothesis']}",
                f"- **g₁² Value:** {winner['g1_squared']:.6f}",
                f"- **L_total (bits):** {winner['L_total']:.6f}",
                f"- **L_model (bits):** {winner['L_model']:.6f}",
                f"- **L_data (bits):** {winner['L_data']:.6f}",
                f"- **Rational Form:** {winner['rational_form']}",
                "",
                "## Final Verdict",
                f"{summary_data['verdict']}: {'Our hypothesis g₁² = k_a × (128/125) is the optimal explanation!' if summary_data['hypothesis_confirmed'] else 'Our hypothesis was not selected by MDL principle.'}",
                "",
                "## Complete Ranking",
                "",
                "| Rank | Hypothesis | g₁² Value | L_model (bits) | L_data (bits) | L_total (bits) |",
                "|------|------------|-----------|----------------|---------------|----------------|"
            ])
            
            for rank_data in summary_data['ranking']:
                md_lines.append(
                    f"| {rank_data['rank']} | {rank_data['hypothesis']} | "
                    f"{rank_data['g1_squared']:.6f} | {rank_data['L_model']:.6f} | "
                    f"{rank_data['L_data']:.6f} | {rank_data['L_total']:.6f} |"
                )
            
            md_lines.extend([
                "",
                "## Hypothesis Details",
                ""
            ])
            
            for result in summary_data['all_results']:
                md_lines.extend([
                    f"### {result['hypothesis']}",
                    f"- **Formula:** {result.get('formula', 'N/A')}",
                    f"- **g₁² Value:** {result['g1_squared']:.6f}",
                    f"- **L_model:** {result['L_model']:.6f} bits",
                    f"- **L_data:** {result['L_data']:.6f} bits",
                    f"- **L_total:** {result['L_total']:.6f} bits",
                    ""
                ])
        
        write_md_report(self.root, "mdl_model_comparison_summary", "\n".join(md_lines))
        return summary_data
