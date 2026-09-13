# Z₇ Kink Field — Live Interactive Visualization

A single-page, offline web app visualizing the dynamics of a real scalar field
Φ(x,t) with seven degenerate vacua:

- Lagrangian: L = ½(∂Φ)² − V(Φ), with V(Φ) = (m²/49)(1 − cos 7Φ)
- Equation of motion: Φ_tt = ∇²Φ − (m²/7)·sin(7Φ)
- Vacua: Φ_k = 2πk/7, k = 0…6 (exact Z₇ shift symmetry)
- Mass scale: m = 1776.86 MeV ⇒ kink width 1/m ≈ 0.111 fm,
  kink rest mass M_kink = (8/49)·m = 290.10 MeV

No build step, no network dependencies (plain HTML + ES modules + Canvas2D /
WebGL2).

## How to run

```bash
cd visualizations/phimdl_kink_dynamics
python3 -m http.server 8710
# open http://localhost:8710
```

(A server is required because the app uses ES modules and fetches replay data;
any static file server works.)

The two bundled reference-run replays (`replay/*.meta.json` + `replay/*.field.f32`)
already ship with the app — no conversion step is needed to run it as-is.
`export_replay_json.py` is only needed to regenerate those files from a fresh
raw NPZ simulation run (an internal research artifact, not part of this app):

```bash
python3 export_replay_json.py --source-dir /path/to/dir/with/the/raw/npz/files
```

## Modes

| Mode | What it shows | Claim level |
|---|---|---|
| **1D kinks** | Live field strip colored by vacuum index, Φ(x) curve, scrolling spacetime history (worldlines). Kinks are moving boundaries between vacuum colors. | Pure sector: **EXACT** (integrable dynamics). Perturbed: **PROVISIONAL** (proxy). |
| **2D domains** | The same scalar EOM on a periodic 2D grid (GPU leapfrog, 512²). In 2D a single scalar's topological objects are domain **walls**; the view shows a Z₇ domain network with moving, tension-driven walls. | Same as 1D per dynamics toggle; the "walls, not point particles" statement is the honest 2D physics. |
| **3D structure** | Volume render of the certified **extended** structure — either a single flat domain wall separating the vacuum from one PSC-admissible sector, or three walls meeting along a shared axis (the 3D analogue of the 2D "triple junction" preset). A fixed gray coordinate grid (1/m tick spacing) is drawn for spatial reference; it is not part of the field. | **PROVEN** no-go: no compact, finite-energy 3D particle exists in this field theory. The rendering itself is a static illustration of the certified extended structure. |

### Dynamics toggle (1D and 2D)

- **Pure (exact):** V as above. The sector is exactly integrable — kinks always
  pass through each other with a spatial phase shift, kink–antikink pairs never
  annihilate, and no radiation is produced. Transient dips of the kink census
  during interpenetration are level-crossing occlusion, not annihilation.
- **Perturbed (proxy):** adds η·(m²/49)(1 − cos 14Φ) with η adjustable up to
  0.05 — an integrability-breaking perturbation (double-sine-Gordon proxy,
  PROVISIONAL). Slow kink–antikink pairs (v_rel ≲ 0.10 at η = 0.05) capture
  into oscillating bions and decay by radiation — genuine annihilation.

## Controls

### 1D
| Action | Effect |
|---|---|
| Drag on the **field strip / curve panel** (the top panel — not the spacetime history panel below it, which is view-only) | Add a kink at that point; horizontal drag distance sets its velocity (arrow preview). Kink count and marker update instantly, with a brief highlight ring at the insertion point. |
| Shift + drag | Add an antikink instead. |
| Mouse wheel | Zoom (single-kink profile ~0.5 fm up to the full ~100 fm domain); physical scale bar bottom-right. |
| Right-drag / Alt-drag | Pan. |
| Random gas | Populate the line with N (2–40) random kinks/antikinks (min separation 15/m, |v| ≤ 0.35). |
| Pause / Step / Reset | Freeze, advance one leapfrog step, or clear to vacuum. |
| Speed | Simulated time units per wall-clock second (log scale); defaults to maximum. |
| Zoom slider | Same range as the mouse wheel (fully zoomed out → maximum magnification, log scale), kept in bidirectional sync with wheel zoom; the readout shows the magnification factor relative to fully zoomed out. Works in all three modes (in 3D it drives the camera distance). |
| Replay | Load one of the two bundled reference runs (24-kink pure gas; 12-kink η = 0.05 gas with 3 annihilation events). |

