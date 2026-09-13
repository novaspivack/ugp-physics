"""
Registry system for experiments and diagnostics.
"""

from typing import Dict, Type, Any
from .logging import get_logger


# Global registries
_EXPERIMENTS: Dict[str, Type] = {}
_DIAGNOSTICS: Dict[str, Type] = {}
_ENGINES: Dict[str, Type] = {}


def register_experiment(name: str):
    """Decorator to register an experiment class."""
    def decorator(cls):
        _EXPERIMENTS[name] = cls
        get_logger("registry").debug(f"Registered experiment: {name}")
        return cls
    return decorator


def register_diagnostic(name: str):
    """Decorator to register a diagnostic class."""
    def decorator(cls):
        _DIAGNOSTICS[name] = cls
        get_logger("registry").debug(f"Registered diagnostic: {name}")
        return cls
    return decorator


def register_engine(name: str):
    """Decorator to register an engine class."""
    def decorator(cls):
        _ENGINES[name] = cls
        get_logger("registry").debug(f"Registered engine: {name}")
        return cls
    return decorator


def get_experiment(name: str) -> Type:
    """Get an experiment class by name."""
    if name not in _EXPERIMENTS:
        available = ", ".join(sorted(_EXPERIMENTS.keys()))
        raise KeyError(f"Unknown experiment: {name}. Available: {available}")
    return _EXPERIMENTS[name]


def get_diagnostic(name: str) -> Type:
    """Get a diagnostic class by name."""
    if name not in _DIAGNOSTICS:
        available = ", ".join(sorted(_DIAGNOSTICS.keys()))
        raise KeyError(f"Unknown diagnostic: {name}. Available: {available}")
    return _DIAGNOSTICS[name]


def get_engine(name: str) -> Type:
    """Get an engine class by name."""
    if name not in _ENGINES:
        available = ", ".join(sorted(_ENGINES.keys()))
        raise KeyError(f"Unknown engine: {name}. Available: {available}")
    return _ENGINES[name]


def list_experiments() -> list[str]:
    """List all registered experiment names."""
    return sorted(_EXPERIMENTS.keys())


def list_diagnostics() -> list[str]:
    """List all registered diagnostic names."""
    return sorted(_DIAGNOSTICS.keys())


def list_engines() -> list[str]:
    """List all registered engine names."""
    return sorted(_ENGINES.keys())


def clear_registries() -> None:
    """Clear all registries (useful for testing)."""
    global _EXPERIMENTS, _DIAGNOSTICS, _ENGINES
    _EXPERIMENTS.clear()
    _DIAGNOSTICS.clear()
    _ENGINES.clear()
