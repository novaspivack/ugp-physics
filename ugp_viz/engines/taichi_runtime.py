"""
Lazy Taichi runtime for VIZLAB engines.

Taichi requires a single ``ti.init`` call per process. We centralize that
init here so multiple engines in the same process can share the same
Taichi runtime. The init is *lazy* — nothing happens until a Taichi-
backed engine is constructed.

Engines opt in by passing ``backend="taichi"`` (default is ``"numpy"``);
if Taichi is not installed or fails to initialize on the requested
arch, we fall back to NumPy and emit a one-time warning.
"""

from __future__ import annotations

import os
import warnings
from typing import Any

_TI: Any = None  # the imported `taichi` module, or False if unavailable
_INITIALIZED = False
_ARCH: str | None = None


def is_available() -> bool:
    """Return True if Taichi is installed AND initialized successfully."""
    if _TI is None:
        try_init()
    return _TI is not None and _TI is not False and _INITIALIZED


def try_init(arch: str | None = None) -> Any:
    """Initialize Taichi if it hasn't been initialized yet.

    The ``arch`` argument selects the backend (``"metal"``, ``"cuda"``,
    ``"vulkan"``, ``"cpu"``). When None, prefer ``UGP_VIZ_TAICHI_ARCH``
    environment variable, then ``metal`` (Apple Silicon default), then
    ``cpu`` as a fallback.

    Returns the imported ``taichi`` module on success, ``False`` if
    Taichi is unavailable, or raises if init failed catastrophically.
    """
    global _TI, _INITIALIZED, _ARCH
    if _INITIALIZED:
        return _TI
    try:
        import taichi as ti  # type: ignore[import-not-found]
    except Exception:
        _TI = False
        _INITIALIZED = True
        warnings.warn(
            "Taichi is not installed; falling back to NumPy. "
            "Install with `pip install taichi` for GPU-accelerated kernels.",
            stacklevel=2,
        )
        return False

    requested = (arch or os.environ.get("UGP_VIZ_TAICHI_ARCH")
                 or "metal")
    archs = [requested]
    if requested != "cpu":
        archs.append("cpu")
    last_exc: Exception | None = None
    for a in archs:
        try:
            ti.init(arch=getattr(ti, a), log_level=ti.WARN)
            _TI = ti
            _ARCH = a
            _INITIALIZED = True
            return ti
        except Exception as exc:  # pragma: no cover - arch-dependent
            last_exc = exc
            continue
    _TI = False
    _INITIALIZED = True
    warnings.warn(
        "Taichi import succeeded but `ti.init` failed on every requested "
        f"arch ({archs}); falling back to NumPy. Last error: {last_exc}",
        stacklevel=2,
    )
    return False


def arch_name() -> str | None:
    """The arch Taichi was initialized with, or None if unavailable."""
    return _ARCH


def taichi_or_none() -> Any:
    """Return the imported taichi module or ``None`` (never False)."""
    if not is_available():
        return None
    return _TI
