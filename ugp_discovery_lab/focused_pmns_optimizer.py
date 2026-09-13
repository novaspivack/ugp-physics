#!/usr/bin/env python3
"""
FOCUSED PMNS Optimizer: Target specific angle improvements
Current status: θ₁₃ GOOD (6.47%), θ₁₂ needs work (11.78%), θ₂₃ needs work (14.34%)
Target: Get θ₁₂ and θ₂₃ to <10% error while keeping θ₁₃ good
"""

import numpy as np
import sys
import os
from pathlib import Path

_LAB_ROOT = Path(__file__).resolve().parent
if str(_LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAB_ROOT))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow
import yaml

class FocusedPMNSOptimizer:
    def __init__(self):
        # Load configuration
        with open('configs/experiments/ugp_single_law_uuf_flow.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # PDG targets
        self.targets = [33.44, 8.57, 49.0]  # θ₁₂, θ₁₃, θ₂₃
        
        # Current baseline results
        self.baseline_errors = [0.1178, 0.0647, 0.1434]  # θ₁₂, θ₁₃, θ₂₃
        self.baseline_avg = np.mean(self.baseline_errors)
        
        print(f"🎯 CURRENT BASELINE:")
        print(f"   θ₁₂: {self.baseline_errors[0]*100:.1f}% error")
        print(f"   θ₁₃: {self.baseline_errors[1]*100:.1f}% error") 
        print(f"   θ₂₃: {self.baseline_errors[2]*100:.1f}% error")
        print(f"   Average: {self.baseline_avg*100:.1f}% error")
        print()
        
    def test_configuration(self, nu_r_triples=None, md_scale=100, mr_scale=1e14, 
                          hierarchy_factor=1e-3, regularization_factor=0.1):
        """Test a specific configuration."""
        try:
            # Create experiment instance
            experiment = UGPSingleLawUUFFlow(self.config, Path('.'))
            
            # Override neutrino triples if provided
            if nu_r_triples is not None:
                original_method = experiment._construct_working_pathB_neutrino_mass
                
                def custom_enhanced_method():
                    # Load left-handed neutrino triples
                    nu_L_triples = [
                        experiment.canonical_triples[("nu_e", "nu", 1)],
                        experiment.canonical_triples[("nu_mu", "nu", 2)],
                        experiment.canonical_triples[("nu_tau", "nu", 3)]
                    ]
                    
                    gens = [1, 2, 3]
                    
                    # Extract irrep features
                    nu_L_features = [experiment._extract_enhanced_irrep_features(a, b, c, g, "nu") 
                                    for (a, b, c), g in zip(nu_L_triples, gens)]
                    nu_R_features = [experiment._extract_enhanced_irrep_features(a, b, c, g, "nu_R") 
                                    for (a, b, c), g in zip(nu_r_triples, gens)]
                    
                    # Enhanced Dirac mass matrix with targeted scaling
                    M_D = np.zeros((3, 3), dtype=complex)
                    for i, feat_L in enumerate(nu_L_features):
                        for j, feat_R in enumerate(nu_R_features):
                            s_L, e_L, delta_L = feat_L
                            s_R, e_R, delta_R = feat_R
                            
                            overlap = (s_L * s_R + 
                                      e_L[0] * e_R[0] + e_L[1] * e_R[1] + 
                                      delta_L * delta_R * experiment.k_L2)
                            
                            M_D[i, j] = overlap * md_scale
                    
                    # Enhanced Majorana mass matrix with hierarchy
                    M_R = np.zeros((3, 3), dtype=complex)
                    for i, feat_i in enumerate(nu_R_features):
                        for j, feat_j in enumerate(nu_R_features):
                            s_i, e_i, delta_i = feat_i
                            s_j, e_j, delta_j = feat_j
                            
                            gram = (s_i * s_j + 
                                   e_i[0] * e_j[0] + e_i[1] * e_j[1] + 
                                   delta_i * delta_j * experiment.k_L2)
                            
                            hierarchy = (1.0 if i == j else hierarchy_factor)
                            M_R[i, j] = gram * mr_scale * hierarchy
                    
                    # Enhanced regularization
                    M_R = 0.5 * (M_R + M_R.T)
                    M_R += np.eye(3) * np.trace(M_R) * regularization_factor
                    
                    # Apply the proven seesaw mechanism
                    M_eff, U_L = experiment._apply_proven_seesaw(M_D, M_R)
                    
                    # Apply sophisticated PMNS derivation
                    pmns_result = experiment._sophisticated_pmns_derivation(M_eff, U_L)
                    
                    # Extract the final neutrino mass matrix
                    U_pmns = np.array(pmns_result['U_pmns'], dtype=complex)
                    U_nu = np.array(pmns_result['U_nu'], dtype=complex)
                    neutrino_masses_squared = np.array(pmns_result['neutrino_masses_squared'])
                    
                    # Build final neutrino mass matrix
                    M_final = U_nu @ np.diag(np.sqrt(np.maximum(neutrino_masses_squared, 1e-12))) @ U_nu.T
                    
                    return M_final
                
                experiment._construct_working_pathB_neutrino_mass = custom_enhanced_method
            
            # Run the experiment
            result = experiment.run_task('single_law_uuf_flow')
            
            if result['status'] == 'success':
                pmns_angles = result['mixing_matrices']['pmns_angles']
                values = [pmns_angles['theta12'], pmns_angles['theta13'], pmns_angles['theta23']]
                errors = [abs(v - t) / t for v, t in zip(values, self.targets)]
                avg_error = np.mean(errors)
                
                return {
                    'success': True,
                    'angles': values,
                    'errors': errors,
                    'avg_error': avg_error,
                    'theta12_error': errors[0],
                    'theta13_error': errors[1], 
                    'theta23_error': errors[2]
                }
            else:
                return {'success': False, 'error': result.get('error', 'Unknown')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def focused_optimization(self):
        """Focused optimization targeting θ₁₂ and θ₂₃ improvements."""
        print("🎯 FOCUSED PMNS OPTIMIZATION")
        print("=" * 50)
        print("Target: Improve θ₁₂ (11.78%) and θ₂₃ (14.34%) while keeping θ₁₃ good (6.47%)")
        print()
        
        # Test different neutrino triple combinations
        test_triples = [
            [(2, 5, 5), (7, 11, 13), (17, 19, 23)],  # Current best
            [(1, 3, 7), (11, 13, 17), (19, 23, 29)],  # Prime numbers
            [(2, 4, 8), (3, 9, 27), (5, 25, 125)],    # Powers
            [(1, 2, 4), (3, 6, 12), (5, 10, 20)],     # Multiples
            [(2, 3, 5), (7, 11, 13), (17, 19, 23)],   # Small primes
            [(1, 1, 2), (2, 3, 5), (8, 13, 21)],      # Fibonacci-like
            [(3, 5, 7), (11, 13, 17), (19, 23, 29)],  # Odd primes
        ]
        
        # Test different mass scales
        test_scales = [
            (100, 1e14, 1e-3, 0.1),    # Baseline
            (50, 1e14, 1e-3, 0.1),     # Lower Dirac
            (200, 1e14, 1e-3, 0.1),    # Higher Dirac
            (100, 1e13, 1e-3, 0.1),    # Lower Majorana
            (100, 1e15, 1e-3, 0.1),    # Higher Majorana
            (100, 1e14, 1e-4, 0.1),    # Lower hierarchy
            (100, 1e14, 1e-2, 0.1),    # Higher hierarchy
            (100, 1e14, 1e-3, 0.05),   # Lower regularization
            (100, 1e14, 1e-3, 0.2),    # Higher regularization
        ]
        
        best_config = None
        best_avg_error = float('inf')
        best_errors = None
        improvements = []
        
        total_tests = len(test_triples) * len(test_scales)
        print(f"🧪 TESTING {total_tests} COMBINATIONS...")
        print()
        
        test_count = 0
        
        for i, triples in enumerate(test_triples):
            for j, (md, mr, hf, rf) in enumerate(test_scales):
                test_count += 1
                
                if test_count % 10 == 0:
                    print(f"  Progress: {test_count}/{total_tests} ({test_count/total_tests*100:.1f}%)")
                    if best_config:
                        print(f"  Best average so far: {best_avg_error*100:.2f}%")
                
                result = self.test_configuration(
                    nu_r_triples=triples,
                    md_scale=md,
                    mr_scale=mr,
                    hierarchy_factor=hf,
                    regularization_factor=rf
                )
                
                if result['success']:
                    # Check if this is an improvement
                    if result['avg_error'] < best_avg_error:
                        best_avg_error = result['avg_error']
                        best_config = {
                            'triples': triples,
                            'md_scale': md,
                            'mr_scale': mr,
                            'hierarchy_factor': hf,
                            'regularization_factor': rf
                        }
                        best_errors = result['errors']
                        
                        improvement = {
                            'test': test_count,
                            'avg_error': result['avg_error'],
                            'theta12_error': result['theta12_error'],
                            'theta13_error': result['theta13_error'],
                            'theta23_error': result['theta23_error'],
                            'config': best_config.copy()
                        }
                        improvements.append(improvement)
                        
                        print(f"    🎯 IMPROVEMENT #{len(improvements)}: {result['avg_error']*100:.2f}% average")
                        print(f"      θ₁₂: {result['angles'][0]:.2f}° (error: {result['errors'][0]*100:.1f}%)")
                        print(f"      θ₁₃: {result['angles'][1]:.2f}° (error: {result['errors'][1]*100:.1f}%)")
                        print(f"      θ₂₃: {result['angles'][2]:.2f}° (error: {result['errors'][2]*100:.1f}%)")
                        print(f"      Triples: {triples}")
                        print(f"      Scales: MD={md}, MR={mr:.0e}, HF={hf:.0e}, RF={rf:.3f}")
                        print()
        
        print(f"\n🎉 FOCUSED OPTIMIZATION COMPLETE!")
        print(f"   Total tests: {test_count}")
        print(f"   Improvements found: {len(improvements)}")
        print(f"   Best average error: {best_avg_error*100:.2f}%")
        
        if best_config:
            print(f"\n🏆 BEST CONFIGURATION:")
            print(f"   Triples: {best_config['triples']}")
            print(f"   M_D scale: {best_config['md_scale']}")
            print(f"   M_R scale: {best_config['mr_scale']:.0e}")
            print(f"   Hierarchy factor: {best_config['hierarchy_factor']:.0e}")
            print(f"   Regularization factor: {best_config['regularization_factor']:.3f}")
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"   θ₁₂: {best_errors[0]*100:.1f}% error (baseline: {self.baseline_errors[0]*100:.1f}%)")
            print(f"   θ₁₃: {best_errors[1]*100:.1f}% error (baseline: {self.baseline_errors[1]*100:.1f}%)")
            print(f"   θ₂₃: {best_errors[2]*100:.1f}% error (baseline: {self.baseline_errors[2]*100:.1f}%)")
            print(f"   Average: {best_avg_error*100:.2f}% (baseline: {self.baseline_avg*100:.1f}%)")
            
            # Calculate improvement
            improvement = (self.baseline_avg - best_avg_error) / self.baseline_avg * 100
            print(f"   Overall improvement: {improvement:.1f}%")
            
            if best_avg_error < 0.10:
                print("   🎉 EXCELLENT: <10% average error achieved!")
            elif best_avg_error < 0.15:
                print("   ✅ VERY GOOD: <15% average error achieved!")
            elif best_avg_error < 0.20:
                print("   ✅ GOOD: <20% average error achieved!")
        
        return best_config, best_avg_error, improvements

if __name__ == "__main__":
    optimizer = FocusedPMNSOptimizer()
    result = optimizer.focused_optimization()
