#!/usr/bin/env python3
"""
Metric Utilities for Black Hole Simulations

Provides Schwarzschild metric, horizon properties, and related GR computations.
"""

import numpy as np

# Physical constants (geometric units: G = c = 1)
G_NEWTON = 1.0  # Geometric units
C_LIGHT = 1.0
HBAR = 1.0
K_BOLTZMANN = 1.0

# Conversion factors
M_SUN_GEOMETRIC = 1.4766  # km (M_sun in geometric units)


def schwarzschild_metric(r: np.ndarray, M: float) -> dict:
    """
    Compute Schwarzschild metric components in Schwarzschild coordinates.
    
    ds² = -f(r)dt² + f(r)⁻¹dr² + r²dΩ²
    where f(r) = 1 - 2M/r
    
    Args:
        r: Radial coordinate array (geometric units)
        M: Black hole mass (geometric units)
    
    Returns:
        dict with metric components:
            'g_tt': -f(r)
            'g_rr': 1/f(r)
            'g_theta_theta': r²
            'f': lapse function f(r)
            'r_h': horizon radius
    """
    r_h = 2.0 * M
    f = 1.0 - r_h / r
    
    # Avoid division by zero at horizon
    f_safe = np.where(r > r_h * 1.001, f, 1e-10)
    
    return {
        'g_tt': -f,
        'g_rr': 1.0 / f_safe,
        'g_theta_theta': r**2,
        'f': f,
        'r_h': r_h,
        'M': M
    }


def horizon_radius(M: float) -> float:
    """
    Schwarzschild horizon radius.
    
    Args:
        M: Black hole mass (geometric units)
    
    Returns:
        r_h = 2M (geometric units)
    """
    return 2.0 * M


def hawking_temperature(M: float) -> float:
    """
    Hawking temperature of Schwarzschild black hole.
    
    T_H = ℏc³/(8πGMk_B) = 1/(8πM) in geometric units
    
    Args:
        M: Black hole mass (geometric units)
    
    Returns:
        T_H (geometric units)
    """
    return 1.0 / (8.0 * np.pi * M)


def surface_gravity(M: float) -> float:
    """
    Surface gravity at horizon.
    
    κ = 1/(4M) in geometric units
    
    Args:
        M: Black hole mass (geometric units)
    
    Returns:
        κ (geometric units)
    """
    return 1.0 / (4.0 * M)


def bekenstein_hawking_entropy(M: float) -> float:
    """
    Bekenstein-Hawking entropy.
    
    S_BH = A/(4G) = 4πM² in geometric units
    
    Args:
        M: Black hole mass (geometric units)
    
    Returns:
        S_BH (dimensionless)
    """
    A = 4.0 * np.pi * (2.0 * M)**2  # Area = 4πr_h²
    return A / 4.0


def christoffel_symbols(r: np.ndarray, M: float) -> dict:
    """
    Non-zero Christoffel symbols for Schwarzschild metric.
    
    Args:
        r: Radial coordinate array
        M: Black hole mass
    
    Returns:
        dict of Christoffel symbols
    """
    r_h = 2.0 * M
    f = 1.0 - r_h / r
    f_prime = r_h / r**2
    
    return {
        'Gamma_t_tr': f_prime / (2.0 * f),
        'Gamma_r_tt': f * f_prime / 2.0,
        'Gamma_r_rr': -f_prime / (2.0 * f),
        'Gamma_r_theta_theta': -r * f,
        'Gamma_theta_r_theta': 1.0 / r
    }


def proper_time_to_coordinate(tau: float, r: float, M: float) -> float:
    """
    Convert proper time to coordinate time at radius r.
    
    dt = dτ/√f(r)
    
    Args:
        tau: Proper time
        r: Radial position
        M: Black hole mass
    
    Returns:
        t: Coordinate time
    """
    f = 1.0 - 2.0 * M / r
    return tau / np.sqrt(max(f, 1e-10))


def redshift_factor(r: float, M: float) -> float:
    """
    Gravitational redshift factor.
    
    1 + z = 1/√f(r)
    
    Args:
        r: Radial position
        M: Black hole mass
    
    Returns:
        Redshift factor (1+z)
    """
    f = 1.0 - 2.0 * M / r
    return 1.0 / np.sqrt(max(f, 1e-10))


def kretschmann_scalar(r: np.ndarray, M: float) -> np.ndarray:
    """
    Kretschmann scalar (curvature invariant).
    
    K = R_{μνρσ}R^{μνρσ} = 48M²/r⁶
    
    Args:
        r: Radial coordinate array
        M: Black hole mass
    
    Returns:
        K (curvature scalar)
    """
    return 48.0 * M**2 / r**6


if __name__ == "__main__":
    # Quick test
    M = 10.0 * M_SUN_GEOMETRIC  # 10 solar masses
    r = np.linspace(2.5 * M, 10.0 * M, 100)
    
    metric = schwarzschild_metric(r, M)
    T_H = hawking_temperature(M)
    S_BH = bekenstein_hawking_entropy(M)
    
    print(f"Black Hole Properties (M = {M/M_SUN_GEOMETRIC:.1f} M_sun):")
    print(f"  Horizon radius: {metric['r_h']:.3f} km")
    print(f"  Hawking temperature: {T_H:.3e} (geometric)")
    print(f"  Bekenstein-Hawking entropy: {S_BH:.3e}")
    print(f"  Surface gravity: {surface_gravity(M):.3e}")

