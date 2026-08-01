# ugp_discovery_lab/experiments/mdl_algebraic_proof_validation.py
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

class MDLAlgebraicProofValidator:
    """
    Validates the algebraic proof that g₁² = 16/125 using MDL principle.
    Specifically designed for the algebraic proof validation pathway.
    """
    
    def __init__(self, targets: Dict[str, float], uncertainties: Dict[str, float]):
        self.targets = targets
        self.uncertainties = uncertainties
        
    def get_structured_model_cost(self, hypothesis_name: str, g1_value: float) -> float:
        """
        Calculate L_model based on the structured encoding of each hypothesis.
        """
        if hypothesis_name == "H_algebraic_proof":
            # g₁² = 1/((k_a k_b k_c)² · 5³) = 16/125
            # This is the most elegant - just the fundamental constants
            return math.log2(16) + math.log2(125)  # ~10.96 bits
            
        elif hypothesis_name == "H_best_fit_float":
            # High-precision decimal - very expensive to encode
            # 15 digits of precision ≈ 50 bits
            return 50.0
            
        elif hypothesis_name == "H_bare_ka":
            # g₁² = k_a = 1/8 (simplest possible)
            return math.log2(8)  # ~3 bits
            
        elif hypothesis_name == "H_old_formula":
            # Complex scaled_geometric_mean formula - very expensive
            # Would need to encode: formula structure + all constants + operations
            return 80.0
            
        elif hypothesis_name == "H_null":
            # Simple 1/8
            return math.log2(1) + math.log2(8)  # 3 bits
            
        else:
            # Generic rational approximation
            frac = Fraction(g1_value).limit_denominator(10000)
            return math.log2(frac.numerator) + math.log2(frac.denominator)
    
    def get_data_cost(self, g1_value: float) -> float:
        """
        Calculate L_data = -log P(data|model) using χ² statistic.
        """
        try:
            chi_sq = 0
            
            # Calculate predictions from g₁²
            g2_squared = 0.425  # Fixed from previous analysis
            g3_squared = 0.118  # Fixed from previous analysis
            
            # sin²θ_W prediction
            sin_sq_theta_w_pred = 1 - (g1_value**2) / (g1_value**2 + g2_squared)
            
            # M_Z prediction (in GeV)
            v = 246.22  # GeV
            M_Z_pred = (v/2) * np.sqrt(g1_value**2 + g2_squared)
            
            # M_W prediction (in GeV)  
            M_W_pred = (v/2) * g2_squared / np.sqrt(g1_value**2 + g2_squared)
            
            # sin²θ_W comparison
            if 'sin_sq_theta_w' in self.targets and 'sin_sq_theta_w_error' in self.uncertainties:
                chi_sq += ((sin_sq_theta_w_pred - self.targets['sin_sq_theta_w']) / self.uncertainties['sin_sq_theta_w_error']) ** 2
            
            # M_Z comparison
            if 'M_Z_gev' in self.targets and 'M_Z_error' in self.uncertainties:
                chi_sq += ((M_Z_pred - self.targets['M_Z_gev']) / self.uncertainties['M_Z_error']) ** 2
            
            # M_W comparison
            if 'M_W_gev' in self.targets and 'M_W_error' in self.uncertainties:
                chi_sq += ((M_W_pred - self.targets['M_W_gev']) / self.uncertainties['M_W_error']) ** 2
            
            # Convert to bits using negative log-likelihood
            # L_data = -log P(data|model) ≈ chi_sq / 2 * log(2)
            logger.debug(f"Chi-squared value: {chi_sq}")
            return chi_sq / 2 * math.log2(math.e)
            
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
                g3_squared = 0.118
                
                # sin²θ_W prediction
                sin_sq_theta_w_pred = 1 - (g1_val**2) / (g1_val**2 + g2_squared)
                
                # M_Z prediction
                v = 246.22
                M_Z_pred = (v/2) * np.sqrt(g1_val**2 + g2_squared)
                
                # M_W prediction
                M_W_pred = (v/2) * g2_squared / np.sqrt(g1_val**2 + g2_squared)
                
                # Compare to targets
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

