#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TE_2.3 Phase 1: Theory Space Parameterization

Reference: TE_2_3_KICKOFF.md, TE_1.R_CONTINOUS_MODEL

This module defines the theory space coordinates for the Standard Model
and provides tools for navigating theory space.

Theory Space Coordinates (k):
- Gauge couplings: g_1, g_2, g_3 (U(1), SU(2), SU(3))
- Yukawa couplings: y_u, y_d, y_e (up, down, electron)
- Higgs parameters: λ, m_H^2
- CKM matrix elements (via Yukawa matrices)
- PMNS matrix elements (via neutrino Yukawa)
- θ_QCD (strong CP angle)

Total dimension: ~30-50 parameters (depending on parameterization)

For Phase 1, we focus on the gauge sector + Higgs:
- dim(k) ≈ 8 (minimal parameterization)
- k = [g_1, g_2, g_3, λ, m_H^2, y_t, y_b, y_tau]

Author: Nova Spivack
Date: November 20, 2025
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from numpy.typing import NDArray

# Physical constants (PDG 2024)
ALPHA_EM_MZ = 1.0 / 127.952  # α(M_Z)
ALPHA_S_MZ = 0.1179  # α_s(M_Z)
SIN2_THETA_W_MZ = 0.23122  # sin²θ_W(M_Z)
M_Z = 91.1876  # GeV
M_W = 80.379  # GeV
M_H = 125.10  # GeV (Higgs mass)
M_T = 172.76  # GeV (top quark mass)
V_EV = 246.22  # GeV (Higgs VEV)

# Derived quantities
G_FERMI = 1.1663787e-5  # GeV^-2 (Fermi constant)


@dataclass
class TheorySpaceConfig:
    """Configuration for theory space parameterization."""
    
    # Coordinate system
    use_running_couplings: bool = True  # Use RG-evolved couplings at M_Z
    include_yukawa: bool = True  # Include Yukawa couplings
    include_ckm: bool = False  # Include CKM matrix (Phase 3)
    include_pmns: bool = False  # Include PMNS matrix (Phase 3)
    include_theta_qcd: bool = False  # Include θ_QCD (Phase 3)
    
    # Gauge coupling convention
    gauge_normalization: str = "canonical"  # "canonical" or "guts"
    
    # Yukawa sector
    yukawa_parameterization: str = "mass_eigenstate"  # "mass_eigenstate" or "flavor"
    n_generations: int = 3
    
    # Higgs sector
    higgs_parameterization: str = "physical"  # "physical" (m_H, v) or "lagrangian" (λ, m²)


@dataclass
class TheoryPoint:
    """
    A point in theory space.
    
    Attributes:
        k: Coordinate vector in theory space
        labels: Human-readable labels for each coordinate
        physical_params: Dictionary of physical parameters
        meta: Metadata (e.g., RG scale, validity flags)
    """
    k: NDArray[np.float64]
    labels: List[str]
    physical_params: Dict[str, float] = field(default_factory=dict)
    meta: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        if len(self.k) != len(self.labels):
            raise ValueError(f"Dimension mismatch: k has {len(self.k)} components, labels has {len(self.labels)}")
    
    @property
    def dim(self) -> int:
        """Dimension of theory space."""
        return len(self.k)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "k": self.k.tolist(),
            "labels": self.labels,
            "physical_params": self.physical_params,
            "meta": self.meta,
        }


