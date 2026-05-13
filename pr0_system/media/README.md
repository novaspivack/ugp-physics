# PR-0 System: Media Gallery

Canonical simulations illustrating emergent force discovery and soliton dynamics.

---

## Videos

### Discovery and binding

| File | What it shows | How to reproduce |
|------|--------------|-----------------|
| `soliton_binding_first_discovery.mp4` | First successful soliton binding — the original discovery of emergent attraction from D-minimization | `python examples/animations/animate_soliton_binding.py` |
| `emergent_meson_formation.mp4` | Meson-like bound state forming from the emergent QCD bootstrap | `python examples/animations/pr0_emergent_qcd.py` |
| `strong_force_capture.mp4` | Strong-force head-on capture showing confinement-like short-range binding | `python examples/animations/animate_collision_strong_capture_multipane.py` |

### EM force dynamics (multi-panel, density + phase + field)

| File | What it shows | How to reproduce |
|------|--------------|-----------------|
| `em_attraction_solitons.mp4` | EM attraction: opposite-charge solitons, medium-energy approach | `python examples/animations/animate_collision_em_attraction_multipane_al.py` |
| `em_attraction_orbital_dynamics.mp4` | EM attraction: high-energy, rich orbital dynamics with energy logging | `python examples/animations/animate_collision_em_attraction_multipane_al.py --vy 0.18 --sep 14 --frames 1200` |
| `em_attraction_3body.mp4` | 3-body EM: two + charges and one − (H₂⁺-like); worldlines and V_em panels | `python examples/animations/animate_unified_3body_multipane_al.py` |
| `em_repulsion_solitons.mp4` | EM repulsion: same-charge solitons, short run | `python examples/animations/animate_collision_em_repulsion_multipane_al.py` |
| `em_repulsion_scattering.mp4` | EM repulsion: full high-energy Coulomb-like scattering with deflection measurement | `python examples/animations/animate_collision_em_repulsion_multipane_al.py --vx 0.20 --sep 16 --frames 1400` |

### Unified 4-force

| File | What it shows | How to reproduce |
|------|--------------|-----------------|
| `unified_all_forces_2body_multipanel.mp4` | All 4 forces simultaneously — 2-body, multi-panel (density, phase, V_em, V_weak) | `python examples/animations/animate_unified_2body_multi_panel.py` |
| `unified_all_forces_3body.mp4` | All 4 forces simultaneously — 3-body system | `python examples/animations/animate_unified_3body_multi_panel.py` |

## Static figures

| File | What it shows |
|------|--------------|
| `scattering_angle_vs_impact_parameter.png` | Scattering angle θ vs. impact parameter b — Rutherford-like scaling |
| `rutherford_scattering_comparison.png` | Emergent scattering angle overlaid on the classical Rutherford formula |
| `em_sweep_outcome_map.png` | Phase diagram of EM collision outcomes (capture / flyby / repulsion) |
| `dispersion_relation_omega_k.png` | Emergent dispersion relation ω(k) — fits ω = ℏₑff k²/2m (QM emergence) |
| `born_rule_validation.png` | P(detection) histogram vs. \|ψ\|² — Born rule emerging from field dynamics |
| `unified_all_forces_timeseries.png` | Time-series of field amplitudes in the unified 4-force simulation (Figure 1 in the companion paper) |

---

## Quick start

```bash
# Install pr0_system from repo root
pip install -e .

# Recommended: multi-panel 2-body unified simulation
cd examples/animations
python animate_unified_2body_multi_panel.py
# Output: ../../media/unified_all_forces_2body_multipanel.mp4

# Measure emergent ℏ from dispersion relation:
python measure_qm_dispersion.py
# Output: ../../media/qm_dispersion.csv + dispersion_relation_omega_k.png

# Validate Born rule:
python validate_born_rule.py
# Output: ../../media/born_rule.csv + born_rule_validation.png
```

All animation and measurement scripts save output to `media/` automatically.
