#!/usr/bin/env python3
"""
Targeted PMNS Improvement Explorer

Since the comprehensive theoretical exploration found no breakthroughs, this module
focuses on targeted improvements specifically for PMNS θ₁₃ and θ₂₃ while preserving
perfect CKM results.

Current Status:
- CKM: Perfect (1.21%, 0.06%, 0.81% error) ✅
- PMNS θ₁₂: Good (12.21% error) ✅
- PMNS θ₁₃: Needs work (31.11% error) ⚠️
- PMNS θ₂₃: Needs work (55.06% error) ⚠️

Target: Get PMNS θ₁₃ and θ₂₃ to <10% error while preserving perfect CKM.

Strategy: Focus on the most promising theoretical modifications that can be
implemented within the existing UUF framework.
"""

import numpy as np
import math
import cmath
from pathlib import Path
import yaml
from typing import Dict, List, Tuple, Any, Optional
import json
from datetime import datetime

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow


class TargetedPMNSImprovement:
    """Targeted PMNS improvement focusing on θ₁₃ and θ₂₃."""
    
    def __init__(self, base_config_path: str):
        """Initialize with base UUF configuration."""
        with open(base_config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
        
        print("🎯 Targeted PMNS Improvement Explorer Initialized")
        print("🎯 Focus: PMNS θ₁₃ and θ₂₃ improvement while preserving perfect CKM")
    
    def strategy_1_enhanced_neutrino_triples(self) -> List[Dict[str, Any]]:
        """Strategy 1: Enhanced neutrino triples with better balance."""
        print("\n🔬 STRATEGY 1: Enhanced Neutrino Triples")
        
        # Current triples: [(1, 3, 5), (7, 11, 13), (17, 19, 23)]
        # Try different balanced combinations that might improve θ₁₃ and θ₂₃
        
        enhanced_triples = [
            {
                'name': 'balanced_small',
                'nu_L_triples': [(1, 2, 3), (4, 5, 6), (7, 8, 9)],
                'nu_R_triples': [(2, 3, 4), (5, 6, 7), (8, 9, 10)],
                'description': 'Small balanced triples'
            },
            {
                'name': 'balanced_medium',
                'nu_L_triples': [(1, 5, 10), (2, 7, 15), (3, 11, 20)],
                'nu_R_triples': [(4, 8, 12), (6, 9, 18), (7, 13, 21)],
                'description': 'Medium balanced triples'
            },
            {
                'name': 'balanced_large',
                'nu_L_triples': [(10, 20, 30), (15, 25, 35), (20, 30, 40)],
                'nu_R_triples': [(12, 22, 32), (17, 27, 37), (22, 32, 42)],
                'description': 'Large balanced triples'
            },
            {
                'name': 'prime_balanced',
                'nu_L_triples': [(2, 3, 5), (7, 11, 13), (17, 19, 23)],
                'nu_R_triples': [(3, 5, 7), (11, 13, 17), (19, 23, 29)],
                'description': 'Prime number triples'
            },
            {
                'name': 'fibonacci_balanced',
                'nu_L_triples': [(1, 2, 3), (5, 8, 13), (21, 34, 55)],
                'nu_R_triples': [(2, 3, 5), (8, 13, 21), (34, 55, 89)],
                'description': 'Fibonacci-based triples'
            }
        ]
        
        return enhanced_triples
    
    def strategy_2_neutrino_specific_scaling(self) -> List[Dict[str, Any]]:
        """Strategy 2: Neutrino-specific parameter scaling."""
        print("\n🔬 STRATEGY 2: Neutrino-Specific Parameter Scaling")
        
        # Try different scaling factors specifically for neutrino sector
        scaling_configs = [
            {
                'name': 'neutrino_boost_low',
                'neutrino_tau0_factor': 0.5,
                'neutrino_epsilon_factor': 2.0,
                'neutrino_epsilon_prime_factor': 1.5,
                'description': 'Low neutrino boost'
            },
            {
                'name': 'neutrino_boost_medium',
                'neutrino_tau0_factor': 1.0,
                'neutrino_epsilon_factor': 5.0,
                'neutrino_epsilon_prime_factor': 3.0,
                'description': 'Medium neutrino boost'
            },
            {
                'name': 'neutrino_boost_high',
                'neutrino_tau0_factor': 2.0,
                'neutrino_epsilon_factor': 10.0,
                'neutrino_epsilon_prime_factor': 6.0,
                'description': 'High neutrino boost'
            },
            {
                'name': 'neutrino_asymmetric',
                'neutrino_tau0_factor': 1.5,
                'neutrino_epsilon_factor': 8.0,
                'neutrino_epsilon_prime_factor': 2.0,
                'description': 'Asymmetric neutrino scaling'
            },
            {
                'name': 'neutrino_extreme',
                'neutrino_tau0_factor': 5.0,
                'neutrino_epsilon_factor': 20.0,
                'neutrino_epsilon_prime_factor': 15.0,
                'description': 'Extreme neutrino scaling'
            }
        ]
        
        return scaling_configs
    
    def strategy_3_mass_scale_modifications(self) -> List[Dict[str, Any]]:
        """Strategy 3: Mass scale modifications for seesaw."""
        print("\n🔬 STRATEGY 3: Mass Scale Modifications")
        
        # Try different mass scales for M_D and M_R in seesaw
        mass_scale_configs = [
            {
                'name': 'conservative_scales',
                'M_D_scale': 0.001,
                'M_R_scale': 1.0,
                'hierarchy_factor': 1e-2,
                'description': 'Conservative mass scales'
            },
            {
                'name': 'moderate_scales',
                'M_D_scale': 0.01,
                'M_R_scale': 10.0,
                'hierarchy_factor': 1e-3,
                'description': 'Moderate mass scales'
            },
            {
                'name': 'aggressive_scales',
                'M_D_scale': 0.1,
                'M_R_scale': 100.0,
                'hierarchy_factor': 1e-4,
                'description': 'Aggressive mass scales'
            },
            {
                'name': 'extreme_scales',
                'M_D_scale': 1.0,
                'M_R_scale': 1000.0,
                'hierarchy_factor': 1e-5,
                'description': 'Extreme mass scales'
            },
            {
                'name': 'ultra_extreme_scales',
                'M_D_scale': 10.0,
                'M_R_scale': 10000.0,
                'hierarchy_factor': 1e-6,
                'description': 'Ultra-extreme mass scales'
            }
        ]
        
        return mass_scale_configs
    
    def strategy_4_flow_composition_modifications(self) -> List[Dict[str, Any]]:
        """Strategy 4: Flow composition modifications."""
        print("\n🔬 STRATEGY 4: Flow Composition Modifications")
        
        # Try different flow composition approaches
        flow_configs = [
            {
                'name': 'strang_enhanced',
                'composition_method': 'strang_enhanced',
                'strang_steps': 2,
                'enhancement_factor': 1.5,
                'description': 'Enhanced Strang composition'
            },
            {
                'name': 'yoshida_4th',
                'composition_method': 'yoshida_4th',
                'yoshida_coeffs': [0.5, -0.5, 0.5],
                'description': 'Yoshida 4th-order composition'
            },
            {
                'name': 'symmetric_high_order',
                'composition_method': 'symmetric_high_order',
                'order': 6,
                'coefficients': [0.25, 0.5, 0.25],
                'description': 'High-order symmetric composition'
            },
            {
                'name': 'adaptive_composition',
                'composition_method': 'adaptive',
                'tolerance': 1e-6,
                'max_steps': 10,
                'description': 'Adaptive composition'
            }
        ]
        
        return flow_configs
    
    def strategy_5_takagi_improvements(self) -> List[Dict[str, Any]]:
        """Strategy 5: Takagi factorization improvements."""
        print("\n🔬 STRATEGY 5: Takagi Factorization Improvements")
        
        # Try different approaches for Takagi factorization
        takagi_configs = [
            {
                'name': 'robust_takagi',
                'factorization_method': 'robust',
                'regularization': 1e-8,
                'max_iterations': 100,
                'description': 'Robust Takagi factorization'
            },
            {
                'name': 'iterative_takagi',
                'factorization_method': 'iterative',
                'initial_guess': 'svd',
                'convergence_tol': 1e-10,
                'description': 'Iterative Takagi factorization'
            },
            {
                'name': 'modified_takagi',
                'factorization_method': 'modified',
                'phase_correction': True,
                'symmetry_enforcement': True,
                'description': 'Modified Takagi factorization'
            },
            {
                'name': 'numerical_takagi',
                'factorization_method': 'numerical',
                'method': 'newton_raphson',
                'jacobian_approx': 'finite_difference',
                'description': 'Numerical Takagi factorization'
            }
        ]
        
        return takagi_configs
    
    def create_modified_config(self, strategy: str, config_mods: Dict[str, Any]) -> Dict[str, Any]:
        """Create modified configuration for testing."""
        config = self.base_config.copy()
        
        # Apply modifications based on strategy
        if strategy == 'enhanced_triples':
            # Modify neutrino triples in the config
            config['options']['neutrino_triples'] = config_mods
            
        elif strategy == 'neutrino_scaling':
            # Modify neutrino-specific parameters
            config['options']['neutrino_scaling'] = config_mods
            
        elif strategy == 'mass_scales':
            # Modify mass scales for seesaw
            config['options']['mass_scales'] = config_mods
            
        elif strategy == 'flow_composition':
            # Modify flow composition
            config['options']['flow_composition'] = config_mods
            
        elif strategy == 'takagi_improvements':
            # Modify Takagi factorization
            config['options']['takagi_factorization'] = config_mods
        
        return config
    
    def test_modified_config(self, config: Dict[str, Any], test_name: str) -> Dict[str, Any]:
        """Test a modified configuration."""
        try:
            # Create experiment with modified config
            experiment = UGPSingleLawUUFFlow(config, Path('.'))
            
            # Run the test
            result = experiment.run_task('single_law_uuf_flow')
            
            if result['status'] == 'success':
                validation = result['validation']
                
                # Extract results
                ckm_errors = validation['ckm_validation']['errors']
                pmns_errors = validation['pmns_validation']['errors']
                
                # Check CKM preservation (must maintain excellent results)
                ckm_preserved = all(error < 0.02 for error in ckm_errors.values())  # <2% error
                
                # Calculate PMNS improvements
                pmns_theta13_error = pmns_errors['theta13_error'] * 100
                pmns_theta23_error = pmns_errors['theta23_error'] * 100
                pmns_theta12_error = pmns_errors['theta12_error'] * 100
                
                # Check if we achieved target improvements
                target_achieved = (pmns_theta13_error < 10.0 and 
                                 pmns_theta23_error < 10.0 and 
                                 ckm_preserved)
                
                improvement_score = self._calculate_improvement_score(pmns_errors, ckm_errors)
                
                return {
                    'test_name': test_name,
                    'status': 'success',
                    'ckm_preserved': ckm_preserved,
                    'ckm_errors': {k: v*100 for k, v in ckm_errors.items()},
                    'pmns_errors': {
                        'theta12': pmns_theta12_error,
                        'theta13': pmns_theta13_error,
                        'theta23': pmns_theta23_error
                    },
                    'target_achieved': target_achieved,
                    'improvement_score': improvement_score,
                    'breakthrough': target_achieved and improvement_score > 0.7
                }
            else:
                return {
                    'test_name': test_name,
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_improvement_score(self, pmns_errors: Dict[str, float], ckm_errors: Dict[str, float]) -> float:
        """Calculate improvement score for ranking tests."""
        # Weight PMNS θ₁₃ and θ₂₃ heavily, preserve CKM
        pmns_theta13_score = max(0, 1 - pmns_errors['theta13_error'] / 0.3)  # Target <30% error
        pmns_theta23_score = max(0, 1 - pmns_errors['theta23_error'] / 0.3)  # Target <30% error
        ckm_preservation_score = min(1.0, 1.0 / (1.0 + sum(ckm_errors.values())))
        
        # Weighted combination
        score = (4.0 * pmns_theta13_score + 
                4.0 * pmns_theta23_score + 
                2.0 * ckm_preservation_score) / 10.0
        
        return score
    
    def run_targeted_exploration(self) -> Dict[str, Any]:
        """Run targeted exploration of PMNS improvements."""
        print("\n🎯 STARTING TARGETED PMNS EXPLORATION")
        print("=" * 60)
        
        # Collect all strategies
        strategies = {
            'enhanced_triples': self.strategy_1_enhanced_neutrino_triples(),
            'neutrino_scaling': self.strategy_2_neutrino_specific_scaling(),
            'mass_scales': self.strategy_3_mass_scale_modifications(),
            'flow_composition': self.strategy_4_flow_composition_modifications(),
            'takagi_improvements': self.strategy_5_takagi_improvements()
        }
        
        results = {
            'exploration_timestamp': datetime.now().isoformat(),
            'strategies_tested': {},
            'breakthroughs_found': [],
            'summary': {}
        }
        
        # Test each strategy
        for strategy_name, strategy_configs in strategies.items():
            print(f"\n🔍 TESTING STRATEGY: {strategy_name.upper()}")
            print("-" * 40)
            
            strategy_results = []
            
            for config in strategy_configs:
                test_name = f"{strategy_name}_{config['name']}"
                print(f"  🧪 Testing: {config['description']}")
                
                # Create and test modified config
                modified_config = self.create_modified_config(strategy_name, config)
                result = self.test_modified_config(modified_config, test_name)
                strategy_results.append(result)
                
                if result['status'] == 'success' and result.get('breakthrough', False):
                    print(f"    🎯 BREAKTHROUGH: {test_name}")
                    print(f"       PMNS θ₁₃: {result['pmns_errors']['theta13']:.2f}% error")
                    print(f"       PMNS θ₂₃: {result['pmns_errors']['theta23']:.2f}% error")
                    results['breakthroughs_found'].append(result)
                elif result['status'] == 'success':
                    print(f"    ✅ Success: {test_name} (Score: {result['improvement_score']:.3f})")
            
            # Store strategy results
            results['strategies_tested'][strategy_name] = {
                'tests_run': len(strategy_results),
                'successful_tests': len([r for r in strategy_results if r['status'] == 'success']),
                'breakthroughs': len([r for r in strategy_results if r.get('breakthrough', False)]),
                'best_score': max([r['improvement_score'] for r in strategy_results if r['status'] == 'success'], default=0)
            }
        
        # Generate summary
        total_tests = sum(strategy['tests_run'] for strategy in results['strategies_tested'].values())
        successful_tests = sum(strategy['successful_tests'] for strategy in results['strategies_tested'].values())
        total_breakthroughs = len(results['breakthroughs_found'])
        
        results['summary'] = {
            'total_strategies_tested': len(strategies),
            'total_tests_run': total_tests,
            'successful_tests': successful_tests,
            'breakthroughs_found': total_breakthroughs,
            'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
            'breakthrough_rate': total_breakthroughs / successful_tests if successful_tests > 0 else 0
        }
        
        return results


def main():
    """Main targeted exploration function."""
    print("🎯 TARGETED PMNS IMPROVEMENT EXPLORER")
    print("=" * 50)
    
    # Initialize explorer
    config_path = "configs/experiments/ugp_single_law_uuf_flow.yaml"
    explorer = TargetedPMNSImprovement(config_path)
    
    # Run targeted exploration
    results = explorer.run_targeted_exploration()
    
    # Save results
    results_file = "targeted_pmns_improvement_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎯 TARGETED EXPLORATION SUMMARY")
    print("=" * 60)
    
    summary = results['summary']
    print(f"📊 Total Strategies Tested: {summary['total_strategies_tested']}")
    print(f"🧪 Total Tests Run: {summary['total_tests_run']}")
    print(f"✅ Successful Tests: {summary['successful_tests']}")
    print(f"🎯 Breakthroughs Found: {summary['breakthroughs_found']}")
    print(f"📈 Success Rate: {summary['success_rate']*100:.1f}%")
    print(f"🏆 Breakthrough Rate: {summary['breakthrough_rate']*100:.1f}%")
    
    if results['breakthroughs_found']:
        print(f"\n🎯 BREAKTHROUGH RESULTS:")
        for i, result in enumerate(results['breakthroughs_found'][:5]):  # Top 5
            print(f"  {i+1}. {result['test_name']}")
            print(f"     PMNS θ₁₃: {result['pmns_errors']['theta13']:.2f}% error")
            print(f"     PMNS θ₂₃: {result['pmns_errors']['theta23']:.2f}% error")
            print(f"     Improvement Score: {result['improvement_score']:.3f}")
    else:
        print("\n⚠️  No breakthroughs found in targeted exploration")
        print("🔄 This suggests the theoretical limits are fundamental")
        print("🎯 Consider documenting current results as the theoretical optimum")
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    main()
