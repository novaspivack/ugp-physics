# REPRODUCE — MFRR computational artifacts

All commands assume **`cd`** to this directory (`MFRR/` at the repo root).

Paths below are **relative to that directory** unless stated otherwise.

**Docstrings:** `TE_1_VALIDATION_PROGRAM/**/*.py` and `TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/*.py` cite README paths **relative to this MFRR root** (no machine-specific prefixes).

**Monograph `sec:code-data`:** bare filenames in the artifact tables use this same MFRR root; scripts named `ts*.py`, `v*.py`, and `e9d_*` / `e9e_*` / `e9f_*` are under `SRRG_VALIDATION_PROGRAM/scripts/` (see § SRRG TS1 below).

**Module count (abstract, `CLM-A-004`):** definition plus reproducible `find` command and current tally — see **`MODULE_INVENTORY.md`** at this MFRR root (**297** first-party `.py` files with standard exclusions as of that file).

## External dependency: delta-machine (DSAC)

The DSAC/$\Delta$-Machine experiments referenced in the monograph (Phase I rediscovery benchmarks, Phase II curvature-invariant and transport law, Phase III Band C / TE₂.H holographic metrics) live in a **separate repository**:

- **GitHub:** https://github.com/novaspivack/delta-machine
- **Paper (77):** https://doi.org/10.5281/zenodo.19429884
- **Transputation theory (76):** https://doi.org/10.5281/zenodo.19429882

The monograph `.tex` references delta-machine data via the relative path `../Delta_machine/` (sibling of `MFRR/`). One figure (TE₂.H holographic metrics) uses `\IfFileExists` and degrades gracefully if the repo is not present — the paper compiles without it.

To reproduce DSAC results:

```bash
# Clone delta-machine as a sibling of this directory
cd ..
git clone https://github.com/novaspivack/delta-machine Delta_machine
cd Delta_machine
pip install -r requirements.txt
# Follow Delta_machine/REPRODUCE.md for step-by-step scenario runs
```

The `pr0_system` package (used for PR-0 field-state backends in DSAC) is the same `pr0_system/` at the root of the `ugp-physics` repository. Set `PYTHONPATH` or `PR0_SYSTEM_ROOT` accordingly per `Delta_machine/notes/1.13_pr0_integration_usage.md`.

## Environment

- **Python:** 3.9+ (development baseline recorded as **Python 3.9.6** on macOS).
- **Core packages:** `numpy`, `scipy`, `matplotlib`; SRRG scripts also use `tqdm`, `pandas` where present.
- **Optional:** `multiprocessing` (stdlib) for parallel sweeps.

Install example (adjust for your environment):

```bash
python3 -m pip install numpy scipy matplotlib tqdm pandas
```

Or use the root `requirements.txt`:

```bash
pip install -r ../requirements.txt
```

## Quick checks (small, deterministic)

### E1 — GTE \(n=10\) ridge trace

```bash
python3 E1_gte_n10_block_trace.py
```

**Expected:** `E1_gte_n10_block_trace_results.json` with `"status": "PASS"`.

### E2 — Lieb–Robinson UWCA

```bash
python3 E2_lieb_robinson_causality_check.py
```

**Outputs:** `E2_lieb_robinson_results.json`, `E2_lieb_robinson_causality.png` next to the script.

### Adjudication–entropy audit

Regression artifact **`results/rft_entropy_vs_events_fit.json`** stores fitted slope metadata (including `eta_over_kB`, `slope_ratio`, `R2`). Verify keys in that JSON against any prose edits before export to ensure numerical consistency with **Theorem Adjudication–Entropy** (\(\eta\approx k_B\ln 2\)) in the monograph abstract.

### E7 — Growth / \(f\sigma_8\) (monograph filename)

```bash
python3 g23_growth_sigma8.py
```

Delegates to `e15_growth.py`; writes under `e15_growth_outputs/` (plots + `fs8_summary.csv`).

## TE₁.A TFT (heavy)

Entrypoints:

- `TE_1_VALIDATION_PROGRAM/TE_1.A_TFT/run_te1a.py` — full suite orchestration, writes under `TE_1_VALIDATION_PROGRAM/TE_1.A_TFT/results/`.
- `TE_1_VALIDATION_PROGRAM/TE_1.A_TFT/te1a_pipeline.py` — library + `run_te1a_case`; imports **`pr0_system`** via path bootstrap to `pr0_system/` at the repo root.

**Canonical PASS bundle (do not re-run full suite unless required):**

`TE_1_VALIDATION_PROGRAM/TE_1.A_TFT/results/run_20251107_210503/`

See `TE_1_VALIDATION_PROGRAM/TE_1.A_TFT/results/CANONICAL_RUN.txt`.

Example (from MFRR root):

```bash
cd TE_1_VALIDATION_PROGRAM/TE_1.A_TFT && python3 run_te1a.py
```

Expect long runtime and multiprocessing; prefer **artifact verification** when canonical outputs exist.

## TE₂.1 Steel-man (Part V)

The monograph names these scripts at **MFRR root**. Thin wrappers delegate to  
`TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/STEELMAN_V3/` (same base names):

```bash
python3 MFRR_Gravity_Steelman.py
python3 MFRR_Entanglement_Steelman.py
python3 MFRR_Quantization_Steelman_v5.py
```

Runtime depends on built-in steps and hardware; not part of the "quick check" suite.

## PR-1 braid atlas (TS7 / SRRG)

Scripts resolve  
`topology_lab/` (braid atlas) via `Path(__file__).parents[4]` from `SRRG_VALIDATION_PROGRAM/scripts/` (no machine-specific prefix).

## SRRG TS1 (moderate — multiprocessing)

```bash
cd SRRG_VALIDATION_PROGRAM/scripts && python3 ts1_final_pure_gte.py
```

**Inputs:** `SRRG_VALIDATION_PROGRAM/data/canonical_sm_triples.json`  
**Outputs:** `SRRG_VALIDATION_PROGRAM/outputs/ts1_final/ts1_final_results.json` (and plots).

## Black hole — QNM script

```bash
cd BH_REFLEXIVE_REALITY/scripts && python3 qnm_rr_shift.py
```

**Outputs (relative to `scripts/` cwd):** `csv/qnm_rr_scan.csv`, `figs/qnm_rr_summary.png`.

## TE₁.B RSM v2

Production-style outputs live under:

`TE_1_VALIDATION_PROGRAM/TE_1.B_RSM_v2/results_production/`

(run ids such as `te1b_v2_20251118_*`). Older paths mentioning `TE_1.B_RSM/results/run_...` may not exist — use **`results_production`** and match the cited metrics to an actual `summary.json` if updating prose.

## Tolerances

- Replication **must not** contradict monograph PASS/FAIL flags. Numerical re-runs may differ slightly in floating-point detail; fix code if results are qualitatively inconsistent with the paper.