class TheorySpace:
    """
    Theory space for the Standard Model.
    
    This class provides:
    - Coordinate systems for theory space
    - Conversion between different parameterizations
    - Standard Model fixed point (SM_FP)
    - Gauge transformations and redundancies
    """
    
    def __init__(self, config: TheorySpaceConfig):
        self.config = config
        self._initialize_coordinates()
        self._initialize_sm_fixed_point()
    
    def _initialize_coordinates(self):
        """Initialize coordinate labels and dimension."""
        self.labels = []
        
        # Gauge sector (always included)
        self.labels.extend(["g_1", "g_2", "g_3"])
        
        # Higgs sector (always included)
        if self.config.higgs_parameterization == "physical":
            self.labels.extend(["m_H", "v"])
        else:  # lagrangian
            self.labels.extend(["lambda_H", "m_H_squared"])
        
        # Yukawa sector (optional)
        if self.config.include_yukawa:
            # For now, just include top, bottom, tau (3rd generation)
            self.labels.extend(["y_t", "y_b", "y_tau"])
        
        # CKM matrix (optional, Phase 3)
        if self.config.include_ckm:
            # 4 parameters: 3 angles + 1 phase
            self.labels.extend(["theta_12_ckm", "theta_13_ckm", "theta_23_ckm", "delta_ckm"])
        
        # PMNS matrix (optional, Phase 3)
        if self.config.include_pmns:
            # 4 parameters: 3 angles + 1 phase (ignoring Majorana phases)
            self.labels.extend(["theta_12_pmns", "theta_13_pmns", "theta_23_pmns", "delta_pmns"])
        
        # θ_QCD (optional, Phase 3)
        if self.config.include_theta_qcd:
            self.labels.append("theta_qcd")
        
        self.dim = len(self.labels)
        print(f"[TheorySpace] Initialized with dim = {self.dim}")
        print(f"[TheorySpace] Coordinates: {self.labels}")
    
    def _initialize_sm_fixed_point(self):
        """
        Initialize the Standard Model fixed point.
        
        This is the "observed" SM at M_Z, using PDG values.
        """
        k_sm = np.zeros(self.dim)
        physical_params = {}
        
        # Gauge couplings at M_Z
        # Convention: g_i = sqrt(4π α_i)
        # α_1 = (5/3) α_EM / cos²θ_W (GUT normalization)
        # α_2 = α_EM / sin²θ_W
        # α_3 = α_s
        
        cos2_theta_w = 1.0 - SIN2_THETA_W_MZ
        
        if self.config.gauge_normalization == "canonical":
            # Standard normalization
            alpha_1 = ALPHA_EM_MZ / cos2_theta_w
            alpha_2 = ALPHA_EM_MZ / SIN2_THETA_W_MZ
            alpha_3 = ALPHA_S_MZ
        else:  # guts
            # GUT normalization: multiply U(1) by sqrt(5/3)
            alpha_1 = (5.0 / 3.0) * ALPHA_EM_MZ / cos2_theta_w
            alpha_2 = ALPHA_EM_MZ / SIN2_THETA_W_MZ
            alpha_3 = ALPHA_S_MZ
        
        g_1 = np.sqrt(4.0 * np.pi * alpha_1)
        g_2 = np.sqrt(4.0 * np.pi * alpha_2)
        g_3 = np.sqrt(4.0 * np.pi * alpha_3)
        
        k_sm[0] = g_1
        k_sm[1] = g_2
        k_sm[2] = g_3
        
        physical_params["g_1"] = g_1
        physical_params["g_2"] = g_2
        physical_params["g_3"] = g_3
        physical_params["alpha_1"] = alpha_1
        physical_params["alpha_2"] = alpha_2
        physical_params["alpha_3"] = alpha_3
        
        # Higgs sector
        if self.config.higgs_parameterization == "physical":
            k_sm[3] = M_H
            k_sm[4] = V_EV
            physical_params["m_H"] = M_H
            physical_params["v"] = V_EV
            # Derived: λ = m_H² / (2 v²)
            lambda_h = M_H**2 / (2.0 * V_EV**2)
            physical_params["lambda_H"] = lambda_h
        else:  # lagrangian
            lambda_h = M_H**2 / (2.0 * V_EV**2)
            m_h_squared = -lambda_h * V_EV**2
            k_sm[3] = lambda_h
            k_sm[4] = m_h_squared
            physical_params["lambda_H"] = lambda_h
            physical_params["m_H_squared"] = m_h_squared
            physical_params["m_H"] = M_H
            physical_params["v"] = V_EV
        
        # Yukawa couplings (if included)
        if self.config.include_yukawa:
            # y = sqrt(2) m / v
            y_t = np.sqrt(2.0) * M_T / V_EV
            y_b = np.sqrt(2.0) * 4.18 / V_EV  # m_b(m_b) ≈ 4.18 GeV
            y_tau = np.sqrt(2.0) * 1.77686 / V_EV  # m_tau = 1.77686 GeV
            
            idx = 5
            k_sm[idx] = y_t
            k_sm[idx + 1] = y_b
            k_sm[idx + 2] = y_tau
            
            physical_params["y_t"] = y_t
            physical_params["y_b"] = y_b
            physical_params["y_tau"] = y_tau
        
        # CKM matrix (if included, Phase 3)
        if self.config.include_ckm:
            # PDG values (Wolfenstein parameterization)
            theta_12_ckm = np.arcsin(0.22650)  # λ ≈ 0.22650
            theta_13_ckm = np.arcsin(0.00361)  # A λ³ ≈ 0.00361
            theta_23_ckm = np.arcsin(0.04053)  # A λ² ≈ 0.04053
            delta_ckm = 1.196  # δ_CP ≈ 68.5° ≈ 1.196 rad
            
            idx = 5 if not self.config.include_yukawa else 8
            k_sm[idx:idx+4] = [theta_12_ckm, theta_13_ckm, theta_23_ckm, delta_ckm]
            
            physical_params["theta_12_ckm"] = theta_12_ckm
            physical_params["theta_13_ckm"] = theta_13_ckm
            physical_params["theta_23_ckm"] = theta_23_ckm
            physical_params["delta_ckm"] = delta_ckm
        
        # PMNS matrix (if included, Phase 3)
        if self.config.include_pmns:
            # PDG values (NuFIT 5.3)
            theta_12_pmns = np.arcsin(np.sqrt(0.304))  # sin²θ_12 ≈ 0.304
            theta_13_pmns = np.arcsin(np.sqrt(0.02225))  # sin²θ_13 ≈ 0.02225
            theta_23_pmns = np.arcsin(np.sqrt(0.573))  # sin²θ_23 ≈ 0.573
            delta_pmns = 1.36 * np.pi  # δ_CP ≈ 1.36π (NO)
            
            idx = 5
            if self.config.include_yukawa:
                idx += 3
            if self.config.include_ckm:
                idx += 4
            k_sm[idx:idx+4] = [theta_12_pmns, theta_13_pmns, theta_23_pmns, delta_pmns]
            
            physical_params["theta_12_pmns"] = theta_12_pmns
            physical_params["theta_13_pmns"] = theta_13_pmns
            physical_params["theta_23_pmns"] = theta_23_pmns
            physical_params["delta_pmns"] = delta_pmns
        
        # θ_QCD (if included, Phase 3)
        if self.config.include_theta_qcd:
            # Experimental bound: |θ_QCD| < 10^-10
            theta_qcd = 0.0  # Assume zero (strong CP problem)
            k_sm[-1] = theta_qcd
            physical_params["theta_qcd"] = theta_qcd
        
        # Create TheoryPoint
        self.sm_fixed_point = TheoryPoint(
            k=k_sm,
            labels=self.labels,
            physical_params=physical_params,
            meta={
                "name": "SM_FP",
                "scale": "M_Z",
                "M_Z": M_Z,
                "source": "PDG 2024",
            }
        )
        
        print(f"[TheorySpace] SM fixed point initialized:")
        print(f"  g_1 = {g_1:.6f}, g_2 = {g_2:.6f}, g_3 = {g_3:.6f}")
        print(f"  α_1(M_Z) = {alpha_1:.6e}, α_2(M_Z) = {alpha_2:.6e}, α_3(M_Z) = {alpha_3:.6e}")
        print(f"  m_H = {M_H:.2f} GeV, v = {V_EV:.2f} GeV, λ = {lambda_h:.6f}")
        if self.config.include_yukawa:
            print(f"  y_t = {y_t:.6f}, y_b = {y_b:.6f}, y_tau = {y_tau:.6f}")
    
    def get_sm_fixed_point(self) -> TheoryPoint:
        """Return the Standard Model fixed point."""
        return self.sm_fixed_point
    
    def create_point(self, k: NDArray[np.float64], **kwargs) -> TheoryPoint:
        """Create a theory point from coordinates."""
        if len(k) != self.dim:
            raise ValueError(f"Expected {self.dim} coordinates, got {len(k)}")
        
        # Compute physical parameters from k
        physical_params = self._k_to_physical(k)
        
        return TheoryPoint(
            k=k,
            labels=self.labels,
            physical_params=physical_params,
            meta=kwargs,
        )
    
    def _k_to_physical(self, k: NDArray[np.float64]) -> Dict[str, float]:
        """Convert theory space coordinates to physical parameters."""
        params = {}
        
        # Gauge couplings
        g_1, g_2, g_3 = k[0], k[1], k[2]
        params["g_1"] = g_1
        params["g_2"] = g_2
        params["g_3"] = g_3
        params["alpha_1"] = g_1**2 / (4.0 * np.pi)
        params["alpha_2"] = g_2**2 / (4.0 * np.pi)
        params["alpha_3"] = g_3**2 / (4.0 * np.pi)
        
        # Higgs sector
        if self.config.higgs_parameterization == "physical":
            m_H, v = k[3], k[4]
            params["m_H"] = m_H
            params["v"] = v
            params["lambda_H"] = m_H**2 / (2.0 * v**2)
        else:
            lambda_h, m_h_squared = k[3], k[4]
            params["lambda_H"] = lambda_h
            params["m_H_squared"] = m_h_squared
            v = np.sqrt(-m_h_squared / lambda_h)
            params["v"] = v
            params["m_H"] = np.sqrt(2.0 * lambda_h * v**2)
        
        # Yukawa couplings
        if self.config.include_yukawa:
            idx = 5
            params["y_t"] = k[idx]
            params["y_b"] = k[idx + 1]
            params["y_tau"] = k[idx + 2]
        
        return params
    
    def distance(self, k1: NDArray[np.float64], k2: NDArray[np.float64], 
                 metric: str = "euclidean") -> float:
        """
        Compute distance between two points in theory space.
        
        Args:
            k1, k2: Theory space coordinates
            metric: Distance metric ("euclidean", "fisher", "mdl")
        
        Returns:
            Distance d(k1, k2)
        """
        if metric == "euclidean":
            return float(np.linalg.norm(k1 - k2))
        elif metric == "fisher":
            # Fisher metric (to be implemented in Phase 1)
            raise NotImplementedError("Fisher metric not yet implemented")
        elif metric == "mdl":
            # MDL metric (to be implemented in Phase 2)
            raise NotImplementedError("MDL metric not yet implemented")
        else:
            raise ValueError(f"Unknown metric: {metric}")


