#!/usr/bin/env python3
"""
CKM-Preserving Balanced PMNS Optimizer V2
=========================================

Uses the CORRECT experiment (UGPYukawaCKMPMNSFlowOptimization) that produces
perfect CKM results, then optimizes PMNS angles while preserving CKM.

Perfect CKM baseline:
- τ₀ scaling: 1.5, ε scaling: 0.8, ε' scaling: 4.0, norm: Frobenius
- CKM errors: θ₁₂: 1.21%, θ₁₃: 0.06%, θ₂₃: 0.81%
"""

import numpy as np
import sys
import os
from typing import Dict, List, Tuple, Any, Optional
import json
import time
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_yukawa_ckm_pmns_flow_optimization import UGPYukawaCKMPMNSFlowOptimization

class CKMPreservingBalancedOptimizerV2:
    """
    CKM-preserving optimizer using the CORRECT experiment that produces perfect CKM.
    
    Strategy:
    1. LOCK perfect CKM parameters (τ₀=1.5, ε=0.8, ε'=4.0, norm=Frobenius)
    2. Test different parameter combinations that might improve PMNS
    3. Strict CKM validation gates to prevent any regression
    4. Focus on balanced PMNS improvement
    """
    
    def __init__(self):
        self.perfect_ckm_params = {
            'tau0_scale': 1.5,
            'epsilon_scale': 0.8,
            'epsilon_prime_scale': 4.0,
            'norm_method': 'frobenius'
        }
        self.baseline_pmns_errors = None
        self.best_config = None
        self.best_pmns_error = float('inf')
        self.improvements_found = 0
        self.total_tests = 0
        self.ckm_violations = 0
        
        # Load configuration
        config_path = project_root / "configs" / "experiments" / "ugp_yukawa_ckm_pmns_flow_optimization.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def validate_ckm_preservation(self, result: Dict[str, Any]) -> Tuple[bool, Dict[str, float]]:
        """
        Strict CKM validation - reject any configuration that harms perfect CKM.
        
        Expected perfect CKM errors:
        - θ₁₂: 1.21% error
        - θ₁₃: 0.06% error  
        - θ₂₃: 0.81% error
        """
        
        if 'experimental_errors' not in result:
            return False, {}
        
        errors = result['experimental_errors']
        
        # Extract CKM errors
        ckm_errors = {
            'theta12': errors.get('theta12_error', 1.0) * 100,  # Convert to percentage
            'theta13': errors.get('theta13_error', 1.0) * 100,
            'theta23': errors.get('theta23_error', 1.0) * 100
        }
        
        # Strict CKM validation gates - must match perfect CKM within tolerance
        ckm_valid = (
            abs(ckm_errors['theta12'] - 1.21) < 0.5 and  # Within 0.5% of perfect
            abs(ckm_errors['theta13'] - 0.06) < 0.5 and  # Within 0.5% of perfect
            abs(ckm_errors['theta23'] - 0.81) < 0.5      # Within 0.5% of perfect
        )
        
        return ckm_valid, ckm_errors
    
    def test_balanced_configuration(self, tau0_scale: float, epsilon_scale: float, 
                                  epsilon_prime_scale: float, norm_method: str) -> Dict[str, Any]:
        """Test a balanced configuration with CKM validation."""
        
        try:
            # Create experiment instance
            experiment = UGPYukawaCKMPMNSFlowOptimization(self.config, project_root)
            
            # Test the configuration
            result = experiment.test_baseline_configuration(
                tau0_scale=tau0_scale,
                epsilon_scale=epsilon_scale,
                epsilon_prime_scale=epsilon_prime_scale,
                norm_method=norm_method
            )
            
            if result is None:
                return {"error": "Experiment failed", "ckm_valid": False}
            
            # STRICT CKM VALIDATION - must preserve perfect CKM
            ckm_valid, ckm_errors = self.validate_ckm_preservation(result)
            
            if not ckm_valid:
                self.ckm_violations += 1
                return {
                    "error": f"CKM validation failed: {ckm_errors}",
                    "ckm_valid": False,
                    "ckm_errors": ckm_errors
                }
            
            # Extract PMNS errors
            if 'experimental_errors' in result:
                errors = result['experimental_errors']
                pmns_errors = {
                    'theta12': errors.get('pmns_theta12_error', 1.0) * 100,
                    'theta13': errors.get('pmns_theta13_error', 1.0) * 100,
                    'theta23': errors.get('pmns_theta23_error', 1.0) * 100
                }
                
                avg_pmns_error = (pmns_errors['theta12'] + pmns_errors['theta13'] + pmns_errors['theta23']) / 3
                
                return {
                    "pmns_errors": pmns_errors,
                    "avg_pmns_error": avg_pmns_error,
                    "ckm_valid": True,
                    "ckm_errors": ckm_errors,
                    "result": result,
                    "success": True
                }
            else:
                return {"error": "No PMNS errors found", "ckm_valid": False}
            
        except Exception as e:
            return {"error": str(e), "ckm_valid": False}
    
    def generate_balanced_parameter_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate parameter combinations that might improve PMNS while preserving CKM.
        
        Strategy: Start with perfect CKM params and make small adjustments
        """
        
        combinations = []
        
        # Perfect CKM baseline
        combinations.append({
            'tau0_scale': 1.5,
            'epsilon_scale': 0.8,
            'epsilon_prime_scale': 4.0,
            'norm_method': 'frobenius',
            'description': 'Perfect CKM baseline'
        })
        
        # Small variations around perfect CKM
        base_params = [1.5, 0.8, 4.0]
        variations = [0.1, 0.2, 0.3, 0.5]
        
        for i, base_param in enumerate(base_params):
            for variation in variations:
                new_params = base_params.copy()
                new_params[i] = base_param + variation
                
                combinations.append({
                    'tau0_scale': new_params[0],
                    'epsilon_scale': new_params[1],
                    'epsilon_prime_scale': new_params[2],
                    'norm_method': 'frobenius',
                    'description': f'Variation {i+1}: +{variation}'
                })
                
                combinations.append({
                    'tau0_scale': new_params[0],
                    'epsilon_scale': new_params[1],
                    'epsilon_prime_scale': new_params[2],
                    'norm_method': 'frobenius',
                    'description': f'Variation {i+1}: -{variation}'
                })
        
        # Test different normalization methods
        for norm in ['spectral_radius', 'max_element', 'trace_norm']:
            combinations.append({
                'tau0_scale': 1.5,
                'epsilon_scale': 0.8,
                'epsilon_prime_scale': 4.0,
                'norm_method': norm,
                'description': f'Different norm: {norm}'
            })
        
        return combinations[:20]  # Limit to reasonable number
    
    def run_balanced_optimization(self) -> Dict[str, Any]:
        """Run CKM-preserving balanced PMNS optimization."""
        
        print("🔒 CKM-PRESERVING BALANCED PMNS OPTIMIZATION V2")
        print("=" * 60)
        print("Strategy: LOCK perfect CKM, test parameter variations for PMNS improvement")
        print("Perfect CKM baseline: τ₀=1.5, ε=0.8, ε'=4.0, norm=Frobenius")
        print()
        
        # Get baseline with perfect CKM
        print("🔒 Getting perfect CKM baseline...")
        baseline_result = self.test_balanced_configuration(**self.perfect_ckm_params)
        
        if not baseline_result.get("success"):
            print(f"❌ Baseline failed: {baseline_result.get('error')}")
            return {"error": "Baseline failed"}
        
        if not baseline_result.get("ckm_valid"):
            print(f"❌ Baseline CKM invalid: {baseline_result.get('ckm_errors')}")
            return {"error": "Baseline CKM invalid"}
        
        self.baseline_pmns_errors = baseline_result["pmns_errors"]
        baseline_avg_error = baseline_result["avg_pmns_error"]
        
        print(f"📊 Perfect CKM Baseline:")
        print(f"   CKM θ₁₂: {baseline_result['ckm_errors']['theta12']:.2f}% (perfect: 1.21%)")
        print(f"   CKM θ₁₃: {baseline_result['ckm_errors']['theta13']:.2f}% (perfect: 0.06%)")
        print(f"   CKM θ₂₃: {baseline_result['ckm_errors']['theta23']:.2f}% (perfect: 0.81%)")
        print(f"   PMNS θ₁₂: {self.baseline_pmns_errors['theta12']:.2f}%")
        print(f"   PMNS θ₁₃: {self.baseline_pmns_errors['theta13']:.2f}%")
        print(f"   PMNS θ₂₃: {self.baseline_pmns_errors['theta23']:.2f}%")
        print(f"   PMNS Average: {baseline_avg_error:.2f}%")
        print()
        
        # Generate parameter combinations
        combinations = self.generate_balanced_parameter_combinations()
        
        print(f"🧮 Generated {len(combinations)} parameter combinations")
        print(f"🎯 Testing combinations with CKM preservation gates...")
        print()
        
        # Test combinations
        improvements = []
        start_time = time.time()
        
        for i, combo in enumerate(combinations):
            if i % 5 == 0:
                elapsed = time.time() - start_time
                print(f"⏱️  Progress: {i}/{len(combinations)} ({i/len(combinations)*100:.1f}%) - {elapsed:.1f}s - CKM violations: {self.ckm_violations}")
            
            result = self.test_balanced_configuration(
                combo['tau0_scale'],
                combo['epsilon_scale'],
                combo['epsilon_prime_scale'],
                combo['norm_method']
            )
            self.total_tests += 1
            
            if result.get("success") and result.get("ckm_valid"):
                # Check if this improves PMNS while preserving CKM
                pmns_improvement = baseline_avg_error - result["avg_pmns_error"]
                
                if pmns_improvement > 0:  # Any PMNS improvement
                    improvements.append({
                        "combo": combo,
                        "pmns_improvement": pmns_improvement,
                        "avg_pmns_error": result["avg_pmns_error"],
                        "pmns_errors": result["pmns_errors"],
                        "ckm_errors": result["ckm_errors"]
                    })
                    
                    self.improvements_found += 1
                    
                    if result["avg_pmns_error"] < self.best_pmns_error:
                        self.best_pmns_error = result["avg_pmns_error"]
                        self.best_config = result
                    
                    print(f"✅ Improvement #{self.improvements_found}: PMNS avg = {result['avg_pmns_error']:.2f}% (improved by {pmns_improvement:.2f}%) - {combo['description']}")
        
        elapsed = time.time() - start_time
        
        # Results summary
        print("\n" + "=" * 60)
        print("🔒 CKM-PRESERVING BALANCED OPTIMIZATION RESULTS V2")
        print("=" * 60)
        print(f"⏱️  Total Time: {elapsed:.1f} seconds")
        print(f"🧮 Total Tests: {self.total_tests}")
        print(f"🔒 CKM Violations: {self.ckm_violations}")
        print(f"✅ Improvements Found: {self.improvements_found}")
        print(f"📈 Success Rate: {self.improvements_found/self.total_tests*100:.1f}%")
        print(f"🔒 CKM Preservation Rate: {(self.total_tests-self.ckm_violations)/self.total_tests*100:.1f}%")
        print()
        
        if self.best_config:
            print("🏆 BEST BALANCED CONFIGURATION:")
            print(f"   PMNS Average Error: {self.best_pmns_error:.2f}% (baseline: {baseline_avg_error:.2f}%)")
            print(f"   PMNS θ₁₂: {self.best_config['pmns_errors']['theta12']:.2f}% (baseline: {self.baseline_pmns_errors['theta12']:.2f}%)")
            print(f"   PMNS θ₁₃: {self.best_config['pmns_errors']['theta13']:.2f}% (baseline: {self.baseline_pmns_errors['theta13']:.2f}%)")
            print(f"   PMNS θ₂₃: {self.best_config['pmns_errors']['theta23']:.2f}% (baseline: {self.baseline_pmns_errors['theta23']:.2f}%)")
            print(f"   CKM Preservation: ✅ PERFECT")
            print()
            
            if self.best_pmns_error < baseline_avg_error * 0.9:
                print("🎉 SUCCESS: Significant balanced PMNS improvement achieved!")
            elif self.best_pmns_error < baseline_avg_error * 0.95:
                print("🎯 GOOD PROGRESS: Moderate balanced PMNS improvement achieved")
            else:
                print("⚠️  LIMITED SUCCESS: Small balanced improvement achieved")
        else:
            print("❌ NO IMPROVEMENTS FOUND")
            print("   All tested configurations either failed CKM gates or didn't improve PMNS")
            print("   This suggests the perfect CKM configuration is already optimal")
        
        return {
            "baseline_pmns_errors": self.baseline_pmns_errors,
            "baseline_avg_error": baseline_avg_error,
            "best_pmns_error": self.best_pmns_error,
            "best_config": self.best_config,
            "improvements_found": self.improvements_found,
            "total_tests": self.total_tests,
            "ckm_violations": self.ckm_violations,
            "ckm_preservation_rate": (self.total_tests-self.ckm_violations)/self.total_tests*100 if self.total_tests > 0 else 0,
            "elapsed_time": elapsed,
            "all_improvements": improvements
        }

def main():
    """Run CKM-preserving balanced optimization."""
    optimizer = CKMPreservingBalancedOptimizerV2()
    results = optimizer.run_balanced_optimization()
    
    # Save results
    output_file = "ckm_preserving_balanced_optimization_v2_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
