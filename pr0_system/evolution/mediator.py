"""
Mediator Field Evolution for PR-0

The mediator field χ (chi) represents force carriers:
- Strong force: Gluons
- EM: Photons
- Weak: W/Z bosons
- Gravity: Metric perturbations

Evolution: Klein-Gordon-like wave equation with source from ψ

Author: AI Assistant
Date: October 31, 2025
Session: 25.10
Reference: SESSION_25_9_PR0_COMPLETE_TECHNICAL_SPECIFICATION.md §6
"""

import numpy as np
from typing import Tuple


class MediatorField:
    """
    Mediator field (χ) evolution.
    
    Evolves via damped wave equation:
      ∂²χ/∂t² = ∇²χ + ρ_ψ - γ_χ·∂χ/∂t - m_χ²·χ
    
    where:
      ρ_ψ = |ψ|² (source from matter field)
      γ_χ = damping coefficient
      m_χ = effective mass (creates range cutoff)
    """
    
    def __init__(self, g: float = 0.1, gamma_chi: float = 0.1, m_chi: float = 0.0):
        """
        Initialize mediator field evolution.
        
        Args:
            g: Coupling strength (ψ-χ interaction)
            gamma_chi: Damping coefficient
            m_chi: Effective mass (Yukawa cutoff)
        """
        self.g = g
        self.gamma_chi = gamma_chi
        self.m_chi = m_chi
    
    def evolve(self, chi: np.ndarray, chi_dot: np.ndarray, psi: np.ndarray,
               dt: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """
        Evolve χ and χ̇ for one timestep.
        
        Args:
            chi: Current χ field
            chi_dot: Current ∂χ/∂t
            psi: Current ψ field (source)
            dt: Timestep
            
        Returns:
            (chi_new, chi_dot_new)
        """
        # Source term from ψ
        rho_psi = np.abs(psi)**2
        rho_psi_safe = np.clip(rho_psi, 0, 10)
        
        # Laplacian of χ
        lap_chi = self._laplacian(chi)
        
        # χ̈ = ∇²χ + ρ - γχ̇ - m²χ
        chi_ddot = (lap_chi + rho_psi_safe - 
                    self.gamma_chi * chi_dot - 
                    self.m_chi**2 * chi)
        
        # Update χ̇ and χ
        chi_dot_new = chi_dot + dt * chi_ddot
        chi_new = chi + dt * chi_dot_new
        
        # Clip for stability
        chi_new = np.clip(chi_new, -10, 10)
        chi_dot_new = np.clip(chi_dot_new, -10, 10)
        
        return chi_new, chi_dot_new
    
    def compute_force_on_psi(self, chi: np.ndarray, psi: np.ndarray) -> np.ndarray:
        """
        Compute force term that χ exerts on ψ.
        
        F_χ = -g·χ·ψ
        
        This is added to dψ/dt.
        
        Args:
            chi: Mediator field
            psi: Matter field
            
        Returns:
            Force term (complex)
        """
        chi_safe = np.clip(chi, -10, 10)
        psi_safe = self._clip_psi(psi, max_val=10)
        
        # Force term (imaginary for ψ evolution)
        force = -1j * self.g * chi_safe * psi_safe
        
        return force
    
    def _laplacian(self, field: np.ndarray) -> np.ndarray:
        """
        Discrete Laplacian (5-point stencil).
        
        ∇²f ≈ f_{i+1,j} + f_{i-1,j} + f_{i,j+1} + f_{i,j-1} - 4f_{i,j}
        """
        lap = (np.roll(field, 1, axis=0) +
               np.roll(field, -1, axis=0) +
               np.roll(field, 1, axis=1) +
               np.roll(field, -1, axis=1) -
               4 * field)
        return lap
    
    def _clip_psi(self, psi: np.ndarray, max_val: float) -> np.ndarray:
        """Clip ψ magnitude while preserving phase."""
        psi_mag = np.abs(psi)
        return np.where(psi_mag > max_val,
                       max_val * psi / (psi_mag + 1e-10),
                       psi)
    
    def __repr__(self):
        return f"MediatorField(g={self.g:.3f}, γ={self.gamma_chi:.3f}, m={self.m_chi:.3f})"

