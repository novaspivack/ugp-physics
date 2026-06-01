#!/usr/bin/env python3
"""
PMNS Optimization Tool: Systematic optimization to achieve <5% error
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

class PMNSOptimizer:
    def __init__(self):
        # Load configuration
        with open('configs/experiments/ugp_single_law_uuf_flow.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # PDG targets
        self.targets = [33.44, 8.57, 49.0]  # θ₁₂, θ₁₃, θ₂₃
        
        # Best results tracking
        self.best_error = float('inf')
        self.best_config = None
        self.best_results = None
        
    def test_configuration(self, md_scale=100, mr_scale=1e14, hierarchy_factor=1e-3, 
                          nu_r_triples=None, optimization_weights=None):
        """Test a specific configuration and return PMNS errors."""
        try:
            # Create experiment instance
            experiment = UGPSingleLawUUFFlow(self.config, Path('.'))
            
            # Override neutrino triples if provided
            if nu_r_triples is not None:
                # Temporarily modify the triples in the method
                original_method = experiment._construct_working_pathB_neutrino_mass
                
                def modified_method():
                    # Load left-handed neutrino triples (exact from working Path B)
                    nu_L_triples = [
                        experiment.canonical_triples[("nu_e", "nu", 1)],
                        experiment.canonical_triples[("nu_mu", "nu", 2)],
                        experiment.canonical_triples[("nu_tau", "nu", 3)]
                    ]
                    
                    # Use provided right-handed triples
                    gens = [1, 2, 3]
                    
                    # Extract irrep features for ν_L and ν_R with enhanced geometry
                    nu_L_features = [experiment._extract_enhanced_irrep_features(a, b, c, g, "nu") 
                                    for (a, b, c), g in zip(nu_L_triples, gens)]
                    nu_R_features = [experiment._extract_enhanced_irrep_features(a, b, c, g, "nu_R") 
                                    for (a, b, c), g in zip(nu_r_triples, gens)]
                    
                    # Construct enhanced Dirac mass matrix M_D with custom scale
                    M_D = np.zeros((3, 3), dtype=complex)
                    for i, feat_L in enumerate(nu_L_features):
                        for j, feat_R in enumerate(nu_R_features):
                            s_L, e_L, delta_L = feat_L
                            s_R, e_R, delta_R = feat_R
                            
                            overlap = (s_L * s_R + 
                                      e_L[0] * e_R[0] + e_L[1] * e_R[1] + 
                                      delta_L * delta_R * experiment.k_L2)
                            
                            M_D[i, j] = overlap * md_scale
                    
                    # Construct enhanced Majorana mass matrix M_R with custom scale
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
                    
                    # Ensure M_R is symmetric and add diagonal enhancement
                    M_R = 0.5 * (M_R + M_R.T)
                    M_R += np.eye(3) * np.trace(M_R) * 0.1
                    
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
                
                experiment._construct_working_pathB_neutrino_mass = modified_method
            
            # Run the experiment
            result = experiment.run_task('single_law_uuf_flow')
            
            if result['status'] == 'success':
                pmns_angles = result['mixing_matrices']['pmns_angles']
                values = [pmns_angles['theta12'], pmns_angles['theta13'], pmns_angles['theta23']]
                errors = [abs(v - t) / t for v, t in zip(values, self.targets)]
                
                # Calculate weighted error if weights provided
                if optimization_weights is not None:
                    weighted_error = sum(w * e for w, e in zip(optimization_weights, errors))
                else:
                    weighted_error = np.mean(errors)
                
                return {
                    'success': True,
                    'angles': values,
                    'errors': errors,
                    'weighted_error': weighted_error,
                    'avg_error': np.mean(errors)
                }
            else:
                return {'success': False, 'error': result.get('error', 'Unknown')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def optimize_mass_scales(self):
        """Optimize mass scales systematically."""
        print("🔧 OPTIMIZING MASS SCALES...")
        
        # Test different mass scale combinations
        md_scales = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]
        mr_scales = [1e12, 1e13, 1e14, 1e15, 1e16]
        hierarchy_factors = [1e-4, 1e-3, 1e-2, 1e-1]
        
        best_config = None
        best_error = float('inf')
        
        total_tests = len(md_scales) * len(mr_scales) * len(hierarchy_factors)
        test_count = 0
        
        for md in md_scales:
            for mr in mr_scales:
                for hf in hierarchy_factors:
                    test_count += 1
                    print(f"  Testing {test_count}/{total_tests}: M_D={md}, M_R={mr:.0e}, hf={hf:.0e}")
                    
                    result = self.test_configuration(md_scale=md, mr_scale=mr, hierarchy_factor=hf)
                    
                    if result['success'] and result['avg_error'] < best_error:
                        best_error = result['avg_error']
                        best_config = {'md_scale': md, 'mr_scale': mr, 'hierarchy_factor': hf}
                        print(f"    🎯 NEW BEST: {best_error*100:.1f}% error")
                        print(f"      θ₁₂: {result['angles'][0]:.2f}° (error: {result['errors'][0]*100:.1f}%)")
                        print(f"      θ₁₃: {result['angles'][1]:.2f}° (error: {result['errors'][1]*100:.1f}%)")
                        print(f"      θ₂₃: {result['angles'][2]:.2f}° (error: {result['errors'][2]*100:.1f}%)")
        
        print(f"\n🏆 BEST MASS SCALE CONFIGURATION:")
        if best_config:
            print(f"   M_D_scale: {best_config['md_scale']}")
            print(f"   M_R_scale: {best_config['mr_scale']}")
            print(f"   hierarchy_factor: {best_config['hierarchy_factor']}")
            print(f"   Average error: {best_error*100:.1f}%")
            
            if best_error < 0.05:
                print("   🎉 TARGET ACHIEVED: <5% error!")
            elif best_error < 0.1:
                print("   ✅ EXCELLENT: <10% error!")
            elif best_error < 0.2:
                print("   ✅ GOOD: <20% error!")
        
        return best_config, best_error
    
    def optimize_neutrino_triples(self, base_config):
        """Optimize neutrino triples around the best mass scale configuration."""
        print("\n🔧 OPTIMIZING NEUTRINO TRIPLES...")
        
        # Start with balanced triples and try variations
        base_triples = [(2, 3, 5), (7, 11, 13), (17, 19, 23)]
        
        # Generate variations around base triples
        variations = []
        for i, (a, b, c) in enumerate(base_triples):
            # Try small variations
            for da in [-2, -1, 0, 1, 2]:
                for db in [-2, -1, 0, 1, 2]:
                    for dc in [-2, -1, 0, 1, 2]:
                        new_a, new_b, new_c = a + da, b + db, c + dc
                        if new_a > 0 and new_b > 0 and new_c > 0:
                            new_triples = base_triples.copy()
                            new_triples[i] = (new_a, new_b, new_c)
                            variations.append(new_triples)
        
        # Limit to reasonable number of tests
        variations = variations[:50]  # Test top 50 variations
        
        best_config = None
        best_error = float('inf')
        
        for i, triples in enumerate(variations):
            print(f"  Testing triple variation {i+1}/{len(variations)}: {triples}")
            
            result = self.test_configuration(
                md_scale=base_config['md_scale'],
                mr_scale=base_config['mr_scale'],
                hierarchy_factor=base_config['hierarchy_factor'],
                nu_r_triples=triples
            )
            
            if result['success'] and result['avg_error'] < best_error:
                best_error = result['avg_error']
                best_config = {**base_config, 'nu_r_triples': triples}
                print(f"    🎯 NEW BEST: {best_error*100:.1f}% error")
                print(f"      θ₁₂: {result['angles'][0]:.2f}° (error: {result['errors'][0]*100:.1f}%)")
                print(f"      θ₁₃: {result['angles'][1]:.2f}° (error: {result['errors'][1]*100:.1f}%)")
                print(f"      θ₂₃: {result['angles'][2]:.2f}° (error: {result['errors'][2]*100:.1f}%)")
        
        print(f"\n🏆 BEST NEUTRINO TRIPLE CONFIGURATION:")
        if best_config:
            print(f"   ν_R triples: {best_config['nu_r_triples']}")
            print(f"   Average error: {best_error*100:.1f}%")
        
        return best_config, best_error
    
    def run_full_optimization(self):
        """Run the complete optimization process."""
        print("🎯 PMNS OPTIMIZATION: From 40.2% to <5% Error")
        print("=" * 60)
        
        # Step 1: Optimize mass scales
        best_mass_config, mass_error = self.optimize_mass_scales()
        
        if not best_mass_config:
            print("❌ Mass scale optimization failed!")
            return None
        
        # Step 2: Optimize neutrino triples
        best_config, final_error = self.optimize_neutrino_triples(best_mass_config)
        
        print(f"\n🎉 FINAL OPTIMIZATION RESULTS:")
        print(f"   Starting error: 40.2%")
        print(f"   Final error: {final_error*100:.1f}%")
        print(f"   Improvement: {(0.402 - final_error) / 0.402 * 100:.1f}%")
        
        if final_error < 0.05:
            print("   🏆 TARGET ACHIEVED: <5% error!")
        elif final_error < 0.1:
            print("   ✅ EXCELLENT: <10% error!")
        elif final_error < 0.2:
            print("   ✅ GOOD: <20% error!")
        
        return best_config, final_error

if __name__ == "__main__":
    optimizer = PMNSOptimizer()
    result = optimizer.run_full_optimization()
