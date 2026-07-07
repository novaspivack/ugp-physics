"""
Field Data Structures for PR-0

Provides containers for field variables (ψ, χ, π) and history tracking.

Author: AI Assistant
Date: October 31, 2025
Session: 25.10
Reference: SESSION_25_9_PR0_COMPLETE_TECHNICAL_SPECIFICATION.md
"""

import numpy as np
from collections import deque
from typing import Optional
from .lattice import Lattice


class FieldState:
    """
    Complete state of PR-0 system.
    
    Contains:
    - Complex scalar field ψ (matter)
    - Real mediator field χ (force carrier)
    - Mediator momentum χ̇
    - History buffers
    """
    
    def __init__(self, lattice: Lattice, history_length: int = 20):
        """
        Initialize field state.
        
        Args:
            lattice: Lattice structure
            history_length: Number of past states to keep
        """
        self.lattice = lattice
        self.L_x = lattice.L_x
        self.L_y = lattice.L_y
        
        # Complex scalar field (matter)
        self.psi = np.zeros((self.L_y, self.L_x), dtype=np.complex128)
        
        # Real mediator field (force carrier)
        self.chi = np.zeros((self.L_y, self.L_x), dtype=np.float64)
        self.chi_dot = np.zeros((self.L_y, self.L_x), dtype=np.float64)
        
        # History buffers
        self.psi_history = deque(maxlen=history_length)
        self.chi_history = deque(maxlen=history_length)
        
        # Timestep counter
        self.timestep = 0
    
    def add_soliton(self, x0: float, y0: float, amplitude: float, width: float,
                    velocity_x: float = 0, velocity_y: float = 0, 
                    charge: int = +1):
        """
        Add a soliton (localized excitation) to ψ field.
        
        Args:
            x0, y0: Center position
            amplitude: Peak amplitude
            width: Spatial width
            velocity_x, velocity_y: Velocities
            charge: Topological charge (±1)
        """
        y, x = np.meshgrid(range(self.L_y), range(self.L_x), indexing='ij')
        
        # Compute distance (with PBC if enabled)
        dx = x - x0
        dy = y - y0

        periodic_x = getattr(self.lattice, "periodic_x", self.lattice.periodic)
        periodic_y = getattr(self.lattice, "periodic_y", self.lattice.periodic)

        if periodic_x:
            dx = np.where(
                np.abs(dx) > self.L_x / 2,
                dx - np.sign(dx) * self.L_x,
                dx,
            )
        if periodic_y:
            dy = np.where(
                np.abs(dy) > self.L_y / 2,
                dy - np.sign(dy) * self.L_y,
                dy,
            )
        
        r = np.sqrt(dx**2 + dy**2)
        
        # Soliton profile (sech envelope)
        rho = amplitude / np.cosh(r / width)
        
        # Phase (includes velocity and topological charge)
        theta = velocity_x * dx + velocity_y * dy + (np.pi if charge < 0 else 0)
        
        # Add to field (superposition)
        self.psi += rho * np.exp(1j * theta)
    
    def save_history(self):
        """Save current state to history buffers."""
        self.psi_history.append(self.psi.copy())
        self.chi_history.append(self.chi.copy())
    
    def clear_fields(self):
        """Reset all fields to zero."""
        self.psi.fill(0)
        self.chi.fill(0)
        self.chi_dot.fill(0)
    
    def get_density(self) -> np.ndarray:
        """Get |ψ|² (matter density)."""
        return np.abs(self.psi)**2
    
    def get_energy_density(self) -> np.ndarray:
        """Get total energy density (ψ + χ contributions)."""
        return np.abs(self.psi)**2 + self.chi**2
    
    def get_total_energy(self) -> float:
        """
        Compute total energy.
        
        E = ∫ (|ψ|² + |∇ψ|² + χ² + χ̇²) dx
        """
        # Kinetic (gradient) energy
        lap_psi = self.lattice.laplacian(self.psi)
        grad_energy = np.sum(np.abs(lap_psi)**2)
        
        # Field energy
        psi_energy = np.sum(np.abs(self.psi)**2)
        chi_energy = np.sum(self.chi**2)
        chi_dot_energy = np.sum(self.chi_dot**2)
        
        return float(psi_energy + 0.1*grad_energy + chi_energy + chi_dot_energy)
    
    def get_total_charge(self) -> float:
        """
        Compute total topological charge.
        
        Q = ∫ |ψ|² dx (for now, proper winding number later)
        """
        return float(np.sum(np.abs(self.psi)**2))
    
    def clip_fields(self, max_psi: float = 10.0, max_chi: float = 10.0):
        """
        Clip fields to prevent numerical overflow.
        
        Args:
            max_psi: Maximum |ψ|
            max_chi: Maximum |χ|
        """
        # Clip ψ magnitude while preserving phase
        psi_mag = np.abs(self.psi)
        self.psi = np.where(psi_mag > max_psi,
                           max_psi * self.psi / (psi_mag + 1e-10),
                           self.psi)
        
        # Clip χ and χ̇
        self.chi = np.clip(self.chi, -max_chi, max_chi)
        self.chi_dot = np.clip(self.chi_dot, -max_chi, max_chi)
    
    def __repr__(self):
        return (f"FieldState({self.L_x}×{self.L_y}, "
                f"|ψ|²_max={np.max(np.abs(self.psi)**2):.3f}, "
                f"E_total={self.get_total_energy():.3f})")


class ParameterSet:
    """
    Container for PR-0 parameters.
    
    Includes all tunable parameters for evolution and bootstrap.
    """
    
    def __init__(self):
        # Ablowitz-Ladik nonlinearity
        self.alpha = 0.5
        
        # Mediator coupling
        self.g = 0.1
        
        # Adaptive damping
        self.gamma_base = 0.013
        self.gamma_scale = 0.644
        
        # Force discovery (potential form)
        self.n = 1.0      # Power law
        self.beta = 0.1   # Cutoff scale
        
        # Gravity
        self.G = 0.06     # Gravitational coupling
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'alpha': self.alpha,
            'g': self.g,
            'gamma_base': self.gamma_base,
            'gamma_scale': self.gamma_scale,
            'n': self.n,
            'beta': self.beta,
            'G': self.G,
        }
    
    def from_dict(self, params: dict):
        """Load from dictionary."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f"ParameterSet(α={self.alpha:.3f}, g={self.g:.3f}, γ={self.gamma_base:.3f})"

