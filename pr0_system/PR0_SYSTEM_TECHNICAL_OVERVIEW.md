# PR-0 System: Technical Overview

**Date**: 2025-11-09  
**Companion docs**: [`README.md`](./README.md), [`MODULE_ORGANIZATION.md`](./MODULE_ORGANIZATION.md), [`PR0_SYSTEM_NOVELTY_AND_ARCHITECTURE.md`](./PR0_SYSTEM_NOVELTY_AND_ARCHITECTURE.md)

---

## 1. Introduction — Purpose and Design Principles

PR-0 (Physics Rule 0) is an emergent-physics substrate that demonstrates how spacetime, matter fields, and the four fundamental interactions arise from ontological dissonance minimization. The `pr0_system` package implements:

- A lattice-based complex scalar field `ψ` coupled to a mediator field `χ` that redistributes energy and enforces attractive dynamics.
- Ablowitz–Ladik integrators with adaptive damping to sustain soliton stability while permitting bound-state formation.
- Force-discovery bootstraps that meta-learn coupling constants by minimizing the ontological dissonance functional `D`.
- Overlay integrators that combine the strong-force bootstrap core with electromagnetic, weak, and gravitational overlays to reproduce Standard-Model-style behavior.

Design priorities:

1. **Scientific fidelity** — physics-first implementation with explicit Laplacian operators, FFT-based spectral solvers, and carefully clipped fields to avoid numerical artifacts.
2. **Extensibility** — modular directories for core state, evolution dynamics, bootstrap machinery, force-specific bootstraps, diagnostics, and integration overlays.
3. **Reproducibility** — each class or routine includes parameter documentation enabling reproducibility across experimental runs.

---

## 2. Directory Survey

| Subsystem | Path | Description |
|-----------|------|-------------|
| Package root | `pr0_system/__init__.py` | Declares package metadata and exposes subpackages. |
| Core lattice & fields | `pr0_system/core/` | Foundational data structures (`Lattice`, `FieldState`, `ParameterSet`). |
| Evolution operators | `pr0_system/evolution/` | Ablowitz–Ladik solver (`PR0_Final`), mediator evolution, adaptive damping. |
| Bootstrap logic | `pr0_system/bootstrap/` | Ontological dissonance metric and SDS bootstrap driver. |
| Force discovery suites | `pr0_system/forces/` | Specialized bootstraps for strong, electromagnetic, weak, and gravity analogues. |
| Unified integrator | `pr0_system/integration/unified.py` | Overlay controller composing base evolution with optional force layers. |
| Diagnostics | `pr0_system/analysis/diagnostics.py` | Peak-finding, toroidal distance helpers, curvature heatmap generation, and dissonance time-series exporters. |
| Examples | `pr0_system/examples/` | Reference scripts for basic and two-soliton scenarios. |
| Tests | `pr0_system/tests/test_smoke.py` | Import-and-step smoke test ensuring solver stability. |

All submodules rely on `numpy`, `scipy.ndimage`, and `numpy.fft`.

---

## 3. API Specification

### 3.1 Core State (`core/`)

| Symbol | Location | Summary |
|--------|----------|---------|
| `Lattice` | `core/lattice.py` | Square lattice with periodic boundary support and discrete Laplacian helper. |
| `DynamicGraph` | same | Stub for future Pachner-move topologies. |
| `FieldState` | `core/fields.py` | Owns `ψ`, `χ`, `χ̇`, history buffers, soliton injection, and energy/charge diagnostics. |
| `ParameterSet` | same | Container for evolution parameters (AL nonlinearity, mediator coupling, damping coefficients, gravitational constant). |

`FieldState.add_soliton(...)` generates localized excitations with sech envelopes and velocity-imprinted phases. History buffers (`psi_history`, `chi_history`) support dissonance calculations that require temporal correlations.

### 3.2 Evolution Dynamics (`evolution/`)

| Symbol | Location | Summary |
|--------|----------|---------|
| `PR0_Final` | `evolution/ablowitz_ladik.py` | Ablowitz–Ladik solver with split-step FFT kinetic updates, mediator coupling, adaptive damping, and hard clipping safeguards. |
| `MediatorField` | `evolution/mediator.py` | Damped wave-equation evolution for `χ`, plus `compute_force_on_psi` for back-reaction. |
| `AdaptiveDamping` | `evolution/damping.py` | Distance-transform-driven damping field, tuned to discovered Goldilocks parameters (`γ_base=0.013`, `γ_scale=0.644`). |
| `UniversalDamping` | same | Uniform exponential damping alternative. |

### 3.3 Bootstrap Machinery (`bootstrap/dissonance.py`)

- `compute_ontological_dissonance(psi, chi, history)` — Implements the four-term dissonance metric.
- `SDSBootstrap` — Generic bootstrap that adapts damping parameters to minimize dissonance using simulated annealing schedules.

### 3.4 Force Discovery Suites (`forces/`)

| Class / Function | Path | Purpose |
|------------------|------|---------|
| `BootstrapPR0` | `forces/strong.py` | Core strong-force bootstrap with separation-aware damping and multi-scale fitness. |
| `compute_dissonance_EM_final`, `BootstrapEM_Final` | `forces/em.py` | Spectral Coulomb solver targeting long-range behavior and precise power-law exponents. |
| `compute_dissonance_weak_final`, `BootstrapWeak_Final` | `forces/weak.py` | Yukawa-style short-range bootstrap emphasizing β > 0.3 cutoffs. |
| `compute_dissonance_gravity`, `BootstrapGravity` | `forces/gravity.py` | Effective curvature bootstrap linking energy density to gravitational coupling `G_grav`. |

