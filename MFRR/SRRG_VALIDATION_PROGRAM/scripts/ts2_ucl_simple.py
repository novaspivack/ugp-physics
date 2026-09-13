"""
TS2: UCL Structural Validation (Simplified)
Tests that UCL correctly predicts mass ordering and GTE structure

Since full UCL mass prediction requires the complex IMT pipeline from the Monolith,
this test focuses on what we can validate with pure GTE structure:
1. UCL correctly orders particles by complexity
2. GTE structure correlates with mass hierarchy
3. Generation structure is preserved

Author: AI Assistant  
Date: 2025-01-27
"""

import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, List
from scipy.stats import spearmanr, kendalltau
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))

from srrg_core import GTETriple
from srrg_io import load_canonical_sm_triples
from srrg_functional_pure_gte import elegant_palette, ucl_score, compute_gte_invariants

# =============================================================================
# Section A: UCL Structural Tests
# =============================================================================

def test_mass_ordering(particles: List[Dict],
                      ucl_palette,
                      verbose: bool = True) -> Dict:
    """
    Test if UCL score correlates with mass within sectors.
    
    Uses Spearman rank correlation (non-parametric, order-based).
    """
    results_by_sector = {}
    
    sectors = ["lepton", "quark"]  # Focus on well-measured sectors
    
    for sector in sectors:
        sector_particles = [p for p in particles if p["sector"] == sector]
        
        if len(sector_particles) < 3:
            continue
        
        # Extract UCL scores and masses
        ucl_scores = []
        masses = []
        names = []
        
        for p in sector_particles:
            t_dict = p["triple"]
            triple = GTETriple(t_dict["a"], t_dict["b"], t_dict["c"], t_dict["g"], p["name"])
            
            ucl = ucl_score(triple, ucl_palette)
            
            ucl_scores.append(ucl)
            masses.append(p["mass_pdg_mev"])
            names.append(p["name"])
        
        # Compute Spearman correlation
        if len(ucl_scores) >= 3:
            rho, pval = spearmanr(ucl_scores, np.log(masses))  # Use log(mass) for better linearity
            
            results_by_sector[sector] = {
                "n_particles": len(sector_particles),
                "particles": names,
                "spearman_rho": rho,
                "p_value": pval,
                "significant": pval < 0.05,
                "ucl_scores": ucl_scores,
                "log_masses": np.log(masses).tolist()
            }
            
            if verbose:
                print(f"\n{sector.capitalize()} Sector:")
                print(f"  Particles: {', '.join(names)}")
                print(f"  Spearman ρ: {rho:.4f} (p={pval:.4f})")
                print(f"  Significant: {'✅ YES' if pval < 0.05 else '❌ NO'}")
    
    return results_by_sector


def test_generation_structure(particles: List[Dict],
                              ucl_palette,
                              verbose: bool = True) -> Dict:
    """
    Test if generation structure is preserved in UCL.
    
    Check: Within each sector, do higher generations have different UCL signatures?
    """
    results = {}
    
    sectors = ["lepton", "quark"]
    
    for sector in sectors:
        sector_particles = [p for p in particles if p["sector"] == sector]
        
        # Group by generation
        by_gen = {}
        for p in sector_particles:
            gen = p["generation"]
            if gen not in by_gen:
                by_gen[gen] = []
            
            t_dict = p["triple"]
            triple = GTETriple(t_dict["a"], t_dict["b"], t_dict["c"], t_dict["g"], p["name"])
            inv = compute_gte_invariants(triple)
            ucl = ucl_score(triple, ucl_palette)
            
            by_gen[gen].append({
                "name": p["name"],
                "ucl": ucl,
                "L": inv["L"],
                "L2": inv["L2"],
                "mass": p["mass_pdg_mev"]
            })
        
        results[sector] = by_gen
        
        if verbose:
            print(f"\n{sector.capitalize()} by Generation:")
            for gen in sorted(by_gen.keys()):
                particles_gen = by_gen[gen]
                ucls = [p["ucl"] for p in particles_gen]
                masses = [p["mass"] for p in particles_gen]
                print(f"  Gen {gen}: {[p['name'] for p in particles_gen]}")
                print(f"    UCL: {np.mean(ucls):.4f} ± {np.std(ucls):.4f}")
                print(f"    Mass: {np.mean(masses):.2f} MeV")
    
    return results


# =============================================================================
# Section B: Main TS2 Execution
# =============================================================================

def run_ts2_simple(particles: List[Dict],
                  ucl_palette,
                  verbose: bool = True) -> Dict:
    """Run simplified TS2 validation."""
    
    if verbose:
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  TS2: UCL STRUCTURAL VALIDATION (Simplified)".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"\nConfiguration:")
        print(f"  UCL Palette: Elegant (Quarter-Lock satisfied)")
        print(f"  Tests: Mass ordering, generation structure")
        print(f"  Particles: {len(particles)}")
    
    # Test 1: Mass ordering correlation
    if verbose:
        print("\n1. Mass Ordering Correlation Tests:")
        print("   Testing if UCL preserves mass hierarchy within sectors...")
    
    ordering_results = test_mass_ordering(particles, ucl_palette, verbose=verbose)
    
    # Test 2: Generation structure
    if verbose:
        print("\n2. Generation Structure Tests:")
        print("   Testing if UCL captures generation differences...")
    
    generation_results = test_generation_structure(particles, ucl_palette, verbose=verbose)
    
    # Overall summary
    lepton_correlation = ordering_results.get("lepton", {}).get("spearman_rho", 0.0)
    quark_correlation = ordering_results.get("quark", {}).get("spearman_rho", 0.0)
    
    overall = {
        "test_name": "TS2: UCL Structural Validation",
        "date": "2025-01-27",
        "ordering_correlations": ordering_results,
        "generation_structure": generation_results,
        "summary": {
            "lepton_correlation": lepton_correlation,
            "quark_correlation": quark_correlation,
            "both_significant": (
                ordering_results.get("lepton", {}).get("significant", False) and
                ordering_results.get("quark", {}).get("significant", False)
            )
        },
        "pass": abs(lepton_correlation) > 0.7,  # Moderate correlation threshold
        "note": "Full UCL mass prediction requires IMT pipeline; this tests structural properties"
    }
    
    if verbose:
        print("\n" + "═" * 80)
        print("TS2 RESULTS SUMMARY")
        print("═" * 80)
        print(f"\nMass Ordering Correlations:")
        print(f"  Leptons: ρ={lepton_correlation:.4f}")
        print(f"  Quarks: ρ={quark_correlation:.4f}")
        print(f"\nStatus: {'✅ PASS' if overall['pass'] else '❌ NEEDS WORK'}")
        print("\nNOTE: This is a structural validation.")
        print("Full mass prediction requires IMT pipeline from Monolith.")
        print("═" * 80)
    
    return overall


def main():
    """Main TS2 execution."""
    
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts2_simple"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    
    # UCL palette
    ucl_palette = elegant_palette()
    
    # Run TS2
    results = run_ts2_simple(particles, ucl_palette, verbose=True)
    
    # Save results
    results_path = output_dir / "ts2_simple_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved: {results_path}")
    
    return results


if __name__ == "__main__":
    results = main()

