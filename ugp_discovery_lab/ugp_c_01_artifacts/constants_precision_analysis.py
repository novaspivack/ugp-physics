#!/usr/bin/env python3
"""
UGP-C-01: Constants Precision Analysis

This script performs detailed precision analysis of the constants used in
the UGP Instantiation Factor calculation to validate the accuracy of our results.

Author: Ninja (Scientific Python Coder)
Date: 2025-09-22
"""

import decimal
import json
from pathlib import Path
from typing import Dict, Any, List


class ConstantsPrecisionAnalyzer:
    """Analyzer for precision validation of UGP constants."""
    
    def __init__(self, max_precision: int = 100):
        """
        Initialize the precision analyzer.
        
        Args:
            max_precision: Maximum precision to test
        """
        self.max_precision = max_precision
        self.precision_results = []
    
    def analyze_precision_effects(self) -> List[Dict[str, Any]]:
        """
        Analyze the effects of different precision settings on results.
        
        Returns:
            List of results for different precision settings
        """
        print("🔍 Analyzing precision effects on UGP constants...")
        
        precisions = [20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        for precision in precisions:
            if precision > self.max_precision:
                continue
                
            result = self._calculate_at_precision(precision)
            self.precision_results.append(result)
            
            print(f"   {precision:3d} digits: φ={result['phi']:.20f}..., "
                  f"δ_UGP={result['delta_ugp']:.20f}...")
        
        return self.precision_results
    
    def _calculate_at_precision(self, precision: int) -> Dict[str, Any]:
        """
        Calculate constants at specified precision.
        
        Args:
            precision: Number of decimal digits
            
        Returns:
            Dictionary containing calculated values
        """
        # Set precision
        decimal.getcontext().prec = precision
        
        # Calculate constants
        sqrt_5 = decimal.Decimal(5).sqrt()
        phi = (decimal.Decimal(1) + sqrt_5) / decimal.Decimal(2)
        k_L_squared = decimal.Decimal(7) / decimal.Decimal(512)
        k_gen2 = -phi / decimal.Decimal(2)
        delta_ugp = k_L_squared / k_gen2
        
        return {
            "precision": precision,
            "phi": phi,
            "k_L_squared": k_L_squared,
            "k_gen2": k_gen2,
            "delta_ugp": delta_ugp
        }
    
    def analyze_convergence(self) -> Dict[str, Any]:
        """
        Analyze convergence of results with increasing precision.
        
        Returns:
            Convergence analysis results
        """
        if not self.precision_results:
            self.analyze_precision_effects()
        
        print("\n📊 Analyzing convergence...")
        
        # Use highest precision result as reference
        reference = self.precision_results[-1]
        reference_delta_ugp = reference["delta_ugp"]
        
        convergence_data = []
        
        for result in self.precision_results:
            delta_ugp = result["delta_ugp"]
            diff = abs(delta_ugp - reference_delta_ugp)
            
            convergence_data.append({
                "precision": result["precision"],
                "delta_ugp": delta_ugp,
                "difference_from_reference": diff,
                "significant_digits": self._count_significant_digits(diff)
            })
        
        return {
            "reference_precision": reference["precision"],
            "reference_delta_ugp": reference_delta_ugp,
            "convergence_data": convergence_data
        }
    
    def _count_significant_digits(self, diff: decimal.Decimal) -> int:
        """
        Count significant digits in the difference.
        
        Args:
            diff: Decimal difference
            
        Returns:
            Number of significant digits
        """
        if diff == 0:
            return float('inf')
        
        # Convert to string and count leading zeros after decimal point
        diff_str = str(abs(diff))
        if '.' in diff_str:
            decimal_part = diff_str.split('.')[1]
            # Count leading zeros
            leading_zeros = 0
            for char in decimal_part:
                if char == '0':
                    leading_zeros += 1
                else:
                    break
            return leading_zeros
        return 0
    
    def validate_constants(self) -> Dict[str, Any]:
        """
        Validate the accuracy of our constants against known values.
        
        Returns:
            Validation results
        """
        print("\n✅ Validating constants against known values...")
        
        # Use 100-digit precision for validation
        decimal.getcontext().prec = 100
        
        # Calculate our values
        sqrt_5 = decimal.Decimal(5).sqrt()
        phi_calculated = (decimal.Decimal(1) + sqrt_5) / decimal.Decimal(2)
        k_L_squared_calculated = decimal.Decimal(7) / decimal.Decimal(512)
        
        # Known high-precision values for validation
        phi_known = decimal.Decimal("1.618033988749894848204586834365638117720309179805762862135448622705260462818902449707207204189391137")
        k_L_squared_known = decimal.Decimal("0.013671875")  # Exact rational
        
        # Calculate differences
        phi_diff = abs(phi_calculated - phi_known)
        k_L_squared_diff = abs(k_L_squared_calculated - k_L_squared_known)
        
        print(f"   φ difference: {phi_diff}")
        print(f"   k_L² difference: {k_L_squared_diff}")
        
        return {
            "phi_calculated": phi_calculated,
            "phi_known": phi_known,
            "phi_difference": phi_diff,
            "k_L_squared_calculated": k_L_squared_calculated,
            "k_L_squared_known": k_L_squared_known,
            "k_L_squared_difference": k_L_squared_diff,
            "phi_valid": phi_diff < decimal.Decimal("1e-50"),
            "k_L_squared_valid": k_L_squared_diff == 0  # Should be exact
        }
    
    def generate_precision_report(self) -> str:
        """
        Generate a comprehensive precision analysis report.
        
        Returns:
            Formatted report string
        """
        if not self.precision_results:
            self.analyze_precision_effects()
        
        convergence = self.analyze_convergence()
        validation = self.validate_constants()
        
        report = f"""
==================================================================
 UGP-C-01: Constants Precision Analysis Report
==================================================================

--- Precision Effects Analysis ---
"""
        
        for result in self.precision_results:
            report += f"Precision {result['precision']:3d}: δ_UGP = {result['delta_ugp']}\n"
        
        report += f"""
--- Convergence Analysis ---
Reference Precision: {convergence['reference_precision']} digits
Reference δ_UGP: {convergence['reference_delta_ugp']}

Precision Convergence:
"""
        
        for data in convergence['convergence_data']:
            sig_digits = data['significant_digits']
            sig_digits_str = "∞" if sig_digits == float('inf') else str(sig_digits)
            report += f"  {data['precision']:3d} digits: {sig_digits_str} significant digits\n"
        
        report += f"""
--- Constants Validation ---
φ Validation:
  Calculated: {validation['phi_calculated']}
  Known:      {validation['phi_known']}
  Difference: {validation['phi_difference']}
  Valid:      {'✅' if validation['phi_valid'] else '❌'}

k_L² Validation:
  Calculated: {validation['k_L_squared_calculated']}
  Known:      {validation['k_L_squared_known']}
  Difference: {validation['k_L_squared_difference']}
  Valid:      {'✅' if validation['k_L_squared_valid'] else '❌'}

--- Precision Recommendations ---
"""
        
        # Find precision where results converge
        convergence_data = convergence['convergence_data']
        stable_precision = None
        for data in convergence_data:
            if data['significant_digits'] >= 30:  # 30+ significant digits
                stable_precision = data['precision']
                break
        
        if stable_precision:
            report += f"Recommended precision: {stable_precision} digits (30+ significant digits stable)\n"
        else:
            report += f"Recommended precision: {self.max_precision} digits (maximum tested)\n"
        
        report += "\n==================================================================\n"
        
        return report
    
    def save_analysis_results(self, output_dir: Path) -> None:
        """
        Save precision analysis results to files.
        
        Args:
            output_dir: Directory to save results
        """
        output_dir.mkdir(exist_ok=True)
        
        # Save detailed results
        results = {
            "precision_analysis": self.precision_results,
            "convergence_analysis": self.analyze_convergence(),
            "validation_results": self.validate_constants()
        }
        
        json_path = output_dir / "ugp_c_01_precision_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"💾 Precision analysis saved to: {json_path}")
        
        # Save human-readable report
        report_path = output_dir / "ugp_c_01_precision_analysis_report.txt"
        with open(report_path, 'w') as f:
            f.write(self.generate_precision_report())
        print(f"📄 Precision report saved to: {report_path}")


def main():
    """Main execution function."""
    print("🔍 UGP-C-01: Constants Precision Analysis")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("ugp_c_01_artifacts")
    
    # Initialize analyzer
    analyzer = ConstantsPrecisionAnalyzer(max_precision=100)
    
    # Run analysis
    print(analyzer.generate_precision_report())
    
    # Save results
    analyzer.save_analysis_results(output_dir)
    
    print("\n🎯 Precision analysis complete!")


if __name__ == "__main__":
    main()
