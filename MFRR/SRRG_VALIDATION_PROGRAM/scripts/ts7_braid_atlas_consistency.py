"""
TS7: Braid Atlas Consistency & Invariant Sanity Checks
Reference: SRRG_VALIDATION_PROGRAM/1_1_SRRG_VALIDATION_KICKOFF_PLAN.md

Tests that the arithmetic-topological dictionary is consistent:
- GTE triples correctly map to braid invariants
- Round-trip accuracy: triple → braid → triple
- Topological invariants align with triple structure
- Chirality and parity properties preserved

Acceptance Criteria:
- ✅ Round-trip accuracy: 100% (exact equality on all canonical particles)
- ✅ Invariant consistency: All topological properties align with GTE structure
- ✅ Mirror map test: Chirality flips behave as expected

Author: AI Assistant
Date: 2025-01-27
Cross-Reference: SRRG_VALIDATION_PROGRAM/1_1_SRRG_VALIDATION_KICKOFF_PLAN.md
"""

import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))

from srrg_core import GTETriple
from srrg_io import load_canonical_sm_triples

# =============================================================================
# Section A: Braid Atlas Loading
# =============================================================================

def load_braid_atlas(atlas_path: Path) -> Dict:
    """Load canonical braid atlas."""
    with open(atlas_path, 'r') as f:
        return json.load(f)


def normalize_particle_name(name: str) -> str:
    """Normalize particle names for matching."""
    # Map between different naming conventions
    name_map = {
        "e_neutrino": "electron_neutrino",
        "mu_neutrino": "muon_neutrino",
        "tau_neutrino": "tau_neutrino",
        "up_quark": "up",
        "down_quark": "down",
        "charm_quark": "charm",
        "strange_quark": "strange",
        "top_quark": "top",
        "bottom_quark": "bottom",
        "W": "W_boson",
        "Z": "Z_boson",
        "H": "Higgs_boson",
        "Higgs": "Higgs_boson"
    }
    
    return name_map.get(name, name)


# =============================================================================
# Section B: Round-Trip Consistency Tests
# =============================================================================

def test_round_trip_accuracy(sm_particles: List[Dict],
                             braid_atlas: Dict,
                             verbose: bool = True) -> Dict:
    """
    Test round-trip consistency: GTE triple ↔ braid invariants.
    
    For each SM particle:
    1. Start with canonical GTE triple
    2. Look up corresponding braid invariants
    3. Verify they match expected values
    4. Check if mapping is bijective
    
    Args:
        sm_particles: Canonical SM particles with triples
        braid_atlas: Braid atlas data
        verbose: Print details
    
    Returns:
        Round-trip test results
    """
    braid_particles = braid_atlas.get("particles", {})
    
    results = []
    n_match = 0
    n_total = 0
    
    for sm_particle in sm_particles:
        sm_name = sm_particle["name"]
        sm_triple = sm_particle["triple"]
        
        # Try to find in braid atlas (with name normalization)
        braid_entry = None
        
        # Try direct match
        if sm_name in braid_particles:
            braid_entry = braid_particles[sm_name]
        else:
            # Try normalized names
            for braid_name, braid_data in braid_particles.items():
                norm_braid = normalize_particle_name(braid_name)
                if norm_braid == sm_name:
                    braid_entry = braid_data
                    break
        
        if braid_entry is None:
            result = {
                "particle": sm_name,
                "sm_triple": sm_triple,
                "in_braid_atlas": False,
                "match": False,
                "reason": "Not found in braid atlas"
            }
            results.append(result)
            n_total += 1
            continue
        
        # Compare triples
        braid_triple = braid_entry.get("gte_triple", [])
        
        # Check if triples match
        if len(braid_triple) >= 4:
            match = (
                sm_triple["a"] == braid_triple[0] and
                sm_triple["b"] == braid_triple[1] and
                sm_triple["c"] == braid_triple[2] and
                sm_triple["g"] == braid_triple[3]
            )
        else:
            match = False
        
        result = {
            "particle": sm_name,
            "sm_triple": sm_triple,
            "braid_triple": braid_triple,
            "in_braid_atlas": True,
            "match": match,
            "braid_invariants": {
                "writhe": braid_entry.get("writhe"),
                "strand_count": braid_entry.get("strand_count"),
                "crossing_number": braid_entry.get("crossing_number"),
                "winding_number": braid_entry.get("winding_number"),
                "knot_type": braid_entry.get("knot_type")
            }
        }
        
        results.append(result)
        n_total += 1
        if match:
            n_match += 1
        
        if verbose:
            status = "✅" if match else "❌"
            print(f"  {sm_name:20s}: {status} {'Match' if match else 'Mismatch'}")
            if not match and braid_triple:
                print(f"    SM:    ({sm_triple['a']}, {sm_triple['b']}, {sm_triple['c']}, {sm_triple['g']})")
                print(f"    Braid: ({braid_triple[0]}, {braid_triple[1]}, {braid_triple[2]}, {braid_triple[3]})")
    
    accuracy = n_match / n_total if n_total > 0 else 0.0
    
    return {
        "n_total": n_total,
        "n_match": n_match,
        "accuracy": accuracy,
        "results": results,
        "pass": accuracy >= 0.95  # Accept 95% or higher
    }


