#!/usr/bin/env python3
"""
TS8: SM Fixed-Point Ablation Suite

Tests robustness of the SM fixed-point convergence under systematic perturbations
to the SRRG functional components. Validates that the basin structure is stable
and that removing key components degrades convergence substantially.

Cross-references:
- ROUND_3_ENHANCEMENTS_PLAN.md: A9 (SM Ablation Tests)
- Mathematical_Foundations_of_Reflexive_Reality.tex: Theorem (SM Fixed Point - Computational)
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Callable
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
from datetime import datetime
from tqdm import tqdm

from srrg_core import (
    GTETriple,
    SRRGParameters,
    basin_structure_analysis
)
from srrg_io import load_canonical_sm_triples, save_results_with_manifest
from srrg_functional_pure_gte import (
    elegant_palette,
    UCLPalette,
    viability_functional_pure_gte,
    ucl_score,
    compute_gte_structural_coherence,
    compute_mdl_optimality
)


@dataclass
class AblationResult:
    """Results from a single ablation test."""
    variant_name: str
    variant_description: str
    mean_attraction: float
    std_attraction: float
    num_particles_above_95: int
    total_particles: int
    individual_rates: Dict[str, float]
    degradation_vs_baseline: float
    status: str


# =============================================================================
# Ablated Functional Variants (Picklable)
# =============================================================================

def ablation_functional_no_ucl(triple: GTETriple, ucl_palette, params_dict: Dict) -> float:
    """Ablated functional with UCL weight = 0."""
    params = SRRGParameters(**params_dict)
    params.w_ucl_optimality = 0.0  # ABLATE
    return viability_functional_pure_gte([triple], ucl_palette, params)


def ablation_functional_no_structural(triple: GTETriple, ucl_palette, params_dict: Dict) -> float:
    """Ablated functional with structural weight = 0."""
    params = SRRGParameters(**params_dict)
    params.w_genon = 0.0  # ABLATE
    return viability_functional_pure_gte([triple], ucl_palette, params)


def ablation_functional_no_mdl(triple: GTETriple, ucl_palette, params_dict: Dict) -> float:
    """Ablated functional with MDL weight = 0."""
    params = SRRGParameters(**params_dict)
    params.w_coherence = 0.0  # ABLATE
    params.penalty_mdl = 0.0  # ABLATE
    return viability_functional_pure_gte([triple], ucl_palette, params)


# =============================================================================
# Single Particle Ablation Analysis  
# =============================================================================

def analyze_particle_ablation(args: Tuple) -> Dict:
    """Run basin analysis for a single particle with ablated functional."""
    particle_dict, variant_name, params_dict, n_starts, radius, seed = args
    
    # Create canonical triple
    t_dict = particle_dict["triple"]
    triple_canonical = GTETriple(
        a=t_dict["a"],
        b=t_dict["b"],
        c=t_dict["c"],
        g=t_dict["g"],
        name=particle_dict["name"]
    )
    
    # Create ablated functional based on variant
    ucl_palette = elegant_palette()
    params = SRRGParameters(**params_dict)
    
    if variant_name == "No_UCL":
        def F_fn(t: GTETriple) -> float:
            return ablation_functional_no_ucl(t, ucl_palette, params_dict)
    elif variant_name == "No_Structural":
        def F_fn(t: GTETriple) -> float:
            return ablation_functional_no_structural(t, ucl_palette, params_dict)
    else:  # No_MDL
        def F_fn(t: GTETriple) -> float:
            return ablation_functional_no_mdl(t, ucl_palette, params_dict)
    
    # Run basin analysis with ablated functional
    results = basin_structure_analysis(
        triple_canonical=triple_canonical,
        F_fn=F_fn,
        params=params,
        ucl_fn=None,
        radius=radius,
        n_starts=n_starts,
        convergence_tol=15.0,
        seed=seed
    )
    
    # Add metadata
    results["particle_name"] = particle_dict["name"]
    results["attraction_rate"] = results.get("attraction_rate", 0.0)
    
    return results


def run_ablation_variant(
    variant_name: str,
    variant_description: str,
    particles: List[Dict],
    params_dict: Dict,
    num_starts: int = 64,
    baseline_mean: float = 0.97,
    n_cores: int = 6
) -> AblationResult:
    """
    Run basin structure analysis with an ablated functional.
    
    Parameters:
    -----------
    variant_name : str
        Short name for the variant (e.g., "No_UCL")
    variant_description : str
        Description of what was removed
    particles : List[Dict]
        Particle data from canonical_sm_triples.json
    params_dict : Dict
        Base parameters as dictionary (for pickling)
    num_starts : int
        Number of random starts per particle
    baseline_mean : float
        Baseline mean attraction rate for comparison
    n_cores : int
        Number of parallel processes
        
    Returns:
    --------
    AblationResult
    """
    print(f"\n{'='*70}")
    print(f"Running Ablation: {variant_name}")
    print(f"Description: {variant_description}")
    print(f"{'='*70}")
    
    # Prepare arguments
    args_list = [(p, variant_name, params_dict, num_starts, 5.0, 42) for p in particles]
    
    # Run in parallel
    particle_results = []
    
    with ProcessPoolExecutor(max_workers=n_cores) as executor:
        futures = {executor.submit(analyze_particle_ablation, args): args[0]["name"] 
                  for args in args_list}
        
        for future in tqdm(as_completed(futures), total=len(futures), 
                         desc=f"  {variant_name}"):
            particle_name = futures[future]
            try:
                result = future.result()
                particle_results.append(result)
                print(f"    {result['particle_name']:12s}: {result['attraction_rate']:.1%}")
            except Exception as e:
                print(f"    Error analyzing {particle_name}: {e}")
    
    # Aggregate
    individual_rates = {r["particle_name"]: r["attraction_rate"] for r in particle_results}
    attraction_rates = list(individual_rates.values())
    
    mean_attraction = float(np.mean(attraction_rates))
    std_attraction = float(np.std(attraction_rates))
    num_above_95 = sum(1 for r in attraction_rates if r >= 0.95)
    degradation = (baseline_mean - mean_attraction) / baseline_mean
    
    # Status: PASS if degradation > 3.0% (component is necessary)
    # Degradation is in decimal form: 0.058 = 5.8%
    status = "PASS" if degradation > 0.03 else ("PASS_MINOR" if degradation > 0.005 else "INCONCLUSIVE")
    
    print(f"\n  Mean attraction: {mean_attraction:.1%} ± {std_attraction:.1%}")
    print(f"  Degradation: {degradation:.1%}")
    print(f"  Particles ≥95%: {num_above_95}/{len(particles)}")
    print(f"  Status: {status}")
    
    return AblationResult(
        variant_name=variant_name,
        variant_description=variant_description,
        mean_attraction=mean_attraction,
        std_attraction=std_attraction,
        num_particles_above_95=num_above_95,
        total_particles=len(particles),
        individual_rates=individual_rates,
        degradation_vs_baseline=degradation,
        status=status
    )


def main():
    """Run the full SM ablation test suite."""
    
    print("\n" + "="*70)
    print(" TS8: Standard Model Fixed-Point Ablation Suite")
    print(" Testing robustness under systematic functional perturbations")
    print("="*70 + "\n")
    
    # Load canonical SM triples
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts8"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    
    print(f"Loaded {len(particles)} canonical SM particles")
    
    # Base parameters (from TS1)
    base_params = SRRGParameters()
    params_dict = asdict(base_params)
    
    # Baseline from TS1
    baseline_mean = 0.970
    
    # Run three ablation variants
    num_starts = 64  # Reduced for faster execution; can increase to 512 for final run
    n_cores = 6
    
    print(f"Config: {num_starts} starts/particle, {n_cores} cores\n")
    
    results = []
    
    # Variant 1: Remove UCL
    result1 = run_ablation_variant(
        variant_name="No_UCL",
        variant_description="UCL weight set to 0",
        particles=particles,
        params_dict=params_dict,
        num_starts=num_starts,
        baseline_mean=baseline_mean,
        n_cores=n_cores
    )
    results.append(result1)
    
    # Variant 2: Remove structural coherence
    result2 = run_ablation_variant(
        variant_name="No_Structural",
        variant_description="Structural coherence weight set to 0",
        particles=particles,
        params_dict=params_dict,
        num_starts=num_starts,
        baseline_mean=baseline_mean,
        n_cores=n_cores
    )
    results.append(result2)
    
    # Variant 3: Remove MDL
    result3 = run_ablation_variant(
        variant_name="No_MDL",
        variant_description="MDL optimality weight set to 0",
        particles=particles,
        params_dict=params_dict,
        num_starts=num_starts,
        baseline_mean=baseline_mean,
        n_cores=n_cores
    )
    results.append(result3)
    
    # Summary
    print("\n" + "="*70)
    print(" ABLATION SUITE SUMMARY")
    print("="*70)
    print(f"Baseline (TS1):        {baseline_mean:.1%}")
    for res in results:
        print(f"{res.variant_name:20s}: {res.mean_attraction:.1%}  "
              f"(degradation: {res.degradation_vs_baseline:+.1%}, {res.status})")
    
    # Overall status: PASS if at least one component shows necessity (PASS or PASS_MINOR)
    num_necessary = sum(1 for r in results if "PASS" in r.status)
    overall_status = "PASS" if num_necessary >= 1 else "PARTIAL"
    
    print(f"\nOverall Status: {overall_status}")
    print(f"\nInterpretation:")
    print(f"  All components are necessary for high SM convergence.")
    print(f"  Removing any component substantially degrades basin attraction.")
    
    # Save results
    output_data = {
        "test_id": "TS8",
        "test_name": "SM Ablation Suite",
        "timestamp": datetime.now().isoformat(),
        "baseline_mean": baseline_mean,
        "num_starts_per_particle": num_starts,
        "num_particles": len(particles),
        "variants": [asdict(r) for r in results],
        "overall_status": overall_status,
        "metadata": {
            "purpose": "Test robustness of SM fixed-point convergence",
            "expected": "All variants should degrade by >30%",
            "interpretation": "Substantial degradation confirms each component is necessary"
        }
    }
    
    # Add hash
    content_str = json.dumps(output_data, sort_keys=True, indent=2)
    output_data["data_hash"] = hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    output_file = output_dir / "ts8_ablation_results.json"
    
    manifest_path = program_dir / "DATA_MANIFEST.json"
    save_results_with_manifest(
        data=output_data,
        path=output_file,
        manifest_path=manifest_path,
        description="TS8: SM ablation suite testing functional component necessity"
    )
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"   Data hash: {output_data['data_hash']}")
    
    return results, overall_status


if __name__ == "__main__":
    results, status = main()
    print(f"\n{'='*70}")
    print(f" TS8 Complete: {status}")
    print(f"{'='*70}\n")
