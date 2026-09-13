"""
Safe process termination utilities.
"""

import os
import signal
import time
from typing import Optional


def safe_kill_process_tree(pid: int, timeout: float = 5.0, force: bool = False) -> bool:
    """
    Safely terminate a process tree.
    
    Args:
        pid: Process ID to terminate
        timeout: Timeout in seconds for graceful termination
        force: Whether to force kill after timeout
        
    Returns:
        True if process was terminated successfully
    """
    try:
        # First try graceful termination
        os.kill(pid, signal.SIGTERM)
        
        # Wait for graceful termination
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if process still exists
                os.kill(pid, 0)
                time.sleep(0.1)
            except ProcessLookupError:
                # Process terminated
                return True
        
        # Force kill if still running and force=True
        if force:
            try:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.1)
                # Check if terminated
                os.kill(pid, 0)
                return False  # Still running
            except ProcessLookupError:
                return True  # Terminated
            except OSError:
                return False  # Error killing
        
        return False  # Timeout without termination
        
    except ProcessLookupError:
        return True  # Process already terminated
    except OSError:
        return False  # Error accessing process


def kill_child_processes(parent_pid: Optional[int] = None) -> int:
    """
    Kill all child processes of the current or specified parent.
    
    Args:
        parent_pid: Parent process ID (None for current process)
        
    Returns:
        Number of processes terminated
    """
    try:
        import psutil
        
        if parent_pid is None:
            parent_pid = os.getpid()
        
        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)
        
        terminated_count = 0
        for child in children:
            try:
                child.terminate()
                terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Wait for graceful termination
        gone, alive = psutil.wait_procs(children, timeout=2)
        terminated_count += len(gone)
        
        # Force kill any remaining children
        for child in alive:
            try:
                child.kill()
                terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return terminated_count
        
    except ImportError:
        # psutil not available, use basic approach
        return 0
    except Exception:
        return 0


def setup_signal_handlers(cleanup_func):
    """
    Set up signal handlers for graceful shutdown.
    
    Args:
        cleanup_func: Function to call on shutdown
    """
    def signal_handler(signum, frame):
        cleanup_func()
        exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
