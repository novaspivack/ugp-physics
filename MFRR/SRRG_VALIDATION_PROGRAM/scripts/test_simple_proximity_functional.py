"""
Simple Proximity-Based Functional Test
Option A Diagnostic: Test if infrastructure works with simple functional

This test uses a trivial functional that rewards proximity to canonical SM triples.
If this produces high attraction rates (≥95%), we know:
- Infrastructure works correctly
- Flow mechanism works
- Problem is with the SRRG functional definition

If this still fails, then problem is with flow mechanism or constraints.

Author: AI Assistant
Date: 2025-01-27
"""

import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Callable

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from srrg_core import (
    GTETriple, SRRGParameters,
    basin_structure_analysis, triple_distance,
    srrg_flow_to_convergence
)
from srrg_io import load_canonical_sm_triples, particles_to_triples

# =============================================================================
# Section A: Simple Proximity-Based Functional
# =============================================================================

def create_proximity_functional(canonical_triples: List[GTETriple]) -> Callable[[GTETriple], float]:
    """
    Create a simple functional that rewards proximity to canonical triples.
    
    F_proximity(triple) = max_canonical [1 / (1 + distance(triple, canonical))]
    
    This should definitely show attraction to canonical if flow mechanism works.
    
    Args:
        canonical_triples: List of canonical SM triples
    
    Returns:
        Functional F(triple) that returns viability score
    """
    def F_proximity(triple: GTETriple) -> float:
        # Find minimum distance to any canonical triple
        min_dist = min(triple_distance(triple, canon) for canon in canonical_triples)
        
        # Reward = inverse distance (closer = higher reward)
        # Add 1 to avoid division by zero
        reward = 1.0 / (1.0 + min_dist)
        
        # Scale to reasonable range (0 to 1)
        return reward
    
    return F_proximity


def create_proximity_functional_with_penalty(canonical_triples: List[GTETriple],
                                             penalty_weight: float = 100.0) -> Callable[[GTETriple], float]:
    """
    Create proximity functional with penalty for constraint violations.
    
    F(triple) = R_proximity(triple) - C_violations(triple)
    
    This tests if constraints are preventing convergence.
    
    Args:
        canonical_triples: List of canonical SM triples
        penalty_weight: Weight for constraint violations
    
    Returns:
        Functional F(triple)
    """
    def F_proximity_penalty(triple: GTETriple) -> float:
        # Reward: proximity
        min_dist = min(triple_distance(triple, canon) for canon in canonical_triples)
        reward = 1.0 / (1.0 + min_dist)
        
        # Cost: simple admissibility check (penalize if out of range)
        cost = 0.0
        
        a, b, c, g = triple.a, triple.b, triple.c, triple.g
        
        # Penalize if generation invalid
        if g not in {0, 1, 2, 3}:
            cost += penalty_weight
        
        # Penalize if a, b, c out of reasonable ranges
        if a < 1 or a > 100_000:
            cost += penalty_weight * 0.1
        
        if b < 1 or b > 1_000_000:
            cost += penalty_weight * 0.1
        
        if c < -1 or (c > 0 and c > 100_000):
            cost += penalty_weight * 0.1
        
        return reward - cost
    
    return F_proximity_penalty


# =============================================================================
# Section B: Single-Particle Test
# =============================================================================

def test_single_particle_proximity(particle_name: str,
                                   canonical_triples: List[GTETriple],
                                   params: SRRGParameters,
                                   n_starts: int = 128,
                                   radius: float = 5.0,
                                   convergence_tol: float = 2.0,
                                   verbose: bool = True) -> Dict:
    """
    Test proximity functional on a single particle.
    
    Args:
        particle_name: Name of particle to test
        canonical_triples: All canonical triples
        params: SRRG parameters (for flow settings)
        n_starts: Number of random starts
        radius: Sampling radius
        convergence_tol: Distance tolerance
        verbose: Print progress
    
    Returns:
        Basin analysis results
    """
    # Find canonical triple for this particle
    canonical_triple = None
    for t in canonical_triples:
        if t.name == particle_name:
            canonical_triple = t
            break
    
    if canonical_triple is None:
        raise ValueError(f"Particle {particle_name} not found in canonical triples")
    
    if verbose:
        print(f"\nTesting {particle_name}: {canonical_triple}")
    
    # Create proximity functional
    F_fn = create_proximity_functional(canonical_triples)
    
    # Test: Check if canonical triple has maximum F
    F_canonical = F_fn(canonical_triple)
    
    # Test nearby triple
    nearby = GTETriple(
        canonical_triple.a + 1,
        canonical_triple.b,
        canonical_triple.c,
        canonical_triple.g,
        canonical_triple.name
    )
    F_nearby = F_fn(nearby)
    
    if verbose:
        print(f"  F(canonical) = {F_canonical:.6f}")
        print(f"  F(nearby) = {F_nearby:.6f}")
        print(f"  F(canonical) > F(nearby): {F_canonical > F_nearby}")
    
    # Run basin analysis
    results = basin_structure_analysis(
        triple_canonical=canonical_triple,
        F_fn=F_fn,
        params=params,
        ucl_fn=None,
        radius=radius,
        n_starts=n_starts,
        convergence_tol=convergence_tol,
        seed=42
    )
    
    results["particle_name"] = particle_name
    results["F_canonical"] = F_canonical
    results["F_nearby"] = F_nearby
    
    return results


