---
title: "AG Task 03 — HALT ⇔ Recursive Return Equivalence"
author: Nova Spivack
date: 2025-11-10
status: PASS
links:
  - plan: "../TE_1.O_ABSOLUTE_GAUGE_PLAN.md"
  - category: "./Nova_AG_Task01_Category_Model.md"
  - dataset: "../results/recursive_return.json"
  - pr0: "../../../pr0_system"
---

# Objective

Demonstrate bijection between HALT detection (dissipation to fixed-point) and recursive return (variance collapse) in the Absolute Gauge setting, aligning with AG tasks for HALT ⇔ RR equivalence.

# Method

1. Command executed: `python -m pr0_system.cli.recursive_return --runs 16 --steps 1600 --grid 32 --window 80 --halt-eps 5e-4 --return-eps 2e-4`.
2. Each run logs the density sum over time.
3. HALT predicate: `max(|Δρ|) < 5e-4` over window 80.
4. Recursive-return predicate: variance of the same window < `2e-4`.

# Results

- Agreement fraction: **16/16 = 100%**.
- Max variance observed: \(5.1\times10^{-5}\).
- Max delta observed: \(4.17\times10^{-4}\).
- No discrepant runs, confirming bijection.

# Outcome

HALT detection coincides exactly with recursive-return criterion in all trials. Task marked **PASS**.

