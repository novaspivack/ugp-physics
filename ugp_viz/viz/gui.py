"""
Taichi GGUI real-time visualization app for VIZLAB.

Supports:
  - 1D continuum models (Phi_MDL 1D, Z7-KG): live field plot + tau_c heatmap
  - 1D CA models (FCA sync, AFCA, Z7 f_MDL): live spacetime + tau_c heatmap
  - 3D Phi_MDL: three axis-aligned slice views (XY, XZ, YZ) with movable
    slice indices

UI:
  - Main viewport (Taichi GGUI canvas)
  - Sidebar control panel with model selector, parameters, step controls,
    catalog injection, screenshot/video toggles
  - Bottom readout: step / time / energy / tau_c stats / fps

Taichi GGUI is optional. If the user doesn't have Taichi installed, the
GUI falls back to a matplotlib loop that updates a single window using
FuncAnimation.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ugp_viz.engines import (
    SimEngine,
    InjectionSpec,
    InitialCondition,
    build_engine,
    list_models,
)
from ugp_viz.catalog.manager import list_entries
from ugp_viz.paths import screenshots_dir, videos_dir


@dataclass
class GUIState:
    model: str
    engine: SimEngine
    paused: bool = True
    substeps_per_frame: int = 1
    spacetime_window: int = 200
    spacetime_history: list[np.ndarray] = None  # type: ignore[assignment]
    tau_history: list[np.ndarray] = None  # type: ignore[assignment]
    slice_indices: tuple[int, int, int] = (32, 32, 32)
    energy_history: list[tuple[float, float]] = None  # type: ignore[assignment]
    frame_count: int = 0
    # Kink tracking (1D continuum only)
    kink_tracker: object | None = None
    last_force_report: dict | None = None

    def __post_init__(self) -> None:
        if self.spacetime_history is None:
            self.spacetime_history = []
        if self.tau_history is None:
            self.tau_history = []
        if self.energy_history is None:
            self.energy_history = []
        if self.kink_tracker is None and self.engine.spatial_dim == 1:
            from ugp_viz.analysis.kink_tracker import KinkTracker
            dx = float(self.engine.params.get("dx", 1.0))
            self.kink_tracker = KinkTracker(dx=dx)


# ──────────────────────────────────────────────────────────────────────
# Backend detection
# ──────────────────────────────────────────────────────────────────────

def _try_import_taichi():
    try:
        import taichi as ti
        return ti
    except Exception:
        return None


def _try_import_tk() -> bool:
    """Return True only if Tkinter is importable AND a display is available."""
    try:
        import tkinter  # noqa: F401
        return True
    except Exception:
        return False


def run_gui(model: str = "phimdl_1d",
            params: dict[str, Any] | None = None,
            initial_inject: str | None = None,
            ic_kind: str = "vacuum",
            backend: str = "auto",
            output_dir: str | Path | None = None,
            notes_path: str | Path | None = None,
            load_run_path: str | Path | None = None,
            load_config_path: str | Path | None = None) -> None:
    """
    Launch the VIZLAB GUI for the given model.

    backend: 'auto' | 'tk' | 'taichi' | 'matplotlib'

    With backend='auto' the Tk backend is preferred when Tkinter is
    available — it is the only backend that exposes the full feature set
    (file menus, parameter editor, notes panel, About modal,
    zoom/pan toolbar). The Taichi GGUI and headless matplotlib backends
    are kept as fallbacks for environments without Tk.

    When ``output_dir`` is None the GUI saves screenshots and videos under
    the package-local ``ugp_viz/runs/screenshots/`` and ``…/videos/``
    directories so artifacts travel with the app.
    """
    # Optional pre-load of a run or config — handled by the Tk backend
    # only since the other backends do not have file-bundle round-trip
    # support; the Tk path passes the loaded engine + notes through.
    preload_notes = None
    if notes_path is not None:
        from ugp_viz.notes import load_notes
        preload_notes = load_notes(notes_path)

    if backend == "auto":
        if _try_import_tk():
            backend = "tk"
        elif _try_import_taichi() is not None:
            backend = "taichi"
        else:
            backend = "matplotlib"

    if backend == "tk":
        if not _try_import_tk():
            print("WARNING: Tkinter not available; falling back to matplotlib.")
            backend = "matplotlib"
        else:
            from ugp_viz.viz.gui_tk import launch_tk_gui
            launch_tk_gui(model=model, params=params,
                          initial_inject=initial_inject,
                          ic_kind=ic_kind, notes=preload_notes)
            return

    engine = build_engine(model, params=params)
    engine.reset(InitialCondition(kind=ic_kind))
    if initial_inject:
        engine.inject(InjectionSpec.from_string(initial_inject))
    state = GUIState(model=model, engine=engine)

    if backend == "taichi":
        ti = _try_import_taichi()
        if ti is None:
            print("WARNING: Taichi not available; falling back to matplotlib.")
            backend = "matplotlib"

    out_path = Path(output_dir) if output_dir is not None else None
    if backend == "taichi":
        _run_taichi_gui(state, output_dir=out_path)
    elif backend == "matplotlib":
        _run_matplotlib_gui(state, output_dir=out_path)
    else:
        raise ValueError(f"unknown GUI backend '{backend}'")


# ──────────────────────────────────────────────────────────────────────
# Taichi GGUI backend
# ──────────────────────────────────────────────────────────────────────

def _run_taichi_gui(state: GUIState, output_dir: Path | None) -> None:
    import taichi as ti

    try:
        ti.init(arch=ti.metal, log_level=ti.WARN)
    except Exception:
        ti.init(arch=ti.cpu, log_level=ti.WARN)

    window = ti.ui.Window("UGP VIZLAB", (1280, 800), vsync=True)
    canvas = window.get_canvas()
    canvas.set_background_color((0.05, 0.05, 0.08))
    gui = window.get_gui()
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    img_w, img_h = 1024, 720
    img_field = ti.Vector.field(3, dtype=ti.f32, shape=(img_w, img_h))

    last_time = time.time()
    fps = 0.0
    while window.running:
        # Sidebar
        with gui.sub_window("Controls", 0.74, 0.0, 0.26, 1.0):
            gui.text(f"Model: {state.model}")
            gui.text(f"Step: {state.engine.step_count}")
            gui.text(f"Time: {state.engine.sim_time:.3f}")
            gui.text(f"FPS:  {fps:.1f}")
            state.paused = gui.checkbox("Paused", state.paused)
            state.substeps_per_frame = int(
                gui.slider_float("Substeps / frame",
                                 state.substeps_per_frame, 1, 32))
            if gui.button("Step (1x substeps)"):
                state.engine.step(state.substeps_per_frame)
            if gui.button("Reset"):
                state.engine.reset(InitialCondition(kind="vacuum"))
                state.spacetime_history.clear()
                state.tau_history.clear()
                state.energy_history.clear()
            if gui.button("Screenshot"):
                _screenshot(state, output_dir)
            if gui.button("Save MP4 (spacetime)"):
                _save_video(state, output_dir)
            if state.engine.spatial_dim == 3:
                if gui.button("Save volume PNG"):
                    _save_volume_image(state, output_dir)
                if gui.button("Save isosurface PNG"):
                    _save_isosurface_image(state, output_dir)
            gui.text("Inject:")
            # Top-level entries first, then a folded group for r110/* etc.
            entries = list_entries(state.model)
            for kind in entries:
                if "/" in kind:
                    continue
                if gui.button(kind):
                    pos = _model_center(state.engine)
                    state.engine.inject(InjectionSpec(kind=kind, position=pos))
            # Kink-tracker controls (1D continuum models only)
            if state.engine.spatial_dim == 1 and state.kink_tracker is not None:
                gui.text("--- Kink force readout ---")
                if gui.button("Auto-mark all kinks"):
                    _auto_mark_kinks(state)
                if gui.button("Clear marked kinks"):
                    state.kink_tracker.clear()
                    state.last_force_report = None
                report = state.last_force_report or {}
                for site in report.get("sites", []):
                    gui.text(
                        f"  {site['label']}: x={site['position']:.2f} "
                        f"E={site['energy_peak']:.3f}"
                    )
                for pair in report.get("pairs", []):
                    gui.text(
                        f"  {pair['a']}-{pair['b']}: "
                        f"d={pair['separation']:.2f} "
                        f"F_{pair['b']}={pair['F_on_b']:+.3e}"
                    )
            if state.engine.spatial_dim == 3:
                Nx, Ny, Nz = state.engine.params["Nx"], state.engine.params["Ny"], state.engine.params["Nz"]
                ix, iy, iz = state.slice_indices
                ix = int(gui.slider_float("x-slice", ix, 0, Nx - 1))
                iy = int(gui.slider_float("y-slice", iy, 0, Ny - 1))
                iz = int(gui.slider_float("z-slice", iz, 0, Nz - 1))
                state.slice_indices = (ix, iy, iz)

        if not state.paused:
            state.engine.step(state.substeps_per_frame)
        _record_spacetime(state)
        _update_kink_report(state)

        # Render to img_field
        img = _render_image(state, img_w, img_h)
        img_field.from_numpy(img.astype(np.float32))
        canvas.set_image(img_field)
        window.show()

        # FPS
        state.frame_count += 1
        now = time.time()
        dt = now - last_time
        if dt > 0.5:
            fps = state.frame_count / dt
            state.frame_count = 0
            last_time = now


def _auto_mark_kinks(state: GUIState) -> None:
    """Detect all kinks in the current snapshot and mark them in the tracker."""
    if state.kink_tracker is None:
        return
    snap = state.engine.snapshot()
    if snap.energy_density is None:
        return
    from ugp_viz.analysis.kink_tracker import detect_kinks_1d
    sites = detect_kinks_1d(snap.energy_density, dx=state.kink_tracker.dx)
    state.kink_tracker.clear()
    for s in sites:
        state.kink_tracker.sites.append(s)
    state.last_force_report = state.kink_tracker.report(snap.energy_density)


def _update_kink_report(state: GUIState) -> None:
    """Refresh the inter-kink force readout from the current snapshot."""
    if state.kink_tracker is None or not state.kink_tracker.sites:
        return
    snap = state.engine.snapshot()
    if snap.energy_density is None:
        return
    state.kink_tracker.update(snap.energy_density, sim_time=state.engine.sim_time)
    state.last_force_report = state.kink_tracker.report(snap.energy_density)


def _model_center(engine: SimEngine) -> int | tuple[int, int, int]:
    if engine.spatial_dim == 1:
        L = int(engine.params.get("L", engine.params.get("N", 256)))
        return L // 2
    Nx = int(engine.params["Nx"])
    Ny = int(engine.params["Ny"])
    Nz = int(engine.params["Nz"])
    return (Nx // 2, Ny // 2, Nz // 2)


def _record_spacetime(state: GUIState) -> None:
    snap = state.engine.snapshot()
    if snap.tape is not None:
        state.spacetime_history.append(snap.tape.copy())
        if snap.tau_c is not None:
            state.tau_history.append(snap.tau_c.copy())
    elif snap.phi is not None:
        # Build a discrete "spacetime" row from phi sign for visualization
        Nphi = int(state.engine.params.get("N_phi",
                                            state.engine.params.get("N_sym", 7)))
        half = 2.0 * np.pi / Nphi * 0.5
        state.spacetime_history.append((snap.phi > half).astype(np.uint8))
        if snap.tau_c is not None:
            state.tau_history.append(snap.tau_c.copy().astype(np.float32))
    if snap.extra.get("total_energy") is not None:
        state.energy_history.append(
            (float(state.engine.sim_time),
             float(snap.extra["total_energy"])))
    keep = state.spacetime_window
    if len(state.spacetime_history) > keep:
        del state.spacetime_history[: len(state.spacetime_history) - keep]
        del state.tau_history[: len(state.tau_history) - keep]


def _render_image(state: GUIState, w: int, h: int) -> np.ndarray:
    if state.engine.spatial_dim == 1:
        return _render_1d_image(state, w, h)
    return _render_3d_slices_image(state, w, h)


def _render_1d_image(state: GUIState, w: int, h: int) -> np.ndarray:
    # Two-panel: top = spacetime (binary), bottom = tau_c heatmap
    if not state.spacetime_history:
        return np.zeros((w, h, 3), dtype=np.float32)
    spacetime = np.stack(state.spacetime_history, axis=0)
    tau = (np.stack(state.tau_history, axis=0)
           if state.tau_history else np.zeros_like(spacetime, dtype=np.float32))
    # Resize via nearest-neighbor sampling
    img = np.zeros((w, h, 3), dtype=np.float32)
    half = h // 2
    img[:, :half, :] = _resize_binary(spacetime, w, half)
    img[:, half:, :] = _resize_heatmap(tau, w, h - half)
    return img


def _render_3d_slices_image(state: GUIState, w: int, h: int) -> np.ndarray:
    engine = state.engine
    if not hasattr(engine, "get_slice"):
        return np.zeros((w, h, 3), dtype=np.float32)
    ix, iy, iz = state.slice_indices
    xy = engine.get_slice(axis=2, index=iz, field="phi")
    xz = engine.get_slice(axis=1, index=iy, field="phi")
    yz = engine.get_slice(axis=0, index=ix, field="phi")
    panel_w = w // 3
    img = np.zeros((w, h, 3), dtype=np.float32)
    img[0:panel_w, :, :] = _resize_field(xy, panel_w, h)
    img[panel_w:2 * panel_w, :, :] = _resize_field(xz, panel_w, h)
    img[2 * panel_w:, :, :] = _resize_field(yz, w - 2 * panel_w, h)
    return img


def _resize_binary(spacetime: np.ndarray, w: int, h: int) -> np.ndarray:
    H, W = spacetime.shape
    xs = (np.arange(w) * W / w).astype(np.int32)
    ys = (np.arange(h) * H / h).astype(np.int32)
    out = spacetime[ys[:, None], xs[None, :]].astype(np.float32)
    out_t = out.T  # (w, h)
    rgb = np.stack([out_t, out_t, out_t], axis=-1)
    return rgb


def _resize_heatmap(tau: np.ndarray, w: int, h: int) -> np.ndarray:
    H, W = tau.shape
    xs = (np.arange(w) * W / max(w, 1)).astype(np.int32)
    ys = (np.arange(h) * H / max(h, 1)).astype(np.int32)
    out = tau[ys[:, None], xs[None, :]].astype(np.float32)
    if out.max() > 0:
        out /= out.max()
    out_t = out.T
    rgb = np.stack([
        np.clip(out_t * 1.5, 0, 1),
        np.clip(out_t * 1.0 - 0.1, 0, 1),
        np.clip(out_t * 0.5 - 0.2, 0, 1),
    ], axis=-1)
    return rgb


def _resize_field(field2d: np.ndarray, w: int, h: int) -> np.ndarray:
    H, W = field2d.shape
    xs = (np.arange(w) * W / max(w, 1)).astype(np.int32)
    ys = (np.arange(h) * H / max(h, 1)).astype(np.int32)
    out = field2d[ys[:, None], xs[None, :]].astype(np.float32)
    vmin, vmax = float(out.min()), float(out.max())
    if vmax - vmin > 1e-9:
        norm = (out - vmin) / (vmax - vmin)
    else:
        norm = np.zeros_like(out)
    norm_t = norm.T
    rgb = np.stack([
        np.clip(0.267 + 0.6 * norm_t, 0, 1),
        np.clip(0.005 + 0.95 * norm_t, 0, 1),
        np.clip(0.329 + 0.4 * (1.0 - norm_t), 0, 1),
    ], axis=-1)
    return rgb


def _save_volume_image(state: GUIState, output_dir: Path | None) -> Path | None:
    engine = state.engine
    if engine.spatial_dim != 3 or not hasattr(engine, "get_volume_phi"):
        print("[VIZLAB] volume render requires a 3D engine")
        return None
    from ugp_viz.viz import figures
    base = Path(output_dir) if output_dir is not None else screenshots_dir()
    base.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = base / f"vol_{state.model}_step{engine.step_count}_{ts}.png"
    figures.plot_field_3d_volumetric(
        engine.get_volume_phi(), path,
        title=f"{state.model} step {engine.step_count} — volumetric",
        n_samples=96,
    )
    print(f"[VIZLAB] saved {path}")
    return path


def _save_isosurface_image(state: GUIState, output_dir: Path | None) -> Path | None:
    engine = state.engine
    if engine.spatial_dim != 3 or not hasattr(engine, "get_volume_phi"):
        print("[VIZLAB] isosurface requires a 3D engine")
        return None
    from ugp_viz.viz import figures
    base = Path(output_dir) if output_dir is not None else screenshots_dir()
    base.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = base / f"iso_{state.model}_step{engine.step_count}_{ts}.png"
    figures.plot_field_3d_isosurface(
        engine.get_volume_phi(), path,
        iso_level=0.0,
        title=f"{state.model} step {engine.step_count} — isosurface (φ=0)",
    )
    print(f"[VIZLAB] saved {path}")
    return path


def _save_video(state: GUIState, output_dir: Path | None) -> Path | None:
    if not state.spacetime_history:
        print("[VIZLAB] no spacetime history yet — run the engine first")
        return None
    from ugp_viz.viz.video import render_spacetime_video
    base = Path(output_dir) if output_dir is not None else videos_dir()
    base.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = base / f"video_{state.model}_step{state.engine.step_count}_{ts}.mp4"
    spacetime = np.stack(state.spacetime_history, axis=0)
    render_spacetime_video(spacetime, path, fps=30,
                           window=min(200, spacetime.shape[0]))
    print(f"[VIZLAB] saved {path}")
    return path


def _screenshot(state: GUIState, output_dir: Path | None) -> Path:
    from ugp_viz.viz import figures
    base = Path(output_dir) if output_dir is not None else screenshots_dir()
    base.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = f"snap_{state.model}_step{state.engine.step_count}_{ts}.png"
    path = base / name
    snap = state.engine.snapshot()
    if state.engine.spatial_dim == 3 and snap.extra.get("shape"):
        engine = state.engine
        figures.plot_field_3d_three_slice(
            engine.get_volume_phi(), path,
            title=f"{state.model} step {engine.step_count}",
            field_name="phi",
        )
    elif snap.phi is not None:
        figures.plot_field_1d(
            snap.phi, path,
            label="phi",
            title=f"{state.model} step {state.engine.step_count}",
        )
    elif snap.tape is not None and state.spacetime_history:
        st = np.stack(state.spacetime_history, axis=0)
        figures.plot_spacetime(st, path, title=f"{state.model}")
    return path


# ──────────────────────────────────────────────────────────────────────
# Matplotlib fallback backend
# ──────────────────────────────────────────────────────────────────────

def _run_matplotlib_gui(state: GUIState, output_dir: Path | None) -> None:
    import matplotlib
    # Try interactive backend; fallback to Agg if not available
    try:
        matplotlib.use("MacOSX")
    except Exception:
        try:
            matplotlib.use("TkAgg")
        except Exception:
            matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 7))
    ax_top = fig.add_subplot(2, 1, 1)
    ax_bot = fig.add_subplot(2, 1, 2)
    fig.suptitle(f"UGP VIZLAB — {state.model}")

    def _on_key(event):
        if event.key == " ":
            state.paused = not state.paused
        elif event.key == "r":
            state.engine.reset()
            state.spacetime_history.clear()
            state.tau_history.clear()
            if state.kink_tracker is not None:
                state.kink_tracker.clear()
            state.last_force_report = None
        elif event.key == "F12":
            _screenshot(state, output_dir)
        elif event.key == "v":
            _save_video(state, output_dir)
        elif event.key == "3":
            _save_volume_image(state, output_dir)
        elif event.key == "i":
            _save_isosurface_image(state, output_dir)
        elif event.key == "k":
            _auto_mark_kinks(state)
        elif event.key == "right":
            state.engine.step(state.substeps_per_frame)
            _record_spacetime(state)
            _update_kink_report(state)

    fig.canvas.mpl_connect("key_press_event", _on_key)

    print("Controls: space=pause, r=reset, right-arrow=step, F12=screenshot, "
          "v=save mp4, 3=volume PNG (3D), i=isosurface PNG (3D), "
          "k=auto-mark kinks (1D)")
    while True:
        if not state.paused:
            state.engine.step(state.substeps_per_frame)
            _record_spacetime(state)
            _update_kink_report(state)
        ax_top.cla()
        ax_bot.cla()
        snap = state.engine.snapshot()
        if state.engine.spatial_dim == 1:
            if state.spacetime_history:
                st = np.stack(state.spacetime_history, axis=0)
                ax_top.imshow(st, cmap="binary", aspect="auto",
                              interpolation="nearest", origin="upper")
                ax_top.set_title("Spacetime (last %d steps)" % len(state.spacetime_history))
            if state.tau_history:
                tau = np.stack(state.tau_history, axis=0)
                ax_bot.imshow(tau, cmap="hot", aspect="auto",
                              interpolation="nearest", origin="upper")
                ax_bot.set_title("tau_c heatmap")
        elif state.engine.spatial_dim == 3:
            engine = state.engine
            cx, cy, cz = state.slice_indices
            ax_top.imshow(engine.get_slice(axis=2, index=cz, field="phi").T,
                          cmap="viridis", origin="lower")
            ax_top.set_title(f"phi XY @ z={cz}")
            ax_bot.imshow(engine.get_slice(axis=1, index=cy, field="phi").T,
                          cmap="viridis", origin="lower")
            ax_bot.set_title(f"phi XZ @ y={cy}")
        ax_top.set_xlabel("Cell")
        ax_bot.set_xlabel("Cell")
        # Live kink force overlay (1D continuum only)
        if (state.engine.spatial_dim == 1
                and state.last_force_report is not None):
            report = state.last_force_report
            lines = []
            for site in report.get("sites", []):
                lines.append(f"{site['label']}: x={site['position']:.2f}")
            for pair in report.get("pairs", []):
                lines.append(
                    f"{pair['a']}-{pair['b']}: d={pair['separation']:.2f} "
                    f"F={pair['F_on_b']:+.2e}"
                )
            if lines:
                ax_top.text(
                    0.01, 0.98, "\n".join(lines),
                    transform=ax_top.transAxes,
                    va="top", ha="left",
                    fontsize=8, color="white",
                    bbox=dict(facecolor="black", alpha=0.45, pad=4),
                )
        plt.pause(0.02)
        if not plt.fignum_exists(fig.number):
            break
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="UGP VIZLAB GUI")
    parser.add_argument("--model", default="phimdl_1d", choices=list_models())
    parser.add_argument("--inject", default=None,
                        help="catalog spec, e.g. gen1_kink@256")
    parser.add_argument("--backend", default="auto",
                        choices=["auto", "taichi", "matplotlib"])
    parser.add_argument("--params", default=None,
                        help="key=val,key=val parameter overrides")
    args = parser.parse_args(argv)
    params = {}
    if args.params:
        for kv in args.params.split(","):
            if not kv.strip():
                continue
            k, v = kv.split("=", 1)
            params[k.strip()] = _coerce(v.strip())
    run_gui(model=args.model, params=params or None,
            initial_inject=args.inject, backend=args.backend)


def _coerce(v: str):
    try:
        if "." in v or "e" in v.lower():
            return float(v)
        return int(v)
    except ValueError:
        return v


if __name__ == "__main__":
    main()
