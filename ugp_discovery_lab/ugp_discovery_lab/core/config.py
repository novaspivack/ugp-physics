"""
Configuration management for UGP Discovery Lab.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


def load_yaml(path: str | Path) -> Dict[str, Any]:
    """Load and parse a YAML configuration file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Configuration file not found: {p}")
    
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def default_workers() -> int:
    """Get the default number of worker processes."""
    n = os.cpu_count() or 4
    return max(1, n - 2)


def ensure_dirs(root: Path) -> None:
    """Ensure all necessary directories exist."""
    # Main results directory
    runs_dir = root / "UGP_discovery_lab_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    # Standard result subdirectories
    for d in ["results/logs", "results/checkpoints", "results/reports", "results/artifacts"]:
        (root / d).mkdir(parents=True, exist_ok=True)


def get_run_dir(root: Path, run_name: str) -> Path:
    """Get the directory for a specific run."""
    runs_dir = root / "UGP_discovery_lab_runs"
    run_dir = runs_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def validate_config(cfg: Dict[str, Any]) -> None:
    """Validate a configuration dictionary."""
    if "experiment" not in cfg:
        raise ValueError("Configuration must contain 'experiment' section")
    
    exp_cfg = cfg["experiment"]
    if "name" not in exp_cfg:
        raise ValueError("Experiment configuration must contain 'name' field")


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries, with override taking precedence."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result
