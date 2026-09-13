# Code-Level Reproduction Guide

This guide describes how to reproduce all computational results supporting the PSC Concordance paper from scratch.

## 1. Environment setup

Requirements:
- Python 3.9 or later
- `numpy` (only external dependency)

Install dependencies:

```bash
cd psc_concordance
pip install -r requirements.txt
```

No GPU, no additional build step, and no database is required. The scan runs entirely in-process.

## 2. Running the full scan pipeline

### Option A: Using the wrapper (recommended for paper reproduction)

From the `psc_concordance/` directory:

```bash
python run_psc_scan.py
```

This imports the constraint modules and scanner from `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/src/`, runs the full 20,160-universe enumeration, and saves results to:

```
psc_concordance/results/psc_scan_results.json
```

### Option B: Running the primary scan code directly

From the repository root:

```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/src/phase2_truncation
python te2_2_run_scan.py
```

Results are saved to:

```
MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/phase2_scan_results.json
```

Both options produce numerically identical results. The SHA-256 of the canonical result file is:

```
f810c1d2b07b598ef301205fee53512310552ea78cf8fb7476b3e9058d5fde93
```

Verify with:

```bash
shasum -a 256 MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/phase2_scan_results.json
```

## 3. Generating figures used in the paper

The paper currently uses no programmatically generated figures (all quantitative results are reported in tables drawn directly from the JSON output above). If figures are added in a future revision, generation scripts will be placed in `psc_concordance/scripts/` and documented here.

## 4. Expected outputs and their paths

| Output | Path | Key values |
|--------|------|------------|
| Scan results (wrapper) | `psc_concordance/results/psc_scan_results.json` | see below |
| Scan results (primary) | `MFRR/.../results/phase2_scan_results.json` | same content |

Key values in the output JSON:

| Field | Expected value |
|-------|---------------|
| `total_universes` | 20160 |
| `psc_universes` | 12 |
| `sm_rank` | 1 |
| `D_sm` | 1.066657903568035 |
| `D_min` | 1.066657903568035 |
| `global_minimizer.d` | 4 |
| `global_minimizer.gauge_group` | `"SU(3)xSU(2)xU(1)"` |
| `global_minimizer.n_generations` | 3 |
| `global_minimizer.n_observers` | 1 |
| `global_minimizer.Lambda` | 1e-122 |
| `global_minimizer.profit_ratio` | 1.13 |
| `global_minimizer.kappa` | 0.0 |
| `global_minimizer.topology` | `"flat"` |

Expected scan runtime: < 1 second on any modern CPU.

## 5. Source module inventory

The constraint implementation is organized as follows:

| Module | Location | Role |
|--------|----------|------|
| `te2_2_constraint_base.py` | `src/phase1_constraints/` | Abstract base class for constraint terms |
| `te2_2_dimensional_constraint.py` | `src/phase1_constraints/` | C_1: dimensional optimality |
| `te2_2_srrg_constraint.py` | `src/phase1_constraints/` | C_2, C_3, C_4: SRRG constraints |
| `te2_2_remaining_constraints.py` | `src/phase1_constraints/` | C_5 through C_14 |
| `te2_2_constraint_aggregator.py` | `src/phase1_constraints/` | Assembles D[Ψ] from all 14 terms |
| `te2_2_universe_enumerator.py` | `src/phase2_truncation/` | Cartesian product enumeration over the 8-parameter grid |
| `te2_2_run_scan.py` | `src/phase2_truncation/` | Entry point for the primary scan |

All paths are relative to `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/`.
