# REPRODUCE — Ontological Dissonance Minimization / SDS Validation

**Requirements:** Python 3.10+, numpy, scipy, matplotlib.

```bash
# From ugp-physics repo root:
pip install -e pr0_system/      # only needed for Figure 1 regeneration
pip install numpy scipy matplotlib
```

---

## 1) D–Φ correlation (r=−0.9108)

```bash
cd pr0_system/examples/paper_analysis
python compare_dissonance_and_phi.py
```

**Expected output:**
```
Correlation(D, Φ) = -0.9108
✅✅✅ STRONG INVERSE CORRELATION!
D range:   [0.18, 1.41]
Φ range:   [0.21, 1.66]
```

This is fully deterministic (no random seed). Run multiple times — result is identical.

**Statistical note:** n=21 measurements (stride 250 steps on a single trajectory).
Lag-1 autocorrelation of D≈0.37; effective n_eff≈25; corrected p<10⁻⁹.

## 2) D-minimization bootstrap (γ parameters)

```bash
cd pr0_system/examples/paper_analysis
python pr0_sds_dissonance_bootstrap.py
```

**Expected:** γ_base≈0.010, γ_scale≈0.51, Best D≈0.81. Values vary slightly
run-to-run (simulated annealing). The bootstrap run reported in the paper
produced γ_base=0.0082, γ_scale=0.4705.

## 3) Figure 1 — unified all-forces time series

The frozen PNG is already present in `pr0_system/media/unified_all_forces_timeseries.png`.
The figure is a qualitative illustration; no quantitative claim depends on it.

**To regenerate from scratch** (optional, requires `pr0_system` installed):
```bash
cd pr0_system/examples/paper_analysis
python run_unified_all_forces_log.py    # writes unified_timeseries.csv here
python plot_unified_time_series.py      # writes ../../media/unified_all_forces_timeseries.png
```

## 4) Compile paper

```bash
cd papers/11_ontological_dissonance
latexmk -pdf -interaction=nonstopmode \
  Ontological_Dissonance_Minimization_SDS_Validation.tex
```

Bibliography is drawn from `../bib/Spivack_Papers_Bibliography.bib`.
