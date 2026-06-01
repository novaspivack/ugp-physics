"""
Cross-platform multiprocessing with robust cleanup for UGP Discovery Lab.
"""

import os
import sys
import atexit
import signal
import time
import multiprocessing as mp
import subprocess
import threading
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import multiprocessing.pool
from .logging import get_logger

# Disable problematic resource tracker that causes errors
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
os.environ['JOBLIB_MULTIPROCESSING'] = '0'


def _set_start_method():
    """Set multiprocessing start method to spawn for cross-platform compatibility."""
    try:
        # Use 'spawn' method to avoid fork issues on macOS and resource tracker problems
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Already set


def _cleanup_resource_tracker():
    """Clean up any lingering resource tracker processes."""
    try:
        # Kill any lingering loky resource tracker processes
        if sys.platform == "darwin":  # macOS
            subprocess.run(["pkill", "-f", "resource_tracker"], 
                         capture_output=True, timeout=5)
            subprocess.run(["pkill", "-f", "loky"], 
                         capture_output=True, timeout=5)
        elif sys.platform == "linux":
            subprocess.run(["pkill", "-f", "resource_tracker"], 
                         capture_output=True, timeout=5)
            subprocess.run(["pkill", "-f", "loky"], 
                         capture_output=True, timeout=5)
        
        # Also clean up any lingering multiprocessing processes
        subprocess.run(["pkill", "-f", "SpawnPoolWorker"], 
                      capture_output=True, timeout=5)
    except Exception:
        pass  # Ignore cleanup errors


def _kill_children(logger):
    """Kill all child processes using psutil if available."""
    try:
        import psutil
        parent = psutil.Process()
        children = parent.children(recursive=True)
        
        if not children:
            return
            
        # Terminate all children
        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Wait for graceful termination
        gone, alive = psutil.wait_procs(children, timeout=2)
        
        # Force kill any remaining children
        for child in alive:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
    except ImportError:
        logger.debug("psutil not available for advanced process cleanup")
    except Exception as e:
        logger.warning(f"Process cleanup failed: {e}")


class SafePool:
    """A multiprocessing pool with robust cleanup and signal handling."""
    
    def __init__(self, processes: int, title: str = "pool"):
        _set_start_method()
        _cleanup_resource_tracker()  # Clean up any lingering resource trackers
        
        self.processes = processes
        self.title = title
        self.logger = get_logger(f"workers:{title}")
        self.pool: Optional[multiprocessing.pool.Pool] = None
        self._closed = False
        self._cleanup_registered = False
        
        # Register cleanup handlers
        def _cleanup():
            try:
                self.terminate()
                _cleanup_resource_tracker()
            except Exception:
                pass
        
        if not self._cleanup_registered:
            atexit.register(_cleanup)
            self._cleanup_registered = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals gracefully."""
        signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        self.logger.warning(f"Signal {signal_name} received; terminating pool...")
        self.terminate()
        sys.exit(1)
    
    def __enter__(self):
        """Enter context manager and create the pool."""
        if self._closed:
            raise RuntimeError("Pool has been closed and cannot be reused")
        
        self.logger.info(f"Starting {self.processes} worker processes for {self.title}")
        
        # Create pool with explicit cleanup and resource management
        try:
            self.pool = mp.Pool(
                processes=self.processes,
                maxtasksperchild=10,  # Reduced to prevent resource leaks
                initializer=_worker_init
            )
        except Exception as e:
            self.logger.error(f"Failed to create multiprocessing pool: {e}")
            raise
        
        return self.pool
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and clean up."""
        self.terminate()
        return False  # Don't suppress exceptions
    
    def terminate(self):
        """Terminate the pool and clean up all processes."""
        if self._closed:
            return
        
        try:
            if self.pool is not None:
                self.logger.debug("Terminating multiprocessing pool...")
                
                # Close the pool first
                self.pool.close()
                
                # Wait for completion with timeout
                try:
                    self.pool.join(timeout=10)
                except Exception:
                    pass
                
                # Force terminate if still alive
                try:
                    self.pool.terminate()
                    self.pool.join(timeout=5)
                except Exception:
                    pass
                
                # Additional cleanup
                _kill_children(self.logger)
                _cleanup_resource_tracker()
                    
        except Exception as e:
            self.logger.error(f"Error terminating pool: {e}")
        finally:
            self._closed = True
            self.pool = None


def _worker_init():
    """Initialize worker processes."""
    # Ignore SIGINT in worker processes (let parent handle it)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def create_task_queue(tasks: list, chunk_size: int = 1):
    """Create a task queue with proper chunking for multiprocessing."""
    if chunk_size <= 0:
        chunk_size = 1
    
    # Ensure we don't create too many chunks for small task lists
    if len(tasks) <= chunk_size:
        return [(i, tasks[i:i+chunk_size]) for i in range(0, len(tasks), chunk_size)]
    
    return [(i, tasks[i:i+chunk_size]) for i in range(0, len(tasks), chunk_size)]


def run_task_chunk(task_chunk_data):
    """Run a chunk of tasks (for multiprocessing)."""
    chunk_id, task_chunk = task_chunk_data
    results = []
    
    for task in task_chunk:
        try:
            # Import here to avoid issues with multiprocessing
            try:
                from ..experiments.base import Experiment
                from ..core.checkpoint import load_checkpoint, save_checkpoint
            except ImportError:
                # Fallback for multiprocessing context
                return {"error": "Import failed in multiprocessing context"}
            
            # This assumes the task contains the experiment class and config
            exp_cls = task["experiment_class"]
            exp_cfg = task["experiment_config"]
            root_path = task["root_path"]
            
            # Create experiment instance
            exp = exp_cls(exp_cfg, root_path)
            
            # Run the task
            result = exp.run_task(task)
            results.append(result)
            
        except Exception as e:
            # Return error result instead of crashing
            error_result = {
                "task_id": task.get("task_id", f"unknown_{chunk_id}"),
                "error": str(e),
                "success": False
            }
            results.append(error_result)
    
    return results
