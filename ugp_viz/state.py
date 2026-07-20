"""
Run-bundle save/load.

A *run bundle* is a directory or filename stem with the following companion
files. All paths share a common stem ``<stem>``:

    <stem>.run.json          Manifest (config, history, measurements, artifacts).
    <stem>.spacetime.npy     Optional rolling spacetime payload.
    <stem>.state.npz         Engine field snapshot (compressed numpy).
    <stem>.state.json        Engine state metadata (params, step, time).
    <stem>.notes.md          Markdown notes with optional YAML front matter.

The companion files are independent: a saved run may omit any subset. The
manifest references everything by relative path. The GUI's "Open Run"
command, the CLI's ``--load-run`` flag, and the YAML experiment runner's
``load_run`` directive all consume the same format.

Save side
---------
``save_run`` is called from:
  - the YAML runner after a successful experiment (with the user's
    ``output:`` block translated into a stem)
  - the GUI's "File → Save Run" menu
  - the CLI ``run --save-state`` flag

Load side
---------
``load_run`` rehydrates a runner ``ExperimentResult``-like dict plus an
optional engine handle. The engine is rebuilt from the saved
``model``/``params`` and then ``load_state`` is called on it so it
resumes at the exact step+time that was saved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from ugp_viz.engines import (
    InitialCondition,
    SimEngine,
    build_engine,
)
from ugp_viz.notes import Notes, load_notes, save_notes


@dataclass
class RunBundle:
    """In-memory representation of a saved run."""

    stem: Path
    manifest: dict[str, Any] = field(default_factory=dict)
    notes: Notes = field(default_factory=Notes.empty)
    spacetime: np.ndarray | None = None  # shape (T, L) or (T, L, *)
    state_arrays: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def model(self) -> str:
        return str(self.manifest.get("model", ""))

    @property
    def params(self) -> dict[str, Any]:
        return dict(self.manifest.get("params", {}) or {})

    @property
    def history(self) -> dict[str, Any]:
        return dict(self.manifest.get("history", {}) or {})

    @property
    def has_state(self) -> bool:
        return bool(self.state_arrays)


def save_run(
    *,
    stem: str | Path,
    manifest: dict[str, Any],
    spacetime: np.ndarray | None = None,
    engine: SimEngine | None = None,
    notes: Notes | None = None,
) -> dict[str, str]:
    """Write a run bundle and return a dict of {label: path} written.

    ``manifest`` is the runner's ``to_json()`` payload (or any dict
    containing at least ``model``, ``params``, ``history``). It is
    augmented in-place with a ``bundle`` section describing companion
    files.
    """
    stem_path = Path(stem)
    stem_path.parent.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}

    if spacetime is not None:
        np.save(stem_path.with_suffix(".spacetime.npy"), spacetime)
        written["spacetime"] = str(stem_path.with_suffix(".spacetime.npy"))

    if engine is not None:
        engine.save_state(stem_path.with_suffix(".state"))
        written["state_arrays"] = str(stem_path.with_suffix(".state.npz"))
        written["state_meta"] = str(stem_path.with_suffix(".state.json"))

    notes_obj = notes if notes is not None else Notes.empty()
    if not notes_obj.is_empty():
        save_notes(stem_path.with_suffix(".notes.md"), notes_obj)
        written["notes"] = str(stem_path.with_suffix(".notes.md"))

    manifest_out = dict(manifest)
    manifest_out["bundle"] = {
        "stem": stem_path.name,
        "files": {k: Path(v).name for k, v in written.items()},
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "schema_version": 1,
    }
    stem_path.with_suffix(".run.json").write_text(
        json.dumps(manifest_out, indent=2))
    written["manifest"] = str(stem_path.with_suffix(".run.json"))
    return written


def load_run(path: str | Path) -> RunBundle:
    """Load a run bundle given any of its companion files or stem.

    Accepted inputs include ``foo.run.json``, ``foo.spacetime.npy``,
    ``foo.state.npz``, ``foo.notes.md``, or simply ``foo`` (the stem).
    Missing companion files are silently skipped.
    """
    stem = _resolve_stem(path)

    manifest_path = stem.with_suffix(".run.json")
    if not manifest_path.exists():
        # Legacy fallback — accept a bare ``<stem>.json`` produced by the
        # original runner format.
        legacy = stem.with_suffix(".json")
        if legacy.exists():
            manifest_path = legacy
        else:
            raise FileNotFoundError(
                f"no run manifest found at {manifest_path} (or {legacy})")
    manifest = json.loads(manifest_path.read_text())

    spacetime: np.ndarray | None = None
    sp_path = stem.with_suffix(".spacetime.npy")
    if sp_path.exists():
        spacetime = np.load(sp_path)

    state_arrays: dict[str, np.ndarray] = {}
    npz_path = stem.with_suffix(".state.npz")
    if npz_path.exists():
        with np.load(npz_path) as nz:
            state_arrays = {k: nz[k] for k in nz.files}

    notes: Notes = Notes.empty()
    md_path = stem.with_suffix(".notes.md")
    json_notes_path = stem.with_suffix(".notes.json")
    if md_path.exists():
        notes = load_notes(md_path)
    elif json_notes_path.exists():
        notes = load_notes(json_notes_path)

    return RunBundle(
        stem=stem,
        manifest=manifest,
        notes=notes,
        spacetime=spacetime,
        state_arrays=state_arrays,
    )


def rebuild_engine(bundle: RunBundle) -> SimEngine:
    """Rebuild a live engine from a saved bundle, restoring step/time.

    The engine is constructed with the saved params, an empty initial
    condition is applied, and then ``load_state`` is called via the saved
    ``state_arrays``. If no state arrays are present, the engine is
    returned at step 0 — callers should check ``bundle.has_state``.
    """
    model = bundle.model
    params = bundle.params
    if not model:
        raise ValueError("bundle manifest is missing 'model'")
    engine = build_engine(model, params=params)
    engine.reset(InitialCondition(kind="vacuum"))
    if bundle.has_state:
        # Mirror the on-disk format expected by SimEngine.load_state:
        # the .state.npz and .state.json must be present. Build them from
        # the in-memory arrays + manifest if the disk files are gone.
        meta_path = bundle.stem.with_suffix(".state.json")
        npz_path = bundle.stem.with_suffix(".state.npz")
        if meta_path.exists() and npz_path.exists():
            engine.load_state(bundle.stem.with_suffix(".state"))
        else:
            engine._step = int(bundle.manifest.get("step", 0))
            engine._time = float(bundle.manifest.get("time", 0.0))
            engine._apply_loaded_arrays(bundle.state_arrays)
    return engine


def _resolve_stem(path: str | Path) -> Path:
    """Strip recognized suffixes to recover the run-bundle stem."""
    p = Path(path)
    # Composite suffixes first so the longer match wins.
    for suffix in (
        ".run.json",
        ".spacetime.npy",
        ".state.npz",
        ".state.json",
        ".notes.md",
        ".notes.json",
    ):
        if p.name.endswith(suffix):
            return p.with_name(p.name[: -len(suffix)])
    if p.suffix == ".json":
        return p.with_suffix("")
    return p


__all__ = [
    "RunBundle",
    "save_run",
    "load_run",
    "rebuild_engine",
]
