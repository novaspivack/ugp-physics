# Reproducing the PSC Concordance paper

## Environment requirements

- Python 3.9+ (no special installation beyond the standard library and `numpy`)
- LaTeX distribution with `pdflatex` and `bibtex` (e.g., TeX Live 2022+)

## Re-running the TE2.2 scan from scratch

The primary scan code lives in the `ugp-physics` repository. From the repository root:

```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/src/phase2_truncation
python te2_2_run_scan.py
```

This exhaustively evaluates the 14-term dissonance functional D[Ψ] over all 20,160 candidate universe descriptions and writes results to:

```
MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/phase2_scan_results.json
```

Expected runtime: < 1 second on modern hardware.

### Expected output

The result file `phase2_scan_results.json` should contain:

| Field | Expected value |
|-------|---------------|
| `total_universes` | 20160 |
| `psc_universes` | 12 |
| `sm_rank` | 1 |
| `D_sm` | 1.066657903568035 |
| `D_min` | 1.066657903568035 |
| `global_minimizer.gauge_group` | `"SU(3)xSU(2)xU(1)"` |
| `global_minimizer.d` | 4 |
| `global_minimizer.n_generations` | 3 |

### SHA-256 verification

The canonical result file has SHA-256:

```
f810c1d2b07b598ef301205fee53512310552ea78cf8fb7476b3e9058d5fde93
```

Verify with:

```bash
shasum -a 256 MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/results/phase2_scan_results.json
```

## Alternatively: using the psc_concordance wrapper

A thin wrapper script is provided in `psc_concordance/`:

```bash
cd psc_concordance
python run_psc_scan.py
```

Results are saved to `psc_concordance/results/psc_scan_results.json`. See `psc_concordance/REPRODUCE.md` for details.

## Building the PDF

From `papers/14_psc_concordance/`:

```bash
pdflatex PSC_Concordance.tex
bibtex PSC_Concordance
pdflatex PSC_Concordance.tex
pdflatex PSC_Concordance.tex
```

Bibliography source: `../bib/Spivack_Papers_Bibliography.bib`.

## Cross-references

- Scan code: `MFRR/TE_2_Advanced_Explorations/TE_2_2_Minimal_PSC_Universe/`
- Wrapper and analysis scripts: `psc_concordance/`
- Lean 4 formalization (Papers 20, 21): DOI 10.5281/zenodo.19433538
