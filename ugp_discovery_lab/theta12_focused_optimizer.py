#!/usr/bin/env python3
"""
θ₁₂-Focused PMNS Optimizer
===========================

Strategic focus on the θ₁₂ mixing angle which contributes 142.4% of total PMNS error.
Targets the (1,2) PMNS matrix element through neutrino triple optimization.
"""

import numpy as np
import sys
import os
from typing import Dict, List, Tuple, Any, Optional
import json
import time
from pathlib import Path
import yaml

# Add the UGP discovery lab to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow

class Theta12FocusedOptimizer:
    """
    Focused optimizer targeting θ₁₂ mixing angle improvement.
    
    Strategy:
    1. Generate balanced neutrino triples that specifically target θ₁₂
    2. Focus on (1,2) PMNS matrix element optimization
    3. Use mathematical patterns that favor θ₁₂ over other angles
    """
    
    def __init__(self):
        self.baseline_error = None
        self.best_config = None
        self.best_error = float('inf')
        self.improvements_found = 0
        self.total_tests = 0
        
        # Load configuration
        config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
    def generate_theta12_focused_triples(self, pattern_type: str = "balanced_squares") -> List[List[Tuple[int, int, int]]]:
        """
        Generate neutrino triple sets specifically designed to improve θ₁₂.
        
        θ₁₂ is controlled by the (1,2) element of PMNS matrix, which depends on:
        - Balanced neutrino mass scales
        - Proper mixing between first and second generations
        - Avoiding extreme ratios that break θ₁₂
        """
        
        triple_sets = []
        
        if pattern_type == "balanced_squares":
            # Balanced square patterns - avoid extreme ratios
            base_squares = [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
            
            for i in range(len(base_squares)):
                for j in range(i+1, len(base_squares)):
                    for k in range(j+1, len(base_squares)):
                        # Create balanced triples
                        triple1 = (base_squares[i], base_squares[j], base_squares[k])
                        triple2 = (base_squares[j], base_squares[k], base_squares[i])
                        triple3 = (base_squares[k], base_squares[i], base_squares[j])
                        
                        # Check ratio constraints for θ₁₂ optimization
                        max_ratio = max(triple1) / min(triple1)
                        if max_ratio <= 100:  # Much more balanced than current 65535:1
                            triple_sets.append([triple1, triple2, triple3])
        
        elif pattern_type == "fibonacci_balanced":
            # Fibonacci-based balanced patterns
            fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
            
            for i in range(len(fib)-2):
                for j in range(i+1, len(fib)-1):
                    for k in range(j+1, len(fib)):
                        triple1 = (fib[i], fib[j], fib[k])
                        triple2 = (fib[j], fib[k], fib[i])
                        triple3 = (fib[k], fib[i], fib[j])
                        
                        max_ratio = max(triple1) / min(triple1)
                        if max_ratio <= 50:  # Balanced for θ₁₂
                            triple_sets.append([triple1, triple2, triple3])
        
        elif pattern_type == "theta12_optimized":
            # Specifically designed for θ₁₂ optimization
            # Use small, balanced numbers that favor (1,2) mixing
            small_balanced = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 60]
            
            for i in range(len(small_balanced)):
                for j in range(i+1, len(small_balanced)):
                    for k in range(j+1, len(small_balanced)):
                        triple1 = (small_balanced[i], small_balanced[j], small_balanced[k])
                        triple2 = (small_balanced[j], small_balanced[k], small_balanced[i])
                        triple3 = (small_balanced[k], small_balanced[i], small_balanced[j])
                        
                        # Very strict ratio constraint for θ₁₂
                        max_ratio = max(triple1) / min(triple1)
                        if max_ratio <= 20:  # Very balanced
                            triple_sets.append([triple1, triple2, triple3])
        
        return triple_sets[:500]  # Limit to reasonable number
    
    def test_theta12_configuration(self, neutrino_triples: List[Tuple[int, int, int]]) -> Dict[str, Any]:
        """Test a specific neutrino triple configuration focusing on θ₁₂."""
        
        try:
            # Create experiment with custom neutrino triples
            experiment = UGPSingleLawUUFFlow(self.config, project_root)
            
            # Override neutrino triples in canonical_triples
            for i, triple in enumerate(neutrino_triples):
                key = (f"nu_{['e', 'mu', 'tau'][i]}", "nu", i+1)
                experiment.canonical_triples[key] = triple
            
            # Build all generators first
            generators = experiment._build_all_generators()
            
            # Apply UUF flow to all sectors
            uuf_results = experiment._apply_uuf_flow_to_all_sectors(generators)
            
            if not uuf_results:
                return {"error": "Experiment failed", "theta12_error": 100.0}
            
            # Calculate mixing matrices
            mixing_matrices = experiment._calculate_mixing_matrices(uuf_results)
            
            if not mixing_matrices:
                return {"error": "Failed to calculate mixing matrices", "theta12_error": 100.0}
            
            # Get PMNS matrix
            pmns_matrix = mixing_matrices.get('U_pmns')
            if pmns_matrix is None:
                return {"error": "No PMNS matrix", "theta12_error": 100.0}
            
            # Convert to numpy array if needed
            if isinstance(pmns_matrix, list):
                pmns_matrix = np.array(pmns_matrix)
            
            # Extract mixing angles
            def extract_mixing_angles(U):
                """Extract mixing angles from unitary matrix."""
                # Standard parameterization
                theta12 = np.arcsin(np.abs(U[0,1]))
                theta13 = np.arcsin(np.abs(U[0,2]))
                theta23 = np.arcsin(np.abs(U[1,2]))
                
                return np.degrees(theta12), np.degrees(theta13), np.degrees(theta23)
            
            theta12_pred, theta13_pred, theta23_pred = extract_mixing_angles(pmns_matrix)
            
            # PDG values
            theta12_pdg = 33.45
            theta13_pdg = 8.62
            theta23_pdg = 42.10
            
            # Calculate errors
            theta12_error = abs(theta12_pred - theta12_pdg) / theta12_pdg * 100
            theta13_error = abs(theta13_pred - theta13_pdg) / theta13_pdg * 100
            theta23_error = abs(theta23_pred - theta23_pdg) / theta23_pdg * 100
            
            avg_error = (theta12_error + theta13_error + theta23_error) / 3
            
            return {
                "theta12_error": theta12_error,
                "theta13_error": theta13_error,
                "theta23_error": theta23_error,
                "avg_error": avg_error,
                "theta12_pred": theta12_pred,
                "theta13_pred": theta13_pred,
                "theta23_pred": theta23_pred,
                "pmns_matrix": pmns_matrix.tolist(),
                "neutrino_triples": neutrino_triples,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e), "theta12_error": 100.0}
    
    def run_theta12_optimization(self, max_patterns: int = 1000) -> Dict[str, Any]:
        """Run focused θ₁₂ optimization."""
        
        print("🎯 θ₁₂-FOCUSED PMNS OPTIMIZATION")
        print("=" * 50)
        print("Strategy: Target (1,2) PMNS element through balanced neutrino triples")
        print("Goal: Reduce θ₁₂ error from 13.39% to <5%")
        print()
        
        # Get baseline
        print("🔒 Getting baseline configuration...")
        baseline_result = self.test_theta12_configuration([(1, 1, 823), (9, 1, 1023), (5, 1, 65535)])
        
        if not baseline_result.get("success"):
            print(f"❌ Baseline failed: {baseline_result.get('error')}")
            return {"error": "Baseline failed"}
        
        self.baseline_error = baseline_result["theta12_error"]
        print(f"📊 Baseline θ₁₂ Error: {self.baseline_error:.2f}%")
        print(f"📊 Baseline θ₁₂ Predicted: {baseline_result['theta12_pred']:.2f}°")
        print()
        
        # Generate focused triple patterns
        patterns = []
        for pattern_type in ["theta12_optimized", "balanced_squares", "fibonacci_balanced"]:
            patterns.extend(self.generate_theta12_focused_triples(pattern_type))
        
        print(f"🧮 Generated {len(patterns)} θ₁₂-focused patterns")
        print(f"🎯 Testing up to {max_patterns} configurations...")
        print()
        
        # Test patterns
        improvements = []
        start_time = time.time()
        
        for i, triple_set in enumerate(patterns[:max_patterns]):
            if i % 100 == 0:
                elapsed = time.time() - start_time
                print(f"⏱️  Progress: {i}/{min(len(patterns), max_patterns)} ({i/min(len(patterns), max_patterns)*100:.1f}%) - {elapsed:.1f}s")
            
            result = self.test_theta12_configuration(triple_set)
            self.total_tests += 1
            
            if result.get("success") and result["theta12_error"] < self.baseline_error:
                improvement = self.baseline_error - result["theta12_error"]
                improvements.append({
                    "triple_set": triple_set,
                    "theta12_error": result["theta12_error"],
                    "improvement": improvement,
                    "avg_error": result["avg_error"],
                    "theta12_pred": result["theta12_pred"]
                })
                
                self.improvements_found += 1
                
                if result["theta12_error"] < self.best_error:
                    self.best_error = result["theta12_error"]
                    self.best_config = result
                
                print(f"✅ Improvement #{self.improvements_found}: θ₁₂ = {result['theta12_error']:.2f}% (improved by {improvement:.2f}%)")
        
        elapsed = time.time() - start_time
        
        # Results summary
        print("\n" + "=" * 50)
        print("🎯 θ₁₂-FOCUSED OPTIMIZATION RESULTS")
        print("=" * 50)
        print(f"⏱️  Total Time: {elapsed:.1f} seconds")
        print(f"🧮 Total Tests: {self.total_tests}")
        print(f"✅ Improvements Found: {self.improvements_found}")
        print(f"📈 Success Rate: {self.improvements_found/self.total_tests*100:.1f}%")
        print()
        
        if self.best_config:
            print("🏆 BEST CONFIGURATION:")
            print(f"   θ₁₂ Error: {self.best_error:.2f}% (baseline: {self.baseline_error:.2f}%)")
            print(f"   θ₁₂ Predicted: {self.best_config['theta12_pred']:.2f}° (PDG: 33.45°)")
            print(f"   Average Error: {self.best_config['avg_error']:.2f}%")
            print(f"   Neutrino Triples: {self.best_config['neutrino_triples']}")
            print()
            
            if self.best_error < 5.0:
                print("🎉 SUCCESS: θ₁₂ error < 5% achieved!")
            elif self.best_error < self.baseline_error * 0.8:
                print("🎯 GOOD PROGRESS: Significant θ₁₂ improvement achieved")
            else:
                print("⚠️  LIMITED SUCCESS: Some improvement but more work needed")
        else:
            print("❌ NO IMPROVEMENTS FOUND")
            print("   All tested configurations were worse than baseline")
        
        return {
            "baseline_error": self.baseline_error,
            "best_error": self.best_error,
            "best_config": self.best_config,
            "improvements_found": self.improvements_found,
            "total_tests": self.total_tests,
            "success_rate": self.improvements_found/self.total_tests*100 if self.total_tests > 0 else 0,
            "elapsed_time": elapsed,
            "all_improvements": improvements
        }

def main():
    """Run θ₁₂-focused optimization."""
    optimizer = Theta12FocusedOptimizer()
    results = optimizer.run_theta12_optimization(max_patterns=1000)
    
    # Save results
    output_file = "theta12_focused_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
