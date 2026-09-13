"""
Example: run PR-0 with observers and CSV logging.

Usage:
    python -m pr0_system.examples.03_recorded_run

The example attaches a CSV logger that records default metrics into
``./pr0_logs/example_run.csv`` without modifying the evolution core.
"""

from __future__ import annotations

from pathlib import Path

from pr0_system.evolution.ablowitz_ladik import PR0_Final
from pr0_system.analysis import SimulationConfig, make_csv_logger, run_with_observers


def main() -> None:
    log_path = Path("pr0_logs/example_run.csv")
    integrator = PR0_Final(L_x=64, L_y=64)
    integrator.set_soliton(x0=20, y0=32, amplitude=3.0, width=4.0, velocity_x=0.15, sign=+1)
    integrator.set_soliton(x0=44, y0=32, amplitude=3.0, width=4.0, velocity_x=-0.15, sign=-1)

    logger = make_csv_logger(log_path)
    try:
        run_with_observers(
            integrator,
            SimulationConfig(steps=2000, dt=0.01, record_every=200, progress=True),
            observers=[logger],
        )
    finally:
        logger.close()
    print(f"[PR-0] metrics exported to {log_path.resolve()}")


if __name__ == "__main__":
    main()


