"""
Reflexive Landauer energy models for ensemble adjudication

Implements energy cost calculations based on:
    ΔE = k_B T ln(n) + λ_Ψ E_Ψ(coherence)

For ensembles, coherence term scales with cascade size and spatial extent.

Cross-reference:
    Mathematical_Foundations_of_Reflexive_Reality.tex (Section reflexive-landauer)
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform

# Physical constants
K_B = 1.380649e-23  # Boltzmann constant (J/K)
T_ROOM = 300.0      # Room temperature (K)

# Derived constants
KBT_ROOM = K_B * T_ROOM  # ~ 4.14e-21 J


def reflexive_landauer_energy(n_branches=2, T=T_ROOM):
    """
    Base Reflexive Landauer energy cost for single adjudication.
    
    ΔE_local = k_B T ln(n)
    
    Args:
        n_branches: Number of branches eliminated (typically 2 for binary CP)
        T: Temperature (K)
        
    Returns:
        Energy in Joules
    """
    return K_B * T * np.log(n_branches)


def coherence_field_energy(psi_amplitude, psi_gradient_sq, volume, alpha1=1.0, alpha2=1.0):
    """
    Coherence field contribution to Landauer energy.
    
    E_Ψ = ∫ (α₁ Ψ² + α₂ ||∇Ψ||²) dV
    
    For discrete cascades, we approximate:
        - Ψ² ~ (cascade size)² / N
        - ||∇Ψ||² ~ (spatial extent)
        - Volume ~ cascade spatial footprint
    
    Args:
        psi_amplitude: Characteristic Ψ amplitude
        psi_gradient_sq: Characteristic ||∇Ψ||²
        volume: Effective volume of coherence region
        alpha1: Self-energy coefficient
        alpha2: Gradient energy coefficient
        
    Returns:
        Coherence energy (arbitrary units, scaled by λ_Ψ later)
    """
    energy_potential = alpha1 * psi_amplitude**2 * volume
    energy_gradient = alpha2 * psi_gradient_sq * volume
    return energy_potential + energy_gradient


def cascade_energy_total(cascade_size, cascade_positions=None, N_total=1000, 
                         lambda_psi=1.0, T=T_ROOM, alpha1=1.0, alpha2=1.0):
    """
    Total energy release from a cascade of adjudications.
    
    Includes:
    1. Logical cost: S × k_B T ln(2)
    2. Coherence cost: λ_Ψ E_Ψ(cascade)
    
    For coherent cascades, E_Ψ scales superlinearly with S due to
    collective field configuration.
    
    Args:
        cascade_size: Number of CPs involved in cascade (S)
        cascade_positions: Optional array of CP positions (Nx2 or Nx3)
        N_total: Total number of CPs in system
        lambda_psi: Coherence coupling strength (dimensionless)
        T: Temperature (K)
        alpha1, alpha2: Field coefficients
        
    Returns:
        Total energy in Joules
    """
    S = cascade_size
    
    # Logical cost (linear in S)
    E_logical = S * reflexive_landauer_energy(n_branches=2, T=T)
    
    # Coherence cost (nonlinear in S)
    # Amplitude scales as sqrt(S/N) (collective enhancement)
    psi_amp = np.sqrt(S / N_total)
    
    # Spatial extent
    if cascade_positions is not None and len(cascade_positions) >= 2:
        # Compute actual spatial extent
        dists = pdist(cascade_positions)
        if len(dists) > 0:
            spatial_extent = np.mean(dists)  # Mean pairwise distance
        else:
            spatial_extent = 1.0
    else:
        # Approximate: random cascade on random graph
        # Expected extent ~ sqrt(S) for diffusive growth
        spatial_extent = np.sqrt(S)
    
    # Gradient term ~ Ψ / extent
    psi_gradient_sq = (psi_amp / spatial_extent)**2 if spatial_extent > 0 else 0.0
    
    # Volume ~ (extent)^d for d-dimensional system
    # Use d=2 as typical for network embedded in plane
    volume = spatial_extent**2
    
    E_coherence = coherence_field_energy(
        psi_amp, psi_gradient_sq, volume, alpha1, alpha2
    )
    
    # Scale coherence by coupling constant and kBT for dimensional consistency
    E_coherence_scaled = lambda_psi * KBT_ROOM * E_coherence
    
    return E_logical + E_coherence_scaled


def cascade_energy_simple(cascade_size, exponent=1.5, prefactor=None):
    """
    Simplified power-law energy scaling for quick analysis.
    
    ΔE(S) = A × S^α
    
    If α > 1, this is superlinear (amplification).
    
    Args:
        cascade_size: Number of CPs (S)
        exponent: Power-law exponent α
        prefactor: Normalization A (if None, uses kBT)
        
    Returns:
        Energy in Joules
    """
    if prefactor is None:
        prefactor = KBT_ROOM
    
    return prefactor * (cascade_size ** exponent)


def energy_from_cascade_data(cascade_sizes, positions_list=None, **kwargs):
    """
    Compute energies for a list of cascades.
    
    Args:
        cascade_sizes: Array of cascade sizes
        positions_list: Optional list of position arrays
        **kwargs: Parameters for cascade_energy_total
        
    Returns:
        Array of energies
    """
    energies = np.zeros(len(cascade_sizes))
    
    for i, S in enumerate(cascade_sizes):
        positions = positions_list[i] if positions_list is not None else None
        energies[i] = cascade_energy_total(S, positions, **kwargs)
    
    return energies


def fit_power_law_energy(sizes, energies):
    """
    Fit power law E = A S^α to energy vs cascade size data.
    
    Uses log-log linear regression.
    
    Args:
        sizes: Array of cascade sizes
        energies: Array of corresponding energies
        
    Returns:
        dict with 'exponent' (α), 'prefactor' (A), 'r_squared'
    """
    # Filter out zeros
    mask = (sizes > 0) & (energies > 0)
    s_valid = sizes[mask]
    e_valid = energies[mask]
    
    if len(s_valid) < 2:
        return {'exponent': np.nan, 'prefactor': np.nan, 'r_squared': np.nan}
    
    # Log-log fit
    log_s = np.log(s_valid)
    log_e = np.log(e_valid)
    
    # Fit: log(E) = α log(S) + log(A)
    coeffs = np.polyfit(log_s, log_e, 1)
    alpha = coeffs[0]
    log_A = coeffs[1]
    A = np.exp(log_A)
    
    # R-squared
    e_pred = A * (s_valid ** alpha)
    ss_res = np.sum((e_valid - e_pred)**2)
    ss_tot = np.sum((e_valid - np.mean(e_valid))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        'exponent': float(alpha),
        'prefactor': float(A),
        'r_squared': float(r_squared)
    }


def theoretical_energy_scaling():
    """
    Return theoretical predictions for energy scaling.
    
    Returns:
        dict with predictions for different regimes
    """
    return {
        'subcritical': {
            'exponent': 1.0,
            'description': 'Linear scaling, independent adjudicators'
        },
        'critical': {
            'exponent': 1.5,
            'description': 'Sublinear to superlinear transition'
        },
        'supercritical': {
            'exponent_min': 1.5,
            'exponent_max': 2.0,
            'description': 'Superlinear scaling, collective coherence dominates'
        }
    }

