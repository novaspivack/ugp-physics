#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TE_2.3 Phase 1: Hessian Computation at SM Fixed Point

Reference: TE_2_3_KICKOFF.md, TE_1.R_CONTINOUS_MODEL

This module computes the Hessian of the Lyapunov functional C[k]
at the Standard Model fixed point, identifies redundant directions
(gauge transformations, field redefinitions, GTE relabelings),
projects to the physical subspace, and verifies positive definiteness.

Lyapunov Functional (from TE_1.R):
    C[k] = ∫ d³x √g (R + ∇Ψ·∇Ψ + V(Ψ) + closure_penalty)

For SRRG, the functional is:
    F[T] = ∑_i w_i (∂_i T)² + λ * closure_penalty

where T is a theory in theory space, parameterized by k.

For the SM, we use a simplified functional:
    C[k] = MDL[k] + PSC_penalty[k] + RG_flow_penalty[k]

where:
- MDL[k] = description length of theory k
- PSC_penalty[k] = sum of squared closure violations
- RG_flow_penalty[k] = distance from RG fixed point

Hessian:
    H_ij = ∂²C/∂k_i∂k_j |_{k=k_SM}

Gauge Redundancies:
1. Quarter-Lock constraint: n·k = 0 (1 direction)
2. SU(3)×SU(2)×U(1) gauge transformations (8+3+1 = 12 directions)
3. Field redefinitions (~5 directions)
4. SL(2,ℤ) GTE relabelings (~2 directions)

Total redundant dimensions: ~20 (out of ~50 total)
Physical dimensions: ~30

