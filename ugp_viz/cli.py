"""
UGP VIZLAB command-line interface.

Subcommands
-----------
    run        Run a model with one or more injections and emit data + figures.
    viz        Render figures from a previously saved run.
    compare    Compare multiple runs on a chosen metric.
    catalog    List / show / add / remove catalog entries.
    export     Render a video from a saved run.
    experiment Run a YAML experiment config (full pipeline).
    gui        Launch the interactive GUI.

Examples
--------
    ugpviz run --model phimdl_1d --inject gen1_kink@256 --steps 5000 \\
        --params m=0.5,g=0.5,N=512 --output ugp_viz/runs/r1

    ugpviz experiment --config ugp_viz/examples/sr_test.yaml

    ugpviz catalog list
    ugpviz catalog show phimdl_1d gen1_kink

    ugpviz viz --input ugp_viz/runs/r1.json --figure tau_c_heatmap \\
        --output ugp_viz/runs/r1_tau.png

    ugpviz compare --runs r1.json r2.json --metric energy \\
        --output cmp.png

    ugpviz gui --model phimdl_1d --inject gen1_kink@256
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from ugp_viz.catalog.manager import (
    list_all,
    list_entries,
    load_entry,
    save_entry,
    delete_entry,
)
from ugp_viz.about import APP_INFO
from ugp_viz.engines import (
    InjectionSpec,
    InitialCondition,
    build_engine,
    list_models,
)
from ugp_viz.experiments.compare import compare_runs
from ugp_viz.experiments.runner import (
    load_yaml,
    run_experiment,
    run_experiment_file,
    save_experiment_config,
)
from ugp_viz.notes import Notes, load_notes, save_notes
from ugp_viz.paths import (
    data_dir,
    figures_dir,
    resolve_output,
    runs_dir,
)
from ugp_viz.state import load_run as load_run_bundle
from ugp_viz.viz import figures, video


def _coerce(val: str) -> Any:
    val = val.strip()
    try:
        if "." in val or "e" in val.lower():
            return float(val)
        return int(val)
    except ValueError:
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        return val


def parse_params(spec: str | None) -> dict[str, Any]:
    if not spec:
        return {}
    out: dict[str, Any] = {}
    for kv in spec.split(","):
        if not kv.strip():
            continue
        if "=" not in kv:
            raise SystemExit(f"--params: '{kv}' must be key=value")
        k, v = kv.split("=", 1)
        out[k.strip()] = _coerce(v)
    return out


def parse_inject(spec: str) -> InjectionSpec:
    return InjectionSpec.from_string(spec)


# ──────────────────────────────────────────────────────────────────────
# Subcommands
# ──────────────────────────────────────────────────────────────────────

def cmd_run(args: argparse.Namespace) -> int:
    params = parse_params(args.params)
    ic_params = parse_params(getattr(args, "ic_params", None))
    cfg: dict[str, Any] = {
        "model": args.model,
        "params": params,
        "steps": args.steps,
        "sample_every": args.sample_every or max(1, args.steps // 200),
        "injections": [{
            "kind": s.kind, "position": s.position,
            "velocity": s.velocity, "params": s.params,
        } for s in (parse_inject(inj) for inj in args.inject or [])],
        "measurements": args.measure or [],
        "output": {
            "data": f"{args.output}.json" if args.output else None,
            "figures": [],
        },
    }
    if args.initial_condition:
        cfg["initial_condition"] = {"kind": args.initial_condition}
        if ic_params:
            cfg["initial_condition"]["params"] = ic_params
    if args.figure:
        for fspec in args.figure:
            ftype, ffile = fspec.split(":", 1)
            cfg["output"]["figures"].append({"type": ftype, "file": ffile})
    if args.video:
        cfg["output"]["video"] = {"file": args.video, "fps": args.fps}
    if args.output and not Path(args.output).is_absolute() \
            and len(Path(args.output).parts) == 1:
        cfg["output"]["data"] = str(data_dir() / f"{args.output}.json")
    if getattr(args, "notes", None):
        cfg["notes"] = args.notes
    if getattr(args, "save_state", False) or getattr(args, "save_run", False):
        cfg["save_state"] = True
    if getattr(args, "save_config", None):
        save_experiment_config(args.save_config, cfg,
                               notes=_resolve_notes(cfg.get("notes")))
        print(f"wrote experiment config to {args.save_config}")
    result = run_experiment(cfg)
    print(_summary_line(result))
    return 0


def _resolve_notes(notes_field: Any) -> Notes | None:
    """Convert the CLI's --notes value to a Notes instance."""
    if notes_field is None:
        return None
    if isinstance(notes_field, dict):
        return Notes.from_dict(notes_field)
    p = Path(str(notes_field))
    if p.exists() and p.is_file():
        return load_notes(p)
    n = Notes(text=str(notes_field))
    n.touch()
    return n


