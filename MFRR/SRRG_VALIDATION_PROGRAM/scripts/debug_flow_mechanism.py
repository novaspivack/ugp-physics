"""
Debug SRRG Flow Mechanism
Deep dive into gradient, Fisher metric, and flow step

Author: AI Assistant
Date: 2025-01-27
"""

import numpy as np
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))

from srrg_core import (
    GTETriple, SRRGParameters,
    compute_gradient_fd, fisher_rao_metric, natural_gradient,
    srrg_flow_step, triple_distance
)
from srrg_io import load_canonical_sm_triples, particles_to_triples

# Simple proximity functional
def create_proximity_functional(canonical_triples):
    def F_fn(triple):
        min_dist = min(triple_distance(triple, canon) for canon in canonical_triples)
        return 1.0 / (1.0 + min_dist)
    return F_fn


def debug_single_particle(particle_name: str, canonical_triples: List[GTETriple]):
    """Deep debug of flow for one particle."""
    
    # Find canonical
    canonical = None
    for t in canonical_triples:
        if t.name == particle_name:
            canonical = t
            break
    
    if canonical is None:
        print(f"Particle {particle_name} not found")
        return
    
    print(f"\n{'='*80}")
    print(f"DEBUGGING: {particle_name}")
    print(f"Canonical: {canonical}")
    print(f"{'='*80}\n")
    
    # Create functional
    F_fn = create_proximity_functional(canonical_triples)
    
    # Test 1: Check F at canonical
    F_canonical = F_fn(canonical)
    print(f"1. F(canonical) = {F_canonical:.6f}")
    
    # Test 2: Check gradient at canonical
    print(f"\n2. Gradient at canonical:")
    grad = compute_gradient_fd(F_fn, canonical, delta=1)
    print(f"   ∇F = {grad}")
    print(f"   ||∇F|| = {np.linalg.norm(grad):.6f}")
    
    # Test 3: Check Fisher metric
    print(f"\n3. Fisher metric at canonical:")
    G = fisher_rao_metric(canonical, diagonal_only=True)
    print(f"   G (diagonal) = {np.diag(G)}")
    print(f"   Condition number: {np.linalg.cond(G):.2e}")
    
    # Test 4: Natural gradient
    print(f"\n4. Natural gradient:")
    eta = natural_gradient(grad, G)
    print(f"   η = G⁻¹ @ ∇F = {eta}")
    print(f"   ||η|| = {np.linalg.norm(eta):.6f}")
    
    # Test 5: Check nearby point
    nearby = GTETriple(canonical.a + 2, canonical.b, canonical.c, canonical.g, canonical.name)
    F_nearby = F_fn(nearby)
    grad_nearby = compute_gradient_fd(F_fn, nearby, delta=1)
    print(f"\n5. Nearby point: {nearby}")
    print(f"   F(nearby) = {F_nearby:.6f}")
    print(f"   ∇F(nearby) = {grad_nearby}")
    print(f"   Should point toward canonical?")
    
    # Test 6: Manual flow step
    print(f"\n6. Testing flow step:")
    params = SRRGParameters()
    triple_new, F_new, alpha = srrg_flow_step(
        canonical, F_fn, params, learning_rate=1.0
    )
    print(f"   Starting from: {canonical}")
    print(f"   After step: {triple_new}")
    print(f"   F changed: {F_canonical:.6f} → {F_new:.6f}")
    print(f"   Step size used: {alpha:.4f}")
    print(f"   Distance moved: {triple_distance(canonical, triple_new):.2f}")
    
    # Test 7: Flow from nearby point
    print(f"\n7. Testing flow from nearby point:")
    triple_from_nearby, F_from_nearby, alpha_nearby = srrg_flow_step(
        nearby, F_fn, params, learning_rate=1.0
    )
    print(f"   Starting from: {nearby}")
    print(f"   After step: {triple_from_nearby}")
    print(f"   F changed: {F_nearby:.6f} → {F_from_nearby:.6f}")
    print(f"   Step size used: {alpha_nearby:.4f}")
    print(f"   Distance to canonical: {triple_distance(triple_from_nearby, canonical):.2f}")
    print(f"   Did it get closer? {triple_distance(triple_from_nearby, canonical) < triple_distance(nearby, canonical)}")
    
    # Test 8: Check if gradient actually points toward canonical
    print(f"\n8. Direction analysis:")
    direction_to_canonical = np.array([
        canonical.a - nearby.a,
        canonical.b - nearby.b,
        canonical.c - nearby.c
    ])
    direction_to_canonical_norm = direction_to_canonical / (np.linalg.norm(direction_to_canonical) + 1e-10)
    
    grad_norm = grad_nearby / (np.linalg.norm(grad_nearby) + 1e-10)
    
    cos_angle = np.dot(grad_norm, direction_to_canonical_norm)
    print(f"   Direction to canonical: {direction_to_canonical}")
    print(f"   Gradient direction: {grad_nearby}")
    print(f"   Cosine of angle: {cos_angle:.4f}")
    print(f"   Should be positive (gradient points toward canonical)")
    
    return {
        "particle": particle_name,
        "F_canonical": F_canonical,
        "grad_at_canonical": grad.tolist(),
        "grad_norm": np.linalg.norm(grad),
        "eta_norm": np.linalg.norm(eta),
        "step_from_canonical": {
            "triple_new": str(triple_new),
            "F_new": F_new,
            "alpha": alpha,
            "distance_moved": triple_distance(canonical, triple_new)
        },
        "step_from_nearby": {
            "triple_new": str(triple_from_nearby),
            "F_new": F_from_nearby,
            "alpha": alpha_nearby,
            "distance_to_canonical": triple_distance(triple_from_nearby, canonical),
            "got_closer": triple_distance(triple_from_nearby, canonical) < triple_distance(nearby, canonical)
        },
        "cos_angle": cos_angle
    }


def main():
    """Debug flow for a few representative particles."""
    
    # Load data
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    canonical_triples = particles_to_triples(particles)
    
    # Test a few particles
    test_particles = ["electron", "down", "strange"]  # One with high, medium, low attraction
    
    results = {}
    
    for particle_name in test_particles:
        try:
            result = debug_single_particle(particle_name, canonical_triples)
            results[particle_name] = result
        except Exception as e:
            print(f"Error debugging {particle_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    for particle_name, result in results.items():
        print(f"{particle_name}:")
        print(f"  ||∇F|| at canonical: {result['grad_norm']:.6f}")
        print(f"  ||η|| at canonical: {result['eta_norm']:.6f}")
        print(f"  Step from canonical moved: {result['step_from_canonical']['distance_moved']:.2f}")
        print(f"  Step from nearby got closer: {result['step_from_nearby']['got_closer']}")
        print(f"  Cos(angle): {result['cos_angle']:.4f}")
        print()
    
    # Save results
    output_dir = program_dir / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    import json
    results_path = output_dir / "debug_flow_mechanism_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✅ Debug results saved: {results_path}")


if __name__ == "__main__":
    main()

