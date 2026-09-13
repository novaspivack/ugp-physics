"""
PR-0 System: Universal Generative Substrate

Complete implementation of PR-0 (Physics Rule 0), the fundamental substrate
from which spacetime, fields, particles, and forces emerge.

Organization:
  core/       - Lattice, fields, update operators
  evolution/  - Ablowitz-Ladik, mediator, damping
  bootstrap/  - D-minimization, meta-learning
  forces/     - Strong, EM, Weak, Gravity discovery
  analysis/   - Diagnostics, visualization
  utils/      - Helper functions

Author: AI Assistant
Date: October 31, 2025
Sessions: 24-25
"""

__version__ = "1.0.0"
__author__ = "AI Assistant & Nova Spivack"

from . import core
from . import evolution
from . import bootstrap
from . import forces
from . import analysis
from . import utils

__all__ = [
    'core',
    'evolution',
    'bootstrap',
    'forces',
    'analysis',
    'utils',
]

