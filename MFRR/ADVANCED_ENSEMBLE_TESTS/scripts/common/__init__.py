"""
Common utilities for Advanced Ensemble Tests

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
    Mathematical_Foundations_of_Reflexive_Reality.tex
"""

from .ensemble_core import *
from .energy_models import *
from .graph_builders import *

__all__ = [
    # Ensemble dynamics
    'avalanche_update',
    'glauber_step',
    'compute_spectral_norm',
    
    # Energy models
    'reflexive_landauer_energy',
    'coherence_field_energy',
    'cascade_energy_total',
    
    # Graph utilities
    'build_erdos_renyi',
    'build_watts_strogatz',
    'build_barabasi_albert',
    'init_coupling_matrix',
    'match_edge_density',
]

