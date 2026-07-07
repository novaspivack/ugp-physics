"""
Utility modules for UGP Discovery Lab.
"""

from .io import (
    get_git_metadata,
    get_system_metadata,
    create_provenance,
    compute_reproducibility_hash,
    pyify,
    safe_json_dump,
    cleanup_files
)

from .timeit import (
    track_performance,
    aggregate_performance_metrics,
    log_performance_summary
)

from .docs import (
    generate_experiment_docs,
    generate_suite_docs
)

__all__ = [
    "get_git_metadata",
    "get_system_metadata", 
    "create_provenance",
    "compute_reproducibility_hash",
    "pyify",
    "safe_json_dump",
    "cleanup_files",
    "track_performance",
    "aggregate_performance_metrics",
    "log_performance_summary",
    "generate_experiment_docs",
    "generate_suite_docs"
]