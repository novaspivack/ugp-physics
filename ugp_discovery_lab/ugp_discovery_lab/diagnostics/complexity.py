"""
Complexity analysis tools for UGP Discovery Lab.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import Counter
import math


class ComplexityAnalyzer:
    """
    Analyze computational complexity and dynamical properties of UGP evolutions.
    """
    
    def __init__(self):
        """Initialize the complexity analyzer."""
        pass
    
    def analyze_entropy(self, sequence: List[int], base: int = 2) -> Dict[str, float]:
        """
        Calculate Shannon entropy of a sequence.
        
        Args:
            sequence: Input sequence
            base: Logarithm base for entropy calculation
            
        Returns:
            Dictionary with entropy statistics
        """
        if not sequence:
            return {"entropy": 0.0, "normalized_entropy": 0.0}
        
        # Count frequencies
        counter = Counter(sequence)
        total = len(sequence)
        
        # Calculate entropy
        entropy = 0.0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log(p, base)
        
        # Normalize by maximum possible entropy
        max_entropy = math.log(len(counter), base) if len(counter) > 1 else 0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return {
            "entropy": float(entropy),
            "normalized_entropy": float(normalized_entropy),
            "unique_symbols": len(counter),
            "total_symbols": total
        }
    
    def analyze_kolmogorov_complexity_proxy(self, sequence: List[int]) -> Dict[str, float]:
        """
        Estimate Kolmogorov complexity using Lempel-Ziv compression.
        
        Args:
            sequence: Input sequence
            
        Returns:
            Dictionary with complexity estimates
        """
        if not sequence:
            return {"lz_complexity": 0.0, "compression_ratio": 0.0}
        
        # Convert to string for LZ analysis
        seq_str = ''.join(map(str, sequence))
        
        # Simple LZ complexity estimation
        lz_complexity = self._lz_complexity(seq_str)
        compression_ratio = lz_complexity / len(sequence) if len(sequence) > 0 else 0
        
        return {
            "lz_complexity": float(lz_complexity),
            "compression_ratio": float(compression_ratio),
            "sequence_length": len(sequence)
        }
    
    def _lz_complexity(self, s: str) -> int:
        """
        Calculate Lempel-Ziv complexity of a string.
        
        Args:
            s: Input string
            
        Returns:
            LZ complexity (number of distinct substrings)
        """
        if not s:
            return 0
        
        n = len(s)
        complexity = 1
        i = 1
        
        while i < n:
            # Find longest match
            max_len = 0
            for j in range(i):
                k = 0
                while i + k < n and s[j + k] == s[i + k]:
                    k += 1
                max_len = max(max_len, k)
            
            if max_len > 0:
                i += max_len
            else:
                i += 1
            complexity += 1
        
        return complexity
    
    def analyze_lyapunov_exponent_proxy(self, sequence: List[float]) -> Dict[str, float]:
        """
        Estimate Lyapunov exponent using sequence divergence.
        
        Args:
            sequence: Input sequence of real numbers
            
        Returns:
            Dictionary with Lyapunov exponent estimates
        """
        if len(sequence) < 2:
            return {"lyapunov_proxy": 0.0, "divergence_rate": 0.0}
        
        # Calculate differences between consecutive elements
        diffs = [abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1)]
        
        # Estimate divergence rate
        if not diffs or all(d == 0 for d in diffs):
            return {"lyapunov_proxy": 0.0, "divergence_rate": 0.0}
        
        # Simple proxy: average log of differences
        log_diffs = [math.log(d) if d > 0 else -10 for d in diffs]
        avg_log_diff = np.mean(log_diffs)
        
        # Divergence rate
        divergence_rate = np.mean(diffs)
        
        return {
            "lyapunov_proxy": float(avg_log_diff),
            "divergence_rate": float(divergence_rate),
            "sequence_length": len(sequence)
        }
    
    def analyze_wolfram_class(self, evolution_history: List[List[int]]) -> Dict[str, Any]:
        """
        Classify evolution according to Wolfram's complexity classes.
        
        Args:
            evolution_history: List of CA states over time
            
        Returns:
            Dictionary with Wolfram class analysis
        """
        if not evolution_history:
            return {"class": "Unknown", "confidence": 0.0}
        
        # Check for fixed points (Class I)
        if len(set(tuple(state) for state in evolution_history)) == 1:
            return {"class": "Class I (Fixed Point)", "confidence": 1.0}
        
        # Check for simple periodicity (Class II)
        periodicity = self._detect_periodicity(evolution_history)
        if periodicity["detected"] and periodicity["period"] <= 4:
            return {
                "class": "Class II (Periodic)", 
                "confidence": 0.9,
                "period": periodicity["period"]
            }
        
        # Analyze entropy evolution
        entropy_sequence = []
        for state in evolution_history:
            entropy_analysis = self.analyze_entropy(state)
            entropy_sequence.append(entropy_analysis["entropy"])
        
        # Check for chaotic behavior (Class III)
        if len(entropy_sequence) > 10:
            entropy_trend = np.polyfit(range(len(entropy_sequence)), entropy_sequence, 1)[0]
            if entropy_trend > 0.1:  # Increasing entropy
                return {
                    "class": "Class III (Chaotic)",
                    "confidence": 0.8,
                    "entropy_trend": float(entropy_trend)
                }
        
        # Check for complex behavior (Class IV)
        # Look for intermediate entropy with complex patterns
        avg_entropy = np.mean(entropy_sequence)
        if 0.3 < avg_entropy < 0.8:
            complexity_analysis = self.analyze_kolmogorov_complexity_proxy(evolution_history[-1])
            if complexity_analysis["compression_ratio"] > 0.5:
                return {
                    "class": "Class IV (Complex)",
                    "confidence": 0.7,
                    "average_entropy": float(avg_entropy),
                    "complexity": complexity_analysis
                }
        
        return {"class": "Unknown/Undetermined", "confidence": 0.3}
    
    def _detect_periodicity(self, sequence: List[List[int]], max_period: int = 20) -> Dict[str, Any]:
        """
        Detect periodic patterns in a sequence of states.
        
        Args:
            sequence: List of states
            max_period: Maximum period to check
            
        Returns:
            Dictionary with periodicity information
        """
        if len(sequence) < max_period * 2:
            return {"detected": False, "period": None}
        
        for period in range(1, min(max_period + 1, len(sequence) // 2)):
            is_periodic = True
            for i in range(len(sequence) - period):
                if sequence[i] != sequence[i + period]:
                    is_periodic = False
                    break
            
            if is_periodic:
                return {
                    "detected": True,
                    "period": period,
                    "pattern_length": len(sequence) // period
                }
        
        return {"detected": False, "period": None}
    
    def analyze_information_flow(self, state_sequence: List[List[int]]) -> Dict[str, Any]:
        """
        Analyze information flow and conservation in state evolution.
        
        Args:
            state_sequence: Sequence of CA states
            
        Returns:
            Dictionary with information flow analysis
        """
        if len(state_sequence) < 2:
            return {"error": "Need at least 2 states for information flow analysis"}
        
        # Calculate mutual information between consecutive states
        mutual_information = []
        for i in range(len(state_sequence) - 1):
            mi = self._calculate_mutual_information(state_sequence[i], state_sequence[i+1])
            mutual_information.append(mi)
        
        # Calculate information loss/gain
        information_change = []
        for i in range(len(state_sequence) - 1):
            prev_entropy = self.analyze_entropy(state_sequence[i])["entropy"]
            curr_entropy = self.analyze_entropy(state_sequence[i+1])["entropy"]
            information_change.append(curr_entropy - prev_entropy)
        
        return {
            "mutual_information": mutual_information,
            "average_mutual_information": float(np.mean(mutual_information)),
            "information_change": information_change,
            "average_information_change": float(np.mean(information_change)),
            "information_conserved": abs(np.mean(information_change)) < 0.1
        }
    
    def _calculate_mutual_information(self, x: List[int], y: List[int]) -> float:
        """
        Calculate mutual information between two sequences.
        
        Args:
            x, y: Input sequences
            
        Returns:
            Mutual information in bits
        """
        if len(x) != len(y):
            return 0.0
        
        # Create joint distribution
        joint_counts = Counter(zip(x, y))
        x_counts = Counter(x)
        y_counts = Counter(y)
        
        total = len(x)
        mi = 0.0
        
        for (xi, yi), joint_count in joint_counts.items():
            if joint_count > 0:
                joint_prob = joint_count / total
                x_prob = x_counts[xi] / total
                y_prob = y_counts[yi] / total
                
                if x_prob > 0 and y_prob > 0:
                    mi += joint_prob * math.log2(joint_prob / (x_prob * y_prob))
        
        return mi
    
    def comprehensive_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive complexity analysis on experimental data.
        
        Args:
            data: Dictionary containing various data sequences
            
        Returns:
            Comprehensive analysis results
        """
        results = {}
        
        # Analyze state sequences if available
        if "state_sequence" in data:
            state_seq = data["state_sequence"]
            results["entropy_analysis"] = self.analyze_entropy(state_seq[-1] if state_seq else [])
            results["wolfram_class"] = self.analyze_wolfram_class(state_seq)
            results["information_flow"] = self.analyze_information_flow(state_seq)
        
        # Analyze coefficient sequences
        for coeff_name in ["a_sequence", "b_sequence", "c_sequence"]:
            if coeff_name in data:
                seq = data[coeff_name]
                results[f"{coeff_name}_analysis"] = {
                    "entropy": self.analyze_entropy(seq),
                    "lyapunov_proxy": self.analyze_lyapunov_exponent_proxy(seq),
                    "complexity": self.analyze_kolmogorov_complexity_proxy(seq)
                }
        
        # Overall complexity assessment
        results["overall_assessment"] = self._assess_overall_complexity(results)
        
        return results
    
    def _assess_overall_complexity(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide overall complexity assessment.
        
        Args:
            analysis_results: Results from various complexity analyses
            
        Returns:
            Overall assessment dictionary
        """
        complexity_score = 0.0
        factors = []
        
        # Factor in entropy
        if "entropy_analysis" in analysis_results:
            entropy = analysis_results["entropy_analysis"]["entropy"]
            if entropy > 2.0:
                complexity_score += 0.3
                factors.append("high_entropy")
        
        # Factor in Wolfram class
        if "wolfram_class" in analysis_results:
            wolfram_class = analysis_results["wolfram_class"]["class"]
            if "Class IV" in wolfram_class:
                complexity_score += 0.4
                factors.append("complex_dynamics")
            elif "Class III" in wolfram_class:
                complexity_score += 0.2
                factors.append("chaotic_dynamics")
        
        # Factor in information conservation
        if "information_flow" in analysis_results:
            info_flow = analysis_results["information_flow"]
            if info_flow["information_conserved"]:
                complexity_score += 0.2
                factors.append("information_conserved")
        
        # Determine complexity level
        if complexity_score > 0.7:
            complexity_level = "High"
        elif complexity_score > 0.4:
            complexity_level = "Medium"
        else:
            complexity_level = "Low"
        
        return {
            "complexity_score": float(complexity_score),
            "complexity_level": complexity_level,
            "contributing_factors": factors,
            "recommendation": self._get_complexity_recommendation(complexity_level)
        }
    
    def _get_complexity_recommendation(self, complexity_level: str) -> str:
        """Get recommendation based on complexity level."""
        recommendations = {
            "High": "High complexity suggests rich dynamics suitable for universal computation",
            "Medium": "Medium complexity indicates interesting but tractable dynamics",
            "Low": "Low complexity suggests simple, predictable dynamics"
        }
        return recommendations.get(complexity_level, "Complexity assessment inconclusive")
