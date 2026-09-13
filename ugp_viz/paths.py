"""
Default output paths.

All run artifacts (data JSON, figures, videos, screenshots, state dumps)
go under the package directory by default so they travel with the app
regardless of the user's working directory. CLI flags and YAML configs
can override these on a per-call basis.

Layout:

    ugp_viz/
    ├── runs/          # default for `runs_dir`
    │   ├── data/      # JSON per-run reports
    │   ├── figures/   # PNG figure exports
    │   ├── videos/    # MP4 video exports
    │   ├── screenshots/ # GUI screenshot exports
    │   └── states/    # save_state / load_state snapshots
    ├── catalog/       # JSON kink/glider catalog (read-only data)
    └── examples/      # example YAML configs

Environment overrides:
    UGP_VIZ_RUNS_DIR   — absolute path for runs/ (overrides default)
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT: Path = Path(__file__).resolve().parent


def runs_dir() -> Path:
    """Return the package-local runs/ directory, honoring env overrides."""
    env = os.environ.get("UGP_VIZ_RUNS_DIR")
    if env:
        return Path(env)
    return PACKAGE_ROOT / "runs"


def data_dir() -> Path:
    return runs_dir() / "data"


def figures_dir() -> Path:
    return runs_dir() / "figures"


def videos_dir() -> Path:
    return runs_dir() / "videos"


def screenshots_dir() -> Path:
    return runs_dir() / "screenshots"


def states_dir() -> Path:
    return runs_dir() / "states"


def catalog_dir() -> Path:
    return PACKAGE_ROOT / "catalog"


def examples_dir() -> Path:
    return PACKAGE_ROOT / "examples"


def ensure_runs_dirs() -> None:
    """Create every standard runs/* subdirectory if missing."""
    for d in (runs_dir(), data_dir(), figures_dir(), videos_dir(),
              screenshots_dir(), states_dir()):
        d.mkdir(parents=True, exist_ok=True)


def resolve_output(path: str | Path | None, *, default_subdir: str,
                   default_name: str | None = None) -> Path:
    """
    Resolve an output path.

    If `path` is None or relative and has no parents (just a filename),
    rewrite it under `runs_dir()/<default_subdir>/`. If `path` is an
    absolute path, leave it untouched. If `path` is a relative path with
    parent directories, leave it relative to the caller's cwd (the
    caller knows what they're doing).
    """
    base = runs_dir() / default_subdir
    if path is None:
        if default_name is None:
            raise ValueError("path=None requires a default_name")
        base.mkdir(parents=True, exist_ok=True)
        return base / default_name
    p = Path(path)
    if not p.is_absolute() and len(p.parts) == 1:
        base.mkdir(parents=True, exist_ok=True)
        return base / p.name
    return p
