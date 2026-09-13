
# UGP Extras — Tools, Explorer, and Data

This folder ships companion code, example CSVs, and static plots for the paper
**“From GTE to UGP: Prime-Locked Universes, Minimality, and the Emergence of Our World.”**

## Quick start

```bash
# 1) Create CSVs for LaTeX figures
python ugp_cli.py scan --n-min 10 --n-max 18 --out .

# 2) (Optional) Explore interactively
pip install streamlit pandas matplotlib
streamlit run streamlit_universe_finder.py
```

The LaTeX document auto-loads `survivors.csv` and `orders.csv` if present
in the same directory as `main.tex`.

## What's inside

- `ugp_tools.py`: core math & helpers
  - deterministic 64-bit Miller–Rabin
  - divisor scan on ridges `R_n=2^n-16`
  - survivors export (`survivors.csv`) and orders export (`orders.csv`)
  - full n=10 ridge table (including composites + reasons)

- `ugp_cli.py`: command-line interface
  - `scan` — writes `survivors.csv` and `orders.csv`
  - `table -n 10` — prints full n=10 ridge table (including composites)

- `streamlit_universe_finder.py`: interactive explorer
  - **New**: mirror-pair highlighting, filters, downloads
  - **New**: invariant panel showing q-gap and Fibonacci lift (b₃ computation)
  - **New**: full n=10 ridge table section for diagnostics

- `survivors.csv`, `orders.csv`: example outputs for n=10..18
- `fig_b1_vs_b2_R1008.png`: static plot of b₁(b₂) over the n=10 ridge
- `fig_orders_10_18.png`: static bar chart of orders vs n
- `fig_universe_map_10_18.png`: static scatter (n vs b₂) for survivors

## Notes

- The Miller–Rabin bases (2,3,5,7,11,13,17) are deterministic for 64‑bit inputs.
- Feel free to widen the scan range; CSVs and plots will adapt.
- License: MIT. Conflicts of Interest: None declared.
