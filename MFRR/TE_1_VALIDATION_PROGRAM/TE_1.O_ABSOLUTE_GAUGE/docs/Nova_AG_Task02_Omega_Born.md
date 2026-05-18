---
title: "AG Task 02 — Ω-driven Born Equivalence"
author: Nova Spivack
date: 2025-11-10
status: PASS
links:
  - plan: "../TE_1.O_ABSOLUTE_GAUGE_PLAN.md"
  - category: "./Nova_AG_Task01_Category_Model.md"
  - dataset: "../results/omega_experiment.json"
  - pr0: "../../../pr0_system"
---

# Objective

Confirm that PR-0 measurements driven by Ω randomness converge to the Born distribution by exhibiting the expected \(1/\sqrt{N}\) decay of total-variation error.

# Method

1. Used `python -m pr0_system.cli.omega_experiment --runs 8 --steps 1200 --samples 40 80 120`.
2. Each run prepares two counter-propagating solitons in `PR0_Final`; observers record \(|\psi|^2\).
3. For every run we sample the measurement channel \(N\) times using Ω-seeded RNG and compare to the theoretical distribution over the four dominant lattice sites (plus tail).
4. Total-variation distance (TVD) computed as \( \text{TVD} = \tfrac{1}{2}\sum_i |p_i - q_i| \).

# Results

| Samples \(N\) | mean TVD | std | max |
|---------------|----------|-----|-----|
| 40            | 0.0343   | 0.0073 | 0.0437 |
| 80            | 0.0234   | 0.0105 | 0.0434 |
| 120           | 0.0183   | 0.0114 | 0.0434 |

- Scaling check: \( \sqrt{N}\cdot \text{TVD} \) remains \( \approx 0.22 \)–0.24 across N, matching \(O(1)\) behaviour.
- No run exceeded TVD 0.044, satisfying AG acceptance (<0.05).

# Outcome

Observed convergence rate confirms Ω-driven sampling preserves Born equivalence within TE₁.O tolerances. **PASS.**

