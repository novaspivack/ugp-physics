"""
Threading-based alternative to multiprocessing for UGP Discovery Lab.
Avoids resource tracker issues while providing parallel execution.
"""

import threading
import queue
import time
from typing import List, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .logging import get_logger


class ThreadSafePool:
    """A threading-based pool with robust cleanup and error handling."""
    
    def __init__(self, max_workers: int, title: str = "thread_pool"):
        self.max_workers = max_workers
        self.title = title
        self.logger = get_logger(f"threading:{title}")
        self.executor: Optional[ThreadPoolExecutor] = None
        self._closed = False
        
    def __enter__(self):
        """Enter context manager and create the thread pool."""
        if self._closed:
            raise RuntimeError("Pool has been closed and cannot be reused")
        
        self.logger.info(f"Starting {self.max_workers} worker threads for {self.title}")
        
        try:
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=f"{self.title}_worker"
            )
        except Exception as e:
            self.logger.error(f"Failed to create thread pool: {e}")
            raise
        
        return self.executor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and clean up."""
        self.terminate()
        return False  # Don't suppress exceptions
    
    def terminate(self):
        """Terminate the pool and clean up all threads."""
        if self._closed:
            return
        
        try:
            if self.executor is not None:
                self.logger.debug("Shutting down thread pool...")
                
                # Shutdown gracefully
                self.executor.shutdown(wait=True)
                
        except Exception as e:
            self.logger.error(f"Error terminating thread pool: {e}")
        finally:
            self._closed = True
            self.executor = None


def run_with_threading(func: Callable, args_list: List[Any], max_workers: int = 4, title: str = "task") -> List[Any]:
    """Run a function with threading instead of multiprocessing."""
    logger = get_logger(f"threading:{title}")
    results = []
    
    try:
        with ThreadSafePool(max_workers=max_workers, title=title) as executor:
            # Submit all tasks
            future_to_arg = {executor.submit(func, arg): arg for arg in args_list}
            
            # Collect results as they complete
            for future in as_completed(future_to_arg):
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per task
                    results.append(result)
                except Exception as e:
                    arg = future_to_arg[future]
                    logger.error(f"Task failed for argument {arg}: {e}")
                    results.append({
                        "error": str(e),
                        "success": False,
                        "status": "error"
                    })
    
    except Exception as e:
        logger.error(f"Threading execution failed: {e}")
        # Fallback to single-threaded execution
        logger.info("Falling back to single-threaded execution")
        for arg in args_list:
            try:
                result = func(arg)
                results.append(result)
            except Exception as task_error:
                logger.error(f"Single-threaded task failed: {task_error}")
                results.append({
                    "error": str(task_error),
                    "success": False,
                    "status": "error"
                })
    
    return results