def test_theory_space():
    """Test theory space initialization and SM fixed point."""
    print("\n" + "="*80)
    print("Testing Theory Space")
    print("="*80 + "\n")
    
    # Minimal configuration (gauge + Higgs + Yukawa)
    config = TheorySpaceConfig(
        use_running_couplings=True,
        include_yukawa=True,
        include_ckm=False,
        include_pmns=False,
        gauge_normalization="canonical",
        higgs_parameterization="physical",
    )
    
    theory_space = TheorySpace(config)
    
    # Get SM fixed point
    sm_fp = theory_space.get_sm_fixed_point()
    
    print("\n[Test 1] SM Fixed Point")
    print(f"  Dimension: {sm_fp.dim}")
    print(f"  Coordinates: {sm_fp.k}")
    print(f"  Labels: {sm_fp.labels}")
    print(f"  Physical parameters:")
    for key, val in sm_fp.physical_params.items():
        print(f"    {key} = {val:.6e}")
    
    # Test distance
    k_perturbed = sm_fp.k + 0.01 * np.random.randn(sm_fp.dim)
    dist = theory_space.distance(sm_fp.k, k_perturbed)
    print(f"\n[Test 2] Distance to perturbed point: {dist:.6e}")
    
    # Test point creation
    k_test = sm_fp.k.copy()
    k_test[0] *= 1.1  # Perturb g_1 by 10%
    point_test = theory_space.create_point(k_test, name="Test Point")
    print(f"\n[Test 3] Created test point:")
    print(f"  g_1 = {point_test.physical_params['g_1']:.6f} (10% increase)")
    print(f"  α_1 = {point_test.physical_params['alpha_1']:.6e}")
    
    print("\n" + "="*80)
    print("✓ Theory Space Tests Passed")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_theory_space()

