"""Load LTR config and resolve paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

TOOL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = TOOL_ROOT / "config" / "ltr_repos.yaml"
DEFAULT_MATHLIB_STUB = TOOL_ROOT / "config" / "mathlib_stub.yaml"
UGP_PHYSICS_ROOT = TOOL_ROOT.parent.parent
DEFAULT_DB = UGP_PHYSICS_ROOT / "data" / "ltr" / "ltr.db"
DEFAULT_PROBE_DIR = UGP_PHYSICS_ROOT / "data" / "ltr" / "probes"
DEFAULT_UNRESOLVED = UGP_PHYSICS_ROOT / "data" / "ltr" / "unresolved_metadata.jsonl"


def expand_path(raw: str) -> str:
    clone_root = os.environ.get("LTR_CLONE_ROOT", "/Users/nova")
    if "${LTR_CLONE_ROOT:-/Users/nova}" in raw:
        raw = raw.replace("${LTR_CLONE_ROOT:-/Users/nova}", clone_root)
    return os.path.expandvars(raw)


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for repo_slug, repo in cfg.get("repos", {}).items():
        if "path" in repo:
            repo["path"] = expand_path(repo["path"])
    return cfg


def load_mathlib_stub(path: Path | None = None) -> list[dict[str, str]]:
    stub_path = path or DEFAULT_MATHLIB_STUB
    if not stub_path.exists():
        return [
            {"prefix": "Mathlib", "stub_id": "stub:Mathlib"},
            {"prefix": "Std", "stub_id": "stub:Std"},
            {"prefix": "Init", "stub_id": "stub:Init"},
            {"prefix": "Lean", "stub_id": "stub:Lean"},
            {"prefix": "Batteries", "stub_id": "stub:Batteries"},
        ]
    with open(stub_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("collapse", [])


def build_namespace_map(cfg: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (namespace_prefix, repo_slug) sorted longest prefix first."""
    pairs: list[tuple[str, str]] = []
    for repo_slug, repo in cfg.get("repos", {}).items():
        for ns in repo.get("namespaces", []):
            pairs.append((ns, repo_slug))
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    return pairs


def paper_id_from_dirname(name: str) -> str | None:
    import re

    m = re.match(r"^(\d+)_", name)
    if not m:
        return None
    return f"P{int(m.group(1))}"
