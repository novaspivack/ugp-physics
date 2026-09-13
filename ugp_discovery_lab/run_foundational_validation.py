#!/usr/bin/env python3
# NOTE: The HolographicTransducer experiment below uses synthetic Rule-110 CA data,
# NOT real GTE triple evolution data. Its import is retained for historical reference
# but this script should not be run for publication results.
# See specs/DEPRECATED/holographic_transducer_experiment_from_ugp_discovery_lab/
"""
Foundational Validation Test Script

Runs foundational experiments as specified in Eval Phase Two.
NOTE: holographic_transducer uses synthetic CA data — see DEPRECATED registry.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append('.')

from ugp_discovery_lab.experiments.dihedral_consistency import DihedralConsistency
from ugp_discovery_lab.experiments.index_lock import IndexLock
from ugp_discovery_lab.experiments.holographic_transducer import HolographicTransducer
from ugp_discovery_lab.experiments.statistical_mechanics import StatisticalMechanics


def run_experiment(exp_class, config_data, experiment_name):
    """Run a single experiment and return results."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {experiment_name}")
    print(f"{'='*60}")
    
    try:
        # Create experiment
        exp = exp_class(config_data, Path('.'))
        print(f"✓ {experiment_name} experiment created")
        
        # Generate tasks
        tasks = exp.tasks()
        print(f"✓ Generated {len(tasks)} tasks")
        
        if not tasks:
            print(f"⚠ No tasks generated for {experiment_name}")
            return {
                "experiment": experiment_name,
                "success": False,
                "error": "No tasks generated",
                "tasks_run": 0,
                "results": []
            }
        
        # Run tasks (no artificial limits)
        results = []
        
        for i, task in enumerate(tasks):
            print(f"  Running task {i+1}/{len(tasks)}: {task.get('task_id', 'unknown')}")
            try:
                result = exp.run_task(task)
                results.append(result)
                # Check both success and status fields for compatibility
                is_success = result.get('success', False) or result.get('status') == 'success'
                status = "✓" if is_success else "✗"
                print(f"    {status} Task completed")
            except Exception as e:
                print(f"    ✗ Task failed: {e}")
                results.append({
                    "task_id": task.get('task_id', 'unknown'),
                    "success": False,
                    "error": str(e)
                })
        
        # Summarize results
        summary = exp.summarize(results)
        print(f"✓ {experiment_name} completed")
        print(f"  Success rate: {summary.get('success_rate', 0):.1%}")
        
        return {
            "experiment": experiment_name,
            "success": True,
            "tasks_run": len(results),
            "results": results,
            "summary": summary
        }
        
    except Exception as e:
        print(f"✗ {experiment_name} failed: {e}")
        return {
            "experiment": experiment_name,
            "success": False,
            "error": str(e),
            "tasks_run": 0,
            "results": []
        }


