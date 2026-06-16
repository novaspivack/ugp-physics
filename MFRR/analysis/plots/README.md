# MFRR Figure Generation Scripts

This directory contains plotting and table-generation scripts for the **Mathematical Foundations of Reflexive Reality (MFRR)** paper, specifically for Appendices G and I.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate all figures and tables
make

# Or generate individually
make plots   # All plots only
make tables  # All tables only
```

---

## Requirements

- **Python:** 3.12 or later
- **Packages:** See `requirements.txt`
  - numpy >= 2.0.0
  - scipy >= 1.14.0
  - matplotlib >= 3.9.0
  - pandas >= 2.2.0
  - seaborn >= 0.13.0 (optional)

---

## Input Data Files

All scripts expect data files in `../../data/`:

### Required Files:

1. **`energy_timeseries.csv`**
   - Columns: `t`, `E_tot`, `D_psi`, `D_chi`, `W_ext`
   - Energy balance traces during PT events

2. **`psi_fields.npz`**
   - Arrays: `psi_t0`, `psi_t1` (2D fields of coherence Ψ)
   - Optional: `grad_psi_t0`, `grad_psi_t1` (gradient magnitudes)

3. **`landauer_trials.csv`**
   - Columns: `trial_id`, `regime`, `delta_E_PT`, `kBTlogn`, `lambda1_intPsi2`, `lambda2_intGradPsi2`
   - Reflexive Landauer bound verification data

4. **`d_phi_series.csv`**
   - Columns: `t`, `D`, `Phi`
   - Dissonance-information correlation time series

---

## Output Files

All outputs go to `../../figures/`:

### Plots (PDF + PNG):
- `pt_energy_balance.pdf` - Energy traces during PT
- `psi_maps.pdf` - Spatial maps of Ψ field (start/end)
- `psi_grad_maps.pdf` - Gradient magnitude maps
- `landauer_margins_scatter.pdf` - Margin scatter by regime
- `d_phi_correlation.pdf` - D-Φ correlation plot

### Tables:
- `landauer_table.tex` - LaTeX table for Appendix I
- `landauer_margins_stats.csv` - Summary statistics

---

## Scripts

### `plot_energy_balance.py`
Generates energy balance traces during PT events.
- Input: `energy_timeseries.csv`
- Output: `pt_energy_balance.{pdf,png}`

### `plot_psi_fields.py`
Generates spatial field maps of Ψ and ‖∇Ψ‖.
- Input: `psi_fields.npz`
- Output: `psi_maps.{pdf,png}`, `psi_grad_maps.{pdf,png}`

### `plot_landauer_margins.py`
Scatter plot of Reflexive Landauer margins by regime.
- Input: `landauer_trials.csv`
- Output: `landauer_margins_scatter.{pdf,png}`, `landauer_margins_stats.csv`

### `plot_d_phi_correlation.py`
D-Φ anticorrelation scatter plot with linear fit.
- Input: `d_phi_series.csv`
- Output: `d_phi_correlation.{pdf,png}`

### `generate_landauer_table.py`
Generates LaTeX table and CSV summary of Landauer bound verification.
- Input: `landauer_trials.csv`
- Output: `landauer_table.tex`, `landauer_margins_stats.csv`

---

## Makefile Targets

```bash
make          # Generate all figures and tables (default)
make plots    # Generate all PDF/PNG plots
make tables   # Generate LaTeX tables and CSV summaries
make clean    # Remove all generated files
make help     # Show help message
```

---

## Integration with MFRR Paper

### In LaTeX Document:

```latex
% Appendix I - PR-0 Numerical Verification
\subsection{Empirical Results}

% Include generated table
\input{figures/landauer_table.tex}

% Include figures
\begin{figure}[H]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/d_phi_correlation.pdf}
  \caption{D-Φ anticorrelation (r=-0.91, p<0.001)}
\end{figure}
```

---

## Directory Structure

```
MATHEMATICAL_FOUNDATIONS_REFLEXIVE_REALITY/
├── analysis/
│   └── plots/
│       ├── Makefile
│       ├── requirements.txt
│       ├── README.md (this file)
│       ├── plot_energy_balance.py
│       ├── plot_psi_fields.py
│       ├── plot_landauer_margins.py
│       ├── plot_d_phi_correlation.py
│       └── generate_landauer_table.py
├── data/
│   ├── energy_timeseries.csv
│   ├── psi_fields.npz
│   ├── landauer_trials.csv
│   └── d_phi_series.csv
└── figures/
    └── (generated outputs)
```

---

## Reproducibility Notes

- All scripts use fixed random seeds where applicable
- Figure styles match paper formatting (11pt fonts, grayscale-friendly colors)
- PDF outputs are publication-quality (vector graphics)
- Scripts are self-contained (no external dependencies beyond requirements.txt)

---

## Version Information

- **Created:** November 3, 2025
- **Python version:** 3.12+
- **Associated paper:** Mathematical Foundations of Reflexive Reality (MFRR)
- **License:** MIT (code), CC BY-NC 4.0 (figures)

---

## Contact

For questions about the plotting pipeline or data formats, see the main MFRR repository documentation.

