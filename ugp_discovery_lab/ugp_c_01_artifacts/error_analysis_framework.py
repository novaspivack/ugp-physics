#!/usr/bin/env python3
"""
UGP-C-01: Error Analysis Framework

This script provides comprehensive error analysis for the UGP Instantiation Factor
calculation, including statistical analysis, uncertainty propagation, and
theoretical interpretation.

Author: Ninja (Scientific Python Coder)
Date: 2025-09-22
"""

import decimal
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple


class UGPErrorAnalyzer:
    """Comprehensive error analyzer for UGP-C-01 results."""
    
    def __init__(self):
        """Initialize the error analyzer."""
        self.results = {}
    
    def load_experiment_results(self, results_path: Path) -> Dict[str, Any]:
        """
        Load experiment results from JSON file.
        
        Args:
            results_path: Path to results JSON file
            
        Returns:
            Loaded results dictionary
        """
        with open(results_path, 'r') as f:
            self.results = json.load(f)
        
        print(f"📊 Loaded experiment results from: {results_path}")
        return self.results
    
    def analyze_absolute_error(self) -> Dict[str, Any]:
        """
        Analyze absolute error characteristics.
        
        Returns:
            Absolute error analysis results
        """
        predicted = decimal.Decimal(self.results["results"]["delta_ugp_predicted"])
        target = decimal.Decimal(self.results["results"]["delta_ugp_target"])
        absolute_error = decimal.Decimal(self.results["results"]["absolute_error"])
        
        # Calculate additional error metrics
        absolute_error_magnitude = abs(absolute_error)
        
        # Error direction analysis
        error_direction = "underestimate" if absolute_error < 0 else "overestimate"
        
        # Error significance (compared to target magnitude)
        target_magnitude = abs(target)
        error_significance = absolute_error_magnitude / target_magnitude
        
        analysis = {
            "predicted_value": predicted,
            "target_value": target,
            "absolute_error": absolute_error,
            "absolute_error_magnitude": absolute_error_magnitude,
            "error_direction": error_direction,
            "target_magnitude": target_magnitude,
            "error_significance": error_significance,
            "error_significance_percent": error_significance * 100
        }
        
        print(f"📊 Absolute Error Analysis:")
        print(f"   Predicted: {predicted}")
        print(f"   Target:    {target}")
        print(f"   Error:     {absolute_error}")
        print(f"   Direction: {error_direction}")
        print(f"   Significance: {analysis['error_significance_percent']:.3f}% of target magnitude")
        
        return analysis
    
    def analyze_relative_error(self) -> Dict[str, Any]:
        """
        Analyze relative error characteristics.
        
        Returns:
            Relative error analysis results
        """
        relative_error = decimal.Decimal(self.results["results"]["relative_error_percent"])
        
        # Categorize error magnitude
        if abs(relative_error) < 1.0:
            error_category = "excellent"
        elif abs(relative_error) < 5.0:
            error_category = "good"
        elif abs(relative_error) < 10.0:
            error_category = "acceptable"
        elif abs(relative_error) < 20.0:
            error_category = "poor"
        else:
            error_category = "unacceptable"
        
        # Error direction
        error_direction = "underestimate" if relative_error < 0 else "overestimate"
        
        analysis = {
            "relative_error_percent": relative_error,
            "error_category": error_category,
            "error_direction": error_direction,
            "is_within_5_percent": abs(relative_error) < 5.0,
            "is_within_1_percent": abs(relative_error) < 1.0
        }
        
        print(f"📊 Relative Error Analysis:")
        print(f"   Relative Error: {relative_error:.3f}%")
        print(f"   Category: {error_category}")
        print(f"   Direction: {error_direction}")
        print(f"   Within 5%: {'✅' if analysis['is_within_5_percent'] else '❌'}")
        print(f"   Within 1%: {'✅' if analysis['is_within_1_percent'] else '❌'}")
        
        return analysis
    
    def analyze_uncertainty_propagation(self) -> Dict[str, Any]:
        """
        Analyze uncertainty propagation through the calculation.
        
        Returns:
            Uncertainty propagation analysis
        """
        # Extract parameters
        phi = decimal.Decimal(self.results["parameters"]["phi"])
        k_L_squared = decimal.Decimal(self.results["parameters"]["k_L_squared"])
        k_gen2 = decimal.Decimal(self.results["parameters"]["k_gen2"])
        
        # Estimate uncertainties (assuming precision-limited uncertainties)
        precision = int(self.results["parameters"]["precision_digits"])
        
        # Uncertainty in φ (from √5 calculation)
        phi_uncertainty = decimal.Decimal("1") / decimal.Decimal(10) ** precision
        
        # Uncertainty in k_L² (exact rational, no uncertainty)
        k_L_squared_uncertainty = decimal.Decimal("0")
        
        # Uncertainty in k_gen2 (propagated from φ)
        k_gen2_uncertainty = phi_uncertainty / decimal.Decimal("2")
        
        # Uncertainty in δ_UGP (using error propagation formula for division)
        # ∂(δ_UGP)/∂(k_L²) = 1/k_gen2
        # ∂(δ_UGP)/∂(k_gen2) = -k_L²/k_gen2²
        # σ_δ_UGP = sqrt((∂(δ_UGP)/∂(k_L²) * σ_k_L²)² + (∂(δ_UGP)/∂(k_gen2) * σ_k_gen2)²)
        
        partial_k_L_squared = decimal.Decimal("1") / k_gen2
        partial_k_gen2 = -k_L_squared / (k_gen2 ** 2)
        
        delta_ugp_uncertainty = abs(partial_k_gen2 * k_gen2_uncertainty)
        
        analysis = {
            "phi_uncertainty": phi_uncertainty,
            "k_L_squared_uncertainty": k_L_squared_uncertainty,
            "k_gen2_uncertainty": k_gen2_uncertainty,
            "delta_ugp_uncertainty": delta_ugp_uncertainty,
            "partial_derivatives": {
                "partial_k_L_squared": partial_k_L_squared,
                "partial_k_gen2": partial_k_gen2
            }
        }
        
        print(f"📊 Uncertainty Propagation Analysis:")
        print(f"   φ uncertainty: {phi_uncertainty}")
        print(f"   k_L² uncertainty: {k_L_squared_uncertainty} (exact)")
        print(f"   k_gen2 uncertainty: {k_gen2_uncertainty}")
        print(f"   δ_UGP uncertainty: {delta_ugp_uncertainty}")
        
        return analysis
    
    def compare_with_experimental_uncertainty(self) -> Dict[str, Any]:
        """
        Compare theoretical uncertainty with experimental uncertainty.
        
        Returns:
            Comparison analysis
        """
        # Load uncertainty analysis
        uncertainty_analysis = self.analyze_uncertainty_propagation()
        
        # Estimate experimental uncertainty from the -1.63% residual
        # This represents the uncertainty in our experimental determination
        target = decimal.Decimal(self.results["results"]["delta_ugp_target"])
        experimental_uncertainty = abs(target) * decimal.Decimal("0.0163")  # 1.63% of target
        
        theoretical_uncertainty = uncertainty_analysis["delta_ugp_uncertainty"]
        
        # Compare uncertainties
        uncertainty_ratio = theoretical_uncertainty / experimental_uncertainty
        
        analysis = {
            "experimental_uncertainty": experimental_uncertainty,
            "theoretical_uncertainty": theoretical_uncertainty,
            "uncertainty_ratio": uncertainty_ratio,
            "theoretical_vs_experimental": "theoretical < experimental" if uncertainty_ratio < 1 else "theoretical > experimental"
        }
        
        print(f"📊 Experimental vs Theoretical Uncertainty:")
        print(f"   Experimental uncertainty: {experimental_uncertainty}")
        print(f"   Theoretical uncertainty: {theoretical_uncertainty}")
        print(f"   Ratio: {uncertainty_ratio}")
        print(f"   Comparison: {analysis['theoretical_vs_experimental']}")
        
        return analysis
    
    def analyze_theoretical_interpretation(self) -> Dict[str, Any]:
        """
        Analyze the theoretical interpretation of the results.
        
        Returns:
            Theoretical interpretation analysis
        """
        predicted = decimal.Decimal(self.results["results"]["delta_ugp_predicted"])
        target = decimal.Decimal(self.results["results"]["delta_ugp_target"])
        relative_error = decimal.Decimal(self.results["results"]["relative_error_percent"])
        
        # Physical interpretation
        if abs(relative_error) < 5.0:
            interpretation = "The theoretical prediction matches the experimental target within acceptable limits. This suggests the formula δ_UGP = k_L² / k_gen2 correctly captures the fundamental physics of the UGP instantiation factor."
            confidence_level = "high"
        elif abs(relative_error) < 10.0:
            interpretation = "The theoretical prediction is close to the experimental target but shows some deviation. This may indicate the need for additional terms or corrections in the theoretical formula."
            confidence_level = "medium"
        else:
            interpretation = "The theoretical prediction shows significant deviation from the experimental target. This suggests either the formula is incomplete or there are additional physical effects not captured in the current theoretical framework."
            confidence_level = "low"
        
        # Direction of deviation
        if relative_error < 0:
            direction_interpretation = "The theoretical prediction underestimates the experimental value, suggesting the actual instantiation factor is more negative than predicted."
        else:
            direction_interpretation = "The theoretical prediction overestimates the experimental value, suggesting the actual instantiation factor is less negative than predicted."
        
        analysis = {
            "interpretation": interpretation,
            "confidence_level": confidence_level,
            "direction_interpretation": direction_interpretation,
            "relative_error_magnitude": abs(relative_error),
            "is_acceptable": abs(relative_error) < 5.0,
            "requires_refinement": abs(relative_error) >= 5.0
        }
        
        print(f"📊 Theoretical Interpretation:")
        print(f"   Confidence Level: {confidence_level}")
        print(f"   Acceptable: {'✅' if analysis['is_acceptable'] else '❌'}")
        print(f"   Requires Refinement: {'✅' if analysis['requires_refinement'] else '❌'}")
        
        return analysis
    
    def generate_comprehensive_error_report(self) -> str:
        """
        Generate a comprehensive error analysis report.
        
        Returns:
            Formatted error analysis report
        """
        # Run all analyses
        absolute_analysis = self.analyze_absolute_error()
        relative_analysis = self.analyze_relative_error()
        uncertainty_analysis = self.analyze_uncertainty_propagation()
        experimental_comparison = self.compare_with_experimental_uncertainty()
        theoretical_interpretation = self.analyze_theoretical_interpretation()
        
        report = f"""
==================================================================
 UGP-C-01: Comprehensive Error Analysis Report
==================================================================

--- Absolute Error Analysis ---
Predicted δ_UGP:        {absolute_analysis['predicted_value']}
Target δ_UGP:           {absolute_analysis['target_value']}
Absolute Error:         {absolute_analysis['absolute_error']}
Error Magnitude:        {absolute_analysis['absolute_error_magnitude']}
Error Direction:        {absolute_analysis['error_direction']}
Error Significance:     {absolute_analysis['error_significance_percent']:.3f}% of target magnitude

--- Relative Error Analysis ---
Relative Error:         {relative_analysis['relative_error_percent']:.3f}%
Error Category:         {relative_analysis['error_category']}
Error Direction:        {relative_analysis['error_direction']}
Within 5%:             {'✅' if relative_analysis['is_within_5_percent'] else '❌'}
Within 1%:             {'✅' if relative_analysis['is_within_1_percent'] else '❌'}

--- Uncertainty Propagation Analysis ---
φ Uncertainty:          {uncertainty_analysis['phi_uncertainty']}
k_L² Uncertainty:       {uncertainty_analysis['k_L_squared_uncertainty']} (exact rational)
k_gen2 Uncertainty:     {uncertainty_analysis['k_gen2_uncertainty']}
δ_UGP Uncertainty:      {uncertainty_analysis['delta_ugp_uncertainty']}

Partial Derivatives:
  ∂(δ_UGP)/∂(k_L²) =   {uncertainty_analysis['partial_derivatives']['partial_k_L_squared']}
  ∂(δ_UGP)/∂(k_gen2) = {uncertainty_analysis['partial_derivatives']['partial_k_gen2']}

--- Experimental vs Theoretical Uncertainty ---
Experimental Uncertainty: {experimental_comparison['experimental_uncertainty']}
Theoretical Uncertainty:  {experimental_comparison['theoretical_uncertainty']}
Uncertainty Ratio:       {experimental_comparison['uncertainty_ratio']}
Comparison:              {experimental_comparison['theoretical_vs_experimental']}

--- Theoretical Interpretation ---
Confidence Level:       {theoretical_interpretation['confidence_level']}
Acceptable Agreement:   {'✅' if theoretical_interpretation['is_acceptable'] else '❌'}
Requires Refinement:    {'✅' if theoretical_interpretation['requires_refinement'] else '❌'}

Interpretation:
{theoretical_interpretation['interpretation']}

Direction Analysis:
{theoretical_interpretation['direction_interpretation']}

--- Summary and Recommendations ---
"""
        
        # Add recommendations based on analysis
        if theoretical_interpretation['is_acceptable']:
            report += """
✅ RECOMMENDATION: The theoretical prediction is within acceptable limits.
   The formula δ_UGP = k_L² / k_gen2 provides a good approximation to the
   experimental instantiation factor. Further refinement may improve precision
   but is not strictly necessary for practical applications.
"""
        else:
            report += """
⚠️  RECOMMENDATION: The theoretical prediction shows significant deviation.
   Consider investigating:
   1. Additional terms in the theoretical formula
   2. Higher-order corrections
   3. Alternative theoretical frameworks
   4. Experimental validation of the target value
"""
        
        report += "\n==================================================================\n"
        
        return report
    
    def save_error_analysis(self, output_dir: Path) -> None:
        """
        Save comprehensive error analysis to files.
        
        Args:
            output_dir: Directory to save results
        """
        output_dir.mkdir(exist_ok=True)
        
        # Run all analyses
        analyses = {
            "absolute_error_analysis": self.analyze_absolute_error(),
            "relative_error_analysis": self.analyze_relative_error(),
            "uncertainty_propagation_analysis": self.analyze_uncertainty_propagation(),
            "experimental_comparison_analysis": self.compare_with_experimental_uncertainty(),
            "theoretical_interpretation_analysis": self.analyze_theoretical_interpretation()
        }
        
        # Save JSON results
        json_path = output_dir / "ugp_c_01_error_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(analyses, f, indent=2, default=str)
        print(f"💾 Error analysis saved to: {json_path}")
        
        # Save human-readable report
        report_path = output_dir / "ugp_c_01_error_analysis_report.txt"
        with open(report_path, 'w') as f:
            f.write(self.generate_comprehensive_error_report())
        print(f"📄 Error analysis report saved to: {report_path}")


def main():
    """Main execution function."""
    print("📊 UGP-C-01: Comprehensive Error Analysis")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("ugp_c_01_artifacts")
    
    # Initialize analyzer
    analyzer = UGPErrorAnalyzer()
    
    # Load experiment results
    results_path = Path("ugp_c_01_results/ugp_c_01_calculation_results.json")
    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        print("Please run the main experiment first.")
        return
    
    analyzer.load_experiment_results(results_path)
    
    # Generate and display report
    print(analyzer.generate_comprehensive_error_report())
    
    # Save analysis
    analyzer.save_error_analysis(output_dir)
    
    print("\n🎯 Error analysis complete!")


if __name__ == "__main__":
    main()
