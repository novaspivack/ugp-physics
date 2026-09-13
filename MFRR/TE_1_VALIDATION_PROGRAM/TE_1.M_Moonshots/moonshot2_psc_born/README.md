---
title: "Moonshot 2 — PSC-Born Uniqueness & Ω Selection"
links:
  - kickoff: "../TE_1.M_1.1_Kickoff.md"
  - plan: "../TE_1.M_1.2_Computational_ProofPlan.md"
  - summary: "../../SESSIONS/TE_1_SUMMARY.md"
---

This package provides the executable tooling for Moonshot 2:

- Ω-driven adjudication harness and metrics.
- Finite-observer complexity deviation analyzers.
- Parallel arm experiments comparing standard Born sampling with Ω selection.
- Cached Ω provider (`omega_cached`) driven by deterministic SHA3 hashing to avoid
  heavy halting-sieve runs while preserving PSC reproducibility.
- PASS report: `Moonshot2_PSC_Born_PASS.md`.

All components are Python modules with reproducible CLI entrypoints, consistent
with the broader TE₁ validation environment.