@register_experiment("mdl_algebraic_proof_validation")
class MDLAlgebraicProofValidationExperiment(Experiment):
    """
    Validates the algebraic proof that g₁² = 16/125 using MDL principle.
    Tests the structured hypothesis g₁² = 16/125 against alternatives.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "validate_algebraic_proof_mdl"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting MDL Algebraic Proof Validation: {task['task_id']}")

        # Configuration
        hypotheses_config = self.cfg.get('hypotheses', [])
        targets = self.cfg.get('targets', {})
        uncertainties = {
            'sin_sq_theta_w_error': targets.get('sin_sq_theta_w_error', 0.00013),
            'M_Z_error': targets.get('M_Z_error', 0.0021),
            'M_W_error': targets.get('M_W_error', 0.009)
        }
        
        logger.info(f"Validating {len(hypotheses_config)} hypotheses using MDL principle")
        logger.info(f"Targets: sin²θ_W={targets.get('sin_sq_theta_w', 'N/A')}, "
                   f"M_Z={targets.get('M_Z_gev', 'N/A')} GeV, M_W={targets.get('M_W_gev', 'N/A')} GeV")
        
        # Initialize MDL calculator
        mdl_calc = MDLAlgebraicProofValidator(targets, uncertainties)
        
        # Define hypothesis values based on configuration
        hypothesis_values = {}
        
        # Parse hypotheses from configuration
        for hypothesis in hypotheses_config:
            name = hypothesis['name']
            if hypothesis['type'] == 'algebraic_proof':
                hypothesis_values[name] = 16/125  # 0.128
            elif hypothesis['type'] == 'best_fit_float':
                # Find the best floating-point fit
                best_fit_value = mdl_calc.find_best_fit_value()
                hypothesis_values[name] = best_fit_value
            elif hypothesis['type'] == 'bare_ka':
                hypothesis_values[name] = 1/8  # 0.125
            elif hypothesis['type'] == 'old_formula':
                hypothesis_values[name] = 0.136619  # Previous scaled_geometric_mean result
            elif hypothesis['type'] == 'null':
                hypothesis_values[name] = 1/8  # 0.125
            else:
                logger.warning(f"Unknown hypothesis type: {hypothesis['type']}")
        
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
        
        logger.info(f"MDL Algebraic Proof Validation completed:")
        logger.info(f"  Winner: {winner['hypothesis']}")
        logger.info(f"  g₁²: {winner['g1_squared']:.6f}")
        logger.info(f"  L_total: {winner['L_total']:.6f} bits")
        logger.info(f"  L_model: {winner['L_model']:.6f} bits")
        logger.info(f"  L_data: {winner['L_data']:.6f} bits")
        
        # Check if algebraic proof won
        is_proof_confirmed = winner['hypothesis'] == "H_algebraic_proof"
        
        result = {
            "task_id": task["task_id"],
            "success": True,
            "status": "completed",
            "hypotheses_evaluated": len(results),
            "winner": winner,
            "proof_confirmed": is_proof_confirmed,
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
        """Summarize MDL algebraic proof validation results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {
                "status": "failed",
                "message": "No successful MDL validations completed",
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0
            }
        
        # Get the most recent successful result
        latest_result = successful_results[-1]
        
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(results) - len(successful_results),
            "success_rate": len(successful_results) / len(results) if results else 0.0,
            "proof_confirmed": latest_result.get("proof_confirmed", False),
            "winner": latest_result.get("winner", {}),
            "ranking": latest_result.get("ranking", []),
            "hypotheses_evaluated": latest_result.get("hypotheses_evaluated", 0)
        }
        
        return summary

    def _save_report(self, summary: Dict[str, Any]) -> None:
        """Save MDL algebraic proof validation report."""
        # Save JSON report
        write_json_report(self.root, "mdl_algebraic_proof_validation_summary", summary, self.cfg)
        
        # Create markdown report
        md_content = self._create_markdown_report(summary)
        write_md_report(self.root, "mdl_algebraic_proof_validation_summary", md_content, summary)
        
        logger.info("MDL algebraic proof validation report saved")
    
    def _create_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Create markdown report content."""
        md_lines = [
            "# MDL Algebraic Proof Validation — Summary",
            "",
            f"- **Total Tasks:** {summary.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary.get('successful_tasks', 0)}",
            f"- **Success Rate:** {summary.get('success_rate', 0):.1%}",
            ""
        ]
        
        if summary.get('status') == 'completed':
            winner = summary.get('winner', {})
            md_lines.extend([
                "## Winner",
                f"- **Hypothesis:** {winner.get('hypothesis', 'N/A')}",
                f"- **g₁² Value:** {winner.get('g1_squared', 0):.6f}",
                f"- **L_total:** {winner.get('L_total', 0):.6f} bits",
                f"- **Proof Confirmed:** {'✅ YES' if summary.get('proof_confirmed', False) else '❌ NO'}",
                ""
            ])
            
            # Add ranking
            ranking = summary.get('ranking', [])
            if ranking:
                md_lines.extend([
                    "## Hypothesis Ranking",
                    "| Rank | Hypothesis | g₁² | L_total | L_model | L_data |",
                    "|------|------------|-----|---------|---------|--------|"
                ])
                for item in ranking:
                    md_lines.append(
                        f"| {item.get('rank', 'N/A')} | {item.get('hypothesis', 'N/A')} | "
                        f"{item.get('g1_squared', 0):.6f} | {item.get('L_total', 0):.6f} | "
                        f"{item.get('L_model', 0):.6f} | {item.get('L_data', 0):.6f} |"
                    )
                md_lines.append("")
        
        return "\n".join(md_lines)
