"""
UGP Discovery Lab

A comprehensive laboratory for exploring the Universal Generative Principle (UGP)
and discovering new lawful evolutions, kernel laws, and computational universality patterns.
"""

__version__ = "0.1.0"
__author__ = "Nova Spivack"

from .core.registry import get_experiment, register_experiment
from .core.config import load_yaml, ensure_dirs, default_workers

# Import all experiments to register them
from .experiments import ca_universality, lawful_evolution, reversible_core
from .experiments import dihedral_lock, kernel_fit, index_lock, rg_flow
from .experiments import dihedral_consistency, quarterlock_anchor, lock_stability
from .experiments import noether_current_scan, rg_cycle_detector
from .experiments import noether_quadratic_scan, rg_sweep
from .experiments import holographic_transducer, negative_control_bias
from .experiments import noether_cubic_scan, rg_long_cycles
from .experiments import info_theory_scan, alpha_changepoint_scan, permutation_tests

__all__ = [
    "get_experiment",
    "register_experiment", 
    "load_yaml",
    "ensure_dirs",
    "default_workers",
]
from .experiments import gte_deep_trajectories
