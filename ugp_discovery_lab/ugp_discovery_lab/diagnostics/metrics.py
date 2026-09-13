"""
Metrics calculation for UGP Discovery Lab experiments.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import Counter
import math


class MetricsCalculator:
    """
    Calculate various metrics for UGP experiments.
    """
    
    def __init__(self):
        """Initialize the metrics calculator."""
        pass
    
    def calculate_fixed_index_metrics(self, gap_sequence: List[int]) -> Dict[str, Any]:
        """
        Calculate metrics for fixed-index events (like F_13 = 233).
        
        Args:
            gap_sequence: Sequence of gaps |q_t - q_{t-1}|
            
        Returns:
            Dictionary with fixed-index metrics
        """
        if not gap_sequence:
            return {"error": "Empty gap sequence"}
        
        # Count gap frequencies
        gap_counts = Counter(gap_sequence)
        total_gaps = len(gap_sequence)
        
        # Find most common gap
        most_common_gap, most_common_count = gap_counts.most_common(1)[0]
        frequency = most_common_count / total_gaps
        
        # Check for exact locks (high frequency gaps)
        exact_locks = []
        for gap, count in gap_counts.items():
            if count / total_gaps > 0.8:  # 80% threshold for exact lock
                exact_locks.append({
                    "gap": gap,
                    "frequency": count / total_gaps,
                    "count": count
                })
        
        # Calculate entropy of gap distribution
        entropy = self._calculate_entropy(list(gap_counts.values()))
        
        return {
            "total_gaps": total_gaps,
            "unique_gaps": len(gap_counts),
            "most_common_gap": most_common_gap,
            "most_common_frequency": frequency,
            "exact_locks": exact_locks,
            "gap_entropy": entropy,
            "is_rigid": len(exact_locks) > 0,
            "gap_distribution": dict(gap_counts)
        }
    
    def calculate_kernel_fit_metrics(self, kernel_points: List[List[float]]) -> Dict[str, Any]:
        """
        Calculate metrics for kernel plane fitting.
        
        Args:
            kernel_points: List of [k_M, k_G, k_L] points
            
        Returns:
            Dictionary with kernel fit metrics
        """
        if len(kernel_points) < 3:
            return {"error": "Need at least 3 points for kernel fitting"}
        
        # Convert to numpy array
        points = np.array(kernel_points)
        
        # Calculate basic statistics
        k_M_mean = np.mean(points[:, 0])
        k_G_mean = np.mean(points[:, 1])
        k_L_mean = np.mean(points[:, 2])
        
        # Calculate covariance matrix
        cov_matrix = np.cov(points.T)
        
        # Calculate principal components
        eigenvals, eigenvecs = np.linalg.eigh(cov_matrix)
        
        # Plane fitting quality metrics
        try:
            # Fit plane using least squares
            A = np.column_stack([points[:, 1], points[:, 0], np.ones(len(points))])
            b = points[:, 2]
            coeffs, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
            
            # R-squared
            k_M_pred = A @ coeffs
            ss_res = np.sum((b - k_M_pred) ** 2)
            ss_tot = np.sum((b - np.mean(b)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Check for Quarter-Lock
            a, b_coeff, c = coeffs
            is_quarter_lock = (abs(a - 1.0) < 1e-6 and 
                             abs(b_coeff - 0.25) < 1e-6 and 
                             abs(c - 0.0) < 1e-6)
            
            return {
                "n_points": len(kernel_points),
                "mean_coefficients": {
                    "k_M": float(k_M_mean),
                    "k_G": float(k_G_mean),
                    "k_L": float(k_L_mean)
                },
                "covariance_matrix": cov_matrix.tolist(),
                "principal_components": {
                    "eigenvalues": eigenvals.tolist(),
                    "eigenvectors": eigenvecs.tolist()
                },
                "plane_fit": {
                    "coefficients": coeffs.tolist(),
                    "r_squared": float(r_squared),
                    "residuals": float(residuals[0]) if len(residuals) > 0 else 0.0,
                    "rank": int(rank)
                },
                "is_quarter_lock": is_quarter_lock,
                "fit_quality": self._assess_fit_quality(float(r_squared))
            }
            
        except np.linalg.LinAlgError:
            return {"error": "Linear algebra error in plane fitting"}
    
    def calculate_universality_metrics(self, ca_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics for CA universality tests.
        
        Args:
            ca_results: List of CA test results
            
        Returns:
            Dictionary with universality metrics
        """
        if not ca_results:
            return {"error": "No CA results to analyze"}
        
        # Extract metrics
        wolfram_classes = [r.get("analysis", {}).get("wolfram_class_estimate", "Unknown") for r in ca_results]
        complexity_scores = [r.get("analysis", {}).get("average_complexity", 0) for r in ca_results]
        entropy_scores = [r.get("analysis", {}).get("final_entropy", 0) for r in ca_results]
        
        # Universality verification
        rule110_results = [r for r in ca_results if r.get("rule") == "rule110"]
        universality_verified = any(
            r.get("analysis", {}).get("rule_properties", {}).get("is_universal", False) 
            for r in rule110_results
        )
        
        # Wolfram class distribution
        class_distribution = Counter(wolfram_classes)
        
        # Complexity analysis
        avg_complexity = np.mean(complexity_scores) if complexity_scores else 0
        avg_entropy = np.mean(entropy_scores) if entropy_scores else 0
        
        return {
            "total_tests": len(ca_results),
            "universality_verified": universality_verified,
            "wolfram_class_distribution": dict(class_distribution),
            "average_complexity": float(avg_complexity),
            "average_entropy": float(avg_entropy),
            "complexity_range": (float(np.min(complexity_scores)), float(np.max(complexity_scores))) if complexity_scores else (0, 0),
            "entropy_range": (float(np.min(entropy_scores)), float(np.max(entropy_scores))) if entropy_scores else (0, 0)
        }
    
    def calculate_rg_flow_metrics(self, rg_iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics for renormalization group flow.
        
        Args:
            rg_iterations: List of RG iteration results
            
        Returns:
            Dictionary with RG flow metrics
        """
        if len(rg_iterations) < 2:
            return {"error": "Need at least 2 RG iterations"}
        
        # Extract convergence data
        plane_distances = [iter_data.get("plane_distance", 0) for iter_data in rg_iterations]
        parameter_drifts = [iter_data.get("parameter_drift", 0) for iter_data in rg_iterations]
        
        # Calculate convergence metrics
        convergence_rate = self._calculate_convergence_rate(plane_distances)
        stability_analysis = self._analyze_stability(parameter_drifts)
        
        # Check for fixed points
        fixed_point_detected = self._detect_fixed_point(plane_distances, parameter_drifts)
        
        return {
            "n_iterations": len(rg_iterations),
            "convergence_rate": float(convergence_rate),
            "final_plane_distance": float(plane_distances[-1]) if plane_distances else 0,
            "final_parameter_drift": float(parameter_drifts[-1]) if parameter_drifts else 0,
            "stability_analysis": stability_analysis,
            "fixed_point_detected": fixed_point_detected,
            "convergence_quality": self._assess_convergence_quality(convergence_rate, plane_distances[-1] if plane_distances else float('inf'))
        }
    
    def calculate_discovery_metrics(self, discoveries: List[str]) -> Dict[str, Any]:
        """
        Calculate metrics for scientific discoveries.
        
        Args:
            discoveries: List of discovery descriptions
            
        Returns:
            Dictionary with discovery metrics
        """
        if not discoveries:
            return {"total_discoveries": 0, "discovery_types": {}}
        
        # Categorize discoveries
        discovery_types = {
            "quarter_lock": sum(1 for d in discoveries if "quarter" in d.lower() and "lock" in d.lower()),
            "dihedral_lock": sum(1 for d in discoveries if "dihedral" in d.lower() and "lock" in d.lower()),
            "gap_lock": sum(1 for d in discoveries if "gap" in d.lower() and "lock" in d.lower()),
            "universality": sum(1 for d in discoveries if "universal" in d.lower()),
            "invariant": sum(1 for d in discoveries if "invariant" in d.lower()),
            "symmetry": sum(1 for d in discoveries if "symmetry" in d.lower()),
            "other": 0
        }
        
        # Count other discoveries
        categorized_count = sum(discovery_types.values()) - discovery_types["other"]
        discovery_types["other"] = len(discoveries) - categorized_count
        
        # Calculate discovery significance
        high_significance = sum(1 for d in discoveries if any(keyword in d.lower() for keyword in 
                                                           ["quarter", "dihedral", "universal", "proof", "theorem"]))
        
        return {
            "total_discoveries": len(discoveries),
            "discovery_types": discovery_types,
            "high_significance_count": high_significance,
            "discovery_rate": len(discoveries),  # Could be normalized by experiment count
            "significance_ratio": high_significance / len(discoveries) if discoveries else 0
        }
    
    def _calculate_entropy(self, counts: List[int]) -> float:
        """Calculate entropy of a distribution."""
        total = sum(counts)
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _assess_fit_quality(self, r_squared: float) -> str:
        """Assess the quality of a plane fit."""
        if r_squared > 0.99:
            return "Excellent"
        elif r_squared > 0.95:
            return "Good"
        elif r_squared > 0.9:
            return "Acceptable"
        else:
            return "Poor"
    
    def _calculate_convergence_rate(self, distances: List[float]) -> float:
        """Calculate convergence rate from distance sequence."""
        if len(distances) < 2:
            return 0.0
        
        # Fit exponential decay: distance = a * exp(-rate * iteration)
        x = np.arange(len(distances))
        y = np.array(distances)
        
        # Avoid log(0)
        y_safe = np.maximum(y, 1e-10)
        
        try:
            # Linear fit to log(y) = log(a) - rate * x
            log_y = np.log(y_safe)
            slope, _ = np.polyfit(x, log_y, 1)
            convergence_rate = -slope
            return max(0, convergence_rate)  # Ensure non-negative
        except:
            return 0.0
    
    def _analyze_stability(self, drifts: List[float]) -> Dict[str, Any]:
        """Analyze parameter drift stability."""
        if not drifts:
            return {"stable": True, "variance": 0.0}
        
        variance = np.var(drifts)
        mean_drift = np.mean(drifts)
        
        return {
            "stable": variance < 1e-6,
            "variance": float(variance),
            "mean_drift": float(mean_drift),
            "max_drift": float(np.max(drifts)),
            "min_drift": float(np.min(drifts))
        }
    
    def _detect_fixed_point(self, distances: List[float], drifts: List[float], 
                           tolerance: float = 1e-6) -> bool:
        """Detect if RG flow has reached a fixed point."""
        if not distances or not drifts:
            return False
        
        # Check if both distance and drift are below tolerance
        return (distances[-1] < tolerance and drifts[-1] < tolerance)
    
    def _assess_convergence_quality(self, rate: float, final_distance: float) -> str:
        """Assess the quality of RG convergence."""
        if final_distance < 1e-6 and rate > 0.1:
            return "Excellent"
        elif final_distance < 1e-4 and rate > 0.01:
            return "Good"
        elif final_distance < 1e-2:
            return "Acceptable"
        else:
            return "Poor"
