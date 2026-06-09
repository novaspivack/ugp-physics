"""
Analysis utilities for PR-0.
"""

from .diagnostics import find_top_k_peaks, torus_distance, order_three_by_x
from .simulation import DEFAULT_FIELDS, SimulationConfig, make_csv_logger, run_with_observers

__all__ = [
    "find_top_k_peaks",
    "torus_distance",
    "order_three_by_x",
    "DEFAULT_FIELDS",
    "SimulationConfig",
    "make_csv_logger",
    "run_with_observers",
]


