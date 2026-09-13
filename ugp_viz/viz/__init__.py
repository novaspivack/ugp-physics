"""VIZLAB visualization layer (matplotlib figures + video + Taichi GGUI)."""

from ugp_viz.viz.figures import (
    plot_spacetime,
    plot_tau_c_heatmap,
    plot_tau_c_with_trajectory,
    plot_tau_c_excess,
    plot_clock_speed_comparison,
    plot_field_1d,
    plot_field_3d_slice,
    plot_field_3d_three_slice,
    plot_energy_trace,
    plot_sr_error,
)
from ugp_viz.viz.video import write_video

__all__ = [
    "plot_spacetime",
    "plot_tau_c_heatmap",
    "plot_tau_c_with_trajectory",
    "plot_tau_c_excess",
    "plot_clock_speed_comparison",
    "plot_field_1d",
    "plot_field_3d_slice",
    "plot_field_3d_three_slice",
    "plot_energy_trace",
    "plot_sr_error",
    "write_video",
]
