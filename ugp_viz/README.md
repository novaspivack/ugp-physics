# UGP Visualization Lab (VIZLAB)

A unified, interactive environment for running, visualizing, and exploring
every GTE simulation built so far: continuum kink fields (Phi_MDL 1D / 3D,
Z7-KG), 2-level fractal cellular automata (FCA sync, AFCA with `τ_c` clock
warping), and the Z7 f_MDL orbit CA. VIZLAB ships with:

- a single, modular **SimEngine** interface, so every model exposes the
  same `reset → inject → step → snapshot` surface;
- a **JSON kink / glider catalog** that includes the full Cook (2004)
  named-glider catalog and Genaro Martinez's 365-pattern phase
  catalog for Rule 110;
- a **publication-quality matplotlib figure library**, an **MP4 video
  exporter**, **volumetric ray-cast** and **marching-cubes isosurface**
  renderers for 3D fields;
- an optional **Taichi Metal GPU backend** for the continuum field
  engines (≈25–100× speedup on 64³ Phi_MDL on Apple Silicon — see
  GPU benchmarks below);
- a **YAML batch experiment runner** that records every parameter,
  injection, measurement, and artifact path;
- a **CLI** (`python -m ugp_viz.cli`);
- a **desktop GUI** (default Tkinter backend, with Taichi GGUI and
  matplotlib fallbacks) featuring a full menubar, file dialogs,
  transport controls, **matplotlib zoom/pan**, a live **engine parameter
  editor**, an **initial-condition selector**, and a **markdown notes
  panel** with rendered preview;
- a **save/load run-bundle** format (`.run.json` + `.spacetime.npy`
  + `.state.npz` + `.state.json` + `.notes.md`) so any simulation can be
  paused, archived, and resumed at the saved step;
- an **About modal** and `about` CLI command listing attribution,
  website, repository, and license.

## Table of Contents

