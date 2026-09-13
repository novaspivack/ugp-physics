"""
RR Common Utilities for Black Hole Computational Tests

Reference: MFRR Paper, Black Holes in Reflexive Reality section
Date: November 4, 2025

Extended for BH1-BH4 validation tests (Choice-Point Extension)
"""

# Existing infrastructure (from original BH work)
from .params import QNMParams, TOVPsiParams, JTParams
from .numerics import (r_to_rstar, V_schwarzschild_axial, find_peak_uniform,
                       second_derivative_stencil, gaussian_window,
                       poschl_teller_qnm_from_peak)
from .io_helpers import write_csv

# New utilities for BH1-BH4 tests
from .metric_utils import (
    schwarzschild_metric, hawking_temperature, horizon_radius,
    surface_gravity, bekenstein_hawking_entropy
)
from .reflexive_energy import (
    compute_reflexive_energy, compute_stress_tensor_psi,
    compute_information_tensor, compute_fiber_curvature,
    landauer_inequality_check
)

__all__ = [
    # Original exports
    'QNMParams', 'TOVPsiParams', 'JTParams',
    'r_to_rstar', 'V_schwarzschild_axial', 'find_peak_uniform',
    'second_derivative_stencil', 'gaussian_window', 'poschl_teller_qnm_from_peak',
    'write_csv',
    # New exports for BH1-BH4
    'schwarzschild_metric', 'hawking_temperature', 'horizon_radius',
    'surface_gravity', 'bekenstein_hawking_entropy',
    'compute_reflexive_energy', 'compute_stress_tensor_psi',
    'compute_information_tensor', 'compute_fiber_curvature',
    'landauer_inequality_check'
]

