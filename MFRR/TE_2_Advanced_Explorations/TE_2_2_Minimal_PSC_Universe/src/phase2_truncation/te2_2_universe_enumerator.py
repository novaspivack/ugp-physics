"""
TE_2.2 Phase 2: Universe Enumerator

Enumerates all candidate universes in a finite truncation of universe space.

Discretization:
- Dimension: d ∈ {2, 3, 4, 5, 6}
- Gauge group: {U(1), SU(2), SU(3), SU(2)xU(1), SU(3)xSU(2)xU(1), SU(5), SO(10)}
- Generations: n ∈ {1, 2, 3, 4}
- Observers: n_obs ∈ {0, 1}
- Lambda: Λ ∈ {0, 10^-122, 10^-60}
- Profit ratio: Gen/Drain ∈ {0.5, 1.0, 1.13, 1.5}

This creates a finite but comprehensive search space.

Cross-Reference:
- TE_2_2_1_KICKOFF.md (Phase 2: Finite Truncation)
- TE_1.Z_MIMINALITY_THEOREM (Dimensional selection)

Author: AI Assistant
Date: 2025-11-20
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase1_constraints'))

import numpy as np
from typing import List, Dict, Tuple
from itertools import product
from te2_2_constraint_base import UniverseParams


class UniverseSpace:
    """
    Defines the discretized universe parameter space.
    """
    
    def __init__(self):
        """Initialize universe space with discrete parameter ranges."""
        
        # Dimension (spacetime)
        self.dimensions = [2, 3, 4, 5, 6]
        
        # Gauge groups (representative sample)
        self.gauge_groups = [
            "U(1)",                      # Abelian
            "SU(2)",                     # Weak
            "SU(3)",                     # Strong
            "SU(2)xU(1)",               # Electroweak
            "SU(3)xSU(2)xU(1)",         # Standard Model ✓
            "SU(5)",                     # GUT
            "SO(10)",                    # GUT
        ]
        
        # Number of generations
        self.n_generations = [1, 2, 3, 4]
        
        # Number of observers
        self.n_observers = [0, 1]
        
        # Cosmological constant (Planck units)
        self.Lambda_values = [
            0.0,           # No dark energy
            1e-122,        # Observed value ✓
            1e-60,         # Too large
        ]
        
        # Information profit ratio (Gen/Drain)
        self.profit_ratios = [
            0.5,           # Below threshold (no observers)
            1.0,           # Near threshold
            1.13,          # Observed value ✓
            1.5,           # Above threshold
        ]
        
        # Spatial curvature
        self.kappa_values = [
            0.0,           # Flat (observed) ✓
            0.01,          # Slightly positive
            -0.01,         # Slightly negative
        ]
        
        # Topology
        self.topologies = ["flat", "hyperbolic"]
        
        print("Universe Space Initialized:")
        print(f"  Dimensions: {len(self.dimensions)}")
        print(f"  Gauge groups: {len(self.gauge_groups)}")
        print(f"  Generations: {len(self.n_generations)}")
        print(f"  Observers: {len(self.n_observers)}")
        print(f"  Lambda values: {len(self.Lambda_values)}")
        print(f"  Profit ratios: {len(self.profit_ratios)}")
        print(f"  Kappa values: {len(self.kappa_values)}")
        print(f"  Topologies: {len(self.topologies)}")
        
        # Compute total size
        self.total_size = (
            len(self.dimensions) *
            len(self.gauge_groups) *
            len(self.n_generations) *
            len(self.n_observers) *
            len(self.Lambda_values) *
            len(self.profit_ratios) *
            len(self.kappa_values) *
            len(self.topologies)
        )
        
        print(f"\nTotal universe space size: {self.total_size:,}")
    
    def enumerate_all(self) -> List[UniverseParams]:
        """
        Enumerate all universes in the discretized space.
        
        Returns:
            List of UniverseParams objects
        """
        universes = []
        
        # Use itertools.product for Cartesian product
        for (d, gauge, n_gen, n_obs, Lambda, profit, kappa, topo) in product(
            self.dimensions,
            self.gauge_groups,
            self.n_generations,
            self.n_observers,
            self.Lambda_values,
            self.profit_ratios,
            self.kappa_values,
            self.topologies,
        ):
            # Create universe
            universe = UniverseParams(
                d=d,
                gauge_group=gauge,
                n_generations=n_gen,
                n_observers=n_obs,
                Lambda=Lambda,
                profit_ratio=profit,
                kappa=kappa,
                topology=topo,
            )
            
            universes.append(universe)
        
        return universes
    
    def enumerate_psc_only(self) -> List[UniverseParams]:
        """
        Enumerate only PSC universes (hard constraints satisfied).
        
        This is a filtered subset of all universes.
        
        Returns:
            List of PSC UniverseParams objects
        """
        from te2_2_constraint_aggregator import DissonanceFunctional
        
        D = DissonanceFunctional()
        all_universes = self.enumerate_all()
        
        psc_universes = [u for u in all_universes if D.is_psc_universe(u)]
        
        print(f"\nPSC Filtering:")
        print(f"  Total universes: {len(all_universes):,}")
        print(f"  PSC universes: {len(psc_universes):,}")
        print(f"  PSC fraction: {len(psc_universes)/len(all_universes)*100:.1f}%")
        
        return psc_universes
    
    def get_sm_universe(self) -> UniverseParams:
        """
        Get the Standard Model universe parameters.
        
        Returns:
            SM UniverseParams
        """
        return UniverseParams(
            d=4,
            gauge_group="SU(3)xSU(2)xU(1)",
            n_generations=3,
            n_observers=1,
            Lambda=1e-122,
            profit_ratio=1.13,
            kappa=0.0,
            topology="flat",
        )


class UniverseScanner:
    """
    Scans universe space to find global minimizer of D[Ψ].
    """
    
    def __init__(self, space: UniverseSpace):
        """
        Initialize scanner.
        
        Args:
            space: UniverseSpace to scan
        """
        self.space = space
        
        # Import dissonance functional
        from te2_2_constraint_aggregator import DissonanceFunctional
        self.D = DissonanceFunctional()
    
    def scan_all(self, psc_only: bool = False) -> Dict:
        """
        Scan all universes and find global minimizer.
        
        Args:
            psc_only: If True, only scan PSC universes
        
        Returns:
            Dictionary with scan results
        """
        print("\n" + "=" * 80)
        print("SCANNING UNIVERSE SPACE")
        print("=" * 80)
        
        # Enumerate universes
        if psc_only:
            print("\nMode: PSC universes only (hard constraints satisfied)")
            universes = self.space.enumerate_psc_only()
        else:
            print("\nMode: All universes")
            universes = self.space.enumerate_all()
        
        print(f"\nScanning {len(universes):,} universes...")
        
        # Compute dissonance for each
        results = []
        
        for i, universe in enumerate(universes):
            D_val = self.D.evaluate(universe)
            is_psc = self.D.is_psc_universe(universe)
            
            results.append({
                'universe': universe,
                'D': D_val,
                'is_psc': is_psc,
            })
            
            # Progress reporting
            if (i + 1) % 1000 == 0:
                print(f"  Progress: {i+1:,}/{len(universes):,} ({(i+1)/len(universes)*100:.1f}%)")
        
        print(f"✓ Scan complete: {len(results):,} universes evaluated")
        
        # Find global minimizer
        results_sorted = sorted(results, key=lambda x: x['D'])
        global_min = results_sorted[0]
        
        # Get SM for comparison
        sm = self.space.get_sm_universe()
        D_sm = self.D.evaluate(sm)
        
        # Find SM in results
        sm_result = None
        sm_rank = None
        for i, r in enumerate(results_sorted):
            if self._is_sm_universe(r['universe']):
                sm_result = r
                sm_rank = i + 1
                break
        
        # Statistics
        stats = {
            'total_universes': len(results),
            'psc_universes': sum(1 for r in results if r['is_psc']),
            'global_min': global_min,
            'sm_result': sm_result,
            'sm_rank': sm_rank,
            'D_sm': D_sm,
            'D_min': global_min['D'],
            'all_results': results_sorted,
        }
        
        return stats
    
    def _is_sm_universe(self, universe: UniverseParams) -> bool:
        """Check if universe is the Standard Model."""
        return (
            universe.d == 4 and
            universe.gauge_group == "SU(3)xSU(2)xU(1)" and
            universe.n_generations == 3 and
            universe.n_observers == 1 and
            abs(universe.Lambda - 1e-122) < 1e-130 and
            abs(universe.profit_ratio - 1.13) < 0.01 and
            abs(universe.kappa) < 0.01 and
            universe.topology == "flat"
        )
    
    def print_summary(self, stats: Dict) -> None:
        """
        Print scan summary.
        
        Args:
            stats: Statistics from scan_all()
        """
        print("\n" + "=" * 80)
        print("SCAN SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal universes scanned: {stats['total_universes']:,}")
        print(f"PSC universes: {stats['psc_universes']:,} ({stats['psc_universes']/stats['total_universes']*100:.1f}%)")
        
        print(f"\n{'='*80}")
        print("GLOBAL MINIMIZER")
        print("=" * 80)
        
        global_min = stats['global_min']
        print(f"\nDissonance: D[Ψ] = {global_min['D']:.6e}")
        print(f"PSC: {global_min['is_psc']}")
        print(f"\nParameters:")
        print(f"  Dimension: d = {global_min['universe'].d}")
        print(f"  Gauge group: {global_min['universe'].gauge_group}")
        print(f"  Generations: n = {global_min['universe'].n_generations}")
        print(f"  Observers: n_obs = {global_min['universe'].n_observers}")
        print(f"  Lambda: Λ = {global_min['universe'].Lambda:.2e}")
        print(f"  Profit ratio: {global_min['universe'].profit_ratio:.2f}")
        print(f"  Curvature: κ = {global_min['universe'].kappa:.2f}")
        print(f"  Topology: {global_min['universe'].topology}")
        
        print(f"\n{'='*80}")
        print("STANDARD MODEL UNIVERSE")
        print("=" * 80)
        
        if stats['sm_result']:
            print(f"\nDissonance: D[Ψ_SM] = {stats['D_sm']:.6e}")
            print(f"Rank: #{stats['sm_rank']:,} / {stats['total_universes']:,}")
            print(f"PSC: {stats['sm_result']['is_psc']}")
            
            # Check if SM is global minimizer
            if stats['sm_rank'] == 1:
                print("\n✓✓✓ SM IS THE GLOBAL MINIMIZER ✓✓✓")
            else:
                print(f"\n✗ SM is NOT the global minimizer (rank #{stats['sm_rank']})")
                print(f"  Dissonance gap: ΔD = {stats['D_sm'] - stats['D_min']:.6e}")
        else:
            print("\n✗ SM not found in scan (should not happen!)")
        
        # Top 10 universes
        print(f"\n{'='*80}")
        print("TOP 10 UNIVERSES (LOWEST DISSONANCE)")
        print("=" * 80)
        
        for i, r in enumerate(stats['all_results'][:10]):
            u = r['universe']
            is_sm = self._is_sm_universe(u)
            marker = " ← SM" if is_sm else ""
            print(f"\n{i+1}. D[Ψ] = {r['D']:.6e}{marker}")
            print(f"   d={u.d}, gauge={u.gauge_group}, n_gen={u.n_generations}, n_obs={u.n_observers}")
            print(f"   Λ={u.Lambda:.2e}, profit={u.profit_ratio:.2f}, PSC={r['is_psc']}")


def test_enumerator():
    """Test universe enumerator."""
    print("=" * 80)
    print("TESTING UNIVERSE ENUMERATOR")
    print("=" * 80)
    
    # Create space
    space = UniverseSpace()
    
    # Test enumeration
    print("\nEnumerating all universes...")
    universes = space.enumerate_all()
    print(f"✓ Enumerated {len(universes):,} universes")
    
    # Test PSC filtering
    print("\nFiltering to PSC universes...")
    psc_universes = space.enumerate_psc_only()
    print(f"✓ Found {len(psc_universes):,} PSC universes")
    
    # Test SM retrieval
    print("\nRetrieving SM universe...")
    sm = space.get_sm_universe()
    print(f"✓ SM: d={sm.d}, gauge={sm.gauge_group}, n_gen={sm.n_generations}")
    
    print("\n" + "=" * 80)
    print("ENUMERATOR TEST COMPLETE ✓")
    print("=" * 80)


if __name__ == "__main__":
    test_enumerator()

