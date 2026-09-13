# PR-0 Animation and Measurement Scripts

Runnable scripts that reproduce canonical simulations and measurements. All output to `pr0_system/media/`.

**Prerequisite:** `pip install -e .` from the `pr0_system/` root.

---

## Standalone scripts (no pr0_system package needed)

These use only `numpy`, `scipy`, and `matplotlib`.

| Script | What it does | Run command |
|--------|-------------|-------------|
| `animate_soliton_binding.py` | D-minimization soliton binding animation | `python animate_soliton_binding.py` |
| `pr0_bootstrap_binding.py` | Core bootstrap class used by the above (library, not run directly) | — |
| `pr0_emergent_qcd.py` | Emergent QCD: meson formation from the strong-force bootstrap | `python pr0_emergent_qcd.py` |

## Simulation scripts (require pr0_system)

Install the package first (`pip install -e .` from repo root).

### Animations — single-force and EM

| Script | What it does | Key args |
|--------|-------------|----------|
| `animate_collision_em_attraction_multipane_al.py` | EM attraction — opposite-charge solitons, multi-panel (AL core) | `--sep`, `--vy`, `--frames` |
| `animate_collision_em_repulsion_multipane_al.py` | EM repulsion — same-charge solitons, Coulomb-like scattering (AL core) | `--sep`, `--vx`, `--frames` |
| `animate_collision_em_repulsion_multipane.py` | EM repulsion multi-panel (standard core) | `--sep`, `--vx` |
| `animate_collision_strong_capture_multipane.py` | Strong-force head-on capture | (see defaults) |

### Animations — unified 4-force

| Script | What it does |
|--------|-------------|
| `animate_unified_2body_multi_panel.py` | All 4 forces active — 2-body multi-panel (density, phase, EM field, weak field) |
| `animate_unified_2body_all_forces.py` | All 4 forces active — 2-body single-panel overview |
| `animate_unified_3body_multipane_al.py` | 3-body EM with AL core — multi-panel (density, phase, V_em, \|∇V_em\|) |
| `animate_unified_3body_multi_panel.py` | All 4 forces — 3-body system |

### Force-combination smoke tests

| Script | What it shows |
|--------|--------------|
| `run_strong_plus_em_binding.py` | Strong + EM binding |
| `run_strong_plus_gravity.py` | Strong + geometric gravity |
| `run_strong_plus_weak_binding.py` | Strong + Yukawa-weak binding |
| `run_unified_three_body.py` | 3-body EM + gravity (two +, one −) |
| `run_unified_free_drift.py` | Free-particle drift — baseline validation |

### Measurement and validation

| Script | What it measures | Output |
|--------|-----------------|--------|
| `measure_meson_binding.py` | Binding energies of meson-like states as a function of mass — hadron spectroscopy | `media/meson_binding.csv` |
| `measure_qm_dispersion.py` | Emergent dispersion relation ω(k) and extraction of effective ℏ | `media/qm_dispersion.csv`, `media/dispersion_relation_omega_k.png` |
| `validate_born_rule.py` | Verifies P(detection) ∝ \|ψ\|² by sampling the field (Born rule emergence) | `media/born_rule.csv`, `media/born_rule_validation.png` |

### Parameter sweeps and analysis

| Script | What it does |
|--------|-------------|
| `sweep_em_orbit_params.py` | Maps capture/orbit/flyby regions in the high-energy EM parameter space | `media/em_high_energy_sweep.csv` |
| `plot_scattering_theta_vs_b.py` | Plots scattering deflection angle θ vs. impact parameter b (Rutherford comparison) | reads `scattering_log.csv` |

---

## Examples

```bash
# From examples/animations/:

# Multi-panel 2-body unified simulation (recommended)
python animate_unified_2body_multi_panel.py

# EM attraction with custom parameters:
python animate_collision_em_attraction_multipane_al.py --vy 0.15 --sep 12 --frames 800

# Measure emergent Planck constant from dispersion relation:
python measure_qm_dispersion.py

# Verify Born rule from field dynamics:
python validate_born_rule.py
```

All output goes to `../../media/` (i.e., `pr0_system/media/`).