### 2D
| Action | Effect |
|---|---|
| Mouse wheel / zoom slider | Zoom, always (both stay in sync). |
| Drag (Pan mode) | Pan. |
| Drag (Paint mode) | Stamp the selected vacuum color at the brush location (right-drag / alt-drag still pans in Paint mode). |
| Paint vacuum palette | Pick which of the 7 vacua the brush paints. |
| Brush slider | Brush radius, 1–15% of the periodic domain. |
| Preset selector + Apply preset | Load a ready-made initial condition (see below) instead of painting by hand. |
| Domain statistics panel | Live domain count, largest-domain area fraction, and wall-cell fraction (recomputed every ~2 s from the same GPU readback used for the energy badge — no extra cost). |
| Isolated-domain size vs. time panel | Live chart and quantitative trend readout tracking the largest domain *other than* the background over time (see "Isolated-domain decay measurement" below). "Reset measurement" clears the history and starts timing fresh without touching the field. |

**Presets:** `random` (the original self-organizing long-wavelength seed),
`blank vacuum` (uniform Φ=0, for painting a scenario entirely by hand),
`single bubble`, `N particles` (2–12 non-overlapping bubbles, each randomly
assigned one of the four SM sectors {up-quark, W⁺/positron, charged lepton,
down-quark} — a controllable, size-adjustable multi-particle collision
setup), `proton` / `neutron` (three quark-sector
bubbles with charge-correct windings — uud: 2,2,6 → +2/3+2/3−1/3 = +1; udd:
2,6,6 → +2/3−1/3−1/3 = 0 — clustered close together; **illustrative only**,
not a derived bound state, since this pure-Φ field has no color/gauge
sector to actually confine them — watch whether they stay clustered or
drift apart under Φ-only dynamics alone. A `pion` preset was deliberately
**not** added: P48's own glossary states sectors {1,5} are dark-branch-only
antiquark conjugates, not stable in our SM branch, so there is no honest
elementary-winding representation of an antiquark to build one from), and
`stripes` (all 7 vacua), `checkerboard`, and `triple junction` — three domains (adjacent vacua 2, 3, 4, so two of the
three internal walls are single elementary kinks and the third is an
unavoidable composite 2-step wall — the Z₇ vacuum ring has no triangles, so no
3-domain junction can be made of three elementary walls) meeting at a point
inside a uniform background disk (vacuum 6). This is the direct 2D analog of
the open question of whether the 3+1D triple-winding intersection carries
genuinely localized excess energy. All non-random, non-blank presets are
pre-smoothed (periodic box blur, ~1 kink-width scale) before handing off to
the leapfrog integrator, so they start near a relaxed profile instead of
ringing violently from a sharp step discontinuity. Because `V(Φ)` has period
`STEP = 2π/7`, any integer multiple of `STEP` congruent to a vacuum index `k`
mod 7 is physically the same vacuum; every preset picks the representative
closest to its neighboring region (`phiNear` in `field2d.js`) so the box-blur
(which smooths the raw real-valued Φ, not mod-7 labels) bridges regions by
the genuinely shortest elementary-kink path — the naive choice (always using
`k·STEP` for `k` in `0..6`) produces spurious extra rings of intermediate
vacua for any pair more than half the ring apart (e.g. vacuum 6 next to
vacuum 0 is one elementary step the "other way", not six).