Each bootstrap class follows a consistent interface:
- `__init__(L_x, L_y)` — grid setup and initial parameter seeds.
- `set_soliton(...)` — injects initial conditions.
- `step(dt=0.01)` — performs one evolution step and periodically triggers meta-learning.
- `density()` and `current_step` — diagnostics consumed by tests or overlays.

### 3.5 Unified Integrator (`integration/unified.py`)

- `OverlayConfig` dataclass defines toggles and scaling factors for EM, weak, gravity, and strong overlays.
- `UnifiedPR0` orchestrates a base solver and applies overlays after each core step.
- `bootstrap/annealing.py` and `bootstrap/meta_learn.py` centralize simulated annealing schedules and best-metric tracking so every bootstrap shares identical stochastic control logic.

### 3.6 Analysis Tools (`analysis/diagnostics.py`)

- `find_top_k_peaks(density, k)` — returns coordinates of dominant soliton peaks.
- `torus_distance(a, b, L_x, L_y)` — distance metric with periodic wrapping.
- `order_three_by_x(coords)` — helper for deterministic ordering of multiple peaks.

### 3.7 Examples & Tests

- `examples/01_basic_soliton.py`, `examples/02_two_soliton_binding.py` — canonical initialization flows.
- `tests/test_smoke.py` — verifies imports, soliton injection, and stability over ten steps.
- `tests/test_bootstrap_regression.py` — regression and diagnostics coverage for annealing utilities.

---

## 4. Operational Narrative — How the System Works

1. **State initialization** — Create a `Lattice` or use solver classes with embedded state. Soliton seeds encode localized excitations with optional relative phases to represent charges.
2. **Evolution core** — The Ablowitz–Ladik engine advances `ψ` using a split-step method: half-step cubic nonlinearity → FFT-based kinetic term → mediator and damping corrections.
3. **Adaptive damping** — `AdaptiveDamping.compute_damping_field` uses a distance transform to suppress oscillations near merging solitons while keeping distant regions lightly damped.
4. **Meta-learning loops** — Every 200 steps, simulated annealing adjusts parameters toward lower dissonance.
5. **Force overlays** — `UnifiedPR0` copies the core `ψ` state into overlay layers and applies phase rotations or damping proportional to potentials computed per layer.
6. **Diagnostics** — Bootstraps expose `density()` and `measure_separation()` helpers for analysis.
7. **Results** — After 20k–50k steps, each bootstrap logs best-fit parameters (α, power-law exponent, β cutoff, gravitational coupling).

---

## 5. Usage Patterns

### 5.1 Minimal Strong-Force Bootstrap

```python
from pr0_system.forces import strong

system = strong.BootstrapPR0(L_x=64, L_y=64)
system.set_soliton(x0=24, y0=32, amplitude=3.0, width=3.0, velocity_x=0.1, charge=+1)
system.set_soliton(x0=40, y0=32, amplitude=3.0, width=3.0, velocity_x=-0.1, charge=-1)

for step in range(40000):
    system.step(dt=0.01)

print(f"Best fitness: {system.best_fitness:.4f}")
```

### 5.2 Unified Overlay Run

```python
from pr0_system.integration.unified import UnifiedPR0, OverlayConfig

overlay = OverlayConfig(enable_em=True, enable_weak=True, enable_gravity=True, enable_strong=True)
solver = UnifiedPR0(L_x=64, L_y=64, overlay=overlay, core_mode="strong")

solver.set_soliton(x0=28, y0=32, amplitude=3.0, width=3.5, velocity_x=0.05, charge=+1)
solver.set_soliton(x0=36, y0=32, amplitude=3.0, width=3.5, velocity_x=-0.05, charge=-1)

for _ in range(2000):
    solver.step(dt=0.01)

density = solver.density()
```

### 5.3 Using Diagnostics

```python
import numpy as np
from pr0_system.analysis import diagnostics

density = np.abs(solver.psi) ** 2
peaks = diagnostics.find_top_k_peaks(density, k=2)
distance = diagnostics.torus_distance(peaks[0], peaks[1], solver.L_x, solver.L_y)
```

---

## 6. Integration Notes and Best Practices

- **Numerical stability**: Stick to `dt ≤ 0.01`. Internal clipping keeps `|ψ|` ≤ 20 and `χ` ≤ 10.
- **Boundary conditions**: All current lattices are toroidal.
- **Meta-learning cadence**: Bootstraps log progress every 200 steps.
- **Extending overlays**: When adding new forces, follow the EM overlay template: copy `ψ`, compute potentials/forces, apply bounded phase rotations, and renormalize.

---

## 7. Related Documentation

- [`README.md`](./README.md) — narrative overview, quick-start snippets, and discovered-force summary.
- [`MODULE_ORGANIZATION.md`](./MODULE_ORGANIZATION.md) — refactor plan and module inventory.
- [`PR0_SYSTEM_NOVELTY_AND_ARCHITECTURE.md`](./PR0_SYSTEM_NOVELTY_AND_ARCHITECTURE.md) — novelty analysis and comparison to prior art.
