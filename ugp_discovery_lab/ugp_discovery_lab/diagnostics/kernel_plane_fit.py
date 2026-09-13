"""
Kernel plane fitting and Quarter-Lock law detection.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from ..core.registry import register_diagnostic


@register_diagnostic("kernel_plane_fit")
class KernelPlaneFitter:
    """
    Fit planes to kernel coefficients and detect Quarter-Lock and related laws.
    
    This implements the mathematical machinery for discovering exact algebraic
    constraints like Quarter-Lock: k_M = k_G + (1/4)k_L
    """
    
    def __init__(self, max_denominator: int = 16):
        """
        Initialize the plane fitter.
        
        Args:
            max_denominator: Maximum denominator for rational coefficient detection
        """
        self.max_denominator = max_denominator
    
    def fit_plane(self, points: List[List[float]]) -> Dict[str, Any]:
        """
        Fit a plane to 3D points using least squares.
        
        Args:
            points: List of [k_M, k_G, k_L] points
            
        Returns:
            Dictionary with plane equation and fit statistics
        """
        if len(points) < 3:
            return {"error": "Need at least 3 points to fit a plane"}
        
        points_array = np.array(points)
        
        # Set up the linear system: k_M = a*k_G + b*k_L + c
        # We want to solve: [k_G k_L 1] * [a; b; c] = k_M
        A = np.column_stack([points_array[:, 1], points_array[:, 0], np.ones(len(points_array))])
        b = points_array[:, 2]  # k_M values
        
        try:
            # Solve using least squares
            coeffs, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
            a, b_coeff, c = coeffs
            
            # Calculate R-squared
            k_M_pred = A @ coeffs
            ss_res = np.sum((b - k_M_pred) ** 2)
            ss_tot = np.sum((b - np.mean(b)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Check for rational coefficients
            rational_coeffs = self._find_rational_coefficients([a, b_coeff, c])
            
            result = {
                "plane_equation": f"k_M = {a:.6f}*k_G + {b_coeff:.6f}*k_L + {c:.6f}",
                "coefficients": {"a": float(a), "b": float(b_coeff), "c": float(c)},
                "r_squared": float(r_squared),
                "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
                "rank": int(rank),
                "rational_coefficients": rational_coeffs,
                "is_quarter_lock": self._is_quarter_lock(a, b_coeff, c),
                "n_points": len(points)
            }
            
            # Add interpretation
            result["interpretation"] = self._interpret_plane(result)
            
            return result
            
        except np.linalg.LinAlgError as e:
            return {"error": f"Linear algebra error: {e}"}
    
    def _find_rational_coefficients(self, coeffs: List[float], tolerance: float = 1e-6) -> Dict[str, Any]:
        """
        Find rational approximations for coefficients.
        
        Args:
            coeffs: List of coefficients [a, b, c]
            tolerance: Tolerance for rational approximation
            
        Returns:
            Dictionary with rational approximations
        """
        rational_coeffs = {}
        
        for i, coeff in enumerate(coeffs):
            rational = self._float_to_rational(coeff, tolerance)
            rational_coeffs[f"coeff_{i}"] = rational
        
        return rational_coeffs
    
    def _float_to_rational(self, x: float, tolerance: float = 1e-6) -> Dict[str, Any]:
        """
        Convert float to rational approximation.
        
        Args:
            x: Float to convert
            tolerance: Tolerance for approximation
            
        Returns:
            Dictionary with rational approximation
        """
        if abs(x) < tolerance:
            return {"numerator": 0, "denominator": 1, "exact": True}
        
        # Try denominators up to max_denominator
        for denom in range(1, self.max_denominator + 1):
            num = round(x * denom)
            if abs(x - num / denom) < tolerance:
                return {
                    "numerator": int(num),
                    "denominator": int(denom),
                    "value": num / denom,
                    "exact": True
                }
        
        # No exact rational found
        return {
            "numerator": None,
            "denominator": None,
            "value": x,
            "exact": False
        }
    
    def _is_quarter_lock(self, a: float, b: float, c: float, tolerance: float = 1e-6) -> bool:
        """
        Check if the plane corresponds to Quarter-Lock law.
        
        Quarter-Lock: k_M = k_G + (1/4)*k_L
        
        Args:
            a, b, c: Plane coefficients (k_M = a*k_G + b*k_L + c)
            tolerance: Tolerance for equality check
            
        Returns:
            True if this is Quarter-Lock
        """
        return (abs(a - 1.0) < tolerance and 
                abs(b - 0.25) < tolerance and 
                abs(c - 0.0) < tolerance)
    
    def _interpret_plane(self, plane_result: Dict[str, Any]) -> str:
        """
        Provide interpretation of the fitted plane.
        
        Args:
            plane_result: Result from fit_plane()
            
        Returns:
            Human-readable interpretation
        """
        if "error" in plane_result:
            return f"Error: {plane_result['error']}"
        
        coeffs = plane_result["coefficients"]
        a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
        r_squared = plane_result["r_squared"]
        
        interpretation = f"Plane fit with R² = {r_squared:.4f}"
        
        if plane_result["is_quarter_lock"]:
            interpretation += " - This is the QUARTER-LOCK LAW: k_M = k_G + (1/4)k_L"
        else:
            # Check for other known patterns
            if abs(a - 1.0) < 1e-6 and abs(b - 0.5) < 1e-6 and abs(c - 0.0) < 1e-6:
                interpretation += " - This matches Half-Lock pattern: k_M = k_G + (1/2)k_L"
            elif abs(a - 1.0) < 1e-6 and abs(b - 1.0) < 1e-6 and abs(c - 0.0) < 1e-6:
                interpretation += " - This matches Full-Lock pattern: k_M = k_G + k_L"
            else:
                interpretation += f" - Custom law: k_M = {a:.3f}k_G + {b:.3f}k_L + {c:.3f}"
        
        # Add quality assessment
        if r_squared > 0.99:
            interpretation += " (Excellent fit)"
        elif r_squared > 0.95:
            interpretation += " (Good fit)"
        elif r_squared > 0.9:
            interpretation += " (Acceptable fit)"
        else:
            interpretation += " (Poor fit - may not be a plane)"
        
        return interpretation
    
    def detect_dihedral_locks(self, points_by_symmetry: Dict[str, List[List[float]]]) -> Dict[str, Any]:
        """
        Detect Dihedral-Lock patterns across different symmetry groups.
        
        Args:
            points_by_symmetry: Dictionary mapping symmetry names to point lists
            
        Returns:
            Dictionary with detected dihedral locks
        """
        results = {}
        
        for symmetry_name, points in points_by_symmetry.items():
            if len(points) >= 3:
                plane_result = self.fit_plane(points)
                results[symmetry_name] = plane_result
                
                # Check for dihedral lock pattern
                if "error" not in plane_result:
                    coeffs = plane_result["coefficients"]
                    a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
                    
                    # Look for pattern: k_M = k_G + (1/λ_n)k_L
                    if abs(a - 1.0) < 1e-6 and abs(c - 0.0) < 1e-6 and b > 0:
                        lambda_n = 1.0 / b if b > 1e-6 else None
                        if lambda_n and self._is_rational(lambda_n):
                            results[symmetry_name]["dihedral_lock"] = {
                                "detected": True,
                                "lambda_n": lambda_n,
                                "equation": f"k_M = k_G + (1/{1/b:.3f})k_L"
                            }
                        else:
                            results[symmetry_name]["dihedral_lock"] = {"detected": False}
                    else:
                        results[symmetry_name]["dihedral_lock"] = {"detected": False}
        
        return results
    
    def _is_rational(self, x: float, tolerance: float = 1e-6) -> bool:
        """Check if a number is rational (has a simple fractional representation)."""
        for denom in range(1, self.max_denominator + 1):
            num = round(x * denom)
            if abs(x - num / denom) < tolerance:
                return True
        return False
    
    def analyze_kernel_evolution(self, kernel_history: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Analyze the evolution of kernel coefficients over time.
        
        Args:
            kernel_history: List of kernel coefficient dictionaries
            
        Returns:
            Dictionary with evolution analysis
        """
        if len(kernel_history) < 3:
            return {"error": "Need at least 3 kernel states for evolution analysis"}
        
        # Extract coefficient sequences
        k_M_seq = [state.get("k_M", 0) for state in kernel_history]
        k_G_seq = [state.get("k_G", 0) for state in kernel_history]
        k_L_seq = [state.get("k_L", 0) for state in kernel_history]
        
        # Create 3D points for plane fitting
        points = [[k_M, k_G, k_L] for k_M, k_G, k_L in zip(k_M_seq, k_G_seq, k_L_seq)]
        
        # Fit plane to the evolution
        plane_result = self.fit_plane(points)
        
        # Analyze coefficient stability
        stability_analysis = {
            "k_M_stability": self._calculate_stability(k_M_seq),
            "k_G_stability": self._calculate_stability(k_G_seq),
            "k_L_stability": self._calculate_stability(k_L_seq)
        }
        
        # Check for conservation laws
        conservation_laws = self._detect_conservation_laws(k_M_seq, k_G_seq, k_L_seq)
        
        return {
            "plane_fit": plane_result,
            "stability_analysis": stability_analysis,
            "conservation_laws": conservation_laws,
            "evolution_length": len(kernel_history)
        }
    
    def _calculate_stability(self, sequence: List[float]) -> Dict[str, float]:
        """Calculate stability metrics for a coefficient sequence."""
        if not sequence:
            return {"variance": 0, "stability": 0}
        
        mean_val = np.mean(sequence)
        variance = np.var(sequence)
        stability = 1.0 / (1.0 + variance)  # Higher stability = lower variance
        
        return {
            "mean": float(mean_val),
            "variance": float(variance),
            "stability": float(stability)
        }
    
    def _detect_conservation_laws(self, k_M_seq: List[float], k_G_seq: List[float], 
                                 k_L_seq: List[float]) -> Dict[str, Any]:
        """Detect potential conservation laws in coefficient evolution."""
        conservation_laws = {}
        
        # Check Quarter-Lock conservation: k_M - k_G - (1/4)k_L should be constant
        quarter_lock_residuals = [
            k_M - k_G - 0.25 * k_L 
            for k_M, k_G, k_L in zip(k_M_seq, k_G_seq, k_L_seq)
        ]
        
        quarter_lock_variance = np.var(quarter_lock_residuals)
        conservation_laws["quarter_lock"] = {
            "conserved": quarter_lock_variance < 1e-6,
            "variance": float(quarter_lock_variance),
            "residuals": quarter_lock_residuals
        }
        
        # Check other potential conservation laws
        # Add more conservation law checks here as needed
        
        return conservation_laws
