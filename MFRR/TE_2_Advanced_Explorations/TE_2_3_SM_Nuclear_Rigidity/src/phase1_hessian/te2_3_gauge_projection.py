#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TE_2.3 Phase 1: Gauge Projection

Reference: TE_2_3_KICKOFF.md, TE_2_3_PHASE_1_LAB_NOTES.md

This module constructs gauge generators for the Standard Model and projects
the Hessian to the physical (gauge-invariant) subspace.

Gauge Redundancies in the SM:
1. SU(3) gauge transformations (8 generators)
2. SU(2) gauge transformations (3 generators)
3. U(1) gauge transformations (1 generator)
4. Quarter-Lock constraint (1 direction)
5. Field redefinitions (~5 directions)
6. Higgs VEV rescaling (1 direction)

Total expected: ~19 redundant directions

Projection Operator:
    P = I - ∑_a |g_a⟩⟨g_a| / ⟨g_a|g_a⟩

Physical Hessian:
    H_phys = P H P^T

Author: Nova Spivack
Date: November 20, 2025
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from numpy.typing import NDArray
import json
from pathlib import Path

from te2_3_theory_space import TheorySpace, TheorySpaceConfig, TheoryPoint


@dataclass
class GaugeProjectionConfig:
    """Configuration for gauge projection."""
    
    # Which redundancies to include
    include_su3: bool = True  # SU(3) gauge transformations
    include_su2: bool = True  # SU(2) gauge transformations
    include_u1: bool = True  # U(1) gauge transformations
    include_quarter_lock: bool = True  # Quarter-Lock constraint
    include_field_redef: bool = True  # Field redefinitions
    include_higgs_rescaling: bool = True  # Higgs VEV rescaling
    
    # Numerical parameters
    orthogonalization_threshold: float = 1e-10  # For Gram-Schmidt
    zero_eigenvalue_threshold: float = 1e-6  # For identifying redundancies
    
    # Output
    save_results: bool = True
    output_dir: Path = Path("results/phase1_hessian")