Author: Nova Spivack
Date: November 20, 2025
"""

from __future__ import annotations

import numpy as np
import jax
import jax.numpy as jnp
from jax import grad, hessian, jit
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from numpy.typing import NDArray
import time
import json
from pathlib import Path

from te2_3_theory_space import TheorySpace, TheorySpaceConfig, TheoryPoint

# Enable 64-bit precision in JAX
jax.config.update("jax_enable_x64", True)


@dataclass
class HessianConfig:
    """Configuration for Hessian computation."""
    
    # Functional weights
    w_mdl: float = 1.0  # Weight for MDL term
    w_psc: float = 10.0  # Weight for PSC penalty
    w_rg: float = 1.0  # Weight for RG flow penalty
    
    # Numerical parameters
    epsilon: float = 1e-8  # Finite difference step (if needed)
    use_jax: bool = True  # Use JAX autodiff (recommended)
    
    # Gauge projection
    identify_redundancies: bool = True  # Identify gauge redundancies
    project_to_physical: bool = True  # Project Hessian to physical subspace
    eigenvalue_threshold: float = 1e-6  # Threshold for zero eigenvalues
    
    # Output
    save_results: bool = True
    output_dir: Path = Path("results/phase1_hessian")


class LyapunovFunctional:
    """
    Lyapunov functional for SRRG in theory space.
    
    This is a simplified version for the SM, combining:
    - MDL (Minimum Description Length)
    - PSC (Perfect Self-Containment) penalty
    - RG flow penalty
    """
    
    def __init__(self, theory_space: TheorySpace, config: HessianConfig):
        self.theory_space = theory_space
        self.config = config
        self.sm_fp = theory_space.get_sm_fixed_point()
        
        # Cache for efficiency
        self._k_sm = self.sm_fp.k
        self._dim = self.sm_fp.dim
    
    def __call__(self, k: jnp.ndarray) -> float:
        """
        Evaluate the Lyapunov functional at theory point k.
        
        Args:
            k: Theory space coordinates (JAX array)
        
        Returns:
            C[k]: Functional value
        """
        # MDL term: description length
        mdl = self._compute_mdl(k)
        
        # PSC penalty: closure violations
        psc_penalty = self._compute_psc_penalty(k)
        
        # RG flow penalty: distance from fixed point
        rg_penalty = self._compute_rg_penalty(k)
        
        # Total functional
        C = (self.config.w_mdl * mdl + 
             self.config.w_psc * psc_penalty + 
             self.config.w_rg * rg_penalty)
        
        return C
    
    def _compute_mdl(self, k: jnp.ndarray) -> float:
        """
        Compute Minimum Description Length for theory k.
        
        MDL[k] = log(# parameters) + log(precision) + complexity_penalty
        
        For now, use a simple proxy:
            MDL[k] = ∑_i log(1 + k_i²)
        """
        return jnp.sum(jnp.log(1.0 + k**2))
    
    def _compute_psc_penalty(self, k: jnp.ndarray) -> float:
        """
        Compute PSC (Perfect Self-Containment) penalty.
        
        PSC requires all closure relations to be satisfied:
        - Gauge anomaly cancellation
        - Renormalizability
        - Unitarity
        - Lorentz invariance
        
        For now, use a simplified penalty based on:
        1. Gauge coupling unification (GUT-like)
        2. Higgs quartic coupling positivity
        3. Yukawa coupling hierarchy
        """
        penalty = 0.0
        
        # Extract gauge couplings
        g_1, g_2, g_3 = k[0], k[1], k[2]
        
        # Penalty 1: Gauge coupling unification at high scale
        # At M_GUT ~ 10^16 GeV, we expect g_1 ≈ g_2 ≈ g_3
        # This is a soft constraint (not exact in SM)
        # Penalty: (g_1 - g_2)² + (g_2 - g_3)² + (g_3 - g_1)²
        unification_penalty = ((g_1 - g_2)**2 + (g_2 - g_3)**2 + (g_3 - g_1)**2)
        penalty += 0.1 * unification_penalty  # Soft weight
        
        # Penalty 2: Higgs quartic coupling positivity
        # λ > 0 required for vacuum stability
        if self.theory_space.config.higgs_parameterization == "physical":
            m_H, v = k[3], k[4]
            lambda_h = m_H**2 / (2.0 * v**2)
        else:
            lambda_h = k[3]
        
        # Penalty if λ < 0 (vacuum instability)
        lambda_penalty = jnp.maximum(0.0, -lambda_h)**2
        penalty += 100.0 * lambda_penalty  # Strong penalty
        
        # Penalty 3: Yukawa coupling hierarchy
        # Expect y_t >> y_b >> y_tau (observed hierarchy)
        if self.theory_space.config.include_yukawa:
            y_t, y_b, y_tau = k[5], k[6], k[7]
            
            # Penalty if hierarchy is violated
            hierarchy_penalty = (jnp.maximum(0.0, y_b - y_t)**2 + 
                                 jnp.maximum(0.0, y_tau - y_b)**2)
            penalty += 10.0 * hierarchy_penalty
        
        return penalty
    
    def _compute_rg_penalty(self, k: jnp.ndarray) -> float:
        """
        Compute RG flow penalty: distance from SM fixed point.
        
        This measures how far k is from the observed SM.
        
        RG_penalty[k] = ||k - k_SM||²
        """
        k_sm_jax = jnp.array(self._k_sm)
        return jnp.sum((k - k_sm_jax)**2)


class HessianAnalyzer:
    """
    Compute and analyze the Hessian of the Lyapunov functional.
    """
    
    def __init__(self, theory_space: TheorySpace, config: HessianConfig):
        self.theory_space = theory_space
        self.config = config
        self.sm_fp = theory_space.get_sm_fixed_point()
        
        # Initialize Lyapunov functional
        self.lyapunov = LyapunovFunctional(theory_space, config)
        
        # Compile JAX functions
        if config.use_jax:
            print("[HessianAnalyzer] Compiling JAX functions...")
            self._grad_func = jit(grad(self.lyapunov))
            self._hessian_func = jit(hessian(self.lyapunov))
            print("[HessianAnalyzer] ✓ JAX functions compiled")
        
        # Results storage
        self.results = {}
    
    def compute_hessian(self) -> NDArray[np.float64]:
        """
        Compute the Hessian at the SM fixed point.
        
        Returns:
            H: Hessian matrix (dim × dim)
        """
        print("\n" + "="*80)
        print("Computing Hessian at SM Fixed Point")
        print("="*80 + "\n")
        
        k_sm_jax = jnp.array(self.sm_fp.k)
        
        # Compute functional value at SM
        C_sm = self.lyapunov(k_sm_jax)
        print(f"[Functional] C[k_SM] = {C_sm:.6e}")
        
        # Compute gradient at SM (should be ~0 at fixed point)
        t0 = time.time()
        grad_sm = self._grad_func(k_sm_jax)
        t_grad = time.time() - t0
        grad_norm = float(jnp.linalg.norm(grad_sm))
        print(f"[Gradient] ||∇C||_{'{k_SM}'} = {grad_norm:.6e} (computed in {t_grad:.3f}s)")
        
        if grad_norm > 1e-3:
            print(f"  ⚠ Warning: Gradient is large at SM fixed point!")
            print(f"  This suggests k_SM may not be a true fixed point of C[k].")
        
        # Compute Hessian at SM
        t0 = time.time()
        H_jax = self._hessian_func(k_sm_jax)
        t_hess = time.time() - t0
        H = np.array(H_jax)
        print(f"[Hessian] Computed {H.shape[0]}×{H.shape[1]} matrix in {t_hess:.3f}s")
        
        # Check symmetry
        symmetry_error = np.max(np.abs(H - H.T))
        print(f"[Hessian] Symmetry error: {symmetry_error:.6e}")
        
        # Symmetrize (numerical errors can break exact symmetry)
        H = 0.5 * (H + H.T)
        
        # Store results
        self.results["C_sm"] = float(C_sm)
        self.results["grad_sm"] = grad_sm.tolist()
        self.results["grad_norm"] = grad_norm
        self.results["H"] = H.tolist()
        self.results["H_shape"] = H.shape
        self.results["symmetry_error"] = float(symmetry_error)
        
        self.H = H
        return H
    
    def analyze_eigenvalues(self) -> Dict:
        """
        Analyze eigenvalues of the Hessian.
        
        Returns:
            eigenvalue_analysis: Dictionary with eigenvalues, eigenvectors, etc.
        """
        print("\n" + "="*80)
        print("Eigenvalue Analysis")
        print("="*80 + "\n")
        
        if not hasattr(self, 'H'):
            raise ValueError("Must compute Hessian first!")
        
        # Compute eigenvalues and eigenvectors
        t0 = time.time()
        eigenvalues, eigenvectors = np.linalg.eigh(self.H)
        t_eig = time.time() - t0
        
        print(f"[Eigenvalues] Computed in {t_eig:.3f}s")
        print(f"[Eigenvalues] Range: [{eigenvalues.min():.6e}, {eigenvalues.max():.6e}]")
        
        # Count positive, negative, zero eigenvalues
        n_positive = np.sum(eigenvalues > self.config.eigenvalue_threshold)
        n_negative = np.sum(eigenvalues < -self.config.eigenvalue_threshold)
        n_zero = np.sum(np.abs(eigenvalues) <= self.config.eigenvalue_threshold)
        
        print(f"[Eigenvalues] Positive: {n_positive}, Negative: {n_negative}, Zero: {n_zero}")
        
        # Print smallest and largest eigenvalues
        print(f"\n[Eigenvalues] Smallest 5:")
        for i in range(min(5, len(eigenvalues))):
            print(f"  λ_{i+1} = {eigenvalues[i]:.6e}")
        
        print(f"\n[Eigenvalues] Largest 5:")
        for i in range(max(0, len(eigenvalues)-5), len(eigenvalues)):
            print(f"  λ_{i+1} = {eigenvalues[i]:.6e}")
        
        # Check positive definiteness
        is_positive_definite = (n_negative == 0) and (n_zero == 0)
        print(f"\n[Positive Definiteness] {is_positive_definite}")
        
        if not is_positive_definite:
            print(f"  ⚠ Hessian is NOT positive definite!")
            print(f"  This suggests either:")
            print(f"    1. Gauge redundancies (expected)")
            print(f"    2. SM is not a local minimum (unexpected)")
        
        # Store results
        self.results["eigenvalues"] = eigenvalues.tolist()
        self.results["eigenvectors"] = eigenvectors.tolist()
        self.results["n_positive"] = int(n_positive)
        self.results["n_negative"] = int(n_negative)
        self.results["n_zero"] = int(n_zero)
        self.results["is_positive_definite"] = bool(is_positive_definite)
        
        self.eigenvalues = eigenvalues
        self.eigenvectors = eigenvectors
        
        return self.results
    
    def identify_redundancies(self) -> Dict:
        """
        Identify redundant directions (gauge transformations, etc.).
        
        Redundant directions correspond to near-zero eigenvalues.
        
        Returns:
            redundancy_analysis: Dictionary with redundant directions
        """
        print("\n" + "="*80)
        print("Identifying Redundant Directions")
        print("="*80 + "\n")
        
        if not hasattr(self, 'eigenvalues'):
            raise ValueError("Must analyze eigenvalues first!")
        
        # Find near-zero eigenvalues
        zero_mask = np.abs(self.eigenvalues) <= self.config.eigenvalue_threshold
        zero_indices = np.where(zero_mask)[0]
        n_redundant = len(zero_indices)
        
        print(f"[Redundancies] Found {n_redundant} near-zero eigenvalues")
        print(f"[Redundancies] Threshold: {self.config.eigenvalue_threshold:.6e}")
        
        # Extract redundant eigenvectors
        redundant_directions = self.eigenvectors[:, zero_indices]
        
        print(f"\n[Redundancies] Near-zero eigenvalues:")
        for i, idx in enumerate(zero_indices):
            print(f"  λ_{idx+1} = {self.eigenvalues[idx]:.6e}")
            
            # Analyze direction
            direction = redundant_directions[:, i]
            dominant_coords = np.argsort(np.abs(direction))[-3:][::-1]
            print(f"    Dominant coordinates:")
            for coord_idx in dominant_coords:
                label = self.sm_fp.labels[coord_idx]
                value = direction[coord_idx]
                print(f"      {label}: {value:.6f}")
        
        # Expected redundancies:
        # 1. Quarter-Lock: n·k = 0 (1 direction)
        # 2. Gauge transformations: SU(3)×SU(2)×U(1) (12 directions)
        # 3. Field redefinitions (~5 directions)
        # 4. GTE relabelings (~2 directions)
        # Total: ~20 directions
        
        print(f"\n[Redundancies] Expected ~20 redundant directions")
        print(f"[Redundancies] Found {n_redundant} redundant directions")
        
        if n_redundant < 15:
            print(f"  ⚠ Warning: Fewer redundancies than expected!")
            print(f"  This may indicate:")
            print(f"    1. Functional does not capture all gauge symmetries")
            print(f"    2. Numerical threshold is too strict")
        
        # Store results
        self.results["n_redundant"] = int(n_redundant)
        self.results["redundant_eigenvalues"] = self.eigenvalues[zero_indices].tolist()
        self.results["redundant_directions"] = redundant_directions.tolist()
        
        self.redundant_directions = redundant_directions
        self.n_redundant = n_redundant
        
        return self.results
    
    def project_to_physical(self) -> NDArray[np.float64]:
        """
        Project Hessian to physical subspace (orthogonal to redundancies).
        
        Returns:
            H_phys: Projected Hessian (dim_phys × dim_phys)
        """
        print("\n" + "="*80)
        print("Projecting to Physical Subspace")
        print("="*80 + "\n")
        
        if not hasattr(self, 'redundant_directions'):
            raise ValueError("Must identify redundancies first!")
        
        # Physical subspace: orthogonal complement of redundant directions
        # Use QR decomposition to find orthonormal basis
        
        # Full eigenvector matrix
        V = self.eigenvectors
        
        # Physical directions: eigenvectors with non-zero eigenvalues
        physical_mask = np.abs(self.eigenvalues) > self.config.eigenvalue_threshold
        physical_indices = np.where(physical_mask)[0]
        n_physical = len(physical_indices)
        
        print(f"[Physical Subspace] Dimension: {n_physical} (out of {self.sm_fp.dim})")
        
        # Physical eigenvectors
        V_phys = V[:, physical_indices]
        
        # Physical eigenvalues
        lambda_phys = self.eigenvalues[physical_indices]
        
        # Projected Hessian in physical subspace
        # H_phys = V_phys^T H V_phys = diag(λ_phys)
        H_phys = np.diag(lambda_phys)
        
        print(f"[Physical Hessian] Shape: {H_phys.shape}")
        print(f"[Physical Hessian] Eigenvalue range: [{lambda_phys.min():.6e}, {lambda_phys.max():.6e}]")
        
        # Check positive definiteness in physical subspace
        is_phys_positive_definite = np.all(lambda_phys > 0)
        print(f"[Physical Hessian] Positive definite: {is_phys_positive_definite}")
        
        if not is_phys_positive_definite:
            n_neg_phys = np.sum(lambda_phys < 0)
            print(f"  ⚠ Warning: {n_neg_phys} negative eigenvalues in physical subspace!")
            print(f"  This suggests SM is NOT a local minimum.")
        else:
            print(f"  ✓ SM is a local minimum in physical subspace!")
        
        # Store results
        self.results["n_physical"] = int(n_physical)
        self.results["physical_eigenvalues"] = lambda_phys.tolist()
        self.results["H_phys"] = H_phys.tolist()
        self.results["is_phys_positive_definite"] = bool(is_phys_positive_definite)
        
        self.H_phys = H_phys
        self.lambda_phys = lambda_phys
        self.V_phys = V_phys
        
        return H_phys
    
    def save_results(self):
        """Save results to JSON."""
        if not self.config.save_results:
            return
        
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main results
        results_file = output_dir / "hessian_analysis.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n[Results] Saved to {results_file}")
        
        # Save Hessian as numpy array
        np.save(output_dir / "hessian.npy", self.H)
        np.save(output_dir / "eigenvalues.npy", self.eigenvalues)
        np.save(output_dir / "eigenvectors.npy", self.eigenvectors)
        
        if hasattr(self, 'H_phys'):
            np.save(output_dir / "hessian_physical.npy", self.H_phys)
            np.save(output_dir / "eigenvalues_physical.npy", self.lambda_phys)
        
        print(f"[Results] Saved numpy arrays to {output_dir}")


def run_phase1():
    """Run Phase 1: Hessian computation and analysis."""
    print("\n" + "="*80)
    print("TE_2.3 PHASE 1: HESSIAN AT SM FIXED POINT")
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
    
    hessian_config = HessianConfig(
        w_mdl=1.0,
        w_psc=10.0,
        w_rg=1.0,
        use_jax=True,
        identify_redundancies=True,
        project_to_physical=True,
        eigenvalue_threshold=1e-6,
        save_results=True,
    )
    
    # Initialize theory space
    theory_space = TheorySpace(theory_config)
    
    # Initialize Hessian analyzer
    analyzer = HessianAnalyzer(theory_space, hessian_config)
    
    # Step 1: Compute Hessian
    H = analyzer.compute_hessian()
    
    # Step 2: Analyze eigenvalues
    analyzer.analyze_eigenvalues()
    
    # Step 3: Identify redundancies
    analyzer.identify_redundancies()
    
    # Step 4: Project to physical subspace
    H_phys = analyzer.project_to_physical()
    
    # Step 5: Save results
    analyzer.save_results()
    
    print("\n" + "="*80)
    print("✓ PHASE 1 COMPLETE")
    print("="*80 + "\n")
    
    # Summary
    print("\n[Summary]")
    print(f"  Theory space dimension: {theory_space.dim}")
    print(f"  Redundant dimensions: {analyzer.n_redundant}")
    print(f"  Physical dimensions: {analyzer.results['n_physical']}")
    print(f"  Positive definite (physical): {analyzer.results['is_phys_positive_definite']}")
    
    return analyzer


if __name__ == "__main__":
    analyzer = run_phase1()

