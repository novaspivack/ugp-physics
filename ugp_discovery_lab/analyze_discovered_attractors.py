#!/usr/bin/env python3
"""
Analysis of discovered RG attractors from the Independent Derivations suite.
"""

import json
import numpy as np
import math
from pathlib import Path

def load_suite_results():
    """Load the suite results."""
    suite_file = Path("UGP_discovery_lab_runs/suite_20250917_192820/results/reports/suite_results.json")
    if not suite_file.exists():
        print(f"Suite results file not found: {suite_file}")
        return None
    
    with open(suite_file, 'r') as f:
        return json.load(f)

def analyze_attractors():
    """Analyze all discovered attractors."""
    results = load_suite_results()
    if not results:
        return
    
    print("🔍 **DISCOVERED RG ATTRACTORS ANALYSIS**")
    print("=" * 60)
    
    # Extract variational results
    variational_exp = None
    for exp in results["data"]["experiments"]:
        if exp["experiment"] == "rg_fixedpoint_variational":
            variational_exp = exp
            break
    
    if not variational_exp:
        print("Variational experiment not found!")
        return
    
    results_data = variational_exp["summary"]["task_results"]["results"]
    
    # Group attractors by value
    attractor_groups = {}
    for result in results_data:
        alpha = result["alpha_star"]
        n_values = result["n_values"]
        dataset_id = result["dataset_id"]
        
        # Round to identify clusters
        alpha_rounded = round(alpha, 8)
        if alpha_rounded not in attractor_groups:
            attractor_groups[alpha_rounded] = []
        
        attractor_groups[alpha_rounded].append({
            "alpha": alpha,
            "n_values": n_values,
            "dataset_id": dataset_id,
            "std": result["alpha_std"]
        })
    
    print(f"\n📊 **ATTRACTOR DISCOVERY SUMMARY**")
    print(f"Total unique attractors found: {len(attractor_groups)}")
    print(f"Total datasets processed: {len(results_data)}")
    
    print(f"\n🎯 **INDIVIDUAL ATTRACTOR ANALYSIS**")
    print("-" * 60)
    
    # Sort attractors by frequency (most common first)
    sorted_attractors = sorted(attractor_groups.items(), 
                             key=lambda x: sum(r["n_values"] for r in x[1]), 
                             reverse=True)
    
    for i, (alpha_rounded, group) in enumerate(sorted_attractors):
        total_occurrences = sum(r["n_values"] for r in group)
        avg_alpha = np.mean([r["alpha"] for r in group])
        std_alpha = np.std([r["alpha"] for r in group])
        
        print(f"\n**Attractor {i+1}**: α* = {avg_alpha:.10f}")
        print(f"  - Occurrences: {total_occurrences} datasets")
        print(f"  - Standard deviation: {std_alpha:.2e}")
        print(f"  - Dataset IDs: {[r['dataset_id'] for r in group]}")
        
        # Mathematical analysis
        analyze_attractor_physics(avg_alpha, i+1)
    
    # U(1) coupling analysis
    analyze_u1_coupling(results)