def main():
    """Run all four foundational validation experiments."""
    print("🚀 FOUNDATIONAL VALIDATION SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Common data source - use actual experiment results
    common_runs = [
        "UGP_discovery_lab_runs/exp_20250917_164452/results/reports/experiment_results.json",
        "UGP_discovery_lab_runs/exp_20250917_141117/results/reports/experiment_results.json",
        "UGP_discovery_lab_runs/exp_20250917_124117/results/reports/experiment_results.json"
    ]
    
    all_results = []
    
    # 1. Dihedral Lock Discovery & High-Precision Validation
    dihedral_config = {
        'experiment': {'name': 'dihedral_consistency', 'description': 'High-precision PSLQ validation'},
        'inputs': {'runs': common_runs},
        'fit': {
            'precision_bits': 200,
            'pslq_max_coeff': 64,
            'pslq_tolerance': 1.0e-10,
            'bootstrap_samples': 100,
            'algebraic_basis': ["1", "cos(pi/n)", "sin(pi/n)", "1/(2*cos(pi/n))", "sqrt(2)", "sqrt(3)", "sqrt(5)"]
        },
        'hypotheses': [
            {'name': 'pslq_algebraic', 'form': 'alpha = algebraic_combination', 'tol_abs': 1.0e-10},
            {'name': 'cos_formula', 'form': 'alpha = 1/(2*cos(pi/n))', 'tol_abs': 1.0e-6}
        ],
        'run': {'steps': 100, 'window': 64, 'seeds': [42, 173, 823]}
    }
    
    result1 = run_experiment(DihedralConsistency, dihedral_config, "Dihedral Lock Discovery")
    all_results.append(result1)
    
    # 2. Index Lock Detection Across Lawful Evolutions
    index_config = {
        'experiment': {'name': 'index_lock', 'description': 'Search for new index locks'},
        'inputs': {'runs': common_runs},
        'detection': {
            'event_types': ['ridge', 'mirror'],
            'min_support_fraction': 0.95,
            'min_support': 20,
            'tolerance': 0
        }
    }
    
    result2 = run_experiment(IndexLock, index_config, "Index Lock Detection")
    all_results.append(result2)
    
    # 3. Holographic Transducer Accuracy Quantification
    holography_config = {
        'experiment': {'name': 'holographic_transducer', 'description': 'Holographic reconstruction accuracy'},
        'data': {'runs': common_runs},
        'eval': {
            'max_steps': 100,
            'metrics': ['exact_match_rate', 'mean_hamming_distance', 'max_prefix_length'],
            'pass_threshold': 0.99
        },
        'boundary_types': ['ridge', 'mirror'],
        'seed_range': [42, 100, 200],
        'window_sizes': [8, 10, 12],
        'transducer_models': ['linear', 'quadratic'],
        'evolution_steps': 50,
        'holographic_threshold': 0.8
    }
    
    result3 = run_experiment(HolographicTransducer, holography_config, "Holographic Transducer")
    all_results.append(result3)
    
    # 4. Statistical Mechanics - Emergent Irreversibility
    statmech_config = {
        'experiment': {'name': 'statistical_mechanics', 'description': 'Verify emergent irreversibility'},
        'inputs': {'runs': common_runs},
        'coarse_graining': {'n_bins_b': 16, 'n_bins_c': 16},
        'verification': {'monotonicity_tolerance': 1.0e-9}
    }
    
    result4 = run_experiment(StatisticalMechanics, statmech_config, "Statistical Mechanics")
    all_results.append(result4)
    
    # Compile final report
    print(f"\n{'='*60}")
    print("FOUNDATIONAL VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    successful_experiments = 0
    total_tasks = 0
    
    for result in all_results:
        exp_name = result['experiment']
        success = result['success']
        tasks_run = result['tasks_run']
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} {exp_name}")
        print(f"  Tasks run: {tasks_run}")
        
        if success:
            successful_experiments += 1
            total_tasks += tasks_run
            
            # Show key findings
            summary = result.get('summary', {})
            if exp_name == "Dihedral Lock Discovery":
                discoveries = summary.get('discoveries', [])
                for discovery in discoveries[:2]:  # Show first 2 discoveries
                    print(f"  📊 {discovery}")
            elif exp_name == "Index Lock Detection":
                metrics = summary.get('metrics', {})
                total_locks = metrics.get('total_locks_detected', 0)
                print(f"  🔍 Total locks detected: {total_locks}")
            elif exp_name == "Holographic Transducer":
                verdict = summary.get('verdict', 'UNKNOWN')
                exact_match = summary.get('exact_match_rate', {}).get('max', 0)
                print(f"  🎯 Verdict: {verdict} (max exact match: {exact_match:.3f})")
            elif exp_name == "Statistical Mechanics":
                entropy_analysis = summary.get('entropy_analysis', {})
                overall_verdict = entropy_analysis.get('overall_verdict', 'UNKNOWN')
                print(f"  🌡️  Second Law verdict: {overall_verdict}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"  ❌ Error: {error}")
    
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS: {successful_experiments}/4 experiments passed")
    print(f"Total tasks executed: {total_tasks}")
    print(f"{'='*60}")
    
    # Save detailed results
    output_file = Path("foundational_validation_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "successful_experiments": successful_experiments,
            "total_experiments": 4,
            "total_tasks": total_tasks,
            "results": all_results
        }, f, indent=2, default=str)
    
    print(f"📄 Detailed results saved to: {output_file}")
    
    return successful_experiments == 4


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
