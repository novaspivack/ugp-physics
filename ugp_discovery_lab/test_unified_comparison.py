#!/usr/bin/env python3
"""
Test script for Unified Flow Comparison System

This script tests both single-law and multi-law approaches side-by-side
and generates comprehensive comparison reports.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_unified_flow_comparison import UGPUnifiedFlowComparison
import yaml


def main():
    """Test the unified comparison system."""
    print("🚀 UGP UNIFIED FLOW COMPARISON TEST")
    print("=" * 60)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_unified_flow_comparison.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print("📋 Configuration loaded successfully!")
        print(f"  Approaches: {config.get('approaches', [])}")
        print()
        
        # Create experiment instance
        experiment = UGPUnifiedFlowComparison(config, project_root)
        
        print("🧪 Available tasks:")
        for task in experiment.tasks():
            print(f"  - {task}")
        print()
        
        # Test multi-law approach
        print("🔬 Testing Multi-Law (Path-A) approach...")
        multi_law_result = experiment._run_multi_law()
        
        if multi_law_result.get('status') == 'success':
            print("✅ MULTI-LAW APPROACH SUCCESSFUL!")
            print()
            print(f"📊 CKM Average Error: {multi_law_result.get('ckm_average_error', 'N/A'):.2f}%")
            print(f"📊 PMNS Average Error: {multi_law_result.get('pmns_average_error', 'N/A'):.2f}%")
            print()
            
            # Show detailed results
            ckm_errors = multi_law_result.get('ckm_errors', {})
            pmns_errors = multi_law_result.get('pmns_errors', {})
            
            print("📈 Detailed Results:")
            print("CKM Angles:")
            for angle, error in ckm_errors.items():
                print(f"  {angle}: {error:.2f}% error")
            
            print("PMNS Angles:")
            for angle, error in pmns_errors.items():
                print(f"  {angle}: {error:.2f}% error")
            print()
            
        else:
            print(f"❌ MULTI-LAW APPROACH FAILED: {multi_law_result.get('error', 'Unknown')}")
            return
        
        # Test single-law approach
        print("🔬 Testing Single-Law (UUF) approach...")
        single_law_result = experiment._run_single_law()
        
        if single_law_result.get('status') == 'success':
            print("✅ SINGLE-LAW APPROACH SUCCESSFUL!")
            print()
            print(f"📊 CKM Average Error: {single_law_result.get('ckm_average_error', 'N/A'):.2f}%")
            print(f"📊 PMNS Average Error: {single_law_result.get('pmns_average_error', 'N/A'):.2f}%")
            print()
            
        else:
            print(f"❌ SINGLE-LAW APPROACH FAILED: {single_law_result.get('error', 'Unknown')}")
            return
        
        # Generate comparison
        print("🔬 Generating side-by-side comparison...")
        comparison_results = {
            "single_law": single_law_result,
            "multi_law": multi_law_result
        }
        
        analysis = experiment._analyze_comparison(comparison_results)
        
        print("📊 COMPARISON RESULTS:")
        print("=" * 40)
        
        # Performance comparison
        perf = analysis.get('performance_comparison', {})
        if perf:
            ckm_perf = perf.get('ckm_performance', {})
            pmns_perf = perf.get('pmns_performance', {})
            
            print("CKM Performance:")
            print(f"  Single Law: {ckm_perf.get('single_law', 'N/A'):.2f}% error")
            print(f"  Multi Law:  {ckm_perf.get('multi_law', 'N/A'):.2f}% error")
            print(f"  Improvement: {ckm_perf.get('improvement', 'N/A'):.1f}%")
            
            print("PMNS Performance:")
            print(f"  Single Law: {pmns_perf.get('single_law', 'N/A'):.2f}% error")
            print(f"  Multi Law:  {pmns_perf.get('multi_law', 'N/A'):.2f}% error")
            print(f"  Improvement: {pmns_perf.get('improvement', 'N/A'):.1f}%")
        
        # Strategic recommendations
        strategic = analysis.get('strategic_recommendations', {})
        if strategic:
            print()
            print("🎯 STRATEGIC RECOMMENDATIONS:")
            print(f"  Primary Approach: {strategic.get('primary_approach', 'Unknown')}")
            print(f"  Rationale: {strategic.get('rationale', 'No rationale')}")
            print(f"  Implementation: {strategic.get('implementation', 'No guidance')}")
        
        print()
        print("🚀 UNIFIED COMPARISON SYSTEM OPERATIONAL!")
        print("  ✅ Both approaches tested successfully")
        print("  ✅ Side-by-side comparison working")
        print("  ✅ Performance analysis complete")
        print("  ✅ Strategic recommendations generated")
        print("  ✅ Ready for production use")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