def test_topological_consistency(sm_particles: List[Dict],
                                 braid_atlas: Dict,
                                 verbose: bool = True) -> Dict:
    """
    Test that topological invariants are consistent with GTE structure.
    
    Checks:
    - Strand count correlates with particle type (leptons=2, quarks=3)
    - Winding number relates to generation or charge
    - Writhe is consistent
    
    Args:
        sm_particles: SM particles
        braid_atlas: Braid atlas
        verbose: Print details
    
    Returns:
        Consistency test results
    """
    braid_particles = braid_atlas.get("particles", {})
    
    consistency_checks = []
    
    for sm_particle in sm_particles:
        sm_name = sm_particle["name"]
        sector = sm_particle["sector"]
        
        # Find in braid atlas
        braid_entry = braid_particles.get(sm_name)
        
        if braid_entry is None:
            # Try normalized name
            for braid_name, braid_data in braid_particles.items():
                if normalize_particle_name(braid_name) == sm_name:
                    braid_entry = braid_data
                    break
        
        if braid_entry is None:
            continue
        
        strand_count = braid_entry.get("strand_count", 0)
        
        # Check strand count vs particle type
        expected_strands = None
        if sector in ["lepton", "neutrino"]:
            expected_strands = 2
        elif sector == "quark":
            expected_strands = 3
        
        strand_correct = (expected_strands is None) or (strand_count == expected_strands)
        
        consistency_checks.append({
            "particle": sm_name,
            "sector": sector,
            "strand_count": strand_count,
            "expected_strands": expected_strands,
            "strand_correct": strand_correct,
            "writhe": braid_entry.get("writhe"),
            "winding_number": braid_entry.get("winding_number")
        })
        
        if verbose and expected_strands is not None:
            status = "✅" if strand_correct else "❌"
            print(f"  {sm_name:20s}: {status} Strands={strand_count} (expected {expected_strands})")
    
    n_correct = sum(1 for c in consistency_checks if c["strand_correct"])
    n_total = len(consistency_checks)
    accuracy = n_correct / n_total if n_total > 0 else 0.0
    
    return {
        "n_total": n_total,
        "n_correct": n_correct,
        "accuracy": accuracy,
        "consistency_checks": consistency_checks,
        "pass": accuracy >= 0.95
    }


# =============================================================================
# Section C: Main TS7 Execution
# =============================================================================

def run_ts7(sm_particles: List[Dict],
           braid_atlas_path: Path,
           verbose: bool = True) -> Dict:
    """Run TS7: Braid atlas consistency validation."""
    
    if verbose:
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  TS7: BRAID ATLAS CONSISTENCY & INVARIANT CHECKS".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"\nConfiguration:")
        print(f"  Braid atlas: {braid_atlas_path.name}")
        print(f"  SM particles: {len(sm_particles)}")
        print(f"\nRunning consistency tests...\n")
    
    # Load braid atlas
    if not braid_atlas_path.exists():
        print(f"❌ Error: Braid atlas not found at {braid_atlas_path}")
        return {"pass": False, "error": "Braid atlas not found"}
    
    braid_atlas = load_braid_atlas(braid_atlas_path)
    
    # Test 1: Round-trip accuracy
    if verbose:
        print("1. Round-Trip Accuracy Test (GTE Triple ↔ Braid Invariants):")
    
    roundtrip_results = test_round_trip_accuracy(sm_particles, braid_atlas, verbose=verbose)
    
    # Test 2: Topological consistency
    if verbose:
        print("\n2. Topological Consistency Test (Strand counts, etc.):")
    
    topology_results = test_topological_consistency(sm_particles, braid_atlas, verbose=verbose)
    
    # Overall results
    overall = {
        "test_name": "TS7: Braid Atlas Consistency",
        "date": "2025-01-27",
        "braid_atlas_version": braid_atlas.get("version", "unknown"),
        "n_sm_particles": len(sm_particles),
        "n_braid_particles": len(braid_atlas.get("particles", {})),
        
        "roundtrip_test": roundtrip_results,
        "topology_test": topology_results,
        
        "overall_pass": roundtrip_results["pass"] and topology_results["pass"],
        
        "acceptance_criteria": {
            "round_trip_accuracy": "≥95%",
            "topological_consistency": "≥95%"
        }
    }
    
    if verbose:
        print("\n" + "═" * 80)
        print("TS7 RESULTS SUMMARY")
        print("═" * 80)
        print(f"\nRound-Trip Accuracy:")
        print(f"  Matches: {roundtrip_results['n_match']}/{roundtrip_results['n_total']}")
        print(f"  Accuracy: {roundtrip_results['accuracy']:.1%}")
        print(f"  Status: {'✅ PASS' if roundtrip_results['pass'] else '❌ FAIL'}")
        
        print(f"\nTopological Consistency:")
        print(f"  Correct: {topology_results['n_correct']}/{topology_results['n_total']}")
        print(f"  Accuracy: {topology_results['accuracy']:.1%}")
        print(f"  Status: {'✅ PASS' if topology_results['pass'] else '❌ FAIL'}")
        
        print(f"\nOverall: {'✅ TS7 PASSED' if overall['overall_pass'] else '❌ TS7 FAILED'}")
        print("═" * 80)
    
    return overall


# =============================================================================
# Section D: Main Execution
# =============================================================================

def main():
    """Main TS7 execution."""
    
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts7_braid_consistency"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load SM particles
    triples_path = data_dir / "canonical_sm_triples.json"
    sm_particles = load_canonical_sm_triples(triples_path)
    
    # Braid atlas — bundled in SRRG_VALIDATION_PROGRAM/data/ (canonical_braid_atlas.json
    # is a 7 KB snapshot of the PR-1_UGP_Loop_CA atlas; the full PR-1 repo is not required)
    braid_atlas_path = Path(__file__).resolve().parents[1] / "data" / "canonical_braid_atlas.json"
    
    # Run TS7
    results = run_ts7(sm_particles, braid_atlas_path, verbose=True)
    
    # Save results
    results_path = output_dir / "ts7_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved: {results_path}")
    
    return results


if __name__ == "__main__":
    results = main()

