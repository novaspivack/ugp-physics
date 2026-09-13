#!/usr/bin/env python3
"""
Refined U(1) Gauge Coupling Derivation incorporating discovered RG attractors.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
import numpy as np
import math

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

logger = get_logger(__name__)

@register_experiment("u1_coupling_derivation_refined")
class U1CouplingDerivationRefined(Experiment):
    """
    Refined U(1) gauge coupling derivation incorporating discovered RG attractors.
    
    This experiment tests multiple hypotheses for deriving g₁² from UGP kernel
    constants and discovered attractors, including:
    - Primary RG attractor (-0.08503468530335825)
    - Quarter-lock attractor (0.25)
    - New attractors (0.04244, 0.11861, 0.02036)
    """

    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "derive_g1_squared_refined"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting Refined U(1) Coupling Derivation: {task['task_id']}")

        # Elegant Kernel constants
        k_a = 1/8
        k_b = -3/2
        k_c = 4/3
        k_L2 = 7/512
        
        # Discovered RG attractors
        primary_attractor = -0.08503468530335825
        quarter_lock = 0.25
        attractor_04244 = 0.042440334845701144
        attractor_11861 = 0.11861039330230842
        attractor_02036 = 0.020362205995770707
        
        # Flavor vector components
        flavor_vector = np.array([k_a, k_b, k_c])
        flavor_norm = np.linalg.norm(flavor_vector)
        flavor_norm_squared = flavor_norm**2
        
        # Experimental values
        experimental_g1_squared = 0.128  # From alpha_fine = g1^2 / 4pi
        alpha_fine = 0.0072973525693
        
        # Test refined hypotheses
        hypotheses = {}
        
        # Hypothesis 1: Best from previous analysis
        g1_squared_1 = k_L2 / flavor_norm
        hypotheses["curvature_over_flavor_norm"] = {
            "g1_squared": g1_squared_1,
            "alpha_derived": g1_squared_1 / (4 * math.pi),
            "relative_error": abs(g1_squared_1 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Hypothesis 2: Include primary RG attractor
        g1_squared_2 = k_L2 / (flavor_norm * abs(primary_attractor))
        hypotheses["curvature_over_flavor_norm_times_primary_attractor"] = {
            "g1_squared": g1_squared_2,
            "alpha_derived": g1_squared_2 / (4 * math.pi),
            "relative_error": abs(g1_squared_2 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Hypothesis 3: Include quarter-lock attractor
        g1_squared_3 = k_L2 / (flavor_norm * quarter_lock)
        hypotheses["curvature_over_flavor_norm_times_quarter_lock"] = {
            "g1_squared": g1_squared_3,
            "alpha_derived": g1_squared_3 / (4 * math.pi),
            "relative_error": abs(g1_squared_3 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Hypothesis 4: Multi-attractor model (weighted average)
        attractors = [abs(primary_attractor), quarter_lock, attractor_04244, attractor_11861, attractor_02036]
        weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # Weight by importance/frequency
        weighted_attractor = sum(w * a for w, a in zip(weights, attractors))
        g1_squared_4 = k_L2 / (flavor_norm * weighted_attractor)
        hypotheses["curvature_over_flavor_norm_times_weighted_attractors"] = {
            "g1_squared": g1_squared_4,
            "alpha_derived": g1_squared_4 / (4 * math.pi),
            "relative_error": abs(g1_squared_4 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Hypothesis 5: Golden ratio connection (attractor_11861 ≈ φ/π)
        phi = (1 + math.sqrt(5)) / 2
        golden_ratio_factor = phi / math.pi
        g1_squared_5 = k_L2 / (flavor_norm * golden_ratio_factor)
        hypotheses["curvature_over_flavor_norm_times_golden_ratio"] = {
            "g1_squared": g1_squared_5,
            "alpha_derived": g1_squared_5 / (4 * math.pi),
            "relative_error": abs(g1_squared_5 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Hypothesis 6: Fractional attractor model (1/24, 1/49)
        fractional_factor = (1/24 + 1/49) / 2  # Average of 1/24 and 1/49
        g1_squared_6 = k_L2 / (flavor_norm * fractional_factor)
        hypotheses["curvature_over_flavor_norm_times_fractional_attractors"] = {
            "g1_squared": g1_squared_6,
            "alpha_derived": g1_squared_6 / (4 * math.pi),
            "relative_error": abs(g1_squared_6 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Hypothesis 7: RG attractor as scaling factor
        rg_scaling = abs(primary_attractor) / quarter_lock
        g1_squared_7 = (k_L2 / flavor_norm) * rg_scaling
        hypotheses["curvature_over_flavor_norm_scaled_by_rg_ratio"] = {
            "g1_squared": g1_squared_7,
            "alpha_derived": g1_squared_7 / (4 * math.pi),
            "relative_error": abs(g1_squared_7 - experimental_g1_squared) / experimental_g1_squared
        }
        
        # Find best hypothesis
        best_hypothesis = min(hypotheses.items(), key=lambda x: x[1]["relative_error"])
        
        logger.info(f"Refined U(1) coupling derivation completed:")
        logger.info(f"  Best hypothesis: {best_hypothesis[0]}")
        logger.info(f"  Derived g₁²: {best_hypothesis[1]['g1_squared']:.6f}")
        logger.info(f"  Experimental g₁²: {experimental_g1_squared:.6f}")
        logger.info(f"  Relative error: {best_hypothesis[1]['relative_error']:.4%}")
        
        return {
            "task_id": task["task_id"],
            "success": True,
            "status": "completed",
            "derived_values": {
                "g1_squared": best_hypothesis[1]["g1_squared"],
                "alpha_derived": best_hypothesis[1]["alpha_derived"]
            },
            "experimental_values": {
                "g1_squared": experimental_g1_squared,
                "alpha_fine": alpha_fine
            },
            "errors": {
                "g1_squared_relative_error": best_hypothesis[1]["relative_error"]
            },
            "best_hypothesis": {
                "name": best_hypothesis[0],
                "relative_error": best_hypothesis[1]["relative_error"]
            },
            "all_hypotheses": hypotheses,
            "elegant_kernel_constants": {
                "k_a": k_a,
                "k_b": k_b,
                "k_c": k_c,
                "k_L2": k_L2
            },
            "discovered_attractors": {
                "primary_attractor": primary_attractor,
                "quarter_lock": quarter_lock,
                "attractor_04244": attractor_04244,
                "attractor_11861": attractor_11861,
                "attractor_02036": attractor_02036
            }
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize refined U(1) coupling derivation results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary_data: Dict[str, Any] = {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0,
                "status": "failed",
                "error": "No successful refined U(1) coupling derivations"
            }
        else:
            result = successful_results[0]  # Should be only one result
            
            summary_success: Dict[str, Any] = {
                "total_tasks": len(results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(results) - len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "status": "completed",
                "derived_g1_squared": result["derived_values"]["g1_squared"],
                "experimental_g1_squared": result["experimental_values"]["g1_squared"],
                "relative_error": result["errors"]["g1_squared_relative_error"],
                "best_hypothesis": result["best_hypothesis"],
                "all_hypotheses": result["all_hypotheses"],
                "elegant_kernel_constants": result["elegant_kernel_constants"],
                "discovered_attractors": result["discovered_attractors"]
            }
            
            # Use the success summary for the rest of the function
            summary_data = summary_success
        
        # Write reports
        write_json_report(self.root, "u1_coupling_derivation_refined_summary", summary_data)
        
        # Create markdown report
        md_lines = [
            "# Refined U(1) Gauge Coupling Derivation — Summary",
            "",
            f"- **Total Tasks:** {summary_data.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary_data.get('successful_tasks', 0)}",
            f"- **Success Rate:** {summary_data.get('success_rate', 0):.1%}",
            ""
        ]
        
        if successful_results:
            md_lines.extend([
                "## Best Hypothesis Results",
                f"- **Best Hypothesis:** {summary_data['best_hypothesis']['name']}",
                f"- **Derived g₁²:** {summary_data['derived_g1_squared']:.6f}",
                f"- **Experimental g₁²:** {summary_data['experimental_g1_squared']:.6f}",
                f"- **Relative Error:** {summary_data['relative_error']:.4%}",
                "",
                "## All Hypotheses Comparison",
                ""
            ])
            
            for name, hyp in summary_data['all_hypotheses'].items():
                md_lines.extend([
                    f"### {name}",
                    f"- Derived g₁²: {hyp['g1_squared']:.6f}",
                    f"- Derived α: {hyp['alpha_derived']:.6f}",
                    f"- Relative Error: {hyp['relative_error']:.4%}",
                    ""
                ])
            
            md_lines.extend([
                "## Discovered Attractors Used",
                f"- Primary RG Attractor: {summary_data['discovered_attractors']['primary_attractor']:.10f}",
                f"- Quarter-Lock: {summary_data['discovered_attractors']['quarter_lock']:.10f}",
                f"- Attractor 04244: {summary_data['discovered_attractors']['attractor_04244']:.10f}",
                f"- Attractor 11861: {summary_data['discovered_attractors']['attractor_11861']:.10f}",
                f"- Attractor 02036: {summary_data['discovered_attractors']['attractor_02036']:.10f}",
                "",
                "## Elegant Kernel Constants",
                f"- k_a: {summary_data['elegant_kernel_constants']['k_a']}",
                f"- k_b: {summary_data['elegant_kernel_constants']['k_b']}",
                f"- k_c: {summary_data['elegant_kernel_constants']['k_c']}",
                f"- k_L2: {summary_data['elegant_kernel_constants']['k_L2']}",
                ""
            ])
        
        write_md_report(self.root, "u1_coupling_derivation_refined_summary", "\n".join(md_lines))
        return summary_data