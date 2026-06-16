"""
Logging configuration for UGP Discovery Lab.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str, logfile: Optional[Path] = None) -> logging.Logger:
    """Get a configured logger with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with timestamps and levels
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Optional file handler
    if logfile:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def setup_root_logging(level: int = logging.INFO) -> None:
    """Set up root logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )


class TaskLogger:
    """Context manager for task-specific logging."""
    
    def __init__(self, task_id: str, log_dir: Path):
        self.task_id = task_id
        self.log_dir = log_dir
        self.logger = None
    
    def __enter__(self):
        logfile = self.log_dir / f"{self.task_id}.log"
        self.logger = get_logger(f"task:{self.task_id}", logfile)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Log completion status
        if exc_type is None:
            self.logger.info(f"Task {self.task_id} completed successfully")
        else:
            self.logger.error(f"Task {self.task_id} failed with {exc_type.__name__}: {exc_val}")
        return False  # Don't suppress exceptions
