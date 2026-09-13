# Paper Analysis Scripts

These scripts reproduce the core computational claims in the companion paper:
*"Ontological Dissonance Minimization and the Self-Defining Substrate (SDS) Validation"*.

They are standalone (no `pr0_system` package import needed for most) and use only
`numpy`, `scipy`, and `matplotlib`.

---

## Scripts

| Script | What it does | Paper claim |
|--------|-------------|-------------|
| `pr0_sds_dissonance_bootstrap.py` | Bootstrap that drives PR-0 field dynamics by minimizing ontological dissonance D instead of explicit force rules | §3: D-minimization produces stable bound states |
| `compare_dissonance_and_phi.py` | Measures both D and Φ_proxy (spatial entropy) for the same bound system across 21 runs; computes correlation | §4: D–Φ anti-correlation, r = −0.9108, p < 10⁻⁹ |
| `run_unified_all_forces_log.py` | Runs the unified 4-force simulation and logs field amplitude / separation time-series to CSV | Figure 1 data |
| `plot_unified_time_series.py` | Reads the CSV from the above and produces the time-series PNG | Figure 1 |

## Usage

```bash
cd examples/paper_analysis

# 1. Run the D-minimization bootstrap (produces bound states)
python pr0_sds_dissonance_bootstrap.py

# 2. Measure D–Φ correlation (reproduces the r = −0.9108 result)
python compare_dissonance_and_phi.py

# 3. Regenerate Figure 1 data + plot
python run_unified_all_forces_log.py   # writes unified_timeseries.csv here
python plot_unified_time_series.py     # writes media/unified_all_forces_timeseries.png
```

`run_unified_all_forces_log.py` and `compare_dissonance_and_phi.py` import
`pr0_system`; install first with `pip install -e ../../../` from repo root.
