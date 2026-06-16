"""
Tkinter-based desktop GUI for VIZLAB.

This is the recommended GUI backend. It provides:

- Menubar (File / Edit / View / Help) with file-open/save dialogs.
- Embedded matplotlib canvas with the standard NavigationToolbar
  (zoom, pan, home, back/forward, save).
- Sidebar with:
    * model and engine parameters (introspected from each engine's
      ``default_params``)
    * initial-condition selector (introspected from each engine's
      ``supported_ic_kinds``)
    * transport controls: Run / Pause / Step / Stop / Reset
    * substeps-per-frame and target FPS
    * catalog injection list
    * file-bundle controls (Save Run, Load Run, Save Config, Load Config)
- Notes panel: a markdown editor on the left and a styled preview on the
  right; both update live. Notes can be loaded from an external file or
  saved alongside the run bundle.
- About modal showing the app name, author, year, website, repo, and
  license.

Implementation detail: the Tk event loop drives the simulation through
``root.after`` callbacks rather than a blocking ``while True`` loop, so
the UI stays responsive at all times. The default frame budget is
~33 ms (≈30 fps target), but the engine substep count per frame is
user-tunable.
"""

from __future__ import annotations

import json
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

import numpy as np

try:  # noqa: SIM105
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "Tkinter is required for the GUI backend. Install python3-tk "
        "or run with --backend matplotlib / --backend taichi."
    ) from exc

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure

from ugp_viz.about import APP_INFO
from ugp_viz.catalog.manager import list_entries
from ugp_viz.engines import (
    InitialCondition,
    InjectionSpec,
    SimEngine,
    build_engine,
    list_models,
)
from ugp_viz.notes import (
    Notes,
    load_notes,
    markdown_to_tk_segments,
    save_notes,
)
from ugp_viz.paths import (
    figures_dir,
    runs_dir,
    screenshots_dir,
    videos_dir,
)
from ugp_viz.state import RunBundle, load_run, rebuild_engine, save_run


# ─────────────────────────────────────────────────────────────────────────
# Per-model viz hints
# ─────────────────────────────────────────────────────────────────────────

# Sensible substeps-per-frame defaults so the canvas updates visibly without
# blowing the frame budget. CA engines look fine at 1 step / frame; continuum
# integrators at dt=0.01 need many more steps before any visual change.
_DEFAULT_SUBSTEPS: dict[str, int] = {
    "afca": 1,
    "fca_sync": 1,
    "z7_fmdl": 1,
    "phimdl_1d": 5,
    "z7_kg": 5,
    "phimdl_3d": 20,
}


def _default_substeps_for(model: str) -> int:
    return _DEFAULT_SUBSTEPS.get(model, 1)


def _is_continuum_1d(model: str) -> bool:
    """1D engines whose snapshot.phi carries a real (continuum) field."""
    return model in ("phimdl_1d", "z7_kg")


def _is_ca_categorical(model: str) -> bool:
    """1D CA engines whose tape carries multi-valued (non-binary) states."""
    return model == "z7_fmdl"


# Field views available for 3D engines. Order matters — used to populate
# the sidebar combobox in this order.
_FIELD_VIEWS_3D: tuple[str, ...] = ("phi", "energy", "kink_charge")


# ─────────────────────────────────────────────────────────────────────────
# Engine handle + simulation worker
# ─────────────────────────────────────────────────────────────────────────

class _SimWorker:
    """Owns the live engine and a rolling history of snapshots.

    The worker is single-threaded — all engine.step calls happen on the
    Tk thread inside ``frame_advance`` so we never touch numpy arrays
    from two threads at once. ``running`` is a simple flag controlled by
    Run/Pause/Stop buttons.
    """

    def __init__(self, model: str, params: dict[str, Any] | None = None,
                 ic_kind: str = "vacuum"):
        self.model = model
        self.engine: SimEngine = build_engine(model, params=params)
        self.ic_kind = ic_kind
        self.engine.reset(InitialCondition(kind=ic_kind))
        self.running = False
        self.history_spacetime: list[np.ndarray] = []
        self.history_tau: list[np.ndarray] = []
        self.history_energy: list[tuple[float, float]] = []
        self.window = 200
        self.substeps_per_frame = _default_substeps_for(model)
        self.kink_tracker = None
        self.last_force_report: dict | None = None
        if self.engine.spatial_dim == 1:
            from ugp_viz.analysis.kink_tracker import KinkTracker
            dx = float(self.engine.params.get("dx", 1.0))
            self.kink_tracker = KinkTracker(dx=dx)

    def reset_engine(self, ic_kind: str | None = None) -> None:
        kind = ic_kind or self.ic_kind
        self.engine.reset(InitialCondition(kind=kind))
        self.ic_kind = kind
        self.history_spacetime.clear()
        self.history_tau.clear()
        self.history_energy.clear()
        if self.kink_tracker is not None:
            self.kink_tracker.clear()
        self.last_force_report = None

    def step_once(self) -> None:
        self.engine.step(self.substeps_per_frame)
        self._record()

    def _record(self) -> None:
        snap = self.engine.snapshot()
        if snap.tape is not None:
            self.history_spacetime.append(snap.tape.copy())
            if snap.tau_c is not None:
                self.history_tau.append(snap.tau_c.copy())
        elif snap.phi is not None and snap.phi.ndim == 1:
            # Continuum 1D field: store the actual float values so the GUI
            # can render a real heatmap. (A previous version thresholded to
            # binary, which discarded amplitude and sign information.)
            self.history_spacetime.append(
                snap.phi.astype(np.float32, copy=True))
            if snap.tau_c is not None and snap.tau_c.ndim == 1:
                self.history_tau.append(
                    snap.tau_c.copy().astype(np.float32))
        if snap.extra.get("total_energy") is not None:
            self.history_energy.append((
                float(self.engine.sim_time),
                float(snap.extra["total_energy"]),
            ))
        if len(self.history_spacetime) > self.window:
            keep = len(self.history_spacetime) - self.window
            del self.history_spacetime[:keep]
            del self.history_tau[:keep]
        if self.kink_tracker is not None and self.kink_tracker.sites \
                and snap.energy_density is not None:
            self.kink_tracker.update(
                snap.energy_density, sim_time=self.engine.sim_time)
            self.last_force_report = self.kink_tracker.report(
                snap.energy_density)


