"""
Evolution Module: Field dynamics for PR-0

Provides:
- Ablowitz-Ladik equation (soliton dynamics)
- Mediator field evolution (force carriers)
- Adaptive damping (thermalization)

Author: AI Assistant
Date: October 31, 2025
Session: 25.10
"""

from .mediator import MediatorField
from .damping import AdaptiveDamping, UniversalDamping

# Note: ablowitz_ladik.py is the full legacy file
# We keep it for backward compatibility but recommend using
# the modular approach with MediatorField + AdaptiveDamping

__all__ = [
    'MediatorField',
    'AdaptiveDamping',
    'UniversalDamping',
]

