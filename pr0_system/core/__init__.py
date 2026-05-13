"""
Core Module: Fundamental data structures for PR-0

Provides:
- Lattice: Square/hexagonal lattice, graph substrate
- FieldState: Container for ψ, χ, history
- ParameterSet: Parameter management

Author: AI Assistant
Date: October 31, 2025
Session: 25.10
"""

from .lattice import Lattice, DynamicGraph
from .fields import FieldState, ParameterSet

__all__ = [
    'Lattice',
    'DynamicGraph',
    'FieldState',
    'ParameterSet',
]

