"""
Utility functions for ΛΩ-RCP Phase II

Cross-references:
  - ../../../ΛΩ-RCP/src/rcp/util.py (Phase I utilities)
"""

import json, math, os, random
import numpy as np

def set_seed(s):
    random.seed(s)
    np.random.seed(s)

def phi():
    return (1.0 + math.sqrt(5.0)) / 2.0

def Lambda():
    """Norfleet's constant: ln(φ)/ln(2π)"""
    return math.log(phi()) / math.log(2.0 * math.pi)

def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def load_yaml(path):
    import yaml
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dirs():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def kB_T_CMB():
    """CMB temperature in natural units (K)"""
    return 2.725  # Kelvin

