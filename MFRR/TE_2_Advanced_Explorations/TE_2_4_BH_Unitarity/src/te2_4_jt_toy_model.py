#!/usr/bin/env python3
"""
TE_2.4 Phase 1: 1+1D JT-Like Gravity + Coherence Field

This module implements a simplified 1+1D dilaton gravity + Ψ field model
for black hole horizon dynamics. The 1+1D reduction makes the system
analytically tractable while preserving the essential physics.

Mathematical Setup:
    S = ∫ dx dt [φ R + (∇Ψ)² + V(Ψ)]
    
    where:
    - φ: dilaton field (plays role of radial coordinate)
    - R: 2D Ricci scalar
    - Ψ: coherence field (from TE_1.C)
    - V(Ψ): potential for Ψ

Why JT-like:
    - Reduces to ODEs/PDEs (analytically transparent)
    - Horizon is 0+1D (finite-dimensional Hilbert space)
    - Matches TE_1.L transducer structure naturally
    - Fits 10-core Mac easily

Cross-references:
    - TE_1.C: Einstein+Ψ+C framework
    - TE_1.L: Reflexive transducer dynamics
    - TE_2_X_6_IMPLEMENTATION_STRATEGY.md: Section "TE_2.4 Phase 1"

Author: TE_2 Implementation Team
Date: November 20, 2025
Status: Phase 1 - Initial Implementation
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from scipy.optimize import minimize


@dataclass(frozen=True)
class JTGravityConfig:
    """
    Configuration for 1+1D JT gravity + Ψ system
    
    All quantities in Planck units (ℏ = c = G = 1)
    """
    # Dilaton coupling
    dilaton_coupling: float = 1.0  # φ₀
    
    # Coherence field parameters
    psi_mass_squared: float = 0.1  # m_Ψ² (small for slow-roll)
    psi_coupling: float = 0.01  # λ_Ψ (weak self-interaction)
    
    # Black hole parameters
    bh_mass: float = 10.0  # M_BH in Planck masses
    
    # Numerical parameters
    spatial_points: int = 100  # Grid points in x
    time_points: int = 1000  # Time steps
    x_min: float = 0.1  # Minimum radius (regularization)
    x_max: float = 100.0  # Maximum radius (asymptotic)
    t_max: float = 100.0  # Maximum time
    
    # Integration tolerances
    rtol: float = 1e-8
    atol: float = 1e-10
    
    # Random seed for reproducibility
    seed: int = 1729


@dataclass
class JTGravityState:
    """
    State of the 1+1D JT gravity + Ψ system
    
    Fields:
        x: Spatial coordinate grid
        t: Time coordinate
        phi: Dilaton field φ(x,t)
        psi: Coherence field Ψ(x,t)
        metric: 2D metric components g_μν
        horizon_location: Position of apparent horizon
    """
    x: NDArray[np.float64]
    t: float
    phi: NDArray[np.float64]
    psi: NDArray[np.float64]
    metric: Dict[str, NDArray[np.float64]]
    horizon_location: Optional[float] = None


class JTGravityWithCoherence:
    """
    1+1D dilaton gravity + Ψ field system
    
    This implements a simplified black hole model where:
    - The horizon is effectively 0+1D (a point in space)
    - The Hilbert space is finite-dimensional
    - Dynamics reduce to coupled ODEs/PDEs
    
    The system is designed to be:
    1. Analytically tractable
    2. Numerically stable on 10-core Mac
    3. Compatible with TE_1.L transducer structure
    4. Suitable for GKSL extraction
    
    Usage:
        >>> config = JTGravityConfig(bh_mass=10.0)
        >>> jt = JTGravityWithCoherence(config)
        >>> state = jt.solve_background()
        >>> horizon = jt.find_horizon(state)
    """
    
    def __init__(self, config: JTGravityConfig):
        """
        Initialize JT gravity system
        
        Args:
            config: Configuration parameters
        """
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        
        # Set up spatial grid
        self.x_grid = np.linspace(
            config.x_min,
            config.x_max,
            config.spatial_points
        )
        self.dx = self.x_grid[1] - self.x_grid[0]
        
        # Set up time grid
        self.t_grid = np.linspace(0, config.t_max, config.time_points)
        self.dt = self.t_grid[1] - self.t_grid[0]
    
    def initial_conditions(self) -> Tuple[NDArray, NDArray]:
        """
        Set up initial conditions for φ and Ψ
        
        Initial state:
        - φ(x,0): Schwarzschild-like dilaton profile
        - Ψ(x,0): Small perturbation around vacuum
        
        Returns:
            (phi_0, psi_0): Initial field configurations
        """
        x = self.x_grid
        M = self.config.bh_mass
        
        # Dilaton: φ ~ x for x >> M, φ ~ M for x ~ M
        # Smooth interpolation: φ(x) = x * tanh(x/M)
        phi_0 = x * np.tanh(x / M)
        
        # Coherence field: small Gaussian perturbation
        # Ψ(x,0) = A * exp(-(x-x₀)²/σ²)
        x0 = 2 * M  # Peak outside horizon
        sigma = M / 2
        amplitude = 0.1
        psi_0 = amplitude * np.exp(-((x - x0) ** 2) / (2 * sigma ** 2))
        
        return phi_0, psi_0
    
    def schwarzschild_radius(self) -> float:
        """
        Compute Schwarzschild radius for given mass
        
        In 1+1D, the "horizon" is at r_H ~ 2M
        (analogous to 3+1D Schwarzschild)
        
        Returns:
            r_H: Horizon radius
        """
        return 2.0 * self.config.bh_mass
    
    def potential(self, psi: NDArray) -> NDArray:
        """
        Potential for coherence field V(Ψ)
        
        V(Ψ) = ½ m² Ψ² + ¼ λ Ψ⁴
        
        Args:
            psi: Coherence field values
        
        Returns:
            V(psi): Potential energy density
        """
        m2 = self.config.psi_mass_squared
        lam = self.config.psi_coupling
        return 0.5 * m2 * psi**2 + 0.25 * lam * psi**4
    
    def equations_of_motion(
        self,
        t: float,
        y: NDArray,
    ) -> NDArray:
        """
        Coupled equations of motion for φ and Ψ
        
        In 1+1D JT gravity with Ψ:
        
        ∂²φ/∂t² - ∂²φ/∂x² = -R φ - T_Ψ
        ∂²Ψ/∂t² - ∂²Ψ/∂x² = -dV/dΨ - coupling to φ
        
        where T_Ψ is the stress-energy of Ψ
        
        Args:
            t: Time
            y: State vector [φ, ∂φ/∂t, Ψ, ∂Ψ/∂t] flattened
        
        Returns:
            dy/dt: Time derivatives
        """
        n = len(self.x_grid)
        
        # Unpack state vector
        phi = y[0:n]
        phi_dot = y[n:2*n]
        psi = y[2*n:3*n]
        psi_dot = y[3*n:4*n]
        
        # Spatial derivatives (second-order finite differences)
        phi_xx = self._laplacian(phi)
        psi_xx = self._laplacian(psi)
        
        # Potential derivative
        dV_dpsi = (self.config.psi_mass_squared * psi + 
                   self.config.psi_coupling * psi**3)
        
        # Stress-energy of Ψ (simplified)
        T_psi = 0.5 * (psi_dot**2 + psi_xx**2) + self.potential(psi)
        
        # Ricci scalar (simplified for 1+1D)
        # R ≈ -∂²φ/∂x² / φ (dilaton-dependent curvature)
        R = -phi_xx / (phi + 1e-10)  # Regularize division
        
        # Equations of motion
        phi_ddot = phi_xx + R * phi + T_psi
        psi_ddot = psi_xx - dV_dpsi
        
        # Pack derivatives
        dy_dt = np.concatenate([phi_dot, phi_ddot, psi_dot, psi_ddot])
        
        return dy_dt
    
    def _laplacian(self, f: NDArray) -> NDArray:
        """
        Compute Laplacian ∂²f/∂x² using finite differences
        
        Uses second-order centered differences with boundary conditions
        
        Args:
            f: Field values on grid
        
        Returns:
            ∂²f/∂x²: Laplacian
        """
        f_xx = np.zeros_like(f)
        dx2 = self.dx ** 2
        
        # Interior points: centered difference
        f_xx[1:-1] = (f[2:] - 2*f[1:-1] + f[:-2]) / dx2
        
        # Boundary conditions: one-sided differences
        # Left boundary (x_min): Dirichlet (f_xx = 0)
        f_xx[0] = 0.0
        
        # Right boundary (x_max): Neumann (∂f/∂x = 0)
        f_xx[-1] = (f[-2] - 2*f[-1] + f[-1]) / dx2
        
        return f_xx
    
    def solve_background(
        self,
        t_eval: Optional[NDArray] = None,
    ) -> JTGravityState:
        """
        Solve background evolution of φ and Ψ
        
        Integrates coupled equations of motion from t=0 to t_max
        
        Args:
            t_eval: Times at which to evaluate solution (default: self.t_grid)
        
        Returns:
            Final state of the system
        
        Raises:
            RuntimeError: If integration fails
        """
        if t_eval is None:
            t_eval = self.t_grid
        
        # Initial conditions
        phi_0, psi_0 = self.initial_conditions()
        
        # Initial velocities (start at rest)
        phi_dot_0 = np.zeros_like(phi_0)
        psi_dot_0 = np.zeros_like(psi_0)
        
        # Pack initial state
        y0 = np.concatenate([phi_0, phi_dot_0, psi_0, psi_dot_0])
        
        # Solve IVP
        print(f"Solving JT gravity + Ψ from t=0 to t={self.config.t_max}...")
        sol = solve_ivp(
            self.equations_of_motion,
            t_span=(0, self.config.t_max),
            y0=y0,
            method='RK45',
            t_eval=t_eval,
            rtol=self.config.rtol,
            atol=self.config.atol,
            dense_output=True,
        )
        
        if not sol.success:
            raise RuntimeError(f"Integration failed: {sol.message}")
        
        # Extract final state
        n = len(self.x_grid)
        y_final = sol.y[:, -1]
        phi_final = y_final[0:n]
        psi_final = y_final[2*n:3*n]
        
        # Compute metric components
        # In 1+1D: ds² = -f(x) dt² + f(x)⁻¹ dx²
        # where f(x) = 1 - 2M/φ(x) (dilaton-dependent lapse)
        f = 1.0 - 2.0 * self.config.bh_mass / (phi_final + 1e-10)
        metric = {
            'g_tt': -f,
            'g_xx': 1.0 / (f + 1e-10),
        }
        
        state = JTGravityState(
            x=self.x_grid,
            t=sol.t[-1],
            phi=phi_final,
            psi=psi_final,
            metric=metric,
        )
        
        print(f"✓ Integration complete: t_final = {state.t:.2f}")
        
        return state
    
    def find_horizon(self, state: JTGravityState) -> float:
        """
        Locate apparent horizon in dilaton gravity
        
        The horizon is where g_tt = 0, i.e., f(x) = 0
        ⇒ φ(x_H) = 2M
        
        Args:
            state: Current state of the system
        
        Returns:
            x_H: Horizon location
        
        Raises:
            ValueError: If no horizon found
        """
        # Find where φ(x) = 2M
        target = 2.0 * self.config.bh_mass
        
        # Find crossing point
        phi = state.phi
        x = state.x
        
        # Look for sign change in (φ - 2M)
        diff = phi - target
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        
        if len(sign_changes) == 0:
            raise ValueError("No horizon found (φ never crosses 2M)")
        
        # Take first crossing (innermost horizon)
        i = sign_changes[0]
        
        # Linear interpolation for sub-grid accuracy
        x1, x2 = x[i], x[i+1]
        phi1, phi2 = phi[i], phi[i+1]
        x_H = x1 + (target - phi1) * (x2 - x1) / (phi2 - phi1)
        
        print(f"✓ Horizon located at x_H = {x_H:.4f} (target φ = {target:.2f})")
        
        return x_H
    
    def hawking_temperature(self, x_horizon: float) -> float:
        """
        Compute Hawking temperature at horizon
        
        In 1+1D JT gravity:
        T_H = κ / (2π)
        where κ is surface gravity
        
        For dilaton gravity: κ ≈ 1/(4M)
        
        Args:
            x_horizon: Horizon location
        
        Returns:
            T_H: Hawking temperature
        """
        # Surface gravity (simplified)
        kappa = 1.0 / (4.0 * self.config.bh_mass)
        T_H = kappa / (2.0 * np.pi)
        
        print(f"✓ Hawking temperature: T_H = {T_H:.6f}")
        
        return T_H
    
    def mode_frequencies(self, x_horizon: float, n_modes: int = 10) -> NDArray:
        """
        Compute near-horizon mode frequencies
        
        Modes are quantized oscillations near the horizon
        For harmonic oscillator approximation:
        ω_n = (n + 1/2) * ω_0
        
        where ω_0 ~ T_H (set by Hawking temperature)
        
        Args:
            x_horizon: Horizon location
            n_modes: Number of modes to compute
        
        Returns:
            Array of mode frequencies
        """
        T_H = self.hawking_temperature(x_horizon)
        omega_0 = 2.0 * np.pi * T_H  # Fundamental frequency
        
        # Harmonic oscillator spectrum
        n = np.arange(n_modes)
        omega_n = (n + 0.5) * omega_0
        
        return omega_n
    
    def save_state(self, state: JTGravityState, filepath: Path) -> None:
        """
        Save state to JSON file
        
        Args:
            state: State to save
            filepath: Output file path
        """
        data = {
            'x': state.x.tolist(),
            't': state.t,
            'phi': state.phi.tolist(),
            'psi': state.psi.tolist(),
            'metric': {k: v.tolist() for k, v in state.metric.items()},
            'horizon_location': state.horizon_location,
            'config': asdict(self.config),
        }
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ State saved to {filepath}")
    
    def load_state(self, filepath: Path) -> JTGravityState:
        """
        Load state from JSON file
        
        Args:
            filepath: Input file path
        
        Returns:
            Loaded state
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        state = JTGravityState(
            x=np.array(data['x']),
            t=data['t'],
            phi=np.array(data['phi']),
            psi=np.array(data['psi']),
            metric={k: np.array(v) for k, v in data['metric'].items()},
            horizon_location=data['horizon_location'],
        )
        
        print(f"✓ State loaded from {filepath}")
        
        return state


