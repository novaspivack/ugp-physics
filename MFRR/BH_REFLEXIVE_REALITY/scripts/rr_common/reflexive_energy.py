#!/usr/bin/env python3
"""
Reflexive Energy Computations for Black Hole Tests

Implements Reflexive Landauer energy, stress tensors, and information tensors
for the BH1-BH4 validation suite.

Reference: MFRR Section 5 (Information-Gravity Coupling)
"""

import numpy as np

# Constants (geometric units)
K_BOLTZMANN = 1.0
HBAR = 1.0


def compute_reflexive_energy(Psi: np.ndarray, grad_Psi: np.ndarray, 
                             T_H: float, Delta_H: float, 
                             alpha1: float = 1e-6, alpha2: float = 1e-6,
                             lambda_Psi: float = 1.0) -> np.ndarray:
    """
    Compute Reflexive Landauer energy density.
    
    ΔE_PT = k_B T_H ΔH + λ_Ψ ∫(α₁Ψ² + α₂||∇Ψ||²)dV
    
    Args:
        Psi: Coherence field amplitude
        grad_Psi: Gradient of coherence field
        T_H: Hawking temperature
        Delta_H: Entropy change (informational cost)
        alpha1: Coupling for Ψ²
        alpha2: Coupling for ||∇Ψ||²
        lambda_Psi: Overall coupling strength
    
    Returns:
        E_PT: Reflexive energy density array
    """
    # Thermal component (Landauer)
    E_thermal = K_BOLTZMANN * T_H * Delta_H
    
    # Geometric component (coherence field energy)
    # Handle grad_Psi as array or list of components
    if isinstance(grad_Psi, (list, tuple)):
        grad_norm_sq = sum(g**2 for g in grad_Psi)
    else:
        grad_norm_sq = grad_Psi**2
    
    E_coherence = lambda_Psi * (alpha1 * Psi**2 + alpha2 * grad_norm_sq)
    
    return E_thermal + E_coherence


def compute_stress_tensor_psi(Psi: np.ndarray, grad_Psi: np.ndarray,
                               metric: dict, mu: float = 0.0, 
                               lambda_field: float = 0.0) -> dict:
    """
    Compute stress-energy tensor T^(Ψ)_μν for scalar field Ψ.
    
    T^(Ψ)_μν = ∇_μΨ∇_νΨ - g_μν[½∇^αΨ∇_αΨ + V(Ψ)]
    
    where V(Ψ) = ½μ²Ψ² + ¼λΨ⁴
    
    Args:
        Psi: Scalar field
        grad_Psi: Gradient components (dr, dtheta, dphi)
        metric: Metric components dict
        mu: Mass parameter
        lambda_field: Self-interaction coupling
    
    Returns:
        dict with T_tt, T_rr, T_theta_theta components
    """
    # Potential
    V = 0.5 * mu**2 * Psi**2 + 0.25 * lambda_field * Psi**4
    
    # Kinetic term (in Schwarzschild: only radial derivative contributes)
    grad_Psi_r = grad_Psi[0] if isinstance(grad_Psi, (list, tuple, np.ndarray)) else grad_Psi
    kinetic = 0.5 * metric['g_rr'] * grad_Psi_r**2
    
    # Stress tensor components
    T_tt = metric['g_tt'] * (kinetic + V)
    T_rr = grad_Psi_r**2 - metric['g_rr'] * (kinetic + V)
    T_theta_theta = -metric['g_theta_theta'] * (kinetic + V)
    
    return {
        'T_tt': T_tt,
        'T_rr': T_rr,
        'T_theta_theta': T_theta_theta,
        'rho': kinetic + V,  # Energy density
        'p_r': grad_Psi_r**2 - (kinetic + V),  # Radial pressure
    }