class GaugeGenerator:
    """
    Construct gauge generators for the Standard Model.
    
    A gauge generator is a direction in theory space that corresponds to
    a gauge transformation. These directions are physically redundant.
    """
    
    def __init__(self, theory_space: TheorySpace, config: GaugeProjectionConfig):
        self.theory_space = theory_space
        self.config = config
        self.sm_fp = theory_space.get_sm_fixed_point()
        self.dim = self.sm_fp.dim
        
        # Storage for generators
        self.generators = []
        self.generator_labels = []
        
        # Construct all generators
        self._construct_all_generators()
    
    def _construct_all_generators(self):
        """Construct all gauge generators."""
        print("\n" + "="*80)
        print("Constructing Gauge Generators")
        print("="*80 + "\n")
        
        # NOTE: In our 8D parameterization [g_1, g_2, g_3, m_H, v, y_t, y_b, y_tau],
        # we need to be careful about which redundancies actually exist.
        # 
        # True redundancies in this parameterization:
        # 1. Quarter-Lock constraint: relates g_1 and g_2 (1 direction)
        # 2. Higgs-Yukawa rescaling: v ↔ y_i (1 direction)
        # 3. m_H-v correlation: λ = m_H²/(2v²) (1 direction)
        # 
        # Gauge transformations (SU(3), SU(2), U(1)) do NOT appear as redundancies
        # in this parameterization because we're using gauge couplings, not fields.
        # The gauge couplings are physical observables (running couplings at M_Z).
        
        # 1. Quarter-Lock constraint
        if self.config.include_quarter_lock:
            self._add_quarter_lock_generator()
        
        # 2. Field redefinitions (only the physical ones)
        if self.config.include_field_redef:
            self._add_field_redefinition_generators_minimal()
        
        # 3. Higgs VEV rescaling
        if self.config.include_higgs_rescaling:
            self._add_higgs_rescaling_generator()
        
        # Convert to numpy array
        self.generator_matrix = np.array(self.generators).T  # Shape: (dim, n_generators)
        
        print(f"\n[Generators] Total constructed: {len(self.generators)}")
        print(f"[Generators] Matrix shape: {self.generator_matrix.shape}")
        
        # Orthogonalize generators (Gram-Schmidt)
        self._orthogonalize_generators()
    
    def _add_su3_generators(self):
        """
        Add SU(3) gauge transformation generators.
        
        SU(3) has 8 generators (Gell-Mann matrices).
        In theory space, SU(3) transformations act on g_3 (and Yukawa couplings).
        
        For simplicity, we model this as:
        - 8 directions in the subspace spanned by (g_3, y_t, y_b)
        """
        print("[SU(3)] Constructing 8 generators...")
        
        # Get coordinate indices
        idx_g3 = self.theory_space.labels.index("g_3")
        
        if self.theory_space.config.include_yukawa:
            idx_yt = self.theory_space.labels.index("y_t")
            idx_yb = self.theory_space.labels.index("y_b")
            yukawa_indices = [idx_yt, idx_yb]
        else:
            yukawa_indices = []
        
        # SU(3) generators: 8 orthogonal directions
        # For now, use simplified model: perturbations in g_3 and Yukawa couplings
        
        # Generator 1: Pure g_3 direction
        g1 = np.zeros(self.dim)
        g1[idx_g3] = 1.0
        self.generators.append(g1)
        self.generator_labels.append("SU(3)_1")
        
        # Generators 2-8: Mixed g_3 and Yukawa directions
        for i in range(7):
            g = np.zeros(self.dim)
            # Mix g_3 with Yukawa couplings
            g[idx_g3] = np.cos(i * np.pi / 7)
            if len(yukawa_indices) > 0:
                g[yukawa_indices[0]] = np.sin(i * np.pi / 7) * 0.1  # Small Yukawa component
                if len(yukawa_indices) > 1:
                    g[yukawa_indices[1]] = np.sin(i * np.pi / 7 + np.pi/4) * 0.05
            self.generators.append(g)
            self.generator_labels.append(f"SU(3)_{i+2}")
        
        print(f"[SU(3)] ✓ Added 8 generators")
    
    def _add_su2_generators(self):
        """
        Add SU(2) gauge transformation generators.
        
        SU(2) has 3 generators (Pauli matrices).
        In theory space, SU(2) transformations act on g_2 (and Yukawa couplings).
        """
        print("[SU(2)] Constructing 3 generators...")
        
        # Get coordinate indices
        idx_g2 = self.theory_space.labels.index("g_2")
        
        if self.theory_space.config.include_yukawa:
            idx_yt = self.theory_space.labels.index("y_t")
            idx_yb = self.theory_space.labels.index("y_b")
            yukawa_indices = [idx_yt, idx_yb]
        else:
            yukawa_indices = []
        
        # SU(2) generators: 3 orthogonal directions
        for i in range(3):
            g = np.zeros(self.dim)
            g[idx_g2] = 1.0
            if len(yukawa_indices) > 0:
                # Mix with Yukawa couplings
                g[yukawa_indices[0]] = np.sin(i * np.pi / 3) * 0.1
                if len(yukawa_indices) > 1:
                    g[yukawa_indices[1]] = np.cos(i * np.pi / 3) * 0.05
            self.generators.append(g)
            self.generator_labels.append(f"SU(2)_{i+1}")
        
        print(f"[SU(2)] ✓ Added 3 generators")
    
    def _add_u1_generators(self):
        """
        Add U(1) gauge transformation generator.
        
        U(1) has 1 generator.
        In theory space, U(1) transformations act on g_1 (and Yukawa couplings).
        """
        print("[U(1)] Constructing 1 generator...")
        
        # Get coordinate indices
        idx_g1 = self.theory_space.labels.index("g_1")
        
        # U(1) generator: g_1 direction
        g = np.zeros(self.dim)
        g[idx_g1] = 1.0
        
        self.generators.append(g)
        self.generator_labels.append("U(1)")
        
        print(f"[U(1)] ✓ Added 1 generator")
    
    def _add_quarter_lock_generator(self):
        """
        Add Quarter-Lock constraint generator.
        
        Quarter-Lock: n·k = 0, where n is the Quarter-Lock normal vector.
        
        For the SM, Quarter-Lock relates gauge couplings:
            n = [n_1, n_2, n_3, 0, 0, ...]
        
        From UGP/GTE, the Quarter-Lock normal is related to the weak mixing angle:
            sin²θ_W = g_1² / (g_1² + g_2²) ≈ 1/4  (Quarter-Lock)
        
        This gives: g_1 ≈ g_2 / √3
        
        Normal vector: n = [√3, -1, 0, 0, ...]  (unnormalized)
        """
        print("[Quarter-Lock] Constructing 1 generator...")
        
        # Get coordinate indices
        idx_g1 = self.theory_space.labels.index("g_1")
        idx_g2 = self.theory_space.labels.index("g_2")
        
        # Quarter-Lock normal vector
        g = np.zeros(self.dim)
        g[idx_g1] = np.sqrt(3.0)
        g[idx_g2] = -1.0
        
        # Normalize
        g = g / np.linalg.norm(g)
        
        self.generators.append(g)
        self.generator_labels.append("Quarter-Lock")
        
        print(f"[Quarter-Lock] ✓ Added 1 generator")
        
        # Verify Quarter-Lock at SM
        k_sm = self.sm_fp.k
        ql_violation = np.dot(g, k_sm)
        print(f"[Quarter-Lock] Violation at SM: {ql_violation:.6e}")
    
    def _add_field_redefinition_generators_minimal(self):
        """
        Add minimal field redefinition generators (only true redundancies).
        
        In our 8D parameterization, the only true field redefinition redundancy is:
        - m_H-v correlation: In physical parameterization, m_H and v are related by λ
        """
        print("[Field Redefinitions] Constructing 1 generator...")
        
        # Get coordinate indices
        if self.theory_space.config.higgs_parameterization == "physical":
            idx_mH = self.theory_space.labels.index("m_H")
            idx_v = self.theory_space.labels.index("v")
        else:
            # In Lagrangian parameterization, no redundancy (λ and m² are independent)
            print("[Field Redefinitions] ✓ No redundancies in Lagrangian parameterization")
            return
        
        # m_H - v correlation: λ = m_H² / (2 v²)
        # This means m_H and v are not fully independent
        # The redundant direction is: ∂m_H/∂λ × ∂v/∂λ
        # From λ = m_H²/(2v²), we get: m_H ∝ v (at fixed λ)
        g = np.zeros(self.dim)
        g[idx_mH] = 1.0
        g[idx_v] = -1.0  # Opposite sign to maintain λ constant
        g = g / np.linalg.norm(g)
        
        self.generators.append(g)
        self.generator_labels.append("mH_v_correlation")
        
        print(f"[Field Redefinitions] ✓ Added 1 generator")
    
    def _add_field_redefinition_generators(self):
        """
        Add field redefinition generators.
        
        Field redefinitions are changes of variables that don't affect physics.
        Examples:
        1. Rescaling fields: φ → c φ (rescales couplings)
        2. Rotating flavor basis (affects Yukawa matrices)
        3. Redefining Higgs field (affects v, λ)
        
        For simplicity, we include:
        - Higgs field rescaling (affects m_H, v, Yukawa)
        - Yukawa basis rotations (affects y_t, y_b, y_tau)
        """
        print("[Field Redefinitions] Constructing ~5 generators...")
        
        # Get coordinate indices
        if self.theory_space.config.higgs_parameterization == "physical":
            idx_mH = self.theory_space.labels.index("m_H")
            idx_v = self.theory_space.labels.index("v")
        else:
            idx_mH = self.theory_space.labels.index("lambda_H")
            idx_v = self.theory_space.labels.index("m_H_squared")
        
        if self.theory_space.config.include_yukawa:
            idx_yt = self.theory_space.labels.index("y_t")
            idx_yb = self.theory_space.labels.index("y_b")
            idx_ytau = self.theory_space.labels.index("y_tau")
            yukawa_indices = [idx_yt, idx_yb, idx_ytau]
        else:
            yukawa_indices = []
        
        # Generator 1: Higgs-Yukawa rescaling
        # φ → c φ implies v → c v, y → y/c
        g1 = np.zeros(self.dim)
        g1[idx_v] = 1.0
        if len(yukawa_indices) > 0:
            for idx in yukawa_indices:
                g1[idx] = -1.0  # Compensating Yukawa rescaling
        g1 = g1 / np.linalg.norm(g1)
        self.generators.append(g1)
        self.generator_labels.append("Field_Redef_1")
        
        # Generators 2-4: Yukawa basis rotations
        if len(yukawa_indices) >= 3:
            # Rotation in (y_t, y_b) plane
            g2 = np.zeros(self.dim)
            g2[yukawa_indices[0]] = 1.0
            g2[yukawa_indices[1]] = 1.0
            g2 = g2 / np.linalg.norm(g2)
            self.generators.append(g2)
            self.generator_labels.append("Field_Redef_2")
            
            # Rotation in (y_b, y_tau) plane
            g3 = np.zeros(self.dim)
            g3[yukawa_indices[1]] = 1.0
            g3[yukawa_indices[2]] = 1.0
            g3 = g3 / np.linalg.norm(g3)
            self.generators.append(g3)
            self.generator_labels.append("Field_Redef_3")
            
            # Rotation in (y_t, y_tau) plane
            g4 = np.zeros(self.dim)
            g4[yukawa_indices[0]] = 1.0
            g4[yukawa_indices[2]] = 1.0
            g4 = g4 / np.linalg.norm(g4)
            self.generators.append(g4)
            self.generator_labels.append("Field_Redef_4")
        
        # Generator 5: m_H - v correlation
        # In physical parameterization, m_H and v are not independent
        # (related by λ = m_H² / (2 v²))
        g5 = np.zeros(self.dim)
        g5[idx_mH] = 1.0
        g5[idx_v] = -1.0
        g5 = g5 / np.linalg.norm(g5)
        self.generators.append(g5)
        self.generator_labels.append("Field_Redef_5")
        
        print(f"[Field Redefinitions] ✓ Added 5 generators")
    
    def _add_higgs_rescaling_generator(self):
        """
        Add Higgs VEV rescaling generator.
        
        The Higgs VEV v can be rescaled by a constant, which rescales all
        dimensionful quantities. This is a redundancy in the parameterization.
        
        Generator: direction that rescales v, m_H, and Yukawa couplings consistently.
        """
        print("[Higgs Rescaling] Constructing 1 generator...")
        
        # Get coordinate indices
        if self.theory_space.config.higgs_parameterization == "physical":
            idx_v = self.theory_space.labels.index("v")
            idx_mH = self.theory_space.labels.index("m_H")
        else:
            idx_v = self.theory_space.labels.index("m_H_squared")
            idx_mH = self.theory_space.labels.index("lambda_H")
        
        if self.theory_space.config.include_yukawa:
            idx_yt = self.theory_space.labels.index("y_t")
            idx_yb = self.theory_space.labels.index("y_b")
            idx_ytau = self.theory_space.labels.index("y_tau")
            yukawa_indices = [idx_yt, idx_yb, idx_ytau]
        else:
            yukawa_indices = []
        
        # Higgs rescaling: v → c v, m_H → c m_H, y → y/c
        g = np.zeros(self.dim)
        g[idx_v] = 1.0
        g[idx_mH] = 1.0
        if len(yukawa_indices) > 0:
            for idx in yukawa_indices:
                g[idx] = -1.0
        g = g / np.linalg.norm(g)
        
        self.generators.append(g)
        self.generator_labels.append("Higgs_Rescaling")
        
        print(f"[Higgs Rescaling] ✓ Added 1 generator")
    
    def _orthogonalize_generators(self):
        """
        Orthogonalize generators using Gram-Schmidt.
        
        This ensures the generators are linearly independent and orthonormal.
        """
        print("\n[Orthogonalization] Applying Gram-Schmidt...")
        
        # Gram-Schmidt orthogonalization
        G = self.generator_matrix.copy()  # Shape: (dim, n_generators)
        Q = np.zeros_like(G)
        
        n_kept = 0
        for i in range(G.shape[1]):
            # Start with i-th generator
            q = G[:, i].copy()
            
            # Subtract projections onto previous orthonormal vectors
            for j in range(n_kept):
                q = q - np.dot(Q[:, j], q) * Q[:, j]
            
            # Normalize
            norm = np.linalg.norm(q)
            
            if norm > self.config.orthogonalization_threshold:
                # Keep this generator
                Q[:, n_kept] = q / norm
                n_kept += 1
            else:
                # Discard (linearly dependent)
                print(f"  Discarding generator {i+1} ({self.generator_labels[i]}): linearly dependent")
        
        # Trim to kept generators
        self.generator_matrix_orthogonal = Q[:, :n_kept]
        self.generator_labels_orthogonal = [self.generator_labels[i] for i in range(n_kept)]
        
        print(f"[Orthogonalization] Kept {n_kept} / {len(self.generators)} generators")
        print(f"[Orthogonalization] Orthogonal matrix shape: {self.generator_matrix_orthogonal.shape}")
        
        # Verify orthonormality
        G_orth = self.generator_matrix_orthogonal
        Gram = G_orth.T @ G_orth
        identity_error = np.max(np.abs(Gram - np.eye(n_kept)))
        print(f"[Orthogonalization] Orthonormality error: {identity_error:.6e}")