See the in-app hint for why pure vs. perturbed is much harder to see by eye in
2D than in 1D (curvature-driven wall coarsening dominates in both modes;
integrability is a 1+1D-only effect).

### Advanced / Verification panel (1D mode)

A collapsible panel (collapsed by default) with two opt-in, OFF-by-default features:

- **Show exact solution:** overlays the exact closed-form Hirota N-soliton
  solution (dashed amber curve) for the kinks currently on the strip, on top
  of the simulated field, and reports the live max discrepancy between them
  (`js/exactsoliton.js`). Pure sector only (no closed-form solution exists in
  Perturbed mode); real-time-capped at 10 active kinks; degenerate
  configurations (equal velocities, or kinks placed too close together) show
  an explicit "undefined for this configuration" message instead of a wrong
  or crashing overlay. A small but nonzero, stable residual (growing slowly
  with elapsed simulation time from ordinary leapfrog discretization drift)
  is the expected and correct result — not exactly zero, and not blowing up.
- **Explore: what if the SCC weren't satisfied?:** reveals a slider for a
  hypothetical m_φ (defaulting to the real, derived SCC value, 1776.86 MeV,
  clearly marked with a tick), a live derived-quantity table (kink mass,
  kink width), and an explicit numeric verdict comparing the hypothetical
  kink mass to the real 290.10 MeV value. The running simulation's physical-
  unit display (scale bar, time, energy) tracks the slider value live and
  exactly — not a static comparison table — because the natural-unit field
  equation contains no m_φ at all (it is scale-covariant); only the length/
  time/MeV conversions depend on it, so this is the literal, exact statement
  of scale covariance, not an approximate re-run. Toggling the checkbox off
  restores the derived value exactly; the underlying PDE integrator is never
  altered.

Run `node verify_exact_soliton.mjs` to re-verify `exactsoliton.js` against
closed-form solutions and finite-difference PDE residuals (8 independent
checks).

### Isolated-domain decay measurement

A closed domain-wall loop in 2D is generically expected to shrink over time:
wall tension makes curved walls contract, so an isolated bubble should lose
area at a steady pace and eventually vanish, rather than persisting
indefinitely. The "Isolated-domain size vs. time" panel turns that
expectation into a live, quantitative check instead of an eyeballed
impression. It tracks the area fraction of the largest domain *other than*
the background (a structural definition — whichever connected region is
largest overall is treated as "background", and the panel tracks the next
largest one), fits a straight-line and an exponential curve to the recent
history, and reports whichever fits better along with a measured rate — or
reports "no measurable decay" if the fit is statistically indistinguishable
from flat (the slope does not exceed twice its own standard error). The
panel is cleanest with a single isolated domain (the **single bubble**
preset): with several domains present, "largest non-background" can jump
between different bubbles as they evolve at different rates, contaminating
a clean single-object measurement. "Reset measurement" clears the history
and restarts the timer without touching the field, so a fresh, uncontaminated
observation window can be started at any point (for example right after
painting a new configuration by hand).

### 3D

Two general theorems prove that a
spatially-compact, winding-carrying, finite-energy particle is **impossible**
in this field content, for every geometry and symmetry class tested. GTE
particles are second-quantized Fock-space excitations certified by an
**extended** classical background instead (Lean-certified, zero
sorry: `phimdl_fock_particle_master_bundle`). This mode renders that
certified extended structure — never a compact blob — as a static
illustration.

| Action | Effect |
|---|---|
| Structure toggle | **Single wall**: a flat domain wall separating the vacuum (k=0) from one selectable PSC-admissible sector. **Triple junction**: three walls (vacua 2, 3, 4) meeting along a shared axis — the 3D analogue of the 2D "triple junction" preset, and the geometry behind the exact BPS wall-junction energetics below. |
| Far-side vacuum selector (wall mode only) | Choose which winding sector (w = 2, 3, 4, 6) is on the far side of the wall; recolors it with that sector's vacuum hue. |
| "Why not a compact particle?" panel | States the wall tension σ ≈ 23.5 GeV/fm² (= M_kink per unit transverse area) and, in junction mode, the exact junction-point energy E₃ = 8·M_kink = 2320.8 MeV — with the explicit statement that neither rescues a finite-energy particle, since the wall areas themselves still diverge. |
| Drag | Rotate the camera; pauses the slow auto-orbit, which resumes automatically ~4 s after you release. |
| Mouse wheel / zoom slider | Zoom (camera distance); both stay in sync. |
| Reset view | Restore the default camera and resume auto-orbit immediately. |