def _summary_line(result) -> str:
    arts = ", ".join(f"{k}:{v}" for k, v in result.artifacts.items())
    return (f"model={result.model} steps={result.n_steps} "
            f"elapsed={result.elapsed_seconds:.2f}s artifacts={{{arts}}}")


def cmd_viz(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.is_absolute() and not input_path.exists():
        candidate = data_dir() / args.input
        if candidate.exists():
            input_path = candidate
    data = json.loads(input_path.read_text())
    history = data.get("history", {})
    out_path = resolve_output(args.output, default_subdir="figures")
    title = args.title or f"{data.get('model','')}: {args.figure}"
    if args.figure == "energy":
        figures.plot_energy_trace(
            np.array(history.get("time", [])),
            np.array(history.get("energy", [])),
            out_path, title=title)
    elif args.figure == "tau_c_mean":
        ys = np.array(history.get("tau_c_mean", []))
        ts = np.array(history.get("time", []))
        if ys.size == 0 or ts.size == 0:
            print("ERROR: no tau_c_mean history in run", file=sys.stderr)
            return 1
        figures.plot_energy_trace(ts, ys, out_path, title=title)
    else:
        print(f"ERROR: unknown --figure '{args.figure}'", file=sys.stderr)
        return 1
    print(f"wrote {out_path}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    summary = compare_runs(args.runs, metric=args.metric, output=args.output)
    print(json.dumps(summary, indent=2))
    return 0


def cmd_catalog(args: argparse.Namespace) -> int:
    if args.action == "list":
        if args.model:
            for name in list_entries(args.model):
                print(name)
        else:
            for model, entries in list_all().items():
                print(f"== {model} ==")
                for name in entries:
                    print(f"  {name}")
        return 0
    if args.action == "show":
        if not args.model or not args.name:
            print("ERROR: show requires <model> <name>", file=sys.stderr)
            return 1
        print(json.dumps(load_entry(args.model, args.name), indent=2))
        return 0
    if args.action == "add":
        if not args.model or not args.name or not args.file:
            print("ERROR: add requires <model> <name> <file>", file=sys.stderr)
            return 1
        data = json.loads(Path(args.file).read_text())
        path = save_entry(args.model, args.name, data)
        print(f"wrote {path}")
        return 0
    if args.action == "remove":
        if not args.model or not args.name:
            print("ERROR: remove requires <model> <name>", file=sys.stderr)
            return 1
        delete_entry(args.model, args.name)
        print(f"removed {args.model}/{args.name}")
        return 0
    print(f"ERROR: unknown action '{args.action}'", file=sys.stderr)
    return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Render a video from a saved run's spacetime."""
    input_path = Path(args.input)
    if not input_path.is_absolute() and not input_path.exists():
        candidate = data_dir() / args.input
        if candidate.exists():
            input_path = candidate
    data = json.loads(input_path.read_text())
    rows_path = input_path.with_suffix(".spacetime.npy")
    if not rows_path.exists():
        print(f"ERROR: spacetime payload not found at {rows_path}",
              file=sys.stderr)
        return 1
    spacetime = np.load(rows_path)
    out_path = resolve_output(args.output, default_subdir="videos")
    video.render_spacetime_video(
        spacetime, out_path, fps=args.fps, window=args.window,
        backend=args.backend)
    print(f"wrote {out_path}")
    return 0


def cmd_experiment(args: argparse.Namespace) -> int:
    cfg = load_yaml(args.config)
    # CLI overrides on top of the YAML
    override_params = parse_params(getattr(args, "params", None))
    if override_params:
        cfg.setdefault("params", {}).update(override_params)
    if getattr(args, "steps", None):
        cfg["steps"] = int(args.steps)
    if getattr(args, "initial_condition", None):
        cfg.setdefault("initial_condition", {})["kind"] = args.initial_condition
    if getattr(args, "notes", None):
        cfg["notes"] = args.notes
    if getattr(args, "save_state", False) or getattr(args, "save_run", False):
        cfg["save_state"] = True
    result = run_experiment(cfg)
    print(_summary_line(result))
    return 0


def cmd_save_config(args: argparse.Namespace) -> int:
    """Translate CLI args into a YAML config without running the experiment."""
    params = parse_params(args.params)
    ic_params = parse_params(getattr(args, "ic_params", None))
    cfg: dict[str, Any] = {
        "model": args.model,
        "params": params,
        "steps": args.steps,
    }
    if args.initial_condition:
        cfg["initial_condition"] = {"kind": args.initial_condition}
        if ic_params:
            cfg["initial_condition"]["params"] = ic_params
    if args.inject:
        cfg["injections"] = [{
            "kind": s.kind, "position": s.position,
            "velocity": s.velocity, "params": s.params,
        } for s in (parse_inject(inj) for inj in args.inject)]
    if args.measure:
        cfg["measurements"] = list(args.measure)
    # Default output so the saved config is immediately runnable. Users
    # can edit it freely; bare filenames route to ugp_viz/runs/{data,
    # figures,videos}/ by the path resolver.
    base = Path(args.output).stem
    cfg["output"] = {
        "data": f"{base}.json",
        "figures": [
            {"type": "spacetime", "file": f"{base}_spacetime.png"},
        ],
    }
    notes = _resolve_notes(getattr(args, "notes", None))
    save_experiment_config(args.output, cfg, notes=notes)
    print(f"wrote {args.output}")
    return 0


def cmd_show_notes(args: argparse.Namespace) -> int:
    """Print the notes attached to a run bundle, config, or notes file."""
    p = Path(args.input)
    if not p.exists():
        candidate = data_dir() / args.input
        if candidate.exists():
            p = candidate
    notes: Notes | None = None
    if p.suffix in (".md",) or p.name.endswith(".notes.md") \
            or p.name.endswith(".notes.json"):
        notes = load_notes(p)
    elif p.name.endswith(".run.json") or p.suffix == ".json":
        try:
            bundle = load_run_bundle(p)
            notes = bundle.notes
        except Exception:
            pass
    elif p.suffix in (".yaml", ".yml"):
        cfg = load_yaml(p)
        nc = cfg.get("notes")
        if isinstance(nc, dict):
            notes = Notes.from_dict(nc)
        elif isinstance(nc, str):
            notes = Notes(text=nc)
        else:
            sidecar = p.with_suffix(".notes.md")
            if sidecar.exists():
                notes = load_notes(sidecar)
    if notes is None or notes.is_empty():
        print("(no notes)")
        return 0
    if notes.title:
        print(f"# {notes.title}\n")
    if notes.author:
        print(f"_by {notes.author}_\n")
    print(notes.text)
    return 0


def cmd_about(args: argparse.Namespace) -> int:
    info = APP_INFO
    print(f"{info['name']} {info['version']}")
    print(info["subtitle"])
    print(info["byline"])
    print(info["programme"])
    print(f"Website:    {info['website']}")
    print(f"Repository: {info['repository']}")
    print(f"License:    {info['license']}")
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    from ugp_viz.viz.gui import run_gui
    params = parse_params(args.params)
    run_gui(model=args.model, params=params or None,
            initial_inject=args.inject,
            ic_kind=getattr(args, "initial_condition", None) or "vacuum",
            backend=args.backend,
            notes_path=getattr(args, "notes", None),
            load_run_path=getattr(args, "load_run", None),
            load_config_path=getattr(args, "load_config", None))
    return 0


# ──────────────────────────────────────────────────────────────────────
# Argparse wiring
# ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ugpviz",
                                     description="UGP Visualization Lab CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # run
    p_run = sub.add_parser("run", help="run a model and emit data + figures")
    p_run.add_argument("--model", required=True, choices=list_models())
    p_run.add_argument("--params", default=None,
                       help="comma-separated key=value parameter overrides")
    p_run.add_argument("--steps", type=int, required=True)
    p_run.add_argument("--sample-every", type=int, default=None)
    p_run.add_argument("--inject", action="append", default=None,
                       help="catalog spec like gen1_kink@256")
    p_run.add_argument("--initial-condition", default=None,
                       help="vacuum | ether | random | load (engine-specific)")
    p_run.add_argument("--ic-params", default=None,
                       help="comma-separated key=value initial-condition params "
                            "(e.g. seed=42,amp=0.1)")
    p_run.add_argument("--figure", action="append", default=None,
                       help="figure spec like tau_c_heatmap:results/tau.png")
    p_run.add_argument("--measure", action="append", default=None,
                       help="add a measurement like tau_c_mean")
    p_run.add_argument("--video", default=None,
                       help="mp4 path to render rolling spacetime video")
    p_run.add_argument("--fps", type=int, default=30)
    p_run.add_argument("--output", default=None,
                       help="basename for run artifacts (writes <name>.json)")
    p_run.add_argument("--notes", default=None,
                       help="markdown notes (path to .md/.notes.json or inline text)")
    p_run.add_argument("--save-state", action="store_true",
                       help="save engine state alongside run JSON")
    p_run.add_argument("--save-run", action="store_true",
                       help="alias for --save-state; writes the full run bundle")
    p_run.add_argument("--save-config", default=None,
                       help="also emit the run's parameters as a YAML config")
    p_run.set_defaults(func=cmd_run)

    # viz
    p_viz = sub.add_parser("viz", help="render a figure from a saved run")
    p_viz.add_argument("--input", required=True)
    p_viz.add_argument("--figure", required=True,
                       choices=["energy", "tau_c_mean"])
    p_viz.add_argument("--output", required=True)
    p_viz.add_argument("--title", default=None)
    p_viz.set_defaults(func=cmd_viz)

    # compare
    p_cmp = sub.add_parser("compare", help="compare multiple runs")
    p_cmp.add_argument("--runs", nargs="+", required=True)
    p_cmp.add_argument("--metric", default="energy")
    p_cmp.add_argument("--output", default=None)
    p_cmp.set_defaults(func=cmd_compare)

    # catalog
    p_cat = sub.add_parser("catalog", help="manage kink/glider catalog")
    p_cat.add_argument("action", choices=["list", "show", "add", "remove"])
    p_cat.add_argument("model", nargs="?")
    p_cat.add_argument("name", nargs="?")
    p_cat.add_argument("--file", default=None,
                       help="path to JSON file (for add action)")
    p_cat.set_defaults(func=cmd_catalog)

    # export
    p_exp = sub.add_parser("export", help="render video from a saved run")
    p_exp.add_argument("--input", required=True)
    p_exp.add_argument("--output", required=True)
    p_exp.add_argument("--fps", type=int, default=30)
    p_exp.add_argument("--window", type=int, default=200)
    p_exp.add_argument("--backend", default="auto",
                       choices=["auto", "animation", "ffmpeg"])
    p_exp.set_defaults(func=cmd_export)

    # experiment (YAML)
    p_xp = sub.add_parser("experiment", help="run a YAML experiment config")
    p_xp.add_argument("--config", required=True)
    p_xp.add_argument("--params", default=None,
                      help="override params on top of the YAML")
    p_xp.add_argument("--steps", type=int, default=None,
                      help="override steps")
    p_xp.add_argument("--initial-condition", default=None,
                      help="override initial-condition kind")
    p_xp.add_argument("--notes", default=None,
                      help="markdown notes (path or inline)")
    p_xp.add_argument("--save-state", action="store_true",
                      help="also save the engine state bundle")
    p_xp.add_argument("--save-run", action="store_true",
                      help="alias for --save-state")
    p_xp.set_defaults(func=cmd_experiment)

    # save-config (no run, just emit a YAML config from CLI args)
    p_sc = sub.add_parser("save-config",
                          help="emit a YAML experiment config without running")
    p_sc.add_argument("--model", required=True, choices=list_models())
    p_sc.add_argument("--params", default=None)
    p_sc.add_argument("--steps", type=int, default=1000)
    p_sc.add_argument("--initial-condition", default=None)
    p_sc.add_argument("--ic-params", default=None)
    p_sc.add_argument("--inject", action="append", default=None)
    p_sc.add_argument("--measure", action="append", default=None)
    p_sc.add_argument("--notes", default=None,
                      help="markdown notes (path or inline)")
    p_sc.add_argument("--output", required=True,
                      help="path to write the YAML to")
    p_sc.set_defaults(func=cmd_save_config)

    # show-notes — print notes attached to any run / config / .md file
    p_sn = sub.add_parser("show-notes",
                          help="print notes attached to a run, config, or .md")
    p_sn.add_argument("input")
    p_sn.set_defaults(func=cmd_show_notes)

    # about
    p_ab = sub.add_parser("about",
                          help="print app identity, links, and license")
    p_ab.set_defaults(func=cmd_about)

    # gui
    p_gui = sub.add_parser("gui", help="launch interactive GUI")
    p_gui.add_argument("--model", default="phimdl_1d", choices=list_models())
    p_gui.add_argument("--inject", default=None)
    p_gui.add_argument("--params", default=None)
    p_gui.add_argument("--initial-condition", default=None,
                       help="initial-condition kind to apply on launch")
    p_gui.add_argument("--notes", default=None,
                       help="path to a .md notes file to load on launch")
    p_gui.add_argument("--load-run", default=None,
                       help="open a saved run bundle on launch")
    p_gui.add_argument("--load-config", default=None,
                       help="open a YAML experiment config on launch")
    p_gui.add_argument("--backend", default="auto",
                       choices=["auto", "tk", "taichi", "matplotlib"])
    p_gui.set_defaults(func=cmd_gui)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
