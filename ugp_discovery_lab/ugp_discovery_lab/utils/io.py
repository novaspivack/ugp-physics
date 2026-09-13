"""
I/O utilities for UGP Discovery Lab.
"""

import os
import sys
import platform
import subprocess
import hashlib
import glob
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def get_git_metadata() -> Dict[str, Any]:
    """Get Git metadata safely with fallbacks."""
    metadata = {
        "commit": None,
        "branch": None,
        "dirty": False,
        "available": False
    }
    
    try:
        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0:
            metadata["commit"] = result.stdout.strip()[:12]  # Short hash
            
        # Get branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0:
            metadata["branch"] = result.stdout.strip()
            
        # Check for dirty working directory
        result = subprocess.run(
            ["git", "diff", "--quiet"],
            capture_output=True,
            cwd=Path.cwd()
        )
        metadata["dirty"] = result.returncode != 0
        
        metadata["available"] = True
        
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        # Git not available or not in a repo
        pass
    
    return metadata


def get_system_metadata() -> Dict[str, str]:
    """Get system metadata."""
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "timestamp": datetime.now().isoformat()
    }


def create_provenance(config: Dict[str, Any]) -> Dict[str, Any]:
    """Create provenance metadata for experiments."""
    git_meta = get_git_metadata()
    system_meta = get_system_metadata()
    
    return {
        "git": git_meta,
        "system": system_meta,
        "config_hash": compute_config_hash(config)
    }


def compute_config_hash(config: Dict[str, Any]) -> str:
    """Compute hash of configuration for reproducibility."""
    import yaml
    
    # Sort keys for deterministic output
    config_str = yaml.dump(config, sort_keys=True, default_flow_style=False)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def compute_reproducibility_hash(
    config: Dict[str, Any],
    input_files: list,
    seeds: list,
    experiment_name: str,
    experiment_version: str = "0.1.0"
) -> str:
    """Compute reproducibility hash for a run."""
    import yaml
    
    # Create deterministic representation
    components = {
        "config": yaml.dump(config, sort_keys=True, default_flow_style=False),
        "input_files": sorted([str(f) for f in input_files]),
        "seeds": sorted([str(s) for s in seeds]),
        "experiment": f"{experiment_name}@{experiment_version}"
    }
    
    # Compute hash
    combined = "|".join(f"{k}:{v}" for k, v in components.items())
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def pyify(obj: Any) -> Any:
    """Convert NumPy types to Python types for JSON serialization."""
    import numpy as np
    
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: pyify(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [pyify(item) for item in obj]
    else:
        return obj


def safe_json_dump(data: Dict[str, Any], **kwargs) -> str:
    """Safely dump data to JSON with NumPy type conversion."""
    import json
    
    # Convert NumPy types to Python types
    safe_data = pyify(data)
    
    # Use custom encoder for any remaining issues
    class SafeJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            return super().default(obj)
    
    return json.dumps(safe_data, cls=SafeJSONEncoder, **kwargs)


def cleanup_files(pattern: str, max_age_days: int, dry_run: bool, logger) -> int:
    """Clean up files matching pattern older than max_age_days."""
    try:
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        
        # Convert Path pattern to glob pattern
        if isinstance(pattern, Path):
            pattern = str(pattern)
        
        # Find all matching files
        for file_path in glob.glob(pattern, recursive=True):
            try:
                file_stat = Path(file_path).stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    if dry_run:
                        logger.info(f"Would remove: {file_path}")
                    else:
                        Path(file_path).unlink()
                        logger.debug(f"Removed: {file_path}")
                    removed_count += 1
                    
            except (OSError, FileNotFoundError):
                # File may have been removed or is inaccessible
                continue
        
        return removed_count
        
    except Exception as e:
        logger.error(f"Error cleaning files with pattern {pattern}: {e}")
        return 0