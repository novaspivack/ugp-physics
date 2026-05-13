---
title: "AG Task 06 — Gauge Converter Invariant Preservation"
author: Nova Spivack
date: 2025-11-10
status: PASS
links:
  - plan: "../TE_1.O_ABSOLUTE_GAUGE_PLAN.md"
  - category: "./Nova_AG_Task01_Category_Model.md"
  - dataset: "../results/gauge_converter.json"
  - pr0: "../../../pr0_system"
---

# Objective

Verify that the analytic gauge converter preserves Absolute Gauge invariants (density, entropy, support) when mapping a PR-0 state through a smoothed analytic surrogate.

# Method

Command executed:

```bash
python -m pr0_system.cli.gauge_converter --steps 1800 --grid 32 \
    --sigma 0.5 --sigma 0.25 --sigma 0.08 \
    --weight 0.4 --weight 0.35 --weight 0.25 \
    --output TE_1_VALIDATION_PROGRAM/TE_1.O_ABSOLUTE_GAUGE/results/gauge_converter.json
```

- Implemented σ-scheduling: weighted blend of three Gaussian smoothers (0.5, 0.25, 0.08) applied to the evolved state.
- Combined surrogate is renormalized to match original \(\|ψ\|_2\).
- Invariants computed before/after transformation.

# Results

- Relative error in density sum: \(5.0\times10^{-16}\) (machine precision).
- Entropy deviation: **0.76%**, accomplishing the <1% follow-up target.
- Support area unchanged (0 at threshold 0.6).

# Outcome

Gauge converter now preserves all tracked invariants within tightened tolerances; σ-scheduling is integrated into the CLI for future reuse. Task remains **PASS** with follow-up closed.

