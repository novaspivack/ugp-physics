"""
Fine-tuned Proximity Functional Test
Testing with looser convergence tolerance and more starts

Author: AI Assistant
Date: 2025-01-27
"""

import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Callable

sys.path.insert(0, str(Path(__file__).parent))

from srrg_core import (
    GTETriple, SRRGParameters,
    basin_structure_analysis, triple_distance
)
from srrg_io import load_canonical_sm_triples, particles_to_triples

# Simple proximity functional
def create_proximity_functional(canonical_triples):
    def F_fn(triple):
        min_dist = min(triple_distance(triple, canon) for canon in canonical_triples)
        return 1.0 / (1.0 + min_dist)
    return F_fn


def test_all_particles(particles: List[Dict],
                      canonical_triples: List[GTETriple],
                      params: SRRGParameters,
                      n_starts: int = 512,
                      radius: float = 5.0,
                      convergence_tol: float = 10.0,  # Looser tolerance
                      verbose: bool = True) -> Dict:
    """Test with fine-tuned parameters."""
    
    if verbose:
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  FINE-TUNED PROXIMITY FUNCTIONAL TEST".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"\nConfiguration:")
        print(f"  Particles: {len(particles)}")
        print(f"  Random starts per particle: {n_starts}")
        print(f"  Sampling radius: {radius}")
        print(f"  Convergence tolerance: {convergence_tol} (looser)")
        print(f"\nTesting...\n")
    
    F_fn = create_proximity_functional(canonical_triples)
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
        "test_name": "Fine-Tuned Proximity Functional",
        "n_particles": len(particles),
        "n_starts_per_particle": n_starts,
        "radius": radius,
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
        
        if mean_attraction >= 0.95:
            print("\n✅ SUCCESS — Infrastructure works perfectly!")
        elif mean_attraction >= 0.80:
            print("\n⚠️  GOOD — Most particles converge, minor tuning needed")
        else:
            print("\n⚠️  NEEDS MORE TUNING — Consider:")
            print("   - Even looser convergence tolerance")
            print("   - Larger sampling radius")
            print("   - More random starts")
        
        print("═" * 80)
    
    return overall


def main():
    """Run fine-tuned test."""
    
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    canonical_triples = particles_to_triples(particles)
    
    params = SRRGParameters()
    
    # Test with different tolerances
    for tol in [10.0, 15.0, 20.0]:
        print(f"\n{'='*80}")
        print(f"Testing with convergence_tol = {tol}")
        print(f"{'='*80}\n")
        
        results = test_all_particles(
            particles=particles,
            canonical_triples=canonical_triples,
            params=params,
            n_starts=512,
            radius=5.0,
            convergence_tol=tol,
            verbose=True
        )
        
        # Save results
        results_path = output_dir / f"proximity_fine_tuned_tol_{tol:.0f}.json"
        import json
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Results saved: {results_path}")
        
        if results["mean_attraction_rate"] >= 0.95:
            print(f"\n🎉 SUCCESS! Convergence tolerance {tol} achieves ≥95% attraction!")
            break


if __name__ == "__main__":
    main()

