"""
Video export.

Two backends:
  - matplotlib.animation -> mp4 via ffmpeg (works wherever ffmpeg is on PATH)
  - Fallback: write PNG frames to a tmp dir + invoke ffmpeg directly

A frame-producer callback yields (step_index, fig) tuples; the writer is
agnostic to the engine that produced them so any model can render videos.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterator

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
import numpy as np


def write_video(
    frame_iter: Iterator[plt.Figure],
    filename: str | Path,
    *,
    fps: int = 30,
    dpi: int = 120,
    backend: str = "auto",
) -> Path:
    """
    Write an MP4 video from an iterator of matplotlib figures.

    Each yielded figure is rendered as one frame and then closed. The
    figures must all be the same size.

    Parameters
    ----------
    frame_iter : iterator of matplotlib Figure objects
    filename   : output MP4 path
    fps        : frames per second
    dpi        : per-frame DPI
    backend    : 'auto' | 'animation' | 'ffmpeg'
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    if backend == "auto":
        backend = "animation" if _ffmpeg_available() else "ffmpeg"

    if backend == "animation":
        return _write_via_animation(frame_iter, path, fps=fps, dpi=dpi)
    if backend == "ffmpeg":
        return _write_via_pngs(frame_iter, path, fps=fps, dpi=dpi)
    raise ValueError(f"unknown backend '{backend}'")


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _write_via_animation(frame_iter, path: Path, *, fps: int, dpi: int) -> Path:
    first = next(frame_iter, None)
    if first is None:
        raise ValueError("no frames produced")
    writer = FFMpegWriter(fps=fps, bitrate=4000)
    with writer.saving(first, str(path), dpi=dpi):
        writer.grab_frame()
        plt.close(first)
        for fig in frame_iter:
            writer.grab_frame()
            plt.close(fig)
    return path


def _write_via_pngs(frame_iter, path: Path, *, fps: int, dpi: int) -> Path:
    if not _ffmpeg_available():
        raise RuntimeError("ffmpeg not on PATH; install ffmpeg to export videos")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        n = 0
        for n, fig in enumerate(frame_iter):
            fig.savefig(tmp_path / f"frame_{n:06d}.png", dpi=dpi,
                        bbox_inches="tight")
            plt.close(fig)
        if n == 0 and not (tmp_path / "frame_000000.png").exists():
            raise ValueError("no frames produced")
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(tmp_path / "frame_%06d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18", str(path),
            ],
            check=True,
            capture_output=True,
        )
    return path


def render_spacetime_video(
    spacetime: np.ndarray,
    filename: str | Path,
    *,
    fps: int = 30,
    dpi: int = 120,
    window: int = 200,
    cmap: str = "binary",
    backend: str = "auto",
) -> Path:
    """
    Convenience: render a rolling spacetime window as a video.
    Each frame shows `window` rows ending at row t.
    """
    n_steps = spacetime.shape[0]

    def _frames():
        for t in range(1, n_steps + 1):
            start = max(0, t - window)
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(spacetime[start:t], cmap=cmap, aspect="auto",
                      interpolation="nearest", origin="upper")
            ax.set_xlabel("Cell position")
            ax.set_ylabel("Time (rolling window)")
            ax.set_title(f"step {t}/{n_steps}")
            yield fig

    return write_video(_frames(), filename, fps=fps, dpi=dpi, backend=backend)
