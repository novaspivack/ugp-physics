"""
Algebraic basis evaluation and PSLQ helpers for dihedral lock analysis.

This module provides tools for evaluating algebraic numbers and testing
hypotheses about dihedral lock constants using PSLQ (Partial Sum of Least Squares)
algorithm for finding integer relations.
"""

import numpy as np
import sympy as sp
from typing import Dict, List, Tuple, Optional, Union
from scipy.optimize import minimize
import warnings


class AlgebraicBasis:
    """Manages algebraic basis evaluation and PSLQ analysis."""
    
    def __init__(self):
        """Initialize with common algebraic constants."""
        self.basis = {
            "1": 1.0,
            "sqrt2": np.sqrt(2),
            "sqrt3": np.sqrt(3),
            "sqrt5": np.sqrt(5),
            "phi": (1 + np.sqrt(5)) / 2,  # golden ratio
            "sqrt(2+sqrt2)": np.sqrt(2 + np.sqrt(2)),
            "sqrt(2-sqrt2)": np.sqrt(2 - np.sqrt(2)),
            "sqrt(10+2sqrt5)/2": np.sqrt(10 + 2*np.sqrt(5)) / 2,
            "sqrt(10-2sqrt5)/2": np.sqrt(10 - 2*np.sqrt(5)) / 2,
            "(sqrt6+sqrt2)/2": (np.sqrt(6) + np.sqrt(2)) / 2,
            "(sqrt6-sqrt2)/2": (np.sqrt(6) - np.sqrt(2)) / 2,
        }
        
        # Dihedral constants for verification
        self.dihedral_constants = {
            "D4": np.sqrt(2),  # 2*cos(pi/4)
            "D5": 2 * np.cos(np.pi/5),  # = phi
            "D6": 2 * np.cos(np.pi/6),  # = sqrt(3)
            "D8": 2 * np.cos(np.pi/8),  # = sqrt(2 + sqrt(2))
            "D10": 2 * np.cos(np.pi/10),
            "D12": 2 * np.cos(np.pi/12),  # = (sqrt(6) + sqrt(2))/2
        }
    
    def evaluate_expression(self, expr: str) -> float:
        """Safely evaluate a mathematical expression string."""
        try:
            # Replace common symbols
            expr = expr.replace("φ", "phi")
            expr = expr.replace("√", "sqrt")
            expr = expr.replace("π", "pi")
            
            # Use sympy for safe evaluation
            return float(sp.sympify(expr).evalf())
        except Exception as e:
            warnings.warn(f"Could not evaluate expression '{expr}': {e}")
            return np.nan
    
    def pslq_search(self, target: float, basis: List[str], 
                   max_denominator: int = 64, tolerance: float = 1e-10) -> Optional[Dict]:
        """
        Search for integer relations using PSLQ algorithm.
        
        Args:
            target: The target value to approximate
            basis: List of basis element names
            max_denominator: Maximum denominator for rational coefficients
            tolerance: Tolerance for the approximation
            
        Returns:
            Dictionary with coefficients and error, or None if no relation found
        """
        try:
            # Build basis vector
            basis_vector = [self.basis[name] for name in basis]
            
            # Add target to the end
            full_vector = basis_vector + [target]
            
            # Use scipy minimize as simple PSLQ approximation
            def objective(coeffs):
                linear_combo = sum(c * v for c, v in zip(coeffs, basis_vector))
                return abs(linear_combo - target)
            
            # Try different coefficient ranges
            best_result = None
            best_error = float('inf')
            
            for denom in range(1, max_denominator + 1):
                # Try integer coefficients scaled by denominator
                x0 = np.zeros(len(basis))
                bounds = [(-max_denominator, max_denominator) for _ in range(len(basis))]
                
                result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
                
                result_fun = float(result.fun)
                if result_fun < best_error and result_fun < float(tolerance):
                    best_error = result_fun
                    best_result = {
                        "coefficients": {str(basis[i]): float(result.x[i]) for i in range(len(basis))},
                        "error": result_fun,
                        "target": float(target),
                        "approximation": float(sum(result.x[i] * basis_vector[i] for i in range(len(basis))))
                    }
            
            return best_result
            
        except Exception as e:
            warnings.warn(f"PSLQ search failed: {e}")
            return None
    
    def test_dihedral_hypothesis(self, target: float, n: int, 
                               tolerance: float = 1e-6) -> Dict:
        """
        Test the 2cos(π/n) hypothesis for dihedral group D_n.
        
        Args:
            target: Observed coefficient value
            n: Dihedral group order
            tolerance: Tolerance for hypothesis testing
            
        Returns:
            Dictionary with hypothesis test results
        """
        # Calculate theoretical value
        theoretical = 2 * np.cos(np.pi / n)
        theoretical_inv = 1.0 / theoretical
        
        # Test both direct and inverse relationships
        direct_error = abs(target - theoretical)
        inverse_error = abs(target - theoretical_inv)
        
        # Test with PSLQ on common algebraic basis
        algebraic_basis = ["1", "sqrt2", "sqrt3", "sqrt5", "phi", 
                          "sqrt(2+sqrt2)", "(sqrt6+sqrt2)/2"]
        
        pslq_result = self.pslq_search(target, algebraic_basis, 
                                     max_denominator=64, tolerance=tolerance)
        
        return {
            "n": n,
            "target": target,
            "theoretical_2cos": theoretical,
            "theoretical_inverse": theoretical_inv,
            "direct_error": direct_error,
            "inverse_error": inverse_error,
            "direct_hypothesis_supported": direct_error < tolerance,
            "inverse_hypothesis_supported": inverse_error < tolerance,
            "pslq_relation": pslq_result,
            "verdict": self._get_verdict(direct_error, inverse_error, pslq_result, tolerance)
        }
    
    def _get_verdict(self, direct_error: float, inverse_error: float, 
                    pslq_result: Optional[Dict], tolerance: float) -> str:
        """Determine verdict based on error analysis."""
        if direct_error < tolerance:
            return "supports_2cos_direct"
        elif inverse_error < tolerance:
            return "supports_2cos_inverse"
        elif pslq_result is not None:
            return "supports_algebraic_relation"
        elif min(direct_error, inverse_error) < 10 * tolerance:
            return "ambiguous"
        else:
            return "rejects_2cos_hypothesis"
    
    def analyze_quarter_lock(self, observed_alpha: float, 
                           tolerance: float = 1e-6) -> Dict:
        """
        Analyze Quarter-Lock coefficient for consistency with 1/4.
        
        Args:
            observed_alpha: Observed coefficient value
            tolerance: Tolerance for consistency check
            
        Returns:
            Analysis results
        """
        target = 0.25  # 1/4
        error = abs(observed_alpha - target)
        
        return {
            "observed_alpha": observed_alpha,
            "target_quarter": target,
            "error": error,
            "is_consistent": error < tolerance,
            "relative_error": error / target,
            "verdict": "consistent" if error < tolerance else "inconsistent"
        }
    
    def generate_verdict_table(self, results: List[Dict]) -> str:
        """Generate a markdown table of hypothesis test results."""
        lines = ["| Dihedral Group | Observed α | 2cos(π/n) | 1/(2cos(π/n)) | Direct Error | Inverse Error | Verdict |"]
        lines.append("|----------------|------------|-----------|----------------|--------------|---------------|---------|")
        
        for result in results:
            lines.append(
                f"| D{result['n']} | {result['target']:.6f} | "
                f"{result['theoretical_2cos']:.6f} | {result['theoretical_inverse']:.6f} | "
                f"{result['direct_error']:.2e} | {result['inverse_error']:.2e} | "
                f"{result['verdict']} |"
            )
        
        return "\n".join(lines)


def test_algebraic_basis():
    """Test the algebraic basis functionality."""
    basis = AlgebraicBasis()
    
    # Test some known relationships
    print("Testing algebraic basis:")
    print(f"φ = {basis.basis['phi']:.10f}")
    print(f"2cos(π/5) = {basis.dihedral_constants['D5']:.10f}")
    print(f"2cos(π/6) = {basis.dihedral_constants['D6']:.10f}")
    print(f"2cos(π/8) = {basis.dihedral_constants['D8']:.10f}")
    
    # Test Quarter-Lock
    quarter_result = basis.analyze_quarter_lock(0.25)
    print(f"\nQuarter-Lock analysis: {quarter_result}")
    
    # Test D5 hypothesis
    d5_result = basis.test_dihedral_hypothesis(basis.dihedral_constants['D5'], 5)
    print(f"\nD5 hypothesis test: {d5_result}")


if __name__ == "__main__":
    test_algebraic_basis()