def compute_information_tensor(Psi: np.ndarray, grad_Psi: np.ndarray,
                               Omega: np.ndarray, metric: dict,
                               alpha1: float = 1e-6, alpha2: float = 1e-6,
                               lambda_Psi: float = 1.0) -> dict:
    """
    Compute information stress-energy tensor C_μν.
    
    C_μν = λ_Ψ[∇_μΨ∇_νΨ - g_μν(α₁Ψ² + α₂||∇Ψ||² + Ω)]
    
    Args:
        Psi: Coherence field
        grad_Psi: Gradient of Ψ
        Omega: Information density (fiber curvature)
        metric: Metric components
        alpha1, alpha2: Coupling constants
        lambda_Psi: Overall coupling
    
    Returns:
        dict with C_tt, C_rr, C_theta_theta components
    """
    grad_Psi_r = grad_Psi[0] if isinstance(grad_Psi, (list, tuple, np.ndarray)) else grad_Psi
    
    # Effective potential
    V_eff = alpha1 * Psi**2 + alpha2 * grad_Psi_r**2 + Omega
    
    # Information tensor components
    C_tt = lambda_Psi * metric['g_tt'] * V_eff
    C_rr = lambda_Psi * (grad_Psi_r**2 - metric['g_rr'] * V_eff)
    C_theta_theta = -lambda_Psi * metric['g_theta_theta'] * V_eff
    
    return {
        'C_tt': C_tt,
        'C_rr': C_rr,
        'C_theta_theta': C_theta_theta,
        'rho_info': V_eff,  # Information energy density
    }


def compute_fiber_curvature(Psi: np.ndarray, grad_Psi: np.ndarray,
                            fisher_approx: str = 'local') -> np.ndarray:
    """
    Compute information-geometric curvature Ω (simplified).
    
    For scalar field: Ω ≈ ||∇Ψ||² (local approximation)
    
    Args:
        Psi: Coherence field (can be scalar or array)
        grad_Psi: Gradient of Ψ (can be scalar, array, or list)
        fisher_approx: Approximation method ('local' or 'integrated')
    
    Returns:
        Omega: Information density (same shape as Psi)
    """
    if fisher_approx == 'local':
        # Local approximation: Ω ∝ ||∇Ψ||²
        if isinstance(grad_Psi, (list, tuple)):
            # List of gradient components - sum squares
            if hasattr(grad_Psi[0], '__len__'):
                # Array of gradients
                return sum(g**2 for g in grad_Psi)
            else:
                # List of scalars
                return sum(g**2 for g in grad_Psi)
        else:
            # Single array
            return grad_Psi**2
    else:
        # Integrated approximation: Ω ∝ Ψ² (for massive regime)
        return Psi**2


def landauer_inequality_check(E_PT: np.ndarray, T: float, Delta_H: float,
                              tolerance: float = 0.02) -> dict:
    """
    Check if Reflexive Landauer bound is satisfied.
    
    ΔE_PT ≥ k_B T ΔH
    
    Args:
        E_PT: Reflexive energy
        T: Temperature
        Delta_H: Entropy change
        tolerance: Relative tolerance for "saturation"
    
    Returns:
        dict with 'satisfied', 'ratio', 'saturated' flags
    """
    E_bound = K_BOLTZMANN * T * Delta_H
    ratio = E_PT / (E_bound + 1e-30)  # Avoid division by zero
    
    return {
        'satisfied': np.all(ratio >= 1.0 - tolerance),
        'ratio': float(np.mean(ratio)),
        'saturated': np.abs(np.mean(ratio) - 1.0) < tolerance,
        'E_bound': E_bound,
        'min_ratio': float(np.min(ratio)),
        'max_ratio': float(np.max(ratio))
    }


if __name__ == "__main__":
    # Quick test
    r = np.linspace(2.5, 10.0, 100)
    Psi = 0.02 * np.exp(-(r - 2.4)**2 / 0.1**2)  # Gaussian shell
    grad_Psi = np.gradient(Psi, r)
    
    T_H = 1.0 / (8.0 * np.pi)  # M=1
    Delta_H = 1.0
    
    E_PT = compute_reflexive_energy(Psi, [grad_Psi], T_H, Delta_H)
    
    check = landauer_inequality_check(E_PT, T_H, Delta_H)
    
    print("Reflexive Energy Test:")
    print(f"  E_PT(r_peak) = {E_PT[np.argmax(Psi)]:.3e}")
    print(f"  Bound satisfied: {check['satisfied']}")
    print(f"  Ratio: {check['ratio']:.3f}")
    print(f"  Saturated: {check['saturated']}")