# =============================================================================
# Section C: All-Particle Test
# =============================================================================

def test_all_particles_proximity(particles: List[Dict],
                                 canonical_triples: List[GTETriple],
                                 params: SRRGParameters,
                                 n_starts: int = 128,
                                 radius: float = 5.0,
                                 convergence_tol: float = 2.0,
                                 verbose: bool = True) -> Dict:
    """
    Test proximity functional on all SM particles.
    
    Args:
        particles: List of particle dictionaries
        canonical_triples: All canonical triples
        params: SRRG parameters
        n_starts: Number of random starts per particle
        radius: Sampling radius
        convergence_tol: Distance tolerance
        verbose: Print progress
    
    Returns:
        Aggregate results
    """
    if verbose:
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  OPTION A: SIMPLE PROXIMITY FUNCTIONAL TEST".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"\nConfiguration:")
        print(f"  Particles: {len(particles)}")
        print(f"  Random starts per particle: {n_starts}")
        print(f"  Sampling radius: {radius}")
        print(f"  Convergence tolerance: {convergence_tol}")
        print(f"\nTesting proximity-based functional...\n")
    
    results_list = []
    
    for particle_dict in particles:
        particle_name = particle_dict["name"]
        
        try:
            result = test_single_particle_proximity(
                particle_name=particle_name,
                canonical_triples=canonical_triples,
                params=params,
                n_starts=n_starts,
                radius=radius,
                convergence_tol=convergence_tol,
                verbose=verbose
            )
            
            result["sector"] = particle_dict["sector"]
            result["generation"] = particle_dict["generation"]
            results_list.append(result)
            
            if verbose:
                print(f"  {particle_name}: attraction={result['attraction_rate']:.1%}")
        
        except Exception as e:
            if verbose:
                print(f"  {particle_name}: ERROR - {e}")
            continue
    
    # Aggregate statistics
    attraction_rates = [r["attraction_rate"] for r in results_list]
    mean_attraction = np.mean(attraction_rates) if attraction_rates else 0.0
    std_attraction = np.std(attraction_rates) if attraction_rates else 0.0
    n_pass = sum(1 for r in attraction_rates if r >= 0.95)
    
    overall = {
        "test_name": "Option A: Simple Proximity Functional",
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
        
        "particle_results": results_list,
        
        "diagnostic": {
            "if_attraction_high": "Infrastructure works; problem is SRRG functional definition",
            "if_attraction_low": "Problem is flow mechanism or constraints; debug further"
        }
    }
    
    if verbose:
        print("\n" + "═" * 80)
        print("OPTION A RESULTS")
        print("═" * 80)
        print(f"\nAttraction Rate:")
        print(f"  Mean: {mean_attraction:.1%} ± {std_attraction:.1%}")
        print(f"  Range: [{min(attraction_rates):.1%}, {max(attraction_rates):.1%}]")
        print(f"  Particles passing ≥95%: {n_pass}/{len(results_list)}")
        
        if mean_attraction >= 0.95:
            print("\n✅ INFRASTRUCTURE WORKS — Problem is SRRG functional definition")
            print("   Next step: Implement proper R[S] using braid invariants or UCL")
        elif mean_attraction >= 0.50:
            print("\n⚠️  PARTIAL SUCCESS — Flow works but may need tuning")
            print("   Consider: Looser convergence tolerance, larger radius")
        else:
            print("\n❌ INFRASTRUCTURE ISSUE — Flow mechanism or constraints problematic")
            print("   Next step: Debug gradient computation, Fisher metric, constraints")
        
        print("═" * 80)
    
    return overall


# =============================================================================
# Section D: Main Execution
# =============================================================================

def main():
    """Run Option A diagnostic test."""
    
    # Setup paths
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Load canonical SM triples
    triples_path = data_dir / "canonical_sm_triples.json"
    
    if not triples_path.exists():
        print(f"❌ Error: {triples_path} not found")
        sys.exit(1)
    
    particles = load_canonical_sm_triples(triples_path)
    canonical_triples = particles_to_triples(particles)
    
    print(f"Loaded {len(particles)} SM particles")
    
    # SRRG parameters (minimal, just for flow settings)
    params = SRRGParameters()
    
    # Run test with smaller n_starts for speed
    results = test_all_particles_proximity(
        particles=particles,
        canonical_triples=canonical_triples,
        params=params,
        n_starts=128,  # Smaller for diagnostic
        radius=5.0,
        convergence_tol=2.0,
        verbose=True
    )
    
    # Save results
    results_path = output_dir / "option_a_proximity_test_results.json"
    import json
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved: {results_path}")
    
    return results


if __name__ == "__main__":
    results = main()