# ─────────────────────────────────────────────────────────────────────────
# Notes editor — markdown source on the left, styled preview on the right
# ─────────────────────────────────────────────────────────────────────────

class _NotesPanel(ttk.Frame):
    """Two-pane notes editor with live styled preview."""

    def __init__(self, master, notes: Notes | None = None,
                 on_change=None) -> None:
        super().__init__(master)
        self.notes = notes or Notes.empty()
        self._on_change = on_change

        self._suppress_change = False  # used during programmatic mutations

        header = ttk.Frame(self)
        header.pack(fill=tk.X, side=tk.TOP)
        ttk.Label(header, text="Title:").pack(side=tk.LEFT, padx=(0, 4))
        self.title_var = tk.StringVar(value=self.notes.title)
        self.title_entry = ttk.Entry(header, textvariable=self.title_var)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.title_var.trace_add("write", lambda *_: self._notify_change())

        meta = ttk.Frame(self)
        meta.pack(fill=tk.X, side=tk.TOP, pady=(2, 2))
        self.meta_label = ttk.Label(meta, text="", foreground="#888")
        self.meta_label.pack(side=tk.LEFT)

        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        edit_frame = ttk.Frame(paned)
        ttk.Label(edit_frame, text="Markdown source").pack(anchor=tk.W)
        self.editor = ScrolledText(edit_frame, wrap=tk.WORD,
                                   font=("Menlo", 11), undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.insert("1.0", self.notes.text)
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        paned.add(edit_frame, weight=1)

        view_frame = ttk.Frame(paned)
        ttk.Label(view_frame, text="Preview").pack(anchor=tk.W)
        self.preview = ScrolledText(view_frame, wrap=tk.WORD, state=tk.DISABLED,
                                    font=("Helvetica", 12), background="#fafafa")
        self.preview.pack(fill=tk.BOTH, expand=True)
        _configure_markdown_tags(self.preview)
        paned.add(view_frame, weight=1)

        self._refresh_preview()
        self._refresh_meta()

    def _on_editor_modified(self, _event=None) -> None:
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        if self._suppress_change:
            return
        self._refresh_preview()
        self._notify_change()

    def _notify_change(self) -> None:
        if self._suppress_change:
            return
        if self._on_change is not None:
            self._on_change()

    def _refresh_preview(self) -> None:
        text = self.editor.get("1.0", tk.END).rstrip()
        self.preview.configure(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        for seg, tags in markdown_to_tk_segments(text):
            self.preview.insert(tk.END, seg, tags)
        self.preview.configure(state=tk.DISABLED)

    def _refresh_meta(self) -> None:
        bits: list[str] = []
        if self.notes.modified:
            bits.append(f"modified {self.notes.modified}")
        if self.notes.created and self.notes.created != self.notes.modified:
            bits.append(f"created {self.notes.created}")
        if self.notes.author:
            bits.append(f"by {self.notes.author}")
        if self.notes.tags:
            bits.append("tags: " + ", ".join(self.notes.tags))
        self.meta_label.configure(text=" · ".join(bits))

    def commit(self) -> Notes:
        """Flush the editor into the underlying Notes object and return it."""
        self.notes.title = self.title_var.get()
        self.notes.text = self.editor.get("1.0", tk.END).rstrip()
        self.notes.touch()
        self._refresh_meta()
        return self.notes

    def replace_notes(self, new_notes: Notes) -> None:
        # Suppress change-propagation while we mutate the widgets — the
        # trace on title_var and the editor's <<Modified>> would otherwise
        # call back into commit() with the old (empty) editor contents and
        # clobber the new notes' text.
        self._suppress_change = True
        try:
            self.notes = new_notes
            self.title_var.set(new_notes.title)
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", new_notes.text)
            self.editor.edit_modified(False)
            self._refresh_preview()
            self._refresh_meta()
        finally:
            self._suppress_change = False


def _configure_markdown_tags(widget: tk.Text) -> None:
    widget.tag_configure("h1", font=("Helvetica", 18, "bold"),
                         spacing1=8, spacing3=4)
    widget.tag_configure("h2", font=("Helvetica", 15, "bold"),
                         spacing1=6, spacing3=3)
    widget.tag_configure("h3", font=("Helvetica", 13, "bold"),
                         spacing1=4, spacing3=2)
    widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
    widget.tag_configure("italic", font=("Helvetica", 12, "italic"))
    widget.tag_configure("code", font=("Menlo", 11), background="#eef")
    widget.tag_configure("codeblock", font=("Menlo", 11),
                         background="#f4f4f4",
                         lmargin1=20, lmargin2=20, spacing1=4, spacing3=4)
    widget.tag_configure("bullet", font=("Helvetica", 12), lmargin1=20,
                         lmargin2=40)
    widget.tag_configure("link", foreground="#1a4fbf",
                         font=("Helvetica", 12, "underline"))
    widget.tag_configure("quote", foreground="#555",
                         font=("Helvetica", 12, "italic"),
                         lmargin1=20, lmargin2=20)
    widget.tag_configure("hr", foreground="#bbb")
    widget.tag_configure("normal", font=("Helvetica", 12))


# ─────────────────────────────────────────────────────────────────────────
# Parameter editor — auto-generates a form from each engine's defaults
# ─────────────────────────────────────────────────────────────────────────

class _ParameterEditor(ttk.LabelFrame):
    """Form fields for a single engine's parameters."""

    def __init__(self, master, engine: SimEngine,
                 on_apply=None) -> None:
        super().__init__(master, text="Engine parameters")
        self._engine = engine
        self._on_apply = on_apply
        self._vars: dict[str, tk.StringVar] = {}
        for row, (key, val) in enumerate(engine.default_params.items()):
            current = engine.params.get(key, val)
            ttk.Label(self, text=key).grid(row=row, column=0,
                                            sticky=tk.W, padx=2, pady=1)
            v = tk.StringVar(value=str(current))
            self._vars[key] = v
            entry = ttk.Entry(self, textvariable=v, width=14)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=2, pady=1)
        self.columnconfigure(1, weight=1)
        ttk.Button(self, text="Apply (rebuilds engine)",
                   command=self._apply).grid(row=row + 1, column=0,
                                              columnspan=2, pady=(6, 2),
                                              sticky=tk.EW)

    def _apply(self) -> None:
        new_params: dict[str, Any] = {}
        for key, var in self._vars.items():
            default_val = self._engine.default_params[key]
            raw = var.get().strip()
            try:
                new_params[key] = _coerce_like(default_val, raw)
            except ValueError as exc:
                messagebox.showerror(
                    "Invalid parameter",
                    f"{key}: {exc}")
                return
        if self._on_apply is not None:
            self._on_apply(new_params)

    def current_params(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, var in self._vars.items():
            default_val = self._engine.default_params[key]
            try:
                out[key] = _coerce_like(default_val, var.get().strip())
            except ValueError:
                out[key] = default_val
        return out


def _coerce_like(template: Any, raw: str) -> Any:
    if isinstance(template, bool):
        if raw.lower() in ("true", "1", "yes", "on"):
            return True
        if raw.lower() in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"expected a boolean, got '{raw}'")
    if isinstance(template, int):
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"expected an integer, got '{raw}'") from exc
    if isinstance(template, float):
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f"expected a number, got '{raw}'") from exc
    return raw


