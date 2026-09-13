"""Online-analysis helpers consumed by the CLI runner and the GUI.

Modules:
  * ``kink_tracker`` — finds and tracks the centers of localized kinks/
    antikinks in 1D continuum runs, and computes the inter-kink force
    from the spatial gradient of the local energy density.
"""

from ugp_viz.analysis.kink_tracker import (
    KinkSite,
    KinkTracker,
    detect_kinks_1d,
    inter_kink_force_1d,
)

__all__ = [
    "KinkSite",
    "KinkTracker",
    "detect_kinks_1d",
    "inter_kink_force_1d",
]
