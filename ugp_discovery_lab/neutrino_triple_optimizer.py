#!/usr/bin/env python3
"""
Neutrino Triple Optimizer - Systematic Exploration

This script systematically explores neutrino triple variations to find
even better configurations for PMNS accuracy.

The breakthrough from [(2,5,5), (7,11,13), (17,19,23)] to [(1,4,9), (16,25,36), (49,64,81)]
achieved 7.85% improvement (32.80% → 24.95%). Let's find even better!
"""

import sys
import os
import json
import yaml
import numpy as np
import copy
from pathlib import Path
from datetime import datetime
from itertools import combinations, permutations, product
from typing import Dict, List, Tuple, Any

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow


class NeutrinoTripleOptimizer:
    """Systematic optimizer for neutrino triple configurations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.baseline_ckm_error = 0.69
        self.baseline_pmns_error = 32.80
        self.current_pmns_error = 24.95  # After breakthrough
        
    def generate_triple_variations(self):
        """Generate systematic variations of neutrino triples."""
        
        variations = []
        
        # 1. Mathematical progressions
        print("🔢 Generating mathematical progression triples...")
        
        # Arithmetic progressions: (a, a+d, a+2d)
        for a in range(1, 20):
            for d in range(1, 10):
                triple1 = (a, a+d, a+2*d)
                for b in range(a+3*d, min(a+6*d, 50)):
                    triple2 = (b, b+d, b+2*d)
                    for c in range(b+3*d, min(b+6*d, 100)):
                        triple3 = (c, c+d, c+2*d)
                        variations.append([triple1, triple2, triple3])
        
        # Geometric progressions: (a, ar, ar²)
        for a in range(1, 15):
            for r in range(2, 6):
                if a*r*r < 100:
                    triple1 = (a, a*r, a*r*r)
                    for b in range(a*r*r+1, min(a*r*r+20, 50)):
                        if b*r*r < 100:
                            triple2 = (b, b*r, b*r*r)
                            for c in range(b*r*r+1, min(b*r*r+20, 100)):
                                if c*r*r < 100:
                                    triple3 = (c, c*r, c*r*r)
                                    variations.append([triple1, triple2, triple3])
        
        # 2. Number theory patterns
        print("🔢 Generating number theory patterns...")
        
        # Prime-based patterns
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        for i in range(len(primes)-2):
            for j in range(i+1, len(primes)-1):
                for k in range(j+1, len(primes)):
                    variations.append([(primes[i], primes[i+1], primes[i+2]), 
                                      (primes[j], primes[j+1], primes[j+2]), 
                                      (primes[k], primes[k+1], primes[k+2])])
        
        # Fibonacci-based
        fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        for i in range(len(fib)-2):
            for j in range(i+1, len(fib)-2):
                for k in range(j+1, len(fib)-2):
                    variations.append([(fib[i], fib[i+1], fib[i+2]), 
                                      (fib[j], fib[j+1], fib[j+2]), 
                                      (fib[k], fib[k+1], fib[k+2])])
        
        # 3. Power-based patterns (building on our breakthrough)
        print("🔢 Generating power-based patterns...")
        
        # Cubes: (a³, b³, c³)
        for a in range(1, 5):
            for b in range(a+1, 6):
                for c in range(b+1, 7):
                    triple1 = (a**3, b**3, c**3)
                    for d in range(c+1, 8):
                        for e in range(d+1, 9):
                            for f in range(e+1, 10):
                                triple2 = (d**3, e**3, f**3)
                                for g in range(f+1, 11):
                                    for h in range(g+1, 12):
                                        for i in range(h+1, 13):
                                            triple3 = (g**3, h**3, i**3)
                                            variations.append([triple1, triple2, triple3])
        
        # Fourth powers: (a⁴, b⁴, c⁴)
        for a in range(1, 4):
            for b in range(a+1, 5):
                for c in range(b+1, 6):
                    triple1 = (a**4, b**4, c**4)
                    for d in range(c+1, 7):
                        for e in range(d+1, 8):
                            for f in range(e+1, 9):
                                triple2 = (d**4, e**4, f**4)
                                for g in range(f+1, 10):
                                    for h in range(g+1, 11):
                                        for i in range(h+1, 12):
                                            triple3 = (g**4, h**4, i**4)
                                            variations.append([triple1, triple2, triple3])
        
        # 4. Harmonic and special sequences
        print("🔢 Generating harmonic and special sequences...")
        
        # Triangular numbers: n(n+1)/2
        for n1 in range(1, 15):
            for n2 in range(n1+1, 16):
                for n3 in range(n2+1, 17):
                    triple1 = (n1*(n1+1)//2, n2*(n2+1)//2, n3*(n3+1)//2)
                    for n4 in range(n3+1, 18):
                        for n5 in range(n4+1, 19):
                            for n6 in range(n5+1, 20):
                                triple2 = (n4*(n4+1)//2, n5*(n5+1)//2, n6*(n6+1)//2)
                                for n7 in range(n6+1, 21):
                                    for n8 in range(n7+1, 22):
                                        for n9 in range(n8+1, 23):
                                            triple3 = (n7*(n7+1)//2, n8*(n8+1)//2, n9*(n9+1)//2)
                                            variations.append([triple1, triple2, triple3])
        
        # 5. Random but structured variations
        print("🔢 Generating structured random variations...")
        
        # Variations around our breakthrough squares
        breakthrough = [(1, 4, 9), (16, 25, 36), (49, 64, 81)]
        for offset in range(-5, 6):
            for scale in [1, 2, 3]:
                variant = []
                for triple in breakthrough:
                    new_triple = tuple(max(1, x + offset * scale) for x in triple)
                    variant.append(new_triple)
                variations.append(variant)
        
        print(f"✅ Generated {len(variations)} triple variations")
        return variations
    
    def test_triple_set(self, triple_set: List[Tuple[int, int, int]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific set of neutrino triples."""
        
        try:
            # Create modified config
            modified_config = copy.deepcopy(config)
            modified_config['options']['nu_R_triples'] = triple_set
            
            # Test the configuration
            exp = UGPSingleLawUUFFlow(modified_config, self.project_root)
            result = exp.run_task('single_law_uuf_flow')
            
            # Extract results
            ckm_validation = result['validation']['ckm_validation']
            pmns_validation = result['validation']['pmns_validation']
            
            ckm_avg_error = (ckm_validation['errors']['theta12_error'] + 
                            ckm_validation['errors']['theta13_error'] + 
                            ckm_validation['errors']['theta23_error']) / 3 * 100
            
            pmns_avg_error = (pmns_validation['errors']['theta12_error'] + 
                             pmns_validation['errors']['theta13_error'] + 
                             pmns_validation['errors']['theta23_error']) / 3 * 100
            
            # Check CKM preservation
            ckm_preserved = ckm_avg_error < 1.5 and abs(ckm_avg_error - self.baseline_ckm_error) < 0.2
            
            return {
                'triple_set': triple_set,
                'success': True,
                'ckm_avg_error': ckm_avg_error,
                'pmns_avg_error': pmns_avg_error,
                'ckm_preserved': ckm_preserved,
                'pmns_improvement': self.current_pmns_error - pmns_avg_error,
                'ckm_angles': ckm_validation['angles'],
                'pmns_angles': pmns_validation['angles'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'triple_set': triple_set,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_optimization(self, max_tests: int = 50):
        """Run the neutrino triple optimization."""
        
        print("🚀 NEUTRINO TRIPLE OPTIMIZER - SYSTEMATIC EXPLORATION")
        print("=" * 70)
        
        # Load base configuration
        config_path = self.project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
        try:
            with open(config_path, 'r') as f:
                base_config = yaml.safe_load(f)
            print(f"✅ Base configuration loaded")
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False
        
        # Generate triple variations
        variations = self.generate_triple_variations()
        
        # Limit to max_tests for initial exploration
        if len(variations) > max_tests:
            # Prioritize promising variations
            variations = variations[:max_tests]
        
        print(f"\n🧪 Testing {len(variations)} triple variations...")
        
        results = []
        improvements = []
        
        for i, triple_set in enumerate(variations):
            print(f"   Testing {i+1}/{len(variations)}: {triple_set}")
            
            result = self.test_triple_set(triple_set, base_config)
            results.append(result)
            
            if result['success']:
                status = "✅" if result['ckm_preserved'] else "❌"
                ckm_change = result['ckm_avg_error'] - self.baseline_ckm_error
                pmns_change = result['pmns_avg_error'] - self.current_pmns_error
                print(f"     {status} CKM: {result['ckm_avg_error']:.2f}% ({ckm_change:+.2f}%), PMNS: {result['pmns_avg_error']:.2f}% ({pmns_change:+.2f}%)")
                
                if result['pmns_improvement'] > 0:
                    improvements.append(result)
                    print(f"     🎯 IMPROVEMENT: {result['pmns_improvement']:.2f}% better!")
            else:
                print(f"     ❌ Failed: {result['error']}")
        
        # Analyze results
        print(f"\n📊 NEUTRINO TRIPLE OPTIMIZATION RESULTS")
        print("=" * 50)
        
        successful_results = [r for r in results if r['success']]
        ckm_preserved_results = [r for r in successful_results if r['ckm_preserved']]
        
        print(f"Total variations tested: {len(results)}")
        print(f"Successful runs: {len(successful_results)}")
        print(f"CKM preserved runs: {len(ckm_preserved_results)}")
        print(f"PMNS improvements: {len(improvements)}")
        
        if improvements:
            # Find best improvement
            best_improvement = max(improvements, key=lambda x: x['pmns_improvement'])
            
            print(f"\n🎯 BEST IMPROVEMENT:")
            print(f"Triple Set: {best_improvement['triple_set']}")
            print(f"CKM Average Error: {best_improvement['ckm_avg_error']:.2f}%")
            print(f"PMNS Average Error: {best_improvement['pmns_avg_error']:.2f}%")
            print(f"PMNS Improvement: {best_improvement['pmns_improvement']:.2f}%")
            print(f"Total Improvement from Baseline: {self.baseline_pmns_error - best_improvement['pmns_avg_error']:.2f}%")
            
            # Save results
            output_dir = self.project_root / "UUF_OPTIMIZATION_ARTIFACTS"
            output_dir.mkdir(exist_ok=True)
            
            results_file = output_dir / "neutrino_triple_optimization_results.json"
            with open(results_file, 'w') as f:
                json.dump({
                    'baseline': {
                        'ckm_error': self.baseline_ckm_error,
                        'pmns_error': self.baseline_pmns_error
                    },
                    'current_breakthrough': {
                        'pmns_error': self.current_pmns_error
                    },
                    'best_improvement': best_improvement,
                    'all_improvements': improvements,
                    'all_results': results,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            # Check if we've achieved significant progress
            if best_improvement['pmns_avg_error'] < 15.0:
                print(f"🎉 MAJOR BREAKTHROUGH: PMNS error < 15%!")
            elif best_improvement['pmns_avg_error'] < 20.0:
                print(f"🎯 SIGNIFICANT BREAKTHROUGH: PMNS error < 20%!")
            elif best_improvement['pmns_avg_error'] < self.current_pmns_error:
                print(f"📈 IMPROVEMENT: PMNS error reduced by {best_improvement['pmns_improvement']:.2f}%")
        
        else:
            print(f"\n⚠️  NO IMPROVEMENTS: All variations failed to improve PMNS")
        
        return True


def run_neutrino_triple_optimization():
    """Run the neutrino triple optimization."""
    
    optimizer = NeutrinoTripleOptimizer(project_root)
    success = optimizer.run_optimization(max_tests=30)  # Start with 30 tests
    
    if success:
        print(f"\n✅ Neutrino triple optimization completed successfully")
    else:
        print(f"\n❌ Neutrino triple optimization failed")
        sys.exit(1)


if __name__ == "__main__":
    run_neutrino_triple_optimization()