def main():
    """
    Test run of JT gravity + Ψ system
    """
    print("=" * 60)
    print("TE_2.4 Phase 1: 1+1D JT Gravity + Coherence Field")
    print("=" * 60)
    
    # Configuration
    config = JTGravityConfig(
        bh_mass=10.0,
        psi_mass_squared=0.1,
        spatial_points=100,
        time_points=100,
        t_max=50.0,
    )
    
    print("\nConfiguration:")
    print(f"  BH mass: {config.bh_mass} M_Planck")
    print(f"  Ψ mass²: {config.psi_mass_squared}")
    print(f"  Grid: {config.spatial_points} × {config.time_points}")
    print(f"  Time: 0 → {config.t_max}")
    
    # Initialize system
    jt = JTGravityWithCoherence(config)
    
    # Solve background
    print("\n" + "-" * 60)
    state = jt.solve_background()
    
    # Find horizon
    print("\n" + "-" * 60)
    x_H = jt.find_horizon(state)
    state.horizon_location = x_H
    
    # Compute Hawking temperature
    print("\n" + "-" * 60)
    T_H = jt.hawking_temperature(x_H)
    
    # Mode frequencies
    print("\n" + "-" * 60)
    omega = jt.mode_frequencies(x_H, n_modes=5)
    print(f"✓ Mode frequencies (first 5):")
    for i, w in enumerate(omega):
        print(f"    ω_{i} = {w:.6f}")
    
    # Save results
    print("\n" + "-" * 60)
    output_dir = Path(__file__).parent.parent / "results" / "jt_toy_model"
    jt.save_state(state, output_dir / "final_state.json")
    
    print("\n" + "=" * 60)
    print("✓ Phase 1 test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