1. [Install](#install)
2. [Quick start](#quick-start)
3. [Architecture](#architecture)
4. [Models](#models)
5. [Catalog](#catalog)
6. [Command-line interface](#command-line-interface)
7. [YAML experiments](#yaml-experiments)
8. [Notes and markdown](#notes-and-markdown)
9. [Saved-run bundles](#saved-run-bundles)
10. [Desktop GUI](#desktop-gui)
11. [Taichi GPU backend](#taichi-gpu-backend)
12. [3D rendering](#3d-rendering)
13. [Output paths](#output-paths)
14. [Extending VIZLAB](#extending-vizlab)
15. [References](#references)

---

## Install

VIZLAB lives in the `ugp_viz/` package of the `ugp-physics` repository.
It runs from a checkout of that repo with `PYTHONPATH` pointing at the
repo root.

### Minimum (NumPy, matplotlib, YAML)

```bash
git clone https://github.com/novaspivack/ugp-physics
cd ugp-physics
pip install -r requirements.txt
```

`requirements.txt` already pins NumPy, SciPy, matplotlib, PyYAML, and
the other dependencies VIZLAB needs.

### Optional extras

| Package          | Purpose                                                  |
|------------------|----------------------------------------------------------|
| `taichi>=1.7`    | GPU backend for PhiMDL 1D / 3D / Z7-KG (Metal on macOS)  |
| `scikit-image`   | Marching-cubes isosurface mesh for `phimdl_3d`           |
| `ffmpeg`         | Fast MP4 export via the `ffmpeg` backend                  |

```bash
pip install taichi scikit-image
brew install ffmpeg          # or apt-get install ffmpeg
```

VIZLAB degrades gracefully without these — the GUI falls back to
matplotlib, the isosurface renderer falls back to a voxel point cloud,
and video export falls back to matplotlib's `FuncAnimation`.

### Run from the repo

```bash
cd /path/to/ugp-physics
PYTHONPATH=. python -m ugp_viz.cli --help
```

Add `PYTHONPATH=.` to your shell once, or `pip install -e .` once a
top-level `pyproject.toml` is wired (intentionally not packaged yet,
since VIZLAB is part of the larger `ugp-physics` mono-repo).

---

## Quick start

```bash
# A Phi_MDL kink-antikink meson breather, full pipeline
PYTHONPATH=. python -m ugp_viz.cli experiment \
    --config ugp_viz/examples/phimdl_1d_meson.yaml

# A 3D spherical kink loop with volumetric + marching-cubes renders
PYTHONPATH=. python -m ugp_viz.cli experiment \
    --config ugp_viz/examples/phimdl_3d_spherical.yaml

# Launch the live GUI on a kink injection
PYTHONPATH=. python -m ugp_viz.cli gui \
    --model phimdl_1d --inject gen1_kink@256

# Drop the canonical Cook C2 glider on Rule 110 and watch it propagate
PYTHONPATH=. python -m ugp_viz.cli gui \
    --model afca --inject r110/cook_C2@128
```

All artifacts (data JSON, figures, videos, screenshots) land under
`ugp_viz/runs/{data,figures,videos,screenshots}/` so they travel with
the app.

---

## Architecture

```
ugp_viz/
├── engines/                         SimEngine + one engine per physics model
│   ├── base.py                      SimEngine ABC, FieldSnapshot, InjectionSpec
│   ├── registry.py                  Lazy engine loader
│   ├── taichi_runtime.py            Single ti.init across all GPU engines
│   ├── phimdl_1d.py                 Coupled Z7×Z3 Klein-Gordon, 1D
│   ├── phimdl_3d.py                 Same, on a 3D periodic cubic lattice
│   ├── z7_kg.py                     Single-component Z7-KG (spectral or FD)
│   ├── fca_sync.py                  Synchronous 2-level fractal CA
│   ├── afca.py                      Asynchronous FCA with τ_c clock warp
│   └── z7_fmdl.py                   Z7 f_MDL orbit CA (1D ring / 3D axis)
├── catalog/                         JSON kink / glider / orbit library
│   ├── manager.py                   Catalog CRUD + recursive subdir lookup
│   ├── build_r110_catalog.py        Cook+Martinez R110 catalog generator
│   ├── _assets/listPhasesR110.txt   Vendored Martinez 2004 phase data
│   ├── phimdl_1d/                   gen1/2/3 kinks, meson, packet
│   ├── phimdl_3d/                   spherical_kink, flux_tube, …
│   ├── z7_kg/                       sg_kink, sg_antikink, wave_packet
│   ├── fca_sync/                    canonical_glider, ether14, r110/*
│   ├── afca/                        canonical_glider, ether14, r110/*
│   └── z7_fmdl/                     gen1/2/3 orbits, vacuum
├── viz/                             matplotlib + MP4 + Taichi GGUI
│   ├── figures.py                   Spacetime, τ_c, energy, SR, 3D volume/iso
│   ├── video.py                     MP4 export (matplotlib + ffmpeg backends)
│   └── gui.py                       Live GUI (Taichi GGUI; matplotlib fallback)
├── analysis/                        Online analysis helpers
│   └── kink_tracker.py              Detect kinks; live inter-kink force readout
├── experiments/                     Reproducible YAML pipeline
│   ├── runner.py                    Parses YAML, runs engine, writes report
│   └── compare.py                   Cross-run metric comparison
├── cli.py                           ugpviz CLI entry point
├── app.py                           Thin GUI launcher
├── paths.py                         Package-local output directory resolver
├── config.yaml                      Default per-model parameters
├── examples/                        Ready-to-run YAML configs
└── runs/                            Output artifacts (gitignored)
    ├── data/                        Run JSON reports
    ├── figures/                     PNG figures
    ├── videos/                      MP4 video exports
    └── screenshots/                 Live-GUI screenshots
```

The `SimEngine` ABC (`ugp_viz/engines/base.py`) is the single source of
truth for the engine API:

```python
class SimEngine(ABC):
    model_name: str
    spatial_dim: int
    default_params: dict

    def reset(self, ic: InitialCondition | None = None) -> None: ...
    def inject(self, spec: InjectionSpec) -> None: ...
    def step(self, n_steps: int = 1) -> None: ...
    def snapshot(self) -> FieldSnapshot: ...
```

`InjectionSpec` describes one catalog inject; `FieldSnapshot` carries
`phi`, optional `chi`, optional `tape`, `energy_density`, `tau_c`, plus
free-form `extra` for model-specific observables. CLI / GUI / runner
code never branches on `model_name`; they just call `snapshot()` and
introspect the fields that came back.

---

## Models

| Key         | Engine                                          | Dim | Backend(s)        |
|-------------|-------------------------------------------------|-----|-------------------|
| `phimdl_1d` | Coupled `(φ, χ)` Z₇×Z₃ Klein-Gordon             | 1D  | NumPy / Taichi    |
| `phimdl_3d` | Same on a 3D periodic cubic lattice             | 3D  | NumPy / Taichi    |
| `z7_kg`     | Single-component Z_N Klein-Gordon               | 1D  | NumPy / Taichi¹   |
| `fca_sync`  | 2-level synchronous fractal CA                  | 1D  | NumPy             |
| `afca`      | Async FCA + region-aware τ_c clock warp         | 1D  | NumPy             |
| `z7_fmdl`   | Z₇ f_MDL orbit CA (1D ring or 3D axis-decomp.)  | 1/3 | NumPy             |

¹ Taichi only for the finite-difference (`spectral: false`) path;
spectral Verlet stays in NumPy since FFTs aren't kernel-fused.

The Phi_MDL and Z7-KG engines run a velocity-Verlet integrator. The
sine-Gordon-like potential

```
V(φ) = (m² / N²)(1 − cos N·φ)
```

gives BPS-stable kinks of width `1/m` and rest-mass `M = 8 m / N²`. The
3D engine uses a 7-point finite-difference Laplacian.

The FCA / AFCA / Z7 f_MDL engines run discrete dynamics on a 1D ring
(or a 3D ring decomposition for `z7_fmdl`). FCA wraps Rule 110 by
default and tracks the local clock rate `τ_c(t, i)`. AFCA runs the
same dynamics with region-aware asynchrony so that matter-like
disturbances warp `τ_c` relative to the ether reference run.

---

## Catalog

Each model has its own folder under `ugp_viz/catalog/<model>/`. Drop a
JSON file in there and it becomes injectable; nested directories work
too (POSIX-style slash names: `r110/cook_C2`).

### Built-in entries

| Model       | Entries                                                                                              |
|-------------|------------------------------------------------------------------------------------------------------|
| `phimdl_1d` | `gen1_kink`, `gen2_kink`, `gen3_kink`, `gen1_antikink`, `meson`, `gaussian_packet`                   |
| `phimdl_3d` | `spherical_kink`, `domain_wall_slab`, `wall_pair`, `flux_tube`                                       |
| `z7_kg`     | `sg_kink`, `sg_antikink`, `wave_packet`                                                              |
| `fca_sync`  | `canonical_glider`, `ether14`, **`r110/cook_*` (10), `r110/martinez_*` (365)**                       |
| `afca`      | same as `fca_sync`                                                                                   |
| `z7_fmdl`   | `gen1_orbit`, `gen2_orbit`, `gen3_orbit`, `vacuum`                                                   |

### Rule 110 glider catalog (Cook + Martinez)

The two canonical reference catalogs for Rule 110 glider dynamics are
both included:

- **Cook (2004), Figure 5** — the named gliders `A`, `B`, `C1`, `C2`,
  `C3`, `D1`, `D2`, `Ē`, `F`, `H` with width, period `(Δt, Δx)`, and
  ω-coefficients. Stored as `r110/cook_<NAME>.json` (10 entries).
  Indexed families `Bbar_n`, `Bhat_n`, `E_n`, `G_n` (with their
  affine width formulas) live in `r110/_cook_indexed_families.json`.
- **Martinez (2004), ESCOM** — 365 cell-bit patterns covering every
  phase of every glider in the Rule 110 family
  (`ether`, `A`, `B`, `B-`, `B^`, `C1`, `C2`, `C3`, `D1`, `D2`, `E`,
  `E-`, `F`, `G`, `H`, `Gun`). Plus 29 published f4_1 aliases. Stored
  as `r110/martinez_<family>_<parent>_<phase>.json`. Source data
  vendored at `ugp_viz/catalog/_assets/listPhasesR110.txt`; regenerate
  the JSON entries with:

  ```bash
  PYTHONPATH=. python -m ugp_viz.catalog.build_r110_catalog
  ```

These match the same source data that `rule110-lean` ingests, so the
glider patterns used in VIZLAB are identical to those proven against
Cook's construction in Lean 4 (see the `Rule110.MartinezPhasesCatalog`
and `Rule110.CookGliderCatalog` modules in
[`rule110-lean`](https://github.com/novaspivack/rule110-lean)).

### Adding entries

Add a new entry programmatically:

```bash
PYTHONPATH=. python -m ugp_viz.cli catalog add phimdl_1d my_kink --file my_kink.json
```

Or just drop a JSON file directly into `ugp_viz/catalog/<model>/`.

---

## Command-line interface

```bash
PYTHONPATH=. python -m ugp_viz.cli <subcommand> [flags]
```

| Subcommand   | Purpose                                                |
|--------------|--------------------------------------------------------|
| `run`        | One-off engine run with figures from CLI flags         |
| `experiment` | Run a full YAML experiment config                      |
| `viz`        | Render a figure from a saved run JSON                  |
| `compare`    | Compare multiple runs on a metric                      |
| `catalog`    | `list` / `show` / `add` / `remove` catalog entries     |
| `export`     | Render an MP4 from a saved spacetime payload           |
| `gui`        | Launch the interactive GUI                             |

Examples:

```bash
# Inspect the catalog
PYTHONPATH=. python -m ugp_viz.cli catalog list
PYTHONPATH=. python -m ugp_viz.cli catalog show fca_sync r110/cook_C2

# Direct run with figures
PYTHONPATH=. python -m ugp_viz.cli run \
    --model phimdl_1d \
    --params m=0.5,g=0.5,N=512 \
    --steps 5000 \
    --inject gen1_kink@256 \
    --figure tau_c_heatmap:tau.png \
    --output r1

# Render an MP4 from a saved run
PYTHONPATH=. python -m ugp_viz.cli export \
    --input ugp_viz/runs/data/r1.json \
    --output r1_video.mp4 --fps 60 --window 200

# Compare two runs
PYTHONPATH=. python -m ugp_viz.cli compare \
    --runs ugp_viz/runs/data/r1.json ugp_viz/runs/data/r2.json \
    --metric energy --output cmp.png
```

Bare filenames (no directory) are auto-routed to
`ugp_viz/runs/{data,figures,videos}/` so the artifacts ship with the
app. Absolute paths or relative paths with sub-directories are honored
as-is.

---

## YAML experiments

Each YAML file under `ugp_viz/examples/` is a fully reproducible run:

```yaml
model: phimdl_1d
params:
  N: 512
  m: 0.5
  g: 0.5
steps: 20000
sample_every: 100
injections:
  - kind: meson
    position: 256
    params:
      separation: 10
measurements:
  - tau_c_mean
  - binding_energy
  - kink_centers
output:
  data: phimdl_1d_meson.json            # → ugp_viz/runs/data/
  figures:
    - type: field_1d
      file: phimdl_1d_meson_field.png   # → ugp_viz/runs/figures/
      params: {title: "phi(x) — meson breather"}
    - type: energy
      file: phimdl_1d_meson_energy.png
    - type: tau_c_heatmap
      file: phimdl_1d_meson_tau.png
    - type: spacetime
      file: phimdl_1d_meson_spacetime.png
  video:                                # optional
    file: phimdl_1d_meson.mp4           # → ugp_viz/runs/videos/
    fps: 30
    window: 200
```

Supported figure types:

| `type:` value              | What it draws                                              |
|----------------------------|------------------------------------------------------------|
| `spacetime`                | Binary CA spacetime diagram                                |
| `tau_c_heatmap`            | τ_c clock-rate heatmap                                     |
| `tau_c_with_trajectory`    | τ_c heatmap with overlaid kink trajectory                  |
| `field_1d`                 | Current `φ(x)` (+ optional `χ(x)`) profile                 |
| `field_3d_three_slice`     | XY, XZ, YZ axis-aligned slices of a 3D field               |
| `field_3d_volumetric`      | True alpha-blended ray-cast of a 3D field                  |
| `field_3d_isosurface`      | Marching-cubes mesh (or voxel cloud) at a chosen iso-level |
| `energy`                   | `E(t)` total-energy trace                                  |

Ready-to-run examples in `ugp_viz/examples/`:

| File                              | What it demonstrates                              |
|-----------------------------------|---------------------------------------------------|
| `phimdl_1d_meson.yaml`            | Kink-antikink meson breather with full diagnostics |
| `phimdl_3d_spherical.yaml`        | Spherical kink loop + volumetric + marching cubes  |
| `afca_glider.yaml`                | Canonical Rule 110 glider on AFCA                  |
| `z7_kg_sr_test.yaml`              | Moving Z7-KG wave packet for SR-error tests        |

---

## Notes and markdown

Every run, experiment config, and saved bundle can carry a markdown
**notes** field. Notes describe the *intent* of an experiment and the
*observations* made during a run. They can be:

- **Inline** in a YAML config:

  ```yaml
  notes:
    title: Two-kink elastic collision
    author: Nova Spivack
    tags: [phimdl_1d, kink-antikink]
    text: |
      # Goal
      Confirm asymptotic attractive force between a gen1 kink and gen1
      antikink at separation 256 cells.
  ```

- **External** markdown files referenced by path:

  ```yaml
  notes: notes/two_kink_collision.md
  ```

  YAML front matter at the top of the `.md` is accepted (`title`,
  `author`, `tags`, `created`, `modified`).

- **Authored in the GUI** — the notes panel has a markdown editor on the
  left and a styled live preview on the right (headings, bold, italic,
  inline code, fenced code blocks, bullets, blockquotes, links). Notes
  travel automatically with the saved-run bundle.

Sidecar markdown files (`<stem>.notes.md`) are also created next to
saved configs (`<stem>.yaml`) so notes remain human-readable outside
the app.

CLI helpers:

```bash
# Print notes attached to any run, config, or .md file:
python -m ugp_viz.cli show-notes ugp_viz/runs/data/two_kink.run.json
python -m ugp_viz.cli show-notes ugp_viz/runs/configs/two_kink.yaml
python -m ugp_viz.cli show-notes ~/Documents/lab/observation.md

# Pass inline or path-based notes to a run:
python -m ugp_viz.cli run --model phimdl_1d --steps 5000 \
    --inject gen1_kink@256 --notes "Quick smoke run" --save-run
```

If the `markdown` PyPI package is installed it is used for HTML
rendering; otherwise a built-in converter handles headings, bold,
italic, code, fenced code blocks, bullets, blockquotes, and paragraphs.

---

## Saved-run bundles

A *bundle* is a self-describing set of companion files sharing a
common stem `<stem>`:

| File                          | What it contains                                                |
|-------------------------------|-----------------------------------------------------------------|
| `<stem>.run.json`             | Manifest: model, params, history, measurements, artifact paths. |
| `<stem>.spacetime.npy`        | Rolling spacetime payload (optional).                           |
| `<stem>.state.npz`            | Compressed engine field snapshot (`phi`, `chi`, `tape`, …).     |
| `<stem>.state.json`           | Engine state metadata (step, time, params, model).              |
| `<stem>.notes.md`             | Markdown notes (with YAML front matter for title/author/tags).  |

Saving and loading:

```bash
# Save a run bundle (everything above):
python -m ugp_viz.cli run --model afca --steps 1000 \
    --inject r110/cook_C2@200 --notes "Cook C2 on AFCA" --save-run \
    --output cook_c2_run

# Re-open in the GUI at exactly the saved step:
python -m ugp_viz.cli gui --load-run \
    ugp_viz/runs/data/cook_c2_run.run.json

# Or load programmatically:
from ugp_viz.state import load_run, rebuild_engine
bundle = load_run("ugp_viz/runs/data/cook_c2_run.run.json")
engine = rebuild_engine(bundle)   # resumes at the saved step / time
```

Bundles are also reachable from the GUI's **File → Open Run…** and
**File → Save Run…** menu items.

---

## Desktop GUI

```bash
python -m ugp_viz.cli gui --model phimdl_1d --inject gen1_kink@256
```

VIZLAB auto-selects the **Tk backend** when Tkinter is available (the
default everywhere Python ships with `tkinter`), falling back to the
Taichi GGUI or a headless matplotlib loop if not. Force a specific
backend with `--backend tk` / `--backend taichi` / `--backend matplotlib`.

Useful pre-load flags:

```bash
# Open a saved run on launch:
python -m ugp_viz.cli gui --load-run ugp_viz/runs/data/cook_c2_run.run.json

# Open a YAML config on launch (model + params + injections):
python -m ugp_viz.cli gui --load-config ugp_viz/examples/phimdl_1d_meson.yaml

# Pre-load notes from a markdown file:
python -m ugp_viz.cli gui --notes notes/two_kink_collision.md
```

### Tk backend (default — full feature set)

**Menubar:**

| Menu       | Items                                                          |
|------------|----------------------------------------------------------------|
| File       | Save Run · Open Run · Save Experiment Config · Load Experiment Config · Open Notes · Save Notes · Quit |
| Simulation | Run / Pause · Step one frame · Stop · Reset                    |
| View       | Reset zoom / pan · Save screenshot · Save MP4 (spacetime)      |
| Help       | About UGP VIZLAB · Open repository · Author website            |

**Matplotlib NavigationToolbar** is embedded above the plot — full
zoom box, pan (drag with the hand tool), home / back / forward,
subplot configuration, and a built-in PNG/PDF/SVG save. Zoom and pan
work on every panel (spacetime, τ_c heatmap, 3D slices, energy trace).

**Sidebar:**

- **Model**: dropdown switches engine on the fly; the parameter editor
  and catalog list refresh automatically.
- **Initial condition**: dropdown showing only the kinds each engine
  actually supports (e.g. AFCA: `ether`, `vacuum`, `random`, `load`;
  PhiMDL: `vacuum`, `random`, `load`).
- **Engine parameters**: auto-generated form with one field per entry
  in `engine.default_params`. Numeric, boolean, and string types are
  recognized. Press **Apply (rebuilds engine)** to commit a new
  parameter set — the engine is rebuilt and re-injected. This is how
  you change e.g. the tape width `L`, lattice size `N`, `Nx/Ny/Nz`,
  time step `dt`, mass `m`, coupling `g`, or `backend: taichi`.
- **Simulation transport**: ▶ Run · ❚❚ Pause · Step · Stop · Reset.
  Substeps-per-frame and rolling-window size are tunable spinboxes.
- **Inject from catalog**: a scrollable list of every catalog entry
  registered for the current model (including all 374 R110 gliders for
  the FCA / AFCA models). Type a cell index or `center` and press
  **Inject selected**.

**Notes panel** (bottom): see [Notes and markdown](#notes-and-markdown).

**Status bar**: short status messages on the left, FPS · step counter
on the right.

**About modal** (Help → About): app name, byline (*By Nova Spivack,
2026*), programme line (*Part of the UGP Physics Programme*), clickable
website and repository links, description, license, and version. The
same identity is printed by `python -m ugp_viz.cli about`.

### Taichi GGUI fallback

Activated with `--backend taichi`. Sidebar identical in spirit but uses
Taichi's immediate-mode widgets (no menubar, no file dialogs, no
markdown editor). Useful when you want the absolute lowest-overhead
canvas on small grids and a Taichi runtime is already initialized.

### Matplotlib fallback keyboard controls (headless)

| Key            | Action                                          |
|----------------|-------------------------------------------------|
| `space`        | Pause / resume                                  |
| `r`            | Reset                                           |
| `→` (right)    | Single step                                     |
| `F12`          | Screenshot                                      |
| `v`            | Save MP4 (last spacetime window)                |
| `3`            | Save volume PNG (3D models only)                |
| `i`            | Save isosurface PNG (3D models only)            |
| `k`            | Auto-mark every kink (1D continuum models only) |

### Kink force readout

For 1D continuum models (Phi_MDL 1D, Z7-KG), VIZLAB tracks kinks across
frames and prints a live force readout in the sidebar / overlay. The
detector finds every kink by scanning the local energy density for
peaks; for each marked pair `(a, b)` we report

```
F_b ≈ - (dE/dx)|_{x = x_b}
```

with central-difference derivatives at sub-grid resolution. Sign
convention: when `F_a * F_b < 0` with `x_a < x_b` the pair is
attracting (typical kink-antikink) — when `F_a * F_b > 0` it is
repelling (typical kink-kink).

---

## Taichi GPU backend

Pass `backend=taichi` in `params` (CLI or YAML) to run an engine on
the GPU:

```bash
PYTHONPATH=. python -m ugp_viz.cli run \
    --model phimdl_3d \
    --params Nx=64,Ny=64,Nz=64,backend=taichi \
    --steps 200 --inject spherical_kink \
    --output run_gpu
```

Approximate wall-clock cost (Apple M2 Max, single-process; **final
read forces device sync**):

| Engine     | Grid          | Steps | NumPy   | Taichi/Metal | Speedup |
|------------|---------------|-------|---------|--------------|---------|
| phimdl_3d  | 64³           | 100   | 0.50 s  | 0.019 s      | ≈27×    |
| phimdl_3d  | 64³           | 1000  | 4.98 s  | 0.05 s       | ≈100×   |
| phimdl_1d  | N=1024        | 2000  | 0.08 s  | 0.28 s       | 0.30×   |
| phimdl_1d  | N=65536       | 2000  | 3.4 s   | 0.55 s       | 6.2×    |
| z7_kg (fd) | N=4096        | 2000  | 0.07 s  | 0.14 s       | 0.50×   |

Small 1D grids are kernel-launch-overhead dominated; Taichi wins
overwhelmingly on 3D where the stencil cost dwarfs launch overhead.
For very short 3D runs (≤10 steps) NumPy may still win because Taichi
JIT-compiles the kernel on first call.

Kernels run in `f32` on the device for Metal portability (Metal has
no hardware `f64`); snapshots are upcast back to `f64` so downstream
analysis stays in double precision. Round-off agreement between
backends is ~10⁻⁶ relative (verified for 100-step PhiMDL 3D runs).

Override the arch with `UGP_VIZ_TAICHI_ARCH=cuda` (or `vulkan`, `cpu`)
before launching the CLI / GUI.

---

## 3D rendering

For 3D models VIZLAB provides three complementary renderers:

1. **Axis-aligned slices** (`field_3d_three_slice`) — three orthogonal
   2D cross-sections at user-chosen indices. Cheap; good for quick
   inspection.
2. **Alpha-blended volumetric ray cast** (`field_3d_volumetric`) —
   per-voxel emission via the chosen colormap, per-voxel density
   from `|φ − ⟨φ⟩|`, traced along a configurable camera direction
   (`azim`, `elev`). Pure NumPy; no GL stack required.
3. **Marching-cubes isosurface** (`field_3d_isosurface`) — wraps
   `skimage.measure.marching_cubes` when scikit-image is available;
   falls back to a voxel point cloud otherwise. Best for visualizing
   domain-wall manifolds at `φ = 0`.

All three are available from the YAML runner and from the live GUI
(buttons in the Taichi sidebar; `3` / `i` keys in the matplotlib
fallback).

---

## Output paths

VIZLAB never writes outside the `ugp_viz/` package tree by default —
every artifact path is rewritten to live under:

```
ugp_viz/runs/data/         # *.json experiment reports
ugp_viz/runs/figures/      # *.png static figures
ugp_viz/runs/videos/       # *.mp4 video exports
ugp_viz/runs/screenshots/  # GUI screenshots
ugp_viz/runs/states/       # save_state / load_state snapshots
```

When the path passed to a CLI flag or YAML field is **absolute** or
contains **a directory component**, VIZLAB honors it as-is — that's
the escape hatch for users who want figures co-located with a paper
or shared scratch directory.

Override the entire runs root with `UGP_VIZ_RUNS_DIR=/some/abs/path`.

The `ugp_viz/runs/` tree is `.gitignore`d (it holds regeneratable
artifacts, sometimes large videos and PNGs).

---

## Extending VIZLAB

Add a new physics engine in three steps:

1. Subclass `SimEngine` in `ugp_viz/engines/<your_engine>.py`:

   ```python
   from ugp_viz.engines.base import SimEngine, FieldSnapshot

   class MyEngine(SimEngine):
       model_name = "myengine"
       spatial_dim = 1
       default_params = {"N": 256, "dt": 0.01}

       def _setup(self) -> None: ...
       def reset(self, ic=None) -> None: ...
       def inject(self, spec) -> None: ...
       def _step_impl(self, n_steps: int) -> None: ...
       def snapshot(self) -> FieldSnapshot: ...
   ```

2. Register it in `ugp_viz/engines/registry.py` (`_ENGINES` table —
   one line: `"myengine": ("ugp_viz.engines.myengine", "MyEngine")`).

3. Drop one or more JSON entries in `ugp_viz/catalog/myengine/`. They
   automatically show up under `ugpviz catalog list` and as buttons
   in the GUI.

The CLI, GUI, runner, and figure library will work immediately — none
of them branch on `model_name`. They just call the SimEngine API.

---

## References

- M. Cook, *Universality in Elementary Cellular Automata*, Complex
  Systems 15(1), 1–40 (2004).
- G. J. Martinez, *Phases fi_1 for gliders in Rule 110*, ESCOM-IPN
  (2001 / updated 2004).
  <http://comunidad.escom.ipn.mx/genaro/rule110/listPhasesR110.txt>
- N. Spivack, *rule110-lean: A Lean 4 formalization of Cook's
  Rule 110 universality theorem.*
  <https://github.com/novaspivack/rule110-lean>
- Taichi authors, *Taichi: a domain-specific language for productive
  parallel programming.*  <https://docs.taichi-lang.org>
