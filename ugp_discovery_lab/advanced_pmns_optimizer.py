#!/usr/bin/env python3
"""
Advanced PMNS Optimizer: Targeted optimization for θ₂₃ and θ₁₂
Current status: θ₁₃ EXCELLENT (3.3%), θ₁₂ GOOD (13.0%), θ₂₃ NEEDS WORK (62.2%)
Target: <5% average error
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

class AdvancedPMNSOptimizer:
    def __init__(self):
        # Load configuration
        with open('configs/experiments/ugp_single_law_uuf_flow.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # PDG targets
        self.targets = [33.44, 8.57, 49.0]  # θ₁₂, θ₁₃, θ₂₃
        
        # Current best results (from previous optimization)
        self.best_error = 0.262  # 26.2% average
        self.best_config = {
            'nu_r_triples': [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
            'md_scale': 100,
            'mr_scale': 1e14,
            'hierarchy_factor': 1e-3
        }
        
        # Results tracking
        self.optimization_history = []
        
    def test_configuration(self, nu_r_triples=None, md_scale=100, mr_scale=1e14, 
                          hierarchy_factor=1e-3, regularization_factor=0.1):
        """Test a specific configuration with enhanced parameters."""
        try:
            # Create experiment instance
            experiment = UGPSingleLawUUFFlow(self.config, Path('.'))
            
            # Override neutrino triples if provided
            if nu_r_triples is not None:
                original_method = experiment._construct_working_pathB_neutrino_mass
                
                def enhanced_method():
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
                    
                    # Construct enhanced Dirac mass matrix M_D
                    M_D = np.zeros((3, 3), dtype=complex)
                    for i, feat_L in enumerate(nu_L_features):
                        for j, feat_R in enumerate(nu_R_features):
                            s_L, e_L, delta_L = feat_L
                            s_R, e_R, delta_R = feat_R
                            
                            overlap = (s_L * s_R + 
                                      e_L[0] * e_R[0] + e_L[1] * e_R[1] + 
                                      delta_L * delta_R * experiment.k_L2)
                            
                            M_D[i, j] = overlap * md_scale
                    
                    # Construct enhanced Majorana mass matrix M_R with advanced hierarchy
                    M_R = np.zeros((3, 3), dtype=complex)
                    for i, feat_i in enumerate(nu_R_features):
                        for j, feat_j in enumerate(nu_R_features):
                            s_i, e_i, delta_i = feat_i
                            s_j, e_j, delta_j = feat_j
                            
                            gram = (s_i * s_j + 
                                   e_i[0] * e_j[0] + e_i[1] * e_j[1] + 
                                   delta_i * delta_j * experiment.k_L2)
                            
                            # Advanced hierarchy: diagonal vs off-diagonal
                            if i == j:
                                hierarchy = 1.0
                            else:
                                # Different hierarchy factors for different off-diagonal elements
                                if (i, j) in [(0, 1), (1, 0)]:  # 1-2 mixing
                                    hierarchy = hierarchy_factor * 0.5
                                elif (i, j) in [(0, 2), (2, 0)]:  # 1-3 mixing
                                    hierarchy = hierarchy_factor * 2.0
                                else:  # 2-3 mixing
                                    hierarchy = hierarchy_factor
                            
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
                
                experiment._construct_working_pathB_neutrino_mass = enhanced_method
            
            # Run the experiment
            result = experiment.run_task('single_law_uuf_flow')
            
            if result['status'] == 'success':
                pmns_angles = result['mixing_matrices']['pmns_angles']
                values = [pmns_angles['theta12'], pmns_angles['theta13'], pmns_angles['theta23']]
                errors = [abs(v - t) / t for v, t in zip(values, self.targets)]
                
                # Weighted error focusing on problematic angles
                weighted_error = (errors[0] * 2.0 + errors[1] * 0.5 + errors[2] * 3.0) / 5.5
                avg_error = np.mean(errors)
                
                return {
                    'success': True,
                    'angles': values,
                    'errors': errors,
                    'weighted_error': weighted_error,
                    'avg_error': avg_error,
                    'theta23_error': errors[2],  # Focus on θ₂₃
                    'theta12_error': errors[0]   # Also focus on θ₁₂
                }
            else:
                return {'success': False, 'error': result.get('error', 'Unknown')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def optimize_hierarchy_factors(self):
        """Optimize hierarchy factors specifically for θ₂₃ and θ₁₂."""
        print("🔧 OPTIMIZING HIERARCHY FACTORS FOR θ₂₃ AND θ₁₂...")
        
        # Fine-tune hierarchy factors around current best
        base_triples = self.best_config['nu_r_triples']
        base_md = self.best_config['md_scale']
        base_mr = self.best_config['mr_scale']
        
        # Test different hierarchy factor combinations
        hierarchy_factors = [1e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2]
        regularization_factors = [0.05, 0.1, 0.15, 0.2, 0.3]
        
        best_config = self.best_config.copy()
        best_error = self.best_error
        best_theta23_error = float('inf')
        
        total_tests = len(hierarchy_factors) * len(regularization_factors)
        test_count = 0
        
        for hf in hierarchy_factors:
            for rf in regularization_factors:
                test_count += 1
                print(f"  Testing {test_count}/{total_tests}: hf={hf:.0e}, rf={rf:.2f}")
                
                result = self.test_configuration(
                    nu_r_triples=base_triples,
                    md_scale=base_md,
                    mr_scale=base_mr,
                    hierarchy_factor=hf,
                    regularization_factor=rf
                )
                
                if result['success']:
                    # Track optimization history
                    self.optimization_history.append({
                        'config': {'hierarchy_factor': hf, 'regularization_factor': rf},
                        'errors': result['errors'],
                        'avg_error': result['avg_error'],
                        'theta23_error': result['theta23_error']
                    })
                    
                    # Prioritize θ₂₃ improvement
                    if result['theta23_error'] < best_theta23_error:
                        best_theta23_error = result['theta23_error']
                        best_config.update({'hierarchy_factor': hf, 'regularization_factor': rf})
                        print(f"    🎯 NEW BEST θ₂₃: {result['theta23_error']*100:.1f}% error")
                        print(f"      θ₁₂: {result['angles'][0]:.2f}° (error: {result['errors'][0]*100:.1f}%)")
                        print(f"      θ₁₃: {result['angles'][1]:.2f}° (error: {result['errors'][1]*100:.1f}%)")
                        print(f"      θ₂₃: {result['angles'][2]:.2f}° (error: {result['errors'][2]*100:.1f}%)")
                        print(f"      Average: {result['avg_error']*100:.1f}%")
                    
                    # Also track overall improvement
                    if result['avg_error'] < best_error:
                        best_error = result['avg_error']
        
        print(f"\n🏆 BEST HIERARCHY CONFIGURATION:")
        print(f"   hierarchy_factor: {best_config['hierarchy_factor']}")
        print(f"   regularization_factor: {best_config['regularization_factor']}")
        print(f"   θ₂₃ error: {best_theta23_error*100:.1f}%")
        print(f"   Average error: {best_error*100:.1f}%")
        
        return best_config, best_error
    
    def optimize_alternative_triples(self, base_config):
        """Test alternative neutrino triple combinations."""
        print("\n🔧 TESTING ALTERNATIVE NEUTRINO TRIPLE COMBINATIONS...")
        
        # Current best: [(2, 5, 5), (7, 11, 13), (17, 19, 23)]
        base_triples = base_config['nu_r_triples']
        
        # Generate alternative combinations focusing on θ₂₃
        alternative_combinations = [
            # Focus on different patterns that might affect θ₂₃
            [(1, 3, 7), (7, 11, 13), (17, 19, 23)],      # Smaller first triple
            [(3, 7, 11), (7, 11, 13), (17, 19, 23)],     # Different first triple
            [(2, 5, 5), (5, 7, 11), (17, 19, 23)],       # Different second triple
            [(2, 5, 5), (7, 11, 13), (13, 17, 19)],      # Different third triple
            [(2, 3, 7), (5, 7, 11), (13, 17, 19)],       # All different
            [(1, 2, 3), (4, 5, 6), (7, 8, 9)],           # Simple progression
            [(2, 3, 5), (7, 11, 13), (17, 19, 23)],      # Original balanced
            [(1, 4, 7), (2, 5, 8), (3, 6, 9)],           # Different pattern
        ]
        
        best_config = base_config.copy()
        best_error = float('inf')
        
        for i, triples in enumerate(alternative_combinations):
            print(f"  Testing alternative {i+1}/{len(alternative_combinations)}: {triples}")
            
            result = self.test_configuration(
                nu_r_triples=triples,
                md_scale=base_config['md_scale'],
                mr_scale=base_config['mr_scale'],
                hierarchy_factor=base_config['hierarchy_factor'],
                regularization_factor=base_config.get('regularization_factor', 0.1)
            )
            
            if result['success'] and result['avg_error'] < best_error:
                best_error = result['avg_error']
                best_config['nu_r_triples'] = triples
                print(f"    🎯 NEW BEST: {result['avg_error']*100:.1f}% error")
                print(f"      θ₁₂: {result['angles'][0]:.2f}° (error: {result['errors'][0]*100:.1f}%)")
                print(f"      θ₁₃: {result['angles'][1]:.2f}° (error: {result['errors'][1]*100:.1f}%)")
                print(f"      θ₂₃: {result['angles'][2]:.2f}° (error: {result['errors'][2]*100:.1f}%)")
        
        print(f"\n🏆 BEST ALTERNATIVE TRIPLE CONFIGURATION:")
        print(f"   ν_R triples: {best_config['nu_r_triples']}")
        print(f"   Average error: {best_error*100:.1f}%")
        
        return best_config, best_error
    
    def run_advanced_optimization(self):
        """Run the complete advanced optimization process."""
        print("🎯 ADVANCED PMNS OPTIMIZATION: Targeting θ₂₃ and θ₁₂")
        print("=" * 60)
        print(f"Current status: θ₁₃ EXCELLENT (3.3%), θ₁₂ GOOD (13.0%), θ₂₃ NEEDS WORK (62.2%)")
        print(f"Target: <5% average error")
        print()
        
        # Step 1: Optimize hierarchy factors
        best_config, best_error = self.optimize_hierarchy_factors()
        
        # Step 2: Test alternative triple combinations
        best_config, final_error = self.optimize_alternative_triples(best_config)
        
        print(f"\n🎉 ADVANCED OPTIMIZATION RESULTS:")
        print(f"   Starting error: 26.2%")
        print(f"   Final error: {final_error*100:.1f}%")
        improvement = (0.262 - final_error) / 0.262 * 100
        print(f"   Improvement: {improvement:.1f}%")
        
        if final_error < 0.05:
            print("   🏆 TARGET ACHIEVED: <5% error!")
        elif final_error < 0.1:
            print("   ✅ EXCELLENT: <10% error!")
        elif final_error < 0.15:
            print("   ✅ VERY GOOD: <15% error!")
        elif final_error < 0.2:
            print("   ✅ GOOD: <20% error!")
        
        # Final test with best configuration
        print(f"\n🧪 FINAL CONFIGURATION TEST:")
        final_result = self.test_configuration(**best_config)
        if final_result['success']:
            print(f"   θ₁₂: {final_result['angles'][0]:.2f}° (error: {final_result['errors'][0]*100:.1f}%)")
            print(f"   θ₁₃: {final_result['angles'][1]:.2f}° (error: {final_result['errors'][1]*100:.1f}%)")
            print(f"   θ₂₃: {final_result['angles'][2]:.2f}° (error: {final_result['errors'][2]*100:.1f}%)")
            print(f"   Average: {final_result['avg_error']*100:.1f}%")
        
        return best_config, final_error

if __name__ == "__main__":
    optimizer = AdvancedPMNSOptimizer()
    result = optimizer.run_advanced_optimization()
