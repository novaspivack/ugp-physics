#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TE_2.3 Phase 2: Global Fixed Point Scanner

Reference: TE_2_3_KICKOFF.md, TE_2_X_6_IMPLEMENTATION_STRATEGY.md

This module implements a multi-metric fixed point scanner to search for
all fixed points in theory space and verify that the SM is the unique
stable fixed point.

Multi-Metric Approach:
1. Fisher metric (from TE_1.R)
2. MDL metric (description length)
3. RG-flow metric (natural gradient)
4. Canonical metric (flat coordinates)

Fixed Point Criteria:
- ∇C[k] = 0 (gradient vanishes)
- All physical eigenvalues of H positive (local minimum)
- Stable under perturbations

Author: Nova Spivack
Date: November 20, 2025
"""

from __future__ import annotations

import numpy as np
import jax
import jax.numpy as jnp
from jax import grad, jit
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from numpy.typing import NDArray
import time
import json
from pathlib import Path
from scipy.optimize import minimize, differential_evolution
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Import from Phase 1
import sys
sys.path.append(str(Path(__file__).parent.parent / "phase1_hessian"))
from te2_3_theory_space import TheorySpace, TheorySpaceConfig, TheoryPoint
from te2_3_hessian import LyapunovFunctional, HessianConfig
from te2_3_gauge_projection import GaugeGenerator, GaugeProjector, GaugeProjectionConfig

# Enable 64-bit precision in JAX
jax.config.update("jax_enable_x64", True)


@dataclass
class FixedPointScanConfig:
    """Configuration for fixed point scanning."""
    
    # Scan parameters
    n_random_starts: int = 100  # Number of random initial points
    n_grid_points: int = 10  # Grid points per dimension (for grid scan)
    use_random_scan: bool = True  # Use random initialization
    use_grid_scan: bool = True  # Use grid initialization
    
    # Optimization parameters
    gradient_threshold: float = 1e-4  # Threshold for ∇C = 0
    eigenvalue_threshold: float = 1e-6  # Threshold for positive definiteness
    max_iterations: int = 1000  # Max optimization iterations
    
    # Search bounds (as fraction of SM values)
    search_radius: float = 2.0  # Search within ±200% of SM values
    
    # Metrics to use
    use_fisher_metric: bool = True
    use_mdl_metric: bool = True
    use_rg_metric: bool = True
    use_canonical_metric: bool = True
    
    # Parallelization
    n_workers: int = 9  # Number of parallel workers
    
    # Output
    save_results: bool = True
    output_dir: Path = Path("results/phase2_fp_scan")


@dataclass
class FixedPointCandidate:
    """A candidate fixed point found during the scan."""
    k: NDArray[np.float64]  # Coordinates
    C: float  # Functional value
    grad_norm: float  # ||∇C||
    eigenvalues: NDArray[np.float64]  # Hessian eigenvalues (physical)
    is_minimum: bool  # All eigenvalues positive?
    is_sm: bool  # Is this the SM fixed point?
    distance_to_sm: float  # Distance from SM
    metric_used: str  # Which metric was used
    meta: Dict = field(default_factory=dict)


class FixedPointScanner:
    """
    Multi-metric fixed point scanner for theory space.
    """
    
    def __init__(self, theory_space: TheorySpace, config: FixedPointScanConfig):
        self.theory_space = theory_space
        self.config = config
        self.sm_fp = theory_space.get_sm_fixed_point()
        
        # Initialize functionals for each metric
        self._initialize_functionals()
        
        # Storage for found fixed points
        self.fixed_points: List[FixedPointCandidate] = []
        
        print(f"[FixedPointScanner] Initialized")
        print(f"  Theory space dimension: {self.sm_fp.dim}")
        print(f"  Search radius: ±{self.config.search_radius*100:.0f}% of SM values")
        print(f"  Random starts: {self.config.n_random_starts}")
        print(f"  Grid points: {self.config.n_grid_points}^{self.sm_fp.dim} = {self.config.n_grid_points**self.sm_fp.dim}")
        print(f"  Parallel workers: {self.config.n_workers}")
    
    def _initialize_functionals(self):
        """Initialize functionals for each metric."""
        print("\n[Functionals] Initializing...")
        
        # Canonical metric (Euclidean)
        hessian_config = HessianConfig(
            w_mdl=1.0,
            w_psc=10.0,
            w_rg=1.0,
            use_jax=True,
        )
        self.lyapunov_canonical = LyapunovFunctional(self.theory_space, hessian_config)
        self.grad_canonical = jit(grad(self.lyapunov_canonical))
        
        # Fisher metric (to be implemented)
        # For now, use canonical as placeholder
        self.lyapunov_fisher = self.lyapunov_canonical
        self.grad_fisher = self.grad_canonical
        
        # MDL metric (to be implemented)
        self.lyapunov_mdl = self.lyapunov_canonical
        self.grad_mdl = self.grad_canonical
        
        # RG-flow metric (to be implemented)
        self.lyapunov_rg = self.lyapunov_canonical
        self.grad_rg = self.grad_canonical
        
        print("[Functionals] ✓ Initialized")
    
    def _get_search_bounds(self) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Get search bounds for optimization."""
        k_sm = self.sm_fp.k
        r = self.config.search_radius
        
        # Bounds: k_sm ± r * |k_sm|
        lower = k_sm * (1.0 - r)
        upper = k_sm * (1.0 + r)
        
        # Ensure positive values for physical quantities
        lower = np.maximum(lower, 1e-6)
        
        return lower, upper
    
    def _generate_random_starts(self, n: int) -> List[NDArray[np.float64]]:
        """Generate random initial points for optimization."""
        lower, upper = self._get_search_bounds()
        
        starts = []
        for _ in range(n):
            k = np.random.uniform(lower, upper)
            starts.append(k)
        
        return starts
    
    def _generate_grid_starts(self) -> List[NDArray[np.float64]]:
        """Generate grid of initial points for optimization."""
        lower, upper = self._get_search_bounds()
        dim = self.sm_fp.dim
        n_grid = self.config.n_grid_points
        
        # Create 1D grids for each dimension
        grids_1d = [np.linspace(lower[i], upper[i], n_grid) for i in range(dim)]
        
        # Create meshgrid
        meshgrids = np.meshgrid(*grids_1d, indexing='ij')
        
        # Flatten and stack
        starts = np.stack([mg.flatten() for mg in meshgrids], axis=1)
        
        print(f"[Grid] Generated {len(starts)} grid points ({n_grid}^{dim})")
        
        # Subsample if too many
        max_grid_points = 10000
        if len(starts) > max_grid_points:
            indices = np.random.choice(len(starts), max_grid_points, replace=False)
            starts = starts[indices]
            print(f"[Grid] Subsampled to {len(starts)} points")
        
        return list(starts)
    
    def _optimize_to_fixed_point(self, k0: NDArray[np.float64], metric: str) -> Optional[FixedPointCandidate]:
        """
        Optimize from initial point k0 to find a fixed point.
        
        Args:
            k0: Initial point
            metric: Which metric to use ("canonical", "fisher", "mdl", "rg")
        
        Returns:
            FixedPointCandidate if found, None otherwise
        """
        # Select functional and gradient based on metric
        if metric == "canonical":
            func = self.lyapunov_canonical
            grad_func = self.grad_canonical
        elif metric == "fisher":
            func = self.lyapunov_fisher
            grad_func = self.grad_fisher
        elif metric == "mdl":
            func = self.lyapunov_mdl
            grad_func = self.grad_mdl
        elif metric == "rg":
            func = self.lyapunov_rg
            grad_func = self.grad_rg
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        # Define objective and gradient for scipy
        def objective(k):
            return float(func(jnp.array(k)))
        
        def gradient(k):
            return np.array(grad_func(jnp.array(k)))
        
        # Get bounds
        lower, upper = self._get_search_bounds()
        bounds = list(zip(lower, upper))
        
        # Optimize
        try:
            result = minimize(
                objective,
                k0,
                method='L-BFGS-B',
                jac=gradient,
                bounds=bounds,
                options={'maxiter': self.config.max_iterations, 'ftol': 1e-10}
            )
            
            if not result.success:
                return None
            
            k_opt = result.x
            C_opt = result.fun
            grad_norm = np.linalg.norm(gradient(k_opt))
            
            # Check if gradient is small enough
            if grad_norm > self.config.gradient_threshold:
                return None
            
            # Compute Hessian eigenvalues (physical subspace)
            eigenvalues_phys = self._compute_physical_eigenvalues(k_opt)
            
            # Check if all physical eigenvalues are positive
            is_minimum = np.all(eigenvalues_phys > self.config.eigenvalue_threshold)
            
            # Check if this is the SM
            distance_to_sm = np.linalg.norm(k_opt - self.sm_fp.k)
            is_sm = distance_to_sm < 0.1  # Within 10% of SM
            
            # Create candidate
            candidate = FixedPointCandidate(
                k=k_opt,
                C=C_opt,
                grad_norm=grad_norm,
                eigenvalues=eigenvalues_phys,
                is_minimum=is_minimum,
                is_sm=is_sm,
                distance_to_sm=distance_to_sm,
                metric_used=metric,
                meta={
                    "optimization_success": result.success,
                    "n_iterations": result.nit,
                }
            )
            
            return candidate
            
        except Exception as e:
            # Optimization failed
            return None
    
    def _compute_physical_eigenvalues(self, k: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Compute physical eigenvalues of Hessian at k.
        
        This is expensive, so we only do it for converged points.
        """
        # Import Hessian analyzer
        from te2_3_hessian import HessianAnalyzer, HessianConfig
        
        # Create temporary theory point
        temp_point = self.theory_space.create_point(k)
        
        # Compute Hessian
        hessian_config = HessianConfig(
            w_mdl=1.0,
            w_psc=10.0,
            w_rg=1.0,
            use_jax=True,
            save_results=False,  # Don't save intermediate results
        )
        
        # Create analyzer
        analyzer = HessianAnalyzer(self.theory_space, hessian_config)
        
        # Temporarily replace SM fixed point
        original_sm = analyzer.sm_fp
        analyzer.sm_fp = temp_point
        analyzer.lyapunov._k_sm = k
        
        # Compute Hessian
        H = analyzer.compute_hessian()
        
        # Restore original SM
        analyzer.sm_fp = original_sm
        analyzer.lyapunov._k_sm = original_sm.k
        
        # Project to physical subspace
        gauge_config = GaugeProjectionConfig(save_results=False)
        gauge_generator = GaugeGenerator(self.theory_space, gauge_config)
        projector = GaugeProjector(gauge_generator, gauge_config)
        projector.construct_projection_operator()
        projector.project_hessian(H)
        
        return projector.eigenvalues_physical
    
    def _scan_worker(self, args: Tuple) -> Optional[FixedPointCandidate]:
        """Worker function for parallel scanning."""
        k0, metric, worker_id = args
        
        # Optimize to fixed point
        candidate = self._optimize_to_fixed_point(k0, metric)
        
        return candidate
    
    def scan(self) -> List[FixedPointCandidate]:
        """
        Scan theory space for all fixed points using multiple metrics.
        
        Returns:
            List of fixed point candidates
        """
        print("\n" + "="*80)
        print("GLOBAL FIXED POINT SCAN")
        print("="*80 + "\n")
        
        # Generate initial points
        initial_points = []
        
        if self.config.use_random_scan:
            print(f"[Initialization] Generating {self.config.n_random_starts} random starts...")
            random_starts = self._generate_random_starts(self.config.n_random_starts)
            initial_points.extend(random_starts)
        
        if self.config.use_grid_scan:
            print(f"[Initialization] Generating grid starts...")
            grid_starts = self._generate_grid_starts()
            initial_points.extend(grid_starts)
        
        print(f"[Initialization] Total initial points: {len(initial_points)}")
        
        # Prepare tasks for each metric
        metrics = []
        if self.config.use_canonical_metric:
            metrics.append("canonical")
        if self.config.use_fisher_metric:
            metrics.append("fisher")
        if self.config.use_mdl_metric:
            metrics.append("mdl")
        if self.config.use_rg_metric:
            metrics.append("rg")
        
        print(f"[Metrics] Using {len(metrics)} metrics: {metrics}")
        
        # Create tasks: (k0, metric, worker_id)
        tasks = []
        for metric in metrics:
            for i, k0 in enumerate(initial_points):
                tasks.append((k0, metric, i))
        
        print(f"[Tasks] Total optimization tasks: {len(tasks)}")
        print(f"[Parallel] Using {self.config.n_workers} workers")
        
        # Run parallel optimization
        candidates = []
        t0 = time.time()
        
        with ProcessPoolExecutor(max_workers=self.config.n_workers) as executor:
            futures = {executor.submit(self._scan_worker, task): task for task in tasks}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 100 == 0:
                    elapsed = time.time() - t0
                    rate = completed / elapsed
                    remaining = len(tasks) - completed
                    eta = remaining / rate if rate > 0 else 0
                    print(f"[Progress] {completed}/{len(tasks)} ({100*completed/len(tasks):.1f}%) | "
                          f"Rate: {rate:.1f} tasks/s | ETA: {eta:.0f}s")
                
                try:
                    candidate = future.result()
                    if candidate is not None:
                        candidates.append(candidate)
                except Exception as e:
                    # Optimization failed, skip
                    pass
        
        t_total = time.time() - t0
        print(f"\n[Scan] Completed in {t_total:.1f}s")
        print(f"[Scan] Found {len(candidates)} candidate fixed points")
        
        # Cluster candidates to remove duplicates
        unique_candidates = self._cluster_candidates(candidates)
        
        print(f"[Clustering] {len(unique_candidates)} unique fixed points after clustering")
        
        self.fixed_points = unique_candidates
        return unique_candidates
    
    def _cluster_candidates(self, candidates: List[FixedPointCandidate], 
                           distance_threshold: float = 0.1) -> List[FixedPointCandidate]:
        """
        Cluster candidates to remove duplicates.
        
        Two candidates are considered the same if ||k1 - k2|| < threshold.
        """
        if len(candidates) == 0:
            return []
        
        # Sort by functional value (best first)
        candidates = sorted(candidates, key=lambda c: c.C)
        
        unique = []
        for candidate in candidates:
            # Check if this candidate is close to any existing unique candidate
            is_duplicate = False
            for unique_candidate in unique:
                distance = np.linalg.norm(candidate.k - unique_candidate.k)
                if distance < distance_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(candidate)
        
        return unique
    
    def analyze_results(self) -> Dict:
        """Analyze the found fixed points."""
        print("\n" + "="*80)
        print("FIXED POINT ANALYSIS")
        print("="*80 + "\n")
        
        if len(self.fixed_points) == 0:
            print("[Analysis] No fixed points found!")
            return {}
        
        # Classify fixed points
        minima = [fp for fp in self.fixed_points if fp.is_minimum]
        saddles = [fp for fp in self.fixed_points if not fp.is_minimum]
        sm_candidates = [fp for fp in self.fixed_points if fp.is_sm]
        
        print(f"[Classification]")
        print(f"  Total fixed points: {len(self.fixed_points)}")
        print(f"  Local minima: {len(minima)}")
        print(f"  Saddle points: {len(saddles)}")
        print(f"  SM candidates: {len(sm_candidates)}")
        
        # Analyze minima
        if len(minima) > 0:
            print(f"\n[Local Minima] Found {len(minima)} local minima:")
            for i, fp in enumerate(sorted(minima, key=lambda x: x.C)):
                print(f"\n  Minimum {i+1}:")
                print(f"    C = {fp.C:.6e}")
                print(f"    ||∇C|| = {fp.grad_norm:.6e}")
                print(f"    λ_min = {fp.eigenvalues.min():.6e}")
                print(f"    λ_max = {fp.eigenvalues.max():.6e}")
                print(f"    Distance to SM = {fp.distance_to_sm:.6e}")
                print(f"    Is SM? {fp.is_sm}")
                print(f"    Metric: {fp.metric_used}")
        
        # Check uniqueness
        is_unique = (len(minima) == 1) and (len(sm_candidates) == 1)
        
        print(f"\n[Uniqueness]")
        if is_unique:
            print(f"  ✓ SM is the UNIQUE stable fixed point!")
        else:
            print(f"  ✗ Found {len(minima)} local minima (expected 1)")
            if len(sm_candidates) == 0:
                print(f"  ✗ SM not found among fixed points!")
            elif len(sm_candidates) > 1:
                print(f"  ✗ Multiple SM candidates found!")
        
        # Store results
        results = {
            "n_fixed_points": len(self.fixed_points),
            "n_minima": len(minima),
            "n_saddles": len(saddles),
            "n_sm_candidates": len(sm_candidates),
            "is_unique": is_unique,
            "fixed_points": [
                {
                    "k": fp.k.tolist(),
                    "C": float(fp.C),
                    "grad_norm": float(fp.grad_norm),
                    "eigenvalues": fp.eigenvalues.tolist(),
                    "is_minimum": bool(fp.is_minimum),
                    "is_sm": bool(fp.is_sm),
                    "distance_to_sm": float(fp.distance_to_sm),
                    "metric_used": fp.metric_used,
                }
                for fp in self.fixed_points
            ]
        }
        
        return results
    
    def save_results(self, results: Dict):
        """Save scan results to file."""
        if not self.config.save_results:
            return
        
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save results
        results_file = output_dir / "fp_scan_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[Results] Saved to {results_file}")


def run_phase2():
    """Run Phase 2: Global fixed point scan."""
    print("\n" + "="*80)
    print("TE_2.3 PHASE 2: GLOBAL FIXED POINT SCAN")
    print("="*80 + "\n")
    
    # Configuration
    theory_config = TheorySpaceConfig(
        use_running_couplings=True,
        include_yukawa=True,
        include_ckm=False,
        include_pmns=False,
        gauge_normalization="canonical",
        higgs_parameterization="physical",
    )
    
    scan_config = FixedPointScanConfig(
        n_random_starts=50,  # Start with smaller number for testing
        n_grid_points=3,  # 3^8 = 6561 grid points
        use_random_scan=True,
        use_grid_scan=False,  # Disable grid for now (too many points)
        gradient_threshold=1e-3,
        eigenvalue_threshold=1e-6,
        max_iterations=500,
        search_radius=0.5,  # Search within ±50% of SM (smaller for testing)
        use_canonical_metric=True,
        use_fisher_metric=False,  # Disable for now (not implemented)
        use_mdl_metric=False,
        use_rg_metric=False,
        n_workers=9,
        save_results=True,
    )
    
    # Initialize theory space
    theory_space = TheorySpace(theory_config)
    
    # Initialize scanner
    scanner = FixedPointScanner(theory_space, scan_config)
    
    # Run scan
    fixed_points = scanner.scan()
    
    # Analyze results
    results = scanner.analyze_results()
    
    # Save results
    scanner.save_results(results)
    
    print("\n" + "="*80)
    print("✓ PHASE 2 SCAN COMPLETE")
    print("="*80 + "\n")
    
    return scanner, results


if __name__ == "__main__":
    scanner, results = run_phase2()