Both structures are static illustrations (not a live field simulation) of
the certified extended geometry; a genuine dynamical 3D field simulator on a
full 3D grid is a natural direction for future extension.

## Numerics

- Integrator: leapfrog / Störmer–Verlet, second order, symplectic; the same
  stencil and time staggering as the verified reference simulation scripts
  (fixed-value boundaries in 1D, periodic in 2D), dt = 0.5·dx (stability bound
  dt ≤ 0.9·dx in 1D, dt ≤ dx/√2 in 2D).
- 1D grid: 18 432 points, dx = 0.05/m (domain ≈ 102 fm).
- 2D grid: 512², dx = 0.12/m, integrated in a WebGL2 fragment shader
  (ping-pong float textures; the neighbor half-update is reconstructed
  in-shader so the update is exact leapfrog).
- For η > 0 the static kink of the perturbed potential is obtained by gradient
  flow before insertion, so added kinks are true static solutions of the
  active dynamics.
- Correctness badges in the header: live relative energy drift ΔE/E (green
  when < 10⁻³) and net topological winding (boundary plateau difference, an
  exactly conserved Z₇ charge).

## Physics readouts and units

Internally the code uses natural units m = 1. Conversions shown in the UI:
1 length unit = ħc/m = 0.11105 fm, 1 time unit = 0.11105 fm/c, energies are
multiplied by m = 1776.86 MeV. In 2D the energy readout is per unit transverse
thickness (MeV·(m·dz)).

## Winding sectors → particles

| w | sector | charge Q |
|---|---|---|
| 0 | vacuum | 0 |
| 1 | dark sector (PSC-forbidden) | — |
| 2 | up-type quarks | +2/3 |
| 3 | W⁺ / positron | +1 |
| 4 | charged leptons (realized as 3 antikinks) | −1 |
| 5 | dark sector (PSC-forbidden) | — |
| 6 | down-type quarks | −1/3 |

Q = w_c/3 with w_c = w for w ≤ 3 and w_c = w − 7 for w ≥ 4 (winding is a
mod-7 charge).

## Files

- `index.html`, `style.css` — app shell and dark theme
- `js/constants.js` — physical constants and the sector table
- `js/palette.js` — the seven vacuum hues and vacuum-index mapping
- `js/field1d.js` — 1+1D leapfrog integrator, kink insertion, gas construction,
  energy/winding/census diagnostics
- `js/view1d.js` — 1D rendering (strip, curve, spacetime history) and interaction
- `js/field2d.js` — 2D GPU leapfrog + domain rendering
- `js/view3d.js` — 3D extended-structure (wall / triple-junction) raymarcher
- `js/trend.js` — reusable linear/exponential trend-fitting for scalar time series
- `js/historychart.js` — reusable Canvas2D line/area chart for a scalar time series
- `js/main.js` — mode switching and control wiring
- `js/exactsoliton.js` — exact Hirota N-soliton solutions (pure sector),
  including the scattering-shift correction needed to match Field1D's
  kink-placement convention; used by the Advanced/Verification panel
- `export_replay_json.py` — converts the NPZ replay artifacts to the
  `replay/*.meta.json` + `replay/*.field.f32` pairs the app loads
- `verify_exact_soliton.mjs` — standalone Node.js verification of
  `js/exactsoliton.js` against closed-form solutions and finite-difference
  PDE residuals (development/verification script, not part of the app)
