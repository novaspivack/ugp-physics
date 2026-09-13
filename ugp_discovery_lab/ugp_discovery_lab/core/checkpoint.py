"""
Checkpointing system for long-running tasks.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional, Dict


def ckpt_path(root: Path, task_id: str) -> Path:
    """Get the checkpoint file path for a task."""
    return root / "results" / "checkpoints" / f"{task_id}.ckpt.json"


def save_checkpoint(root: Path, task_id: str, state: Dict[str, Any]) -> None:
    """Save checkpoint state for a task."""
    p = ckpt_path(root, task_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    checkpoint_data = {
        "task_id": task_id,
        "timestamp": _get_timestamp(),
        "state": state
    }
    
    try:
        p.write_text(json.dumps(checkpoint_data, indent=2), encoding="utf-8")
    except Exception as e:
        # Log error but don't crash the task
        import logging
        logger = logging.getLogger("checkpoint")
        logger.warning(f"Failed to save checkpoint for {task_id}: {e}")


def load_checkpoint(root: Path, task_id: str) -> Optional[Dict[str, Any]]:
    """Load checkpoint state for a task."""
    p = ckpt_path(root, task_id)
    
    if not p.exists():
        return None
    
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("state", {})
    except Exception as e:
        import logging
        logger = logging.getLogger("checkpoint")
        logger.warning(f"Failed to load checkpoint for {task_id}: {e}")
        return None


def clear_checkpoint(root: Path, task_id: str) -> None:
    """Clear checkpoint file for a task."""
    p = ckpt_path(root, task_id)
    if p.exists():
        try:
            p.unlink()
        except Exception as e:
            import logging
            logger = logging.getLogger("checkpoint")
            logger.warning(f"Failed to clear checkpoint for {task_id}: {e}")


def checkpoint_exists(root: Path, task_id: str) -> bool:
    """Check if a checkpoint exists for a task."""
    return ckpt_path(root, task_id).exists()


def get_checkpoint_info(root: Path, task_id: str) -> Optional[Dict[str, Any]]:
    """Get checkpoint metadata without loading the full state."""
    p = ckpt_path(root, task_id)
    
    if not p.exists():
        return None
    
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {
            "task_id": data.get("task_id"),
            "timestamp": data.get("timestamp"),
            "has_state": "state" in data
        }
    except Exception:
        return None


def list_checkpoints(root: Path) -> list[str]:
    """List all checkpoint task IDs."""
    ckpt_dir = root / "results" / "checkpoints"
    if not ckpt_dir.exists():
        return []
    
    checkpoints = []
    for p in ckpt_dir.glob("*.ckpt.json"):
        task_id = p.stem.replace(".ckpt", "")
        checkpoints.append(task_id)
    
    return sorted(checkpoints)


def cleanup_old_checkpoints(root: Path, max_age_days: int = 7) -> int:
    """Clean up checkpoints older than max_age_days."""
    import time
    from datetime import datetime, timedelta
    
    ckpt_dir = root / "results" / "checkpoints"
    if not ckpt_dir.exists():
        return 0
    
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    removed_count = 0
    
    for p in ckpt_dir.glob("*.ckpt.json"):
        try:
            if p.stat().st_mtime < cutoff_time:
                p.unlink()
                removed_count += 1
        except Exception as e:
            import logging
            logger = logging.getLogger("checkpoint")
            logger.warning(f"Failed to remove old checkpoint {p}: {e}")
    
    return removed_count


def _get_timestamp() -> str:
    """Get current timestamp as ISO string."""
    from datetime import datetime
    return datetime.now().isoformat()
