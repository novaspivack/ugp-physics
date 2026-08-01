"""
Performance tracking utilities for UGP Discovery Lab.
"""

import time
import functools
import psutil
import os
from typing import Dict, Any, Callable, Optional


def track_performance(
    track_memory: bool = True,
    track_cpu: bool = True,
    track_disk: bool = False
) -> Callable:
    """
    Decorator to track performance metrics of functions.
    
    Args:
        track_memory: Whether to track memory usage
        track_cpu: Whether to track CPU usage
        track_disk: Whether to track disk I/O (not implemented yet)
    
    Returns:
        Decorated function with performance tracking
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get process info
            process = psutil.Process(os.getpid())
            
            # Record initial state
            start_time = time.time()
            initial_memory = process.memory_info().rss if track_memory else 0
            initial_cpu_times = process.cpu_times() if track_cpu else None
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Record final state
                end_time = time.time()
                final_memory = process.memory_info().rss if track_memory else 0
                final_cpu_times = process.cpu_times() if track_cpu else None
                
                # Calculate metrics
                runtime_s = end_time - start_time
                max_rss_mb = final_memory / (1024 * 1024)  # Convert to MB
                memory_delta_mb = (final_memory - initial_memory) / (1024 * 1024)
                
                cpu_pct = 0.0
                if track_cpu and initial_cpu_times and final_cpu_times:
                    # Calculate CPU percentage during execution
                    cpu_time_delta = sum(final_cpu_times) - sum(initial_cpu_times)
                    cpu_pct = (cpu_time_delta / runtime_s) * 100 if runtime_s > 0 else 0
                
                # Create metrics dict
                metrics = {
                    "runtime_s": round(runtime_s, 4),
                    "max_rss_mb": round(max_rss_mb, 2),
                    "memory_delta_mb": round(memory_delta_mb, 2),
                    "cpu_pct": round(cpu_pct, 1)
                }
                
                # Add metrics to result if it's a dict
                if isinstance(result, dict):
                    result["metrics"] = metrics
                elif hasattr(result, '__dict__'):
                    # For objects, add metrics as attribute
                    result._performance_metrics = metrics
                
                return result
                
            except Exception as e:
                # Still record metrics even if function fails
                end_time = time.time()
                runtime_s = end_time - start_time
                
                metrics = {
                    "runtime_s": round(runtime_s, 4),
                    "max_rss_mb": 0,
                    "memory_delta_mb": 0,
                    "cpu_pct": 0,
                    "error": str(e)
                }
                
                # Re-raise the exception
                raise e
                
        return wrapper
    return decorator


def aggregate_performance_metrics(results: list) -> Dict[str, Any]:
    """
    Aggregate performance metrics from multiple results.
    
    Args:
        results: List of result dictionaries with metrics
    
    Returns:
        Dictionary with aggregated performance statistics
    """
    if not results:
        return {}
    
    # Extract metrics from results
    all_metrics = []
    for result in results:
        if isinstance(result, dict) and "metrics" in result:
            all_metrics.append(result["metrics"])
    
    if not all_metrics:
        return {}
    
    # Aggregate statistics
    runtimes = [m["runtime_s"] for m in all_metrics if "runtime_s" in m]
    memory_usage = [m["max_rss_mb"] for m in all_metrics if "max_rss_mb" in m]
    cpu_usage = [m["cpu_pct"] for m in all_metrics if "cpu_pct" in m]
    
    aggregated = {
        "total_tasks": len(all_metrics),
        "runtime_stats": {
            "total_s": round(sum(runtimes), 2),
            "avg_s": round(sum(runtimes) / len(runtimes), 2) if runtimes else 0,
            "min_s": round(min(runtimes), 2) if runtimes else 0,
            "max_s": round(max(runtimes), 2) if runtimes else 0
        },
        "memory_stats": {
            "avg_mb": round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0,
            "max_mb": round(max(memory_usage), 2) if memory_usage else 0,
            "min_mb": round(min(memory_usage), 2) if memory_usage else 0
        },
        "cpu_stats": {
            "avg_pct": round(sum(cpu_usage) / len(cpu_usage), 1) if cpu_usage else 0,
            "max_pct": round(max(cpu_usage), 1) if cpu_usage else 0,
            "min_pct": round(min(cpu_usage), 1) if cpu_usage else 0
        }
    }
    
    return aggregated


def log_performance_summary(metrics: Dict[str, Any], logger) -> None:
    """
    Log a performance summary.
    
    Args:
        metrics: Performance metrics dictionary
        logger: Logger instance
    """
    if not metrics:
        return
    
    logger.info("=== Performance Summary ===")
    logger.info(f"Total tasks: {metrics.get('total_tasks', 0)}")
    
    runtime_stats = metrics.get("runtime_stats", {})
    logger.info(f"Runtime: {runtime_stats.get('total_s', 0)}s total, "
                f"{runtime_stats.get('avg_s', 0)}s avg")
    
    memory_stats = metrics.get("memory_stats", {})
    logger.info(f"Memory: {memory_stats.get('avg_mb', 0)}MB avg, "
                f"{memory_stats.get('max_mb', 0)}MB peak")
    
    cpu_stats = metrics.get("cpu_stats", {})
    logger.info(f"CPU: {cpu_stats.get('avg_pct', 0)}% avg, "
                f"{cpu_stats.get('max_pct', 0)}% peak")