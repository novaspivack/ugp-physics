"""
U(1) Gauge Coupling Derivation

Tests the hypothesis that the U(1) gauge coupling g₁ (where α_fine ≈ g₁² / 4π) 
can be derived from the UGP Elegant Kernel constants.
"""

import numpy as np
import math
from typing import Dict, List, Any
from pathlib import Path

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

logger = get_logger(__name__)


@register_experiment("u1_coupling_derivation")
class U1CouplingDerivation(Experiment):
    """
    Derives the U(1) gauge coupling from UGP Elegant Kernel constants.
    
    Hypothesis: g₁² is proportional to the norm of the flavor vector
    normalized by the geometric curvature.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for U(1) coupling derivation."""
        return [{"task_id": "u1_coupling_derivation"}]
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run U(1) coupling derivation."""
        task_id = task["task_id"]
        
        logger.info(f"Starting U(1) coupling derivation: {task_id}")
        
        try:
            # UGP Elegant Kernel constants (exact values)
            k_a = 1/8
            k_b = -3/2
            k_c = 4/3
            k_L2 = 7/512
            
            # Experimental values for comparison
            alpha_fine_experimental = 7.2973525693e-3  # Fine-structure constant
            g1_squared_experimental = 4 * math.pi * alpha_fine_experimental
            
            # Hypothesis: g₁² is proportional to the norm of the flavor vector
            # normalized by the geometric curvature
            flavor_norm_squared = k_a**2 + k_b**2 + k_c**2
            g1_squared_candidate = flavor_norm_squared / k_L2
            
            # Calculate derived fine-structure constant
            alpha_fine_derived = g1_squared_candidate / (4 * math.pi)
            
            # Calculate relative errors
            g1_error = abs(g1_squared_candidate - g1_squared_experimental) / g1_squared_experimental
            alpha_error = abs(alpha_fine_derived - alpha_fine_experimental) / alpha_fine_experimental
            
            # Additional analysis: check different hypotheses
            hypotheses = {
                "flavor_norm_over_curvature": g1_squared_candidate,
                "flavor_norm_squared_over_curvature": flavor_norm_squared**2 / k_L2,
                "curvature_over_flavor_norm": k_L2 / flavor_norm_squared,
                "sqrt_flavor_norm_over_curvature": math.sqrt(flavor_norm_squared) / k_L2,
            }
            
            # Find best hypothesis
            best_hypothesis = None
            best_error = float('inf')
            hypothesis_results = {}
            
            for name, g1_sq in hypotheses.items():
                alpha_derived = g1_sq / (4 * math.pi)
                error = abs(alpha_derived - alpha_fine_experimental) / alpha_fine_experimental
                
                hypothesis_results[name] = {
                    "g1_squared": float(g1_sq),
                    "alpha_derived": float(alpha_derived),
                    "relative_error": float(error)
                }
                
                if error < best_error:
                    best_error = error
                    best_hypothesis = name
            
            # Calculate additional derived constants
            derived_constants = {
                "alpha_fine": float(alpha_fine_derived),
                "g1_squared": float(g1_squared_candidate),
                "flavor_norm_squared": float(flavor_norm_squared),
                "geometric_curvature": float(k_L2),
                "ratio": float(flavor_norm_squared / k_L2)
            }
            
            result = {
                "task_id": task_id,
                "success": True,
                "elegant_kernel_constants": {
                    "k_a": float(k_a),
                    "k_b": float(k_b),
                    "k_c": float(k_c),
                    "k_L2": float(k_L2)
                },
                "experimental_values": {
                    "alpha_fine": float(alpha_fine_experimental),
                    "g1_squared": float(g1_squared_experimental)
                },
                "derived_values": derived_constants,
                "errors": {
                    "g1_squared_relative_error": float(g1_error),
                    "alpha_fine_relative_error": float(alpha_error)
                },
                "hypotheses": hypothesis_results,
                "best_hypothesis": {
                    "name": best_hypothesis,
                    "relative_error": float(best_error)
                },
                "order_of_magnitude_agreement": {
                    "g1_squared_oom": math.log10(g1_squared_candidate / g1_squared_experimental),
                    "alpha_fine_oom": math.log10(alpha_fine_derived / alpha_fine_experimental)
                }
            }
            
            logger.info(f"U(1) coupling derivation completed:")
            logger.info(f"  Derived g₁²: {g1_squared_candidate:.6e}")
            logger.info(f"  Experimental g₁²: {g1_squared_experimental:.6e}")
            logger.info(f"  Relative error: {g1_error:.3%}")
            logger.info(f"  Best hypothesis: {best_hypothesis} (error: {best_error:.3%})")
            
            return result
            
        except Exception as e:
            logger.error(f"U(1) coupling derivation failed for {task_id}: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize U(1) coupling derivation results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary: Dict[str, Any] = {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0,
                "status": "failed",
                "error": "No successful U(1) coupling derivations"
            }
        else:
            result = successful_results[0]  # Should be only one result
            
            summary = {
                "total_tasks": len(results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(results) - len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "status": "completed",
                "derived_g1_squared": result["derived_values"]["g1_squared"],
                "experimental_g1_squared": result["experimental_values"]["g1_squared"],
                "relative_error": result["errors"]["g1_squared_relative_error"],
                "order_of_magnitude_agreement": result["order_of_magnitude_agreement"],
                "best_hypothesis": result["best_hypothesis"],
                "elegant_kernel_constants": result["elegant_kernel_constants"],
                "all_hypotheses": result["hypotheses"]
            }
        
        # Write reports
        write_json_report(self.root, "u1_coupling_derivation_summary", summary)
        
        # Create markdown report
        md_lines = [
            "# U(1) Gauge Coupling Derivation — Summary",
            "",
            f"**Status:** {summary['status']}",
            ""
        ]
        
        if successful_results:
            md_lines.extend([
                "## Elegant Kernel Constants",
                f"- **k_a:** {summary['elegant_kernel_constants']['k_a']:.6f}",
                f"- **k_b:** {summary['elegant_kernel_constants']['k_b']:.6f}",
                f"- **k_c:** {summary['elegant_kernel_constants']['k_c']:.6f}",
                f"- **k_L2:** {summary['elegant_kernel_constants']['k_L2']:.6f}",
                "",
                "## Derived vs Experimental Values",
                f"- **Derived g₁²:** {summary['derived_g1_squared']:.6e}",
                f"- **Experimental g₁²:** {summary['experimental_g1_squared']:.6e}",
                f"- **Relative Error:** {summary['relative_error']:.3%}",
                "",
                "## Order of Magnitude Agreement",
                f"- **g₁² OOM:** {summary['order_of_magnitude_agreement']['g1_squared_oom']:.2f}",
                f"- **α_fine OOM:** {summary['order_of_magnitude_agreement']['alpha_fine_oom']:.2f}",
                "",
                "## Best Hypothesis",
                f"- **Name:** {summary['best_hypothesis']['name']}",
                f"- **Relative Error:** {summary['best_hypothesis']['relative_error']:.3%}",
                "",
                "## All Hypotheses",
                ""
            ])
            
            for name, hyp in summary['all_hypotheses'].items():
                md_lines.extend([
                    f"### {name}",
                    f"- **g₁²:** {hyp['g1_squared']:.6e}",
                    f"- **α_derived:** {hyp['alpha_derived']:.6e}",
                    f"- **Relative Error:** {hyp['relative_error']:.3%}",
                    ""
                ])
        
        write_md_report(self.root, "u1_coupling_derivation_summary", "\n".join(md_lines))
        
        return summary
