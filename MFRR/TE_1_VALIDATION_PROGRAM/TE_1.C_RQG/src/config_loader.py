"""
Utility helpers for reading YAML/JSON configs for TE_1.C pipelines.

Referenced by TE_1.C.1_PLAN.md (Phase 1 reproducibility bundle).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "PyYAML is required to parse YAML configs. Install with `pip install pyyaml`."
            ) from exc
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported config extension: {suffix}")