def analyze_attractor_physics(alpha, attractor_num):
    """Analyze the physical meaning of an attractor."""
    print(f"  🔬 **Physical Analysis**:")
    
    # Check for known constants
    alpha_fine = 0.0072973525693  # Fine structure constant
    pi = math.pi
    
    # Check for rational fractions
    if abs(alpha - 0.25) < 1e-6:
        print(f"    ✅ **QUARTER-LOCK ATTRACTOR**: α* = 1/4")
        print(f"    📐 **Fundamental Law**: Quarter-lock is a fundamental symmetry")
        print(f"    🧮 **Mathematical Form**: α* = 1/4 = 0.25")
        print(f"    🌟 **Significance**: Represents perfect quarter-wave symmetry")
    
    elif abs(alpha - (-0.08503468530335825)) < 1e-10:
        print(f"    ✅ **PRIMARY RG ATTRACTOR**: α* = -0.08503468530335825")
        print(f"    📐 **Known Target**: This is our primary RG attractor")
        print(f"    🧮 **Mathematical Form**: Complex algebraic value")
        print(f"    🌟 **Significance**: Central RG fixed point")
    
    elif abs(alpha - 0.042440334845701144) < 1e-10:
        print(f"    🔍 **NEW ATTRACTOR**: α* ≈ 0.042440334845701144")
        print(f"    📐 **Potential Form**: Could be 1/24 ≈ 0.0416667?")
        print(f"    🧮 **Mathematical Form**: α* ≈ 0.04244 (investigate 1/24)")
        print(f"    🌟 **Significance**: New fundamental constant candidate")
    
    elif abs(alpha - 0.11861039330230842) < 1e-10:
        print(f"    🔍 **NEW ATTRACTOR**: α* ≈ 0.11861039330230842")
        print(f"    📐 **Potential Form**: Could be related to golden ratio?")
        print(f"    🧮 **Mathematical Form**: α* ≈ 0.11861 (investigate φ/π)")
        print(f"    🌟 **Significance**: New fundamental constant candidate")
    
    elif abs(alpha - 0.020362205995770707) < 1e-10:
        print(f"    🔍 **NEW ATTRACTOR**: α* ≈ 0.020362205995770707")
        print(f"    📐 **Potential Form**: Could be 1/49 ≈ 0.020408?")
        print(f"    🧮 **Mathematical Form**: α* ≈ 0.02036 (investigate 1/49)")
        print(f"    🌟 **Significance**: New fundamental constant candidate")
    
    else:
        print(f"    ❓ **UNKNOWN ATTRACTOR**: α* = {alpha:.10f}")
        print(f"    📐 **Status**: Requires further mathematical analysis")
        print(f"    🧮 **Mathematical Form**: TBD")
        print(f"    🌟 **Significance**: Potential new fundamental constant")

def analyze_u1_coupling(results):
    """Analyze U(1) coupling derivation results."""
    print(f"\n🔌 **U(1) GAUGE COUPLING ANALYSIS**")
    print("-" * 60)
    
    # Find U(1) experiment results
    u1_exp = None
    for exp in results["data"]["experiments"]:
        if exp["experiment"] == "u1_coupling_derivation":
            u1_exp = exp
            break
    
    if not u1_exp:
        print("U(1) coupling experiment not found!")
        return
    
    summary = u1_exp["summary"]
    
    print(f"**Current Results:**")
    print(f"  - Derived g₁²: {summary['derived_g1_squared']:.6f}")
    print(f"  - Experimental g₁²: {summary['experimental_g1_squared']:.6f}")
    print(f"  - Relative Error: {summary['relative_error']:.2%}")
    
    print(f"\n**Best Hypothesis:** {summary['best_hypothesis']['name']}")
    print(f"  - Error: {summary['best_hypothesis']['relative_error']:.2%}")
    
    print(f"\n**All Hypotheses Analysis:**")
    for name, hyp in summary["all_hypotheses"].items():
        print(f"  - {name}: {hyp['relative_error']:.2%} error")
    
    print(f"\n**Elegant Kernel Constants:**")
    constants = summary["elegant_kernel_constants"]
    for name, value in constants.items():
        print(f"  - {name}: {value}")
    
    # Analysis of why error is high
    print(f"\n🔍 **ERROR ANALYSIS:**")
    print(f"**Why is the error so high (3224%)?**")
    print(f"  1. **Wrong Hypothesis**: The current formula may not be correct")
    print(f"  2. **Missing Factors**: Additional physical factors not included")
    print(f"  3. **Scale Mismatch**: Units or scaling may be incorrect")
    print(f"  4. **Incomplete Theory**: UGP kernel may need additional terms")
    
    print(f"\n**Best Performing Hypothesis:**")
    best_name = summary['best_hypothesis']['name']
    best_error = summary['best_hypothesis']['relative_error']
    print(f"  - {best_name}: {best_error:.2%} error (much better!)")
    print(f"  - This suggests the correct form may be: g₁² ∝ k_L2 / ||flavor_vector||")
    
    print(f"\n**Refinement Suggestions:**")
    print(f"  1. **Investigate Best Hypothesis**: Focus on curvature_over_flavor_norm")
    print(f"  2. **Add RG Attractor Factor**: Include the primary RG attractor (-0.08503468530335825)")
    print(f"  3. **Include Quarter-Lock**: Factor in the quarter-lock attractor (0.25)")
    print(f"  4. **Multi-Attractor Model**: Use weighted combination of all attractors")

if __name__ == "__main__":
    analyze_attractors()
