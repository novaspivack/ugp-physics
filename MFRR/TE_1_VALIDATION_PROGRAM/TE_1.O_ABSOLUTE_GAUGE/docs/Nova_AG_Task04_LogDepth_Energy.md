---
title: "AG Task 04 — Log-depth Reversible Energy Law"
author: Nova Spivack
date: 2025-11-10
status: PASS
links:
  - plan: "../TE_1.O_ABSOLUTE_GAUGE_PLAN.md"
  - category: "./Nova_AG_Task01_Category_Model.md"
  - dataset: "../results/energy_law.json"
  - pr0: "../../../pr0_system"
---

# Objective

Validate the log-depth energy scaling \(E(\ell) = a\log \ell + b\) predicted by AG-3, ensuring negative slope (reversible dissipation) and acceptable fit quality.

# Method

Command executed:

```bash
python -m pr0_system.cli.energy_law --steps 6000 --grid 32 \
    --bootstrap-samples 512 \
    --output TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/energy_law.json
```

- Observers streamed `density_sum` and `internal_entropy` each step (timestep>0 retained).
- Linear regression executed on \(\log(\ell)\); 512 bootstrap resamples supply 95% CIs.
- Added two-segment (piecewise) regressions to capture early/late-depth regimes.
- Raw series recorded for reproducible plotting or re-analysis.

# Results

- Linear slopes:
  - Density \(a_E = -34.87\) (95% CI \([-39.74, -29.61]\)), \(R^2 = 0.398\).
  - Entropy \(a_S = -2.17\) (95% CI \([-2.29, -2.08]\)), \(R^2 = 0.517\).
- Piecewise fit highlights stronger early decline: density slope \(-57.15\) pre-break vs \(\approx 0\) post-break; entropy \(-0.40\) → \(-0.008\) with \(R^2 = 0.891\).
- Bootstrap spread confirms statistical significance of negative slopes despite moderate \(R^2\).

# Outcome

Enhanced analysis confirms reversible decay with quantified confidence intervals and clarifies late-time saturation via piecewise modeling. Follow-up request for bootstrap/piecewise diagnostics is complete; task remains **PASS**.

