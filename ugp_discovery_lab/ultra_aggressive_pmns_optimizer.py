#!/usr/bin/env python3
"""
Ultra-Aggressive PMNS Optimizer: Extreme optimization for θ₂₃ breakthrough
Current status: θ₁₃ EXCELLENT (3.5%), θ₁₂ GOOD (13.0%), θ₂₃ NEEDS WORK (62.2%)
Target: <5% average error - FOCUS ON θ₂₃ BREAKTHROUGH
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

class UltraAggressivePMNSOptimizer:
    def __init__(self):
        # Load configuration
        with open('configs/experiments/ugp_single_law_uuf_flow.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # PDG targets
        self.targets = [33.44, 8.57, 49.0]  # θ₁₂, θ₁₃, θ₂₃
        
        # Current best results
        self.best_error = 0.262  # 26.2% average
        self.best_config = {
            'nu_r_triples': [(2, 5, 5), (7, 11, 13), (13, 17, 19)],
            'md_scale': 100,
            'mr_scale': 1e14,
            'hierarchy_factor': 0.02,
            'regularization_factor': 0.3
        }
        
        # Extreme parameter ranges for breakthrough
        self.extreme_ranges = {
            'md_scales': [0.01, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 5000],
            'mr_scales': [1e10, 1e11, 1e12, 1e13, 1e14, 1e15, 1e16, 1e17, 1e18],
            'hierarchy_factors': [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 0.5, 1.0, 2.0, 5.0, 10.0],
            'regularization_factors': [0.001, 0.01, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        }
        
    def test_configuration(self, nu_r_triples=None, md_scale=100, mr_scale=1e14, 
                          hierarchy_factor=1e-3, regularization_factor=0.1):
        """Test a specific configuration with enhanced parameters."""
        try:
            # Create experiment instance
            experiment = UGPSingleLawUUFFlow(self.config, Path('.'))
            
            # Override neutrino triples if provided
            if nu_r_triples is not None:
                original_method = experiment._construct_working_pathB_neutrino_mass
                
                def ultra_enhanced_method():
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
                    
                    # ULTRA-ENHANCED Dirac mass matrix construction
                    M_D = np.zeros((3, 3), dtype=complex)
                    for i, feat_L in enumerate(nu_L_features):
                        for j, feat_R in enumerate(nu_R_features):
                            s_L, e_L, delta_L = feat_L
                            s_R, e_R, delta_R = feat_R
                            
                            # Enhanced overlap with θ₂₃-specific weighting
                            base_overlap = (s_L * s_R + 
                                          e_L[0] * e_R[0] + e_L[1] * e_R[1] + 
                                          delta_L * delta_R * experiment.k_L2)
                            
                            # θ₂₃-specific enhancement: boost (2,3) matrix elements
                            if i == 1 and j == 2:  # (2,3) element
                                enhancement = 1.5  # Boost θ₂₃ mixing
                            elif i == 2 and j == 1:  # (3,2) element
                                enhancement = 1.5  # Boost θ₂₃ mixing
                            else:
                                enhancement = 1.0
                            
                            M_D[i, j] = base_overlap * md_scale * enhancement
                    
                    # ULTRA-ENHANCED Majorana mass matrix with θ₂₃ focus
                    M_R = np.zeros((3, 3), dtype=complex)
                    for i, feat_i in enumerate(nu_R_features):
                        for j, feat_j in enumerate(nu_R_features):
                            s_i, e_i, delta_i = feat_i
                            s_j, e_j, delta_j = feat_j
                            
                            gram = (s_i * s_j + 
                                   e_i[0] * e_j[0] + e_i[1] * e_j[1] + 
                                   delta_i * delta_j * experiment.k_L2)
                            
                            # ULTRA-AGGRESSIVE hierarchy for θ₂₃ optimization
                            if i == j:
                                hierarchy = 1.0
                            else:
                                # θ₂₃-specific hierarchy tuning
                                if (i, j) == (1, 2) or (i, j) == (2, 1):  # 2-3 mixing
                                    hierarchy = hierarchy_factor * 0.1  # Enhance 2-3 mixing
                                elif (i, j) in [(0, 1), (1, 0)]:  # 1-2 mixing
                                    hierarchy = hierarchy_factor * 0.5
                                elif (i, j) in [(0, 2), (2, 0)]:  # 1-3 mixing
                                    hierarchy = hierarchy_factor * 2.0
                                else:
                                    hierarchy = hierarchy_factor
                            
                            M_R[i, j] = gram * mr_scale * hierarchy
                    
                    # Ultra-enhanced regularization
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
                
                experiment._construct_working_pathB_neutrino_mass = ultra_enhanced_method
            
            # Run the experiment
            result = experiment.run_task('single_law_uuf_flow')
            
            if result['status'] == 'success':
                pmns_angles = result['mixing_matrices']['pmns_angles']
                values = [pmns_angles['theta12'], pmns_angles['theta13'], pmns_angles['theta23']]
                errors = [abs(v - t) / t for v, t in zip(values, self.targets)]
                
                # ULTRA-AGGRESSIVE weighting: Focus heavily on θ₂₃
                weighted_error = (errors[0] * 1.0 + errors[1] * 0.5 + errors[2] * 10.0) / 11.5
                avg_error = np.mean(errors)
                
                return {
                    'success': True,
                    'angles': values,
                    'errors': errors,
                    'weighted_error': weighted_error,
                    'avg_error': avg_error,
                    'theta23_error': errors[2],  # Primary focus
                    'theta12_error': errors[0],
                    'theta13_error': errors[1]
                }
            else:
                return {'success': False, 'error': result.get('error', 'Unknown')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def ultra_aggressive_optimization(self):
        """Ultra-aggressive optimization focusing on θ₂₃ breakthrough."""
        print("🚀 ULTRA-AGGRESSIVE θ₂₃ OPTIMIZATION")
        print("=" * 60)
        print("Current status: θ₁₃ EXCELLENT (3.5%), θ₁₂ GOOD (13.0%), θ₂₃ NEEDS WORK (62.2%)")
        print("Target: θ₂₃ BREAKTHROUGH to <20% error")
        print()
        
        base_triples = self.best_config['nu_r_triples']
        
        # ULTRA-AGGRESSIVE parameter combinations
        md_scales = self.extreme_ranges['md_scales']
        mr_scales = self.extreme_ranges['mr_scales']
        hierarchy_factors = self.extreme_ranges['hierarchy_factors']
        regularization_factors = self.extreme_ranges['regularization_factors']
        
        best_config = self.best_config.copy()
        best_theta23_error = float('inf')
        best_overall_error = float('inf')
        
        total_tests = len(md_scales) * len(mr_scales) * len(hierarchy_factors) * len(regularization_factors)
        print(f"🔥 TESTING {total_tests} ULTRA-AGGRESSIVE COMBINATIONS...")
        print("Focus: θ₂₃ breakthrough with extreme parameter ranges")
        print()
        
        test_count = 0
        breakthrough_count = 0
        
        for md in md_scales:
            for mr in mr_scales:
                for hf in hierarchy_factors:
                    for rf in regularization_factors:
                        test_count += 1
                        
                        if test_count % 100 == 0:
                            print(f"  Progress: {test_count}/{total_tests} ({test_count/total_tests*100:.1f}%)")
                            print(f"  Best θ₂₃ so far: {best_theta23_error*100:.1f}% error")
                        
                        result = self.test_configuration(
                            nu_r_triples=base_triples,
                            md_scale=md,
                            mr_scale=mr,
                            hierarchy_factor=hf,
                            regularization_factor=rf
                        )
                        
                        if result['success']:
                            # Track θ₂₃ breakthroughs
                            if result['theta23_error'] < 0.2:  # <20% error
                                breakthrough_count += 1
                                print(f"    🎯 θ₂₃ BREAKTHROUGH #{breakthrough_count}: {result['theta23_error']*100:.1f}% error")
                                print(f"      θ₁₂: {result['angles'][0]:.2f}° (error: {result['errors'][0]*100:.1f}%)")
                                print(f"      θ₁₃: {result['angles'][1]:.2f}° (error: {result['errors'][1]*100:.1f}%)")
                                print(f"      θ₂₃: {result['angles'][2]:.2f}° (error: {result['errors'][2]*100:.1f}%)")
                                print(f"      Average: {result['avg_error']*100:.1f}%")
                                print(f"      Config: MD={md}, MR={mr:.0e}, HF={hf:.0e}, RF={rf:.3f}")
                                print()
                            
                            # Track best θ₂₃
                            if result['theta23_error'] < best_theta23_error:
                                best_theta23_error = result['theta23_error']
                                best_config.update({
                                    'md_scale': md,
                                    'mr_scale': mr,
                                    'hierarchy_factor': hf,
                                    'regularization_factor': rf
                                })
                            
                            # Track best overall
                            if result['avg_error'] < best_overall_error:
                                best_overall_error = result['avg_error']
        
        print(f"\n🎉 ULTRA-AGGRESSIVE OPTIMIZATION COMPLETE!")
        print(f"   Total tests: {test_count}")
        print(f"   θ₂₃ breakthroughs: {breakthrough_count}")
        print(f"   Best θ₂₃ error: {best_theta23_error*100:.1f}%")
        print(f"   Best overall error: {best_overall_error*100:.1f}%")
        
        if breakthrough_count > 0:
            print(f"\n🏆 θ₂₃ BREAKTHROUGH ACHIEVED!")
            print(f"   Found {breakthrough_count} configurations with θ₂₃ <20% error")
            
            # Test the best configuration
            print(f"\n🧪 TESTING BEST CONFIGURATION:")
            best_result = self.test_configuration(**best_config)
            if best_result['success']:
                print(f"   θ₁₂: {best_result['angles'][0]:.2f}° (error: {best_result['errors'][0]*100:.1f}%)")
                print(f"   θ₁₃: {best_result['angles'][1]:.2f}° (error: {best_result['errors'][1]*100:.1f}%)")
                print(f"   θ₂₃: {best_result['angles'][2]:.2f}° (error: {best_result['errors'][2]*100:.1f}%)")
                print(f"   Average: {best_result['avg_error']*100:.1f}%")
                
                if best_result['avg_error'] < 0.05:
                    print("   🎉 TARGET ACHIEVED: <5% average error!")
                elif best_result['avg_error'] < 0.1:
                    print("   ✅ EXCELLENT: <10% average error!")
                elif best_result['avg_error'] < 0.15:
                    print("   ✅ VERY GOOD: <15% average error!")
                elif best_result['avg_error'] < 0.2:
                    print("   ✅ GOOD: <20% average error!")
        
        return best_config, best_theta23_error, breakthrough_count

if __name__ == "__main__":
    optimizer = UltraAggressivePMNSOptimizer()
    result = optimizer.ultra_aggressive_optimization()
