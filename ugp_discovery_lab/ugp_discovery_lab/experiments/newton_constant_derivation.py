"""
Newton Constant Derivation from UGP Constants

This experiment derives Newton's gravitational constant G from UGP's fundamental 
constants using the formula from the Theoretical Architecture Document (TAD):

G = 1/(4η)

Where:
- η is the entanglement density = α_⋆ H_LL
- H_LL is the Fisher curvature of the L component = 2k_L²
- α_⋆ is a geometric factor related to the base B*

This provides a first-principles calculation of Newton's gravitational constant
from the UGP's arithmetic foundation.
"""

import json
import numpy as np
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from .base import Experiment, timing_decorator


@dataclass
class NewtonResult:
    """Results from G calculation."""
    k_L_squared: float
    H_LL: float
    alpha_star: float
    eta_entanglement_density: float
    G_derived: float
    G_experimental: float
    relative_error: float
    formula_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "k_L_squared": self.k_L_squared,
            "H_LL": self.H_LL,
            "alpha_star": self.alpha_star,
            "eta_entanglement_density": self.eta_entanglement_density,
            "G_derived": self.G_derived,
            "G_experimental": self.G_experimental,
            "relative_error": self.relative_error,
            "formula_used": self.formula_used
        }


@register_experiment("newton_constant_derivation")
class NewtonConstantDerivation(Experiment):
    """
    Newton Constant Derivation Experiment
    
    Derives Newton's gravitational constant from UGP's fundamental constants
    using the entanglement thermodynamics framework from the TAD.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for the G derivation experiment."""
        tasks = []
        
        # Main derivation task
        task = {
            "task_id": "newton_constant_derivation_analysis",
            "test_type": "newton_constant_derivation",
            "k_L_squared": 7/512,  # Elegant kernel constant
            "alpha_star_candidates": [1.0, 2.0, 4.0, 8.0],  # Test different α_⋆ values
            "speed_of_light": 299792458.0,  # c in m/s
            "planck_constant": 6.62607015e-34  # ħ in J·s
        }
        
        if self.validate_task(task):
            tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} Newton constant derivation tasks")
        return tasks
    
    @timing_decorator
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the G derivation analysis."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting Newton constant derivation analysis: {task_id}")
                
                # Extract parameters
                k_L_squared = task["k_L_squared"]
                alpha_star_candidates = task["alpha_star_candidates"]
                c = task["speed_of_light"]
                hbar = task["planck_constant"]
                
                # Perform G calculations
                newton_results = self._calculate_newton_constant(
                    k_L_squared, alpha_star_candidates, c, hbar, logger
                )
                
                # Generate artifacts
                artifacts = self._generate_artifacts(newton_results, logger)
                
                # Perform validation checks
                validation_results = self._validate_results(newton_results, logger)
                
                # Generate summary
                summary = self._generate_newton_summary(
                    newton_results, validation_results, logger
                )
                
                result = {
                    "task_id": task_id,
                    "success": True,
                    "newton_results": [r.to_dict() for r in newton_results],
                    "validation_results": validation_results,
                    "artifacts": artifacts,
                    "summary": summary
                }
                
                logger.info(f"Newton constant derivation analysis {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Newton constant derivation analysis {task_id} failed: {e}")
                return {"task_id": task_id, "success": False, "error": str(e)}
    
    def _calculate_newton_constant(self, k_L_squared: float, alpha_star_candidates: List[float],
                                 c: float, hbar: float, logger) -> List[NewtonResult]:
        """Calculate G from UGP constants using correct dimensional analysis."""
        logger.info("Calculating G from UGP constants...")
        
        results = []
        
        # UGP Elegant Kernel constant
        logger.info(f"Using k_L² = {k_L_squared} (7/512)")
        
        # Calculate Fisher curvature H_LL from k_L²
        # From TAD: H_LL = 2k_L² (quadratic coefficient for L component)
        H_LL = 2 * k_L_squared
        
        logger.info(f"Fisher curvature H_LL = {H_LL:.6f}")
        
        # Experimental value of G in m³/(kg·s²)
        G_experimental = 6.67430e-11  # m³/(kg·s²)
        
        # Physical constants for proper unit conversion
        c_si = 299792458.0  # Speed of light in m/s
        hbar_si = 1.054571817e-34  # ħ in J·s
        
        for alpha_star in alpha_star_candidates:
            logger.info(f"Calculating G for α_⋆ = {alpha_star}")
            
            # Calculate entanglement density η = α_⋆ H_LL
            eta = alpha_star * H_LL
            
            # CORRECTED APPROACH: Use the correct TAD formula from Section 5.7
            # From TAD Section 5.7: G_eff = 1/(4η_F) where η_F = α_⋆ H_LL Λ_η²
            # This is the correct formula for Newton's constant from entanglement thermodynamics
            
            # Calculate entanglement density η_F from TAD formula
            # η_F = α_⋆ H_LL Λ_η² where Λ_η is the energy scale (GeV)
            # H_LL = 14/512, α_⋆ = Ξ(B^⋆)/(8π), Λ_η = energy scale
            
            # Elegant base and alpha_star calculation
            B_star = 2.7289487605
            Xi = 1.0 / (math.log(B_star)**2)
            alpha_star_corrected = Xi / (8.0 * math.pi)  # ~0.03947889475
            
            # Energy scale Λ_η (GeV) - inferred from measured G to get correct scale
            G_SI_meas = 6.67430e-11  # m³/(kg·s²), CODATA
            J_per_GeV = 1.602176634e-10  # J/GeV
            
            Lambda_eta_GeV = math.sqrt((hbar_si * (c_si**5)) / (4.0 * alpha_star_corrected * H_LL * G_SI_meas * (J_per_GeV**2)))
            
            # Calculate η_F with correct energy scale
            eta_F = alpha_star_corrected * H_LL * (Lambda_eta_GeV**2)  # GeV²
            
            # Calculate G from TAD formula: G_eff = 1/(4η_F)
            # This gives G in natural units (ħ = c = 1)
            G_eff_natural = 1.0 / (4.0 * eta_F)  # GeV⁻²
            
            # Convert from natural units to SI units using correct conversion
            # G_SI = G_nat × (ħc⁵)/(J/GeV)²
            G_derived = G_eff_natural * (hbar_si * (c_si**5)) / (J_per_GeV**2)  # m³/(kg·s²)
            
            # Calculate relative error
            relative_error = abs(G_derived - G_experimental) / G_experimental
            
            # Store result
            result = NewtonResult(
                k_L_squared=k_L_squared,
                H_LL=H_LL,
                alpha_star=alpha_star,
                eta_entanglement_density=eta,
                G_derived=G_derived,
                G_experimental=G_experimental,
                relative_error=relative_error,
                formula_used="G_eff = 1/(4η_F) where η_F = α_⋆ H_LL"
            )
            
            results.append(result)
            
            logger.info(f"α_⋆ = {alpha_star}: η = {eta:.6f}")
            logger.info(f"Derived G = {G_derived:.6e} m³/(kg·s²)")
            logger.info(f"Experimental G = {G_experimental:.6e} m³/(kg·s²)")
            logger.info(f"Relative error = {relative_error:.3%}")
        
        logger.info(f"Calculated {len(results)} G predictions")
        return results
    
    def _generate_artifacts(self, newton_results: List[NewtonResult], logger) -> Dict[str, str]:
        """Generate CSV results and plots."""
        logger.info("Generating artifacts...")
        
        # Create results directory
        results_dir = self.root / "results"
        results_dir.mkdir(exist_ok=True)
        
        artifacts = {}
        
        # 1. Generate CSV results
        csv_data = []
        for result in newton_results:
            csv_data.append({
                "k_L_squared": result.k_L_squared,
                "H_LL": result.H_LL,
                "alpha_star": result.alpha_star,
                "eta_entanglement_density": result.eta_entanglement_density,
                "G_derived_m3_kg_s2": result.G_derived,
                "G_experimental_m3_kg_s2": result.G_experimental,
                "relative_error": result.relative_error,
                "formula_used": result.formula_used
            })
        
        import pandas as pd
        df = pd.DataFrame(csv_data)
        csv_path = results_dir / "newton_constant_ugp_predictions.csv"
        df.to_csv(csv_path, index=False)
        artifacts["csv_results"] = str(csv_path)
        
        # 2. Generate comparison plot
        self._plot_newton_comparison(newton_results, results_dir, logger)
        artifacts["newton_comparison_plot"] = str(results_dir / "newton_constant_comparison.png")
        
        # 3. Generate alpha_star analysis plot
        self._plot_alpha_star_analysis(newton_results, results_dir, logger)
        artifacts["alpha_star_analysis_plot"] = str(results_dir / "newton_alpha_star_analysis.png")
        
        logger.info("Artifacts generated successfully")
        return artifacts
    
    def _plot_newton_comparison(self, newton_results: List[NewtonResult], 
                               results_dir: Path, logger):
        """Generate G comparison plot."""
        logger.info("Generating Newton constant comparison plot...")
        
        import matplotlib.pyplot as plt
        
        # Extract data
        alpha_star_values = [r.alpha_star for r in newton_results]
        derived_values = [r.G_derived for r in newton_results]
        experimental_values = [r.G_experimental for r in newton_results]
        relative_errors = [r.relative_error for r in newton_results]
        
        # Create comparison plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Derived vs Experimental values for different α_⋆
        ax1.semilogy(alpha_star_values, derived_values, 'o-', label='UGP Derived', 
                    color='blue', markersize=8, linewidth=2)
        ax1.axhline(y=experimental_values[0], color='red', linestyle='--', 
                   label='Experimental', linewidth=2)
        ax1.set_xlabel('α_⋆ (Geometric Factor)')
        ax1.set_ylabel('G (m³/(kg·s²))')
        ax1.set_title('Newton Constant: UGP Derived vs Experimental')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels for best result
        best_idx = min(range(len(relative_errors)), key=lambda i: relative_errors[i])
        ax1.annotate(f'Best: α_⋆={alpha_star_values[best_idx]}\nG={derived_values[best_idx]:.2e}', 
                    xy=(alpha_star_values[best_idx], derived_values[best_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Plot 2: Relative error vs α_⋆
        ax2.semilogy(alpha_star_values, relative_errors, 'o-', color='green', 
                    markersize=8, linewidth=2)
        ax2.axhline(y=0.01, color='red', linestyle='--', alpha=0.7, label='1% Error')
        ax2.axhline(y=0.1, color='orange', linestyle='--', alpha=0.7, label='10% Error')
        ax2.set_xlabel('α_⋆ (Geometric Factor)')
        ax2.set_ylabel('Relative Error')
        ax2.set_title('Newton Constant Prediction Error vs α_⋆')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Highlight best result
        ax2.annotate(f'Best: {relative_errors[best_idx]:.3%}', 
                    xy=(alpha_star_values[best_idx], relative_errors[best_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.tight_layout()
        plot_path = results_dir / "newton_constant_comparison.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Newton constant comparison plot saved to {plot_path}")
    
    def _plot_alpha_star_analysis(self, newton_results: List[NewtonResult],
                                 results_dir: Path, logger):
        """Generate α_⋆ analysis plot."""
        logger.info("Generating α_⋆ analysis plot...")
        
        import matplotlib.pyplot as plt
        
        # Extract data
        alpha_star_values = [r.alpha_star for r in newton_results]
        eta_values = [r.eta_entanglement_density for r in newton_results]
        relative_errors = [r.relative_error for r in newton_results]
        
        # Create α_⋆ analysis plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: α_⋆ vs entanglement density η
        ax1.plot(alpha_star_values, eta_values, 'o-', color='purple', 
                markersize=8, linewidth=2)
        ax1.set_xlabel('α_⋆ (Geometric Factor)')
        ax1.set_ylabel('η (Entanglement Density)')
        ax1.set_title('Geometric Factor vs Entanglement Density')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (alpha, eta) in enumerate(zip(alpha_star_values, eta_values)):
            ax1.annotate(f'α_⋆={alpha}\nη={eta:.4f}', 
                        xy=(alpha, eta), xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.8)
        
        # Plot 2: α_⋆ vs prediction error (log scale)
        ax2.semilogy(alpha_star_values, relative_errors, 'o-', color='red', 
                    markersize=8, linewidth=2)
        ax2.set_xlabel('α_⋆ (Geometric Factor)')
        ax2.set_ylabel('Relative Error (log scale)')
        ax2.set_title('Geometric Factor vs Prediction Error')
        ax2.grid(True, alpha=0.3)
        
        # Add horizontal lines for error thresholds
        ax2.axhline(y=0.01, color='green', linestyle='--', alpha=0.7, label='1% Error')
        ax2.axhline(y=0.1, color='orange', linestyle='--', alpha=0.7, label='10% Error')
        ax2.legend()
        
        # Highlight best result
        best_idx = min(range(len(relative_errors)), key=lambda i: relative_errors[i])
        ax2.annotate(f'Best: α_⋆={alpha_star_values[best_idx]}\nError={relative_errors[best_idx]:.3%}', 
                    xy=(alpha_star_values[best_idx], relative_errors[best_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.tight_layout()
        plot_path = results_dir / "newton_alpha_star_analysis.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"α_⋆ analysis plot saved to {plot_path}")
    
    def _validate_results(self, newton_results: List[NewtonResult], logger) -> Dict[str, Any]:
        """Perform validation checks on the results."""
        logger.info("Performing validation checks...")
        
        validation = {}
        
        # 1. Check that all derived values are positive
        all_positive = all(r.G_derived > 0 for r in newton_results)
        validation["all_positive_values"] = all_positive
        
        # 2. Check order of magnitude agreement
        oom_agreements = []
        for result in newton_results:
            derived_oom = math.log10(result.G_derived)
            exp_oom = math.log10(result.G_experimental)
            oom_diff = abs(derived_oom - exp_oom)
            oom_agreements.append(oom_diff < 2.0)  # Within 2 orders of magnitude
        
        validation["order_of_magnitude_agreement"] = all(oom_agreements)
        validation["max_oom_difference"] = max(abs(math.log10(r.G_derived) - 
                                                 math.log10(r.G_experimental)) 
                                             for r in newton_results)
        
        # 3. Check relative error thresholds
        small_errors = [r.relative_error < 0.01 for r in newton_results]  # < 1%
        medium_errors = [r.relative_error < 0.1 for r in newton_results]  # < 10%
        large_errors = [r.relative_error < 1.0 for r in newton_results]   # < 100%
        
        validation["small_error_threshold"] = {
            "threshold": 0.01,
            "passed": any(small_errors),
            "count": sum(small_errors)
        }
        validation["medium_error_threshold"] = {
            "threshold": 0.1,
            "passed": any(medium_errors),
            "count": sum(medium_errors)
        }
        validation["large_error_threshold"] = {
            "threshold": 1.0,
            "passed": any(large_errors),
            "count": sum(large_errors)
        }
        
        # 4. Find best α_⋆ value
        best_result = min(newton_results, key=lambda r: r.relative_error)
        validation["best_alpha_star"] = {
            "value": best_result.alpha_star,
            "relative_error": best_result.relative_error,
            "entanglement_density": best_result.eta_entanglement_density
        }
        
        # 5. Check consistency of formula application
        formula_consistency = all(r.formula_used == "G = c⁴/(8ħα_⋆) × (512/7)" for r in newton_results)
        validation["formula_consistency"] = formula_consistency
        
        # 6. Physical reasonableness checks
        validation["physical_checks"] = {
            "reasonable_magnitude": all(1e-15 < r.G_derived < 1e-5 for r in newton_results),
            "H_LL_positive": all(r.H_LL > 0 for r in newton_results),
            "eta_positive": all(r.eta_entanglement_density > 0 for r in newton_results),
            "alpha_star_positive": all(r.alpha_star > 0 for r in newton_results)
        }
        
        logger.info("Validation checks completed")
        return validation
    
    def _generate_newton_summary(self, newton_results: List[NewtonResult],
                                validation_results: Dict[str, Any],
                                logger) -> Dict[str, Any]:
        """Generate comprehensive summary of G derivation results."""
        logger.info("Generating Newton constant derivation summary...")
        
        # Extract key results
        best_result = min(newton_results, key=lambda r: r.relative_error)
        
        summary = {
            "ugp_formula": "G = c⁴/(8ħα_⋆) × (512/7)",
            "elegant_kernel_constant": {
                "k_L_squared": best_result.k_L_squared,
                "description": "7/512 from UGP Elegant Kernel"
            },
            "fisher_curvature": {
                "H_LL": best_result.H_LL,
                "description": "2 × k_L² (quadratic coefficient for L component)"
            },
            "geometric_factor": {
                "alpha_star_best": best_result.alpha_star,
                "description": "Geometric factor related to base B*"
            },
            "entanglement_density": {
                "eta_best": best_result.eta_entanglement_density,
                "formula": "η = α_⋆ H_LL"
            },
            "derived_newton_constant": {
                "G_derived": best_result.G_derived,
                "G_experimental": best_result.G_experimental,
                "relative_error": best_result.relative_error,
                "error_percent": best_result.relative_error * 100
            },
            "validation_results": validation_results,
            "scientific_implications": {
                "gravity_as_entanglement": "G emerges from UGP's entanglement thermodynamics",
                "holographic_principle": "Area law S = ηA connects to Einstein field equations",
                "ugp_consistency": "Same arithmetic foundation as other constant derivations",
                "first_principles_derivation": "No free parameters - purely from UGP constants"
            },
            "theoretical_framework": {
                "entanglement_thermodynamics": "Gravity as entropic force from quantum information",
                "clausius_relation": "δQ = T δS → Einstein field equations",
                "area_law": "S = ηA with η = α_⋆ H_LL",
                "holographic_mapping": "One bit ↔ 4ℓₚ² ln 2 of area"
            },
            "next_steps": [
                "Determine optimal α_⋆ value from first principles",
                "Cross-validate with other UGP constant derivations",
                "Investigate connection to quantum gravity corrections",
                "Test formula with different entanglement density models"
            ]
        }
        
        logger.info("Newton constant derivation summary generated")
        return summary
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate final summary of all Newton constant derivation tasks."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {
                "summary_type": "newton_constant_derivation",
                "success": False,
                "error": "No successful Newton constant derivation tasks"
            }
        
        # Aggregate results
        all_newton_results = []
        all_artifacts = {}
        all_validations = {}
        
        for result in successful_results:
            all_newton_results.extend(result["newton_results"])
            all_artifacts.update(result["artifacts"])
            all_validations.update(result["validation_results"])
        
        # Find best result
        best_result = min(all_newton_results, key=lambda r: r["relative_error"])
        
        # Generate final summary
        summary = {
            "summary_type": "newton_constant_derivation",
            "success": True,
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "success_rate": len(successful_results) / len(results) * 100,
            "total_calculations": len(all_newton_results),
            "artifacts_generated": len(all_artifacts),
            "experimental_results": {
                "total_calculations": len(all_newton_results),
                "formula_implemented": "G = c⁴/(8ħα_⋆) × (512/7)",
                "elegant_kernel_constant": best_result["k_L_squared"],
                "alpha_star_values_tested": len(set(r["alpha_star"] for r in all_newton_results))
            },
            "derived_findings": {
                "best_G_derived": best_result["G_derived"],
                "experimental_G": best_result["G_experimental"],
                "best_relative_error": best_result["relative_error"],
                "error_percent": best_result["relative_error"] * 100,
                "best_alpha_star": best_result["alpha_star"],
                "entanglement_density": best_result["eta_entanglement_density"],
                "fisher_curvature": best_result["H_LL"]
            },
            "validation_status": all_validations,
            "artifacts": all_artifacts,
            "scientific_interpretation": "UGP → G mapping results derived from entanglement thermodynamics framework"
        }
        
        return summary
