"""
YAML experiment runner.

A self-describing YAML config drives the entire pipeline (engine, params,
injections, measurements, figures, video). The runner records every
parameter, every result, and every artifact path back into a JSON report so
the run is reproducible from the YAML alone.

Schema (all fields except `model` and `steps` are optional):

    model: phimdl_1d
    params:                # engine parameter overrides
      m: 0.5
      g: 0.5
      N: 512
    initial_condition:
      kind: vacuum         # vacuum | ether | random | load
      params: {seed: 42}
    steps: 5000
    sample_every: 50
    injections:
      - kind: gen1_kink
        position: 128
        velocity: 0.3
      - kind: gen2_antikink
        position: 384
    measurements:
      - tau_c_mean
      - sr_error
      - binding_energy
      - kink_centers
    output:
      data: results/run1.json
      figures:
        - {type: tau_c_heatmap, file: results/tau_c.png}
        - {type: spacetime,     file: results/spacetime.png}
      video:
        file: results/sim.mp4
        fps: 30
        backend: auto
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from ugp_viz.engines import (
    SimEngine,
    InjectionSpec,
    InitialCondition,
    build_engine,
)
from ugp_viz.notes import Notes, load_notes, save_notes
from ugp_viz.paths import resolve_output
from ugp_viz.state import save_run
from ugp_viz.viz import figures, video


@dataclass
class ExperimentResult:
    model: str
    params: dict[str, Any]
    n_steps: int
    elapsed_seconds: float
    measurements: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    history: dict[str, list[float]] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "params": _json_safe(self.params),
            "n_steps": self.n_steps,
            "elapsed_seconds": self.elapsed_seconds,
            "measurements": _json_safe(self.measurements),
            "artifacts": dict(self.artifacts),
            "history": {k: list(map(float, v)) for k, v in self.history.items()},
        }


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


def load_yaml(path: str | Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML not installed. pip install pyyaml")
    return yaml.safe_load(Path(path).read_text())


def save_experiment_config(path: str | Path, cfg: dict[str, Any],
                           *, notes: Notes | None = None) -> Path:
    """Write an experiment YAML alongside an optional ``.notes.md``.

    ``cfg`` is the same dict accepted by :func:`run_experiment`. Notes
    are stored both inline (so the YAML is self-describing) and as a
    sidecar markdown file (so they are readable outside the app).
    """
    if yaml is None:
        raise RuntimeError("PyYAML not installed. pip install pyyaml")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    serializable = _json_safe(cfg)
    if notes is not None and not notes.is_empty():
        serializable = dict(serializable)
        serializable["notes"] = notes.to_dict()
        save_notes(p.with_suffix(".notes.md"), notes)
    p.write_text(yaml.safe_dump(serializable, sort_keys=False))
    return p


def run_experiment_file(path: str | Path) -> ExperimentResult:
    return run_experiment(load_yaml(path))


def run_experiment(cfg: dict[str, Any]) -> ExperimentResult:
    model = cfg["model"]
    params = cfg.get("params", {}) or {}
    steps = int(cfg["steps"])
    sample_every = int(cfg.get("sample_every", max(1, steps // 200)))
    engine = build_engine(model, params=params)

    ic_cfg = cfg.get("initial_condition")
    if ic_cfg:
        ic = InitialCondition(
            kind=ic_cfg.get("kind", "vacuum"),
            path=ic_cfg.get("path"),
            params=ic_cfg.get("params", {}) or {},
        )
        engine.reset(ic)

    for inj_cfg in cfg.get("injections", []) or []:
        spec = InjectionSpec(
            kind=inj_cfg["kind"],
            position=inj_cfg.get("position"),
            velocity=inj_cfg.get("velocity"),
            params=inj_cfg.get("params", {}) or {},
        )
        engine.inject(spec)

    history: dict[str, list[float]] = {
        "time": [],
        "energy": [],
        "tau_c_mean": [],
    }
    spacetime_rows: list[np.ndarray] = []
    tau_rows: list[np.ndarray] = []

    t0 = time.time()
    for step in range(steps):
        engine.step(1)
        if (step + 1) % sample_every == 0 or step + 1 == steps:
            snap = engine.snapshot()
            history["time"].append(float(snap.time))
            history["energy"].append(
                float(snap.extra.get("total_energy", float("nan"))))
            if snap.tau_c is not None:
                history["tau_c_mean"].append(float(np.mean(snap.tau_c)))
                tau_rows.append(snap.tau_c.copy())
            if snap.tape is not None:
                spacetime_rows.append(snap.tape.copy())
            elif snap.phi is not None:
                Nphi = int(params.get("N_phi", params.get("N_sym", 7)))
                half = 2.0 * np.pi / Nphi * 0.5
                spacetime_rows.append((snap.phi > half).astype(np.uint8))
    elapsed = time.time() - t0

    result = ExperimentResult(
        model=model,
        params=dict(engine.params),
        n_steps=steps,
        elapsed_seconds=elapsed,
        history=history,
    )

    # Measurements
    for m in cfg.get("measurements", []) or []:
        result.measurements[m] = _compute_measurement(m, engine, history,
                                                     spacetime_rows, tau_rows)

    # Outputs (figures + video + data JSON). Bare filenames are auto-routed
    # under <package>/runs/<subdir>/ so artifacts travel with the app.
    output = cfg.get("output", {}) or {}
    figure_specs = output.get("figures", []) or []
    for fs in figure_specs:
        ftype = fs["type"]
        path = resolve_output(fs["file"], default_subdir="figures")
        path.parent.mkdir(parents=True, exist_ok=True)
        _render_figure(ftype, path, engine, spacetime_rows, tau_rows, history,
                       fs.get("params") or {})
        result.artifacts[ftype] = str(path)

    vid_cfg = output.get("video")
    if vid_cfg:
        vpath = resolve_output(vid_cfg["file"], default_subdir="videos")
        fps = int(vid_cfg.get("fps", 30))
        _ = vid_cfg.get("backend", "auto")
        if spacetime_rows:
            spacetime = np.stack(spacetime_rows, axis=0)
            video.render_spacetime_video(
                spacetime, vpath, fps=fps,
                window=int(vid_cfg.get("window", 200)),
            )
            result.artifacts["video"] = str(vpath)

    # Notes — accepted as inline text/title or as an external markdown
    # path. Notes travel with the saved run bundle.
    notes_cfg = cfg.get("notes")
    notes_obj: Notes | None = None
    if isinstance(notes_cfg, str):
        notes_path = Path(notes_cfg)
        if notes_path.exists():
            notes_obj = load_notes(notes_path)
        else:
            notes_obj = Notes(text=notes_cfg)
            notes_obj.touch()
    elif isinstance(notes_cfg, dict):
        notes_obj = Notes.from_dict(notes_cfg)
        notes_obj.touch()

    data_path = output.get("data")
    if data_path:
        dpath = resolve_output(data_path, default_subdir="data")
        dpath.parent.mkdir(parents=True, exist_ok=True)
        spacetime_arr = (np.stack(spacetime_rows, axis=0)
                          if spacetime_rows else None)
        manifest = result.to_json()
        if notes_obj is not None and not notes_obj.is_empty():
            manifest["notes"] = notes_obj.to_dict()
        if cfg.get("save_state") or cfg.get("save_run"):
            stem = dpath.with_suffix("")
            written = save_run(
                stem=stem,
                manifest=manifest,
                spacetime=spacetime_arr,
                engine=engine,
                notes=notes_obj,
            )
            for k, v in written.items():
                result.artifacts[f"bundle_{k}"] = v
            result.artifacts["data"] = written["manifest"]
        else:
            dpath.write_text(json.dumps(manifest, indent=2))
            result.artifacts["data"] = str(dpath)
            if spacetime_arr is not None:
                np.save(dpath.with_suffix(".spacetime.npy"), spacetime_arr)
            if notes_obj is not None and not notes_obj.is_empty():
                stem = dpath.with_suffix("")
                save_notes(stem.with_suffix(".notes.md"), notes_obj)
                result.artifacts["notes"] = str(
                    stem.with_suffix(".notes.md"))

    return result


def _compute_measurement(
    name: str,
    engine: SimEngine,
    history: dict[str, list[float]],
    spacetime_rows: list[np.ndarray],
    tau_rows: list[np.ndarray],
) -> Any:
    if name == "tau_c_mean":
        return float(np.mean(history["tau_c_mean"])) if history["tau_c_mean"] else None
    if name == "tau_c_ratio":
        snap = engine.snapshot()
        if snap.tau_c is None:
            return None
        return float(snap.tau_c.mean() / max(np.median(snap.tau_c), 1e-9))
    if name == "binding_energy":
        if len(history["energy"]) < 2:
            return None
        return float(history["energy"][-1] - history["energy"][0])
    if name == "kink_centers":
        snap = engine.snapshot()
        if snap.phi is None:
            return None
        dphi = np.abs(np.diff(snap.phi))
        return [int(np.argmax(dphi))]
    if name == "sr_error":
        # Placeholder: SR error is computed by a dedicated experiment script
        # and stored in extra. Here we just report the last extras['sr_error']
        # if present.
        snap = engine.snapshot()
        return snap.extra.get("sr_error")
    return None


def _render_figure(
    ftype: str,
    path: Path,
    engine: SimEngine,
    spacetime_rows: list[np.ndarray],
    tau_rows: list[np.ndarray],
    history: dict[str, list[float]],
    extra: dict[str, Any],
) -> None:
    if ftype == "tau_c_heatmap" and tau_rows:
        figures.plot_tau_c_heatmap(np.stack(tau_rows, axis=0), path,
                                   title=extra.get("title", "tau_c heatmap"))
    elif ftype == "spacetime" and spacetime_rows:
        figures.plot_spacetime(np.stack(spacetime_rows, axis=0), path,
                               title=extra.get("title", "Spacetime"))
    elif ftype == "field_1d":
        snap = engine.snapshot()
        if snap.phi is not None:
            extra_curves = {}
            if snap.chi is not None:
                extra_curves["chi"] = snap.chi
            figures.plot_field_1d(snap.phi, path,
                                  title=extra.get("title", "Field profile"),
                                  extra_curves=extra_curves)
    elif ftype == "field_3d_three_slice":
        if hasattr(engine, "get_volume_phi"):
            figures.plot_field_3d_three_slice(
                engine.get_volume_phi(), path,
                title=extra.get("title", "3D phi slices"),
                field_name="phi")
    elif ftype == "field_3d_volumetric":
        if hasattr(engine, "get_volume_phi"):
            figures.plot_field_3d_volumetric(
                engine.get_volume_phi(), path,
                title=extra.get("title", "3D phi volumetric"),
                cmap=extra.get("cmap", "viridis"),
                n_samples=int(extra.get("n_samples", 96)),
                azim=float(extra.get("azim", 35.0)),
                elev=float(extra.get("elev", 22.0)),
                alpha_gain=float(extra.get("alpha_gain", 1.0)),
            )
    elif ftype == "field_3d_isosurface":
        if hasattr(engine, "get_volume_phi"):
            iso = extra.get("iso_level")
            figures.plot_field_3d_isosurface(
                engine.get_volume_phi(), path,
                iso_level=(None if iso is None else float(iso)),
                title=extra.get("title", "3D phi isosurface"),
                azim=float(extra.get("azim", 35.0)),
                elev=float(extra.get("elev", 22.0)),
                color=extra.get("color", "C2"),
            )
    elif ftype == "energy":
        figures.plot_energy_trace(
            np.array(history["time"]), np.array(history["energy"]),
            path, title=extra.get("title", "Energy E(t)"))
    elif ftype == "tau_c_with_trajectory" and tau_rows:
        figures.plot_tau_c_with_trajectory(
            np.stack(tau_rows, axis=0),
            extra.get("com_positions", []),
            path,
            title=extra.get("title", "tau_c heatmap with CoM"))
    else:
        # No-op for unknown types (do not silently mislead the user — print).
        print(f"WARNING: skipping unknown figure type '{ftype}'")
