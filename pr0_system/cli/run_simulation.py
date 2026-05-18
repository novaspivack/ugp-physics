"""
Run a PR-0 simulation from a JSON/YAML specification.

Example:
    python -m pr0_system.cli.run_simulation --config configs/example.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # noqa: BLE001
    yaml = None  # type: ignore

from pr0_system.analysis import (
    DEFAULT_FIELDS,
    SimulationConfig,
    make_csv_logger,
    run_with_observers,
)
from pr0_system.evolution.ablowitz_ladik import PR0_Final
from pr0_system.integration.unified import OverlayConfig, UnifiedPR0


def load_config(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML configs")
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_integrator(cfg: Dict[str, Any], observers):
    integrator_cfg = cfg.get("integrator", {})
    L_x, L_y = integrator_cfg.get("size", [64, 64])
    mode = integrator_cfg.get("mode", "al")
    if integrator_cfg.get("type", "pr0_final") == "unified":
        overlay_cfg = integrator_cfg.get("overlay", {})
        overlay = OverlayConfig(**overlay_cfg)
        return UnifiedPR0(
            L_x=L_x,
            L_y=L_y,
            overlay=overlay,
            core_mode=mode,
            observers=observers,
        )
    return PR0_Final(L_x=L_x, L_y=L_y, g=integrator_cfg.get("g", 0.1), observers=observers)


def _initialize_solitons(integrator, config: Dict[str, Any]) -> None:
    for soliton in config.get("solitons", []):
        integrator.set_soliton(**soliton)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PR-0 simulation from config.")
    parser.add_argument("--config", required=True, help="Path to JSON/YAML configuration file.")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    cfg = load_config(config_path)

    log_cfg = cfg.get("log", {})
    observers = []
    csv_logger = None
    if log_cfg.get("path"):
        fields = log_cfg.get("fields") or DEFAULT_FIELDS
        csv_logger = make_csv_logger(log_cfg["path"], fields=fields)
        observers.append(csv_logger)

    integrator = _build_integrator(cfg, observers)
    _initialize_solitons(integrator, cfg)

    sim_cfg = cfg.get("simulation", {})
    simulation = SimulationConfig(
        steps=int(sim_cfg.get("steps", 1000)),
        dt=float(sim_cfg.get("dt", 0.01)),
        record_every=int(sim_cfg.get("record_every", 100)),
        progress=bool(sim_cfg.get("progress", False)),
    )

    try:
        run_with_observers(integrator, simulation, observers=observers)
    finally:
        if csv_logger is not None:
            csv_logger.close()


if __name__ == "__main__":
    main()