# ─────────────────────────────────────────────────────────────────────────
# About modal
# ─────────────────────────────────────────────────────────────────────────

def _open_about_dialog(parent: tk.Misc) -> None:
    info = APP_INFO
    win = tk.Toplevel(parent)
    win.title(f"About {info['name']}")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    frm = ttk.Frame(win, padding=20)
    frm.pack()

    ttk.Label(frm, text=info["name"], font=("Helvetica", 20, "bold")
              ).pack(anchor=tk.W)
    ttk.Label(frm, text=info["subtitle"], font=("Helvetica", 13, "italic"),
              foreground="#555").pack(anchor=tk.W, pady=(0, 8))
    ttk.Label(frm, text=info["byline"], font=("Helvetica", 12)
              ).pack(anchor=tk.W)
    ttk.Label(frm, text=info["programme"], font=("Helvetica", 12)
              ).pack(anchor=tk.W, pady=(0, 8))

    def _add_link(label: str, url: str) -> None:
        row = ttk.Frame(frm)
        row.pack(anchor=tk.W, fill=tk.X)
        ttk.Label(row, text=f"{label}:").pack(side=tk.LEFT)
        lbl = tk.Label(row, text=url, fg="#1a4fbf", cursor="hand2",
                       font=("Helvetica", 12, "underline"))
        lbl.pack(side=tk.LEFT, padx=(4, 0))
        lbl.bind("<Button-1>", lambda _e, u=url: webbrowser.open(u))

    _add_link("Website", info["website"])
    _add_link("Repository", info["repository"])

    ttk.Separator(frm, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
    ttk.Label(frm, text=info["description"], wraplength=480,
              justify=tk.LEFT).pack(anchor=tk.W)
    ttk.Label(frm, text=f"License: {info['license']}",
              foreground="#555").pack(anchor=tk.W, pady=(8, 0))
    ttk.Label(frm, text=f"Version: {info['version']}",
              foreground="#555").pack(anchor=tk.W)

    ttk.Button(frm, text="Close", command=win.destroy).pack(pady=(12, 0))


# ─────────────────────────────────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────────────────────────────────

class VizLabApp:
    """Top-level Tk application."""

    def __init__(self, model: str = "phimdl_1d",
                 params: dict[str, Any] | None = None,
                 initial_inject: str | None = None,
                 ic_kind: str = "vacuum",
                 notes: Notes | None = None) -> None:
        self.root = tk.Tk()
        self.root.title(f"UGP VIZLAB — {model}")
        self.root.geometry("1400x900")

        self.worker = _SimWorker(model=model, params=params, ic_kind=ic_kind)
        if initial_inject:
            self.worker.engine.inject(InjectionSpec.from_string(initial_inject))
        self.notes_obj = notes or Notes.empty()

        self._build_menubar()
        self._build_layout()
        self._build_sidebar()
        self._build_canvas()
        self._build_notes_panel()
        self._build_status_bar()

        self._frame_period_ms = 33  # ~30 fps target
        self._stopped = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.root.after(self._frame_period_ms, self._tick)

    # ── layout ──────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        self.outer = ttk.Frame(self.root)
        self.outer.pack(fill=tk.BOTH, expand=True)

        self.main_pane = ttk.Panedwindow(self.outer, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.sidebar = ttk.Frame(self.main_pane, width=320)
        self.main_pane.add(self.sidebar, weight=0)

        self.right_pane = ttk.Panedwindow(self.main_pane, orient=tk.VERTICAL)
        self.main_pane.add(self.right_pane, weight=1)

    # ── menubar ─────────────────────────────────────────────────────
    def _build_menubar(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Save Run…", command=self._save_run_dialog)
        file_menu.add_command(label="Open Run…", command=self._open_run_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Save Experiment Config…",
                              command=self._save_config_dialog)
        file_menu.add_command(label="Load Experiment Config…",
                              command=self._load_config_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Open Notes…",
                              command=self._open_notes_dialog)
        file_menu.add_command(label="Save Notes…",
                              command=self._save_notes_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._on_quit)
        menubar.add_cascade(label="File", menu=file_menu)

        sim_menu = tk.Menu(menubar, tearoff=False)
        sim_menu.add_command(label="Run / Pause",
                             command=self._toggle_run)
        sim_menu.add_command(label="Step one frame",
                             command=self._step_one)
        sim_menu.add_command(label="Stop",
                             command=self._stop_sim)
        sim_menu.add_command(label="Reset",
                             command=self._reset_sim)
        menubar.add_cascade(label="Simulation", menu=sim_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Reset zoom / pan",
                              command=self._reset_view)
        view_menu.add_command(label="Save screenshot",
                              command=self._screenshot)
        view_menu.add_command(label="Save MP4 (spacetime)",
                              command=self._save_video)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About UGP VIZLAB",
                              command=lambda: _open_about_dialog(self.root))
        help_menu.add_command(label="Open repository",
                              command=lambda: webbrowser.open(
                                  APP_INFO["repository"]))
        help_menu.add_command(label="Author website",
                              command=lambda: webbrowser.open(
                                  APP_INFO["website"]))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ── sidebar (model, IC, params, transport, catalog) ─────────────
    def _build_sidebar(self) -> None:
        side = self.sidebar

        # Model selector
        model_frame = ttk.LabelFrame(side, text="Model")
        model_frame.pack(fill=tk.X, padx=4, pady=4)
        self.model_var = tk.StringVar(value=self.worker.model)
        ttk.Combobox(model_frame, textvariable=self.model_var,
                     values=list_models(), state="readonly"
                     ).pack(fill=tk.X, padx=4, pady=4)
        self.model_var.trace_add("write", lambda *_: self._switch_model())

        # IC selector
        ic_frame = ttk.LabelFrame(side, text="Initial condition")
        ic_frame.pack(fill=tk.X, padx=4, pady=4)
        self.ic_var = tk.StringVar(value=self.worker.ic_kind)
        self.ic_combo = ttk.Combobox(ic_frame, textvariable=self.ic_var,
                                     values=list(self.worker.engine.supported_ic_kinds),
                                     state="readonly")
        self.ic_combo.pack(fill=tk.X, padx=4, pady=4)

        # 3D field-view selector (φ / energy / |∇φ|²) — only shown when
        # the active engine has a slice viewer. Built unconditionally so
        # ``_refresh_field_view_visibility`` can pack/unpack it at will.
        self.field_view_frame = ttk.LabelFrame(side, text="3D field view")
        self.field_view_var = tk.StringVar(value="phi")
        self.field_view_combo = ttk.Combobox(
            self.field_view_frame, textvariable=self.field_view_var,
            values=list(_FIELD_VIEWS_3D), state="readonly")
        self.field_view_combo.pack(fill=tk.X, padx=4, pady=4)
        self.field_view_var.trace_add(
            "write", lambda *_: self._draw())

        # Param editor (auto-generated from engine.default_params)
        self.param_editor = _ParameterEditor(
            side, self.worker.engine, on_apply=self._apply_params)
        self.param_editor.pack(fill=tk.X, padx=4, pady=4)
        # Now that param_editor exists we can pack the 3D-view selector at
        # the correct position (between IC and params) when applicable.
        self._refresh_field_view_visibility()

        # Transport controls
        ctl = ttk.LabelFrame(side, text="Simulation")
        ctl.pack(fill=tk.X, padx=4, pady=4)
        self.run_btn = ttk.Button(ctl, text="▶ Run",
                                  command=self._toggle_run)
        self.run_btn.grid(row=0, column=0, padx=2, pady=2, sticky=tk.EW)
        ttk.Button(ctl, text="Step", command=self._step_one
                   ).grid(row=0, column=1, padx=2, pady=2, sticky=tk.EW)
        ttk.Button(ctl, text="Stop", command=self._stop_sim
                   ).grid(row=1, column=0, padx=2, pady=2, sticky=tk.EW)
        ttk.Button(ctl, text="Reset", command=self._reset_sim
                   ).grid(row=1, column=1, padx=2, pady=2, sticky=tk.EW)
        ctl.columnconfigure(0, weight=1)
        ctl.columnconfigure(1, weight=1)

        # Substeps and window
        rate = ttk.LabelFrame(side, text="Rate")
        rate.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(rate, text="Substeps / frame").grid(row=0, column=0,
                                                      sticky=tk.W)
        self.substeps_var = tk.IntVar(value=self.worker.substeps_per_frame)
        ttk.Spinbox(rate, from_=1, to=256, textvariable=self.substeps_var,
                    width=6, command=self._sync_rate
                    ).grid(row=0, column=1, sticky=tk.EW)
        ttk.Label(rate, text="Spacetime window").grid(row=1, column=0,
                                                      sticky=tk.W)
        self.window_var = tk.IntVar(value=self.worker.window)
        ttk.Spinbox(rate, from_=10, to=4000, textvariable=self.window_var,
                    width=6, command=self._sync_rate
                    ).grid(row=1, column=1, sticky=tk.EW)
        rate.columnconfigure(1, weight=1)

        # Catalog injection list
        cat = ttk.LabelFrame(side, text="Inject from catalog")
        cat.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        ttk.Label(cat, text="Position:").pack(anchor=tk.W)
        self.inject_pos_var = tk.StringVar(value="center")
        ttk.Entry(cat, textvariable=self.inject_pos_var, width=10
                  ).pack(fill=tk.X, padx=2)
        self.catalog_list = tk.Listbox(cat, height=12)
        self.catalog_list.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        ttk.Button(cat, text="Inject selected",
                   command=self._inject_selected
                   ).pack(fill=tk.X, padx=2, pady=2)
        self._refresh_catalog()

    # ── canvas + nav toolbar (zoom/pan) ─────────────────────────────
    def _build_canvas(self) -> None:
        canvas_frame = ttk.Frame(self.right_pane)
        self.right_pane.add(canvas_frame, weight=3)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, canvas_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._init_axes()

    def _init_axes(self) -> None:
        self.fig.clear()
        eng = self.worker.engine
        if eng.spatial_dim == 1:
            self.ax_top = self.fig.add_subplot(2, 1, 1)
            self.ax_bot = self.fig.add_subplot(2, 1, 2)
            self.ax_third = None
        else:
            self.ax_top = self.fig.add_subplot(1, 2, 1)
            self.ax_bot = self.fig.add_subplot(1, 2, 2)
            self.ax_third = None
        self.fig.tight_layout()
        self.canvas.draw_idle()

    # ── notes panel ─────────────────────────────────────────────────
    def _build_notes_panel(self) -> None:
        notes_frame = ttk.LabelFrame(self.right_pane, text="Notes (markdown)")
        self.right_pane.add(notes_frame, weight=1)
        self.notes_panel = _NotesPanel(notes_frame, notes=self.notes_obj,
                                       on_change=self._on_notes_changed)
        self.notes_panel.pack(fill=tk.BOTH, expand=True)

    # ── status bar ──────────────────────────────────────────────────
    def _build_status_bar(self) -> None:
        bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value="ready.")
        ttk.Label(bar, textvariable=self.status_var, anchor=tk.W
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.fps_var = tk.StringVar(value="0 fps")
        ttk.Label(bar, textvariable=self.fps_var, anchor=tk.E
                  ).pack(side=tk.RIGHT, padx=4)
        self._frame_counter = 0
        self._last_fps_t = time.time()

    # ── transport ───────────────────────────────────────────────────
    def _toggle_run(self) -> None:
        self.worker.running = not self.worker.running
        self.run_btn.configure(
            text="❚❚ Pause" if self.worker.running else "▶ Run")
        self.status_var.set("running" if self.worker.running else "paused")

    def _step_one(self) -> None:
        self.worker.step_once()
        self._draw()

    def _stop_sim(self) -> None:
        self.worker.running = False
        self.run_btn.configure(text="▶ Run")
        self.status_var.set("stopped")

    def _reset_sim(self) -> None:
        self.worker.reset_engine(self.ic_var.get())
        self._draw()
        self.status_var.set(f"reset ({self.ic_var.get()})")

    def _sync_rate(self) -> None:
        try:
            self.worker.substeps_per_frame = max(1, int(self.substeps_var.get()))
        except (TypeError, tk.TclError):
            pass
        try:
            self.worker.window = max(10, int(self.window_var.get()))
        except (TypeError, tk.TclError):
            pass

    # ── model / param switching ─────────────────────────────────────
    def _refresh_field_view_visibility(self) -> None:
        """Show the 3D-field-view selector only for ≥2D engines.

        Anchored via ``before=self.param_editor`` so the widget always sits
        between the IC selector and the parameter editor, regardless of
        repack ordering from earlier model/parameter switches.
        """
        if not hasattr(self, "field_view_frame") \
                or not hasattr(self, "param_editor"):
            return
        if self.worker.engine.spatial_dim >= 2:
            self.field_view_frame.pack(fill=tk.X, padx=4, pady=4,
                                       before=self.param_editor)
        else:
            self.field_view_frame.pack_forget()

    def _switch_model(self) -> None:
        new_model = self.model_var.get()
        if new_model == self.worker.model:
            return
        self.worker = _SimWorker(model=new_model,
                                 ic_kind=self.ic_var.get())
        self.root.title(f"UGP VIZLAB — {new_model}")
        # Replace param editor and IC selector
        self.param_editor.destroy()
        self.param_editor = _ParameterEditor(
            self.sidebar, self.worker.engine,
            on_apply=self._apply_params)
        # Re-pack at the same place (third child of sidebar)
        self.param_editor.pack(fill=tk.X, padx=4, pady=4,
                               after=self.sidebar.winfo_children()[1])
        self.ic_combo.configure(
            values=list(self.worker.engine.supported_ic_kinds))
        if self.ic_var.get() not in self.worker.engine.supported_ic_kinds:
            self.ic_var.set(self.worker.engine.supported_ic_kinds[0])
        self._refresh_field_view_visibility()
        if hasattr(self, "substeps_var"):
            self.substeps_var.set(self.worker.substeps_per_frame)
        self._refresh_catalog()
        self._init_axes()
        self.status_var.set(f"switched to {new_model}")

    def _apply_params(self, new_params: dict[str, Any]) -> None:
        # Preserve the user's current rate choice across rebuilds; only
        # full model switches should snap back to the model default.
        old_substeps = self.worker.substeps_per_frame
        self.worker = _SimWorker(model=self.worker.model,
                                 params=new_params,
                                 ic_kind=self.ic_var.get())
        self.worker.substeps_per_frame = old_substeps
        self._refresh_field_view_visibility()
        self._refresh_catalog()
        self._init_axes()
        self.status_var.set(
            "parameters applied; engine rebuilt")

    def _refresh_catalog(self) -> None:
        self.catalog_list.delete(0, tk.END)
        for name in list_entries(self.worker.model):
            self.catalog_list.insert(tk.END, name)

    def _inject_selected(self) -> None:
        idx = self.catalog_list.curselection()
        if not idx:
            self.status_var.set("select a catalog entry first")
            return
        kind = self.catalog_list.get(idx[0])
        pos_raw = self.inject_pos_var.get().strip()
        engine = self.worker.engine
        if pos_raw in ("", "center"):
            if engine.spatial_dim == 1:
                pos = int(engine.params.get("L", engine.params.get("N", 256))) // 2
            else:
                pos = (int(engine.params["Nx"]) // 2,
                       int(engine.params["Ny"]) // 2,
                       int(engine.params["Nz"]) // 2)
        else:
            try:
                pos = int(pos_raw)
            except ValueError:
                self.status_var.set(f"invalid position '{pos_raw}'")
                return
        try:
            engine.inject(InjectionSpec(kind=kind, position=pos))
        except Exception as exc:
            # Surface engine-side injection errors instead of letting Tk
            # swallow them silently (which previously left the field at
            # vacuum and looked indistinguishable from "nothing happened").
            self.status_var.set(
                f"inject {kind} failed: {type(exc).__name__}: {exc}")
            return
        self.status_var.set(f"injected {kind} @ {pos}")
        self._draw()

    # ── notes lifecycle ─────────────────────────────────────────────
    def _on_notes_changed(self) -> None:
        # Soft sync: keep the worker's notes object up to date so quick
        # Save-Run picks up edits without an explicit commit.
        self.notes_panel.commit()
        self.notes_obj = self.notes_panel.notes

    def _open_notes_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Open notes",
            filetypes=[("Markdown", "*.md"), ("Notes JSON", "*.json"),
                       ("All files", "*.*")],
            initialdir=str(runs_dir()),
        )
        if not path:
            return
        try:
            notes = load_notes(path)
        except Exception as exc:
            messagebox.showerror("Open notes failed", str(exc))
            return
        self.notes_panel.replace_notes(notes)
        self.notes_obj = notes
        self.status_var.set(f"loaded notes from {Path(path).name}")

    def _save_notes_dialog(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save notes",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Notes JSON", "*.json")],
            initialdir=str(runs_dir()),
        )
        if not path:
            return
        notes = self.notes_panel.commit()
        out = save_notes(path, notes)
        self.status_var.set(f"saved notes to {out.name}")

    # ── run + config persistence ────────────────────────────────────
    def _save_run_dialog(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save run bundle",
            defaultextension=".run.json",
            filetypes=[("Run manifest", "*.run.json"),
                       ("JSON", "*.json")],
            initialdir=str(runs_dir() / "data"),
        )
        if not path:
            return
        stem = Path(path)
        if stem.name.endswith(".run.json"):
            stem = stem.with_name(stem.name[: -len(".run.json")])
        else:
            stem = stem.with_suffix("")
        notes = self.notes_panel.commit()
        spacetime = (np.stack(self.worker.history_spacetime, axis=0)
                     if self.worker.history_spacetime else None)
        history = {
            "time": [t for t, _ in self.worker.history_energy],
            "energy": [e for _, e in self.worker.history_energy],
        }
        manifest = {
            "model": self.worker.model,
            "params": dict(self.worker.engine.params),
            "step": int(self.worker.engine.step_count),
            "time": float(self.worker.engine.sim_time),
            "ic_kind": self.worker.ic_kind,
            "history": history,
            "artifacts": {},
        }
        save_run(stem=stem, manifest=manifest,
                 spacetime=spacetime, engine=self.worker.engine,
                 notes=notes if not notes.is_empty() else None)
        self.status_var.set(f"saved run to {stem.name}.run.json")

    def _open_run_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Open run bundle",
            filetypes=[("Run manifest", "*.run.json"),
                       ("JSON", "*.json")],
            initialdir=str(runs_dir() / "data"),
        )
        if not path:
            return
        try:
            bundle: RunBundle = load_run(path)
        except Exception as exc:
            messagebox.showerror("Open run failed", str(exc))
            return
        try:
            engine = rebuild_engine(bundle)
        except Exception as exc:
            messagebox.showerror("Restore engine failed", str(exc))
            return
        # Reseat the worker on the restored engine.
        self.worker.engine = engine
        self.worker.model = bundle.model
        self.worker.ic_kind = bundle.manifest.get("ic_kind", "vacuum")
        self.worker.history_spacetime = (
            list(bundle.spacetime) if bundle.spacetime is not None else [])
        self.worker.history_tau = []
        self.worker.history_energy = list(zip(
            bundle.history.get("time", []),
            bundle.history.get("energy", []),
        ))
        self.notes_panel.replace_notes(bundle.notes)
        self.notes_obj = bundle.notes
        self.model_var.set(bundle.model)
        self._init_axes()
        self._draw()
        self.status_var.set(f"loaded run {bundle.stem.name}")

    def _save_config_dialog(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save experiment config",
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml *.yml"), ("All files", "*.*")],
            initialdir=str(runs_dir() / "configs"),
        )
        if not path:
            return
        from ugp_viz.experiments.runner import save_experiment_config
        cfg = {
            "model": self.worker.model,
            "params": dict(self.worker.engine.params),
            "initial_condition": {"kind": self.ic_var.get()},
            "steps": 1000,
            "sample_every": 1,
        }
        notes = self.notes_panel.commit()
        save_experiment_config(path, cfg,
                               notes=notes if not notes.is_empty() else None)
        self.status_var.set(f"saved config to {Path(path).name}")

    def _load_config_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Load experiment config",
            filetypes=[("YAML", "*.yaml *.yml"), ("All files", "*.*")],
            initialdir=str(runs_dir() / "configs"),
        )
        if not path:
            return
        from ugp_viz.experiments.runner import load_yaml
        try:
            cfg = load_yaml(path)
        except Exception as exc:
            messagebox.showerror("Load config failed", str(exc))
            return
        model = cfg.get("model", self.worker.model)
        params = cfg.get("params", {}) or {}
        ic_kind = (cfg.get("initial_condition") or {}).get("kind", "vacuum")
        self.worker = _SimWorker(model=model, params=params, ic_kind=ic_kind)
        # Refresh sidebar
        self.model_var.set(model)
        self._switch_model()  # rebuilds editor + catalog + axes
        self.ic_var.set(ic_kind)
        # Inject any catalog entries listed in the config
        for inj in cfg.get("injections", []) or []:
            self.worker.engine.inject(InjectionSpec(
                kind=inj["kind"],
                position=inj.get("position"),
                velocity=inj.get("velocity"),
                params=inj.get("params") or {},
            ))
        # Notes (either inline or as a sidecar .notes.md alongside the YAML)
        notes_cfg = cfg.get("notes")
        notes_obj: Notes | None = None
        if isinstance(notes_cfg, dict):
            notes_obj = Notes.from_dict(notes_cfg)
        elif isinstance(notes_cfg, str):
            notes_obj = Notes(text=notes_cfg)
        else:
            sidecar = Path(path).with_suffix(".notes.md")
            if sidecar.exists():
                notes_obj = load_notes(sidecar)
        if notes_obj is not None:
            self.notes_panel.replace_notes(notes_obj)
            self.notes_obj = notes_obj
        self.status_var.set(f"loaded config {Path(path).name}")

    # ── view helpers ────────────────────────────────────────────────
    def _reset_view(self) -> None:
        if hasattr(self.toolbar, "home"):
            self.toolbar.home()

    def _screenshot(self) -> None:
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y%m%d_%H%M%S")
        path = screenshots_dir() / (
            f"viz_{self.worker.model}_step{self.worker.engine.step_count}_{ts}.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=120, bbox_inches="tight")
        self.status_var.set(f"screenshot {path.name}")

    def _save_video(self) -> None:
        if not self.worker.history_spacetime:
            self.status_var.set("no spacetime history yet — run engine first")
            return
        from ugp_viz.viz.video import render_spacetime_video
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y%m%d_%H%M%S")
        path = videos_dir() / (
            f"viz_{self.worker.model}_step{self.worker.engine.step_count}_{ts}.mp4")
        path.parent.mkdir(parents=True, exist_ok=True)
        spacetime = np.stack(self.worker.history_spacetime, axis=0)
        render_spacetime_video(spacetime, path, fps=30,
                               window=min(self.worker.window,
                                          spacetime.shape[0]))
        self.status_var.set(f"video {path.name}")

    # ── animation tick ──────────────────────────────────────────────
    def _tick(self) -> None:
        if self._stopped:
            return
        if self.worker.running:
            self.worker.step_once()
            self._draw()
        self._frame_counter += 1
        now = time.time()
        if now - self._last_fps_t > 0.5:
            fps = self._frame_counter / (now - self._last_fps_t)
            self.fps_var.set(f"{fps:.0f} fps · step {self.worker.engine.step_count}")
            self._frame_counter = 0
            self._last_fps_t = now
        self.root.after(self._frame_period_ms, self._tick)

    def _draw(self) -> None:
        ax_top, ax_bot = self.ax_top, self.ax_bot
        ax_top.clear()
        ax_bot.clear()
        engine = self.worker.engine
        model = self.worker.model
        if engine.spatial_dim == 1:
            self._draw_1d(model, engine, ax_top, ax_bot)
        else:
            self._draw_3d(model, engine, ax_top, ax_bot)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _draw_1d(self, model, engine, ax_top, ax_bot) -> None:
        if self.worker.history_spacetime:
            st = np.stack(self.worker.history_spacetime, axis=0)
            if _is_continuum_1d(model):
                # Real-valued φ field: diverging colormap, centred on the
                # midpoint between the two SG vacua at φ = 0 and φ = 2π/N.
                Nsym = int(engine.params.get(
                    "N_phi", engine.params.get("N_sym", 7)))
                vac = 2.0 * np.pi / max(Nsym, 1)
                ax_top.imshow(
                    st, cmap="RdBu_r", aspect="auto",
                    interpolation="nearest", origin="upper",
                    vmin=0.0, vmax=vac,
                )
                ax_top.set_title(
                    f"φ field  (0 = vacuum_low, 2π/{Nsym} ≈ {vac:.3f} = "
                    f"vacuum_high; last {st.shape[0]} samples)")
            elif _is_ca_categorical(model):
                # Z₇ CA: discrete 7-level palette so individual states are
                # distinguishable instead of blending into greyscale.
                ax_top.imshow(
                    st, cmap="tab10", aspect="auto",
                    interpolation="nearest", origin="upper",
                    vmin=0, vmax=9,
                )
                ax_top.set_title(
                    f"Z₇ state  (0 = vacuum; last {st.shape[0]} samples)")
            else:
                # Binary CA (afca, fca_sync, ...): on/off states.
                ax_top.imshow(
                    st, cmap="binary", aspect="auto",
                    interpolation="nearest", origin="upper",
                )
                ax_top.set_title(f"Spacetime (last {st.shape[0]} samples)")
            ax_top.set_xlabel("Cell")
            ax_top.set_ylabel("Step (newest = bottom)")
        if self.worker.history_tau:
            tau = np.stack(self.worker.history_tau, axis=0)
            ax_bot.imshow(tau, cmap="hot", aspect="auto",
                          interpolation="nearest", origin="upper")
            ax_bot.set_title("τ_c heatmap")
            ax_bot.set_xlabel("Cell")
            ax_bot.set_ylabel("Step")
        else:
            # Continuum 1D engines emit no τ_c stream into history_tau.
            # Show the latest φ profile as a line plot instead, which is
            # more legible than a blank panel.
            if self.worker.history_spacetime and _is_continuum_1d(model):
                latest = self.worker.history_spacetime[-1]
                ax_bot.plot(latest, color="#1f77b4", linewidth=1.2)
                Nsym = int(engine.params.get(
                    "N_phi", engine.params.get("N_sym", 7)))
                vac = 2.0 * np.pi / max(Nsym, 1)
                ax_bot.axhline(0.0, color="grey", linewidth=0.5, alpha=0.5)
                ax_bot.axhline(vac, color="grey", linewidth=0.5, alpha=0.5)
                ax_bot.set_ylim(-0.1 * vac, 1.1 * vac)
                ax_bot.set_title("Latest φ(x)")
                ax_bot.set_xlabel("Cell")
                ax_bot.set_ylabel("φ")
        if self.worker.last_force_report is not None:
            lines = []
            for site in self.worker.last_force_report.get("sites", []):
                lines.append(
                    f"{site['label']}: x={site['position']:.2f}")
            for pair in self.worker.last_force_report.get("pairs", []):
                lines.append(
                    f"{pair['a']}-{pair['b']}: d={pair['separation']:.2f} "
                    f"F={pair['F_on_b']:+.2e}")
            if lines:
                ax_top.text(
                    0.01, 0.98, "\n".join(lines),
                    transform=ax_top.transAxes, va="top", ha="left",
                    fontsize=8, color="white",
                    bbox=dict(facecolor="black", alpha=0.55, pad=4))

    def _draw_3d(self, model, engine, ax_top, ax_bot) -> None:
        if not hasattr(engine, "get_slice"):
            ax_top.text(
                0.5, 0.5, "3D engine has no slice viewer",
                ha="center", va="center", transform=ax_top.transAxes)
            return
        view = (self.field_view_var.get()
                if hasattr(self, "field_view_var") else "phi")
        if view not in _FIELD_VIEWS_3D:
            view = "phi"
        Nz = int(engine.params.get("Nz", 64))
        Ny = int(engine.params.get("Ny", 64))
        z = Nz // 2
        y = Ny // 2
        Nphi = int(engine.params.get("N_phi", 7))
        if view == "phi":
            vmax = 2.0 * np.pi / max(Nphi, 1)
            vmin, cmap, label = 0.0, "RdBu_r", "φ"
        else:
            # Energy / kink charge: derive vmax from a percentile of the
            # current full volume so small features stay visible without
            # being washed out by the autoscale.
            if view == "energy":
                vol = engine.get_volume_energy()
                cmap, label = "magma", "energy density"
            else:
                vol = engine._kink_charge_density()
                cmap, label = "magma", "|∇φ|² (kink charge)"
            vmax = float(np.percentile(np.abs(vol), 99.5)) or 1.0
            vmin = 0.0
        ax_top.imshow(
            engine.get_slice(axis=2, index=z, field=view).T,
            cmap=cmap, origin="lower", vmin=vmin, vmax=vmax,
        )
        ax_top.set_title(f"{label} · XY @ z={z}")
        ax_bot.imshow(
            engine.get_slice(axis=1, index=y, field=view).T,
            cmap=cmap, origin="lower", vmin=vmin, vmax=vmax,
        )
        ax_bot.set_title(f"{label} · XZ @ y={y}")

    def _on_quit(self) -> None:
        self._stopped = True
        self.worker.running = False
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def launch_tk_gui(model: str = "phimdl_1d",
                  params: dict[str, Any] | None = None,
                  initial_inject: str | None = None,
                  ic_kind: str = "vacuum",
                  notes: Notes | None = None) -> None:
    """Entry point: build and run the Tk-based VIZLAB app."""
    app = VizLabApp(model=model, params=params,
                    initial_inject=initial_inject,
                    ic_kind=ic_kind, notes=notes)
    app.run()


__all__ = ["VizLabApp", "launch_tk_gui"]
