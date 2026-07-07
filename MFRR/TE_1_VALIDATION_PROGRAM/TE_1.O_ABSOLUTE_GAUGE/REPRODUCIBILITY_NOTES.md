# TE₁.O Absolute Gauge — Reproducibility Notes

Cross-links: [Kickoff](TE_1.0_1_1_ABSOLUTE_GAUGE_KICKOFF.md) · [Plan](TE_1.O_ABSOLUTE_GAUGE_PLAN.md) · [Final report](TE_1.0_1_3_NOVA_TASKS_FINAL_REPORT.md)

---

## 1. Runtime Environment
- Base path: repository root of `ugp-physics` (clone this archive and `cd` into it).
- Python ≥ 3.10 with `numpy` installed; all commands use the project’s virtualenv shell used for TE-program runs.
- Core availability: single-core execution unless otherwise noted.
- PR-0 tooling lives in `pr0_system` and is treated as the reusable implementation of the Absolute Gauge discrete gauge.

## 2. Dataset → Command Mapping
All JSON artifacts under `TE_1.O_ABSOLUTE_GAUGE/results/` were produced by CLI drivers shipped with PR-0. Each command below was run from the repository root; outputs were redirected into this phase directory.

| Dataset | Command | Source module |
|---------|---------|---------------|
| `results/omega_experiment.json` | `python -m pr0_system.cli.omega_experiment --runs 8 --steps 1200 --samples 40 80 120 --grid 32 --output "TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/omega_experiment.json"` | `pr0_system/cli/omega_experiment.py` |
| `results/recursive_return.json` | `python -m pr0_system.cli.recursive_return --runs 16 --steps 1600 --grid 32 --window 80 --halt-eps 5e-4 --return-eps 2e-4 --output "TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/recursive_return.json"` | `pr0_system/cli/recursive_return.py` |
| `results/energy_law.json` | `python -m pr0_system.cli.energy_law --steps 6000 --grid 32 --depth 8 --warmup 600 --output "TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/energy_law.json"` | `pr0_system/cli/energy_law.py` |
| `results/area_law.json` | `python -m pr0_system.cli.area_law --steps 3600 --grid 64 --g 0.15 --threshold 0.5 --threshold 0.7 --threshold 0.85 --weight-mode area --quantile 0.95 --mass-fraction 0.97 --output "TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/area_law.json"` | `pr0_system/cli/area_law.py` |
| `results/gauge_converter.json` | `python -m pr0_system.cli.gauge_converter --steps 1800 --grid 32 --sigma 0.5 --sigma 0.25 --sigma 0.08 --weights 0.4 0.35 0.25 --output "TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/gauge_converter.json"` | `pr0_system/cli/gauge_converter.py` |

Each CLI emits progress logs to stdout and writes the JSON payload atomically. Commands were executed after enabling the PR-0 observer hooks noted in the plan (§4) and task reports.

## 3. Observer Configuration & Seeds
- RNG seeding follows the CLI defaults: `seed = 0 .. runs-1` per task. No additional seeds were forced.
- Observer hooks enabled: `density_sum`, `internal_entropy`, `support_area`, and custom flux logs were toggled via the PR-0 config patch described in `Nova_AG_Task01_Category_Model.md`.
- Feature flags introduced for Absolute Gauge remain off by default; the CLIs explicitly enable only the instrumentation needed for these datasets.

## 4. Post-processing & Documentation
- Analytical write-ups reside under this validation program tree with cross-references to the plan and kickoff notes.
- Downstream consumers import these JSONs by paths relative to the repository root.
- Any rerun should update the SHA256 digests captured in downstream status reports; retain original outputs for provenance unless an explicit supersession is recorded here.

## 5. Outstanding Fast-Win Checks
The Kickoff (§7) and Nova final report (§“Concrete next steps”) request two additional closures:
1. Z₂ half-turn audit using the PT normal-step integrator (`pt_normal_step_integrator.py`).
2. Ω–λ⋆ comparison linking the Born-law dataset to PT restoration time.

Results from the present audit appear in the run log accompanying this file and will be summarized in the session status update.
