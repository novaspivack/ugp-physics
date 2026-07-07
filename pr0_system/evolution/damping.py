"""
Adaptive Damping for PR-0

Separation-dependent damping that enables binding by removing excess
kinetic energy from radial oscillations.

This is the "Track 1" effective thermostat - not fully UGP-native but
serves as coarse-grained thermalization.

Author: AI Assistant
Date: October 31, 2025  
Session: 25.10
Reference: SESSION_25_9_PR0_COMPLETE_TECHNICAL_SPECIFICATION.md §7
"""

import numpy as np
from scipy.ndimage import distance_transform_edt


class AdaptiveDamping:
    """
    Adaptive damping mechanism.
    
    Damping γ(x,y) depends on distance to nearest soliton:
      γ(x,y) = γ_base + γ_scale / (sep(x,y) + 1)
    
    where sep(x,y) = distance to nearest high-density region.
    
    Discovered values (Session 24):
      γ_base = 0.013
      γ_scale = 0.644
    """
    
    def __init__(self, gamma_base: float = 0.013, gamma_scale: float = 0.644,
                 threshold: float = 0.5):
        """
        Initialize adaptive damping.
        
        Args:
            gamma_base: Minimum damping rate
            gamma_scale: Separation-dependent scaling
            threshold: Density threshold for soliton detection
        """
        self.gamma_base = gamma_base
        self.gamma_scale = gamma_scale
        self.threshold = threshold
    
    def compute_damping_field(self, psi: np.ndarray) -> np.ndarray:
        """
        Compute spatially-varying damping field γ(x,y).
        
        Args:
            psi: Current ψ field
            
        Returns:
            γ field (same shape as ψ)
        """
        # Get density
        dens = np.abs(psi)**2
        
        # Binary mask: 1 where soliton, 0 elsewhere
        mask = (dens > self.threshold).astype(np.float64)
        
        # Distance transform (Euclidean distance to nearest 1)
        sep_map = distance_transform_edt(1.0 - mask)
        
        # Damping formula
        gamma = self.gamma_base + self.gamma_scale / (sep_map + 1.0)
        
        # Clip to prevent extreme values
        gamma = np.clip(gamma, self.gamma_base, 2.0)
        
        return gamma
    
    def apply(self, psi: np.ndarray, dt: float = 0.01) -> np.ndarray:
        """
        Apply damping to ψ field.
        
        dψ/dt ← dψ/dt - γ(x,y)·ψ
        
        Args:
            psi: Current ψ field
            dt: Timestep
            
        Returns:
            Damping term to add to dψ/dt
        """
        # Compute damping field
        gamma_field = self.compute_damping_field(psi)
        
        # Clip ψ for safety
        psi_safe = self._clip_psi(psi, max_val=10)
        
        # Damping term
        damping_term = -gamma_field * psi_safe
        
        return damping_term
    
    def _clip_psi(self, psi: np.ndarray, max_val: float) -> np.ndarray:
        """Clip ψ magnitude while preserving phase."""
        psi_mag = np.abs(psi)
        return np.where(psi_mag > max_val,
                       max_val * psi / (psi_mag + 1e-10),
                       psi)
    
    def __repr__(self):
        return f"AdaptiveDamping(γ_base={self.gamma_base:.3f}, γ_scale={self.gamma_scale:.3f})"


class UniversalDamping:
    """
    Universal (non-adaptive) damping.
    
    Simple exponential decay:
      dψ/dt = -γ·ψ
    
    Less effective for binding but simpler.
    """
    
    def __init__(self, gamma: float = 0.01):
        """
        Initialize universal damping.
        
        Args:
            gamma: Damping rate (constant everywhere)
        """
        self.gamma = gamma
    
    def apply(self, psi: np.ndarray, dt: float = 0.01) -> np.ndarray:
        """
        Apply universal damping.
        
        Args:
            psi: Current ψ field
            dt: Timestep
            
        Returns:
            Damping term to add to dψ/dt
        """
        psi_safe = self._clip_psi(psi, max_val=10)
        return -self.gamma * psi_safe
    
    def _clip_psi(self, psi: np.ndarray, max_val: float) -> np.ndarray:
        """Clip ψ magnitude while preserving phase."""
        psi_mag = np.abs(psi)
        return np.where(psi_mag > max_val,
                       max_val * psi / (psi_mag + 1e-10),
                       psi)
    
    def __repr__(self):
        return f"UniversalDamping(γ={self.gamma:.3f})"

