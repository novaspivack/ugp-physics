#!/usr/bin/env python3
"""
UGP-C-01: Test Suite for UGP Instantiation Factor (δ_UGP) Verification

This test suite validates the precision, accuracy, and correctness of the
UGP-C-01 calculator implementation.

Author: Ninja (Scientific Python Coder)
Date: 2025-09-22
"""

import decimal
import json
import unittest
import sys
from pathlib import Path
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ugp_c_01_delta_ugp_calculator import UGPDeltaCalculator


class TestUGPDeltaCalculator(unittest.TestCase):
    """Test suite for UGPDeltaCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = UGPDeltaCalculator(precision_digits=50)
    
    def test_precision_setup(self):
        """Test that precision is set correctly."""
        self.assertEqual(decimal.getcontext().prec, 50)
    
    def test_phi_calculation(self):
        """Test golden ratio calculation accuracy."""
        # Expected golden ratio to high precision
        expected_phi = decimal.Decimal("1.6180339887498948482045868343656381177203091798058")
        
        # Calculate difference
        diff = abs(self.calculator.phi - expected_phi)
        
        # Should be within precision tolerance
        self.assertLess(diff, decimal.Decimal("1e-40"))
        
        print(f"✅ φ calculation test passed")
        print(f"   Calculated φ: {self.calculator.phi}")
        print(f"   Expected φ:   {expected_phi}")
        print(f"   Difference:   {diff}")
    
    def test_k_L_squared_calculation(self):
        """Test geometric curvature constant calculation."""
        # Expected value: 7/512 = 0.013671875 (exact)
        expected_k_L_squared = decimal.Decimal("0.013671875")
        
        self.assertEqual(self.calculator.k_L_squared, expected_k_L_squared)
        
        print(f"✅ k_L² calculation test passed")
        print(f"   k_L² = {self.calculator.k_L_squared}")
    
    def test_k_gen2_calculation(self):
        """Test generational curvature constant calculation."""
        # k_gen2 = -φ/2
        expected_k_gen2 = -self.calculator.phi / decimal.Decimal(2)
        
        self.assertEqual(self.calculator.k_gen2, expected_k_gen2)
        
        print(f"✅ k_gen2 calculation test passed")
        print(f"   k_gen2 = {self.calculator.k_gen2}")
    
    def test_delta_ugp_calculation(self):
        """Test the core δ_UGP calculation."""
        delta_ugp_predicted = self.calculator.calculate_delta_ugp()
        
        # Verify calculation: δ_UGP = k_L² / k_gen2
        expected_delta_ugp = self.calculator.k_L_squared / self.calculator.k_gen2
        
        self.assertEqual(delta_ugp_predicted, expected_delta_ugp)
        
        print(f"✅ δ_UGP calculation test passed")
        print(f"   δ_UGP = {delta_ugp_predicted}")
    
    def test_error_analysis(self):
        """Test error analysis calculations."""
        delta_ugp_predicted = self.calculator.calculate_delta_ugp()
        error_analysis = self.calculator.analyze_errors(delta_ugp_predicted)
        
        # Test absolute error calculation
        expected_absolute_error = delta_ugp_predicted - self.calculator.delta_ugp_target
        self.assertEqual(error_analysis["absolute_error"], expected_absolute_error)
        
        # Test relative error calculation
        expected_relative_error = (expected_absolute_error / self.calculator.delta_ugp_target) * decimal.Decimal(100)
        self.assertEqual(error_analysis["relative_error_percent"], expected_relative_error)
        
        print(f"✅ Error analysis test passed")
        print(f"   Absolute Error:  {error_analysis['absolute_error']}")
        print(f"   Relative Error:  {error_analysis['relative_error_percent']:.3f}%")
    
    def test_json_output_format(self):
        """Test JSON output format and content."""
        delta_ugp_predicted = self.calculator.calculate_delta_ugp()
        error_analysis = self.calculator.analyze_errors(delta_ugp_predicted)
        json_output = self.calculator.generate_json_output(delta_ugp_predicted, error_analysis)
        
        # Test required fields exist
        self.assertIn("experiment_id", json_output)
        self.assertIn("parameters", json_output)
        self.assertIn("results", json_output)
        
        # Test experiment ID
        self.assertEqual(json_output["experiment_id"], "UGP-C-01_Delta_UGP_Verification")
        
        # Test parameters section
        params = json_output["parameters"]
        self.assertIn("precision_digits", params)
        self.assertIn("phi", params)
        self.assertIn("k_L_squared", params)
        self.assertIn("k_gen2", params)
        
        # Test results section
        results = json_output["results"]
        self.assertIn("delta_ugp_predicted", results)
        self.assertIn("delta_ugp_target", results)
        self.assertIn("absolute_error", results)
        self.assertIn("relative_error_percent", results)
        
        # Test that all values are strings (for precision preservation)
        for key, value in params.items():
            self.assertIsInstance(value, str)
        for key, value in results.items():
            self.assertIsInstance(value, str)
        
        print(f"✅ JSON output format test passed")
    
    def test_human_readable_report(self):
        """Test human-readable report generation."""
        delta_ugp_predicted = self.calculator.calculate_delta_ugp()
        error_analysis = self.calculator.analyze_errors(delta_ugp_predicted)
        report = self.calculator.generate_human_readable_report(delta_ugp_predicted, error_analysis)
        
        # Test that report contains required sections
        self.assertIn("UGP Instantiation Factor (δ_UGP) Verification Report", report)
        self.assertIn("High-Precision Inputs", report)
        self.assertIn("Calculation Results", report)
        self.assertIn("Error Analysis", report)
        
        # Test that all values are included
        self.assertIn(str(self.calculator.phi), report)
        self.assertIn(str(self.calculator.k_L_squared), report)
        self.assertIn(str(self.calculator.k_gen2), report)
        self.assertIn(str(delta_ugp_predicted), report)
        self.assertIn(str(self.calculator.delta_ugp_target), report)
        
        print(f"✅ Human-readable report test passed")


class TestPrecisionValidation(unittest.TestCase):
    """Test precision requirements and edge cases."""
    
    def test_different_precisions(self):
        """Test calculator with different precision settings."""
        precisions = [20, 50, 100]
        results = []
        
        for precision in precisions:
            calculator = UGPDeltaCalculator(precision_digits=precision)
            delta_ugp = calculator.calculate_delta_ugp()
            results.append((precision, delta_ugp))
        
        # Results should be consistent across precisions (within rounding)
        base_result = results[0][1]
        for precision, result in results[1:]:
            # Allow for small rounding differences
            diff = abs(result - base_result)
            self.assertLess(diff, decimal.Decimal("1e-15"))
        
        print(f"✅ Precision consistency test passed")
        for precision, result in results:
            print(f"   {precision} digits: {result}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        calculator = UGPDeltaCalculator(precision_digits=50)
        
        # Test that division by k_gen2 (which is negative) works correctly
        delta_ugp = calculator.calculate_delta_ugp()
        
        # δ_UGP should be negative (k_L² is positive, k_gen2 is negative)
        self.assertLess(delta_ugp, decimal.Decimal(0))
        
        # δ_UGP should be small in magnitude (close to target of -0.0163)
        self.assertLess(abs(delta_ugp), decimal.Decimal(1))
        
        print(f"✅ Edge cases test passed")
        print(f"   δ_UGP sign: {'Negative' if delta_ugp < 0 else 'Positive'}")
        print(f"   δ_UGP magnitude: {abs(delta_ugp)}")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete experiment."""
    
    def test_complete_experiment(self):
        """Test the complete experiment workflow."""
        calculator = UGPDeltaCalculator(precision_digits=50)
        results = calculator.run_experiment()
        
        # Test that all required components are present
        self.assertIn("json_results", results)
        self.assertIn("human_report", results)
        self.assertIn("execution_time", results)
        
        # Test execution time is reasonable (should complete quickly)
        self.assertLess(results["execution_time"], 10.0)  # Less than 10 seconds
        
        print(f"✅ Complete experiment test passed")
        print(f"   Execution time: {results['execution_time']:.3f} seconds")
    
    def test_result_validation(self):
        """Test that results are physically reasonable."""
        calculator = UGPDeltaCalculator(precision_digits=50)
        delta_ugp_predicted = calculator.calculate_delta_ugp()
        
        # δ_UGP should be negative and small in magnitude
        self.assertLess(delta_ugp_predicted, decimal.Decimal(0))
        self.assertGreater(delta_ugp_predicted, decimal.Decimal(-1))
        
        # Should be in reasonable range compared to target
        target = calculator.delta_ugp_target
        relative_diff = abs(delta_ugp_predicted - target) / abs(target)
        self.assertLess(relative_diff, decimal.Decimal(1))  # Within 100% of target
        
        print(f"✅ Result validation test passed")
        print(f"   δ_UGP predicted: {delta_ugp_predicted}")
        print(f"   δ_UGP target:    {target}")
        print(f"   Relative diff:   {relative_diff:.3f}")


def run_test_suite():
    """Run the complete test suite."""
    print("🧪 Running UGP-C-01 Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUGPDeltaCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestPrecisionValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("🧪 TEST SUITE SUMMARY")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures:  {len(result.failures)}")
    print(f"   Errors:    {len(result.errors)}")
    print(f"   Success:   {result.wasSuccessful()}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
