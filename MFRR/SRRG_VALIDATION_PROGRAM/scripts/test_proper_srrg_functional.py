"""
Test Proper SRRG Functional with Basin Analysis
Using actual braid invariants and UCL

Author: AI Assistant
Date: 2025-01-27
"""

import numpy as np
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from srrg_core import GTETriple, SRRGParameters, basin_structure_analysis
from srrg_io import load_canonical_sm_triples, particles_to_triples
from srrg_functional_proper import (
    load_braid_atlas_safe, elegant_palette,
    viability_functional_proper
)

def test_proper_functional(particles: List[Dict],
                          canonical_triples: List[GTETriple],
                          n_starts: int = 128,
                          radius: float = 5.0,
                          convergence_tol: float = 15.0,
                          verbose: bool = True) -> Dict:
    """Test proper SRRG functional with basin analysis."""
    
    # Load braid atlas — bundled snapshot in SRRG data/ directory
    atlas_path = Path(__file__).resolve().parents[1] / "data" / "canonical_braid_atlas.json"
    braid_atlas = load_braid_atlas_safe(atlas_path)
    
    # UCL palette
    ucl_palette = elegant_palette()
    
    # SRRG parameters
    params = SRRGParameters()
    
    if verbose:
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  PROPER SRRG FUNCTIONAL TEST (Braid + UCL)".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"\nConfiguration:")
        print(f"  Braid atlas: {len(braid_atlas)} particles")
        print(f"  UCL palette: Elegant (Quarter-Lock satisfied)")
        print(f"  Random starts per particle: {n_starts}")
        print(f"  Convergence tolerance: {convergence_tol}")
        print(f"\nTesting...\n")
    
    # Create functional using braid + UCL
    def F_fn(triple):
        return viability_functional_proper([triple], braid_atlas, ucl_palette, params)
    
    results_list = []
    
    for particle_dict in particles:
        particle_name = particle_dict["name"]
        
        # Find canonical
        canonical = None
        for t in canonical_triples:
            if t.name == particle_name:
                canonical = t
                break
        
        if canonical is None:
            continue
        
        # Run basin analysis
        result = basin_structure_analysis(
            triple_canonical=canonical,
            F_fn=F_fn,
            params=params,
            ucl_fn=None,
            radius=radius,
            n_starts=n_starts,
            convergence_tol=convergence_tol,
            seed=42
        )
        
        result["particle_name"] = particle_name
        result["sector"] = particle_dict["sector"]
        result["generation"] = particle_dict["generation"]
        results_list.append(result)
        
        if verbose:
            print(f"  {particle_name:20s}: {result['attraction_rate']:6.1%} ({result['n_converged']}/{result['n_total']})")
    
    # Aggregate
    attraction_rates = [r["attraction_rate"] for r in results_list]
    mean_attraction = np.mean(attraction_rates) if attraction_rates else 0.0
    std_attraction = np.std(attraction_rates) if attraction_rates else 0.0
    n_pass = sum(1 for r in attraction_rates if r >= 0.95)
    
    overall = {
        "test_name": "Proper SRRG Functional (Braid + UCL)",
        "n_particles": len(particles),
        "n_starts_per_particle": n_starts,
        "convergence_tol": convergence_tol,
        
        "mean_attraction_rate": mean_attraction,
        "std_attraction_rate": std_attraction,
        "min_attraction_rate": min(attraction_rates) if attraction_rates else 0.0,
        "max_attraction_rate": max(attraction_rates) if attraction_rates else 0.0,
        "n_pass_95pct": n_pass,
        "n_total": len(results_list),
        
        "particle_results": results_list
    }
    
    if verbose:
        print("\n" + "═" * 80)
        print("RESULTS")
        print("═" * 80)
        print(f"\nAttraction Rate:")
        print(f"  Mean: {mean_attraction:.1%} ± {std_attraction:.1%}")
        print(f"  Range: [{min(attraction_rates):.1%}, {max(attraction_rates):.1%}]")
        print(f"  Particles passing ≥95%: {n_pass}/{len(results_list)}")
        
        if n_pass >= len(results_list) * 0.95:
            print("\n✅ SUCCESS — Proper SRRG functional validates SM as attractors!")
        elif mean_attraction >= 0.80:
            print("\n⚠️  GOOD — Most particles converge, may need weight tuning")
        else:
            print("\n⚠️  NEEDS WORK — Functional may need calibration")
        
        print("═" * 80)
    
    return overall


def main():
    """Run proper SRRG functional test."""
    
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    canonical_triples = particles_to_triples(particles)
    
    # Run test
    results = test_proper_functional(
        particles=particles,
        canonical_triples=canonical_triples,
        n_starts=128,  # Smaller for faster test
        radius=5.0,
        convergence_tol=15.0,
        verbose=True
    )
    
    # Save results
    results_path = output_dir / "proper_srrg_functional_test_results.json"
    import json
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved: {results_path}")
    
    return results


if __name__ == "__main__":
    results = main()

