# PSC Concordance — Code Companion

This directory is the code companion to the paper:

> **Formal and Computational Concordance on PSC-Selected Standard Model Structure: Axiomatic Closure Theorems and Finite Universe Enumeration**
> Nova Spivack, 2026
> (`papers/14_psc_concordance/PSC_Concordance.tex`)

## What this code does

The PSC concordance scan exhaustively evaluates the 14-term PSC dissonance functional

```
D[Ψ] = Σ_{i=1}^{14} w_i ‖C_i[Ψ]‖²
```

over 20,160 candidate universe descriptions. Each description is an eight-parameter tuple

```
Ψ = (d, G, N_gen, N_obs, Λ, ρ, κ, τ)
```

parameterizing spacetime dimension, gauge group, number of fermion generations, observer count, cosmological constant, information profit ratio, spatial curvature, and global topology.

The scan identifies the global minimizer of D[Ψ], counts how many candidates pass the hard PSC filters, and verifies that the Standard Model gauge structure (d=4, G=SU(3)×SU(2)×U(1), N_gen=3) is the unique co-minimum family.

## Primary scan code

The scan implementation lives in:

```
MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/
```

The modules there define the constraint functions, universe enumerator, and scanner. This `psc_concordance/` directory provides:

- `run_psc_scan.py` — a thin wrapper that imports from the primary scan code, runs the full scan, and saves results here under `results/`
- `REPRODUCE.md` — code-level reproduction guide

## Installation

No special packages are required beyond the Python standard library and `numpy`:

```bash
pip install -r requirements.txt
```

Python 3.9 or later is required.

## How to run

From the `psc_concordance/` directory:

```bash
python run_psc_scan.py
```

This runs the full 20,160-universe scan and prints a summary to stdout. Results are saved to `results/psc_scan_results.json`.

## Expected outputs

| Output | Path | Description |
|--------|------|-------------|
| Scan results JSON | `results/psc_scan_results.json` | Full scan output including all top-10 universes |
| Console summary | stdout | Total universes, PSC count, SM rank, D_SM |

Expected console output (values may differ slightly in `elapsed_seconds` and `throughput`):

```
Total universes:  20160
PSC-passing:      12  (0.06%)
SM rank:          1
D_SM:             1.066658
D_min:            1.066658
Global minimizer: d=4, G=SU(3)xSU(2)xU(1), N_gen=3
```

## File inventory

| File | Description |
|------|-------------|
| `run_psc_scan.py` | Entry-point wrapper; imports scan from MFRR source, saves results here |
| `requirements.txt` | Python dependencies (numpy) |
| `README.md` | This file |
| `REPRODUCE.md` | Detailed code-level reproduction guide |
| `results/` | Output directory created at runtime |

## Canonical result

The canonical result file (committed to the repository) is:

```
MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/phase2_scan_results.json
```

SHA-256: `f810c1d2b07b598ef301205fee53512310552ea78cf8fb7476b3e9058d5fde93`

## Paper

See `papers/14_psc_concordance/` for the LaTeX source, compiled PDF, figures, and provenance documentation.
