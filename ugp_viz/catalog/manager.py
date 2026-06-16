"""
Catalog manager.

Each model has its own subdirectory under `ugp_viz/catalog/<model>/`
containing JSON files. Each file is a single named entry. The schema is
intentionally permissive: the engine that consumes the entry validates
the fields it needs.

File schema (common subset):

    {
      "name":   "gen1_kink",            # required, must match file stem
      "model":  "phimdl_1d",            # required, must match parent dir
      "type":   "kink"|"antikink"|...,  # required, engine-specific
      "default_position": 256,          # optional
      "velocity": 0.0,                  # optional
      "params":  {...},                 # engine-specific extras
      "notes":   "free text"            # optional
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_ROOT = Path(__file__).resolve().parent


def _model_dir(model: str) -> Path:
    d = CATALOG_ROOT / model
    if not d.exists():
        raise FileNotFoundError(
            f"catalog directory missing: {d} (model '{model}')"
        )
    return d


def list_models() -> list[str]:
    return sorted(
        d.name
        for d in CATALOG_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )


def list_entries(model: str) -> list[str]:
    """List every catalog entry under <catalog>/<model>/, recursively.

    Top-level entries appear by their file stem (e.g. ``gen1_kink``).
    Nested entries appear as POSIX-style relative paths (e.g.
    ``r110/cook_A``). Hidden files / index manifests starting with an
    underscore are filtered out.
    """
    root = _model_dir(model)
    names: list[str] = []
    for p in root.rglob("*.json"):
        if p.name.startswith("_"):
            continue
        rel = p.relative_to(root).with_suffix("")
        names.append(rel.as_posix())
    return sorted(names)


def load_entry(model: str, name: str) -> dict[str, Any]:
    root = _model_dir(model)
    # Allow either POSIX-style nested names (e.g. r110/cook_A) or bare names.
    candidate = (root / f"{name}.json").resolve()
    # Guard against path traversal outside the model directory.
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(
            f"catalog '{model}/{name}' resolves outside the model directory"
        ) from exc
    if not candidate.exists():
        available = list_entries(model)
        raise FileNotFoundError(
            f"catalog '{model}/{name}' not found. "
            f"{len(available)} entries available; first 10 = {available[:10]}"
        )
    data = json.loads(candidate.read_text())
    if "name" in data and data["name"] not in (name, Path(name).name):
        raise ValueError(
            f"catalog file {candidate} has name='{data['name']}' "
            f"but should be '{name}' (or its basename)"
        )
    return data


def save_entry(model: str, name: str, entry: dict[str, Any]) -> Path:
    model_dir = CATALOG_ROOT / model
    rel = Path(name)
    target = (model_dir / rel.with_suffix(".json")).resolve()
    try:
        target.relative_to(model_dir.resolve())
    except ValueError as exc:
        raise ValueError(
            f"entry name '{name}' resolves outside catalog directory"
        ) from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(entry)
    entry.setdefault("name", name)
    entry.setdefault("model", model)
    if entry["name"] not in (name, rel.name):
        raise ValueError(f"entry name '{entry['name']}' != '{name}'")
    target.write_text(json.dumps(entry, indent=2))
    return target


def delete_entry(model: str, name: str) -> None:
    path = (_model_dir(model) / f"{name}.json").resolve()
    if path.exists():
        path.unlink()


def list_all() -> dict[str, list[str]]:
    return {model: list_entries(model) for model in list_models()}
