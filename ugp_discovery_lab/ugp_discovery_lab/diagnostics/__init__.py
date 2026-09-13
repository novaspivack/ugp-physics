"""
Diagnostic modules for UGP Discovery Lab.
"""

from .algebraic_basis import AlgebraicBasis
from .plotting import (
    is_plotting_available,
    create_heatmap,
    plot_trajectory,
    plot_rg_trajectory,
    save_plot,
    create_lock_stability_heatmap,
    create_rg_flow_plots,
    export_experiment_plots
)
from .data_linter import (
    lint_generator,
    validate_data_integrity,
    DataIntegrityError,
    DataIntegrityWarning,
    compute_generator_signature,
    cli_integrity_check
)
from .generators import (
    neutral_trig_with_memory,
    neutral_multiscale_noise,
    neutral_markov_ar,
    get_generator_signature,
    validate_generator_independence,
    get_approved_generators,
    generate_neutral_data,
    NEUTRAL_GENERATORS
)

__all__ = [
    "AlgebraicBasis",
    "is_plotting_available",
    "create_heatmap",
    "plot_trajectory", 
    "plot_rg_trajectory",
    "save_plot",
    "create_lock_stability_heatmap",
    "create_rg_flow_plots",
    "export_experiment_plots",
    "lint_generator",
    "validate_data_integrity",
    "DataIntegrityError",
    "DataIntegrityWarning",
    "compute_generator_signature",
    "cli_integrity_check",
    "neutral_trig_with_memory",
    "neutral_multiscale_noise",
    "neutral_markov_ar",
    "get_generator_signature",
    "validate_generator_independence",
    "get_approved_generators",
    "generate_neutral_data",
    "NEUTRAL_GENERATORS"
]