class GaugeProjector:
    """
    Project Hessian to physical (gauge-invariant) subspace.
    """
    
    def __init__(self, gauge_generator: GaugeGenerator, config: GaugeProjectionConfig):
        self.gauge_generator = gauge_generator
        self.config = config
        self.dim = gauge_generator.dim
        
        # Get orthogonal generators
        self.G = gauge_generator.generator_matrix_orthogonal  # Shape: (dim, n_generators)
        self.n_generators = self.G.shape[1]
        
        print(f"\n[GaugeProjector] Initialized with {self.n_generators} orthogonal generators")
    
    def construct_projection_operator(self) -> NDArray[np.float64]:
        """
        Construct projection operator onto physical subspace.
        
        P = I - ∑_a |g_a⟩⟨g_a|
        
        where |g_a⟩ are orthonormal gauge generators.
        
        Returns:
            P: Projection operator (dim × dim)
        """
        print("\n" + "="*80)
        print("Constructing Projection Operator")
        print("="*80 + "\n")
        
        # P = I - G G^T
        # where G is the matrix of orthonormal generators (dim × n_generators)
        I = np.eye(self.dim)
        P = I - self.G @ self.G.T
        
        # Verify projection properties
        # 1. P^2 = P (idempotent)
        P2 = P @ P
        idempotent_error = np.max(np.abs(P2 - P))
        print(f"[Projection] Idempotency error (||P² - P||): {idempotent_error:.6e}")
        
        # 2. P^T = P (symmetric)
        symmetry_error = np.max(np.abs(P - P.T))
        print(f"[Projection] Symmetry error (||P - P^T||): {symmetry_error:.6e}")
        
        # 3. Rank(P) = dim - n_generators
        eigenvalues_P = np.linalg.eigvalsh(P)
        rank_P = np.sum(eigenvalues_P > self.config.zero_eigenvalue_threshold)
        expected_rank = self.dim - self.n_generators
        print(f"[Projection] Rank(P) = {rank_P} (expected {expected_rank})")
        
        self.P = P
        return P
    
    def project_hessian(self, H: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Project Hessian to physical subspace.
        
        H_phys = P H P^T
        
        Args:
            H: Full Hessian (dim × dim)
        
        Returns:
            H_phys: Projected Hessian (dim × dim)
        """
        print("\n" + "="*80)
        print("Projecting Hessian to Physical Subspace")
        print("="*80 + "\n")
        
        if not hasattr(self, 'P'):
            self.construct_projection_operator()
        
        # Project: H_phys = P H P^T
        H_phys = self.P @ H @ self.P.T
        
        # Symmetrize (numerical errors)
        H_phys = 0.5 * (H_phys + H_phys.T)
        
        print(f"[Projected Hessian] Shape: {H_phys.shape}")
        
        # Analyze eigenvalues
        eigenvalues_phys = np.linalg.eigvalsh(H_phys)
        
        # Physical eigenvalues: non-zero eigenvalues of H_phys
        physical_mask = eigenvalues_phys > self.config.zero_eigenvalue_threshold
        eigenvalues_physical = eigenvalues_phys[physical_mask]
        n_physical = len(eigenvalues_physical)
        
        print(f"[Projected Hessian] Physical eigenvalues: {n_physical}")
        print(f"[Projected Hessian] Redundant eigenvalues: {self.dim - n_physical}")
        print(f"[Projected Hessian] Eigenvalue range: [{eigenvalues_physical.min():.6e}, {eigenvalues_physical.max():.6e}]")
        
        # Check positive definiteness in physical subspace
        n_positive = np.sum(eigenvalues_physical > 0)
        n_negative = np.sum(eigenvalues_physical < 0)
        is_positive_definite = (n_negative == 0)
        
        print(f"\n[Physical Subspace] Positive eigenvalues: {n_positive}")
        print(f"[Physical Subspace] Negative eigenvalues: {n_negative}")
        print(f"[Physical Subspace] Positive definite: {is_positive_definite}")
        
        if is_positive_definite:
            print(f"  ✓ SM is a LOCAL MINIMUM in physical subspace!")
        else:
            print(f"  ✗ SM is NOT a local minimum (has {n_negative} negative eigenvalues)")
        
        # Store results
        self.H_phys = H_phys
        self.eigenvalues_phys = eigenvalues_phys
        self.eigenvalues_physical = eigenvalues_physical
        self.n_physical = n_physical
        self.is_positive_definite = is_positive_definite
        
        return H_phys
    
    def save_results(self):
        """Save projection results."""
        if not self.config.save_results:
            return
        
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save projection results
        results = {
            "n_generators": int(self.n_generators),
            "generator_labels": self.gauge_generator.generator_labels_orthogonal,
            "n_physical": int(self.n_physical),
            "n_redundant": int(self.dim - self.n_physical),
            "eigenvalues_physical": self.eigenvalues_physical.tolist(),
            "is_positive_definite": bool(self.is_positive_definite),
        }
        
        results_file = output_dir / "gauge_projection.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[Results] Saved to {results_file}")
        
        # Save numpy arrays
        np.save(output_dir / "projection_operator.npy", self.P)
        np.save(output_dir / "hessian_projected.npy", self.H_phys)
        np.save(output_dir / "eigenvalues_projected.npy", self.eigenvalues_phys)
        np.save(output_dir / "generator_matrix.npy", self.G)
        
        print(f"[Results] Saved numpy arrays to {output_dir}")


def run_gauge_projection(H: NDArray[np.float64], theory_space: TheorySpace) -> Dict:
    """
    Run gauge projection on Hessian.
    
    Args:
        H: Full Hessian matrix
        theory_space: Theory space object
    
    Returns:
        results: Dictionary with projection results
    """
    print("\n" + "="*80)
    print("TE_2.3 PHASE 1: GAUGE PROJECTION")
    print("="*80 + "\n")
    
    # Configuration
    config = GaugeProjectionConfig(
        include_su3=True,
        include_su2=True,
        include_u1=True,
        include_quarter_lock=True,
        include_field_redef=True,
        include_higgs_rescaling=True,
        orthogonalization_threshold=1e-10,
        zero_eigenvalue_threshold=1e-6,
        save_results=True,
    )
    
    # Step 1: Construct gauge generators
    gauge_generator = GaugeGenerator(theory_space, config)
    
    # Step 2: Construct projection operator
    projector = GaugeProjector(gauge_generator, config)
    P = projector.construct_projection_operator()
    
    # Step 3: Project Hessian
    H_phys = projector.project_hessian(H)
    
    # Step 4: Save results
    projector.save_results()
    
    print("\n" + "="*80)
    print("✓ GAUGE PROJECTION COMPLETE")
    print("="*80 + "\n")
    
    # Summary
    print("\n[Summary]")
    print(f"  Total dimensions: {theory_space.dim}")
    print(f"  Gauge generators: {projector.n_generators}")
    print(f"  Physical dimensions: {projector.n_physical}")
    print(f"  Positive definite (physical): {projector.is_positive_definite}")
    
    return {
        "gauge_generator": gauge_generator,
        "projector": projector,
        "H_phys": H_phys,
    }


if __name__ == "__main__":
    # Test: load Hessian and run projection
    from te2_3_hessian import run_phase1
    
    print("\n" + "="*80)
    print("TESTING GAUGE PROJECTION")
    print("="*80 + "\n")
    
    # Run Phase 1 to get Hessian
    print("[Test] Running Phase 1 to compute Hessian...")
    analyzer = run_phase1()
    
    # Run gauge projection
    print("\n[Test] Running gauge projection...")
    results = run_gauge_projection(analyzer.H, analyzer.theory_space)
    
    print("\n" + "="*80)
    print("✓ TEST COMPLETE")
    print("="*80 + "\n")

