"""
Thin GUI entry point. Equivalent to `python -m ugp_viz.cli gui`.

Usage:
    python -m ugp_viz.app --model phimdl_1d --inject gen1_kink@256
"""

from ugp_viz.viz.gui import main


if __name__ == "__main__":
    main()
