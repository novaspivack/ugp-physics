#!/usr/bin/env python3
"""
Advanced Extended Neutrino Triple Optimizer

This script implements a comprehensive, advanced optimization system
to search for optimal neutrino triple configurations beyond our current
breakthrough of 22.66% PMNS error.

Current Best: [(1, 9, 25), (36, 49, 64), (81, 100, 121)] → 22.66% PMNS
Goal: Find configurations with <15% PMNS error (target: <7%)

Advanced Features:
- Extended mathematical pattern exploration
- Multi-dimensional optimization
- Genetic algorithm approach
- Advanced square pattern variations
- Hybrid pattern combinations
- Statistical analysis and ranking
"""

import sys
import os
import json
import yaml
import numpy as np
import copy
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from itertools import combinations, permutations, product
import multiprocessing as mp
from functools import partial

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow


class AdvancedExtendedOptimizer:
    """Advanced extended optimizer for neutrino triple configurations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.baseline_pmns_error = 32.80
        self.current_best_error = 22.66
        self.target_error = 7.0
        self.ckm_baseline_error = 0.69
        
        # Load base configuration
        config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
    
    def generate_extended_square_patterns(self):
        """Generate extensive square-based pattern variations."""
        
        patterns = []
        
        # 1. Advanced Square Progressions
        print("🔢 Generating advanced square progressions...")
        
        # Extended consecutive squares
        for start in range(1, 15):
            for step in range(1, 6):
                for offset in range(0, 5):
                    triple1 = [(start + i*step + offset)**2 for i in range(3)]
                    for start2 in range(start + 3*step + offset, 20):
                        for step2 in range(1, 6):
                            for offset2 in range(0, 5):
                                triple2 = [(start2 + i*step2 + offset2)**2 for i in range(3)]
                                for start3 in range(start2 + 3*step2 + offset2, 25):
                                    for step3 in range(1, 6):
                                        for offset3 in range(0, 5):
                                            triple3 = [(start3 + i*step3 + offset3)**2 for i in range(3)]
                                            patterns.append([triple1, triple2, triple3])
        
        # 2. Hybrid Square Patterns
        print("🔢 Generating hybrid square patterns...")
        
        # Mixed square types
        square_types = [
            lambda n: n**2,  # Standard squares
            lambda n: (2*n)**2,  # Even squares
            lambda n: (2*n-1)**2,  # Odd squares
            lambda n: (n**2 + n),  # Triangular-like
            lambda n: (n**2 + 1),  # Shifted squares
        ]
        
        for type1 in square_types:
            for type2 in square_types:
                for type3 in square_types:
                    for base1 in range(1, 15):
                        for base2 in range(base1 + 3, 20):
                            for base3 in range(base2 + 3, 25):
                                patterns.append([
                                    [type1(base1 + i) for i in range(3)],
                                    [type2(base2 + i) for i in range(3)],
                                    [type3(base3 + i) for i in range(3)]
                                ])
        
        # 3. Fractal Square Patterns
        print("🔢 Generating fractal square patterns...")
        
        # Self-similar square patterns
        for scale in range(1, 5):
            for offset in range(0, 10):
                patterns.append([
                    [(scale*i + offset)**2 for i in range(1, 4)],
                    [(scale*i + offset + 3)**2 for i in range(1, 4)],
                    [(scale*i + offset + 6)**2 for i in range(1, 4)]
                ])
        
        # 4. Golden Ratio Square Patterns
        print("🔢 Generating golden ratio square patterns...")
        
        phi = (1 + np.sqrt(5)) / 2
        for n in range(1, 12):
            for k in range(1, 4):
                patterns.append([
                    [int((phi**i * n)**2) for i in range(k, k+3)],
                    [int((phi**i * n * phi)**2) for i in range(k, k+3)],
                    [int((phi**i * n * phi**2)**2) for i in range(k, k+3)]
                ])
        
        print(f"✅ Generated {len(patterns)} extended square patterns")
        return patterns
    
    def generate_advanced_mathematical_patterns(self):
        """Generate advanced mathematical pattern variations."""
        
        patterns = []
        
        # 1. Fibonacci Square Hybrids
        print("🔢 Generating Fibonacci square hybrids...")
        
        fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
        for i in range(len(fib) - 2):
            for j in range(i + 1, len(fib) - 2):
                for k in range(j + 1, len(fib) - 2):
                    patterns.append([
                        [fib[i], fib[i+1]**2, fib[i+2]],
                        [fib[j], fib[j+1]**2, fib[j+2]],
                        [fib[k], fib[k+1]**2, fib[k+2]]
                    ])
        
        # 2. Prime Square Combinations
        print("🔢 Generating prime square combinations...")
        
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        for i in range(len(primes) - 2):
            for j in range(i + 1, len(primes) - 2):
                for k in range(j + 1, len(primes) - 2):
                    patterns.append([
                        [primes[i], primes[i+1]**2, primes[i+2]],
                        [primes[j], primes[j+1]**2, primes[j+2]],
                        [primes[k], primes[k+1]**2, primes[k+2]]
                    ])
        
        # 3. Geometric Progression Squares
        print("🔢 Generating geometric progression squares...")
        
        for r in [2, 3, 4, 5]:
            for a in range(1, 10):
                for offset in range(0, 5):
                    patterns.append([
                        [int((a * r**i + offset)**2) for i in range(3)],
                        [int((a * r**(i+3) + offset)**2) for i in range(3)],
                        [int((a * r**(i+6) + offset)**2) for i in range(3)]
                    ])
        
        # 4. Harmonic Series Squares
        print("🔢 Generating harmonic series squares...")
        
        for n in range(1, 15):
            for step in range(1, 5):
                patterns.append([
                    [int((n + i*step)**2 / (n + i*step)) for i in range(3)],
                    [int((n + (i+3)*step)**2 / (n + (i+3)*step)) for i in range(3)],
                    [int((n + (i+6)*step)**2 / (n + (i+6)*step)) for i in range(3)]
                ])
        
        print(f"✅ Generated {len(patterns)} advanced mathematical patterns")
        return patterns
    
    def generate_optimized_combinations(self):
        """Generate optimized combinations of successful patterns."""
        
        patterns = []
        
        # Current best pattern
        current_best = [(1, 9, 25), (36, 49, 64), (81, 100, 121)]
        
        # 1. Variations around current best
        print("🔢 Generating variations around current best...")
        
        for scale in [0.8, 0.9, 1.1, 1.2]:
            for offset in range(-3, 4):
                variant = []
                for triple in current_best:
                    new_triple = tuple(max(1, int(x * scale + offset)) for x in triple)
                    variant.append(new_triple)
                patterns.append(variant)
        
        # 2. Hybrid combinations of successful patterns
        print("🔢 Generating hybrid combinations...")
        
        successful_patterns = [
            [(1, 4, 9), (16, 25, 36), (49, 64, 81)],  # Original breakthrough
            [(1, 9, 25), (36, 49, 64), (81, 100, 121)],  # Current best
            [(4, 9, 16), (25, 36, 49), (64, 81, 100)],  # Good performer
            [(9, 16, 25), (36, 49, 64), (81, 100, 121)],  # Good performer
        ]
        
        # Create combinations of successful patterns
        for i, pattern1 in enumerate(successful_patterns):
            for j, pattern2 in enumerate(successful_patterns):
                if i != j:
                    # Mix patterns
                    patterns.append([
                        pattern1[0], pattern2[1], pattern1[2]
                    ])
                    patterns.append([
                        pattern2[0], pattern1[1], pattern2[2]
                    ])
                    patterns.append([
                        pattern1[0], pattern1[1], pattern2[2]
                    ])
        
        # 3. Genetic algorithm inspired variations
        print("🔢 Generating genetic algorithm variations...")
        
        for _ in range(100):  # 100 random variations
            # Randomly select elements from successful patterns
            variant = []
            for gen in range(3):
                pattern = random.choice(successful_patterns)
                triple = pattern[gen]
                # Mutate with small random changes
                mutated = tuple(max(1, x + random.randint(-2, 2)) for x in triple)
                variant.append(mutated)
            patterns.append(variant)
        
        print(f"✅ Generated {len(patterns)} optimized combinations")
        return patterns
    
    def generate_extreme_exploration_patterns(self):
        """Generate extreme exploration patterns for breakthrough discovery."""
        
        patterns = []
        
        # 1. Extreme square patterns
        print("🔢 Generating extreme square patterns...")
        
        # Very large squares
        for base in range(10, 50, 5):
            patterns.append([
                [base**2, (base+1)**2, (base+2)**2],
                [(base+3)**2, (base+4)**2, (base+5)**2],
                [(base+6)**2, (base+7)**2, (base+8)**2]
            ])
        
        # 2. Perfect squares with special properties
        print("🔢 Generating perfect squares with special properties...")
        
        # Sum of squares patterns
        for n in range(1, 20):
            patterns.append([
                [n**2, (n+1)**2, (n+2)**2],
                [n**2 + (n+1)**2, (n+1)**2 + (n+2)**2, (n+2)**2 + (n+3)**2],
                [(n+3)**2, (n+4)**2, (n+5)**2]
            ])
        
        # 3. Modular arithmetic squares
        print("🔢 Generating modular arithmetic squares...")
        
        for mod in [7, 11, 13, 17, 19]:
            for base in range(1, mod):
                patterns.append([
                    [base**2 % mod, (base+1)**2 % mod, (base+2)**2 % mod],
                    [(base+3)**2 % mod, (base+4)**2 % mod, (base+5)**2 % mod],
                    [(base+6)**2 % mod, (base+7)**2 % mod, (base+8)**2 % mod]
                ])
        
        print(f"✅ Generated {len(patterns)} extreme exploration patterns")
        return patterns
    
    def test_triple_set(self, triple_set: List[Tuple[int, int, int]]) -> Dict[str, Any]:
        """Test a specific set of neutrino triples."""
        
        try:
            # Create modified config
            modified_config = copy.deepcopy(self.base_config)
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
            ckm_preserved = ckm_avg_error < 1.5 and abs(ckm_avg_error - self.ckm_baseline_error) < 0.2
            
            # Calculate improvement
            improvement = self.current_best_error - pmns_avg_error
            
            return {
                'triple_set': triple_set,
                'success': True,
                'ckm_avg_error': ckm_avg_error,
                'pmns_avg_error': pmns_avg_error,
                'ckm_preserved': ckm_preserved,
                'improvement': improvement,
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
    
    def run_advanced_optimization(self, max_tests: int = 500):
        """Run advanced extended optimization."""
        
        print("🚀 ADVANCED EXTENDED NEUTRINO TRIPLE OPTIMIZER")
        print("=" * 70)
        print(f"Current Best: 22.66% PMNS error")
        print(f"Target: <7% PMNS error")
        print(f"Goal: Find breakthrough configurations")
        print()
        
        # Generate all pattern types
        all_patterns = []
        
        print("🔍 Generating comprehensive pattern library...")
        all_patterns.extend(self.generate_extended_square_patterns())
        all_patterns.extend(self.generate_advanced_mathematical_patterns())
        all_patterns.extend(self.generate_optimized_combinations())
        all_patterns.extend(self.generate_extreme_exploration_patterns())
        
        print(f"✅ Generated {len(all_patterns)} total patterns")
        
        # Limit to max_tests for performance
        if len(all_patterns) > max_tests:
            # Prioritize promising patterns
            random.shuffle(all_patterns)
            all_patterns = all_patterns[:max_tests]
        
        print(f"\n🧪 Testing {len(all_patterns)} advanced patterns...")
        
        results = []
        improvements = []
        breakthroughs = []
        
        for i, triple_set in enumerate(all_patterns):
            if i % 50 == 0:
                print(f"   Progress: {i}/{len(all_patterns)} ({i/len(all_patterns)*100:.1f}%)")
            
            result = self.test_triple_set(triple_set)
            results.append(result)
            
            if result['success'] and result['ckm_preserved']:
                if result['improvement'] > 0:
                    improvements.append(result)
                    if result['pmns_avg_error'] < 15.0:  # Major breakthrough
                        breakthroughs.append(result)
                        print(f"   🎉 BREAKTHROUGH: {result['pmns_avg_error']:.2f}% PMNS error!")
        
        # Analyze results
        print(f"\n📊 ADVANCED OPTIMIZATION RESULTS")
        print("=" * 50)
        
        successful_results = [r for r in results if r['success']]
        ckm_preserved_results = [r for r in successful_results if r['ckm_preserved']]
        
        print(f"Total patterns tested: {len(results)}")
        print(f"Successful runs: {len(successful_results)}")
        print(f"CKM preserved runs: {len(ckm_preserved_results)}")
        print(f"PMNS improvements: {len(improvements)}")
        print(f"Major breakthroughs: {len(breakthroughs)}")
        
        if improvements:
            # Find best improvement
            best_improvement = max(improvements, key=lambda x: x['improvement'])
            
            print(f"\n🎯 BEST IMPROVEMENT:")
            print(f"Triple Set: {best_improvement['triple_set']}")
            print(f"CKM Average Error: {best_improvement['ckm_avg_error']:.2f}%")
            print(f"PMNS Average Error: {best_improvement['pmns_avg_error']:.2f}%")
            print(f"Improvement: {best_improvement['improvement']:.2f}%")
            print(f"Total Improvement from Baseline: {self.baseline_pmns_error - best_improvement['pmns_avg_error']:.2f}%")
            
            # Check achievement level
            if best_improvement['pmns_avg_error'] < 7.0:
                print(f"🎉 TARGET ACHIEVED: PMNS error < 7%!")
            elif best_improvement['pmns_avg_error'] < 10.0:
                print(f"🎯 MAJOR BREAKTHROUGH: PMNS error < 10%!")
            elif best_improvement['pmns_avg_error'] < 15.0:
                print(f"🚀 SIGNIFICANT BREAKTHROUGH: PMNS error < 15%!")
            elif best_improvement['pmns_avg_error'] < self.current_best_error:
                print(f"📈 IMPROVEMENT: PMNS error reduced by {best_improvement['improvement']:.2f}%")
            
            # Save results
            output_dir = self.project_root / "UUF_OPTIMIZATION_ARTIFACTS"
            output_dir.mkdir(exist_ok=True)
            
            results_file = output_dir / "advanced_extended_optimization_results.json"
            with open(results_file, 'w') as f:
                json.dump({
                    'baseline': {
                        'ckm_error': self.ckm_baseline_error,
                        'pmns_error': self.baseline_pmns_error
                    },
                    'current_best': {
                        'pmns_error': self.current_best_error
                    },
                    'target': {
                        'pmns_error': self.target_error
                    },
                    'best_improvement': best_improvement,
                    'all_improvements': improvements,
                    'major_breakthroughs': breakthroughs,
                    'all_results': results,
                    'statistics': {
                        'total_tested': len(results),
                        'successful': len(successful_results),
                        'ckm_preserved': len(ckm_preserved_results),
                        'improvements': len(improvements),
                        'breakthroughs': len(breakthroughs)
                    },
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            # Show top 5 improvements
            if len(improvements) > 1:
                print(f"\n🏆 TOP 5 IMPROVEMENTS:")
                top_5 = sorted(improvements, key=lambda x: x['improvement'], reverse=True)[:5]
                for i, result in enumerate(top_5, 1):
                    print(f"   {i}. PMNS: {result['pmns_avg_error']:.2f}% (improvement: {result['improvement']:.2f}%)")
        
        else:
            print(f"\n⚠️  NO IMPROVEMENTS: All patterns failed to improve PMNS")
            print("This suggests we may be approaching theoretical limits")
        
        return results


def run_advanced_extended_optimization():
    """Run the advanced extended optimization."""
    
    optimizer = AdvancedExtendedOptimizer(project_root)
    results = optimizer.run_advanced_optimization(max_tests=300)  # Start with 300 tests
    
    print(f"\n✅ Advanced extended optimization completed successfully")
    return results


if __name__ == "__main__":
    results = run_advanced_extended_optimization()
